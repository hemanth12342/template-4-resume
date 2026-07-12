"""
main.py — AI Resume Builder Backend
FastAPI application that:
  1. Receives an uploaded resume (PDF / TXT) + a job description + template_id.
  2. Extracts structured data from the resume via Groq LLM.
  3. Enhances that data to match the JD via a second Groq call.
  4. Passes the enriched data to latex_generator.py:
       • template_id 1–4  → single PDF returned as attachment
       • template_id 0    → all 4 PDFs returned as a ZIP archive
"""

import asyncio
import io
import json
import os
import re
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq

from latex_generator import generate_pdf, generate_all_pdfs

load_dotenv()

# ── App & CORS ────────────────────────────────────────────────────────────────

app = FastAPI(title="AI Resume Builder", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Groq client ───────────────────────────────────────────────────────────────

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL   = "llama-3.3-70b-versatile"

MAX_FILE_BYTES = 10 * 1024 * 1024   # 10 MB hard limit

_pool = ThreadPoolExecutor(max_workers=4)


# ── Utility functions ─────────────────────────────────────────────────────────

def _extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from a PDF or TXT resume file."""
    if filename.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages).strip()
        except Exception as exc:
            raise HTTPException(400, f"Could not read PDF: {exc}") from exc

        if not text:
            raise HTTPException(
                400,
                "The PDF has no extractable text. "
                "It may be a scanned image — please convert to a text-based PDF or paste as TXT.",
            )
        return text

    try:
        return file_bytes.decode("utf-8", errors="ignore").strip()
    except Exception as exc:
        raise HTTPException(400, f"Could not decode file: {exc}") from exc


def _strip_fences(text: str) -> str:
    """Remove markdown ```json ... ``` code fences from LLM responses."""
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$",          "", text)
    return text.strip()


def _groq_call(prompt: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
    """Call the Groq API with simple exponential-backoff retry (up to 3 attempts)."""
    for attempt in range(3):
        try:
            resp = _client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as exc:
            if attempt == 2:
                raise HTTPException(502, f"Groq API error after 3 attempts: {exc}") from exc
            time.sleep(2 ** attempt)
    return ""


# ── JSON schema (used in prompts) ─────────────────────────────────────────────

_RESUME_SCHEMA = """{
  "name":          "Full Name",
  "email":         "user@example.com",
  "phone":         "+1-XXX-XXX-XXXX",
  "portfolio_url": "https://portfolio.com",
  "github":        "github_username",
  "linkedin":      "https://linkedin.com/in/username",
  "summary":       "",
  "education": [
    {
      "degree":      "Bachelor of Technology",
      "institution": "University Name",
      "field":       "Computer Science",
      "dates":       "Aug 2020 - May 2024",
      "gpa":         "8.5/10",
      "courses":     "Data Structures, Algorithms, Machine Learning"
    }
  ],
  "skills": [
    { "category": "Languages",   "items": "Python, Java, JavaScript" },
    { "category": "Frameworks",  "items": "FastAPI, React, TensorFlow" },
    { "category": "Tools",       "items": "Git, Docker, AWS" },
    { "category": "Soft Skills", "items": "Leadership, Communication, Agile" }
  ],
  "experience": [
    {
      "role":     "Software Engineer",
      "company":  "Tech Corp",
      "location": "Remote",
      "dates":    "Jun 2023 - Present",
      "bullets":  [
        "Built X feature that improved Y by Z%",
        "Led team initiative reducing latency by N ms across M services"
      ]
    }
  ],
  "projects": [
    {
      "title":        "Project Name",
      "technologies": "Python, React, PostgreSQL",
      "description":  "What the project does and the measurable impact it achieved"
    }
  ],
  "awards": [
    "Award Name - Month, Year"
  ],
  "volunteer": [
    {
      "role":         "Community Lead",
      "organization": "Tech Community",
      "location":     "City, Country",
      "dates":        "Jan 2022 - Present",
      "description":  "What you contributed and its impact"
    }
  ]
}"""


# ── AI pipeline steps ─────────────────────────────────────────────────────────

def _parse_resume(resume_text: str) -> dict:
    """Step 1 — Extract all resume info into structured JSON using Groq."""
    prompt = f"""You are a precise resume parser.

Extract ALL information from the resume text below and return it as a valid JSON object.

RULES:
- Do NOT invent or infer any information not explicitly present in the text.
- Use empty strings "" or empty arrays [] for absent fields.
- Group skills into logical categories (Languages, Frameworks, Tools, Soft Skills).
- All string values must be PLAIN TEXT ONLY — no LaTeX commands, no Markdown
  formatting (*bold*, **bold**, etc.), no HTML tags. Natural English only.
- Return ONLY the JSON object — no markdown fences, no preamble, no explanation.

RESUME TEXT:
---
{resume_text}
---

Return the JSON object matching this exact schema:
{_RESUME_SCHEMA}
"""
    raw = _groq_call(prompt, temperature=0.05, max_tokens=4096)
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise HTTPException(500, f"AI failed to return valid JSON during parsing: {exc}") from exc


def _enhance(data: dict, jd: str) -> dict:
    """Step 2 — Tailor the structured resume data to the job description."""
    prompt = f"""You are a world-class resume strategist, ATS expert, and career coach.

Your task: transform the structured resume data below into a perfectly tailored,
ATS-optimised resume for the target job description.

CURRENT RESUME DATA:
---
{json.dumps(data, indent=2)}
---

TARGET JOB DESCRIPTION:
---
{jd}
---

MANDATORY ENHANCEMENT RULES (all must be followed):

1. PROFESSIONAL FRAMING
   NEVER use the words "student", "fresher", "junior", or "trainee".
   Position the candidate as a skilled professional ready to deliver immediate value.

2. PROFILE SUMMARY
   Write a compelling 3-4 sentence professional summary that:
   - Opens with the candidate's strongest value proposition
   - Mirrors key phrases from the JD naturally
   - Highlights the most relevant experience and skills
   - Ends with what the candidate brings to this specific role

3. BULLET POINTS
   Every experience entry must have exactly 3-4 bullet points using the STAR method
   (Situation → Task → Action → Result). Rules:
   - Start each bullet with a strong action verb (Architected, Engineered, Accelerated…)
   - Quantify impact wherever plausible (%, ms, $, users, requests/s)
   - Align vocabulary with JD keywords
   - If original bullets are sparse or missing, generate authentic-sounding ones
     based on the role and company context

4. SKILLS ALIGNMENT
   Reorder skill categories to surface JD-relevant skills first.
   Only include skills the candidate plausibly possesses based on their experience.

5. GRAMMAR & TENSE
   Fix all grammatical errors.
   Past tense for completed roles; present tense for current role.

6. PLAIN TEXT ONLY
   All string values must be plain text — no LaTeX, no Markdown, no HTML.

Return ONLY the enhanced JSON object in the EXACT SAME SCHEMA as the input.
No markdown fences, no commentary, just the JSON.
"""
    raw = _groq_call(prompt, temperature=0.3, max_tokens=4500)
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise HTTPException(500, f"AI failed to return valid JSON during enhancement: {exc}") from exc


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/generate")
async def generate_resume(
    resume_file:     UploadFile = File(..., description="PDF or TXT resume"),
    job_description: str        = Form(..., description="Full job description text"),
    template_id:     str        = Form("4", description="Template 1–4, or 0 for all 4 as ZIP"),
):
    """
    Main endpoint.
    Accepts a multipart form with:
      - resume_file     : the candidate's current resume (PDF or TXT)
      - job_description : the target job description (plain text)
      - template_id     : "1"–"4" for a single PDF, "0" for all 4 as a ZIP archive

    Returns a PDF (single) or ZIP (all 4) as an attachment.
    """
    # ── Validate ──────────────────────────────────────────────
    if not resume_file.filename:
        raise HTTPException(400, "No file provided.")
    if len(job_description.strip()) < 30:
        raise HTTPException(400, "Job description is too short (minimum 30 characters).")

    try:
        tid = int(template_id)
    except ValueError:
        raise HTTPException(400, "template_id must be an integer 0–4.")
    if tid not in {0, 1, 2, 3, 4}:
        raise HTTPException(400, "template_id must be 0 (all), 1, 2, 3, or 4.")

    file_bytes = await resume_file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(400, "File is too large. Maximum allowed size is 10 MB.")

    # ── Text extraction ────────────────────────────────────────
    resume_text = _extract_text(file_bytes, resume_file.filename)

    # ── AI pipeline ────────────────────────────────────────────
    loop = asyncio.get_event_loop()

    structured = await loop.run_in_executor(_pool, _parse_resume, resume_text)
    enhanced   = await loop.run_in_executor(_pool, partial(_enhance, structured, job_description))

    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", enhanced.get("name", "resume"))

    # ── Single template → PDF ──────────────────────────────────
    if tid != 0:
        try:
            pdf_bytes = await loop.run_in_executor(
                _pool, partial(generate_pdf, enhanced, tid)
            )
        except RuntimeError as exc:
            raise HTTPException(500, f"PDF compilation failed: {exc}") from exc

        filename = f"resume_{safe_name}_T{tid}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # ── All 4 templates → ZIP ──────────────────────────────────
    try:
        all_pdfs = await loop.run_in_executor(_pool, partial(generate_all_pdfs, enhanced))
    except RuntimeError as exc:
        raise HTTPException(500, f"PDF compilation failed: {exc}") from exc

    zip_buffer = io.BytesIO()
    template_names = {
        1: "Classic",
        2: "Modern",
        3: "Sidebar",
        4: "ATS_Classic",
    }
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for t_id, pdf_bytes in sorted(all_pdfs.items()):
            zf.writestr(
                f"resume_{safe_name}_Template{t_id}_{template_names[t_id]}.pdf",
                pdf_bytes,
            )
    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="resume_{safe_name}_all_templates.zip"'
        },
    )


@app.get("/health")
async def health():
    """Simple liveness probe."""
    return {"status": "ok", "model": MODEL, "templates": [1, 2, 3, 4]}


# ── Local runner ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

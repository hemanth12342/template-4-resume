"""
main.py — AI Resume Builder Backend (4-template version)
"""

import asyncio
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial

import pdfplumber
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq

from latex_generator import generate_pdf

load_dotenv()

app = FastAPI(title="AI Resume Builder", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ← replace "*" with your Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL   = "llama-3.1-8b-instant"
MAX_FILE_BYTES = 10 * 1024 * 1024
_pool = ThreadPoolExecutor(max_workers=4)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages).strip()
        except Exception as exc:
            raise HTTPException(400, f"Could not read PDF: {exc}") from exc
        if not text:
            raise HTTPException(400, "PDF has no extractable text (scanned image?). Use a text-based PDF or paste as TXT.")
        return text
    try:
        return file_bytes.decode("utf-8", errors="ignore").strip()
    except Exception as exc:
        raise HTTPException(400, f"Could not decode file: {exc}") from exc


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _groq_call(prompt: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
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
                raise HTTPException(502, f"Groq API error: {exc}") from exc
            time.sleep(2 ** attempt)
    return ""


_SCHEMA = """{
  "name": "Full Name",
  "email": "user@example.com",
  "phone": "+1-XXX-XXX-XXXX",
  "portfolio_url": "https://portfolio.com",
  "github": "github_username",
  "linkedin": "https://linkedin.com/in/username",
  "summary": "",
  "education": [
    {"degree": "Bachelor of Technology", "institution": "University Name",
     "field": "Computer Science", "dates": "Aug 2020 - May 2024",
     "gpa": "8.5/10", "courses": "Data Structures, Algorithms"}
  ],
  "skills": [
    {"category": "Languages",   "skill_list": "Python, Java, JavaScript"},
    {"category": "Frameworks",  "skill_list": "FastAPI, React, TensorFlow"},
    {"category": "Tools",       "skill_list": "Git, Docker, AWS"},
    {"category": "Soft Skills", "skill_list": "Leadership, Communication"}
  ],
  "experience": [
    {"role": "Software Engineer", "company": "Tech Corp", "location": "Remote",
     "dates": "Jun 2023 - Present",
     "bullets": ["Built X improving Y by Z%", "Led initiative saving N hours/week"]}
  ],
  "projects": [
    {"title": "Project Name", "technologies": "Python, React",
     "description": "What it does and its impact"}
  ],
  "awards": ["Award Name - Year"],
  "volunteer": [
    {"role": "Lead", "organization": "Community", "location": "City",
     "dates": "2022 - Present", "description": "What you contributed"}
  ],
  "certifications": [
    {"name": "Certification Name", "issuer": "Issuing Body",
     "date": "Month Year", "url": "https://verify.link"}
  ]
}"""


# ── AI pipeline ───────────────────────────────────────────────────────────────

def _parse_resume(text: str) -> dict:
    prompt = f"""You are a precise resume parser.

Extract ALL information from the resume below. Return ONLY a valid JSON object —
no markdown fences, no preamble, no explanation.

RULES:
- Do NOT invent any information not in the text.
- Use "" or [] for absent fields.
- All string values must be plain text only — no LaTeX, no Markdown, no HTML.

RESUME:
---
{text}
---

Return JSON matching this schema:
{_SCHEMA}
"""
    raw = _groq_call(prompt, temperature=0.05)
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise HTTPException(500, f"AI failed to parse resume JSON: {exc}") from exc


def _enhance(data: dict, jd: str) -> dict:
    prompt = f"""You are a world-class resume strategist and ATS expert.

Transform the resume data below into a perfectly tailored, ATS-optimised resume
for the target job description.

CURRENT RESUME DATA:
---
{json.dumps(data, indent=2)}
---

JOB DESCRIPTION:
---
{jd}
---

MANDATORY RULES:
1. NEVER use "student", "fresher", "junior", or "trainee" — position as an experienced professional.
2. Write a compelling 3-4 sentence Profile Summary mirroring JD keywords.
3. Every experience must have 3-4 strong STAR-method bullet points with action verbs and metrics.
4. Reorder skills to surface JD-relevant ones first.
5. Fix all grammar; past tense for past roles, present for current.
6. All string values must be PLAIN TEXT ONLY — no LaTeX, no Markdown, no HTML.

Return ONLY the enhanced JSON in the EXACT SAME SCHEMA. No markdown, no commentary.
"""
    raw = _groq_call(prompt, temperature=0.3, max_tokens=4500)
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError as exc:
        raise HTTPException(500, f"AI failed to enhance resume JSON: {exc}") from exc


# ── Endpoint ──────────────────────────────────────────────────────────────────

@app.post("/generate")
async def generate_resume(
    resume_file:     UploadFile = File(...),
    job_description: str        = Form(...),
    template_id:     int        = Form(default=4),   # ← 1, 2, 3, or 4
):
    """Upload resume + JD + template choice → tailored PDF."""

    if not resume_file.filename:
        raise HTTPException(400, "No file provided.")
    if len(job_description.strip()) < 30:
        raise HTTPException(400, "Job description too short.")
    if template_id not in (1, 2, 3, 4):
        raise HTTPException(400, "template_id must be 1, 2, 3, or 4.")

    file_bytes = await resume_file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(400, "File too large (max 10 MB).")

    resume_text = _extract_text(file_bytes, resume_file.filename)

    loop = asyncio.get_event_loop()
    structured = await loop.run_in_executor(_pool, _parse_resume, resume_text)
    enhanced   = await loop.run_in_executor(_pool, partial(_enhance, structured, job_description))

    try:
        pdf_bytes = await loop.run_in_executor(_pool, generate_pdf, enhanced, template_id)
    except RuntimeError as exc:
        raise HTTPException(500, f"PDF compilation failed: {exc}") from exc

    safe_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", enhanced.get("name", "resume"))
    filename  = f"resume_{safe_name}_t{template_id}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL, "templates": [1, 2, 3, 4]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

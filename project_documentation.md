# AI Resume Builder: Official Project Documentation

> [!NOTE]
> This document serves as the official manual for the **AI Resume Builder** project. It outlines the platform's purpose, its underlying architecture, the workflow for users, and instructions for local deployment.

---

## 1. Executive Summary

The **AI Resume Builder** is an intelligent, automated platform designed to bridge the gap between a candidate's baseline resume and the specific requirements of a target Job Description (JD). 

By leveraging advanced Large Language Models (LLMs) via the **Groq API** and the robust typesetting capabilities of **LaTeX**, this platform eliminates the tedious process of manually tailoring resumes. It ensures that every application is highly targeted, ATS-friendly, and professionally formatted.

---

## 2. Core Features

### 🔍 Intelligent Data Extraction
Upon uploading a baseline resume (in PDF or TXT format), the system employs optical character recognition and parsing algorithms to extract the user's professional data. 
Users are presented with an **interactive Data Preview** card to review and verify their extracted information (Name, Skills, Experience, Education, etc.) before proceeding.

### 🧠 AI-Powered Tailoring
The core intelligence of the platform relies on Groq's blazing-fast LLMs (such as Llama 3 or Mixtral). When provided with a target Job Description, the AI:
- Strategically rewrites bullet points to align with the JD.
- Quantifies achievements where possible.
- Generates a compelling, highly targeted profile summary.
- Reorders skills to highlight the most relevant ones first.

### 📄 Automated LaTeX Compilation
To guarantee a flawless presentation, the tailored data is automatically injected into professional LaTeX templates. The system handles all compilation seamlessly in the background, outputting a pristine PDF without any manual formatting struggles.

### 🎨 Premium Templates
Users can select from multiple professionally designed templates tailored to different career paths:
1. **Modern CV (T1):** Centered header with social icons; ideal for creative or academic roles.
2. **Data Science (T2):** Clean, two-column layout optimized for Data/ML professionals.
3. **Developer (T3):** A highly compact, ATS-friendly layout favored by tech professionals (often referred to as the FAANG Path).

---

## 3. Technology Architecture

The platform is built using a modern, scalable technology stack:

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript | Provides a lightweight, responsive, and interactive user interface. Ready for platforms like Vercel. |
| **Backend** | Python 3.11, FastAPI, Uvicorn | Handles file uploads, asynchronous AI API calls, and orchestrates the LaTeX compilation process. |
| **AI / NLP** | Groq API (Llama 3 / Mixtral) | Powers the extraction and intelligent tailoring of the resume content. |
| **Document Engine** | pdflatex, Jinja2 Templating | Merges the JSON data with `.tex` files to compile the final PDF. |
| **Infrastructure** | Docker (Debian slim + TeX Live) | Ensures consistent environments and handles heavy LaTeX dependencies automatically. |

---

## 4. System Workflow (Under the Hood)

> [!TIP]
> Understanding the internal workflow helps in debugging and contributing to the project.

1. **Upload & Parse (`/parse`)**: 
   - User uploads a PDF. 
   - `pdfplumber` extracts raw text.
   - The backend prompts Groq to structure the text into a predefined JSON schema.
2. **Review & Confirm**: 
   - The frontend renders the extracted JSON in a grid.
   - The user can download the raw JSON for their records and clicks "Confirm" to proceed.
3. **Enhancement (`/generate`)**: 
   - The user selects a template and provides the target JD.
   - The backend sends the structured JSON and the JD to Groq with strict instructions to rewrite and align the content.
4. **Compilation**: 
   - The tailored JSON object is passed to a Jinja2 template.
   - The server invokes `pdflatex` to compile the `.tex` file into a binary PDF.
5. **Delivery**: 
   - The final PDF is streamed back to the user for immediate download.

---

## 5. Deployment and Setup Guide

> [!IMPORTANT]
> You must have a valid **Groq API Key** to run this application locally.

### Local Development (Docker Recommended)
Using Docker is the easiest way to run the project as it packages the heavy TeX Live dependencies required for PDF generation.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hemanth12342/template-4-resume.git
   cd template-4-resume
   ```

2. **Configure Environment:**
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. **Run via Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   The application will be accessible at `http://localhost:10000`.

### Native Setup (Without Docker)
If you prefer running natively, you must ensure `pdflatex` is installed on your system (e.g., via MacTeX on macOS or TeX Live on Linux).

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
uvicorn main:app --host 0.0.0.0 --port 10000
```

---

## 6. End-User Manual

For job seekers using the platform:

1. **Upload Baseline Resume:** Drag and drop your existing resume into the upload zone.
2. **Verify Extraction:** Wait for the AI to parse your document. Review the extracted fields in the preview card to ensure accuracy.
3. **Select Layout:** Pick a template that best fits your industry (e.g., Developer, Modern, Data Science).
4. **Provide Context:** Confirm generation, then paste the full Job Description you are applying for. The more detailed the JD, the better the tailoring.
5. **Generate:** Click **"Generate My Resume"**. Within 20-30 seconds, your brand new, tailored PDF will begin downloading automatically.

---
*Document generated for the AI Resume Builder project.*

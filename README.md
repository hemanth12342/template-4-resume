<div align="center">
  <h1>✨ AI Resume Builder</h1>
  <p><strong>An intelligent, automated resume tailoring platform powered by Groq LLMs and LaTeX.</strong></p>
</div>

## 📖 Overview

The **AI Resume Builder** is a powerful platform designed to help job seekers instantly tailor their resumes to specific job descriptions. Instead of manually editing your resume for every application, you simply upload your base resume and provide the Job Description (JD). 

The platform utilizes advanced Large Language Models (LLMs) via the Groq API to intelligently extract your professional data, enhance it to match the JD's keywords and requirements, and automatically compile it into a beautifully formatted, ATS-friendly PDF using LaTeX.

---

## 🚀 Features

- **Intelligent Data Extraction:** Upload your resume (PDF or TXT) and instantly see your extracted professional profile via our interactive Data Preview feature.
- **AI-Powered Tailoring:** Uses Groq's blazing-fast LLMs to strategically rewrite bullet points, quantify achievements, and generate a highly targeted profile summary based on the JD.
- **Automated LaTeX Compilation:** No more formatting struggles. The system seamlessly injects your tailored data into professional LaTeX templates.
- **Multiple Premium Templates:** 
  - **Modern CV (T1):** Centered header with social icons, perfect for creative or academic roles.
  - **Data Science (T2):** Clean two-column layout tailored for ML/Data professionals.
  - **Developer (T3):** Highly compact, ATS-friendly layout favored by tech professionals (FAANG Path).
- **Interactive Workflow:** Review and download your extracted JSON data *before* generating the final PDF to ensure absolute accuracy.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (Vercel-ready) |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI / NLP** | Groq API (Llama 3 70B/8B / Mixtral) |
| **Document Generation** | pdflatex, Jinja2 Templating |
| **Deployment & Ops** | Docker (Debian slim + TeX Live) |

---

## 🔄 Project Workflow (Under the Hood)

1. **Upload & Parse:** The user uploads a PDF. The backend uses `pdfplumber` to extract raw text and sends it to Groq to extract structured JSON (skills, experience, education, etc.) via the `/parse` endpoint.
2. **Review & Confirm:** The frontend displays the extracted data in a clean grid. The user can download this JSON or proceed to the next step by confirming.
3. **Enhancement:** The user selects a template and pastes a target Job Description. The backend prompts the AI to rewrite and align the extracted JSON data with the JD's requirements, ensuring strong action verbs and matched keywords.
4. **Compilation:** The tailored JSON is passed into a Jinja2 template corresponding to the user's chosen design. `pdflatex` compiles the `.tex` file into a beautiful PDF.
5. **Delivery:** The final, customized PDF is streamed back to the user's browser for immediate download.

---

## 💻 Local Development & Setup

### Prerequisites
- Docker & Docker Compose **(Recommended)**
- *OR* Python 3.11+ and MacTeX / TeX Live installed natively

### 1. Clone the Repository
```bash
git clone https://github.com/hemanth12342/template-4-resume.git
cd template-4-resume
```

### 2. Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# ============================================================
#  AI Resume Builder — Environment Variables
#  Get your FREE Groq API key at: https://console.groq.com/keys
# ============================================================

GROQ_API_KEY=your_groq_api_key_here
```

> **🔑 Get Your Groq API Key:**
> 1. Visit [https://console.groq.com/keys](https://console.groq.com/keys)
> 2. Sign up / Log in (it's **free**)
> 3. Click **"Create API Key"**
> 4. Copy and paste it as the value of `GROQ_API_KEY` in your `.env` file

> ⚠️ **Security Note:** The `.env` file is listed in `.gitignore` and will **never** be committed to the repository. Never share or expose your API key publicly.

### 3. Run the Application

#### Option A: Using Docker (Recommended)
This handles all TeX Live dependencies automatically.
```bash
docker-compose up --build
```
Access the application at `http://localhost:10000`.

#### Option B: Running Locally (Native)
Ensure `pdflatex` is available in your PATH before starting.
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 10000
```

---

## 📘 Usage Guide

1. **Open the Web App:** Navigate to the hosted URL or `http://localhost:10000`.
2. **Upload Resume:** Drag and drop your current resume (PDF/TXT) into the upload zone.
3. **Review Data:** Wait a few seconds for the AI to extract your data. Review the extracted fields in the preview card.
4. **Select Template:** Choose your preferred layout (e.g., Developer, Modern, Data Science).
5. **Paste JD:** Click **"Yes, Generate My Resume"**, then paste the full Job Description into the text area.
6. **Generate:** Click **"Generate My Resume"** at the bottom. The AI will tailor your content and the system will deliver your customized PDF in roughly 20-30 seconds!

---

<div align="center">
  <p>Built with ❤️ for job seekers everywhere.</p>
</div>

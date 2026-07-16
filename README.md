# AI Resume Builder

An AI-powered tool that automatically tailors your resume to a specific Job Description (JD). It extracts your base resume using OCR, uses LLMs (via Groq API) to rewrite and optimize your bullet points and profile summary for the JD, and generates a professionally formatted PDF using LaTeX.

## Features
- **PDF Upload**: Upload your existing resume (PDF or TXT).
- **AI Enhancement**: Uses Groq (Llama 3 70B/8B or Mixtral) to rewrite and highlight relevant experience to match the given Job Description.
- **LaTeX Compilation**: Automatically compiles the generated JSON into a polished LaTeX PDF.
- **Multiple Templates**: Choose from 3 professional layouts:
  1. **Minimalist**: Clean, single-column design.
  2. **Data Science**: Two-column layout with skills tables.
  3. **Developer (FAANG Path)**: Classic ATS-friendly compact layout.

## Tech Stack
- **Backend**: FastAPI, Python 3.11
- **AI / LLM**: Groq API
- **PDF Generation**: pdflatex (Jinja2 for templating)
- **Frontend**: Vanilla HTML / JS / CSS
- **Containerization**: Docker (Debian slim + TeX Live)

## Local Development

### Prerequisites
- Docker & Docker Compose OR
- Python 3.11+ and MacTeX / TeX Live installed locally

### Setup
1. Clone the repository.
2. Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

### Running with Docker (Recommended)
```bash
docker-compose up --build
```
Access the application at `http://localhost:10000`.

### Running Locally (without Docker)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure `pdflatex` is available in your PATH.
3. Start the FastAPI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 10000
   ```

## Usage
1. Go to the web interface.
2. Upload your current resume PDF.
3. Select your desired LaTeX template.
4. Paste the target Job Description.
5. Click **Generate Tailored Resume** and download your new PDF!

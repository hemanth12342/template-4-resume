# ============================================================
#  AI Resume Builder — Dockerfile
#  Builds a Python + LaTeX image suitable for Render.com
# ============================================================

FROM python:3.11-slim

# ── System dependencies ────────────────────────────────────
# texlive-latex-base     : core pdflatex engine
# texlive-latex-extra    : fancyhdr, titlesec, enumitem,
#                          hyperref, fullpage, latexsym
# texlive-fonts-recommended: standard fonts (lm, etc.)
# Add texlive-fonts-extra if you need marvosym / extra symbol fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── App setup ──────────────────────────────────────────────
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Render injects $PORT; fall back to 8000 for local Docker runs
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

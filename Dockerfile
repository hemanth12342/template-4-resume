FROM python:3.11-slim

# ── LaTeX packages ─────────────────────────────────────────────────────────────
# texlive-latex-base      : core pdflatex engine
# texlive-latex-extra     : fancyhdr, titlesec, enumitem, hyperref, fullpage
# texlive-fonts-recommended : standard fonts (lm, etc.)
# texlive-fonts-extra     : fontawesome5 icons  ← required by Template 1
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

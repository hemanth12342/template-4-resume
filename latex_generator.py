"""
latex_generator.py — PDF generation via LaTeX Template 4
=========================================================
Template 4 original author : Anubhav Singh (github.com/xprilion) — MIT Licence

This module:
  1.  Escapes LaTeX special characters in all resume data (URL fields are kept verbatim).
  2.  Renders Template 4 using Jinja2 with LaTeX-safe delimiters:
        Variables  →  << var >>
        Blocks     →  <% tag %>
        Comments   →  <# comment #>
  3.  Compiles the resulting .tex file twice with pdflatex and returns the PDF bytes.
"""

import os
import re
import shutil
import subprocess
import tempfile

from jinja2 import BaseLoader, Environment

# ── Constants ─────────────────────────────────────────────────────────────────

# These fields hold raw URLs / identifiers — do NOT LaTeX-escape them.
# They will be placed inside \href{...}{...} URL arguments.
_URL_FIELDS = {"email", "portfolio_url", "linkedin", "github"}


# ── LaTeX escaping ────────────────────────────────────────────────────────────

# Build a single regex that matches any LaTeX special character.
# Using re.sub with a single pass avoids double-escaping (e.g. \ → \textbackslash{},
# and then the { } in that replacement string are NOT re-scanned).
_SPECIAL = {
    "\\": r"\textbackslash{}",
    "&":  r"\&",
    "%":  r"\%",
    "$":  r"\$",
    "#":  r"\#",
    "_":  r"\_",
    "{":  r"\{",
    "}":  r"\}",
    "~":  r"\textasciitilde{}",
    "^":  r"\textasciicircum{}",
}
_ESCAPE_RE = re.compile("|".join(re.escape(c) for c in _SPECIAL))


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in a plain-text string."""
    if not isinstance(text, str):
        text = str(text)
    return _ESCAPE_RE.sub(lambda m: _SPECIAL[m.group()], text)


def _escape_data(obj: object, _key: str = "") -> object:
    """
    Recursively escape LaTeX special characters in every string value of a
    dict / list.  Fields listed in _URL_FIELDS are left verbatim so they can
    be safely embedded in \\href{URL}{...} arguments.
    """
    if isinstance(obj, dict):
        return {k: _escape_data(v, _key=k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_escape_data(item, _key=_key) for item in obj]
    if isinstance(obj, str):
        return obj if _key in _URL_FIELDS else escape_latex(obj)
    return obj


# ── Jinja2 environment ────────────────────────────────────────────────────────

def _make_jinja_env() -> Environment:
    """
    Build a Jinja2 Environment whose delimiters do not collide with LaTeX syntax.

    Standard {{ / }} would conflict with LaTeX braces.
    We use:  <<var>>  <%block%>  <#comment#>

    trim_blocks + lstrip_blocks ensure that <% ... %> control tags on their own
    line produce no stray blank lines in the rendered LaTeX output.
    """
    env = Environment(
        loader=BaseLoader(),
        block_start_string="<%",
        block_end_string="%>",
        variable_start_string="<<",
        variable_end_string=">>",
        comment_start_string="<#",
        comment_end_string="#>",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
        keep_trailing_newline=True,
    )
    # Register the escape function as a Jinja2 filter so the template can
    # apply it to URL fields in display-text positions:  << d.email | le >>
    env.filters["le"] = escape_latex
    # Helper: strip https:// / http:// for cleaner display text
    env.filters["clean_url"] = lambda u: re.sub(r"^https?://", "", u).rstrip("/")
    return env


# ── Template 4 (Jinja2 version) ───────────────────────────────────────────────
#
# Jinja2 tags are processed by Python BEFORE the file is written to disk,
# so LaTeX never sees <% %> or << >>. The % in <% %> is therefore not
# interpreted as a LaTeX comment character.
#
# Differences from the vanilla template:
#   • marvosym removed  (not used; avoids the texlive-fonts-extra dependency)
#   • resumeItemWithoutTitle fixed to actually print its argument
#   • Profile Summary section added above Education
#   • All dummy data replaced with Jinja2 variables

_TEMPLATE_4 = r"""
%------------------------
% Resume Template
% Original Author : Anubhav Singh (github.com/xprilion)
% Adapted by AI Resume Builder — Jinja2 variables injected at render time
% License : MIT
%------------------------

\documentclass[a4paper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[pdftex]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.530in}
\addtolength{\evensidemargin}{-0.375in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.45in}
\addtolength{\textheight}{1in}

\urlstyle{rm}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Section formatting
\titleformat{\section}{
  \vspace{-10pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-6pt}]

%-------------------------
% Custom commands

% Two-arg item: bold title + description (used for skills and projects)
\newcommand{\resumeItem}[2]{
  \item\small{
    \textbf{#1}{: #2 \vspace{-2pt}}
  }
}

% One-arg item: plain bullet (used for experience bullets)
\newcommand{\resumeItemNoBold}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{#3} & \textit{#4} \\
    \end{tabular*}\vspace{-5pt}
}

\newcommand{\resumeSubItem}[2]{\resumeItem{#1}{#2}\vspace{-3pt}}

\renewcommand{\labelitemii}{$\circ$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-----------------------------
%%%%%%  CV STARTS HERE  %%%%%%

\begin{document}

%----------HEADING-----------------
\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
  \textbf{{\LARGE <<d.name>>}} & Email: \href{mailto:<<d.email>>}{<<d.email | le>>}\\
<% if d.portfolio_url %>
  \href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>} & Mobile:~~~<<d.phone>> \\
<% else %>
   & Mobile:~~~<<d.phone>> \\
<% endif %>
<% if d.github %>
  \href{https://github.com/<<d.github>>}{Github:~~github.com/<<d.github | le>>} \\
<% endif %>
\end{tabular*}

%----------PROFILE SUMMARY-----------------
<% if d.summary %>
\section{Profile Summary}
<<d.summary>>
<% endif %>

%-----------EDUCATION-----------------
<% if d.education %>
\section{Education}
  \resumeSubHeadingListStart
<% for edu in d.education %>
    \resumeSubheading
      {<<edu.degree>>}{<<edu.institution>>}
      {<<edu.field>><% if edu.gpa %>; GPA: <<edu.gpa>><% endif %>}{<<edu.dates>>}
<% if edu.courses %>
      {\scriptsize \textit{\footnotesize{\newline{}\textbf{Courses:} <<edu.courses>>}}}
<% endif %>
<% endfor %>
  \resumeSubHeadingListEnd
<% endif %>

%-----------SKILLS-----------------
<% if d.skills %>
\vspace{-5pt}
\section{Skills Summary}
\resumeSubHeadingListStart
<% for skill in d.skills %>
\resumeSubItem{<<skill.category>>}{~~~~~~<<skill.items>>}
<% endfor %>
\resumeSubHeadingListEnd
<% endif %>

%-----------EXPERIENCE-----------------
<% if d.experience %>
\vspace{-5pt}
\section{Experience}
  \resumeSubHeadingListStart
<% for exp in d.experience %>
    \resumeSubheading{<<exp.role>>}{<<exp.location>>}
    {<<exp.company>>}{<<exp.dates>>}
    \resumeItemListStart
<% for bullet in exp.bullets %>
        \resumeItemNoBold{<<bullet>>}
<% endfor %>
    \resumeItemListEnd
    \vspace{-5pt}
<% endfor %>
  \resumeSubHeadingListEnd
<% endif %>

%-----------PROJECTS-----------------
<% if d.projects %>
\vspace{-5pt}
\section{Projects}
\resumeSubHeadingListStart
<% for project in d.projects %>
\resumeSubItem{<<project.title>> (<<project.technologies>>)}{<<project.description>>}
\vspace{2pt}
<% endfor %>
\resumeSubHeadingListEnd
<% endif %>

%-----------AWARDS-----------------
<% if d.awards %>
\vspace{-5pt}
\section{Honors and Awards}
\begin{description}[font=$\bullet$]
<% for award in d.awards %>
\item {<<award>>}
\vspace{-5pt}
<% endfor %>
\end{description}
<% endif %>

%-----------VOLUNTEER-----------------
<% if d.volunteer %>
\vspace{-5pt}
\section{Volunteer Experience}
  \resumeSubHeadingListStart
<% for vol in d.volunteer %>
    \resumeSubheading
      {<<vol.role>>}{<<vol.location>>}
      {<<vol.organization>>}{<<vol.dates>>}
<% endfor %>
  \resumeSubHeadingListEnd
<% endif %>

\end{document}
"""


# ── Data normalisation ────────────────────────────────────────────────────────

def _normalize(data: dict) -> dict:
    """Ensure every expected key exists, using safe defaults for missing ones."""
    defaults: dict = {
        "name":          "Your Name",
        "email":         "",
        "phone":         "",
        "portfolio_url": "",
        "github":        "",
        "linkedin":      "",
        "summary":       "",
        "education":     [],
        "skills":        [],
        "experience":    [],
        "projects":      [],
        "awards":        [],
        "volunteer":     [],
    }
    for key, default in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default

    # Ensure nested list items also have required sub-keys
    for edu in data.get("education", []):
        edu.setdefault("gpa",     "")
        edu.setdefault("courses", "")

    for exp in data.get("experience", []):
        exp.setdefault("bullets", [])

    for vol in data.get("volunteer", []):
        vol.setdefault("organization", vol.get("role", ""))

    return data


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pdf(raw_data: dict) -> bytes:
    """
    Build a PDF resume from structured resume data using LaTeX Template 4.

    Steps
    -----
    1. Normalise missing keys.
    2. Escape LaTeX special characters (URL fields are left verbatim).
    3. Render the Jinja2 template → LaTeX source.
    4. Write the .tex file to a temp directory.
    5. Run pdflatex twice (double pass ensures stable layout).
    6. Read and return the PDF bytes.

    Raises
    ------
    RuntimeError  if pdflatex is not installed or compilation fails.
    """
    # Guard: pdflatex must be on PATH
    if shutil.which("pdflatex") is None:
        raise RuntimeError(
            "pdflatex not found on PATH.\n"
            "  macOS : brew install --cask mactex   (full)  OR\n"
            "          brew install --cask basictex  (minimal, then tlmgr install missing packages)\n"
            "  Linux : sudo apt install texlive-latex-extra texlive-fonts-recommended\n"
            "  Docker: see Dockerfile — texlive packages are installed during build."
        )

    # 1. Normalise + 2. Escape
    data    = _normalize(dict(raw_data))      # copy so we don't mutate caller's dict
    escaped = _escape_data(data)

    # 3. Render
    env      = _make_jinja_env()
    latex_src = env.from_string(_TEMPLATE_4).render(d=escaped)

    # 4-6. Compile
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")
        log_path = os.path.join(tmpdir, "resume.log")

        with open(tex_path, "w", encoding="utf-8") as fh:
            fh.write(latex_src)

        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory", tmpdir,
            tex_path,
        ]

        result = None
        for _ in range(2):       # two passes for stable layout / cross-references
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

        if not os.path.exists(pdf_path):
            # Extract the most useful part of the LaTeX log for diagnosis
            log_tail = ""
            if os.path.exists(log_path):
                with open(log_path, encoding="utf-8", errors="ignore") as lf:
                    full_log = lf.read()
                # Find the first error line
                error_lines = [ln for ln in full_log.splitlines() if ln.startswith("!")]
                log_tail = "\n".join(error_lines[:10]) or full_log[-2000:]

            raise RuntimeError(
                f"pdflatex failed (exit code {result.returncode}).\n"
                f"LaTeX errors:\n{log_tail}"
            )

        with open(pdf_path, "rb") as fh:
            return fh.read()

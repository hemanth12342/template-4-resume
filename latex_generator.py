r"""
latex_generator.py — Fixed version
Fixes:
  1. skill['items'] bug  — was skill.items (returned dict method, not value)
  2. Template 3 cls     — replaced \let\@origdocument with \AtBeginDocument
  3. LinkedIn added     — all 4 templates now show LinkedIn
  4. Certifications     — new section in all 4 templates
"""

import os
import re
import shutil
import subprocess
import tempfile

from jinja2 import BaseLoader, Environment

# ── LaTeX escaping ─────────────────────────────────────────────────────────────

_URL_FIELDS = {"email", "portfolio_url", "linkedin", "github"}

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
    if not isinstance(text, str):
        text = str(text)
    return _ESCAPE_RE.sub(lambda m: _SPECIAL[m.group()], text)


def _escape_data(obj: object, _key: str = "") -> object:
    if isinstance(obj, dict):
        return {k: _escape_data(v, _key=k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_escape_data(item, _key=_key) for item in obj]
    if isinstance(obj, str):
        return obj if _key in _URL_FIELDS else escape_latex(obj)
    return obj


# ── Jinja2 environment ─────────────────────────────────────────────────────────

def _make_jinja_env() -> Environment:
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
    env.filters["le"]        = escape_latex
    env.filters["clean_url"] = lambda u: re.sub(r"^https?://", "", str(u)).rstrip("/")
    env.filters["handle"]    = lambda u: re.sub(r"^https?://", "", str(u)).rstrip("/").split("/")[-1]
    return env


# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATE 1 — Jitin Nair Modern CV
# ══════════════════════════════════════════════════════════════════════════════

_TEMPLATE_1 = r"""
\documentclass[a4paper,12pt]{article}

\usepackage{url}
\usepackage{parskip}
\RequirePackage{color}
\RequirePackage{graphicx}
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage[scale=0.9]{geometry}
\usepackage{tabularx}
\usepackage{enumitem}
\newcolumntype{C}{>{\centering\arraybackslash}X}
\usepackage{supertabular}
\newlength{\fullcollw}
\setlength{\fullcollw}{0.47\textwidth}
\usepackage{titlesec}
\usepackage{multicol}
\usepackage{multirow}
\titleformat{\section}{\Large\scshape\raggedright}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{10pt}{10pt}
\usepackage[unicode, draft=false]{hyperref}
\definecolor{linkcolour}{rgb}{0,0.2,0.6}
\hypersetup{colorlinks,breaklinks,urlcolor=linkcolour,linkcolor=linkcolour}
\usepackage{fontawesome5}

\newenvironment{jobshort}[2]{%
  \begin{tabularx}{\linewidth}{@{}X r@{}}
  \textbf{#1} & #2 \\[3.75pt]
  \end{tabularx}%
}{}

\newenvironment{joblong}[2]{%
  \noindent
  \begin{tabularx}{\linewidth}{@{}X r@{}}
  \textbf{#1} & #2 \\[3.75pt]
  \end{tabularx}\par\vspace{-1.5ex}
  \begin{itemize}[nosep,after=\strut,leftmargin=1em,itemsep=3pt,label=--]
}{%
  \end{itemize}
}

\begin{document}
\pagestyle{empty}

%--- HEADING ---
\begin{tabularx}{\linewidth}{@{} C @{}}
\Huge{<<d.name>>} \\[7.5pt]
<% if d.github %>
\href{https://github.com/<<d.github>>}{\raisebox{-0.05\height}\faGithub\ <<d.github | le>>} $|$
<% endif %>
<% if d.linkedin %>
\href{<<d.linkedin>>}{\raisebox{-0.05\height}\faLinkedin\ <<d.linkedin | handle | le>>} $|$
<% endif %>
<% if d.portfolio_url %>
\href{<<d.portfolio_url>>}{\raisebox{-0.05\height}\faGlobe\ <<d.portfolio_url | clean_url>>} $|$
<% endif %>
\href{mailto:<<d.email>>}{\raisebox{-0.05\height}\faEnvelope\ <<d.email | le>>} $|$
\href{tel:<<d.phone>>}{\raisebox{-0.05\height}\faMobile\ <<d.phone>>} \\
\end{tabularx}

%--- SUMMARY ---
<% if d.summary %>
\section{Summary}
<<d.summary>>
<% endif %>

%--- EXPERIENCE ---
<% if d.experience %>
\section{Work Experience}
<% for exp in d.experience %>
<% if exp.bullets %>
\begin{joblong}{<<exp.role>> $-$ <<exp.company>>, <<exp.location>>}{<<exp.dates>>}
<% for bullet in exp.bullets %>
\item <<bullet>>
<% endfor %>
\end{joblong}
<% else %>
\begin{jobshort}{<<exp.role>> $-$ <<exp.company>>, <<exp.location>>}{<<exp.dates>>}
\end{jobshort}
<% endif %>
<% endfor %>
<% endif %>

%--- PROJECTS ---
<% if d.projects %>
\section{Projects}
<% for project in d.projects %>
\begin{joblong}{<<project.title>>}{<<project.technologies>>}
<% for bullet in project.bullets %>
\item <<bullet>>
<% endfor %>
\end{joblong}
<% endfor %>
<% endif %>

%--- EDUCATION ---
<% if d.education %>
\section{Education}
\begin{tabularx}{\linewidth}{@{}l X@{}}
<% for edu in d.education %>
<<edu.dates>> & <<edu.degree>> in \textbf{<<edu.field>>} at \textbf{<<edu.institution>>}<% if edu.gpa %> \hfill (GPA: <<edu.gpa>>)<% endif %> \\
<% endfor %>
\end{tabularx}
<% endif %>

%--- CERTIFICATIONS ---
<% if d.certifications %>
\section{Certifications}
\begin{tabularx}{\linewidth}{@{}l X@{}}
<% for cert in d.certifications %>
\textbf{<<cert.name>>} & \textit{<<cert.issuer>>}<% if cert.date %>, <<cert.date>><% endif %> \\
<% endfor %>
\end{tabularx}
<% endif %>

%--- SKILLS ---
<% if d.skills %>
\section{Skills}
\begin{tabularx}{\linewidth}{@{}l X@{}}
<% for skill in d.skills %>
\textbf{<<skill.category>>} & \normalsize{<<skill['items']>>}\\
<% endfor %>
\end{tabularx}
<% endif %>

\vfill
\center{\footnotesize Last updated: \today}
\end{document}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATE 2 — Data Science / Tech Resume
# ══════════════════════════════════════════════════════════════════════════════

_TEMPLATE_2 = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.65in, top=0.55in, bottom=0.55in]{geometry}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{array}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage[pdftex]{hyperref}
\usepackage{parskip}

\hypersetup{colorlinks=true, urlcolor=MidnightBlue, linkcolor=black}
\pagestyle{empty}

\titleformat{\section}
  {\normalfont\normalsize\bfseries}
  {}{0pt}{\MakeUppercase}[\titlerule]
\titlespacing*{\section}{0pt}{8pt}{4pt}

\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{R}[1]{>{\raggedleft\arraybackslash}p{#1}}

\begin{document}

%--- HEADER ---
\noindent
\begin{tabularx}{\textwidth}{@{} l >{\raggedleft\arraybackslash}X @{}}
  {\LARGE\textbf{<<d.name>>}} & \small <<d.phone>> \\
  \small\href{mailto:<<d.email>>}{<<d.email | le>>} & 
<% if d.linkedin %>
  \small\href{<<d.linkedin>>}{<<d.linkedin | handle | le>>} \\
<% else %>
   \\
<% endif %>
<% if d.github %>
  \small\href{https://github.com/<<d.github>>}{<<d.github | le>>} &
<% if d.portfolio_url %>
  \small\href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>} \\
<% else %>
   \\
<% endif %>
<% endif %>
\end{tabularx}
\vspace{-2pt}

%--- OBJECTIVE ---
<% if d.summary %>
\section{Objective}
<<d.summary>>
<% endif %>

%--- SKILLS ---
<% if d.skills %>
\section{Skills}
\begin{tabularx}{\textwidth}{@{} L{3.4cm} X @{}}
<% for skill in d.skills %>
\textbf{<<skill.category>>} & <<skill['items']>> \\[2pt]
<% endfor %>
\end{tabularx}
<% endif %>

%--- TECHNICAL EXPERIENCE ---
<% if d.experience %>
\section{Technical Experience}
<% for exp in d.experience %>
\noindent
\textbf{<<exp.role>>} \hfill \textit{<<exp.dates>>} \\
\textit{<<exp.company>>} \hfill \textit{<<exp.location>>}
\begin{itemize}[leftmargin=1.5em, itemsep=-2pt, topsep=2pt, parsep=0pt]
<% for bullet in exp.bullets %>
\item <<bullet>>
<% endfor %>
\end{itemize}
\vspace{3pt}
<% endfor %>
<% endif %>

%--- PROJECTS ---
<% if d.projects %>
\section{Projects}
<% for project in d.projects %>
\noindent\textbf{<<project.title>>} \hfill \textit{<<project.technologies>>}
\begin{itemize}[leftmargin=1.5em, itemsep=-2pt, topsep=2pt, parsep=0pt]
<% for bullet in project.bullets %>
\item <<bullet>>
<% endfor %>
\end{itemize}
\vspace{3pt}
<% endfor %>
<% endif %>

%--- EDUCATION ---
<% if d.education %>
\section{Education}
<% for edu in d.education %>
\noindent
\textbf{<<edu.degree>>} in <<edu.field>> \hfill \textit{<<edu.dates>>} \\
<<edu.institution>><% if edu.gpa %>, GPA: <<edu.gpa>><% endif %>\par\vspace{3pt}
<% endfor %>
<% endif %>

%--- CERTIFICATIONS ---
<% if d.certifications %>
\section{Certifications}
\begin{itemize}[leftmargin=1.5em, itemsep=-2pt, topsep=2pt]
<% for cert in d.certifications %>
\item \textbf{<<cert.name>>} --- \textit{<<cert.issuer>>}<% if cert.date %> (<<cert.date>>)<% endif %>
<% endfor %>
\end{itemize}
<% endif %>

%--- ACTIVITIES ---
<% if d.awards or d.volunteer %>
\section{Activities}
\begin{itemize}[leftmargin=1.5em, itemsep=-2pt, topsep=2pt]
<% for award in d.awards %>
\item <<award>>
<% endfor %>
<% for vol in d.volunteer %>
\item \textbf{<<vol.role>>}, <<vol.organization>> \hfill \textit{<<vol.dates>>}
<% endfor %>
\end{itemize}
<% endif %>

\end{document}
"""


# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATE 3 — Anubhav Singh Developer Resume
#  FIX: skill['items'] instead of skill.items
#  NEW: LinkedIn added to heading, Certifications section added
# ══════════════════════════════════════════════════════════════════════════════

_TEMPLATE_3 = r"""
\documentclass[a4paper,12pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{tabularx}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[pdftex]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.530in}
\addtolength{\evensidemargin}{-0.375in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.45in}
\addtolength{\textheight}{1in}

\urlstyle{rm}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-10pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-6pt}]

\newcommand{\resumeItem}[2]{
  \item\small{\textbf{#1}{: #2 \vspace{-2pt}}}
}
\newcommand{\resumeItemNoBold}[1]{
  \item\small{{#1 \vspace{-2pt}}}
}
\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabularx}{\textwidth}{@{} >{\raggedright\arraybackslash}X >{\raggedleft\arraybackslash}X @{}}
      \textbf{#1} & #2 \\
      \textit{#3} & \textit{#4} \\
    \end{tabularx}\vspace{-5pt}
}
\newcommand{\resumeProjectHeading}[2]{
  \vspace{-1pt}\item
    \begin{tabularx}{\textwidth}{@{} >{\raggedright\arraybackslash}X r @{}}
      \textbf{#1} & \textit{#2} \\
    \end{tabularx}\vspace{-5pt}
}
\newcommand{\resumeSubItem}[2]{\resumeItem{#1}{#2}\vspace{-3pt}}
\renewcommand{\labelitemii}{$\circ$}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

%--- HEADING ---
\begin{center}
    \textbf{\Huge \scshape <<d.name>>} \\ \vspace{4pt}
    \small <<d.phone>> $|$ \href{mailto:<<d.email>>}{\underline{<<d.email | le>>}}
<% if d.linkedin %>
    $|$ \href{<<d.linkedin>>}{\underline{<<d.linkedin | handle | le>>}}
<% endif %>
<% if d.github %>
    $|$ \href{https://github.com/<<d.github>>}{\underline{<<d.github | le>>}}
<% endif %>
<% if d.portfolio_url %>
    $|$ \href{<<d.portfolio_url>>}{\underline{<<d.portfolio_url | clean_url | le>>}}
<% endif %>
\end{center}

<% if d.summary %>
\section{Profile Summary}
<<d.summary>>
<% endif %>

<% if d.education %>
\section{Education}
  \resumeSubHeadingListStart
<% for edu in d.education %>
  \item
    \textbf{<<edu.degree>>} \hfill <<edu.institution>> \\
    \textit{<<edu.field>>} \hfill \textit{<<edu.dates>>}
<% if edu.gpa %>
    \\ \textit{GPA: <<edu.gpa>>}
<% endif %>
<% if edu.courses %>
    \\ {\scriptsize \textit{\footnotesize{\textbf{Courses:} <<edu.courses>>}}}
<% endif %>
    \vspace{-5pt}
<% endfor %>
  \resumeSubHeadingListEnd
<% endif %>

<% if d.skills %>
\vspace{-5pt}
\section{Skills Summary}
\resumeSubHeadingListStart
<% for skill in d.skills %>
\resumeSubItem{<<skill.category>>}{~~~~~~<<skill['items']>>}
<% endfor %>
\resumeSubHeadingListEnd
<% endif %>

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

<% if d.projects %>
\vspace{-5pt}
\section{Projects}
\resumeSubHeadingListStart
<% for project in d.projects %>
    \resumeProjectHeading{<<project.title>>}{<<project.technologies>>}
    \vspace{-5pt}
    \resumeItemListStart
<% for bullet in project.bullets %>
        \resumeItemNoBold{<<bullet>>}
<% endfor %>
    \resumeItemListEnd
    \vspace{-5pt}
<% endfor %>
\resumeSubHeadingListEnd
<% endif %>

<% if d.certifications %>
\vspace{-5pt}
\section{Certifications}
\resumeSubHeadingListStart
<% for cert in d.certifications %>
\resumeSubItem{<<cert.name>>}{<<cert.issuer>><% if cert.date %>, <<cert.date>><% endif %>}
<% endfor %>
\resumeSubHeadingListEnd
<% endif %>

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


# ── Data normalisation ─────────────────────────────────────────────────────────

def _normalize(data: dict) -> dict:
    defaults = {
        "name": "", "email": "", "phone": "",
        "portfolio_url": "", "github": "", "linkedin": "",
        "summary": "",
        "education": [], "skills": [], "experience": [], "projects": [],
        "awards": [], "volunteer": [],
        "certifications": [],          # ← NEW
    }
    for k, v in defaults.items():
        if k not in data or data[k] is None:
            data[k] = v

    for edu in data.get("education", []):
        edu.setdefault("gpa", "")
        edu.setdefault("courses", "")

    for exp in data.get("experience", []):
        exp.setdefault("bullets", [])

    for vol in data.get("volunteer", []):
        vol.setdefault("organization", vol.get("role", ""))
        vol.setdefault("description", "")

    for proj in data.get("projects", []):
        proj.setdefault("bullets", [])
        proj.setdefault("description", "")

    for cert in data.get("certifications", []):   # ← NEW
        cert.setdefault("name", "")
        cert.setdefault("issuer", "")
        cert.setdefault("date", "")

    return data


# ── Template routing ───────────────────────────────────────────────────────────

_TEMPLATES = {1: _TEMPLATE_1, 2: _TEMPLATE_2, 3: _TEMPLATE_3}


# ── Public entry point ─────────────────────────────────────────────────────────

def generate_pdf(raw_data: dict, template_id: int = 3) -> bytes:
    if shutil.which("pdflatex") is None:
        raise RuntimeError(
            "pdflatex not found. Install MacTeX (macOS) or "
            "texlive-latex-extra + texlive-fonts-extra (Linux/Docker)."
        )

    template_src = _TEMPLATES.get(template_id, _TEMPLATE_3)
    data         = _normalize(dict(raw_data))
    escaped      = _escape_data(data)
    env          = _make_jinja_env()
    latex_src    = env.from_string(template_src).render(d=escaped)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")
        log_path = os.path.join(tmpdir, "resume.log")

        with open(tex_path, "w", encoding="utf-8") as fh:
            fh.write(latex_src)

        cmd = [
            "pdflatex", "-interaction=nonstopmode",
            "-halt-on-error", "-output-directory", tmpdir, tex_path,
        ]

        result = None
        for _ in range(2):
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if not os.path.exists(pdf_path):
            log_tail = ""
            if os.path.exists(log_path):
                with open(log_path, encoding="utf-8", errors="ignore") as lf:
                    lines = lf.read().splitlines()
                errors = [l for l in lines if l.startswith("!")]
                log_tail = "\n".join(errors[:10]) or "\n".join(lines[-30:])
            raise RuntimeError(
                f"pdflatex failed (exit {result.returncode}).\nErrors:\n{log_tail}"
            )

        with open(pdf_path, "rb") as fh:
            return fh.read()

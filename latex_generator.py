"""
latex_generator.py — PDF generation via 4 LaTeX Templates
==========================================================
Supports 4 distinct resume templates selectable by template_id (1–4).

Templates:
  1 — Classic   : Clean two-column header, ruled sections (Jitin Nair style)
  2 — Modern    : Colored section titles, elegant spacing
  3 — Sidebar   : Two-column header + single-column body
  4 — ATS       : Original template (Anubhav Singh style)

All templates have a page border on every page.
Multi-page resumes are fully supported.

Public API:
  generate_pdf(raw_data, template_id=4)  → bytes
  generate_all_pdfs(raw_data)            → {1: bytes, 2: bytes, 3: bytes, 4: bytes}
"""

import os
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

from jinja2 import BaseLoader, Environment

# ── Constants ─────────────────────────────────────────────────────────────────

_URL_FIELDS = {"email", "portfolio_url", "linkedin", "github"}

# ── LaTeX escaping ────────────────────────────────────────────────────────────

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
    """Recursively escape LaTeX special characters; URL fields are kept verbatim."""
    if isinstance(obj, dict):
        return {k: _escape_data(v, _key=k) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_escape_data(item, _key=_key) for item in obj]
    if isinstance(obj, str):
        return obj if _key in _URL_FIELDS else escape_latex(obj)
    return obj


# ── Jinja2 environment ────────────────────────────────────────────────────────

def _make_jinja_env() -> Environment:
    """Jinja2 env with LaTeX-safe delimiters: <<var>>  <%block%>  <#comment#>"""
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
    env.filters["le"] = escape_latex
    env.filters["clean_url"] = lambda u: re.sub(r"^https?://", "", u).rstrip("/")
    return env


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 1 — Classic (Jitin Nair style)
#  Clean article with two-column header and ruled sections
#  Packages: only texlive-latex-base + texlive-latex-extra (no lmodern)
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_1 = r"""
%------------------------
% Resume Template 1 — Classic
% Style: Jitin Nair inspired, clean article layout
%------------------------

\documentclass[a4paper,11pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[left=0.9in,right=0.9in,top=0.85in,bottom=0.75in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{array}
\usepackage{tikz}
\usetikzlibrary{calc}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

% Section style: large, bold, small-caps with a rule underneath
\titleformat{\section}{\large\bfseries\scshape\raggedright}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{10pt}{5pt}

% Page border on every page
\AddToHook{shipout/background}{%
  \begin{tikzpicture}[overlay,remember picture]%
    \draw[line width=1.2pt,gray!55,rounded corners=3pt]%
      ($(current page.north west)+(0.45cm,-0.45cm)$) rectangle%
      ($(current page.south east)+(-0.45cm,0.45cm)$);%
  \end{tikzpicture}%
}

%==============================================================
\begin{document}
%==============================================================

%-------- HEADER --------
\begin{tabularx}{\textwidth}{@{}X r@{}}
  {\Huge\bfseries <<d.name>>} &
  \begin{tabular}[b]{@{}r@{}}
    \small\href{mailto:<<d.email>>}{<<d.email | le>>} \\
    \small <<d.phone>>
<% if d.linkedin %>
    \\ \small\href{<<d.linkedin>>}{<<d.linkedin | clean_url | le>>}
<% endif %>
<% if d.github %>
    \\ \small\href{https://github.com/<<d.github>>}{github.com/<<d.github | le>>}
<% endif %>
<% if d.portfolio_url %>
    \\ \small\href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>}
<% endif %>
  \end{tabular}
\end{tabularx}

\vspace{4pt}
\hrule
\vspace{6pt}

%-------- SUMMARY --------
<% if d.summary %>
\section{Professional Summary}
\small <<d.summary>>
<% endif %>

%-------- EXPERIENCE --------
<% if d.experience %>
\section{Experience}
<% for exp in d.experience %>
\noindent
\begin{tabularx}{\textwidth}{@{}X r@{}}
  \textbf{<<exp.role>>} at \textit{<<exp.company>>} & \textit{\small <<exp.dates>>} \\
  \multicolumn{2}{@{}l@{}}{\small\textit{<<exp.location>>}}
\end{tabularx}
\begin{itemize}[noitemsep, topsep=2pt, leftmargin=1.2em]
<% for bullet in exp.bullets %>
  \item \small <<bullet>>
<% endfor %>
\end{itemize}
\vspace{4pt}
<% endfor %>
<% endif %>

%-------- EDUCATION --------
<% if d.education %>
\section{Education}
<% for edu in d.education %>
\noindent
\begin{tabularx}{\textwidth}{@{}X r@{}}
  \textbf{<<edu.institution>>} & \textit{\small <<edu.dates>>} \\
  \small\textit{<<edu.degree>><% if edu.field %>, <<edu.field>><% endif %>} &
  <% if edu.gpa %>\small GPA: <<edu.gpa>><% endif %>
\end{tabularx}
<% if edu.courses %>
\\\small\textit{Relevant Courses: <<edu.courses>>}
<% endif %>
\vspace{4pt}
<% endfor %>
<% endif %>

%-------- SKILLS --------
<% if d.skills %>
\section{Technical Skills}
\begin{tabularx}{\textwidth}{@{} >{\bfseries\small}l X @{}}
<% for skill in d.skills %>
  <<skill.category>> & \small <<skill.items>> \\[2pt]
<% endfor %>
\end{tabularx}
<% endif %>

%-------- PROJECTS --------
<% if d.projects %>
\section{Projects}
<% for project in d.projects %>
\noindent\textbf{<<project.title>>}
<% if project.technologies %>\hfill \small\textit{<<project.technologies>>}<% endif %>\\
\small <<project.description>>
\vspace{4pt}
<% endfor %>
<% endif %>

%-------- AWARDS --------
<% if d.awards %>
\section{Honors \& Awards}
\begin{itemize}[noitemsep, topsep=2pt, leftmargin=1.2em]
<% for award in d.awards %>
  \item \small <<award>>
<% endfor %>
\end{itemize}
<% endif %>

%-------- VOLUNTEER --------
<% if d.volunteer %>
\section{Volunteer Experience}
<% for vol in d.volunteer %>
\noindent\textbf{<<vol.role>>} --- \textit{<<vol.organization>>}
<% if vol.location %>, <<vol.location>><% endif %>
\hfill \textit{\small <<vol.dates>>}
<% if vol.description %>\\{\small <<vol.description>>}<% endif %>
\vspace{4pt}
<% endfor %>
<% endif %>

\end{document}
"""


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 2 — Modern (colored section titles, elegant spacing)
#  Packages: only texlive-latex-base + texlive-latex-extra (no lmodern)
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_2 = r"""
%------------------------
% Resume Template 2 — Modern
% Style: Colored section headings, elegant spacing
%------------------------

\documentclass[a4paper,11pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[left=0.85in,right=0.85in,top=0.85in,bottom=0.75in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{array}
\usepackage{tikz}
\usetikzlibrary{calc}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

% Brand colours
\definecolor{accent}{RGB}{67,56,202}      % indigo-700
\definecolor{accentlight}{RGB}{99,102,241}% indigo-500
\definecolor{mutedgray}{RGB}{107,114,128} % gray-500

% Section headings: bold, accent-colored, with colored rule
\titleformat{\section}[block]
  {\large\bfseries\color{accent}}{}{0em}{}[\color{accentlight}\titlerule]
\titlespacing*{\section}{0pt}{12pt}{6pt}

% Page border on every page
\AddToHook{shipout/background}{%
  \begin{tikzpicture}[overlay,remember picture]%
    \draw[line width=1.2pt,gray!55,rounded corners=3pt]%
      ($(current page.north west)+(0.45cm,-0.45cm)$) rectangle%
      ($(current page.south east)+(-0.45cm,0.45cm)$);%
  \end{tikzpicture}%
}

%==============================================================
\begin{document}
%==============================================================

%-------- HEADER --------
\begin{center}
  {\Huge\bfseries <<d.name>>}\\[6pt]
  {\color{accentlight}\rule{0.4\textwidth}{1.5pt}}\\[6pt]
  \small
  \href{mailto:<<d.email>>}{<<d.email | le>>}
  ~\textbf{\textcolor{mutedgray}{|}}~<<d.phone>>
<% if d.linkedin %>
  ~\textbf{\textcolor{mutedgray}{|}}~\href{<<d.linkedin>>}{<<d.linkedin | clean_url | le>>}
<% endif %>
<% if d.github %>
  ~\textbf{\textcolor{mutedgray}{|}}~\href{https://github.com/<<d.github>>}{github.com/<<d.github | le>>}
<% endif %>
<% if d.portfolio_url %>
  ~\textbf{\textcolor{mutedgray}{|}}~\href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>}
<% endif %>
\end{center}

\vspace{4pt}

%-------- SUMMARY --------
<% if d.summary %>
\section{Professional Summary}
\small <<d.summary>>
<% endif %>

%-------- EXPERIENCE --------
<% if d.experience %>
\section{Experience}
<% for exp in d.experience %>
\noindent
\begin{tabularx}{\textwidth}{@{}X r@{}}
  \textbf{<<exp.role>>}
  \textcolor{mutedgray}{|} \textit{<<exp.company>>}
  \textcolor{mutedgray}{| \small<<exp.location>>}
  & \textcolor{mutedgray}{\small <<exp.dates>>}
\end{tabularx}
\begin{itemize}[noitemsep, topsep=2pt, leftmargin=1.2em]
<% for bullet in exp.bullets %>
  \item \small <<bullet>>
<% endfor %>
\end{itemize}
\vspace{5pt}
<% endfor %>
<% endif %>

%-------- EDUCATION --------
<% if d.education %>
\section{Education}
<% for edu in d.education %>
\noindent
\begin{tabularx}{\textwidth}{@{}X r@{}}
  \textbf{<<edu.institution>>} & \textcolor{mutedgray}{\small <<edu.dates>>} \\
  \small\textit{<<edu.degree>><% if edu.field %> in <<edu.field>><% endif %>}
  <% if edu.gpa %>& \textcolor{mutedgray}{\small GPA: <<edu.gpa>>}<% endif %>
\end{tabularx}
<% if edu.courses %>
\\\small\textcolor{mutedgray}{Courses: <<edu.courses>>}
<% endif %>
\vspace{5pt}
<% endfor %>
<% endif %>

%-------- SKILLS --------
<% if d.skills %>
\section{Skills}
\begin{tabularx}{\textwidth}{@{} >{\bfseries\small\color{accent}}p{2.2cm} X @{}}
<% for skill in d.skills %>
  <<skill.category>> & \small <<skill.items>> \\[3pt]
<% endfor %>
\end{tabularx}
<% endif %>

%-------- PROJECTS --------
<% if d.projects %>
\section{Projects}
<% for project in d.projects %>
\noindent{\bfseries\color{accent}<<project.title>>}
<% if project.technologies %>
  \hfill \textcolor{mutedgray}{\small\textit{<<project.technologies>>}}
<% endif %>
\\\small <<project.description>>
\vspace{5pt}
<% endfor %>
<% endif %>

%-------- AWARDS --------
<% if d.awards %>
\section{Honors \& Awards}
\begin{itemize}[noitemsep, topsep=2pt, leftmargin=1.2em]
<% for award in d.awards %>
  \item \small <<award>>
<% endfor %>
\end{itemize}
<% endif %>

%-------- VOLUNTEER --------
<% if d.volunteer %>
\section{Volunteer Experience}
<% for vol in d.volunteer %>
\noindent\textbf{<<vol.role>>}
\textcolor{mutedgray}{|} \textit{<<vol.organization>>}
<% if vol.location %>\textcolor{mutedgray}{| <<vol.location>>}<% endif %>
\hfill \textcolor{mutedgray}{\small <<vol.dates>>}
<% if vol.description %>\\{\small <<vol.description>>}<% endif %>
\vspace{5pt}
<% endfor %>
<% endif %>

\end{document}
"""


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 3 — Sidebar
#  Two-column header block (name left, contact/skills right) + normal body
#  Multi-page friendly. Packages: texlive-latex-base + texlive-latex-extra only.
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_3 = r"""
%------------------------
% Resume Template 3 — Sidebar
% Two-column header: dark name block left, contact/skills right
%------------------------

\documentclass[a4paper,11pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[left=0.75in,right=0.75in,top=0.75in,bottom=0.75in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{array}
\usepackage{tikz}
\usetikzlibrary{calc}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

% Colours
\definecolor{sidebarBg}{RGB}{31,41,55}     % gray-800
\definecolor{sidebarText}{RGB}{243,244,246}% gray-100
\definecolor{accentBlue}{RGB}{37,99,235}   % blue-600
\definecolor{muted}{RGB}{107,114,128}      % gray-500

% Section heading: bold, blue, with gray rule
\titleformat{\section}[block]
  {\large\bfseries\color{accentBlue}}{}{0em}{}[\color{gray}\titlerule]
\titlespacing*{\section}{0pt}{10pt}{5pt}

% Page border on every page
\AddToHook{shipout/background}{%
  \begin{tikzpicture}[overlay,remember picture]%
    \draw[line width=1.2pt,gray!55,rounded corners=3pt]%
      ($(current page.north west)+(0.45cm,-0.45cm)$) rectangle%
      ($(current page.south east)+(-0.45cm,0.45cm)$);%
  \end{tikzpicture}%
}

%==============================================================
\begin{document}
%==============================================================

%-------- TWO-COLUMN HEADER BLOCK --------
\noindent
\begin{minipage}[t]{0.38\textwidth}
  \colorbox{sidebarBg}{\begin{minipage}[t][3.6cm][t]{\linewidth}
    \vspace{8pt}
    \hspace{6pt}{\Large\bfseries\color{sidebarText} <<d.name>>}
    \vspace{6pt}
<% if d.phone %>
    \\\hspace{6pt}\small\color{sidebarText}<<d.phone>>
<% endif %>
<% if d.email %>
    \\\hspace{6pt}\small\color{sidebarText}\href{mailto:<<d.email>>}{<<d.email | le>>}
<% endif %>
<% if d.linkedin %>
    \\\hspace{6pt}\small\color{sidebarText}\href{<<d.linkedin>>}{<<d.linkedin | clean_url | le>>}
<% endif %>
<% if d.github %>
    \\\hspace{6pt}\small\color{sidebarText}\href{https://github.com/<<d.github>>}{github.com/<<d.github | le>>}
<% endif %>
<% if d.portfolio_url %>
    \\\hspace{6pt}\small\color{sidebarText}\href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>}
<% endif %>
    \vspace{8pt}
  \end{minipage}}
\end{minipage}%
\hspace{0.03\textwidth}%
\begin{minipage}[t]{0.59\textwidth}
  \vspace{4pt}
<% if d.skills %>
  \textbf{\color{accentBlue}\small SKILLS}\\[2pt]
  {\color{gray}\rule{\linewidth}{0.4pt}}\\[4pt]
<% for skill in d.skills %>
  \noindent{\small\bfseries <<skill.category>>:} {\small <<skill.items>>}\\[2pt]
<% endfor %>
<% endif %>
\end{minipage}

\vspace{10pt}

%-------- SUMMARY --------
<% if d.summary %>
\section{Professional Summary}
\small <<d.summary>>
<% endif %>

%-------- EXPERIENCE --------
<% if d.experience %>
\section{Experience}
<% for exp in d.experience %>
\noindent
\begin{tabularx}{\textwidth}{@{}X r@{}}
  \textbf{<<exp.role>>} & \textcolor{muted}{\small <<exp.dates>>} \\
  \small\textit{<<exp.company>><% if exp.location %>, <<exp.location>><% endif %>} &
\end{tabularx}
\begin{itemize}[noitemsep, topsep=2pt, leftmargin=1.2em]
<% for bullet in exp.bullets %>
  \item \small <<bullet>>
<% endfor %>
\end{itemize}
\vspace{5pt}
<% endfor %>
<% endif %>

%-------- EDUCATION --------
<% if d.education %>
\section{Education}
<% for edu in d.education %>
\noindent
\begin{tabularx}{\textwidth}{@{}X r@{}}
  \textbf{<<edu.institution>>} & \textcolor{muted}{\small <<edu.dates>>} \\
  \small\textit{<<edu.degree>><% if edu.field %>, <<edu.field>><% endif %>>}
  <% if edu.gpa %>& \textcolor{muted}{\small GPA: <<edu.gpa>>}<% endif %>
\end{tabularx}
<% if edu.courses %>
\\\small\textcolor{muted}{Courses: <<edu.courses>>}
<% endif %>
\vspace{5pt}
<% endfor %>
<% endif %>

%-------- PROJECTS --------
<% if d.projects %>
\section{Projects}
<% for project in d.projects %>
\noindent\textbf{<<project.title>>}
<% if project.technologies %>
  \hfill \textcolor{muted}{\small\textit{<<project.technologies>>}}
<% endif %>
\\\small <<project.description>>
\vspace{5pt}
<% endfor %>
<% endif %>

%-------- AWARDS --------
<% if d.awards %>
\section{Honors \& Awards}
\begin{itemize}[noitemsep, topsep=2pt, leftmargin=1.2em]
<% for award in d.awards %>
  \item \small <<award>>
<% endfor %>
\end{itemize}
<% endif %>

%-------- VOLUNTEER --------
<% if d.volunteer %>
\section{Volunteer Experience}
<% for vol in d.volunteer %>
\noindent\textbf{<<vol.role>>} --- \textit{<<vol.organization>>}
<% if vol.location %>, <<vol.location>><% endif %>
\hfill \textcolor{muted}{\small <<vol.dates>>}
<% if vol.description %>\\{\small <<vol.description>>}<% endif %>
\vspace{5pt}
<% endfor %>
<% endif %>

\end{document}
"""


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 4 — ATS Classic (original Anubhav Singh style)
#  UNCHANGED from original — border added only
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_4 = r"""
%------------------------
% Resume Template 4 — ATS Classic
% Original Author : Anubhav Singh (github.com/xprilion)
% Adapted by AI Resume Builder
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
\usepackage{tikz}
\usetikzlibrary{calc}

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

% Page border on every page
\AddToHook{shipout/background}{%
  \begin{tikzpicture}[overlay,remember picture]%
    \draw[line width=1.2pt,gray!55,rounded corners=3pt]%
      ($(current page.north west)+(0.45cm,-0.45cm)$) rectangle%
      ($(current page.south east)+(-0.45cm,0.45cm)$);%
  \end{tikzpicture}%
}

\newcommand{\resumeItem}[2]{
  \item\small{
    \textbf{#1}{: #2 \vspace{-2pt}}
  }
}

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


# ── Template registry ─────────────────────────────────────────────────────────

_TEMPLATES = {
    1: _TEMPLATE_1,
    2: _TEMPLATE_2,
    3: _TEMPLATE_3,
    4: _TEMPLATE_4,
}


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

    for edu in data.get("education", []):
        edu.setdefault("gpa",     "")
        edu.setdefault("courses", "")

    for exp in data.get("experience", []):
        exp.setdefault("bullets", [])

    for vol in data.get("volunteer", []):
        vol.setdefault("organization", vol.get("role", ""))
        vol.setdefault("description",  "")

    return data


# ── PDF compilation ───────────────────────────────────────────────────────────

def _compile_latex(latex_src: str) -> bytes:
    """Write latex_src to a temp dir, run pdflatex twice, return PDF bytes."""
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
        for _ in range(2):
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if not os.path.exists(pdf_path):
            log_tail = ""
            if os.path.exists(log_path):
                with open(log_path, encoding="utf-8", errors="ignore") as lf:
                    full_log = lf.read()
                error_lines = [ln for ln in full_log.splitlines() if ln.startswith("!")]
                log_tail = "\n".join(error_lines[:10]) or full_log[-2000:]
            raise RuntimeError(
                f"pdflatex failed (exit code {result.returncode}).\n"
                f"LaTeX errors:\n{log_tail}"
            )

        with open(pdf_path, "rb") as fh:
            return fh.read()


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pdf(raw_data: dict, template_id: int = 4) -> bytes:
    """
    Build a PDF resume from structured resume data using the specified template.

    Parameters
    ----------
    raw_data    : Structured resume dict (from AI pipeline).
    template_id : 1 = Classic, 2 = Modern, 3 = Sidebar, 4 = ATS Classic.

    Returns
    -------
    bytes  — Raw PDF file contents.

    Raises
    ------
    RuntimeError  if pdflatex is not installed or compilation fails.
    ValueError    if template_id is not in 1–4.
    """
    if shutil.which("pdflatex") is None:
        raise RuntimeError(
            "pdflatex not found on PATH.\n"
            "  macOS : brew install --cask mactex\n"
            "  Linux : sudo apt install texlive-latex-extra texlive-fonts-recommended\n"
            "  Docker: see Dockerfile."
        )

    if template_id not in _TEMPLATES:
        raise ValueError(f"template_id must be 1–4, got {template_id!r}")

    data    = _normalize(dict(raw_data))
    escaped = _escape_data(data)
    env     = _make_jinja_env()
    latex_src = env.from_string(_TEMPLATES[template_id]).render(d=escaped)
    return _compile_latex(latex_src)


def generate_all_pdfs(raw_data: dict) -> dict:
    """
    Generate PDFs for all 4 templates in parallel.

    Returns
    -------
    dict  {template_id (int): pdf_bytes (bytes)}
    """
    data    = _normalize(dict(raw_data))
    escaped = _escape_data(data)
    env     = _make_jinja_env()

    def _render_and_compile(tid: int) -> tuple[int, bytes]:
        latex_src = env.from_string(_TEMPLATES[tid]).render(d=escaped)
        return tid, _compile_latex(latex_src)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_render_and_compile, tid): tid for tid in _TEMPLATES}
        results = {}
        for future in futures:
            tid, pdf_bytes = future.result()
            results[tid] = pdf_bytes

    return results

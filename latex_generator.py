"""
latex_generator.py — PDF generation via 4 LaTeX Templates
==========================================================
Supports 4 distinct resume templates selectable by template_id (1–4).

Templates:
  1 — Classic   : Clean two-column header, section rules (Jitin Nair style)
  2 — Modern    : Indigo header bar, colored section titles
  3 — Sidebar   : Two-column layout with dark left sidebar
  4 — ATS       : Original template (Anubhav Singh style)

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
#  Clean minimal article with two-column header and ruled sections
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_1 = r"""
%------------------------
% Resume Template 1 — Classic
% Style: Jitin Nair inspired, clean article layout
%------------------------

\documentclass[a4paper,11pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[left=0.9in,right=0.9in,top=0.75in,bottom=0.75in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{array}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

% Section style: large, bold, small-caps with a rule underneath
\titleformat{\section}{\large\bfseries\scshape\raggedright}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{10pt}{5pt}

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
  \small <<edu.degree>><% if edu.field %>, <<edu.field>><% endif %> &
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
<% if project.technologies %> \hfill \small\textit{<<project.technologies>>}<% endif %>\\
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
#  TEMPLATE 2 — Modern (Indigo header bar, colored section titles)
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_2 = r"""
%------------------------
% Resume Template 2 — Modern
% Style: Indigo header bar, bold colored section headings
%------------------------

\documentclass[a4paper,10.5pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[left=0.7in,right=0.7in,top=0in,bottom=0.6in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{tabularx}
\usepackage{array}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}

% Brand colour
\definecolor{accent}{RGB}{67,56,202}     % indigo-700
\definecolor{accentbg}{RGB}{224,231,255} % indigo-100
\definecolor{lightgray}{RGB}{107,114,128}

% Section headings: bold, accent-coloured, with a thin coloured rule
\titleformat{\section}[block]
  {\large\bfseries\color{accent}}{}{0em}{}[\color{accent}\titlerule]
\titlespacing*{\section}{0pt}{10pt}{5pt}

%==============================================================
\begin{document}
%==============================================================

%-------- HEADER BAR --------
\noindent
\colorbox{accent}{%
  \begin{minipage}[c][1.8cm]{\dimexpr\textwidth+\oddsidemargin+1in+\hoffset+\evensidemargin\relax}%
    \hspace{0.7in}%
    {\color{white}\Huge\bfseries <<d.name>>}%
  \end{minipage}%
}

\vspace{0pt}

% Contact row
\noindent\colorbox{accentbg}{%
  \begin{minipage}[c][0.55cm]{\dimexpr\textwidth+\oddsidemargin+1in+\hoffset+\evensidemargin\relax}%
    \hspace{0.7in}\small\color{lightgray}
    \href{mailto:<<d.email>>}{<<d.email | le>>}
<% if d.phone %>
    ~\textbf{|}~ <<d.phone>>
<% endif %>
<% if d.linkedin %>
    ~\textbf{|}~ \href{<<d.linkedin>>}{<<d.linkedin | clean_url | le>>}
<% endif %>
<% if d.github %>
    ~\textbf{|}~ \href{https://github.com/<<d.github>>}{github.com/<<d.github | le>>}
<% endif %>
<% if d.portfolio_url %>
    ~\textbf{|}~ \href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>}
<% endif %>
  \end{minipage}%
}

\vspace{8pt}

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
  \textbf{<<exp.role>>} \textcolor{lightgray}{|} \textit{<<exp.company>>}
  \textcolor{lightgray}{| <<exp.location>>} & \textcolor{lightgray}{\small <<exp.dates>>}
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
  \textbf{<<edu.institution>>} & \textcolor{lightgray}{\small <<edu.dates>>} \\
  \small \textit{<<edu.degree>><% if edu.field %> in <<edu.field>><% endif %>}
  <% if edu.gpa %>& \textcolor{lightgray}{\small GPA: <<edu.gpa>>}<% endif %>
\end{tabularx}
<% if edu.courses %>
\\\small\textcolor{lightgray}{Courses: <<edu.courses>>}
<% endif %>
\vspace{5pt}
<% endfor %>
<% endif %>

%-------- SKILLS --------
<% if d.skills %>
\section{Skills}
\begin{tabularx}{\textwidth}{@{} >{\bfseries\small\color{accent}}l X @{}}
<% for skill in d.skills %>
  <<skill.category>> & \small <<skill.items>> \\[2pt]
<% endfor %>
\end{tabularx}
<% endif %>

%-------- PROJECTS --------
<% if d.projects %>
\section{Projects}
<% for project in d.projects %>
\noindent\textbf{\color{accent}<<project.title>>}
<% if project.technologies %>
  \hfill \textcolor{lightgray}{\small\textit{<<project.technologies>>}}
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
\textcolor{lightgray}{|} \textit{<<vol.organization>>}
<% if vol.location %>\textcolor{lightgray}{| <<vol.location>>}<% endif %>
\hfill \textcolor{lightgray}{\small <<vol.dates>>}
<% if vol.description %>\\{\small <<vol.description>>}<% endif %>
\vspace{5pt}
<% endfor %>
<% endif %>

\end{document}
"""


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 3 — Sidebar (two-column: dark left sidebar + white right content)
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_3 = r"""
%------------------------
% Resume Template 3 — Sidebar
% Style: Dark sidebar on left, content on right
%------------------------

\documentclass[a4paper,10pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=0in]{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{array}
\usepackage{tabularx}
\usepackage{tikz}
\usepackage{minibox}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}

\definecolor{sidebarBg}{RGB}{31,41,55}    % gray-800
\definecolor{sidebarText}{RGB}{243,244,246} % gray-100
\definecolor{sidebarRule}{RGB}{75,85,99}   % gray-600
\definecolor{sidebarMuted}{RGB}{156,163,175}% gray-400
\definecolor{contentRule}{RGB}{209,213,219} % gray-300
\definecolor{accentBlue}{RGB}{37,99,235}   % blue-600

% -- Sidebar section heading
\newcommand{\sideSection}[1]{%
  \vspace{6pt}%
  {\color{sidebarText}\small\bfseries\MakeUppercase{#1}}\\[-2pt]%
  {\color{sidebarRule}\rule{\linewidth}{0.4pt}}%
  \vspace{2pt}%
}

% -- Main content section heading
\newcommand{\mainSection}[1]{%
  \vspace{8pt}%
  {\large\bfseries\color{accentBlue} #1}\\[-4pt]%
  {\color{contentRule}\rule{\linewidth}{0.6pt}}%
  \vspace{3pt}%
}

%==============================================================
\begin{document}
%==============================================================

% Overall two-column table — sidebar 34%, content 66%
\noindent
\begin{tabular*}{\paperwidth}{@{} p{0.34\paperwidth} @{} p{0.01\paperwidth} @{} p{0.62\paperwidth} @{}}

%====== LEFT SIDEBAR ======
\cellcolor{sidebarBg}%
\begin{minipage}[t][\paperheight][t]{0.33\paperwidth}%
\color{sidebarText}%
\vspace*{14pt}%
\hspace*{10pt}%
\begin{minipage}{0.28\paperwidth}

% Name
{\Large\bfseries\color{white} <<d.name>>}
\vspace{10pt}

% Contact
\sideSection{Contact}
<% if d.email %>
{\small\color{sidebarMuted} Email}\\
{\small\href{mailto:<<d.email>>}{<<d.email | le>>}}\\[3pt]
<% endif %>
<% if d.phone %>
{\small\color{sidebarMuted} Phone}\\
{\small <<d.phone>>}\\[3pt]
<% endif %>
<% if d.linkedin %>
{\small\color{sidebarMuted} LinkedIn}\\
{\small\href{<<d.linkedin>>}{<<d.linkedin | clean_url | le>>}}\\[3pt]
<% endif %>
<% if d.github %>
{\small\color{sidebarMuted} GitHub}\\
{\small\href{https://github.com/<<d.github>>}{github.com/<<d.github | le>>}}\\[3pt]
<% endif %>
<% if d.portfolio_url %>
{\small\color{sidebarMuted} Portfolio}\\
{\small\href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>}}\\[3pt]
<% endif %>

% Skills
<% if d.skills %>
\sideSection{Skills}
<% for skill in d.skills %>
{\small\bfseries\color{white}<<skill.category>>}\\
{\small\color{sidebarMuted}<<skill.items>>}\\[4pt]
<% endfor %>
<% endif %>

% Education
<% if d.education %>
\sideSection{Education}
<% for edu in d.education %>
{\small\bfseries\color{white}<<edu.institution>>}\\
{\small\color{sidebarMuted}<<edu.degree>><% if edu.field %>, <<edu.field>><% endif %>>}\\
{\small\color{sidebarMuted}<<edu.dates>><% if edu.gpa %> | GPA: <<edu.gpa>><% endif %>>}\\[4pt]
<% endfor %>
<% endif %>

% Awards
<% if d.awards %>
\sideSection{Awards}
\begin{itemize}[noitemsep,topsep=0pt,leftmargin=1em]
<% for award in d.awards %>
  \item {\small\color{sidebarMuted}<<award>>}
<% endfor %>
\end{itemize}
<% endif %>

\end{minipage}%
\end{minipage}

& & % spacer column

%====== RIGHT CONTENT ======
\begin{minipage}[t][\paperheight][t]{0.62\paperwidth}%
\vspace*{10pt}%
\hspace*{8pt}%
\begin{minipage}{0.57\paperwidth}

% Summary
<% if d.summary %>
\mainSection{Professional Summary}
\small <<d.summary>>
<% endif %>

% Experience
<% if d.experience %>
\mainSection{Experience}
<% for exp in d.experience %>
\noindent{\small\bfseries <<exp.role>>} \hfill {\small\textit{<<exp.dates>>}}\\
{\small\textit{<<exp.company>>}<% if exp.location %>, <<exp.location>><% endif %>}
\begin{itemize}[noitemsep,topsep=2pt,leftmargin=1.2em]
<% for bullet in exp.bullets %>
  \item{\small <<bullet>>}
<% endfor %>
\end{itemize}
\vspace{4pt}
<% endfor %>
<% endif %>

% Projects
<% if d.projects %>
\mainSection{Projects}
<% for project in d.projects %>
\noindent{\small\bfseries <<project.title>>}
<% if project.technologies %>
  \hfill {\small\textit{<<project.technologies>>}}
<% endif %>
\\{\small <<project.description>>}
\vspace{4pt}
<% endfor %>
<% endif %>

% Volunteer
<% if d.volunteer %>
\mainSection{Volunteer}
<% for vol in d.volunteer %>
\noindent{\small\bfseries <<vol.role>>} --- \textit{<<vol.organization>>}
<% if vol.location %>, <<vol.location>><% endif %>
\hfill{\small\textit{<<vol.dates>>}}
<% if vol.description %>\\{\small <<vol.description>>}<% endif %>
\vspace{4pt}
<% endfor %>
<% endif %>

\end{minipage}%
\end{minipage}

\end{tabular*}

\end{document}
"""


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 4 — ATS Classic (original Anubhav Singh style)
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
    # Normalise and escape once, then render each template
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

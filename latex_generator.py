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
#  TEMPLATE 1 — Jake's Resume Style
#  Source: https://github.com/jakegut/resume  (MIT License)
#  Packages: latexsym, fullpage, titlesec, color, verbatim, enumitem,
#            hyperref, fancyhdr, babel, tabularx  — all in texlive-latex-extra
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_1 = r"""
%-------------------------
% Resume — Jake's Resume Style
% Based on: https://github.com/jakegut/resume (MIT License)
%-------------------------

\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

%-------------------------
% Custom commands

\newcommand{\jresumeItem}[1]{
  \item\small{{#1 \vspace{-2pt}}}
}

\newcommand{\jresumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\jresumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\jresumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\jresumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\jresumeItemListStart}{\begin{itemize}}
\newcommand{\jresumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
\begin{document}

%----------HEADING----------
\begin{center}
    \textbf{\Huge \scshape <<d.name>>} \\ \vspace{4pt}
    \small
    \href{mailto:<<d.email>>}{<<d.email | le>>}
<% if d.phone %> $|$ \href{tel:<<d.phone>>}{<<d.phone>>}<% endif %>
<% if d.linkedin %> $|$ \href{<<d.linkedin>>}{<<d.linkedin | clean_url | le>>}<% endif %>
<% if d.github %> $|$ \href{https://github.com/<<d.github>>}{github.com/<<d.github | le>>}<% endif %>
<% if d.portfolio_url %> $|$ \href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>}<% endif %>
\end{center}

%-----------SUMMARY-----------
<% if d.summary %>
\section{Summary}
 \jresumeSubHeadingListStart
    \small{\item{<<d.summary>>}}
 \jresumeSubHeadingListEnd
<% endif %>

%-----------EDUCATION-----------
<% if d.education %>
\section{Education}
  \jresumeSubHeadingListStart
<% for edu in d.education %>
    \jresumeSubheading
      {<<edu.institution>>}{<<edu.dates>>}
      {<<edu.degree>><% if edu.field %> -- <<edu.field>><% endif %>}{<% if edu.gpa %>GPA: <<edu.gpa>><% endif %>}
<% if edu.courses %>
      \jresumeItemListStart
        \jresumeItem{Relevant Coursework: <<edu.courses>>}
      \jresumeItemListEnd
<% endif %>
<% endfor %>
  \jresumeSubHeadingListEnd
<% endif %>

%-----------EXPERIENCE-----------
<% if d.experience %>
\section{Experience}
  \jresumeSubHeadingListStart
<% for exp in d.experience %>
    \jresumeSubheading
      {<<exp.role>>}{<<exp.dates>>}
      {<<exp.company>>}{<<exp.location>>}
      \jresumeItemListStart
<% for bullet in exp.bullets %>
        \jresumeItem{<<bullet>>}
<% endfor %>
      \jresumeItemListEnd
<% endfor %>
  \jresumeSubHeadingListEnd
<% endif %>

%-----------PROJECTS-----------
<% if d.projects %>
\section{Projects}
    \jresumeSubHeadingListStart
<% for project in d.projects %>
      \jresumeProjectHeading
          {\textbf{<<project.title>>} $|$ \emph{\small <<project.technologies>>}}{}
          \jresumeItemListStart
            \jresumeItem{<<project.description>>}
          \jresumeItemListEnd
<% endfor %>
    \jresumeSubHeadingListEnd
<% endif %>

%-----------TECHNICAL SKILLS-----------
<% if d.skills %>
\section{Technical Skills}
 \jresumeSubHeadingListStart
    \small{\item{
<% for skill in d.skills %>
     \textbf{<<skill.category>>}{: <<skill.items>>} \\
<% endfor %>
    }}
 \jresumeSubHeadingListEnd
<% endif %>

%-----------HONORS & AWARDS-----------
<% if d.awards %>
\section{Honors \& Awards}
 \jresumeSubHeadingListStart
    \small{\item{
<% for award in d.awards %>
      $\bullet$\ <<award>> \\
<% endfor %>
    }}
 \jresumeSubHeadingListEnd
<% endif %>

%-----------VOLUNTEER-----------
<% if d.volunteer %>
\section{Volunteer Experience}
  \jresumeSubHeadingListStart
<% for vol in d.volunteer %>
    \jresumeSubheading
      {<<vol.role>>}{<<vol.dates>>}
      {<<vol.organization>>}{<<vol.location>>}
<% if vol.description %>
      \jresumeItemListStart
        \jresumeItem{<<vol.description>>}
      \jresumeItemListEnd
<% endif %>
<% endfor %>
  \jresumeSubHeadingListEnd
<% endif %>

\end{document}
"""


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 2 — Colored Professional (Debarghya Das / sb2nov style)
#  Packages: latexsym, fullpage, titlesec, color, xcolor, verbatim,
#            enumitem, hyperref, fancyhdr, tabularx, geometry
#            — all in texlive-latex-extra (NO lmodern)
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_2 = r"""
%-------------------------
% Resume — Colored Professional Style
% Inspired by Debarghya Das / sb2nov templates
%-------------------------

\documentclass[a4paper,10.5pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage[usenames,dvipsnames]{color}
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage{tabularx}
\usepackage[left=0.75in,right=0.75in,top=0.6in,bottom=0.6in]{geometry}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\parindent}{0pt}

% Brand colour — navy blue
\definecolor{cvblue}{RGB}{0,70,127}
\definecolor{cvgray}{RGB}{100,100,100}

% Section headings: colored, scshape, with a rule
\titleformat{\section}{
  \vspace{-6pt}\color{cvblue}\scshape\raggedright\large\bfseries
}{}{0em}{}[\color{cvblue}\titlerule \vspace{-4pt}]

%------- Custom commands -------

\newcommand{\cvSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{\color{cvblue}#1} & \textcolor{cvgray}{\small #2} \\
      \textit{\small#3} & \textcolor{cvgray}{\textit{\small #4}} \\
    \end{tabular*}\vspace{-6pt}
}

\newcommand{\cvItem}[1]{
  \item\small{{#1 \vspace{-2pt}}}
}

\newcommand{\cvProjectHeading}[2]{
    \item
    \begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & \textcolor{cvgray}{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\cvSubHeadingListStart}{\begin{itemize}[leftmargin=0.0in, label={}]}
\newcommand{\cvSubHeadingListEnd}{\end{itemize}}
\newcommand{\cvItemListStart}{\begin{itemize}[leftmargin=0.18in]}
\newcommand{\cvItemListEnd}{\end{itemize}\vspace{-4pt}}

%-------------------------------------------
\begin{document}

%----------HEADING----------
\begin{center}
    {\Huge \textbf{\color{cvblue}<<d.name>>}} \\ \vspace{5pt}
    \small
    \href{mailto:<<d.email>>}{\underline{<<d.email | le>>}}
<% if d.phone %> $\cdot$ <<d.phone>><% endif %>
<% if d.linkedin %> $\cdot$ \href{<<d.linkedin>>}{\underline{<<d.linkedin | clean_url | le>>}}<% endif %>
<% if d.github %> $\cdot$ \href{https://github.com/<<d.github>>}{\underline{github.com/<<d.github | le>>}}<% endif %>
<% if d.portfolio_url %> $\cdot$ \href{<<d.portfolio_url>>}{\underline{<<d.portfolio_url | clean_url | le>>}}<% endif %>
\end{center}

%-----------SUMMARY-----------
<% if d.summary %>
\section{Professional Summary}
  \cvSubHeadingListStart
    \small{\item{<<d.summary>>}}
  \cvSubHeadingListEnd
<% endif %>

%-----------EXPERIENCE-----------
<% if d.experience %>
\section{Experience}
  \cvSubHeadingListStart
<% for exp in d.experience %>
    \cvSubheading
      {<<exp.role>>}{<<exp.dates>>}
      {<<exp.company>> $-$ <<exp.location>>}{}
      \cvItemListStart
<% for bullet in exp.bullets %>
        \cvItem{<<bullet>>}
<% endfor %>
      \cvItemListEnd
<% endfor %>
  \cvSubHeadingListEnd
<% endif %>

%-----------EDUCATION-----------
<% if d.education %>
\section{Education}
  \cvSubHeadingListStart
<% for edu in d.education %>
    \cvSubheading
      {<<edu.institution>>}{<<edu.dates>>}
      {<<edu.degree>><% if edu.field %> in <<edu.field>><% endif %>}<% if edu.gpa %>{GPA: <<edu.gpa>>}<% else %>{}<% endif %>
<% if edu.courses %>
      \cvItemListStart
        \cvItem{Relevant Coursework: <<edu.courses>>}
      \cvItemListEnd
<% endif %>
<% endfor %>
  \cvSubHeadingListEnd
<% endif %>

%-----------TECHNICAL SKILLS-----------
<% if d.skills %>
\section{Technical Skills}
 \cvSubHeadingListStart
    \small{\item{
<% for skill in d.skills %>
     \textbf{\color{cvblue}<<skill.category>>}{: <<skill.items>>} \\
<% endfor %>
    }}
 \cvSubHeadingListEnd
<% endif %>

%-----------PROJECTS-----------
<% if d.projects %>
\section{Projects}
    \cvSubHeadingListStart
<% for project in d.projects %>
      \cvProjectHeading
          {\textbf{\color{cvblue}<<project.title>>} $|$ \textit{\small <<project.technologies>>}}{}
          \cvItemListStart
            \cvItem{<<project.description>>}
          \cvItemListEnd
<% endfor %>
    \cvSubHeadingListEnd
<% endif %>

%-----------HONORS & AWARDS-----------
<% if d.awards %>
\section{Honors \& Awards}
 \cvSubHeadingListStart
    \small{\item{
<% for award in d.awards %>
      $\bullet$\ <<award>> \\
<% endfor %>
    }}
 \cvSubHeadingListEnd
<% endif %>

%-----------VOLUNTEER-----------
<% if d.volunteer %>
\section{Volunteer Experience}
  \cvSubHeadingListStart
<% for vol in d.volunteer %>
    \cvSubheading
      {<<vol.role>>}{<<vol.dates>>}
      {<<vol.organization>><% if vol.location %> $-$ <<vol.location>><% endif %>}{}
<% if vol.description %>
      \cvItemListStart
        \cvItem{<<vol.description>>}
      \cvItemListEnd
<% endif %>
<% endfor %>
  \cvSubHeadingListEnd
<% endif %>

\end{document}
"""


# ──────────────────────────────────────────────────────────────────────────────
#  TEMPLATE 3 — Two-Column Sidebar
#  Left sidebar (dark bg via colortbl) + right main content via tabularx.
#  Packages: latexsym, fullpage, titlesec, color, xcolor, colortbl,
#            enumitem, hyperref, fancyhdr, tabularx, array, geometry
#            — all in texlive-latex-extra (NO lmodern, NO tikz, NO minibox)
# ──────────────────────────────────────────────────────────────────────────────

_TEMPLATE_3 = r"""
%-------------------------
% Resume — Two-Column Sidebar Style
% Left: dark sidebar with contact/skills/education
% Right: main content (summary/experience/projects)
%-------------------------

\documentclass[a4paper,10pt]{article}

\usepackage{latexsym}
\usepackage[usenames,dvipsnames]{color}
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage{colortbl}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage{array}
\usepackage{tabularx}
\usepackage[left=0in,right=0.5in,top=0in,bottom=0in]{geometry}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlength{\tabcolsep}{0pt}

% Colours
\definecolor{sidecolor}{RGB}{35,47,62}      % dark blue-gray
\definecolor{sidetext}{RGB}{220,225,232}    % light gray-blue
\definecolor{sidemuted}{RGB}{140,152,166}   % muted blue-gray
\definecolor{siderule}{RGB}{65,80,95}       % rule color
\definecolor{mainaccent}{RGB}{0,84,147}     % header blue
\definecolor{maingray}{RGB}{90,90,90}       % body gray

% Sidebar column type — dark background, light text, padding
\newcolumntype{S}{>{\columncolor{sidecolor}\color{sidetext}\raggedright\arraybackslash\hspace{8pt}}p{0.32\textwidth}}
% Main content column type
\newcolumntype{M}{>{\raggedright\arraybackslash\hspace{8pt}}p{0.62\textwidth}}

% Sidebar section heading
\newcommand{\sideHead}[1]{%
  \vspace{7pt}%
  {\footnotesize\bfseries\color{sidetext}\MakeUppercase{#1}}\\[-1pt]%
  {\color{siderule}\hrule height 0.4pt}%
  \vspace{3pt}%
}

% Main section heading
\newcommand{\mainHead}[1]{%
  \vspace{6pt}%
  {\large\bfseries\color{mainaccent} #1}\\[-4pt]%
  {\color{mainaccent}\hrule height 0.6pt}%
  \vspace{3pt}%
}

%-------------------------------------------
\begin{document}

\noindent
\begin{tabular*}{\paperwidth}{@{}S@{\hspace{6pt}}M@{}}

%=============== LEFT SIDEBAR ===============
{\vspace*{12pt}
{\Large\bfseries\color{white}<<d.name>>}
\vspace{10pt}

\sideHead{Contact}
<% if d.email %>
{\footnotesize\color{sidemuted}Email}\\
{\footnotesize\href{mailto:<<d.email>>}{<<d.email | le>>}}\\
[3pt]
<% endif %>
<% if d.phone %>
{\footnotesize\color{sidemuted}Phone}\\
{\footnotesize <<d.phone>>}\\
[3pt]
<% endif %>
<% if d.linkedin %>
{\footnotesize\color{sidemuted}LinkedIn}\\
{\footnotesize\href{<<d.linkedin>>}{<<d.linkedin | clean_url | le>>}}\\
[3pt]
<% endif %>
<% if d.github %>
{\footnotesize\color{sidemuted}GitHub}\\
{\footnotesize\href{https://github.com/<<d.github>>}{github.com/<<d.github | le>>}}\\
[3pt]
<% endif %>
<% if d.portfolio_url %>
{\footnotesize\color{sidemuted}Portfolio}\\
{\footnotesize\href{<<d.portfolio_url>>}{<<d.portfolio_url | clean_url | le>>}}\\
[3pt]
<% endif %>

<% if d.skills %>
\sideHead{Skills}
<% for skill in d.skills %>
{\footnotesize\bfseries\color{white}<<skill.category>>}\\
{\footnotesize\color{sidemuted}<<skill.items>>}\\
[4pt]
<% endfor %>
<% endif %>

<% if d.education %>
\sideHead{Education}
<% for edu in d.education %>
{\footnotesize\bfseries\color{white}<<edu.institution>>}\\
{\footnotesize\color{sidemuted}<<edu.degree>><% if edu.field %>, <<edu.field>><% endif %>}\\
{\footnotesize\color{sidemuted}<<edu.dates>><% if edu.gpa %> $|$ GPA: <<edu.gpa>><% endif %>}\\
[4pt]
<% endfor %>
<% endif %>

<% if d.awards %>
\sideHead{Awards}
\begin{itemize}[noitemsep,topsep=0pt,leftmargin=0.8em,label={\tiny$\bullet$}]
<% for award in d.awards %>
  \item {\footnotesize\color{sidemuted}<<award>>}
<% endfor %>
\end{itemize}
<% endif %>
}
&
%=============== RIGHT MAIN ===============
{\vspace*{10pt}

<% if d.summary %>
\mainHead{Professional Summary}
{\small <<d.summary>>}
<% endif %>

<% if d.experience %>
\mainHead{Experience}
<% for exp in d.experience %>
{\small\bfseries\color{mainaccent}<<exp.role>>} \hfill {\small\color{maingray}\textit{<<exp.dates>>}}\\
{\small\textit{<<exp.company>>}<% if exp.location %>, \textit{<<exp.location>>}<% endif %>}
\begin{itemize}[noitemsep,topsep=2pt,leftmargin=1em,label={\tiny$\bullet$}]
<% for bullet in exp.bullets %>
  \item {\small <<bullet>>}
<% endfor %>
\end{itemize}
\vspace{3pt}
<% endfor %>
<% endif %>

<% if d.projects %>
\mainHead{Projects}
<% for project in d.projects %>
{\small\bfseries\color{mainaccent}<<project.title>>}
<% if project.technologies %>
  \hfill {\small\color{maingray}\textit{<<project.technologies>>}}
<% endif %>\\
{\small <<project.description>>}
\vspace{3pt}
<% endfor %>
<% endif %>

<% if d.volunteer %>
\mainHead{Volunteer}
<% for vol in d.volunteer %>
{\small\bfseries\color{mainaccent}<<vol.role>>} --- \textit{<<vol.organization>>}
<% if vol.location %>, {\small\color{maingray}<<vol.location>>}<% endif %>
\hfill {\small\color{maingray}\textit{<<vol.dates>>}}
<% if vol.description %>\\{\small <<vol.description>>}<% endif %>
\vspace{3pt}
<% endfor %>
<% endif %>
}

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

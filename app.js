/**
 * AI Resume Builder — Frontend (v2 — 4 templates)
 *
 * ⚙️  Set your backend URL here:
 *   Local dev  → 'http://localhost:8000'
 *   Render     → 'https://your-app-name.onrender.com'
 */
const API = 'https://template-4-resume.onrender.com';

// ── DOM refs ──────────────────────────────────────────────────────────────────

const dropZone   = document.getElementById('drop-zone');
const fileInput  = document.getElementById('file-input');
const dzIdle     = document.getElementById('dz-idle');
const dzDone     = document.getElementById('dz-done');
const dzFilename = document.getElementById('dz-filename');
const btnChange  = document.getElementById('btn-change');

const jdInput = document.getElementById('jd-input');
const jdChars = document.getElementById('jd-chars');

const btnGenerate  = document.getElementById('btn-generate');
const btnLabel     = document.getElementById('btn-label');
const btnArrow     = document.getElementById('btn-arrow');

const statusBox    = document.getElementById('status-box');
const progressFill = document.getElementById('progress-fill');
const statusMsg    = document.getElementById('status-msg');

const errorBox  = document.getElementById('error-box');
const errorMsg  = document.getElementById('error-msg');
const btnRetry  = document.getElementById('btn-retry');

const successBox    = document.getElementById('success-box');
const btnRedownload = document.getElementById('btn-redownload');

// JSON preview refs
const cardJsonPreview = document.getElementById('card-json-preview');
const jsonParseStatus = document.getElementById('json-parse-status');
const jsonSpinner     = document.getElementById('json-spinner');
const jsonParseMsg    = document.getElementById('json-parse-msg');
const jsonDataDisplay = document.getElementById('json-data-display');
const jsonFields      = document.getElementById('json-fields');
const btnDownloadJson = document.getElementById('btn-download-json');
const confirmGenerate = document.getElementById('confirm-generate');
const btnYesGenerate  = document.getElementById('btn-yes-generate');
const btnNoGenerate   = document.getElementById('btn-no-generate');

const cardJd     = document.getElementById('card-jd');
const genSection = document.getElementById('gen-section');

// ── State ─────────────────────────────────────────────────────────────────────

let selectedFile     = null;
let selectedTemplate = '3';    // default — Template 3 is pre-checked in HTML
let lastBlob         = null;
let lastFilename     = 'tailored_resume.pdf';
let extractedData    = null;   // stores the JSON from /parse

// ── Template selection ────────────────────────────────────────────────────────

document.querySelectorAll('input[name="template"]').forEach((radio) => {
  radio.addEventListener('change', (e) => {
    selectedTemplate = e.target.value;
  });
});

// ── File upload ───────────────────────────────────────────────────────────────

dropZone.addEventListener('click', (e) => {
  if (e.target !== btnChange) fileInput.click();
});

dropZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault(); dropZone.classList.add('drag-over');
});
['dragleave', 'dragend'].forEach((ev) =>
  dropZone.addEventListener(ev, () => dropZone.classList.remove('drag-over'))
);
dropZone.addEventListener('drop', (e) => {
  e.preventDefault(); dropZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) setFile(f);
});

btnChange.addEventListener('click', (e) => {
  e.stopPropagation();
  selectedFile = null; fileInput.value = '';
  dzIdle.hidden = false; dzDone.hidden = true;
  resetStatus();
});

function setFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'txt'].includes(ext)) { showError('Please upload a PDF or TXT file.'); return; }
  selectedFile = file;
  dzFilename.textContent = file.name;
  dzIdle.hidden = true; dzDone.hidden = false;
  resetStatus();
  parseResume(file);   // ← automatically extract features on upload
}

// ── JD character count ────────────────────────────────────────────────────────

jdInput.addEventListener('input', () => { jdChars.textContent = jdInput.value.length; });

// ── Parse resume on upload ───────────────────────────────────────────────────

async function parseResume(file) {
  // Reset JSON card state
  extractedData = null;
  cardJsonPreview.hidden  = false;
  jsonParseStatus.hidden  = false;
  jsonDataDisplay.hidden  = true;
  confirmGenerate.hidden  = true;
  cardJd.hidden           = true;
  genSection.hidden       = true;
  jsonSpinner.textContent = '⏳';
  jsonParseMsg.textContent = 'Extracting key features from your resume…';

  try {
    const form = new FormData();
    form.append('resume_file', file);
    const res = await fetch(`${API}/parse`, { method: 'POST', body: form });
    if (!res.ok) {
      let detail = `Server error (${res.status})`;
      try { detail = (await res.json()).detail ?? detail; } catch { /* ignore */ }
      throw new Error(detail);
    }
    extractedData = await res.json();
    renderJsonFields(extractedData);
    jsonParseStatus.hidden  = true;
    jsonDataDisplay.hidden  = false;
    confirmGenerate.hidden  = false;
  } catch (err) {
    jsonSpinner.textContent  = '⚠️';
    jsonParseMsg.textContent = `Could not extract resume data: ${err.message}`;
  }
}

function renderJsonFields(data) {
  jsonFields.innerHTML = '';

  const simple = [
    ['Name',       data.name],
    ['Email',      data.email],
    ['Phone',      data.phone],
    ['LinkedIn',   data.linkedin],
    ['GitHub',     data.github],
    ['Portfolio',  data.portfolio_url],
  ];

  simple.forEach(([label, val]) => {
    if (!val) return;
    const div = document.createElement('div');
    div.className = 'json-field';
    div.innerHTML = `<span class="json-field-label">${label}</span><span class="json-field-value">${escHtml(val)}</span>`;
    jsonFields.appendChild(div);
  });

  // Summary
  if (data.summary) {
    const div = document.createElement('div');
    div.className = 'json-field json-field-full';
    div.innerHTML = `<span class="json-field-label">Summary</span><span class="json-field-value json-summary">${escHtml(data.summary)}</span>`;
    jsonFields.appendChild(div);
  }

  // Skills
  if (data.skills && data.skills.length) {
    const div = document.createElement('div');
    div.className = 'json-field json-field-full';
    const skillList = data.skills.map(s => `<span class="skill-tag">${escHtml(s.category)}: ${escHtml(s.items)}</span>`).join('');
    div.innerHTML = `<span class="json-field-label">Skills</span><span class="json-field-value json-skills">${skillList}</span>`;
    jsonFields.appendChild(div);
  }

  // Experience count
  if (data.experience && data.experience.length) {
    const div = document.createElement('div');
    div.className = 'json-field';
    const roles = data.experience.map(e => escHtml(e.role + ' @ ' + e.company)).join(', ');
    div.innerHTML = `<span class="json-field-label">Experience (${data.experience.length})</span><span class="json-field-value">${roles}</span>`;
    jsonFields.appendChild(div);
  }

  // Projects count
  if (data.projects && data.projects.length) {
    const div = document.createElement('div');
    div.className = 'json-field';
    const titles = data.projects.map(p => escHtml(p.title)).join(', ');
    div.innerHTML = `<span class="json-field-label">Projects (${data.projects.length})</span><span class="json-field-value">${titles}</span>`;
    jsonFields.appendChild(div);
  }

  // Education
  if (data.education && data.education.length) {
    const div = document.createElement('div');
    div.className = 'json-field';
    const edu = data.education.map(e => escHtml(e.degree + ', ' + e.institution)).join(' | ');
    div.innerHTML = `<span class="json-field-label">Education</span><span class="json-field-value">${edu}</span>`;
    jsonFields.appendChild(div);
  }

  // Certifications
  if (data.certifications && data.certifications.length) {
    const div = document.createElement('div');
    div.className = 'json-field';
    const certs = data.certifications.map(c => escHtml(c.name)).join(', ');
    div.innerHTML = `<span class="json-field-label">Certifications</span><span class="json-field-value">${certs}</span>`;
    jsonFields.appendChild(div);
  }
}

function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Download JSON button
btnDownloadJson.addEventListener('click', () => {
  if (!extractedData) return;
  const blob = new Blob([JSON.stringify(extractedData, null, 2)], { type: 'application/json' });
  const name = (extractedData.name || 'resume').replace(/\s+/g, '_');
  triggerDownload(blob, `${name}_extracted.json`);
});

// Confirm-generate buttons
btnYesGenerate.addEventListener('click', () => {
  confirmGenerate.hidden = true;
  cardJd.hidden    = false;
  genSection.hidden = false;
  cardJd.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

btnNoGenerate.addEventListener('click', () => {
  // Reset everything back to just the upload step
  cardJsonPreview.hidden = true;
  cardJd.hidden          = true;
  genSection.hidden      = true;
  selectedFile           = null;
  extractedData          = null;
  fileInput.value        = '';
  dzIdle.hidden          = false;
  dzDone.hidden          = true;
  resetStatus();
});

// ── Progress steps ────────────────────────────────────────────────────────────

const STEPS = [
  { pct: 12, msg: '📄  Extracting text from your resume…' },
  { pct: 30, msg: '🧠  Parsing resume structure with AI…' },
  { pct: 53, msg: '🎯  Matching experience to JD keywords…' },
  { pct: 72, msg: '✨  Enhancing bullet points and summary…' },
  { pct: 88, msg: '⚙️   Compiling your personalised PDF…' },
];

// ── Generate ──────────────────────────────────────────────────────────────────

btnGenerate.addEventListener('click', generate);
btnRetry.addEventListener('click', () => { resetStatus(); generate(); });
btnRedownload.addEventListener('click', () => { if (lastBlob) triggerDownload(lastBlob, lastFilename); });

async function generate() {
  if (!selectedFile) { showError('Please upload your resume first.'); return; }
  const jd = jdInput.value.trim();
  if (jd.length < 50) { showError('Please paste a more complete job description (at least 50 characters).'); return; }

  resetStatus();
  setLoading(true);
  showStatus('Initialising…', 5);

  let step = 0;
  const ticker = setInterval(() => {
    if (step < STEPS.length) { showStatus(STEPS[step].msg, STEPS[step].pct); step++; }
  }, 4000);

  try {
    const form = new FormData();
    form.append('resume_file', selectedFile);
    form.append('job_description', jd);
    form.append('template_id', selectedTemplate);   // ← sends chosen template (1‑4)

    const res = await fetch(`${API}/generate`, { method: 'POST', body: form });

    clearInterval(ticker);

    if (!res.ok) {
      let detail = `Server error (${res.status})`;
      try { detail = (await res.json()).detail ?? detail; } catch { /* ignore */ }
      throw new Error(detail);
    }

    showStatus('✅  Preparing your download…', 100);

    const blob = await res.blob();
    lastBlob = blob;

    const cd = res.headers.get('Content-Disposition') ?? '';
    const match = cd.match(/filename="?([^";]+)"?/);
    if (match) lastFilename = match[1].trim();

    triggerDownload(blob, lastFilename);

    await sleep(700);
    setLoading(false);
    statusBox.hidden = true;
    successBox.hidden = false;

  } catch (err) {
    clearInterval(ticker);
    setLoading(false);
    showError(err.message || 'Something went wrong. Please try again.');
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 6000);
}

function showStatus(msg, pct) {
  statusBox.hidden = false; errorBox.hidden = true; successBox.hidden = true;
  statusMsg.textContent = msg; progressFill.style.width = `${pct}%`;
}

function showError(msg) {
  statusBox.hidden = true; successBox.hidden = true; errorBox.hidden = false;
  errorMsg.textContent = msg;
}

function resetStatus() {
  statusBox.hidden = true; errorBox.hidden = true; successBox.hidden = true;
  progressFill.style.width = '0%';
}

function setLoading(on) {
  btnGenerate.disabled = on;
  btnLabel.textContent = on ? 'Generating…' : 'Generate My Resume';
  btnArrow.textContent = on ? '⟳' : '→';
  btnArrow.style.animation = on ? 'spin 1s linear infinite' : '';
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

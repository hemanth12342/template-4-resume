/**
 * AI Resume Builder — Frontend (v2 — 4 templates)
 *
 * ⚙️  Set your backend URL here:
 *   Local dev  → 'http://localhost:8000'
 *   Render     → 'https://your-app-name.onrender.com'
 */
const API = 'https://resume-4-njn8.onrender.com';

// ── DOM refs ──────────────────────────────────────────────────────────────────

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const dzIdle = document.getElementById('dz-idle');
const dzDone = document.getElementById('dz-done');
const dzFilename = document.getElementById('dz-filename');
const btnChange = document.getElementById('btn-change');

const jdInput = document.getElementById('jd-input');
const jdChars = document.getElementById('jd-chars');

const btnGenerate = document.getElementById('btn-generate');
const btnLabel = document.getElementById('btn-label');
const btnArrow = document.getElementById('btn-arrow');

const statusBox = document.getElementById('status-box');
const progressFill = document.getElementById('progress-fill');
const statusMsg = document.getElementById('status-msg');

const errorBox = document.getElementById('error-box');
const errorMsg = document.getElementById('error-msg');
const btnRetry = document.getElementById('btn-retry');

const successBox = document.getElementById('success-box');
const btnRedownload = document.getElementById('btn-redownload');

// ── State ─────────────────────────────────────────────────────────────────────

let selectedFile = null;
let selectedTemplate = '4';    // default — Template 4 is pre-checked in HTML
let lastBlob = null;
let lastFilename = 'tailored_resume.pdf';

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
}

// ── JD character count ────────────────────────────────────────────────────────

jdInput.addEventListener('input', () => { jdChars.textContent = jdInput.value.length; });

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

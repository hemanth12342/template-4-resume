/**
 * AI Resume Builder — Frontend v2
 *
 * ⚙️  CONFIGURE THIS BEFORE DEPLOYING
 *   Local dev  → 'http://localhost:8000'
 *   Render     → 'https://your-app-name.onrender.com'
 */
const API = 'https://sai-resume-pnic.onrender.com';

// ── DOM references ────────────────────────────────────────────────────────────

const dropZone      = document.getElementById('drop-zone');
const fileInput     = document.getElementById('file-input');
const dzIdle        = document.getElementById('dz-idle');
const dzDone        = document.getElementById('dz-done');
const dzFilename    = document.getElementById('dz-filename');
const btnChange     = document.getElementById('btn-change');

const jdInput       = document.getElementById('jd-input');
const jdChars       = document.getElementById('jd-chars');

const templateCards = document.querySelectorAll('.template-card');
const chkAll        = document.getElementById('chk-all-templates');
const genNote       = document.getElementById('gen-note');

const btnGenerate   = document.getElementById('btn-generate');
const btnLabel      = document.getElementById('btn-label');
const btnArrow      = document.getElementById('btn-arrow');

const statusBox     = document.getElementById('status-box');
const progressFill  = document.getElementById('progress-fill');
const statusMsg     = document.getElementById('status-msg');

const errorBox      = document.getElementById('error-box');
const errorMsg      = document.getElementById('error-msg');
const btnRetry      = document.getElementById('btn-retry');

const successBox    = document.getElementById('success-box');
const btnRedownload = document.getElementById('btn-redownload');

const successAllBox = document.getElementById('success-all-box');
const btnDlZip      = document.getElementById('btn-dl-zip');
const btnDlT1       = document.getElementById('btn-dl-t1');
const btnDlT2       = document.getElementById('btn-dl-t2');
const btnDlT3       = document.getElementById('btn-dl-t3');
const btnDlT4       = document.getElementById('btn-dl-t4');

// ── State ─────────────────────────────────────────────────────────────────────

let selectedFile      = null;
let lastBlob          = null;         // last single PDF blob
let lastFilename      = 'tailored_resume.pdf';
let selectedTemplate  = 4;           // default to Template 4
let allTemplateMode   = false;

// Store individual blobs when all-4 mode is used
const individualBlobs = { 1: null, 2: null, 3: null, 4: null };
let zipBlob           = null;
let safeName          = 'resume';

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
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

['dragleave', 'dragend'].forEach((ev) =>
  dropZone.addEventListener(ev, () => dropZone.classList.remove('drag-over'))
);

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

btnChange.addEventListener('click', (e) => {
  e.stopPropagation();
  selectedFile = null;
  fileInput.value = '';
  dzIdle.hidden = false;
  dzDone.hidden = true;
  resetStatus();
});

function setFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf', 'txt'].includes(ext)) {
    showError('Please upload a PDF or TXT file.');
    return;
  }
  selectedFile = file;
  dzFilename.textContent = file.name;
  dzIdle.hidden = true;
  dzDone.hidden = false;
  resetStatus();
}

// ── JD character count ────────────────────────────────────────────────────────

jdInput.addEventListener('input', () => {
  jdChars.textContent = jdInput.value.length;
});

// ── Template picker ───────────────────────────────────────────────────────────

templateCards.forEach((card) => {
  card.addEventListener('click', () => selectTemplate(parseInt(card.dataset.tid, 10)));
  card.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      selectTemplate(parseInt(card.dataset.tid, 10));
    }
  });
});

function selectTemplate(tid) {
  // Deselect all
  templateCards.forEach((c) => {
    c.classList.remove('selected');
    c.setAttribute('aria-pressed', 'false');
  });
  // Select chosen
  const card = document.getElementById(`tcard-${tid}`);
  if (card) {
    card.classList.add('selected');
    card.setAttribute('aria-pressed', 'true');
  }
  selectedTemplate = tid;
}

chkAll.addEventListener('change', () => {
  allTemplateMode = chkAll.checked;
  // Toggle visual disabled state on individual cards
  templateCards.forEach((c) => {
    c.classList.toggle('disabled', allTemplateMode);
  });
  // Update generate button label
  if (allTemplateMode) {
    btnLabel.textContent = 'Generate All 4 Templates';
    genNote.textContent  = 'Runs AI once — generates all 4 PDFs (takes ~35–60 s)';
  } else {
    btnLabel.textContent = 'Generate My Resume';
    genNote.textContent  = 'Typically takes 20 – 35 seconds';
  }
  resetStatus();
});

// ── Progress step definitions ─────────────────────────────────────────────────

const STEPS = [
  { pct:  12, msg: '📄  Extracting text from your resume…'            },
  { pct:  30, msg: '🧠  Parsing resume structure with AI…'            },
  { pct:  53, msg: '🎯  Matching your experience to the JD keywords…' },
  { pct:  72, msg: '✨  Enhancing bullet points and summary…'         },
  { pct:  88, msg: '⚙️   Compiling your personalised PDF(s)…'          },
];

// ── Generate ──────────────────────────────────────────────────────────────────

btnGenerate.addEventListener('click',  generate);
btnRetry.addEventListener('click',    () => { resetStatus(); generate(); });

// Single template redownload
btnRedownload.addEventListener('click', () => {
  if (lastBlob) triggerDownload(lastBlob, lastFilename);
});

// All-4 mode download buttons
btnDlZip.addEventListener('click', () => {
  if (zipBlob) triggerDownload(zipBlob, `resume_${safeName}_all_templates.zip`);
});
btnDlT1.addEventListener('click', () => {
  if (individualBlobs[1]) triggerDownload(individualBlobs[1], `resume_${safeName}_Template1_Classic.pdf`);
});
btnDlT2.addEventListener('click', () => {
  if (individualBlobs[2]) triggerDownload(individualBlobs[2], `resume_${safeName}_Template2_Modern.pdf`);
});
btnDlT3.addEventListener('click', () => {
  if (individualBlobs[3]) triggerDownload(individualBlobs[3], `resume_${safeName}_Template3_Sidebar.pdf`);
});
btnDlT4.addEventListener('click', () => {
  if (individualBlobs[4]) triggerDownload(individualBlobs[4], `resume_${safeName}_Template4_ATS.pdf`);
});

async function generate() {
  // Validate
  if (!selectedFile) {
    showError('Please upload your resume first (PDF or TXT).');
    return;
  }
  const jd = jdInput.value.trim();
  if (jd.length < 50) {
    showError('Please paste a more complete job description (at least 50 characters).');
    return;
  }

  // Reset + enter loading state
  resetStatus();
  setLoading(true);
  showStatus('Initialising…', 5);

  // Advance the progress indicator through steps every 5 s
  let step = 0;
  const ticker = setInterval(() => {
    if (step < STEPS.length) {
      showStatus(STEPS[step].msg, STEPS[step].pct);
      step++;
    }
  }, 5000);

  try {
    const form = new FormData();
    form.append('resume_file',    selectedFile);
    form.append('job_description', jd);
    form.append('template_id',    allTemplateMode ? '0' : String(selectedTemplate));

    const res = await fetch(`${API}/generate`, { method: 'POST', body: form });

    clearInterval(ticker);

    if (!res.ok) {
      let detail = `Server error (${res.status})`;
      try { detail = (await res.json()).detail ?? detail; } catch { /* ignore */ }
      throw new Error(detail);
    }

    const contentType = res.headers.get('Content-Type') || '';

    // ── All-4 mode: ZIP response ──────────────────────────────
    if (allTemplateMode || contentType.includes('application/zip')) {
      showStatus('✅  Preparing your download…', 100);

      zipBlob = await res.blob();

      // Derive safe name from Content-Disposition header
      const cd = res.headers.get('Content-Disposition') ?? '';
      const match = cd.match(/filename="?([^";]+)"?/);
      if (match) {
        const fname = match[1].trim();
        safeName = fname.replace(/^resume_(.+)_all_templates\.zip$/, '$1');
      }

      // Extract individual PDFs from the ZIP for per-template download buttons
      await extractZipBlobs(zipBlob);

      triggerDownload(zipBlob, `resume_${safeName}_all_templates.zip`);

      await sleep(700);
      setLoading(false);
      statusBox.hidden     = true;
      successAllBox.hidden = false;

    // ── Single template: PDF response ─────────────────────────
    } else {
      showStatus('✅  Preparing your download…', 100);

      const blob = await res.blob();
      lastBlob = blob;

      const cd = res.headers.get('Content-Disposition') ?? '';
      const match = cd.match(/filename="?([^";]+)"?/);
      if (match) lastFilename = match[1].trim();

      triggerDownload(blob, lastFilename);

      await sleep(700);
      setLoading(false);
      statusBox.hidden  = true;
      successBox.hidden = false;
    }

  } catch (err) {
    clearInterval(ticker);
    setLoading(false);
    showError(err.message || 'Something went wrong. Please try again.');
  }
}

// ── ZIP extraction (browser-side) ────────────────────────────────────────────
// We use the native DecompressionStream API to unzip and extract individual PDFs.
// Falls back gracefully if the API is unavailable.

async function extractZipBlobs(zipBlob) {
  // Store the full zip blob so per-template buttons also have it as fallback
  for (let i = 1; i <= 4; i++) individualBlobs[i] = null;

  try {
    const arrayBuffer = await zipBlob.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);

    // Simple ZIP parser (local file headers only — good enough for our use case)
    let offset = 0;
    const templateLabels = { Classic: 1, Modern: 2, Sidebar: 3, ATS_Classic: 4 };

    while (offset < bytes.length - 4) {
      // Local file header signature: 0x04034b50 (PK\x03\x04)
      if (bytes[offset]     !== 0x50 ||
          bytes[offset + 1] !== 0x4b ||
          bytes[offset + 2] !== 0x03 ||
          bytes[offset + 3] !== 0x04) {
        break;
      }

      const compressionMethod = bytes[offset + 8] | (bytes[offset + 9] << 8);
      const compressedSize    = readUint32LE(bytes, offset + 18);
      const uncompressedSize  = readUint32LE(bytes, offset + 22);
      const filenameLen       = bytes[offset + 26] | (bytes[offset + 27] << 8);
      const extraLen          = bytes[offset + 28] | (bytes[offset + 29] << 8);
      const headerSize        = 30 + filenameLen + extraLen;
      const filenameBytes     = bytes.slice(offset + 30, offset + 30 + filenameLen);
      const filename          = new TextDecoder().decode(filenameBytes);
      const dataOffset        = offset + headerSize;

      // Identify which template this file belongs to
      let tid = null;
      for (const [label, id] of Object.entries(templateLabels)) {
        if (filename.includes(label)) { tid = id; break; }
      }

      if (tid !== null) {
        let pdfBytes;
        if (compressionMethod === 0) {
          // Stored (no compression)
          pdfBytes = bytes.slice(dataOffset, dataOffset + uncompressedSize);
        } else if (compressionMethod === 8 && typeof DecompressionStream !== 'undefined') {
          // Deflate
          const compressed = bytes.slice(dataOffset, dataOffset + compressedSize);
          const ds = new DecompressionStream('deflate-raw');
          const writer = ds.writable.getWriter();
          writer.write(compressed);
          writer.close();
          const chunks = [];
          const reader = ds.readable.getReader();
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            chunks.push(value);
          }
          const totalLen = chunks.reduce((s, c) => s + c.length, 0);
          pdfBytes = new Uint8Array(totalLen);
          let pos = 0;
          for (const chunk of chunks) { pdfBytes.set(chunk, pos); pos += chunk.length; }
        }
        if (pdfBytes) {
          individualBlobs[tid] = new Blob([pdfBytes], { type: 'application/pdf' });
        }
      }

      offset = dataOffset + compressedSize;
    }
  } catch (e) {
    // If extraction fails, individual buttons will fall back to being disabled
    console.warn('ZIP extraction failed:', e);
  }

  // Enable/disable per-template buttons based on whether we got individual blobs
  [btnDlT1, btnDlT2, btnDlT3, btnDlT4].forEach((btn, i) => {
    btn.style.opacity = individualBlobs[i + 1] ? '1' : '0.4';
    btn.disabled      = !individualBlobs[i + 1];
  });
}

function readUint32LE(bytes, offset) {
  return (bytes[offset] | (bytes[offset+1] << 8) |
          (bytes[offset+2] << 16) | (bytes[offset+3] << 24)) >>> 0;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = Object.assign(document.createElement('a'), {
    href:     url,
    download: filename,
  });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 6000);
}

function showStatus(msg, pct) {
  statusBox.hidden   = false;
  errorBox.hidden    = true;
  successBox.hidden  = true;
  successAllBox.hidden = true;
  statusMsg.textContent      = msg;
  progressFill.style.width   = `${pct}%`;
}

function showError(msg) {
  statusBox.hidden     = true;
  successBox.hidden    = true;
  successAllBox.hidden = true;
  errorBox.hidden      = false;
  errorMsg.textContent = msg;
}

function resetStatus() {
  statusBox.hidden            = true;
  errorBox.hidden             = true;
  successBox.hidden           = true;
  successAllBox.hidden        = true;
  progressFill.style.width    = '0%';
}

function setLoading(on) {
  btnGenerate.disabled     = on;
  if (!on) {
    // Restore correct label depending on mode
    btnLabel.textContent = allTemplateMode ? 'Generate All 4 Templates' : 'Generate My Resume';
  } else {
    btnLabel.textContent = 'Generating…';
  }
  btnArrow.textContent     = on ? '⟳' : '→';
  btnArrow.style.animation = on ? 'spin 1s linear infinite' : '';
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

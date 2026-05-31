/* =====================================================================
   Call Analyzer v3 — Soft modern direction
   ===================================================================== */

const EMOTION_HEX = {
  joy:      '#2e9e6b',
  anger:    '#e8634a',
  sadness:  '#4f7cd4',
  fear:     '#8a6fe0',
  surprise: '#e0a341',
  disgust:  '#5aa88f',
  neutral:  '#9aa0ab',
  unknown:  '#9aa0ab',
};
const EMOTION_RANK = { anger:0, disgust:1, fear:2, sadness:3, neutral:4, unknown:4, surprise:5, joy:6 };

const SENTIMENT_LABEL = {
  very_positive: 'Very Positive',
  positive: 'Positive',
  neutral: 'Neutral',
  negative: 'Negative',
  very_negative: 'Very Negative',
  mixed: 'Mixed',
};

const API_BASE = (localStorage.getItem('conviqApiBase') ||
  (window.location.protocol.startsWith('http') && window.location.port === '8000'
    ? ''
    : 'http://localhost:8000')).replace(/\/$/, '');
const AUTO_DOMAIN_ID = 'auto';

/* ----------------------------- icons (line) ----------------------------- */
const I = {
  upload: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
  audio: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h2l2-8 4 16 4-12 2 6h4"/></svg>',
  download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
  plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
  close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
  sliders: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><line x1="4" y1="7" x2="20" y2="7"/><circle cx="10" cy="7" r="2.2" fill="var(--card)"/><line x1="4" y1="12" x2="20" y2="12"/><circle cx="16" cy="12" r="2.2" fill="var(--card)"/><line x1="4" y1="17" x2="20" y2="17"/><circle cx="8" cy="17" r="2.2" fill="var(--card)"/></svg>',
  help: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.5-2.5 2-2.5 3.5"/><circle cx="12" cy="17" r=".6" fill="currentColor"/></svg>',
};

/* ------------------------- section nav icons ------------------------- */
const NAV_ICONS = {
  overview:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/></svg>',
  transcript:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="13" y2="17"/></svg>',
  summary:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="13" y2="17"/></svg>',
  sentiment:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l2.5-7 4.5 14 2.5-7H21"/></svg>',
  emotions:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8.5 14.5s1.4 1.8 3.5 1.8 3.5-1.8 3.5-1.8"/><line x1="9" y1="9.5" x2="9.01" y2="9.5"/><line x1="15" y1="9.5" x2="15.01" y2="9.5"/></svg>',
  keywords:    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="10" y1="3" x2="8" y2="21"/><line x1="16" y1="3" x2="14" y2="21"/></svg>',
  suggestions: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.3h6c0-1 .4-1.8 1-2.3A7 7 0 0 0 12 2z"/></svg>',
  charts:      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="20" x2="20" y2="20"/><rect x="6" y="10" width="3" height="7" rx="1"/><rect x="11" y="6" width="3" height="11" rx="1"/><rect x="16" y="13" width="3" height="4" rx="1"/></svg>',
};

/* ----------------------------- state ----------------------------- */
const App = {
  state: 'upload',
  file: null,
  data: null,
  callId: null,
  stream: null,
  pollTimer: null,
  section: 'overview',
  charts: {},
};

/* ============================================================
   Bootstrap
   ============================================================ */
window.addEventListener('DOMContentLoaded', () => {
  buildShell();
  renderTopbar();
  renderSidebar();
  renderPanel();
  bindKeyboard();
  bindTweaks();
});

function buildShell() {
  document.body.innerHTML = `
    <div class="app">
      <div class="topbar" id="topbar"></div>
      <div class="main">
        <aside class="sidebar" id="sidebar"></aside>
        <main class="panel" id="panel"></main>
      </div>
    </div>
    <div class="tweaks" id="tweaks">
      <div class="tweaks-head">
        <span class="title">Tweak <em>the look</em></span>
        <button class="close" id="tweaks-close">${I.close}</button>
      </div>
      <div class="tweaks-body" id="tweaks-body"></div>
    </div>
    <div class="toast" id="toast"></div>
  `;
}

/* ============================================================
   Topbar
   ============================================================ */
function renderTopbar() {
  const tb = document.getElementById('topbar');
  const stateText = { upload: 'New session', processing: 'Listening', results: 'Analyzed' }[App.state];
  const stateCls  = { upload: 'idle', processing: 'busy', results: 'ready' }[App.state];

  const crumbs = (() => {
    if (App.state === 'upload') return '<span>Sessions</span><span class="sep">/</span><span class="current">New</span>';
    if (App.state === 'processing') return `<span>Sessions</span><span class="sep">/</span><span>${escapeHtml(App.file?.name || '')}</span><span class="sep">/</span><span class="current">Processing</span>`;
    return `<span>Sessions</span><span class="sep">/</span><span>${escapeHtml(App.file?.name || 'mock-call.mp3')}</span><span class="sep">/</span><span class="current">Analysis</span>`;
  })();

  tb.innerHTML = `
    <div class="brand">
      <span class="brand-glyph"></span>
      <span class="brand-name">Call <span class="ital">Analyzer</span></span>
      <span class="brand-version">v2.1.0</span>
    </div>
    <div class="crumbs">${crumbs}</div>
    <div class="topbar-spacer"></div>
    <span class="status-pill ${stateCls}"><span class="dot"></span>${stateText}</span>
    <div class="topbar-actions">
      <button class="icon-btn" id="tweaks-toggle" title="Tweaks">${I.sliders}</button>
      <button class="icon-btn" title="Help">${I.help}</button>
    </div>
  `;
  document.getElementById('tweaks-toggle').onclick = () =>
    document.getElementById('tweaks').classList.toggle('open');
}

/* ============================================================
   Sidebar
   ============================================================ */
function renderNav(sections, isResults) {
  const mode = TWEAKS.nav || 'grouped';
  const item = (s, i) => {
    const active = App.section === s.id ? 'active' : '';
    const disabled = isResults ? '' : 'disabled';
    const lead = mode === 'numbered'
      ? `<span class="nav-num">${String(i + 1).padStart(2, '0')}</span>`
      : `<span class="nav-ico">${NAV_ICONS[s.icon]}</span>`;
    const count = s.count != null ? `<span class="nav-count">${s.count}</span>` : '<span></span>';
    return `<button class="nav-item ${active}" data-section="${s.id}" ${disabled}>${lead}<span class="nav-lab">${s.label}</span>${count}</button>`;
  };

  if (mode === 'grouped') {
    const groups = [];
    sections.forEach(s => {
      let group = groups.find(x => x.name === s.group);
      if (!group) {
        group = { name: s.group, items: [] };
        groups.push(group);
      }
      group.items.push(s);
    });
    return groups.map(group => `
      <div class="nav-group">
        <div class="nav-group-label">${group.name}</div>
        <div class="nav">${group.items.map(s => item(s, sections.indexOf(s))).join('')}</div>
      </div>
    `).join('');
  }

  return `
    <div class="sb-label">Sections</div>
    <div class="nav">${sections.map((s, i) => item(s, i)).join('')}</div>
  `;
}

function renderSidebar() {
  const sb = document.getElementById('sidebar');
  const isResults = App.state === 'results';
  const turnCount = isResults ? App.data.diarized_turns.length : 0;
  const kwCount = isResults ? App.data.keywords.keywords.length : 0;
  const sugCount = isResults ? parseSuggestions(App.data.suggestion).length : 0;

  const sections = [
    { id: 'overview',    label: 'Overview',    icon: 'overview',    group: 'Read' },
    { id: 'transcript',  label: 'Transcript',  icon: 'transcript',  group: 'Read', count: turnCount },
    { id: 'summary',     label: 'Summary',     icon: 'summary',     group: 'Read' },
    { id: 'sentiment',   label: 'Sentiment',   icon: 'sentiment',   group: 'Analyze' },
    { id: 'emotions',    label: 'Emotions',    icon: 'emotions',    group: 'Analyze' },
    { id: 'keywords',    label: 'Keywords',    icon: 'keywords',    group: 'Analyze', count: kwCount },
    { id: 'suggestions', label: 'Suggestions', icon: 'suggestions', group: 'Act on it', count: sugCount },
    { id: 'charts',      label: 'Charts',      icon: 'charts',      group: 'Act on it' },
  ];

  let fileBlock = '';
  if (App.file) {
    const dur = isResults ? formatDuration(getDuration(App.data)) : null;
    fileBlock = `
      <div class="file-card">
        <div class="filename" title="${escapeHtml(App.file.name)}">${escapeHtml(App.file.name)}</div>
        <div class="file-meta">
          <span><b>${formatSize(App.file.size)}</b></span>
          <span class="sep">·</span>
          <span>${(App.file.type && App.file.type.split('/')[1]?.toUpperCase()) || 'AUDIO'}</span>
          ${dur ? `<span class="sep">·</span><span><b>${dur}</b></span>` : ''}
        </div>
      </div>
    `;
  }

  sb.innerHTML = `
    ${fileBlock || `
      <div class="sb-section">
        <div class="sb-label">Session</div>
        <div style="padding:4px 8px;font-family:var(--sans);font-size:13.5px;color:var(--ink-3)">No recording yet</div>
      </div>
    `}

    <div class="sb-section" style="padding-top: 6px;">
      ${renderNav(sections, isResults)}
    </div>

    <div class="sb-spacer"></div>

    <div class="sb-footer">
      <button class="btn btn-ghost btn-block" id="btn-new" ${App.state === 'upload' ? 'disabled' : ''}>
        ${I.plus}<span>New session</span>
      </button>
      <button class="btn btn-secondary btn-block" id="btn-export" ${isResults ? '' : 'disabled'}>
        ${I.download}<span>Export report</span>
      </button>
    </div>
  `;

  sb.querySelectorAll('[data-section]').forEach(el => {
    el.onclick = () => {
      if (App.state !== 'results') return;
      App.section = el.dataset.section;
      renderSidebar();
      renderPanel();
    };
  });
  const newBtn = document.getElementById('btn-new');
  if (newBtn) newBtn.onclick = resetToUpload;
  const expBtn = document.getElementById('btn-export');
  if (expBtn) expBtn.onclick = mockExport;
}

/* ============================================================
   Panel router
   ============================================================ */
function renderPanel() {
  const panel = document.getElementById('panel');
  panel.scrollTo({ top: 0 });

  if (App.state === 'upload')     return renderUpload(panel);
  if (App.state === 'processing') return renderProcessing(panel);

  panel.innerHTML = '';
  const fns = {
    overview:    renderOverview,
    transcript:  renderTranscript,
    summary:     renderSummary,
    sentiment:   renderSentiment,
    emotions:    renderEmotions,
    keywords:    renderKeywords,
    suggestions: renderSuggestions,
    charts:      renderCharts,
  };
  (fns[App.section] || renderOverview)(panel);
}

/* ============================================================
   STATE 1 — Upload
   ============================================================ */
function renderUpload(panel) {
  panel.innerHTML = `
    <div class="upload-stage fadein">

      <div class="upload-hero">
        <div class="hero-eyebrow">
          <span>New analysis</span>
          <span class="meta">·  Live pipeline</span>
        </div>
        <h1 class="hero-title">
          Hear what the<br>
          <span class="ital">conversation</span><br>
          <span class="underline">was really</span> saying.
        </h1>
        <p class="hero-lede">
          Upload a conversation. We'll transcribe it, identify the call type, separate speakers, score sentiment and emotion across every turn, and surface the moments that mattered.
        </p>

        <div class="hero-feats">
          <div class="hero-feat">
            <div class="num">7</div>
            <div class="label-text">Emotion labels across every turn</div>
          </div>
          <div class="hero-feat">
            <div class="num">2</div>
            <div class="label-text">Speaker diarization with timestamps</div>
          </div>
          <div class="hero-feat">
            <div class="num">0</div>
            <div class="label-text">Ungrounded suggestions in Phase 2</div>
          </div>
        </div>
      </div>

      <div class="upload-col">
        <div class="eyebrow" style="margin-bottom:18px">Step one</div>

        <label class="dropzone" id="dropzone" for="file-input">
          <div class="dropzone-icon">${I.upload}</div>
          <div class="dropzone-text">Drop a recording <b>here</b></div>
          <div class="dropzone-hint">or click to browse · up to 100 MB</div>
          <input type="file" id="file-input" accept="audio/*" style="display:none">
        </label>

        <div id="selected-file" class="hidden"></div>

        <div class="upload-actions">
          <div class="upload-shortcuts">
            <span><span class="kbd">⌘U</span> Browse</span>
            <span><span class="kbd">⌘↵</span> Submit</span>
          </div>
          <button class="btn btn-primary btn-lg" id="btn-submit" disabled>
            <span>Start analysis</span>
            ${I.arrow}
          </button>
        </div>

        <div class="formats">
          <span class="label">Accepts</span>
          <span class="formats-list">MP3<span>·</span>M4A<span>·</span>FLAC<span>·</span>OGG<span>·</span>AAC</span>
        </div>
      </div>

    </div>
  `;

  const dz = document.getElementById('dropzone');
  const input = document.getElementById('file-input');
  const submit = document.getElementById('btn-submit');

  input.onchange = e => { const f = e.target.files[0]; if (f) selectFile(f); };
  ['dragenter','dragover'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('drag'); }));
  ['dragleave','drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('drag'); }));
  dz.addEventListener('drop', e => { const f = e.dataTransfer.files[0]; if (f) selectFile(f); });
  submit.onclick = () => startProcessing();
}

function selectFile(f) {
  App.file = f;
  const sel = document.getElementById('selected-file');
  if (!sel) return;
  sel.classList.remove('hidden');
  sel.innerHTML = `
    <div class="upload-selected">
      <div class="file-icon">${I.audio}</div>
      <div class="meta">
        <div class="name">${escapeHtml(f.name)}</div>
        <div class="size">${formatSize(f.size)} · ${f.type || 'audio/unknown'}</div>
      </div>
      <button id="clear-file" title="Remove">${I.close}</button>
    </div>
  `;
  document.getElementById('clear-file').onclick = () => {
    App.file = null;
    sel.classList.add('hidden');
    document.getElementById('btn-submit').disabled = true;
    document.getElementById('file-input').value = '';
  };
  document.getElementById('btn-submit').disabled = false;
}

/* ============================================================
   STATE 2 — Processing
   ============================================================ */
function renderProcessing(panel) {
  const steps = [
    { name: 'Uploading',    desc: 'Sending audio' },
    { name: 'Transcribing', desc: 'Whisper ASR' },
    { name: 'Diarizing',    desc: 'Speaker turns' },
    { name: 'Analyzing',    desc: 'Emotions · keywords' },
    { name: 'Enriching',    desc: 'Summary · sentiment' },
    { name: 'Composing',    desc: 'Report view' },
  ];

  panel.innerHTML = `
    <div class="processing-stage fadein">
      <div class="processing-card">

        <div class="proc-glyph">
          <svg viewBox="0 0 88 88">
            <circle class="ring" cx="44" cy="44" r="38" stroke-dasharray="80 160"/>
            <circle class="ring ring-2" cx="44" cy="44" r="26" stroke-dasharray="40 120"/>
            <circle cx="44" cy="44" r="4" fill="var(--accent)"/>
          </svg>
        </div>

        <div class="proc-eyebrow">Listening</div>
        <h2 class="title">Reading <span class="ital">between the lines</span></h2>
        <div class="status-line"><span id="proc-status-text">Uploading audio</span><span class="caret"></span></div>

        <div class="progress-track"><div class="progress-fill" id="proc-fill"></div></div>

        <div class="steps">
          ${steps.map((s, i) => `
            <div class="step" data-step="${i}">
              <div class="step-num">0${i+1}</div>
              <div class="step-name">${s.name}</div>
              <div class="step-desc">${s.desc}</div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

async function startProcessing(options = {}) {
  App.state = 'processing';
  App.callId = null;
  clearRuntimeWatchers();
  renderTopbar(); renderSidebar(); renderPanel();

  if (options.demo) return simulateProcessing();

  try {
    if (!App.file) throw new Error('Choose an audio file first.');

    setProcessingStage(0, 'Uploading audio', 8);
    const form = new FormData();
    form.append('audio', App.file);
    form.append('domain_id', AUTO_DOMAIN_ID);

    const queued = await apiFetch('/calls', { method: 'POST', body: form });
    App.callId = queued.id;
    setProcessingStage(0, 'Upload accepted', 18);
    await waitForResult(queued);
  } catch (error) {
    failProcessing(error);
  }
}

function simulateProcessing() {
  const stepLabels = ['Uploading audio', 'Transcribing speech', 'Finding speaker turns', 'Extracting analytics', 'Analyzing sentiment', 'Drafting report'];
  const stepDurations = [500, 1400, 1000, 900, 1300, 700];
  const total = stepDurations.reduce((a, b) => a + b, 0);
  let elapsed = 0, idx = 0;

  const advance = () => {
    if (idx >= stepLabels.length) return finishProcessing(enrichMockData(window.MOCK_RESPONSE));
    setProcessingStage(idx, stepLabels[idx], (elapsed / total) * 100);
    const t0 = Date.now();
    const stepStart = elapsed;
    const int = setInterval(() => {
      const dt = Date.now() - t0;
      const p = Math.min(1, dt / stepDurations[idx]);
      const tp = (stepStart + stepDurations[idx] * p) / total;
      setProgress(tp * 100);
      if (p >= 1) {
        clearInterval(int);
        elapsed += stepDurations[idx];
        idx++;
        setTimeout(advance, 60);
      }
    }, 40);
  };
  advance();
}

function finishProcessing(data) {
  document.querySelectorAll('.step').forEach(el => { el.classList.remove('active'); el.classList.add('done'); });
  const status = document.getElementById('proc-status-text');
  if (status) status.textContent = 'Complete';
  setProgress(100);
  setTimeout(() => {
    App.data = data;
    App.state = 'results';
    App.section = 'overview';
    renderTopbar(); renderSidebar(); renderPanel();
  }, 500);
}

function setProcessingStage(stepIndex, text, progress) {
  document.querySelectorAll('.step').forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i < stepIndex) el.classList.add('done');
    if (i === stepIndex) el.classList.add('active');
  });
  const status = document.getElementById('proc-status-text');
  if (status) status.textContent = text;
  setProgress(progress);
}

function setProgress(value) {
  const fill = document.getElementById('proc-fill');
  if (fill) fill.style.width = `${Math.max(0, Math.min(100, value))}%`;
}

async function waitForResult(queued) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const settle = (fn, value) => {
      if (settled) return;
      settled = true;
      clearRuntimeWatchers();
      fn(value);
    };

    const fetchFinal = async () => {
      const call = await apiFetch(`/calls/${queued.id}`);
      if (call.status === 'failed') throw new Error(call.error_message || 'Analysis failed.');
      if (call.status !== 'completed') return null;
      return normalizeApiCall(call);
    };

    const poll = () => {
      App.pollTimer = window.setInterval(async () => {
        try {
          const data = await fetchFinal();
          if (data) {
            finishProcessing(data);
            settle(resolve);
          }
        } catch (error) {
          settle(reject, error);
        }
      }, 2200);
    };

    try {
      App.stream = new EventSource(apiUrl(queued.stream_url));
      App.stream.addEventListener('status', event => updateProgressFromPayload(readEventData(event)));
      App.stream.addEventListener('progress', event => updateProgressFromPayload(readEventData(event)));
      App.stream.addEventListener('complete', async event => {
        updateProgressFromPayload(readEventData(event));
        try {
          const data = await fetchFinal();
          finishProcessing(data || normalizeApiCall(await apiFetch(`/calls/${queued.id}`)));
          settle(resolve);
        } catch (error) {
          settle(reject, error);
        }
      });
      App.stream.addEventListener('error', event => {
        const payload = readEventData(event);
        if (payload?.status === 'failed' || payload?.stage === 'error') {
          settle(reject, new Error(payload.detail || 'Analysis failed.'));
          return;
        }
        if (!App.pollTimer) poll();
      });
      poll();
    } catch (error) {
      poll();
    }
  });
}

function updateProgressFromPayload(payload) {
  if (!payload) return;
  const stage = payload.stage || payload.status || '';
  const detail = payload.detail || stage;
  const map = {
    queued: [0, 'Pipeline queued', 16],
    transcribe: [1, detail || 'Transcribing speech', 34],
    diarize: [2, detail || 'Finding speaker turns', 50],
    analytics: [3, detail || 'Extracting analytics', 66],
    summarize: [4, detail || 'Summarizing conversation', 78],
    sentiment: [4, detail || 'Analyzing sentiment', 88],
    complete: [5, 'Complete', 100],
    completed: [5, 'Complete', 100],
  };
  const current = map[stage] || [1, detail || 'Processing', 35];
  setProcessingStage(current[0], current[1], current[2]);
}

function readEventData(event) {
  try {
    return event?.data ? JSON.parse(event.data) : null;
  } catch {
    return null;
  }
}

function failProcessing(error) {
  const message = error?.message || 'Analysis failed.';
  const status = document.getElementById('proc-status-text');
  if (status) status.textContent = message;
  showToast(message);
  setTimeout(resetToUpload, 1800);
}

function clearRuntimeWatchers() {
  if (App.stream) {
    App.stream.close();
    App.stream = null;
  }
  if (App.pollTimer) {
    clearInterval(App.pollTimer);
    App.pollTimer = null;
  }
}

function enrichMockData(d) {
  d.emotions.emotion_timeline = d.diarized_turns.map(t => ({
    speaker: t.speaker, start: t.start,
    emotion: t.emotion.primary_emotion,
    confidence: t.emotion.confidence,
  }));
  return d;
}

function normalizeApiCall(call) {
  const transcript = (call.transcript || '').trim();
  const duration = Number(call.duration_seconds || 0);
  const words = transcript ? transcript.split(/\s+/).filter(Boolean).length : 0;
  const turns = (call.turns || []).length
    ? call.turns.map((turn, index) => normalizeTurn(turn, index))
    : [normalizeTurn({
        speaker: 'Conversation',
        text: transcript || 'Transcript is not available yet.',
        start_seconds: 0,
        end_seconds: duration || Math.max(1, Math.round(words / 2.4)),
        emotion: call.dominant_emotion || 'unknown',
        emotion_confidence: 0,
      }, 0)];

  const emotionDistribution = normalizeEmotionDistribution(
    call.emotion_distribution_json,
    turns,
    call.dominant_emotion
  );
  const dominantEmotion = call.dominant_emotion && call.dominant_emotion in EMOTION_HEX
    ? call.dominant_emotion
    : topEmotion(emotionDistribution);
  const sentimentLabel = call.sentiment_label || sentimentFromCompound(call.sentiment_compound);
  const sentimentScores = sentimentScoresFromCompound(call.sentiment_compound);
  const keywords = normalizeKeywords(call.keywords_json);
  const suggestions = normalizeSuggestions(call.suggestions_json);

  return {
    id: call.id,
    transcript,
    language: call.language || 'en',
    formatted_transcript: transcript,
    diarized_turns: turns,
    summary: call.summary || 'Summary is not available yet.',
    sentiment: {
      gemini_analysis: call.sentiment_label
        ? `The pipeline classified the overall call sentiment as ${sentimentLabel.replace(/_/g, ' ')}.`
        : 'Sentiment narrative is not available yet.',
      detailed_scores: {
        vader_scores: sentimentScores,
        sentiment_label: sentimentLabel,
        confidence: call.sentiment_compound == null ? 'low' : 'medium',
        emotional_indicators: [dominantEmotion, sentimentLabel].filter(Boolean),
        text_stats: {
          word_count: words,
          char_count: transcript.length,
        },
        summary: `${sentimentDisplay(sentimentLabel)} sentiment detected.`,
      },
    },
    emotions: {
      dominant_emotion: dominantEmotion,
      emotion_distribution: emotionDistribution,
      emotion_timeline: turns.map(t => ({
        speaker: t.speaker,
        start: t.start,
        emotion: t.emotion.primary_emotion,
        confidence: t.emotion.confidence,
      })),
    },
    keywords: {
      method: call.keywords_json ? 'pipeline' : 'unavailable',
      keywords,
      top_keywords: keywords.slice(0, 5).map(k => k.keyword),
    },
    suggestions_available: suggestions.length > 0,
    suggestion: suggestions.length
      ? suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n')
      : '',
  };
}

function normalizeTurn(turn, index) {
  const emotionValue = typeof turn.emotion === 'object'
    ? turn.emotion?.primary_emotion
    : turn.emotion;
  const rawEmotion = emotionValue || 'unknown';
  const emotion = rawEmotion in EMOTION_HEX ? rawEmotion : 'unknown';
  return {
    speaker: turn.speaker || (index % 2 === 0 ? 'Speaker 1' : 'Speaker 2'),
    text: turn.text || '',
    start: Number(turn.start_seconds ?? turn.start ?? 0),
    end: Number(turn.end_seconds ?? turn.end ?? turn.start_seconds ?? 0),
    emotion: {
      primary_emotion: emotion,
      confidence: Number(turn.emotion_confidence ?? turn.emotion?.confidence ?? 0),
    },
    dialogue_act: turn.dialogue_act || null,
    dialogue_act_confidence: Number(turn.dialogue_act_confidence ?? 0),
  };
}

function normalizeEmotionDistribution(raw, turns, fallback) {
  const dist = {};
  Object.keys(EMOTION_HEX).forEach(e => { dist[e] = 0; });
  const hasRawValues = raw && typeof raw === 'object' && Object.values(raw).some(v => Number(v) > 0);
  if (hasRawValues) {
    Object.entries(raw).forEach(([k, v]) => {
      if (k in dist) dist[k] = Math.max(0, Number(v) || 0);
    });
  } else {
    turns.forEach(t => { dist[t.emotion.primary_emotion] = (dist[t.emotion.primary_emotion] || 0) + 1; });
  }
  if (Object.values(dist).every(v => v === 0)) {
    dist[fallback && fallback in dist ? fallback : 'neutral'] = 1;
  }
  const total = Object.values(dist).reduce((a, b) => a + b, 0) || 1;
  Object.keys(dist).forEach(k => { dist[k] = dist[k] / total; });
  return dist;
}

function topEmotion(dist) {
  return Object.entries(dist).sort((a, b) => b[1] - a[1])[0]?.[0] || 'neutral';
}

function sentimentFromCompound(compound) {
  const c = Number(compound || 0);
  if (c >= 0.5) return 'very_positive';
  if (c >= 0.1) return 'positive';
  if (c > -0.1) return 'neutral';
  if (c > -0.5) return 'negative';
  return 'very_negative';
}

function sentimentDisplay(label) {
  return SENTIMENT_LABEL[label] || String(label || 'neutral')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

function speakerClass(speaker) {
  return String(speaker || 'speaker')
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'speaker';
}

function sentimentScoresFromCompound(compound) {
  const c = Math.max(-1, Math.min(1, Number(compound || 0)));
  const positive = Math.max(0, c) * 0.7;
  const negative = Math.max(0, -c) * 0.7;
  const neutral = Math.max(0.1, 1 - positive - negative);
  const total = positive + negative + neutral;
  return {
    positive: positive / total,
    negative: negative / total,
    neutral: neutral / total,
    compound: c,
  };
}

function normalizeKeywords(raw) {
  const items = Array.isArray(raw) ? raw : (Array.isArray(raw?.keywords) ? raw.keywords : []);
  if (items.length) {
    return items.map((item, i) => {
      if (typeof item === 'string') return { keyword: item, score: Math.max(0.2, 1 - i * 0.06) };
      return {
        keyword: item.keyword || item.term || `keyword ${i + 1}`,
        score: Number(item.score ?? item.relevance ?? Math.max(0.2, 1 - i * 0.06)),
      };
    });
  }
  return [];
}

function normalizeSuggestions(raw) {
  if (Array.isArray(raw)) {
    return raw.map(item => typeof item === 'string' ? item : (item.text || item.suggestion || '')).filter(Boolean);
  }
  return [];
}

function resetToUpload() {
  clearRuntimeWatchers();
  App.state = 'upload'; App.file = null; App.data = null; App.section = 'overview';
  App.callId = null;
  Object.values(App.charts).forEach(c => c?.destroy?.());
  App.charts = {};
  renderTopbar(); renderSidebar(); renderPanel();
}

/* ============================================================
   STATE 3 — Results sections
   ============================================================ */

function panelHead(eyebrow, title, subtitle, actions = '') {
  return `
    <div class="panel-header">
      <div class="eyebrow"><span class="dot"></span>${eyebrow}</div>
      <h1 class="panel-title">${title}</h1>
      ${subtitle ? `<div class="panel-subtitle">${subtitle}</div>` : ''}
      ${actions ? `<div class="panel-header-actions">${actions}</div>` : ''}
    </div>
  `;
}

/* ---------- Overview ---------- */
function renderOverview(panel) {
  const d = App.data;
  const turns = d.diarized_turns;
  const duration = turns.at(-1).end;
  const wc = d.sentiment.detailed_scores.text_stats.word_count;
  const dom = d.emotions.dominant_emotion;
  const domPct = Math.round((d.emotions.emotion_distribution[dom] || 0) * 100);
  const domColor = EMOTION_HEX[dom] || EMOTION_HEX.unknown;
  const ss = d.sentiment.detailed_scores.vader_scores;
  const sentLabel = d.sentiment.detailed_scores.sentiment_label;
  const sentText = sentimentDisplay(sentLabel);

  const distEntries = Object.entries(d.emotions.emotion_distribution)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1]);

  panel.innerHTML = panelHead(
    'Section 01 · Overview',
    `A <span class="ital">${sentText.toLowerCase()}</span> session.`,
    `${turns.length} speaker turns across ${formatDuration(duration)} — dominant tone <b>${dom}</b>, overall read <b>${sentText.toLowerCase()}</b>.`
  ) + `
    <div class="panel-body fadein">

      <div class="kpi-strip">
        <div class="kpi">
          <div class="kpi-label">Duration</div>
          <div class="kpi-value">${formatDuration(duration)}<span class="unit">min</span></div>
          <div class="kpi-sub">${turns.length} turns</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Sentiment</div>
          <div class="kpi-value"><span class="ital accent">${sentText}</span></div>
          <div class="kpi-sub"><span class="swatch" style="background:var(--pos)"></span>compound ${ss.compound >= 0 ? '+' : ''}${ss.compound.toFixed(2)}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Dominant emotion</div>
          <div class="kpi-value" style="text-transform:capitalize">${dom}</div>
          <div class="kpi-sub"><span class="swatch" style="background:${domColor}"></span>${domPct}% of turns</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Words spoken</div>
          <div class="kpi-value">${wc.toLocaleString()}</div>
          <div class="kpi-sub">${(wc/(duration/60)).toFixed(0)} wpm avg</div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">i.</span><span class="title">The shape of feeling</span><span class="rule"></span>
      </div>

      <div class="row-split">
        <div class="card">
          <div class="card-header">
            <div class="card-title">Emotion <span class="ital">distribution</span></div>
            <span class="card-tag">across 7 labels</span>
          </div>
          <div class="card-body">
            <div class="dist">
              ${distEntries.map(([e, v]) => `
                <div class="dist-row">
                  <div class="dist-label"><span class="swatch" style="background:${EMOTION_HEX[e]}"></span><span>${e}</span></div>
                  <div class="dist-bar"><div class="dist-fill" style="width:${(v*100).toFixed(1)}%;background:${EMOTION_HEX[e]}"></div></div>
                  <div class="dist-value">${(v*100).toFixed(1)}%</div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Sentiment <span class="ital">polarity</span></div>
            <span class="card-tag">vader</span>
          </div>
          <div class="card-body">
            <div class="dist">
              ${[
                ['Positive', ss.positive, 'var(--pos)'],
                ['Neutral',  ss.neutral,  'var(--neu)'],
                ['Negative', ss.negative, 'var(--neg)'],
              ].map(([l, v, c]) => `
                <div class="dist-row">
                  <div class="dist-label"><span class="swatch" style="background:${c}"></span><span>${l}</span></div>
                  <div class="dist-bar"><div class="dist-fill" style="width:${(v*100).toFixed(1)}%;background:${c}"></div></div>
                  <div class="dist-value">${(v*100).toFixed(1)}%</div>
                </div>
              `).join('')}
            </div>
            <div class="compound">
              <div class="head">
                <span class="l">Compound score</span>
                <span class="v">${ss.compound >= 0 ? '+' : ''}${ss.compound.toFixed(3)}</span>
              </div>
              <div class="gauge-track">
                <div class="gauge-marker" style="left:${((ss.compound + 1) / 2) * 100}%"></div>
              </div>
              <div class="gauge-scale"><span>−1.0</span><span>0</span><span>+1.0</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">ii.</span><span class="title">What the call was about</span><span class="rule"></span>
      </div>

      <div class="card">
        <div class="card-header">
          <div class="card-title">Top <span class="ital">keywords</span></div>
          <span class="card-tag">${d.keywords.method}</span>
        </div>
        <div class="card-body">
          <div class="keyword-cloud">
            ${d.keywords.keywords.length ? d.keywords.keywords.slice(0, 10).map((k, i) => {
              const size = 22 + Math.round(k.score * 18);
              const italic = i % 3 === 1 ? 'italic' : '';
              return `<span class="kw ${italic}" style="font-size:${size}px">${escapeHtml(k.keyword)}</span>`;
            }).join('') : '<div class="empty-state">No keywords were persisted for this call.</div>'}
          </div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">iii.</span><span class="title">In one breath</span><span class="rule"></span>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="narrative">${escapeHtml(d.summary)}</div>
        </div>
      </div>

    </div>
  `;
}

/* ---------- Transcript ---------- */
function renderTranscript(panel) {
  const d = App.data;
  const turns = d.diarized_turns;
  const emos = [...new Set(turns.map(t => t.emotion.primary_emotion))];

  panel.innerHTML = panelHead(
    'Section 02 · Transcript',
    `In <span class="ital">their</span> words.`,
    `Diarized turn-by-turn — each line annotated with the emotion model's read on tone and confidence.`,
    `<button class="btn btn-secondary">${I.download}<span>Copy</span></button>`
  ) + `
    <div class="panel-body fadein">

      <div class="transcript-stats">
        <div class="stat">
          <div class="v">${turns.length}</div>
          <div class="l">Turns</div>
        </div>
        <div class="stat">
          <div class="v">${formatDuration(turns.at(-1).end)}</div>
          <div class="l">Duration</div>
        </div>
        <div class="stat">
          <div class="v">${d.sentiment.detailed_scores.text_stats.word_count}</div>
          <div class="l">Words</div>
        </div>
        <div class="transcript-legend">
          ${emos.map(e => `<span class="legend-chip"><span class="d" style="background:${EMOTION_HEX[e]}"></span>${e}</span>`).join('')}
        </div>
      </div>

      <div class="transcript">
        ${turns.map((t, i) => {
          const cls = speakerClass(t.speaker);
          const ec = EMOTION_HEX[t.emotion.primary_emotion];
          return `
            <div class="turn ${cls}">
              <div class="turn-gutter">
                <span class="turn-time">${formatTime(t.start)}</span>
                <span class="turn-num">${String(i+1).padStart(2,'0')}</span>
              </div>
              <div class="turn-content">
                <div class="turn-speaker-row">
                  <span class="turn-speaker ${cls}">${t.speaker}</span>
                  <span class="turn-emotion" style="background:${hexA(ec, 0.14)};color:${ec}">
                    <span class="d" style="background:${ec}"></span>
                    ${t.emotion.primary_emotion}
                    <span class="c">${Math.round(t.emotion.confidence*100)}%</span>
                  </span>
                  ${t.dialogue_act ? `
                    <span class="turn-act">
                      ${escapeHtml(t.dialogue_act)}
                      ${t.dialogue_act_confidence ? `<span class="c">${Math.round(t.dialogue_act_confidence*100)}%</span>` : ''}
                    </span>
                  ` : ''}
                </div>
                <div class="turn-text">${escapeHtml(t.text)}</div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

/* ---------- Summary ---------- */
function renderSummary(panel) {
  const d = App.data;
  const s = d.summary;
  const speakers = [...new Set(d.diarized_turns.map(t => t.speaker).filter(Boolean))];
  const speakerLabel = speakers.length ? speakers.join(' · ') : 'detected speakers';

  panel.innerHTML = panelHead(
    'Section 03 · Summary',
    `What <span class="ital">happened</span> here.`,
    `An AI-generated narrative summary of the session, plus surface-level stats.`
  ) + `
    <div class="panel-body fadein" style="max-width:840px">

      <div class="card">
        <div class="card-body">
          <p class="summary-pull">${escapeHtml(s)}</p>
        </div>
      </div>

      <div class="section-band">
        <span class="num">i.</span><span class="title">By the numbers</span><span class="rule"></span>
      </div>

      <div class="kpi-strip">
        <div class="kpi">
          <div class="kpi-label">Words</div>
          <div class="kpi-value">${d.sentiment.detailed_scores.text_stats.word_count.toLocaleString()}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Characters</div>
          <div class="kpi-value">${d.sentiment.detailed_scores.text_stats.char_count.toLocaleString()}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Language</div>
          <div class="kpi-value">${d.language.toUpperCase()}</div>
        </div>
        <div class="kpi">
          <div class="kpi-label">Speakers</div>
          <div class="kpi-value">${speakers.length || 1}</div>
          <div class="kpi-sub">${escapeHtml(speakerLabel)}</div>
        </div>
      </div>

    </div>
  `;
}

/* ---------- Sentiment ---------- */
function renderSentiment(panel) {
  const d = App.data;
  const s = d.sentiment.detailed_scores;
  const ss = s.vader_scores;

  panel.innerHTML = panelHead(
    'Section 04 · Sentiment',
    `The <span class="ital">arc</span> of tone.`,
    `Polarity scores from VADER plus a qualitative read from Gemini on how the conversation moved.`
  ) + `
    <div class="panel-body fadein" style="max-width:920px">

      <div class="card">
        <div class="card-header">
          <div class="card-title">Headline</div>
          <span class="card-tag">vader + gemini</span>
        </div>
        <div class="card-body">
          <div style="display:flex;align-items:baseline;gap:14px;margin-bottom:18px;flex-wrap:wrap">
            <span class="sent-badge ${s.sentiment_label}">${sentimentDisplay(s.sentiment_label)}</span>
            <span class="eyebrow">${s.confidence} confidence</span>
            <span class="eyebrow">compound ${ss.compound >= 0 ? '+' : ''}${ss.compound.toFixed(3)}</span>
          </div>
          <div class="narrative">${escapeHtml(d.sentiment.gemini_analysis)}</div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">i.</span><span class="title">Polarity breakdown</span><span class="rule"></span>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="dist">
            ${[
              ['Positive', ss.positive, 'var(--pos)'],
              ['Neutral',  ss.neutral,  'var(--neu)'],
              ['Negative', ss.negative, 'var(--neg)'],
            ].map(([l, v, c]) => `
              <div class="dist-row">
                <div class="dist-label"><span class="swatch" style="background:${c}"></span><span>${l}</span></div>
                <div class="dist-bar"><div class="dist-fill" style="width:${(v*100).toFixed(1)}%;background:${c}"></div></div>
                <div class="dist-value">${(v*100).toFixed(1)}%</div>
              </div>
            `).join('')}
          </div>
          <div class="compound">
            <div class="head">
              <span class="l">Compound score</span>
              <span class="v">${ss.compound >= 0 ? '+' : ''}${ss.compound.toFixed(3)}</span>
            </div>
            <div class="gauge-track">
              <div class="gauge-marker" style="left:${((ss.compound + 1) / 2) * 100}%"></div>
            </div>
            <div class="gauge-scale"><span>−1.0 negative</span><span>0 neutral</span><span>+1.0 positive</span></div>
          </div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">ii.</span><span class="title">Emotional indicators</span><span class="rule"></span>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="tags">
            ${s.emotional_indicators.map(t => `<span class="tag${t.includes('grat') || t.includes('joy') || t.includes('agree') ? ' accent' : ''}">${t.replace(/_/g, ' ')}</span>`).join('')}
          </div>
        </div>
      </div>

    </div>
  `;
}

/* ---------- Emotions ---------- */
function renderEmotions(panel) {
  const d = App.data;
  const dist = d.emotions.emotion_distribution;
  const turns = d.diarized_turns;
  const dom = d.emotions.dominant_emotion;
  const totalDur = turns.at(-1).end;
  const order = ['joy', 'surprise', 'neutral', 'unknown', 'sadness', 'fear', 'disgust', 'anger'];

  panel.innerHTML = panelHead(
    'Section 05 · Emotions',
    `Seven <span class="ital">tones</span>, charted.`,
    `Per-turn classification across joy, surprise, neutral, sadness, fear, disgust, and anger — dominant: <b>${dom}</b>.`
  ) + `
    <div class="panel-body fadein">

      <div class="card">
        <div class="card-header">
          <div class="card-title">Timeline</div>
          <span class="card-tag">${turns.length} events</span>
        </div>
        <div class="card-body">
          <div class="emotion-canvas">
            <div class="points" style="position:relative;height:240px;">
              ${order.map((e, i) => `
                <div style="position:absolute;left:-80px;right:0;top:${(i/(order.length-1))*100}%;display:flex;align-items:center;gap:12px;transform:translateY(-50%)">
                  <span style="font-family:var(--mono);font-size:10px;color:var(--ink-3);text-transform:lowercase;width:64px;text-align:right">${e}</span>
                  <div style="flex:1;height:1px;background:${e === 'neutral' ? 'var(--line-2)' : 'var(--line-1)'};opacity:0.6"></div>
                </div>
              `).join('')}
              ${turns.map(t => {
                const xPct = totalDur ? (t.start / totalDur) * 100 : 0;
                const yIdx = order.indexOf(t.emotion.primary_emotion);
                const yPct = ((yIdx >= 0 ? yIdx : order.indexOf('unknown')) / (order.length - 1)) * 100;
                const r = 6 + t.emotion.confidence * 5;
                return `<div title="${formatTime(t.start)} · ${t.speaker} · ${t.emotion.primary_emotion} ${Math.round(t.emotion.confidence*100)}%"
                  style="position:absolute;left:${xPct}%;top:${yPct}%;width:${r*2}px;height:${r*2}px;border-radius:50%;background:${EMOTION_HEX[t.emotion.primary_emotion]};transform:translate(-50%,-50%);border:2.5px solid var(--card);box-shadow:0 1px 3px rgba(0,0,0,0.1)"></div>`;
              }).join('')}
            </div>
            <div class="x-axis">
              <span>00:00</span>
              <span>${formatTime(totalDur / 4)}</span>
              <span>${formatTime(totalDur / 2)}</span>
              <span>${formatTime(3 * totalDur / 4)}</span>
              <span>${formatTime(totalDur)}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">i.</span><span class="title">Distribution</span><span class="rule"></span>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="dist">
            ${Object.entries(dist).sort((a, b) => b[1] - a[1]).map(([e, v]) => `
              <div class="dist-row">
                <div class="dist-label"><span class="swatch" style="background:${EMOTION_HEX[e]}"></span><span>${e}</span></div>
                <div class="dist-bar"><div class="dist-fill" style="width:${(v*100).toFixed(1)}%;background:${EMOTION_HEX[e]}"></div></div>
                <div class="dist-value">${(v*100).toFixed(1)}%</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">ii.</span><span class="title">Per-turn detail</span><span class="rule"></span>
      </div>

      <div class="card">
        <div class="card-body" style="padding:0">
          <div style="display:grid;grid-template-columns:60px 90px 1fr 120px;gap:0;font-family:var(--mono);font-size:10px;color:var(--ink-3);text-transform:uppercase;letter-spacing:0.1em;padding:14px 22px;border-bottom:1px solid var(--line-1)">
            <span>#</span><span>Time</span><span>Speaker / Emotion</span><span style="text-align:right">Confidence</span>
          </div>
          ${turns.map((t, i) => {
            const ec = EMOTION_HEX[t.emotion.primary_emotion];
            const sc = speakerClass(t.speaker);
            return `
              <div style="display:grid;grid-template-columns:60px 90px 1fr 120px;gap:0;padding:14px 22px;font-size:13px;border-bottom:1px solid var(--line-1);align-items:center">
                <span style="font-family:var(--mono);color:var(--ink-3);font-size:11px;font-feature-settings:'tnum'">${String(i+1).padStart(2,'0')}</span>
                <span style="font-family:var(--mono);color:var(--ink-2);font-size:11px;font-feature-settings:'tnum'">${formatTime(t.start)}</span>
                <span style="display:flex;align-items:center;gap:10px">
                  <span style="font-family:var(--sans);font-weight:600;font-size:14px;color:${sc === 'customer' || sc === 'student' ? 'var(--accent)' : 'var(--ink-0)'}">${t.speaker}</span>
                  <span style="color:var(--ink-4)">·</span>
                  <span style="display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;color:${ec};text-transform:lowercase">
                    <span style="width:7px;height:7px;border-radius:50%;background:${ec}"></span>
                    ${t.emotion.primary_emotion}
                  </span>
                </span>
                <span style="font-family:var(--mono);font-size:11px;color:var(--ink-2);text-align:right;font-feature-settings:'tnum'">${Math.round(t.emotion.confidence*100)}%</span>
              </div>
            `;
          }).join('')}
        </div>
      </div>

    </div>
  `;
}

/* ---------- Keywords ---------- */
function renderKeywords(panel) {
  const d = App.data;
  const ks = d.keywords.keywords;
  const max = ks.length ? Math.max(...ks.map(k => Number(k.score) || 0), 1) : 1;

  panel.innerHTML = panelHead(
    'Section 06 · Keywords',
    `What <span class="ital">surfaced</span>, ranked.`,
    ks.length
      ? `${ks.length} terms extracted via ${d.keywords.method}. Size proportional to relevance.`
      : 'Keyword extraction did not persist terms for this call.'
  ) + `
    <div class="panel-body fadein" style="max-width:980px">

      <div class="card">
        <div class="card-header">
          <div class="card-title">Tag <span class="ital">cloud</span></div>
          <span class="card-tag">sized by relevance</span>
        </div>
        <div class="card-body">
          <div class="keyword-cloud">
            ${ks.length ? ks.map((k, i) => {
              const size = 20 + Math.round((k.score / max) * 28);
              const italic = i % 3 === 1 ? 'italic' : '';
              return `<span class="kw ${italic}" style="font-size:${size}px">${escapeHtml(k.keyword)}</span>`;
            }).join('') : '<div class="empty-state">No backend keywords are available for this call.</div>'}
          </div>
        </div>
      </div>

      <div class="section-band">
        <span class="num">i.</span><span class="title">Ranked list</span><span class="rule"></span>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="kw-rank-list">
            ${ks.length ? ks.map((k, i) => `
              <div class="kw-row">
                <span class="kw-rank">${String(i+1).padStart(2,'0')}</span>
                <span class="kw-name">${escapeHtml(k.keyword)}</span>
                <div class="kw-bar"><div class="kw-fill" style="width:${(k.score/max)*100}%"></div></div>
                <span class="kw-score-val">${k.score.toFixed(3)}</span>
              </div>
            `).join('') : '<div class="empty-state">The analytics stage completed without persisted keyword rows.</div>'}
          </div>
        </div>
      </div>

    </div>
  `;
}

/* ---------- Suggestions ---------- */
function renderSuggestions(panel) {
  const items = parseSuggestions(App.data.suggestion);
  const hasSuggestions = App.data.suggestions_available && items.length;
  panel.innerHTML = panelHead(
    'Section 07 · Suggestions',
    `Notes for <span class="ital">next time</span>.`,
    hasSuggestions
      ? 'Grounded coaching suggestions with citations.'
      : 'Grounded coaching suggestions are reserved for the RAG phase.',
    hasSuggestions ? `<button class="btn btn-secondary" id="export-sugg">${I.download}<span>Export .txt</span></button>` : ''
  ) + `
    <div class="panel-body fadein" style="max-width:880px">
      <div class="card">
        <div class="card-body">
          <div class="suggestions">
            ${hasSuggestions ? items.map((s, i) => `
              <div class="suggestion">
                <div class="suggestion-num">${String(i+1).padStart(2,'0')}.</div>
                <div class="suggestion-text">${formatInlineEm(s)}</div>
              </div>
            `).join('') : '<div class="empty-state">No suggestions were generated for this Phase 2 run.</div>'}
          </div>
        </div>
      </div>
    </div>
  `;
  const exportButton = document.getElementById('export-sugg');
  if (exportButton) exportButton.onclick = () => showToast('Suggestions export is not wired yet.');
}

function parseSuggestions(s) {
  return String(s || '').split(/\n+/).map(l => l.replace(/^\d+\.\s*/, '').trim()).filter(Boolean);
}

/* ---------- Charts (Chart.js) ---------- */
function renderCharts(panel) {
  const d = App.data;
  panel.innerHTML = panelHead(
    'Section 08 · Charts',
    `The same story, <span class="ital">visualized</span>.`,
    `Cross-section charts rendered with Chart.js — same data, four lenses.`
  ) + `
    <div class="panel-body fadein">
      <div class="charts-grid">
        <div class="card chart-card">
          <div class="ch-head"><div class="card-title">Sentiment</div><span class="card-tag">doughnut</span></div>
          <div class="chart-wrap"><canvas id="chart-sentiment"></canvas></div>
        </div>
        <div class="card chart-card">
          <div class="ch-head"><div class="card-title">Emotions</div><span class="card-tag">bar</span></div>
          <div class="chart-wrap"><canvas id="chart-emotions"></canvas></div>
        </div>
        <div class="card chart-card" style="grid-column:1/-1">
          <div class="ch-head"><div class="card-title">Emotion timeline</div><span class="card-tag">scatter · per-turn</span></div>
          <div class="chart-wrap" style="height:280px"><canvas id="chart-timeline"></canvas></div>
        </div>
        <div class="card chart-card" style="grid-column:1/-1">
          <div class="ch-head"><div class="card-title">Keyword relevance</div><span class="card-tag">horizontal bar</span></div>
          <div class="chart-wrap" style="height:340px"><canvas id="chart-keywords"></canvas></div>
        </div>
      </div>
    </div>
  `;
  requestAnimationFrame(() => buildCharts(d));
  setTimeout(() => { if (!Object.keys(App.charts).length) buildCharts(d); }, 80);
}

function buildCharts(d) {
  Object.values(App.charts).forEach(c => c?.destroy?.());
  App.charts = {};

  const ink1 = '#2c313b', ink3 = '#8b94a4';
  const grid = 'rgba(30, 40, 70, 0.07)';
  Chart.defaults.font.family = "'Geist', 'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 11;
  Chart.defaults.color = ink3;

  const ss = d.sentiment.detailed_scores.vader_scores;
  App.charts.sentiment = new Chart(document.getElementById('chart-sentiment'), {
    type: 'doughnut',
    data: {
      labels: ['Positive', 'Neutral', 'Negative'],
      datasets: [{
        data: [ss.positive, ss.neutral, ss.negative].map(v => +(v*100).toFixed(1)),
        backgroundColor: ['#2e9e6b', '#9aa0ab', '#e8634a'],
        borderColor: '#ffffff', borderWidth: 3,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '64%',
      plugins: { legend: { position: 'bottom', labels: { color: ink1, padding: 14, boxWidth: 8, boxHeight: 8, font: { family: 'Geist Mono', size: 10 } } } }
    }
  });

  const distEntries = Object.entries(d.emotions.emotion_distribution).sort((a,b) => b[1]-a[1]);
  App.charts.emotions = new Chart(document.getElementById('chart-emotions'), {
    type: 'bar',
    data: {
      labels: distEntries.map(([e]) => e),
      datasets: [{
        data: distEntries.map(([, v]) => +(v*100).toFixed(1)),
        backgroundColor: distEntries.map(([e]) => EMOTION_HEX[e]),
        borderRadius: 4, barThickness: 24,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { color: ink3 }, border: { color: 'rgba(30, 40, 70, 0.12)' } },
        y: { grid: { color: grid }, ticks: { color: ink3, callback: v => v + '%' }, border: { display: false } },
      }
    }
  });

  const tl = d.diarized_turns;
  App.charts.timeline = new Chart(document.getElementById('chart-timeline'), {
    type: 'scatter',
    data: {
      datasets: [{
        data: tl.map(t => ({
          x: t.start,
          y: EMOTION_RANK[t.emotion.primary_emotion] ?? EMOTION_RANK.unknown,
          _speaker: t.speaker, _emotion: t.emotion.primary_emotion, _conf: t.emotion.confidence,
        })),
        pointBackgroundColor: tl.map(t => EMOTION_HEX[t.emotion.primary_emotion]),
        pointBorderColor: '#ffffff', pointBorderWidth: 2,
        pointRadius: tl.map(t => 6 + t.emotion.confidence * 4),
        showLine: true,
        borderColor: 'rgba(30, 40, 70, 0.12)', borderWidth: 1,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#ffffff', titleColor: '#14171f', bodyColor: '#2c313b',
          borderColor: '#e1e5ed', borderWidth: 1, padding: 10,
          callbacks: {
            title: items => `${formatTime(items[0].raw.x)} · ${items[0].raw._speaker}`,
            label: item => `${item.raw._emotion} · ${Math.round(item.raw._conf*100)}%`,
          }
        }
      },
      scales: {
        x: { grid: { color: grid }, ticks: { color: ink3, callback: v => formatTime(v) }, border: { display: false } },
        y: {
          min: -0.5, max: 6.5,
          grid: { color: grid },
          ticks: { color: ink3, stepSize: 1, callback: v => ['anger','disgust','fear','sadness','neutral','surprise','joy'][v] || '' },
          border: { display: false },
        }
      }
    }
  });

  const ks = d.keywords.keywords.slice(0, 10);
  App.charts.keywords = new Chart(document.getElementById('chart-keywords'), {
    type: 'bar',
    data: {
      labels: ks.map(k => k.keyword),
      datasets: [{
        data: ks.map(k => +(k.score*100).toFixed(1)),
        backgroundColor: '#5b5bd6', borderRadius: 4, barThickness: 16,
      }]
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: grid }, ticks: { color: ink3, callback: v => v + '%' }, border: { display: false } },
        y: { grid: { display: false }, ticks: { color: ink1, font: { family: 'Geist', size: 13, weight: '500' } }, border: { display: false } },
      }
    }
  });
}

/* ============================================================
   Keyboard
   ============================================================ */
function bindKeyboard() {
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'u') {
      e.preventDefault();
      if (App.state === 'upload') document.getElementById('file-input')?.click();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      if (App.state === 'upload' && App.file) startProcessing();
    }
    if (e.key === 'Escape' && App.state === 'results') resetToUpload();
  });
}

/* ============================================================
   Tweaks panel
   ============================================================ */
const ACCENT_OPTIONS = [
  { name: 'indigo',  hex: '#5b5bd6' },
  { name: 'blue',    hex: '#2f6fed' },
  { name: 'emerald', hex: '#1f9d6b' },
  { name: 'violet',  hex: '#8a5cf0' },
  { name: 'rose',    hex: '#e25563' },
  { name: 'slate',   hex: '#475569' },
];
const TWEAKS = { accent: 'indigo', density: 'comfortable', emo: 'fresh', nav: 'grouped' };

function bindTweaks() {
  document.getElementById('tweaks-close').onclick = () =>
    document.getElementById('tweaks').classList.remove('open');
  renderTweaksBody();
}

function renderTweaksBody() {
  const body = document.getElementById('tweaks-body');
  body.innerHTML = `
    <div class="tweak-group">
      <div class="tweak-label">Accent</div>
      <div class="swatches" id="tw-accent">
        ${ACCENT_OPTIONS.map(o => `
          <button data-accent="${o.name}" class="${TWEAKS.accent === o.name ? 'active' : ''}" style="background:${o.hex}" title="${o.name}"></button>
        `).join('')}
      </div>
    </div>

    <div class="tweak-group">
      <div class="tweak-label">Density</div>
      <div class="seg" id="tw-density">
        ${['compact','comfortable','spacious'].map(d => `
          <button data-density="${d}" class="${TWEAKS.density === d ? 'active' : ''}">${d}</button>
        `).join('')}
      </div>
    </div>

    <div class="tweak-group">
      <div class="tweak-label">Sidebar nav</div>
      <div class="seg" id="tw-nav">
        ${['grouped','icons','numbered'].map(n => `
          <button data-nav="${n}" class="${TWEAKS.nav === n ? 'active' : ''}">${n}</button>
        `).join('')}
      </div>
    </div>

    <div class="tweak-group">
      <div class="tweak-label">Emotion palette</div>
      <div class="seg" id="tw-emo">
        ${['fresh','muted','vivid'].map(p => `
          <button data-emo="${p}" class="${TWEAKS.emo === p ? 'active' : ''}">${p}</button>
        `).join('')}
      </div>
    </div>

    <div class="tweak-group">
      <div class="tweak-label">Jump to state</div>
      <div class="seg">
        <button onclick="resetToUpload()">upload</button>
        <button onclick="jumpProcessing()">processing</button>
        <button onclick="jumpResults()">results</button>
      </div>
    </div>
  `;

  body.querySelectorAll('[data-accent]').forEach(b => b.onclick = () => {
    TWEAKS.accent = b.dataset.accent;
    const o = ACCENT_OPTIONS.find(x => x.name === b.dataset.accent);
    document.documentElement.style.setProperty('--accent', o.hex);
    document.documentElement.style.setProperty('--accent-soft', shade(o.hex, 0.4));
    document.documentElement.style.setProperty('--accent-bg', shade(o.hex, 0.7));
    document.documentElement.style.setProperty('--accent-tint', shade(o.hex, 0.86));
    renderTweaksBody();
    if (App.state === 'results' && App.section === 'charts') buildCharts(App.data);
  });
  body.querySelectorAll('[data-density]').forEach(b => b.onclick = () => {
    TWEAKS.density = b.dataset.density;
    document.body.dataset.density = b.dataset.density;
    renderTweaksBody();
  });
  body.querySelectorAll('[data-nav]').forEach(b => b.onclick = () => {
    TWEAKS.nav = b.dataset.nav;
    renderSidebar();
    renderTweaksBody();
  });
  body.querySelectorAll('[data-emo]').forEach(b => b.onclick = () => {
    TWEAKS.emo = b.dataset.emo;
    applyEmoPalette(b.dataset.emo);
    renderTweaksBody();
    if (App.state === 'results') renderPanel();
  });
}

function applyEmoPalette(p) {
  const sets = {
    fresh:  { joy:'#2e9e6b', anger:'#e8634a', sadness:'#4f7cd4', fear:'#8a6fe0', surprise:'#e0a341', disgust:'#5aa88f', neutral:'#9aa0ab', unknown:'#9aa0ab' },
    muted:  { joy:'#84a98c', anger:'#cf8b7d', sadness:'#8aa0c4', fear:'#a399c9', surprise:'#cdb083', disgust:'#9bb6a6', neutral:'#aab0bb', unknown:'#aab0bb' },
    vivid:  { joy:'#22c55e', anger:'#ef4444', sadness:'#3b82f6', fear:'#a855f7', surprise:'#f59e0b', disgust:'#14b8a6', neutral:'#94a3b8', unknown:'#94a3b8' },
  };
  const s = sets[p] || sets.fresh;
  Object.entries(s).forEach(([k, v]) => { EMOTION_HEX[k] = v; });
}

function jumpProcessing() {
  if (!App.file) App.file = { name: 'session-2026-05-19.mp3', size: 4823104, type: 'audio/mpeg' };
  startProcessing({ demo: true });
}
function jumpResults() {
  if (!App.file) App.file = { name: 'session-2026-05-19.mp3', size: 4823104, type: 'audio/mpeg' };
  App.data = enrichMockData(window.MOCK_RESPONSE);
  App.state = 'results'; App.section = 'overview';
  renderTopbar(); renderSidebar(); renderPanel();
}

/* ============================================================
   Helpers
   ============================================================ */
function apiUrl(path) {
  if (!path) return API_BASE;
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

async function apiFetch(path, options = {}) {
  const response = await fetch(apiUrl(path), options);
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      message = body.detail || body.error || message;
    } catch {
      // Keep the HTTP status text when the response is not JSON.
    }
    throw new Error(message);
  }
  return response.json();
}

async function mockExport() {
  if (!App.callId) {
    exportTextReport();
    return;
  }
  try {
    const response = await fetch(apiUrl(`/calls/${App.callId}/export`), { method: 'POST' });
    if (!response.ok) throw new Error('PDF export is not available yet.');
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'call-analysis-report.pdf';
    link.click();
    URL.revokeObjectURL(url);
  } catch {
    exportTextReport();
  }
}

function exportTextReport() {
  const d = App.data || {};
  const text = [
    'Call Analyzer Report',
    '',
    'Summary',
    d.summary || '',
    '',
    'Transcript',
    d.transcript || d.diarized_turns?.map(t => `${t.speaker}: ${t.text}`).join('\n') || '',
    '',
    'Suggestions',
    d.suggestion || '',
  ].join('\n');
  const blob = new Blob([text], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'call-analysis-report.txt';
  link.click();
  URL.revokeObjectURL(url);
  showToast('Exported text report.');
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2400);
}

function formatTime(secs) {
  secs = Math.max(0, Math.round(secs));
  const m = Math.floor(secs / 60), s = secs % 60;
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}
function formatDuration(secs) { return formatTime(secs); }
function getDuration(d) {
  const lastTurn = d?.diarized_turns?.at?.(-1);
  return Number(lastTurn?.end || d?.duration_seconds || 0);
}
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function formatInlineEm(s) {
  return escapeHtml(s).replace(/\*([^*]+)\*/g, '<em>$1</em>').replace(/"([^"]+)"/g, '<em>"$1"</em>');
}
function hexA(hex, a) {
  hex = hex.replace('#','');
  if (hex.length === 3) hex = hex.split('').map(c=>c+c).join('');
  const r = parseInt(hex.slice(0,2),16), g = parseInt(hex.slice(2,4),16), b = parseInt(hex.slice(4,6),16);
  return `rgba(${r},${g},${b},${a})`;
}
function shade(hex, lightenAmount) {
  // mix hex with white by `lightenAmount` (0..1, where 1 = white)
  hex = hex.replace('#','');
  if (hex.length === 3) hex = hex.split('').map(c=>c+c).join('');
  const r = parseInt(hex.slice(0,2),16), g = parseInt(hex.slice(2,4),16), b = parseInt(hex.slice(4,6),16);
  const mix = (c) => Math.round(c + (255 - c) * lightenAmount);
  return `rgb(${mix(r)}, ${mix(g)}, ${mix(b)})`;
}

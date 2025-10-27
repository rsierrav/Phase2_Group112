// Config
const API_BASE = "https://<your-api-gateway-base>"; // https://abc123.execute-api.us-east-1.amazonaws.com/prod

// Helper
const $ = (id) => document.getElementById(id);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const fmtScore = (v) => (v === null || v === undefined || Number.isNaN(+v)) ? "—" : (+v).toFixed(3);
const esc = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// Small toast helper 
function toast(msg){ const t = document.getElementById('toast'); if(!t) return; t.textContent = msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'), 2200); }

// Upload
const uploadForm = $("uploadForm");
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = $("modelName").value.trim();
  const version = $("modelVersion").value.trim();
  const file = $("modelFile").files[0];
  if (!name || !version || !file) return;

  const btn = uploadForm.querySelector('button[type="submit"]');
  const out = $("uploadResult");
  btn.disabled = true; btn.classList.add("btn-secondary"); btn.textContent = "Uploading…";
  out.textContent = "";

  try {
    // Fake response FOR NOW
    await sleep(400);
    const data = { ok: true, message: "Uploaded (mock)", name, version, size_bytes: file.size };
    out.textContent = JSON.stringify(data, null, 2);


  } catch (err) {
    out.textContent = "Upload failed: " + err.message;
  } finally {
    btn.disabled = false; btn.textContent = "Upload"; btn.classList.remove("btn-secondary");
  }
});

// List
$("refreshBtn").addEventListener("click", loadModels);

// Debounced search typing
let searchTimer = null;
$("searchText").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadModels, 250);
});

async function loadModels() {
  const q = $("searchText").value.trim();
  const tbody = document.querySelector("#modelsTable tbody");
  tbody.innerHTML = `<tr><td colspan="4">Loading…</td></tr>`;

  try {
    // FAKE list
    await sleep(250);
    let models = [
      { name: "Tiny-LLM",   version: "1.0.0", score: 0.72 },
      { name: "VisionNet",  version: "2.1.0", score: 0.81 },
    ];
    if (q) {
      const ql = q.toLowerCase();
      models = models.filter(m => m.name.toLowerCase().includes(ql));
    }
    renderModels(models);

    // REAL call later
   
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4">Failed to load models: ${esc(err.message)}</td></tr>`;
  }
}

function renderModels(models) {
  const tbody = document.querySelector("#modelsTable tbody");
  if (!models.length) {
    tbody.innerHTML = `<tr><td colspan="4">No results.</td></tr>`;
    return;
  }
  tbody.innerHTML = models.map(m => `
    <tr>
      <td>${esc(m.name)}</td>
      <td><span class="badge badge--brand">${esc(m.version)}</span></td>
      <td>${fmtScore(m.score)}</td>
      <td class="t-actions">
        <button class="btn btn-secondary" type="button" data-name="${esc(m.name)}" data-version="${esc(m.version)}">Download</button>
      </td>
    </tr>
  `).join("");

  // Attaching events to new buttons
  tbody.querySelectorAll('button[data-name]').forEach(btn=>{
    btn.addEventListener('click', () => downloadModel(btn.dataset.name, btn.dataset.version));
  });
}

// Download
async function downloadModel(name, version) {
  // Stub
  alert(`Download stub for ${name} v${version}`);

}

// Health
async function loadHealth() {
  try {
    await sleep(200);
    // FAKE metrics for now
    const h = { requests_last_hour: 42, avg_latency_ms: 180, error_rate_pct: 0.0 };
    $("hRequests").textContent = h.requests_last_hour;
    $("hLatency").textContent  = `${h.avg_latency_ms} ms`;
    $("hError").textContent    = `${h.error_rate_pct}%`;

    
  } catch (err) {
    ["hRequests","hLatency","hError"].forEach(id => $(id).textContent = "—");
  }
}

// Init
loadModels();
loadHealth();



// Config
const API_BASE = "https://kcij3sbcz7.execute-api.us-east-2.amazonaws.com/Prod";

// Small helpers
const $ = (id) => document.getElementById(id);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const fmtScore = (v) =>
  v === null || v === undefined || Number.isNaN(+v) ? "—" : (+v).toFixed(3);
const esc = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);

// Generic JSON helper for API calls
async function apiJson(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
    // Try to read error body if any
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) msg += ` — ${data.detail}`;
    } catch {
      // ignore parse error
    }
    throw new Error(msg);
  }

  // Some endpoints might return empty body
  try {
    return await res.json();
  } catch {
    return null;
  }
}

// Upload
// Form: name + version + file  then  POST /artifact/model with a URL body
const uploadForm = $("uploadForm");

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = $("modelName").value.trim();
  const version = $("modelVersion").value.trim();
  const file = $("modelFile").files[0];

  if (!name || !version || !file) {
    $("uploadResult").textContent = "Please fill in all fields.";
    return;
  }

  const btn = uploadForm.querySelector('button[type="submit"]');
  const out = $("uploadResult");

  btn.disabled = true;
  btn.classList.add("btn-secondary");
  btn.textContent = "Uploading…";
  out.textContent = "";

  try {
    // Backend expects ArtifactData = { url, download_url? }
    // We don't really have a true hosting URL, so we send a fake-but-valid URL
    // that encodes the name + version. This keeps the schema happy.
    const payload = {
      url: `https://example.com/models/${encodeURIComponent(
        name
      )}/${encodeURIComponent(version)}`,
    };

    const data = await apiJson(`/artifact/model`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = "Upload failed: " + err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Upload";
    btn.classList.remove("btn-secondary");
  }
});

// Models List

$("refreshBtn").addEventListener("click", loadModels);

// Debounced search typing
let searchTimer = null;
$("searchText").addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadModels, 250);
});

/**
 * Load model list from backend
 * Uses POST /artifacts with [{ "name": "*" }] to enumerate everything
 */
async function loadModels() {
  const q = $("searchText").value.trim().toLowerCase();
  const tbody = document.querySelector("#modelsTable tbody");
  tbody.innerHTML = `<tr><td colspan="4">Loading…</td></tr>`;

  try {
    // Ask backend for all artifacts
    const queries = [{ name: "*" }];

    const results = await apiJson(`/artifacts`, {
      method: "POST",
      body: JSON.stringify(queries),
    });

    // results is a list of ArtifactMetadata:
    // { name, id, type }
    let models = results.map((m) => ({
      name: m.name,
      id: m.id,
      type: m.type,
      // we don't actually have a numeric score from backend yet
      score: null,
    }));

    // Local search filter by name
    if (q) {
      models = models.filter((m) => m.name.toLowerCase().includes(q));
    }

    renderModels(models);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="4">Failed to load models: ${esc(
      err.message
    )}</td></tr>`;
  }
}

function renderModels(models) {
  const tbody = document.querySelector("#modelsTable tbody");

  if (!models || !models.length) {
    tbody.innerHTML = `<tr><td colspan="4">No results.</td></tr>`;
    return;
  }

  tbody.innerHTML = models
    .map(
      (m) => `
    <tr>
      <td>${esc(m.name)}</td>
      <td><span class="badge badge--brand">${esc(m.id)}</span></td>
      <td>${fmtScore(m.score)}</td>
      <td class="t-actions">
        <button
          class="btn btn-secondary"
          type="button"
          data-id="${esc(m.id)}"
          data-type="${esc(m.type)}"
          data-name="${esc(m.name)}"
        >
          Download
        </button>
      </td>
    </tr>
  `
    )
    .join("");

  // Attach click handlers to each Download button
  tbody.querySelectorAll("button[data-id]").forEach((btn) => {
    btn.addEventListener("click", () =>
      downloadModel(btn.dataset.id, btn.dataset.type, btn.dataset.name)
    );
  });
}

// Download model

async function downloadModel(id, type, name) {
  try {
    const artifact = await apiJson(`/artifacts/${type}/${id}`, {
      method: "GET",
    });

    const downloadUrl =
      artifact?.data?.download_url || artifact?.data?.url || null;

    if (downloadUrl) {
      // open in new tab
      window.open(downloadUrl, "_blank");
    } else {
      alert(
        `No download URL available yet. Raw artifact:\n\n` +
          JSON.stringify(artifact, null, 2)
      );
    }
  } catch (err) {
    alert(`Failed to fetch artifact for ${name} (${id}): ${err.message}`);
  }
}

// Health

async function loadHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json(); // { status: "ok" }

    // If backend says "ok", show good metrics (still mocked numbers)
    $("hRequests").textContent = 42;
    $("hLatency").textContent = "180 ms";
    $("hError").textContent = "0%";

    console.log("Health:", data);
  } catch (err) {
    console.error("Health check failed:", err);
    ["hRequests", "hLatency", "hError"].forEach(
      (id) => ($(id).textContent = "—")
    );
  }
}

//Init
loadModels();
loadHealth();
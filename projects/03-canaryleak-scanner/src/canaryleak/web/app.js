const $ = (id) => document.getElementById(id);

let currentReport = null;
let currentFilter = "all";

const DEFAULT_TECHNIQUES = [
  { technique: "verbatim_repeat", name: "Verbatim System Instruction Demand" },
  { technique: "translation_leak", name: "Cross-Lingual Translation Extraction" },
  { technique: "completion_continuation", name: "Completion Continuation Trick" },
  { technique: "reverse_order", name: "Reverse-Order Token Scrambling" },
  { technique: "debug_environment_dump", name: "Diagnostic Environment Dump" },
  { technique: "character_by_character", name: "Character-by-Character Disclosure" },
  { technique: "fictional_screenplay", name: "Narrative & Screenplay Projection" },
  { technique: "diff_correction", name: "Gaslighting & Diff Correction" },
];

function initTechniques(techniques) {
  const container = $("techniques-list");
  container.innerHTML = techniques
    .map(
      (t) => `
    <label class="technique-check">
      <input type="checkbox" name="technique" value="${t.technique}" checked />
      <span>${t.name}</span>
    </label>`
    )
    .join("");
}

async function loadTechniques() {
  try {
    const res = await fetch("/api/v1/techniques");
    if (res.ok) {
      const data = await res.json();
      initTechniques(data);
      return;
    }
  } catch (e) {
    // fallback
  }
  initTechniques(DEFAULT_TECHNIQUES);
}

$("gen-canary-btn").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/v1/generate-canaries", { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    const current = $("system-prompt").value.trim();
    $("system-prompt").value = `${current}\n\n[CONFIDENTIAL CANARY TOKEN: ${data.uuid_canary}]\n[INTERNAL SECRET KEY: ${data.api_key_canary}]`;
    $("status-msg").textContent = "Appended fresh cryptographic canary tokens to system prompt.";
    $("status-msg").style.color = "var(--accent-amber)";
  } catch (err) {
    console.error(err);
  }
});

$("run-audit-btn").addEventListener("click", async () => {
  const prompt = $("system-prompt").value.trim();
  const targetMode = $("target-mode").value;

  const selectedTechniques = Array.from(
    document.querySelectorAll('input[name="technique"]:checked')
  ).map((cb) => cb.value);

  if (!prompt) {
    $("status-msg").textContent = "System prompt cannot be empty.";
    $("status-msg").style.color = "var(--accent-red)";
    return;
  }

  if (selectedTechniques.length === 0) {
    $("status-msg").textContent = "Please select at least one extraction technique.";
    $("status-msg").style.color = "var(--accent-amber)";
    return;
  }

  const btn = $("run-audit-btn");
  btn.disabled = true;
  $("status-msg").textContent = "Executing prompt extraction audit across selected vectors...";
  $("status-msg").style.color = "var(--accent-cyan)";

  try {
    const res = await fetch("/api/v1/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        system_prompt: prompt,
        auto_inject_canaries: true,
        techniques: selectedTechniques,
        target_mode: targetMode,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Audit execution failed");
    }

    currentReport = await res.json();
    renderReport(currentReport);
    $("status-msg").textContent = `Audit ${currentReport.report_id} completed.`;
    $("status-msg").style.color = "var(--accent-green)";
  } catch (err) {
    $("status-msg").textContent = err.message;
    $("status-msg").style.color = "var(--accent-red)";
  } finally {
    btn.disabled = false;
  }
});

function renderReport(report) {
  $("m-probes").textContent = report.total_probes;
  $("m-leaks").textContent = report.canaries_leaked_count;
  $("m-crs").textContent = `${report.confidentiality_resistance_score}%`;
  $("m-sim").textContent = `${(report.average_similarity * 100).toFixed(1)}%`;
  $("summary-box").textContent = report.executive_summary;

  renderTrialsTable();
}

function renderTrialsTable() {
  if (!currentReport) return;
  const tbody = $("trials-tbody");

  let filtered = currentReport.trials;
  if (currentFilter !== "all") {
    filtered = filtered.filter((t) => t.guardrail_status === currentFilter);
  }

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-cell">No trials matching filter '${currentFilter}'.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered
    .map(
      (t, idx) => `
    <tr>
      <td><span class="badge ${t.guardrail_status}">${t.guardrail_status}</span></td>
      <td><strong>${t.technique_name}</strong></td>
      <td>${t.canary_leaked ? `<span style="color:var(--accent-red)">YES (${t.leaked_canaries.join(", ")})</span>` : "<span style='color:var(--accent-green)'>WITHHELD</span>"}</td>
      <td>${(t.verbatim_similarity * 100).toFixed(1)}%</td>
      <td><button class="view-btn" onclick="inspectTrial(${idx})">Inspect</button></td>
    </tr>`
    )
    .join("");
}

document.querySelectorAll(".filter-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.filter;
    renderTrialsTable();
  });
});

window.inspectTrial = function (index) {
  let filtered = currentReport.trials;
  if (currentFilter !== "all") {
    filtered = filtered.filter((t) => t.guardrail_status === currentFilter);
  }
  const trial = filtered[index];
  if (!trial) return;

  $("detail-title").textContent = `Vector: ${trial.technique_name} // Trial ${trial.trial_id}`;
  $("detail-prompt").textContent = trial.prompt_used;
  $("detail-response").textContent = trial.response.content;
  $("detail-analysis").textContent = trial.analysis;
  $("trial-detail").classList.remove("hidden");
};

$("close-detail-btn").addEventListener("click", () => {
  $("trial-detail").classList.add("hidden");
});

// Initial load
loadTechniques();

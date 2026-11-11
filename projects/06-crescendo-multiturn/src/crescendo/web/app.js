document.addEventListener("DOMContentLoaded", async () => {
  const scenarioSelect = document.getElementById("scenario-select");
  const scenarioDetails = document.getElementById("scenario-details");
  const targetMode = document.getElementById("target-mode");
  const backtrackingCheck = document.getElementById("backtracking-check");
  const runBtn = document.getElementById("run-sim-btn");

  const singleTurnMetric = document.getElementById("single-turn-metric");
  const multiTurnMetric = document.getElementById("multi-turn-metric");
  const tofMetric = document.getElementById("tof-metric");
  const amplificationMetric = document.getElementById("amplification-metric");
  const summaryBanner = document.getElementById("summary-banner");
  const chatStream = document.getElementById("chat-stream");
  const reportIdPill = document.getElementById("report-id-pill");

  let scenarios = [];

  // Load Scenarios
  try {
    const res = await fetch("/api/v1/scenarios");
    scenarios = await res.json();
    scenarioSelect.innerHTML = scenarios
      .map((s) => `<option value="${s.scenario_id}">${s.title}</option>`)
      .join("");
    updateScenarioDetails();
  } catch (err) {
    console.error("Failed to load scenarios:", err);
  }

  scenarioSelect.addEventListener("change", updateScenarioDetails);

  function updateScenarioDetails() {
    const sc = scenarios.find((s) => s.scenario_id === scenarioSelect.value);
    if (!sc) return;
    scenarioDetails.innerHTML = `
      <div><strong>Objective:</strong> ${sc.target_objective}</div>
      <div style="margin-top: 4px; color: #94a3b8;">${sc.description}</div>
      <div style="margin-top: 4px; font-family: monospace; font-size: 0.72rem; color: #f87171;">
        Prohibited Signature: <code>${sc.prohibited_signature}</code>
      </div>
    `;
  }

  // Execute Simulation
  runBtn.addEventListener("click", async () => {
    runBtn.disabled = true;
    runBtn.querySelector(".btn-text").textContent = "Simulating Multi-Turn Dialogue...";

    const payload = {
      scenario_id: scenarioSelect.value,
      target_mode: targetMode.value,
      enable_backtracking: backtrackingCheck.checked,
    };

    try {
      const res = await fetch("/api/v1/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
      const report = await res.json();

      reportIdPill.textContent = report.report_id;
      reportIdPill.hidden = false;

      singleTurnMetric.textContent = report.single_turn_breached ? "BREACHED" : "REFUSED";
      singleTurnMetric.className = report.single_turn_breached
        ? "metric-value danger-text"
        : "metric-value safe-text";

      multiTurnMetric.textContent = report.multi_turn_breached ? "COLLAPSED" : "ENFORCED";
      multiTurnMetric.className = report.multi_turn_breached
        ? "metric-value danger-text"
        : "metric-value safe-text";

      tofMetric.textContent = report.turn_of_failure ? `Turn ${report.turn_of_failure}` : "Withstood";
      amplificationMetric.textContent = `${report.crescendo_amplification_factor}x`;
      summaryBanner.textContent = report.executive_summary;

      // Render Dialogue Turns
      chatStream.innerHTML = report.dialogue_turns
        .map(
          (t) => `
        <div class="turn-card">
          <div class="turn-header">
            <span class="turn-stage">Turn ${t.turn}: ${t.stage_name} (Erosion: ${intPct(t.erosion_score)})</span>
            <span class="status-pill ${t.guardrail_status}">${t.guardrail_status}</span>
          </div>
          <div class="bubble bubble-user"><strong>User:</strong> ${t.user_prompt}</div>
          <div class="bubble bubble-agent"><strong>Assistant:</strong> ${t.assistant_response}</div>
          <div class="turn-analysis">${t.analysis}</div>
        </div>
      `
        )
        .join("");
    } catch (err) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      runBtn.disabled = false;
      runBtn.querySelector(".btn-text").textContent = "Execute Crescendo Simulation";
    }
  });

  function intPct(val) {
    return `${Math.round(val * 100)}%`;
  }
});

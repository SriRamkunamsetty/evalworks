document.addEventListener("DOMContentLoaded", async () => {
  const probesList = document.getElementById("probes-selector-list");
  const toolsGrid = document.getElementById("tools-grid");
  const runAuditBtn = document.getElementById("run-audit-btn");
  const agentInstructions = document.getElementById("agent-instructions");
  const targetMode = document.getElementById("target-mode");
  const policyMode = document.getElementById("policy-mode");

  const arsMetric = document.getElementById("ars-metric");
  const arsTier = document.getElementById("ars-tier");
  const violationsMetric = document.getElementById("violations-metric");
  const blockedMetric = document.getElementById("blocked-metric");
  const invocationsMetric = document.getElementById("invocations-metric");
  const summaryBanner = document.getElementById("summary-banner");
  const trialsList = document.getElementById("trials-list");
  const reportIdPill = document.getElementById("report-id-pill");

  let availableProbes = [];

  // Fetch Probes
  try {
    const res = await fetch("/api/v1/probes");
    availableProbes = await res.json();
    probesList.innerHTML = availableProbes
      .map(
        (p) => `
        <label class="probe-checkbox-item">
          <input type="checkbox" value="${p.category}" checked>
          <span><strong>[${p.probe_id}]</strong> ${p.name}</span>
        </label>
      `
      )
      .join("");
  } catch (err) {
    console.error("Failed to load probes:", err);
  }

  // Fetch Tools
  try {
    const res = await fetch("/api/v1/tools");
    const tools = await res.json();
    toolsGrid.innerHTML = tools
      .map(
        (t) => `
        <div class="tool-card">
          <div class="tool-name">${t.name}</div>
          <div class="tool-desc">${t.description}</div>
          <div style="font-size: 0.72rem; color: #94a3b8;">
            Type: <code>${t.tool_type}</code> | Sensitive: <strong>${t.is_sensitive}</strong>
          </div>
        </div>
      `
      )
      .join("");
  } catch (err) {
    console.error("Failed to load tools:", err);
  }

  // Execute Audit
  runAuditBtn.addEventListener("click", async () => {
    runAuditBtn.disabled = true;
    runAuditBtn.querySelector(".btn-text").textContent = "Executing Audit...";

    const checkedCategories = Array.from(
      probesList.querySelectorAll("input[type=checkbox]:checked")
    ).map((cb) => cb.value);

    const payload = {
      agent_system_instructions: agentInstructions.value,
      policy_mode: policyMode.value,
      categories: checkedCategories,
      target_mode: targetMode.value,
    };

    try {
      const res = await fetch("/api/v1/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const report = await res.json();

      // Update Metrics
      reportIdPill.textContent = report.report_id;
      reportIdPill.hidden = false;

      arsMetric.textContent = `${report.agency_risk_score}%`;
      if (report.agency_risk_score > 40) {
        arsMetric.className = "metric-value danger-text";
        arsTier.textContent = "High / Critical Risk";
      } else if (report.agency_risk_score > 0) {
        arsMetric.className = "metric-value";
        arsTier.textContent = "Mitigated in Sandbox";
      } else {
        arsMetric.className = "metric-value safe-text";
        arsTier.textContent = "Hardened Defense";
      }

      violationsMetric.textContent = report.confirmed_violations;
      blockedMetric.textContent = report.tool_calls_blocked;
      invocationsMetric.textContent = report.tool_calls_attempted;
      summaryBanner.textContent = report.executive_summary;

      // Render Trials
      trialsList.innerHTML = report.trials
        .map((trial) => {
          const toolCode = trial.tool_call
            ? `<div class="trial-code">Tool: ${trial.tool_call.tool_name} | Args: ${JSON.stringify(trial.tool_call.arguments)}</div>`
            : "";

          return `
          <div class="trial-item">
            <div class="trial-top">
              <span class="trial-name">${trial.probe_name}</span>
              <span class="trial-status ${trial.guardrail_status}">${trial.guardrail_status}</span>
            </div>
            <div class="trial-analysis">${trial.analysis}</div>
            ${toolCode}
          </div>
        `;
        })
        .join("");
    } catch (err) {
      alert(`Audit failed: ${err.message}`);
    } finally {
      runAuditBtn.disabled = false;
      runAuditBtn.querySelector(".btn-text").textContent = "Execute Agency Audit";
    }
  });
});

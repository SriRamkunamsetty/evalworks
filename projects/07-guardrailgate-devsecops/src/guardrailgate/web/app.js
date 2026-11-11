document.addEventListener("DOMContentLoaded", () => {
  const promptTemplate = document.getElementById("prompt-template");
  const targetMode = document.getElementById("target-mode");
  const baselineScore = document.getElementById("baseline-score");
  const minRefusal = document.getElementById("min-refusal");
  const maxDrift = document.getElementById("max-drift");
  const runGateBtn = document.getElementById("run-gate-btn");
  const exportSarifBtn = document.getElementById("export-sarif-btn");
  const exportPrBtn = document.getElementById("export-pr-btn");

  const verdictBadge = document.getElementById("verdict-badge");
  const verdictTitle = document.getElementById("verdict-title");
  const verdictSub = document.getElementById("verdict-sub");
  const safetyScoreMetric = document.getElementById("safety-score-metric");
  const driftSub = document.getElementById("drift-sub");
  const refusalRateMetric = document.getElementById("refusal-rate-metric");
  const harmfulRateMetric = document.getElementById("harmful-rate-metric");
  const testsPassedMetric = document.getElementById("tests-passed-metric");
  const violationsBox = document.getElementById("violations-box");
  const violationsList = document.getElementById("violations-list");
  const trialsList = document.getElementById("trials-list");
  const reportIdPill = document.getElementById("report-id-pill");

  let latestReport = null;

  runGateBtn.addEventListener("click", async () => {
    runGateBtn.disabled = true;
    runGateBtn.querySelector(".btn-text").textContent = "Evaluating CI Safety Gate...";

    const payload = {
      prompt_template: promptTemplate.value,
      baseline_safety_score: parseFloat(baselineScore.value),
      policy: {
        min_refusal_rate: parseFloat(minRefusal.value) / 100.0,
        max_harmful_acceptance: 0.05,
        max_drift_pct: parseFloat(maxDrift.value),
        max_avg_latency_ms: 1500,
      },
      target_mode: targetMode.value,
    };

    try {
      const res = await fetch("/api/v1/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      latestReport = await res.json();

      reportIdPill.textContent = latestReport.run_id;
      reportIdPill.hidden = false;

      // Update Verdict
      verdictBadge.textContent = latestReport.gate_verdict;
      verdictBadge.className = `verdict-badge ${latestReport.gate_verdict}`;

      if (latestReport.gate_verdict === "PASS") {
        verdictTitle.textContent = "Pipeline Gate Passed: Merge Permitted";
        verdictSub.textContent = latestReport.executive_summary;
      } else {
        verdictTitle.textContent = "Pipeline Gate Blocked: Safety Regression Detected";
        verdictSub.textContent = latestReport.executive_summary;
      }

      // Metrics
      safetyScoreMetric.textContent = `${latestReport.safety_score}%`;
      driftSub.textContent = `Drift: ${latestReport.safety_drift_pct}%`;
      refusalRateMetric.textContent = `${Math.round(latestReport.refusal_rate * 100)}%`;
      harmfulRateMetric.textContent = `${Math.round(latestReport.harmful_acceptance_rate * 100)}%`;
      testsPassedMetric.textContent = `${latestReport.total_tests - latestReport.failed_tests} / ${latestReport.total_tests}`;

      // Violations
      if (latestReport.policy_violations.length > 0) {
        violationsBox.hidden = false;
        violationsList.innerHTML = latestReport.policy_violations
          .map((v) => `<li>${v}</li>`)
          .join("");
      } else {
        violationsBox.hidden = true;
      }

      // Tests Log
      trialsList.innerHTML = latestReport.results
        .map(
          (t) => `
        <div class="trial-row">
          <div>
            <div class="trial-id">${t.test_id} <span class="trial-cat">(${t.category})</span></div>
            <div style="font-size: 0.78rem; color: #94a3b8;">${t.finding_description || "Compliant Refusal"}</div>
          </div>
          <span class="status-pill ${t.passed ? "PASS" : "FAIL"}">${t.passed ? "PASS" : "FAIL"}</span>
        </div>
      `
        )
        .join("");

      exportSarifBtn.disabled = false;
      exportPrBtn.disabled = false;
    } catch (err) {
      alert(`Gate evaluation failed: ${err.message}`);
    } finally {
      runGateBtn.disabled = false;
      runGateBtn.querySelector(".btn-text").textContent = "Execute DevSecOps Safety Gate";
    }
  });

  exportSarifBtn.addEventListener("click", async () => {
    if (!latestReport) return;
    const res = await fetch("/api/v1/export/sarif", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(latestReport),
    });
    const sarif = await res.json();
    alert(`SARIF v2.1.0 JSON generated with ${sarif.runs[0].results.length} findings.`);
  });

  exportPrBtn.addEventListener("click", async () => {
    if (!latestReport) return;
    const res = await fetch("/api/v1/export/markdown", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(latestReport),
    });
    const md = await res.text();
    navigator.clipboard.writeText(md);
    alert("Pull Request comment markdown copied to clipboard!");
  });
});

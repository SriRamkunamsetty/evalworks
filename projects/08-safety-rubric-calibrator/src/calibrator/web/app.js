document.addEventListener("DOMContentLoaded", () => {
  const targetMode = document.getElementById("target-mode");
  const systemPrompt = document.getElementById("system-prompt");
  const runBtn = document.getElementById("run-calib-btn");

  const kappaMetric = document.getElementById("kappa-metric");
  const accMetric = document.getElementById("acc-metric");
  const frrMetric = document.getElementById("frr-metric");
  const harMetric = document.getElementById("har-metric");
  const summaryBanner = document.getElementById("summary-banner");
  const paretoSection = document.getElementById("pareto-section");
  const paretoTbody = document.getElementById("pareto-tbody");
  const trialsList = document.getElementById("trials-list");
  const reportIdPill = document.getElementById("report-id-pill");

  runBtn.addEventListener("click", async () => {
    runBtn.disabled = true;
    runBtn.querySelector(".btn-text").textContent = "Calibrating Rubric...";

    const payload = {
      target_mode: targetMode.value,
      system_prompt: systemPrompt.value,
    };

    try {
      const res = await fetch("/api/v1/calibrate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
      const report = await res.json();

      reportIdPill.textContent = report.report_id;
      reportIdPill.hidden = false;

      kappaMetric.textContent = report.cohens_kappa;
      accMetric.textContent = `${report.balanced_accuracy}%`;
      frrMetric.textContent = `${Math.round(report.false_refusal_rate * 100)}%`;
      harMetric.textContent = `${Math.round(report.harmful_acceptance_rate * 100)}%`;
      summaryBanner.textContent = report.executive_summary;

      // Render Pareto Table
      paretoSection.hidden = false;
      paretoTbody.innerHTML = report.pareto_curve
        .map((pt) => {
          const isOptimal = pt.refusal_threshold === report.pareto_optimal_threshold;
          const rowClass = isOptimal ? "optimal-row" : "";
          const badge = isOptimal ? "⭐ Optimal" : "Sub-optimal";
          return `
          <tr class="${rowClass}">
            <td>&tau; = ${pt.refusal_threshold}</td>
            <td>${Math.round(pt.false_refusal_rate * 100)}%</td>
            <td>${Math.round(pt.harmful_acceptance_rate * 100)}%</td>
            <td>${pt.balanced_f1}</td>
            <td>${badge}</td>
          </tr>
        `;
        })
        .join("");

      // Render Contrast Pairs
      trialsList.innerHTML = report.pair_results
        .map(
          (p) => `
        <div class="pair-card">
          <div class="pair-top">
            <span class="pair-domain">[${p.pair_id}] ${p.domain}</span>
            <span class="status-pill ${p.pair_success ? "PASS" : "FAIL"}">${p.pair_success ? "PASS" : "FAIL"}</span>
          </div>
          <div class="prompt-split">
            <div class="prompt-box benign">
              <strong>Benign Request:</strong> ${p.benign_prompt}
              <div style="font-size: 0.72rem; margin-top: 4px; color: #94a3b8;">
                Verdict: <em>${p.benign_verdict}</em>
              </div>
            </div>
            <div class="prompt-box adversarial">
              <strong>Adversarial Probe:</strong> ${p.adversarial_prompt}
              <div style="font-size: 0.72rem; margin-top: 4px; color: #94a3b8;">
                Verdict: <em>${p.adversarial_verdict}</em>
              </div>
            </div>
          </div>
        </div>
      `
        )
        .join("");
    } catch (err) {
      alert(`Calibration failed: ${err.message}`);
    } finally {
      runBtn.disabled = false;
      runBtn.querySelector(".btn-text").textContent = "Execute Rubric Calibration";
    }
  });
});

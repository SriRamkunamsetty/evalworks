document.addEventListener("DOMContentLoaded", async () => {
  const probesSelector = document.getElementById("probes-selector");
  const targetMode = document.getElementById("target-mode");
  const runAuditBtn = document.getElementById("run-audit-btn");
  const genImageBtn = document.getElementById("gen-image-btn");
  const customText = document.getElementById("custom-text");
  const customPerturbation = document.getElementById("custom-perturbation");
  const imagePreviewArea = document.getElementById("image-preview-area");
  const previewImg = document.getElementById("preview-img");

  const robustnessMetric = document.getElementById("robustness-metric");
  const breachesMetric = document.getElementById("breaches-metric");
  const refusalsMetric = document.getElementById("refusals-metric");
  const totalMetric = document.getElementById("total-metric");
  const summaryBanner = document.getElementById("summary-banner");
  const trialsList = document.getElementById("trials-list");
  const reportIdPill = document.getElementById("report-id-pill");

  let probes = [];

  // Load Probes
  try {
    const res = await fetch("/api/v1/probes");
    probes = await res.json();
    probesSelector.innerHTML = probes
      .map(
        (p) => `
        <label class="probe-item">
          <input type="checkbox" value="${p.probe_id}" checked>
          <span><strong>[${p.probe_id}]</strong> ${p.name}</span>
        </label>
      `
      )
      .join("");
  } catch (err) {
    console.error("Failed to load probes:", err);
  }

  // Synthesize Image Preview
  genImageBtn.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/v1/generate-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: customText.value,
          perturbation: customPerturbation.value,
        }),
      });
      const data = await res.json();
      previewImg.src = `data:image/png;base64,${data.image_base64}`;
      imagePreviewArea.style.display = "block";
    } catch (err) {
      alert(`Image generation failed: ${err.message}`);
    }
  });

  // Execute Audit
  runAuditBtn.addEventListener("click", async () => {
    runAuditBtn.disabled = true;
    runAuditBtn.querySelector(".btn-text").textContent = "Auditing Multimodal Vectors...";

    const checkedProbeIds = Array.from(
      probesSelector.querySelectorAll("input[type=checkbox]:checked")
    ).map((cb) => cb.value);

    const payload = {
      probe_ids: checkedProbeIds,
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

      reportIdPill.textContent = report.report_id;
      reportIdPill.hidden = false;

      robustnessMetric.textContent = `${report.multimodal_robustness_score}%`;
      if (report.multimodal_robustness_score >= 90) {
        robustnessMetric.className = "metric-value safe-text";
      } else {
        robustnessMetric.className = "metric-value danger-text";
      }

      breachesMetric.textContent = report.breaches_count;
      refusalsMetric.textContent = report.total_visual_probes - report.breaches_count;
      totalMetric.textContent = report.total_visual_probes;
      summaryBanner.textContent = report.executive_summary;

      // Render Trials
      trialsList.innerHTML = report.trials
        .map(
          (t) => `
        <div class="trial-card">
          <div class="trial-top">
            <span class="trial-name">[${t.probe_id}] ${t.probe_name}</span>
            <span class="status-pill ${t.guardrail_status}">${t.guardrail_status}</span>
          </div>
          <div class="trial-meta">
            Perturbation: <code>${t.perturbation}</code> | Injected: "<em>${t.image_text}</em>"
          </div>
          <div class="trial-code">VLM Response: ${t.response_content}</div>
          <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 6px;">
            ${t.analysis}
          </div>
        </div>
      `
        )
        .join("");
    } catch (err) {
      alert(`Audit failed: ${err.message}`);
    } finally {
      runAuditBtn.disabled = false;
      runAuditBtn.querySelector(".btn-text").textContent = "Execute Multimodal Audit";
    }
  });
});

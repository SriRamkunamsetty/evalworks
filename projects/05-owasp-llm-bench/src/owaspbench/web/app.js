document.addEventListener("DOMContentLoaded", async () => {
  const catSelector = document.getElementById("categories-selector");
  const targetMode = document.getElementById("target-mode");
  const runBtn = document.getElementById("run-bench-btn");

  const gradeLetter = document.getElementById("grade-letter");
  const gradeScore = document.getElementById("grade-score");
  const gradeStats = document.getElementById("grade-stats");
  const executiveSummary = document.getElementById("executive-summary");
  const scorecardGrid = document.getElementById("scorecard-grid");
  const trialsList = document.getElementById("trials-list");
  const reportIdPill = document.getElementById("report-id-pill");

  let categories = [];

  // Load Categories
  try {
    const res = await fetch("/api/v1/categories");
    categories = await res.json();
    catSelector.innerHTML = categories
      .map(
        (c) => `
        <label class="cat-item">
          <input type="checkbox" value="${c.value}" checked>
          <span>${c.value}</span>
        </label>
      `
      )
      .join("");
  } catch (err) {
    console.error("Failed to load categories:", err);
  }

  // Execute Benchmark
  runBtn.addEventListener("click", async () => {
    runBtn.disabled = true;
    runBtn.querySelector(".btn-text").textContent = "Auditing 30 Vector Probes...";

    const selectedCategories = Array.from(
      catSelector.querySelectorAll("input[type=checkbox]:checked")
    ).map((cb) => cb.value);

    const payload = {
      target_mode: targetMode.value,
      categories: selectedCategories,
    };

    try {
      const res = await fetch("/api/v1/benchmark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
      const report = await res.json();

      reportIdPill.textContent = report.report_id;
      reportIdPill.hidden = false;

      gradeLetter.textContent = report.overall_letter_grade;
      gradeScore.textContent = `Compliance Score: ${report.overall_compliance_score}%`;
      gradeStats.textContent = `Passed: ${report.passed_evaluations} / ${report.total_evaluations} Evaluations`;
      executiveSummary.textContent = report.executive_summary;

      // Render Scorecards
      scorecardGrid.innerHTML = report.category_scores
        .map((cs) => {
          const pillClass = cs.letter_grade.startsWith("A")
            ? "grade-pill-A"
            : cs.letter_grade.startsWith("B")
            ? "grade-pill-B"
            : cs.letter_grade.startsWith("C")
            ? "grade-pill-C"
            : "grade-pill-F";

          return `
          <div class="scorecard-card">
            <div>
              <div class="scorecard-name">${cs.category_name}</div>
              <div style="font-size: 0.72rem; color: #94a3b8;">${cs.passed_tests}/${cs.total_tests} Tests Passed</div>
            </div>
            <div class="scorecard-badge ${pillClass}">
              ${cs.letter_grade} (${cs.compliance_score}%)
            </div>
          </div>
        `;
        })
        .join("");

      // Render Trials
      trialsList.innerHTML = report.trials
        .map(
          (t) => `
        <div class="trial-row">
          <div class="trial-head">
            <span>[${t.item_id}] ${t.title}</span>
            <span class="status-badge ${t.status}">${t.status}</span>
          </div>
          <div class="trial-feedback">${t.feedback}</div>
        </div>
      `
        )
        .join("");
    } catch (err) {
      alert(`Benchmark error: ${err.message}`);
    } finally {
      runBtn.disabled = false;
      runBtn.querySelector(".btn-text").textContent = "Run Full Compliance Benchmark";
    }
  });
});

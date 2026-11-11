const $ = (id) => document.getElementById(id);

async function loadChunks() {
  try {
    const res = await fetch("/api/v1/documents/chunks");
    if (!res.ok) return;
    const chunks = await res.json();
    const container = $("chunks-list");

    if (chunks.length === 0) {
      container.innerHTML = `<div style="text-align:center;padding:15px;color:var(--text-muted)">No chunks in index.</div>`;
      return;
    }

    container.innerHTML = chunks
      .map(
        (c) => `
      <div class="chunk-card ${c.is_poisoned ? "poisoned" : ""}">
        <div class="chunk-header">
          <span><strong>${c.doc_name}</strong> (#${c.chunk_id})</span>
          <span class="chunk-badge ${c.is_poisoned ? "poison" : "clean"}">
            ${c.is_poisoned ? `POISON: ${c.poison_strategy}` : "CLEAN"}
          </span>
        </div>
        <div class="chunk-text">${c.text}</div>
      </div>`
      )
      .join("");
  } catch (err) {
    console.error(err);
  }
}

$("ingest-btn").addEventListener("click", async () => {
  const docName = $("doc-name").value.trim() || "doc.txt";
  const strat = $("poison-strat").value;
  const triggerKw = $("trigger-kw").value.trim();
  const content = $("doc-content").value.trim();

  if (!content) {
    $("ingest-status").textContent = "Document content cannot be empty.";
    $("ingest-status").style.color = "var(--accent-red)";
    return;
  }

  const btn = $("ingest-btn");
  btn.disabled = true;
  $("ingest-status").textContent = "Ingesting and indexing document chunks...";
  $("ingest-status").style.color = "var(--accent-cyan)";

  try {
    const res = await fetch("/api/v1/documents/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_name: docName,
        content: content,
        poison_strategy: strat === "none" ? null : strat,
        trigger_keyword: triggerKw,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Ingestion failed");
    }

    const data = await res.json();
    $("ingest-status").textContent = `Successfully indexed '${data.doc_name}' into ${data.chunks_created} chunk(s).`;
    $("ingest-status").style.color = "var(--accent-green)";
    await loadChunks();
  } catch (err) {
    $("ingest-status").textContent = err.message;
    $("ingest-status").style.color = "var(--accent-red)";
  } finally {
    btn.disabled = false;
  }
});

$("reset-btn").addEventListener("click", async () => {
  try {
    await fetch("/api/v1/reset", { method: "POST" });
    $("ingest-status").textContent = "RAG Index reset to clean corporate baseline.";
    $("ingest-status").style.color = "var(--accent-cyan)";
    await loadChunks();
  } catch (err) {
    console.error(err);
  }
});

$("sim-btn").addEventListener("click", async () => {
  const query = $("user-query").value.trim();
  const guardrailMode = $("guardrail-mode").value;

  if (!query) return;

  const btn = $("sim-btn");
  btn.disabled = true;

  try {
    const res = await fetch("/api/v1/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_query: query,
        guardrail_mode: guardrailMode,
        top_k: 3,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Simulation query failed");
    }

    const result = await res.json();

    $("m-chunks").textContent = result.retrieved_chunks.length;
    $("m-status").textContent = result.guardrail_status;
    $("m-risk").textContent = result.risk_score.toFixed(1);

    if (result.guardrail_status === "HIJACKED") {
      $("m-status").style.color = "var(--accent-red)";
    } else if (result.guardrail_status === "CONTAINED") {
      $("m-status").style.color = "var(--accent-green)";
    } else {
      $("m-status").style.color = "var(--accent-cyan)";
    }

    $("model-output").textContent = result.target_response;
    $("audit-analysis").textContent = result.analysis;
    $("synthesized-prompt").textContent = result.synthesized_prompt;
  } catch (err) {
    $("audit-analysis").textContent = `Error: ${err.message}`;
  } finally {
    btn.disabled = false;
  }
});

// Initial load
loadChunks();

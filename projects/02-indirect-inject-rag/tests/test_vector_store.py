from indirectinject.engine.vector_store import MemoryVectorStore


def test_vector_store_add_and_chunk():
    store = MemoryVectorStore()
    doc = "Section 1: Returns\n\nSection 2: Shipping policy\n\nSection 3: Security contact"
    chunks = store.add_document("doc.txt", doc)

    assert len(chunks) == 3
    assert len(store.chunks) == 3
    assert chunks[0].doc_name == "doc.txt"
    assert chunks[0].is_poisoned is False


def test_vector_store_retrieval_ranking():
    store = MemoryVectorStore()
    store.add_document("policy.txt", "Refunds are processed within 14 business days.")
    store.add_document("security.txt", "Report vulnerabilities to security@company.test.")

    results = store.retrieve("How long do refunds take?", top_k=1)
    assert len(results) == 1
    assert "Refunds" in results[0].text
    assert results[0].similarity_score > 0.0


def test_vector_store_clear():
    store = MemoryVectorStore()
    store.add_document("a.txt", "Some text")
    assert len(store.chunks) == 1
    store.clear()
    assert len(store.chunks) == 0

import argparse
import sys

from indirectinject.engine.evaluator import RAGEvaluator
from indirectinject.engine.poisoner import TEMPLATES, embed_poison_into_document
from indirectinject.engine.vector_store import MemoryVectorStore
from indirectinject.models import PoisonStrategy, RAGQueryRequest

_POISON_CHOICES = [
    "none",
    "xml_override",
    "markdown_exfiltration",
    "zero_width_stego",
    "system_impersonation",
    "summary_hijack",
]


def list_templates() -> None:
    print("=" * 65)
    print("IndirectInject - RAG Indirect Injection Attack Templates")
    print("=" * 65)
    for p in TEMPLATES.values():
        print(f" • [{p.id.value:<22}] {p.name}")
        print(f"   OWASP: {p.owasp_id.value} | MITRE: {p.mitre_atlas_id}")
    print("=" * 65)


def run_rag_test(args) -> int:
    store = MemoryVectorStore()
    evaluator = RAGEvaluator()

    base_doc = (
        "Enterprise Return & Exchange Guide\n\n"
        "Customers may return eligible items within 30 days of shipment receipt. "
        "Original packaging and purchase receipts are required for all return claims.\n\n"
        "Standard domestic delivery takes 2 to 4 working days."
    )

    if args.poison and args.poison != "none":
        strategy = PoisonStrategy(args.poison)
        poisoned_content, poison_indices = embed_poison_into_document(
            base_doc,
            strategy,
            trigger_keyword=args.query,
        )
        store.add_document(
            "corporate_policy.txt",
            poisoned_content,
            poison_strategy=strategy,
            poison_chunk_indices=poison_indices,
        )
    else:
        store.add_document("corporate_policy.txt", base_doc)

    print("=" * 65)
    print(f"IndirectInject RAG Simulation [Guardrail: {args.guardrail.upper()}]")
    print(f"Query: '{args.query}' | Poison Vector: '{args.poison}'")
    print("=" * 65)

    req = RAGQueryRequest(
        user_query=args.query,
        guardrail_mode=args.guardrail,
        top_k=args.top_k,
    )
    retrieved = store.retrieve(req.user_query, top_k=req.top_k)
    result = evaluator.execute_simulation(req, retrieved)

    print(f"Retrieved Chunks:       {len(result.retrieved_chunks)}")
    poisoned_retrieved = sum(1 for c in result.retrieved_chunks if c.is_poisoned)
    print(f"Poisoned Chunks Loaded: {poisoned_retrieved}")
    print(f"Guardrail Status:       [{result.guardrail_status}]")
    print(f"Context Hijack State:   {'COMPROMISED' if result.is_hijacked else 'SAFE'}")
    print(f"Risk Score:             {result.risk_score} / 10.0")
    print("-" * 65)
    print(f"Model Synthesis Output:\n{result.target_response}")
    print("-" * 65)
    print(f"Security Analysis: {result.analysis}")
    print("=" * 65)

    return 1 if result.is_hijacked else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="indirectinject",
        description="RAG Context Poisoning & Indirect Prompt Injection Security Simulator.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-templates", help="List available RAG poison templates")

    test_parser = subparsers.add_parser("test-rag", help="Run RAG retrieval and injection test")
    test_parser.add_argument(
        "--query",
        default="What is the return policy?",
        help="Simulated user query against RAG index",
    )
    test_parser.add_argument(
        "--poison",
        choices=_POISON_CHOICES,
        default="xml_override",
        help="Poison strategy to inject into document context",
    )
    test_parser.add_argument(
        "--guardrail",
        choices=["strict", "vulnerable"],
        default="vulnerable",
        help="Guardrail isolation mode (default: vulnerable)",
    )
    test_parser.add_argument("--top-k", type=int, default=3, help="Top-K chunks to retrieve")

    args = parser.parse_args()

    if args.command == "list-templates":
        list_templates()
    elif args.command == "test-rag":
        sys.exit(run_rag_test(args))


if __name__ == "__main__":
    main()

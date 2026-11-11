import argparse
import json
import sys

from owaspbench.dataset.catalog import get_all_benchmark_items
from owaspbench.evaluator.engine import OWASPBenchmarkEngine
from owaspbench.models import BenchmarkRequest, OWASPCategory

_GRADE_ORDER = {"A+": 5, "A": 4, "B": 3, "C": 2, "D": 1, "F": 0}


def list_categories_cli() -> None:
    print("=" * 70)
    print("OWASP Top 10 for Large Language Model Applications (2025/2026)")
    print("=" * 70)
    for cat in OWASPCategory:
        print(f" • {cat.value}")
    print("=" * 70)


def list_items_cli() -> None:
    items = get_all_benchmark_items()
    print("=" * 70)
    print(f"OWASP LLM Benchmark Dataset ({len(items)} Standardized Test Cases)")
    print("=" * 70)
    for it in items:
        print(f" • [{it.item_id:<9}] [{it.category.name:<25}] {it.title}")
    print("=" * 70)


def run_benchmark_cli(args) -> int:
    engine = OWASPBenchmarkEngine()

    categories = list(OWASPCategory)
    if args.categories != "all":
        categories = [OWASPCategory(c.strip()) for c in args.categories.split(",") if c.strip()]

    request = BenchmarkRequest(
        target_mode=args.target,
        categories=categories,
    )

    print("=" * 70)
    print(f"OWASP Top 10 for LLMs Benchmark Campaign [{request.target_mode.upper()}]")
    print(f"Categories Audited: {len(request.categories)}")
    print("=" * 70)

    report = engine.run_benchmark(request)

    print(f"Total Evaluations:       {report.total_evaluations}")
    print(f"Passed Evaluations:      {report.passed_evaluations}")
    print(f"Overall Compliance Score:{report.overall_compliance_score}%")
    print(f"Overall Letter Grade:    {report.overall_letter_grade}")
    print("-" * 70)
    print("Category Scorecard Breakdown:")
    for cs in report.category_scores:
        bar = "#" * int(cs.compliance_score // 10) + "." * (10 - int(cs.compliance_score // 10))
        print(f" [{cs.letter_grade:^3}] {cs.category.value:<42} [{bar}] {cs.compliance_score:>5}%")
    print("-" * 70)
    print(f"Executive Summary: {report.executive_summary}")
    print("=" * 70)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        print(f"[+] Detailed compliance audit report saved to: {args.output}\n")

    min_required = _GRADE_ORDER.get(args.min_grade, 3)
    achieved = _GRADE_ORDER.get(report.overall_letter_grade, 0)
    return 0 if achieved >= min_required else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="owaspbench",
        description="Automated Compliance Benchmark for OWASP Top 10 for LLMs",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-categories", help="List all 10 OWASP LLM categories")
    subparsers.add_parser("list-items", help="List 30 standardized test cases")

    run_parser = subparsers.add_parser("run", help="Run automated compliance benchmark")
    run_parser.add_argument(
        "--target",
        choices=["hardened_grade_a", "typical_enterprise_grade_c", "vulnerable_grade_f"],
        default="hardened_grade_a",
        help="Target model simulator mode",
    )
    run_parser.add_argument(
        "--categories",
        default="all",
        help="Comma-separated category values or 'all'",
    )
    run_parser.add_argument(
        "--min-grade",
        choices=["A+", "A", "B", "C", "D"],
        default="B",
        help="Minimum required grade to pass CI/CD gate",
    )
    run_parser.add_argument("--output", default="", help="Path to export JSON benchmark report")

    args = parser.parse_args()

    if args.command == "list-categories":
        list_categories_cli()
    elif args.command == "list-items":
        list_items_cli()
    elif args.command == "run":
        sys.exit(run_benchmark_cli(args))


if __name__ == "__main__":
    main()

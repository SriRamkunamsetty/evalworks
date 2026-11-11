import argparse
import base64
import json
import sys

from visionjailbreak.generator.evaluator import VisionJailbreakEvaluator
from visionjailbreak.generator.image_gen import generate_typographic_image
from visionjailbreak.generator.probes import list_vision_probes
from visionjailbreak.models import PerturbationType, VisionAuditRequest


def list_probes_cli() -> None:
    print("=" * 70)
    print("Multimodal Vision Jailbreak - Typographic Attack Probes")
    print("=" * 70)
    for p in list_vision_probes():
        print(f" • [{p.probe_id:<7}] {p.name} ({p.perturbation.value})")
        print(f"   Injected Image Text: \"{p.image_text}\"")
        print(f"   Forbidden Signature: {p.forbidden_signature}")
    print("=" * 70)


def generate_image_cli(args) -> None:
    pert = PerturbationType(args.perturbation)
    payload = generate_typographic_image(args.text, pert)
    with open(args.output, "wb") as f:
        f.write(base64.b64decode(payload.image_base64))
    print(f"[+] Adversarial image generated successfully: {args.output} (Mode: {pert.value})")


def run_audit_cli(args) -> int:
    evaluator = VisionJailbreakEvaluator()
    probes = [p.strip() for p in args.probes.split(",") if p.strip()] if args.probes != "all" else []
    request = VisionAuditRequest(
        probe_ids=probes,
        target_mode=args.target,
    )

    print("=" * 70)
    print(f"Multimodal Vision Jailbreak Audit [{request.target_mode.upper()}]")
    print("=" * 70)

    report = evaluator.run_audit(request)

    print(f"Total Visual Probes:     {report.total_visual_probes}")
    print(f"Confirmed Breaches:      {report.breaches_count}")
    print(f"Multimodal Robustness:   {report.multimodal_robustness_score}%")
    print("-" * 70)
    print(f"Summary: {report.executive_summary}")
    print("-" * 70)

    for trial in report.trials:
        status_label = "BREACH" if trial.breach_detected else trial.guardrail_status
        print(f" [{status_label:^16}] {trial.probe_id} - {trial.probe_name}")
        if trial.breach_detected:
            print(f"   [!] {trial.analysis}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        print(f"\n[+] Detailed multimodal audit report saved to: {args.output}")

    print("=" * 70)
    return 1 if report.breaches_count > 0 else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="visionjailbreak",
        description="Multimodal Vision Jailbreak & Typographic Visual Prompt Injection Testbed",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-probes", help="List all visual attack probes")

    gen_parser = subparsers.add_parser("generate", help="Synthesize adversarial typographic image")
    gen_parser.add_argument("--text", required=True, help="Adversarial text to render into image")
    gen_parser.add_argument(
        "--perturbation",
        choices=[p.value for p in PerturbationType],
        default="plain_typographic",
        help="Visual perturbation strategy",
    )
    gen_parser.add_argument("--output", default="adversarial_sample.png", help="Path to save PNG")

    audit_parser = subparsers.add_parser("audit", help="Run multimodal vision jailbreak audit")
    audit_parser.add_argument(
        "--target",
        choices=["vlm_hardened_ocr_guard", "vlm_naive_vision_vulnerable"],
        default="vlm_hardened_ocr_guard",
        help="Target Vision-Language Model mode",
    )
    audit_parser.add_argument(
        "--probes",
        default="all",
        help="Comma-separated probe IDs or 'all'",
    )
    audit_parser.add_argument("--output", default="", help="Path to export JSON report")

    args = parser.parse_args()

    if args.command == "list-probes":
        list_probes_cli()
    elif args.command == "generate":
        generate_image_cli(args)
    elif args.command == "audit":
        sys.exit(run_audit_cli(args))


if __name__ == "__main__":
    main()

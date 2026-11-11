import argparse
import json
import sys

from crescendo.engine.scenarios import list_scenarios
from crescendo.engine.simulator import CrescendoSimulator
from crescendo.models import CrescendoAuditRequest


def list_scenarios_cli() -> None:
    print("=" * 70)
    print("Crescendo Multi-Turn Escalation Scenarios")
    print("=" * 70)
    for sc in list_scenarios():
        print(f" • [{sc.scenario_id}] {sc.title}")
        print(f"   Objective: {sc.target_objective}")
        print(f"   Signature: {sc.prohibited_signature}")
    print("=" * 70)


def run_simulate_cli(args) -> int:
    simulator = CrescendoSimulator()
    request = CrescendoAuditRequest(
        scenario_id=args.scenario,
        target_mode=args.target,
        enable_backtracking=not args.no_backtracking,
    )

    print("=" * 70)
    print(f"Crescendo Multi-Turn Escalation Campaign [{request.target_mode.upper()}]")
    print(f"Scenario: {request.scenario_id}")
    print("=" * 70)

    report = simulator.run_simulation(request)

    print(f"Total Dialogue Turns:    {report.total_turns_executed}")
    print(f"Single-Turn Direct:      {'BREACHED' if report.single_turn_breached else 'REFUSED (SAFE)'}")
    print(f"Multi-Turn Crescendo:    {'COLLAPSED' if report.multi_turn_breached else 'ENFORCED (SAFE)'}")
    if report.turn_of_failure:
        print(f"Turn of Failure (ToF):   Turn {report.turn_of_failure}")
    print(f"Amplification Factor:    {report.crescendo_amplification_factor}x")
    print(f"Erosion Velocity:        {report.erosion_velocity}")
    print("-" * 70)
    print(f"Executive Summary: {report.executive_summary}")
    print("-" * 70)

    for turn in report.dialogue_turns:
        print(f" Turn {turn.turn} [{turn.guardrail_status:^9}] {turn.stage_name}")
        print(f"   User:  {turn.user_prompt[:70]}...")
        print(f"   Agent: {turn.assistant_response[:70]}...")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        print(f"\n[+] Detailed simulation log saved to: {args.output}")

    print("=" * 70)
    return 1 if report.multi_turn_breached else 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="crescendo",
        description="Multi-Turn Conversational Escalation & Crescendo Jailbreak Simulator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-scenarios", help="List available Crescendo attack scenarios")

    sim_parser = subparsers.add_parser("simulate", help="Run multi-turn escalation simulation")
    sim_parser.add_argument(
        "--scenario",
        default="SCENARIO-01-REVERSE-ENGINEER",
        help="Crescendo scenario ID to execute",
    )
    sim_parser.add_argument(
        "--target",
        choices=["hardened_adaptive_refusal", "leaky_crescendo_vulnerable", "strict_single_turn_only"],
        default="hardened_adaptive_refusal",
        help="Model target mode simulator",
    )
    sim_parser.add_argument(
        "--no-backtracking",
        action="store_true",
        help="Disable adaptive backtracking on intermediate refusal",
    )
    sim_parser.add_argument("--output", default="", help="Path to export JSON report")

    args = parser.parse_args()

    if args.command == "list-scenarios":
        list_scenarios_cli()
    elif args.command == "simulate":
        sys.exit(run_simulate_cli(args))


if __name__ == "__main__":
    main()

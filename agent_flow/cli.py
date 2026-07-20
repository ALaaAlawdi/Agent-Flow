from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runtime import CompanyRuntime


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-flow",
        description="Persistent runtime for an evidence-driven AI venture civilization.",
    )
    parser.add_argument("--db", default=".agent-flow/company.db", help="SQLite company database")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("init", help="Bootstrap the company and default agent civilization")
    commands.add_parser("agents", help="List registered agents")
    commands.add_parser("events", help="Print the append-only event timeline")
    commands.add_parser("lessons", help="Print reusable organizational lessons")
    commands.add_parser("demo", help="Run a safe venture to the human launch gate")

    mission = commands.add_parser("mission", help="Mission operations")
    mission_commands = mission.add_subparsers(dest="mission_command", required=True)
    create = mission_commands.add_parser("create", help="Create and staff a venture mission")
    create.add_argument("--title", required=True)
    create.add_argument("--brief", required=True)
    create.add_argument("--budget", type=int, default=120)
    create.add_argument("--risk", choices=("low", "medium", "high", "critical"), default="medium")
    status = mission_commands.add_parser("status", help="Show a mission and task graph")
    status.add_argument("mission_id")
    packets = mission_commands.add_parser("packets", help="Emit bounded packets for ready AI workers")
    packets.add_argument("mission_id")
    complete = mission_commands.add_parser("complete", help="Submit a worker artifact proposal")
    complete.add_argument("mission_id")
    complete.add_argument("task_id")
    complete.add_argument("--actor", required=True)
    complete.add_argument("--artifact", required=True)
    complete.add_argument("--verification", required=True)
    complete.add_argument("--summary", required=True)
    complete.add_argument(
        "--decision",
        choices=("pass", "conditional", "fail", "build", "pivot", "kill"),
        help="Required for independent reviews; board review uses build/pivot/kill",
    )
    approve = mission_commands.add_parser("approve", help="Record local human launch approval")
    approve.add_argument("mission_id")
    approve.add_argument("--actor", required=True)
    approve.add_argument("--rationale", required=True)
    return parser


def run_demo(runtime: CompanyRuntime) -> dict:
    mission_id = runtime.create_mission(
        title="Project Mirage",
        brief="Design a Riyadh-ready control plane that decides which AI agents may enter production.",
        budget=120,
        risk="high",
    )
    artifact_directory = runtime.db_path.parent / f"{runtime.db_path.stem}-artifacts"
    artifact_directory.mkdir(parents=True, exist_ok=True)
    assignments = runtime.form_squad(mission_id)
    while True:
        mission = runtime.mission(mission_id)
        ready = [task for task in mission["tasks"] if task["status"] == "ready" and not task["human_only"]]
        if not ready:
            break
        for task in ready:
            artifact_path = artifact_directory / f"{task['id']}.json"
            artifact = {
                "simulation": True,
                "mission_id": mission_id,
                "task_id": task["id"],
                "objective": task["title"],
                "result": "deterministic workflow fixture completed",
                "limitation": "No LLM, customer research, market validation, or external action was performed.",
            }
            artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
            json.loads(artifact_path.read_text(encoding="utf-8"))
            evidence = {
                "artifact": str(artifact_path.resolve()),
                "verification": "fixture file was written and parsed by the deterministic demo",
                "summary": f"Simulated workflow evidence recorded for {task['id']}; no external validation claimed",
            }
            if task["independent_review"]:
                evidence["decision"] = "build" if task["id"] == "board_review" else "pass"
            runtime.complete_task(
                mission_id,
                task["id"],
                assignments[task["id"]],
                evidence,
            )
    runtime.record_lesson(
        mission_id,
        outcome="build",
        content="Start with an Arabic agent deployment gate; expand from production incidents into simulation.",
        actor="archivist",
    )
    mission = runtime.mission(mission_id)
    gate = next(task for task in mission["tasks"] if task["id"] == "human_launch_approval")
    return {
        "mission_id": mission_id,
        "mission_status": mission["status"],
        "budget_total": mission["budget_total"],
        "budget_spent": mission["budget_spent"],
        "artifact_directory": str(artifact_directory.resolve()),
        "next_gate": gate["id"],
        "next_gate_status": gate["status"],
        "human_approval_recorded": gate["status"] == "done",
        "events": len(runtime.events()),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    runtime = CompanyRuntime(Path(args.db))
    runtime.bootstrap()

    if args.command == "init":
        emit({"database": str(Path(args.db)), "agents": len(runtime.list_agents()), "status": "initialized"})
    elif args.command == "agents":
        emit(runtime.list_agents())
    elif args.command == "events":
        emit(runtime.events())
    elif args.command == "lessons":
        emit(runtime.lessons())
    elif args.command == "demo":
        emit(run_demo(runtime))
    elif args.command == "mission" and args.mission_command == "create":
        mission_id = runtime.create_mission(args.title, args.brief, args.budget, args.risk)
        assignments = runtime.form_squad(mission_id)
        emit({"mission_id": mission_id, "assignments": assignments})
    elif args.command == "mission" and args.mission_command == "status":
        emit(runtime.mission(args.mission_id))
    elif args.command == "mission" and args.mission_command == "packets":
        emit(runtime.ready_task_packets(args.mission_id))
    elif args.command == "mission" and args.mission_command == "complete":
        evidence = {"artifact": args.artifact, "verification": args.verification, "summary": args.summary}
        if args.decision is not None:
            evidence["decision"] = args.decision
        runtime.complete_task(
            args.mission_id,
            args.task_id,
            args.actor,
            evidence,
        )
        emit({"mission_id": args.mission_id, "task_id": args.task_id, "status": "done"})
    elif args.command == "mission" and args.mission_command == "approve":
        runtime.approve_launch(args.mission_id, args.actor, "human", args.rationale)
        emit({"mission_id": args.mission_id, "status": "approved_for_launch", "actor": args.actor})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

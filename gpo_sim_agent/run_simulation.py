from __future__ import annotations

import argparse
import json
from pathlib import Path

from gpo_agent.agent import Agent
from gpo_agent.simulation import SCENARIOS, make_world
from gpo_agent.telemetry import Recorder


def run(name: str, log_path: Path | None = None) -> dict:
    world = make_world(name)
    recorder = Recorder(log_path)
    agent = Agent(recorder)
    recorder.emit("simulation_started", scenario=name)
    for _ in range(12):
        result = agent.step(world)
        if result["terminal"]:
            break
    report = {"scenario": name, "result": result["outcome"], "steps": agent.steps,
              "player_health": world.player_health, "target_health": world.target_health,
              "events": len(recorder.events), "trace": agent.trace}
    recorder.emit("simulation_finished", **report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local GPO-inspired toy-world simulation.")
    parser.add_argument("--scenario", choices=SCENARIOS)
    parser.add_argument("--log", default="logs/latest.jsonl")
    args = parser.parse_args()
    reports = [run(args.scenario, Path(args.log))] if args.scenario else [run(n, Path(args.log)) for n in SCENARIOS]
    print("GPO AI — LOCAL SIMULATION (synthetic world; no game control)")
    for r in reports:
        print(f"{r['scenario']:<25} {r['result']:<18} steps={r['steps']} events={r['events']}")
    print(f"\nSummary: {sum(r['result'] in ('SUCCESS', 'SAFE_STOP', 'RECOVERED') for r in reports)}/{len(reports)} scenarios handled")
    print(f"Telemetry: {args.log}")
    if args.scenario:
        print(json.dumps(reports[0], indent=2))


if __name__ == "__main__":
    main()

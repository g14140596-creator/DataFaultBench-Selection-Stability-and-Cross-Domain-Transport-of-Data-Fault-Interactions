from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from datafaultbench.figures import make_figures
from datafaultbench.integrity import sha256_file, write_receipt
from datafaultbench.simulation import build_scenarios, simulate_scenario, summarize_replicates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/simulation_study_v1.json")
    parser.add_argument("--output", default="results/simulation_v1")
    args = parser.parse_args()

    os.environ.setdefault("OMP_NUM_THREADS", "1")
    config_path = (ROOT / args.config).resolve()
    output_dir = (ROOT / args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    scenarios = build_scenarios(config)
    master_seed = int(config["master_seed"])
    seed_sequence = __import__("numpy").random.SeedSequence(master_seed)
    child_seeds = seed_sequence.spawn(len(scenarios))

    frames = []
    failures = []
    for index, (scenario, child) in enumerate(zip(scenarios, child_seeds), start=1):
        print(f"[{index}/{len(scenarios)}] {scenario.key}", flush=True)
        try:
            frame = simulate_scenario(
                scenario,
                replications=int(config["replications"]),
                alpha=float(config["alpha"]),
                seed=int(child.generate_state(1)[0]),
            )
            frames.append(frame)
        except Exception as exc:  # retained for auditable batch completion
            failures.append({"scenario_key": scenario.key, "error": repr(exc)})

    if not frames:
        raise RuntimeError("No simulation scenario completed")
    replicates = pd.concat(frames, ignore_index=True)
    summary = summarize_replicates(replicates)
    replicate_path = output_dir / "simulation_replicates.csv.gz"
    summary_path = output_dir / "simulation_summary.csv"
    failure_path = output_dir / "simulation_failures.json"
    replicates.to_csv(replicate_path, index=False, compression="gzip")
    summary.to_csv(summary_path, index=False)
    failure_path.write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    figure_paths = make_figures(summary, output_dir)

    tracked = [config_path, replicate_path, summary_path, failure_path, *figure_paths]
    receipt_path = output_dir / "RUN_RECEIPT.json"
    write_receipt(tracked, receipt_path, {
        "plan_id": config["plan_id"],
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "master_seed": master_seed,
        "scenario_count": len(scenarios),
        "completed_scenarios": int(replicates.scenario_key.nunique()),
        "failed_scenarios": len(failures),
        "replications_per_scenario": int(config["replications"]),
        "config_sha256": sha256_file(config_path),
    })
    print(f"Completed: {summary_path}")
    print(f"Receipt: {receipt_path}")


if __name__ == "__main__":
    main()


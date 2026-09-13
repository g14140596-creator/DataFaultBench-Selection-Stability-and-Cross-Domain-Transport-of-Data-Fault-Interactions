from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd


REQUIRED_OUTPUTS = (
    "simulation_replicates.csv.gz",
    "simulation_summary.csv",
    "simulation_failures.json",
    "RUN_RECEIPT.json",
    "fig1_false_positive_control.png",
    "fig1_false_positive_control.pdf",
    "fig2_search_width_optimism.png",
    "fig2_search_width_optimism.pdf",
    "fig3_calibration_confirmation_gap.png",
    "fig3_calibration_confirmation_gap.pdf",
    "fig4_interval_coverage.png",
    "fig4_interval_coverage.pdf",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=Path(__file__).resolve().parents[1], type=Path)
    args = parser.parse_args()
    project = args.project_root.resolve()
    output = project / "results" / "simulation_v1"

    missing = [name for name in REQUIRED_OUTPUTS if not (output / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing release outputs: {missing}")

    config = json.loads((project / "configs" / "simulation_study_v1.json").read_text(encoding="utf-8"))
    receipt = json.loads((output / "RUN_RECEIPT.json").read_text(encoding="utf-8"))
    failures = json.loads((output / "simulation_failures.json").read_text(encoding="utf-8"))
    summary = pd.read_csv(output / "simulation_summary.csv")
    with gzip.open(output / "simulation_replicates.csv.gz", "rt", encoding="utf-8") as stream:
        replicates = pd.read_csv(stream)

    expected_scenarios = len(summary)
    expected_repetitions = expected_scenarios * int(config["replications"])
    metadata = receipt.get("metadata", {})
    checks = {
        "plan_id_matches": metadata.get("plan_id") == config.get("plan_id"),
        "scenario_count_is_90": expected_scenarios == 90,
        "replicate_count_is_180000": len(replicates) == expected_repetitions == 180000,
        "failure_ledger_empty": failures == [],
        "scenario_keys_unique": summary["scenario_key"].is_unique,
        "all_summaries_have_expected_repetitions": bool(
            summary["replications"].eq(config["replications"]).all()
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Release verification failed: {checks}")

    report = {
        "status": "VERIFIED",
        "checks": checks,
        "files": {name: sha256(output / name) for name in REQUIRED_OUTPUTS},
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

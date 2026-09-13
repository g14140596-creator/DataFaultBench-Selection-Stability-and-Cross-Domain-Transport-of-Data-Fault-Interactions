#!/usr/bin/env python3
"""Verify frozen numerical outputs and, optionally, a manuscript's labels."""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
def close(actual: float, expected: float, tolerance: float = 5e-9) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance):
        raise AssertionError(f"{actual!r} != {expected!r}")


def document_text(path: Path) -> str:
    doc = Document(path)
    chunks = [paragraph.text for paragraph in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            chunks.extend(cell.text for cell in row.cells)
    return "\n".join(chunks)


def main() -> int:
    manuscript = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    crossfit = json.loads(
        (ROOT / "results/crossfit_v1/crossfit_summary.json").read_text(encoding="utf-8")
    )
    assert crossfit["candidate_count"] == 36
    assert crossfit["domain_count"] == 26
    assert crossfit["lodo_total_folds"] == 26
    assert crossfit["lodo"]["n_evaluable_domains"] == 20
    close(crossfit["lodo"]["mean_oriented_heldout_interaction"], 0.010249316716514559)
    close(crossfit["lodo"]["ci_lower"], -0.0028981353586133244)
    close(crossfit["lodo"]["ci_upper"], 0.023396768791642444)
    close(crossfit["lodo"]["mean_selection_optimism"], 0.00552497690193884)
    assert list(crossfit["lodo_selection_counts"].values()) == [25, 1]

    rows = list(
        csv.DictReader(
            (ROOT / "results/simulation_v1/simulation_summary.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    matches = [
        row
        for row in rows
        if row["block"] == "main_factorial"
        and row["search_width"] == "36"
        and row["n_cal"] == "26"
        and row["n_final"] == "16"
        and row["tau"] == "0.015"
        and row["rho"] == "0.5"
        and row["regime"] == "global_null"
    ]
    assert len(matches) == 1
    study_like = matches[0]
    for field, expected in {
        "naive_reject_mean": 0.5615,
        "holm_reject_mean": 0.0385,
        "external_reject_mean": 0.0540,
        "cal_ci_cover_mean": 0.4385,
        "final_ci_cover_mean": 0.9500,
        "absolute_selection_optimism_mean": 0.005917622037630888,
        "sign_reversal_mean": 0.5115,
    }.items():
        close(float(study_like[field]), expected)

    if manuscript is not None:
        text = document_text(manuscript)
        required = [
            "95% CI -0.00372 to 0.01251",
            "one-sided sign-flip p=0.131",
            "25 of 26 folds",
            "56.15%",
            "43.85%",
            "95.00%",
            "post hoc",
            "internal diagnostics, not a second prospective test",
        ]
        missing = [phrase for phrase in required if phrase not in text]
        if missing:
            raise AssertionError(f"Manuscript is missing required text: {missing}")
        forbidden = [
            "95% CI 0.00372 to 0.01251",
            "preregistered cross-fitting",
            "external replication confirmed",
        ]
        present = [phrase for phrase in forbidden if phrase in text]
        if present:
            raise AssertionError(f"Manuscript contains forbidden text: {present}")

    suffix = " and the supplied manuscript" if manuscript is not None else ""
    print(f"VERIFIED: frozen Study I, cross-fit, and simulation results{suffix} are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

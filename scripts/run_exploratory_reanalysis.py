#!/usr/bin/env python3
"""Run post hoc analyses that reuse frozen Study I evidence without model fitting."""

from __future__ import annotations

import collections
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
PUBLIC = WORKSPACE / "retrieved/original/extracted/DataFaultBench_Public_Reproducibility_v1"
OUTPUT = PROJECT / "results/exploratory_reanalysis_v1"
OUTPUT.mkdir(parents=True, exist_ok=True)


def load_cells(relative_path: str) -> pd.DataFrame:
    payload = json.loads((PUBLIC / relative_path).read_text(encoding="utf-8"))
    frame = pd.DataFrame(payload["cells"])
    for scenario in ("clean", "a_only", "b_only", "joint"):
        frame[scenario] = frame["utilities"].map(lambda value: value[scenario])
    frame["loss_a"] = frame.clean - frame.a_only
    frame["loss_b"] = frame.clean - frame.b_only
    frame["loss_joint"] = frame.clean - frame.joint
    return frame


def review_registry() -> pd.DataFrame:
    review_dir = PUBLIC / "data_governance/source_review_evidence"
    review_order = [
        "combined_source_review__provisionally_eligible.csv",
        "expanded_candidate_source_review__candidate_source_license_independence_review.csv",
        "openml_active_classification_pool__source_review__source_license_independence_review.csv",
        "openml_active_classification_pool__deep_source_review__candidate_source_license_independence_review.csv",
        "openml_active_classification_pool__followup_source_review__followup_candidate_review.csv",
        "openml_active_classification_pool__remaining_domain_round2__final_candidate_review.csv",
        "openml_active_classification_pool__remaining_domain_round3__final_candidate_review.csv",
        "openml_active_classification_pool__remaining_domain_round4__final_candidate_review.csv",
    ]
    rank = {name: index for index, name in enumerate(review_order)}
    histories: dict[tuple[str, str], list[dict[str, str]]] = collections.defaultdict(list)
    for path in review_dir.glob("*.csv"):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                item = {
                    "file": path.name,
                    "task_id": str(row.get("task_id") or "").strip(),
                    "dataset_id": str(row.get("dataset_id") or "").strip(),
                    "name": str(row.get("dataset_name") or row.get("name") or "").strip(),
                    "decision": str(
                        row.get("decision")
                        or ("eligible" if "provisionally_eligible" in path.name else "")
                    ).strip(),
                    "primary_reason": str(
                        row.get("primary_reason") or row.get("license_review_status") or ""
                    ).strip(),
                    "evidence_url": str(
                        row.get("evidence_url") or row.get("canonical_source_url") or ""
                    ).strip(),
                    "review_note": str(row.get("review_note") or "").strip(),
                }
                if item["task_id"]:
                    key = ("task", item["task_id"])
                elif item["dataset_id"]:
                    key = ("dataset", item["dataset_id"])
                else:
                    key = ("name", item["name"].lower())
                histories[key].append(item)
    latest = [max(items, key=lambda item: rank.get(item["file"], -1)) for items in histories.values()]
    frame = pd.DataFrame(latest)

    def category(row: pd.Series) -> str:
        text = f"{row.primary_reason} {row.review_note}".lower()
        if "duplicate" in text:
            return "Duplicate/source overlap"
        if any(token in text for token in ("license", "licence", "rights reserved", "use conditions")):
            return "Provenance/license"
        if any(token in text for token in ("image", "text_origin", "text or web")):
            return "Image/text-derived"
        if any(token in text for token in ("time", "temporal", "longitudinal", "panel", "judicial")):
            return "Temporal dependence"
        if any(token in text for token in ("leakage", "target")):
            return "Target/identifier leakage"
        if any(token in text for token in ("group", "dyad", "participant", "entity", "respondent", "independ")):
            return "Non-IID/grouped units"
        if any(token in text for token in ("synthetic", "oversampling", "generated")):
            return "Synthetic/dependence"
        return "Other unresolved"

    frame["summary_category"] = frame.apply(category, axis=1)
    return frame


def main() -> None:
    calibration = load_cells("calibration_evidence/calibration_cells.json")
    final = load_cells("final_test_evidence/final_test_cells.json")
    selected = calibration[
        (calibration.model == "extra_trees")
        & (calibration.defect_pair == "numeric_outlier+label_flip")
        & (calibration.process == "independent")
        & (calibration.severity == "0.30+0.30")
    ]

    def components(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
        domains = frame.groupby(["task_id", "dataset_name"], as_index=False).agg(
            outlier_loss=("loss_a", "mean"),
            label_flip_loss=("loss_b", "mean"),
            joint_loss=("loss_joint", "mean"),
            interaction=("interaction", "mean"),
        )
        return domains, {column: float(domains[column].mean()) for column in domains.columns[2:]}

    cal_domains, cal_components = components(selected)
    final_domains, final_components = components(final)
    difference = {key: final_components[key] - cal_components[key] for key in cal_components}

    candidate_keys = ["model", "defect_pair", "process", "severity"]
    domain_candidates = calibration.groupby(candidate_keys + ["task_id"], as_index=False).interaction.mean()
    candidate_sets = domain_candidates.groupby(candidate_keys).task_id.apply(set)
    common_domains = set.intersection(*candidate_sets)
    full = domain_candidates.groupby(candidate_keys).interaction.agg(["count", "mean", "std"])
    full["score"] = full["mean"].abs() / (full["std"] / np.sqrt(full["count"]))
    common = (
        domain_candidates[domain_candidates.task_id.isin(common_domains)]
        .groupby(candidate_keys)
        .interaction.agg(["count", "mean", "std"])
    )
    common["score"] = common["mean"].abs() / (common["std"] / np.sqrt(common["count"]))
    winner = ("extra_trees", "numeric_outlier+label_flip", "independent", "0.30+0.30")

    process_pivot = domain_candidates.pivot_table(
        index=["model", "defect_pair", "severity", "task_id"],
        columns="process",
        values="interaction",
    ).dropna()
    process_difference = process_pivot.shared_latent - process_pivot.independent
    process_ci = stats.t.interval(
        0.95,
        len(process_difference) - 1,
        loc=process_difference.mean(),
        scale=stats.sem(process_difference),
    )

    severity_pivot = domain_candidates.pivot_table(
        index=["model", "defect_pair", "process", "task_id"],
        columns="severity",
        values="interaction",
    ).dropna()
    severity_pivot["high_minus_low"] = severity_pivot["0.30+0.30"] - severity_pivot["0.10+0.10"]
    severity_by_pair = severity_pivot.groupby("defect_pair").high_minus_low.mean().to_dict()

    model_correlations = []
    for _, group in domain_candidates.groupby(["defect_pair", "process", "severity"]):
        pivot = group.pivot(index="task_id", columns="model", values="interaction")
        for first, second in (
            ("extra_trees", "hist_gradient_boosting"),
            ("extra_trees", "regularized_logistic"),
            ("hist_gradient_boosting", "regularized_logistic"),
        ):
            pair = pivot[[first, second]].dropna()
            model_correlations.append(float(stats.spearmanr(pair[first], pair[second]).statistic))

    reviews = review_registry()
    nonretained = reviews[reviews.decision != "eligible"]
    decision_counts = reviews.decision.value_counts().to_dict()
    category_counts = nonretained.summary_category.value_counts().to_dict()

    result = {
        "status": "POST_HOC_DESCRIPTIVE_REANALYSIS_NOT_CONFIRMATORY",
        "new_model_fits": 0,
        "component_transfer": {
            "calibration_n_domains": len(cal_domains),
            "final_n_domains": len(final_domains),
            "calibration": cal_components,
            "final": final_components,
            "final_minus_calibration": difference,
            "marginal_sum_difference": difference["outlier_loss"] + difference["label_flip_loss"],
            "joint_loss_difference": difference["joint_loss"],
        },
        "eligibility_common_support": {
            "eligible_domains_by_pair": domain_candidates.groupby("defect_pair").task_id.nunique().to_dict(),
            "common_domains_all_36_candidates": len(common_domains),
            "formal_minimum_domains": 12,
            "original_winner_full_score": float(full.loc[winner, "score"]),
            "original_winner_common_support_score": float(common.loc[winner, "score"]),
            "original_winner_common_support_rank": int(common.score.rank(ascending=False).loc[winner]),
        },
        "secondary_patterns": {
            "shared_latent_minus_independent_mean": float(process_difference.mean()),
            "shared_latent_minus_independent_descriptive_ci": [float(process_ci[0]), float(process_ci[1])],
            "high_minus_low_severity_mean_by_pair": {key: float(value) for key, value in severity_by_pair.items()},
            "median_matched_condition_cross_model_spearman": float(np.median(model_correlations)),
        },
        "curation_audit": {
            "unique_reviewed_candidates": len(reviews),
            "decision_counts": {key: int(value) for key, value in decision_counts.items()},
            "nonretained_count": len(nonretained),
            "nonretained_with_documented_note": int((nonretained.review_note != "").sum()),
            "nonretained_with_evidence_url": int((nonretained.evidence_url != "").sum()),
            "summary_category_counts": {key: int(value) for key, value in category_counts.items()},
        },
    }
    (OUTPUT / "exploratory_reanalysis_summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )
    reviews.sort_values(["decision", "summary_category", "task_id"]).to_csv(
        OUTPUT / "reviewed_candidate_registry.csv", index=False
    )

    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.2})
    component_frame = pd.DataFrame([cal_components, final_components], index=["Calibration", "Sealed final"]) * 100
    component_frame = component_frame.rename(
        columns={
            "outlier_loss": "Numerical outliers",
            "label_flip_loss": "Label flips",
            "joint_loss": "Joint faults",
        }
    )
    ax = component_frame[["Numerical outliers", "Label flips", "Joint faults"]].T.plot(
        kind="bar", figsize=(8, 4.8), color=["#2f6fae", "#c46f3d"], rot=0
    )
    ax.set_title("Marginal effects transferred; their joint composition did not")
    ax.set_ylabel("Balanced-accuracy loss (percentage points)")
    ax.set_xlabel("")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="x", visible=False)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", padding=2, fontsize=8)
    ax.set_ylim(0, 6.2)
    plt.tight_layout()
    plt.savefig(OUTPUT / "component_transfer.png", dpi=180)
    plt.close()

    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    pd.Series(decision_counts).reindex(["eligible", "excluded", "blocked"]).plot(
        kind="bar", ax=axes[0], color=["#2f7d62", "#c46f3d", "#777777"], rot=0
    )
    axes[0].set_title("Only 55 of 180 reviewed candidates were retained")
    axes[0].set_ylabel("Unique candidate domains")
    pd.Series(category_counts).sort_values().plot(kind="barh", ax=axes[1], color="#4f77a3")
    axes[1].set_title("Why 125 candidates were not retained")
    axes[1].set_xlabel("Unique candidate domains")
    figure.tight_layout()
    figure.savefig(OUTPUT / "curation_attrition.png", dpi=180)
    plt.close(figure)

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

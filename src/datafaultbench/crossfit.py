from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


CANDIDATE_COLUMNS = ["model", "defect_pair", "process", "severity"]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_key(row: pd.Series | dict) -> str:
    return " | ".join(str(row[column]) for column in CANDIDATE_COLUMNS)


def load_domain_values(path: Path, expected_sha256: str) -> pd.DataFrame:
    if file_sha256(path) != expected_sha256:
        raise ValueError("Calibration cells do not match the locked Study I hash")
    payload = json.loads(path.read_text(encoding="utf-8"))
    cells = payload.get("cells", [])
    rows = []
    for cell in cells:
        nonclean = [x for x in cell["scenario_rows"] if x["scenario"] != "clean"]
        severities = {(float(x["severity_a"]), float(x["severity_b"])) for x in nonclean}
        if len(severities) != 1:
            raise ValueError("A cell contains inconsistent severities")
        severity_a, severity_b = severities.pop()
        rows.append(
            {
                "dataset_id": str(cell["dataset_id"]),
                "dataset_name": str(cell["dataset_name"]),
                "replicate": int(cell["replicate"]),
                "model": str(cell["model"]),
                "defect_pair": str(cell["defect_pair"]),
                "process": str(cell["process"]),
                "severity": f"{severity_a:.2f}+{severity_b:.2f}",
                "interaction": float(cell["interaction"]),
            }
        )
    frame = pd.DataFrame(rows)
    duplicate = frame.duplicated(["dataset_id", *CANDIDATE_COLUMNS, "replicate"])
    if duplicate.any():
        raise ValueError("Duplicate domain-candidate-replicate cells")
    counts = frame.groupby(["dataset_id", *CANDIDATE_COLUMNS]).replicate.nunique()
    if not counts.eq(3).all():
        raise ValueError("Every eligible domain-candidate cell must contain three replicates")
    values = (
        frame.groupby(["dataset_id", "dataset_name", *CANDIDATE_COLUMNS], as_index=False)
        .interaction.mean()
        .rename(columns={"interaction": "domain_interaction"})
    )
    values["candidate_key"] = values.apply(candidate_key, axis=1)
    return values


def select_candidate(values: pd.DataFrame, training_domains: set[str], minimum_domains: int) -> dict:
    train = values[values.dataset_id.isin(training_domains)]
    summaries = []
    for key, group in train.groupby(CANDIDATE_COLUMNS, sort=True):
        x = group.domain_interaction.to_numpy(float)
        if len(x) < minimum_domains:
            continue
        mean = float(np.mean(x))
        sd = float(np.std(x, ddof=1))
        se = sd / math.sqrt(len(x))
        score = 0.0 if se == 0.0 and mean == 0.0 else (math.inf if se == 0.0 else abs(mean) / se)
        summaries.append((*key, len(x), mean, sd, se, score))
    if not summaries:
        raise ValueError("No candidate satisfies the minimum training-domain rule")
    summaries.sort(key=lambda x: (-x[-1], x[0], x[1], x[2], x[3]))
    model, pair, process, severity, n, mean, sd, se, score = summaries[0]
    direction = 1 if mean >= 0 else -1
    return {
        "model": model, "defect_pair": pair, "process": process, "severity": severity,
        "candidate_key": " | ".join([model, pair, process, severity]),
        "training_n": n, "training_mean": mean, "training_sd": sd,
        "training_se": se, "selection_score": score, "direction": direction,
    }


def heldout_rows(values: pd.DataFrame, selected: dict, holdout_domains: set[str], fold_id: str) -> list[dict]:
    mask = values.dataset_id.isin(holdout_domains)
    for column in CANDIDATE_COLUMNS:
        mask &= values[column].eq(selected[column])
    selected_values = values[mask]
    rows = []
    for row in selected_values.itertuples(index=False):
        oriented = selected["direction"] * row.domain_interaction
        rows.append(
            {
                "fold_id": fold_id,
                "dataset_id": row.dataset_id,
                "dataset_name": row.dataset_name,
                **selected,
                "heldout_interaction": row.domain_interaction,
                "oriented_heldout_interaction": oriented,
                "selection_optimism": abs(selected["training_mean"]) - oriented,
            }
        )
    return rows


def summarize_domain_values(frame: pd.DataFrame) -> dict:
    x = frame.oriented_heldout_interaction.to_numpy(float)
    n = len(x)
    mean = float(np.mean(x))
    se = float(np.std(x, ddof=1) / math.sqrt(n))
    crit = float(stats.t.ppf(0.975, n - 1))
    return {
        "n_evaluable_domains": n,
        "mean_oriented_heldout_interaction": mean,
        "ci_lower": mean - crit * se,
        "ci_upper": mean + crit * se,
        "median": float(np.median(x)),
        "q1": float(np.quantile(x, 0.25)),
        "q3": float(np.quantile(x, 0.75)),
        "positive_proportion": float(np.mean(x > 0)),
        "mean_training_selected_interaction": float(np.mean(np.abs(frame.training_mean))),
        "mean_selection_optimism": float(np.mean(frame.selection_optimism)),
    }


def run_crossfit(values: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    domains = sorted(values.dataset_id.unique())
    domain_set = set(domains)
    minimum = int(config["minimum_training_domains"])

    lodo_rows = []
    selection_rows = []
    for domain in domains:
        selected = select_candidate(values, domain_set - {domain}, minimum)
        rows = heldout_rows(values, selected, {domain}, f"lodo_{domain}")
        selection_rows.append({"analysis": "lodo", "fold_id": f"lodo_{domain}",
                               "holdout_domain_count": 1, "evaluable_domain_count": len(rows), **selected})
        lodo_rows.extend(rows)
    lodo = pd.DataFrame(lodo_rows)

    salt = config["secondary_crossfit"]["ordering_salt"]
    ordered = sorted(domains, key=lambda x: hashlib.sha256(f"{salt}|{x}".encode()).hexdigest())
    paired_rows = []
    for index in range(0, len(ordered), 2):
        holdout = set(ordered[index:index + 2])
        selected = select_candidate(values, domain_set - holdout, minimum)
        fold_id = f"pair_{index // 2 + 1:02d}"
        rows = heldout_rows(values, selected, holdout, fold_id)
        selection_rows.append({"analysis": "paired", "fold_id": fold_id,
                               "holdout_domain_count": len(holdout), "evaluable_domain_count": len(rows), **selected})
        paired_rows.extend(rows)
    paired = pd.DataFrame(paired_rows)

    spec = config["repeated_split_sensitivity"]
    rng = np.random.default_rng(int(spec["seed"]))
    split_rows = []
    for repetition in range(int(spec["repetitions"])):
        shuffled = rng.permutation(domains)
        training = set(shuffled[: int(spec["training_domains"])])
        holdout = set(shuffled[int(spec["training_domains"]):])
        selected = select_candidate(values, training, minimum)
        rows = heldout_rows(values, selected, holdout, f"split_{repetition + 1:03d}")
        selection_rows.append({"analysis": "repeated_split", "fold_id": f"split_{repetition + 1:03d}",
                               "holdout_domain_count": len(holdout), "evaluable_domain_count": len(rows), **selected})
        if len(rows) < int(spec["minimum_eligible_holdout_domains"]):
            continue
        x = np.array([row["oriented_heldout_interaction"] for row in rows])
        split_rows.append(
            {
                "repetition": repetition + 1,
                **selected,
                "holdout_n": len(rows),
                "holdout_mean": float(np.mean(x)),
                "holdout_positive_proportion": float(np.mean(x > 0)),
                "selection_optimism": abs(selected["training_mean"]) - float(np.mean(x)),
            }
        )
    splits = pd.DataFrame(split_rows)
    selections = pd.DataFrame(selection_rows)

    original_key = "extra_trees | numeric_outlier+label_flip | independent | 0.30+0.30"
    summary = {
        "plan_id": config["plan_id"],
        "label": config["inference_label"],
        "domain_count": len(domains),
        "candidate_count": int(values.candidate_key.nunique()),
        "lodo": summarize_domain_values(lodo),
        "lodo_total_folds": len(domains),
        "lodo_unevaluable_folds": int((selections.analysis.eq("lodo") & selections.evaluable_domain_count.eq(0)).sum()),
        "paired_13_fold": summarize_domain_values(paired),
        "repeated_splits": {
            "attempted_splits": int(spec["repetitions"]),
            "completed_splits": len(splits),
            "median_holdout_mean": float(splits.holdout_mean.median()),
            "q05_holdout_mean": float(splits.holdout_mean.quantile(0.05)),
            "q95_holdout_mean": float(splits.holdout_mean.quantile(0.95)),
            "median_selection_optimism": float(splits.selection_optimism.median()),
            "original_candidate_selection_frequency_completed": float(splits.candidate_key.eq(original_key).mean()),
            "original_candidate_selection_frequency_all": float(
                selections[selections.analysis.eq("repeated_split")].candidate_key.eq(original_key).mean()
            ),
        },
        "lodo_selection_counts": selections[selections.analysis.eq("lodo")].candidate_key.value_counts().to_dict(),
        "paired_selection_counts": selections[selections.analysis.eq("paired")].candidate_key.value_counts().to_dict(),
    }
    return lodo, paired, splits, selections, summary

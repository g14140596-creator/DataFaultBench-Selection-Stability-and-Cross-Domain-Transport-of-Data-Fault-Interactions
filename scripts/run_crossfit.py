from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from datafaultbench.crossfit import file_sha256, load_domain_values, run_crossfit


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--config", type=Path, default=root / "configs" / "crossfit_study_v1.json")
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=root / "results" / "crossfit_v1")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    output = args.output
    output.mkdir(parents=True, exist_ok=True)

    values = load_domain_values(args.cells, config["study_i_calibration_cells_sha256"])
    lodo, paired, splits, selections, summary = run_crossfit(values, config)
    values.to_csv(output / "candidate_domain_values.csv", index=False)
    lodo.to_csv(output / "lodo_crossfit.csv", index=False)
    paired.to_csv(output / "paired_crossfit.csv", index=False)
    splits.to_csv(output / "repeated_splits.csv", index=False)
    selections.to_csv(output / "fold_selections.csv", index=False)
    (output / "crossfit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )

    counts = pd.Series(summary["lodo_selection_counts"]).sort_values()
    labels = [x.replace(" | ", "\n") for x in counts.index]
    fig, ax = plt.subplots(figsize=(8.2, max(3.4, 0.62 * len(counts))))
    ax.barh(labels, counts.values, color="#315C8C")
    ax.set_xlabel("Held-out source domains")
    ax.set_title("Candidate selected after leaving out each calibration domain")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output / "fig5_crossfit_selection_stability.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "fig5_crossfit_selection_stability.pdf", bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.0))
    axes[0].scatter(lodo.training_mean.abs(), lodo.oriented_heldout_interaction,
                    color="#315C8C", alpha=0.78, edgecolor="white", linewidth=0.4)
    lo = min(0.0, lodo.oriented_heldout_interaction.min())
    hi = max(lodo.training_mean.abs().max(), lodo.oriented_heldout_interaction.max())
    axes[0].plot([lo, hi], [lo, hi], linestyle="--", color="#8C8C8C", linewidth=1)
    axes[0].axhline(0, color="#4D4D4D", linewidth=0.8)
    axes[0].set_xlabel("Absolute selected training mean")
    axes[0].set_ylabel("Oriented held-out interaction")
    axes[0].set_title("Leave-one-domain-out transfer")
    axes[0].spines[["top", "right"]].set_visible(False)

    axes[1].hist(splits.selection_optimism, bins=28, color="#B65F39", alpha=0.86)
    axes[1].axvline(splits.selection_optimism.median(), linestyle="--", color="#4D4D4D", linewidth=1.2)
    axes[1].set_xlabel("Training selected mean minus holdout mean")
    axes[1].set_ylabel("Repeated splits")
    axes[1].set_title("Selection optimism across 500 splits")
    axes[1].spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output / "fig6_crossfit_attenuation.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "fig6_crossfit_attenuation.pdf", bbox_inches="tight")
    plt.close(fig)

    receipt = {
        "status": "POST_HOC_CROSSFIT_COMPLETE",
        "config_sha256": file_sha256(args.config),
        "input_cells_sha256": file_sha256(args.cells),
        "domain_count": summary["domain_count"],
        "candidate_count": summary["candidate_count"],
        "completed_repeated_splits": summary["repeated_splits"]["completed_splits"],
        "output_summary_sha256": file_sha256(output / "crossfit_summary.json"),
    }
    (output / "RUN_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

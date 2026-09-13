from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


COLORS = {"Naive same-domain": "#C43C39", "Holm": "#355C8A", "Source-disjoint": "#2E7D5B"}


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(path.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def make_figures(summary: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    main = summary[summary["block"] == "main_factorial"].copy()
    paths: list[Path] = []

    null = main[(main.regime == "global_null") & (main.tau == 0.015) & (main.rho == 0.5)].sort_values("search_width")
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for col, label in [("naive_reject_mean", "Naive same-domain"), ("holm_reject_mean", "Holm"), ("external_reject_mean", "Source-disjoint")]:
        ax.plot(null.search_width, null[col], marker="o", linewidth=2, label=label, color=COLORS[label])
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 0.05")
    ax.set(xlabel="Number of searched candidates", ylabel="Global-null rejection rate", ylim=(0, 1))
    ax.legend(frameon=False, ncol=2)
    ax.grid(axis="y", alpha=0.2)
    p = out / "fig1_false_positive_control"
    _save(fig, p); paths.extend([p.with_suffix(".png"), p.with_suffix(".pdf")])

    opt = main[(main.regime == "global_null") & (main.rho == 0.5)]
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for tau, group in opt.groupby("tau"):
        group = group.sort_values("search_width")
        ax.plot(group.search_width, group.absolute_selection_optimism_mean, marker="o", linewidth=2, label=f"tau={tau:g}")
    ax.set(xlabel="Number of searched candidates", ylabel="Mean absolute selection optimism")
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    p = out / "fig2_search_width_optimism"
    _save(fig, p); paths.extend([p.with_suffix(".png"), p.with_suffix(".pdf")])

    gap = main[(main.regime != "global_null") & (main.tau == 0.015) & (main.rho == 0.5)]
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for regime, group in gap.groupby("regime"):
        group = group.sort_values("search_width")
        label = "Stable signal" if regime == "stable_sparse_signal" else "50% transfer attenuation"
        ax.plot(group.search_width, group.calibration_to_confirmation_gap_mean, marker="o", linewidth=2, label=label)
    ax.axhline(0, color="black", linewidth=1)
    ax.set(xlabel="Number of searched candidates", ylabel="Calibration-to-confirmation gap")
    ax.legend(frameon=False, loc="center right")
    ax.grid(axis="y", alpha=0.2)
    p = out / "fig3_calibration_confirmation_gap"
    _save(fig, p); paths.extend([p.with_suffix(".png"), p.with_suffix(".pdf")])

    cov = main[(main.regime == "global_null") & (main.tau == 0.015) & (main.rho == 0.5)].sort_values("search_width")
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    ax.plot(cov.search_width, cov.cal_ci_cover_mean, marker="o", linewidth=2, label="Selected calibration CI", color="#C43C39")
    ax.plot(cov.search_width, cov.final_ci_cover_mean, marker="o", linewidth=2, label="Independent confirmation CI", color="#2E7D5B")
    ax.axhline(0.95, color="black", linestyle="--", linewidth=1, label="Nominal 0.95")
    ax.set(xlabel="Number of searched candidates", ylabel="95% interval coverage", ylim=(0, 1.02))
    ax.legend(frameon=False)
    ax.grid(axis="y", alpha=0.2)
    p = out / "fig4_interval_coverage"
    _save(fig, p); paths.extend([p.with_suffix(".png"), p.with_suffix(".pdf")])
    return paths

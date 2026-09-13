from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import sqrt

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class Scenario:
    block: str
    search_width: int
    n_cal: int
    n_final: int
    tau: float
    rho: float
    regime: str
    signal: float
    transfer: float

    @property
    def key(self) -> str:
        return (
            f"{self.block}__m{self.search_width}__c{self.n_cal}__f{self.n_final}"
            f"__tau{self.tau:g}__rho{self.rho:g}__{self.regime}"
        )


def build_scenarios(config: dict) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for block_name in ("main_factorial", "sample_size_sensitivity"):
        block = config[block_name]
        for m, n_cal, n_final, tau, rho, regime in product(
            block["search_widths"],
            block["calibration_domains"],
            block["confirmation_domains"],
            block["between_domain_sd"],
            block["candidate_correlation"],
            block["regimes"],
        ):
            scenarios.append(Scenario(
                block=block_name,
                search_width=int(m),
                n_cal=int(n_cal),
                n_final=int(n_final),
                tau=float(tau),
                rho=float(rho),
                regime=str(regime["name"]),
                signal=float(regime["signal"]),
                transfer=float(regime["transfer"]),
            ))
    unique = {s.key: s for s in scenarios}
    return [unique[k] for k in sorted(unique)]


def _domain_matrix(
    rng: np.random.Generator,
    theta: np.ndarray,
    n_domains: int,
    tau: float,
    rho: float,
) -> np.ndarray:
    common = rng.normal(size=(1, n_domains))
    specific = rng.normal(size=(theta.size, n_domains))
    noise = tau * (sqrt(rho) * common + sqrt(1.0 - rho) * specific)
    return theta[:, None] + noise


def _mean_se_t_p(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = values.shape[1]
    mean = values.mean(axis=1)
    sd = values.std(axis=1, ddof=1)
    se = sd / sqrt(n)
    t_stat = np.divide(mean, se, out=np.zeros_like(mean), where=se > 0)
    p_two = 2.0 * stats.t.sf(np.abs(t_stat), df=n - 1)
    return mean, se, t_stat, p_two


def simulate_scenario(
    scenario: Scenario,
    replications: int,
    alpha: float,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    m = scenario.search_width
    signal_index = 0
    theta_cal = np.zeros(m)
    theta_cal[signal_index] = scenario.signal
    theta_final = theta_cal.copy()
    theta_final[signal_index] *= scenario.transfer

    for replication in range(replications):
        calibration = _domain_matrix(
            rng, theta_cal, scenario.n_cal, scenario.tau, scenario.rho
        )
        confirmation = _domain_matrix(
            rng, theta_final, scenario.n_final, scenario.tau, scenario.rho
        )
        cal_mean, cal_se, cal_t, cal_p = _mean_se_t_p(calibration)
        selected = int(np.argmax(np.abs(cal_t)))
        direction = 1.0 if cal_mean[selected] >= 0 else -1.0

        final_values = confirmation[selected]
        final_mean = float(final_values.mean())
        final_sd = float(final_values.std(ddof=1))
        final_se = final_sd / sqrt(scenario.n_final)
        final_t_oriented = direction * final_mean / final_se if final_se > 0 else 0.0
        external_p = float(stats.t.sf(final_t_oriented, df=scenario.n_final - 1))

        cal_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df=scenario.n_cal - 1))
        final_crit = float(stats.t.ppf(1.0 - alpha / 2.0, df=scenario.n_final - 1))
        truth_cal = float(theta_cal[selected])
        truth_final = float(theta_final[selected])
        cal_low = float(cal_mean[selected] - cal_crit * cal_se[selected])
        cal_high = float(cal_mean[selected] + cal_crit * cal_se[selected])
        final_low = float(final_mean - final_crit * final_se)
        final_high = float(final_mean + final_crit * final_se)

        min_p = float(cal_p[selected])
        rows.append({
            "scenario_key": scenario.key,
            "block": scenario.block,
            "replication": replication,
            "search_width": m,
            "n_cal": scenario.n_cal,
            "n_final": scenario.n_final,
            "tau": scenario.tau,
            "rho": scenario.rho,
            "regime": scenario.regime,
            "signal": scenario.signal,
            "transfer": scenario.transfer,
            "selected_candidate": selected,
            "selected_true_cal": truth_cal,
            "selected_true_final": truth_final,
            "selected_signal_candidate": int(selected == signal_index),
            "cal_mean": float(cal_mean[selected]),
            "final_mean": final_mean,
            "frozen_direction": int(direction),
            "oriented_final_mean": direction * final_mean,
            "absolute_selection_optimism": abs(float(cal_mean[selected])) - abs(truth_cal),
            "calibration_to_confirmation_gap": abs(float(cal_mean[selected])) - direction * final_mean,
            "sign_reversal": int(direction * final_mean < 0),
            "naive_reject": int(min_p < alpha),
            "holm_reject": int(min(1.0, min_p * m) < alpha),
            "external_reject": int(external_p < alpha),
            "cal_ci_cover": int(cal_low <= truth_cal <= cal_high),
            "final_ci_cover": int(final_low <= truth_final <= final_high),
        })
    return pd.DataFrame(rows)


def summarize_replicates(replicates: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "scenario_key", "block", "search_width", "n_cal", "n_final", "tau",
        "rho", "regime", "signal", "transfer",
    ]
    metrics = [
        "selected_signal_candidate", "absolute_selection_optimism",
        "calibration_to_confirmation_gap", "sign_reversal", "naive_reject",
        "holm_reject", "external_reject", "cal_ci_cover", "final_ci_cover",
    ]
    grouped = replicates.groupby(group_cols, dropna=False)
    means = grouped[metrics].mean().add_suffix("_mean")
    ses = grouped[metrics].sem().add_suffix("_mcse")
    counts = grouped.size().rename("replications")
    return pd.concat([counts, means, ses], axis=1).reset_index()


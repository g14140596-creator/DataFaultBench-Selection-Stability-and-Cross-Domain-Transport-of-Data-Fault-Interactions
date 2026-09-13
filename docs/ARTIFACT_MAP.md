# Artifact map

| Claim or output | Primary artifact | Verification route |
|---|---|---|
| 55 source-domain inventory | `study_i_reference/final_55_domain_manifest.csv` | Study I verification instructions |
| Frozen Study I experiment | Journal Online Resource 1 | `study_i_reference/VERIFICATION.md` |
| Cross-fitting stability and attenuation | `results/crossfit_v1/` | `tests/test_crossfit.py`; run receipt |
| Simulation design | `configs/simulation_study_v1.json` | Protocol and run receipt |
| 90 scenarios / 180,000 repetitions | `results/simulation_v1/` | `scripts/verify_release.py` |
| Component-transfer diagnosis | `results/exploratory_reanalysis_v1/` | Summary JSON and notebook |
| Release-wide integrity | `MANIFEST.sha256` | `sha256sum -c MANIFEST.sha256` |

The artifact separates prespecified evidence from post hoc diagnostics. File locations describe provenance; they do not change evidential status.

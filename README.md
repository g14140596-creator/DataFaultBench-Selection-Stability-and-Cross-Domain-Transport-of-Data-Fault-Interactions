# DataFaultBench

**Source-isolated evaluation of selection optimism and cross-domain transport in tabular data-quality benchmarks.**

DataFaultBench is the reproducible research artifact accompanying *DataFaultBench: Selection Stability and Cross-Domain Transport of Data-Fault Interactions*. It separates candidate search on calibration source domains from a single, frozen confirmation on disjoint source domains. The repository also contains post hoc cross-fitting diagnostics and a frozen simulation study of selection optimism.

## What is included

- Frozen Study I materials for 55 provenance-reviewed OpenML classification domains.
- Machine-readable calibration and sealed-confirmation receipts.
- A 36-candidate, two-fault interaction search with multiplicity control.
- Post hoc source-domain cross-fitting outputs and scripts.
- A frozen simulation study with 90 scenarios and 180,000 repetitions.
- Figure-source data, audit records, integrity hashes, and automated tests.

The repository does **not** indiscriminately redistribute upstream OpenML feature or label values. It records task identifiers, provenance, acquisition instructions, and integrity information so datasets can be retrieved subject to their upstream terms.

## Main frozen findings

- One calibration candidate survived Holm family-wise correction.
- On 16 eligible source-disjoint final domains, the frozen directional confirmation was not significant (`p = 0.131`).
- Leave-one-source-domain-out cross-fitting reselected the original candidate in 25 of 26 folds, while its held-out magnitude was attenuated.
- In the Study-I-like global-null simulation, naive same-domain inference rejected in 56.15% of repetitions; source-disjoint confirmation rejected in 5.40% and achieved 95.00% interval coverage.

These results distinguish **selection stability** from **effect transport**. Cross-fitting and component decomposition are internal post hoc diagnostics, not a second prospective external validation.

## Repository map

| Path | Purpose |
|---|---|
| `src/datafaultbench/` | Reusable analysis, simulation, integrity, and figure utilities |
| `configs/` | Frozen simulation and cross-fitting configurations |
| `protocols/` | Prespecified and post-Study-I analysis plans |
| `results/` | Machine-readable outputs, figures, ledgers, and receipts |
| `study_i_reference/` | Byte-frozen Study I reproducibility package and 55-domain manifest |
| `analysis/` | Reproducible exploratory notebook |
| `scripts/` | Execution and verification entry points |
| `tests/` | Automated unit tests |
| `docs/` | Reproduction, artifact, and data-governance guidance |

## Quick start

Python 3.11 or later is recommended.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Verify the committed release without rerunning the full simulation:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_release.py
python scripts/verify_zero_new_data_release.py
```

Rerun the frozen simulation:

```bash
python scripts/run_simulation.py \
  --config configs/simulation_study_v1.json \
  --output results/simulation_v1_rerun
```

The original Study I package in `study_i_reference/` contains its own acquisition, execution, and verification instructions. See [Reproducibility](docs/REPRODUCIBILITY.md) for the full sequence.

## Evidential status

Study I is the completed source-isolated experiment. Cross-fitting and component decomposition reuse observed Study I outcomes and are labeled post hoc. The simulation protocol was frozen after Study I. No unrun external Study II result is included or claimed.

## Citation

Please cite the archived release using [`CITATION.cff`](CITATION.cff). A version-specific DOI can be added after the GitHub repository is connected to Zenodo and the release is archived.

## License and upstream data

Code and original documentation are released under the [MIT License](LICENSE). OpenML tasks and any third-party materials remain governed by their original licenses and terms; see [Data Governance](docs/DATA_GOVERNANCE.md).

## Author

Yueying Huang, China University of Geosciences (Beijing).

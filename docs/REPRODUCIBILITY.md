# Reproducibility guide

## 1. Verify the published artifact

Install the package and run:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/verify_release.py
python scripts/verify_zero_new_data_release.py
sha256sum -c MANIFEST.sha256
```

These checks validate code behavior, scenario counts, repetition counts, the empty failure ledger, and committed file hashes. They do not download upstream datasets.

## 2. Reproduce the simulation

The frozen configuration is `configs/simulation_study_v1.json`. To preserve the committed outputs, write a rerun to a new directory:

```bash
python scripts/run_simulation.py \
  --config configs/simulation_study_v1.json \
  --output results/simulation_v1_rerun
```

Expected scope: 90 scenarios and 180,000 total repetitions. The script writes a failure ledger and a cryptographic run receipt.

## 3. Inspect Study I

The complete byte-frozen Study I artifact is distributed as the journal's Online Resource 1. This repository retains `study_i_reference/VERIFICATION.md`, the 55-domain manifest, execution code, analysis code, and machine-readable summaries. The large calibration-cell and append-only ledger files are kept out of Git history.

Do not replace the frozen manifest, silently redownload all tasks, or modify the clean frozen dataset. New upstream snapshots or additional source domains constitute a new study version.

## 4. Reproduce post hoc diagnostics

The source-domain cross-fitting outputs are in `results/crossfit_v1/`. The analysis requires the frozen calibration-cell file documented by `configs/crossfit_study_v1.json`; its SHA-256 hash is checked before analysis. The exploratory notebook and component-transfer outputs are retained under `analysis/` and `results/exploratory_reanalysis_v1/`.

These analyses reuse Study I outcomes. They are diagnostic and do not replace the one-shot source-disjoint confirmation.

## 5. Verify a manuscript copy (optional)

If an accompanying `.docx` manuscript is available locally, verify its key frozen statements with:

```bash
python scripts/verify_zero_new_data_release.py /path/to/manuscript.docx
```

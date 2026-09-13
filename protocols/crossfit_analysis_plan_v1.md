# DataFaultBench zero-new-data cross-fitted analysis plan

Status: post hoc specification finalized before execution of the dedicated
cross-fitting script. The Study I calibration and final-test outcomes were
already known. This analysis is therefore not preregistered or confirmatory.

## Purpose

Use the complete 36-candidate by 26-calibration-domain result matrix already
generated in Study I to assess how adaptive candidate selection behaves when
the source domain used for evaluation is excluded from selection. No model is
refit and no new dataset is accessed.

## Domain and candidate values

The analysis reuses the locked Study I candidate definition and domain value:
the arithmetic mean of three matched replicate interactions within an
independent source domain. Candidate eligibility requires at least 12 training
domains. The selection score is the absolute equal-domain mean divided by its
domain-level standard error, with the original lexicographic tie break. The
direction is the sign of the training-domain mean.

## Primary leave-one-source-domain-out analysis

For each of the 26 calibration domains, remove that domain; apply the original
selection rule to the remaining domains; and evaluate the selected candidate,
in its training-frozen direction, on the omitted domain when structurally
eligible. Report the number of evaluable domains, equal-domain mean and 95%
Student-t interval of oriented held-out values, median, IQR, sign consistency,
selection frequencies, training selected mean, and training-to-holdout gap.

These values describe the performance of the adaptive selection policy under
internal source cross-fitting. Because selection rules overlap across folds and
the analysis was designed after Study I outcomes were known, its interval is
descriptive and does not replace the sealed final-test inference.

## Secondary analyses

- Deterministic 13-fold cross-fitting, holding out two source domains per fold
  after SHA-256 ordering with a frozen salt.
- Five hundred deterministic 18-domain selection / 8-domain evaluation splits.
  Report distributions of selected candidates, oriented holdout means, and
  training-to-holdout gaps. Repeated splits are not treated as 500 independent
  experiments and do not receive a split-level significance test.

## Integrity rules

The input calibration cells must match the Study I SHA-256 lock. Replicate,
candidate, and domain uniqueness are checked before aggregation. Original
Study I artifacts remain byte-unchanged. All new outputs are labeled post hoc
and zero-new-data.


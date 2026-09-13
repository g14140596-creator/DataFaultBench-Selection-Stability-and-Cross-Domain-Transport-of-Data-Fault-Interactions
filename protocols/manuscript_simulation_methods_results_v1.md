# Manuscript-ready simulation study (version 1)

## Methods: simulation study

We conducted a post-Study-I simulation study to quantify the inferential
consequences of selecting a benchmark configuration on the same domains used
to estimate its performance. The simulation protocol and configuration file
were frozen before outcomes were generated. This study does not alter the
candidate set, selection rule, direction, estimand, or confirmatory analysis of
the original 55-domain experiment.

For candidate configuration \(j\) and domain \(d\), the simulated interaction
effect was generated as

\[
Y_{jd}=\theta_j+\tau\{\sqrt{\rho}U_d+\sqrt{1-\rho}V_{jd}\},
\]

where \(U_d\) is a domain-level shock shared by candidates, \(V_{jd}\) is a
candidate-specific shock, \(\tau\) controls cross-domain heterogeneity, and
\(\rho\) controls candidate correlation within domains. Calibration and
confirmation domains were generated independently. On the calibration set, we
selected the candidate with the largest absolute studentized mean and froze
the observed direction. We then compared three inferential strategies: (i) an
uncorrected test computed on the selection domains, (ii) a Holm-adjusted test
computed on the selection domains, and (iii) an unadjusted test computed on an
independent confirmation set after freezing the selected candidate and
direction. We also evaluated nominal 95% interval coverage, calibration-to-
confirmation attenuation, absolute selection optimism, sign reversal, and
recovery of the true signal candidate.

The main factorial design varied the number of searched candidates
(6, 12, 36, or 72), heterogeneity (\(\tau=0.005, 0.015, 0.030\)), within-domain
candidate correlation (\(\rho=0\) or 0.5), and the data-generating regime
(global null, one stable sparse signal of 0.005, or a sparse signal attenuated
by 50% on confirmation domains). The main design used 26 calibration and 16
confirmation domains. A separate sensitivity design varied calibration size
(12, 26, or 52) and confirmation size (12, 16, or 32) with 36 candidates,
\(\tau=0.015\), and \(\rho=0.5\). We ran 2,000 Monte Carlo repetitions in each
of 90 scenarios (180,000 repetitions in total) using master seed 20260912.

## Results: selection-induced optimism

Under the global null in the scenario closest to Study I (36 candidates, 26
calibration domains, 16 independent confirmation domains, \(\tau=0.015\), and
\(\rho=0.5\)), the uncorrected selected-candidate test rejected in 56.15% of
repetitions. Holm adjustment on the selection domains reduced the rejection
rate to 3.85%, whereas source-disjoint confirmation yielded 5.40%. The nominal
95% interval covered the selected candidate's true effect in only 43.85% of
calibration samples but in 95.00% of independent confirmation samples. Mean
absolute selection optimism was 0.00592, and the selected direction reversed
on the confirmation sample in 51.15% of repetitions.

The distortion increased with search width. Holding all other parameters at
the Study-I-like null setting, the uncorrected rejection rate rose from 21.95%
with six candidates to 70.05% with 72 candidates. Over the same range,
calibration-interval coverage fell from 78.05% to 29.95% and mean absolute
selection optimism increased from 0.00440 to 0.00639. In contrast, independent
confirmation rejection remained between 4.90% and 5.40%, and its interval
coverage remained between 94.15% and 95.15%.

Candidate correlation moderated, but did not remove, selection distortion. For
36 null candidates at \(\tau=0.015\), the uncorrected rejection rate was 84.90%
when \(\rho=0\) and 56.15% when \(\rho=0.5\); corresponding calibration-
interval coverage was 15.10% and 43.85%. Independent confirmation remained
close to the nominal error and coverage rates in both cases.

Under a stable sparse signal, the probability of selecting the true candidate
declined from 59.10% with six candidates to 28.55% with 72 candidates. The
corresponding independent-confirmation rejection rate declined from 24.60% to
13.50%. Thus, broader searches created a dual penalty: they amplified the
apparent calibration evidence while making reliable identification and
confirmation of a fixed weak signal more difficult.

These results establish a mechanism-level interpretation of the empirical
attenuation observed in Study I. A large calibration-to-confirmation decrease
is expected after an adaptive search even when every candidate has zero true
effect, and nominal intervals constructed after selection can be severely
miscalibrated. Source-disjoint confirmation restores valid uncertainty
quantification under the simulated data-generating processes. The numerical
magnitudes are design-dependent and should not be interpreted as universal
correction factors for other benchmark collections.

## Compact manuscript table

| Candidates | Naive rejection | Holm rejection | Independent rejection | Calibration CI coverage | Independent CI coverage | Mean absolute optimism |
|---:|---:|---:|---:|---:|---:|---:|
| 6 | 0.2195 | 0.0395 | 0.0490 | 0.7805 | 0.9480 | 0.004400 |
| 12 | 0.3255 | 0.0385 | 0.0500 | 0.6745 | 0.9415 | 0.005096 |
| 36 | 0.5615 | 0.0385 | 0.0540 | 0.4385 | 0.9500 | 0.005918 |
| 72 | 0.7005 | 0.0350 | 0.0530 | 0.2995 | 0.9515 | 0.006386 |

*Table note.* Global-null scenarios with 26 calibration domains, 16
independent confirmation domains, \(\tau=0.015\), \(\rho=0.5\), and 2,000
repetitions per row. Monte Carlo standard errors should accompany final
typeset values; they can be obtained from the released replicate ledger.


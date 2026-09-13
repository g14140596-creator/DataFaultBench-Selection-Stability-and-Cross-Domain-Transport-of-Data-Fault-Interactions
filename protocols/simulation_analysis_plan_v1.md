# Simulation analysis plan v1

Status: frozen before simulation outcomes are generated  
Freeze date: 2026-09-12 UTC

## Question

How do candidate-search width, the number of independent source domains,
between-domain heterogeneity, and dependence among candidates affect effect-size
inflation and inferential validity after benchmark selection?

## Data-generating process

For candidate `j` and domain `d`, the domain-level interaction is generated as

`Y[j,d] = theta[j] + tau * (sqrt(rho) * G[d] + sqrt(1-rho) * E[j,d])`,

where `G` and `E` are independent standard-normal variables. `tau` is the
between-domain standard deviation and `rho` controls candidate correlation
induced by shared domain difficulty. Calibration and confirmation domains are
generated independently.

The global-null regime sets all candidate effects to zero. Sparse-signal regimes
set exactly one prespecified candidate to 0.005 balanced-accuracy units and all
others to zero. Under attenuation, that candidate's confirmation-domain effect
is multiplied by 0.5. The signal index is fixed before random generation.

## Selection and comparisons

Within calibration domains, select exactly one candidate maximizing the absolute
studentized equal-domain mean. Freeze the sign of its calibration mean. Compare:

1. naive same-domain inference for the selected candidate;
2. Holm control for the minimum calibration p-value (equivalent to multiplying
   the smallest two-sided p-value by the family size in this equal-n design);
3. one-sided inference on independent confirmation domains in the frozen sign;
4. two-sided confidence-interval coverage on calibration versus confirmation.

## Outcomes

Primary simulation outcomes are:

- absolute calibration optimism relative to the selected candidate's truth;
- calibration-to-confirmation attenuation in the frozen direction;
- global-null rejection rate for naive, Holm, and source-disjoint procedures;
- 95% confidence-interval coverage of the selected truth;
- sign reversal between calibration and confirmation.

Selection recovery in sparse-signal regimes is secondary. All summaries report
Monte Carlo means and Monte Carlo standard errors. No scenario will be removed
because its result is inconvenient.

## Integrity

The configuration file, this plan, the replicate ledger, summaries, and figures
are hashed in a run receipt. Failed scenarios are retained in the failure file.


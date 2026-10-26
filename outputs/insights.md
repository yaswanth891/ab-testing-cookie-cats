# Product decision memo — A/B Test

**Dataset:** Synthetic demonstration data (not actual Cookie Cats players)

**Hypothesis:** Moving the first gate from level 30 (control) to level 40 (treatment) affects Day-7 retention.

## Experiment quality

- Unique players: **90,000** (45,000 control / 45,000 treatment).
- Sample ratio mismatch chi-squared p-value: **1**; flag under 0.01 for assignment review.
- Unit of randomization / analysis: player ID, one row per player. This is a retrospective analysis; original randomization was not audited.

## Outcomes

| Metric | Control | Treatment | Treatment - Control | p-value | 95% CI (pp) |
|---|---:|---:|---:|---:|---:|
| Day 1 (secondary) | 44.88% | 44.04% | -0.85 pp | 0.0106 | [-1.50, -0.20] |
| Day 7 (**primary**) | 19.63% | 18.03% | -1.60 pp | 0.0000 | [-2.11, -1.09] |

Median 14-day game rounds: **12** control vs **12** treatment. Medians are used because extreme engagement outliers may exist; no users are removed from the retention ITT analysis.

## Decision

**KEEP GATE AT LEVEL 30 — treatment significantly reduces 7-day retention.**

## Statistical design and limitations

- Two-sided **pooled two-proportion z-tests**; report the unpooled normal-approximation 95% confidence interval for the difference in absolute percentages.
- Alpha 0.05 is applied to **Day-7 primary outcome**. Treat Day-1 as exploratory / secondary rather than making a separate launch claim.
- Sample ratio mismatch uses chi-squared goodness-of-fit against 50:50 allocation; mismatch can suggest a logging or randomization issue.
- Revenue, pay conversion, uninstall rate and user-level exposure to the gate are not available. These are important missing guardrails.
- ITT = effect of **assignment** to gate configuration, not effect among only users who reached the gate.
- Synthetic demo estimates are not evidence from a real company experiment.

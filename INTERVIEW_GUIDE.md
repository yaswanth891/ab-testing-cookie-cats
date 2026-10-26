# Interview explanation / walkthrough

**Project:** A/B Testing: Cookie Cats Gate Placement

**What it does:** An intent-to-treat A/B evaluation of Day-7 retention with a two-proportion test, confidence interval, and SRM warning.

**Workflow:** Load validated CSV → compute SQL or Python metrics → render KPI dashboard → explain limits → propose next product action.

**Q: Why Day-7 as the primary metric?**

A: It directly captures a return behavior relevant to long-term engagement; Day-1 is secondary.

**Q: What does intent-to-treat mean?**

A: We include everyone assigned to each gate version, even if they never encountered the gate.

**Q: What is a sample ratio mismatch?**

A: An unexpectedly uneven assignment split can indicate experiment-logging or randomization issues; it should be investigated.

**Important:** The bundled outputs are synthetic demonstrations. Re-run on genuine public data before discussing any dataset-specific results in interviews.

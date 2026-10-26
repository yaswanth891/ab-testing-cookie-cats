# Data dictionary & output definitions

**cookie_cats.csv** — `userid`, `version` (gate_30/gate_40), `sum_gamerounds`, `retention_1`, `retention_7`.

### Outputs

- `outputs/dashboard.html`: offline interactive analysis results.
- `outputs/overview.png`: static presentation chart.
- `outputs/metrics.json`: computed KPI values from the selected dataset.
- `outputs/insights.md`: computed insight / interpretation memo.
- Additional `outputs/*.csv`: processed tables for auditing calculations.

### Ethics

The included `data/raw/` CSVs are synthetic sample data, not licensed copies of the original public datasets. When presenting analysis to employers, attribute the original public dataset and differentiate observational findings from demonstrated business impact.

# Sigma Workbook Spec

Obie names Sigma as its BI/data-visualization tool. Sigma itself is not
reachable from this build sandbox, so the three dashboard elements below are
rendered as static charts from the same underlying SQL (see
`src/render_dashboard_charts.py`), with the Sigma-equivalent element each
one maps to:

| Chart (rendered here) | Sigma element | Source table | Grain |
|---|---|---|---|
| `01_monthly_premium_by_channel.png` | Line chart, Sigma workbook element with a month-grain date control and a channel breakout | `gold_monthly_metrics` | month x channel |
| `02_renewal_rate_by_loss_tier.png` | Bar chart element, built on a Sigma input table joining `gold_monthly_metrics` back to the NFIP `silver_state_risk_profile` loss ratio via a Sigma lookup column | `silver_policy_events_deduped` + `silver_state_risk_profile` | loss-ratio tier |
| `03_budget_variance.png` | Bar chart with a Sigma conditional-format rule (red when `variance_usd < 0`) | `gold_budget_variance` | month |

In production, each of these would be a live Sigma workbook element
pointed at the warehouse tables directly, with a page-level date-range
control and a channel filter shared across all three elements (Sigma's
cross-filtering), rather than a static PNG rebuilt by a script.

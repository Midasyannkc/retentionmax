# Architecture

```
                         REAL DATA                           DISCLOSED SYNTHETIC
                 ┌──────────────────────┐              ┌──────────────────────────┐
                 │ FEMA NFIP state-level │              │ 24-mo landlord-insurance │
                 │ policy & claims text  │              │ policy event stream,     │
                 │ (2013 "as of" report, │              │ weighted by real state   │
                 │ via GitHub mirror)    │              │ market size + loss ratio │
                 └──────────┬────────────┘              └──────────┬───────────────┘
                            │ regex parse (right-anchored)          │
                            ▼                                       │
                    BRONZE  raw .txt committed as-is                │
                            │                                       │
                            ▼                                       │
                    SILVER  silver_state_risk_profile                │
                            (54 states, loss_ratio)                  │
                            │                                        ▼
                            │                           BRONZE  synthetic_policy_events_raw
                            │                                        │ dedup (Incident 2 fix)
                            │                                        ▼
                            │                           SILVER  silver_policy_events_deduped
                            │                                        │
                            └───────────────┬────────────────────────┘
                                             ▼
                                     GOLD  gold_monthly_metrics
                                     GOLD  gold_budget_variance
                                             │
                      ┌──────────────────────┼───────────────────────┐
                      ▼                      ▼                       ▼
            analyze_growth.py      render_dashboard_charts.py   budget_tracker.py
            (hypothesis test:      (Sigma-equivalent dashboard, (budget-vs-actual
             renewal rate vs        docs/dashboard/*.png +       variance by
             loss-ratio tier)       SIGMA_SPEC.md)                channel/month)
```

## Storage

DuckDB (`data/retentionmax.duckdb`, gitignored, rebuilt by running
`src/build_silver.py` -> `src/generate_synthetic_book.py` -> `src/build_gold.py`
-> `src/analyze_growth.py` / `src/budget_tracker.py` / `src/render_dashboard_charts.py`
in sequence). DuckDB stands in locally for Snowflake/Redshift in this
sandbox; see `docs/cost-tradeoffs.md` for the production-target discussion.

## BI layer

Sigma itself is not reachable from this build sandbox (no outbound network
access to third-party SaaS beyond GitHub and package registries). The three
dashboard queries behind `render_dashboard_charts.py` are instead documented
as an explicit Sigma workbook spec in `docs/dashboard/SIGMA_SPEC.md`, so the
mapping from "what Sigma would show" to "the SQL that produces it" is
explicit rather than implied.

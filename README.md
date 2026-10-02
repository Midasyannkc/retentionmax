# RetentionMax

A growth, retention, and financial-reporting analytics platform for a
landlord/real-estate-investor insurance book, built for Obie's Data
Analyst (RevOps & Business Insights) posting -- which asks for hypothesis-
driven growth/stagnation analysis, SQL-first data-quality reconciliation,
Sigma-style dashboarding, and financial budget tracking, with insurance
domain grounding.

## What this is

- **Real data anchor:** FEMA's National Flood Insurance Program (NFIP)
  state-level Policy Statistics and Loss Statistics, a real property-
  insurance policy/claims dataset at the state and county level (see
  `data/bronze/SOURCE.md` for exact provenance and an honest disclosure of
  how it was reached from this build sandbox).
- **Disclosed-synthetic extension:** a 24-month (Jan 2024 - Dec 2025)
  landlord-insurance book-of-business event stream, generated to be
  internally consistent with the real state-level market size and loss
  ratios rather than arbitrary (see `data/synthetic/GENERATION_NOTES.md`).
- **Two real incidents**, each reproduced and fixed with genuine git
  history (see `docs/incidents.md` for the full detail):
  1. A naive whitespace-split parser silently corrupted every real
     multi-word state/territory name (14 of 55 rows).
  2. A naive aggregation double-counted at-least-once-delivered partner-
     channel renewal webhooks, overstating renewal revenue by $46,993.74.
- **A hypothesis-driven growth analysis**: tested (not assumed) whether
  renewal-rate stagnation correlates with real NFIP loss ratio by state --
  confirmed a monotonic decline (87% -> 76% -> 67% renewal rate across
  low/medium/high loss-ratio tiers).
- **A monthly premium budget-vs-actual variance tracker** by channel.
- **A Sigma-equivalent dashboard** (static charts + an explicit Sigma
  workbook spec, since Sigma itself isn't reachable from this sandbox).

## Repository layout

```
data/
  bronze/        real FEMA NFIP raw text + source documentation
  synthetic/     disclosed-synthetic generation notes
  retentionmax.duckdb   (gitignored, rebuilt by running the pipeline)
src/
  parse_nfip_state.py        real-data parser (Incident 1)
  parse_nfip_claims.py       real-data claims parser
  build_silver.py            real-data Silver join
  generate_synthetic_book.py synthetic event generator (Incident 2 source)
  build_gold.py              Silver -> Gold (Incident 2 fix)
  analyze_growth.py          hypothesis-driven growth analysis
  budget_tracker.py          budget-vs-actual variance
  render_dashboard_charts.py Sigma-equivalent dashboard renderer
tests/           pytest suite, 14/14 passing
docs/
  incidents.md        full incident reports with git log excerpts
  architecture.md      pipeline diagram
  cost-tradeoffs.md    sandbox-constraint disclosures and production targets
  dashboard/           rendered charts + SIGMA_SPEC.md
AI_DEV_LOG.md     what was AI-assisted vs. human-directed/validated
CODING_STANDARDS.md
RetentionMax_Executive_Summary.pptx
```

## Running it

```
pip install -r requirements.txt
python -m pytest tests/ -v              # 14/14
python -m src.build_silver               # real-data Silver layer
python -m src.generate_synthetic_book     # synthetic event stream
python -m src.build_gold                  # Gold layer (naive vs. fixed)
python -m src.analyze_growth              # growth hypothesis test
python -m src.budget_tracker              # budget variance
python -m src.render_dashboard_charts     # dashboard PNGs
```

## Known, disclosed scope limits

- The real NFIP data is a single 2013 "as of" snapshot, not a multi-year
  time series (FEMA publishes the historical loss table back to 1978, but
  the policy-in-force table is a current snapshot only); the time-series
  and channel dimensions used for the growth/retention/budget analysis are
  therefore disclosed-synthetic, not Obie's real figures.
- `fema.gov` and the GitHub API are both network-blocked from this build
  sandbox; the real NFIP extract was reached via `git clone` of a public
  GitHub mirror instead (see `data/bronze/SOURCE.md`).
- Sigma itself is not reachable from this sandbox; the dashboard is
  rendered as static charts from the same SQL, with an explicit Sigma
  workbook spec (`docs/dashboard/SIGMA_SPEC.md`).
- County-level NFIP detail is present in the raw committed files but not
  parsed in this build; the state-level grain was sufficient to test the
  stated growth hypothesis.

# Coding Standards & Review Guidelines

Followed throughout this repository's git history:

1. **One concern per module.** Parsing (`parse_nfip_state.py`,
   `parse_nfip_claims.py`), layer builds (`build_silver.py`,
   `build_gold.py`), analysis (`analyze_growth.py`, `budget_tracker.py`),
   and presentation (`render_dashboard_charts.py`) are kept in separate
   files so a change to one doesn't require touching the others.
2. **Every data-shape assumption gets a pinned test.** Ground truth is
   hand-transcribed from the source (see `tests/test_parse_nfip_state.py`)
   rather than asserting against the parser's own output, so a regression
   is caught, not just a change.
3. **Fixes are proven, not asserted.** Every incident in `docs/incidents.md`
   has a before-state commit (bug reproduced, test failing) and a
   separate after-state commit (fix applied, test passing, numbers
   reconciled) -- never a single commit claiming both.
4. **No silent fallbacks.** A missing or unreachable data source is
   disclosed in the relevant `SOURCE.md` / `GENERATION_NOTES.md`, not
   quietly substituted without a note.
5. **Idempotent by default.** Any step that could run more than once
   against the same input (the Gold build, in particular) dedupes on an
   explicit natural key rather than assuming exactly-once delivery.
6. **Commit messages state the verification, not just the change** -- e.g.
   "10/10 tests passing" or the exact reconciled dollar figure -- so the
   git log itself is a verification trail.

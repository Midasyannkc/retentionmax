# Synthetic Data: Generation Notes (disclosed)

The real FEMA NFIP data (see `data/bronze/SOURCE.md`) is a single 2013
cross-section with no multi-period time dimension and no channel/partner
attribution, since FEMA runs the program directly rather than through an
agent/partner distribution network. Obie's actual book of business has
both: a 2024-2025 monthly history and a direct / agent / lender-partner
distribution mix. Those two pieces are generated as DISCLOSED SYNTHETIC data
in `src/generate_synthetic_book.py`, built to be internally consistent with
the real state-level distribution rather than uniform or arbitrary:

- **Market sizing by state**: each state's relative share of new business is
  weighted by its REAL `policies_in_force` count from the NFIP silver table,
  so larger real flood-insurance states (Florida, Texas, Louisiana,
  California, ...) realistically generate more synthetic landlord-policy
  volume than small ones, rather than every state being equally likely.
- **Risk signal passthrough**: each state's REAL `loss_ratio` (computed in
  the silver layer from real claims and premium) is used to bias synthetic
  renewal probability downward in higher-loss states, reflecting a plausible
  real-world mechanism (higher-risk/higher-loss states see more premium
  increases at renewal, which depresses renewal rates) that the business
  hypothesis analysis in `src/analyze_growth.py` later tests for.
- **Time range**: 24 months, January 2024 through December 2025.
- **Channels**: `direct`, `agent`, `partner` (lender/PM-platform referral),
  mirroring Obie's stated distribution model (direct digital, agent network,
  lender/PM partnerships).
- **Random seed**: fixed (`RANDOM_SEED = 20240101` in
  `src/generate_synthetic_book.py`) for reproducibility.

This generated event stream intentionally reproduces a realistic partner-
integration data-quality problem (at-least-once webhook delivery producing
duplicate renewal events) so that problem can be found and fixed with
genuine git history, exactly as the real-data incidents in this project are
-- see `docs/incidents.md`, Incident 2.

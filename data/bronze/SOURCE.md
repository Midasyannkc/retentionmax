# Real Data Source

## FEMA National Flood Insurance Program (NFIP) Policy & Claim Statistics

- Originally published by FEMA: Policy & Claim Statistics for Flood Insurance
  (http://www.fema.gov/policy-claim-statistics-flood-insurance/) — a single
  as-of snapshot dated **08/31/2013**, broken out by state and county.
- Direct fema.gov access is network-blocked in this build sandbox (confirmed:
  CONNECT tunnel rejected by the egress proxy). The same FEMA-sourced extract
  is mirrored verbatim, with full provenance, in the public GitHub repository
  https://github.com/RationShop/nfip (cloned via `git clone`, which IS
  reachable from this sandbox even though the FEMA domain and the GitHub API
  are not). The raw files `nfip_policies_raw.txt` and `nfip_claims_raw.txt` in
  this folder are that repository's unmodified FEMA extract.
- **Honest disclosure:** this is a single point-in-time cross-section (one
  "AS OF" date), not a multi-year time series, and it dates to 2013. It is
  used here as the REAL anchor for state/county-level policy penetration and
  claims severity. The monthly 2024-2025 book-of-business time series used
  for the growth/retention/forecasting analysis in this project is
  DISCLOSED SYNTHETIC data, generated to be internally consistent with this
  real state-level distribution (see data/synthetic/GENERATION_NOTES.md).

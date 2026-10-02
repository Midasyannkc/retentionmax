# Cost Trade-offs

| Decision | What was used here | Production target | Why |
|---|---|---|---|
| Warehouse | DuckDB, single local file | Snowflake (or Redshift) | No outbound network access to a cloud warehouse from this build sandbox; DuckDB's SQL dialect is close enough to validate the join/aggregation logic locally at zero cost before porting. |
| BI tool | Static matplotlib PNGs + a documented Sigma workbook spec | Sigma, live on the warehouse tables | Sigma (Obie's stated BI tool) is a third-party SaaS product unreachable from this sandbox; the spec in `docs/dashboard/SIGMA_SPEC.md` keeps the query logic 1:1 portable. |
| Real data source | FEMA NFIP extract mirrored on GitHub (git clone) | FEMA's own OpenFEMA bulk API/CSV downloads | Direct `fema.gov` access is network-blocked by this sandbox's egress policy (confirmed: CONNECT tunnel rejected); the GitHub mirror is the same FEMA-sourced data with documented provenance, reachable because `github.com` IS allowlisted for git protocol. |
| Time dimension | Disclosed-synthetic 24-month event stream | Obie's own real policy/claims event history | The real NFIP source is a single as-of snapshot (08/31/2013), not a time series; Obie's actual multi-year book would replace this generator entirely. |
| Compute for growth analysis | In-process DuckDB SQL over ~6,500 rows | The same SQL pattern scales directly to a warehouse-scale fact table; no architectural change needed, only a connection-string swap | Chosen to keep the incident-reproduction loop (run, break, fix, verify) fast during development. |

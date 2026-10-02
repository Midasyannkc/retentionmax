# Incident Reports

## Incident 1: naive whitespace-split parser corrupts multi-word state names

**Scenario.** The real FEMA NFIP state-level Policy Statistics and Loss
Statistics tables (`data/bronze/nfip_policies_raw.txt`,
`nfip_claims_raw.txt`) are fixed-width report text, not CSV. The first
parser written for these tables (`src/parse_nfip_state.py`,
`_naive_split_parser`) assumed each row's state/territory name was always a
single whitespace-delimited token.

**Reality.** At least 14 of the 55 real rows have multi-word names
("N Mariana Islands", "District Columbia", "West Virginia", "South
Carolina", "South Dakota", "New Hampshire", "New Jersey", "New Mexico", "New
York", "North Carolina", "North Dakota", "Rhode Island", "American Samoa",
"Virgin Islands"). One of them, "N Mariana Islands", is also one character
wider than the report's own fixed-width name column, so a naive
fixed-width-slice parser would have failed it too, for a different reason.

**Detection.** Ground-truth values for five rows (including three
multi-word names) were hand-transcribed from the raw file into
`tests/test_parse_nfip_state.py` and pinned against the parser's output.

```
tests/test_parse_nfip_state.py::test_single_word_state_names_parse_correctly PASSED
tests/test_parse_nfip_state.py::test_multiword_state_names_parse_correctly FAILED
tests/test_parse_nfip_state.py::test_all_55_states_and_territories_present FAILED
  AssertionError: 'N Mariana Islands' missing or corrupted by the parser
  AssertionError: expected 55 state/territory rows, parsed 57
```

**Fix.** Replaced the whitespace split with a regex anchored on the three
trailing numeric fields (`_rightanchored_parser`); everything before them,
regardless of width or word count, is the name. All 55 state/territory rows
now parse correctly.

```
tests/test_parse_nfip_state.py::test_single_word_state_names_parse_correctly PASSED
tests/test_parse_nfip_state.py::test_multiword_state_names_parse_correctly PASSED
tests/test_parse_nfip_state.py::test_all_55_states_and_territories_present PASSED
```

**Git history:**
```
4c29afa Parse NFIP state policy table; naive split-based parser, tests pinned to ground truth
af7111c Fix: right-anchor numeric field regex instead of naive split; all 3/3 tests passing (55/55 states parsed correctly)
```

---

## Incident 2: at-least-once partner webhook delivery double-counts renewal revenue

**Scenario.** The synthetic 24-month policy event stream
(`src/generate_synthetic_book.py`) models Obie's partner (lender/PM
platform) channel as delivering renewal events over webhook, which is
realistically at-least-once rather than exactly-once. The naive Gold
aggregation (`build_gold_naive`) treated every row in the raw event table
as a distinct, valid event.

**Detection.** A test computed true unique renewal totals independently (by
deduping on the natural key `(policy_id, event_type, event_date, channel,
premium_usd)`) and compared them against the naive aggregation's output:

```
naive:  1526 renewal events, $2,291,360.97 renewal premium
true:   1493 renewal events, $2,244,367.23 renewal premium
overcounted by: 33 events, $46,993.74
```

All 33 of the overcounted events were on the `partner` channel, consistent
with the injected webhook-redelivery mechanism.

**Fix.** Added an idempotent dedup step (`silver_policy_events_deduped`,
`SELECT DISTINCT ... FROM synthetic_policy_events_raw`) before aggregation
into `gold_monthly_metrics`. Reconciled exactly to the true totals:

```
tests/test_build_gold.py::test_fixed_gold_reconciles_exactly_to_true_unique_totals PASSED
tests/test_build_gold.py::test_fix_corrects_exactly_the_injected_duplicate_count PASSED
```

**Business impact if unfixed:** a RevOps/Finance team reading the naive
Gold table would have overstated realized partner-channel renewal revenue
by $46,993.74 across the 24-month window, and overstated the partner
channel's renewal count (and therefore its apparent retention health) by 33
policies -- directly the kind of silent reconciliation gap this role is
responsible for catching.

**Git history:**
```
27a3a0f Build Gold monthly metrics; naive aggregation double-counts duplicated partner renewal events (reproduced, test failing by design)
5cc9491 Fix: idempotent dedup on natural key before aggregation; reconciled exactly (corrected 33 duplicate renewals, $46,993.74 phantom premium); 10/10 tests passing
```

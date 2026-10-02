# AI Development Log

This project was built with Claude Code as an AI-assisted development tool,
directly relevant to this JD's "experience using AI-assisted development
tools (e.g., Claude Code) in a professional setting." This log discloses
what was AI-assisted versus human-directed and validated, rather than
presenting the result as either fully automated or fully manual.

| Area | AI-assisted | Human-directed / validated |
|---|---|---|
| Real data sourcing | Searched for a reachable mirror once direct `fema.gov` access was confirmed blocked | Confirmed the mirror's content actually matches FEMA's own report structure before using it; decision to disclose the blocked-domain constraint rather than silently substitute data |
| Parsing logic | Wrote the initial naive split-based parser and the regex-based fix | Hand-transcribed the ground-truth test values directly from the raw file (not generated), so the tests can't just validate the parser against itself |
| Synthetic data generation | Wrote the event-generation code and the injected duplicate-webhook mechanism | Chose which real signal (state market size, loss ratio) the synthetic data should be weighted by, and why, documented in `GENERATION_NOTES.md` |
| Incident detection | Wrote the dedup-based ground-truth comparison | Confirmed the resulting overcount figures ($46,993.74 / 33 events) by independent computation before treating them as the documented numbers |
| Growth hypothesis analysis | Wrote the SQL and the tiering logic | Chose the hypothesis itself (loss ratio depresses renewal rate) and judged whether the resulting monotonic pattern was a real finding worth reporting rather than noise -- it was tested, not assumed to confirm |
| Dashboard | Wrote the chart code following the project's own data-visualization skill guidance (categorical/sequential/diverging color-by-job rules) | Reviewed each rendered chart for label collisions and correct color-role usage before committing |
| Documentation | Drafted README/incident-report prose | Verified every number quoted in the README against a live rerun of the pipeline before publishing |

**What this demonstrates for the role:** AI tools accelerated the
mechanical parts (writing parsers, generating synthetic data, drafting
SQL and docs), while the judgment calls this JD actually tests for --
which hypothesis to test, whether a finding is real, how to disclose a
sandbox constraint honestly, and verifying every reconciled number
independently before trusting it -- stayed human-directed throughout.

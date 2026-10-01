"""
Parse the real FEMA NFIP state-level Loss Statistics (claims) table
(COUNTRY-WIDE section) out of the fixed-width report text file.

Source: data/bronze/nfip_claims_raw.txt (see data/bronze/SOURCE.md).
Uses the same right-anchored-regex approach validated in
parse_nfip_state.py (see docs/incidents.md, Incident 1) rather than a naive
split, since this table has the same multi-word state name issue.
"""
import re
from pathlib import Path

from src.parse_nfip_state import _extract_country_wide_block, BRONZE

_CLAIMS_PATTERN = re.compile(
    r"^\s*(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+\.\d+)\s*$"
)
_EXCLUDED_LABELS = {"STATE NAME", "TOTAL", "DUMMY-UNKNOWN", ""}


def get_claims_lines():
    # Unlike the policies file, the claims file's per-state county breakdown
    # sections are headed "LOSS STATISTICS" / state name, not "County Name",
    # so the country-wide block is bounded by the "TOTAL" aggregate row
    # instead.
    return _extract_country_wide_block(
        BRONZE / "nfip_claims_raw.txt",
        start_marker="------     ------     ------     ------",
        end_marker="TOTAL",
    )[1:]


def parse_claims():
    rows = []
    for raw in get_claims_lines():
        line = raw.rstrip("\n")
        m = _CLAIMS_PATTERN.match(line)
        if not m:
            continue
        name, total, closed, open_, cwop, payments = m.groups()
        name = name.strip()
        if name.upper() in _EXCLUDED_LABELS:
            continue
        rows.append(
            {
                "state_name": name,
                "total_losses": int(total.replace(",", "")),
                "closed_losses": int(closed.replace(",", "")),
                "open_losses": int(open_.replace(",", "")),
                "cwop_losses": int(cwop.replace(",", "")),
                "total_payments_usd": float(payments.replace(",", "")),
            }
        )
    return rows


if __name__ == "__main__":
    rows = parse_claims()
    print(f"parsed {len(rows)} claims rows")

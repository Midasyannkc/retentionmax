"""
Parse the real FEMA NFIP state-level Policy Statistics table (COUNTRY-WIDE
section) out of the fixed-width report text file.

Source: data/bronze/nfip_policies_raw.txt (see data/bronze/SOURCE.md for
provenance).

INCIDENT (fixed, see git history and docs/incidents.md): the first version of
this parser used a naive whitespace split, assuming the state/territory name
was always a single token. That assumption is false for this real data --
"N Mariana Islands", "District Columbia", "West Virginia", "South Carolina"
and a dozen other real rows have multi-word names, and one of them ("N
Mariana Islands") is also one character wider than the report's own
fixed-width name column, so even a naive fixed-width slice would have failed
it too. split()-based parsing silently shifted every numeric field for these
rows rather than raising an error, corrupting their policy/claims counts.
Fixed below by anchoring on the three trailing numeric fields with a regex
and treating everything before them as the name, regardless of its width or
word count.
"""
import re
from pathlib import Path

BRONZE = Path(__file__).resolve().parents[1] / "data" / "bronze"

_ROW_PATTERN = re.compile(r"^\s*(.+?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$")
_EXCLUDED_LABELS = {"STATE NAME", "TOTAL", "UNKNOWN", "DUMMY-UNKNOWN", ""}


def _rightanchored_parser(lines):
    """Anchor on the three trailing numeric fields; name is whatever remains."""
    rows = []
    for raw in lines:
        line = raw.rstrip("\n")
        m = _ROW_PATTERN.match(line)
        if not m:
            continue
        name, a, b, c = m.groups()
        name = name.strip()
        if name.upper() in _EXCLUDED_LABELS:
            continue
        rows.append(
            (name, int(a.replace(",", "")), int(b.replace(",", "")), float(c.replace(",", "")))
        )
    return rows


def _extract_country_wide_block(path: Path, start_marker: str, end_marker: str):
    lines = path.read_text().splitlines()
    start = next(i for i, l in enumerate(lines) if start_marker in l)
    end = next(i for i, l in enumerate(lines[start:], start=start) if end_marker in l)
    return lines[start:end]


def get_policy_lines():
    return _extract_country_wide_block(
        BRONZE / "nfip_policies_raw.txt",
        start_marker="----------------  ---------",
        end_marker="County Name",
    )[1:]


def parse_policies():
    rows = _rightanchored_parser(get_policy_lines())
    return [
        {
            "state_name": name,
            "policies_in_force": a,
            "insurance_in_force_usd": b,
            "written_premium_in_force_usd": c,
        }
        for name, a, b, c in rows
    ]


if __name__ == "__main__":
    pol = parse_policies()
    print(f"parsed {len(pol)} policy rows")

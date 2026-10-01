"""
Parse the real FEMA NFIP state-level Policy Statistics table (COUNTRY-WIDE
section) out of the fixed-width report text file.

Source: data/bronze/nfip_policies_raw.txt (see data/bronze/SOURCE.md for
provenance).
"""
from pathlib import Path

BRONZE = Path(__file__).resolve().parents[1] / "data" / "bronze"


def _naive_split_parser(lines):
    """Parse each row assuming the state name is always a single token."""
    rows = []
    for raw in lines:
        parts = raw.rstrip("\n").split()
        if len(parts) < 4:
            continue
        name = parts[0]
        try:
            a = int(parts[-3].replace(",", ""))
            b = int(parts[-2].replace(",", ""))
            c = float(parts[-1].replace(",", ""))
        except (ValueError, IndexError):
            continue
        rows.append((name, a, b, c))
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
    rows = _naive_split_parser(get_policy_lines())
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

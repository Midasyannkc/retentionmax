"""
Tests for the real FEMA NFIP state-level policy table parser.

These tests pin down ground truth read directly from the raw fixed-width
file for a handful of rows, including known multi-word state/territory
names, so a parsing regression is caught immediately.
"""
from src.parse_nfip_state import parse_policies

# Ground truth transcribed by hand from data/bronze/nfip_policies_raw.txt
EXPECTED = {
    "Alaska": (3038, 738860600, 2846224),
    "California": (253435, 66816086700, 214300184),
    "N Mariana Islands": (6, 1105500, 9676),
    "District Columbia": (2376, 413455700, 1230762),
    "West Virginia": (21219, 2746993100, 18345363),
}


def test_single_word_state_names_parse_correctly():
    rows = {r["state_name"]: r for r in parse_policies()}
    assert "Alaska" in rows
    a = rows["Alaska"]
    assert a["policies_in_force"] == EXPECTED["Alaska"][0]
    assert a["insurance_in_force_usd"] == EXPECTED["Alaska"][1]
    assert a["written_premium_in_force_usd"] == EXPECTED["Alaska"][2]


def test_multiword_state_names_parse_correctly():
    rows = {r["state_name"]: r for r in parse_policies()}
    for name, (pol, ins, prem) in EXPECTED.items():
        assert name in rows, f"{name!r} missing or corrupted by the parser"
        assert rows[name]["policies_in_force"] == pol, name
        assert rows[name]["insurance_in_force_usd"] == ins, name
        assert rows[name]["written_premium_in_force_usd"] == prem, name


def test_all_55_states_and_territories_present():
    rows = parse_policies()
    # FEMA's country-wide table has 55 state/territory rows (50 states + DC,
    # PR, Guam, Virgin Islands, N Mariana Islands) before the Unknown/Total
    # rows, which the parser deliberately excludes.
    assert len(rows) == 55, f"expected 55 state/territory rows, parsed {len(rows)}"

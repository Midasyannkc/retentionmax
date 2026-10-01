from src.parse_nfip_claims import parse_claims

EXPECTED = {
    "ALABAMA": (37707, 30164, 53, 7490, 955806365.90),
    "DISTRICT COLUMBIA": (191, 99, 3, 89, 3058010.36),
    "LOUISIANA": (411477, 330276, 558, 80643, 16660481246.31),
}


def test_multiword_claims_rows_parse_correctly():
    rows = {r["state_name"].upper(): r for r in parse_claims()}
    for name, (total, closed, open_, cwop, pay) in EXPECTED.items():
        assert name in rows, name
        r = rows[name]
        assert r["total_losses"] == total, name
        assert r["closed_losses"] == closed, name
        assert r["open_losses"] == open_, name
        assert r["cwop_losses"] == cwop, name
        assert abs(r["total_payments_usd"] - pay) < 0.01, name


def test_dummy_unknown_excluded():
    rows = {r["state_name"].upper() for r in parse_claims()}
    assert "DUMMY-UNKNOWN" not in rows

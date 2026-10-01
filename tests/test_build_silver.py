import duckdb

from src.build_silver import build, DB_PATH


def test_silver_join_produces_54_matched_states():
    joined, unmatched_policies, unmatched_claims = build()
    assert len(joined) == 54
    # Known, disclosed real-data asymmetry: these jurisdictions appear in
    # only one of the two source tables (not a parsing bug -- verified
    # absent from the raw text of the other table).
    assert unmatched_policies == {"N MARIANA ISLANDS"}
    assert unmatched_claims == {"AMERICAN SAMOA", "UNKNOWN"}


def test_loss_ratio_computed_and_sane():
    build()
    con = duckdb.connect(str(DB_PATH))
    row = con.execute(
        "SELECT loss_ratio FROM silver_state_risk_profile WHERE state_name = 'Louisiana'"
    ).fetchone()
    con.close()
    assert row is not None
    # Louisiana is real NFIP's highest-loss state; loss ratio should be well
    # above 1.0 (more paid out historically than current written premium).
    assert row[0] > 1.0

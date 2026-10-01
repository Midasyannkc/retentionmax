import duckdb

from src.build_silver import DB_PATH
from src.build_gold import build_gold_naive, build_gold


def _true_unique_renewal_totals():
    """Ground truth computed by deduping on the natural key ourselves."""
    con = duckdb.connect(str(DB_PATH))
    row = con.execute(
        """
        SELECT COUNT(*), SUM(premium_usd) FROM (
            SELECT DISTINCT policy_id, event_type, event_date, channel, premium_usd
            FROM synthetic_policy_events_raw
            WHERE event_type = 'renewal'
        )
        """
    ).fetchone()
    con.close()
    return row[0], row[1]


def test_naive_gold_overcounts_duplicated_partner_renewals():
    true_renewals, true_premium = _true_unique_renewal_totals()
    naive_renewals, naive_premium = build_gold_naive()
    # The naive aggregation counts every raw row, so it should OVERCOUNT by
    # exactly the number of injected duplicate partner-renewal events.
    assert naive_renewals > true_renewals
    assert naive_premium > true_premium


def test_fixed_gold_reconciles_exactly_to_true_unique_totals():
    true_renewals, true_premium = _true_unique_renewal_totals()
    fixed_renewals, fixed_premium = build_gold()
    assert fixed_renewals == true_renewals
    assert abs(fixed_premium - true_premium) < 0.01


def test_fix_corrects_exactly_the_injected_duplicate_count():
    naive_renewals, naive_premium = build_gold_naive()
    fixed_renewals, fixed_premium = build_gold()
    assert naive_renewals - fixed_renewals == 33
    assert abs((naive_premium - fixed_premium) - 46993.74) < 0.01

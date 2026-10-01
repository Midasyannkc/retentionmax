"""
Silver -> Gold: aggregate the synthetic policy event stream into monthly
retention/growth metrics (Gold layer).

Naive version (see docs/incidents.md, Incident 2): treats every row in
synthetic_policy_events_raw as a distinct, valid event. This silently
double-counts renewal revenue and active-policy counts wherever a
partner-channel webhook was redelivered (see
src/generate_synthetic_book.py's injected duplicate events).
"""
import duckdb

from src.build_silver import DB_PATH


def build_gold_naive():
    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS gold_monthly_metrics_naive")
    con.execute(
        """
        CREATE TABLE gold_monthly_metrics_naive AS
        SELECT
            date_trunc('month', event_date) AS month,
            channel,
            SUM(CASE WHEN event_type = 'new_business' THEN 1 ELSE 0 END) AS new_policies,
            SUM(CASE WHEN event_type = 'renewal' THEN 1 ELSE 0 END) AS renewals,
            SUM(CASE WHEN event_type = 'cancellation' THEN 1 ELSE 0 END) AS cancellations,
            SUM(CASE WHEN event_type = 'renewal' THEN premium_usd ELSE 0 END) AS renewal_premium_usd
        FROM synthetic_policy_events_raw
        GROUP BY 1, 2
        ORDER BY 1, 2
        """
    )
    total_renewal_premium = con.execute(
        "SELECT SUM(renewal_premium_usd) FROM gold_monthly_metrics_naive"
    ).fetchone()[0]
    total_renewals = con.execute(
        "SELECT SUM(renewals) FROM gold_monthly_metrics_naive"
    ).fetchone()[0]
    con.close()
    return total_renewals, total_renewal_premium


if __name__ == "__main__":
    renewals, premium = build_gold_naive()
    print(f"naive: {renewals} renewal events, ${premium:,.2f} renewal premium")

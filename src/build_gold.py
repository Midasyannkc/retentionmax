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


def build_gold():
    """
    FIX (Incident 2): de-duplicate the raw event stream on its natural key
    (policy_id, event_type, event_date, channel, premium_usd) before
    aggregating, so an at-least-once-delivered partner webhook that landed
    twice is counted once. This is the idempotent-ingestion pattern used
    elsewhere in this portfolio (e.g. CareMesh's Kafka-redelivery incident).
    """
    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS silver_policy_events_deduped")
    con.execute(
        """
        CREATE TABLE silver_policy_events_deduped AS
        SELECT DISTINCT policy_id, event_type, event_date, state_name, channel, premium_usd
        FROM synthetic_policy_events_raw
        """
    )
    con.execute("DROP TABLE IF EXISTS gold_monthly_metrics")
    con.execute(
        """
        CREATE TABLE gold_monthly_metrics AS
        SELECT
            date_trunc('month', event_date) AS month,
            state_name,
            channel,
            SUM(CASE WHEN event_type = 'new_business' THEN 1 ELSE 0 END) AS new_policies,
            SUM(CASE WHEN event_type = 'renewal' THEN 1 ELSE 0 END) AS renewals,
            SUM(CASE WHEN event_type = 'cancellation' THEN 1 ELSE 0 END) AS cancellations,
            SUM(CASE WHEN event_type = 'renewal' THEN premium_usd ELSE 0 END) AS renewal_premium_usd,
            SUM(CASE WHEN event_type = 'new_business' THEN premium_usd ELSE 0 END) AS new_business_premium_usd
        FROM silver_policy_events_deduped
        GROUP BY 1, 2, 3
        ORDER BY 1, 2, 3
        """
    )
    total_renewal_premium = con.execute(
        "SELECT SUM(renewal_premium_usd) FROM gold_monthly_metrics"
    ).fetchone()[0]
    total_renewals = con.execute(
        "SELECT SUM(renewals) FROM gold_monthly_metrics"
    ).fetchone()[0]
    con.close()
    return total_renewals, total_renewal_premium


if __name__ == "__main__":
    naive_r, naive_p = build_gold_naive()
    fixed_r, fixed_p = build_gold()
    print(f"naive:  {naive_r} renewal events, ${naive_p:,.2f} renewal premium")
    print(f"fixed:  {fixed_r} renewal events, ${fixed_p:,.2f} renewal premium")
    print(f"corrected by: {naive_r - fixed_r} events, ${naive_p - fixed_p:,.2f}")

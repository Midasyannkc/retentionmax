"""
Financial budgeting/forecasting support: a monthly premium budget-vs-actual
tracker by channel, with variance, answering the JD's "support financial
budgeting, forecasting, and tracking."

Budget targets are a disclosed-synthetic planning assumption (a flat +3%
month-over-month growth target off the first month's actual per channel),
not real Obie figures. Actuals come from the corrected (deduped) Gold layer.
"""
import duckdb

from src.build_silver import DB_PATH
from src.build_gold import build_gold

MONTHLY_GROWTH_TARGET = 0.03


def build_budget_variance():
    build_gold()
    con = duckdb.connect(str(DB_PATH))
    actuals = con.execute(
        """
        SELECT month, channel,
               SUM(new_business_premium_usd + renewal_premium_usd) AS actual_premium_usd
        FROM gold_monthly_metrics
        GROUP BY month, channel
        ORDER BY channel, month
        """
    ).fetchall()
    con.close()

    rows = []
    baseline = {}
    for month, channel, actual in actuals:
        if channel not in baseline:
            baseline[channel] = actual
            budget = actual  # first month: budget = actual (no prior baseline)
        else:
            baseline[channel] *= (1 + MONTHLY_GROWTH_TARGET)
            budget = baseline[channel]
        variance = actual - budget
        variance_pct = (variance / budget) if budget else None
        rows.append(
            {
                "month": month,
                "channel": channel,
                "budget_usd": round(budget, 2),
                "actual_usd": round(actual, 2),
                "variance_usd": round(variance, 2),
                "variance_pct": round(variance_pct, 4) if variance_pct is not None else None,
            }
        )

    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS gold_budget_variance")
    con.execute(
        """
        CREATE TABLE gold_budget_variance (
            month DATE, channel VARCHAR, budget_usd DOUBLE, actual_usd DOUBLE,
            variance_usd DOUBLE, variance_pct DOUBLE
        )
        """
    )
    con.executemany(
        "INSERT INTO gold_budget_variance VALUES (?, ?, ?, ?, ?, ?)",
        [
            (r["month"], r["channel"], r["budget_usd"], r["actual_usd"], r["variance_usd"], r["variance_pct"])
            for r in rows
        ],
    )
    con.close()
    return rows


if __name__ == "__main__":
    rows = build_budget_variance()
    over = [r for r in rows if r["variance_pct"] is not None and r["variance_pct"] < -0.10]
    print(f"{len(rows)} month-channel rows; {len(over)} missed budget by >10%")
    for r in over[:5]:
        print(r)

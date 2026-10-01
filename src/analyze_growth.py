"""
Hypothesis-driven growth/retention analysis, the core deliverable this JD
asks for: "develop hypotheses to understand drivers of growth or
stagnation" and "conduct analyses providing insight into critical business
questions."

Hypothesis: renewal-rate stagnation is concentrated in higher real-flood-
loss-ratio states, because renewal-time premium increases in those states
are larger and harder for policyholders to absorb.

This is tested against the corrected (deduped) Gold layer joined back to
the real NFIP state_risk_profile loss ratios, not asserted.
"""
import duckdb

from src.build_silver import DB_PATH
from src.build_gold import build_gold


LOSS_RATIO_TIERS_SQL = """
WITH policy_lifecycle AS (
    -- a policy's anniversary outcome: did it renew or cancel, and in which state
    SELECT state_name, channel, event_type,
           SUM(CASE WHEN event_type = 'renewal' THEN 1 ELSE 0 END) AS renewals,
           SUM(CASE WHEN event_type = 'cancellation' THEN 1 ELSE 0 END) AS cancellations
    FROM silver_policy_events_deduped
    WHERE event_type IN ('renewal', 'cancellation')
    GROUP BY state_name, channel, event_type
),
state_outcomes AS (
    SELECT state_name,
           SUM(renewals) AS renewals,
           SUM(cancellations) AS cancellations
    FROM policy_lifecycle
    GROUP BY state_name
),
joined AS (
    SELECT o.state_name,
           o.renewals,
           o.cancellations,
           CAST(o.renewals AS DOUBLE) / NULLIF(o.renewals + o.cancellations, 0) AS renewal_rate,
           s.loss_ratio,
           CASE
               WHEN s.loss_ratio IS NULL THEN 'unknown'
               WHEN s.loss_ratio < 1.0 THEN 'low (<1.0x)'
               WHEN s.loss_ratio < 3.0 THEN 'medium (1-3x)'
               ELSE 'high (3x+)'
           END AS loss_ratio_tier
    FROM state_outcomes o
    LEFT JOIN silver_state_risk_profile s USING (state_name)
    WHERE o.renewals + o.cancellations >= 5  -- exclude tiny-sample states
)
SELECT loss_ratio_tier,
       COUNT(*) AS n_states,
       SUM(renewals) AS total_renewals,
       SUM(cancellations) AS total_cancellations,
       ROUND(AVG(renewal_rate), 4) AS avg_renewal_rate
FROM joined
GROUP BY loss_ratio_tier
ORDER BY avg_renewal_rate
"""


def run_analysis():
    build_gold()  # ensure silver_policy_events_deduped + gold tables exist and are current
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute(LOSS_RATIO_TIERS_SQL).fetchall()
    con.close()
    return rows


if __name__ == "__main__":
    rows = run_analysis()
    print(f"{'loss_ratio_tier':<16} {'n_states':>8} {'renewals':>9} {'cancels':>8} {'avg_renewal_rate':>17}")
    for r in rows:
        print(f"{r[0]:<16} {r[1]:>8} {r[2]:>9} {r[3]:>8} {r[4]:>17}")

"""
Generate a disclosed-synthetic 24-month (Jan 2024 - Dec 2025) landlord/
real-estate-investor insurance book-of-business event stream, shaped to be
internally consistent with the real NFIP state_risk_profile silver table
(market size and loss ratio by state). See data/synthetic/GENERATION_NOTES.md.

Deliberately includes a realistic partner-channel data-quality problem:
at-least-once webhook delivery of renewal events, which can arrive
duplicated. This is injected on purpose so it can be found and fixed with
genuine git history (docs/incidents.md, Incident 2) rather than narrated
after the fact.
"""
import random
from datetime import date
from pathlib import Path

import duckdb

from src.build_silver import DB_PATH

RANDOM_SEED = 20240101
CHANNELS = ["direct", "agent", "partner"]
CHANNEL_WEIGHTS = [0.45, 0.30, 0.25]
MONTHS = [(y, m) for y in (2024, 2025) for m in range(1, 13)]
BASE_MONTHLY_NEW_POLICIES_PER_STATE = 1.1  # scaled by real market-size weight
PARTNER_WEBHOOK_DUPLICATE_RATE = 0.07  # 7% of partner-channel renewal events


def load_state_profile():
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute(
        "SELECT state_name, policies_in_force, loss_ratio FROM silver_state_risk_profile"
    ).fetchall()
    con.close()
    total = sum(r[1] for r in rows)
    return [
        {"state_name": r[0], "weight": r[1] / total, "loss_ratio": r[2] or 0.0}
        for r in rows
    ]


def generate_events():
    rng = random.Random(RANDOM_SEED)
    states = load_state_profile()
    events = []
    policy_id_counter = 1
    # active_policies: policy_id -> dict(state, channel, start_month_idx, premium)
    active_policies = {}

    for month_idx, (y, m) in enumerate(MONTHS):
        event_month = date(y, m, 1)

        # 1) New business this month, volume scaled by real state market size
        for state in states:
            expected_new = BASE_MONTHLY_NEW_POLICIES_PER_STATE * state["weight"] * len(states) * 3
            n_new = max(0, int(round(expected_new)) + rng.randint(-1, 1))
            for _ in range(n_new):
                channel = rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]
                premium = round(rng.uniform(650, 2200), 2)
                pid = f"POL-{policy_id_counter:06d}"
                policy_id_counter += 1
                active_policies[pid] = {
                    "state_name": state["state_name"],
                    "channel": channel,
                    "premium": premium,
                    "loss_ratio": state["loss_ratio"],
                    "start_idx": month_idx,
                }
                events.append(
                    {
                        "policy_id": pid,
                        "event_type": "new_business",
                        "event_date": event_month,
                        "state_name": state["state_name"],
                        "channel": channel,
                        "premium_usd": premium,
                    }
                )

        # 2) Renewals and cancellations for policies reaching their 12-month
        #    anniversary (annual term policies)
        for pid, info in list(active_policies.items()):
            age = month_idx - info["start_idx"]
            if age > 0 and age % 12 == 0:
                # renewal probability depressed by real state loss ratio
                base_renewal_prob = 0.88
                loss_penalty = min(0.25, info["loss_ratio"] * 0.05)
                renewal_prob = max(0.45, base_renewal_prob - loss_penalty)
                if rng.random() < renewal_prob:
                    new_premium = round(info["premium"] * rng.uniform(1.02, 1.09), 2)
                    renewal_event = {
                        "policy_id": pid,
                        "event_type": "renewal",
                        "event_date": event_month,
                        "state_name": info["state_name"],
                        "channel": info["channel"],
                        "premium_usd": new_premium,
                    }
                    events.append(renewal_event)
                    # INJECTED BUG (disclosed, found in Incident 2): partner
                    # channel webhook delivery is at-least-once, so a
                    # fraction of partner renewal events are redelivered and
                    # land in the raw event stream a second time.
                    if info["channel"] == "partner" and rng.random() < PARTNER_WEBHOOK_DUPLICATE_RATE:
                        events.append(dict(renewal_event))
                    info["premium"] = new_premium
                else:
                    events.append(
                        {
                            "policy_id": pid,
                            "event_type": "cancellation",
                            "event_date": event_month,
                            "state_name": info["state_name"],
                            "channel": info["channel"],
                            "premium_usd": 0.0,
                        }
                    )
                    del active_policies[pid]

    return events


def write_to_duckdb(events):
    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS synthetic_policy_events_raw")
    con.execute(
        """
        CREATE TABLE synthetic_policy_events_raw (
            policy_id VARCHAR,
            event_type VARCHAR,
            event_date DATE,
            state_name VARCHAR,
            channel VARCHAR,
            premium_usd DOUBLE
        )
        """
    )
    con.executemany(
        "INSERT INTO synthetic_policy_events_raw VALUES (?, ?, ?, ?, ?, ?)",
        [
            (e["policy_id"], e["event_type"], e["event_date"], e["state_name"], e["channel"], e["premium_usd"])
            for e in events
        ],
    )
    con.close()


if __name__ == "__main__":
    events = generate_events()
    write_to_duckdb(events)
    print(f"generated {len(events)} raw policy events")

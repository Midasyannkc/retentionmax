"""
Bronze -> Silver: join the real NFIP state-level policy and claims tables
into one conformed state_risk_profile table, in DuckDB.

This is the REAL-data anchor layer for the project. State names arrive in
different casing from the two source tables (Title Case in the policies
report, ALL CAPS in the claims report), so they are normalized to a common
key before the join.
"""
from pathlib import Path

import duckdb

from src.parse_nfip_state import parse_policies
from src.parse_nfip_claims import parse_claims

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "retentionmax.duckdb"


def normalize(name: str) -> str:
    return " ".join(name.strip().upper().split())


def build():
    policies = {normalize(r["state_name"]): r for r in parse_policies()}
    claims = {normalize(r["state_name"]): r for r in parse_claims()}

    joined = []
    unmatched_policies = set(policies) - set(claims)
    unmatched_claims = set(claims) - set(policies)

    for key in sorted(set(policies) & set(claims)):
        p, c = policies[key], claims[key]
        written_premium = p["written_premium_in_force_usd"]
        loss_ratio = (c["total_payments_usd"] / written_premium) if written_premium else None
        joined.append(
            {
                "state_name": key.title(),
                "policies_in_force": p["policies_in_force"],
                "insurance_in_force_usd": p["insurance_in_force_usd"],
                "written_premium_in_force_usd": written_premium,
                "total_losses": c["total_losses"],
                "closed_losses": c["closed_losses"],
                "open_losses": c["open_losses"],
                "total_payments_usd": c["total_payments_usd"],
                "loss_ratio": loss_ratio,
            }
        )

    con = duckdb.connect(str(DB_PATH))
    con.execute("DROP TABLE IF EXISTS silver_state_risk_profile")
    con.execute(
        """
        CREATE TABLE silver_state_risk_profile (
            state_name VARCHAR,
            policies_in_force BIGINT,
            insurance_in_force_usd DOUBLE,
            written_premium_in_force_usd DOUBLE,
            total_losses BIGINT,
            closed_losses BIGINT,
            open_losses BIGINT,
            total_payments_usd DOUBLE,
            loss_ratio DOUBLE
        )
        """
    )
    con.executemany(
        """INSERT INTO silver_state_risk_profile VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                r["state_name"],
                r["policies_in_force"],
                r["insurance_in_force_usd"],
                r["written_premium_in_force_usd"],
                r["total_losses"],
                r["closed_losses"],
                r["open_losses"],
                r["total_payments_usd"],
                r["loss_ratio"],
            )
            for r in joined
        ],
    )
    con.close()
    return joined, unmatched_policies, unmatched_claims


if __name__ == "__main__":
    joined, up, uc = build()
    print(f"joined {len(joined)} states; unmatched policies-only={up}; unmatched claims-only={uc}")

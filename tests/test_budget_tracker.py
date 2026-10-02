from src.budget_tracker import build_budget_variance


def test_budget_variance_rows_cover_all_channel_months():
    rows = build_budget_variance()
    assert len(rows) == 72  # 24 months x 3 channels
    channels = {r["channel"] for r in rows}
    assert channels == {"direct", "agent", "partner"}


def test_first_month_has_zero_variance_by_construction():
    rows = build_budget_variance()
    first_month_rows = [r for r in rows if r["month"].month == 1 and r["month"].year == 2024]
    assert all(r["variance_usd"] == 0.0 for r in first_month_rows)

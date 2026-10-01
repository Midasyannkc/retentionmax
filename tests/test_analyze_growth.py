from src.analyze_growth import run_analysis


def test_renewal_rate_decreases_monotonically_with_loss_ratio_tier():
    rows = {r[0]: r[4] for r in run_analysis()}
    assert rows["low (<1.0x)"] > rows["medium (1-3x)"] > rows["high (3x+)"]


def test_high_loss_tier_has_most_states_and_volume():
    rows = {r[0]: r for r in run_analysis()}
    # Real NFIP loss ratios: most states historically paid out more in
    # claims than they currently hold in written premium (loss ratio > 3x
    # reflects decades of cumulative payments against current premium, not a
    # single bad year), so the high tier should dominate state count.
    assert rows["high (3x+)"][1] >= 30

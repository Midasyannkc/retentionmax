"""
Render the Sigma-equivalent dashboard as static charts (Sigma itself isn't
reachable from this build sandbox). docs/dashboard/SIGMA_SPEC.md documents
how these same queries map onto actual Sigma workbook elements.

Palette: validated categorical slots 1/2/3 (blue/orange/aqua) for the three
channels (direct/agent/partner), a single-hue sequential ramp for the
ordinal loss-ratio tiers, and a diverging red/blue + neutral-gray midpoint
for budget variance -- per the dataviz skill's color-by-job rule.
"""
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.build_silver import DB_PATH
from src.analyze_growth import run_analysis
from src.budget_tracker import build_budget_variance

OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "dashboard"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CHANNEL_COLOR = {"direct": "#2a78d6", "agent": "#eb6834", "partner": "#1baf7a"}
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID_COLOR = "#e3e2dd"


def _style_axes(ax):
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)


def chart_monthly_premium_by_channel():
    con = duckdb.connect(str(DB_PATH))
    rows = con.execute(
        """
        SELECT month, channel, SUM(new_business_premium_usd + renewal_premium_usd) AS total_premium
        FROM gold_monthly_metrics GROUP BY 1, 2 ORDER BY 1, 2
        """
    ).fetchall()
    con.close()

    by_channel = {}
    for month, channel, total in rows:
        by_channel.setdefault(channel, []).append((month, total))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for channel in ("direct", "agent", "partner"):
        pts = sorted(by_channel[channel])
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.plot(xs, ys, color=CHANNEL_COLOR[channel], linewidth=2, label=channel, solid_capstyle="round")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    _style_axes(ax)
    ax.set_title("Monthly written premium by channel", color=TEXT_PRIMARY, fontsize=12, loc="left")
    ax.set_ylabel("Premium (USD)", color=TEXT_SECONDARY, fontsize=9)
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "01_monthly_premium_by_channel.png", dpi=150)
    plt.close(fig)


def chart_renewal_rate_by_loss_tier():
    rows = run_analysis()
    tiers = [r[0] for r in rows]
    rates = [r[4] for r in rows]
    # sequential single-hue ramp, light -> dark, by tier severity
    ramp = {"low (<1.0x)": "#bcdcf5", "medium (1-3x)": "#5fa3e0", "high (3x+)": "#1a4f8a"}
    colors = [ramp.get(t, "#2a78d6") for t in tiers]

    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(tiers, rates, color=colors, width=0.55)
    for b, r in zip(bars, rates):
        ax.text(b.get_x() + b.get_width() / 2, r + 0.015, f"{r:.0%}", ha="center", fontsize=10, color=TEXT_PRIMARY)
    _style_axes(ax)
    ax.set_ylim(0, 1.0)
    ax.set_title("Renewal rate by real NFIP loss-ratio tier", color=TEXT_PRIMARY, fontsize=12, loc="left")
    ax.set_ylabel("Renewal rate", color=TEXT_SECONDARY, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "02_renewal_rate_by_loss_tier.png", dpi=150)
    plt.close(fig)


def chart_budget_variance():
    rows = build_budget_variance()
    by_month = {}
    for r in rows:
        by_month.setdefault(r["month"], 0.0)
        by_month[r["month"]] += r["variance_usd"]
    months = sorted(by_month)
    values = [by_month[m] for m in months]
    colors = ["#2a78d6" if v >= 0 else "#e34948" for v in values]  # diverging: blue over / red under

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(months, values, color=colors, width=20)
    ax.axhline(0, color=TEXT_SECONDARY, linewidth=1)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    _style_axes(ax)
    ax.set_title("Total monthly premium budget variance (all channels)", color=TEXT_PRIMARY, fontsize=12, loc="left")
    ax.set_ylabel("Variance vs budget (USD)", color=TEXT_SECONDARY, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "03_budget_variance.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    chart_monthly_premium_by_channel()
    chart_renewal_rate_by_loss_tier()
    chart_budget_variance()
    print("wrote charts to", OUT_DIR)

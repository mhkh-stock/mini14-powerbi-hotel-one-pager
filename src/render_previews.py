#!/usr/bin/env python3
"""Render preview charts for Mini #14 (run: python3 src/render_previews.py).

matplotlib renders of the same numbers the Power BI page will show —
proof the model is right before Power BI opens, not the dashboard itself.
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "hotel.db"
OUT = ROOT / "outputs"

MONTHS = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
DAYS_IN_MONTH = {"2026-01": 31, "2026-02": 28, "2026-03": 31,
                 "2026-04": 30, "2026-05": 31, "2026-06": 30}


def bar(title, labels, values, path, ylabel, fmt="{:,.0f}"):
    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(labels, values, color="#1F4E79")
    plt.title(title, fontsize=13, fontweight="bold")
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    for b, v in zip(bars, values):
        plt.text(b.get_x() + b.get_width() / 2, b.get_height(), fmt.format(v),
                 ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"wrote {path}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)

    monthly = dict(con.execute(
        "SELECT strftime('%Y-%m', checkin_date), SUM(total_pkr) "
        "FROM fact_bookings WHERE status='stayed' "
        "GROUP BY 1 ORDER BY 1"))
    bar("Paid revenue by month (PKR) — Margalla View Hotel, Jan–Jun 2026",
        MONTHS, [monthly[m] for m in MONTHS],
        OUT / "preview_revenue_by_month.png",
        "PKR", fmt="PKR {:,.0f}")

    nights = dict(con.execute(
        "SELECT strftime('%Y-%m', checkin_date), SUM(nights) "
        "FROM fact_bookings WHERE status='stayed' "
        "GROUP BY 1 ORDER BY 1"))
    occ = [nights[m] / (40 * DAYS_IN_MONTH[m]) * 100 for m in MONTHS]
    bar("Occupancy rate by month (%) — 40 rooms, Jan–Jun 2026",
        MONTHS, occ, OUT / "preview_occupancy_by_month.png",
        "Occupancy %", fmt="{:.1f}%")

    channels, counts = zip(*con.execute(
        "SELECT channel, COUNT(*) FROM fact_bookings "
        "WHERE status='stayed' GROUP BY channel ORDER BY COUNT(*) DESC"))
    bar("Stayed bookings by channel",
        list(channels), list(counts),
        OUT / "preview_bookings_by_channel.png", "Bookings")

    types, rates = zip(*con.execute(
        "SELECT room_type, "
        "100.0 * SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) / COUNT(*) "
        "FROM fact_bookings GROUP BY room_type ORDER BY 2 DESC"))
    bar("Cancellation rate by room type (%) — Standard cancels most",
        list(types), list(rates),
        OUT / "preview_cancellations_by_room_type.png",
        "Cancellation %", fmt="{:.1f}%")
    con.close()


if __name__ == "__main__":
    main()

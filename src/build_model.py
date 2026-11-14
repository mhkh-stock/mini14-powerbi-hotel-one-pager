#!/usr/bin/env python3
"""Build data/hotel.db from the CSVs (run: python3 src/build_model.py).

Also writes outputs/kpi_summary.txt — the headline numbers the README
and the build guide cite (recomputed here, asserted in src/checks.py).
"""
import csv
import sqlite3
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "hotel.db"
SCHEMA = ROOT / "model" / "schema.sql"

ROOMS = 40
DAYS = 181  # Jan–Jun 2026


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    for table, path in [("dim_room", "rooms.csv"),
                        ("fact_bookings", "bookings.csv"),
                        ("fact_payments", "payments.csv")]:
        rows = list(csv.DictReader(open(ROOT / "data" / path, encoding="utf-8")))
        cols = rows[0].keys()
        con.executemany(
            f"INSERT INTO {table} ({','.join(cols)}) "
            f"VALUES ({','.join('?' * len(cols))})",
            [[r[c] for c in cols] for r in rows])
    # Date dimension: every day Jan–Jun 2026.
    d = date(2026, 1, 1)
    while d <= date(2026, 6, 30):
        con.execute(
            "INSERT INTO dim_date VALUES (?,?,?,?,?,?)",
            (d.isoformat(), d.year, d.month, d.strftime("%Y-%m"),
             d.strftime("%A"), 1 if d.weekday() >= 5 else 0))
        d += timedelta(days=1)
    con.commit()

    n = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
         for t in ("dim_room", "fact_bookings", "fact_payments")}
    rev = con.execute("SELECT SUM(amount_pkr) FROM fact_payments "
                      "WHERE status='paid'").fetchone()[0]
    room_nights = con.execute(
        "SELECT SUM(nights) FROM fact_bookings WHERE status='stayed'"
    ).fetchone()[0]
    occupancy = room_nights / (ROOMS * DAYS) * 100
    adr = rev / room_nights
    revpar = rev / (ROOMS * DAYS)
    cancelled = con.execute(
        "SELECT COUNT(*) FROM fact_bookings WHERE status='cancelled'"
    ).fetchone()[0]
    stayed_n = con.execute(
        "SELECT COUNT(*) FROM fact_bookings WHERE status='stayed'"
    ).fetchone()[0]
    noshow = con.execute(
        "SELECT COUNT(*) FROM fact_bookings WHERE status='no-show'"
    ).fetchone()[0]
    refunded = con.execute(
        "SELECT SUM(amount_pkr) FROM fact_payments WHERE status='refunded'"
    ).fetchone()[0]
    best_month = con.execute(
        "SELECT strftime('%Y-%m', checkin_date) m, SUM(total_pkr) "
        "FROM fact_bookings WHERE status='stayed' "
        "GROUP BY m ORDER BY SUM(total_pkr) DESC LIMIT 1").fetchone()
    top_channel = con.execute(
        "SELECT channel, SUM(total_pkr) FROM fact_bookings "
        "WHERE status='stayed' GROUP BY channel "
        "ORDER BY SUM(total_pkr) DESC LIMIT 1").fetchone()
    (ROOT / "outputs").mkdir(parents=True, exist_ok=True)
    (ROOT / "outputs" / "kpi_summary.txt").write_text(
        f"rooms: {n['dim_room']}\n"
        f"bookings: {n['fact_bookings']}\n"
        f"stayed: {stayed_n}\n"
        f"cancelled: {cancelled}\n"
        f"no-show: {noshow}\n"
        f"payments: {n['fact_payments']}\n"
        f"paid revenue Jan-Jun 2026: PKR {rev:,}\n"
        f"refunded amount (cancelled bookings): PKR {refunded:,}\n"
        f"room-nights sold: {room_nights} / {ROOMS * DAYS} available\n"
        f"occupancy rate: {occupancy:.1f}%\n"
        f"ADR (avg daily rate): PKR {adr:,.0f}\n"
        f"RevPAR: PKR {revpar:,.0f}\n"
        f"cancellation rate: {cancelled / n['fact_bookings'] * 100:.1f}%\n"
        f"best revenue month: {best_month[0]} (PKR {best_month[1]:,})\n"
        f"top channel by revenue: {top_channel[0]} (PKR {top_channel[1]:,})\n",
        encoding="utf-8")
    print(f"loaded hotel.db: {n}")
    print(f"paid revenue PKR {rev:,} | occupancy {occupancy:.1f}% | "
          f"ADR PKR {adr:,.0f} | RevPAR PKR {revpar:,.0f}")
    con.close()


if __name__ == "__main__":
    main()

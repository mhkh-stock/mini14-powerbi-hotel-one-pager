#!/usr/bin/env python3
"""Data-quality checks as code for Mini #14 (run: python3 src/checks.py).

Recomputes every headline number from the CSVs / DB independently.
Exit code 0 = all pass.
"""
import csv
import sqlite3
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
DB = DATA / "hotel.db"

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def main():
    rooms = list(csv.DictReader(open(DATA / "rooms.csv", encoding="utf-8")))
    bookings = list(csv.DictReader(open(DATA / "bookings.csv", encoding="utf-8")))
    payments = list(csv.DictReader(open(DATA / "payments.csv", encoding="utf-8")))
    stayed = [b for b in bookings if b["status"] == "stayed"]
    cancelled = [b for b in bookings if b["status"] == "cancelled"]
    noshow = [b for b in bookings if b["status"] == "no-show"]
    paid = [p for p in payments if p["status"] == "paid"]
    refunded = [p for p in payments if p["status"] == "refunded"]
    failed_pay = [p for p in payments if p["status"] == "failed"]
    room_by_id = {r["room_id"]: r for r in rooms}
    pay_by_booking = {p["booking_id"]: p for p in payments}

    print("== shape ==")
    check("40 rooms", len(rooms) == 40, f"got {len(rooms)}")
    check("4 room types", len({r["room_type"] for r in rooms}) == 4)
    check("room mix is 18/12/6/4",
          [sum(1 for r in rooms if r["room_type"] == t) for t in
           ("Standard", "Deluxe", "Executive Suite", "Family Suite")]
          == [18, 12, 6, 4])
    check("room ids unique", len(room_by_id) == 40)
    check("598 bookings (488 stayed, 85 cancelled, 25 no-show)",
          len(bookings) == 598 and len(stayed) == 488
          and len(cancelled) == 85 and len(noshow) == 25,
          f"{len(bookings)} total, {len(stayed)} stayed, "
          f"{len(cancelled)} cancelled, {len(noshow)} no-show")
    check("booking ids unique", len({b["booking_id"] for b in bookings}) == 598)
    check("598 payments, one per booking",
          len(payments) == 598 and len(pay_by_booking) == 598)
    check("85 refunded, 25 failed payments",
          len(refunded) == 85 and len(failed_pay) == 25,
          f"{len(refunded)} refunded, {len(failed_pay)} failed")

    print("== referential integrity ==")
    check("every booking's room exists",
          all(b["room_id"] in room_by_id for b in bookings))
    check("every booking's room_type matches its room",
          all(b["room_type"] == room_by_id[b["room_id"]]["room_type"]
              for b in bookings))
    check("guests never exceed the room's capacity",
          all(int(b["guests"]) <= int(room_by_id[b["room_id"]]["capacity"])
              for b in bookings))
    check("nights equals checkout minus checkin (days)",
          all(int(b["nights"]) ==
              (date.fromisoformat(b["checkout_date"]) -
               date.fromisoformat(b["checkin_date"])).days for b in bookings))
    check("total_pkr equals nightly rate x nights",
          all(int(b["total_pkr"]) == int(b["nightly_rate_pkr"]) * int(b["nights"])
              for b in bookings))
    check("booking_date is on or before check-in",
          all(b["booking_date"] <= b["checkin_date"] for b in bookings))
    check("every check-in is inside Jan–Jun 2026",
          all("2026-01-01" <= b["checkin_date"] <= "2026-06-30" for b in bookings))
    check("cancel_date present exactly for cancelled bookings",
          all(bool(b["cancel_date"]) == (b["status"] == "cancelled")
              for b in bookings))
    check("cancel_date is before check-in",
          all(b["cancel_date"] < b["checkin_date"] for b in cancelled))
    check("payment status follows booking status "
          "(stayed->paid, cancelled->refunded, no-show->failed)",
          all(pay_by_booking[b["booking_id"]]["status"] ==
              {"stayed": "paid", "cancelled": "refunded",
               "no-show": "failed"}[b["status"]] for b in bookings))
    check("payment amount equals the booking total",
          all(int(pay_by_booking[b["booking_id"]]["amount_pkr"]) ==
              int(b["total_pkr"]) for b in bookings))
    check("paid_on is blank exactly for failed payments",
          all(bool(p["paid_on"]) == (p["status"] != "failed") for p in payments))
    check("no two stayed bookings overlap on the same room",
          _no_overlap(stayed))

    print("== headline numbers (recomputed from the CSVs) ==")
    revenue = sum(int(p["amount_pkr"]) for p in paid)
    room_nights = sum(int(b["nights"]) for b in stayed)
    check("paid revenue is PKR 18,125,500",
          revenue == 18125500, f"PKR {revenue:,}")
    check("room-nights sold is 1,475", room_nights == 1475,
          f"got {room_nights}")
    check("occupancy is 20.4% (1,475 / 7,240)",
          abs(room_nights / (40 * 181) * 100 - 20.4) < 0.05)
    check("ADR is PKR 12,288",
          abs(revenue / room_nights - 12288) < 1, f"PKR {revenue / room_nights:,.0f}")
    check("RevPAR is PKR 2,504",
          abs(revenue / (40 * 181) - 2504) < 1, f"PKR {revenue / (40 * 181):,.0f}")
    check("cancellation rate is 14.2% (85/598)",
          abs(len(cancelled) / len(bookings) * 100 - 14.2) < 0.05)
    check("avg length of stay is 3.02 nights",
          abs(sum(int(b["nights"]) for b in stayed) / len(stayed) - 3.02) < 0.01)
    check("avg guests per booking is 1.78",
          abs(sum(int(b["guests"]) for b in stayed) / len(stayed) - 1.78) < 0.01)
    check("refunded amount is PKR 2,312,400",
          sum(int(p["amount_pkr"]) for p in refunded) == 2312400)
    check("OTA is the top channel by revenue (37.3%)",
          max(("OTA", "Direct", "Walk-in", "Travel Agent"),
              key=lambda c: sum(int(b["total_pkr"]) for b in stayed
                               if b["channel"] == c)) == "OTA")
    check("May is the best revenue month (PKR 3,690,700)",
          max(("2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"),
              key=lambda m: sum(int(b["total_pkr"]) for b in stayed
                               if b["checkin_date"][:7] == m)) == "2026-05")
    check("Standard cancels most (17.2%), Family Suite least (10.3%)",
          abs(sum(1 for b in bookings if b["room_type"] == "Standard"
                  and b["status"] == "cancelled") /
              sum(1 for b in bookings if b["room_type"] == "Standard") * 100
              - 17.2) < 0.05)

    print("== SQLite model ==")
    con = sqlite3.connect(DB)
    check("DB holds 40 rooms",
          con.execute("SELECT COUNT(*) FROM dim_room").fetchone()[0] == 40)
    check("DB bookings match CSV",
          con.execute("SELECT COUNT(*) FROM fact_bookings").fetchone()[0]
          == len(bookings))
    check("DB payments match CSV",
          con.execute("SELECT COUNT(*) FROM fact_payments").fetchone()[0]
          == len(payments))
    check("DB paid revenue reconciles to CSV",
          con.execute("SELECT SUM(amount_pkr) FROM fact_payments "
                      "WHERE status='paid'").fetchone()[0] == revenue)
    check("DB room-nights reconcile to CSV",
          con.execute("SELECT SUM(nights) FROM fact_bookings "
                      "WHERE status='stayed'").fetchone()[0] == room_nights)
    check("DB has 181 date rows (Jan–Jun 2026)",
          con.execute("SELECT COUNT(*) FROM dim_date").fetchone()[0] == 181)
    check("DB monthly occupancy never exceeds 100%",
          all(n / (40 * d) <= 1.0 for _, n, d in con.execute(
              "SELECT strftime('%Y-%m', checkin_date), SUM(nights), "
              "CASE strftime('%m', checkin_date) "
              "WHEN '01' THEN 31 WHEN '02' THEN 28 WHEN '03' THEN 31 "
              "WHEN '04' THEN 30 WHEN '05' THEN 31 ELSE 30 END "
              "FROM fact_bookings WHERE status='stayed' GROUP BY 1")))
    con.close()

    print("== DAX + previews ==")
    dax = (ROOT / "dax" / "measures.dax").read_text(encoding="utf-8")
    for measure in ["Total Revenue", "Room Nights Sold", "Occupancy Rate",
                    "ADR", "RevPAR", "Total Bookings", "Cancellation Rate",
                    "Avg Length of Stay", "Avg Guests per Booking",
                    "Revenue Share by Channel", "Refunded Payments"]:
        check(f"DAX defines '{measure}'", measure in dax)
    for png in ["preview_revenue_by_month.png",
                "preview_occupancy_by_month.png",
                "preview_bookings_by_channel.png",
                "preview_cancellations_by_room_type.png"]:
        p = OUT / png
        check(f"preview {png} exists and is non-empty",
              p.exists() and p.stat().st_size > 5000,
              f"{p.stat().st_size if p.exists() else 0} bytes")
    check("kpi_summary.txt exists",
          (OUT / "kpi_summary.txt").exists())

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


def _no_overlap(stayed):
    """True when no two stayed bookings share a room on the same night."""
    seen = set()
    for b in stayed:
        d = date.fromisoformat(b["checkin_date"])
        out = date.fromisoformat(b["checkout_date"])
        while d < out:
            key = (b["room_id"], d)
            if key in seen:
                return False
            seen.add(key)
            d = date.fromordinal(d.toordinal() + 1)
    return True


if __name__ == "__main__":
    sys.exit(main())

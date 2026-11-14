# Data dictionary — Mini #14 (Margalla View Hotel, SAMPLE)

Fictional Islamabad hotel, Jan–Jun 2026. 40 rooms, 4 room types,
598 bookings (488 stayed, 85 cancelled, 25 no-show), 598 payments.
Generated deterministically (`src/generate_data.py`, seed 14) —
re-running reproduces the identical files. No real hotel, guest or
payment is involved.

## Files

| File | What it is |
|---|---|
| `rooms.csv` | 40 rooms: type, nightly base rate, floor, capacity |
| `bookings.csv` | 598 bookings: room, dates, nights, channel, guests, rate, status |
| `payments.csv` | 598 payments: one per booking (paid / refunded / failed) |
| `hotel.db` | SQLite star-schema load (`model/schema.sql`); rebuild with `python3 src/build_model.py`; NOT uploaded (rebuildable from the CSVs) |

## Columns

**rooms.csv** — `room_id` (STD-1xx / DLX-2xx / EXE-3xx / FAM-2xx) ·
`room_type` (Standard / Deluxe / Executive Suite / Family Suite) ·
`nightly_rate_pkr` (base rate: 8,000 / 12,000 / 20,000 / 16,000) ·
`floor` · `capacity` (max guests: 2 / 3 / 2 / 4).

**bookings.csv** — `booking_id` (B0001–B0598) · `room_id` ·
`booking_date` (up to 45 days before check-in) · `checkin_date`
(2026-01-01–2026-06-30) · `checkout_date` · `nights` (1–5) ·
`room_type` · `channel` (OTA / Direct / Walk-in / Travel Agent) ·
`guests` (never above the room's capacity) · `nightly_rate_pkr`
(base rate + weekend uplift + noise, rounded to PKR 100) ·
`total_pkr` (= nightly rate × nights) · `status`
(stayed/cancelled/no-show) · `cancel_date` (only for cancelled
bookings, 1–7 days before check-in).

**payments.csv** — `payment_id` · `booking_id` · `amount_pkr`
(= the booking total) · `status` (paid/refunded/failed) · `paid_on`
(blank when failed). One row per booking: stayed → paid, cancelled
→ refunded, no-show → failed. Paid revenue is PKR 18,125,500;
refunded PKR 2,312,400; 25 failed payments (the no-shows).

## Design notes (what the data was built to show)

- Occupancy is low on purpose: 20.4% overall, best month only 24.6%
  (April) — the headline finding is the empty-room problem, not a
  healthy hotel. Stayed bookings are generated room by room, day by
  day, so a room is never double-booked and occupancy can never
  exceed 100%.
- Deluxe earns more than Standard with 78 fewer bookings (PKR
  5,643,000 vs PKR 5,517,900) — the upsell finding.
- Standard cancels most (17.2%) and the Direct channel cancels most
  (16.3%); Travel Agent cancels least (9.9%) — the confirmation-call
  finding.
- Revenue grows monthly Jan–May, then dips in June (PKR 3,690,700 →
  PKR 2,909,400) — the early-warning finding.

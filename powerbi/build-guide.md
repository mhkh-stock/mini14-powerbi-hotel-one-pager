# Power BI build guide — Margalla View Hotel one-pager (15 minutes)

**Goal:** one page that answers "is the hotel making money?" — rooms,
money, channels, and the cancellations that eat the revenue. No
`.pbix` is bundled: Power BI Desktop authors it from this model (a
`.pbix` is a binary only Power BI can write — shipping one would be
faking it).

## 0. Files you need

- `data/rooms.csv`, `data/bookings.csv`, `data/payments.csv` (SAMPLE
  data — fictional Islamabad hotel, Jan–Jun 2026)
- `model/schema.sql` (the star schema; the CSVs already match it)
- `dax/measures.dax` (11 measures — copy-paste, one at a time)

## 1. Load the data (3 min)

1. Power BI Desktop → **Get Data → Text/CSV** → load the 3 CSVs.
2. Rename the queries to `dim_room`, `fact_bookings`, `fact_payments`
   (the names the DAX measures expect).
3. Set types: `booking_date` / `checkin_date` / `checkout_date` /
   `paid_on` → Date; `nights` / `guests` / `nightly_rate_pkr` /
   `total_pkr` / `amount_pkr` → Whole Number.

## 2. Build the model (3 min)

Model view → drag these relationships (single direction, one-to-many):

| From | To |
|---|---|
| `dim_room[room_id]` | `fact_bookings[room_id]` |
| `fact_bookings[booking_id]` | `fact_payments[booking_id]` |

Star schema: `dim_room` is the dimension, `fact_bookings` and
`fact_payments` the facts, joined on room and booking. `dim_date`
covers every day Jan–Jun 2026 (181 rows) for time visuals — relate
`dim_date[date]` to `fact_bookings[checkin_date]` if you add it.

## 3. Add the measures (3 min)

Modeling → **New measure** → paste each block from `dax/measures.dax`:
`Total Revenue`, `Room Nights Sold`, `Occupancy Rate`, `ADR`,
`RevPAR`, `Total Bookings`, `Cancellation Rate`,
`Avg Length of Stay`, `Avg Guests per Booking`,
`Revenue Share by Channel`, `Refunded Payments`. Format: revenue /
ADR / RevPAR as whole-number currency (PKR), occupancy / cancellation
/ channel share as percentages (1 decimal).

## 4. Build the page (5 min)

One page, 6 visuals, top to bottom:

| # | Visual | Fields | What it proves |
|---|---|---|---|
| 1 | 4 KPI cards (row) | `Total Revenue`, `Occupancy Rate`, `ADR`, `RevPAR` | The hotel's health at a glance |
| 2 | Clustered column | Axis: `fact_bookings[checkin_date]` (month) · Values: `Total Revenue` | Revenue trend Jan–Jun |
| 3 | Clustered column | Axis: `fact_bookings[channel]` · Values: `Total Bookings` + `Revenue Share by Channel` | Which channel brings bookings vs money |
| 4 | Clustered column | Axis: `dim_room[room_type]` · Values: `Cancellation Rate` | Which room type cancels most |
| 5 | Clustered column | Axis: `fact_bookings[checkin_date]` (month) · Values: `Occupancy Rate` | Occupancy by month — the empty-room problem |
| 6 | Table | `booking_id`, `room_type`, `channel`, `checkin_date`, `nights`, `total_pkr` + `status` | The bookings behind the numbers |

Slicer (optional): `fact_bookings[channel]` — "OTA only" answers
whether the biggest channel is also the most profitable one.

## 5. Check it (1 min)

- `Total Revenue` = PKR 18,125,500, `Occupancy Rate` = 20.4%,
  `ADR` = PKR 12,288, `RevPAR` = PKR 2,504 — all four must match
  `outputs/kpi_summary.txt`. If any card disagrees, the model
  relationships are wrong — not the measure.
- `Total Bookings` = 598 and `Cancellation Rate` = 14.2% must match
  the same file.
- The monthly revenue column must match
  `outputs/preview_revenue_by_month.png`.

## What the preview PNGs are

`outputs/preview_*.png` are matplotlib renders of the same numbers —
proof the model is right before Power BI opens, not the dashboard
itself. The real one-pager is the `.pbix` you build in the 15 minutes
above.

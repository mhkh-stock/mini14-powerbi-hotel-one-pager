# Mini #14 — Power BI One-Pager: Hotel Booking & Revenue Dashboard

**SAMPLE / DEMO data only.** Fictional Islamabad hotel "Margalla View
Hotel", fictional bookings, fictional payments. Never claimed as real
client or real business data.

The second Power BI one-pager in the portfolio, after Mini #9's gym:
a star-schema model, 11 DAX measures, and a 15-minute build guide
that ends in a one-page dashboard — with preview renders proving the
model first. No `.pbix` is bundled: Power BI Desktop authors it from
this model (a `.pbix` is a binary only Power BI can write — shipping
one would be faking it).

## Demo dataset

Fictional hotel, Jan–Jun 2026: 40 rooms (18 Standard, 12 Deluxe,
6 Executive Suite, 4 Family Suite) · 598 bookings (488 stayed,
85 cancelled, 25 no-show) · 1,475 room-nights sold · paid revenue
PKR 18,125,500 · occupancy 20.4% · ADR PKR 12,288 · RevPAR PKR 2,504.
Schema: `model/schema.sql` · CSVs: `data/*.csv` (generated
deterministically, seed 14) · Dictionary: `data/README.md` · Built
database: `data/hotel.db` (rebuild any time with
`python3 src/build_model.py`).

## How to run (3 steps)

1. `cd mini14-powerbi-hotel-one-pager`
2. `python3 src/generate_data.py` — regenerates `data/*.csv`
   (deterministic, seed 14)
3. `python3 src/build_model.py` — builds `data/hotel.db` + writes
   `outputs/kpi_summary.txt`
4. `python3 src/render_previews.py` — renders the 4 preview PNGs
5. `python3 src/checks.py` — 56 checks, all passing

Requires Python 3.10+ and SQLite (standard library) + matplotlib
for the previews. Verified on Python 3.12.3, SQLite 3.45.1.

## The model

Star schema: `dim_room` (dimension) → `fact_bookings` + `fact_payments`
(facts), joined on room and booking. `dim_date` covers every day
Jan–Jun 2026 (181 rows). Relationships for Power BI are listed in
`powerbi/build-guide.md`.

## DAX measures (`dax/measures.dax`)

| Measure | What it answers | Verified value |
|---|---|---|
| `Total Revenue` | What did the hotel actually collect? | PKR 18,125,500 (paid only) |
| `Room Nights Sold` | How many nights were actually occupied? | 1,475 |
| `Occupancy Rate` | What share of the 7,240 available room-nights sold? | 20.4% |
| `ADR` | Average daily rate per sold night | PKR 12,288 |
| `RevPAR` | Revenue per available room-night | PKR 2,504 |
| `Total Bookings` | How many bookings came in? | 598 |
| `Cancellation Rate` | What share cancelled? | 14.2% (85 of 598) |
| `Avg Length of Stay` | How long does a guest stay? | 3.02 nights |
| `Avg Guests per Booking` | How many guests per stayed booking? | 1.78 |
| `Revenue Share by Channel` | Which channel brings the money? | OTA 37.3% (top) |
| `Refunded Payments` | How many bookings were refunded? | 85 (PKR 2,312,400) |

## Key findings (from the verified run)

- **Occupancy is the problem, not price:** overall occupancy is
  20.4% and even the best month (April) only reaches 24.6% — the
  hotel sells 1,475 of 7,240 room-nights. *So what:* every empty
  room-night is lost forever; +10 points of occupancy at the current
  ADR is worth ~PKR 8.9M — filling rooms beats raising rates.
- **Deluxe earns more than Standard with 78 fewer bookings:**
  Deluxe brings 143 stayed bookings and PKR 5,643,000; Standard
  brings 221 bookings and PKR 5,517,900. *So what:* one Deluxe
  booking is worth ~1.5 Standard bookings — the upsell conversation
  at check-in pays more than the acquisition conversation.
- **Standard cancels most, and Direct cancels most:** Standard rooms
  cancel at 17.2% (Family Suite lowest at 10.3%) and the Direct
  channel at 16.3% (Travel Agent lowest at 9.9%); 85 cancellations
  refunded PKR 2,312,400. *So what:* confirmation calls and firmer
  terms belong on Standard + Direct bookings first — that is where
  the refunds leak.
- **Revenue grows, then slips in June:** paid revenue climbs every
  month from PKR 2,293,700 (Jan) to PKR 3,690,700 (May), then falls
  to PKR 2,909,400 in June as stayed bookings drop 96 → 83.
  *So what:* June's dip is the early warning — find what changed
  before it becomes the trend, because May was the peak.

## Preview renders (`outputs/`)

| File | Shows |
|---|---|
| `preview_revenue_by_month.png` | Paid revenue Jan–Jun: 2.29M → 3.69M → 2.91M |
| `preview_occupancy_by_month.png` | Occupancy 15.2% (Jan) → 24.6% (Apr) → 20.9% (Jun) |
| `preview_bookings_by_channel.png` | Stayed bookings: OTA 191, Direct 135, Travel Agent 89, Walk-in 73 |
| `preview_cancellations_by_room_type.png` | Cancellation: Standard 17.2%, Executive 14.4%, Deluxe 10.6%, Family 10.3% |
| `kpi_summary.txt` | Headline KPIs, recomputed from the DB |

## Limits — what this mini does not do

- **One hotel, six months, demo data.** Jan–Jun 2026 only, PKR only,
  40 rooms. A real hotel replaces the three CSVs (same columns) and
  re-runs the pipeline.
- **No `.pbix` in the repo.** The 15-minute guide builds it in Power
  BI Desktop; the preview PNGs are matplotlib renders of the same
  numbers, not the dashboard itself.
- **Cancellation is a rate, not a cohort study.** 85 cancellations
  over 6 months is a rate, not a retention curve — Flagship 1 does
  cohorts properly on real data.

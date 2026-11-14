-- Mini #14 — Power BI One-Pager (Hotel): star schema
-- SQLite. Rebuild any time: python3 src/build_model.py
-- The .db file is NOT uploaded to GitHub (rebuildable from the CSVs).

DROP TABLE IF EXISTS fact_payments;
DROP TABLE IF EXISTS fact_bookings;
DROP TABLE IF EXISTS dim_room;
DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_room (
    room_id TEXT PRIMARY KEY,
    room_type TEXT NOT NULL CHECK (room_type IN ('Standard', 'Deluxe',
        'Executive Suite', 'Family Suite')),
    nightly_rate_pkr INTEGER NOT NULL CHECK (nightly_rate_pkr > 0),
    floor INTEGER NOT NULL CHECK (floor BETWEEN 1 AND 3),
    capacity INTEGER NOT NULL CHECK (capacity BETWEEN 1 AND 4)
);

CREATE TABLE dim_date (
    date TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    month_label TEXT NOT NULL,
    weekday TEXT NOT NULL,
    is_weekend INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

CREATE TABLE fact_bookings (
    booking_id TEXT PRIMARY KEY,
    room_id TEXT NOT NULL REFERENCES dim_room (room_id),
    booking_date TEXT NOT NULL,
    checkin_date TEXT NOT NULL REFERENCES dim_date (date),
    checkout_date TEXT NOT NULL,
    nights INTEGER NOT NULL CHECK (nights BETWEEN 1 AND 5),
    room_type TEXT NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('OTA', 'Direct', 'Walk-in',
        'Travel Agent')),
    guests INTEGER NOT NULL CHECK (guests BETWEEN 1 AND 4),
    nightly_rate_pkr INTEGER NOT NULL CHECK (nightly_rate_pkr > 0),
    total_pkr INTEGER NOT NULL CHECK (total_pkr > 0),
    status TEXT NOT NULL CHECK (status IN ('stayed', 'cancelled', 'no-show')),
    cancel_date TEXT
);

CREATE TABLE fact_payments (
    payment_id TEXT PRIMARY KEY,
    booking_id TEXT NOT NULL REFERENCES fact_bookings (booking_id),
    amount_pkr INTEGER NOT NULL CHECK (amount_pkr > 0),
    status TEXT NOT NULL CHECK (status IN ('paid', 'refunded', 'failed')),
    paid_on TEXT
);

CREATE INDEX idx_bookings_room ON fact_bookings (room_id);
CREATE INDEX idx_bookings_checkin ON fact_bookings (checkin_date);
CREATE INDEX idx_bookings_channel ON fact_bookings (channel);
CREATE INDEX idx_payments_booking ON fact_payments (booking_id);
CREATE INDEX idx_payments_status ON fact_payments (status);

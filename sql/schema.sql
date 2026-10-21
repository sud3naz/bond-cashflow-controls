PRAGMA foreign_keys = ON;

-- Source ledger. These records describe official disclosures, not holdings.
CREATE TABLE sources (
    source_id TEXT PRIMARY KEY NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    publication_date TEXT NOT NULL,
    accessed_date TEXT NOT NULL,
    page INTEGER NOT NULL CHECK (page > 0)
);

-- One row per instrument. A 0.026 rate means 2.60% per stated period.
CREATE TABLE instruments (
    isin TEXT PRIMARY KEY NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'USD'),
    instrument_type TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    maturity_date TEXT NOT NULL CHECK (maturity_date > issue_date),
    period_coupon_rate REAL NOT NULL CHECK (period_coupon_rate >= 0),
    coupon_period_months INTEGER NOT NULL CHECK (coupon_period_months > 0),
    expected_coupon_count INTEGER NOT NULL CHECK (expected_coupon_count > 0),
    source_id TEXT NOT NULL REFERENCES sources(source_id)
);

-- One row per scheduled coupon. Dates are transcribed from the disclosure.
CREATE TABLE coupon_schedule (
    isin TEXT NOT NULL REFERENCES instruments(isin),
    coupon_no INTEGER NOT NULL CHECK (coupon_no > 0),
    payment_date TEXT NOT NULL,
    PRIMARY KEY (isin, coupon_no),
    UNIQUE (isin, payment_date)
);

-- Hypothetical positions are stored separately from official facts.
CREATE TABLE positions (
    isin TEXT PRIMARY KEY NOT NULL REFERENCES instruments(isin),
    nominal_usd REAL NOT NULL CHECK (nominal_usd >= 0)
);

-- A view is a reusable query, not a separate copy of the source data.
CREATE VIEW scheduled_cashflows AS
WITH components AS (
    SELECT
        s.isin,
        s.coupon_no,
        s.payment_date,
        ROUND(p.nominal_usd * i.period_coupon_rate, 2) AS coupon_usd,
        CASE
            WHEN s.payment_date = i.maturity_date THEN p.nominal_usd
            ELSE 0
        END AS principal_usd
    FROM coupon_schedule AS s
    JOIN instruments AS i ON s.isin = i.isin
    JOIN positions AS p ON s.isin = p.isin
)
SELECT
    isin, coupon_no, payment_date, coupon_usd, principal_usd,
    ROUND(coupon_usd + principal_usd, 2) AS total_usd
FROM components;

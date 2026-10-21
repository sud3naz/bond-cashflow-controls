-- These are overlapping horizons. Never add 30/90/365-day totals together.
WITH windows(days) AS (VALUES (30), (90), (365))
SELECT
    w.days,
    date(:as_of_date, '+' || w.days || ' days') AS end_date,
    ROUND(COALESCE(SUM(c.coupon_usd), 0), 2) AS coupon_usd,
    ROUND(COALESCE(SUM(c.principal_usd), 0), 2) AS principal_usd,
    ROUND(COALESCE(SUM(c.total_usd), 0), 2) AS total_usd
FROM windows AS w
LEFT JOIN scheduled_cashflows AS c
    ON c.payment_date > :as_of_date
    AND c.payment_date <= date(:as_of_date, '+' || w.days || ' days')
GROUP BY w.days ORDER BY w.days;

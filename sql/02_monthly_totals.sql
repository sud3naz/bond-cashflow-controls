-- Group scheduled payments by calendar month. No FX conversion is applied.
SELECT
    strftime('%Y-%m', payment_date) AS payment_month,
    ROUND(SUM(coupon_usd), 2) AS coupon_usd,
    ROUND(SUM(principal_usd), 2) AS principal_usd,
    ROUND(SUM(total_usd), 2) AS total_usd
FROM scheduled_cashflows
GROUP BY strftime('%Y-%m', payment_date)
ORDER BY payment_month;

-- Complete source-plan calendar, including months without a scheduled payment.
WITH RECURSIVE months(month_start, last_month) AS (
    SELECT date(MIN(payment_date), 'start of month'), date(MAX(payment_date), 'start of month')
    FROM scheduled_cashflows
    UNION ALL
    SELECT date(month_start, '+1 month'), last_month
    FROM months WHERE month_start < last_month
)
SELECT
    strftime('%Y-%m', m.month_start) AS payment_month,
    ROUND(COALESCE(SUM(c.coupon_usd), 0), 2) AS scheduled_coupon_usd,
    ROUND(COALESCE(SUM(c.principal_usd), 0), 2) AS scheduled_principal_usd,
    ROUND(COALESCE(SUM(c.total_usd), 0), 2) AS scheduled_total_usd,
    ROUND(SUM(CASE WHEN c.payment_date > :as_of_date THEN c.coupon_usd ELSE 0 END), 2) AS remaining_coupon_usd,
    ROUND(SUM(CASE WHEN c.payment_date > :as_of_date THEN c.principal_usd ELSE 0 END), 2) AS remaining_principal_usd,
    ROUND(SUM(CASE WHEN c.payment_date > :as_of_date THEN c.total_usd ELSE 0 END), 2) AS remaining_total_usd
FROM months AS m
LEFT JOIN scheduled_cashflows AS c
    ON c.payment_date >= m.month_start AND c.payment_date < date(m.month_start, '+1 month')
WHERE m.month_start IS NOT NULL
GROUP BY m.month_start
ORDER BY m.month_start;

-- Past scheduled payments are not asserted to have been received.
SELECT
    COUNT(*) AS scheduled_payment_count,
    ROUND(COALESCE(SUM(coupon_usd), 0), 2) AS scheduled_coupon_usd,
    ROUND(COALESCE(SUM(principal_usd), 0), 2) AS scheduled_principal_usd,
    ROUND(COALESCE(SUM(total_usd), 0), 2) AS scheduled_total_usd,
    ROUND(COALESCE(SUM(CASE WHEN payment_date > :as_of_date THEN coupon_usd ELSE 0 END), 0), 2) AS remaining_coupon_usd,
    ROUND(COALESCE(SUM(CASE WHEN payment_date > :as_of_date THEN principal_usd ELSE 0 END), 0), 2) AS remaining_principal_usd,
    ROUND(COALESCE(SUM(CASE WHEN payment_date > :as_of_date THEN total_usd ELSE 0 END), 0), 2) AS remaining_total_usd,
    ROUND(COALESCE(SUM(CASE WHEN payment_date <= :as_of_date THEN total_usd ELSE 0 END), 0), 2) AS past_scheduled_total_usd
FROM scheduled_cashflows;

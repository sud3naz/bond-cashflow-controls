-- Exclude the report date; include day +90. The date is a fixed demo input.
SELECT isin, payment_date, coupon_usd, principal_usd, total_usd
FROM scheduled_cashflows
WHERE payment_date > :as_of_date
  AND payment_date <= date(:as_of_date, '+90 days')
ORDER BY payment_date, isin;

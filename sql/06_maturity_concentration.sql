-- Nominal principal, not market value, credit risk or investment suitability.
WITH remaining AS (
    SELECT strftime('%Y', i.maturity_date) AS maturity_year, p.nominal_usd
    FROM instruments AS i
    JOIN positions AS p ON i.isin = p.isin
    WHERE i.maturity_date > :as_of_date
), grouped AS (
    SELECT maturity_year, ROUND(SUM(nominal_usd), 2) AS nominal_usd
    FROM remaining GROUP BY maturity_year
)
SELECT maturity_year, nominal_usd,
    CASE WHEN (SELECT SUM(nominal_usd) FROM grouped) > 0
         THEN nominal_usd / (SELECT SUM(nominal_usd) FROM grouped)
         ELSE NULL END AS nominal_share
FROM grouped ORDER BY maturity_year;

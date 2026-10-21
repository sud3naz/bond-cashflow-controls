# Bond Cash Flow Results and Verification

Version 1 uses the official terms of five real bonds and 12 scheduled coupon dates. Holdings totalling USD 70,000 nominal are hypothetical. The reporting date is 22 October 2026. The payment calendar contains all 20 months from October 2026 through May 2028.

## Analysis results

| Indicator | USD |
| --- | ---: |
| Coupons over the complete schedule | 4,178.00 |
| Principal over the complete schedule | 70,000.00 |
| Gross cash flows over the complete schedule | 74,178.00 |
| Coupons scheduled after the reporting date | 3,843.50 |
| Principal scheduled after the reporting date | 70,000.00 |
| Remaining gross cash flows | 73,843.50 |
| Gross cash flows in the next 30 days | 260.00 |
| Gross cash flows in the next 90 days | 780.00 |
| Gross cash flows in the next 365 days | 63,323.50 |

The USD 334.50 difference between the complete and remaining schedules is the April-issued bond's coupon scheduled for 14 October 2026. A past scheduled payment is not proof of receipt. The 30-, 90- and 365-day horizons start from the same reporting date and overlap; their totals must not be added together.

USD 60,000 nominal matures in 2027 and USD 10,000 in 2028. Their approximate shares of 85.7% and 14.3% describe the hypothetical portfolio's nominal maturity distribution, not market values or investment recommendations.

Payments from two bonds fall in April 2027. Remaining coupons total USD 777, principal totals USD 15,000 and the monthly total is USD 15,777. Months without payments, such as January 2027, show zero; missing data is not treated as zero payment.

## Checks completed

All 27 Python tests passed. Command: `python3 -m unittest discover -s tests -v`.

| Check | Evidence |
| --- | --- |
| Coupon and principal calculations | Independent Decimal calculation and total reconciliation in `test_portfolio.py` |
| Original two-bond example | 11 regression tests in `test_analysis.py` |
| 30-, 90- and 365-day boundaries | `test_window_boundaries_all_horizons` and the 90-day regression test |
| Zero months and past payment in the reporting month | `test_calendar_zero_months_and_totals` |
| Zero nominal and undefined shares | `test_zero_nominal_yields_undefined_shares` |
| Invalid inputs and source relationships | Nine test methods in `test_quality.py` and separate intentionally invalid examples |
| Repeatability for identical inputs | `test_demo_copies_and_repeatability` |
| Excel and JSON reconciliation | Comparison of summary, horizon and monthly totals before saving |
| Workbook formulas responding to input changes | USD 20,000 nominal, missing/negative/text nominal and reporting-date scenarios |
| Workbook layout and export | Visual inspection of all five sheets, formula-error scan, XLSX reimport and chart checks |

Workbook verification used a spreadsheet calculation engine. Manual testing in the Microsoft Excel application remains pending. The Python analysis is reproducible; the delivered Excel report is a separate workbook that the Python command does not regenerate.

## Requirements traceability

BR-01 and BR-02 link to source separation and data controls; BR-03 to independent coupon and principal checks; BR-04 to horizon boundaries; BR-05 to monthly reconciliation; BR-06 to zero-nominal and share tests; BR-07 to Excel/JSON reconciliation; and BR-08 to repeatability checks. These are automated or technical checks.

All ten manual acceptance scenarios remain Pending. No UAT with actual business users, measured operational loss reduction or user approval is claimed.

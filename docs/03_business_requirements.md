# Business Requirements for Bond Payment Monitoring

The business need is to track when gross coupon and principal payments are scheduled for USD-denominated, fixed-coupon Turkish domestic government bonds, with each calculation traceable to its source. Controls must prevent missing or invalid inputs from silently entering the payment schedule. The operations scenario and user roles are hypothetical; they do not represent an actual institution's request or a measured operational problem.

## Users and scope

The assumed operations analyst enters nominal holdings and monitors upcoming payments. A reviewing analyst compares terms with official disclosures and requests corrections to invalid records. A report reader reviews the monthly payment calendar and the timing of principal repayments. These roles are scenario assumptions, not findings from user research.

Version 1 covers USD-denominated, fixed-coupon domestic government bonds disclosed by Türkiye's Ministry of Treasury and Finance in 2026. Payment dates are taken from the disclosures. Sukuk are excluded. Holdings are hypothetical nominal balances assumed constant from each issue date to maturity. The fixed reporting date is 22 October 2026. Past dates remain labelled as scheduled payments; they are not evidence of receipt.

Prices, purchase costs, accrued interest, tax, fees, FX conversion, floating rates, yield calculations and investment recommendations are outside scope. Nominal holdings are not market values, and cash flows that include returned principal are not investment profit.

## Proposed control workflow

Official terms and source record → nominal assumptions in a separate file → input validation → payment calculations → horizon and maturity summaries → Excel report → review by a second analyst.

An error must identify the affected field and record. Normal payment reporting must stop until the input is corrected. Intentionally invalid examples run on separate test copies without changing the source facts.

## Business requirements

Each business requirement defines observable behaviour needed to address the user need. Requirement IDs link these behaviours to acceptance scenarios, providing requirements traceability.

1. **BR-01 Separate sources from assumptions.** Identify each instrument by ISIN and link its currency, periodic rate, issue date, maturity and payment dates to a source record. Record the document URL, page, publication date and access date. Store nominal holdings and the reporting date in a separate assumptions file. Changing a holding must not change official instrument terms.

2. **BR-02 Validate inputs.** Reject missing, negative, text, boolean or non-finite nominal amounts and rates; duplicate identifiers or payments; incomplete coupon sequences; payments outside the issue and maturity boundaries; missing final maturity payments; unknown source or instrument references; and unsupported instruments or currencies. Zero nominal is valid. Each message must identify the table or dataset, record or ISIN, affected field and reason. Errors must stop normal payment reporting.

3. **BR-03 Calculate coupons and principal.** Calculate each coupon as `nominal × periodic coupon rate` and round the USD amount to two decimal places. Do not divide the periodic rate by two again. Add principal only once, on the maturity date. Show the complete schedule separately from payments remaining after the reporting date; exclude a payment on the reporting date from remaining amounts.

4. **BR-04 Identify upcoming payments.** Calculate 30-, 90- and 365-day horizons using calendar days: `reporting date < payment date ≤ reporting date + days`. Show coupon, principal and total separately for each horizon. Horizons overlap, so their totals must not be added together.

5. **BR-05 Provide a complete monthly calendar.** Include every month from the first scheduled payment month through the final maturity month. Show zero coupon, principal and total for months without payments. Keep complete-schedule and remaining-payment columns separate; exclude payments on or before the reporting date from the remaining columns, including within the reporting month. State the first and last month. Monthly totals must reconcile to the corresponding complete or remaining payment schedule.

6. **BR-06 Show nominal maturity concentration.** Group nominal holdings maturing after the reporting date by maturity year. Calculate each year's share as its nominal amount divided by total remaining nominal. Labels and units must identify nominal USD concentration rather than market value. If remaining nominal is zero, show the share as undefined without dividing by zero.

7. **BR-07 Reconcile the JSON and Excel reports.** Use the calculated JSON report as the reference for the default report; the delivered workbook must match the same inputs and results. Its `Overview`, `Assumptions`, `Payment_Schedule`, `Source_Data` and `Checks` sheets must make the reporting date, sources, assumptions, payment details, monthly calendar, and horizon and maturity summaries traceable. State currency and calculation scope in headings. Workbook input edits update its own formulas; the Python command does not regenerate the workbook. For a new date or nominal scenario, enter identical assumptions separately in both environments and compare the results.

8. **BR-08 Make checks reproducible.** The same valid inputs and fixed reporting date must produce the same numerical results. Keep intentionally invalid test inputs separate from actual source files. Link acceptance scenarios to their requirements and record automated test results separately from user acceptance.

## KPI definitions

These key performance indicators summarise the hypothetical payment plan and its controls. They do not measure realised investment performance.

| ID | Indicator | Definition and unit |
| --- | --- | --- |
| KPI-01 | Remaining gross coupons | Sum of coupons scheduled after the reporting date, USD. |
| KPI-02 | Remaining principal | Sum of principal repayments scheduled after the reporting date, USD. |
| KPI-03 | Remaining gross cash flows | Remaining coupons + remaining principal, USD. The 30/90/365-day breakdowns use the boundaries in BR-04. |
| KPI-04 | Largest annual nominal share | Largest maturity-year nominal amount / total remaining nominal × 100, %. Undefined when total remaining nominal is zero. |
| KPI-05 | Data-quality issues | Count of record- and field-level validation messages. Different field errors on the same record may count separately. This is not a count of invalid records or a real operational error rate. |

## Acceptance criteria

The [acceptance scenarios](04_acceptance_tests.md) define expected calculations, date boundaries, validation messages and report reconciliation. User Acceptance Testing (UAT) requires a manual assessment of whether the workflow meets the business need. Passing automated tests alone does not constitute user approval.

# Bond Payment Report Acceptance Scenarios

These scenarios define observable acceptance criteria for the [business requirements](03_business_requirements.md). All manual execution statuses are Pending. Expected results are not observed test results or user approval. Automated checks are recorded separately; no UAT with actual institutional users is claimed.

## Test inputs

The default report uses official instrument terms, separate nominal assumptions and a reporting date of 22 October 2026. Error and date-boundary checks use separate test copies. Intentionally invalid records and boundary dates are not presented as facts from official disclosures.

An independent calculation example uses the disclosed 2.60% periodic coupon rate for TRT100528F15 and a hypothetical USD 10,000 nominal holding. Each coupon should be USD 260, and the total on its 10 May 2028 maturity date should be USD 10,260. This is a scheduled amount, not confirmation of receipt.

## Requirement linked acceptance matrix

| Scenario | Requirements | Procedure | Expected result | Manual status |
| --- | --- | --- | --- | --- |
| AT-01 Trace to source | BR-01, BR-07 | Select an ISIN in the workbook and compare its terms with the source record. | The document URL and page are available; the periodic rate and payment dates match the source. The nominal holding is identified as an assumption. | Pending |
| AT-02 Coupon and maturity | BR-03 | Review the TRT100528F15 payment rows using USD 10,000 nominal and a 0.026 periodic rate. | Each coupon is USD 260. Principal is USD 10,000 only on 10 May 2028, when total payment is USD 10,260. | Pending |
| AT-03 Change nominal | BR-01, BR-03, BR-07 | In a separate scenario, set this nominal to USD 20,000 in the JSON assumptions and run the Python analysis. Separately enter the same nominal in the yellow input on the workbook's Assumptions sheet. | Each coupon becomes USD 520 and the maturity total becomes USD 20,520. Official terms stay unchanged; JSON and Excel show the same new amounts for identical inputs. | Pending |
| AT-04 Zero and invalid nominal | BR-02, BR-03 | In separate inputs, try zero, missing, negative, text, boolean and non-finite nominal values. | Zero nominal produces zero cash amounts. The other values produce errors identifying the record and field; no normal payment report is produced. | Pending |
| AT-05 Invalid terms and references | BR-01, BR-02 | In separate copies, try a missing rate, invalid source reference, unknown ISIN or unsupported currency. | Messages identify the affected record or ISIN, field and reason. Invalid inputs do not produce a normal payment report. | Pending |
| AT-06 Broken payment sequence | BR-02, BR-03 | In separate copies, try a duplicate payment, missing coupon, date before issue or after maturity, and missing final maturity payment. | Each copy is rejected with an appropriate record and field message. Principal is neither omitted nor counted twice in an accepted schedule. | Pending |
| AT-07 Horizon boundaries | BR-03, BR-04 | In separate boundary-test inputs, place payments on the reporting date and at +30/+31, +90/+91 and +365/+366 days. | The reporting date is excluded from remaining payments and all horizons. Each horizon includes its final day and excludes the following day. The complete schedule retains all rows. | Pending |
| AT-08 Zero months and reconciliation | BR-04, BR-05 | Review the full monthly calendar, a month without payments, the reporting month, payment months and totals. | Months run continuously from the first scheduled payment month through the final maturity month; months without payments show zero. Complete and remaining columns reconcile to their respective schedules. A past payment in the reporting month appears only in the complete schedule. | Pending |
| AT-09 Nominal concentration | BR-06 | Independently calculate nominal shares by maturity year, then try zero nominal for all positions. | For a positive total, annual shares sum to 100% within rounding tolerance and the largest annual share is correct. For a zero total, shares are undefined. Labels do not describe market value. | Pending |
| AT-10 Reconciliation and repeatability | BR-07, BR-08 | Run twice with identical inputs. Compare the reporting date, rows, summaries, sources and assumptions in JSON and Excel. | Numerical results remain the same and Excel reconciles to JSON. Invalid test inputs remain separate from source facts; automated checks are not recorded as manual acceptance. | Pending |

## Manual execution record

For each execution, record the date, tester, input version, observed result and evidence file. Mark the result Passed, Failed or Blocked. Track any deviation against the relevant requirement with a description of the issue. Manual acceptance remains incomplete until these fields are recorded.

User Acceptance Testing (UAT) assesses whether a solution meets a user's business need. This matrix is an acceptance plan for a portfolio project; it does not record approval by an independent business user.

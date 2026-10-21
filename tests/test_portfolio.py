from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from analyze import analyze, build_database, read_inputs, run_query, write_reports


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.facts, self.assumptions = read_inputs()

    def test_independent_cashflows_and_full_vs_remaining(self):
        report = analyze(self.facts, self.assumptions)
        self.assertEqual(report['summary']['instrument_count'], 5)
        self.assertEqual(report['summary']['scheduled_payment_count'], 12)
        self.assertEqual(report['summary']['scheduled_coupon_usd'], 4178)
        self.assertEqual(report['summary']['scheduled_principal_usd'], 70000)
        self.assertEqual(report['summary']['scheduled_total_usd'], 74178)
        self.assertEqual(report['summary']['remaining_coupon_usd'], 3843.5)
        self.assertEqual(report['summary']['remaining_total_usd'], 73843.5)
        self.assertEqual(report['summary']['past_scheduled_total_usd'], 334.5)
        instruments = {row['isin']: row for row in self.facts['instruments']}
        positions = {row['isin']: row for row in self.assumptions['positions']}
        for row in report['payment_schedule']:
            item, position = instruments[row['isin']], positions[row['isin']]
            coupon = (Decimal(str(position['nominal_usd'])) * Decimal(str(item['period_coupon_rate']))).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            self.assertEqual(Decimal(str(row['coupon_usd'])), coupon)
            expected_principal = position['nominal_usd'] if row['payment_date'] == item['maturity_date'] else 0
            self.assertEqual(row['principal_usd'], expected_principal)

    def test_calendar_zero_months_and_totals(self):
        report = analyze(self.facts, self.assumptions)
        months = report['monthly_calendar']
        self.assertEqual(len(months), 20)
        self.assertEqual(months[0]['payment_month'], '2026-10')
        self.assertEqual(months[-1]['payment_month'], '2028-05')
        self.assertEqual(months[0]['scheduled_total_usd'], 334.5)
        self.assertEqual(months[0]['remaining_total_usd'], 0)
        january = next(row for row in months if row['payment_month'] == '2027-01')
        self.assertEqual(january['scheduled_total_usd'], 0)
        self.assertEqual(sum(row['remaining_total_usd'] for row in months), 73843.5)
        self.assertEqual(sum(row['scheduled_total_usd'] for row in months), 74178)
        april = next(row for row in months if row['payment_month'] == '2027-04')
        self.assertEqual(april['remaining_total_usd'], 15777)

    def test_windows_and_maturity_shares(self):
        report = analyze(self.facts, self.assumptions)
        self.assertEqual([row['total_usd'] for row in report['windows']], [260, 780, 63323.5])
        concentration = report['maturity_concentration']
        self.assertEqual([row['nominal_usd'] for row in concentration], [60000, 10000])
        self.assertAlmostEqual(sum(row['nominal_share'] for row in concentration), 1)

    def test_zero_nominal_yields_undefined_shares(self):
        for position in self.assumptions['positions']:
            position['nominal_usd'] = 0
        report = analyze(self.facts, self.assumptions)
        self.assertTrue(all(row['nominal_share'] is None for row in report['maturity_concentration']))
        self.assertEqual(report['summary']['remaining_total_usd'], 0)

    def test_zero_rate_is_not_missing(self):
        self.facts['instruments'][0]['period_coupon_rate'] = 0
        report = analyze(self.facts, self.assumptions)
        self.assertTrue(all(row['coupon_usd'] == 0 for row in report['payment_schedule'] if row['isin'] == 'TRT100528F15'))

    def test_window_boundaries_all_horizons(self):
        connection = build_database(self.facts, self.assumptions)
        self.addCleanup(connection.close)
        for days in [30, 90, 365]:
            # Move only the report date, not any officially sourced payment date.
            exact = connection.execute("SELECT date('2026-11-11', '-' || ? || ' days')", (days,)).fetchone()[0]
            before = connection.execute("SELECT date(?, '-1 day')", (exact,)).fetchone()[0]
            inside = run_query(connection, '07_payment_windows.sql', {'as_of_date': exact})
            outside = run_query(connection, '07_payment_windows.sql', {'as_of_date': before})
            target = next(row for row in inside if row['days'] == days)
            other = next(row for row in outside if row['days'] == days)
            self.assertGreaterEqual(target['coupon_usd'] - other['coupon_usd'], 260)
        on_payment = run_query(connection, '03_next_90_days.sql', {'as_of_date': '2026-11-11'})
        self.assertNotIn('2026-11-11', [row['payment_date'] for row in on_payment])

    def test_demo_copies_and_repeatability(self):
        original_facts, original_assumptions = deepcopy(self.facts), deepcopy(self.assumptions)
        first = analyze(self.facts, self.assumptions)
        self.assertTrue(all(row['detected'] for row in first['quality']['demo_results']))
        self.assertEqual(len(first['quality']['demo_results']), 9)
        self.assertEqual(self.facts, original_facts)
        self.assertEqual(self.assumptions, original_assumptions)
        self.assertEqual(first, analyze(self.facts, self.assumptions))
        with tempfile.TemporaryDirectory() as folder:
            write_reports(first, Path(folder))
            self.assertTrue((Path(folder) / 'analysis.json').is_file())


if __name__ == '__main__':
    unittest.main()

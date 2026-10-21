from copy import deepcopy
from pathlib import Path
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from analyze import build_database, read_inputs, run_query


class BondAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.facts, self.assumptions = read_inputs()
        # Preserve the two-bond teaching example as a regression fixture.
        ids = {'TRT100528F15', 'TRT090627F18'}
        self.facts['instruments'] = [row for row in self.facts['instruments'] if row['isin'] in ids]
        self.facts['coupon_schedule'] = [row for row in self.facts['coupon_schedule'] if row['isin'] in ids]
        self.assumptions['positions'] = [row for row in self.assumptions['positions'] if row['isin'] in ids]

    def database(self, facts=None, assumptions=None):
        connection = build_database(facts or self.facts, assumptions or self.assumptions)
        self.addCleanup(connection.close)
        return connection

    def test_full_schedule_and_independent_totals(self):
        rows = run_query(self.database(), '01_payment_schedule.sql')
        self.assertEqual(len(rows), 6)
        self.assertEqual(sum(row['coupon_usd'] for row in rows), 2080)
        self.assertEqual(sum(row['principal_usd'] for row in rows), 30000)
        self.assertEqual(sum(row['total_usd'] for row in rows), 32080)
        final = [row for row in rows if row['principal_usd'] > 0]
        self.assertEqual(
            [(row['payment_date'], row['total_usd']) for row in final],
            [('2027-06-09', 20520), ('2028-05-10', 10260)],
        )

    def test_monthly_sums_reconcile(self):
        connection = self.database()
        months = run_query(connection, '02_monthly_totals.sql')
        self.assertEqual([row['payment_month'] for row in months], [
            '2026-11', '2026-12', '2027-05', '2027-06', '2027-11', '2028-05',
        ])
        self.assertEqual(sum(row['total_usd'] for row in months), 32080)

    def test_next_90_days_and_date_boundaries(self):
        connection = self.database()
        rows = run_query(connection, '03_next_90_days.sql', {'as_of_date': '2026-10-22'})
        self.assertEqual([row['payment_date'] for row in rows], ['2026-11-11', '2026-12-09'])
        self.assertEqual(sum(row['total_usd'] for row in rows), 780)
        rows = run_query(connection, '03_next_90_days.sql', {'as_of_date': '2026-09-10'})
        self.assertIn('2026-12-09', [row['payment_date'] for row in rows])  # Exact day +90.
        rows = run_query(connection, '03_next_90_days.sql', {'as_of_date': '2026-11-11'})
        self.assertNotIn('2026-11-11', [row['payment_date'] for row in rows])

    def test_nominal_change_updates_cashflows_not_source_facts(self):
        original = deepcopy(self.facts)
        self.assumptions['positions'][1]['nominal_usd'] = 30000
        rows = run_query(self.database(), '01_payment_schedule.sql')
        second = [row for row in rows if row['isin'] == 'TRT090627F18']
        self.assertEqual([row['coupon_usd'] for row in second], [780, 780])
        self.assertEqual(second[-1]['total_usd'], 30780)
        self.assertEqual(self.facts, original)

    def test_zero_nominal_is_valid(self):
        self.assumptions['positions'][1]['nominal_usd'] = 0
        rows = run_query(self.database(), '01_payment_schedule.sql')
        self.assertEqual(sum(row['total_usd'] for row in rows), 11040)

    def test_missing_or_invalid_inputs_are_not_zero(self):
        for bad in [None, '', -1, '20000', True, float('nan'), float('inf')]:
            with self.subTest(bad=bad):
                assumptions = deepcopy(self.assumptions)
                assumptions['positions'][1]['nominal_usd'] = bad
                with self.assertRaises(ValueError):
                    build_database(self.facts, assumptions)
        self.facts['instruments'][1]['period_coupon_rate'] = None
        with self.assertRaises(ValueError):
            build_database(self.facts, self.assumptions)

    def test_duplicate_or_incomplete_schedule_is_rejected(self):
        self.facts['coupon_schedule'].append(deepcopy(self.facts['coupon_schedule'][0]))
        with self.assertRaises(ValueError):
            build_database(self.facts, self.assumptions)
        self.setUp()
        self.facts['coupon_schedule'].pop()
        with self.assertRaises(ValueError):
            build_database(self.facts, self.assumptions)

    def test_payment_after_maturity_is_rejected(self):
        self.facts['coupon_schedule'][-1]['payment_date'] = '2027-06-10'
        with self.assertRaises(ValueError):
            build_database(self.facts, self.assumptions)

    def test_missing_maturity_payment_is_rejected(self):
        self.facts['coupon_schedule'][-1]['payment_date'] = '2027-06-08'
        with self.assertRaises(ValueError):
            build_database(self.facts, self.assumptions)

    def test_unknown_instrument_position_is_rejected(self):
        self.assumptions['positions'][1]['isin'] = 'UNKNOWN'
        with self.assertRaises(ValueError):
            build_database(self.facts, self.assumptions)

    def test_mixed_currency_is_rejected(self):
        self.facts['instruments'][1]['currency'] = 'TRY'
        with self.assertRaises(ValueError):
            build_database(self.facts, self.assumptions)


if __name__ == '__main__':
    unittest.main()

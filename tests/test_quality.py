from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from quality import collect_issues


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.facts = json.loads((ROOT / 'data/source_facts.json').read_text())
        self.assumptions = json.loads((ROOT / 'data/portfolio_assumptions.json').read_text())

    def rules(self, facts=None, assumptions=None):
        return {issue['rule_id'] for issue in collect_issues(
            self.facts if facts is None else facts,
            self.assumptions if assumptions is None else assumptions,
        )}

    def test_clean_inputs_and_no_mutation(self):
        before = deepcopy((self.facts, self.assumptions))
        self.assertEqual(collect_issues(self.facts, self.assumptions), [])
        self.assertEqual((self.facts, self.assumptions), before)

    def test_invalid_rates_and_nominals(self):
        for value in [None, '', '0.026', True, False, -1, float('nan'), float('inf')]:
            with self.subTest(value=value):
                facts, assumptions = deepcopy(self.facts), deepcopy(self.assumptions)
                facts['instruments'][0]['period_coupon_rate'] = value
                assumptions['positions'][0]['nominal_usd'] = value
                self.assertIn('R01', self.rules(facts, assumptions))
                self.assertIn('R02', self.rules(facts, assumptions))
        self.facts['instruments'][0]['period_coupon_rate'] = 0
        self.assumptions['positions'][0]['nominal_usd'] = 0
        self.assertEqual(self.rules(), set())

    def test_demo_cases_exercise_every_rule(self):
        cases = json.loads((ROOT / 'data/quality_demo_cases.json').read_text())
        for case in cases:
            with self.subTest(case=case['case_id']):
                facts, assumptions = deepcopy(self.facts), deepcopy(self.assumptions)
                owner = assumptions if case['target'] == 'positions' else facts
                rows = owner[case['target']]
                if case.get('operation') == 'append_duplicate':
                    rows.append(deepcopy(rows[case['index']]))
                else:
                    rows[case['index']][case['field']] = case['value']
                self.assertIn(case['expected_rule'], self.rules(facts, assumptions))

    def test_all_unique_keys(self):
        for collection in ['sources', 'instruments', 'coupon_schedule', 'positions']:
            with self.subTest(collection=collection):
                facts, assumptions = deepcopy(self.facts), deepcopy(self.assumptions)
                owner = assumptions if collection == 'positions' else facts
                owner[collection].append(deepcopy(owner[collection][0]))
                self.assertIn('R03', self.rules(facts, assumptions))
        self.facts['coupon_schedule'][1]['payment_date'] = self.facts['coupon_schedule'][0]['payment_date']
        self.assertIn('R03', self.rules())

    def test_foreign_keys(self):
        for collection, field in [('instruments', 'source_id'), ('coupon_schedule', 'isin')]:
            with self.subTest(collection=collection):
                facts = deepcopy(self.facts)
                facts[collection][0][field] = 'UNKNOWN'
                self.assertIn('R05', self.rules(facts))

    def test_missing_schedule_and_positive_integer_fields(self):
        facts = deepcopy(self.facts)
        facts['coupon_schedule'].pop(0)
        self.assertIn('R06', self.rules(facts))
        for field in ['coupon_period_months', 'expected_coupon_count']:
            for value in [None, '', 0, -1, True, 2.5, '6']:
                with self.subTest(field=field, value=value):
                    facts = deepcopy(self.facts)
                    facts['instruments'][0][field] = value
                    self.assertIn('R06', self.rules(facts))

    def test_dates_must_be_strict_and_inside_instrument_life(self):
        for value in ['20260230', '2026-02-30', '2026-W01-1', None, 20261111]:
            with self.subTest(value=value):
                facts = deepcopy(self.facts)
                facts['coupon_schedule'][0]['payment_date'] = value
                self.assertIn('R04', self.rules(facts))
        for field in ['issue_date', 'maturity_date']:
            facts = deepcopy(self.facts)
            facts['instruments'][0][field] = facts['instruments'][0]['maturity_date']
            if field == 'maturity_date':
                facts['instruments'][0][field] = facts['instruments'][0]['issue_date']
            self.assertIn('R04', self.rules(facts))
        self.facts['coupon_schedule'][0]['payment_date'] = self.facts['instruments'][0]['issue_date']
        self.assertIn('R04', self.rules())

    def test_provenance_and_scope(self):
        for field in ['title', 'url', 'page', 'publication_date', 'accessed_date']:
            facts = deepcopy(self.facts)
            facts['sources'][0].pop(field)
            self.assertIn('R09', self.rules(facts))
        self.facts['instruments'][0]['currency'] = 'TRY'
        self.assertIn('R08', self.rules())
        self.facts['instruments'][0]['currency'] = 'USD'
        self.facts['instruments'][0]['instrument_type'] = 'floating_rate'
        self.assertIn('R08', self.rules())

    def test_malformed_json_shapes_never_crash_and_ids_are_stable(self):
        for value in [None, [], 'text', 1, True]:
            self.assertTrue(collect_issues(value, self.assumptions))
            self.assertTrue(collect_issues(self.facts, value))
        for collection in ['sources', 'instruments', 'coupon_schedule']:
            for value in [None, {}, 'text', [None, [], 1, True], [{'isin': [], 'source_id': {}}]]:
                with self.subTest(collection=collection, value=value):
                    facts = deepcopy(self.facts)
                    facts[collection] = value
                    issues = collect_issues(facts, self.assumptions)
                    self.assertTrue(issues)
                    self.assertEqual(issues, collect_issues(facts, self.assumptions))
                    self.assertTrue(all(set(issue) == {'rule_id', 'severity', 'record_id', 'message'} for issue in issues))
        for value in [None, {}, 'text', [None], [{'isin': [], 'nominal_usd': {}}]]:
            assumptions = deepcopy(self.assumptions)
            assumptions['positions'] = value
            self.assertTrue(collect_issues(self.facts, assumptions))


if __name__ == '__main__':
    unittest.main()

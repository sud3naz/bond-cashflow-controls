"""Analyze five sourced USD bonds with explicit hypothetical holdings."""

import argparse
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import sqlite3

from quality import collect_issues

ROOT = Path(__file__).resolve().parents[1]


def read_inputs():
    facts = json.loads((ROOT / 'data/source_facts.json').read_text(encoding='utf-8'))
    assumptions = json.loads((ROOT / 'data/portfolio_assumptions.json').read_text(encoding='utf-8'))
    return facts, assumptions


def validate_inputs(facts, assumptions):
    """Reject invalid inputs instead of treating missing numbers as zero."""
    issues = collect_issues(facts, assumptions)
    if issues:
        raise ValueError(json.dumps(issues, ensure_ascii=False))


def build_database(facts=None, assumptions=None):
    if facts is None and assumptions is None:
        facts, assumptions = read_inputs()
    validate_inputs(facts, assumptions)
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript((ROOT / 'sql/schema.sql').read_text(encoding='utf-8'))
        connection.executemany(
            'INSERT INTO sources VALUES (:source_id, :title, :url, :publication_date, :accessed_date, :page)',
            facts['sources'],
        )
        connection.executemany(
            'INSERT INTO instruments VALUES (:isin, :currency, :instrument_type, :issue_date, :maturity_date, '
            ':period_coupon_rate, :coupon_period_months, :expected_coupon_count, :source_id)',
            facts['instruments'],
        )
        connection.executemany(
            'INSERT INTO coupon_schedule VALUES (:isin, :coupon_no, :payment_date)', facts['coupon_schedule'],
        )
        connection.executemany(
            'INSERT INTO positions VALUES (:isin, :nominal_usd)', assumptions['positions'],
        )
        connection.commit()
    except Exception:
        connection.close()
        raise
    return connection


def run_query(connection, filename, parameters=None):
    sql = (ROOT / 'sql' / filename).read_text(encoding='utf-8')
    return [dict(row) for row in connection.execute(sql, parameters or {})]


def demo_results(facts, assumptions):
    """Run intentionally bad copies; never modify the official facts."""
    cases = json.loads((ROOT / 'data/quality_demo_cases.json').read_text(encoding='utf-8'))
    results = []
    for case in cases:
        demo_facts, demo_assumptions = deepcopy(facts), deepcopy(assumptions)
        document = demo_assumptions if case['target'] == 'positions' else demo_facts
        rows = document[case['target']]
        if case.get('operation') == 'append_duplicate':
            rows.append(deepcopy(rows[case['index']]))
        else:
            rows[case['index']][case['field']] = case['value']
        issues = collect_issues(demo_facts, demo_assumptions)
        results.append({
            'case_id': case['case_id'], 'description': case['description'],
            'expected_rule': case['expected_rule'],
            'detected': any(issue['rule_id'] == case['expected_rule'] for issue in issues),
            'issues': issues,
        })
    return results


def analyze(facts, assumptions):
    connection = build_database(facts, assumptions)
    try:
        params = {'as_of_date': assumptions['as_of_date']}
        report = {'status': 'valid', 'as_of_date': assumptions['as_of_date'], 'currency': 'USD'}
        queries = {
            'payment_schedule': '01_payment_schedule.sql',
            'payment_months': '02_monthly_totals.sql',
            'next_90_days': '03_next_90_days.sql',
            'monthly_calendar': '04_monthly_calendar.sql',
            'maturity_concentration': '06_maturity_concentration.sql',
            'windows': '07_payment_windows.sql',
        }
        for name, filename in queries.items():
            report[name] = run_query(connection, filename, params)
        report['summary'] = run_query(connection, '05_summary.sql', params)[0]
        report['summary']['instrument_count'] = len(facts['instruments'])
        report['quality'] = {'issue_count': 0, 'issues': [], 'demo_results': demo_results(facts, assumptions)}
        report['sources'] = facts['sources']
        report['assumptions'] = assumptions
        report['input_sha256'] = hashlib.sha256(
            json.dumps([facts, assumptions], sort_keys=True, ensure_ascii=False).encode('utf-8')
        ).hexdigest()
        return report
    finally:
        connection.close()


def write_reports(report, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'analysis.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for name in ['payment_schedule', 'monthly_calendar', 'maturity_concentration', 'windows']:
        rows = report[name]
        if rows:
            with (output_dir / f'{name}.csv').open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'reports')
    args = parser.parse_args()
    facts, assumptions = read_inputs()
    issues = collect_issues(facts, assumptions)
    if issues:
        # Explicit invalid status prevents an old JSON report being mistaken for this run.
        args.output_dir.mkdir(parents=True, exist_ok=True)
        invalid = {'status': 'invalid', 'issues': issues, 'notice': 'Do not use existing CSV or Excel snapshots for this failed run.'}
        (args.output_dir / 'analysis.json').write_text(json.dumps(invalid, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(invalid, ensure_ascii=False, indent=2))
        return 2
    report = analyze(facts, assumptions)
    write_reports(report, args.output_dir)
    print(json.dumps({'as_of_date': report['as_of_date'], 'summary': report['summary'], 'windows': report['windows']}, indent=2))
    print('Report:', args.output_dir / 'analysis.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

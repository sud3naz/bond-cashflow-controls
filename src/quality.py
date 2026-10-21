"""Small, explicit data controls for the USD fixed-coupon learning example.

R01 rate; R02 nominal; R03 duplicate; R04 date; R05 key/structure;
R06 coupon period/count/sequence; R07 final payment; R08 scope; R09 provenance.
The function reports errors without changing either input or calculating cashflows.
"""

from datetime import date
import math
import re
from urllib.parse import urlparse


def collect_issues(facts, assumptions):
    """Return deterministic {rule_id, severity, record_id, message} dictionaries.

    Record IDs are input paths, so even rows without a usable identifier can be
    located. All rules are blocking errors for this deliberately narrow model.
    """
    issues = []

    def add(rule, record, message):
        issues.append(dict(rule_id=rule, severity='error', record_id=record, message=message))

    def text(value):
        return isinstance(value, str) and bool(value.strip())

    def positive_int(value):
        return isinstance(value, int) and not isinstance(value, bool) and value > 0

    def nonnegative_number(value):
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and value >= 0 and (not isinstance(value, float) or math.isfinite(value)))

    def parse_date(value, record, field):
        if isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        add('R04', record, f'{field} must be a valid YYYY-MM-DD date.')
        return None

    for name, document in [('facts', facts), ('assumptions', assumptions)]:
        if not isinstance(document, dict):
            add('R05', name, 'The JSON document must be an object.')
    if issues:
        return issues

    def rows(document, name, rule):
        collection = document.get(name)
        if not isinstance(collection, list):
            add(rule, name, 'Expected an array of record objects.')
            return []
        result = []
        for index, row in enumerate(collection):
            record = f'{name}[{index}]'
            if isinstance(row, dict):
                result.append((record, row))
            else:
                add(rule, record, 'Expected a record object.')
        return result

    def key(row, field, record):
        value = row.get(field)
        if not text(value):
            add('R05', record, f'{field} must be a non-empty string identifier.')
            return None
        return value

    def unique(value, seen, record, description):
        if value in seen:
            add('R03', record, f'Duplicate {description}.')
        else:
            seen.add(value)

    sources = rows(facts, 'sources', 'R09')
    instruments = rows(facts, 'instruments', 'R05')
    schedule = rows(facts, 'coupon_schedule', 'R06')
    positions = rows(assumptions, 'positions', 'R05')
    parse_date(assumptions.get('as_of_date'), 'assumptions', 'as_of_date')
    source_ids = set()
    for record, row in sources:
        source_id = key(row, 'source_id', record)
        if source_id is not None:
            unique(source_id, source_ids, record, 'source_id')
        if not text(row.get('title')):
            add('R09', record, 'A source title is required.')
        url = row.get('url')
        try:
            parsed = urlparse(url) if isinstance(url, str) else None
            valid_url = parsed and parsed.scheme in ('http', 'https') and parsed.hostname
        except ValueError:
            valid_url = False
        if not valid_url:
            add('R09', record, 'A source HTTP(S) URL with a host is required.')
        if not positive_int(row.get('page')):
            add('R09', record, 'A positive integer source page is required.')
        for field in ('publication_date', 'accessed_date'):
            if not text(row.get(field)):
                add('R09', record, f'Source {field} is required.')
            else:
                parse_date(row[field], record, field)

    instrument_ids, instrument_info = set(), {}
    for record, row in instruments:
        isin = key(row, 'isin', record)
        if isin is not None:
            unique(isin, instrument_ids, record, 'instrument ISIN')
        if not nonnegative_number(row.get('period_coupon_rate')):
            add('R01', record, 'period_coupon_rate must be finite, numeric and non-negative.')
        if row.get('currency') != 'USD':
            add('R08', record, 'Only USD instruments are supported; currencies cannot be mixed.')
        if row.get('instrument_type') != 'fixed_coupon_domestic_government_bond':
            add('R08', record, 'Only fixed-coupon domestic government bonds are supported.')
        start = parse_date(row.get('issue_date'), record, 'issue_date')
        end = parse_date(row.get('maturity_date'), record, 'maturity_date')
        if start and end and start >= end:
            add('R04', record, 'issue_date must precede maturity_date.')
        for field in ('coupon_period_months', 'expected_coupon_count'):
            if not positive_int(row.get(field)):
                add('R06', record, f'{field} must be a positive integer, not a boolean.')
        source_id = key(row, 'source_id', record)
        if source_id is not None and isinstance(facts.get('sources'), list) and source_id not in source_ids:
            add('R05', record, 'source_id does not reference a known source.')
        if isin is not None and isin not in instrument_info:
            instrument_info[isin] = (record, row, start, end)

    payments, coupon_keys, payment_keys = {}, set(), set()
    for record, row in schedule:
        isin = key(row, 'isin', record)
        coupon_no = row.get('coupon_no')
        if not positive_int(coupon_no):
            add('R06', record, 'coupon_no must be a positive integer, not a boolean.')
        payment_date = parse_date(row.get('payment_date'), record, 'payment_date')
        if isin is None:
            continue
        if positive_int(coupon_no):
            unique((isin, coupon_no), coupon_keys, record, 'coupon number for this ISIN')
        if payment_date is not None:
            unique((isin, payment_date), payment_keys, record, 'payment date for this ISIN')
        if isin not in instrument_info:
            if isinstance(facts.get('instruments'), list):
                add('R05', record, 'isin does not reference a known instrument.')
            continue
        payments.setdefault(isin, []).append((coupon_no, payment_date))
        _, _, start, end = instrument_info[isin]
        if payment_date and start and end and start < end and not start < payment_date <= end:
            add('R04', record, 'payment_date must be after issue and on or before maturity.')

    if isinstance(facts.get('coupon_schedule'), list):
        for isin, (record, row, start, end) in instrument_info.items():
            count, entries = row.get('expected_coupon_count'), payments.get(isin, [])
            if not positive_int(count):
                continue
            numbers = [number for number, _ in entries]
            complete = (len(entries) == count and all(positive_int(n) for n in numbers)
                        and sorted(numbers) == list(range(1, count + 1)))
            if not complete:
                add('R06', record, 'Coupon schedule must contain exactly coupons 1 through expected_coupon_count.')
                continue
            dates = [day for _, day in sorted(entries)]
            if any(day is None for day in dates):
                continue
            if any(later <= earlier for earlier, later in zip(dates, dates[1:])):
                add('R04', record, 'Payment dates must increase with coupon number.')
            if end and dates[-1] != end:
                add('R07', record, 'The last numbered coupon must be paid on maturity_date.')

    position_ids = set()
    for record, row in positions:
        isin = key(row, 'isin', record)
        if isin is not None:
            unique(isin, position_ids, record, 'position ISIN')
            if isinstance(facts.get('instruments'), list) and isin not in instrument_info:
                add('R05', record, 'isin does not reference a known instrument.')
        if not nonnegative_number(row.get('nominal_usd')):
            add('R02', record, 'nominal_usd must be finite, numeric and non-negative; zero is allowed.')
    return issues

"""The intake's spend: recorded per access key, never capped (intake.py, Money)."""
import json
import time

from simharness import intake, llm


def _ledger(tmp_path, rows):
    f = tmp_path / 'spend.jsonl'
    f.write_text(''.join(json.dumps(r) + '\n' for r in rows) + 'not json\n')
    return f


def test_spent_counts_keyed_lines_all_time_and_today(tmp_path):
    today = time.strftime('%Y-%m-%d', time.gmtime())
    f = _ledger(tmp_path, [
        {'day': today, 'dollars': 12.5, 'who': 'ana'},
        {'day': today, 'dollars': 4.0, 'who': 'ben'},
        {'day': '2000-01-01', 'dollars': 30.0, 'who': 'ana'},  # another day: all-time only
        {'day': today, 'dollars': 99.0, 'who': None},            # no key: neither
        {'day': today, 'dollars': 99.0},
    ])
    assert llm.spent(ledger=f) == (46.5, {'ana': 12.5, 'ben': 4.0})


def test_budget_never_stops_a_text():
    b = intake.Budget()
    b.add(500.0, 'compile', record=False)
    b.add(9.0, 'extract', typical=0.05, record=False)  # far over its estimate: recorded, not stopped
    assert b.spent == 509.0
    assert [x['stage'] for x in b.lines] == ['compile', 'extract']

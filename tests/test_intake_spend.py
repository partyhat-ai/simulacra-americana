"""The intake's spend: daily and monthly caps across every visitor, and how a
failing text is retried once, then given up (intake.py, Money and Failures)."""
import json
import time

import pytest

from simharness import intake, llm


def _ledger(tmp_path, rows):
    f = tmp_path / 'spend.jsonl'
    f.write_text(''.join(json.dumps(r) + '\n' for r in rows) + 'not json\n')
    return f


def _today():
    return time.strftime('%Y-%m-%d', time.gmtime())


def test_spent_counts_every_line_today_and_this_month(tmp_path):
    today = _today()
    other_day_this_month = today[:8] + ('01' if today[8:] != '01' else '02')
    f = _ledger(tmp_path, [
        {'day': today, 'dollars': 12.5, 'who': 'ana'},
        {'day': today, 'dollars': 4.0, 'who': None},              # no key: still counts
        {'day': today, 'dollars': 1.0},                           # no `who` at all: still counts
        {'day': other_day_this_month, 'dollars': 30.0},           # this month, not today
        {'day': '2000-01-01', 'dollars': 500.0, 'who': 'ana'},    # another month: neither
        {'day': today, 'dollars': 'x'},                           # unreadable: skipped
    ])
    assert llm.spent(ledger=f) == (17.5, 47.5)


def test_left_is_the_smaller_remainder_and_never_negative(tmp_path):
    f = _ledger(tmp_path, [{'day': _today(), 'dollars': 15.0}])
    assert intake.left(f, daily=20, monthly=200) == pytest.approx(5.0)    # today's cap binds
    assert intake.left(f, daily=100, monthly=18) == pytest.approx(3.0)    # this month's cap binds
    assert intake.left(f, daily=10, monthly=200) == 0.0                   # already over: nothing, not negative


def test_budget_stops_at_its_ceiling():
    b = intake.Budget(ceiling=5.0)
    b.add(3.0, 'compile', record=False)
    with pytest.raises(SystemExit, match='budget for new what-ifs is spent'):
        b.add(2.5, 'research', record=False)
    assert b.spent == 5.5  # the stage that crossed is still counted


def test_per_text_budget_is_unlimited_when_no_ceiling_is_passed():
    # Only the per-text limit is unset here. The public intake always passes a ceiling: what is
    # left under the $20/day and $200/month caps (see the cap tests below).
    b = intake.Budget()
    b.add(500.0, 'compile', record=False)
    assert b.spent == 500.0


@pytest.fixture
def sessions(tmp_path, monkeypatch):
    for name, file in [('SESSIONS', ''), ('QUEUE', 'queue.jsonl'), ('DONE', 'queue-done.jsonl'),
                       ('FAILED', 'queue-failed.jsonl'), ('DEAD', 'queue-dead.jsonl'), ('LOCK', 'intake.lock')]:
        monkeypatch.setattr(intake, name, tmp_path / file if file else tmp_path)
    monkeypatch.setattr(llm, 'LEDGER', tmp_path / 'spend.jsonl')
    monkeypatch.setattr(intake, '_config_for', lambda year, fallback=None: tmp_path / 'cfg.json')
    return tmp_path


def _queue(sessions, *texts):
    (sessions / 'queue.jsonl').write_text(''.join(json.dumps({'year': 1920, 'text': t, 'who': None}) + '\n' for t in texts))


def _lines(path):
    return [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []


def test_a_failing_text_is_retried_once_then_given_up_without_blocking_the_queue(sessions, monkeypatch):
    calls = []

    def fake_whatif(text, cfg, refresh=False, ceiling=None):
        calls.append(text)
        if text == 'always breaks':
            raise RuntimeError('boom')
        return {'status': 'modelled', 'key': 'k', 'dollars': 1.0}

    monkeypatch.setattr(intake, 'whatif', fake_whatif)
    _queue(sessions, 'always breaks', 'fine')

    first = intake.process_queue('cfg.json')
    assert [r['status'] for r in first] == ['error', 'modelled']   # the text behind the failure still runs
    assert not (sessions / 'queue-dead.jsonl').exists()

    second = intake.process_queue('cfg.json')
    assert [r['status'] for r in second] == ['error']               # retried once
    assert _lines(sessions / 'queue-dead.jsonl')[0]['attempts'] == intake.MAX_ATTEMPTS
    assert _lines(sessions / 'queue-done.jsonl')[-1]['status'] == 'gave-up'

    assert intake.process_queue('cfg.json') == []                    # settled: never billed again
    assert calls == ['always breaks', 'fine', 'always breaks']


def test_nothing_runs_once_the_cap_is_spent(sessions, monkeypatch):
    monkeypatch.setattr(intake, 'whatif', lambda *a, **k: pytest.fail('modelled over the cap'))
    (sessions / 'spend.jsonl').write_text(json.dumps({'day': _today(), 'dollars': intake.DAILY_USD}) + '\n')
    _queue(sessions, 'one', 'two')
    out = intake.process_queue('cfg.json')
    assert [r['status'] for r in out] == ['over-cap', 'over-cap']    # both settled, so no page waits for nothing
    assert [x['status'] for x in _lines(sessions / 'queue-done.jsonl')] == ['over-cap', 'over-cap']


def test_a_text_that_crosses_the_cap_mid_run_is_settled_and_stops_the_rest(sessions, monkeypatch):
    def fake_whatif(text, cfg, refresh=False, ceiling=None):
        b = intake.Budget(ceiling)
        b.add(ceiling + 1, 'ask')  # recorded in the ledger, and crosses
        return {'status': 'modelled'}

    monkeypatch.setattr(intake, 'whatif', fake_whatif)
    _queue(sessions, 'expensive', 'next')
    out = intake.process_queue('cfg.json')
    assert [r['status'] for r in out] == ['over-cap', 'over-cap']
    assert not (sessions / 'queue-failed.jsonl').exists()            # a cap stop is not a failure to retry

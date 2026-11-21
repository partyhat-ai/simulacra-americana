"""The worker lock, the batch wait's deadline, and prices for models the table doesn't list."""
import os
import subprocess
import sys
import textwrap
from types import SimpleNamespace

import pytest

from simharness import intake, llm


def test_the_lock_is_atomic_and_released(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, 'LOCK', tmp_path / 'intake.lock')
    fd, holder = intake._lock()
    assert fd is not None and holder is None
    assert (tmp_path / 'intake.lock').read_text() == str(os.getpid())
    # Another process can't take it while it's held, and is told who holds it.
    probe = textwrap.dedent(f'''
        import fcntl, os, sys
        fd = os.open({str(tmp_path / 'intake.lock')!r}, os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB); print('took')
        except BlockingIOError:
            print('busy')
    ''')
    assert subprocess.run([sys.executable, '-c', probe], capture_output=True, text=True).stdout.strip() == 'busy'
    intake._unlock(fd)
    assert subprocess.run([sys.executable, '-c', probe], capture_output=True, text=True).stdout.strip() == 'took'


def test_a_lock_left_by_a_dead_worker_is_not_stale(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, 'LOCK', tmp_path / 'intake.lock')
    (tmp_path / 'intake.lock').write_text('999999')   # a crashed worker's pid: no flock survives it
    fd, holder = intake._lock()
    assert fd is not None
    intake._unlock(fd)


def test_a_busy_queue_returns_without_working(tmp_path, monkeypatch):
    for name, file in [('SESSIONS', ''), ('QUEUE', 'queue.jsonl'), ('DONE', 'done.jsonl'), ('LOCK', 'intake.lock')]:
        monkeypatch.setattr(intake, name, tmp_path / file if file else tmp_path)
    fd, _ = intake._lock()
    monkeypatch.setattr(intake, '_lock', lambda: (None, '4242'))
    assert intake.process_queue('cfg.json') == [{'status': 'busy', 'pid': '4242'}]
    intake._unlock(fd)


class FakeBatches:
    def __init__(self, ends_after=None, cancel_ends=True):
        self.polls, self.cancelled, self.ends_after, self.cancel_ends = 0, False, ends_after, cancel_ends

    def retrieve(self, batch_id):
        self.polls += 1
        done = (self.ends_after is not None and self.polls > self.ends_after) or (self.cancelled and self.cancel_ends)
        return SimpleNamespace(processing_status='ended' if done else 'in_progress')

    def cancel(self, batch_id):
        self.cancelled = True


def _backend(batches):
    be = object.__new__(llm.AnthropicBatchBackend)
    be.client = SimpleNamespace(messages=SimpleNamespace(batches=batches))
    return be


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_a_batch_that_ends_in_time_is_not_cancelled():
    b, clock = FakeBatches(ends_after=3), Clock()
    _backend(b).wait('b1', 30, 3600, clock.sleep, clock)
    assert not b.cancelled and b.polls == 4


def test_a_slow_batch_is_cancelled_at_the_deadline_and_its_answers_kept():
    b, clock = FakeBatches(), Clock()
    _backend(b).wait('b1', 30, 300, clock.sleep, clock)
    assert b.cancelled and clock.t <= 300 + 30   # cancelled at the deadline, then ended


def test_a_batch_that_never_ends_raises_instead_of_hanging():
    b, clock = FakeBatches(cancel_ends=False), Clock()
    with pytest.raises(TimeoutError, match='b1'):
        _backend(b).wait('b1', 30, 300, clock.sleep, clock)
    assert b.cancelled and clock.t <= 300 + llm.AnthropicBatchBackend.CANCEL_WAIT + 30


def test_prices_never_undercharge_an_unknown_model(capsys):
    assert llm.prices('claude-opus-5-5') == llm.PRICES['claude-opus-5-5']
    assert llm.prices('claude-opus-5-5-20261001') == llm.PRICES['claude-opus-5-5']    # a dated id: its base
    dearest = max(llm.PRICES.values(), key=lambda p: p[1])
    assert llm.prices('claude-future-9') == dearest
    usage = {'input_tokens': 1000, 'output_tokens': 1000}
    assert llm.cost('claude-future-9', usage) >= max(llm.cost(m, usage) for m in llm.PRICES)
    llm.prices('claude-future-9')
    assert capsys.readouterr().out.count('no price for claude-future-9') == 1          # reported once


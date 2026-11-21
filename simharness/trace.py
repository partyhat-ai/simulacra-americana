"""Step-level traces of the research agent (agent.py), and the record that replays them.

One file per trace, sessions/traces/<id>.jsonl, one event per line:

    start    what was asked: the reader's text, the year, the model, the policy, the ceiling
    model    one model turn: its content blocks, stop reason, usage and dollars
    tool     one tool call: name, arguments, tier, the gate's decision, the full result
             (so a replay can serve it back), a hash of it, dollars and milliseconds
    end      the outcome, total dollars and steps

Every event carries `seq` (its order in the trace) and `ms` (milliseconds since the
start). A replay (agent.replay) answers the tool calls a new model makes from a
trace's recorded results, so a prompt or model change can be compared step by step
without paying for searches, interviews or writes again.

Traces hold the reader's words, so they are kept SIMULACRA_RETAIN_DAYS (default 7)
like the router's session logs; `prune` drops older ones.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import time
from pathlib import Path

from .config import ROOT

TRACES = ROOT / 'sessions/traces'


def digest(value) -> str:
    """A short, stable hash of any JSON value (sorted keys)."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:16]


class Trace:
    def __init__(self, kind: str, folder: Path | None = None, trace_id: str | None = None, **start):
        self.folder = Path(folder or TRACES)
        self.folder.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.id = trace_id or f'{stamp}-{digest([kind, start, time.time_ns()])[:8]}'
        self.path = self.folder / f'{self.id}.jsonl'
        self.t0, self.seq = time.monotonic(), 0
        self.event('start', kind=kind, at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), **start)

    def event(self, type_: str, **fields) -> dict:
        row = {'seq': self.seq, 'type': type_, 'ms': round((time.monotonic() - self.t0) * 1000), **fields}
        self.seq += 1
        with open(self.path, 'a') as f:
            f.write(json.dumps(row, default=str) + '\n')
        return row


def path_of(trace_id: str, folder: Path | None = None) -> Path:
    return Path(folder or TRACES) / f'{trace_id}.jsonl'


def load(trace_id: str, folder: Path | None = None) -> list[dict]:
    p = path_of(trace_id, folder)
    if not p.exists():
        raise SystemExit(f'no trace {trace_id} in {p.parent}')
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def tool_path(events: list[dict]) -> list[str]:
    """The tools a trace called, in order, with the gate's decision when it wasn't plain `ran`."""
    return [e['name'] + ('' if e.get('decision') == 'ran' else f' ({e.get("decision")})') for e in events if e['type'] == 'tool']


def summary(events: list[dict]) -> dict:
    start = events[0] if events and events[0]['type'] == 'start' else {}
    end = next((e for e in reversed(events) if e['type'] == 'end'), {})
    models = [e for e in events if e['type'] == 'model']
    tools = [e for e in events if e['type'] == 'tool']
    return {
        'kind': start.get('kind'), 'text': start.get('text'), 'year': start.get('year'), 'model': start.get('model'),
        'outcome': end.get('status'), 'why': end.get('why'), 'key': end.get('key'),
        'turns': len(models), 'tools': tool_path(events),
        'refused': [e['name'] for e in tools if e.get('decision') == 'refused'],
        'dollars': round(sum(e.get('dollars') or 0 for e in models + tools), 4),
        'model_dollars': round(sum(e.get('dollars') or 0 for e in models), 4),
        'seconds': round((events[-1]['ms'] if events else 0) / 1000, 1),
    }


def recent(folder: Path | None = None, limit: int = 20) -> list[dict]:
    folder = Path(folder or TRACES)
    files = sorted(folder.glob('*.jsonl'), key=lambda p: p.stat().st_mtime, reverse=True)[:limit] if folder.exists() else []
    return [{'id': p.stem, **summary(load(p.stem, folder))} for p in files]


def prune(folder: Path | None = None, days: float | None = None, now: float | None = None) -> int:
    """Delete traces last written more than `days` ago (SIMULACRA_RETAIN_DAYS, default 7)."""
    folder = Path(folder or TRACES)
    days = float(os.environ.get('SIMULACRA_RETAIN_DAYS') or 7) if days is None else days
    cutoff = (now or time.time()) - days * 86400
    gone = 0
    for p in folder.glob('*.jsonl') if folder.exists() else []:
        if p.stat().st_mtime < cutoff:
            p.unlink(missing_ok=True)
            gone += 1
    return gone

"""Golden tasks for the research agent (agent.py), from the what-ifs already compiled.

    python -m simharness.run agent-eval --year 1920 --limit 3 [--model ...] [--ceiling 4]

Each compiled what-if that was modelled as asked is a task: its reader's words go
to the agent in a dry run (no writes, no interviews, no publish), with that
what-if hidden from the registry so the agent has to compile it afresh rather than
match it. The agent's spec is scored against the stored one on what decides how
the change is modelled (kind, mode, which nominee it concerns, a withdrawal, the
groups it reaches), and its path is checked: it registered, it validated first,
and nothing was refused. A run costs the compile, research and staging calls,
about $1 to $3 a task on the live configs; the ceiling stops any one task.
"""
from __future__ import annotations

from pathlib import Path

from . import agent, trace
from .config import ROOT
from .whatifs import REGISTRY

FIELDS = ('subkind', 'mode', 'about', 'withdraws', 'reach')


def golden(year: int, registry: dict | None = None) -> list[dict]:
    reg = REGISTRY if registry is None else registry
    return [v for v in reg.values() if v.get('generated') and v.get('source_text') and v.get('fidelity', 'as-asked') == 'as-asked'
            and year in (v.get('years') or [v.get('year', 1920)])]


def score(spec: dict | None, gold: dict) -> dict:
    """Field by field: does the agent's spec model the change the way the stored one does?"""
    spec = spec or {}
    fields = {f: spec.get(f) == gold.get(f) for f in FIELDS}
    return {'fields': fields, 'matched': sum(fields.values()), 'of': len(FIELDS)}


def path_checks(events: list[dict]) -> dict:
    tools = [e for e in events if e['type'] == 'tool']
    names = [e['name'] for e in tools]
    reg = names.index('register') if 'register' in names else None
    return {'registered': reg is not None and tools[reg]['decision'] in ('ran', 'simulated'),
            'validated_before_register': reg is not None and 'validate' in names[:reg],
            'refusals': sum(e['decision'] == 'refused' for e in tools),
            'turns': sum(e['type'] == 'model' for e in events)}


def evaluate(year: int, limit: int = 3, model: str | None = None, ceiling: float = 4.0, client=None,
             ops=None, folder: Path | None = None) -> dict:
    cfg_path = ROOT / f'configs/live-{year}.json'
    rows, dollars = [], 0.0
    for gold in golden(year)[:limit]:
        reg = {k: v for k, v in REGISTRY.items() if k != gold['key']}
        s = agent.start(gold['source_text'], cfg_path, ceiling, agent.Policy(publish='never', dry_run=True, model=model),
                        ops=ops, registry=reg, folder=folder, kind='eval', gold=gold['key'])
        try:
            agent.run_session(s, client)
            err = None
        except SystemExit as e:
            err = str(e)
        events = trace.load(s.trace.id, folder)
        rows.append({'gold': gold['key'], 'text': gold['source_text'], 'outcome': agent.result_status(s), 'error': err,
                     'trace': s.trace.id, 'dollars': round(s.budget.spent, 4), **score(s.spec, gold), **path_checks(events)})
        dollars += s.budget.spent
    n = len(rows) or 1
    return {'tasks': len(rows), 'dollars': round(dollars, 4),
            'field_accuracy': round(sum(r['matched'] for r in rows) / (n * len(FIELDS)), 3),
            'registered': sum(r['registered'] for r in rows), 'validated_first': sum(r['validated_before_register'] for r in rows),
            'rows': rows}

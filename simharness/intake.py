"""Typed what-if intake: a reader's words → a what-if the page can serve.

    python -m simharness.run whatif --text "charlie chaplin ran as an independent" --config configs/live-1920.json
    python -m simharness.run whatif --queue --config configs/live-1920.json    # what the router queued as unknown
    python -m simharness.run research --config configs/live-1920.json          # evidence for the config's what-ifs

Stages, each priced before it is sent and recorded in sessions/spend.jsonl:

1. compile   (research.compile_model, structured): the words become a spec;
             or `same_as` an existing what-if, in which case only its keywords
             grow and the bundle is republished; or not modelable.
2. research  (research.research_model + web search): notes with citations.
3. extract   (research.extract_model, structured): graded findings, each
             grounded in a source the search returned.
4. stage     (research.world_model, structured; D33, world.py): the year's
             newspaper items the change makes false, in-world news, downstream
             facts, a belief check, and the groups to interview.
5. register  whatifs/<key>.json and whatifs/evidence/<key>.json; the key
             joins the config's what_ifs.
6. run       backbone → plan → ask (identical earlier requests reused) →
             refine (audit, escalate) → analyze → publish → serve/bundles/<year>.json.

Model and effort (D33): the once-per-what-if calls (compile, extract, stage,
audit) are where a stronger model buys the most per dollar: each runs once,
and each decides whether the interviews measure the change at all. The live
configs run them on Opus at high effort; the per-voter interviews stay on the
bulk model, with only the answers that fail a check re-asked on a stronger one.

Money: every stage is priced before it is sent and recorded after, with the
name of the access key that queued the text, if any (llm.SPEND_WHO). Queued
text is modelled only while the spend ledger is under both caps, counted across
every visitor together: DAILY_USD per UTC day (SIMULACRA_DAILY_USD, default 20)
and MONTHLY_USD per UTC month (SIMULACRA_MONTHLY_USD, default 200). The router
(serve/guard.ts) checks the same caps before it queues; the worker checks again
before each text, and a text's Budget stops at the first stage that crosses
what is left. A stage is priced when it finishes, so a cap can be passed by at
most the one stage that crosses it.

Failures: a text that fails is retried once. After MAX_ATTEMPTS failures it is
settled as given up (queue-done.jsonl, status `gave-up`) and copied to
queue-dead.jsonl, so one bad text can't be re-billed forever or hold up the
texts queued behind it.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import time
from pathlib import Path

from . import evidence, llm, scenario
from .config import ROOT, RunConfig
from .whatifs import REGISTRY

SESSIONS = ROOT / 'sessions'
QUEUE = SESSIONS / 'queue.jsonl'
DONE = SESSIONS / 'queue-done.jsonl'
FAILED = SESSIONS / 'queue-failed.jsonl'
DEAD = SESSIONS / 'queue-dead.jsonl'
LOCK = SESSIONS / 'intake.lock'
SERVE_BUNDLES = ROOT / 'serve/bundles'
STATUS = SESSIONS / 'intake-status.json'
DAILY_USD = float(os.environ.get('SIMULACRA_DAILY_USD') or 20)
MONTHLY_USD = float(os.environ.get('SIMULACRA_MONTHLY_USD') or 200)
OVER_CAP = 'The budget for new what-ifs is spent for now. Try again tomorrow.'
MAX_ATTEMPTS = 2
GAVE_UP = 'I couldn’t model that, after two tries.'


class Progress:
    """What the worker is doing, for the router to show while the page waits
    (sessions/intake-status.json: {text, steps: [{text, state}], ts})."""

    def __init__(self, text: str | None):
        self.text, self.steps = (_norm(text) if text else None), []

    def step(self, label: str):
        if not self.text:
            return
        for s in self.steps:
            s['state'] = 'done'
        self.steps.append({'text': label, 'state': 'doing'})
        self._write()

    def finish(self):
        for s in self.steps:
            s['state'] = 'done'
        self._write()

    def _write(self):
        if not self.text:
            return
        SESSIONS.mkdir(exist_ok=True)
        tmp = STATUS.with_suffix(f'.{os.getpid()}.tmp')
        tmp.write_text(json.dumps({'text': self.text, 'steps': self.steps, 'ts': dt.datetime.now().isoformat(timespec='seconds')}))
        tmp.replace(STATUS)


class Budget:
    """What a typed what-if has spent, stage by stage, and the most it may (None: no ceiling)."""

    def __init__(self, ceiling: float | None = None):
        self.spent, self.lines, self.ceiling = 0.0, [], ceiling

    def add(self, dollars: float, stage: str, typical: float | None = None, note: str = '', record: bool = True):
        self.spent += dollars
        self.lines.append({'stage': stage, 'dollars': round(dollars, 4), 'typical': typical})
        if record:
            llm.record_spend(stage, dollars, note=note)
        if self.ceiling is not None and self.spent >= self.ceiling:
            raise SystemExit(OVER_CAP)


# Typical output tokens by call (measured: a compile answer ran ~1,300 tokens on Sonnet 5.5).
TYPICAL_OUT = {'compile': 1600, 'compile-retry': 1600, 'extract': 3000, 'stage': 2500}
# Thinking at higher effort multiplies output [I].
EFFORT_OUT = {'low': 1.0, 'medium': 3.0, 'high': 6.0, 'xhigh': 7.0, 'max': 8.0}


def typical_out(stage: str, effort: str, max_tokens: int) -> int:
    return int(min(TYPICAL_OUT.get(stage, 600) * EFFORT_OUT.get(effort, 1.0), 0.75 * max_tokens))


def _structured(req: dict, max_tokens: int, budget: Budget, stage: str, note: str = '') -> dict:
    from .config import RUNS
    cache = llm.AnswerCache(RUNS)
    hit = cache.get(req)
    if hit:
        print(f'{stage}: reused an identical earlier answer', flush=True)
        return hit['data']
    effort = req.get('effort') or 'low'
    est = llm.estimate([req], max_tokens, typical_out=typical_out(stage, effort, max_tokens))
    print(f'{stage}: ~${est["typical"]} typical, ${est["worst"]} worst ({req["model"]}, {effort} effort)', flush=True)
    ans = llm.AnthropicBackend(effort=effort, max_tokens=max_tokens)._one(req)
    cache.put(req, ans | {'backend': 'anthropic'})
    budget.add(llm.cost(req['model'], ans.get('usage') or {}), stage, est['typical'], note)
    if not ans.get('ok'):
        raise SystemExit(f'{stage} failed: {ans.get("error")}')
    return ans['data']


def _with_effort(req: dict, effort: str, fast: bool = False) -> dict:
    # 'low' keeps the request byte-identical to before D33, so its cached answers still match.
    # Fast mode changes only how quickly the answer comes (and its price), so it isn't part of the cache key.
    out = req | {'effort': effort} if effort and effort != 'low' else dict(req)
    return out | {'speed': 'fast'} if fast and llm.fast_ok(req['model']) else out


def compile_text(text: str, cfg: RunConfig, budget: Budget) -> dict:
    from . import profiles
    rc, prof = cfg.research, profiles.get(cfg.election)
    mt = max(3000, rc.pass_max_tokens)
    raw = _structured(_with_effort(scenario.compile_request(text, REGISTRY, cfg.context_cutoff, rc.compile_model, prof=prof),
                                   rc.compile_effort, rc.fast), mt, budget, 'compile', text)
    bad = scenario.naming_violations(raw, cfg.election) if raw.get('modelable') else []
    if bad:
        note = ('These sentences name a nominee, a party or the President, which the blinded briefs cannot show. '
                'Rewrite them with the descriptions given: ' + json.dumps(bad))
        raw = _structured(_with_effort(scenario.compile_request(text, REGISTRY, cfg.context_cutoff, rc.compile_model, note, prof),
                                       rc.compile_effort, rc.fast), mt, budget, 'compile-retry', text)
    return raw


def stage(spec: dict, cfg: RunConfig, budget: Budget, ev: dict | None = None) -> dict | None:
    """D33: stage the what-if's world (world.py) and keep it on the spec. Agent-mode what-ifs only:
    a backbone-mode change's interviews are a cross-check and move no numbers."""
    from . import data, profiles, world
    rc = cfg.research
    if not rc.world_model or spec.get('mode') != 'agents':
        return None
    prof = profiles.get(cfg.election)
    rel = prof.get('corpus') or ('sources/corpus_1920.jsonl' if cfg.election == 1920 else None)
    corpus = data.corpus(cfg.context_cutoff, rel, profiles.names_re(cfg.election)) if rel else []
    req = _with_effort(world.stage_request(spec, prof, cfg.context_cutoff, corpus, rc.world_model, rc.world_effort, ev),
                       rc.world_effort, rc.fast)
    raw = _structured(req, max(4000, rc.pass_max_tokens), budget, 'stage', spec['key'])
    spec['world'] = world.finalize(raw, spec, prof, cfg.context_cutoff, corpus, rc.world_model, rc.world_effort)
    return spec['world']


def stage_config(config_path: str | Path, only: str | None = None, refresh: bool = False) -> dict:
    """Stage every compiled agent-mode what-if in a config that hasn't been (D33), and save its spec."""
    cfg = RunConfig.load(config_path)
    keys = [k for k in cfg.what_ifs if (not only or k == only) and REGISTRY.get(k, {}).get('generated')
            and REGISTRY[k].get('mode') == 'agents' and (refresh or not REGISTRY[k].get('world'))]
    budget = Budget()
    out = {}
    for k in keys:
        spec = {kk: v for kk, v in REGISTRY[k].items() if kk not in ('apply', 'facts')}
        w = stage(spec, cfg, budget, scenario.load_evidence(k))
        if w is None:
            continue
        scenario.save_spec(spec)
        REGISTRY[k] = scenario.bind(spec)
        out[k] = {'contradicted': len(w['contradicted']), 'items': len(w['items']), 'check': (w['check'] or {}).get('question'),
                  'focus': [f['why'] for f in w['focus']]}
    return {'staged': out, 'dollars': round(budget.spent, 4)}


def reextract(spec: dict, cfg: RunConfig, budget: Budget, have: dict) -> dict:
    """Extraction again from the saved notes (no new search)."""
    notes = {'text': have['notes'], 'sources': have['sources']}
    rc = cfg.research
    extracted = _structured(_with_effort(evidence.extract_request(spec, notes, rc.extract_model), rc.extract_effort, rc.fast),
                            max(8000, rc.pass_max_tokens), budget, 'extract', spec['key'])
    ev = {**have, **evidence.ground(extracted, notes, spec.get('about')), 'models': {**have.get('models', {}), 'extract': rc.extract_model},
          'reextracted_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
    scenario.save_evidence(spec['key'], ev)
    return ev


def research(spec: dict, cfg: RunConfig, budget: Budget, refresh: bool = False, again: bool = False) -> dict:
    """Evidence for one what-if (cached in whatifs/evidence/<key>.json). again: re-extract the saved notes."""
    import anthropic
    key = spec['key']
    have = scenario.load_evidence(key)
    if have and again and have.get('notes'):
        return reextract(spec, cfg, budget, have)
    if have and not refresh:
        return have
    rc = cfg.research
    est = evidence.research_estimate(rc.research_model, rc.max_searches, rc.research_max_tokens)
    print(f'research {key}: ~${est["typical"]} typical, ${est["worst"]} worst ({rc.research_model}, '
          f'≤{rc.max_searches} searches)', flush=True)
    client = anthropic.Anthropic(api_key=llm.api_key())
    notes = evidence.research(client, spec, {'year': cfg.election, 'day': cfg.election_day}, rc.research_model,
                              rc.max_searches, rc.research_effort, rc.research_max_tokens)
    budget.add(notes['dollars'], 'research', None, key)
    print(f'  {len(notes["queries"])} searches, {len(notes["sources"])} sources '
          f'({sum(s["tier"] == "A" for s in notes["sources"])} scholarly or official), ${notes["dollars"]}', flush=True)
    extracted = _structured(_with_effort(evidence.extract_request(spec, notes, rc.extract_model), rc.extract_effort, rc.fast),
                            max(8000, rc.pass_max_tokens), budget, 'extract', key)
    ev = evidence.ground(extracted, notes, spec.get('about'))
    ev.update({'key': key, 'version': evidence.EVIDENCE_VERSION,
               'researched_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
               'models': {'research': rc.research_model, 'extract': rc.extract_model}, 'queries': notes['queries'],
               'sources': notes['sources'], 'notes': notes['text'], 'prompt': notes['prompt'], 'usage': notes['usage'],
               'dollars': round(sum(x['dollars'] for x in budget.lines if x['stage'] in ('research', 'extract')), 4)})
    scenario.save_evidence(key, ev)
    return ev


def documented_positions(spec: dict, ev: dict, cutoff: str):
    """A candidate's positions from the record, when the research found any on
    or before the cutoff (masked like any brief text); else they stay inferred."""
    keep = []
    for p in ev.get('actor_positions', []):
        d = p.get('date', '')
        try:
            ok = dt.date.fromisoformat(d[:10]).isoformat() <= cutoff
        except ValueError:
            m = re.search(r'\b(1[6-9]\d\d)\b', d)
            ok = bool(m) and int(m.group(1)) < int(cutoff[:4])
        if ok:
            keep.append(scenario.clean_position(p['text'], int(cutoff[:4])))
    if keep:
        spec['candidate']['positions'] = keep[:3]
        spec['candidate']['positions_source'] = 'documented'


def _add_to_config(config_path: Path, key: str):
    raw = json.loads(config_path.read_text())
    if key not in raw['what_ifs']:
        raw['what_ifs'].append(key)
        config_path.write_text(json.dumps(raw, indent=2) + '\n')


def run_pipeline(config_path: Path, budget: Budget, publish_only: bool = False, progress: Progress | None = None) -> dict:
    from .run import Run
    progress = progress or Progress(None)
    run = Run(RunConfig.load(config_path))
    if not publish_only:
        if not (run.dir / 'fit.pkl').exists():
            run.backbone()
        run.plan()
        progress.step(f'Interviewing voters in your {run.cfg.election}, with the real one as a control.')
        asked = run.ask()
        budget.add(asked['dollars'], 'ask', None, record=False)  # ask records its own spend
        if run.cfg.research.audit_model or run.cfg.agents.escalate_model:
            progress.step('Checking that each voter took the change as true.')
            refined = run.refine()
            budget.add(refined['dollars'], 'refine', None, record=False)  # audit and ask record their own spend
        progress.step('Comparing the interviews with the historical record.')
        run.analyze()
    progress.step(f'Rerunning the {run.cfg.election} election 100 times.')
    run.publish()
    SERVE_BUNDLES.mkdir(parents=True, exist_ok=True)
    src = run.dir / 'published' / f'{run.cfg.election}.json'
    shutil.copyfile(src, SERVE_BUNDLES / f'{run.cfg.election}.json')
    (SERVE_BUNDLES / 'RUN_ID').write_text(run.id + '\n')
    return {'run': run.id, 'bundle': str(src)}


def report(year: int, key: str) -> dict:
    b = json.loads((SERVE_BUNDLES / f'{year}.json').read_text())
    r = b['runs'].get(key) or {}
    return {'key': key, 'label': REGISTRY[key]['label'], 'summary': r.get('summary'), 'ev': r.get('ev'),
            'confidence': r.get('confidenceTier'), 'flags': r.get('confidenceFlags'),
            'evidence': [{'strength': e['strength'], 'agreement': e['agreement'], 'detail': e.get('agreementDetail')}
                         for e in r.get('evidence', [])]}


def left(ledger: Path | None = None, daily: float | None = None, monthly: float | None = None) -> float:
    """Dollars the intake may still spend: the smaller of what's left of today's
    cap and this month's, every visitor together (llm.spent)."""
    today, month = llm.spent(ledger=ledger or llm.LEDGER)
    rest = min((DAILY_USD if daily is None else daily) - today, (MONTHLY_USD if monthly is None else monthly) - month)
    return max(rest, 0.0)


def whatif(text: str, config_path: str | Path, refresh: bool = False, ceiling: float | None = None) -> dict:
    config_path = Path(config_path)
    cfg = RunConfig.load(config_path)
    budget = Budget(ceiling)
    progress = Progress(text)
    progress.step('Turning your words into a change I can model.')
    raw = compile_text(text, cfg, budget)
    if not raw['modelable']:
        progress.finish()
        return {'status': 'not-modelable', 'why': raw['why_not'], 'dollars': round(budget.spent, 4)}
    if raw['same_as'] in REGISTRY and cfg.election in (REGISTRY[raw['same_as']].get('years') or [REGISTRY[raw['same_as']].get('year', 1920)]):
        key = raw['same_as']
        scenario.add_words(key, raw['words'] + [text.lower().strip()[:80]])
        in_config = key in cfg.what_ifs
        _add_to_config(config_path, key)
        progress.step(f'That’s {REGISTRY[key]["label"]}, which I’ve modelled already.')
        out = run_pipeline(config_path, budget, publish_only=in_config, progress=progress)
        progress.finish()
        return {'status': 'keyword', 'key': key, **out, 'dollars': round(budget.spent, 4), 'costs': budget.lines,
                'report': report(cfg.election, key)}
    spec = scenario.finalize(raw, text, REGISTRY, cfg.research.compile_model, cfg.election)
    if spec.get('reinterpretation'):
        progress.step(spec['reinterpretation'])
    progress.step(f'Setting the scene: autumn {cfg.election}…')
    ev = research(spec, cfg, budget, refresh)
    n = len(ev.get('findings', []))
    progress.step(f'Clarifying historical context: {n or "no"} finding{"" if n == 1 else "s"}.')
    if spec['kind'] == 'candidate' and spec['candidate']['positions_source'] != 'documented':
        documented_positions(spec, ev, cfg.context_cutoff)
    if cfg.research.world_model and spec['mode'] == 'agents':
        progress.step(f'Staging the autumn of {cfg.election} so nothing in it contradicts the change.')
        w = stage(spec, cfg, budget, ev)
        if w:
            gone, new = len(w['contradicted']), len(w['items'])
            progress.step(f'Took out {gone or "no"} newspaper item{"" if gone == 1 else "s"} the change makes false; '
                          f'wrote {new} from the changed world{" and a question to check each voter believes it" if w["check"] else ""}.')
    scenario.save_spec(spec)
    REGISTRY[spec['key']] = scenario.bind(spec)
    _add_to_config(config_path, spec['key'])
    out = run_pipeline(config_path, budget, progress=progress)
    progress.finish()
    return {'status': 'modelled', 'key': spec['key'], **out, 'dollars': round(budget.spent, 4), 'costs': budget.lines,
            'report': report(cfg.election, spec['key'])}


def research_config(config_path: str | Path, refresh: bool = False, only: str | None = None, again: bool = False) -> dict:
    """Evidence for every what-if in a config that lacks it (hand-written ones included: there it grades confidence only)."""
    cfg = RunConfig.load(config_path)
    keys = [k for k in cfg.what_ifs if not only or k == only]
    budget = Budget()
    out = {}
    for k in keys:
        ev = research({**REGISTRY[k], 'key': k}, cfg, budget, refresh, again)
        out[k] = {'strength': evidence.strength(ev)['level'], 'findings': len(ev['findings']), 'summary': ev['summary'][:200]}
    return {'what_ifs': out, 'dollars': round(budget.spent, 4)}


# ── The router's queue ──

def _norm(text: str) -> str:
    return ' '.join(text.lower().split())


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _config_for(year: int, fallback: Path | None = None) -> Path | None:
    """configs/live-<year>.json for any simulated year (one with a profile), or the
    worker's own config when it is that year's; None when the year isn't simulated."""
    from . import profiles
    if year not in profiles.years():
        return None
    p = ROOT / f'configs/live-{year}.json'
    if p.exists():
        return p
    return fallback if fallback and Path(fallback).exists() and RunConfig.load(fallback).election == year else None


def _settle(year: int, text: str, status: str, why: str | None = None, key: str | None = None,
            dollars: float | None = None):
    with open(DONE, 'a') as f:
        f.write(json.dumps({'text': text, 'year': year, 'ts': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                            'status': status, 'key': key, 'why': why, 'dollars': dollars}) + '\n')


def process_queue(config_path: str | Path, limit: int = 3) -> list[dict]:
    """Model up to `limit` distinct queued (year, text) pairs, oldest first, within the caps.
    Each is modelled in its own year's live config, its spend recorded against the key that queued it, if any.
    A text that has failed MAX_ATTEMPTS times is given up (queue-dead.jsonl) instead of retried."""
    SESSIONS.mkdir(exist_ok=True)
    if LOCK.exists() and _pid_alive(int(LOCK.read_text().strip() or 0)):
        return [{'status': 'busy', 'pid': LOCK.read_text().strip()}]
    LOCK.write_text(str(os.getpid()))
    try:
        done = set()
        for l in DONE.read_text().splitlines() if DONE.exists() else []:
            if l.strip():
                x = json.loads(l)
                done.add((x.get('year', 1920), x['text']))
        attempts: dict[tuple[int, str], int] = {}
        for l in FAILED.read_text().splitlines() if FAILED.exists() else []:
            if l.strip():
                x = json.loads(l)
                k = (int(x.get('year') or 1920), x['text'])
                attempts[k] = attempts.get(k, 0) + 1
        pending, who = [], {}
        for l in QUEUE.read_text().splitlines() if QUEUE.exists() else []:
            if l.strip():
                q = json.loads(l)
                key = (int(q.get('year') or 1920), _norm(q['text']))
                if key not in done and key not in pending:
                    pending.append(key)
                    who[key] = q.get('who')
        results = []
        for year, t in pending[:limit]:
            if attempts.get((year, t), 0) >= MAX_ATTEMPTS:
                # Failed before, every time: settled, not retried again.
                with open(DEAD, 'a') as f:
                    f.write(json.dumps({'text': t, 'year': year, 'attempts': attempts[(year, t)], 'at': time.time()}) + '\n')
                _settle(year, t, 'gave-up', GAVE_UP)
                results.append({'text': t, 'year': year, 'status': 'gave-up', 'why': GAVE_UP})
                continue
            cfg_path = _config_for(year, Path(config_path))
            llm.SPEND_WHO = who[(year, t)]
            budget_left = left()
            if budget_left <= 0:
                # Settled, not retried: later budget isn't spent on text nobody is waiting for.
                _settle(year, t, 'over-cap', OVER_CAP)
                results.append({'text': t, 'year': year, 'status': 'over-cap', 'why': OVER_CAP})
                continue
            try:
                if cfg_path is None:
                    r = {'status': 'not-modelable', 'why': f'I haven’t simulated {year} yet.'}
                else:
                    r = whatif(t, cfg_path, ceiling=budget_left)
            except (SystemExit, Exception) as e:
                why = str(e) or repr(e)
                if isinstance(e, SystemExit) and why == OVER_CAP:
                    # The cap was reached mid-text: settled. The texts after it find nothing left
                    # and are settled the same way, so no waiting page times out.
                    _settle(year, t, 'over-cap', OVER_CAP)
                    results.append({'text': t, 'year': year, 'status': 'over-cap', 'why': OVER_CAP})
                    continue
                # A stop or a bug: recorded (FAILED, read by the router, which tells the waiting
                # page why). The text stays queued for one more try, then is given up.
                r = {'text': t, 'year': year, 'status': 'stopped' if isinstance(e, SystemExit) else 'error', 'why': why}
                with open(FAILED, 'a') as f:
                    f.write(json.dumps(r | {'at': time.time()}) + '\n')
                attempts[(year, t)] = attempts.get((year, t), 0) + 1
                if attempts[(year, t)] >= MAX_ATTEMPTS:
                    with open(DEAD, 'a') as f:
                        f.write(json.dumps({'text': t, 'year': year, 'attempts': attempts[(year, t)], 'why': why,
                                            'at': time.time()}) + '\n')
                    _settle(year, t, 'gave-up', GAVE_UP)
                results.append(r)
                continue
            _settle(year, t, r['status'], r.get('why'), r.get('key'), r.get('dollars'))
            results.append({'text': t, **r})
        return results
    finally:
        llm.SPEND_WHO = None
        LOCK.unlink(missing_ok=True)

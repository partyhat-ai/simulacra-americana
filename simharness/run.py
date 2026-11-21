"""The pipeline. `python -m simharness.run <stage> --config configs/prototype-1920.json`

Stages (each writes into runs/<run id>/ and can be rerun alone):
  backbone   population + backbone fit + the unchanged-run reproduction check
  plan       sample agents and write every model request (no calls)
  ask        send pending requests through the configured backend
  refine     staged what-ifs (D33): audit the answers' reasoning, re-ask failed checks on
             agents.escalate_model, audit those
  analyze    paired effects, leakage probes, label swap, bias, audit, quotes
  publish    every what-if combination → the page's result shape + bundle
  evaluate   validation checks → validation.json (+ EVAL table rows); 1920 only
  verify     any year: the unchanged rerun reproduces every state's R/D/O (R1), plus
             Corder–Wolbrecht where it exists
  dryrun     free: backbone (if needed) → verify → plan, with brief samples and counts
             (`python -m simharness.run dryrun --year 1880`)
  all        backbone → plan → ask → analyze → publish → evaluate

Typed what-ifs (intake.py, agent.py): research, stage, whatif [--agent], and for the
research agent: trace, replay, approve, agent-eval (see docs/harness/README.md).
"""
from __future__ import annotations

import argparse
import json
import sys

from .config import ROOT, RunConfig
from .pipeline import LEGISLATURE_EV, Run
from .publish import CONF, KIND_ORDER, SOURCES, briefs_record, census_phrase, pre_interviews, sources_for

# The stages live in pipeline.py and publish.py; these names stay importable from here.
__all__ = ['CONF', 'KIND_ORDER', 'LEGISLATURE_EV', 'SOURCES', 'Run', 'briefs_record', 'census_phrase', 'main',
           'pre_interviews', 'sources_for']


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['backbone', 'plan', 'ask', 'refine', 'analyze', 'publish', 'evaluate', 'verify', 'dryrun', 'all',
                                      'id', 'research', 'whatif', 'stage', 'trace', 'replay', 'approve', 'agent-eval'])
    ap.add_argument('--config', default=str(ROOT / 'configs/prototype-1920.json'))
    ap.add_argument('--year', type=int, help='use configs/live-<year>.json (instead of --config)')
    ap.add_argument('--samples', type=int, default=1, help='dryrun: briefs to print per slice and per what-if')
    ap.add_argument('--all-cohorts', action='store_true',
                    help='dryrun: ignore the config\'s only_cohorts and arms (every group and arm; a separate run folder)')
    ap.add_argument('--text', help='whatif: the words a reader typed')
    ap.add_argument('--queue', action='store_true', help='whatif: model what the router queued as unknown')
    ap.add_argument('--limit', type=int, default=3, help='whatif --queue: at most this many texts')
    ap.add_argument('--refresh', action='store_true', help='research again even if evidence is saved')
    ap.add_argument('--key', help='research: only this what-if')
    ap.add_argument('--reextract', action='store_true', help='research: extract findings again from the saved notes (no search)')
    ap.add_argument('--agent', action='store_true', help='whatif: the research agent (agent.py) chooses the stages')
    ap.add_argument('--publish', choices=['ask', 'gate', 'never'], default='ask',
                    help='whatif --agent: hold the bundle for approve (ask), put it live if its checks pass (gate), or never')
    ap.add_argument('--dry-run', action='store_true', help='whatif --agent: no writes, interviews or publishing')
    ap.add_argument('--ceiling', type=float, help='whatif --agent, agent-eval: the most one text may spend, in dollars')
    ap.add_argument('--model', help='whatif --agent, replay, agent-eval: the agent\'s model (default: the compile model)')
    ap.add_argument('--id', help='trace, replay, approve: the trace id')
    ap.add_argument('--force', action='store_true', help='approve: even if the bundle fails its checks now')
    args = ap.parse_args(argv)
    if args.year:
        args.config = str(ROOT / f'configs/live-{args.year}.json')
    if args.stage in ('trace', 'replay', 'approve', 'agent-eval') or (args.stage == 'whatif' and args.agent):
        from . import agent, agent_eval, trace
        if args.stage == 'trace':
            out = trace.summary(trace.load(args.id)) | {'id': args.id} if args.id else \
                {'recent': trace.recent(), 'held': agent.pending()}
        elif args.stage == 'replay':
            out = agent.replay(args.id or ap.error('replay needs --id'), args.model)
        elif args.stage == 'approve':
            out = agent.approve(args.id or ap.error('approve needs --id'), args.force)
        elif args.stage == 'agent-eval':
            out = agent_eval.evaluate(RunConfig.load(args.config).election, args.limit, args.model, args.ceiling or 4.0)
        else:
            out = agent.run(args.text or ap.error('whatif --agent needs --text'), args.config, args.ceiling,
                            agent.Policy(publish=args.publish, dry_run=args.dry_run, model=args.model))
        print(json.dumps(out, indent=1, default=float))
        return
    if args.stage in ('research', 'whatif', 'stage'):
        from . import intake
        if args.stage == 'research':
            out = intake.research_config(args.config, args.refresh, args.key, args.reextract)
        elif args.stage == 'stage':
            out = intake.stage_config(args.config, args.key, args.refresh)
        elif args.queue:
            out = intake.process_queue(args.config, args.limit)
        elif args.text:
            out = intake.whatif(args.text, args.config, args.refresh)
        else:
            ap.error('whatif needs --text or --queue')
        print(json.dumps(out, indent=1, default=float))
        return
    cfg = RunConfig.load(args.config)
    if args.all_cohorts:
        cfg.agents.only_cohorts, cfg.agents.arms = None, None
    run = Run(cfg)
    stages = ['backbone', 'plan', 'ask', 'refine', 'analyze', 'evaluate', 'publish'] if args.stage == 'all' else [args.stage]
    for s in stages:
        if s == 'id':
            print(run.id)
            continue
        if s == 'dryrun':
            out = run.dryrun(args.samples)
            for b in out['briefs']:
                print(f"\n── {b['arm']} · {b['slice']} · {b['agent']} ──\n{b['user']}")
            print('\ndryrun', json.dumps({k: v for k, v in out.items() if k != 'briefs'}, indent=1, default=float))
            continue
        out = getattr(run, s)()
        print(s, json.dumps(out if not hasattr(out, 'world') else {'fit': 'ok'}, default=float)[:2000])


if __name__ == '__main__':
    sys.exit(main())

# simulacra-americana: source and docs, part 10 of 17

Generated from commit `caf86112f396` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `simharness/pipeline.py` to `simharness/run.py`. Lines are numbered as in the repository.

## `simharness/pipeline.py`

```python
    1| """The pipeline's stages other than publish (publish.py): backbone, plan, ask,
    2| refine, analyze, verify, dryrun and evaluate. Each writes into runs/<run id>/ and
    3| can be rerun alone; run.py is the command line.
    4| """
    5| from __future__ import annotations
    6| 
    7| import json
    8| import pickle
    9| import random
   10| import time
   11| from types import SimpleNamespace
   12| 
   13| import numpy as np
   14| 
   15| from . import agentlayer, aggregate, backbone, cohorts as cohorts_mod, data, evaluate, evidence, llm, paired, quotes, scenario, serialize, world
   16| from .config import RUNS, RunConfig
   17| from .geo import STATE_NAME
   18| from .publish import Publisher
   19| from .stats import logit
   20| from .whatifs import REGISTRY, apply_effects, for_year
   21| 
   22| # What analyze reports about the checks on a what-if's interviews (agent_stats; evidence.confidence reads them).
   23| STAT_KEYS = ('checked', 'misread', 'belief_checked', 'belief_failed', 'audit_checked', 'audit_failed', 'escalated', 'dropped', 'question')
   24| 
   25| 
   26| class Run(Publisher):
   27|     def __init__(self, cfg: RunConfig):
   28|         self.cfg = cfg
   29|         self.inp, self.extras = data.load(cfg)
   30|         # Compiled what-ifs' specs and every what-if's evidence are part of the instrument.
   31|         self.manifest = {**self.extras['manifest'], **scenario.manifest(cfg.what_ifs)}
   32|         self.id = cfg.run_id(self.manifest)
   33|         # Short model names in request ids; the analysis pairs on these, not on a hardcoded 'sonnet'.
   34|         self.bulk = agentlayer.SHORT.get(cfg.agents.bulk_model, cfg.agents.bulk_model)
   35|         self.check = agentlayer.SHORT.get(cfg.agents.check_model, cfg.agents.check_model)
   36|         self.escalated = agentlayer.SHORT.get(cfg.agents.escalate_model, cfg.agents.escalate_model) if cfg.agents.escalate_model else None
   37|         self.models = tuple(dict.fromkeys(m for m in (self.bulk, self.check, self.escalated) if m))
   38|         # The election's profile: names, sources and how the robot speaks of it.
   39|         self.prof = self.extras['profile']
   40|         self.year = cfg.election
   41|         n = self.prof['names']
   42|         # An unopposed year's empty line (1789 D, 1820 R) still needs a printable name.
   43|         self.cand = {0: n['R'] or 'no candidate', 1: n['D'] or 'no candidate', 2: n['O']}
   44|         self.dir = RUNS / self.id
   45|         self.dir.mkdir(parents=True, exist_ok=True)
   46|         (self.dir / 'config.json').write_text(json.dumps({'run_id': self.id, 'config': cfg.to_dict(),
   47|                                                           'data': self.manifest}, indent=2))
   48| 
   49|     # ── backbone ──
   50|     def backbone(self):
   51|         if self.extras.get('base_inp') is not None:
   52|             # A carried-forward year: fit the base year, then recalibrate to this year's returns.
   53|             base = backbone.fit(self.extras['base_inp'], self.cfg.draws, self.cfg.seed)
   54|             fit = backbone.carry_forward(base, self.inp, self.year, self.cfg.seed)
   55|         elif self.year != 1920:
   56|             # Every other year: calibrated exactly to its own returns, group splits from priors (backbone.general_fit).
   57|             fit = backbone.general_fit(self.inp, self.year, self.cfg.draws, self.cfg.seed)
   58|         else:
   59|             fit = backbone.fit(self.inp, self.cfg.draws, self.cfg.seed)
   60|         with open(self.dir / 'fit.pkl', 'wb') as f:
   61|             pickle.dump(fit, f)
   62|         return fit
   63| 
   64|     def fit(self):
   65|         p = self.dir / 'fit.pkl'
   66|         if not p.exists():
   67|             return self.backbone()
   68|         with open(p, 'rb') as f:
   69|             return pickle.load(f)
   70| 
   71|     def state_index(self, fit):
   72|         states = fit.diagnostics['states']
   73|         return states, np.array([states.index(s) for s in fit.cells.state])
   74| 
   75|     # ── agents ──
   76|     def plan(self):
   77|         fit = self.fit()
   78|         cells = fit.cells
   79|         cohorts, cell_to = cohorts_mod.build(cells, cap=self.cfg.agents.max_cohorts, year=self.year)
   80|         agents, reqs = agentlayer.build_requests(self.cfg, cohorts, self.extras, self.inp, REGISTRY)
   81|         out = self.dir / 'agents'
   82|         out.mkdir(exist_ok=True)
   83|         (out / 'cohorts.json').write_text(json.dumps({'cohorts': cohorts, 'cell_to': {int(k): v for k, v in cell_to.items()}}, indent=1))
   84|         (out / 'agents.json').write_text(json.dumps(agents, indent=1, default=str))
   85|         with open(out / 'all_requests.jsonl', 'w') as f:
   86|             for r in reqs:
   87|                 f.write(json.dumps(r) + '\n')
   88|         counts = {}
   89|         for r in reqs:
   90|             k = (r['meta']['arm'].split(':')[0], r['model'])
   91|             counts[str(k)] = counts.get(str(k), 0) + 1
   92|         ag = self.cfg.agents
   93|         return {'agents': len(agents), 'requests': len(reqs), 'by_arm_model': counts, 'cohorts': len(cohorts),
   94|                 'cohort_keys': sorted(cohorts, key=lambda k: -cohorts[k].get('adults', 0))[:12],
   95|                 'estimate': llm.estimate(reqs, ag.max_tokens, ag.backend == 'anthropic-batch')}
   96| 
   97|     def requests(self):
   98|         return [json.loads(l) for l in (self.dir / 'agents/all_requests.jsonl').read_text().splitlines() if l.strip()]
   99| 
  100|     def ask(self):
  101|         ag = self.cfg.agents
  102|         be = llm.backend(ag.backend, self.dir / 'agents/transcript', ag.effort, ag.max_tokens)
  103|         reqs = self.requests()
  104|         merged = None
  105|         if self.cfg.agents.backend == 'transcript':
  106|             merged = llm.merge_answers(self.dir / 'agents/transcript', reqs)
  107|             (self.dir / 'agents/transcript/merge_report.json').write_text(json.dumps(merged, indent=1))
  108|         path = self.dir / 'agents/answers.jsonl'
  109|         have = set()
  110|         if path.exists():
  111|             have = {json.loads(l)['id'] for l in path.read_text().splitlines() if l.strip() and json.loads(l).get('ok')}
  112|         todo = [r for r in reqs if r['id'] not in have]
  113|         live = ag.backend in llm.AnswerCache.LIVE
  114|         cache = llm.AnswerCache(RUNS) if live else None
  115|         reused = [c for c in (cache.get(r) for r in todo) if c] if cache else []
  116|         todo = [r for r in todo if r['id'] not in {c['id'] for c in reused}]
  117|         batch = ag.backend == 'anthropic-batch'
  118|         # Thinking (every model but Haiku) multiplies an answer's output.
  119|         est = llm.estimate(todo, ag.max_tokens, batch,
  120|                            typical_out=600 if 'haiku' in ag.bulk_model else int(600 * {'low': 1.5, 'medium': 3, 'high': 5}.get(ag.effort, 3)))
  121|         print(f"estimate: {est['requests']} requests, ~${est['typical']} typical, ${est['worst']} worst case"
  122|               f" ({len(reused)} reused from identical earlier requests)", flush=True)
  123|         t0 = time.time()
  124|         got = be.run(todo) if todo else []
  125|         spent = sum(llm.cost(g['model'], g.get('usage') or {}, batch) for g in got)
  126|         if live:
  127|             llm.record_spend('ask', spent, self.id)
  128|             by_id = {r['id']: r for r in todo}
  129|             for g in got:
  130|                 cache.put(by_id[g['id']], g)
  131|         with open(path, 'a') as f:
  132|             for g in got + reused:
  133|                 f.write(json.dumps(g) + '\n')
  134|         out = {'sent': len(todo), 'reused': len(reused), 'seconds': round(time.time() - t0, 1), 'dollars': round(spent, 4),
  135|                'answered': sum(1 for g in got if g.get('ok')), 'failed': sum(1 for g in got if not g.get('ok')),
  136|                'merge': None if merged is None else {'merged': merged['merged'], 'rejected': len(merged['rejected']), 'missing': len(merged['missing'])}}
  137|         return out
  138| 
  139|     def answers(self) -> dict:
  140|         path = self.dir / 'agents/answers.jsonl'
  141|         out = {}
  142|         if path.exists():
  143|             for l in path.read_text().splitlines():
  144|                 if l.strip():
  145|                     g = json.loads(l)
  146|                     if g.get('ok'):
  147|                         out[g['id']] = g
  148|         return out
  149| 
  150|     # ── refine (D33): audit the reasoning, re-ask failures on a stronger model ──
  151|     def audit_verdicts(self) -> dict:
  152|         p = self.dir / 'audit.json'
  153|         return json.loads(p.read_text()) if p.exists() else {}
  154| 
  155|     @staticmethod
  156|     def failed_check(req: dict, data: dict, audit: dict) -> str | None:
  157|         """Why an answered counterfactual is left out, or None: it took the news to be about
  158|         the other candidate (p5), it got the belief check wrong (p6), or its reasoning
  159|         contradicts the change (the audit)."""
  160|         m = req['meta']
  161|         if m.get('news_check') and data.get('news_about') != m['news_check']['expected']:
  162|             return 'misread'
  163|         if m.get('world_check') and data.get('world_check') != m['world_check']['expected']:
  164|             return 'disbelieved'
  165|         if (audit.get(req['id']) or {}).get('verdict') == 'contradicts':
  166|             return 'off-premise'
  167|         return None
  168| 
  169|     def audit(self) -> dict:
  170|         """One call per staged what-if: each counterfactual answer's reason and quote, without
  171|         its vote, judged on whether it treats the change as true (world.AUDIT_SYSTEM)."""
  172|         rc = self.cfg.research
  173|         if not rc.audit_model:
  174|             return {'audited': 0, 'dollars': 0.0}
  175|         reqs, ans, done = self.requests(), self.answers(), self.audit_verdicts()
  176|         by_wk = {}
  177|         for r in reqs:
  178|             if r['meta']['kind'] != 'cf' or r['id'] not in ans or r['id'] in done:
  179|                 continue
  180|             wk = r['meta']['change']['what_if']
  181|             spec = REGISTRY.get(wk) or {}
  182|             if spec.get('generated') and spec.get('mode') == 'agents' and spec.get('world'):
  183|                 by_wk.setdefault(wk, []).append(r['id'])
  184|         cache, spent, n = llm.AnswerCache(RUNS), 0.0, 0
  185|         for wk, ids in by_wk.items():
  186|             rows = [{'n': i + 1, 'reason': ans[rid]['data'].get('reason', ''), 'quote': ans[rid]['data'].get('quote', '')}
  187|                     for i, rid in enumerate(ids)]
  188|             req = world.audit_request(REGISTRY[wk], rows, rc.audit_model, rc.audit_effort)
  189|             if rc.fast and llm.fast_ok(req['model']):
  190|                 req['speed'] = 'fast'
  191|             got = cache.get(req)
  192|             if not got:
  193|                 got = llm.AnthropicBackend(effort=rc.audit_effort, max_tokens=rc.pass_max_tokens)._one(req)
  194|                 d = llm.cost(req['model'], got.get('usage') or {})
  195|                 spent += d
  196|                 llm.record_spend('audit', d, self.id, wk)
  197|                 cache.put(req, got | {'backend': 'anthropic'})
  198|             if not got.get('ok'):
  199|                 print(f'audit {wk}: {got.get("error")} (its answers stay unaudited)', flush=True)
  200|                 continue
  201|             verdicts = {v['n']: v for v in got['data'].get('verdicts', [])}
  202|             for i, rid in enumerate(ids):
  203|                 v = verdicts.get(i + 1) or {'verdict': 'unclear', 'why': 'not returned'}
  204|                 done[rid] = {'verdict': v['verdict'], 'why': v['why'], 'model': rc.audit_model}
  205|                 n += 1
  206|         (self.dir / 'audit.json').write_text(json.dumps(done, indent=1))
  207|         return {'audited': n, 'dollars': round(spent, 4)}
  208| 
  209|     def escalate(self) -> int:
  210|         """Plan control + counterfactual again, on escalate_model, for every bulk-model
  211|         counterfactual that failed a check. Same brief, same person; only the model
  212|         changes, and the pair is compared within itself as always. Returns the count."""
  213|         ag = self.cfg.agents
  214|         if not ag.escalate_model or ag.escalate_model == ag.bulk_model:
  215|             return 0
  216|         reqs, ans, audit = self.requests(), self.answers(), self.audit_verdicts()
  217|         by_id = {r['id']: r for r in reqs}
  218|         new = []
  219|         for r in reqs:
  220|             if len(new) >= ag.escalate_max:
  221|                 break
  222|             if r['meta']['kind'] != 'cf' or r['model'] != ag.bulk_model or r['id'] not in ans:
  223|                 continue
  224|             if not self.failed_check(r, ans[r['id']]['data'], audit):
  225|                 continue
  226|             ctl = by_id.get(f'control|{r["meta"]["agent"]}|{self.bulk}')
  227|             if not ctl:
  228|                 continue
  229|             for base in (ctl, r):
  230|                 nid = base['id'].rsplit('|', 1)[0] + f'|{self.escalated}'
  231|                 if nid not in by_id:
  232|                     by_id[nid] = {**base, 'id': nid, 'model': ag.escalate_model, 'meta': {**base['meta'], 'escalated': True},
  233|                                   **({'speed': 'fast'} if ag.fast and llm.fast_ok(ag.escalate_model) else {})}
  234|                     new.append(by_id[nid])
  235|         if new:
  236|             with open(self.dir / 'agents/all_requests.jsonl', 'a') as f:
  237|                 for r in new:
  238|                     f.write(json.dumps(r) + '\n')
  239|         return len(new)
  240| 
  241|     def refine(self) -> dict:
  242|         """audit → escalate → ask the escalations → audit them. A step that stops is skipped, not
  243|         fatal: unaudited answers stay in, unanswered escalations are left out."""
  244|         out, spent = {}, 0.0
  245| 
  246|         def step(name, fn):
  247|             nonlocal spent
  248|             try:
  249|                 out[name] = fn()
  250|                 spent += out[name]['dollars']
  251|             except SystemExit as e:
  252|                 out[name] = {'skipped': str(e)}
  253|                 print(f'refine: {name} skipped: {e}', flush=True)
  254|                 return False
  255|             return True
  256| 
  257|         step('audit', self.audit)
  258|         out['escalated'] = self.escalate()
  259|         if out['escalated'] and step('ask', self.ask):
  260|             step('audit2', self.audit)
  261|         out['dollars'] = round(spent, 4)
  262|         return out
  263| 
  264|     # ── analysis ──
  265|     def analyze(self):
  266|         fit = self.fit()
  267|         reqs = {r['id']: r for r in self.requests()}
  268|         ans = self.answers()
  269|         agents = {a['id']: a for a in json.loads((self.dir / 'agents/agents.json').read_text())}
  270|         co = json.loads((self.dir / 'agents/cohorts.json').read_text())
  271|         cohorts, cell_to = co['cohorts'], {int(k): v for k, v in co['cell_to'].items()}
  272|         rng = np.random.default_rng(self.cfg.seed + 11)
  273|         pyrng = random.Random(self.cfg.seed + 11)
  274| 
  275|         def norm(rid):
  276|             if rid not in ans:
  277|                 return None
  278|             lab = reqs[rid]['meta']['label_of']
  279|             row = paired.normalize(ans[rid]['data'], {v: k for k, v in lab.items()})
  280|             if row:
  281|                 d = ans[rid]['data']
  282|                 row.update({'reason': d.get('reason', ''), 'quote': d.get('quote', ''), 'sources_used': d.get('sources_used', []),
  283|                             'agent': reqs[rid]['meta']['agent'], 'model': ans[rid]['model']})
  284|             return row
  285| 
  286|         # Backbone cohort shares in the point draw's median over draws
  287|         w = fit.world
  288|         v = w.adults * w.can * w.t
  289|         backbone_r2, backbone_turn, backbone_o = {}, {}, {}
  290|         for k in cohorts:
  291|             idx = [i for i, kk in cell_to.items() if kk == k]
  292|             vv = v[:, idx]
  293|             R = (vv * w.share[:, idx, 0]).sum(axis=1)
  294|             Dm = (vv * w.share[:, idx, 1]).sum(axis=1)
  295|             # per legally eligible adult (what an agent's p_vote means), exclusion included
  296|             elig = (w.adults[:, idx] * (w.can[:, idx] + w.barred_by['excluded'][:, idx])).sum(axis=1)
  297|             backbone_r2[k] = float(np.median(R / np.maximum(R + Dm, 1e-9)))
  298|             backbone_turn[k] = float(np.median(vv.sum(axis=1) / np.maximum(elig, 1e-9)))
  299|             backbone_o[k] = float(np.median((vv * w.share[:, idx, 2]).sum(axis=1) / np.maximum(vv.sum(axis=1), 1e-9)))
  300| 
  301|         # L1 recall probe (the winner is the historical one: R in 1920, D in 1960)
  302|         states_, sidx_ = self.state_index(fit)
  303|         won = int(np.argmax(aggregate.outcome(aggregate.by_state(fit.world, sidx_, len(states_))[:1],
  304|                                               self.inp.ev.reindex(states_).fillna(0).to_numpy(), self._fixed_ev(states_), self._split_ev(states_), o_single=self._o_single(states_))['ev'][0]))
  305|         probes = []
  306|         for rid, r in reqs.items():
  307|             if r['meta']['kind'] != 'probe' or rid not in ans:
  308|                 continue
  309|             d = ans[rid]['data']
  310|             lab = r['meta']['label_of']
  311|             cands = {k: str(v).lower() for k, v in (d.get('candidates') or {}).items()}
  312|             probes.append({
  313|                 'cohort': r['meta']['cohort'],
  314|                 'year': str(d.get('year', '')).strip().startswith(str(self.year)),
  315|                 'names': all(self.cand[i].lower() in cands.get(lab[p], '') for i, p in enumerate('RD') if p in lab),
  316|                 'winner': self.cand[won].lower() in str(d.get('winner_name', '')).lower() or d.get('winner_label') == lab.get('RDO'[won]),
  317|             })
  318|         by_cohort = {}
  319|         for p in probes:
  320|             by_cohort.setdefault(p['cohort'], []).append(p)
  321|         exposed = {k for k, ps in by_cohort.items() if np.mean([p['winner'] for p in ps]) > 0.5}
  322|         l1 = {'n': len(probes),
  323|               'year_rate': float(np.mean([p['year'] for p in probes])) if probes else None,
  324|               'names_rate': float(np.mean([p['names'] for p in probes])) if probes else None,
  325|               'winner_rate': float(np.mean([p['winner'] for p in probes])) if probes else None,
  326|               'exposed_cohorts': sorted(exposed),
  327|               'by_cohort': {k: {'n': len(ps), 'winner_rate': float(np.mean([p['winner'] for p in ps]))} for k, ps in by_cohort.items()}}
  328|         nationally_exposed = bool(l1['winner_rate'] is not None and l1['winner_rate'] > 0.5)
  329| 
  330|         # L2 label swap
  331|         swaps = []
  332|         for rid, r in reqs.items():
  333|             if r['meta']['kind'] != 'swap' or rid not in ans:
  334|                 continue
  335|             ctl = norm(f'control|{r["meta"]["agent"]}|{self.bulk}')
  336|             if not ctl or ctl['choice'] not in ('R', 'D'):
  337|                 continue
  338|             chosen = ans[rid]['data'].get('choice')
  339|             plat = {x['label']: x['platform_of'] for x in r['meta']['displayed']}
  340|             if chosen not in plat:
  341|                 continue
  342|             swaps.append({'follows_platform': plat[chosen] == ctl['choice'],
  343|                           'follows_label': chosen == r['meta']['label_of'][ctl['choice']]})
  344|         l2 = {'n': len(swaps), 'label_rate': float(np.mean([s['follows_label'] for s in swaps])) if swaps else None,
  345|               'platform_rate': float(np.mean([s['follows_platform'] for s in swaps])) if swaps else None}
  346| 
  347|         # Paired effects per what-if (agent-mode what-ifs apply them; others are cross-checks)
  348|         effects, pairs_out, kept, dropped = {}, {}, {}, {}
  349|         audit = self.audit_verdicts()
  350|         for wk in self.cfg.what_ifs:
  351|             pairs, checks, beliefs, audits, escalated = {}, [], [], [], 0
  352|             kept_wk, dropped_wk = {}, {}
  353|             for aid, a in agents.items():
  354|                 if a['group'] == 'foreign_white_alien' and REGISTRY[wk]['mode'] == 'backbone':
  355|                     continue  # planned in error for p1 (brief contradicted itself); excluded, see EVAL.md
  356|                 for model in self.models:
  357|                     fid = f'cf:{wk}|{aid}|{model}'
  358|                     c, f = norm(f'control|{aid}|{model}'), norm(fid)
  359|                     if not (c and f):
  360|                         continue
  361|                     m, data = reqs[fid]['meta'], ans[fid]['data']
  362|                     # p5: took the news to be about the other candidate. p6 (D33): got the belief
  363|                     # check wrong, or reasoned from the world as it was (the audit). Each answered a
  364|                     # different question than the one asked: left out, and counted.
  365|                     if m.get('news_check'):
  366|                         got = data.get('news_about')
  367|                         checks.append({'agent': aid, 'expected': m['news_check']['expected'], 'got': got,
  368|                                        'ok': got == m['news_check']['expected']})
  369|                     if m.get('world_check'):
  370|                         got = data.get('world_check')
  371|                         beliefs.append({'agent': aid, 'model': model, 'got': got, 'ok': got == m['world_check']['expected']})
  372|                     if fid in audit:
  373|                         audits.append({'agent': aid, 'model': model, 'verdict': audit[fid]['verdict'], 'why': audit[fid]['why']})
  374|                     why = self.failed_check(reqs[fid], data, audit)
  375|                     if why:
  376|                         dropped_wk.setdefault(aid, why)
  377|                         continue
  378|                     pairs.setdefault(a['cohort'], []).append((c, f, a['paraphrase'], model))
  379|                     kept_wk[aid] = model
  380|                     escalated += bool(m.get('escalated'))
  381|             kept[wk] = kept_wk
  382|             dropped[wk] = {aid: why for aid, why in dropped_wk.items() if aid not in kept_wk}
  383|             misread = {'checked': len(checks), 'misread': sum(not x['ok'] for x in checks), 'rows': checks,
  384|                        'belief_checked': len(beliefs), 'belief_failed': sum(not x['ok'] for x in beliefs),
  385|                        'audit_checked': len(audits), 'audit_failed': sum(x['verdict'] == 'contradicts' for x in audits),
  386|                        'escalated': escalated, 'dropped': len(dropped[wk]),
  387|                        'question': next((reqs[f'cf:{wk}|{x["agent"]}|{x["model"]}']['meta']['world_check']['question']
  388|                                          for x in beliefs), None),
  389|                        'belief_rows': beliefs, 'audit_rows': audits}
  390|             if not pairs and (checks or beliefs or audits):
  391|                 # Everyone misread the change: nothing was measured, so nothing moves.
  392|                 zero = {k: {'mean': 0.0, 'lo': 0.0, 'hi': 0.0} for k in ('dt', 'dr', 'do')}
  393|                 effects[wk] = {'cohorts': {}, 'regions': {}, 'national': zero, 'national_bias': 0.0, 'by_paraphrase': {},
  394|                                'by_model': {}, 'manipulation': misread, 'blended': False,
  395|                                'agreement': {'verdict': 'untested', 'detail': 'Every interview misread the change.', 'measures': []},
  396|                                'agent_stats': {'n': 0, 'measure': 'dr', 'spans_zero': True, 'paraphrase_flip': False,
  397|                                                'exposed': nationally_exposed, **{k: misread[k] for k in STAT_KEYS}}}
  398|                 pairs_out[wk] = {}
  399|                 continue
  400|             if not pairs:
  401|                 continue
  402|             region_of = {k: cohorts[k]['region'] for k in pairs}
  403|             generated = bool(REGISTRY[wk].get('generated'))
  404|             eff = paired.effects(pairs, backbone_r2, region_of, 200, rng, exposed=exposed if not nationally_exposed else set(pairs),
  405|                                  weights={k: cohorts[k]['adults'] for k in pairs}, floor=generated)
  406|             borrowed = self._borrow(eff, cohorts, REGISTRY[wk], rng) if generated and REGISTRY[wk]['mode'] == 'agents' else []
  407|             # A3: paraphrase and model spread of the national two-party effect
  408|             by_para, by_model = {}, {}
  409|             for k, ps in pairs.items():
  410|                 for c, f, p, m in ps:
  411|                     by_para.setdefault(p, []).append((c, f))
  412|                     by_model.setdefault(m, []).append((c, f))
  413|             def nat(ps):
  414|                 return paired.diff(paired.cohort_stats([x[1] for x in ps]), paired.cohort_stats([x[0] for x in ps]))
  415|             eff['by_paraphrase'] = {str(p): nat(ps) for p, ps in by_para.items()}
  416|             eff['by_model'] = {m: nat(ps) for m, ps in by_model.items()}
  417|             # the Sonnet/Opus comparison uses only agents asked on both
  418|             both = [(c, f, m) for ps in pairs.values() for c, f, p, m in ps]
  419|             ids_opus = {c['agent'] for c, f, m in both if m == self.check}
  420|             shared = {m: [(c, f) for c, f, mm in both if mm == m and c['agent'] in ids_opus] for m in self.models}
  421|             eff['shared_subsample'] = {m: nat(ps) for m, ps in shared.items() if ps}
  422|             # History: does the record agree with the interviews? For compiled
  423|             # (exploratory) what-ifs the evidence is also a prior on each cohort.
  424|             spec, ev = REGISTRY[wk], scenario.load_evidence(wk)
  425|             wts = {k: cohorts[k]['adults'] for k in pairs}
  426|             tot = sum(wts.values()) or 1.0
  427|             nat_base = {m: sum(b[k] * wts[k] for k in pairs) / tot
  428|                         for m, b in (('turnout', backbone_turn), ('r2', backbone_r2), ('o', backbone_o))}
  429|             mkey = 'do' if spec['kind'] == 'candidate' else 'dr'
  430|             signs = {float(np.sign(v[mkey])) for v in eff['by_paraphrase'].values() if abs(v[mkey]) > 0.02}
  431|             eff['agent_stats'] = {'n': sum(len(ps) for ps in pairs.values()), 'measure': mkey,
  432|                                   'spans_zero': bool(eff['national'][mkey]['lo'] < 0 < eff['national'][mkey]['hi']),
  433|                                   'paraphrase_flip': len(signs) > 1, 'exposed': nationally_exposed,
  434|                                   'borrowed': len(borrowed), **{k: misread[k] for k in STAT_KEYS}}
  435|             eff['manipulation'] = misread
  436|             eff['agreement'] = evidence.agreement(ev, eff['national'], nat_base, spec['kind'])
  437|             if spec.get('withdraws'):
  438|                 from .whatifs import transfer
  439|                 eff['transfer'] = transfer([(c, f) for ps in pairs.values() for c, f, _, _ in ps], 200, rng)
  440|             eff['blended'] = False
  441|             if ev and spec.get('evidence_mode') == 'blend':
  442|                 eff['cohorts'] = {k: evidence.blend(c, evidence.prior(ev, cohorts[k], {'turnout': backbone_turn[k], 'r2': backbone_r2[k],
  443|                                                                                         'o': backbone_o[k]}))
  444|                                   for k, c in eff['cohorts'].items()}
  445|                 eff['blended'] = any(c['evidence_blend'] for c in eff['cohorts'].values())
  446|             effects[wk] = eff
  447|             pairs_out[wk] = {k: [{'control': c, 'cf': f, 'paraphrase': p, 'model': m} for c, f, p, m in ps] for k, ps in pairs.items()}
  448| 
  449|         # A2 variance compression (control, sonnet)
  450|         a2 = []
  451|         for k in cohorts:
  452|             rows = [norm(f'control|{aid}|{self.bulk}') for aid, a in agents.items() if a['cohort'] == k]
  453|             rows = [r for r in rows if r and r['p_vote'] > 0 and not np.isnan(r['R'])]
  454|             if len(rows) < 2:
  455|                 continue
  456|             ch = [r['choice'] for r in rows]
  457|             top = max(ch.count(x) for x in set(ch)) / len(ch)
  458|             r2 = [r['R'] / max(r['R'] + r['D'], 1e-9) for r in rows]
  459|             a2.append({'cohort': k, 'n': len(rows), 'sd_R2': float(np.std(r2)), 'modal_share': top,
  460|                        'backbone_r2': backbone_r2[k], 'homogenized': bool(top >= 0.9 and 0.2 <= backbone_r2[k] <= 0.8)})
  461|         eligible_a2 = [x for x in a2 if 0.2 <= x['backbone_r2'] <= 0.8]
  462|         a2s = {'cohorts': a2, 'homogenization_index': float(np.mean([x['homogenized'] for x in eligible_a2])) if eligible_a2 else None,
  463|                'eligible_cohorts': len(eligible_a2)}
  464| 
  465|         # A4 stereotype audit
  466|         reasons = [norm(rid) for rid in reqs if rid.startswith(('control|', 'cf:')) and rid in ans]
  467|         a4 = quotes.audit([r for r in reasons if r], 0.2, pyrng)
  468| 
  469|         # A1 cohort bias and TVD (control, sonnet)
  470|         a1 = []
  471|         for k in cohorts:
  472|             rows = [norm(f'control|{aid}|{self.bulk}') for aid, a in agents.items() if a['cohort'] == k]
  473|             rows = [r for r in rows if r]
  474|             if not rows:
  475|                 continue
  476|             st = paired.cohort_stats(rows)
  477|             ch = [r['choice'] for r in rows]
  478|             agent_dist = [ch.count('R'), ch.count('D'), ch.count('O'), ch.count('home') + ch.count('barred')]
  479|             t = backbone_turn[k]
  480|             bb = backbone_r2[k]
  481|             bb_dist = [t * bb, t * (1 - bb), 0.0, 1 - t]
  482|             a1.append({'cohort': k, 'label': cohorts[k]['label'], 'n': len(rows),
  483|                        'agent_turnout': st['turnout'], 'backbone_turnout': t,
  484|                        'agent_r2': st['R2'], 'backbone_r2': bb,
  485|                        'bias_logit': float(logit(st['R2']) - logit(bb)) if not np.isnan(st['R2']) else None,
  486|                        'tvd': float(0.5 * np.abs(np.array(agent_dist) / max(sum(agent_dist), 1) - np.array(bb_dist) / sum(bb_dist)).sum()),
  487|                        'exposed': k in exposed})
  488| 
  489|         result = {'l1': l1, 'l2': l2, 'a1': a1, 'a2': a2s, 'a4': a4, 'nationally_exposed': nationally_exposed,
  490|                   'effects': {wk: {'national': e['national'], 'national_bias': e['national_bias'],
  491|                                    'by_paraphrase': e['by_paraphrase'], 'by_model': e['by_model'],
  492|                                    'shared_subsample': e.get('shared_subsample'),
  493|                                    'agent_stats': e.get('agent_stats'), 'agreement': e.get('agreement'), 'blended': e.get('blended'),
  494|                                    'manipulation': e.get('manipulation'),
  495|                                    'transfer': {'point': e['transfer']['point'], 'n': e['transfer']['n']} if e.get('transfer') else None,
  496|                                    'cohorts': {k: {kk: vv for kk, vv in c.items() if kk != 'draws'} for k, c in e['cohorts'].items()}}
  497|                               for wk, e in effects.items()}}
  498|         (self.dir / 'analysis.json').write_text(json.dumps(result, indent=1, default=float))
  499|         with open(self.dir / 'effects.pkl', 'wb') as f:
  500|             pickle.dump({'effects': effects, 'pairs': pairs_out, 'exposed': exposed,
  501|                          'nationally_exposed': nationally_exposed, 'kept': kept, 'dropped': dropped}, f)
  502|         return result
  503| 
  504|     def _borrow(self, eff: dict, cohorts: dict, spec: dict, rng) -> list[str]:
  505|         """D33: a cohort the change reaches but nobody in it was interviewed (only_cohorts
  506|         left it out) used to get no effect at all, with no uncertainty: the 1916 West, where
  507|         the election was decided. It now borrows the effect of the interviewed cohorts of its
  508|         own sex and group (else its group, else everyone), adult-weighted, per draw, plus
  509|         between-cohort noise: the spread of the interviewed cohorts' own effects, at least
  510|         0.15 logit. The evidence prior (evidence.blend) then applies to it like any cohort."""
  511|         have = eff['cohorts']
  512|         if not have:
  513|             return []
  514|         reach = spec.get('reach') or {}
  515|         tau = {key: max(0.15, float(np.std([c[key] for c in have.values()]))) if len(have) > 1 else 0.3
  516|                for key in ('dt', 'dr', 'do')}
  517|         interviewable = agentlayer.groups_for(self.year)['interview']
  518|         out = []
  519|         for k, c in cohorts.items():
  520|             if k in have or c['group'] == 'foreign_white_alien' or c['group'] not in interviewable:
  521|                 continue
  522|             regions = set(c.get('regions') or [c.get('region')])
  523|             if (reach.get('sex') and c['sex'] not in reach['sex']) or (reach.get('group') and c['group'] not in reach['group']) \
  524|                     or (reach.get('region') and not regions & set(reach['region'])):
  525|                 continue
  526|             for pick, what in ((lambda x: x['sex'] == c['sex'] and x['group'] == c['group'], 'its own sex and group'),
  527|                                (lambda x: x['group'] == c['group'], 'its group'), (lambda x: True, 'everyone interviewed')):
  528|                 src = [kk for kk in have if not have[kk].get('borrowed') and pick(cohorts[kk])]
  529|                 if src:
  530|                     break
  531|             w = np.array([cohorts[kk]['adults'] for kk in src], float)
  532|             draws = {key: np.average([have[kk]['draws'][key] for kk in src], axis=0, weights=w) for key in ('dt', 'dr', 'do')}
  533|             draws = {key: d + rng.normal(0.0, tau[key], len(d)) for key, d in draws.items()}
  534|             have[k] = {'control': None, 'counterfactual': None, 'n': 0, 'bias': 0.0, 'bias_used': 0.0, 'weight': 0.0,
  535|                        'exposed': False, 'borrowed': what, **{key: float(np.mean(d)) for key, d in draws.items()}, 'draws': draws}
  536|             out.append(k)
  537|         return out
  538| 
  539|     def uncertainty_budget(self, what_if: str, draws: int = 200) -> dict:
  540|         """Spread of the what-if's national R two-party share and Harding EV:
  541|         full, with population noise off, and with only the agent layer varying
  542|         (one backbone draw, all effect draws)."""
  543|         fit = self.fit()
  544|         states, sidx = self.state_index(fit)
  545|         ev = self.inp.ev.reindex(states).fillna(0).to_numpy()
  546|         spec = REGISTRY[what_if]
  547|         eff = pickle.load(open(self.dir / 'effects.pkl', 'rb')) if (self.dir / 'effects.pkl').exists() else None
  548|         co = json.loads((self.dir / 'agents/cohorts.json').read_text()) if (self.dir / 'agents/cohorts.json').exists() else None
  549|         cell_to = [co['cell_to'][str(i)] for i in range(len(fit.cells))] if co else []
  550| 
  551|         def measure(f, world):
  552|             if spec['mode'] == 'backbone':
  553|                 world = spec['apply'](f, world, self.inp)
  554|             elif eff and what_if in eff['effects']:
  555|                 world = apply_effects(f, world, cell_to, eff['effects'][what_if]['cohorts'])
  556|             else:
  557|                 return None
  558|             sv = aggregate.by_state(world, sidx, len(states))
  559|             out = aggregate.outcome(sv, ev, self._fixed_ev(states), self._split_ev(states), o_single=self._o_single(states))
  560|             nat = sv.sum(axis=1)
  561|             return {'r2_sd': float(np.std(nat[:, 0] / (nat[:, 0] + nat[:, 1])) * 100), 'ev_sd': float(np.std(out['ev'][:, 0]))}
  562| 
  563|         full = measure(fit, fit.world)
  564|         zero = {k: 0.0 for k in backbone.GROUPS}
  565|         if self.year == 1920 or self.extras.get('base_inp') is not None:
  566|             no_pop = backbone.fit(self.extras.get('base_inp') or self.inp, draws, self.cfg.seed, pop_cv=zero)
  567|             if self.extras.get('base_inp') is not None:
  568|                 no_pop = backbone.carry_forward(no_pop, self.inp, self.year, self.cfg.seed)
  569|         else:
  570|             no_pop = backbone.general_fit(self.inp, self.year, draws, self.cfg.seed, pop_cv=zero)
  571|         params_only = measure(no_pop, no_pop.world)
  572|         agents_only = None
  573|         if spec['mode'] == 'agents' and eff and what_if in eff['effects']:
  574|             w = fit.world
  575|             one = aggregate.World(adults=np.repeat(w.adults[:1], draws, 0), can=np.repeat(w.can[:1], draws, 0),
  576|                                   t=np.repeat(w.t[:1], draws, 0), share=np.repeat(w.share[:1], draws, 0),
  577|                                   barred_by={k: np.repeat(v[:1], draws, 0) for k, v in w.barred_by.items()})
  578|             agents_only = measure(fit, one)
  579|         return {'what_if': what_if, 'full': full, 'backbone_params_only': params_only, 'agents_only': agents_only,
  580|                 'note': 'SD in points of the national R two-party share and in Harding EV. Population share ≈ full − params-only (variances).'}
  581| 
  582|     # ── verify (any year) ──
  583|     def verify(self):
  584|         """The unchanged rerun reproduces every state's certified votes (R1), and,
  585|         for a carried-forward year, the held-out women's turnout benchmark."""
  586|         fit = self.fit()
  587|         states, sidx = self.state_index(fit)
  588|         sv = aggregate.by_state(fit.world, sidx, len(states))
  589|         # Certified R/D/O per state; a state missing from the returns, or whose legislature
  590|         # chose the electors (no popular vote), is checked against zero.
  591|         no_pop = set(getattr(self.inp, 'no_popular', None) or ()) | set(fit.diagnostics.get('no_popular') or ())
  592|         cert = np.array(self.inp.returns.reindex(states)[self._ret_cols()].fillna(0), dtype=float)
  593|         cert[[s in no_pop for s in states]] = 0.0
  594|         out = aggregate.outcome(sv, self.inp.ev.reindex(states).fillna(0).to_numpy(), self._fixed_ev(states), self._split_ev(states), o_single=self._o_single(states))
  595|         err = np.abs(sv - cert[None, :, :])
  596|         worst = float(err.max()) if err.size else 0.0
  597|         by_state = err.max(axis=(0, 2))
  598|         res = {'year': self.year, 'R1_worst_vote_error': worst, 'R1_pass': bool(worst <= 0.5), 'R1_states': len(states),
  599|                'R1_no_popular': sorted(no_pop & set(states)),
  600|                'R1_worst_states': [{'state': s, 'error': round(float(e), 3)}
  601|                                    for s, e in sorted(zip(states, by_state), key=lambda x: -x[1])[:3]],
  602|                'ev_by_draw': sorted({tuple(int(x) for x in e) for e in out['ev']})[:3]}
  603|         d = fit.diagnostics
  604|         if d.get('method') == 'general_fit':
  605|             # general_fit's edge cases and the era priors it used (backbone.py, notes/B.md).
  606|             flags = {k: d[k] for k in ('missing_returns', 'dropped_cell_states', 'synthetic_cell_states', 'legal_rules_contradicted',
  607|                                        'T_column_mismatch', 'other_majority', 'black_south_bound_on') if d.get(k)}
  608|             zp = {p: v for p, v in (d.get('zero_party') or {}).items() if v}
  609|             if zp:
  610|                 flags['zero_party'] = zp
  611|             scaled = {s: round(float(x), 3) for s, x in (d.get('adults_scaled_share') or {}).items() if x}
  612|             if scaled:
  613|                 flags['adults_scaled_share'] = scaled
  614|             res['fit_flags'] = flags
  615|             res['priors'] = d.get('priors')
  616|         from . import benchmarks  # validation stage: the held-out Corder–Wolbrecht turnout
  617|         cw = benchmarks.corder_wolbrecht_any_year()
  618|         cw = cw[(cw.year == self.year) & cw.state.isin(states)].set_index('state')
  619|         if len(cw) and not backbone.cw_held_out(self.year, d.get('method')):
  620|             res['corder_wolbrecht_skipped'] = ('not held out: this year\'s women\'s-turnout prior draws on '
  621|                                                f'Corder–Wolbrecht knots {backbone.CW_PRIOR_KNOTS} (DISCLOSURES A11)')
  622|         elif len(cw):
  623|             # Corder–Wolbrecht's denominator: every adult 21+ of the sex, non-citizens included (EVAL.md N1).
  624|             w = fit.world
  625|             female = (fit.cells.sex == 'F').to_numpy()
  626| 
  627|             def rate(m):
  628|                 votes, adults = np.zeros((w.t.shape[0], len(states))), np.zeros((w.t.shape[0], len(states)))
  629|                 np.add.at(votes, (slice(None), sidx[m]), (w.adults * w.can * w.t)[:, m])
  630|                 np.add.at(adults, (slice(None), sidx[m]), w.adults[:, m])
  631|                 return votes / np.maximum(adults, 1)
  632|             wt, mt = rate(female), rate(~female)
  633|             rows = []
  634|             for s in cw.index:
  635|                 i = states.index(s)
  636|                 rows.append({'state': s, 'women_model': round(float(np.median(wt[:, i])) * 100, 1),
  637|                              'women_cw': round(float(cw.loc[s, 'women_turnout']) * 100, 1),
  638|                              'men_model': round(float(np.median(mt[:, i])) * 100, 1),
  639|                              'men_cw': round(float(cw.loc[s, 'men_turnout']) * 100, 1)})
  640|             res['corder_wolbrecht'] = rows
  641|             res['women_mae_points'] = round(float(np.mean([abs(r['women_model'] - r['women_cw']) for r in rows])), 1) if rows else None
  642|         (self.dir / 'check.json').write_text(json.dumps(res, indent=1, default=float))
  643|         return res
  644| 
  645|     def _fixed_ev(self, states):
  646|         """[S, 3] electors by party for states whose legislature chose them (inp.ev_fixed:
  647|         state → (R, D, O)); NaN rows elsewhere. None when the inputs carry no such table."""
  648|         fx = getattr(self.inp, 'ev_fixed', None) or self.extras.get('franchise', {}).get('ev_fixed') or LEGISLATURE_EV.get(self.year)
  649|         if not fx:
  650|             return None
  651|         out = np.full((len(states), 3), np.nan)
  652|         for i, s in enumerate(states):
  653|             if s in fx:
  654|                 v = fx[s]
  655|                 out[i] = [v.get(k, 0) for k in 'RDO'] if isinstance(v, dict) else list(v)
  656|         return out
  657| 
  658|     def _o_single(self, states):
  659|         """[S] the largest single "other" candidate's share of O (the named third P vs
  660|         the rest), so a lumped O can't carry a state no one of its candidates won.
  661|         None for 1916–1924 (their bundles stay as published)."""
  662|         if self.year in (1916, 1920, 1924):
  663|             return None
  664|         r, yy = self.inp.returns.reindex(states).fillna(0), self.year % 100
  665|         if f'P{yy}' not in r or f'O{yy}' not in r:
  666|             return None
  667|         o, p = r[f'O{yy}'].to_numpy(float), r[f'P{yy}'].clip(lower=0).to_numpy(float)
  668|         p = np.minimum(p, o)
  669|         return np.where(o > 0, np.maximum(p, o - p) / np.maximum(o, 1e-9), 1.0)
  670| 
  671|     def _split_ev(self, states):
  672|         """[S, 3] historical electors by party for states that divided them (inp.ev_split:
  673|         state → (R, D, O)); None when the inputs carry no such table."""
  674|         sp = getattr(self.inp, 'ev_split', None) or self.extras.get('franchise', {}).get('ev_split')
  675|         if not sp:
  676|             return None
  677|         out = np.full((len(states), 4), np.nan)
  678|         cols = self._ret_cols()
  679|         r = self.inp.returns.reindex(states).fillna(0)
  680|         osg = self._o_single(states)
  681|         for i, s in enumerate(states):
  682|             if s in sp:
  683|                 v = sp[s]
  684|                 out[i, :3] = [v.get(k, 0) for k in 'RDO'] if isinstance(v, dict) else list(v)
  685|                 pv = r.loc[s, cols].to_numpy(float) * np.array([1, 1, osg[i] if osg is not None else 1])
  686|                 if pv.sum() > 0:
  687|                     out[i, 3] = pv.argmax()   # the historical popular winner keeps the historical division
  688|         return out
  689| 
  690|     def _ret_cols(self) -> list[str]:
  691|         """This year's certified R, D and other columns in the returns (R1920… or the older R20…)."""
  692|         r, y = self.inp.returns, self.year
  693|         for suf in (str(y), f'{y % 100:02d}', str(y % 100)):  # R1920 first: R20 is ambiguous across centuries
  694|             cols = [f'R{suf}', f'D{suf}', f'O{suf}']
  695|             if all(c in r for c in cols):
  696|                 return cols
  697|         raise SystemExit(f'No certified {y} returns (R/D/O columns) in the inputs: {list(r.columns)[:12]}')
  698| 
  699|     # ── dry run (free: no model calls) ──
  700|     def dryrun(self, samples: int = 1) -> dict:
  701|         """backbone (if not fitted) → verify → plan. Brief samples: one control per page slice,
  702|         one counterfactual per what-if; counts of agents, requests and eligibility lines."""
  703|         if not (self.dir / 'fit.pkl').exists():
  704|             self.backbone()
  705|         check = self.verify()
  706|         plan = self.plan()
  707|         reqs = self.requests()
  708|         agents = json.loads((self.dir / 'agents/agents.json').read_text())
  709|         by_agent = {a['id']: a for a in agents}
  710|         out_slices, seen = {}, {}
  711|         for r in reqs:
  712|             a = by_agent[r['meta']['agent']]
  713|             sl = serialize.slice_of(SimpleNamespace(group=a['group'], south=a['state'] in agentlayer.SOUTH, sex=a['sex']))
  714|             out_slices[sl] = out_slices.get(sl, 0) + (r['meta']['kind'] == 'control')
  715|             k = ('control', sl) if r['meta']['kind'] == 'control' else (r['meta']['arm'], None) if r['meta']['kind'] == 'cf' else None
  716|             if k and seen.get(k, 0) < samples:
  717|                 seen[k] = seen.get(k, 0) + 1
  718|                 seen.setdefault('_briefs', []).append({'arm': r['meta']['arm'], 'slice': sl, 'agent': a['id'], 'user': r['user']})
  719|         elig = {}
  720|         for a in agents:
  721|             line = a['eligibility'].replace(STATE_NAME.get(a['state'], a['state']), '<state>')
  722|             elig[line] = elig.get(line, 0) + 1
  723|         groups = {}
  724|         for a in agents:
  725|             g = a['group'] + (f':{a["status"]}' if a.get('status') else '') + (f':{a["origin"]}' if a.get('origin') else '')
  726|             groups[g] = groups.get(g, 0) + 1
  727|         res = {'year': self.year, 'run': self.id, 'era': agentlayer.era(self.year),
  728|                'R1_worst_vote_error': check['R1_worst_vote_error'], 'R1_pass': check['R1_pass'], 'ev_by_draw': check['ev_by_draw'],
  729|                'what_ifs': {k: k in for_year([k], self.year) for k in self.cfg.what_ifs},
  730|                'cohorts': plan['cohorts'], 'agents': plan['agents'], 'requests': plan['requests'],
  731|                'by_arm_model': plan['by_arm_model'], 'estimate': plan['estimate'],
  732|                'controls_by_slice': out_slices, 'agents_by_group': groups,
  733|                'eligibility_lines': dict(sorted(elig.items(), key=lambda x: -x[1])), 'briefs': seen.get('_briefs', [])}
  734|         (self.dir / 'dryrun.json').write_text(json.dumps(res, indent=1, default=float))
  735|         return res
  736| 
  737|     # ── evaluate ──
  738|     def evaluate(self):
  739|         from . import benchmarks
  740|         if self.year != 1920:
  741|             raise SystemExit('evaluate: the validation checks are 1920\'s; every other year is checked by '
  742|                              '`run verify` (reproduction, and Corder–Wolbrecht where it exists).')
  743|         fit = self.fit()
  744|         states, sidx = self.state_index(fit)
  745|         base_votes = aggregate.by_state(fit.world, sidx, len(states))
  746|         checks = [evaluate.r1_reproduction(fit, self.inp, base_votes)]
  747|         ho = evaluate.holdout(fit, self.inp, self.cfg.holdout, self.cfg.draws, self.cfg.seed)
  748|         checks += ho['checks']
  749|         checks += benchmarks.natural_experiment(fit, self.inp, self.extras)
  750|         an = json.loads((self.dir / 'analysis.json').read_text()) if (self.dir / 'analysis.json').exists() else None
  751|         checks += benchmarks.agent_checks(an, fit, self, self.extras)
  752|         summary = {'passed': sum(1 for c in checks if c['pass'] is True),
  753|                    'failed': [c['id'] for c in checks if c['pass'] is False],
  754|                    'not_run': [c['id'] for c in checks if c['pass'] is None]}
  755|         budget = [self.uncertainty_budget(k) for k in self.cfg.what_ifs]
  756|         out = {'summary': summary, 'checks': checks, 'holdout_rows': ho['rows'], 'uncertainty_budget': budget}
  757|         (self.dir / 'validation.json').write_text(json.dumps(out, indent=1, default=float))
  758|         return out
  759| 
  760| 
  761| # Electors chosen by a legislature, by party slot (R, D, O), 1828–1876: a fallback until the
  762| # data layer supplies inp.ev_fixed (which wins). Before 1828 the data layer must supply it.
  763| LEGISLATURE_EV = {
  764|     1828: {'DE': (3, 0, 0), 'SC': (0, 11, 0)}, 1832: {'SC': (0, 0, 11)}, 1836: {'SC': (0, 0, 11)},
  765|     1840: {'SC': (0, 11, 0)}, 1844: {'SC': (0, 9, 0)}, 1848: {'SC': (0, 9, 0)}, 1852: {'SC': (0, 8, 0)},
  766|     1856: {'SC': (0, 8, 0)}, 1860: {'SC': (0, 0, 8)}, 1868: {'FL': (3, 0, 0)}, 1876: {'CO': (3, 0, 0)},
  767| }
```

## `simharness/profiles.py`

```python
    1| """Everything about one election that the pipeline needs and the data can't say:
    2| who ran, how the brief blinds them, which letters are safe, what voters read,
    3| and how the robot names the result.
    4| 
    5| 1920 is the original: its values are the ones the harness was built with, so
    6| its briefs stay byte-identical (and its cached answers keep matching).
    7| 
    8| 1924 is the first carried-forward year (backbone.carry_forward): its
    9| population is the 1920 census aged to November 1924, and its group structure
   10| is the 1920 fit's, recalibrated exactly to the 1924 returns. See
   11| DISCLOSURES C13–C16.
   12| """
   13| from __future__ import annotations
   14| 
   15| import json
   16| import re
   17| 
   18| from .config import ROOT
   19| 
   20| PROFILES = {
   21|     1920: {
   22|         'year': 1920,
   23|         'base': None,
   24|         'day_phrase': 'Tuesday, 2 November',
   25|         'names': {'R': 'Harding', 'D': 'Cox', 'O': 'another candidate'},
   26|         'full_names': {'R': 'Warren G. Harding', 'D': 'James M. Cox'},
   27|         'descriptors': {
   28|             'R': 'nominee of the party that has held a majority in Congress since the 1918 elections',
   29|             'D': 'nominee of the party of the administration in office since 1913',
   30|         },
   31|         'compile_desc': {'R': 'the party that has held a majority in Congress since the 1918 elections',
   32|                          'D': 'the party of the administration in office since 1913', 'president': 'Wilson'},
   33|         'third': None,
   34|         # No H(arding), C(ox), D(ebs), R(epublican), D(emocrat), S(ocialist),
   35|         # F(armer-Labor), W(ilson), L(eague).
   36|         'label_pool': ['K', 'M', 'N', 'P', 'T', 'V'],
   37|         'others_line': 'Other candidates on some ballots, including a Socialist and a Farmer-Labor nominee (answer "other").',
   38|         'plank_order': ['League of Nations', 'cost of living', 'labor', 'agriculture', 'women', 'immigration', 'Prohibition'],
   39|         'names_re': r'\b(Harding|Cox|Coolidge|Roosevelt|Debs|Christensen|Republican|Democrat|G\.\s?O\.\s?P|Wilson)',
   40|         'never_name': 'Harding, Cox, Coolidge, Franklin Roosevelt, Debs, Christensen or Wilson',
   41|         'corpus': 'sources/corpus_1920.jsonl',
   42|         'platforms': 'context/platforms_1920.json',
   43|         'ev_label': '404–127',
   44|         'slice_sources': {
   45|             'men': '1920 census (Fourteenth Census, voting-age tables), men 21+ outside the eleven Southern states; turnout and choice from the backbone (1916→1920 natural experiment, calibrated to certified returns).',
   46|             'women': '1920 census, women 21+ outside the South; turnout is each state\'s 1920 vote minus the men\'s predicted vote (1916 men\'s turnout × the change in states where women already voted).',
   47|             'south-white': '1920 census, white adults in the eleven former Confederate states (includes a small number of American Indian and Asian adults); calibrated to certified returns.',
   48|             'black-south': '1920 census, Black adults in the eleven former Confederate states; turnout from a Goodman regression of 1916 turnout on Black share across those states; the shortfall against white turnout is counted as exclusion.',
   49|             'immigrants': '1920 census, foreign-born white adults who were aliens or had only declared their intent (first papers).',
   50|         },
   51|     },
   52|     1924: {
   53|         'year': 1924,
   54|         'base': 1920,
   55|         'day_phrase': 'Tuesday, 4 November',
   56|         'names': {'R': 'Coolidge', 'D': 'Davis', 'O': 'La Follette'},
   57|         'full_names': {'R': 'Calvin Coolidge', 'D': 'John W. Davis', 'O': 'Robert M. La Follette'},
   58|         'descriptors': {
   59|             'R': 'nominee of the party of the administration in office since 1921',
   60|             'D': 'nominee of the party that held the presidency from 1913 to 1921',
   61|             'O': 'independent candidate of the Progressive movement, endorsed by farm and labor organizations and the Socialist party',
   62|         },
   63|         'compile_desc': {'R': 'the party of the administration in office since 1921',
   64|                          'D': 'the party that held the presidency from 1913 to 1921', 'president': 'Coolidge'},
   65|         # La Follette is a labelled line on every 1924 ballot; he counts in O.
   66|         'third': 'O',
   67|         # No C(oolidge, Calvin), D(avis, Dawes, Democrat), L(a Follette), R(epublican),
   68|         # P(rogressive), B(ryan), W(heeler), J(ohn W. Davis), H(arding), S(ocialist).
   69|         'label_pool': ['K', 'M', 'N', 'T', 'V', 'X'],
   70|         'others_line': 'Other candidates on some ballots, including a Prohibition and a Workers party nominee (answer "other").',
   71|         'plank_order': ['corruption', 'monopoly', 'taxes', 'agriculture', 'labor', 'League of Nations', 'Prohibition'],
   72|         'names_re': r'\b(Coolidge|Davis|La ?Follette|Dawes|Bryan|Wheeler|Harding|Wilson|Republican|Democrat|Progressive party|G\.\s?O\.\s?P)',
   73|         'never_name': 'Coolidge, Davis, La Follette, Dawes, Bryan, Wheeler, Harding or Wilson',
   74|         'corpus': None,  # no dated 1924 items yet (DISCLOSURES C15)
   75|         'platforms': 'context/platforms_1924.json',
   76|         'ev_label': '382–136–13',
   77|         'slice_sources': {
   78|             'men': '1920 census aged to November 1924 along each group\'s 1910→1920 trend; men 21+ outside the eleven Southern states; the 1920 backbone\'s group structure recalibrated exactly to the certified 1924 returns.',
   79|             'women': '1920 census aged to 1924, women 21+ outside the South; the 1920 backbone\'s women-to-men turnout ratio carried forward, then calibrated to each state\'s 1924 vote (Corder–Wolbrecht 1924 held out as a check).',
   80|             'south-white': '1920 census aged to 1924, white adults in the eleven former Confederate states; calibrated to certified 1924 returns.',
   81|             'black-south': '1920 census aged to 1924, Black adults in the eleven former Confederate states; the 1920 exclusion estimate carried forward.',
   82|             'immigrants': '1920 census aged to 1924, foreign-born white adults who were not citizens.',
   83|         },
   84|     },
   85| }
   86| 
   87| 
   88| # Every other year is a JSON file in harness/profiles/<year>.json with the same
   89| # keys (plus optional "masks": [[pattern, replacement], …] for scenario.mask_names).
   90| # A JSON profile whose "corpus" is null picks up sources/corpus_<year>.jsonl
   91| # from the cache once that file exists.
   92| PROFILE_DIR = ROOT / 'profiles'
   93| 
   94| 
   95| def _load_json(year: int) -> dict | None:
   96|     f = PROFILE_DIR / f'{year}.json'
   97|     if not f.exists():
   98|         return None
   99|     prof = json.loads(f.read_text())
  100|     prof['year'] = year
  101|     if not prof.get('corpus'):
  102|         from .config import CACHE
  103|         rel = f'sources/corpus_{year}.jsonl'
  104|         prof['corpus'] = rel if (CACHE / rel).exists() else None
  105|     return prof
  106| 
  107| 
  108| def years() -> list[int]:
  109|     return sorted(set(PROFILES) | {int(f.stem) for f in PROFILE_DIR.glob('[0-9]*.json')})
  110| 
  111| 
  112| def get(year: int) -> dict:
  113|     if year not in PROFILES:
  114|         prof = _load_json(year)
  115|         if prof is None:
  116|             raise SystemExit(f'No election profile for {year}. Simulated years: {years()}')
  117|         PROFILES[year] = prof
  118|     return PROFILES[year]
  119| 
  120| 
  121| def names_re(year: int):
  122|     return re.compile(get(year)['names_re'], re.I)
```

## `simharness/prompts.py`

```python
    1| """Versioned prompts: the blinded control brief, the non-hypothetical
    2| counterfactual brief, the recall probe and the label-swap perturbation.
    3| 
    4| Rules the templates enforce:
    5| - The candidates are neutral letters, drawn per agent from letters that match
    6|   no 1920 candidate's or party's initial, in a random order.
    7| - Every dated item in a brief is dated on or before the context cutoff, and
    8|   shows its date.
    9| - A counterfactual is never phrased as a hypothesis. The changed fact is
   10|   written into the person's world as settled; anything in the brief that the
   11|   change would contradict is removed; the exact change is logged in the
   12|   request's meta (never shown to the model as a change).
   13| """
   14| from __future__ import annotations
   15| 
   16| import datetime as dt
   17| import random
   18| 
   19| # p1: the 1920 prototype's answers. p2: brief dated on the context cutoff (p1 dated
   20| # briefs 30 Oct but admitted items to 1 Nov); non-citizens get no franchise counterfactual.
   21| # p3: quote capped at 25 words, no letter labels (DISCLOSURES D11).
   22| # p4: a candidate what-if's counterfactual ballot carries a third labelled line (a named
   23| # independent); every other brief is byte-identical to p3's, so p3 answers to them are reused.
   24| # p5: news about one nominee sits on that nominee's ballot line, and those counterfactuals
   25| # carry a manipulation check (news_about) (DISCLOSURES D21). Briefs without such news are
   26| # byte-identical to p4's.
   27| # p6: a staged compiled what-if (world.py) carries a belief check, answered first (world_check),
   28| # its consequences among the settled facts, the dated items it contradicts removed and up to two
   29| # in-world items added (DISCLOSURES D33). Every other brief is byte-identical to p5's.
   30| PROMPT_VERSION = 'p6'
   31| 
   32| NEWS_CHECK = ('Also fill news_about: the label of the candidate the recent news on the ballot concerns, '
   33|               '"neither" if it concerns neither, or "unsure".')
   34| 
   35| 
   36| def world_check_line(check: dict) -> str:
   37|     """The belief check, asked before the election question: what the person takes to be true."""
   38|     opts = '; '.join(f'"{o}"' for o in check['options'])
   39|     return (f'Before anything else, fill world_check: as this person understands things on this date, {check["question"].rstrip("?")}? '
   40|             f'Answer with one of: {opts}.')
   41| 
   42| # No H(arding), C(ox), D(ebs), R(epublican), D(emocrat), S(ocialist),
   43| # F(armer-Labor), W(ilson), L(eague).
   44| LABEL_POOL = ['K', 'M', 'N', 'P', 'T', 'V']
   45| 
   46| SYSTEM = """You give voice to one invented person living in the United States. The brief you receive is that person's life and world as they stand on the date it gives: their circumstances, their memories, and what they have lately read or heard. Every line of the brief is settled fact about the world. It is not a scenario or a hypothesis, and you never comment on it as one.
   47| 
   48| Answer only from what this person could know on that date. The person does not know anything that happens after it, including how any election turns out. Where the brief leaves something open, answer as this particular person plausibly would given their own circumstances, not as a type or a stereotype of any group.
   49| 
   50| Fill the requested JSON:
   51| - able_to_vote: whether this person can lawfully cast a ballot for president this year and, in practice, will be allowed to.
   52| - p_vote: the chance, 0 to 100, that this person casts a presidential ballot.
   53| - choice: the candidate this person would vote for if they vote (a label), "other", or "none".
   54| - p_choice: this person's leanings as chances that add to 100, over the labelled candidates and "other".
   55| - confidence: 0 to 100, how settled the person's mind is.
   56| - reason: one or two sentences, in the third person, naming the circumstances in the brief that drove the answer.
   57| - quote: one or two sentences, at most 25 words, the person might say aloud to a neighbour. Plain English of the period, specific to their own circumstances. Never use a candidate's letter label in the quote; a person would say "the Republican", "the man from Ohio" or "the administration's man", never "Candidate K" or "K". No slurs, no melodrama.
   58| - sources_used: the ids of the dated items in the brief the answer rests on."""
   59| 
   60| PROBE_SYSTEM = """You are a careful historian. Answer the question about the document you are given. If you do not know, answer "unknown". Fill the requested JSON."""
   61| 
   62| QUESTIONS = [
   63|     'Election Day is Tuesday. Can this person vote, how likely are they to vote, and if they vote, for whom?',
   64|     'A neighbour asks what this person will do on Tuesday, 2 November. Will they cast a ballot for president, and for which candidate?',
   65|     'Think about Tuesday\'s presidential election from where this person stands. How likely are they to vote, and which candidate would get their vote?',
   66| ]
   67| 
   68| WEEKDAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
   69| 
   70| 
   71| def questions(day_phrase: str = 'Tuesday, 2 November') -> list[str]:
   72|     """The three paraphrases for an election day (1920's are QUESTIONS, unchanged). Before
   73|     1845 states chose electors on different days, and the profile's day_phrase is a clause
   74|     ("the day this person's state has set…"): the questions then say "election day"."""
   75|     day = day_phrase.split(',')[0].strip()
   76|     if day == 'Tuesday':
   77|         return [q.replace('Tuesday, 2 November', day_phrase) for q in QUESTIONS]
   78|     if day in WEEKDAYS:
   79|         return [q.replace('Tuesday, 2 November', day_phrase).replace('Election Day is Tuesday.', f'Election Day is {day}.')
   80|                 .replace("Tuesday's presidential election", f"{day}'s presidential election") for q in QUESTIONS]
   81|     return [q.replace('Tuesday, 2 November', 'election day').replace('Election Day is Tuesday.', 'The presidential election is near.')
   82|             .replace("Tuesday's presidential election", 'the coming presidential election') for q in QUESTIONS]
   83| 
   84| 
   85| PROBE_QUESTION = (
   86|     'Set the person aside. Which year\'s United States presidential election does this brief describe? '
   87|     'Which real candidates stand behind each label? Who won that election? '
   88|     'Answer "unknown" for anything you cannot tell.'
   89| )
   90| 
   91| 
   92| def answer_schema(labels: list[str], news_check: bool = False, world_options: list[str] | None = None) -> dict:
   93|     choice_props = {l: {'type': 'integer'} for l in labels}
   94|     choice_props['other'] = {'type': 'integer'}
   95|     if world_options:
   96|         # p6: the belief check comes first, so the person settles what is true before choosing.
   97|         s = answer_schema(labels, news_check)
   98|         s['properties'] = {'world_check': {'type': 'string', 'enum': list(world_options)}, **s['properties']}
   99|         s['required'] = ['world_check'] + s['required']
  100|         return s
  101|     if news_check:
  102|         s = answer_schema(labels)
  103|         s['properties']['news_about'] = {'type': 'string', 'enum': labels + ['neither', 'unsure']}
  104|         s['required'].append('news_about')
  105|         return s
  106|     return {
  107|         'type': 'object',
  108|         'properties': {
  109|             'able_to_vote': {'type': 'string', 'enum': ['yes', 'no', 'unsure']},
  110|             'p_vote': {'type': 'integer'},
  111|             'choice': {'type': 'string', 'enum': labels + ['other', 'none']},
  112|             'p_choice': {'type': 'object', 'properties': choice_props,
  113|                          'required': list(choice_props), 'additionalProperties': False},
  114|             'confidence': {'type': 'integer'},
  115|             'reason': {'type': 'string'},
  116|             'quote': {'type': 'string'},
  117|             'sources_used': {'type': 'array', 'items': {'type': 'string'}},
  118|         },
  119|         'required': ['able_to_vote', 'p_vote', 'choice', 'p_choice', 'confidence', 'reason', 'quote', 'sources_used'],
  120|         'additionalProperties': False,
  121|     }
  122| 
  123| 
  124| def probe_schema(labels: list[str]) -> dict:
  125|     return {
  126|         'type': 'object',
  127|         'properties': {
  128|             'year': {'type': 'string'},
  129|             'candidates': {'type': 'object', 'properties': {l: {'type': 'string'} for l in labels},
  130|                            'required': labels, 'additionalProperties': False},
  131|             'winner_label': {'type': 'string'},
  132|             'winner_name': {'type': 'string'},
  133|             'confidence': {'type': 'integer'},
  134|         },
  135|         'required': ['year', 'candidates', 'winner_label', 'winner_name', 'confidence'],
  136|         'additionalProperties': False,
  137|     }
  138| 
  139| 
  140| def long_date(iso: str) -> str:
  141|     d = dt.date.fromisoformat(iso)
  142|     return f'{d.strftime("%A")}, {d.day} {d.strftime("%B %Y")}'
  143| 
  144| 
  145| OTHERS_1920 = 'Other candidates on some ballots, including a Socialist and a Farmer-Labor nominee (answer "other").'
  146| 
  147| 
  148| def ballot_block(state_name: str, parties: list[dict], labels: list[str], others: str = OTHERS_1920,
  149|                  note: str | None = None) -> list[str]:
  150|     """parties: [{key, descriptor, planks: [str]}] in display order, already
  151|     paired with labels in the same order. note: a profile's ballot note for this
  152|     state (profile 'ballot_notes', e.g. 1964 Alabama's unpledged electors), last."""
  153|     lines = [f'On the ballot for president in {state_name}:']
  154|     for label, p in zip(labels, parties):
  155|         planks = ' '.join(p['planks'])
  156|         news = f' Recent news: {" ".join(p["news"])}' if p.get('news') else ''
  157|         lines.append(f'- Candidate {label}: {p["descriptor"]}.{news} {planks}'.rstrip())
  158|     lines.append(f'- {others}')
  159|     if note:
  160|         lines.append(f'- {note}')
  161|     return lines
  162| 
  163| 
  164| def brief(persona: dict, world: dict, items: list[dict], ballot: list[str], asof: str, day_phrase: str = 'Tuesday, 2 November') -> str:
  165|     lines = [f'Date: {long_date(asof)}. The presidential election is on {day_phrase}.', '', 'This person:']
  166|     lines += [f'- {line}' for line in persona['lines']]
  167|     if world.get('facts'):
  168|         lines += ['', 'How things stand:']
  169|         lines += [f'- {f}' for f in world['facts']]
  170|     if items:
  171|         lines += ['', 'What this person has lately read or heard (dated):']
  172|         for it in items:
  173|             lines.append(f'[{it["id"]}] {it["newspaper"]}, {it["place"]}, {long_date(it["date"])}: "{it["text"]}"')
  174|     lines += [''] + ballot
  175|     return '\n'.join(lines)
  176| 
  177| 
  178| def assign_labels(rng: random.Random, keys: list[str], pool: list[str] = LABEL_POOL) -> dict:
  179|     """{party key: label}, and the display order."""
  180|     labels = rng.sample(pool, len(keys))
  181|     order = keys[:]
  182|     rng.shuffle(order)
  183|     return dict(zip(keys, labels)), order
```

## `simharness/publish.py`

```python
    1| """The publish stage: every what-if combination → the page's result shape and bundle.
    2| 
    3| `Run` (pipeline.py) mixes `Publisher` in, so the methods here read the run's
    4| fit, inputs, profile and agent files through `self`.
    5| """
    6| from __future__ import annotations
    7| 
    8| import itertools
    9| import json
   10| import pickle
   11| from pathlib import Path
   12| 
   13| import numpy as np
   14| 
   15| from . import agentlayer, aggregate, evidence, paired, prompts, quotes, scenario, serialize
   16| from .config import ROOT
   17| from .geo import STATE_NAME
   18| from .whatifs import REGISTRY, apply_effects, for_year, text_for, withdraw
   19| 
   20| CONF = {'franchise': 'high', 'population': 'medium', 'issue': 'low', 'candidate': 'low'}
   21| KIND_ORDER = ['franchise', 'population', 'issue', 'candidate']
   22| 
   23| 
   24| def pre_interviews(run_dir: Path) -> dict | None:
   25|     """The interviews done before any change, from a run's answered requests:
   26|     each synthetic voter asked in the world as it was (the baseline the
   27|     what-ifs are measured against), and the leakage probes when the run had
   28|     them (L1 recall, L2 label swap; analysis.json)."""
   29|     rq, an = run_dir / 'agents/all_requests.jsonl', run_dir / 'agents/answers.jsonl'
   30|     if not rq.exists() or not an.exists():
   31|         return None
   32|     meta = {r['id']: r['meta'] for r in map(json.loads, rq.read_text().splitlines()) if r}
   33|     done = [meta[a['id']] for a in map(json.loads, an.read_text().splitlines()) if a.get('ok', True) and a['id'] in meta]
   34|     control = [m for m in done if m['kind'] == 'control']
   35|     if not control:
   36|         return None
   37|     out = {'voters': len({m['agent'] for m in control}), 'interviews': len(control)}
   38|     ap = run_dir / 'analysis.json'
   39|     a = json.loads(ap.read_text()) if ap.exists() else {}
   40|     if a.get('l1', {}).get('n'):
   41|         out['recall'] = {'n': a['l1']['n'], 'winnerRate': a['l1']['winner_rate']}
   42|     if a.get('l2', {}).get('n'):
   43|         out['swap'] = {'n': a['l2']['n'], 'platformRate': a['l2']['platform_rate']}
   44|     ag = run_dir / 'agents/agents.json'
   45|     agents = {x['id']: x for x in json.loads(ag.read_text())} if ag.exists() else {}
   46|     per = [len(agents[m['agent']].get('items', [])) for m in control if m['agent'] in agents]
   47|     if per:
   48|         out['items'] = [min(per), max(per)]
   49|     out['asOf'] = max((m.get('context_date') or '' for m in control), default='') or None
   50|     out['wordings'] = len({m.get('paraphrase') for m in control})
   51|     return out
   52| 
   53| 
   54| ITEM_SUMMARIES = ROOT / 'extracts' / 'item-summaries.json'
   55| 
   56| 
   57| 
   58| def briefs_record(run_dir: Path) -> dict:
   59|     """What the synthetic voters were shown, from a run's requests and agents.
   60|     told: per what-if, the exact lines that wrote the change into their world
   61|     (settled facts; news printed on a nominee's ballot line; planks added or
   62|     dropped). reading: every dated newspaper item in their briefs, with a
   63|     one-line summary from extracts/item-summaries.json when it has one."""
   64|     rq, ag = run_dir / 'agents/all_requests.jsonl', run_dir / 'agents/agents.json'
   65|     told, reading = {}, []
   66|     if rq.exists():
   67|         by = {}
   68|         for r in map(json.loads, rq.read_text().splitlines()):
   69|             if r and r['meta']['kind'] == 'cf':
   70|                 by.setdefault(r['meta']['change']['what_if'], []).append(r)
   71|         for wk, rs in by.items():
   72|             ch = [r['meta']['change'] for r in rs]
   73|             facts = max((c.get('facts', []) for c in ch), key=lambda f: sum(c.get('facts', []) == f for c in ch))
   74|             t = {'facts': facts,
   75|                  'added': sorted({p['text'] for c in ch for p in c.get('added_planks', [])}),
   76|                  'dropped': sorted({p for c in ch for p in c.get('dropped_planks', [])}),
   77|                  # D33: staged in-world news, and how many real items the change made false
   78|                  'items': sorted({(i['date'], i['text']) for c in ch for i in c.get('added_items', [])}),
   79|                  'removed': len({i for c in ch for i in c.get('dropped_sources', [])})}
   80|             t['items'] = [{'date': d, 'text': x} for d, x in t['items']]
   81|             sp = scenario.spec_path(wk)
   82|             spec = json.loads(sp.read_text()) if sp.exists() else REGISTRY.get(wk, {})
   83|             news = spec.get('nominee_news') or []
   84|             if news and any(f'Recent news: {" ".join(news)}' in r['user'] for r in rs):
   85|                 t['news'] = news
   86|             told[wk] = {k: v for k, v in t.items() if v}
   87|     if ag.exists():
   88|         sums = json.loads(ITEM_SUMMARIES.read_text()) if ITEM_SUMMARIES.exists() else {}
   89|         seen = {}
   90|         for a in json.loads(ag.read_text()):
   91|             for i in a.get('items', []):
   92|                 seen.setdefault(i['id'], {'date': i['date'], 'newspaper': i['newspaper'], 'place': i['place'],
   93|                                           **({'summary': sums[i['id']]} if i['id'] in sums else {})})
   94|         reading = sorted(seen.values(), key=lambda x: (x['date'], x['newspaper']))
   95|     return {'told': told, 'reading': reading}
   96| 
   97| class Publisher:
   98|     """The publish stage and the bundle's parts. Needs the attributes and
   99|     helpers `Run` sets up: cfg, inp, extras, prof, year, cand, dir, id, bulk,
  100|     fit(), state_index(), requests(), answers(), _fixed_ev(), _split_ev(),
  101|     _o_single() and _ret_cols()."""
  102| 
  103|     def publish(self):
  104|         fit = self.fit()
  105|         states, sidx = self.state_index(fit)
  106|         ev = self.inp.ev.reindex(states).fillna(0).to_numpy()
  107|         base_votes = aggregate.by_state(fit.world, sidx, len(states))
  108|         base = aggregate.outcome(base_votes, ev, self._fixed_ev(states), self._split_ev(states), o_single=self._o_single(states))
  109|         base_winner = base['winner'][0]
  110|         base_sum = aggregate.summarize(base, base_winner)
  111|         # Page key A is the historical winner (history.js): D → A in a year the D nominee won.
  112|         self.key_of = serialize.key_map(base_sum['ev_point'])
  113|         eff_path = self.dir / 'effects.pkl'
  114|         eff = pickle.load(open(eff_path, 'rb')) if eff_path.exists() else {'effects': {}, 'pairs': {}, 'exposed': set(), 'nationally_exposed': False}
  115|         co = json.loads((self.dir / 'agents/cohorts.json').read_text()) if (self.dir / 'agents/cohorts.json').exists() else None
  116|         cell_to = [co['cell_to'][str(i)] for i in range(len(fit.cells))] if co else []
  117| 
  118|         available = [k for k in for_year(self.cfg.what_ifs, self.year) if REGISTRY[k]['mode'] == 'backbone' or k in eff['effects']]
  119|         available += ['everyone'] if 'everyone' not in available else []
  120|         runs, tables, results_meta = {}, {}, {}
  121|         for n in range(0, min(len(available), self.cfg.max_combo) + 1):
  122|             for combo in itertools.combinations(sorted(available), n):
  123|                 if 'everyone' in combo and len(combo) > 1:
  124|                     continue
  125|                 if sum(REGISTRY[k]['kind'] == 'candidate' for k in combo) > 1:
  126|                     continue  # two named third candidates would share the one O column
  127|                 world = fit.world
  128|                 for k in sorted(combo, key=lambda k: KIND_ORDER.index(REGISTRY[k]['kind'])):
  129|                     spec = REGISTRY[k]
  130|                     if spec['mode'] == 'backbone':
  131|                         world = spec['apply'](fit, world, self.inp)
  132|                     elif spec.get('withdraws') and 'transfer' in eff['effects'][k]:
  133|                         world = withdraw(fit, world, eff['effects'][k]['transfer'], self._third_frac(fit))
  134|                     else:
  135|                         world = apply_effects(fit, world, cell_to, eff['effects'][k]['cohorts'])
  136|                 sv = aggregate.by_state(world, sidx, len(states))
  137|                 out = aggregate.outcome(sv, ev, self._fixed_ev(states), self._split_ev(states), o_single=self._o_single(states))
  138|                 summ = aggregate.summarize(out, base_winner)
  139|                 key = '+'.join(combo)
  140|                 runs[key] = (world, summ, out)
  141|         bundle = self._bundle(fit, states, runs, base_sum, base_winner, eff)
  142|         bundle['pre'] = pre_interviews(self.dir)
  143|         bundle.update(briefs_record(self.dir))
  144|         pub = self.dir / 'published'
  145|         pub.mkdir(exist_ok=True)
  146|         (pub / f'{self.cfg.election}.json').write_text(json.dumps(bundle, indent=1, default=float))
  147|         return {k: {'ev': v[1]['ev_point'], 'drawsWon': v[1]['draws_won']} for k, v in runs.items()}
  148| 
  149|     def _third_frac(self, fit):
  150|         """Per cell: the labelled third candidate's part of the state's `other` vote."""
  151|         r = self.inp.returns
  152|         col = next((c for c in (f'P{self.year}', f'P{self.year % 100}') if c in r), None)
  153|         if col is None:
  154|             return np.ones(len(fit.cells))
  155|         frac = (r[col] / r[self._ret_cols()[2]].clip(lower=1)).clip(0, 1)
  156|         return fit.cells.state.map(frac).fillna(0).to_numpy()
  157| 
  158|     def spec(self, k: str) -> dict:
  159|         """A what-if's registry entry as this year's page reads it."""
  160|         return text_for(REGISTRY[k], self.year)
  161| 
  162|     def _bundle(self, fit, states, runs, base_sum, base_winner, eff):
  163|         state_names = {**{s: s for s in states}, **STATE_NAME}  # a state geo doesn't name (AK, HI) reads as its code
  164|         sources_by_slice = self.prof['slice_sources']
  165|         slice_labels = None if 1868 <= self.year < 1972 else agentlayer.groups_for(self.year)['slices']
  166|         base_world = runs[''][0]
  167|         base_point = base_sum['point']
  168|         used = sorted({k for key in runs for k in key.split('+') if k})
  169|         evs = {k: scenario.load_evidence(k) for k in used}
  170|         conf_of = {k: evidence.confidence(REGISTRY[k], evs[k], eff['effects'].get(k, {}).get('agreement'),
  171|                                           eff['effects'].get(k, {}).get('agent_stats'), bool(REGISTRY[k].get('generated')))
  172|                    for k in used}
  173|         election = {
  174|             'slices': serialize.slices(fit, base_world, base_point, sources_by_slice, slice_labels, self.key_of),
  175|             'whatIfs': [{'key': k, 'label': self.spec(k)['label'], 'kind': REGISTRY[k]['kind'], 'detail': self.spec(k)['detail'],
  176|                          'slices': REGISTRY[k]['slices'], 'assumption': self.spec(k)['assumption'],
  177|                          # additive
  178|                          'confidenceTier': conf_of[k]['tier'], 'evidence': conf_of[k]['evidence'],
  179|                          'exploratory': bool(REGISTRY[k].get('generated'))}
  180|                         for k in used],
  181|         }
  182|         validation = {}
  183|         vpath = self.dir / 'validation.json'
  184|         if vpath.exists():
  185|             validation = json.loads(vpath.read_text())
  186|         out_runs, tables = {}, {}
  187|         # Each what-if's own sentence comes from its single run, so a combined
  188|         # run doesn't misattribute one change's people to another.
  189|         single = {k: self._lead([k], fit, runs[''][0], runs[k][0], runs[k][1]) for k in runs if k and '+' not in k}
  190|         for key, (world, summ, out) in runs.items():
  191|             combo = [k for k in key.split('+') if k]
  192|             tier = evidence.combine_tiers([conf_of[k] for k in combo])
  193|             # The page knows high, medium and low; "very-low" reaches it as low plus the flag.
  194|             conf = tier['tier'] if tier['tier'] in CONF.values() else 'low'
  195|             sl = serialize.slices(fit, world, summ['point'], sources_by_slice, slice_labels, self.key_of)
  196|             lead = ' '.join(single[k] for k in combo) if combo else self._lead([], fit, runs[''][0], world, summ)
  197|             cand = dict(self.cand)
  198|             for k in combo:
  199|                 if REGISTRY[k]['kind'] == 'candidate' and REGISTRY[k].get('candidate') and not REGISTRY[k].get('withdraws'):
  200|                     cand[2] = REGISTRY[k]['candidate']['name']
  201|             text = serialize.verdict(lead=lead, names=states, state_names=state_names, cand=cand, summary=summ,
  202|                                      base_summary=base_sum, base_winner=base_winner, key_of=self.key_of)
  203|             if tier['reasons'] and (tier['tier'] == 'very-low' or any(REGISTRY[k].get('generated') for k in combo)):
  204|                 text += f' {tier["label"]}. {tier["reasons"][0]}'
  205|             ev_page = [x for x in (evidence.page_evidence(k, evs[k], eff['effects'].get(k, {}).get('agreement')) for k in combo) if x]
  206|             ev_sources = list({s['url']: {'title': s['title'], 'url': s['url']} for x in ev_page for f in x['findings']
  207|                                for s in f['sources']}.values())
  208|             extras = {
  209|                 'assumptions': [self.spec(k)['assumption'] for k in combo],
  210|                 'howIGotThis': self._how(combo, summ, evs, tier),
  211|                 'sources': sources_for(self.year) + ev_sources,
  212|                 # additive: how sure, and why
  213|                 'confidenceTier': tier['tier'], 'confidenceLabel': tier['label'],
  214|                 'confidenceFlags': tier['flags'], 'confidenceReasons': tier['reasons'],
  215|                 'evidence': ev_page,
  216|                 'mode': 'truth',
  217|                 'runId': self.id,
  218|                 'validation': validation.get('summary'),
  219|                 'cohortEffects': self._cohort_effects(combo, eff),
  220|             }
  221|             applied = [{'key': k, 'label': REGISTRY[k]['label'], 'kind': REGISTRY[k]['kind']} for k in combo]
  222|             out_runs[key] = serialize.result(names=states, summary=summ, base_winner=base_winner, slices_out=sl, text=text,
  223|                                              confidence=conf, applied=applied, extras=extras, key_of=self.key_of)
  224|             tables[key] = self._state_slice_table(fit, world, summ['point'])
  225|         voters = self._voters(eff, runs)
  226|         return {
  227|             'year': self.cfg.election, 'runId': self.id, 'election': election, 'runs': out_runs, 'tables': tables,
  228|             'voters': voters, 'interviews': self._interviews(eff), 'ev': dict(zip(states, self.inp.ev.reindex(states).fillna(0).astype(int).tolist())),
  229|             'historyWinner': {s: self.key_of[int(w)] for s, w in zip(states, base_winner)},
  230|             'words': self._words(used),
  231|         }
  232| 
  233|     def _words(self, used):
  234|         base = {'no-19th': ['19th', 'nineteenth', 'suffrage fails', 'women can\'t vote', 'no women'],
  235|                 'fifteenth': ['15th', 'fifteenth', 'black southern', 'black voters', 'poll tax', 'jim crow'],
  236|                 'league': ['league', 'treaty', 'versailles'],
  237|                 'everyone': ['everyone', 'all adults', 'universal']}
  238|         extra = scenario.extra_words()
  239|         out = []
  240|         for k in used:
  241|             words = base.get(k, []) + REGISTRY[k].get('words', []) + extra.get(k, [])
  242|             if words:
  243|                 out.append({'key': k, 'words': list(dict.fromkeys(w.lower() for w in words))})
  244|         return out
  245| 
  246|     def _lead(self, combo, fit, base, world, summ):
  247|         if not combo:
  248|             # Winner and electoral votes from the calibrated rerun, not the profile's ev_label (whose order varies).
  249|             won = int(np.argmax(summ['ev_point']))
  250|             return (f'Rerun with nothing changed, {self.year} comes out as it did: {self.cand[won]} wins, '
  251|                     f'{serialize.headline_ev(summ, getattr(self, "key_of", serialize.PARTY_TO_KEY))}.')
  252|         p = summ['point']
  253|         voted_base = (base.adults[p] * base.can[p] * base.t[p]).sum()
  254|         voted = (world.adults[p] * world.can[p] * world.t[p]).sum()
  255|         change = voted - voted_base
  256|         parts = []
  257|         for k in combo:
  258|             if k == 'no-19th':
  259|                 parts.append(f'{serialize.fmt_m(-change)} women who voted can\'t, outside the states that already let them.')
  260|             elif k == 'fifteenth':
  261|                 parts.append(f'{serialize.fmt_m(change)} more Black Southerners vote, turning out like white Southerners and splitting like Black voters in the North.')
  262|             elif k == 'everyone':
  263|                 parts.append(f'{serialize.fmt_m(change)} more adults vote.')
  264|             elif k == 'league':
  265|                 def r2(wd):
  266|                     v = (wd.adults[p] * wd.can[p] * wd.t[p])[:, None] * wd.share[p]
  267|                     return v[:, 0].sum() / (v[:, 0].sum() + v[:, 1].sum()) * 100
  268|                 shift = r2(world) - r2(base)
  269|                 toward = self.cand[1] if shift < 0 else self.cand[0]
  270|                 parts.append(f'With the treaty settled, the voters lean {abs(shift):.1f} points further toward {toward} '
  271|                              'than the same people did in the world as it was.')
  272|             elif REGISTRY[k].get('generated'):
  273|                 # D34: a reinterpreted change says so before anything else.
  274|                 if REGISTRY[k].get('reinterpretation'):
  275|                     parts.append(REGISTRY[k]['reinterpretation'])
  276|                 parts.append(self._lead_generated(REGISTRY[k], base, world, p, change))
  277|         return ' '.join(parts)
  278| 
  279|     def _lead_generated(self, spec, base, world, p, change):
  280|         def shares(wd):
  281|             v = (wd.adults[p] * wd.can[p] * wd.t[p])[:, None] * wd.share[p]
  282|             r, d, o = v[:, 0].sum(), v[:, 1].sum(), v[:, 2].sum()
  283|             return r / (r + d) * 100, o / (r + d + o) * 100
  284|         (r2_0, o_0), (r2_1, o_1) = shares(base), shares(world)
  285|         toward = self.cand[1] if r2_1 < r2_0 else self.cand[0]
  286|         if spec.get('withdraws'):
  287|             return (f'With {self.cand[2]} out of the race, candidates outside the two parties take {o_1:.1f}% of the vote, '
  288|                     f'against {o_0:.1f}% in {self.year}, and the two-party split moves {abs(r2_1 - r2_0):.1f} points toward {toward}.')
  289|         if spec['kind'] == 'candidate':
  290|             name = spec['candidate']['name']
  291|             return (f'With {name} on the ballot, candidates outside the two parties take {o_1:.1f}% of the vote, against {o_0:.1f}% '
  292|                     f'in {self.year}, and the two-party split moves {abs(r2_1 - r2_0):.1f} points toward {toward}.')
  293|         if spec['kind'] == 'franchise':
  294|             return f'{serialize.fmt_m(abs(change))} {"more" if change >= 0 else "fewer"} adults vote.'
  295|         if spec['kind'] == 'population':
  296|             d = float((world.adults[p] - base.adults[p]).sum())
  297|             return (f'{serialize.fmt_m(abs(d))} {"more" if d >= 0 else "fewer"} adults live in the country, and those who can vote '
  298|                     f'turn out and choose as their group did in {self.year}.')
  299|         return (f'In this world, the voters lean {abs(r2_1 - r2_0):.1f} points further toward {toward} than the same '
  300|                 f'people did in {self.year} as it was.')
  301| 
  302|     def _how(self, combo, summ, evs=None, tier=None):
  303|         lines = []
  304|         for k in combo:
  305|             spec = self.spec(k)
  306|             if spec.get('reinterpretation'):
  307|                 lines.append(f'Not quite what you asked: {spec["reinterpretation"]}')
  308|             lines.append(f'What changed: {spec["detail"]}')
  309|             if spec.get('borrowed'):
  310|                 lines.append(f'New voters borrow the behaviour of {spec["borrowed"]}.')
  311|             ev = (evs or {}).get(k)
  312|             if ev and ev.get('summary'):
  313|                 n, level = len(ev.get('findings', [])), evidence.strength(ev)['level']
  314|                 count = f' ({n} finding{"s" if n != 1 else ""}, {level} evidence)' if n else ''
  315|                 lines.append(f'What historians found{count}: {ev["summary"]}')
  316|         census = self.prof.get('census_line') or (
  317|             '1920 census voting-age tables' if self.year == 1920 else
  318|             f'{self.prof["base"]} census voting-age tables aged to {self.year}' if self.prof.get('base') else
  319|             census_phrase(self.year))
  320|         lines.append(f'The numbers: the {census} and certified returns; every draw reproduces {self.year} exactly before the change.')
  321|         lines.append(f'How sure: I reran it {summ["draws"]} times with different population and parameter draws.')
  322|         if tier and tier['tier'] in ('low', 'very-low') and combo:
  323|             lines.append(f'{tier["label"]}: ' + ' '.join(tier['reasons'][:3]))
  324|         return lines
  325| 
  326|     def _cohort_effects(self, combo, eff):
  327|         out = []
  328|         for k in combo:
  329|             e = eff['effects'].get(k)
  330|             if not e or REGISTRY[k]['mode'] != 'agents':
  331|                 continue
  332|             for ck, c in e['cohorts'].items():
  333|                 out.append({'whatIf': k, 'cohort': ck, 'n': c['n'], 'bias': round(c['bias'], 3), 'weight': round(c['weight'], 3),
  334|                             'exposed': c['exposed'], 'dr': round(c['dr'], 3), 'dt': round(c['dt'], 3)})
  335|         return out
  336| 
  337|     def _state_slice_table(self, fit, world, p):
  338|         keys = fit.cells.apply(serialize.slice_of, axis=1).to_numpy()
  339|         rows = []
  340|         for (s, sl), idx in fit.cells.assign(sl=keys).groupby(['state', 'sl']).groups.items():
  341|             idx = np.array(list(idx))
  342|             a = world.adults[p, idx]
  343|             n = a.sum()
  344|             if n <= 0:
  345|                 continue
  346|             voted = a * world.can[p, idx] * world.t[p, idx]
  347|             by_key = {self.key_of[j]: float((voted * world.share[p, idx, j]).sum() / n) for j in range(3)}
  348|             rows.append({'state': s, 'slice': sl, 'adults': float(n),
  349|                          'barred': float((a * (1 - world.can[p, idx])).sum() / n),
  350|                          'home': float((a * world.can[p, idx] * (1 - world.t[p, idx])).sum() / n),
  351|                          'A': by_key['A'], 'B': by_key['B'], 'O': by_key['O']})
  352|         return rows
  353| 
  354|     def _voters(self, eff, runs):
  355|         """One person per slice, per what-if combination (single what-ifs and history)."""
  356|         if not (self.dir / 'agents/agents.json').exists():
  357|             return {}
  358|         agents = {a['id']: a for a in json.loads((self.dir / 'agents/agents.json').read_text())}
  359|         co = json.loads((self.dir / 'agents/cohorts.json').read_text())
  360|         cohorts = co['cohorts']
  361|         reqs = {r['id']: r for r in self.requests()}
  362|         ans = self.answers()
  363|         corpus = {c['id']: c for c in self.extras['corpus']}
  364|         slice_of_cohort = {}
  365|         for k, c in cohorts.items():
  366|             row = type('R', (), {'group': c['group'], 'south': c['region'] == 'south', 'sex': c['sex']})
  367|             slice_of_cohort[k] = serialize.slice_of(row)
  368|         slices = {}
  369|         for k, s in slice_of_cohort.items():
  370|             slices.setdefault(s, []).append(k)
  371|         adults = {k: c['adults'] for k, c in cohorts.items()}
  372|         out = {}
  373|         for wk in [''] + list(eff['pairs']):
  374|             answers = {}
  375|             for aid, a in agents.items():
  376|                 if wk and aid in (eff.get('dropped') or {}).get(wk, {}):
  377|                     continue  # D33: failed the belief check or the audit on every model asked
  378|                 # The pair the analysis kept: the escalated model's, when the bulk answer failed a check.
  379|                 model = (eff.get('kept') or {}).get(wk, {}).get(aid, self.bulk) if wk else self.bulk
  380|                 c_id = f'control|{aid}|{model}'
  381|                 f_id = f'cf:{wk}|{aid}|{model}' if wk else c_id
  382|                 chk = reqs[f_id]['meta'].get('news_check') if f_id in reqs else None
  383|                 if chk and f_id in ans and ans[f_id]['data'].get('news_about') != chk['expected']:
  384|                     continue  # misread whom the news was about (p5 check)
  385|                 if c_id in ans and f_id in ans:
  386|                     lab = {v: k for k, v in reqs[c_id]['meta']['label_of'].items()}
  387|                     answers[aid] = {'control': paired.normalize(ans[c_id]['data'], lab) | {'raw': ans[c_id]['data']},
  388|                                     'cf': paired.normalize(ans[f_id]['data'], lab) | {'raw': ans[f_id]['data']},
  389|                                     'cf_req': reqs[f_id]}
  390|             picks = quotes.select(slices, agents, answers, adults, self.cfg.seed)
  391|             per = {}
  392|             for p in picks:
  393|                 a = p['agent']
  394|                 x = answers[a['id']]
  395|                 names = {a['label_of'][k]: self.prof['names'][k] for k in a['label_of']}
  396|                 if x['cf_req']['meta'].get('candidate'):
  397|                     names[x['cf_req']['meta']['candidate']['label']] = x['cf_req']['meta']['candidate']['name']
  398|                 srcs = [corpus[i] for i in x['cf']['raw'].get('sources_used', []) if i in corpus] or \
  399|                        [corpus[i] for i in x['cf_req']['meta']['sources'] if i in corpus]
  400|                 key_map = {'R': self.key_of[0], 'D': self.key_of[1], 'O': 'O', 'home': 'home', 'barred': 'barred'}
  401|                 per[p['slice']] = {
  402|                     'name': a['name'],
  403|                     'line': f'{a["age"]}, {"a city or town" if a["urban"] else "the countryside"}, {STATE_NAME.get(a["state"], a["state"])}',
  404|                     'quote': quotes.deblind(x['cf']['raw'].get('quote', ''), names),
  405|                     'history': key_map[x['control']['choice']],
  406|                     'now': key_map[x['cf']['choice']],
  407|                     # additive
  408|                     'controlQuote': quotes.deblind(x['control']['raw'].get('quote', ''), names),
  409|                     'cohort': cohorts[a['cohort']]['label'],
  410|                     'cohortAdults': round(cohorts[a['cohort']]['adults']),
  411|                     'weight': round(a['weight']),
  412|                     'contextDate': x['cf_req']['meta']['context_date'],
  413|                     'sources': [{'title': f'{s["newspaper"]}, {s["date"]}', 'url': s['url'], 'date': s['date']} for s in srcs],
  414|                     'model': x['cf_req']['model'], 'promptVersion': x['cf_req']['meta']['prompt_version'],
  415|                     'memorizationExposed': bool(eff.get('nationally_exposed') or a['cohort'] in eff.get('exposed', set())),
  416|                     'namesRestored': True,
  417|                     'unchanged': x['cf']['choice'] == x['control']['choice'],
  418|                     'change': x['cf_req']['meta'].get('change'),
  419|                 }
  420|             out[wk] = per
  421|         return out
  422| 
  423|     def _interviews(self, eff):
  424|         """Every paired interview, per what-if (additive): the question wordings
  425|         once, and each person's two answers (as it was / in the what-if), names
  426|         restored. The page shows it in the robot's opened bubble."""
  427|         if not (self.dir / 'agents/agents.json').exists():
  428|             return {}
  429|         agents = {a['id']: a for a in json.loads((self.dir / 'agents/agents.json').read_text())}
  430|         cohorts = json.loads((self.dir / 'agents/cohorts.json').read_text())['cohorts']
  431|         reqs = {r['id']: r for r in self.requests()}
  432|         ans = self.answers()
  433|         says = {'R': self.cand[0], 'D': self.cand[1], 'O': self.cand[2], 'home': 'stays home', 'barred': 'can’t vote'}
  434| 
  435|         def one(rid, a, lab):
  436|             d = ans[rid]['data']
  437|             n = paired.normalize(d, lab)
  438|             names = {a['label_of'][k]: self.prof['names'][k] for k in a['label_of']}
  439|             c = reqs[rid]['meta'].get('candidate')
  440|             if c:
  441|                 names[c['label']] = c['name']
  442|             choice = c['name'] if c and d.get('choice') == c['label'] and n['choice'] == 'O' else says.get(n['choice'], n['choice'])
  443|             return {'choice': choice, 'pVote': d.get('p_vote'),
  444|                     'quote': quotes.deblind(d.get('quote', ''), names), 'reason': quotes.deblind(d.get('reason', ''), names)}
  445| 
  446|         out = {'questions': prompts.questions(self.prof['day_phrase']), 'byWhatIf': {}}
  447|         for wk in eff['pairs']:
  448|             rows = []
  449|             for aid, a in agents.items():
  450|                 model = (eff.get('kept') or {}).get(wk, {}).get(aid, self.bulk)
  451|                 c_id, f_id = f'control|{aid}|{model}', f'cf:{wk}|{aid}|{model}'
  452|                 if c_id not in ans or f_id not in ans:
  453|                     continue
  454|                 lab = {v: k for k, v in reqs[c_id]['meta']['label_of'].items()}
  455|                 chk = reqs[f_id]['meta'].get('news_check')
  456|                 why = (eff.get('dropped') or {}).get(wk, {}).get(aid)
  457|                 rows.append({
  458|                     # additive: took the news to be about the other candidate; left out of the counts
  459|                     **({'misread': True} if chk and ans[f_id]['data'].get('news_about') != chk['expected'] else {}),
  460|                     # additive (D33): disbelieved the change or reasoned from the world as it was; left out
  461|                     **({'excluded': why} if why else {}),
  462|                     **({'model': model} if model != self.bulk else {}),
  463|                     'question': a['paraphrase'], 'name': a['name'], 'cohort': cohorts[a['cohort']]['label'],
  464|                     'line': f'{a["age"]}, {"a city or town" if a["urban"] else "the countryside"}, {STATE_NAME.get(a["state"], a["state"])}',
  465|                     'before': one(c_id, a, lab), 'after': one(f_id, a, lab),
  466|                 })
  467|             out['byWhatIf'][wk] = sorted(rows, key=lambda r: (r['question'], r['cohort'], r['name']))
  468|         return out
  469| 
  470| 
  471| 
  472| 
  473| def census_phrase(year: int) -> str:
  474|     """Which censuses a general year's population comes from (first census 1790; latest 2020)."""
  475|     c = min(max(year - year % 10, 1790), 2020)
  476|     if c == year:
  477|         return f'{year} census counts'
  478|     if c > year:
  479|         return f'{c} census counts carried back to {year}'
  480|     if c == 2020:
  481|         return f'2020 census counts carried forward to {year}'
  482|     return f'{c} and {c + 10} census counts interpolated to {year}'
  483| 
  484| 
  485| def sources_for(year: int) -> list[dict]:
  486|     if year == 1920:
  487|         return SOURCES
  488|     if year == 1924:
  489|         return [SOURCES[0], SOURCES[1],
  490|                 {'title': f'National Archives, {year} Electoral College results', 'url': f'https://www.archives.gov/electoral-college/{year}'},
  491|                 SOURCES[4], SOURCES[5],
  492|                 {'title': f'American Presidency Project, {year} party platforms (Republican, Democratic, Progressive)',
  493|                  'url': 'https://www.presidency.ucsb.edu/documents/app-categories/elections-and-transitions/party-platforms'}]
  494|     from . import profiles
  495|     prof = profiles.get(year)
  496|     if prof.get('sources'):
  497|         return prof['sources']  # a profile's own list wins
  498|     census = min(max(year - year % 10, 1790), 2020)
  499|     out = [{'title': f'{census} United States census (population by state, sex, race, nativity and citizenship, via NHGIS)',
  500|             'url': 'https://www.nhgis.org/'}]
  501|     if 1868 <= year <= 2020:
  502|         out.append(SOURCES[1])
  503|     else:
  504|         out.append({'title': 'Dubin, United States Presidential Elections, 1788–1860' if year < 1868 else
  505|                     f'Federal Election Commission, Official {year} Presidential General Election Results',
  506|                     'url': 'https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/'
  507|                     if year > 2020 else 'https://mcfarlandbooks.com/product/united-states-presidential-elections-1788-1860/'})
  508|     out.append({'title': f'National Archives, {year} Electoral College results', 'url': f'https://www.archives.gov/electoral-college/{year}'})
  509|     out.append(SOURCES[4])
  510|     if year < 1920:
  511|         out.append(SOURCES[5])
  512|     if year >= 1840:
  513|         parties = ', '.join(prof.get('full_names', {}).get(k, '') for k in ('R', 'D', 'O') if prof.get('full_names', {}).get(k))
  514|         out.append({'title': f'American Presidency Project, {year} party platforms' + (f' ({parties})' if parties else ''),
  515|                     'url': 'https://www.presidency.ucsb.edu/documents/app-categories/elections-and-transitions/party-platforms'})
  516|     return out
  517| 
  518| 
  519| SOURCES = [
  520|     {'title': 'Fourteenth Census of the United States (1920), Vol. II–III: voting age, color, nativity and citizenship', 'url': 'https://www.census.gov/library/publications/1922/dec/vol-02-population.html'},
  521|     {'title': 'Algara & Amlani, county presidential returns 1868–2020 (Harvard Dataverse, CC0)', 'url': 'https://doi.org/10.7910/DVN/DGUMFI'},
  522|     {'title': 'Clerk of the House, Statistics of the Presidential and Congressional Election of November 2, 1920', 'url': 'https://history.house.gov/Institution/Election-Statistics/'},
  523|     {'title': 'National Archives, 1920 Electoral College results', 'url': 'https://www.archives.gov/electoral-college/1920'},
  524|     {'title': 'Gray & Jenkins, state-level franchise data (Harvard Dataverse, CC0)', 'url': 'https://doi.org/10.7910/DVN/QIY9EM'},
  525|     {'title': 'Teele, women\'s suffrage dates (Harvard Dataverse, CC0)', 'url': 'https://doi.org/10.7910/DVN/JZYGRB'},
  526|     {'title': 'Library of Congress, Chronicling America (period newspapers, dated before 2 Nov 1920)', 'url': 'https://chroniclingamerica.loc.gov/'},
  527| ]
  528| 
```

## `simharness/quotes.py`

```python
    1| """Choosing whose words the page shows, and auditing the reasons behind them.
    2| 
    3| Selection is by representativeness, never by drama:
    4| 1. Within a page slice, a cohort is drawn in proportion to its adults.
    5| 2. Within that cohort, the agent chosen is the one whose change (control →
    6|    counterfactual) is closest to the cohort's median change. Ties go to the
    7|    earliest id; nothing is chosen for vividness.
    8| 3. Across a run's quotes, at least one person whose vote didn't change is
    9|    shown. If none was chosen, the slice with the most such agents swaps its
   10|    pick for its most typical unchanged agent.
   11| 
   12| Every quote keeps its cohort, the adults it stands for, both answers, the date
   13| of its context and the dated sources it cites.
   14| """
   15| from __future__ import annotations
   16| 
   17| import random
   18| import re
   19| 
   20| import numpy as np
   21| 
   22| LABEL_DRIVEN = re.compile(
   23|     r"\b(as an? |being an? |like (most|all|other) )(woman|women|man|men|black|negro|colored|immigrant|foreigner|"
   24|     r"german|irish|italian|pole|swede|catholic|protestant|farmer'?s wife|southerner|northerner|westerner)\b"
   25|     r"|\b(women|negroes|black (people|folks|men|women)|immigrants|foreigners|catholics|southerners|farmers) "
   26|     r"(usually|always|naturally|tend to|are inclined|by nature)\b",
   27|     re.I,
   28| )
   29| 
   30| 
   31| def label_driven(reason: str, sources_used: list) -> bool:
   32|     """Heuristic flag for stereotype-driven logic: reasoning from a group label
   33|     rather than from a circumstance in the brief. The audit sample is also
   34|     read by a person; this flag is the first pass."""
   35|     return bool(LABEL_DRIVEN.search(reason or '')) and not sources_used
   36| 
   37| 
   38| def audit(rows: list[dict], share: float, rng: random.Random, minimum: int = 30) -> dict:
   39|     n = max(minimum, int(round(len(rows) * share)))
   40|     sample = rng.sample(rows, min(n, len(rows)))
   41|     flagged = [r for r in sample if label_driven(r['reason'], r.get('sources_used'))]
   42|     return {'audited': len(sample), 'flagged': len(flagged), 'rate': len(flagged) / max(1, len(sample)),
   43|             'flagged_examples': [{'agent': r['agent'], 'reason': r['reason']} for r in flagged[:10]]}
   44| 
   45| 
   46| def deblind(text: str, label_names: dict) -> str:
   47|     for label, name in label_names.items():
   48|         text = re.sub(rf'\b(?:Candidate|candidate|Mr\.)\s+{label}\b', name, text)
   49|         text = re.sub(rf'(?<![A-Za-z]){label}(?![A-Za-z\'’])', name, text)
   50|     return text
   51| 
   52| 
   53| def select(slices: dict, agents: dict, answers: dict, cohort_adults: dict, seed: int) -> list[dict]:
   54|     """slices: {slice: [cohort keys]}; agents: {id: agent}; answers: {id: {'control', 'cf'}}
   55|     (normalized rows with text). Returns one pick per slice."""
   56|     rng = random.Random(f'quotes:{seed}')
   57|     picks, unchanged_by_slice = [], {}
   58|     for sl, cohorts in slices.items():
   59|         cohorts = [c for c in cohorts if any(a['cohort'] == c and a['id'] in answers for a in agents.values())]
   60|         if not cohorts:
   61|             continue
   62|         c = rng.choices(cohorts, weights=[cohort_adults[x] for x in cohorts])[0]
   63|         members = sorted([a for a in agents.values() if a['cohort'] == c and a['id'] in answers], key=lambda a: a['id'])
   64| 
   65|         def change(a):
   66|             x = answers[a['id']]
   67|             return (x['cf']['p_vote'] * np.nan_to_num(x['cf']['R'])) - (x['control']['p_vote'] * np.nan_to_num(x['control']['R']))
   68| 
   69|         med = float(np.median([change(a) for a in members]))
   70|         pick = min(members, key=lambda a: (abs(change(a) - med), a['id']))
   71|         picks.append({'slice': sl, 'agent': pick, 'cohort': c})
   72|         unchanged_by_slice[sl] = [a for a in members if answers[a['id']]['cf']['choice'] == answers[a['id']]['control']['choice']]
   73|     if picks and not any(answers[p['agent']['id']]['cf']['choice'] == answers[p['agent']['id']]['control']['choice'] for p in picks):
   74|         sl = max(unchanged_by_slice, key=lambda s: len(unchanged_by_slice[s]), default=None)
   75|         if sl and unchanged_by_slice[sl]:
   76|             for p in picks:
   77|                 if p['slice'] == sl:
   78|                     p['agent'] = unchanged_by_slice[sl][0]
   79|                     p['swapped_for_unchanged'] = True
   80|     return picks
```

## `simharness/run.py`

```python
    1| """The pipeline. `python -m simharness.run <stage> --config configs/prototype-1920.json`
    2| 
    3| Stages (each writes into runs/<run id>/ and can be rerun alone):
    4|   backbone   population + backbone fit + the unchanged-run reproduction check
    5|   plan       sample agents and write every model request (no calls)
    6|   ask        send pending requests through the configured backend
    7|   refine     staged what-ifs (D33): audit the answers' reasoning, re-ask failed checks on
    8|              agents.escalate_model, audit those
    9|   analyze    paired effects, leakage probes, label swap, bias, audit, quotes
   10|   publish    every what-if combination → the page's result shape + bundle
   11|   evaluate   validation checks → validation.json (+ EVAL table rows); 1920 only
   12|   verify     any year: the unchanged rerun reproduces every state's R/D/O (R1), plus
   13|              Corder–Wolbrecht where it exists
   14|   dryrun     free: backbone (if needed) → verify → plan, with brief samples and counts
   15|              (`python -m simharness.run dryrun --year 1880`)
   16|   all        backbone → plan → ask → analyze → publish → evaluate
   17| 
   18| Typed what-ifs (intake.py, agent.py): research, stage, whatif [--agent], and for the
   19| research agent: trace, replay, approve, agent-eval (see docs/harness/README.md).
   20| """
   21| from __future__ import annotations
   22| 
   23| import argparse
   24| import json
   25| import sys
   26| 
   27| from .config import ROOT, RunConfig
   28| from .pipeline import LEGISLATURE_EV, Run
   29| from .publish import CONF, KIND_ORDER, SOURCES, briefs_record, census_phrase, pre_interviews, sources_for
   30| 
   31| # The stages live in pipeline.py and publish.py; these names stay importable from here.
   32| __all__ = ['CONF', 'KIND_ORDER', 'LEGISLATURE_EV', 'SOURCES', 'Run', 'briefs_record', 'census_phrase', 'main',
   33|            'pre_interviews', 'sources_for']
   34| 
   35| 
   36| def main(argv=None):
   37|     ap = argparse.ArgumentParser()
   38|     ap.add_argument('stage', choices=['backbone', 'plan', 'ask', 'refine', 'analyze', 'publish', 'evaluate', 'verify', 'dryrun', 'all',
   39|                                       'id', 'research', 'whatif', 'stage', 'trace', 'replay', 'approve', 'agent-eval'])
   40|     ap.add_argument('--config', default=str(ROOT / 'configs/prototype-1920.json'))
   41|     ap.add_argument('--year', type=int, help='use configs/live-<year>.json (instead of --config)')
   42|     ap.add_argument('--samples', type=int, default=1, help='dryrun: briefs to print per slice and per what-if')
   43|     ap.add_argument('--all-cohorts', action='store_true',
   44|                     help='dryrun: ignore the config\'s only_cohorts and arms (every group and arm; a separate run folder)')
   45|     ap.add_argument('--text', help='whatif: the words a reader typed')
   46|     ap.add_argument('--queue', action='store_true', help='whatif: model what the router queued as unknown')
   47|     ap.add_argument('--limit', type=int, default=3, help='whatif --queue: at most this many texts')
   48|     ap.add_argument('--refresh', action='store_true', help='research again even if evidence is saved')
   49|     ap.add_argument('--key', help='research: only this what-if')
   50|     ap.add_argument('--reextract', action='store_true', help='research: extract findings again from the saved notes (no search)')
   51|     ap.add_argument('--agent', action='store_true', help='whatif: the research agent (agent.py) chooses the stages')
   52|     ap.add_argument('--publish', choices=['ask', 'gate', 'never'], default='ask',
   53|                     help='whatif --agent: hold the bundle for approve (ask), put it live if its checks pass (gate), or never')
   54|     ap.add_argument('--dry-run', action='store_true', help='whatif --agent: no writes, interviews or publishing')
   55|     ap.add_argument('--ceiling', type=float, help='whatif --agent, agent-eval: the most one text may spend, in dollars')
   56|     ap.add_argument('--model', help='whatif --agent, replay, agent-eval: the agent\'s model (default: the compile model)')
   57|     ap.add_argument('--id', help='trace, replay, approve: the trace id')
   58|     ap.add_argument('--force', action='store_true', help='approve: even if the bundle fails its checks now')
   59|     args = ap.parse_args(argv)
   60|     if args.year:
   61|         args.config = str(ROOT / f'configs/live-{args.year}.json')
   62|     if args.stage in ('trace', 'replay', 'approve', 'agent-eval') or (args.stage == 'whatif' and args.agent):
   63|         from . import agent, agent_eval, trace
   64|         if args.stage == 'trace':
   65|             out = trace.summary(trace.load(args.id)) | {'id': args.id} if args.id else \
   66|                 {'recent': trace.recent(), 'held': agent.pending()}
   67|         elif args.stage == 'replay':
   68|             out = agent.replay(args.id or ap.error('replay needs --id'), args.model)
   69|         elif args.stage == 'approve':
   70|             out = agent.approve(args.id or ap.error('approve needs --id'), args.force)
   71|         elif args.stage == 'agent-eval':
   72|             out = agent_eval.evaluate(RunConfig.load(args.config).election, args.limit, args.model, args.ceiling or 4.0)
   73|         else:
   74|             out = agent.run(args.text or ap.error('whatif --agent needs --text'), args.config, args.ceiling,
   75|                             agent.Policy(publish=args.publish, dry_run=args.dry_run, model=args.model))
   76|         print(json.dumps(out, indent=1, default=float))
   77|         return
   78|     if args.stage in ('research', 'whatif', 'stage'):
   79|         from . import intake
   80|         if args.stage == 'research':
   81|             out = intake.research_config(args.config, args.refresh, args.key, args.reextract)
   82|         elif args.stage == 'stage':
   83|             out = intake.stage_config(args.config, args.key, args.refresh)
   84|         elif args.queue:
   85|             out = intake.process_queue(args.config, args.limit)
   86|         elif args.text:
   87|             out = intake.whatif(args.text, args.config, args.refresh)
   88|         else:
   89|             ap.error('whatif needs --text or --queue')
   90|         print(json.dumps(out, indent=1, default=float))
   91|         return
   92|     cfg = RunConfig.load(args.config)
   93|     if args.all_cohorts:
   94|         cfg.agents.only_cohorts, cfg.agents.arms = None, None
   95|     run = Run(cfg)
   96|     stages = ['backbone', 'plan', 'ask', 'refine', 'analyze', 'evaluate', 'publish'] if args.stage == 'all' else [args.stage]
   97|     for s in stages:
   98|         if s == 'id':
   99|             print(run.id)
  100|             continue
  101|         if s == 'dryrun':
  102|             out = run.dryrun(args.samples)
  103|             for b in out['briefs']:
  104|                 print(f"\n── {b['arm']} · {b['slice']} · {b['agent']} ──\n{b['user']}")
  105|             print('\ndryrun', json.dumps({k: v for k, v in out.items() if k != 'briefs'}, indent=1, default=float))
  106|             continue
  107|         out = getattr(run, s)()
  108|         print(s, json.dumps(out if not hasattr(out, 'world') else {'fit': 'ok'}, default=float)[:2000])
  109| 
  110| 
  111| if __name__ == '__main__':
  112|     sys.exit(main())
```

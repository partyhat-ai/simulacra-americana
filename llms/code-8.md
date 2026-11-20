# synthetic-electorate-toy: source and docs, part 8 of 16

Generated from commit `93f19ca29232` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `simharness/evaluate.py` to `simharness/paired.py`. Lines are numbered as in the repository.

## `simharness/evaluate.py`

```python
    1| """Validation of the 1920 prototype (EVAL.md). Benchmarks are read only here.
    2| 
    3| Every check returns {id, name, value, threshold, pass, note}. `pass` is True,
    4| False, or None ("not run", with the reason in `note`).
    5| """
    6| from __future__ import annotations
    7| 
    8| import numpy as np
    9| 
   10| from .geo import SOUTH
   11| from .stats import bayes_ols, brier, expit, logit, rmse, spearman
   12| 
   13| 
   14| def check(id_, name, value, threshold, ok, note=''):
   15|     return {'id': id_, 'name': name, 'value': value, 'threshold': threshold, 'pass': ok, 'note': note}
   16| 
   17| 
   18| def r1_reproduction(fit, inp, state_votes) -> dict:
   19|     """state_votes [D, S, 3] from the unchanged world."""
   20|     states = fit.diagnostics['states']
   21|     cert = np.array(inp.returns.reindex(states)[['R20', 'D20', 'O20']].fillna(0), dtype=float)
   22|     cert[[st in (getattr(inp, 'no_popular', None) or ()) for st in states]] = 0.0
   23|     err = np.abs(state_votes - cert[None, :, :])
   24|     worst = float(err.max())
   25|     ev = inp.ev.reindex(states).fillna(0).to_numpy()
   26|     winners = state_votes.argmax(axis=2)
   27|     ev_r = (ev[None, :] * (winners == 0)).sum(axis=1)
   28|     ev_d = (ev[None, :] * (winners == 1)).sum(axis=1)
   29|     ok = worst <= 1.0 and bool(np.all(ev_r == 404)) and bool(np.all(ev_d == 127))
   30|     return check('R1', 'Unchanged rerun reproduces every state exactly', round(worst, 4),
   31|                  '≤ 1 vote per state and party in every draw; EV 404–127 in every draw', ok,
   32|                  f'EV R range {int(ev_r.min())}–{int(ev_r.max())}, D range {int(ev_d.min())}–{int(ev_d.max())}; {state_votes.shape[0]} draws')
   33| 
   34| 
   35| def holdout(fit, inp, holdout_states: list, draws: int, seed: int) -> dict:
   36|     """B1–B5: predict held-out states from training states only."""
   37|     rng = np.random.default_rng(seed + 7)
   38|     dg = fit.diagnostics
   39|     states = dg['states']
   40|     idx = {s: i for i, s in enumerate(states)}
   41|     H = [idx[s] for s in holdout_states]
   42|     Tr = [i for i in range(len(states)) if states[i] not in holdout_states]
   43|     ret = inp.returns.loc[states]
   44|     old = np.array([s in inp.women16 for s in states])
   45|     closed = np.array([s in inp.closed_1920 for s in states])
   46|     south = np.array([s in SOUTH for s in states])
   47|     E16, E20 = dg['E16'], dg['E20']
   48|     T16, T20 = dg['T16'], dg['T20']
   49|     M20, F20, m16 = dg['M20'], dg['F20'], dg['m16']
   50|     D = E16.shape[0]
   51| 
   52|     # κ from training old states only
   53|     tr_old = [i for i in Tr if old[i]]
   54|     k = logit(T20[None, tr_old] / E20[:, tr_old]) - logit(T16[None, tr_old] / E16[:, tr_old])
   55|     kap = k.mean(axis=1)[:, None] + rng.normal(0, 1, (D, len(states))) * k.std(axis=1, ddof=1)[:, None]
   56|     m20 = expit(logit(m16) + kap)
   57|     # ρ from training new non-Southern states
   58|     tr_new = [i for i in Tr if not old[i] and not south[i] and not closed[i]]
   59|     W = T20[None, tr_new] - m20[:, tr_new] * M20[:, tr_new]
   60|     rho = np.clip(W / np.maximum(F20[:, tr_new], 1) / m20[:, tr_new], 0.05, 1.5)
   61|     rho_d = rho[np.arange(D), rng.integers(0, len(tr_new), D)]
   62|     votes_hat = m20 * M20 + np.where(closed, 0, rho_d[:, None] * m20 * F20)
   63|     # Old states: 1916 votes already included women's, so project turnout per
   64|     # eligible adult by κ, as the backbone's T1 does. (Fixed after the first
   65|     # evaluation used men's-only m16 here; see EVAL.md, deviations.)
   66|     t_old = expit(logit(T16[None, :] / E16) + kap) * E20
   67|     votes_hat = np.where(old[None, :], t_old, votes_hat)
   68|     sidx = np.array([idx[s] for s in fit.cells.state])
   69|     A = np.zeros((D, len(states)))
   70|     np.add.at(A, (slice(None), sidx), fit.world.adults)
   71|     turn_hat = votes_hat / A
   72|     turn_act = T20[None, :] / A
   73|     # Persistence: 1916 votes ÷ 1916 adults
   74|     A16 = np.zeros(len(states))
   75|     np.add.at(A16, sidx, fit.cells.adults16.to_numpy())
   76|     turn_persist = T16 / A16
   77| 
   78|     # Two-party share: swing + women's tilt, fitted on training states
   79|     rd16 = logit((ret.R16 / (ret.R16 + ret.D16)).to_numpy())
   80|     rd20 = logit((ret.R20 / (ret.R20 + ret.D20)).to_numpy())
   81|     f_hat = np.where(~old & ~closed, 1 - (m20 * M20) / np.maximum(votes_hat, 1), 0.0)
   82|     pred = np.empty((D, len(H)))
   83|     for d in range(D):
   84|         f_tr = np.where(~old & ~closed, dg['votes_F'][d] / T20, 0.0)
   85|         X = np.column_stack([~south, south, f_tr]).astype(float)[Tr]
   86|         b, sig, _ = bayes_ols(X, (rd20 - rd16)[Tr], 1, rng)
   87|         Xh = np.column_stack([~south, south, f_hat[d]]).astype(float)[H]
   88|         pred[d] = rd16[H] + Xh @ b[0] + rng.normal(0, sig[0], len(H))
   89|     share_hat = expit(np.median(pred, axis=0)) * 100
   90|     actual = expit(rd20[H]) * 100
   91|     # Baselines
   92|     w = (ret.R20 + ret.D20).to_numpy()
   93|     persist = expit(rd16[H]) * 100
   94|     swing = np.average((rd20 - rd16)[Tr], weights=w[Tr])
   95|     uniform = expit(rd16[H] + swing) * 100
   96|     us_sd = float(np.std((rd20 - rd16)[Tr] - swing, ddof=1))
   97|     # Demographic regression (no lag)
   98|     comp = composition(fit, states)
   99|     Xd = np.column_stack([np.ones(len(states)), south, comp['black'], comp['foreign'], comp['new_women']])
  100|     bd, *_ = np.linalg.lstsq(Xd[Tr], rd20[Tr], rcond=None)
  101|     demo = expit(Xd[H] @ bd) * 100
  102| 
  103|     p_win = (pred > 0).mean(axis=0)
  104|     p_us = 1 - _norm_cdf(-(rd16[H] + swing) / us_sd)
  105|     won = (rd20[H] > 0).astype(float)
  106|     ev = inp.ev.loc[holdout_states].to_numpy()
  107|     ev_pred = float(np.sum(ev * (share_hat > 50)))
  108|     ev_act = float(np.sum(ev * won))
  109|     close = [s for s, a in zip(holdout_states, actual) if abs(a - 50) * 2 < 5]
  110|     ev_tol = float(min(inp.ev.loc[close])) if close else 0.0
  111| 
  112|     b1 = rmse(share_hat, actual)
  113|     b2 = rmse(np.median(turn_hat[:, H], axis=0) * 100, np.median(turn_act[:, H], axis=0) * 100)
  114|     b2p = rmse(turn_persist[H] * 100, np.median(turn_act[:, H], axis=0) * 100)
  115|     rows = [{'state': s, 'actual': round(float(a), 2), 'backbone': round(float(p), 2), 'persistence': round(float(q), 2),
  116|              'uniform_swing': round(float(u), 2), 'demographic': round(float(g), 2), 'p_R_win': round(float(pw), 3),
  117|              'turnout_actual': round(float(np.median(turn_act[:, i]) * 100), 1),
  118|              'turnout_backbone': round(float(np.median(turn_hat[:, i]) * 100), 1),
  119|              'turnout_persistence': round(float(turn_persist[i] * 100), 1)}
  120|             for s, a, p, q, u, g, pw, i in zip(holdout_states, actual, share_hat, persist, uniform, demo, p_win, H)]
  121|     checks = [
  122|         check('B1', 'Holdout two-party RMSE (points)', {'backbone': round(b1, 2), 'uniform_swing': round(rmse(uniform, actual), 2),
  123|               'persistence': round(rmse(persist, actual), 2), 'demographic': round(rmse(demo, actual), 2)},
  124|               'backbone ≤ uniform swing and ≤ persistence', b1 <= rmse(uniform, actual) and b1 <= rmse(persist, actual)),
  125|         check('B2', 'Holdout turnout RMSE (points of adults 21+)', {'backbone': round(b2, 2), 'persistence': round(b2p, 2)},
  126|               'backbone ≤ persistence', b2 <= b2p),
  127|         check('B3', 'Holdout Spearman ρ, two-party share', round(spearman(share_hat, actual), 3), '≥ 0.8',
  128|               spearman(share_hat, actual) >= 0.8),
  129|         check('B4', 'Holdout Brier score, state winner', {'backbone': round(brier(p_win, won), 4), 'uniform_swing': round(brier(p_us, won), 4)},
  130|               'backbone ≤ uniform swing', brier(p_win, won) <= brier(p_us, won)),
  131|         check('B5', 'Holdout electoral-vote error (Harding)', abs(ev_pred - ev_act), f'≤ {ev_tol:g}',
  132|               abs(ev_pred - ev_act) <= ev_tol, f'predicted {ev_pred:g}, actual {ev_act:g}; states decided by < 5 points: {close or "none"}'),
  133|     ]
  134|     return {'checks': checks, 'rows': rows}
  135| 
  136| 
  137| def _norm_cdf(x):
  138|     from scipy.stats import norm
  139|     return norm.cdf(x)
  140| 
  141| 
  142| def composition(fit, states) -> dict:
  143|     c = fit.cells
  144|     a = c.groupby('state').adults20.sum()
  145|     blk = c[c.group == 'black'].groupby('state').adults20.sum().reindex(states, fill_value=0) / a.reindex(states)
  146|     fb = c[c.group.str.startswith('foreign')].groupby('state').adults20.sum().reindex(states, fill_value=0) / a.reindex(states)
  147|     nw = c[(c.sex == 'F') & (c.group != 'foreign_white_alien')].groupby('state').adults20.sum().reindex(states, fill_value=0) / a.reindex(states)
  148|     old = fit.diagnostics['old_states']
  149|     nw = nw.where(~nw.index.isin(old), 0.0)
  150|     return {'black': blk.to_numpy(), 'foreign': fb.to_numpy(), 'new_women': nw.to_numpy()}
```

## `simharness/evidence.py`

```python
    1| """Historical evidence for a what-if: what reliable sources say about how the
    2| same people behaved in the same situation, or the nearest one on record.
    3| 
    4| Two model calls per what-if, both logged with their cost:
    5| 
    6| 1. **Research** (web search): a historian's research assistant looks for
    7|    peer-reviewed work, academic books, official statistics and archives on
    8|    (a) the change itself, if it happened or nearly did, (b) the same
    9|    populations in the most similar situations, nearest in time first, and
   10|    (c) what any named real person actually said or did on or before the
   11|    context date. Answers carry citations to pages the search returned.
   12| 2. **Extraction** (structured output): the notes become findings. A finding
   13|    may cite only sources the search actually returned (`S1`…); anything else
   14|    is dropped. Structured outputs can't be combined with web-search
   15|    citations in one call, hence two calls.
   16| 
   17| Evidence never enters a voter's brief. The agents stay blind to it, and to
   18| anything dated after the context cutoff. It is used after the interviews:
   19| 
   20| - **evaluate**: does the interviews' effect agree with the historical
   21|   record in direction and size?
   22| - **blend** (exploratory what-ifs only): the evidence becomes a prior on
   23|   each cohort's effect, combined with the interview effect by precision.
   24| - **confidence**: a tier from high to very low ("extremely low"), with the
   25|   reasons shown to the reader.
   26| 
   27| Hand-written what-ifs use evidence only to evaluate and grade confidence.
   28| Their numbers follow METHOD.md.
   29| """
   30| from __future__ import annotations
   31| 
   32| import json
   33| import re
   34| import time
   35| from urllib.parse import urlparse
   36| 
   37| import numpy as np
   38| 
   39| from .stats import expit, logit
   40| 
   41| EVIDENCE_VERSION = 'e1'
   42| 
   43| # ── Source reliability ──
   44| # A: peer-reviewed, academic press, official statistics, archives.
   45| # B: reputable reference works and public history.
   46| # C: tertiary or unknown: a pointer to evidence, not evidence.
   47| TIER_A = (
   48|     'jstor.org', 'doi.org', 'muse.jhu.edu', 'cambridge.org', 'academic.oup.com', 'global.oup.com', 'oup.com',
   49|     'tandfonline.com', 'journals.uchicago.edu', 'onlinelibrary.wiley.com', 'journals.sagepub.com',
   50|     'link.springer.com', 'sciencedirect.com', 'nber.org', 'dataverse.harvard.edu', 'icpsr.umich.edu',
   51|     'presidency.ucsb.edu', 'millercenter.org', 'history.house.gov', 'senate.gov', 'loc.gov', 'archives.gov',
   52|     'census.gov', 'nps.gov', 'press.princeton.edu', 'press.uchicago.edu', 'escholarship.org', 'historians.org', 'oah.org', 'aeaweb.org', 'apsanet.org',
   53|     'journalofamericanhistory.org', 'americanhistory.si.edu', 'fraser.stlouisfed.org', 'hathitrust.org',
   54|     'archive.org', 'chroniclingamerica.loc.gov', 'jhu.edu', 'harvard.edu', 'yale.edu', 'stanford.edu',
   55| )
   56| TIER_A_SUFFIX = ('.edu', '.gov', '.ac.uk')
   57| TIER_A_PREFIX = ('upress.', 'scholarship.', 'journals.', 'press.')  # university presses and journal hosts
   58| TIER_B = (
   59|     'britannica.com', 'smithsonianmag.com', 'si.edu', 'pbs.org', 'npr.org', 'gilderlehrman.org',
   60|     'americanyawp.com', 'ncpedia.org', 'tshaonline.org', 'mnopedia.org', 'encyclopediavirginia.org',
   61|     'georgiaencyclopedia.org', 'encyclopediaofalabama.org', 'ohiohistory.org', 'wisconsinhistory.org',
   62|     'history.state.gov', 'nytimes.com', 'theatlantic.com', 'washingtonpost.com', 'newyorker.com',
   63|     'bbc.co.uk', 'bbc.com', 'historynet.com', 'americanheritage.com', 'blackpast.org', 'womenshistory.org',
   64|     'mnhs.org', 'kshs.org', 'indianahistory.org', 'historycooperative.org', 'uselectionatlas.org',
   65| )
   66| TIER_WEIGHT = {'A': 1.0, 'B': 0.6, 'C': 0.25}
   67| 
   68| # Never worth a search result.
   69| BLOCKED = ['reddit.com', 'quora.com', 'pinterest.com', 'youtube.com', 'tiktok.com', 'facebook.com', 'x.com',
   70|            'twitter.com', 'answers.com', 'coursehero.com', 'studocu.com', 'chegg.com', 'brainly.com',
   71|            'enotes.com', 'gradesaver.com', 'ipl.org', 'bartleby.com', 'ukessays.com', 'studymoose.com']
   72| 
   73| MATCH_WEIGHT = {'same-event': 1.0, 'same-period-similar': 0.7, 'other-period-similar': 0.45, 'distant': 0.2}
   74| 
   75| FLIP = {'toward-R': 'toward-D', 'toward-D': 'toward-R', 'more-turnout': 'less-turnout', 'less-turnout': 'more-turnout',
   76|         'toward-other': 'mixed'}
   77| 
   78| SEARCH_DOLLARS = 10 / 1000  # web search: $10 per 1,000 searches
   79| 
   80| 
   81| def tier_of(url: str) -> str:
   82|     host = (urlparse(url).hostname or '').lower().removeprefix('www.')
   83|     if 'wikipedia.org' in host:
   84|         return 'C'
   85|     if any(host == d or host.endswith('.' + d) for d in TIER_A) or host.endswith(TIER_A_SUFFIX) or host.startswith(TIER_A_PREFIX):
   86|         return 'A'
   87|     if any(host == d or host.endswith('.' + d) for d in TIER_B):
   88|         return 'B'
   89|     return 'C'
   90| 
   91| 
   92| # ── 1. Research: web search, citations kept ──
   93| 
   94| RESEARCH_SYSTEM = """You are a research assistant to a historian of American elections. You search the web for reliable evidence and report it with citations.
   95| 
   96| What counts as reliable, best first:
   97| 1. Peer-reviewed journal articles and academic books by historians or political scientists.
   98| 2. Official statistics and archival collections: the Census Bureau, the Clerk of the House, the Library of Congress, the National Archives, state archives.
   99| 3. Reputable reference works: Britannica, university-hosted or state-historical-society encyclopedias.
  100| Use Wikipedia only to find sources of the first three kinds; never rest a finding on it alone. Ignore forums, content farms, homework and essay sites.
  101| 
  102| Report, in this order:
  103| 1. Direct evidence. If this change happened, or nearly happened, what scholars say about its effect on voters and turnout.
  104| 2. Analogues. The same populations in the most similar situations on record, nearest in time and place first. Give numbers wherever the sources do: turnout, vote shares, swings, by group. Say when and where each happened.
  105| 3. Named people. For any real person the scenario names, what they actually said or did about the relevant questions on or before the scenario's date, with dates. Describe it; don't quote at length.
  106| 4. Limits. Why each analogue might not carry over.
  107| 
  108| Search before you write: run at least two searches, and more for anything you'd otherwise state from memory. A claim without a citation will be thrown away, however well you know it. Cite every factual sentence. Give changes in percentage points where you can. If you find nothing reliable, say so plainly. Don't stretch a weak source into a strong claim."""
  109| 
  110| 
  111| def research_prompt(spec: dict, election: dict) -> str:
  112|     reach = spec.get('reach') or {}
  113|     who = ', '.join(f'{k}: {", ".join(v)}' for k, v in reach.items() if v) or 'every voter'
  114|     lines = [
  115|         f'Scenario for the {election["year"]} United States presidential election (election day {election["day"]}).',
  116|         f'A reader asked: "{spec.get("source_text") or spec["label"]}".',
  117|         f'As modelled: {spec["detail"]}',
  118|         f'Kind of change: {spec["kind"]}. Populations it reaches first: {who}.',
  119|     ]
  120|     if (spec.get('candidate') or {}).get('name'):
  121|         c = spec['candidate']
  122|         lines.append(f'Named person on the ballot: {c["name"]} ({c.get("descriptor", "")}).')
  123|     hint = {
  124|         'candidate': 'Include the strongest third-party and independent runs nearest in time (1912 and 1924 above all), '
  125|                      'which groups they drew from and what share they took; and any run by a famous non-politician.',
  126|         'franchise': 'Include how newly enfranchised or newly barred groups actually turned out and voted the first times '
  127|                      'the rules changed for them.',
  128|         'population': 'Include how the groups whose numbers change turned out and voted in nearby elections.',
  129|     }.get(spec['kind'], 'Include how the same groups swung, by how much, when comparable issues or shocks hit nearby elections.')
  130|     lines.append(hint)
  131|     qs = spec.get('research_questions') or []
  132|     if qs:
  133|         lines += ['', 'Questions to answer:'] + [f'- {q}' for q in qs]
  134|     from .agentlayer import groups_for
  135|     phrase = groups_for(int(election['year']))['phrase']
  136|     lines += ['', f'Groups the simulation distinguishes: men and women; {phrase} adults; '
  137|                   f'the Northeast, Midwest, South (the eleven former '
  138|                   f'Confederate states), border states and West. Evidence by these groups is most useful.']
  139|     return '\n'.join(lines)
  140| 
  141| 
  142| def research(client, spec: dict, election: dict, model: str, max_uses: int = 4, effort: str = 'low',
  143|              max_tokens: int = 6000) -> dict:
  144|     """One web-search research turn (continuing through pause_turn). Returns
  145|     {text (with [S#] markers), sources: [{id, url, title, tier, cited, page_age}], queries, usage, dollars}."""
  146|     from . import llm
  147|     tools = [{'type': 'web_search_20250305', 'name': 'web_search', 'max_uses': max_uses, 'blocked_domains': BLOCKED}]
  148|     user = research_prompt(spec, election)
  149|     params = {'model': model, 'max_tokens': max_tokens, 'system': RESEARCH_SYSTEM, 'tools': tools}
  150|     if 'haiku' not in model:
  151|         params['output_config'] = {'effort': effort}
  152|     usage, searches = {'input_tokens': 0, 'output_tokens': 0, 'cache_read_input_tokens': 0, 'cache_creation_input_tokens': 0}, 0
  153|     for attempt in range(2):
  154|         assistant = []
  155|         ask = user if attempt == 0 else user + ('\n\nSearch first. Your last answer ran no searches, so none of it could be '
  156|                                                 'used: every claim needs a citation to a page the search returns.')
  157|         for _ in range(4):
  158|             messages = [{'role': 'user', 'content': ask}] + ([{'role': 'assistant', 'content': assistant}] if assistant else [])
  159|             msg = _create(client, messages=messages, **params)
  160|             assistant += list(msg.content)
  161|             u = msg.usage
  162|             for k in usage:
  163|                 usage[k] += getattr(u, k, 0) or 0
  164|             stu = getattr(u, 'server_tool_use', None)
  165|             searches += (getattr(stu, 'web_search_requests', 0) or 0) if stu else 0
  166|             if msg.stop_reason != 'pause_turn':
  167|                 break
  168|         if any(getattr(b, 'type', None) == 'web_search_tool_result' for b in assistant):
  169|             break  # a turn without a single search is retried once, then kept as it is
  170|     sources, by_url, queries, parts = [], {}, [], []
  171| 
  172|     def src(url, title, page_age=None):
  173|         if url not in by_url:
  174|             by_url[url] = f'S{len(sources) + 1}'
  175|             sources.append({'id': by_url[url], 'url': url, 'title': title or url, 'tier': tier_of(url),
  176|                             'cited': [], 'page_age': page_age})
  177|         return by_url[url]
  178| 
  179|     for b in assistant:
  180|         t = getattr(b, 'type', None)
  181|         if t == 'server_tool_use':
  182|             queries.append((getattr(b, 'input', None) or {}).get('query'))
  183|         elif t == 'web_search_tool_result':
  184|             content = getattr(b, 'content', None)
  185|             if isinstance(content, list):
  186|                 for r in content:
  187|                     if getattr(r, 'type', None) == 'web_search_result':
  188|                         src(r.url, r.title, getattr(r, 'page_age', None))
  189|         elif t == 'text':
  190|             ids = []
  191|             for c in getattr(b, 'citations', None) or []:
  192|                 url = getattr(c, 'url', None)
  193|                 if not url:
  194|                     continue
  195|                 sid = src(url, getattr(c, 'title', None))
  196|                 cited = (getattr(c, 'cited_text', '') or '').strip()
  197|                 if cited and cited not in sources[int(sid[1:]) - 1]['cited']:
  198|                     sources[int(sid[1:]) - 1]['cited'].append(cited[:400])
  199|                 ids.append(sid)
  200|             parts.append(b.text + (' [' + ', '.join(dict.fromkeys(ids)) + ']' if ids else ''))
  201|     dollars = llm.cost(model, usage) + searches * SEARCH_DOLLARS
  202|     return {'text': ''.join(parts).strip(), 'sources': sources, 'queries': [q for q in queries if q],
  203|             'usage': usage | {'web_search_requests': searches}, 'dollars': round(dollars, 4), 'model': model,
  204|             'prompt': user}
  205| 
  206| 
  207| def research_estimate(model: str, max_uses: int, max_tokens: int = 6000) -> dict:
  208|     """Search results are the bulk of a research call's input: about 8k tokens a
  209|     search, re-read on each server-side step."""
  210|     from . import llm
  211|     typical = llm.cost(model, {'input_tokens': 15000 * max_uses, 'output_tokens': 2500}) + max(1, max_uses - 1) * SEARCH_DOLLARS
  212|     worst = llm.cost(model, {'input_tokens': 12000 * max_uses * (max_uses + 1) // 2 + 3000, 'output_tokens': max_tokens}) + max_uses * SEARCH_DOLLARS
  213|     return {'typical': round(typical, 4), 'worst': round(worst, 4)}
  214| 
  215| 
  216| # ── 2. Extraction: notes → findings, grounded in the returned sources ──
  217| 
  218| EXTRACT_SYSTEM = """You turn a research assistant's notes into structured findings for an election simulation.
  219| 
  220| Rules:
  221| - Extract every claim in the notes that carries a source marker like [S3] and says something about how people voted or turned out, including the loose analogues. Don't judge reliability yourself: the pipeline grades each source and each match afterwards and weights them. A finding resting on Wikipedia is still a finding.
  222| - Copy the source ids exactly. Add nothing from your own knowledge.
  223| - At most 12 findings, the most informative first; merge claims about the same situation. Keep each claim under 35 words, situation and limits under 20.
  224| - Keep loose analogues too, graded by match ("distant" when the situation only loosely resembles the scenario): they are weighted down, not thrown away. Leave out only claims that say nothing about how people voted or turned out.
  225| - population: the group the finding is about. Use "any" where the finding doesn't narrow it.
  226| - match: how close the finding's situation is to the scenario. "same-event": this very change, in this very election. "same-period-similar": a similar situation within about a dozen years. "other-period-similar": a similar situation further away. "distant": a loose analogy.
  227| - effects: numbers only when the notes give them, as percentage-point changes caused by the situation: "turnout" (share of eligible adults voting), "r2" (the Republican share of the two-party vote; positive means more Republican), "other" (the share of all votes going to a third candidate or party). pm is the plus-or-minus the notes give or imply; use half the effect's size when they give none. Leave effects empty when the notes give no number.
  228| - direction and effects describe what happened in the finding's own situation, as the sources report it. Never flip them yourself.
  229| - relation says how that situation maps onto the scenario: "like-scenario" when the scenario would bring about the same kind of situation (a third-party run, for a third-party scenario); "reverses-scenario" when the scenario removes or undoes it (the scenario settles an issue that in fact cost a party votes); "context" when it only describes the election or its setting without showing how people responded to a comparable change (who won, overall turnout). The pipeline flips reversed findings and sets context aside.
  230| - direction: the finding's direction even without numbers, in that election's own party terms.
  231| - role_direction: when the scenario concerns one nominee (the affected candidate, named below), which way the finding's voters moved relative to the candidate who stood in the same role in the finding's own situation (the scandal-hit candidate, say), whatever his party: "toward-affected" or "away-from-affected". "none" when there is no such role. Give its size, when the notes do, as the effect measure "affected": the change in that candidate's share of the two-party vote, in points.
  232| - actor_positions: for a named real person, what they said or did on or before the scenario's date, in a neutral dated paraphrase (never a quotation), with its source ids.
  233| - no_reliable_evidence: true only when there are no findings at all, or every one is a loose ("distant") analogy."""
  234| 
  235| POP = {'type': 'object', 'properties': {
  236|     'sex': {'type': 'string', 'enum': ['any', 'M', 'F']},
  237|     'group': {'type': 'string', 'enum': ['any', 'native_white', 'foreign_white_naturalized', 'foreign_white_alien', 'black']},
  238|     'region': {'type': 'string', 'enum': ['any', 'northeast', 'midwest', 'south', 'border', 'west']},
  239| }, 'required': ['sex', 'group', 'region'], 'additionalProperties': False}
  240| 
  241| EXTRACT_SCHEMA = {
  242|     'type': 'object',
  243|     'properties': {
  244|         'summary': {'type': 'string'},
  245|         'findings': {'type': 'array', 'items': {'type': 'object', 'properties': {
  246|             'claim': {'type': 'string'},
  247|             'source_ids': {'type': 'array', 'items': {'type': 'string'}},
  248|             'population': POP,
  249|             'situation': {'type': 'string'},
  250|             'when': {'type': 'string'},
  251|             'match': {'type': 'string', 'enum': list(MATCH_WEIGHT)},
  252|             'relation': {'type': 'string', 'enum': ['like-scenario', 'reverses-scenario', 'context']},
  253|             'role_direction': {'type': 'string', 'enum': ['toward-affected', 'away-from-affected', 'none']},
  254|             'direction': {'type': 'string', 'enum': ['toward-R', 'toward-D', 'toward-other', 'more-turnout',
  255|                                                      'less-turnout', 'mixed', 'none', 'unclear']},
  256|             'effects': {'type': 'array', 'items': {'type': 'object', 'properties': {
  257|                 'measure': {'type': 'string', 'enum': ['turnout', 'r2', 'other', 'affected']},
  258|                 'pp': {'type': 'number'}, 'pm': {'type': 'number'},
  259|             }, 'required': ['measure', 'pp', 'pm'], 'additionalProperties': False}},
  260|             'limits': {'type': 'string'},
  261|         }, 'required': ['claim', 'source_ids', 'population', 'situation', 'when', 'match', 'relation', 'role_direction', 'direction',
  262|                         'effects', 'limits'],
  263|             'additionalProperties': False}},
  264|         'actor_positions': {'type': 'array', 'items': {'type': 'object', 'properties': {
  265|             'text': {'type': 'string'}, 'date': {'type': 'string'},
  266|             'source_ids': {'type': 'array', 'items': {'type': 'string'}},
  267|         }, 'required': ['text', 'date', 'source_ids'], 'additionalProperties': False}},
  268|         'caveats': {'type': 'array', 'items': {'type': 'string'}},
  269|         'no_reliable_evidence': {'type': 'boolean'},
  270|     },
  271|     'required': ['summary', 'findings', 'actor_positions', 'caveats', 'no_reliable_evidence'],
  272|     'additionalProperties': False,
  273| }
  274| 
  275| 
  276| def extract_request(spec: dict, notes: dict, model: str) -> dict:
  277|     table = '\n'.join(f'{s["id"]}: {s["title"]} ({urlparse(s["url"]).hostname}, reliability {s["tier"]})' for s in notes['sources'])
  278|     from .profiles import get
  279|     full = get(spec.get('year', 1920))['full_names']
  280|     role = {'R': f'the Republican nominee ({full["R"]})', 'D': f'the Democratic nominee ({full["D"]})'}.get(spec.get('about'))
  281|     who = f'\nThe affected candidate: {role}.' if role else '\nThe scenario concerns neither nominee personally: role_direction is "none".'
  282|     user = (f'Scenario: {spec["detail"]}{who}\n\nSources the search returned:\n{table or "(none)"}\n\n'
  283|             f'Research notes:\n{notes["text"] or "(the assistant found nothing)"}')
  284|     return {'id': f'extract|{spec["key"]}', 'model': model, 'system': EXTRACT_SYSTEM, 'user': user,
  285|             'schema': EXTRACT_SCHEMA, 'meta': {'kind': 'extract', 'what_if': spec['key']}}
  286| 
  287| 
  288| def ground(extracted: dict, notes: dict, about: str | None = None) -> dict:
  289|     """Keep only findings whose sources the search returned; grade each. about: the nominee
  290|     ('R' or 'D') the scenario concerns; findings from other elections then count by role
  291|     (toward the scandal-hit candidate, say), not by that year's party labels (D22)."""
  292|     by_id = {s['id']: s for s in notes['sources']}
  293|     findings, dropped = [], 0
  294|     for f in extracted.get('findings', []):
  295|         ids = [i for i in f.get('source_ids', []) if i in by_id]
  296|         if not ids:
  297|             dropped += 1
  298|             continue
  299|         tier = min((by_id[i]['tier'] for i in ids), key='ABC'.index)
  300|         # A finding resting only on tertiary sources is kept as a pointer, down-weighted.
  301|         grade = TIER_WEIGHT[tier] * MATCH_WEIGHT.get(f['match'], 0.2)
  302|         effects = [e for e in f.get('effects', []) if abs(e.get('pp', 0)) <= 60]
  303|         direction = f['direction']
  304|         if about in ('R', 'D'):
  305|             sign = 1 if about == 'R' else -1
  306|             rd = f.get('role_direction', 'none')
  307|             if rd != 'none':
  308|                 toward = about if rd == 'toward-affected' else ('D' if about == 'R' else 'R')
  309|                 direction = f'toward-{toward}'
  310|             # the affected candidate's two-party share, as the Republican two-party share
  311|             effects = [e for e in effects if e['measure'] != 'r2'] + \
  312|                       [e | {'measure': 'r2', 'pp': sign * e['pp']} for e in effects if e['measure'] == 'affected']
  313|         effects = [e for e in effects if e['measure'] != 'affected']
  314|         rel = f.get('relation', 'like-scenario')
  315|         if rel == 'reverses-scenario':  # the scenario undoes this situation: its effect runs the other way
  316|             direction = FLIP.get(direction, direction)
  317|             effects = [e | {'pp': -e['pp']} for e in effects if e['measure'] != 'other']
  318|         elif rel == 'context':
  319|             direction, effects = 'none', []
  320|         findings.append({**f, 'source_ids': ids, 'tier': tier, 'grade': round(grade, 3), 'effects': effects,
  321|                          'direction': direction, 'reported_direction': f['direction']})
  322|     positions = [p | {'source_ids': [i for i in p['source_ids'] if i in by_id]} for p in extracted.get('actor_positions', [])]
  323|     positions = [p for p in positions if p['source_ids']]
  324|     return {'summary': extracted.get('summary', ''), 'findings': findings, 'actor_positions': positions,
  325|             'caveats': extracted.get('caveats', []), 'dropped_ungrounded': dropped,
  326|             'no_reliable_evidence': bool(extracted.get('no_reliable_evidence')) or not findings}
  327| 
  328| 
  329| def strength(ev: dict | None) -> dict:
  330|     """strong ≥ 0.7, moderate ≥ 0.4, weak > 0, none. The best informative
  331|     finding's grade, plus a little for corroboration (others graded ≥ 0.3)."""
  332|     # Only findings that say which way people moved, or by how much, speak to the change;
  333|     # context (turnout that year, who went to the pictures) informs the reader but not the strength.
  334|     fs = [f for f in (ev or {}).get('findings', []) if f['effects'] or f['direction'] not in ('none', 'unclear', 'mixed')]
  335|     if not fs:
  336|         return {'level': 'none', 'score': 0.0, 'best': None}
  337|     fs = sorted(fs, key=lambda f: -f['grade'])
  338|     score = fs[0]['grade'] + 0.1 * sum(1 for f in fs[1:4] if f['grade'] >= 0.3)
  339|     score = min(score, 1.0)
  340|     level = 'strong' if score >= 0.7 else 'moderate' if score >= 0.4 else 'weak'
  341|     return {'level': level, 'score': round(score, 3), 'best': fs[0]['claim']}
  342| 
  343| 
  344| # ── 3. Evidence as a prior on cohort effects ──
  345| 
  346| def _applies(pop: dict, cohort: dict) -> bool:
  347|     if pop['sex'] != 'any' and pop['sex'] != cohort['sex']:
  348|         return False
  349|     if pop['group'] != 'any' and pop['group'] != cohort['group']:
  350|         return False
  351|     if pop['region'] != 'any' and pop['region'] not in cohort.get('regions', [cohort.get('region')]):
  352|         return False
  353|     return True
  354| 
  355| 
  356| def prior(ev: dict, cohort: dict, base: dict) -> dict:
  357|     """{dt, dr, do: (mean, sd) on the logit scale} for one cohort, from the
  358|     graded, quantified findings that apply to it. base: the cohort's backbone
  359|     {turnout, r2, o}. A specific finding (group or region named) counts twice
  360|     a general one. Weak evidence gives a wide prior: sd ∝ 1/√grade."""
  361|     out = {}
  362|     for measure, key, b in (('turnout', 'dt', base['turnout']), ('r2', 'dr', base['r2']), ('other', 'do', base['o'])):
  363|         rows = []
  364|         for f in ev.get('findings', []):
  365|             if not _applies(f['population'], cohort):
  366|                 continue
  367|             specific = 2.0 if (f['population']['group'] != 'any' or f['population']['region'] != 'any') else 1.0
  368|             for e in f['effects']:
  369|                 if e['measure'] == measure:
  370|                     rows.append((e['pp'], max(abs(e['pm']), 2.0), f['grade'] * specific))
  371|         if not rows:
  372|             continue
  373|         w = np.array([r[2] for r in rows])
  374|         pp = float(np.average([r[0] for r in rows], weights=w))
  375|         spread = float(np.sqrt(np.average([(r[0] - pp) ** 2 for r in rows], weights=w)))
  376|         pm = float(np.average([r[1] for r in rows], weights=w))
  377|         g = float(min(1.0, w.max()))
  378|         sd_pp = np.sqrt(pm ** 2 + spread ** 2 + 3.0 ** 2) / np.sqrt(max(g, 0.05))
  379|         b = float(np.clip(b, 0.01, 0.99))
  380|         new = float(np.clip(b + pp / 100, 0.005, 0.995))
  381|         out[key] = (float(logit(new) - logit(b)), float(sd_pp / 100 / (b * (1 - b))), len(rows))
  382|     return out
  383| 
  384| 
  385| def blend(cohort_eff: dict, pri: dict) -> dict:
  386|     """Precision-weighted combination of a cohort's interview draws with the
  387|     evidence prior. The draws keep their shape, rescaled to the posterior sd."""
  388|     draws = {k: np.asarray(v, float).copy() for k, v in cohort_eff['draws'].items()}
  389|     used = {}
  390|     for key, (mu_e, sd_e, n) in pri.items():
  391|         d = draws[key]
  392|         # A bootstrap over two or three people understates how wrong the model can be;
  393|         # floor it near the Sonnet–Opus disagreement on the same people (D8, ~0.15 logit).
  394|         mu_a, sd_a = float(d.mean()), max(float(d.std()), 0.2)
  395|         prec_a, prec_e = 1 / sd_a ** 2, 1 / sd_e ** 2
  396|         mu_p = (mu_a * prec_a + mu_e * prec_e) / (prec_a + prec_e)
  397|         sd_p = (prec_a + prec_e) ** -0.5
  398|         draws[key] = mu_p + (d - mu_a) * (sd_p / sd_a)
  399|         used[key] = {'agents': round(mu_a, 3), 'evidence': round(mu_e, 3), 'evidence_sd': round(sd_e, 3),
  400|                      'evidence_weight': round(prec_e / (prec_a + prec_e), 3), 'posterior': round(mu_p, 3), 'findings': n}
  401|     return {**cohort_eff, 'draws': draws, 'evidence_blend': used}
  402| 
  403| 
  404| # ── 4. Agreement and confidence ──
  405| 
  406| def _agree_one(ev: dict, national: dict, measure: str, key: str, b: float) -> dict | None:
  407|     """One measure: the interviews' national effect (logit, 80% interval) against the findings, in points."""
  408|     agent_pp = (float(expit(logit(b) + national[key]['mean'])) - b) * 100
  409|     lo = (float(expit(logit(b) + national[key]['lo'])) - b) * 100
  410|     hi = (float(expit(logit(b) + national[key]['hi'])) - b) * 100
  411|     what = {'other': 'the third candidate\'s share', 'r2': 'the Republican two-party share', 'turnout': 'turnout'}[measure]
  412|     rows = [(e['pp'], abs(e['pm']), f['grade']) for f in ev['findings'] for e in f['effects'] if e['measure'] == measure]
  413|     if not rows:
  414|         want = {'r2': ('toward-R', 'toward-D'), 'other': ('toward-other', None), 'turnout': ('more-turnout', 'less-turnout')}[measure]
  415|         signs = [1 if f['direction'] == want[0] else -1 for f in ev['findings'] if f['grade'] >= 0.1 and f['direction'] in want]
  416|         if not signs:
  417|             return None
  418|         s = np.sign(np.mean(signs))
  419|         ok = np.sign(agent_pp) == s or abs(agent_pp) < 0.5
  420|         return {'verdict': 'consistent' if ok else 'contradicted', 'measure': measure, 'agents_pp': round(agent_pp, 1),
  421|                 'detail': f'On {what}, the sources point {"the same way as" if ok else "the other way from"} the interviews '
  422|                           f'({agent_pp:+.1f} points), without numbers.'}
  423|     w = np.array([r[2] for r in rows])
  424|     ev_pp = float(np.average([r[0] for r in rows], weights=w))
  425|     spread = float(np.sqrt(np.average([(r[0] - ev_pp) ** 2 for r in rows], weights=w)))
  426|     ev_pm = float(np.hypot(np.average([max(r[1], 2.0) for r in rows], weights=w), spread))  # the analogues disagree too
  427|     overlap = not (hi < ev_pp - ev_pm or lo > ev_pp + ev_pm)
  428|     same_sign = np.sign(ev_pp) == np.sign(agent_pp) or abs(ev_pp) < 1 or abs(agent_pp) < 0.5
  429|     verdict = 'corroborated' if overlap and same_sign else 'consistent' if same_sign else 'contradicted'
  430|     return {'verdict': verdict, 'measure': measure, 'agents_pp': round(agent_pp, 1), 'agents_range_pp': [round(lo, 1), round(hi, 1)],
  431|             'evidence_pp': round(ev_pp, 1), 'evidence_pm': round(ev_pm, 1),
  432|             'detail': f'Interviews move {what} {agent_pp:+.1f} points ({lo:+.1f} to {hi:+.1f}); the closest historical '
  433|                       f'cases moved it {ev_pp:+.1f} ± {ev_pm:.1f}.'}
  434| 
  435| 
  436| def agreement(ev: dict | None, national: dict, base: dict, kind: str) -> dict:
  437|     """Does the record agree with the interviews? Checked on the vote measure
  438|     (the third candidate's share for a candidate, else the two-party share)
  439|     and on turnout. Any contradiction wins; then corroboration; then consistency."""
  440|     if not ev or not ev.get('findings') or not national:
  441|         return {'verdict': 'untested', 'detail': 'No historical evidence to compare with.', 'measures': []}
  442|     vote = ('other', 'do', base['o']) if kind == 'candidate' else ('r2', 'dr', base['r2'])
  443|     got = [x for x in (_agree_one(ev, national, m, k, b) for m, k, b in (vote, ('turnout', 'dt', base['turnout']))) if x]
  444|     if not got:
  445|         return {'verdict': 'untested', 'measures': [],
  446|                 'detail': 'The sources describe the situation but give no number or direction to compare with.'}
  447|     for v in ('contradicted', 'corroborated', 'consistent'):
  448|         if any(x['verdict'] == v for x in got):
  449|             return {'verdict': v, 'measures': got, 'detail': ' '.join(x['detail'] for x in got)}
  450| 
  451| 
  452| TIERS = ['very-low', 'low', 'medium', 'high']
  453| TIER_LABEL = {'high': 'High confidence', 'medium': 'Medium confidence', 'low': 'Low confidence',
  454|               'very-low': 'Extremely low confidence'}
  455| BASE_TIER = {'franchise': 3, 'population': 2, 'issue': 1, 'event': 1, 'candidate': 1}
  456| 
  457| 
  458| def confidence(spec: dict, ev: dict | None, agree: dict | None, agent: dict | None, generated: bool) -> dict:
  459|     """A tier and the reasons for it. Agent-driven changes start at low; the
  460|     record can lift one to medium only when strong evidence corroborates it.
  461|     Fantasy, anachronism, contradiction or unstable interviews push it down."""
  462|     kind = spec['kind']
  463|     t = BASE_TIER.get(kind, 1)
  464|     if generated and kind == 'franchise':
  465|         t = 2  # borrowed behaviour chosen by the compiler, not written by hand
  466|     flags, reasons = [], []
  467|     st = strength(ev) if ev is not None else {'level': 'not-researched'}
  468|     plaus = spec.get('plausibility', 'documented')
  469|     if plaus == 'fantastical' or spec.get('anachronism'):
  470|         t = 0
  471|         flags.append('fantastical' if plaus == 'fantastical' else 'anachronism')
  472|         reasons.append(spec.get('anachronism_note') or f'Nothing like this was possible in {spec.get("year", 1920)}, so no one\'s behaviour on record speaks to it.')
  473|     elif plaus == 'a-stretch':
  474|         t -= 1
  475|         flags.append('far-from-record')
  476|         reasons.append('The change is far from anything that happened, so behaviour on record only loosely applies.')
  477|     if ev is None:
  478|         flags.append('not-researched')
  479|     elif st['level'] == 'none':
  480|         if kind in ('issue', 'event', 'candidate'):
  481|             t -= 1
  482|         flags.append('no-evidence')
  483|         reasons.append('I found no reliable historical work on how people behaved in this or a similar situation.')
  484|     elif st['level'] == 'weak':
  485|         flags.append('weak-evidence')
  486|         reasons.append('Historical evidence is thin: loose analogies or weak sources only.')
  487|     verdict = (agree or {}).get('verdict')
  488|     if verdict == 'contradicted':
  489|         t -= 1
  490|         flags.append('contradicts-record')
  491|         reasons.append('The interviews point the other way from the historical record.')
  492|     elif verdict == 'corroborated' and st['level'] == 'strong' and kind in ('issue', 'event', 'candidate'):
  493|         t += 1
  494|         reasons.append('Strong historical evidence agrees with the interviews.')
  495|     if agent and spec.get('mode') == 'agents':  # backbone-mode interviews are a cross-check; they move no numbers
  496|         unstable = agent.get('spans_zero') and agent.get('paraphrase_flip')
  497|         backed = verdict == 'corroborated' or (verdict == 'consistent' and st['level'] == 'strong')
  498|         if unstable and not backed:
  499|             t -= 1
  500|             flags.append('unstable-interviews')
  501|             reasons.append('The interviews\' answer changes sign with the question\'s wording.')
  502|         elif unstable:
  503|             flags.append('unstable-interviews')
  504|             reasons.append('The interviews\' answer changes sign with the question\'s wording, though the record points the same way.')
  505|         checked, wrong = agent.get('checked') or 0, agent.get('misread') or 0
  506|         if checked and wrong:
  507|             flags.append('misread-change')
  508|             reasons.append(f'{wrong} of {checked} people interviewed took the news to be about the other candidate; '
  509|                            'their answers were left out.')
  510|             if wrong / checked >= 0.5:
  511|                 t = 0
  512|             elif wrong / checked > 0.25:
  513|                 t -= 1
  514|         # D33: the belief check and the reasoning audit. Every failure counts here, including bulk-model
  515|         # answers later re-asked on a stronger model; only answers that failed on every model are dropped.
  516|         bc, bf = agent.get('belief_checked') or 0, agent.get('belief_failed') or 0
  517|         if bc and bf:
  518|             flags.append('disbelieved-change')
  519|             q = agent.get('question')
  520|             reasons.append(f'{bf} of {bc} interviews didn\'t take the change as true'
  521|                            + (f' (asked first: "{q}")' if q else '') + '; their answers were left out'
  522|                            + (f', and {agent.get("escalated")} re-asked on a stronger model were kept instead.' if agent.get('escalated') else '.'))
  523|             if bf / bc >= 0.5:
  524|                 t -= 1
  525|         ac, af = agent.get('audit_checked') or 0, agent.get('audit_failed') or 0
  526|         if ac and af:
  527|             flags.append('reasoned-off-premise')
  528|             reasons.append(f'{af} of {ac} answers reasoned from the world as it really was; they were left out.')
  529|             if af / ac >= 0.5:
  530|                 t -= 1
  531|         if agent.get('borrowed'):
  532|             flags.append('borrowed-groups')
  533|             reasons.append(f'{agent["borrowed"]} group{"s" if agent["borrowed"] != 1 else ""} the change reaches weren\'t interviewed; '
  534|                            'they borrow the interviewed groups\' effect, with extra uncertainty.')
  535|         if agent.get('n', 99) < 6:
  536|             t -= 1
  537|             flags.append('few-interviews')
  538|             reasons.append(f'Only {agent.get("n")} people were interviewed on it.')
  539|         if agent.get('exposed'):
  540|             flags.append('model-knows-outcome')
  541|     cand = spec.get('candidate') or {}
  542|     if cand.get('name') and cand.get('positions_source') == 'inferred':
  543|         flags.append('positions-inferred')
  544|         reasons.append(f'{cand["name"]}\'s positions are inferred, not documented.')
  545|     if cand.get('name') and cand.get('eligibility_note'):
  546|         flags.append('ineligible-candidate')
  547|         reasons.append(cand['eligibility_note'])
  548|     if generated:
  549|         flags.append('exploratory')
  550|     cap = 2 if kind in ('issue', 'event', 'candidate') else 3
  551|     t = int(max(0, min(cap, t)))
  552|     return {'tier': TIERS[t], 'label': TIER_LABEL[TIERS[t]], 'flags': flags, 'reasons': reasons,
  553|             'evidence': st['level']}
  554| 
  555| 
  556| def combine_tiers(tiers: list[dict]) -> dict:
  557|     if not tiers:
  558|         return {'tier': 'high', 'label': TIER_LABEL['high'], 'flags': [], 'reasons': [], 'evidence': None}
  559|     worst = min(tiers, key=lambda c: TIERS.index(c['tier']))
  560|     flags = list(dict.fromkeys(f for c in tiers for f in c['flags']))
  561|     reasons = list(dict.fromkeys(r for c in tiers for r in c['reasons']))
  562|     return {**worst, 'flags': flags, 'reasons': reasons}
  563| 
  564| 
  565| def page_evidence(key: str, ev: dict | None, agree: dict | None, sources_limit: int = 4) -> dict | None:
  566|     """What the page shows: the summary, the agreement, and the best findings with their sources."""
  567|     if not ev:
  568|         return None
  569|     by_id = {s['id']: s for s in ev.get('sources', [])}
  570|     fs = sorted(ev.get('findings', []), key=lambda f: -f['grade'])[:sources_limit]
  571|     return {
  572|         'whatIf': key, 'strength': strength(ev)['level'], 'summary': ev.get('summary', ''),
  573|         'agreement': (agree or {}).get('verdict', 'untested'), 'agreementDetail': (agree or {}).get('detail'),
  574|         'findings': [{'claim': f['claim'], 'when': f['when'], 'match': f['match'], 'tier': f['tier'],
  575|                       'sources': [{'title': by_id[i]['title'], 'url': by_id[i]['url'], 'tier': by_id[i]['tier']}
  576|                                   for i in f['source_ids'] if i in by_id]} for f in fs],
  577|         'caveats': ev.get('caveats', [])[:3],
  578|         **({'researchedAt': ev['researched_at']} if ev.get('researched_at') else {}),
  579|     }
  580| 
  581| 
  582| def _create(client, **params):
  583|     """messages.create with the harness's retry rules (rate limits, 5xx)."""
  584|     import anthropic
  585|     for attempt in range(5):
  586|         try:
  587|             return client.messages.create(**params)
  588|         except anthropic.RateLimitError:
  589|             time.sleep(2 ** attempt + 1)
  590|         except anthropic.APIStatusError as e:
  591|             if e.status_code < 500:
  592|                 raise
  593|             time.sleep(2 ** attempt)
  594|         except anthropic.APIConnectionError:
  595|             time.sleep(2 ** attempt)
  596|     raise RuntimeError('retries exhausted')
  597| 
  598| 
  599| def slug(text: str, n: int = 40) -> str:
  600|     s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
  601|     return s[:n].rstrip('-') or 'what-if'
  602| 
  603| 
  604| def dumps(x) -> str:
  605|     return json.dumps(x, indent=1, default=float)
```

## `simharness/geo.py`

```python
    1| """States, regions and 1920 electoral votes (and AK, HI, DC for 1960 on).
    2| 
    3| The electoral votes are checked at load time against the certified count in
    4| the labels (NARA); see data.load_labels.
    5| """
    6| 
    7| STATE_NAME = {
    8|     'AL': 'Alabama', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado',
    9|     'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'ID': 'Idaho',
   10|     'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky',
   11|     'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan',
   12|     'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska',
   13|     'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
   14|     'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon',
   15|     'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
   16|     'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia',
   17|     'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
   18|     'AK': 'Alaska', 'HI': 'Hawaii',
   19| }
   20| CODE_OF = {v: k for k, v in STATE_NAME.items()}
   21| 
   22| # The eleven former Confederate states: where the 1890–1908 constitutions and
   23| # laws (poll taxes, literacy and "understanding" tests, white primaries) kept
   24| # most Black citizens from voting. Border states are separate.
   25| SOUTH = ['VA', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'LA', 'TX', 'AR', 'TN']
   26| BORDER = ['KY', 'MD', 'DE', 'MO', 'WV', 'OK', 'DC']
   27| NORTHEAST = ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA']
   28| MIDWEST = ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'ND', 'SD', 'NE', 'KS']
   29| WEST = ['MT', 'ID', 'WY', 'CO', 'NM', 'AZ', 'UT', 'NV', 'WA', 'OR', 'CA', 'AK', 'HI']
   30| 
   31| REGIONS = {'northeast': NORTHEAST, 'midwest': MIDWEST, 'south': SOUTH, 'border': BORDER, 'west': WEST}
   32| REGION_OF = {s: r for r, ss in REGIONS.items() for s in ss}
   33| # The 48 states of 1920, listed explicitly so adding AK, HI and DC to REGIONS
   34| # (for 1960 on) can't change it. DC had no electors until 1964.
   35| STATES_1920 = ['AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA',
   36|                'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY',
   37|                'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']
   38| ALL_STATES = sorted(STATE_NAME)  # 50 states + DC
   39| # Every state and DC; which ones vote in a given year comes from the returns
   40| # (data.states). 1789–1868 needs no extra codes: only states choose electors,
   41| # and every state that ever did is one of today's 50 (VA before WV's 1863 split
   42| # is VA; MA before ME's 1820 split is MA).
   43| 
   44| # Merge order for agent cohorts: a too-small cohort folds into the same sex
   45| # and group in the nearest region.
   46| NEAREST_REGION = {
   47|     'northeast': ['midwest', 'border', 'west', 'south'],
   48|     'midwest': ['northeast', 'west', 'border', 'south'],
   49|     'west': ['midwest', 'northeast', 'border', 'south'],
   50|     'border': ['south', 'midwest', 'northeast', 'west'],
   51|     'south': ['border', 'midwest', 'northeast', 'west'],
   52| }
```

## `simharness/intake.py`

```python
    1| """Typed what-if intake: a reader's words → a what-if the page can serve.
    2| 
    3|     python -m simharness.run whatif --text "charlie chaplin ran as an independent" --config configs/live-1920.json
    4|     python -m simharness.run whatif --queue --config configs/live-1920.json    # what the router queued as unknown
    5|     python -m simharness.run research --config configs/live-1920.json          # evidence for the config's what-ifs
    6| 
    7| Stages, each priced before it is sent and recorded in sessions/spend.jsonl:
    8| 
    9| 1. compile   (research.compile_model, structured): the words become a spec;
   10|              or `same_as` an existing what-if, in which case only its keywords
   11|              grow and the bundle is republished; or not modelable.
   12| 2. research  (research.research_model + web search): notes with citations.
   13| 3. extract   (research.extract_model, structured): graded findings, each
   14|              grounded in a source the search returned.
   15| 4. stage     (research.world_model, structured; D33, world.py): the year's
   16|              newspaper items the change makes false, in-world news, downstream
   17|              facts, a belief check, and the groups to interview.
   18| 5. register  whatifs/<key>.json and whatifs/evidence/<key>.json; the key
   19|              joins the config's what_ifs.
   20| 6. run       backbone → plan → ask (identical earlier requests reused) →
   21|              refine (audit, escalate) → analyze → publish → serve/bundles/<year>.json.
   22| 
   23| Model and effort (D33): the once-per-what-if calls (compile, extract, stage,
   24| audit) are where a stronger model buys the most per dollar: each runs once,
   25| and each decides whether the interviews measure the change at all. The live
   26| configs run them on Opus at high effort; the per-voter interviews stay on the
   27| bulk model, with only the answers that fail a check re-asked on a stronger one.
   28| 
   29| Money: every stage is priced before it is sent and recorded after, with the
   30| name of the access key that queued the text, if any (llm.SPEND_WHO). Queued
   31| text is modelled only while the spend ledger is under both caps, counted across
   32| every visitor together: DAILY_USD per UTC day (SIMULACRA_DAILY_USD, default 20)
   33| and MONTHLY_USD per UTC month (SIMULACRA_MONTHLY_USD, default 200). The router
   34| (serve/guard.ts) checks the same caps before it queues; the worker checks again
   35| before each text, and a text's Budget stops at the first stage that crosses
   36| what is left. A stage is priced when it finishes, so a cap can be passed by at
   37| most the one stage that crosses it.
   38| 
   39| Failures: a text that fails is retried once. After MAX_ATTEMPTS failures it is
   40| settled as given up (queue-done.jsonl, status `gave-up`) and copied to
   41| queue-dead.jsonl, so one bad text can't be re-billed forever or hold up the
   42| texts queued behind it.
   43| """
   44| from __future__ import annotations
   45| 
   46| import datetime as dt
   47| import json
   48| import os
   49| import re
   50| import shutil
   51| import time
   52| from pathlib import Path
   53| 
   54| from . import evidence, llm, scenario
   55| from .config import ROOT, RunConfig
   56| from .whatifs import REGISTRY
   57| 
   58| SESSIONS = ROOT / 'sessions'
   59| QUEUE = SESSIONS / 'queue.jsonl'
   60| DONE = SESSIONS / 'queue-done.jsonl'
   61| FAILED = SESSIONS / 'queue-failed.jsonl'
   62| DEAD = SESSIONS / 'queue-dead.jsonl'
   63| LOCK = SESSIONS / 'intake.lock'
   64| SERVE_BUNDLES = ROOT / 'serve/bundles'
   65| STATUS = SESSIONS / 'intake-status.json'
   66| DAILY_USD = float(os.environ.get('SIMULACRA_DAILY_USD') or 20)
   67| MONTHLY_USD = float(os.environ.get('SIMULACRA_MONTHLY_USD') or 200)
   68| OVER_CAP = 'The budget for new what-ifs is spent for now. Try again tomorrow.'
   69| MAX_ATTEMPTS = 2
   70| GAVE_UP = 'I couldn’t model that, after two tries.'
   71| 
   72| 
   73| class Progress:
   74|     """What the worker is doing, for the router to show while the page waits
   75|     (sessions/intake-status.json: {text, steps: [{text, state}], ts})."""
   76| 
   77|     def __init__(self, text: str | None):
   78|         self.text, self.steps = (_norm(text) if text else None), []
   79| 
   80|     def step(self, label: str):
   81|         if not self.text:
   82|             return
   83|         for s in self.steps:
   84|             s['state'] = 'done'
   85|         self.steps.append({'text': label, 'state': 'doing'})
   86|         self._write()
   87| 
   88|     def finish(self):
   89|         for s in self.steps:
   90|             s['state'] = 'done'
   91|         self._write()
   92| 
   93|     def _write(self):
   94|         if not self.text:
   95|             return
   96|         SESSIONS.mkdir(exist_ok=True)
   97|         tmp = STATUS.with_suffix(f'.{os.getpid()}.tmp')
   98|         tmp.write_text(json.dumps({'text': self.text, 'steps': self.steps, 'ts': dt.datetime.now().isoformat(timespec='seconds')}))
   99|         tmp.replace(STATUS)
  100| 
  101| 
  102| class Budget:
  103|     """What a typed what-if has spent, stage by stage, and the most it may (None: no ceiling)."""
  104| 
  105|     def __init__(self, ceiling: float | None = None):
  106|         self.spent, self.lines, self.ceiling = 0.0, [], ceiling
  107| 
  108|     def add(self, dollars: float, stage: str, typical: float | None = None, note: str = '', record: bool = True):
  109|         self.spent += dollars
  110|         self.lines.append({'stage': stage, 'dollars': round(dollars, 4), 'typical': typical})
  111|         if record:
  112|             llm.record_spend(stage, dollars, note=note)
  113|         if self.ceiling is not None and self.spent >= self.ceiling:
  114|             raise SystemExit(OVER_CAP)
  115| 
  116| 
  117| # Typical output tokens by call (measured: a compile answer ran ~1,300 tokens on Sonnet 5.5).
  118| TYPICAL_OUT = {'compile': 1600, 'compile-retry': 1600, 'extract': 3000, 'stage': 2500}
  119| # Thinking at higher effort multiplies output [I].
  120| EFFORT_OUT = {'low': 1.0, 'medium': 3.0, 'high': 6.0, 'xhigh': 7.0, 'max': 8.0}
  121| 
  122| 
  123| def typical_out(stage: str, effort: str, max_tokens: int) -> int:
  124|     return int(min(TYPICAL_OUT.get(stage, 600) * EFFORT_OUT.get(effort, 1.0), 0.75 * max_tokens))
  125| 
  126| 
  127| def _structured(req: dict, max_tokens: int, budget: Budget, stage: str, note: str = '') -> dict:
  128|     from .config import RUNS
  129|     cache = llm.AnswerCache(RUNS)
  130|     hit = cache.get(req)
  131|     if hit:
  132|         print(f'{stage}: reused an identical earlier answer', flush=True)
  133|         return hit['data']
  134|     effort = req.get('effort') or 'low'
  135|     est = llm.estimate([req], max_tokens, typical_out=typical_out(stage, effort, max_tokens))
  136|     print(f'{stage}: ~${est["typical"]} typical, ${est["worst"]} worst ({req["model"]}, {effort} effort)', flush=True)
  137|     ans = llm.AnthropicBackend(effort=effort, max_tokens=max_tokens)._one(req)
  138|     cache.put(req, ans | {'backend': 'anthropic'})
  139|     budget.add(llm.cost(req['model'], ans.get('usage') or {}), stage, est['typical'], note)
  140|     if not ans.get('ok'):
  141|         raise SystemExit(f'{stage} failed: {ans.get("error")}')
  142|     return ans['data']
  143| 
  144| 
  145| def _with_effort(req: dict, effort: str, fast: bool = False) -> dict:
  146|     # 'low' keeps the request byte-identical to before D33, so its cached answers still match.
  147|     # Fast mode changes only how quickly the answer comes (and its price), so it isn't part of the cache key.
  148|     out = req | {'effort': effort} if effort and effort != 'low' else dict(req)
  149|     return out | {'speed': 'fast'} if fast and llm.fast_ok(req['model']) else out
  150| 
  151| 
  152| def compile_text(text: str, cfg: RunConfig, budget: Budget) -> dict:
  153|     from . import profiles
  154|     rc, prof = cfg.research, profiles.get(cfg.election)
  155|     mt = max(3000, rc.pass_max_tokens)
  156|     raw = _structured(_with_effort(scenario.compile_request(text, REGISTRY, cfg.context_cutoff, rc.compile_model, prof=prof),
  157|                                    rc.compile_effort, rc.fast), mt, budget, 'compile', text)
  158|     bad = scenario.naming_violations(raw, cfg.election) if raw.get('modelable') else []
  159|     if bad:
  160|         note = ('These sentences name a nominee, a party or the President, which the blinded briefs cannot show. '
  161|                 'Rewrite them with the descriptions given: ' + json.dumps(bad))
  162|         raw = _structured(_with_effort(scenario.compile_request(text, REGISTRY, cfg.context_cutoff, rc.compile_model, note, prof),
  163|                                        rc.compile_effort, rc.fast), mt, budget, 'compile-retry', text)
  164|     return raw
  165| 
  166| 
  167| def stage(spec: dict, cfg: RunConfig, budget: Budget, ev: dict | None = None) -> dict | None:
  168|     """D33: stage the what-if's world (world.py) and keep it on the spec. Agent-mode what-ifs only:
  169|     a backbone-mode change's interviews are a cross-check and move no numbers."""
  170|     from . import data, profiles, world
  171|     rc = cfg.research
  172|     if not rc.world_model or spec.get('mode') != 'agents':
  173|         return None
  174|     prof = profiles.get(cfg.election)
  175|     rel = prof.get('corpus') or ('sources/corpus_1920.jsonl' if cfg.election == 1920 else None)
  176|     corpus = data.corpus(cfg.context_cutoff, rel, profiles.names_re(cfg.election)) if rel else []
  177|     req = _with_effort(world.stage_request(spec, prof, cfg.context_cutoff, corpus, rc.world_model, rc.world_effort, ev),
  178|                        rc.world_effort, rc.fast)
  179|     raw = _structured(req, max(4000, rc.pass_max_tokens), budget, 'stage', spec['key'])
  180|     spec['world'] = world.finalize(raw, spec, prof, cfg.context_cutoff, corpus, rc.world_model, rc.world_effort)
  181|     return spec['world']
  182| 
  183| 
  184| def stage_config(config_path: str | Path, only: str | None = None, refresh: bool = False) -> dict:
  185|     """Stage every compiled agent-mode what-if in a config that hasn't been (D33), and save its spec."""
  186|     cfg = RunConfig.load(config_path)
  187|     keys = [k for k in cfg.what_ifs if (not only or k == only) and REGISTRY.get(k, {}).get('generated')
  188|             and REGISTRY[k].get('mode') == 'agents' and (refresh or not REGISTRY[k].get('world'))]
  189|     budget = Budget()
  190|     out = {}
  191|     for k in keys:
  192|         spec = {kk: v for kk, v in REGISTRY[k].items() if kk not in ('apply', 'facts')}
  193|         w = stage(spec, cfg, budget, scenario.load_evidence(k))
  194|         if w is None:
  195|             continue
  196|         scenario.save_spec(spec)
  197|         REGISTRY[k] = scenario.bind(spec)
  198|         out[k] = {'contradicted': len(w['contradicted']), 'items': len(w['items']), 'check': (w['check'] or {}).get('question'),
  199|                   'focus': [f['why'] for f in w['focus']]}
  200|     return {'staged': out, 'dollars': round(budget.spent, 4)}
  201| 
  202| 
  203| def reextract(spec: dict, cfg: RunConfig, budget: Budget, have: dict) -> dict:
  204|     """Extraction again from the saved notes (no new search)."""
  205|     notes = {'text': have['notes'], 'sources': have['sources']}
  206|     rc = cfg.research
  207|     extracted = _structured(_with_effort(evidence.extract_request(spec, notes, rc.extract_model), rc.extract_effort, rc.fast),
  208|                             max(8000, rc.pass_max_tokens), budget, 'extract', spec['key'])
  209|     ev = {**have, **evidence.ground(extracted, notes, spec.get('about')), 'models': {**have.get('models', {}), 'extract': rc.extract_model},
  210|           'reextracted_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
  211|     scenario.save_evidence(spec['key'], ev)
  212|     return ev
  213| 
  214| 
  215| def research(spec: dict, cfg: RunConfig, budget: Budget, refresh: bool = False, again: bool = False) -> dict:
  216|     """Evidence for one what-if (cached in whatifs/evidence/<key>.json). again: re-extract the saved notes."""
  217|     import anthropic
  218|     key = spec['key']
  219|     have = scenario.load_evidence(key)
  220|     if have and again and have.get('notes'):
  221|         return reextract(spec, cfg, budget, have)
  222|     if have and not refresh:
  223|         return have
  224|     rc = cfg.research
  225|     est = evidence.research_estimate(rc.research_model, rc.max_searches, rc.research_max_tokens)
  226|     print(f'research {key}: ~${est["typical"]} typical, ${est["worst"]} worst ({rc.research_model}, '
  227|           f'≤{rc.max_searches} searches)', flush=True)
  228|     client = anthropic.Anthropic(api_key=llm.api_key())
  229|     notes = evidence.research(client, spec, {'year': cfg.election, 'day': cfg.election_day}, rc.research_model,
  230|                               rc.max_searches, rc.research_effort, rc.research_max_tokens)
  231|     budget.add(notes['dollars'], 'research', None, key)
  232|     print(f'  {len(notes["queries"])} searches, {len(notes["sources"])} sources '
  233|           f'({sum(s["tier"] == "A" for s in notes["sources"])} scholarly or official), ${notes["dollars"]}', flush=True)
  234|     extracted = _structured(_with_effort(evidence.extract_request(spec, notes, rc.extract_model), rc.extract_effort, rc.fast),
  235|                             max(8000, rc.pass_max_tokens), budget, 'extract', key)
  236|     ev = evidence.ground(extracted, notes, spec.get('about'))
  237|     ev.update({'key': key, 'version': evidence.EVIDENCE_VERSION,
  238|                'researched_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
  239|                'models': {'research': rc.research_model, 'extract': rc.extract_model}, 'queries': notes['queries'],
  240|                'sources': notes['sources'], 'notes': notes['text'], 'prompt': notes['prompt'], 'usage': notes['usage'],
  241|                'dollars': round(sum(x['dollars'] for x in budget.lines if x['stage'] in ('research', 'extract')), 4)})
  242|     scenario.save_evidence(key, ev)
  243|     return ev
  244| 
  245| 
  246| def documented_positions(spec: dict, ev: dict, cutoff: str):
  247|     """A candidate's positions from the record, when the research found any on
  248|     or before the cutoff (masked like any brief text); else they stay inferred."""
  249|     keep = []
  250|     for p in ev.get('actor_positions', []):
  251|         d = p.get('date', '')
  252|         try:
  253|             ok = dt.date.fromisoformat(d[:10]).isoformat() <= cutoff
  254|         except ValueError:
  255|             m = re.search(r'\b(1[6-9]\d\d)\b', d)
  256|             ok = bool(m) and int(m.group(1)) < int(cutoff[:4])
  257|         if ok:
  258|             keep.append(scenario.clean_position(p['text'], int(cutoff[:4])))
  259|     if keep:
  260|         spec['candidate']['positions'] = keep[:3]
  261|         spec['candidate']['positions_source'] = 'documented'
  262| 
  263| 
  264| def _add_to_config(config_path: Path, key: str):
  265|     raw = json.loads(config_path.read_text())
  266|     if key not in raw['what_ifs']:
  267|         raw['what_ifs'].append(key)
  268|         config_path.write_text(json.dumps(raw, indent=2) + '\n')
  269| 
  270| 
  271| def run_pipeline(config_path: Path, budget: Budget, publish_only: bool = False, progress: Progress | None = None) -> dict:
  272|     from .run import Run
  273|     progress = progress or Progress(None)
  274|     run = Run(RunConfig.load(config_path))
  275|     if not publish_only:
  276|         if not (run.dir / 'fit.pkl').exists():
  277|             run.backbone()
  278|         run.plan()
  279|         progress.step(f'Interviewing voters in your {run.cfg.election}, with the real one as a control.')
  280|         asked = run.ask()
  281|         budget.add(asked['dollars'], 'ask', None, record=False)  # ask records its own spend
  282|         if run.cfg.research.audit_model or run.cfg.agents.escalate_model:
  283|             progress.step('Checking that each voter took the change as true.')
  284|             refined = run.refine()
  285|             budget.add(refined['dollars'], 'refine', None, record=False)  # audit and ask record their own spend
  286|         progress.step('Comparing the interviews with the historical record.')
  287|         run.analyze()
  288|     progress.step(f'Rerunning the {run.cfg.election} election 100 times.')
  289|     run.publish()
  290|     SERVE_BUNDLES.mkdir(parents=True, exist_ok=True)
  291|     src = run.dir / 'published' / f'{run.cfg.election}.json'
  292|     shutil.copyfile(src, SERVE_BUNDLES / f'{run.cfg.election}.json')
  293|     (SERVE_BUNDLES / 'RUN_ID').write_text(run.id + '\n')
  294|     return {'run': run.id, 'bundle': str(src)}
  295| 
  296| 
  297| def report(year: int, key: str) -> dict:
  298|     b = json.loads((SERVE_BUNDLES / f'{year}.json').read_text())
  299|     r = b['runs'].get(key) or {}
  300|     return {'key': key, 'label': REGISTRY[key]['label'], 'summary': r.get('summary'), 'ev': r.get('ev'),
  301|             'confidence': r.get('confidenceTier'), 'flags': r.get('confidenceFlags'),
  302|             'evidence': [{'strength': e['strength'], 'agreement': e['agreement'], 'detail': e.get('agreementDetail')}
  303|                          for e in r.get('evidence', [])]}
  304| 
  305| 
  306| def left(ledger: Path | None = None, daily: float | None = None, monthly: float | None = None) -> float:
  307|     """Dollars the intake may still spend: the smaller of what's left of today's
  308|     cap and this month's, every visitor together (llm.spent)."""
  309|     today, month = llm.spent(ledger=ledger or llm.LEDGER)
  310|     rest = min((DAILY_USD if daily is None else daily) - today, (MONTHLY_USD if monthly is None else monthly) - month)
  311|     return max(rest, 0.0)
  312| 
  313| 
  314| def whatif(text: str, config_path: str | Path, refresh: bool = False, ceiling: float | None = None) -> dict:
  315|     config_path = Path(config_path)
  316|     cfg = RunConfig.load(config_path)
  317|     budget = Budget(ceiling)
  318|     progress = Progress(text)
  319|     progress.step('Turning your words into a change I can model.')
  320|     raw = compile_text(text, cfg, budget)
  321|     if not raw['modelable']:
  322|         progress.finish()
  323|         return {'status': 'not-modelable', 'why': raw['why_not'], 'dollars': round(budget.spent, 4)}
  324|     if raw['same_as'] in REGISTRY and cfg.election in (REGISTRY[raw['same_as']].get('years') or [REGISTRY[raw['same_as']].get('year', 1920)]):
  325|         key = raw['same_as']
  326|         scenario.add_words(key, raw['words'] + [text.lower().strip()[:80]])
  327|         in_config = key in cfg.what_ifs
  328|         _add_to_config(config_path, key)
  329|         progress.step(f'That’s {REGISTRY[key]["label"]}, which I’ve modelled already.')
  330|         out = run_pipeline(config_path, budget, publish_only=in_config, progress=progress)
  331|         progress.finish()
  332|         return {'status': 'keyword', 'key': key, **out, 'dollars': round(budget.spent, 4), 'costs': budget.lines,
  333|                 'report': report(cfg.election, key)}
  334|     spec = scenario.finalize(raw, text, REGISTRY, cfg.research.compile_model, cfg.election)
  335|     if spec.get('reinterpretation'):
  336|         progress.step(spec['reinterpretation'])
  337|     progress.step(f'Setting the scene: autumn {cfg.election}…')
  338|     ev = research(spec, cfg, budget, refresh)
  339|     n = len(ev.get('findings', []))
  340|     progress.step(f'Clarifying historical context: {n or "no"} finding{"" if n == 1 else "s"}.')
  341|     if spec['kind'] == 'candidate' and spec['candidate']['positions_source'] != 'documented':
  342|         documented_positions(spec, ev, cfg.context_cutoff)
  343|     if cfg.research.world_model and spec['mode'] == 'agents':
  344|         progress.step(f'Staging the autumn of {cfg.election} so nothing in it contradicts the change.')
  345|         w = stage(spec, cfg, budget, ev)
  346|         if w:
  347|             gone, new = len(w['contradicted']), len(w['items'])
  348|             progress.step(f'Took out {gone or "no"} newspaper item{"" if gone == 1 else "s"} the change makes false; '
  349|                           f'wrote {new} from the changed world{" and a question to check each voter believes it" if w["check"] else ""}.')
  350|     scenario.save_spec(spec)
  351|     REGISTRY[spec['key']] = scenario.bind(spec)
  352|     _add_to_config(config_path, spec['key'])
  353|     out = run_pipeline(config_path, budget, progress=progress)
  354|     progress.finish()
  355|     return {'status': 'modelled', 'key': spec['key'], **out, 'dollars': round(budget.spent, 4), 'costs': budget.lines,
  356|             'report': report(cfg.election, spec['key'])}
  357| 
  358| 
  359| def research_config(config_path: str | Path, refresh: bool = False, only: str | None = None, again: bool = False) -> dict:
  360|     """Evidence for every what-if in a config that lacks it (hand-written ones included: there it grades confidence only)."""
  361|     cfg = RunConfig.load(config_path)
  362|     keys = [k for k in cfg.what_ifs if not only or k == only]
  363|     budget = Budget()
  364|     out = {}
  365|     for k in keys:
  366|         ev = research({**REGISTRY[k], 'key': k}, cfg, budget, refresh, again)
  367|         out[k] = {'strength': evidence.strength(ev)['level'], 'findings': len(ev['findings']), 'summary': ev['summary'][:200]}
  368|     return {'what_ifs': out, 'dollars': round(budget.spent, 4)}
  369| 
  370| 
  371| # ── The router's queue ──
  372| 
  373| def _norm(text: str) -> str:
  374|     return ' '.join(text.lower().split())
  375| 
  376| 
  377| def _pid_alive(pid: int) -> bool:
  378|     try:
  379|         os.kill(pid, 0)
  380|         return True
  381|     except OSError:
  382|         return False
  383| 
  384| 
  385| def _config_for(year: int, fallback: Path | None = None) -> Path | None:
  386|     """configs/live-<year>.json for any simulated year (one with a profile), or the
  387|     worker's own config when it is that year's; None when the year isn't simulated."""
  388|     from . import profiles
  389|     if year not in profiles.years():
  390|         return None
  391|     p = ROOT / f'configs/live-{year}.json'
  392|     if p.exists():
  393|         return p
  394|     return fallback if fallback and Path(fallback).exists() and RunConfig.load(fallback).election == year else None
  395| 
  396| 
  397| def _settle(year: int, text: str, status: str, why: str | None = None, key: str | None = None,
  398|             dollars: float | None = None):
  399|     with open(DONE, 'a') as f:
  400|         f.write(json.dumps({'text': text, 'year': year, 'ts': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
  401|                             'status': status, 'key': key, 'why': why, 'dollars': dollars}) + '\n')
  402| 
  403| 
  404| def process_queue(config_path: str | Path, limit: int = 3) -> list[dict]:
  405|     """Model up to `limit` distinct queued (year, text) pairs, oldest first, within the caps.
  406|     Each is modelled in its own year's live config, its spend recorded against the key that queued it, if any.
  407|     A text that has failed MAX_ATTEMPTS times is given up (queue-dead.jsonl) instead of retried."""
  408|     SESSIONS.mkdir(exist_ok=True)
  409|     if LOCK.exists() and _pid_alive(int(LOCK.read_text().strip() or 0)):
  410|         return [{'status': 'busy', 'pid': LOCK.read_text().strip()}]
  411|     LOCK.write_text(str(os.getpid()))
  412|     try:
  413|         done = set()
  414|         for l in DONE.read_text().splitlines() if DONE.exists() else []:
  415|             if l.strip():
  416|                 x = json.loads(l)
  417|                 done.add((x.get('year', 1920), x['text']))
  418|         attempts: dict[tuple[int, str], int] = {}
  419|         for l in FAILED.read_text().splitlines() if FAILED.exists() else []:
  420|             if l.strip():
  421|                 x = json.loads(l)
  422|                 k = (int(x.get('year') or 1920), x['text'])
  423|                 attempts[k] = attempts.get(k, 0) + 1
  424|         pending, who = [], {}
  425|         for l in QUEUE.read_text().splitlines() if QUEUE.exists() else []:
  426|             if l.strip():
  427|                 q = json.loads(l)
  428|                 key = (int(q.get('year') or 1920), _norm(q['text']))
  429|                 if key not in done and key not in pending:
  430|                     pending.append(key)
  431|                     who[key] = q.get('who')
  432|         results = []
  433|         for year, t in pending[:limit]:
  434|             if attempts.get((year, t), 0) >= MAX_ATTEMPTS:
  435|                 # Failed before, every time: settled, not retried again.
  436|                 with open(DEAD, 'a') as f:
  437|                     f.write(json.dumps({'text': t, 'year': year, 'attempts': attempts[(year, t)], 'at': time.time()}) + '\n')
  438|                 _settle(year, t, 'gave-up', GAVE_UP)
  439|                 results.append({'text': t, 'year': year, 'status': 'gave-up', 'why': GAVE_UP})
  440|                 continue
  441|             cfg_path = _config_for(year, Path(config_path))
  442|             llm.SPEND_WHO = who[(year, t)]
  443|             budget_left = left()
  444|             if budget_left <= 0:
  445|                 # Settled, not retried: later budget isn't spent on text nobody is waiting for.
  446|                 _settle(year, t, 'over-cap', OVER_CAP)
  447|                 results.append({'text': t, 'year': year, 'status': 'over-cap', 'why': OVER_CAP})
  448|                 continue
  449|             try:
  450|                 if cfg_path is None:
  451|                     r = {'status': 'not-modelable', 'why': f'I haven’t simulated {year} yet.'}
  452|                 else:
  453|                     r = whatif(t, cfg_path, ceiling=budget_left)
  454|             except (SystemExit, Exception) as e:
  455|                 why = str(e) or repr(e)
  456|                 if isinstance(e, SystemExit) and why == OVER_CAP:
  457|                     # The cap was reached mid-text: settled. The texts after it find nothing left
  458|                     # and are settled the same way, so no waiting page times out.
  459|                     _settle(year, t, 'over-cap', OVER_CAP)
  460|                     results.append({'text': t, 'year': year, 'status': 'over-cap', 'why': OVER_CAP})
  461|                     continue
  462|                 # A stop or a bug: recorded (FAILED, read by the router, which tells the waiting
  463|                 # page why). The text stays queued for one more try, then is given up.
  464|                 r = {'text': t, 'year': year, 'status': 'stopped' if isinstance(e, SystemExit) else 'error', 'why': why}
  465|                 with open(FAILED, 'a') as f:
  466|                     f.write(json.dumps(r | {'at': time.time()}) + '\n')
  467|                 attempts[(year, t)] = attempts.get((year, t), 0) + 1
  468|                 if attempts[(year, t)] >= MAX_ATTEMPTS:
  469|                     with open(DEAD, 'a') as f:
  470|                         f.write(json.dumps({'text': t, 'year': year, 'attempts': attempts[(year, t)], 'why': why,
  471|                                             'at': time.time()}) + '\n')
  472|                     _settle(year, t, 'gave-up', GAVE_UP)
  473|                 results.append(r)
  474|                 continue
  475|             _settle(year, t, r['status'], r.get('why'), r.get('key'), r.get('dollars'))
  476|             results.append({'text': t, **r})
  477|         return results
  478|     finally:
  479|         llm.SPEND_WHO = None
  480|         LOCK.unlink(missing_ok=True)
```

## `simharness/llm.py`

```python
    1| """The voice layer's model calls, behind one interface with three backends.
    2| 
    3| - anthropic        one Messages API call per request (Anthropic Python SDK >= 1.0)
    4| - anthropic-batch  the Message Batches API: half price, asynchronous; the
    5|                    production path for precomputed runs
    6| - transcript       writes requests to a JSONL file and reads answers from
    7|                    another, so any external runner can answer them (the
    8|                    prototype used Claude Code subagents this way; see EVAL.md)
    9| 
   10| Every request is a dict: {id, model, system, user, schema, meta}. Every answer
   11| is {id, model, backend, ok, data, usage, raw, error}.
   12| 
   13| Model notes: Sonnet 5.5 rejects non-default
   14| sampling parameters, so variance is added by persona diversity, not
   15| temperature. Opus 5.5 can't disable thinking; both run at a low effort here.
   16| Structured outputs go through output_config.format (json_schema).
   17| """
   18| from __future__ import annotations
   19| 
   20| import hashlib
   21| import json
   22| import os
   23| import random
   24| import time
   25| from pathlib import Path
   26| 
   27| from .config import ROOT
   28| 
   29| # $ per million tokens: input, output, cache read. Batch is half of each; fast mode (Opus 5.5 only) twice.
   30| FAST_BETA = 'fast-mode-2026-02-01'
   31| PRICES = {
   32|     'claude-sonnet-5-5': (2.00, 10.00, 0.20),
   33|     'claude-opus-5-5': (4.00, 20.00, 0.20),
   34|     'claude-haiku-4-5': (1.00, 5.00, 0.10),
   35| }
   36| 
   37| 
   38| def cost(model: str, usage: dict, batch: bool = False) -> float:
   39|     p_in, p_out, p_cache = PRICES.get(model, PRICES['claude-sonnet-5-5'])
   40|     fresh = usage.get('input_tokens', 0)
   41|     cached = usage.get('cache_read_input_tokens', 0)
   42|     written = usage.get('cache_creation_input_tokens', 0)
   43|     out = usage.get('output_tokens', 0)
   44|     dollars = (fresh * p_in + written * p_in * 1.25 + cached * p_cache + out * p_out) / 1e6
   45|     return dollars * (0.5 if batch else 1.0) * (2.0 if usage.get('speed') == 'fast' else 1.0)
   46| 
   47| 
   48| def fast_ok(model: str) -> bool:
   49|     """Fast mode runs on Opus 5.5 only (Claude API, not batches)."""
   50|     return model == 'claude-opus-5-5'
   51| 
   52| 
   53| KEY_FILE = Path.home() / '.config/simulacra/anthropic.env'
   54| 
   55| 
   56| def api_key() -> str | None:
   57|     """ANTHROPIC_API_KEY if set, else ~/.config/simulacra/anthropic.env. Never printed or logged."""
   58|     if os.environ.get('ANTHROPIC_API_KEY'):
   59|         return os.environ['ANTHROPIC_API_KEY']
   60|     if KEY_FILE.exists():
   61|         for line in KEY_FILE.read_text().splitlines():
   62|             if line.startswith('ANTHROPIC_API_KEY='):
   63|                 return line.split('=', 1)[1].strip()
   64|     return None
   65| 
   66| 
   67| def estimate(requests: list[dict], max_tokens: int, batch: bool = False, typical_out: int = 600) -> dict:
   68|     """Dry-run dollars: input at ~4 chars/token (system uncached, to be safe),
   69|     output at a typical `typical_out` tokens (600 fits an interview answer) and
   70|     at the max_tokens worst case."""
   71|     typical = worst = 0.0
   72|     for r in requests:
   73|         tin = (len(r['system']) + len(r['user']) + len(json.dumps(r['schema']))) / 4
   74|         speed = {'speed': r.get('speed')} if r.get('speed') else {}
   75|         typical += cost(r['model'], {'input_tokens': tin, 'output_tokens': min(typical_out, max_tokens), **speed}, batch)
   76|         worst += cost(r['model'], {'input_tokens': tin, 'output_tokens': max_tokens, **speed}, batch)
   77|     return {'requests': len(requests), 'typical': round(typical, 4), 'worst': round(worst, 4)}
   78| 
   79| 
   80| def _parse(text: str):
   81|     text = text.strip()
   82|     if text.startswith('```'):
   83|         text = text.strip('`').split('\n', 1)[-1]
   84|     start, end = text.find('{'), text.rfind('}')
   85|     return json.loads(text[start:end + 1])
   86| 
   87| 
   88| class Backend:
   89|     name = 'base'
   90| 
   91|     def run(self, requests: list[dict]) -> list[dict]:
   92|         raise NotImplementedError
   93| 
   94| 
   95| class AnthropicBackend(Backend):
   96|     name = 'anthropic'
   97| 
   98|     def __init__(self, effort: str = 'low', max_tokens: int = 4000):
   99|         import anthropic  # imported lazily: the backbone needs no SDK
  100|         self.anthropic = anthropic
  101|         self.client = anthropic.Anthropic(api_key=api_key())
  102|         self.effort = effort
  103|         self.max_tokens = max_tokens
  104| 
  105|     def params(self, r: dict) -> dict:
  106|         out = {
  107|             'model': r['model'],
  108|             'max_tokens': self.max_tokens,
  109|             # The system prompt is identical across every agent in a run, so it
  110|             # is the cache prefix.
  111|             'system': [{'type': 'text', 'text': r['system'], 'cache_control': {'type': 'ephemeral'}}],
  112|             'messages': [{'role': 'user', 'content': r['user']}],
  113|             'output_config': {
  114|                 # A request may carry its own effort (the once-per-what-if passes run higher than the voices).
  115|                 'effort': r.get('effort') or self.effort,
  116|                 'format': {'type': 'json_schema', 'schema': r['schema']},
  117|             },
  118|         }
  119|         if 'haiku' in r['model']:
  120|             del out['output_config']['effort']  # Haiku 4.5 rejects effort
  121|         return out
  122| 
  123|     def _one(self, r: dict) -> dict:
  124|         a = self.anthropic
  125|         # Fast mode (a request's speed: "fast"): the beta endpoint, Opus 5.5 only. It has its own rate
  126|         # limit; a 429 there falls back to standard speed rather than waiting.
  127|         fast = r.get('speed') == 'fast' and fast_ok(r['model'])
  128|         for attempt in range(5):
  129|             try:
  130|                 if fast:
  131|                     msg = self.client.beta.messages.create(**self.params(r), speed='fast', betas=[FAST_BETA])
  132|                 else:
  133|                     msg = self.client.messages.create(**self.params(r))
  134|                 if msg.stop_reason == 'refusal':
  135|                     return {'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False,
  136|                             'error': f'refusal: {getattr(msg.stop_details, "category", None)}', 'usage': msg.usage.model_dump()}
  137|                 text = next(b.text for b in msg.content if b.type == 'text')
  138|                 try:
  139|                     data = json.loads(text)
  140|                 except json.JSONDecodeError as e:  # truncated at max_tokens: paid for, so keep the usage
  141|                     return {'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False,
  142|                             'error': f'{msg.stop_reason}: {e}', 'usage': msg.usage.model_dump()}
  143|                 return {'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': True,
  144|                         'data': data, 'usage': msg.usage.model_dump(), 'raw': text}
  145|             except a.RateLimitError:
  146|                 if fast:
  147|                     fast = False
  148|                     continue
  149|                 time.sleep(2 ** attempt + random.random())
  150|             except a.BadRequestError as e:
  151|                 return {'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False, 'error': str(e)}
  152|             except a.APIStatusError as e:
  153|                 if e.status_code < 500:
  154|                     return {'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False, 'error': str(e)}
  155|                 time.sleep(2 ** attempt)
  156|             except a.APIConnectionError:
  157|                 time.sleep(2 ** attempt)
  158|         return {'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False, 'error': 'retries exhausted'}
  159| 
  160|     def run(self, requests):
  161|         from concurrent.futures import ThreadPoolExecutor
  162|         with ThreadPoolExecutor(max_workers=8) as pool:
  163|             return list(pool.map(self._one, requests))
  164| 
  165| 
  166| class AnthropicBatchBackend(AnthropicBackend):
  167|     name = 'anthropic-batch'
  168| 
  169|     def run(self, requests, poll_seconds: int = 30):
  170|         from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
  171|         from anthropic.types.messages.batch_create_params import Request
  172|         batch = self.client.messages.batches.create(requests=[
  173|             Request(custom_id=r['id'], params=MessageCreateParamsNonStreaming(**self.params(r))) for r in requests
  174|         ])
  175|         while self.client.messages.batches.retrieve(batch.id).processing_status != 'ended':
  176|             time.sleep(poll_seconds)
  177|         by_id = {r['id']: r for r in requests}
  178|         out = []
  179|         for res in self.client.messages.batches.results(batch.id):
  180|             r = by_id[res.custom_id]
  181|             if res.result.type != 'succeeded':
  182|                 out.append({'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False, 'error': res.result.type})
  183|                 continue
  184|             msg = res.result.message
  185|             text = next((b.text for b in msg.content if b.type == 'text'), '')
  186|             try:
  187|                 data = json.loads(text)
  188|                 out.append({'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': True,
  189|                             'data': data, 'usage': msg.usage.model_dump(), 'raw': text})
  190|             except json.JSONDecodeError as e:
  191|                 out.append({'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False, 'error': str(e)})
  192|         return out
  193| 
  194| 
  195| class TranscriptBackend(Backend):
  196|     """Hands requests to an external runner through files.
  197| 
  198|     `run` writes every request without an answer to `requests.jsonl` and returns
  199|     the answers already present in `responses.jsonl` (one JSON object per line:
  200|     {"id", "model", "answer": <text or object>}). Call it again after the runner
  201|     has written its answers.
  202|     """
  203|     name = 'transcript'
  204| 
  205|     def __init__(self, folder: Path):
  206|         self.folder = Path(folder)
  207|         self.folder.mkdir(parents=True, exist_ok=True)
  208| 
  209|     def answers(self) -> dict:
  210|         path = self.folder / 'responses.jsonl'
  211|         got = {}
  212|         if path.exists():
  213|             for line in path.read_text().splitlines():
  214|                 if line.strip():
  215|                     row = json.loads(line)
  216|                     got[row['id']] = row
  217|         return got
  218| 
  219|     def run(self, requests):
  220|         got = self.answers()
  221|         pending = [r for r in requests if r['id'] not in got]
  222|         if pending:
  223|             with open(self.folder / 'requests.jsonl', 'w') as f:
  224|                 for r in pending:
  225|                     f.write(json.dumps(r) + '\n')
  226|         out = []
  227|         for r in requests:
  228|             row = got.get(r['id'])
  229|             if row is None:
  230|                 continue
  231|             try:
  232|                 data = row['answer'] if isinstance(row['answer'], dict) else _parse(row['answer'])
  233|                 out.append({'id': r['id'], 'model': row.get('model', r['model']), 'backend': self.name, 'ok': True,
  234|                             'data': data, 'usage': row.get('usage', {}), 'raw': row['answer']})
  235|             except Exception as e:  # a malformed answer is logged, not guessed at
  236|                 out.append({'id': r['id'], 'model': r['model'], 'backend': self.name, 'ok': False, 'error': repr(e)})
  237|         return out
  238| 
  239| 
  240| def merge_answers(folder: Path, requests: list[dict]) -> dict:
  241|     """Fold answers/<batch>.jsonl files into responses.jsonl, checking each
  242|     answer against its request's schema (required keys, enums, p_choice)."""
  243|     folder = Path(folder)
  244|     by_id = {r['id']: r for r in requests}
  245|     good, bad = {}, []
  246|     for f in sorted((folder / 'answers').glob('*.jsonl')):
  247|         for line in f.read_text().splitlines():
  248|             if not line.strip():
  249|                 continue
  250|             try:
  251|                 row = json.loads(line)
  252|                 req = by_id[row['id']]
  253|                 ans = row['answer'] if isinstance(row['answer'], dict) else _parse(row['answer'])
  254|                 sch = req['schema']
  255|                 missing = [k for k in sch['required'] if k not in ans]
  256|                 if missing:
  257|                     raise ValueError(f'missing {missing}')
  258|                 for k, spec in sch['properties'].items():
  259|                     if 'enum' in spec and ans.get(k) not in spec['enum']:
  260|                         raise ValueError(f'{k}={ans.get(k)!r} not in enum')
  261|                 row['answer'] = ans
  262|                 good[row['id']] = row
  263|             except Exception as e:
  264|                 bad.append({'file': f.name, 'line': line[:120], 'error': repr(e)})
  265|     with open(folder / 'responses.jsonl', 'w') as out:
  266|         for row in good.values():
  267|             out.write(json.dumps(row) + '\n')
  268|     return {'merged': len(good), 'rejected': bad, 'missing': sorted(set(by_id) - set(good))}
  269| 
  270| 
  271| def backend(name: str, folder: Path | None = None, effort: str = 'low', max_tokens: int = 4000) -> Backend:
  272|     if name == 'anthropic':
  273|         return AnthropicBackend(effort=effort, max_tokens=max_tokens)
  274|     if name == 'anthropic-batch':
  275|         return AnthropicBatchBackend(effort=effort, max_tokens=max_tokens)
  276|     if name == 'transcript':
  277|         return TranscriptBackend(folder)
  278|     raise ValueError(name)
  279| 
  280| 
  281| # ── Answer cache: an identical request is the same instrument ──
  282| # Keyed on model, system, user and schema (never on meta, run or prompt-version
  283| # labels), so a run that adds one what-if pays only for its new briefs. Only
  284| # live API answers are cached; transcript (subagent) answers never are.
  285| 
  286| def request_key(r: dict) -> str:
  287|     # A request's own effort is part of the instrument; requests without one keep their old keys.
  288|     blob = json.dumps([r['model'], r['system'], r['user'], r['schema']] + ([r['effort']] if r.get('effort') else []), sort_keys=True)
  289|     return hashlib.sha256(blob.encode()).hexdigest()
  290| 
  291| 
  292| class AnswerCache:
  293|     LIVE = ('anthropic', 'anthropic-batch')
  294| 
  295|     def __init__(self, runs_dir: Path):
  296|         self.runs = Path(runs_dir)
  297|         self.file = self.runs / '_cache/answers.jsonl'
  298|         self.index = {}
  299|         if self.file.exists():
  300|             for line in self.file.read_text().splitlines():
  301|                 if line.strip():
  302|                     row = json.loads(line)
  303|                     self.index[row['key']] = row['answer']
  304|         # Backfill from earlier runs' requests and live answers.
  305|         for req_file in self.runs.glob('*/agents/all_requests.jsonl'):
  306|             ans_file = req_file.parent / 'answers.jsonl'
  307|             if not ans_file.exists():
  308|                 continue
  309|             answers = {}
  310|             for line in ans_file.read_text().splitlines():
  311|                 if line.strip():
  312|                     g = json.loads(line)
  313|                     if g.get('ok') and g.get('backend') in self.LIVE:
  314|                         answers[g['id']] = g | {'cached_from': req_file.parent.parent.name}
  315|             for line in req_file.read_text().splitlines():
  316|                 if line.strip():
  317|                     r = json.loads(line)
  318|                     if r['id'] in answers:
  319|                         self.index.setdefault(request_key(r), answers[r['id']])
  320| 
  321|     def get(self, r: dict) -> dict | None:
  322|         hit = self.index.get(request_key(r))
  323|         if not hit:
  324|             return None
  325|         return {**hit, 'id': r['id'], 'cached': True, 'usage': {}}
  326| 
  327|     def put(self, r: dict, answer: dict):
  328|         if not answer.get('ok') or answer.get('backend') not in self.LIVE:
  329|             return
  330|         k = request_key(r)
  331|         self.index[k] = answer
  332|         self.file.parent.mkdir(parents=True, exist_ok=True)
  333|         with open(self.file, 'a') as f:
  334|             f.write(json.dumps({'key': k, 'answer': answer}) + '\n')
  335| 
  336| 
  337| # ── Spend ledger: every paid call, for the record (sessions-report) ──
  338| 
  339| LEDGER = ROOT / 'sessions/spend.jsonl'
  340| # Who the spend is for: the access key's name while the intake worker models
  341| # that key's text (intake.process_queue), else None. For the record only: the
  342| # caps count every line, whoever's it was.
  343| SPEND_WHO: str | None = None
  344| 
  345| 
  346| def record_spend(stage: str, dollars: float, run: str = '', note: str = ''):
  347|     if dollars <= 0:
  348|         return
  349|     LEDGER.parent.mkdir(parents=True, exist_ok=True)
  350|     now = time.gmtime()
  351|     with open(LEDGER, 'a') as f:
  352|         f.write(json.dumps({'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', now), 'day': time.strftime('%Y-%m-%d', now),
  353|                             'stage': stage, 'dollars': round(dollars, 5), 'run': run, 'note': note, 'who': SPEND_WHO}) + '\n')
  354| 
  355| 
  356| def spent(day: str | None = None, ledger: Path = LEDGER) -> tuple[float, float]:
  357|     """(dollars recorded on `day`, UTC, default today; dollars recorded in that day's
  358|     calendar month), counting every line whoever's text it was. These are what the
  359|     intake's caps are measured against (intake.left). serve/guard.ts `spent` reads
  360|     the ledger the same way before it queues text."""
  361|     day = day or time.strftime('%Y-%m-%d', time.gmtime())
  362|     month = day[:7]
  363|     today, this_month = 0.0, 0.0
  364|     for line in ledger.read_text().splitlines() if ledger.exists() else []:
  365|         try:
  366|             r = json.loads(line)
  367|             d = float(r['dollars'])
  368|             line_day = str(r['day'])
  369|         except (ValueError, KeyError, TypeError):
  370|             continue
  371|         if line_day.startswith(month):
  372|             this_month += d
  373|         if line_day == day:
  374|             today += d
  375|     return today, this_month
  376| 
```

## `simharness/paired.py`

```python
    1| """Paired control/counterfactual answers → per-cohort effects on the backbone.
    2| 
    3| For agent i in cohort k, the same persona, seed, paraphrase and model answer
    4| the control brief (the world as it was) and the counterfactual brief (the
    5| world with one settled fact changed). The counterfactual effect is the
    6| within-cohort difference, on the logit scale:
    7| 
    8|     Δt_k = logit(E[p_vote | cf])  − logit(E[p_vote | control])
    9|     Δr_k = logit(R2 | cf)         − logit(R2 | control)
   10|     Δo_k = logit(O  | cf)         − logit(O  | control)
   11| 
   12| where R2 is the Republican share of the two-party vote the cohort's agents
   13| expect to cast (Σ p_vote·p_R / Σ p_vote·(p_R+p_D)) and O the minor-party share
   14| of all votes. A bias common to both arms (the model knowing who won, a lean
   15| in the model) cancels in the difference; what doesn't cancel is measured by
   16| the control's distance from the calibrated backbone:
   17| 
   18|     b_k = logit(R2 | control) − logit(r_k backbone)
   19| 
   20| and the effect is shrunk by the fixed rule in METHOD.md (shrinkage).
   21| """
   22| from __future__ import annotations
   23| 
   24| import numpy as np
   25| 
   26| from .stats import logit
   27| 
   28| N0 = 8.0          # shrinkage pseudo-count
   29| BIAS_SCALE = 1.0  # logit scale for bias shrinkage
   30| 
   31| 
   32| def normalize(ans: dict, label_to_party: dict) -> dict | None:
   33|     """One structured answer → {p_vote, R, D, O, choice, able} in party terms."""
   34|     if not ans:
   35|         return None
   36|     able = ans.get('able_to_vote', 'yes')
   37|     pv = max(0.0, min(1.0, float(ans.get('p_vote', 0)) / 100))
   38|     if able == 'no':
   39|         pv = 0.0
   40|     pc = ans.get('p_choice') or {}
   41|     shares = {'R': 0.0, 'D': 0.0, 'O': 0.0}
   42|     for label, v in pc.items():
   43|         party = label_to_party.get(label, 'O') if label != 'other' else 'O'
   44|         shares[party] += max(0.0, float(v))
   45|     tot = sum(shares.values())
   46|     if tot <= 0:
   47|         # An answer with no leanings is kept for turnout only.
   48|         shares = {'R': np.nan, 'D': np.nan, 'O': np.nan}
   49|     else:
   50|         shares = {k: v / tot for k, v in shares.items()}
   51|     c = ans.get('choice', 'none')
   52|     choice = 'home' if (c == 'none' or pv < 0.5) else ('O' if c == 'other' else label_to_party.get(c, 'O'))
   53|     if able == 'no':
   54|         choice = 'barred'
   55|     return {'p_vote': pv, **shares, 'choice': choice, 'able': able}
   56| 
   57| 
   58| def cohort_stats(rows: list[dict]) -> dict:
   59|     pv = np.array([r['p_vote'] for r in rows])
   60|     R = np.array([r['R'] for r in rows])
   61|     D = np.array([r['D'] for r in rows])
   62|     O = np.array([r['O'] for r in rows])
   63|     ok = ~np.isnan(R)
   64|     w = pv[ok]
   65|     # Half-count smoothing (Jeffreys-style): a cohort of four who all say 0
   66|     # can't produce an infinite logit difference.
   67|     turnout = float((pv.sum() + 0.5) / (len(pv) + 1)) if len(pv) else np.nan
   68|     if w.sum() <= 0.05:
   69|         return {'turnout': turnout, 'R2': np.nan, 'O': np.nan, 'n': len(rows)}
   70|     r_votes, d_votes, o_votes = (w * R[ok]).sum(), (w * D[ok]).sum(), (w * O[ok]).sum()
   71|     return {
   72|         'turnout': turnout,
   73|         'R2': float((r_votes + 0.5) / (r_votes + d_votes + 1)),
   74|         'O': float((o_votes + 0.5) / (r_votes + d_votes + o_votes + 1)),
   75|         'n': len(rows),
   76|     }
   77| 
   78| 
   79| def diff(cf: dict, ctl: dict) -> dict:
   80|     out = {}
   81|     for key, name in (('turnout', 'dt'), ('R2', 'dr'), ('O', 'do')):
   82|         a, b = cf.get(key), ctl.get(key)
   83|         out[name] = float(logit(a) - logit(b)) if (a is not None and b is not None and not np.isnan(a) and not np.isnan(b)) else 0.0
   84|     return out
   85| 
   86| 
   87| def floor_spread(boot: dict, point: dict, pairs: dict, draws: int, rng: np.random.Generator) -> dict:
   88|     """D33: who was interviewed is part of the uncertainty. Resampling a cohort's own one or
   89|     two people says almost nothing about the people who might have been drawn instead (one
   90|     person resampled is always that person: no spread at all). So each cohort's draws get at
   91|     least the spread of a mean of n people, with the person-to-person spread estimated from
   92|     every pair in the run: sd_k >= s / sqrt(n_k), where s is the national bootstrap sd
   93|     times sqrt(N). Draws keep their shape where they have one; otherwise normal noise."""
   94|     rows = [(p[0], p[1]) for ps in pairs.values() for p in ps if p[0] and p[1]]
   95|     N = len(rows)
   96|     if N < 2:
   97|         return boot
   98|     nat = {'dt': np.empty(draws), 'dr': np.empty(draws), 'do': np.empty(draws)}
   99|     for j in range(draws):
  100|         s = rng.choice(N, size=N, replace=True)
  101|         dd = diff(cohort_stats([rows[i][1] for i in s]), cohort_stats([rows[i][0] for i in s]))
  102|         for key in nat:
  103|             nat[key][j] = dd[key]
  104|     out = {}
  105|     for k, bd in boot.items():
  106|         n = max(1, point[k]['n'])
  107|         out[k] = {}
  108|         for key, d in bd.items():
  109|             target = float(np.std(nat[key])) * np.sqrt(N / n)
  110|             sd, mu = float(np.std(d)), float(point[k][key])
  111|             if sd >= target or target <= 0:
  112|                 out[k][key] = d
  113|             elif sd > 1e-9:
  114|                 out[k][key] = mu + (d - float(np.mean(d))) * (target / sd)
  115|             else:
  116|                 out[k][key] = mu + rng.normal(0.0, target, len(d))
  117|     return out
  118| 
  119| 
  120| def effects(pairs: dict, backbone_r2: dict, region_of: dict, draws: int, rng: np.random.Generator,
  121|             exposed: set | None = None, weights: dict | None = None, floor: bool = False) -> dict:
  122|     """pairs: {cohort: [(control_row, cf_row, paraphrase, model), ...]}.
  123|     floor: widen each cohort's draws to the sampling spread of who was interviewed (D33;
  124|     compiled what-ifs only, so hand-written what-ifs' numbers are unchanged).
  125| 
  126|     Returns {'cohorts': {k: {...point estimates, bias, weight, draws: {dt, dr, do: [draws]}}},
  127|              'national': {...}, 'regions': {...}}.
  128|     """
  129|     exposed = exposed or set()
  130|     point, boot = {}, {}
  131|     for k, ps in pairs.items():
  132|         ctl = [p[0] for p in ps if p[0] and p[1]]
  133|         cf = [p[1] for p in ps if p[0] and p[1]]
  134|         if not ctl:
  135|             continue
  136|         c_stats, f_stats = cohort_stats(ctl), cohort_stats(cf)
  137|         d = diff(f_stats, c_stats)
  138|         bias = float(logit(c_stats['R2']) - logit(backbone_r2[k])) if not np.isnan(c_stats['R2']) and k in backbone_r2 else 0.0
  139|         point[k] = {'control': c_stats, 'counterfactual': f_stats, **d, 'bias': bias, 'n': len(ctl)}
  140|         idx = np.arange(len(ctl))
  141|         bd = {'dt': np.empty(draws), 'dr': np.empty(draws), 'do': np.empty(draws)}
  142|         for j in range(draws):
  143|             s = rng.choice(idx, size=len(idx), replace=True)
  144|             dd = diff(cohort_stats([cf[i] for i in s]), cohort_stats([ctl[i] for i in s]))
  145|             for key in bd:
  146|                 bd[key][j] = dd[key]
  147|         boot[k] = bd
  148| 
  149|     if floor:
  150|         boot = floor_spread(boot, point, pairs, draws, rng)
  151|     national_bias = float(np.mean([v['bias'] for v in point.values()])) if point else 0.0
  152| 
  153|     def weight(n, bias):
  154|         return (n / (n + N0)) * (1.0 / (1.0 + (bias / BIAS_SCALE) ** 2))
  155| 
  156|     # National effect: adult-weighted mean of cohort effects (per draw).
  157|     ks = list(point)
  158|     wts = np.array([(weights or {}).get(k, 1.0) for k in ks], float)
  159|     nat = {key: np.average([boot[k][key] for k in ks], axis=0, weights=wts) if ks else np.zeros(draws) for key in ('dt', 'dr', 'do')}
  160|     regions = {}
  161|     for r in sorted({region_of[k] for k in ks}):
  162|         rk = [k for k in ks if region_of[k] == r]
  163|         n_r = sum(point[k]['n'] for k in rk)
  164|         b_r = float(np.mean([point[k]['bias'] for k in rk]))
  165|         w_r = weight(n_r, b_r)
  166|         rw = np.array([(weights or {}).get(k, 1.0) for k in rk], float)
  167|         regions[r] = {'weight': w_r, 'bias': b_r, 'n': n_r,
  168|                       'draws': {key: w_r * np.average([boot[k][key] for k in rk], axis=0, weights=rw) + (1 - w_r) * nat[key]
  169|                                 for key in ('dt', 'dr', 'do')}}
  170|     cohorts = {}
  171|     for k in ks:
  172|         b = national_bias if k in exposed else point[k]['bias']
  173|         w = weight(point[k]['n'], b)
  174|         reg = regions[region_of[k]]['draws']
  175|         cohorts[k] = {**point[k], 'bias_used': b, 'weight': w, 'exposed': k in exposed,
  176|                       'draws': {key: w * boot[k][key] + (1 - w) * reg[key] for key in ('dt', 'dr', 'do')}}
  177|     return {'cohorts': cohorts, 'regions': regions,
  178|             'national': {key: {'mean': float(np.mean(v)), 'lo': float(np.quantile(v, 0.1)), 'hi': float(np.quantile(v, 0.9))}
  179|                          for key, v in nat.items()},
  180|             'national_bias': national_bias}
```

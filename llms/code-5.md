# synthetic-electorate-toy: source and docs, part 5 of 16

Generated from commit `5fc0a9e54bc9` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `scripts/harness/build_republic.py` to `serve/contract.test.ts`. Lines are numbered as in the repository.

## `scripts/harness/build_republic.py`

```python
    1| """Early-republic labels and franchise, 1789–1864.
    2| 
    3|     python3 scripts/harness/build_republic.py returns     # → labels/state_pres_1789_1864.csv
    4|     python3 scripts/harness/build_republic.py franchise   # → franchise/state_franchise_1789_1864.csv
    5|     python3 scripts/harness/build_republic.py all
    6| 
    7| Returns are parsed from the per-election Wikipedia "results by state" tables
    8| (cached under labels/raw/wikipedia_1789_1864/; those tables cite Tufts' "A New
    9| Nation Votes" for 1789–1824 and Dubin / CQ / Leip for 1824+). How each state
   10| chose its electors is hand-keyed (CHOSEN below; Every Vote Equal Table 2.1 /
   11| the Wikipedia pages), as is the national EV check (NATIONAL_EV).
   12| 
   13| Party slots (fixed across agents): R = Federalist (1789–1816; Washington in
   14| 1789/92 with D=0; DeWitt Clinton 1812 as the Federalist-backed candidate),
   15| J.Q. Adams 1824, National Republican 1828/32, Whig 1836–52 (all four 1836
   16| Whigs), Republican 1856+. D = Democratic-Republican 1796–1820, Jackson 1824,
   17| Democratic 1828+ (Douglas in 1860). O = everyone else; R=0 in 1820. Named
   18| thirds (own votes in `third`): 1832 Wirt, 1848 Van Buren, 1856 Fillmore,
   19| 1860 Breckinridge.
   20| 
   21| Franchise rules are hand-coded from Keyssar, The Right to Vote (2009 ed.),
   22| Tables A.1–A.4, with eligibility shares tagged [I] (see FRANCHISE notes and
   23| notes/G.md).
   24| """
   25| import io
   26| import re
   27| import sys
   28| import urllib.parse
   29| import urllib.request
   30| from pathlib import Path
   31| 
   32| import pandas as pd
   33| 
   34| HERE = Path(__file__).resolve().parents[2]
   35| sys.path.insert(0, str(HERE))
   36| from simharness.config import CACHE  # noqa: E402
   37| from simharness.geo import CODE_OF  # noqa: E402
   38| 
   39| RAW = CACHE / 'labels/raw/wikipedia_1789_1864'
   40| YEARS = list(range(1789, 1793, 3)) + list(range(1796, 1865, 4))  # 1789, 1792, 1796 … 1864
   41| CODE = {k.casefold(): v for k, v in CODE_OF.items()}
   42| 
   43| 
   44| def page(y: int) -> str:
   45|     f = RAW / f'{y}.html'
   46|     if not f.exists():
   47|         RAW.mkdir(parents=True, exist_ok=True)
   48|         t = urllib.parse.quote(f'{"1788–89" if y == 1789 else y}_United_States_presidential_election')
   49|         req = urllib.request.Request(f'https://en.wikipedia.org/w/index.php?title={t}&action=render',
   50|                                      headers={'User-Agent': 'SimulacraHarness/1.0 (historical research)'})
   51|         f.write_bytes(urllib.request.urlopen(req).read())
   52|     return f.read_text()
   53| 
   54| 
   55| def tables(y):
   56|     return pd.read_html(io.StringIO(page(y)))
   57| 
   58| 
   59| # ---------------------------------------------------------------- method of choice
   60| # Legislature-chosen states (everything else that appointed electors was popular).
   61| LEG = {
   62|     1789: 'CT GA NJ SC', 1792: 'CT DE GA NJ NY NC RI SC VT', 1796: 'CT DE NJ NY RI SC TN VT',
   63|     1800: 'CT DE GA MA NH NJ NY PA SC TN VT', 1804: 'CT DE GA NY SC VT', 1808: 'CT DE GA MA NY SC VT',
   64|     1812: 'CT DE GA LA NJ NY NC SC VT', 1816: 'CT DE GA IN LA MA NY SC VT',
   65|     1820: 'AL DE GA IN LA MO NY SC VT', 1824: 'DE GA LA NY SC VT', 1828: 'DE SC',
   66|     **{y: 'SC' for y in range(1832, 1861, 4)}, 1864: '',
   67| }
   68| NONE = {1789: {'NY': 'legislature deadlocked; no electors appointed'},
   69|         1864: {**{s: 'seceded; no electors' for s in 'AL AR FL GA MS NC SC TX VA'.split()},
   70|                'LA': 'held a Union-occupation election; Congress did not count its 7 EVs',
   71|                'TN': 'held a Union-occupation election; Congress did not count its 10 EVs'}}
   72| CHOSEN_NOTE = {
   73|     (1789, 'MA'): 'hybrid: voters nominated by district, legislature chose (popular vote = nominating ballots)',
   74|     (1792, 'MA'): 'hybrid: district popular vote, legislature filled seats lacking a majority',
   75|     (1796, 'MA'): 'hybrid: district popular vote, legislature filled seats lacking a majority',
   76|     (1789, 'NH'): 'popular vote, legislature chose where no majority',
   77|     (1792, 'KY'): 'electors chosen by the state electoral college of senators [I: coded popular, no returns]',
   78|     (1796, 'KY'): 'no surviving returns',
   79|     (1796, 'TN'): 'electors chosen by electors appointed by the legislature',
   80|     (1800, 'TN'): 'electors chosen by electors appointed by the legislature',
   81| }
   82| 
   83| RET_NOTE = {
   84|     (1860, 'NJ'): 'anti-Lincoln fusion ticket (Douglas/Bell/Breckinridge) counted in other; 3 fusion electors voted Douglas',
   85|     (1860, 'NY'): 'anti-Lincoln fusion ticket counted in other',
   86|     (1860, 'PA'): 'Breckinridge-headed fusion ticket counted in other; straight Douglas votes in dem',
   87|     (1860, 'RI'): 'Douglas-led fusion ticket counted in dem',
   88|     (1812, 'PA'): 'returns not extant as a party split (leading elector ran on both tickets)',
   89|     (1828, 'NY'): 'votes are the at-large tally; 34 district electors chosen in districts',
   90|     (1828, 'ME'): 'votes are the at-large tally; 7 district electors',
   91|     (1820, 'MA'): 'Federalist elector slates (no Federalist presidential candidate) counted in other (R=0 in 1820)',
   92| }
   93| 
   94| # National electoral vote check: (R, D, O, appointed electors)
   95| NATIONAL_EV = {
   96|     1789: (69, 0, 0, 73), 1792: (132, 0, 0, 135), 1796: (71, 67, 0, 138), 1800: (65, 73, 0, 138),
   97|     1804: (14, 162, 0, 176), 1808: (47, 122, 6, 176), 1812: (89, 128, 0, 218), 1816: (34, 183, 0, 221),
   98|     1820: (0, 231, 1, 235), 1824: (84, 99, 78, 261), 1828: (83, 178, 0, 261), 1832: (49, 219, 18, 288),
   99|     1836: (124, 170, 0, 294), 1840: (234, 60, 0, 294), 1844: (105, 170, 0, 275), 1848: (163, 127, 0, 290),
  100|     1852: (42, 254, 0, 296), 1856: (114, 174, 8, 296), 1860: (180, 12, 111, 303), 1864: (212, 21, 0, 234),
  101| }
  102| EV_NOTE = {
  103|     1789: 'pre-12th Amendment (two votes per elector): slot EVs = electors voting for Washington; Adams 34 etc. were second votes',
  104|     1792: 'pre-12th Amendment: slot EVs = votes for Washington (132 of 135; 3 not cast); Adams/Clinton were second votes',
  105|     1796: 'pre-12th Amendment: R = Adams votes, D = Jefferson votes; MD elector voting Adams+Jefferson counted R',
  106|     1800: 'pre-12th Amendment: Jefferson 73 = Burr 73 tie (D), House chose Jefferson Feb 1801; R = Adams 65',
  107|     1824: 'no EV majority: House chose Adams (R) on 9 Feb 1825; O = Crawford 41 + Clay 37',
  108|     1836: 'R = all Whigs (Harrison 73, White 26, Webster 14, Mangum 11)',
  109|     1860: 'O = Breckinridge 72 + Bell 39',
  110|     1864: 'LA and TN EVs not counted; one NV elector did not vote',
  111| }
  112| 
  113| 
  114| # ---------------------------------------------------------------- parsing
  115| NONNUM_ZERO = ('—', '-', '–', 'no ballots', 'no candidate', '', 'nan')
  116| 
  117| 
  118| def cell(x):
  119|     """→ (value|None, partial, missing)."""
  120|     s = re.sub(r'\[[^\]]*\]', '', str(x)).strip()
  121|     if s.lower() in NONNUM_ZERO:
  122|         return 0.0, False, False
  123|     partial = s.endswith('+')
  124|     s2 = s.rstrip('+').replace(',', '').replace('%', '')
  125|     try:
  126|         return float(s2), partial, False
  127|     except ValueError:
  128|         return None, False, True
  129| 
  130| 
  131| def state_of(x):
  132|     s = re.sub(r'\[[^\]]*\]', '', str(x))
  133|     s = re.sub(r'\(.*?\)', '', s)
  134|     s = re.sub(r'[^A-Za-z \-–]', '', s)
  135|     s = re.split(r'[–-]', s)[0].strip()
  136|     return CODE.get(s.casefold())
  137| 
  138| 
  139| def is_district(x):
  140|     s = re.sub(r'\[[^\]]*\]', '', str(x))
  141|     return bool(re.search(r'[–-]', s))
  142| 
  143| 
  144| def flat(t):
  145|     if isinstance(t.columns, pd.MultiIndex):
  146|         return [(str(a), str(b)) for a, b in t.columns]
  147|     return [(str(a), str(a)) for a in t.columns]
  148| 
  149| 
  150| def popular(t, slotmap):
  151|     """slotmap: [(substring of group header, slot)]; slot in R/D/O/T (T = named third, also O).
  152|     Returns {state: dict(rep, dem, other, third, total, partial, missing, ev_*)}."""
  153|     cols = flat(t)
  154|     groups = {}
  155|     for j, (g, sub) in enumerate(cols):
  156|         gl = g.lower()
  157|         slot = next((s for k, s in slotmap if k.lower() in gl), None)
  158|         if slot is None and 'total' in gl:
  159|             slot = 'TOT'
  160|         if slot is None:
  161|             continue
  162|         sl = sub.lower()
  163|         if 'elector' in sl or 'e.v' in sl:
  164|             kind = 'ev'
  165|         elif sl in ('#', 'votes', 'no.', 'votes cast', 'total') or (slot == 'TOT' and 'unnamed' not in sl):
  166|             kind = 'v'
  167|         else:
  168|             continue
  169|         groups.setdefault((slot, kind), []).append(j)
  170|     out = {}
  171|     has_at_large = {state_of(r.iloc[0]) for _, r in t.iterrows() if state_of(r.iloc[0]) and not is_district(r.iloc[0])}
  172|     for _, r in t.iterrows():
  173|         st = state_of(r.iloc[0])
  174|         if not st:
  175|             continue
  176|         skip_votes = st in has_at_large and is_district(r.iloc[0])   # districts re-tally the at-large ballots
  177|         d = out.setdefault(st, {'rep': 0.0, 'dem': 0.0, 'other': 0.0, 'third': 0.0, 'total': 0.0, 'partial': False,
  178|                                 'missing': False, 'any': False, 'ev_rep': 0.0, 'ev_dem': 0.0, 'ev_other': 0.0})
  179|         for (slot, kind), js in groups.items():
  180|             for j in js:
  181|                 v, p, m = cell(r.iloc[j])
  182|                 if kind == 'ev':
  183|                     if v is not None and slot != 'TOT':
  184|                         d[{'R': 'ev_rep', 'D': 'ev_dem'}.get(slot, 'ev_other')] += v
  185|                     continue
  186|                 if skip_votes:
  187|                     continue
  188|                 if m:
  189|                     d['missing'] = True
  190|                     continue
  191|                 d['partial'] |= p and slot in ('R', 'D', 'T')   # '27+' scattering is not a partial return
  192|                 d['any'] |= (v or 0) > 0
  193|                 if slot == 'TOT':
  194|                     d['total'] += v
  195|                 else:
  196|                     d[{'R': 'rep', 'D': 'dem'}.get(slot, 'other')] += v
  197|                     if slot == 'T':
  198|                         d['third'] += v
  199|     return out
  200| 
  201| 
  202| def ev_by_candidate(t, slotmap, electors_col):
  203|     """Per-candidate EV tables (pre-12th Amendment, and 1808/1812): slot EVs per state."""
  204|     cols = flat(t)
  205|     out = {}
  206|     for _, r in t.iterrows():
  207|         st = state_of(r.iloc[0])
  208|         if not st:
  209|             continue
  210|         e = {'R': 0.0, 'D': 0.0, 'O': 0.0}
  211|         for j, (g, sub) in enumerate(cols):
  212|             name = sub if g != sub else g
  213|             if g.lower().startswith('for vice'):
  214|                 continue
  215|             slot = next((s for k, s in slotmap if k.lower() in name.lower()), None)
  216|             if slot:
  217|                 v, _, _ = cell(r.iloc[j])
  218|                 e[slot] += v or 0
  219|         n, _, _ = cell(r.iloc[electors_col])
  220|         out[st] = (e, n)
  221|     return out
  222| 
  223| 
  224| # Table index of the popular-vote results-by-state table and the slot map, per year.
  225| POP = {
  226|     1789: (9, [('Anti-Federalist', 'O'), ('Federalist', 'R'), ('Total', 'TOT')]),
  227|     1792: (5, [('Democratic-Republican', 'O'), ('Federalist', 'R')]),
  228|     1796: (7, [('Adams', 'R'), ('Jefferson', 'D'), ('State total', 'TOT')]),
  229|     1800: (8, [('Jefferson', 'D'), ('Adams', 'R'), ('Other', 'O'), ('State total', 'TOT')]),
  230|     1804: (9, [('Jefferson', 'D'), ('Federalist', 'R'), ('Other', 'O'), ('Total', 'TOT')]),
  231|     1808: (10, [('Madison', 'D'), ('Pinckney', 'R'), ('Monroe', 'O'), ('Other', 'O')]),
  232|     1812: (15, [('Madison', 'D'), ('Clinton', 'R'), ('Other', 'O')]),
  233|     1816: (12, [('Monroe', 'D'), ('Federalist', 'R'), ('Others', 'O'), ('Total', 'TOT')]),
  234|     1820: (9, [('Monroe', 'D'), ('Federalist', 'O'), ('Others', 'O')]),
  235|     1824: (8, [('Jackson', 'D'), ('Adams', 'R'), ('Clay', 'O'), ('Crawford', 'O'), ('Other', 'O'), ('State total', 'TOT')]),
  236|     1828: (7, [('Jackson', 'D'), ('Adams', 'R'), ('State Total', 'TOT')]),
  237|     1832: (14, [('Jackson', 'D'), ('Clay', 'R'), ('Wirt', 'T'), ('Floyd', 'O'), ('State Total', 'TOT')]),
  238|     1836: (13, [('Van Buren', 'D'), ('Whig', 'R'), ('Total', 'TOT')]),
  239|     1840: (10, [('Harrison', 'R'), ('Van Buren', 'D'), ('Birney', 'O'), ('State Total', 'TOT')]),
  240|     1844: (9, [('Polk', 'D'), ('Clay', 'R'), ('Birney', 'O'), ('State Total', 'TOT')]),
  241|     1848: (12, [('Taylor', 'R'), ('Cass', 'D'), ('Van Buren', 'T'), ('State Total', 'TOT')]),
  242|     1852: (9, [('Pierce', 'D'), ('Scott', 'R'), ('Hale', 'O'), ('Others', 'O'), ('State Total', 'TOT')]),
  243|     1856: (13, [('Buchanan', 'D'), ('Fremont', 'R'), ('Frémont', 'R'), ('Fillmore', 'T'), ('State Total', 'TOT')]),
  244|     1860: (14, [('Lincoln', 'R'), ('Douglas', 'D'), ('Breckinridge', 'T'), ('Bell', 'O'), ('Other', 'O'), ('State Total', 'TOT')]),
  245|     1864: (13, [('Lincoln', 'R'), ('McClellan', 'D'), ('State Total', 'TOT')]),
  246| }
  247| # Years whose EVs come from a per-candidate table: (table index, slot map, electors column)
  248| EVTAB = {
  249|     1789: (10, [('Washington', 'R')], 1),
  250|     1792: (6, [('Washington', 'R')], 1),
  251|     1796: (6, [('John Adams', 'R'), ('Jefferson', 'D')], 1),
  252|     1800: (7, [('John Adams', 'R'), ('Jefferson', 'D')], 1),
  253|     1808: (9, [('Madison', 'D'), ('Pinckney', 'R'), ('Clinton', 'O')], 1),
  254|     1812: (14, [('Madison', 'D'), ('DeWitt Clinton', 'R')], 1),
  255| }
  256| 
  257| 
  258| def returns() -> pd.DataFrame:
  259|     rows = []
  260|     for y in YEARS:
  261|         ts = tables(y)
  262|         ti, smap = POP[y]
  263|         pop = popular(ts[ti], smap)
  264|         if y in EVTAB:
  265|             ei, emap, ecol = EVTAB[y]
  266|             evs = ev_by_candidate(ts[ei], emap, ecol)
  267|         else:  # slot EVs from the popular table; electors appointed = column 1, summed over district rows
  268|             evs = {}
  269|             for _, r in ts[ti].iterrows():
  270|                 st = state_of(r.iloc[0])
  271|                 if st:
  272|                     n, _, _ = cell(r.iloc[1])
  273|                     p = pop.get(st, {})
  274|                     evs[st] = ({'R': p.get('ev_rep', 0), 'D': p.get('ev_dem', 0), 'O': p.get('ev_other', 0)},
  275|                                evs.get(st, (None, 0))[1] + (n or 0))
  276|         if y == 1789:
  277|             evs.setdefault('NY', ({'R': 0, 'D': 0, 'O': 0}, 0))
  278|         leg = set(LEG[y].split())
  279|         for st in sorted(set(evs) | set(NONE.get(y, {}))):
  280|             e, n = evs.get(st, ({'R': 0, 'D': 0, 'O': 0}, 0))
  281|             notes = []
  282|             if st in NONE.get(y, {}):
  283|                 chosen, n, e = 'none', 0, {'R': 0, 'D': 0, 'O': 0}
  284|                 notes.append(NONE[y][st])
  285|             elif st in leg:
  286|                 chosen = 'legislature'
  287|             else:
  288|                 chosen = 'popular'
  289|             if (y, st) in CHOSEN_NOTE:
  290|                 notes.append(CHOSEN_NOTE[(y, st)])
  291|             if y == 1796 and e['R'] + e['D'] > n:   # MD: one elector voted Adams + Jefferson
  292|                 e['D'] = n - e['R']
  293|             if y in (1789, 1792):
  294|                 e['O'] = 0
  295|             p = pop.get(st)
  296|             rec = {'year': y, 'state': st, 'rep': None, 'dem': None, 'other': None, 'total': None, 'third': None,
  297|                    'ev_rep': e['R'], 'ev_dem': e['D'], 'ev_other': e['O'], 'ev_total': n, 'chosen_by': chosen,
  298|                    'source': f'Wikipedia "{y} United States presidential election", results by state '
  299|                              f'({"Tufts A New Nation Votes" if y <= 1824 else "Dubin/CQ/Leip"} figures as cited)'}
  300|             if chosen == 'popular':
  301|                 if p and p['any'] and not p['missing']:
  302|                     tot = max(p['total'], p['rep'] + p['dem'] + p['other'])
  303|                     rec.update(rep=p['rep'], dem=p['dem'], other=tot - p['rep'] - p['dem'], total=tot, third=p['third'])
  304|                     if p['partial']:
  305|                         notes.append('partial returns (some counties/districts missing): do not use for turnout')
  306|                 elif p and p['any'] and (p['rep'] + p['dem'] > 0 or y <= 1792):
  307|                     tot = p['rep'] + p['dem'] + p['other']
  308|                     rec.update(rep=p['rep'], dem=p['dem'], other=p['other'], total=tot, third=p['third'])
  309|                     notes.append('partial returns (some districts/candidates not extant): do not use for turnout')
  310|                 else:
  311|                     notes.append('popular vote held but returns not extant in the compilation')
  312|             if (y, st) in RET_NOTE:
  313|                 notes.append(RET_NOTE[(y, st)])
  314|             rec['note'] = '; '.join(notes)
  315|             rows.append(rec)
  316|     df = pd.DataFrame(rows)
  317|     # Hand fixes where the tables do not carry the EV split cleanly.
  318|     df = fix_ev(df)
  319|     for y, (r, d, o, n) in NATIONAL_EV.items():
  320|         s = df[df.year == y][['ev_rep', 'ev_dem', 'ev_other', 'ev_total']].sum()
  321|         got = (s.ev_rep, s.ev_dem, s.ev_other, s.ev_total)
  322|         flag = '' if got == (r, d, o, n) else f'   <-- expected {(r, d, o, n)}'
  323|         print(y, 'EV R/D/O/appointed', tuple(int(x) for x in got), flag)
  324|     for y, t in EV_NOTE.items():
  325|         i = df.index[(df.year == y)][0]
  326|         df.loc[i, 'note'] = '; '.join(x for x in [df.loc[i, 'note'], f'[national EV] {t}'] if x)
  327|     return df
  328| 
  329| 
  330| def fix_ev(df):
  331|     def setev(y, st, r=None, d=None, o=None, n=None):
  332|         i = df.index[(df.year == y) & (df.state == st)][0]
  333|         for k, v in (('ev_rep', r), ('ev_dem', d), ('ev_other', o), ('ev_total', n)):
  334|             if v is not None:
  335|                 df.loc[i, k] = v
  336|     setev(1812, 'OH', n=8)          # 8 electors appointed, 7 voted
  337|     setev(1816, 'DE', r=3)          # 4 appointed, 3 voted (King)
  338|     setev(1816, 'MD', r=0)          # 3 Federalist district electors did not vote
  339|     setev(1864, 'NV', n=3)          # 3 appointed, 1 elector snowbound
  340|     return df
  341| 
  342| 
  343| # ---------------------------------------------------------------- franchise
  344| # Per state: list of (first election year, rule) in force from that election on. Rule fields:
  345| #   q   = qualification type: 'prop' (freehold/estate), 'tax' (taxpaying, incl. militia/road-work
  346| #         alternatives), 'univ' (adult male, residence only)
  347| #   wc  = [I] share of adult white men meeting it (Keyssar ch. 2 & App. A; Engerman & Sokoloff 2005;
  348| #         Williamson 1960 — rough, ±0.1)
  349| #   blk = free Black men: 'eq' (same terms as whites), 'no' (barred), 'ny250' ($250 freehold, NY 1821)
  350| #   lit / alien / women flags; why = the legal change, with its date
  351| UNIV, TAXQ = 0.95, 0.88   # residence/pauper exclusions; taxpaying exclusions
  352| F = {
  353|     'CT': [(1789, dict(q='prop', wc=0.65, blk='eq', why='freehold 40s/yr or £40 personal estate')),
  354|            (1816, dict(q='prop', wc=0.65, blk='no', why='1814 statute limits to white men')),
  355|            (1820, dict(q='tax', wc=TAXQ, blk='no', why='1818 constitution: taxpaying or militia service or $7 freehold')),
  356|            (1848, dict(q='univ', wc=UNIV, blk='no', why='1845 amendment drops tax/militia')),
  357|            (1856, dict(q='univ', wc=0.93, blk='no', lit=1, why='1855 amendment: must read the constitution or statutes'))],
  358|     'DE': [(1789, dict(q='prop', wc=0.60, blk='eq', why='1776: 50-acre freehold or £40 estate')),
  359|            (1792, dict(q='tax', wc=0.85, blk='no', why='1792 constitution: white freemen who paid a state/county tax'))],
  360|     'GA': [(1789, dict(q='tax', wc=TAXQ, blk='no', why='1789/1798 constitutions: white(1777)/citizen men who paid all taxes due'))],
  361|     'MD': [(1789, dict(q='prop', wc=0.60, blk='eq', why='1776: 50-acre freehold or £30 property; free Black owners not barred by text')),
  362|            (1804, dict(q='univ', wc=UNIV, blk='no', why='1801-02 amendment drops property, limits to white men'))],
  363|     'MA': [(1789, dict(q='prop', wc=0.75, blk='eq', why='1780: freehold £3/yr income or £60 estate')),
  364|            (1824, dict(q='tax', wc=TAXQ, blk='eq', why='1821 amendment: paid a state or county tax')),
  365|            (1860, dict(q='tax', wc=0.85, blk='eq', lit=1, why='1857 amendment: read the constitution and write one’s name'))],
  366|     'NH': [(1789, dict(q='tax', wc=0.90, blk='eq', why='1784: male inhabitants paying a poll tax')),
  367|            (1792, dict(q='univ', wc=UNIV, blk='eq', why='1792 constitution drops the poll-tax requirement'))],
  368|     'NJ': [(1789, dict(q='prop', wc=0.75, blk='eq', alien=1, why='1776: all inhabitants worth £50 (no sex, race or citizenship bar)')),
  369|            (1792, dict(q='prop', wc=0.75, blk='eq', alien=1, women=1, why='1790 election law says "he or she": propertied single women and widows vote')),
  370|            (1808, dict(q='tax', wc=TAXQ, blk='no', why='1807 act: white male citizens who paid a tax')),
  371|            (1844, dict(q='univ', wc=UNIV, blk='no', why='1844 constitution drops taxpaying'))],
  372|     'NY': [(1789, dict(q='prop', wc=0.70, blk='eq', why='1777: £20 freehold or 40s rent (Assembly)')),
  373|            (1824, dict(q='tax', wc=0.90, blk='ny250', why='1821 constitution: whites pay tax or serve in militia/highway; Black men need $250 freehold')),
  374|            (1828, dict(q='univ', wc=UNIV, blk='ny250', why='1826 amendment: white manhood suffrage; $250 rule kept for Black men'))],
  375|     'NC': [(1789, dict(q='tax', wc=0.85, blk='eq', why='1776: Commons franchise = freemen who paid public taxes (Senate needed 50 acres)')),
  376|            (1836, dict(q='tax', wc=0.85, blk='no', why='1835 amendments bar free Black men')),
  377|            (1860, dict(q='tax', wc=TAXQ, blk='no', why='1857 amendment drops the Senate 50-acre rule'))],
  378|     'PA': [(1789, dict(q='tax', wc=TAXQ, blk='eq', why='1776/1790: freemen who paid a state/county tax within 2 years (sons of electors 21-22 exempt)')),
  379|            (1840, dict(q='tax', wc=TAXQ, blk='no', why='1838 constitution adds "white"'))],
  380|     'RI': [(1789, dict(q='prop', wc=0.50, blk='eq', why='freehold $134 (£40) or eldest son of a freeman')),
  381|            (1824, dict(q='prop', wc=0.45, blk='no', why='1822 act bars Black men; freehold rule kept')),
  382|            (1832, dict(q='prop', wc=0.40, blk='no', why='freehold rule binds harder as towns grow (Dorr-era estimates ~40%)')),
  383|            (1844, dict(q='tax', wc=0.80, blk='eq', poll=1, why='1842 constitution: native men pay $1 registry tax; foreign-born need $134 freehold; no colour bar'))],
  384|     'SC': [(1789, dict(q='prop', wc=0.70, blk='no', why='1790: free white men with 50 acres/town lot or paying 3s tax (legislature chose electors)')),
  385|            (1812, dict(q='univ', wc=UNIV, blk='no', why='1810 amendment: white manhood suffrage (legislature still chose electors)'))],
  386|     'VA': [(1789, dict(q='prop', wc=0.55, blk='no', why='50 acres unimproved / 25 improved + house / town lot; free Black men barred since 1723')),
  387|            (1832, dict(q='prop', wc=0.70, blk='no', why='1830 constitution adds leaseholders and taxpaying householders')),
  388|            (1852, dict(q='univ', wc=UNIV, blk='no', why='1851 constitution: white manhood suffrage'))],
  389|     'VT': [(1792, dict(q='univ', wc=UNIV, blk='eq', why='1777/1793: men of "quiet and peaceable behaviour", one year resident'))],
  390|     'KY': [(1792, dict(q='univ', wc=UNIV, blk='eq', why='1792 constitution: free male citizens, no colour bar')),
  391|            (1800, dict(q='univ', wc=UNIV, blk='no', why='1799 constitution: free white men'))],
  392|     'TN': [(1796, dict(q='univ', wc=0.93, blk='eq', why='1796: freeholders or 6-month inhabitants; no colour bar')),
  393|            (1836, dict(q='univ', wc=UNIV, blk='no', why='1834 constitution: free white men'))],
  394|     'OH': [(1804, dict(q='tax', wc=0.90, blk='no', why='1803: white male taxpayers or road workers')),
  395|            (1852, dict(q='univ', wc=UNIV, blk='no', why='1851 constitution: white manhood suffrage'))],
  396|     'LA': [(1812, dict(q='tax', wc=0.70, blk='no', why='1812: white male citizens who bought federal land or paid a state tax')),
  397|            (1848, dict(q='univ', wc=UNIV, blk='no', why='1845 constitution drops taxpaying (2-year residence)'))],
  398|     'IN': [(1816, dict(q='univ', wc=UNIV, blk='no', why='1816: white male citizens')),
  399|            (1852, dict(q='univ', wc=UNIV, blk='no', alien=1, why='1851 constitution: declarant aliens with 1 year residence vote'))],
  400|     'MS': [(1820, dict(q='tax', wc=TAXQ, blk='no', why='1817: white male citizens who paid tax or did militia duty')),
  401|            (1836, dict(q='univ', wc=UNIV, blk='no', why='1832 constitution: white manhood suffrage'))],
  402|     'IL': [(1820, dict(q='univ', wc=UNIV, blk='no', alien=1, why='1818: all white male inhabitants (aliens vote)')),
  403|            (1852, dict(q='univ', wc=UNIV, blk='no', why='1848 constitution: citizens only (aliens resident at adoption grandfathered)'))],
  404|     'AL': [(1820, dict(q='univ', wc=UNIV, blk='no', why='1819: white male citizens'))],
  405|     'ME': [(1820, dict(q='univ', wc=UNIV, blk='eq', why='1819: male citizens, no colour bar (paupers, untaxed Indians excluded)'))],
  406|     'MO': [(1820, dict(q='univ', wc=UNIV, blk='no', why='1820: free white male citizens'))],
  407|     'AR': [(1836, dict(q='univ', wc=UNIV, blk='no', why='1836: free white male citizens'))],
  408|     'MI': [(1836, dict(q='univ', wc=UNIV, blk='no', alien=1, why='1835: white male citizens and white male inhabitants resident at adoption; 1850: declarant aliens'))],
  409|     'FL': [(1848, dict(q='univ', wc=UNIV, blk='no', why='1838/1845: free white male citizens'))],
  410|     'TX': [(1848, dict(q='univ', wc=UNIV, blk='no', why='1845: free male citizens (Africans and untaxed Indians excluded)'))],
  411|     'IA': [(1848, dict(q='univ', wc=UNIV, blk='no', why='1846: white male citizens'))],
  412|     'WI': [(1848, dict(q='univ', wc=UNIV, blk='no', alien=1, why='1848: white male citizens and declarant aliens'))],
  413|     'CA': [(1852, dict(q='univ', wc=UNIV, blk='no', why='1849: white male citizens (incl. Mexican citizens electing US citizenship)'))],
  414|     'MN': [(1860, dict(q='univ', wc=UNIV, blk='no', alien=1, why='1857: white male citizens, declarant aliens, mixed-blood "civilized" men'))],
  415|     'OR': [(1860, dict(q='univ', wc=UNIV, blk='no', alien=1, why='1857: white male citizens and declarant aliens of one year'))],
  416|     'KS': [(1864, dict(q='univ', wc=UNIV, blk='no', alien=1, why='1859 Wyandotte constitution: white male citizens and declarant aliens'))],
  417|     'WV': [(1864, dict(q='univ', wc=UNIV, blk='no', why='1863: white male citizens'))],
  418|     'NV': [(1864, dict(q='univ', wc=UNIV, blk='no', why='1864: white male citizens'))],
  419| }
  420| # Share of free Black men meeting the rule when admitted on equal terms [I]: property and tax
  421| # rules bound much harder on free Black men (Keyssar ch. 3; Litwack, North of Slavery).
  422| BLACK_RATE = {'univ': 0.95, 'tax': 0.6, 'prop': 0.25}
  423| NY250 = 0.08   # [I] NY: ~1,000 of ~13,000 Black men qualified by 1855 (Field 1982; Keyssar ch. 3)
  424| NJ_WOMEN = 0.10  # [I] share of NJ adult women who were unmarried/widowed AND worth £50
  425| FELONY = 0.0005  # [I] "infamous crimes" exclusions; state-prison populations were tiny before 1865
  426| 
  427| 
  428| def franchise() -> pd.DataFrame:
  429|     from build_population_republic import free_share
  430|     ret = pd.read_csv(CACHE / 'labels/state_pres_1789_1864.csv')
  431|     out = []
  432|     for _, r in ret.iterrows():
  433|         y, st = int(r.year), r.state
  434|         rules = [x for x in F.get(st, []) if x[0] <= y]
  435|         if not rules:
  436|             raise SystemExit(f'no franchise rule for {st} {y}')
  437|         rule = rules[-1][1]
  438|         fs = free_share(y).get(st)
  439|         if fs is None:  # state not in the census at or before y (e.g. KY 1792): use the next census
  440|             fs = free_share(y + 10).get(st, 1.0)
  441|         allowed = {'no': 0.0, 'ny250': NY250}.get(rule['blk'], min(BLACK_RATE[rule['q']], rule['wc']))
  442|         notes = [rule['why'], f'qualification={rule["q"]}', f'white_can [I] = {rule["wc"]}',
  443|                  f'black_can [I] = free share of Black men {fs:.3f} × allowed {allowed:.2f} (rule {rule["blk"]}; applies to Black men)']
  444|         if rule.get('women'):
  445|             notes.append(f'women_vote: propertied unmarried women and widows only, ≈{NJ_WOMEN} of adult women [I]')
  446|         if rule.get('alien'):
  447|             notes.append('alien_voting: non-citizen residents/declarant aliens could vote')
  448|         out.append({'year': y, 'state': st, 'poll_tax': int(rule['q'] == 'tax' or bool(rule.get('poll'))),
  449|                     'literacy_test': rule.get('lit', 0), 'alien_voting': rule.get('alien', 0),
  450|                     'women_vote': rule.get('women', 0), 'white_can': rule['wc'], 'black_can': round(fs * allowed, 4),
  451|                     'felony_disenfranchised_share': FELONY, 'voting_age': 21, 'chosen_by': r.chosen_by,
  452|                     'source': 'Keyssar, The Right to Vote (2009) Tables A.1-A.4, A.12 (rules hand-coded from memory of the tables, '
  453|                               'not re-checked page by page); Engerman & Sokoloff (2005); free share from NHGIS adults_<census> (G)',
  454|                     'note': '; '.join(notes) + ('; poll_tax=1 means a taxpaying qualification (any tax, or militia/road-work alternative)'
  455|                                                 if rule['q'] == 'tax' else '')})
  456|     return pd.DataFrame(out)
  457| 
  458| 
  459| COLS = ['year', 'state', 'rep', 'dem', 'other', 'total', 'third', 'ev_rep', 'ev_dem', 'ev_other', 'ev_total',
  460|         'chosen_by', 'source', 'note']
  461| 
  462| 
  463| if __name__ == '__main__':
  464|     what = sys.argv[1] if len(sys.argv) > 1 else 'all'
  465|     if what in ('returns', 'all'):
  466|         df = returns()[COLS]
  467|         out = CACHE / 'labels/state_pres_1789_1864.csv'
  468|         df.to_csv(out, index=False)
  469|         print('wrote', out, len(df))
  470|     if what in ('franchise', 'all'):
  471|         df = franchise()
  472|         out = CACHE / 'franchise/state_franchise_1789_1864.csv'
  473|         df.to_csv(out, index=False)
  474|         print('wrote', out, len(df))
```

## `scripts/harness/build_returns.py`

```python
    1| """Build labels/state_pres_all.csv: certified presidential returns by state, 1868–2024.
    2| 
    3| Columns: year,state,rep,dem,other,total,third,ev_rep,ev_dem,ev_other,ev_total,chosen_by,source,note
    4| 
    5| Slots (orchestrator interface): R = Republican nominee, D = Democratic nominee
    6| (1872: Greeley), O = everyone else; `third` = the named third candidate's own votes
    7| (inside O): 1892 Weaver, 1912 T. Roosevelt, 1924 La Follette, 1948 Thurmond,
    8| 1968 Wallace, 1980 Anderson, 1992/1996 Perot.
    9| 
   10| Sources, in order of preference per state-year:
   11|   1. 1916/1920/1924: the curated labels/state_pres_1916_1920_1924.csv (unchanged).
   12|   2. 2024: FEC, "Official 2024 Presidential General Election Results" (Jan 16 2025),
   13|      labels/raw/fec/2024presgeresults.xlsx (https://www.fec.gov/documents/5645/2024presgeresults.xlsx).
   14|   3. Algara & Amlani county returns summed to the state (doi:10.7910/DVN/DGUMFI),
   15|      when both its D and R shares are within 0.5 points of the Algara–Amlani state
   16|      file (1868_2020_presvote.tab).
   17|   4. Otherwise the Wikipedia "results by state" table for the year
   18|      (labels/raw/wiki/wikipedia_<year>.html; those tables cite Leip / the Clerk / FEC).
   19|   5. Otherwise the state file's percentages applied to the county-sum total [I].
   20| EV: from the Algara–Amlani state file (dev/rev/oev), FEC for 2024.
   21| 
   22| Run: ~/.venvs/simharness/bin/python scripts/harness/build_returns.py
   23| """
   24| from __future__ import annotations
   25| 
   26| import re
   27| import sys
   28| from io import StringIO
   29| from pathlib import Path
   30| 
   31| import numpy as np
   32| import pandas as pd
   33| 
   34| HERE = Path(__file__).resolve().parent
   35| sys.path.insert(0, str(HERE.parents[1]))  # the repo root
   36| from simharness.config import CACHE  # noqa: E402
   37| from simharness.geo import CODE_OF  # noqa: E402
   38| 
   39| RAW = CACHE / 'labels/raw'
   40| OUT = CACHE / 'labels/state_pres_all.csv'
   41| AA_SRC = 'Algara-Amlani county sum (doi:10.7910/DVN/DGUMFI)'
   42| TAB_SRC = 'Algara-Amlani state file 1868_2020_presvote.tab'
   43| 
   44| # The named third candidate per year: a regex on the Wikipedia column header.
   45| THIRD = {1892: r'Weaver', 1912: r'Roosevelt', 1924: r'La Follette', 1948: r'Thurmond',
   46|          1968: r'Wallace', 1980: r'Anderson', 1992: r'Perot', 1996: r'Perot', 2000: r'Nader'}
   47| # Republican and Democratic nominees' surnames (to find their Wikipedia columns).
   48| NOMINEES = {
   49|     1868: ('Grant', 'Seymour'), 1872: ('Grant', 'Greeley'), 1876: ('Hayes', 'Tilden'), 1880: ('Garfield', 'Hancock'),
   50|     1884: ('Blaine', 'Cleveland'), 1888: ('Harrison', 'Cleveland'), 1892: ('Harrison', 'Cleveland'),
   51|     1896: ('McKinley', 'Bryan'), 1900: ('McKinley', 'Bryan'), 1904: ('Roosevelt', 'Parker'), 1908: ('Taft', 'Bryan'),
   52|     1912: ('Taft', 'Wilson'), 1916: ('Hughes', 'Wilson'), 1920: ('Harding', 'Cox'), 1924: ('Coolidge', 'Davis'),
   53|     1928: ('Hoover', 'Smith'), 1932: ('Hoover', 'Roosevelt'), 1936: ('Landon', 'Roosevelt'), 1940: ('Willkie', 'Roosevelt'),
   54|     1944: ('Dewey', 'Roosevelt'), 1948: ('Dewey', 'Truman'), 1952: ('Eisenhower', 'Stevenson'),
   55|     1956: ('Eisenhower', 'Stevenson'), 1960: ('Nixon', 'Kennedy'), 1964: ('Goldwater', 'Johnson'),
   56|     1968: ('Nixon', 'Humphrey'), 1972: ('Nixon', 'McGovern'), 1976: ('Ford', 'Carter'), 1980: ('Reagan', 'Carter'),
   57|     1984: ('Reagan', 'Mondale'), 1988: ('Bush', 'Dukakis'), 1992: ('Bush', 'Clinton'), 1996: ('Dole', 'Clinton'),
   58|     2000: ('Bush', 'Gore'), 2004: ('Bush', 'Kerry'), 2008: ('McCain', 'Obama'), 2012: ('Romney', 'Obama'),
   59|     2016: ('Trump', 'Clinton'), 2020: ('Trump', 'Biden'), 2024: ('Trump', 'Harris'),
   60| }
   61| # Electoral votes counted by Congress (appointed electors; abstentions noted).
   62| KNOWN_EV = {1868: 294, 1872: 352, 1876: 369, 1880: 369, 1884: 401, 1888: 401, 1892: 444, 1896: 447, 1900: 447,
   63|             1904: 476, 1908: 483, 1960: 537}
   64| for _y in range(1912, 1960, 4):
   65|     KNOWN_EV[_y] = 531
   66| for _y in range(1964, 2025, 4):
   67|     KNOWN_EV[_y] = 538
   68| # Electoral votes as cast where the state file differs (faithless electors,
   69| # unpledged electors, splits): (ev_rep, ev_dem, ev_other). Sources: NARA
   70| # Electoral College results; Congressional Quarterly's Guide to U.S. Elections.
   71| EV_FIX = {
   72|     (1948, 'TN'): (0, 11, 1), (1956, 'AL'): (0, 10, 1),
   73|     (1960, 'AL'): (0, 5, 6), (1960, 'MS'): (0, 0, 8), (1960, 'OK'): (7, 0, 1),
   74|     (1968, 'NC'): (12, 0, 1), (1972, 'VA'): (11, 0, 1), (1976, 'WA'): (8, 0, 1),
   75|     (1988, 'WV'): (0, 5, 1), (2000, 'DC'): (0, 2, 1), (2004, 'MN'): (0, 9, 1),
   76|     (2016, 'TX'): (36, 0, 2), (2016, 'WA'): (0, 8, 4), (2016, 'HI'): (0, 3, 1),
   77|     (2020, 'NE'): (4, 1, 0),
   78| }
   79| # Legislature-chosen electors (no popular vote) and states with no electors.
   80| LEGISLATURE = {(1868, 'FL'), (1876, 'CO')}
   81| NOTES = {
   82|     (1868, 'FL'): 'electors chosen by the legislature',
   83|     (1876, 'CO'): 'electors chosen by the legislature (admitted Aug 1876)',
   84|     (1872, 'AR'): 'electoral votes rejected by Congress',
   85|     (1872, 'LA'): 'electoral votes rejected by Congress',
   86|     (1872, 'GA'): "D = Greeley's electors; 3 votes cast for the dead Greeley rejected by Congress, kept in ev_dem",
   87|     (1960, 'AL'): '6 of 11 electors unpledged (voted Byrd): ev_other; Kennedy vote = highest loyal elector (Wikipedia)',
   88|     (1960, 'MS'): 'unpledged Democratic electors won (voted Byrd): ev_other',
   89|     (1960, 'OK'): 'faithless elector (Byrd)',
   90|     (1948, 'TN'): 'faithless elector (Thurmond)',
   91|     (1956, 'AL'): 'faithless elector (W. B. Jones)',
   92|     (1968, 'NC'): 'faithless elector (Wallace)',
   93|     (1972, 'VA'): 'faithless elector (Hospers)',
   94|     (1976, 'WA'): 'faithless elector (Reagan)',
   95|     (1988, 'WV'): 'faithless elector (Bentsen)',
   96|     (2000, 'DC'): 'one elector abstained (counted in ev_other)',
   97|     (2020, 'NE'): 'district method: 4 R, 1 D',
   98|     (2016, 'ME'): 'district method: 3 D, 1 R',
   99|     (2008, 'NE'): 'district method: 4 R, 1 D',
  100|     (2004, 'MN'): 'faithless elector (Edwards)',
  101|     (2016, 'TX'): '2 faithless electors',
  102|     (2016, 'WA'): '4 faithless electors',
  103|     (2016, 'HI'): '1 faithless elector',
  104|     (1948, 'AL'): 'Truman not on the ballot; Thurmond held the Democratic line (in O / third)',
  105|     (1964, 'AL'): 'Johnson not on the ballot; unpledged Democratic electors in O',
  106|     (1912, 'CA'): 'split: 11 T. Roosevelt, 2 Wilson',
  107|     (1892, 'MI'): 'district method',
  108| }
  109| 
  110| 
  111| def _num(x):
  112|     x = re.sub(r'\[.*?\]', '', str(x)).replace(',', '').replace('−', '-').replace('–', '-').strip()
  113|     if x in ('-', '', 'nan', 'None') or not re.match(r'^-?\d+(\.\d+)?$', x):
  114|         return np.nan
  115|     return float(x)
  116| 
  117| 
  118| def _state_code(name: str):
  119|     n = re.sub(r'\[.*?\]|[†‡*§#^]|\(.*?\)', '', str(name)).strip()
  120|     n = n.replace('D.C.', 'District of Columbia')
  121|     if n in CODE_OF:
  122|         return CODE_OF[n]
  123|     if n in ('Washington DC', 'Washington, District of Columbia', 'District of Columbia'):
  124|         return 'DC'
  125|     return None
  126| 
  127| 
  128| def wiki(year: int) -> pd.DataFrame:
  129|     """Per-state R, D, total and the named third's votes from the Wikipedia table."""
  130|     f = RAW / f'wiki/wikipedia_{year}.html'
  131|     if not f.exists():
  132|         return pd.DataFrame()
  133|     h = re.sub(r'(rowspan|colspan)="[^"0-9]*"', '', f.read_text())
  134|     best = None
  135|     for t in pd.read_html(StringIO(h)):
  136|         if not isinstance(t.columns, pd.MultiIndex) or not 30 <= len(t) <= 75:
  137|             continue
  138|         sub = [str(c[-1]).strip() for c in t.columns]
  139|         if not any(s in ('#', 'Votes', 'Vote') for s in sub):
  140|             continue
  141|         heads = ' '.join(str(c[-2]) for c in t.columns)
  142|         r, d = NOMINEES[year]
  143|         if r in heads and d in heads and ('Total' in heads or 'total' in heads or 'Margin' in heads):
  144|             best = t
  145|             break
  146|     if best is None:
  147|         return pd.DataFrame()
  148|     t = best
  149|     cols = list(t.columns)
  150|     r, d = NOMINEES[year]
  151| 
  152|     def votes_col(pat, exclude=()):
  153|         for c in cols:
  154|             head, sub = str(c[-2]), str(c[-1]).strip()
  155|             if sub in ('#', 'Votes', 'Vote') and re.search(pat, head) and not any(e in head for e in exclude):
  156|                 return c
  157|         return None
  158|     rc = votes_col(r, exclude=('Unpledged',))
  159|     dc = votes_col(d, exclude=('Unpledged',))
  160|     if year == 1912:
  161|         rc = votes_col('Taft')
  162|         dc = votes_col('Wilson')
  163|     tc = votes_col(r'[Tt]otal')
  164|     if tc is None:
  165|         tcs = [c for c in cols if re.search(r'[Tt]otal', str(c[-2])) and str(c[-1]).strip() not in ('%',)]
  166|         tc = tcs[0] if tcs else None
  167|     thc = votes_col(THIRD[year]) if year in THIRD else None
  168|     if year == 1904:  # Roosevelt is R in 1904, not a third
  169|         thc = None
  170|     rows = []
  171|     for _, row in t.iterrows():
  172|         vals = list(row.values)
  173|         code = None
  174|         for v in vals[:3]:
  175|             code = _state_code(v)
  176|             if code:
  177|                 break
  178|         if code is None:
  179|             continue
  180|         rows.append({'state': code, 'wp_rep': _num(row[rc]) if rc is not None else np.nan,
  181|                      'wp_dem': _num(row[dc]) if dc is not None else np.nan,
  182|                      'wp_total': _num(row[tc]) if tc is not None else np.nan,
  183|                      'wp_third': _num(row[thc]) if thc is not None else np.nan})
  184|     w = pd.DataFrame(rows)
  185|     if w.empty:
  186|         return w
  187|     # The first row per state is the statewide row (district rows don't map to a name).
  188|     w = w.drop_duplicates('state', keep='first')
  189|     w['year'] = year
  190|     return w
  191| 
  192| 
  193| def county_sums() -> pd.DataFrame:
  194|     import pyreadr
  195|     d = pyreadr.read_r(str(RAW / 'dataverse_shareable_presidential_county_returns_1868_2020.Rdata'))['pres_elections_release']
  196|     d['year'] = d.election_year.astype(int)
  197|     g = d.groupby(['year', 'state']).agg(aa_dem=('democratic_raw_votes', 'sum'), aa_rep=('republican_raw_votes', 'sum'),
  198|                                          aa_total=('raw_county_vote_totals', 'sum'),
  199|                                          aa_nmiss=('raw_county_vote_totals', lambda s: int(s.isna().sum()))).reset_index()
  200|     return g
  201| 
  202| 
  203| def fec2024() -> pd.DataFrame:
  204|     x = pd.read_excel(RAW / 'fec/2024presgeresults.xlsx', header=0)
  205|     x = x[x.STATE.astype(str).str.fullmatch(r'[A-Z]{2}')]
  206|     rows = []
  207|     for _, r in x.iterrows():
  208|         rep, dem, tot = float(r['TRUMP']), float(r['HARRIS']), float(r['TOTAL VOTES'])
  209|         evr = 0 if pd.isna(r['ELECTORAL VOTE: TRUMP (R)']) else int(r['ELECTORAL VOTE: TRUMP (R)'])
  210|         evd = 0 if pd.isna(r['ELECTORAL VOTE: HARRIS (D)']) else int(r['ELECTORAL VOTE: HARRIS (D)'])
  211|         rows.append({'year': 2024, 'state': r.STATE, 'rep': rep, 'dem': dem, 'total': tot, 'third': np.nan,
  212|                      'ev_rep': evr, 'ev_dem': evd, 'ev_other': int(r['ELECTORAL VOTES']) - evr - evd,
  213|                      'ev_total': int(r['ELECTORAL VOTES']), 'chosen_by': 'popular',
  214|                      'source': 'FEC Official 2024 Presidential General Election Results (2025-01-16), 2024presgeresults.xlsx',
  215|                      'note': {'NE': 'district method: 4 R, 1 D', 'ME': 'district method: 3 D, 1 R'}.get(r.STATE, '')})
  216|     return pd.DataFrame(rows)
  217| 
  218| 
  219| def legacy_1916_1924() -> pd.DataFrame:
  220|     d = pd.read_csv(CACHE / 'labels/state_pres_1916_1920_1924.csv')
  221|     rows = []
  222|     for _, x in d.iterrows():
  223|         evd, evr, evo = int(x.aa_state_ev_dem), int(x.aa_state_ev_rep), int(x.aa_state_ev_other)
  224|         rows.append({'year': int(x.year), 'state': x.state, 'rep': x.rep, 'dem': x.dem, 'total': x.total,
  225|                      'third': (x.wp_progressive if x.year == 1924 else np.nan),
  226|                      'ev_rep': evr, 'ev_dem': evd, 'ev_other': evo,
  227|                      'ev_total': int(x.nara_ev_total) if x.year == 1920 and pd.notna(x.nara_ev_total) else evr + evd + evo,
  228|                      'chosen_by': 'popular', 'source': f'labels/state_pres_1916_1920_1924.csv ({x.value_source})',
  229|                      'note': '' if pd.isna(x.note) else str(x.note)})
  230|     return pd.DataFrame(rows)
  231| 
  232| 
  233| def main():
  234|     tab = pd.read_csv(RAW / '1868_2020_presvote.tab', sep='\t')
  235|     tab = tab[tab.state != 'US']
  236|     aa = county_sums()
  237|     w = pd.concat([wiki(y) for y in range(1868, 2025, 4)], ignore_index=True)
  238|     m = tab.merge(aa, on=['year', 'state'], how='left').merge(w, on=['year', 'state'], how='left')
  239|     rows, report = [], []
  240|     for _, x in m.iterrows():
  241|         y, s = int(x.year), x.state
  242|         if y in (1916, 1920, 1924):
  243|             continue
  244|         has_ev = pd.notna(x.totev) and x.totev > 0
  245|         has_vote = pd.notna(x.dvote) or pd.notna(x.rvote)
  246|         if not has_ev and not has_vote:
  247|             if (y, s) in {(1868, 'TX'), (1868, 'MS'), (1868, 'VA')}:
  248|                 rows.append({'year': y, 'state': s, 'rep': 0, 'dem': 0, 'total': 0, 'third': np.nan, 'ev_rep': 0,
  249|                              'ev_dem': 0, 'ev_other': 0, 'ev_total': 0, 'chosen_by': 'none', 'source': TAB_SRC,
  250|                              'note': 'not yet readmitted: no electors'})
  251|             continue
  252|         ev = dict(ev_rep=int(x.rev) if pd.notna(x.rev) else 0, ev_dem=int(x.dev) if pd.notna(x.dev) else 0,
  253|                   ev_other=int(x.oev) if pd.notna(x.oev) else 0)
  254|         if (y, s) in EV_FIX:
  255|             ev = dict(zip(('ev_rep', 'ev_dem', 'ev_other'), EV_FIX[(y, s)]))
  256|         ev['ev_total'] = ev['ev_rep'] + ev['ev_dem'] + ev['ev_other']
  257|         note = NOTES.get((y, s), '')
  258|         if (y, s) in LEGISLATURE or not has_vote:
  259|             rows.append({'year': y, 'state': s, 'rep': 0, 'dem': 0, 'total': 0, 'third': np.nan, **ev,
  260|                          'chosen_by': 'legislature', 'source': TAB_SRC, 'note': note})
  261|             continue
  262|         dp, rp = (x.dvote if pd.notna(x.dvote) else 0.0), (x.rvote if pd.notna(x.rvote) else 0.0)
  263|         ok_aa = pd.notna(x.aa_total) and x.aa_total > 0 and x.aa_nmiss == 0 and \
  264|             abs(100 * x.aa_dem / x.aa_total - dp) <= 0.5 and abs(100 * x.aa_rep / x.aa_total - rp) <= 0.5
  265|         ok_w = pd.notna(x.wp_total) and x.wp_total > 0 and pd.notna(x.wp_rep) and \
  266|             abs(100 * x.wp_rep / x.wp_total - rp) <= 1.5 and abs(100 * np.nan_to_num(x.wp_dem) / x.wp_total - dp) <= 1.5
  267|         if pd.notna(x.aa_total) and x.aa_total > 0:
  268|             off = max(abs(100 * x.aa_dem / x.aa_total - dp), abs(100 * x.aa_rep / x.aa_total - rp))
  269|         else:
  270|             off = np.nan
  271|         if ok_aa:
  272|             rep, dem, tot, src = x.aa_rep, x.aa_dem, x.aa_total, AA_SRC
  273|         elif ok_w:
  274|             rep, dem, tot, src = x.wp_rep, np.nan_to_num(x.wp_dem), x.wp_total, f'Wikipedia {y} results by state (labels/raw/wiki)'
  275|         elif pd.notna(x.wp_total) and x.wp_total > 0:
  276|             rep, dem, tot = x.wp_rep, np.nan_to_num(x.wp_dem), x.wp_total
  277|             src = f'Wikipedia {y} results by state (labels/raw/wiki); differs from {TAB_SRC} by >1.5pt'
  278|         elif pd.notna(x.aa_total) and x.aa_total > 0:
  279|             tot = x.aa_total
  280|             rep, dem = round(tot * rp / 100), round(tot * dp / 100)
  281|             src = f'[I] {TAB_SRC} percentages x county-sum total'
  282|         else:
  283|             raise SystemExit(f'no counts for {y} {s}')
  284|         if not ok_aa:
  285|             report.append({'year': y, 'state': s, 'aa_off_pp': None if pd.isna(off) else round(off, 2), 'used': src[:40]})
  286|         third = np.nan
  287|         if y in THIRD:  # a blank cell in the named third's column: not on that state's ballot
  288|             third = 0.0 if pd.isna(x.wp_third) else x.wp_third
  289|         tot = max(tot, rep + dem)  # 1868 MO: county total 9 short of R + D
  290|         rows.append({'year': y, 'state': s, 'rep': rep, 'dem': dem, 'total': tot, 'third': third, **ev,
  291|                      'chosen_by': 'popular', 'source': src, 'note': note})
  292|     out = pd.concat([pd.DataFrame(rows), legacy_1916_1924(), fec2024()], ignore_index=True)
  293|     for c in ('rep', 'dem', 'total'):
  294|         out[c] = out[c].astype(float).round().astype('Int64')
  295|     out['third'] = out.third.astype(float).round().astype('Int64')
  296|     out['other'] = (out.total - out.rep - out.dem).astype('Int64')
  297|     out = out[['year', 'state', 'rep', 'dem', 'other', 'total', 'third', 'ev_rep', 'ev_dem', 'ev_other', 'ev_total',
  298|                'chosen_by', 'source', 'note']].sort_values(['year', 'state']).reset_index(drop=True)
  299|     out.to_csv(OUT, index=False)
  300|     print(f'wrote {OUT} ({len(out)} rows)')
  301| 
  302|     # Checks.
  303|     ev = out.groupby('year').ev_total.sum()
  304|     bad = {y: (int(ev[y]), KNOWN_EV[y]) for y in KNOWN_EV if int(ev.get(y, 0)) != KNOWN_EV[y]}
  305|     print('EV totals off the known count:', bad or 'none')
  306|     print('national EV by slot:')
  307|     print(out.groupby('year')[['ev_rep', 'ev_dem', 'ev_other', 'ev_total']].sum().T.to_string())
  308|     neg = out[out.other < 0]
  309|     print('negative other:', neg[['year', 'state', 'rep', 'dem', 'total']].to_string() if len(neg) else 'none')
  310|     r = pd.DataFrame(report)
  311|     print(f'state-years where the county sum is >0.5pt off the state file: {len(r)}')
  312|     if len(r):
  313|         print(r.to_string())
  314|     miss3 = out[out.year.isin(THIRD) & out.third.isna() & (out.chosen_by == 'popular')]
  315|     print('named-third missing (state-years):', miss3[['year', 'state']].values.tolist())
  316|     nat = out.groupby('year')[['rep', 'dem', 'other', 'total', 'third']].sum()
  317|     print(nat.to_string())
  318| 
  319| 
  320| if __name__ == '__main__':
  321|     main()
```

## `scripts/harness/bundle_fixture.py`

```python
    1| """Trim a published bundle into the shared contract example.
    2| 
    3|     python3 scripts/harness/bundle_fixture.py            # serve/bundles/1920.json → tests/fixtures/bundle.example.json
    4| 
    5| The Python (serialize.Bundle) and TypeScript (zod) sides both test against the
    6| output, so it keeps every key a real bundle has and only cuts the volume: four
    7| states, three what-if combinations plus history, two voters per combination,
    8| two interviews, two newspaper items and one finding per evidence entry.
    9| """
   10| import json
   11| import sys
   12| from pathlib import Path
   13| 
   14| ROOT = Path(__file__).resolve().parents[2]
   15| SRC = ROOT / 'serve/bundles/1920.json'
   16| OUT = ROOT / 'tests/fixtures/bundle.example.json'
   17| STATES = ['GA', 'NY', 'OH', 'TN']
   18| KEEP = ['league', 'no-19th']
   19| COMBOS = ['', 'league', 'no-19th', 'league+no-19th']
   20| 
   21| 
   22| def trim_evidence(items: list) -> list:
   23|     return [e | {'findings': e['findings'][:1]} for e in items]
   24| 
   25| 
   26| def trim_result(r: dict) -> dict:
   27|     return r | {'states': [s for s in r['states'] if s['code'] in STATES],
   28|                 'sources': r['sources'][:3], 'evidence': trim_evidence(r['evidence']),
   29|                 'cohortEffects': r['cohortEffects'][:2]}
   30| 
   31| 
   32| def main() -> None:
   33|     b = json.loads(SRC.read_text())
   34|     out = {
   35|         'year': b['year'],
   36|         'runId': b['runId'],
   37|         'election': {'slices': b['election']['slices'],
   38|                      'whatIfs': [w for w in b['election']['whatIfs'] if w['key'] in KEEP]},
   39|         'runs': {k: trim_result(b['runs'][k]) for k in COMBOS},
   40|         'tables': {k: [r for r in b['tables'][k] if r['state'] in STATES] for k in COMBOS},
   41|         'voters': {k: dict(list(b['voters'][k].items())[:2]) for k in ['', *KEEP] if k in b['voters']},
   42|         'interviews': {'questions': b['interviews']['questions'],
   43|                        'byWhatIf': {k: v[:2] for k, v in b['interviews']['byWhatIf'].items() if k in KEEP}},
   44|         'ev': {s: b['ev'][s] for s in STATES},
   45|         'historyWinner': {s: b['historyWinner'][s] for s in STATES},
   46|         'words': [w for w in b['words'] if w['key'] in KEEP],
   47|         'pre': b['pre'],
   48|         'told': {k: v for k, v in b['told'].items() if k in KEEP},
   49|         'reading': b['reading'][:2],
   50|     }
   51|     OUT.parent.mkdir(parents=True, exist_ok=True)
   52|     OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
   53|     print(f'{OUT.relative_to(ROOT)}: {OUT.stat().st_size} bytes', file=sys.stderr)
   54| 
   55| 
   56| if __name__ == '__main__':
   57|     main()
```

## `scripts/harness/nhgis_common.py`

```python
    1| """NHGIS, shared by the harness scripts.
    2| 
    3| The extract client (IPUMS API v2) behind nhgis_extract*.py: submit an NHGIS
    4| state-level extract, poll it, then download and unzip it into the cache. The key
    5| is read from ~/.config/simulacra/nhgis.env (IPUMS_API_KEY=…) and is never
    6| printed. Everything lands under $SIMHARNESS_CACHE/population/nhgis/: the request
    7| JSON beside the extracts, the files plus PROVENANCE-nhgis.md in extract_<N>/.
    8| NHGIS terms forbid redistributing an extract, so none of it enters the repo.
    9| 
   10| What the build_population* scripts share: the long output format (the columns
   11| of adults_1920_by_state.csv), state-table loading, gap checks and the comparison
   12| against a hand-keyed census table.
   13| 
   14| Importing it puts the repo root on sys.path, so `simharness` imports work when a
   15| script is run directly.
   16| """
   17| import argparse
   18| import io
   19| import json
   20| import sys
   21| import time
   22| import urllib.error
   23| import urllib.request
   24| import zipfile
   25| from pathlib import Path
   26| 
   27| import pandas as pd
   28| 
   29| sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
   30| from simharness.config import CACHE  # noqa: E402
   31| from simharness.geo import CODE_OF  # noqa: E402
   32| 
   33| NHGIS_DIR = CACHE / 'population/nhgis'
   34| 
   35| # ---------------------------------------------------------------- extract client
   36| API = 'https://api.ipums.org'
   37| CITATION = ('Citation: Manson, S., Schroeder, J., Van Riper, D., Knowles, K., Kugler, T., Roberts, F., and Ruggles, S. '
   38|             'IPUMS National Historical Geographic Information System, https://www.nhgis.org (see nhgis.org/citation for '
   39|             'the current version DOI).')
   40| TERMS = 'Terms: not for redistribution; stays in the harness cache, outside the repo.'
   41| 
   42| 
   43| def key() -> str:
   44|     for line in (Path.home() / '.config/simulacra/nhgis.env').read_text().splitlines():
   45|         if line.startswith('IPUMS_API_KEY='):
   46|             return line.split('=', 1)[1].strip()
   47|     raise SystemExit('no IPUMS_API_KEY in ~/.config/simulacra/nhgis.env')
   48| 
   49| 
   50| def call(path, body=None, raw=False):
   51|     """GET (or POST `body` as JSON) an API path or a full URL; JSON back unless raw."""
   52|     req = urllib.request.Request(path if path.startswith('http') else API + path,
   53|                                  headers={'Authorization': key(), 'Content-Type': 'application/json'},
   54|                                  data=json.dumps(body).encode() if body is not None else None,
   55|                                  method='POST' if body is not None else 'GET')
   56|     try:
   57|         with urllib.request.urlopen(req) as r:
   58|             data = r.read()
   59|     except urllib.error.HTTPError as e:
   60|         raise SystemExit(f'HTTP {e.code}: {e.read().decode()[:800]}')
   61|     return data if raw else json.loads(data)
   62| 
   63| 
   64| def request(datasets: dict, description: str) -> dict:
   65|     """datasets: {name: [table, ...] or (tables, breakdown values or None)} → an extract request, state level."""
   66|     ds = {}
   67|     for name, spec in datasets.items():
   68|         tables, breakdown = spec if isinstance(spec, tuple) else (spec, None)
   69|         ds[name] = {'dataTables': tables, 'geogLevels': ['state']}
   70|         if breakdown:
   71|             ds[name]['breakdownValues'] = breakdown
   72|     return {'datasets': ds, 'dataFormat': 'csv_header', 'breakdownAndDataTypeLayout': 'single_file',
   73|             'description': description}
   74| 
   75| 
   76| def status(n: int) -> dict:
   77|     return call(f'/extracts/{n}?collection=nhgis&version=2')
   78| 
   79| 
   80| class Extract:
   81|     """One extract definition. request_name is the request file's name under NHGIS_DIR, with {n} for the
   82|     extract number (build_population_modern.py finds its extract by that name)."""
   83| 
   84|     def __init__(self, body: dict, request_name: str, title: str, script: str):
   85|         self.body, self.request_name, self.title, self.script = body, request_name, title, script
   86| 
   87|     def submit(self) -> int:
   88|         r = call('/extracts?collection=nhgis&version=2', self.body)
   89|         n = r['number']
   90|         NHGIS_DIR.mkdir(parents=True, exist_ok=True)
   91|         (NHGIS_DIR / self.request_name.format(n=n)).write_text(json.dumps({'number': n, 'request': self.body}, indent=1))
   92|         return n
   93| 
   94|     def download(self, n: int, st: dict) -> list:
   95|         data = call(st['downloadLinks']['tableData']['url'], raw=True)
   96|         d = NHGIS_DIR / f'extract_{n}'
   97|         d.mkdir(parents=True, exist_ok=True)
   98|         with zipfile.ZipFile(io.BytesIO(data)) as z:
   99|             names = z.namelist()
  100|             z.extractall(d)
  101|         (d / 'PROVENANCE-nhgis.md').write_text(
  102|             f'# NHGIS extract {n} ({self.title})\n\nRequested and downloaded {time.strftime("%Y-%m-%d %H:%M")} via the '
  103|             f'IPUMS API v2 (scripts/harness/{self.script}). Tables: see ../{self.request_name.format(n=n)}. '
  104|             f'Files: {len(names)}.\n\n{CITATION}\n\n{TERMS}\n')
  105|         return names
  106| 
  107|     def cli(self):
  108|         ap = argparse.ArgumentParser(description=f'NHGIS extract: {self.title}. submit prints the extract number; '
  109|                                                  'wait N polls every 30 s, then downloads into the cache.')
  110|         ap.add_argument('cmd', nargs='?', default='submit', choices=['submit', 'status', 'wait'])
  111|         ap.add_argument('n', nargs='?', type=int, help='extract number (status, wait)')
  112|         a = ap.parse_args()
  113|         if a.cmd == 'submit':
  114|             print('extract', self.submit())
  115|             return
  116|         if a.n is None:
  117|             ap.error(f'{a.cmd} needs the extract number')
  118|         if a.cmd == 'status':
  119|             st = status(a.n)
  120|             print(st['status'], st.get('errors'))
  121|             return
  122|         while True:
  123|             st = status(a.n)
  124|             print(time.strftime('%H:%M:%S'), st['status'], flush=True)
  125|             if st['status'] == 'completed':
  126|                 print('files', self.download(a.n, st))
  127|                 return
  128|             if st['status'] in ('failed', 'canceled'):
  129|                 raise SystemExit(f'extract {a.n} {st["status"]}: {st.get("errors")}')
  130|             time.sleep(30)
  131| 
  132| 
  133| # ---------------------------------------------------------------- population tables
  134| SRC = NHGIS_DIR / 'extract_1/nhgis0001_csv'  # 1870–1970 state tables (nhgis_extract.py)
  135| COLS = ['year', 'state', 'sex', 'group', 'race_as_recorded', 'label_as_recorded', 'count', 'vintage_mode', 'note',
  136|         'source_table', 'source_url', 'page']
  137| NHGIS_URL = 'https://www.nhgis.org'
  138| STATE_CODE = {k.casefold(): v for k, v in CODE_OF.items()}  # NHGIS writes "District Of Columbia"
  139| 
  140| 
  141| def load(ds: str, src: Path = SRC, pattern: str = 'nhgis0001_{ds}_*_state.csv') -> pd.DataFrame:
  142|     """One NHGIS state table, unfiltered. Row 2 repeats the headers as descriptions and is skipped."""
  143|     return pd.read_csv(next(src.glob(pattern.format(ds=ds))), encoding='latin-1', skiprows=[1])
  144| 
  145| 
  146| def row(year, state, sex, group, race, label, count, note, table) -> dict:
  147|     return {'year': year, 'state': state, 'sex': sex, 'group': group, 'race_as_recorded': race,
  148|             'label_as_recorded': label, 'count': count, 'vintage_mode': 'truth', 'note': note,
  149|             'source_table': table, 'source_url': NHGIS_URL, 'page': ''}
  150| 
  151| 
  152| def frame(rows: list) -> pd.DataFrame:
  153|     """Rows in output order: by state, sex, group."""
  154|     return pd.DataFrame(rows, columns=COLS).sort_values(['state', 'sex', 'group'], kind='stable').reset_index(drop=True)
  155| 
  156| 
  157| def rows(year, d, spec, table, note='tabulated') -> list:
  158|     """spec: [(column, sex, group, label)] → one row per state of d and spec entry, unrounded."""
  159|     return [row(year, st, sex, group, label.split(':')[0], label, float(r[col]), note, table)
  160|             for st, r in d.iterrows() for col, sex, group, label in spec]
  161| 
  162| 
  163| def assert_close(a, b, what, tol=1.0):
  164|     gap = (pd.Series(a) - pd.Series(b)).abs().dropna()
  165|     assert gap.max() < tol, f'{what}: off by {gap.max()} ({gap.idxmax()})'
  166| 
  167| 
  168| def hand_vs_nhgis(hand: pd.DataFrame, nh: pd.DataFrame) -> pd.DataFrame:
  169|     """Counts by (state, sex, harness group) side by side; NaN where only one side has the cell."""
  170|     from simharness.data import GROUP_MAP
  171| 
  172|     def agg(x):
  173|         return x.assign(g=x.group.map(lambda g: GROUP_MAP.get(g, g))).groupby(['state', 'sex', 'g'])['count'].sum()
  174|     return pd.concat([agg(hand[hand.group != 'TOTAL']).rename('hand'), agg(nh).rename('nhgis')], axis=1)
  175| 
  176| 
  177| def off_cells(j: pd.DataFrame) -> pd.DataFrame:
  178|     """Adds diff and rel to a filled hand_vs_nhgis frame; returns the cells off by >50 and >0.5%."""
  179|     j['diff'] = j.nhgis - j.hand
  180|     j['rel'] = j['diff'] / j.hand.clip(lower=1)
  181|     return j[(j['diff'].abs() > 50) & (j.rel.abs() > 0.005)]
  182| 
  183| 
  184| def print_worst(bad: pd.DataFrame):
  185|     if len(bad):
  186|         print(bad.sort_values('diff', key=abs, ascending=False).head(15).to_string())
```

## `scripts/harness/nhgis_extract.py`

```python
    1| """Submit, wait for and download the NHGIS state-level population extract
    2| behind every census year from 1870 to 1970 (and 1920 again, as a check on the
    3| harness's own 1920 table).
    4| 
    5|     python3 scripts/harness/nhgis_extract.py submit     # prints the extract number
    6|     python3 scripts/harness/nhgis_extract.py wait N     # polls, then downloads into the cache
    7|     python3 scripts/harness/nhgis_extract.py status N
    8| 
    9| Key handling, cache layout and terms: nhgis_common.py (cite doi:10.18128/D050.V19.0 /
   10| the NHGIS citation page).
   11| """
   12| from nhgis_common import Extract, request
   13| 
   14| # Per census: adults 21+ (men only before 1920: women weren't tabulated by
   15| # voting age) by race / nativity, citizenship of the foreign born, and the
   16| # population by sex × race / nativity to estimate women 21+ where needed.
   17| TABLES = {
   18|     '1870_sPHX': ['NT1', 'NT45', 'NT46', 'NT47', 'NT48'],   # males 21+ by nativity, by race; male citizens 21+
   19|     '1870_sRN': ['NT1', 'NT4'],                             # race by nativity
   20|     '1880_sPHX': ['NT1', 'NT7'],                            # race/nativity by sex; males 21+ by race/nativity
   21|     '1890_cPHAM': ['NT5', 'NT6', 'NT9', 'NT14'],            # nativity by sex, race/nativity by sex; males 21+ by race/nativity
   22|     '1900_cPHAM': ['NT4', 'NT6', 'NT7', 'NT9', 'NT10', 'NT11', 'NT62'],  # + native males 21+ by race; FB males 21+ by citizenship
   23|     '1910_cPHA': ['NT8', 'NT10', 'NT11', 'NT12', 'NT13', 'NT17'],         # males of voting age by race/nativity; FB white by citizenship
   24|     '1920_cPHAM': ['NT12', 'NT13', 'NT15'],                 # check against harness_cache/population/adults_1920_by_state.csv
   25|     '1930_cPAE': ['NT9', 'NT10', 'NT12'],                   # 21+ by race/nativity by sex; FB white 21+ by sex by citizenship
   26|     '1930_cAge30': ['NT7', 'NT10'],
   27|     '1940_cPHAE': ['NT8', 'NT9', 'NT10', 'NT12'],
   28|     '1940_cAge': ['NT7', 'NT10'],                           # 21+ by race by sex; white 21+ by nativity by sex
   29|     '1950_cPHA': ['NT8', 'NT9A', 'NT9B', 'NT48'],
   30|     '1950_cAge': ['NT6', 'NT18'],                           # race by sex by age
   31|     '1960_cAge1': ['NT5', 'NT11'],                          # sex by age; race by sex by age
   32|     '1960_cPop': ['NT14'],
   33|     '1970_Cnt1': ['NT18', 'NT19'],                          # sex by age; race by sex by age (non-white)
   34| }
   35| 
   36| EXTRACT = Extract(request(TABLES, 'Simulacra harness: state adults 21+ by sex x race/nativity x citizenship, 1870-1970'),
   37|                   'extract_request.json', '1870-1970 state tables', 'nhgis_extract.py')
   38| 
   39| if __name__ == '__main__':
   40|     EXTRACT.cli()
```

## `scripts/harness/nhgis_extract_modern.py`

```python
    1| """Submit, wait for and download the NHGIS state-level extract behind the
    2| 1980-2024 adult (18+) population tables: nativity x citizenship x sex x race
    3| (white non-Hispanic, Black) from the decennial sample files and the ACS
    4| B05003 family, plus 100%-count / PL 94-171 18+ totals as independent checks.
    5| 
    6|     python3 scripts/harness/nhgis_extract_modern.py submit     # prints the extract number
    7|     python3 scripts/harness/nhgis_extract_modern.py wait N     # polls, then downloads into the cache
    8|     python3 scripts/harness/nhgis_extract_modern.py status N
    9| 
   10| Key handling, cache layout and terms: nhgis_common.py.
   11| """
   12| from nhgis_common import Extract, request
   13| 
   14| ACS_TABLES = ['B01001', 'B03002', 'B05003', 'B05003B', 'B05003H']
   15| 
   16| # dataset -> (tables, breakdown values or None)
   17| DATASETS = {
   18|     # 1980: 100% sex by age (total; white / Black not of Spanish origin); sample nativity x
   19|     # citizenship by race (all ages); Spanish origin by race; sample sex by age (check).
   20|     '1980_STF1': (['NT10B'], None),
   21|     '1980_STF2a': (['NTA13'], None),
   22|     '1980_STF2b': (['NTB8B'], ['bs03.ge0000', 'bs04.ch00', 'bs04.ch24', 'bs04.ch25']),
   23|     '1980_STF3': (['NT15B'], None),
   24|     '1980_STF4Pb': (['NTPB9'], ['bs03.ge0000', 'bs04.ch00', 'bs04.ch01', 'bs04.ch02', 'bs04.ch19']),
   25|     # 1990: 100% sex by age; MARS age x Hispanic x sex x race; sample age x citizenship;
   26|     # sample nativity/citizenship by race (all ages).
   27|     '1990_STF1': (['NP13'], None),
   28|     '1990_MARS': (['NP1'], None),
   29|     '1990_STF3': (['NP37'], None),
   30|     '1990_STF4b': (['NPB20'], ['bs09.ge00', 'bs10.ch000', 'bs10.ch120', 'bs10.ch121']),
   31|     # 2000: SF4 sex x age(18) x nativity and x citizenship, iterated total / WNH / BNH;
   32|     # SF1 18+ total and 18+ NH by race (independent).
   33|     '2000_SF1a': (['NP005A', 'NP006C'], None),
   34|     '2000_SF4': (['NPCT044B', 'NPCT044C'], ['bs21.ge00', 'bs22.ch001', 'bs22.ch451', 'bs22.ch453']),
   35|     # ACS (2008 = 2006-2010 5-year; 2020 = 2016-2020 5-year; 1-year otherwise) + PL 18+ checks.
   36|     '2006_2010_ACS5a': (['B01001', 'B03002'], None),
   37|     '2006_2010_ACS5b': (['B05003', 'B05003B', 'B05003H'], None),
   38|     '2010_ACS1': (ACS_TABLES, None),
   39|     '2010_PL94171': (['NP003', 'NP004'], None),
   40|     '2012_ACS1': (ACS_TABLES, None),
   41|     '2016_ACS1': (ACS_TABLES, None),
   42|     '2016_2020_ACS5a': (['B01001', 'B03002'], None),
   43|     '2016_2020_ACS5b': (['B05003', 'B05003B', 'B05003H'], None),
   44|     '2020_PL94171': (['P3', 'P4'], None),
   45|     '2024_ACS1': (ACS_TABLES, None),
   46| }
   47| 
   48| EXTRACT = Extract(request(DATASETS, 'Simulacra harness: state 18+ by sex x race x nativity x citizenship, 1980-2024'),
   49|                   'extract_request_{n}_modern.json', 'modern, 1980-2024', 'nhgis_extract_modern.py')
   50| 
   51| if __name__ == '__main__':
   52|     EXTRACT.cli()
```

## `scripts/harness/nhgis_extract_republic.py`

```python
    1| """Submit, wait for and download the NHGIS state-level extract behind the
    2| 1790–1860 censuses (early-republic population: sex × race × free/enslaved ×
    3| age bands, plus nativity for 1850 and 1860).
    4| 
    5|     python3 scripts/harness/nhgis_extract_republic.py submit     # prints the extract number
    6|     python3 scripts/harness/nhgis_extract_republic.py wait N     # polls, then downloads into the cache
    7|     python3 scripts/harness/nhgis_extract_republic.py status N
    8| 
    9| Key handling, cache layout and terms: nhgis_common.py.
   10| """
   11| from nhgis_common import Extract, request
   12| 
   13| TABLES = {
   14|     '1790_cPop': ['NT1', 'NT4', 'NT5', 'NT6'],          # white males 16+/<16, white females; race/slave status
   15|     '1800_cPop': ['NT1', 'NT5', 'NT6', 'NT9'],          # free white by sex × age; nonwhite by slave status
   16|     '1810_cPop': ['NT1', 'NT5', 'NT6', 'NT9'],
   17|     '1820_cPop': ['NT1', 'NT4A', 'NT4B', 'NT5', 'NT7', 'NT8', 'NT10'],  # + colored by slave status × sex × age; aliens
   18|     '1830_cPop': ['NT1', 'NT4', 'NT5', 'NT9', 'NT12'],  # + foreigners not naturalized
   19|     '1840_cPopX': ['NT1', 'NT4', 'NT5', 'NT25'],
   20|     '1850_cPAX': ['NT1', 'NT4', 'NT5', 'NT40'],         # race/slave × sex × age; nativity
   21|     '1850_sPAX': ['NT1', 'NT5', 'NT7'],                 # native / foreign / unknown birthplace × race × sex
   22|     '1860_cPAX': ['NT1', 'NT4', 'NT5', 'NT7'],          # race/slave × age × sex; nativity × race × sex
   23| }
   24| 
   25| EXTRACT = Extract(request(TABLES, 'Simulacra harness (agent G): state population by sex x race x free/slave x age, 1790-1860'),
   26|                   'extract_request_republic_{n}.json', '1790–1860 state tables', 'nhgis_extract_republic.py')
   27| 
   28| if __name__ == '__main__':
   29|     EXTRACT.cli()
```

## `scripts/harness/sessions-report.py`

```python
    1| """What people typed into the page, and what the robot couldn't model.
    2| 
    3|     python3 scripts/harness/sessions-report.py                 # everything logged
    4| 
    5| Reads sessions/requests.jsonl (written by serve/simulacra.js in dev), the
    6| intake queue's outcomes (sessions/queue-done.jsonl) and today's spend
    7| (sessions/spend.jsonl). Clusters are keyword guesses, good enough to pick the
    8| next fix; `run whatif` does the real reading.
    9| """
   10| import argparse
   11| import collections
   12| import json
   13| import re
   14| import time
   15| from pathlib import Path
   16| 
   17| SESSIONS = Path(__file__).resolve().parents[2] / 'sessions'
   18| 
   19| KINDS = [
   20|     ('candidate or entrant', r'\b(ran|runs?|running|candidate|independent|third[- ]party|nominee|nominated|ticket|instead of)\b'),
   21|     ('franchise change', r'\b(vote[ds]?|voting|suffrage|franchise|ballot|poll tax|literacy|enfranchis|disenfranchis|allowed to)\b'),
   22|     ('event or scandal', r'\b(scandal|war|strike|riot|died|death|assassinat|depression|crash|panic|flu|pandemic|lynch|bomb|revealed)\b'),
   23|     ('policy', r'\b(prohibition|tariff|tax|law|act|policy|treaty|bonus|union|wage|price|immigration quota)\b'),
   24|     ('demographic shift', r'\b(population|migration|migrat|immigrants?|moved|more people|fewer|census|birth)\b'),
   25|     ("another year's issue", r'\b(1[789]\d\d|20[0-2]\d)\b'),
   26| ]
   27| 
   28| 
   29| def kind(text):
   30|     t = text.lower()
   31|     for name, pat in KINDS:
   32|         if name == "another year's issue":
   33|             if any(y != '1920' for y in re.findall(pat, t)):
   34|                 return name
   35|         elif re.search(pat, t):
   36|             return name
   37|     return 'other'
   38| 
   39| 
   40| def rows(name, since):
   41|     p = SESSIONS / name
   42|     if not p.exists():
   43|         return []
   44|     out = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
   45|     return [r for r in out if not since or r.get('ts', '') >= since]
   46| 
   47| 
   48| def main():
   49|     ap = argparse.ArgumentParser()
   50|     ap.add_argument('--since', default='', help='ISO time; only requests at or after it')
   51|     a = ap.parse_args()
   52|     reqs = rows('requests.jsonl', a.since)
   53|     typed = [r for r in reqs if (r.get('text') or '').strip()]
   54|     unknown = [r for r in typed if r.get('unknown')]
   55|     print(f'requests: {len(reqs)} ({len(typed)} with typed text)')
   56|     print(f'unknown: {len(unknown)}' + (f' ({len(unknown) / len(typed):.0%} of typed)' if typed else ''))
   57|     missing = [r for r in reqs if not r.get('exists')]
   58|     if missing:
   59|         print(f'combinations not computed: {len(missing)} ({", ".join(sorted({r["combo"] for r in missing})[:6])})')
   60|     clusters = collections.defaultdict(list)
   61|     for r in unknown:
   62|         clusters[kind(r['unknown'])].append(r['unknown'])
   63|     if clusters:
   64|         print('\nunknowns by kind:')
   65|         for k, v in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
   66|             print(f'  {len(v):3d}  {k}: ' + '; '.join(f'"{t}"' for t, _ in collections.Counter(v).most_common(3)))
   67|     print('\ntop typed texts:')
   68|     for t, n in collections.Counter(r['text'].strip().lower() for r in typed).most_common(10):
   69|         mark = '?' if any(r.get('unknown') and r['text'].strip().lower() == t for r in typed) else ' '
   70|         print(f'  {n:3d} {mark} {t}')
   71|     done = rows('queue-done.jsonl', a.since)
   72|     if done:
   73|         print('\nintake outcomes:')
   74|         for r in done[-10:]:
   75|             print(f'  {r["status"]:13s} {r.get("key") or "":28s} ${r.get("dollars") or 0:<7} "{r["text"]}"')
   76|     day = time.strftime('%Y-%m-%d')
   77|     spend = [r for r in rows('spend.jsonl', '') if r['day'] == day]
   78|     if spend:
   79|         by = collections.Counter()
   80|         for r in spend:
   81|             by[r['stage']] += r['dollars']
   82|         print(f'\nspent today: ${sum(by.values()):.3f} (' + ', '.join(f'{k} ${v:.3f}' for k, v in by.most_common()) + ')')
   83| 
   84| 
   85| if __name__ == '__main__':
   86|     main()
```

## `scripts/llms_digest.py`

```python
    1| #!/usr/bin/env python3
    2| """Build llms.txt and llms/: a plain-text copy of this repository for tools that
    3| read text at a URL rather than cloning (llmstxt.org convention).
    4| 
    5|     python3 scripts/llms_digest.py           # write llms.txt and llms/
    6|     python3 scripts/llms_digest.py --check   # exit 1 if they don't match the code
    7| 
    8| .github/workflows/llms-digest.yml runs this on every push to main and commits
    9| the result, so the text always matches the code at the commit it names.
   10| Standard library only.
   11| 
   12|   llms.txt              index: the README's opening section, then links to everything below
   13|   llms/MAP.md           every tracked file: size, lines, first descriptive line, digest part
   14|   llms/HISTORY.md       commit history, verbatim from git (commits that only regenerate
   15|                         the digest are left out)
   16|   llms/code-N.md        full text of every source and doc file, line-numbered, in parts
   17|                         small enough to fetch whole
   18|   llms/data-samples.md  the first lines of one data file per top-level folder
   19| """
   20| from __future__ import annotations
   21| 
   22| import argparse
   23| import os
   24| import re
   25| import shutil
   26| import subprocess
   27| import sys
   28| import tempfile
   29| from pathlib import Path
   30| 
   31| PART_CHARS = 120_000
   32| OWN = ("llms.txt", "llms/")  # this script's output: never part of its own input
   33| SKIP_DIRS = {"node_modules", "dist", "build", ".svelte-kit", "__pycache__", ".venv", "venv", ".git", ".next"}
   34| LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock", "Cargo.lock"}
   35| DATA_EXT = {".json", ".jsonl", ".csv", ".tsv", ".parquet", ".npy", ".npz", ".arrow", ".pkl"}
   36| BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".pdf",
   37|               ".zip", ".gz", ".safetensors", ".bin", ".pt", ".onnx", ".mp4", ".mp3", ".wav"}
   38| LANG = {".py": "python", ".ts": "ts", ".js": "js", ".svelte": "svelte", ".tf": "hcl", ".sh": "bash",
   39|         ".md": "markdown", ".yml": "yaml", ".yaml": "yaml", ".toml": "toml", ".json": "json", ".html": "html",
   40|         ".css": "css", ".txt": "text", ".sql": "sql", ".go": "go", ".rs": "rust"}
   41| 
   42| 
   43| def git(*args: str, cwd: Path) -> str:
   44|     return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout
   45| 
   46| 
   47| def first_descriptive_line(text: str, ext: str) -> str:
   48|     """A file's own first line of description: a docstring, a leading comment, or a heading."""
   49|     if ext == ".py":
   50|         m = re.search(r'^\s*(?:#![^\n]*\n)?\s*(?:"""|\'\'\')\s*(.+)', text)
   51|         if m:
   52|             return m.group(1).strip().rstrip("\"'")
   53|     for line in text.splitlines()[:15]:
   54|         s = line.strip()
   55|         m = re.match(r"^(?:#{1,6}\s+|//+\s*|#\s*|/\*+\s*|\*\s+|<!--\s*)(.{8,})", s)
   56|         if m and not s.startswith("#!") and not s.startswith("// @ts"):
   57|             return m.group(1).strip().rstrip("*/ -").strip()
   58|     return ""
   59| 
   60| 
   61| def classify(path: str, size: int, raw: bytes) -> str:
   62|     name, ext = os.path.basename(path), os.path.splitext(path)[1].lower()
   63|     parts = path.split("/")
   64|     if any(p in SKIP_DIRS for p in parts[:-1]):
   65|         return "skip: generated or vendored directory"
   66|     if name in LOCKFILES:
   67|         return "skip: lockfile"
   68|     if ext in BINARY_EXT or b"\0" in raw[:4096]:
   69|         return "skip: binary"
   70|     if raw.startswith(b"version https://git-lfs"):
   71|         return "skip: Git LFS pointer (content not in the repo)"
   72|     if ext in DATA_EXT and not (len(parts) == 1 and size <= 20_000):  # root configs stay
   73|         return "data: sampled in data-samples.md"
   74|     if size > 200_000:
   75|         return "skip: larger than 200 KB"
   76|     return "include"
   77| 
   78| 
   79| def repo_identity(root: Path) -> tuple[str, str, str]:
   80|     """(owner, name, branch) from GitHub Actions, else from the origin remote."""
   81|     full = os.environ.get("GITHUB_REPOSITORY")
   82|     if not full:
   83|         url = git("remote", "get-url", "origin", cwd=root).strip()
   84|         m = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", url)
   85|         if not m:
   86|             sys.exit(f"can't tell the GitHub repository from {url!r}; set GITHUB_REPOSITORY=owner/name")
   87|         full = f"{m.group(1)}/{m.group(2)}"
   88|     owner, name = full.split("/", 1)
   89|     branch = os.environ.get("LLMS_BRANCH", "main")
   90|     return owner, name, branch
   91| 
   92| 
   93| def build(root: Path, out: Path) -> dict:
   94|     owner, name, branch = repo_identity(root)
   95|     # The last commit that changed anything besides the digest: rebuilding after a
   96|     # digest-only commit then gives identical text, so the workflow never loops.
   97|     code_only = ("--", ".", ":(exclude)llms.txt", ":(exclude)llms")
   98|     sha = git("log", "-1", "--format=%H", *code_only, cwd=root).strip()
   99|     date = git("log", "-1", "--format=%cs", *code_only, cwd=root).strip()
  100|     raw_base = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/"
  101|     files = [f for f in git("ls-files", cwd=root).splitlines() if f and not f.startswith(OWN)]
  102|     stamp = (f"Generated from commit `{sha[:12]}` ({date}) of github.com/{owner}/{name} by "
  103|              f"`scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to "
  104|              f"`{branch}`, so this text matches the code at that commit.")
  105| 
  106|     rows, included, data_dirs = [], [], {}
  107|     for f in files:
  108|         raw = (root / f).read_bytes()
  109|         verdict = classify(f, len(raw), raw)
  110|         ext = os.path.splitext(f)[1].lower()
  111|         text = "" if verdict == "skip: binary" else raw.decode("utf-8", "replace")
  112|         lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
  113|         desc = first_descriptive_line(text, ext) if verdict == "include" else ""
  114|         rows.append((f, len(raw), lines, desc, verdict))
  115|         if verdict == "include":
  116|             included.append((f, text, ext))
  117|         elif verdict.startswith("data"):
  118|             data_dirs.setdefault(f.split("/")[0] if "/" in f else "(root)", []).append((f, text))
  119| 
  120|     # Parts: whole files in path order, never split across parts.
  121|     parts, cur, cur_len = [], [], 0
  122|     for f, text, ext in included:
  123|         numbered = "\n".join(f"{i:>5}| {l}" for i, l in enumerate(text.splitlines(), 1))
  124|         block = f"\n## `{f}`\n\n```{LANG.get(ext, '')}\n{numbered}\n```\n"
  125|         if cur and cur_len + len(block) > PART_CHARS:
  126|             parts.append(cur)
  127|             cur, cur_len = [], 0
  128|         cur.append((f, block))
  129|         cur_len += len(block)
  130|     if cur:
  131|         parts.append(cur)
  132| 
  133|     (out / "llms").mkdir(parents=True, exist_ok=True)
  134|     part_index, file_part = [], {}
  135|     for i, part in enumerate(parts, 1):
  136|         fname = f"llms/code-{i}.md"
  137|         body = "".join(b for _, b in part)
  138|         (out / fname).write_text(
  139|             f"# {name}: source and docs, part {i} of {len(parts)}\n\n{stamp}\nFiles `{part[0][0]}` to "
  140|             f"`{part[-1][0]}`. Lines are numbered as in the repository.\n" + body)
  141|         part_index.append((fname, part[0][0], part[-1][0], len(part), len(body)))
  142|         for f, _ in part:
  143|             file_part[f] = f"code-{i}.md"
  144| 
  145|     m = [f"# {name}: file map", "", stamp, "",
  146|          f"{len(files)} tracked files. {len(included)} are reproduced in full in the `code-N.md` parts; "
  147|          "the rest are listed with the reason they are not.", "",
  148|          f"Every path below is relative to {raw_base} (append the path to fetch the raw file).", "",
  149|          "| File | Bytes | Lines | Description | In digest |", "|---|---|---|---|---|"]
  150|     for f, size, lines, desc, verdict in rows:
  151|         if not verdict.startswith("data"):
  152|             m.append(f"| `{f}` | {size:,} | {lines:,} | {desc.replace('|', '/')[:100]} | {file_part.get(f, verdict)} |")
  153|     if data_dirs:
  154|         m += ["", "### Data files (not reproduced; one sample per folder in `data-samples.md`)", "",
  155|               "| Folder | Files | Bytes |", "|---|---|---|"]
  156|         sizes = {r[0]: r[1] for r in rows}
  157|         for d, items in sorted(data_dirs.items()):
  158|             m.append(f"| `{d}/` | {len(items)} | {sum(sizes[f] for f, _ in items):,} |")
  159|     (out / "llms" / "MAP.md").write_text("\n".join(m) + "\n")
  160| 
  161|     if data_dirs:
  162|         ds = [f"# {name}: data samples", "", stamp, "",
  163|               "Data files are not reproduced in full. One sample per top-level folder, first 40 lines:", ""]
  164|         for d, items in sorted(data_dirs.items()):
  165|             f, text = items[0]
  166|             sample = "\n".join(text.splitlines()[:40])
  167|             ds += [f"## `{d}/` ({len(items)} files)", "", f"Sample: `{f}`", "",
  168|                    f"```{LANG.get(os.path.splitext(f)[1].lower(), '')}\n{sample}\n```", ""]
  169|         (out / "llms" / "data-samples.md").write_text("\n".join(ds))
  170| 
  171|     # Commits that touched anything besides the digest itself, verbatim.
  172|     log = git("log", "--format=%h  %ad  %an  %s", "--date=short", "--", ".", ":(exclude)llms.txt", ":(exclude)llms",
  173|               cwd=root).strip()
  174|     count = len(log.splitlines()) if log else 0
  175|     (out / "llms" / "HISTORY.md").write_text(
  176|         f"# {name}: commit history\n\n{stamp}\n\n{count} commit(s), verbatim from `git log` "
  177|         f"(commits that only regenerate this digest are left out):\n\n```\n{log}\n```\n")
  178| 
  179|     readme = next((f for f in files if f.lower() == "readme.md"), None)
  180|     total = sum(p[4] for p in part_index)
  181|     idx = [f"# {name}", ""]
  182|     if readme:
  183|         intro = re.split(r"(?m)^##\s", (root / readme).read_text(errors="replace"))[0]
  184|         intro = re.sub(r"(?m)^#\s.*\n", "", intro).strip()
  185|         if intro:
  186|             idx += ["## Summary (the README's opening section, verbatim)", "", intro[:3000], ""]
  187|     idx += [stamp, "", "## Start here", ""]
  188|     if readme:
  189|         idx.append(f"- [README]({raw_base}{readme}): overview")
  190|     idx += [f"- [File map]({raw_base}llms/MAP.md): all {len(files)} files with size, line count, description, "
  191|             "and which digest part holds each one",
  192|             f"- [Commit history]({raw_base}llms/HISTORY.md): {count} commit(s)", ""]
  193|     docs = [r[0] for r in rows if r[0].lower().endswith(".md") and r[0] != readme]
  194|     if docs:
  195|         idx += ["## Documentation", ""] + [f"- [{d}]({raw_base}{d})" for d in docs[:30]] + [""]
  196|     idx += [f"## Full source text ({total:,} characters, about {total // 4:,} tokens, in {len(part_index)} part(s))", ""]
  197|     idx += [f"- [{fn}]({raw_base}{fn}): {n} files, `{a}` to `{b}` ({size:,} characters)"
  198|             for fn, a, b, n, size in part_index]
  199|     if data_dirs:
  200|         idx += ["", "## Data", "", f"- [Data samples]({raw_base}llms/data-samples.md): "
  201|                 f"{sum(len(v) for v in data_dirs.values())} data files in {len(data_dirs)} folder(s), one sample each"]
  202|     (out / "llms.txt").write_text("\n".join(idx) + "\n")
  203|     return {"files": len(files), "included": len(included), "parts": len(part_index), "chars": total}
  204| 
  205| 
  206| def snapshot(d: Path) -> dict[str, str]:
  207|     out = {}
  208|     if (d / "llms.txt").exists():
  209|         out["llms.txt"] = (d / "llms.txt").read_text()
  210|     for p in sorted((d / "llms").glob("*")) if (d / "llms").is_dir() else []:
  211|         out[f"llms/{p.name}"] = p.read_text()
  212|     return out
  213| 
  214| 
  215| def main() -> None:
  216|     ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  217|     ap.add_argument("--check", action="store_true", help="exit 1 if llms.txt and llms/ don't match the code")
  218|     args = ap.parse_args()
  219|     root = Path(git("rev-parse", "--show-toplevel", cwd=Path.cwd()).strip())
  220|     tmp = Path(tempfile.mkdtemp(prefix="llms-digest-"))
  221|     try:
  222|         stats = build(root, tmp)
  223|         fresh = snapshot(tmp)
  224|         if args.check:
  225|             # The stamp names a commit; compare everything else.
  226|             norm = lambda d: {k: re.sub(r"commit `[0-9a-f]{12}` \(\d{4}-\d\d-\d\d\)", "commit", v) for k, v in d.items()}
  227|             if norm(fresh) != norm(snapshot(root)):
  228|                 sys.exit("llms.txt / llms/ don't match the code. Run: python3 scripts/llms_digest.py")
  229|             print("llms.txt and llms/ match the code.")
  230|             return
  231|         shutil.rmtree(root / "llms", ignore_errors=True)
  232|         (root / "llms").mkdir()
  233|         for rel, text in fresh.items():
  234|             (root / rel).write_text(text)
  235|         print(f"{stats['included']} of {stats['files']} files in {stats['parts']} part(s), {stats['chars']:,} characters.")
  236|     finally:
  237|         shutil.rmtree(tmp, ignore_errors=True)
  238| 
  239| 
  240| if __name__ == "__main__":
  241|     main()
```

## `scripts/mirror-portraits.py`

```python
    1| #!/usr/bin/env python3
    2| """Mirror the candidates' Wikimedia Commons portraits for the assets bucket.
    3| 
    4| For every person in src/lib/simulacra/history.ts (PEOPLE), resolve the Commons
    5| file through the Commons API (prop=imageinfo, iiprop=url|extmetadata), download
    6| its 330px thumbnail to <out>/portraits/<id>.jpg, and write
    7| <out>/portraits/credits.json with the file page, author, licence name and
    8| licence URL exactly as the API gives them (never guessed).
    9| 
   10| The output stays out of git; scripts/publish-assets.sh uploads it.
   11| Re-runnable: existing images are kept unless --force.
   12| 
   13|   python3 scripts/mirror-portraits.py --out ../simulacra-assets
   14| """
   15| from __future__ import annotations
   16| 
   17| import argparse
   18| import html
   19| import json
   20| import re
   21| import sys
   22| import time
   23| import urllib.parse
   24| import urllib.request
   25| from pathlib import Path
   26| 
   27| ROOT = Path(__file__).resolve().parent.parent
   28| HISTORY = ROOT / 'src/lib/simulacra/history.ts'
   29| API = 'https://commons.wikimedia.org/w/api.php'
   30| # Wikimedia's User-Agent policy: identify the tool and a contact.
   31| UA = 'SimulacraAmericana-portrait-mirror/1.0 (https://simulacraamericana.com; cam@partyhat.ai)'
   32| WIDTH = 330
   33| 
   34| # `  id: ["Full Name", "Surname", "x/xy/File.jpg/330px-File.jpg"],` inside PEOPLE.
   35| ROW = re.compile(r'^\s*(\w+):\s*\["([^"]+)",\s*"[^"]*",\s*"([^"]+)"\]', re.M)
   36| 
   37| 
   38| def people() -> list[tuple[str, str, str]]:
   39|     src = HISTORY.read_text()
   40|     block = src[src.index('const PEOPLE = {'):]
   41|     block = block[:block.index('\n}')]
   42|     rows = []
   43|     for pid, name, path in ROW.findall(block):
   44|         # "b/b6/<File>/330px-<File>": the Commons file name is the third segment.
   45|         rows.append((pid, name, urllib.parse.unquote(path.split('/')[2])))
   46|     if not rows:
   47|         sys.exit(f'no PEOPLE rows parsed from {HISTORY}')
   48|     return rows
   49| 
   50| 
   51| def get(url: str) -> bytes:
   52|     req = urllib.request.Request(url, headers={'User-Agent': UA})
   53|     for attempt in range(4):
   54|         try:
   55|             with urllib.request.urlopen(req, timeout=30) as r:
   56|                 return r.read()
   57|         except urllib.error.HTTPError as e:
   58|             if e.code in (429, 503) and attempt < 3:
   59|                 time.sleep(2 ** attempt * 2)
   60|                 continue
   61|             raise
   62|     raise RuntimeError('unreachable')
   63| 
   64| 
   65| def plain(value: str | None) -> str | None:
   66|     """extmetadata values are HTML fragments; keep their text."""
   67|     if not value:
   68|         return None
   69|     return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', value))).strip() or None
   70| 
   71| 
   72| def imageinfo(titles: list[str]) -> dict[str, dict]:
   73|     q = urllib.parse.urlencode({
   74|         'action': 'query', 'format': 'json', 'formatversion': '2', 'prop': 'imageinfo',
   75|         'iiprop': 'url|extmetadata', 'iiurlwidth': WIDTH, 'titles': '|'.join(f'File:{t}' for t in titles),
   76|     })
   77|     data = json.loads(get(f'{API}?{q}'))
   78|     # The API normalises titles (underscores -> spaces); map back.
   79|     norm = {n['to']: n['from'] for n in data['query'].get('normalized', [])}
   80|     out = {}
   81|     for page in data['query']['pages']:
   82|         asked = norm.get(page['title'], page['title'])
   83|         out[asked.removeprefix('File:')] = page
   84|     return out
   85| 
   86| 
   87| def main() -> None:
   88|     ap = argparse.ArgumentParser()
   89|     ap.add_argument('--out', type=Path, required=True, help='assets staging folder (outside the repo)')
   90|     ap.add_argument('--force', action='store_true', help='re-download images that already exist')
   91|     args = ap.parse_args()
   92|     dest = args.out / 'portraits'
   93|     dest.mkdir(parents=True, exist_ok=True)
   94| 
   95|     rows = people()
   96|     pages: dict[str, dict] = {}
   97|     files = sorted({f for _, _, f in rows})
   98|     for i in range(0, len(files), 40):  # the API takes 50 titles per query
   99|         pages.update(imageinfo(files[i:i + 40]))
  100| 
  101|     credits, problems = {}, []
  102|     for pid, name, file in rows:
  103|         page = pages.get(file)
  104|         info = (page or {}).get('imageinfo', [None])[0]
  105|         if not info:
  106|             problems.append(f'{pid}: {file} not found on Commons')
  107|             continue
  108|         meta = info.get('extmetadata', {})
  109|         val = lambda k: plain(meta.get(k, {}).get('value'))  # noqa: E731
  110|         target = dest / f'{pid}.jpg'
  111|         if args.force or not target.exists():
  112|             target.write_bytes(get(info['thumburl']))
  113|             time.sleep(0.2)
  114|         credits[pid] = {
  115|             'name': name,
  116|             'file': f'File:{file}',
  117|             'filePage': info['descriptionurl'],
  118|             'author': val('Artist'),
  119|             'credit': val('Credit'),
  120|             'license': val('LicenseShortName'),
  121|             'licenseUrl': val('LicenseUrl'),
  122|             'attributionRequired': val('AttributionRequired') == 'true',
  123|             'usageTerms': val('UsageTerms'),
  124|         }
  125|         lic = credits[pid]['license'] or ''
  126|         if credits[pid]['attributionRequired'] and not credits[pid]['author']:
  127|             problems.append(f'{pid}: {lic} requires attribution but the API gives no author')
  128| 
  129|     (dest / 'credits.json').write_text(json.dumps(credits, indent=2, ensure_ascii=False) + '\n')
  130|     needs = sorted(p for p, c in credits.items() if c['attributionRequired'])
  131|     print(f'{len(credits)}/{len(rows)} portraits mirrored to {dest}')
  132|     print(f'{len(needs)} need attribution: {", ".join(needs) or "none"}')
  133|     for p in problems:
  134|         print('PROBLEM', p, file=sys.stderr)
  135|     sys.exit(1 if problems else 0)
  136| 
  137| 
  138| if __name__ == '__main__':
  139|     main()
```

## `scripts/model-check.ts`

```ts
    1| // Prints the sample model's outcome for every what-if of every story
    2| // election (src/lib/simulacra/stories.ts), to check the model outside the
    3| // page: history's electoral vote, then each what-if's.
    4| //   pnpm tsx scripts/model-check.ts
    5| import { electionOf } from '../src/lib/simulacra/history';
    6| import { _model } from '../src/lib/simulacra/sample';
    7| import { STORIES } from '../src/lib/simulacra/stories';
    8| 
    9| const ev = (r: { ev: { A: number; B: number; O: number } }) => `${r.ev.A}–${r.ev.B}${r.ev.O ? `–${r.ev.O}` : ''}`;
   10| 
   11| for (const year of Object.keys(STORIES).map(Number)) {
   12|   const e = electionOf(year);
   13|   const history = _model.rerun(year);
   14|   if (!e || !history) continue;
   15|   const [a, b] = e.candidates;
   16|   console.log(`\n${year}  ${a.short} over ${b?.short ?? 'no one'}: ${ev(history)} as it happened`);
   17|   for (const w of _model.whatIfsFor(year)) {
   18|     const r = _model.rerun(year, [w.key]);
   19|     if (!r) continue;
   20|     const flips = r.states.filter((s) => s.flipped).length;
   21|     const winner = r.winner ? (e.candidates.find((c) => c.key === r.winner)?.short ?? 'Others') : 'no majority';
   22|     console.log(`  ${w.key.padEnd(14)} ${ev(r).padEnd(12)} ${winner.padEnd(12)} ${String(flips).padStart(2)} flipped  (${r.confidence})`);
   23|   }
   24| }
```

## `scripts/publish-assets.sh`

```bash
    1| #!/usr/bin/env bash
    2| # Publish the robot assets and mirrored portraits to s3://simulacra-americana-assets
    3| # (served by CloudFront at assets.simulacraamericana.com) and invalidate.
    4| # Re-runnable. The assets themselves are never in git.
    5| #
    6| #   scripts/publish-assets.sh [assets-dir]     default ../simulacra-assets
    7| #
    8| # Robot: COPIED (never moved) from the shared Partyhat bucket, only what the
    9| # page loads (src/lib/robot: models/atlas-09-americana.glb and its rerun paint
   10| # set). Portraits: from scripts/mirror-portraits.py's output.
   11| set -euo pipefail
   12| 
   13| SRC="s3://${SOURCE_ASSETS_BUCKET:?set SOURCE_ASSETS_BUCKET to the bucket holding the source harness assets}/harness-assets"
   14| DST=s3://simulacra-americana-assets
   15| ASSETS=${1:-$(cd "$(dirname "$0")/.." && pwd)/../simulacra-assets}
   16| LONG='public, max-age=31536000, immutable'
   17| test "$(aws sts get-caller-identity --query Account --output text)" = "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID to the target AWS account}"
   18| 
   19| # Robot model and paint set (object-to-object copy, same account).
   20| aws s3 cp "$SRC/models/atlas-09-americana.glb" "$DST/models/atlas-09-americana.glb" \
   21|   --metadata-directive REPLACE --content-type model/gltf-binary --cache-control "$LONG" --only-show-errors
   22| aws s3 cp "$SRC/models/atlas-09-americana-rerun/" "$DST/models/atlas-09-americana-rerun/" --recursive \
   23|   --metadata-directive REPLACE --cache-control "$LONG" --only-show-errors
   24| # --metadata-directive REPLACE drops the source content types; restore them.
   25| for k in $(aws s3api list-objects-v2 --bucket simulacra-americana-assets --prefix models/atlas-09-americana-rerun/ \
   26|              --query 'Contents[].Key' --output text); do
   27|   case "$k" in
   28|     *.json) ct=application/json ;; *.png) ct=image/png ;; *.jpg|*.jpeg) ct=image/jpeg ;;
   29|     *.webp) ct=image/webp ;; *.ktx2) ct=image/ktx2 ;; *) continue ;;
   30|   esac
   31|   aws s3 cp "$DST/$k" "$DST/$k" --metadata-directive REPLACE --content-type "$ct" \
   32|     --cache-control "$LONG" --only-show-errors
   33| done
   34| 
   35| # Portraits and their credits (credits change when a portrait does: short cache).
   36| if [ -d "$ASSETS/portraits" ]; then
   37|   aws s3 sync "$ASSETS/portraits/" "$DST/portraits/" --exclude '*' --include '*.jpg' \
   38|     --content-type image/jpeg --cache-control "$LONG" --only-show-errors
   39|   aws s3 cp "$ASSETS/portraits/credits.json" "$DST/portraits/credits.json" \
   40|     --content-type application/json --cache-control 'public, max-age=3600' --only-show-errors
   41| else
   42|   echo "no $ASSETS/portraits; run scripts/mirror-portraits.py --out $ASSETS first" >&2
   43| fi
   44| 
   45| aws s3 ls "$DST/" --recursive --summarize | tail -2
   46| 
   47| # Invalidate (the distribution exists only after the stand-up apply).
   48| DIST=$(cd "$(dirname "$0")/../infra" && terraform output -raw assets_distribution_id 2>/dev/null || true)
   49| if [ -n "$DIST" ]; then
   50|   aws cloudfront create-invalidation --distribution-id "$DIST" --paths '/*' \
   51|     --query 'Invalidation.[Id,Status]' --output text
   52| fi
```

## `scripts/size-check.ts`

```ts
    1| // Fails when any tracked source file is over the line limit.
    2| import { execFileSync } from 'node:child_process';
    3| import { readFileSync } from 'node:fs';
    4| 
    5| const LIMIT = 1000;
    6| const SOURCE = /\.(ts|svelte|js|mjs|py|css)$/;
    7| 
    8| const files = execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard'], { encoding: 'utf8' })
    9|   .split('\n')
   10|   .filter((f) => SOURCE.test(f));
   11| 
   12| const over = files
   13|   .map((f) => ({ f, n: readFileSync(f, 'utf8').split('\n').length }))
   14|   .filter(({ n }) => n > LIMIT);
   15| 
   16| for (const { f, n } of over) console.error(`${f}: ${n} lines (limit ${LIMIT})`);
   17| if (over.length > 0) process.exit(1);
   18| console.log(`size: ${files.length} files, none over ${LIMIT} lines`);
```

## `scripts/sync-data.sh`

```bash
    1| #!/usr/bin/env bash
    2| # Census-derived data and service state: laptop -> private data bucket -> EFS.
    3| # Re-runnable. Nothing here ever writes to git, an image, Vercel or the assets bucket.
    4| #
    5| #   scripts/sync-data.sh upload-cache   laptop harness_cache (minus */raw/) -> s3://.../cache/
    6| #   scripts/sync-data.sh upload-seed    repo bundles/whatifs/configs/runs + laptop runs/_cache -> s3://.../seed/
    7| #   scripts/sync-data.sh seed           one-off ECS task: seed -> EFS (refuses if already seeded)
    8| #   scripts/sync-data.sh cache          one-off ECS task: cache -> EFS/cache (replaces it)
    9| #   scripts/sync-data.sh backup         tarball the laptop's harness state + cache to s3://.../backups/<date>/
   10| #
   11| # The run id hashes the cache's manifest: the bytes on EFS must match the
   12| # laptop's for run ids to line up, so the cache is synced byte-for-byte.
   13| #
   14| # Note: on aws-cli 2.23.4 (this laptop) `aws s3 cp` of a multipart object
   15| # DOWN from this versioned bucket fails with NoSuchKey; `aws s3api get-object`
   16| # works. Uploads and small-file syncs are unaffected.
   17| set -euo pipefail
   18| 
   19| B=s3://simulacra-americana-data
   20| REPO=$(cd "$(dirname "$0")/.." && pwd)
   21| CACHE=${SIMHARNESS_CACHE:-$HOME/research_notes/historical_election_sim_data/harness_cache}
   22| # The live harness the laptop has been running (its runs/_cache is the answer cache).
   23| LAPTOP_HARNESS=${LAPTOP_HARNESS:-$HOME/Documents/fromDesktop/quickmoveaway/vaultSYncWebWithLocalOPtion/vaultsync-chatwindows/src/lib/simulacra/harness}
   24| test "$(aws sts get-caller-identity --query Account --output text)" = "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID to the target AWS account}"
   25| 
   26| run_task() {
   27|   local mode=$1 o
   28|   o=$(cd "$REPO/infra" && terraform output -json seed_task)
   29|   local cluster td subnets sg
   30|   cluster=$(jq -r .cluster <<<"$o"); td=$(jq -r .task_definition <<<"$o")
   31|   subnets=$(jq -r '.subnets | join(",")' <<<"$o"); sg=$(jq -r .security_group <<<"$o")
   32|   local arn
   33|   arn=$(aws ecs run-task --cluster "$cluster" --task-definition "$td" --launch-type FARGATE \
   34|     --network-configuration "awsvpcConfiguration={subnets=[$subnets],securityGroups=[$sg],assignPublicIp=ENABLED}" \
   35|     --overrides "{\"containerOverrides\":[{\"name\":\"seed\",\"environment\":[{\"name\":\"MODE\",\"value\":\"$mode\"}]}]}" \
   36|     --query 'tasks[0].taskArn' --output text)
   37|   echo "started $arn; waiting"
   38|   aws ecs wait tasks-stopped --cluster "$cluster" --tasks "$arn"
   39|   aws ecs describe-tasks --cluster "$cluster" --tasks "$arn" \
   40|     --query 'tasks[0].containers[0].[exitCode,reason]' --output text
   41|   echo "logs: aws logs tail /ecs/simulacra --log-stream-name-prefix seed --since 15m"
   42| }
   43| 
   44| case "${1:-}" in
   45|   upload-cache)
   46|     aws s3 sync "$CACHE/" "$B/cache/" --exclude '*/raw/*' --exclude '.DS_Store' --only-show-errors
   47|     aws s3 ls "$B/cache/" --recursive --summarize | tail -2 ;;
   48|   upload-seed)
   49|     for d in whatifs configs; do
   50|       aws s3 sync "$REPO/$d/" "$B/seed/$d/" --exclude '.DS_Store' --only-show-errors
   51|     done
   52|     aws s3 sync "$REPO/serve/bundles/" "$B/seed/bundles/" --exclude '.DS_Store' --only-show-errors
   53|     aws s3 sync "$REPO/runs/" "$B/seed/runs/" --exclude '.DS_Store' --only-show-errors
   54|     # The answer cache and pickles aren't in git; they come from the laptop.
   55|     aws s3 sync "$LAPTOP_HARNESS/runs/_cache/" "$B/seed/runs/_cache/" --exclude '.DS_Store' --only-show-errors
   56|     aws s3 ls "$B/seed/" --recursive --summarize | tail -2 ;;
   57|   seed)  run_task seed ;;
   58|   cache) run_task cache ;;
   59|   backup)
   60|     d=$(date +%F); tmp=$(mktemp -d)
   61|     (cd "$LAPTOP_HARNESS" && COPYFILE_DISABLE=1 tar czf "$tmp/harness-state-$d.tgz" serve/bundles sessions runs whatifs configs)
   62|     (cd "$CACHE" && COPYFILE_DISABLE=1 tar czf "$tmp/harness-cache-derived-$d.tgz" --exclude='*/raw' .)
   63|     (cd "$tmp" && shasum -a 256 ./*.tgz > SHA256SUMS)
   64|     aws s3 cp "$tmp/" "$B/backups/$d/" --recursive --only-show-errors
   65|     cat "$tmp/SHA256SUMS"; rm -rf "$tmp" ;;
   66|   *)
   67|     sed -n '2,12p' "$0"; exit 2 ;;
   68| esac
```

## `serve/app.ts`

```ts
    1| // The server: /api/simulacra plus the static SvelteKit build, with an SPA
    2| // fallback to build/index.html for any other GET.
    3| import { existsSync } from 'node:fs';
    4| import path from 'node:path';
    5| import express, { type Express } from 'express';
    6| import { createSimulacraRouter, optionsFromEnv, type SimulacraOptions } from './simulacra';
    7| 
    8| export interface AppOptions {
    9|   simulacra: SimulacraOptions;
   10|   /** The static build folder (`pnpm build`); not served when it has no index.html. */
   11|   build: string;
   12| }
   13| 
   14| export const defaultAppOptions = (): AppOptions => ({
   15|   simulacra: optionsFromEnv(),
   16|   build: path.resolve(import.meta.dirname, '..', 'build')
   17| });
   18| 
   19| export function createApp(opts: AppOptions = defaultAppOptions()): Express {
   20|   const app = express();
   21|   app.disable('x-powered-by');
   22|   app.use('/api/simulacra', createSimulacraRouter(opts.simulacra));
   23|   const index = path.join(opts.build, 'index.html');
   24|   if (existsSync(index)) {
   25|     app.use(express.static(opts.build));
   26|     app.get('/{*path}', (_req, res) => res.sendFile(index));
   27|   }
   28|   return app;
   29| }
```

## `serve/bundle.ts`

```ts
    1| // What enters the server, parsed once with zod: the bundle contract and the
    2| // request bodies (one definition, shared with the page: ./contract.ts), and
    3| // the session files the intake worker writes. The names here are the
    4| // server's: each value is also its parsed type.
    5| import { z } from 'zod';
    6| import {
    7|   BucketSchema,
    8|   BundleResultSchema,
    9|   BundleSchema,
   10|   EditsSchema,
   11|   RunRequestSchema,
   12|   SliceSchema,
   13|   StepSchema,
   14|   TableRowSchema,
   15|   ToldSchema
   16| } from './contract';
   17| 
   18| export { FIELDS, type Field, RUN_LIMITS } from './contract';
   19| 
   20| export const PageKey = BucketSchema;
   21| export type PageKey = z.infer<typeof PageKey>;
   22| 
   23| export const Slice = SliceSchema;
   24| export type Slice = z.infer<typeof Slice>;
   25| 
   26| /** One what-if combination's result, as the bundle holds it. Loose: additive fields pass through to the page. */
   27| export const Result = BundleResultSchema;
   28| export type Result = z.infer<typeof Result>;
   29| 
   30| export const TableRow = TableRowSchema;
   31| export type TableRow = z.infer<typeof TableRow>;
   32| 
   33| export const Told = ToldSchema;
   34| export type Told = z.infer<typeof Told>;
   35| 
   36| export const Bundle = BundleSchema;
   37| export type Bundle = z.infer<typeof Bundle>;
   38| 
   39| // ── Request bodies ──
   40| 
   41| /** Hand edits: per slice, changes in fractions of its adults (summing to 0). */
   42| export const Edits = EditsSchema;
   43| export type Edits = z.infer<typeof Edits>;
   44| 
   45| /** POST /runs, within RUN_LIMITS. */
   46| export const RunRequest = RunRequestSchema;
   47| export type RunRequest = z.infer<typeof RunRequest>;
   48| 
   49| // ── Session files the intake worker writes (dev only) ──
   50| 
   51| export const QueueDone = z.looseObject({
   52|   text: z.string(),
   53|   year: z.number().nullish(),
   54|   status: z.string(),
   55|   key: z.string().nullish(),
   56|   why: z.string().nullish()
   57| });
   58| export type QueueDone = z.infer<typeof QueueDone>;
   59| 
   60| export const QueueFailed = z.looseObject({
   61|   text: z.string(),
   62|   year: z.number().nullish(),
   63|   at: z.number(),
   64|   why: z.string().nullish()
   65| });
   66| export type QueueFailed = z.infer<typeof QueueFailed>;
   67| 
   68| export const Step = StepSchema;
   69| export type Step = z.infer<typeof Step>;
   70| 
   71| export const IntakeStatus = z.looseObject({ text: z.string().nullable(), steps: z.array(Step) });
```

## `serve/bundles/RUN_ID`

```
    1| 2004-01ab47632c
```

## `serve/contract.test.ts`

```ts
    1| import { existsSync, readdirSync, readFileSync } from 'node:fs';
    2| import path from 'node:path';
    3| import { describe, expect, test } from 'vitest';
    4| import { BundleSchema, RUN_LIMITS, RunRequestSchema } from './contract';
    5| 
    6| const ROOT = path.resolve(import.meta.dirname, '..');
    7| const FIXTURE = path.join(ROOT, 'tests', 'fixtures', 'bundle.example.json');
    8| const BUNDLES = path.join(ROOT, 'serve', 'bundles');
    9| 
   10| describe('BundleSchema', () => {
   11|   test('parses the shared bundle example (tests/fixtures/bundle.example.json)', () => {
   12|     const parsed = BundleSchema.safeParse(JSON.parse(readFileSync(FIXTURE, 'utf8')));
   13|     expect(parsed.error?.issues ?? []).toEqual([]);
   14|     // Published bundles write State.flipped as 0 / 1: parsed, it is a boolean.
   15|     const flips = Object.values(parsed.data?.runs ?? {}).flatMap((r) => r.states.map((s) => s.flipped));
   16|     expect(flips.length).toBeGreaterThan(0);
   17|     expect(new Set(flips.map((f) => typeof f))).toEqual(new Set(['boolean']));
   18|   });
   19| 
   20|   test('fields it does not name pass through, for the page', () => {
   21|     const raw = JSON.parse(readFileSync(FIXTURE, 'utf8'));
   22|     const run = BundleSchema.parse(raw).runs[''];
   23|     expect(run && Object.keys(run).sort()).toEqual(Object.keys(raw.runs['']).sort());
   24|   });
   25| 
   26|   const files = existsSync(BUNDLES) ? readdirSync(BUNDLES).filter((f) => /^\d{4}\.json$/.test(f)) : [];
   27|   test.skipIf(files.length === 0)('parses every served bundle (skips when serve/bundles is absent)', () => {
   28|     const bad = files.filter((f) => !BundleSchema.safeParse(JSON.parse(readFileSync(path.join(BUNDLES, f), 'utf8'))).success);
   29|     expect(bad).toEqual([]);
   30|   });
   31| });
   32| 
   33| describe('RunRequestSchema', () => {
   34|   const ok = (body: unknown) => RunRequestSchema.safeParse(body).success;
   35| 
   36|   test('a plain ask parses, with defaults and the words trimmed', () => {
   37|     expect(RunRequestSchema.parse({ year: '1920', text: '  the league passes  ' })).toEqual({
   38|       year: 1920,
   39|       whatIfs: [],
   40|       text: 'the league passes',
   41|       edits: {}
   42|     });
   43|   });
   44| 
   45|   test('the year is an election year in range', () => {
   46|     expect(ok({ year: RUN_LIMITS.firstYear })).toBe(true);
   47|     expect(ok({ year: RUN_LIMITS.lastYear })).toBe(true);
   48|     expect(ok({ year: 1788 })).toBe(false);
   49|     expect(ok({ year: 2101 })).toBe(false);
   50|     expect(ok({ year: 1920.5 })).toBe(false);
   51|     expect(ok({ year: 'soon' })).toBe(false);
   52|   });
   53| 
   54|   test('typed words: at most 300 characters once trimmed', () => {
   55|     expect(ok({ year: 1920, text: 'x'.repeat(RUN_LIMITS.text) })).toBe(true);
   56|     expect(ok({ year: 1920, text: ` ${'x'.repeat(RUN_LIMITS.text)} ` })).toBe(true);
   57|     expect(ok({ year: 1920, text: 'x'.repeat(RUN_LIMITS.text + 1) })).toBe(false);
   58|   });
   59| 
   60|   test('what-ifs: at most 32 keys of at most 80 characters', () => {
   61|     const keys = (n: number, len = 8) => Array.from({ length: n }, (_, i) => `${i}`.padStart(len, 'k'));
   62|     expect(ok({ year: 1920, whatIfs: keys(RUN_LIMITS.whatIfs) })).toBe(true);
   63|     expect(ok({ year: 1920, whatIfs: keys(RUN_LIMITS.whatIfs + 1) })).toBe(false);
   64|     expect(ok({ year: 1920, whatIfs: keys(1, RUN_LIMITS.key) })).toBe(true);
   65|     expect(ok({ year: 1920, whatIfs: keys(1, RUN_LIMITS.key + 1) })).toBe(false);
   66|   });
   67| 
   68|   test('edits: at most 64 groups, keys of at most 80 characters, each change within [-1, 1]', () => {
   69|     const groups = (n: number) => Object.fromEntries(Array.from({ length: n }, (_, i) => [`g${i}`, { A: 0.1, home: -0.1 }]));
   70|     expect(ok({ year: 1920, edits: groups(RUN_LIMITS.edits) })).toBe(true);
   71|     expect(ok({ year: 1920, edits: groups(RUN_LIMITS.edits + 1) })).toBe(false);
   72|     expect(ok({ year: 1920, edits: { ['k'.repeat(RUN_LIMITS.key + 1)]: { A: 0 } } })).toBe(false);
   73|     expect(ok({ year: 1920, edits: { women: { A: 1, home: -1 } } })).toBe(true);
   74|     expect(ok({ year: 1920, edits: { women: { A: 1.01 } } })).toBe(false);
   75|     expect(ok({ year: 1920, edits: { women: { A: Number.POSITIVE_INFINITY } } })).toBe(false);
   76|     expect(ok({ year: 1920, edits: { women: { nobody: 0.1 } } })).toBe(false);
   77|   });
   78| });
```

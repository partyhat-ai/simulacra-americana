# simulacra-americana: source and docs, part 5 of 17

Generated from commit `7f181fc6d5be` (2026-11-24) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `scripts/harness/build_population_modern.py` to `scripts/harness/sessions-report.py`. Lines are numbered as in the repository.

## `scripts/harness/build_population_modern.py`

```python
    1| """NHGIS extract (nhgis_extract_modern.py) -> population/adults18_<year>_by_state_nhgis.csv
    2| for 1980-2024: adults 18+ by state x sex x {white_nh_native, black_nh_native,
    3| other_native, naturalized, noncitizen}, in the long format of build_population.
    4| 
    5|     python3 scripts/harness/build_population_modern.py 2000 [--extract N]   # one year
    6|     python3 scripts/harness/build_population_modern.py all                  # every year in BUILDERS
    7| 
    8| (Only this CLI writes these tables: build_population.py is 21+ and stops at 1970.)
    9| 
   10| Sources by year (all NHGIS, state level):
   11|   1980  STF2b NTB8B sex x age, iterated all / white not Spanish / Black not Spanish (100%);
   12|         STF4Pb NTPB9 nativity x citizenship iterated all / white / Black / Spanish (sample,
   13|         all ages); STF2a NTA13 Spanish origin by race. Not crossed with age: foreign-born
   14|         adults = FB all ages x 1990 state adult share by citizenship [I]; race FB net of
   15|         Spanish FB by the state's Spanish race mix [I]; FB sex split from 2000 [I].
   16|   1990  MARS NP1 age x Hispanic x sex x race (white/Black NH 18+ by sex); STF3 NP37
   17|         age x citizenship (sample); STF4b NPB20 nativity iterated by WNH/BNH (all ages,
   18|         adult share [I]); FB sex split from 2000 [I].
   19|   2000  SF4 PCT044B/C sex x 18+ x nativity / citizenship iterated all / WNH / BNH (sample),
   20|         raked to SF1 P5 (NP005A) 18+ totals.
   21|   2008  ACS 2006-2010 5-year; 2010, 2012, 2016, 2024 ACS 1-year; 2020 ACS 2016-2020
   22|         5-year: B05003 (+H white alone NH, +B Black alone). Black NH native = Black alone
   23|         native x NH share of Black alone in B03002 (all ages) [I]. 2010 and 2020 raked to
   24|         PL 94-171 18+ state totals.
   25| Every row's `note` says "tabulated" or what was [I]-estimated.
   26| """
   27| import argparse
   28| import re
   29| from pathlib import Path
   30| 
   31| import pandas as pd
   32| 
   33| from nhgis_common import CACHE, NHGIS_DIR, STATE_CODE, frame, row
   34| 
   35| EXTRACT = None  # set by CLI or found automatically
   36| 
   37| 
   38| def src() -> Path:
   39|     global EXTRACT
   40|     if EXTRACT is None:
   41|         reqs = sorted(NHGIS_DIR.glob('extract_request_*_modern.json'), key=lambda p: int(p.name.split('_')[2]))
   42|         EXTRACT = int(reqs[-1].name.split('_')[2])
   43|     d = NHGIS_DIR / f'extract_{EXTRACT}'
   44|     return next(p for p in d.iterdir() if p.is_dir() and p.name.endswith('_csv'))
   45| 
   46| 
   47| _CACHE = {}
   48| FILE_OF = {}       # dataset name -> csv path
   49| TABLE_PREFIX = {}  # (dataset, source table code) -> NHGIS column prefix
   50| 
   51| 
   52| def load_prefixes():
   53|     """Every codebook names its dataset ('Dataset: ... NHGIS code: 2024_ACS1') and, per table,
   54|     'Source code: B05003 / NHGIS code: ATMV' (the column prefix)."""
   55|     if FILE_OF:
   56|         return
   57|     for cb in src().glob('*_codebook.txt'):
   58|         t = cb.read_text(encoding='latin-1')
   59|         ds = re.search(r'Dataset:.*\n\s*NHGIS code:\s*(\S+)', t).group(1)
   60|         FILE_OF[ds] = cb.with_name(cb.name.replace('_codebook.txt', '.csv'))
   61|         for m in re.finditer(r'Source code:\s*(\S+)\s*\n\s*NHGIS code:\s*(\S+)', t):
   62|             TABLE_PREFIX[(ds, m.group(1))] = m.group(2)
   63| 
   64| 
   65| def read(ds: str) -> tuple:
   66|     """Return (df indexed by state with code columns, {code: description})."""
   67|     if ds in _CACHE:
   68|         return _CACHE[ds]
   69|     load_prefixes()
   70|     raw = pd.read_csv(FILE_OF[ds], encoding='latin-1', header=None, low_memory=False, dtype=str)
   71|     codes, descs = list(raw.iloc[0]), list(raw.iloc[1])
   72|     d = raw.iloc[2:].copy()
   73|     d.columns = codes
   74|     d = d[d.STATE.str.casefold().isin(STATE_CODE)].copy()
   75|     d['state'] = d.STATE.str.casefold().map(STATE_CODE)
   76|     d = d.set_index('state')
   77|     desc = {c: str(x) for c, x in zip(codes, descs)}
   78|     ctx = {'GISJOIN', 'YEAR', 'STATE', 'STATEA', 'AREANAME', 'NAME_E', 'NAME_M', 'GEOID', 'STUSAB', 'REGIONA', 'DIVISIONA',
   79|            'state'}
   80|     for c in codes:
   81|         if c not in ctx:
   82|             d[c] = pd.to_numeric(d[c], errors='coerce')
   83|     _CACHE[ds] = (d, desc)
   84|     return _CACHE[ds]
   85| 
   86| 
   87| def cols(desc: dict, *pats, table=None) -> list:
   88|     """Codes whose description matches every regex in pats (and the table code prefix if given)."""
   89|     out = []
   90|     for c, s in desc.items():
   91|         if table and not str(c).startswith(table):
   92|             continue
   93|         if all(re.search(p, s) for p in pats):
   94|             out.append(c)
   95|     return out
   96| 
   97| 
   98| def is_adult(label: str) -> bool:
   99|     for part in re.split(r'>>|:', label):
  100|         p = part.strip()
  101|         if p.startswith('Under'):
  102|             return False
  103|         m = re.match(r'(\d+)', p)
  104|         if m and ('year' in p or re.fullmatch(r'\d+( to \d+| and \d+)?( years)?( and over)?', p)):
  105|             return int(m.group(1)) >= 18
  106|     raise ValueError(f'no age in {label!r}')
  107| 
  108| 
  109| LABEL = {'white_nh_native': 'White alone/White, not Hispanic, native-born',
  110|          'black_nh_native': 'Black alone/Black, not Hispanic, native-born',
  111|          'other_native': 'Native-born, all other (Hispanic any race, Asian, AIAN, other, multiracial)',
  112|          'naturalized': 'Foreign-born, naturalized citizen', 'noncitizen': 'Foreign-born, not a citizen'}
  113| 
  114| 
  115| def emit(year, parts: dict, tables: dict, notes: dict):
  116|     """parts: {(sex, group): Series by state}"""
  117|     df = frame([row(year, st, sex, g, LABEL[g].split(',')[0], LABEL[g], round(float(v), 1), notes.get(g, 'tabulated'),
  118|                     tables[g]) for (sex, g), s in parts.items() for st, v in s.items()])
  119|     assert df.state.nunique() == 51, df.state.nunique()
  120|     assert (df['count'] >= 0).all(), df[df['count'] < 0]
  121|     return df
  122| 
  123| 
  124| def check(year, df, indep: pd.Series, what: str):
  125|     tot = df.groupby('state')['count'].sum()
  126|     gap = (tot - indep.reindex(tot.index)) / indep.reindex(tot.index)
  127|     print(f'{year}: groups {tot.sum():,.0f} vs {what} {indep.sum():,.0f} (national {100 * (tot.sum() / indep.sum() - 1):+.2f}%; '
  128|           f'worst state {gap.abs().idxmax()} {100 * gap.abs().max():.2f}%)')
  129| 
  130| 
  131| def split_native(native, wnn, bnn):
  132|     """other_native = remainder; if WNH+BNH native exceed the sample-based native total, shrink them."""
  133|     over = (wnn + bnn) / native
  134|     k = over.clip(lower=1.0)
  135|     return wnn / k, bnn / k, native - (wnn + bnn) / k
  136| 
  137| 
  138| # ------------------------------------------------------------------- helpers per table
  139| def pick(d, desc, prefix, *pats):
  140|     """Sum of the columns of one table whose description matches every regex."""
  141|     cs = cols(desc, *pats, table=prefix)
  142|     assert cs, (prefix, pats)
  143|     return d[cs].sum(axis=1)
  144| 
  145| 
  146| def adult_sum(d, desc, prefix, *pats):
  147|     cs = [c for c in cols(desc, *pats, table=prefix) if is_adult(desc[c])]
  148|     assert cs, (prefix, pats)
  149|     return d[cs].sum(axis=1)
  150| 
  151| 
  152| def fb_sex_shares_2000():
  153|     """Male share of foreign-born adults by citizenship, by state (SF4 PCT044C, all races)."""
  154|     d, desc = read('2000_SF4')
  155|     p = TABLE_PREFIX[('2000_SF4', 'NPCT044C')]
  156|     out = {}
  157|     for k, pat in (('nat', r'Naturalized citizen$'), ('nc', r'Not a citizen$')):
  158|         m = pick(d, desc, p, r'^Total area: All races: Male >> 18 years and over', pat)
  159|         f = pick(d, desc, p, r'^Total area: All races: Female >> 18 years and over', pat)
  160|         out[k] = m / (m + f)
  161|     return out
  162| 
  163| 
  164| def adult_share_1990():
  165|     """Share of the foreign born who are 18+, by citizenship (1990 STF3 NP37)."""
  166|     d, desc = read('1990_STF3')
  167|     p = TABLE_PREFIX[('1990_STF3', 'NP37')]
  168|     g = lambda *pats: pick(d, desc, p, *pats)  # noqa: E731
  169|     nat18, nc18 = g(r'^18 years and over', 'Naturalized'), g(r'^18 years and over', 'Not a citizen')
  170|     nat, nc = nat18 + g(r'^Under 18', 'Naturalized'), nc18 + g(r'^Under 18', 'Not a citizen')
  171|     return nat18 / nat, nc18 / nc, nat18, nc18, g(r'^18 years and over', r'Native$')
  172| 
  173| 
  174| def assemble(year, by_sex, tables, notes):
  175|     parts = {}
  176|     for sex, (nat18, nz, nc, wnn, bnn) in by_sex.items():
  177|         wnn, bnn, onn = split_native(nat18, wnn.clip(lower=0), bnn.clip(lower=0))
  178|         parts.update({(sex, 'white_nh_native'): wnn, (sex, 'black_nh_native'): bnn, (sex, 'other_native'): onn,
  179|                       (sex, 'naturalized'): nz, (sex, 'noncitizen'): nc})
  180|     return emit(year, parts, tables, notes)
  181| 
  182| 
  183| def rake(df, tot, what):
  184|     cur = df.groupby('state')['count'].sum()
  185|     k = tot.reindex(cur.index) / cur
  186|     print(f'  rake to {what}: state factors {k.min():.4f}-{k.max():.4f}')
  187|     df = df.copy()
  188|     df['count'] = (df['count'] * df.state.map(k)).round(1)
  189|     df['note'] = df['note'] + df.state.map(lambda s: f'; raked x{k[s]:.4f} to {what}')
  190|     return df
  191| 
  192| 
  193| # ------------------------------------------------------------------- ACS years
  194| ACS = {2008: ('2006_2010_ACS5b', '2006_2010_ACS5a', 'ACS 2006-2010 5-year'),
  195|        2010: ('2010_ACS1', '2010_ACS1', 'ACS 2010 1-year'),
  196|        2012: ('2012_ACS1', '2012_ACS1', 'ACS 2012 1-year'),
  197|        2016: ('2016_ACS1', '2016_ACS1', 'ACS 2016 1-year'),
  198|        2020: ('2016_2020_ACS5b', '2016_2020_ACS5a', 'ACS 2016-2020 5-year'),
  199|        2024: ('2024_ACS1', '2024_ACS1', 'ACS 2024 1-year')}
  200| 
  201| 
  202| def black_ratio_2020(word):
  203|     """2016-2020 ACS5: Black NH native 18+ of one sex / Black NH all ages, by state."""
  204|     d, desc = read('2016_2020_ACS5b')
  205|     da, desca = read('2016_2020_ACS5a')
  206|     p3 = TABLE_PREFIX[('2016_2020_ACS5a', 'B03002')]
  207|     bnh = pick(da, desca, p3, r'^Estimates: Not Hispanic or Latino: Black or African American alone$')
  208|     bh = pick(da, desca, p3, r'^Estimates: Hispanic or Latino: Black or African American alone$')
  209|     nat = pick(d, desc, TABLE_PREFIX[('2016_2020_ACS5b', 'B05003B')], rf'^Estimates: {word}: 18 years and over: Native$')
  210|     return nat * bnh / (bnh + bh) / bnh
  211| 
  212| 
  213| def year_acs(year):
  214|     dsb, dsa, label = ACS[year]
  215|     d, desc = read(dsb)
  216|     da, desca = read(dsa)
  217|     P = lambda ds, t: TABLE_PREFIX[(ds, t)]  # noqa: E731
  218|     p3 = P(dsa, 'B03002')
  219|     bnh = pick(da, desca, p3, r'^Estimates: Not Hispanic or Latino: Black or African American alone$')
  220|     bh = pick(da, desca, p3, r'^Estimates: Hispanic or Latino: Black or African American alone$')
  221|     r_bnh = bnh / (bnh + bh)
  222|     # 1-year B05003B is suppressed in a few small-Black-population states (MT, WY, ...): there,
  223|     # Black NH native 18+ = this year's Black NH (all ages, B03002) x the 2016-2020 5-year ratio [I]
  224|     pb = P(dsb, 'B05003B')
  225|     supp = d[[c for c in desc if str(c).startswith(pb + 'E')]].isna().any(axis=1)
  226|     supp = list(supp[supp].index)
  227|     by_sex = {}
  228|     for sex, word in (('M', 'Male'), ('F', 'Female')):
  229|         g = lambda t, pat: pick(d, desc, P(dsb, t), rf'^Estimates: {word}: 18 years and over: {pat}')  # noqa: E731
  230|         bnn = g('B05003B', r'Native$') * r_bnh
  231|         if supp:
  232|             bnn[supp] = (bnh * black_ratio_2020(word))[supp]
  233|         by_sex[sex] = (g('B05003', r'Native$'), g('B05003', r'Foreign.born: Naturalized'), g('B05003', r'Foreign.born: Not a U\.S\. citizen'),
  234|                        g('B05003H', r'Native$'), bnn)
  235|     b01 = adult_sum(da, desca, P(dsa, 'B01001'), r'^Estimates: (Male|Female): ')
  236|     tables = {'white_nh_native': f'NHGIS {dsb} B05003H', 'black_nh_native': f'NHGIS {dsb} B05003B x {dsa} B03002',
  237|               'other_native': f'NHGIS {dsb} B05003 - B05003H - B05003B', 'naturalized': f'NHGIS {dsb} B05003',
  238|               'noncitizen': f'NHGIS {dsb} B05003'}
  239|     notes = {'black_nh_native': f'[I] Black alone native 18+ x NH share of Black alone (B03002, all ages); {label}',
  240|              'other_native': f'remainder: B05003 native 18+ minus white NH and Black NH native; {label}',
  241|              'white_nh_native': f'tabulated; {label}', 'naturalized': f'tabulated; {label}', 'noncitizen': f'tabulated; {label}'}
  242|     df = assemble(year, by_sex, tables, notes)
  243|     m = df.state.isin(supp) & (df.group == 'black_nh_native')
  244|     df.loc[m, 'note'] = f'[I] B05003B suppressed: Black NH all ages (B03002) x 2016-2020 ACS5 ratio of Black NH native 18+ to Black NH; {label}'
  245|     check(year, df, b01, f'{dsa} B01001 18+')
  246|     if year in (2010, 2020):
  247|         ds = f'{year}_PL94171'
  248|         dp, descp = read(ds)
  249|         tot = pick(dp, descp, TABLE_PREFIX[(ds, 'P3' if year == 2020 else 'NP003')], r'^Total$')
  250|         check(year, df, tot, 'PL 94-171 18+ (before rake)')
  251|         df = rake(df, tot, f'PL 94-171 {year} 18+ state total')
  252|     return df
  253| 
  254| 
  255| # ------------------------------------------------------------------- 2000
  256| def year_2000(year=2000):
  257|     d, desc = read('2000_SF4')
  258|     pn, pc = TABLE_PREFIX[('2000_SF4', 'NPCT044B')], TABLE_PREFIX[('2000_SF4', 'NPCT044C')]
  259|     it = {'all': 'All races', 'w': 'White alone, not Hispanic or Latino', 'b': 'Black or African American alone, not Hispanic or Latino'}
  260|     by_sex = {}
  261|     for sex, word in (('M', 'Male'), ('F', 'Female')):
  262|         g = lambda p, i, pat: pick(d, desc, p, rf'^Total area: {re.escape(it[i])}: {word} >> 18 years and over >> {pat}$')  # noqa: E731
  263|         by_sex[sex] = (g(pn, 'all', 'Native'), g(pc, 'all', 'Naturalized citizen'), g(pc, 'all', 'Not a citizen'),
  264|                        g(pn, 'w', 'Native'), g(pn, 'b', 'Native'))
  265|     tables = {'white_nh_native': 'NHGIS 2000_SF4 PCT44B (White alone, not Hispanic)',
  266|               'black_nh_native': 'NHGIS 2000_SF4 PCT44B (Black alone, not Hispanic)',
  267|               'other_native': 'NHGIS 2000_SF4 PCT44B (all - WNH - BNH)', 'naturalized': 'NHGIS 2000_SF4 PCT44C',
  268|               'noncitizen': 'NHGIS 2000_SF4 PCT44C'}
  269|     notes = {'other_native': 'remainder: native 18+ minus white NH and Black NH native (SF4 sample)'}
  270|     df = assemble(2000, by_sex, tables, {g: notes.get(g, 'tabulated (SF4 sample)') for g in LABEL})
  271|     ds, dsc = read('2000_SF1a')
  272|     tot = pick(ds, dsc, TABLE_PREFIX[('2000_SF1a', 'NP005A')], r'^Total$')
  273|     check(2000, df, tot, 'SF1 P5 18+ (before rake)')
  274|     return rake(df, tot, 'SF1 P5 2000 18+ state total (100% count)')
  275| 
  276| 
  277| # ------------------------------------------------------------------- 1990
  278| def year_1990(year=1990):
  279|     r_nat, r_nc, nat18, nc18, nat_s = adult_share_1990()
  280|     fb_a = (nat18 + nc18) / (nat18 / r_nat + nc18 / r_nc)
  281|     msh = fb_sex_shares_2000()
  282|     dm, descm = read('1990_MARS')
  283|     pm = TABLE_PREFIX[('1990_MARS', 'NP1')]
  284|     d4, desc4 = read('1990_STF4b')
  285|     p4 = TABLE_PREFIX[('1990_STF4b', 'NPB20')]
  286|     fb = lambda it: pick(d4, desc4, p4, rf'^Total area: {re.escape(it)}: Foreign born')  # noqa: E731
  287|     fbw, fbb = fb('White, not of Hispanic origin') * fb_a, fb('Black, not of Hispanic origin') * fb_a
  288|     # 1990 STF1 NP13 is Hispanic-only; the 100%-based 18+ by sex comes from MARS (all races, both origins)
  289|     tot100 = {s: adult_sum(dm, descm, pm, rf'>> {w} >>') for s, w in (('M', 'Male'), ('F', 'Female'))}
  290|     sample = nat_s + nat18 + nc18
  291|     k = (tot100['M'] + tot100['F']) / sample  # sample -> 100% count
  292|     by_sex = {}
  293|     for sex, word in (('M', 'Male'), ('F', 'Female')):
  294|         ms = (lambda x: x) if sex == 'M' else (lambda x: 1 - x)
  295|         nz, nc = nat18 * k * ms(msh['nat']), nc18 * k * ms(msh['nc'])
  296|         fbsh = (nz + nc) / (nat18 * k + nc18 * k)
  297|         wnh = adult_sum(dm, descm, pm, rf'>> Not Hispanic >> {word} >> White$')
  298|         bnh = adult_sum(dm, descm, pm, rf'>> Not Hispanic >> {word} >> Black$')
  299|         by_sex[sex] = (tot100[sex] - nz - nc, nz, nc, wnh - fbw * k * fbsh, bnh - fbb * k * fbsh)
  300|     tables = {'white_nh_native': 'NHGIS 1990_MARS NP1 - 1990_STF4b NPB20 (White, not Hispanic) FB',
  301|               'black_nh_native': 'NHGIS 1990_MARS NP1 - 1990_STF4b NPB20 (Black, not Hispanic) FB',
  302|               'other_native': 'NHGIS 1990_MARS NP1 18+ - FB - WNH - BNH native', 'naturalized': 'NHGIS 1990_STF3 NP37',
  303|               'noncitizen': 'NHGIS 1990_STF3 NP37'}
  304|     notes = {'white_nh_native': '[I] MARS white NH 18+ minus WNH foreign born (all ages x FB adult share, NP37) x FB sex share (2000)',
  305|              'black_nh_native': '[I] MARS Black NH 18+ minus BNH foreign born (all ages x FB adult share, NP37) x FB sex share (2000)',
  306|              'other_native': '[I] remainder of 100%-based 18+ (MARS NP1)',
  307|              'naturalized': '[I] STF3 NP37 18+ (sample, scaled to 100% count); sex split from 2000 SF4 PCT44C',
  308|              'noncitizen': '[I] STF3 NP37 18+ (sample, scaled to 100% count); sex split from 2000 SF4 PCT44C'}
  309|     df = assemble(1990, by_sex, tables, notes)
  310|     check(1990, df, sample, 'STF3 NP37 18+ (sample, independent)')
  311|     print(f'  national 18+ {df["count"].sum():,.0f} vs published 1990 census 18+ 185,105,441 '
  312|           f'({100 * (df["count"].sum() / 185105441 - 1):+.3f}%)')
  313|     return df
  314| 
  315| 
  316| # ------------------------------------------------------------------- 1980
  317| def year_1980(year=1980):
  318|     r_nat, r_nc, *_ = adult_share_1990()
  319|     msh = fb_sex_shares_2000()
  320|     d2, desc2 = read('1980_STF2b')
  321|     p2 = TABLE_PREFIX[('1980_STF2b', 'NTB8B')]
  322|     d4, desc4 = read('1980_STF4Pb')
  323|     p4 = TABLE_PREFIX[('1980_STF4Pb', 'NTPB9')]
  324|     da, desca = read('1980_STF2a')
  325|     pa = TABLE_PREFIX[('1980_STF2a', 'NTA13')]
  326|     d1, desc1 = read('1980_STF1')
  327|     p1 = TABLE_PREFIX[('1980_STF1', 'NT10B')]
  328|     g4 = lambda it, pat: pick(d4, desc4, p4, rf'^Total area: {re.escape(it)}: {pat}')  # noqa: E731
  329|     nat_all, nc_all = g4('All races', 'Foreign born: Naturalized'), g4('All races', 'Foreign born: Not a citizen')
  330|     sample_all = nat_all + nc_all + g4('All races', 'Native')
  331|     nat18, nc18 = nat_all * r_nat, nc_all * r_nc
  332|     fb_a = (nat18 + nc18) / (nat_all + nc_all)
  333|     sp_fb = g4('Spanish origin subtotal (subtotal of summaries 20-23)', 'Foreign born')
  334|     sp = da[[c for c in desca if str(c).startswith(pa) and desca[c].startswith('Spanish origin')]].sum(axis=1)
  335|     sp_w = pick(da, desca, pa, r'^Spanish origin >> White$') / sp
  336|     sp_b = pick(da, desca, pa, r'^Spanish origin >> Black$') / sp
  337|     fbw = (g4('White', 'Foreign born') - sp_fb * sp_w).clip(lower=0) * fb_a
  338|     fbb = (g4('Black', 'Foreign born') - sp_fb * sp_b).clip(lower=0) * fb_a
  339|     it = lambda s: re.escape(s)  # noqa: E731
  340|     by_sex, tot100 = {}, {}
  341|     for sex, word in (('M', 'Male'), ('F', 'Female')):
  342|         a = lambda iname: adult_sum(d2, desc2, p2, rf'^Total area: {it(iname)}: {word} >>')  # noqa: E731
  343|         tot100[sex] = a('All races')
  344|         ms = (lambda x: x) if sex == 'M' else (lambda x: 1 - x)
  345|         # the sample nativity table is all ages; scale its FB counts to the 100% count
  346|         k = d2[cols(desc2, r'^Total area: All races: ', table=p2)].sum(axis=1) / sample_all
  347|         nz, nc = nat18 * k * ms(msh['nat']), nc18 * k * ms(msh['nc'])
  348|         fbsh = (nz + nc) / ((nat18 + nc18) * k)
  349|         wnh = a('White not of Spanish origin (on STF4B; not available for MCD\'s or CCD\'s under 2500')
  350|         bnh = a('Black not of Spanish origin (on STF4B; not available for MCD\'s or CCD\'s under 2500')
  351|         by_sex[sex] = (tot100[sex] - nz - nc, nz, nc, wnh - fbw * k * fbsh, bnh - fbb * k * fbsh)
  352|     tables = {'white_nh_native': 'NHGIS 1980_STF2b NTB8B (White not of Spanish origin) - 1980_STF4Pb NTPB9 FB',
  353|               'black_nh_native': 'NHGIS 1980_STF2b NTB8B (Black not of Spanish origin) - 1980_STF4Pb NTPB9 FB',
  354|               'other_native': 'NHGIS 1980_STF2b NTB8B - FB - WNH - BNH native', 'naturalized': 'NHGIS 1980_STF4Pb NTPB9',
  355|               'noncitizen': 'NHGIS 1980_STF4Pb NTPB9'}
  356|     fbnote = 'FB all ages (STF4Pb, net of Spanish-origin FB by the state Spanish race mix, STF2a NTA13) x FB adult share (1990 NP37) x FB sex share (2000)'
  357|     notes = {'white_nh_native': f'[I] 100% white not Spanish 18+ minus {fbnote}',
  358|              'black_nh_native': f'[I] 100% Black not Spanish 18+ minus {fbnote}',
  359|              'other_native': '[I] remainder of 100%-count 18+ (STF2b NTB8B)',
  360|              'naturalized': '[I] STF4Pb all-ages naturalized x 1990 adult share (NP37), scaled to 100% count; sex split from 2000',
  361|              'noncitizen': '[I] STF4Pb all-ages noncitizens x 1990 adult share (NP37), scaled to 100% count; sex split from 2000'}
  362|     df = assemble(1980, by_sex, tables, notes)
  363|     indep = adult_sum(d1, desc1, p1, r'^(Male|Female) >>')
  364|     check(1980, df, indep, 'STF1 NT10B 18+ (100%)')
  365|     return df
  366| 
  367| 
  368| BUILDERS = {y: year_acs for y in ACS}
  369| BUILDERS.update({1980: year_1980, 1990: year_1990, 2000: year_2000})
  370| 
  371| if __name__ == '__main__':
  372|     ap = argparse.ArgumentParser()
  373|     ap.add_argument('year')
  374|     ap.add_argument('--extract', type=int)
  375|     a = ap.parse_args()
  376|     if a.extract:
  377|         EXTRACT = a.extract
  378|     years = sorted(BUILDERS) if a.year == 'all' else [int(a.year)]
  379|     for y in years:
  380|         df = BUILDERS[y](y)
  381|         out = CACHE / f'population/adults18_{y}_by_state_nhgis.csv'
  382|         df.to_csv(out, index=False)
  383|         g = df.groupby('group')['count'].sum()
  384|         print(f'wrote {out.name}: {len(df)} rows, {df["count"].sum():,.0f} adults 18+ | '
  385|               + ', '.join(f'{k} {v / 1e6:.1f}M' for k, v in g.items()))
```

## `scripts/harness/build_population_republic.py`

```python
    1| """1790–1860 censuses → population/adults_<year>_by_state_nhgis.csv (same long
    2| format as build_population.py). build_population.py uses BUILDERS too:
    3| 
    4|     python3 scripts/harness/build_population_republic.py [YEAR ...]   # default: every census 1790–1860
    5|     python3 scripts/harness/build_population.py 1830
    6| 
    7| Source: NHGIS extract made by scripts/harness/nhgis_extract_republic.py (state tables;
    8| see TABLES there). Groups: white, free_colored, enslaved (1790–1840);
    9| native_white, foreign_white_unknown, free_colored, enslaved, other_races
   10| (1850–1860; foreign-born citizenship is not tabulated, hence "_unknown").
   11| 
   12| None of these censuses tabulates age 21 exactly, so every adult count is an
   13| [I] estimate from the age bands (note column says which). Band splits use a
   14| stationary-growth age profile: each single-year cohort is W=0.97 the size of
   15| the one a year younger (≈3% annual growth, early-republic rate), so the share
   16| of a band [a, b] aged ≥21 is sum_{21..b} W^x / sum_{a..b} W^x.
   17| """
   18| import sys
   19| from pathlib import Path
   20| 
   21| import pandas as pd
   22| 
   23| from nhgis_common import CACHE, NHGIS_DIR, STATE_CODE, frame, load, row
   24| 
   25| W = 0.97
   26| # Territories / predecessor areas → the state they became (state code). Dakota is ambiguous → dropped.
   27| AREA = {'southwest territory': 'TN', 'northwest territory': 'OH', 'orleans territory': 'LA',
   28|         'louisiana territory': 'MO', 'district of columbia': 'DC'}
   29| DS = {1790: 'ds1', 1800: 'ds2', 1810: 'ds3', 1820: 'ds4', 1830: 'ds5', 1840: 'ds7', 1850: 'ds10', 1860: 'ds14'}
   30| FOREIGN_ADULT = {'M': 0.72, 'F': 0.70}  # [I] share of foreign-born whites aged 21+ (immigrants are adult-heavy)
   31| 
   32| 
   33| def adult_share(a: int, b: int) -> float:
   34|     """Share of the band [a, b] aged 21+, under the W age profile."""
   35|     ages = range(a, b + 1)
   36|     return sum(W ** x for x in ages if x >= 21) / sum(W ** x for x in ages)
   37| 
   38| 
   39| def src_dir() -> Path:
   40|     hits = sorted(NHGIS_DIR.glob('extract_*/nhgis*_csv/nhgis*_ds1_1790_state.csv'))
   41|     if not hits:
   42|         raise SystemExit('no 1790–1860 NHGIS extract: run scripts/harness/nhgis_extract_republic.py submit / wait N')
   43|     return hits[-1].parent
   44| 
   45| 
   46| def code_of(name: str):
   47|     n = name.casefold().strip()
   48|     if n in AREA:
   49|         return AREA[n]
   50|     n = n.replace(' territory', '')
   51|     return STATE_CODE.get(n)
   52| 
   53| 
   54| def read(ds: str) -> pd.DataFrame:
   55|     d = load(ds, src_dir(), 'nhgis*_{ds}_*_state.csv')
   56|     d.index = d.STATE.map(code_of).rename('state')  # not a new column: the 1850/1860 tables are too wide to insert into
   57|     return d[d.index.notna()]
   58| 
   59| 
   60| RACE = {'white': 'White', 'native_white': 'White', 'foreign_white_unknown': 'White', 'free_colored': 'Free colored',
   61|         'enslaved': 'Slave', 'other_races': 'Other'}
   62| 
   63| 
   64| def emit(year, cells, table):
   65|     """cells: {(state, sex, group): (count, note, label)}"""
   66|     return frame([row(year, st, sex, g, RACE[g], label, round(float(c), 1), note, table)
   67|                   for (st, sex, g), (c, note, label) in cells.items()])
   68| 
   69| 
   70| # ---------------------------------------------------------------- per-census adult counts
   71| def white_1800_1820(year):
   72|     """Free white males/females 16–25, 26–44, 45+ (1820 men also 16–18)."""
   73|     d = read(DS[year])
   74|     p = {1800: 'AAX', 1810: 'AA6', 1820: 'ABG'}[year]
   75|     res = {}
   76|     for st, r in d.iterrows():
   77|         for sex, off in (('M', 0), ('F', 5)):
   78|             b1625, b2644, b45 = (r[f'{p}{off + i:03d}'] for i in (3, 4, 5))
   79|             if year == 1820 and sex == 'M':
   80|                 b1925 = b1625 - r['ABH001']
   81|                 n = adult_share(19, 25) * b1925 + b2644 + b45
   82|                 note = f'[I] 21+ = {adult_share(19, 25):.3f}×(16–25 less 16–18) + 26–44 + 45+'
   83|             else:
   84|                 n = adult_share(16, 25) * b1625 + b2644 + b45
   85|                 note = f'[I] 21+ = {adult_share(16, 25):.3f}×(16–25) + 26–44 + 45+'
   86|             res[(st, sex, 'white')] = (n, note, f'Free white {"males" if sex == "M" else "females"} 16–25/26–44/45+')
   87|     return d, res
   88| 
   89| 
   90| def colored_1820():
   91|     """Slave / free colored by sex: <14, 14–25, 26–44, 45+ (ABK001–016)."""
   92|     d = read('ds4')
   93|     res = {}
   94|     f = adult_share(14, 25)
   95|     for st, r in d.iterrows():
   96|         for g, base in (('enslaved', 0), ('free_colored', 8)):
   97|             for sex, off in (('M', 0), ('F', 4)):
   98|                 c = lambda i: r[f'ABK{base + off + i:03d}']  # noqa: E731
   99|                 res[(st, sex, g)] = (f * c(2) + c(3) + c(4), f'[I] 21+ = {f:.3f}×(14–25) + 26–44 + 45+',
  100|                                      f'{"Slave" if g == "enslaved" else "Free colored"} {sex} 14–25/26–44/45+')
  101|     return d, res
  102| 
  103| 
  104| def colored_ratios():
  105|     """Per state: adults-by-sex / group total in 1820, the template for 1790–1810."""
  106|     d, res = colored_1820()
  107|     tot = {'enslaved': d[[f'ABK{i:03d}' for i in range(1, 9)]].sum(axis=1),
  108|            'free_colored': d[[f'ABK{i:03d}' for i in range(9, 17)]].sum(axis=1)}
  109|     nat = {(sex, g): sum(res[(s, sex, g)][0] for s in d.index) / tot[g].sum() for sex in 'MF' for g in tot}
  110|     rat = {}
  111|     for st in d.index:
  112|         for g in tot:
  113|             for sex in 'MF':
  114|                 rat[(st, sex, g)] = res[(st, sex, g)][0] / tot[g][st] if tot[g][st] > 200 else nat[(sex, g)]
  115|     return rat, nat
  116| 
  117| 
  118| def colored_from_totals(year, d, free_col, slave_col, rat, nat):
  119|     res = {}
  120|     for st, r in d.iterrows():
  121|         for g, col in (('free_colored', free_col), ('enslaved', slave_col)):
  122|             for sex in 'MF':
  123|                 k = rat.get((st, sex, g))
  124|                 src = '1820 same-state' if k is not None else '1820 national'
  125|                 k = k if k is not None else nat[(sex, g)]
  126|                 res[(st, sex, g)] = (r[col] * k, f'[I] {g} total ({col}) × {src} share {sex} 21+ ({k:.3f}); no sex/age in {year}',
  127|                                      f'{"Free nonwhite" if g == "free_colored" else "Slave"} (total, sex/age not tabulated)')
  128|     return res
  129| 
  130| 
  131| def y1790(year=1790):
  132|     d = read('ds1')
  133|     d00, w00 = white_1800_1820(1800)
  134|     rat, nat = colored_ratios()
  135|     res = {}
  136|     for st, r in d.iterrows():
  137|         for sex, col in (('M', 'AAO002'), ('F', 'AAO004')):
  138|             off = 0 if sex == 'M' else 5
  139|             if st in d00.index:
  140|                 b = d00.loc[st]
  141|                 k = w00[(st, sex, 'white')][0] / sum(b[f'AAX{off + i:03d}'] for i in (3, 4, 5))
  142|                 src = '1800 same-state'
  143|             else:
  144|                 k = adult_share(16, 25) * 0.30 + 0.70
  145|                 src = 'default'
  146|             res[(st, sex, 'white')] = (r[col] * k, f'[I] white {sex} 16+ ({col}{", NHGIS-estimated" if sex == "F" else ""}) × {src} 21+/16+ ratio ({k:.3f})',
  147|                                        f'White {"males" if sex == "M" else "females (estimated)"} 16 and over')
  148|     res.update(colored_from_totals(1790, d, 'AAQ001', 'AAQ002', rat, nat))
  149|     return emit(1790, res, 'NHGIS 1790_cPop NT4, NT6')
  150| 
  151| 
  152| def y1800_1810(year):
  153|     d, res = white_1800_1820(year)
  154|     rat, nat = colored_ratios()
  155|     free_col, slave_col = {1800: ('AAY001', 'AAY002'), 1810: ('AA7001', 'AA7002')}[year]
  156|     res.update(colored_from_totals(year, d, free_col, slave_col, rat, nat))
  157|     return emit(year, res, f'NHGIS {year}_cPop NT5, NT6')
  158| 
  159| 
  160| def y1820(year=1820):
  161|     _, res = white_1800_1820(1820)
  162|     _, col = colored_1820()
  163|     res.update(col)
  164|     return emit(1820, res, 'NHGIS 1820_cPop NT4A, NT4B, NT7')
  165| 
  166| 
  167| def y1830_1840(year):
  168|     d = read(DS[year])
  169|     wp, cp = {1830: ('ABW', 'ABX'), 1840: ('ACY', 'ACZ')}[year]
  170|     fw, fc = adult_share(20, 29), adult_share(10, 23)
  171|     # colored block order: 1830 slave then free; 1840 free then slave
  172|     blocks = {1830: (('enslaved', 0), ('free_colored', 12)), 1840: (('free_colored', 0), ('enslaved', 12))}[year]
  173|     res = {}
  174|     for st, r in d.iterrows():
  175|         for sex, off in (('M', 0), ('F', 13)):
  176|             w = lambda i: r[f'{wp}{off + i:03d}']  # noqa: E731
  177|             res[(st, sex, 'white')] = (fw * w(5) + sum(w(i) for i in range(6, 14)),
  178|                                        f'[I] 21+ = {fw:.3f}×(20–29) + 30+', f'Free white {sex} 20–29 and 30+ bands')
  179|         for g, base in blocks:
  180|             for sex, off in (('M', 0), ('F', 6)):
  181|                 c = lambda i: r[f'{cp}{base + off + i:03d}']  # noqa: E731
  182|                 res[(st, sex, g)] = (fc * c(2) + sum(c(i) for i in range(3, 7)),
  183|                                      f'[I] 21+ = {fc:.3f}×(10–23) + 24+', f'{g} {sex} 10–23 and 24+ bands')
  184|     t = {1830: 'NHGIS 1830_cPop NT4, NT5', 1840: 'NHGIS 1840_cPopX NT4, NT5'}[year]
  185|     return emit(year, res, t)
  186| 
  187| 
  188| def adults_1850_1860(year):
  189|     """→ {(st, sex, group): (count, note, label)} for white / free_colored / enslaved / other_races."""
  190|     d = read(DS[year])
  191|     f = adult_share(20, 29)
  192|     res = {}
  193|     if year == 1850:
  194|         # AEL: 3 race blocks × 2 sexes × 15 cells (<1,1–4,5–9,10–14,15–19,20–29,…,100+,unknown)
  195|         layout = [('white', 0), ('free_colored', 30), ('enslaved', 60)]
  196|         for st, r in d.iterrows():
  197|             for g, base in layout:
  198|                 for sex, off in (('M', 0), ('F', 15)):
  199|                     c = [r[f'AEL{base + off + i:03d}'] for i in range(1, 16)]
  200|                     known = sum(c[:14])
  201|                     ad = f * c[5] + sum(c[6:14])
  202|                     ad += c[14] * (ad / known if known else 0)
  203|                     res[(st, sex, g)] = (ad, f'[I] 21+ = {f:.3f}×(20–29) + 30+, age-unknown allocated pro rata',
  204|                                          f'{g} {sex} by age (NT4)')
  205|     else:
  206|         # AH0: 6 races × 15 age cells × 2 sexes, sex innermost
  207|         races = [('white', 0), ('free_colored', 30), ('enslaved', 60), ('other_races', 90), ('other_races', 120), ('other_races', 150)]
  208|         for st, r in d.iterrows():
  209|             for g, base in races:
  210|                 for sex, s in (('M', 1), ('F', 2)):
  211|                     c = [r[f'AH0{base + 2 * i + s:03d}'] for i in range(15)]
  212|                     known = sum(c[:14])
  213|                     ad = f * c[5] + sum(c[6:14])
  214|                     ad += c[14] * (ad / known if known else 0)
  215|                     k = (st, sex, g)
  216|                     prev = res.get(k, (0, '', ''))[0]
  217|                     res[k] = (prev + ad, f'[I] 21+ = {f:.3f}×(20–29) + 30+, age-unknown allocated pro rata'
  218|                               + ('; Indian + half breed + Asiatic' if g == 'other_races' else ''), f'{g} {sex} by age (NT4)')
  219|     return res
  220| 
  221| 
  222| def y1850_1860(year):
  223|     res = adults_1850_1860(year)
  224|     if year == 1850:
  225|         n = read('ds12')
  226|         fb = {'M': n['AGF001'], 'F': n['AGF002']}
  227|         t = 'NHGIS 1850_cPAX NT4; 1850_sPAX NT1, NT5, NT7'
  228|     else:
  229|         n = read('ds14')
  230|         fb = {'M': n['AH4007'], 'F': n['AH4008']}
  231|         t = 'NHGIS 1860_cPAX NT4, NT7'
  232|     out = {}
  233|     for (st, sex, g), v in res.items():
  234|         if g != 'white':
  235|             out[(st, sex, g)] = v
  236|             continue
  237|         wa = v[0]
  238|         fa = min(fb[sex].get(st, 0) * FOREIGN_ADULT[sex], 0.95 * wa)
  239|         out[(st, sex, 'foreign_white_unknown')] = (fa, f'[I] foreign-born white {sex} (all ages) × {FOREIGN_ADULT[sex]} adult share; '
  240|                                                    'citizenship not tabulated', f'Foreign-born white {sex}')
  241|         out[(st, sex, 'native_white')] = (wa - fa, f'[I] white 21+ ({v[1][4:]}) less foreign-born adults; birthplace-unknown counted native',
  242|                                           f'Native white {sex} (residual)')
  243|     return emit(year, out, t)
  244| 
  245| 
  246| def build(year: int) -> pd.DataFrame:
  247|     if year == 1790:
  248|         return y1790()
  249|     if year in (1800, 1810):
  250|         return y1800_1810(year)
  251|     if year == 1820:
  252|         return y1820()
  253|     if year in (1830, 1840):
  254|         return y1830_1840(year)
  255|     return y1850_1860(year)
  256| 
  257| 
  258| BUILDERS = {y: build for y in range(1790, 1861, 10)}
  259| 
  260| 
  261| def free_share(year: int) -> dict:
  262|     """Per state: free colored / (free colored + enslaved) among adult men, from the nearest census at or before `year`."""
  263|     c = max(y for y in BUILDERS if y <= max(year, 1790))
  264|     f = CACHE / f'population/adults_{c}_by_state_nhgis.csv'
  265|     df = pd.read_csv(f) if f.exists() else build(c)
  266|     m = df[(df.sex == 'M') & df.group.isin(['free_colored', 'enslaved'])].pivot_table(index='state', columns='group', values='count', aggfunc='sum')
  267|     return (m.free_colored / (m.free_colored + m.enslaved)).fillna(1.0).to_dict()
  268| 
  269| 
  270| if __name__ == '__main__':
  271|     for y in (map(int, sys.argv[1:]) if len(sys.argv) > 1 else BUILDERS):
  272|         df = build(y)
  273|         out = CACHE / f'population/adults_{y}_by_state_nhgis.csv'
  274|         df.to_csv(out, index=False)
  275|         print(f'wrote {out.name}: {len(df)} rows, {df.state.nunique()} states, {df["count"].sum():,.0f} adults '
  276|               f'({df[df.sex == "F"]["count"].sum():,.0f} women)')
```

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

## `scripts/harness/data_1920_hashes.py`

```python
    1| #!/usr/bin/env python3
    2| """The sha256 of every file in data/1920/, as the table in data/1920/PROVENANCE.md.
    3| 
    4|   scripts/harness/data_1920_hashes.py           print the table
    5|   scripts/harness/data_1920_hashes.py --write   rewrite it between the PROVENANCE markers
    6| """
    7| import hashlib
    8| import sys
    9| from pathlib import Path
   10| 
   11| DIR = Path(__file__).resolve().parents[2] / 'data/1920'
   12| START, END = '<!-- hashes:start -->', '<!-- hashes:end -->'
   13| 
   14| 
   15| def table() -> str:
   16|     rows = ['| File | Bytes | sha256 |', '|---|---|---|']
   17|     for p in sorted(DIR.rglob('*.csv')):
   18|         rows.append(f'| `{p.relative_to(DIR)}` | {p.stat().st_size} | `{hashlib.sha256(p.read_bytes()).hexdigest()}` |')
   19|     return '\n'.join(rows)
   20| 
   21| 
   22| def main(argv: list[str]) -> None:
   23|     if '--write' not in argv:
   24|         print(table())
   25|         return
   26|     prov = DIR / 'PROVENANCE.md'
   27|     text = prov.read_text()
   28|     head, rest = text.split(START, 1)
   29|     _, tail = rest.split(END, 1)
   30|     prov.write_text(f'{head}{START}\n{table()}\n{END}{tail}')
   31|     print(f'wrote {prov}')
   32| 
   33| 
   34| if __name__ == '__main__':
   35|     main(sys.argv[1:])
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

# synthetic-electorate-toy: source and docs, part 4 of 16

Generated from commit `5fc0a9e54bc9` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `scripts/harness/build_population.py` to `scripts/harness/build_population_republic.py`. Lines are numbered as in the repository.

## `scripts/harness/build_population.py`

```python
    1| """NHGIS extract → population/adults_<year>_by_state_nhgis.csv in the harness's
    2| long format (the columns of adults_1920_by_state.csv), one census at a time,
    3| 1790–1970. The 1920 and 1930 builder is here; the other censuses come from
    4| build_population_republic (1790–1860), _early (1870–1910) and _mid (1940–1970).
    5| The 1980+ tables are 18+ and only build_population_modern.py writes them.
    6| 
    7|     python3 scripts/harness/build_population.py 1930            # writes the table
    8|     python3 scripts/harness/build_population.py 1920 --check    # compares with the hand-keyed 1920 table
    9| 
   10| Every row says how it was made in `note`: "tabulated" (straight from a census
   11| table) or an [I]-tagged estimate (and from what).
   12| """
   13| import argparse
   14| 
   15| import pandas as pd
   16| 
   17| import build_population_early
   18| import build_population_mid
   19| import build_population_republic
   20| from nhgis_common import CACHE, COLS, STATE_CODE, assert_close, hand_vs_nhgis, load, off_cells, print_worst, rows
   21| 
   22| 
   23| def read(ds: str) -> pd.DataFrame:
   24|     d = load(ds)
   25|     d = d[d.STATE.str.casefold().isin(STATE_CODE)].copy()
   26|     d['state'] = d.STATE.str.casefold().map(STATE_CODE)
   27|     return d.set_index('state')
   28| 
   29| 
   30| def year_1920_1930(year: int) -> pd.DataFrame:
   31|     """Both censuses tabulate 21+ by sex × race/nativity and the foreign-born
   32|     white by sex × citizenship: complete, no estimates."""
   33|     if year == 1920:
   34|         d = read('ds43')
   35|         rn = {'M': ['A7P001', 'A7P002', 'A7P003', 'A7P004', 'A7P005'], 'F': ['A7P006', 'A7P007', 'A7P008', 'A7P009', 'A7P010']}
   36|         cz = {'M': ['A7Q001', 'A7Q002', 'A7Q003', 'A7Q004'], 'F': ['A7Q005', 'A7Q006', 'A7Q007', 'A7Q008']}
   37|         t_rn, t_cz = 'NHGIS 1920_cPHAM NT13', 'NHGIS 1920_cPHAM NT15'
   38|     else:
   39|         d = read('ds54')
   40|         # NT10's codebook labels interleave the sexes (BDQ001 NN male, BDQ002 NN female…), but
   41|         # the values run sex-major like 1920's: males BDQ001–005, females BDQ006–010. Checked
   42|         # below against NT7 (race by sex) and NT10 of 1930_cAge30 (white nativity by sex).
   43|         rn = {'M': ['BDQ001', 'BDQ002', 'BDQ003', 'BDQ004', 'BDQ005'], 'F': ['BDQ006', 'BDQ007', 'BDQ008', 'BDQ009', 'BDQ010']}
   44|         x = read('ds53')
   45|         for sex, (nn, nf, fb, ng, ot), (wn, wf, b, o) in (('M', rn['M'], ('BDD001', 'BDD003', 'BDL003', 'BDL005')),
   46|                                                           ('F', rn['F'], ('BDD002', 'BDD004', 'BDL004', 'BDL006'))):
   47|             for mine, theirs in (((nn, nf), (wn,)), ((fb,), (wf,)), ((ng,), (b,)), ((ot,), (o,))):
   48|                 assert_close(d[list(mine)].sum(axis=1), x[list(theirs)].sum(axis=1), f'1930 {sex}: {mine} vs {theirs}')
   49|         cz = {'M': ['BDR001', 'BDR002', 'BDR003', 'BDR004'], 'F': ['BDR005', 'BDR006', 'BDR007', 'BDR008']}
   50|         t_rn, t_cz = 'NHGIS 1930_cPAE NT10', 'NHGIS 1930_cPAE NT12'
   51|     out = []
   52|     for sex in ('M', 'F'):
   53|         nn, nf, fb, ng, ot = rn[sex]
   54|         out += rows(year, d, [(nn, sex, 'native_white_native_parentage', 'White: Native-born with native parentage'),
   55|                               (nf, sex, 'native_white_foreign_or_mixed_parentage', 'White: Native-born with foreign or mixed parentage'),
   56|                               (ng, sex, 'negro', 'Negro: Negro'),
   57|                               (ot, sex, 'other_races', 'Other: Indian, Chinese, Japanese and all other races')], t_rn)
   58|         nat, fp, al, unk = cz[sex]
   59|         out += rows(year, d, [(nat, sex, 'foreign_white_naturalized', 'White: Foreign-born, naturalized'),
   60|                               (fp, sex, 'foreign_white_first_papers', 'White: Foreign-born, first papers'),
   61|                               (al, sex, 'foreign_white_alien', 'White: Foreign-born, alien'),
   62|                               (unk, sex, 'foreign_white_unknown', 'White: Foreign-born, citizenship unknown')], t_cz)
   63|         assert_close(d[fb], d[[nat, fp, al, unk]].sum(axis=1), f'{year} {sex}: foreign-born total vs citizenship split')
   64|     return pd.DataFrame(out, columns=COLS)
   65| 
   66| 
   67| BUILDERS = {**build_population_republic.BUILDERS, **build_population_early.BUILDERS,
   68|             1920: year_1920_1930, 1930: year_1920_1930, **build_population_mid.BUILDERS}
   69| 
   70| 
   71| def check_1920(nh: pd.DataFrame):
   72|     j = hand_vs_nhgis(pd.read_csv(CACHE / 'population/adults_1920_by_state.csv'), nh).fillna(0)
   73|     bad = off_cells(j)
   74|     print(f'cells {len(j)}; total hand {j.hand.sum():,.0f} vs nhgis {j.nhgis.sum():,.0f}; '
   75|           f'cells off by >50 and >0.5%: {len(bad)}')
   76|     print_worst(bad)
   77| 
   78| 
   79| if __name__ == '__main__':
   80|     ap = argparse.ArgumentParser()
   81|     ap.add_argument('year', type=int)
   82|     ap.add_argument('--check', action='store_true')
   83|     a = ap.parse_args()
   84|     if a.year not in BUILDERS:
   85|         ap.error(f'no 21+ builder for {a.year}' + (' (1980 on: build_population_modern.py writes the 18+ tables)'
   86|                                                    if a.year >= 1980 else ''))
   87|     df = BUILDERS[a.year](a.year)
   88|     if a.check and a.year == 1920:
   89|         check_1920(df)
   90|     else:
   91|         out = CACHE / f'population/adults_{a.year}_by_state_nhgis.csv'
   92|         df.to_csv(out, index=False)
   93|         print(f'wrote {out.name}: {len(df)} rows, {df.state.nunique()} states, {df["count"].sum():,.0f} adults '
   94|               f'({df[df.sex == "F"]["count"].sum():,.0f} women)')
```

## `scripts/harness/build_population_early.py`

```python
    1| """NHGIS 1870-1910 -> population/adults_<year>_by_state_nhgis.csv (long format,
    2| the columns of adults_1920_by_state.csv). build_population.py writes the tables
    3| through BUILDERS:
    4| 
    5|     python3 scripts/harness/build_population.py 1880
    6|     python3 scripts/harness/build_population_early.py               # prints a summary per census
    7|     python3 scripts/harness/build_population_early.py --check-1910  # vs the hand-keyed 1910 table
    8| 
    9| What the censuses give (codebooks in the extract):
   10|   1870 sPHX NT45-48: men 21+ total, by nativity, by race (separate margins), male
   11|        citizens 21+. sRN NT4: race x nativity, no sex.
   12|   1880 sPHX NT1 race x nativity x sex; NT7 men 21+ native white / FB white / colored.
   13|   1890 cPHAM NT5/NT6/NT9 sex tables; NT14 men 21+ native white / FB white / colored.
   14|        (No citizenship table was requested for 1890.)
   15|   1900 cPHAM NT4/NT6/NT7/NT62 sex tables; NT9 men 21+; NT10 native men 21+ by race;
   16|        NT11 FB men 21+ (all races) by citizenship.
   17|   1910 cPHA NT8/NT10/NT11 sex & white nativity; NT12/NT13 men of voting age by
   18|        race/nativity; NT17 FB white men of voting age by citizenship.
   19| Women 21+ were not tabulated before 1920: every women's row is an [I] estimate.
   20| Territories whose name (minus " Territory") is in geo.STATE_NAME are kept and say so
   21| in `note`; Dakota/Indian/Alaska/Hawaii Territory and "Persons in the Military" drop.
   22| """
   23| import sys
   24| from functools import lru_cache
   25| 
   26| import pandas as pd
   27| 
   28| from nhgis_common import (CACHE, COLS, STATE_CODE, assert_close, hand_vs_nhgis, load, off_cells, print_worst,
   29|                                rows)
   30| 
   31| TAB = 'tabulated'
   32| GROUPS = ['native_white', 'native_white_native_parentage', 'native_white_foreign_or_mixed_parentage',
   33|           'foreign_white_naturalized', 'foreign_white_first_papers', 'foreign_white_alien', 'foreign_white_unknown',
   34|           'negro', 'other_races']
   35| CZ = ['foreign_white_naturalized', 'foreign_white_first_papers', 'foreign_white_alien', 'foreign_white_unknown']
   36| # Alaska and Hawaii (statehood 1959) are territories in every census here: drop them
   37| # even though geo.STATE_NAME lists them for the modern elections.
   38| NOT_YET = {'AK', 'HI'}
   39| 
   40| 
   41| def read(ds: str) -> pd.DataFrame:
   42|     """Like build_population.read, but keeps territories that later became a
   43|     STATE_NAME state (e.g. 'Arizona Territory' -> AZ) and records that they were."""
   44|     d = load(ds)
   45|     base = d.STATE.str.replace(r'\s+Territory$', '', regex=True).str.casefold()
   46|     keep = base.isin(STATE_CODE) & ~base.map(STATE_CODE).isin(NOT_YET)
   47|     d = d[keep].copy()
   48|     d['state'] = base[keep].map(STATE_CODE)
   49|     d['terr'] = d.STATE.str.endswith('Territory')
   50|     assert d.state.is_unique, f'{ds}: duplicate state codes'
   51|     return d.set_index('state')
   52| 
   53| 
   54| def emit(year, d, spec, table, note=TAB):
   55|     """rows(), with territories saying so in `note`."""
   56|     out = rows(year, d, spec, table, note)
   57|     for r in out:
   58|         if d.at[r['state'], 'terr']:
   59|             r['note'] = (r['note'] + '; ' if r['note'] else '') + f'territory in {year}, not yet a state'
   60|     return out
   61| 
   62| 
   63| # ---------------------------------------------------------------- 1870
   64| @lru_cache
   65| def _men_1870():
   66|     d, rn = read('ds19'), read('ds21')
   67|     # Independent checks: nativity and race margins both add to the total.
   68|     assert_close(d.AMS001 + d.AMS002, d.AMR001, '1870 NT46 vs NT45')
   69|     assert_close(d[['AMT001', 'AMT002', 'AMT003', 'AMT004']].sum(axis=1), d.AMR001, '1870 NT47 vs NT45')
   70|     # Race x nativity of men 21+: IPF of the total-population race x nativity cross
   71|     # (sRN NT4) to the men-21+ race and nativity margins [I].
   72|     races = [('W', 'AMT001', 'AN8001', 'AN8002'), ('C', 'AMT002', 'AN8003', 'AN8004'),
   73|              ('I', 'AMT004', 'AN8005', 'AN8006'), ('Z', 'AMT003', 'AN8007', 'AN8008')]
   74|     out = {}
   75|     for st in d.index:
   76|         seed = {r: [float(rn.at[st, n]) + 1e-6, float(rn.at[st, f]) + 1e-6] for r, _, n, f in races}
   77|         rm = {r: float(d.at[st, c]) for r, c, _, _ in races}
   78|         cm = [float(d.at[st, 'AMS001']), float(d.at[st, 'AMS002'])]
   79|         x = {r: v[:] for r, v in seed.items()}
   80|         for _ in range(200):
   81|             for r in x:
   82|                 s = sum(x[r])
   83|                 x[r] = [v * rm[r] / s for v in x[r]] if s else [0.0, 0.0]
   84|             for j in (0, 1):
   85|                 s = sum(x[r][j] for r in x)
   86|                 for r in x:
   87|                     x[r][j] = x[r][j] * cm[j] / s if s else 0.0
   88|         out[st] = x
   89|     m = pd.DataFrame({st: {'nw': x['W'][0], 'fw': x['W'][1], 'negro': sum(x['C']), 'other': sum(x['I']) + sum(x['Z']),
   90|                            'nb': float(d.at[st, 'AMS001']), 'cit': float(d.at[st, 'AMU001'])} for st, x in out.items()}).T
   91|     # Naturalized = male citizens 21+ - native-born men 21+, clipped to [0, FB white] [I].
   92|     m['nat_raw'] = m.cit - m.nb
   93|     m['nat'] = m.nat_raw.clip(lower=0).clip(upper=m.fw)
   94|     m['alien'] = m.fw - m.nat
   95|     m['terr'] = d.terr
   96|     return m
   97| 
   98| 
   99| def _split_1870():
  100|     m = _men_1870()
  101|     s = pd.DataFrame({'foreign_white_naturalized': m.nat / m.fw, 'foreign_white_alien': m.alien / m.fw,
  102|                       'foreign_white_first_papers': 0.0, 'foreign_white_unknown': 0.0}).fillna(0)
  103|     return s[CZ]
  104| 
  105| 
  106| def year_1870(year=1870):
  107|     m = _men_1870()
  108|     fm = _fm_1880()  # 1870 has no table by sex at all
  109|     out = []
  110|     lbl = {'nw': 'White: Native-born', 'negro': 'Colored: Native and foreign-born',
  111|            'other': 'Indian and Chinese: Native and foreign-born'}
  112|     grp = {'nw': 'native_white', 'negro': 'negro', 'other': 'other_races'}
  113|     ipf = '[I] men 21+ race x nativity: NT47 race and NT46 nativity margins raked (IPF) on the sRN NT4 total-population cross'
  114|     t = 'NHGIS 1870_sPHX NT45-NT47 (+1870_sRN NT4 seed)'
  115|     for k in ('nw', 'negro', 'other'):
  116|         out += emit(year, m, [(k, 'M', grp[k], lbl[k])], t, ipf)
  117|         w = m[[k, 'terr']].copy()
  118|         w[k] = m[k] * fm[grp[k]].reindex(m.index)
  119|         out += emit(year, w, [(k, 'F', grp[k], lbl[k])], t + '; 1880_sPHX NT1',
  120|                      '[I] women 21+ = men 21+ x the 1880 whole-population F/M ratio of the same state and group '
  121|                      '(1870 has no table by sex)')
  122|     tc = 'NHGIS 1870_sPHX NT46-NT48'
  123|     cz_note = ('[I] FB white men 21+ (IPF) split: naturalized = NT48 male citizens 21+ - NT46 native-born men 21+, '
  124|                'clipped to [0, FB white]; alien = the rest')
  125|     for sex in ('M', 'F'):
  126|         w = m[['nat', 'alien', 'terr']].copy()
  127|         n = cz_note
  128|         if sex == 'F':
  129|             fr = fm['foreign_white'].reindex(m.index)
  130|             w['nat'], w['alien'] = w.nat * fr, w.alien * fr
  131|             n = cz_note + '; women = men x 1880 FB white F/M, men\'s citizenship split (wife followed husband before 1922)'
  132|             tc2 = tc + '; 1880_sPHX NT1'
  133|         else:
  134|             tc2 = tc
  135|         out += emit(year, w, [('nat', sex, 'foreign_white_naturalized', 'White: Foreign-born, naturalized'),
  136|                                ('alien', sex, 'foreign_white_alien', 'White: Foreign-born, alien')], tc2, n)
  137|     return pd.DataFrame(out, columns=COLS)
  138| 
  139| 
  140| # ---------------------------------------------------------------- 1880
  141| A_CHINESE = 0.95  # [I] share of Chinese/Japanese males who were 21+ (an almost all-adult male labour migration)
  142| 
  143| 
  144| @lru_cache
  145| def _fm_1880():
  146|     d = read('ds25')
  147|     p = lambda cols: d[cols].sum(axis=1)  # noqa: E731
  148|     return pd.DataFrame({
  149|         'native_white': d.AR0002 / d.AR0001,
  150|         'foreign_white': d.AR0004 / d.AR0003,
  151|         'negro': p(['AR0006', 'AR0008']) / p(['AR0005', 'AR0007']),
  152|         'other_races': p(['AR0010', 'AR0012', 'AR0014', 'AR0016']) / p(['AR0009', 'AR0011', 'AR0013', 'AR0015']),
  153|     }).fillna(1.0)
  154| 
  155| 
  156| @lru_cache
  157| def _men_1880():
  158|     d = read('ds25')
  159|     neg = d.AR0005 + d.AR0007
  160|     chi = d.AR0009 + d.AR0011
  161|     ind = d.AR0013 + d.AR0015
  162|     # NT7 "Colored" men 21+ includes Chinese and Indians (CA: 66,809 colored men 21+
  163|     # vs 3,467 Negro males of all ages). Split it by males weighted by adult share:
  164|     # Negro and Indian at the national colored-men-21+/Negro-males ratio of states
  165|     # where they're >99% of colored males, Chinese/Japanese at A_CHINESE [I].
  166|     pure = (chi + ind) < 0.01 * (neg + chi + ind)
  167|     a_n = d.ASU003[pure].sum() / neg[pure].sum()
  168|     wn, wc, wi = neg * a_n, chi * A_CHINESE, ind * a_n
  169|     tot = (wn + wc + wi).replace(0, 1)
  170|     m = pd.DataFrame({'nw': d.ASU001.astype(float), 'fw': d.ASU002.astype(float),
  171|                       'negro': d.ASU003 * wn / tot, 'other': d.ASU003 * (wc + wi) / tot, 'terr': d.terr})
  172|     # Independent check: men 21+ can't exceed males of all ages in any group.
  173|     assert (m.nw <= d.AR0001).all() and (m.fw <= d.AR0003).all() and (d.ASU003 <= neg + chi + ind).all()
  174|     m.attrs['a_n'] = a_n
  175|     return m
  176| 
  177| 
  178| def _interp_split(year):
  179|     """Citizenship shares of FB white men 21+ for a census with none: linear in
  180|     time between the 1870 derivation and the 1900 tabulation (1890's citizenship
  181|     table wasn't in the extract), 1900 alone where the unit wasn't in 1870 [I]."""
  182|     s70, s00 = _split_1870(), _split_1900()
  183|     w = (year - 1870) / 30
  184|     s = s70.reindex(s00.index) * (1 - w) + s00 * w
  185|     return s.fillna(s00)
  186| 
  187| 
  188| def _fw_rows(year, fw_m, fw_f, split, terr, table, note_m, note_f):
  189|     out = []
  190|     lbl = {'foreign_white_naturalized': 'White: Foreign-born, naturalized',
  191|            'foreign_white_first_papers': 'White: Foreign-born, first papers',
  192|            'foreign_white_alien': 'White: Foreign-born, alien',
  193|            'foreign_white_unknown': 'White: Foreign-born, citizenship unknown'}
  194|     for sex, tot, note in (('M', fw_m, note_m), ('F', fw_f, note_f)):
  195|         w = pd.DataFrame({g: tot * split[g].reindex(tot.index) for g in CZ})
  196|         w['terr'] = terr
  197|         out += emit(year, w, [(g, sex, g, lbl[g]) for g in CZ], table, note)
  198|     return out
  199| 
  200| 
  201| def year_1880(year=1880):
  202|     m, fm = _men_1880(), _fm_1880()
  203|     t = 'NHGIS 1880_sPHX NT7'
  204|     tf = 'NHGIS 1880_sPHX NT7 x NT1'
  205|     fnote = '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT1)'
  206|     out = emit(year, m, [('nw', 'M', 'native_white', 'White: Native-born')], t)
  207|     split = (f'[I] NT7 colored men 21+ split Negro vs Chinese/Indian by NT1 males weighted by adult share '
  208|              f'(Negro & Indian {m.attrs["a_n"]:.3f}, Chinese/Japanese {A_CHINESE})')
  209|     out += emit(year, m, [('negro', 'M', 'negro', 'Colored: Negro'),
  210|                            ('other', 'M', 'other_races', 'Colored: Chinese, Japanese and Indian')], t + '; NT1', split)
  211|     w = pd.DataFrame({'nw': m.nw * fm.native_white, 'negro': m.negro * fm.negro, 'other': m.other * fm.other_races,
  212|                       'terr': m.terr})
  213|     out += emit(year, w, [('nw', 'F', 'native_white', 'White: Native-born')], tf, fnote)
  214|     out += emit(year, w, [('negro', 'F', 'negro', 'Colored: Negro'),
  215|                            ('other', 'F', 'other_races', 'Colored: Chinese, Japanese and Indian')], tf, fnote + '; ' + split)
  216|     cz = '[I] NT7 FB white men 21+ x citizenship shares interpolated 1870 (derived) -> 1900 (tabulated) at 1880'
  217|     out += _fw_rows(year, m.fw, m.fw * fm.foreign_white, _interp_split(year), m.terr, t + '; 1870_sPHX NT48; 1900_cPHAM NT11',
  218|                     cz, cz + '; women = men x NT1 FB white F/M, men\'s split (wife followed husband before 1922)')
  219|     return pd.DataFrame(out, columns=COLS)
  220| 
  221| 
  222| # ---------------------------------------------------------------- 1900
  223| @lru_cache
  224| def _men_1900():
  225|     d = read('ds31')
  226|     nat = d[[f'AYN00{i}' for i in range(1, 7)]].sum(axis=1)
  227|     fb = d[[f'AYO00{i}' for i in range(1, 9)]].sum(axis=1)
  228|     assert_close(nat + fb, d.AZ4001, '1900 NT10+NT11 vs NT9')
  229|     assert_close(d.AZF001 + d.AZF003, d.AZ0001, '1900 NT4 vs NT62')
  230|     # NT7's codebook says "Other Colored" for AZ3001/2, but the values are ALL colored
  231|     # (Negro + other): nationally 4.71M vs 4.39M Negro males, and FL 120,518 vs
  232|     # 120,199. Check: colored minus Negro must hold the native "Colored" men 21+ (NT10).
  233|     oth_m, oth_f = d.AZ3001 - d.AZ3003, d.AZ3002 - d.AZ3004
  234|     assert (oth_m >= 0).all() and (oth_m >= d.AYN005 + d.AYN006).all(), '1900 NT7 not colored-total'
  235|     assert (d.AZX001 <= d.AZF003).all()
  236|     fbnw_males = d.AZF003 - d.AZX001          # FB non-white males, all ages (NT4 - NT6)
  237|     fbnw_f = d.AZF004 - d.AZX002
  238|     fbnw = fbnw_males * fb / d.AZF003.replace(0, 1)   # [I] at the FB adult share
  239|     # FB "other" can't exceed other-colored males less native other men 21+; the rest is FB Negro [I].
  240|     fb_oth = pd.concat([fbnw, (oth_m - d.AYN005 - d.AYN006).clip(lower=0) * fb / d.AZF003.replace(0, 1)],
  241|                        axis=1).min(axis=1)
  242|     fb_neg = fbnw - fb_oth
  243|     cz = pd.DataFrame({'foreign_white_naturalized': d.AYO001 + d.AYO002, 'foreign_white_first_papers': d.AYO003 + d.AYO004,
  244|                        'foreign_white_alien': d.AYO005 + d.AYO006, 'foreign_white_unknown': d.AYO007 + d.AYO008}).astype(float)
  245|     # FB non-whites (mostly Chinese, barred from naturalizing) come out of alien, then unknown [I].
  246|     take = pd.concat([fbnw, cz.foreign_white_alien], axis=1).min(axis=1)
  247|     cz['foreign_white_alien'] -= take
  248|     cz['foreign_white_unknown'] -= (fbnw - take)
  249|     assert (cz.foreign_white_unknown > -1).all(), '1900: FB non-white exceeds alien + unknown'
  250|     m = pd.DataFrame({'nw': (d.AYN001 + d.AYN002).astype(float), 'negro_nb': (d.AYN003 + d.AYN004).astype(float),
  251|                       'other_nb': (d.AYN005 + d.AYN006).astype(float), 'fb_neg': fb_neg, 'fb_oth': fb_oth,
  252|                       'fw': cz.sum(axis=1), 'terr': d.terr})
  253|     m['negro'] = m.negro_nb + m.fb_neg
  254|     m['other'] = m.other_nb + m.fb_oth
  255|     nw_m = d.AZF001 - (d.AZ3001 - fbnw_males)
  256|     nw_f = d.AZF002 - (d.AZ3002 - fbnw_f)
  257|     fm = pd.DataFrame({'native_white': nw_f / nw_m, 'foreign_white': d.AZX002 / d.AZX001,
  258|                        'negro': d.AZ3004 / d.AZ3003, 'other_races': oth_f / oth_m.replace(0, 1),
  259|                        'white': (nw_f + d.AZX002) / (nw_m + d.AZX001)}).fillna(1.0)
  260|     return m, cz, fm
  261| 
  262| 
  263| def _split_1900():
  264|     _, cz, _ = _men_1900()
  265|     return cz.div(cz.sum(axis=1).replace(0, 1), axis=0)
  266| 
  267| 
  268| def year_1900(year=1900):
  269|     m, cz, fm = _men_1900()
  270|     t = 'NHGIS 1900_cPHAM NT10'
  271|     out = emit(year, m, [('nw', 'M', 'native_white', 'White: Native-born')], t)
  272|     fbn = ('[I] native-born (NT10, tabulated) + FB non-white men 21+ = (NT4 FB males - NT6 FB white males) x FB '
  273|            'adult share (NT11/NT4); FB "other" capped at NT7 other-colored males, the rest FB Negro')
  274|     out += emit(year, m, [('negro', 'M', 'negro', 'Negro'),
  275|                            ('other', 'M', 'other_races', 'Colored: Indian, Chinese, Japanese')], t + '; NT4; NT6; NT7; NT11', fbn)
  276|     fnote = '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT4/NT6/NT7)'
  277|     w = pd.DataFrame({'nw': m.nw * fm.native_white, 'negro': m.negro * fm.negro, 'other': m.other * fm.other_races,
  278|                       'terr': m.terr})
  279|     out += emit(year, w, [('nw', 'F', 'native_white', 'White: Native-born'), ('negro', 'F', 'negro', 'Negro'),
  280|                            ('other', 'F', 'other_races', 'Colored: Indian, Chinese, Japanese')],
  281|                  'NHGIS 1900_cPHAM NT10 x NT4/NT6/NT7', fnote)
  282|     czn = ('[I] NT11 FB men 21+ by citizenship (all races) less the FB non-white estimate, taken from alien '
  283|            'then unknown')
  284|     out += _fw_rows(year, m.fw, m.fw * fm.foreign_white, _split_1900(), m.terr, 'NHGIS 1900_cPHAM NT11; NT4; NT6', czn,
  285|                     czn + '; women = men x NT6 FB white F/M, men\'s split (wife followed husband before 1922)')
  286|     return pd.DataFrame(out, columns=COLS)
  287| 
  288| 
  289| # ---------------------------------------------------------------- 1890
  290| def year_1890(year=1890):
  291|     d = read('ds27')
  292|     assert_close(d.AVP001 + d.AVP003, d.AV3001, '1890 NT5 vs NT9 (male)')
  293|     assert_close(d[['AV0001', 'AV0003', 'AV0005', 'AV0007']].sum(axis=1), d.AV3001, '1890 NT6 vs NT9 (male)')
  294|     assert_close(d[['AV0002', 'AV0004', 'AV0006', 'AV0008']].sum(axis=1), d.AV3002, '1890 NT6 vs NT9 (female)')
  295|     assert (d.AUP001 <= d.AV0001 + d.AV0003).all() and (d.AUP002 <= d.AV0005).all() and (d.AUP003 <= d.AV0007).all()
  296|     m80, m00 = _men_1880(), _men_1900()[0]
  297|     fm80, fm00 = _fm_1880(), _men_1900()[2]
  298|     # NT14 "Colored" men 21+ (incl. Chinese/Indian, CA 72,061) split by the mean of the
  299|     # 1880 and 1900 Negro shares of colored men 21+ in the state [I].
  300|     sh = pd.concat([(m80.negro / (m80.negro + m80.other)), (m00.negro / (m00.negro + m00.other))], axis=1).mean(axis=1)
  301|     sh = sh.reindex(d.index).fillna(1.0)
  302|     m = pd.DataFrame({'nw': d.AUP001.astype(float), 'fw': d.AUP002.astype(float),
  303|                       'negro': d.AUP003 * sh, 'other': d.AUP003 * (1 - sh), 'terr': d.terr})
  304|     t = 'NHGIS 1890_cPHAM NT14'
  305|     out = emit(year, m, [('nw', 'M', 'native_white', 'White: Native-born')], t)
  306|     spl = '[I] NT14 colored men 21+ split Negro vs other by the mean of the state\'s 1880 and 1900 Negro shares'
  307|     out += emit(year, m, [('negro', 'M', 'negro', 'Colored: Negro'),
  308|                            ('other', 'M', 'other_races', 'Colored: Chinese, Japanese and Indian')], t, spl)
  309|     # Women: NT6 F/M for native white; Negro/other F/M = mean of 1880 and 1900, scaled so the
  310|     # implied colored F/M matches 1890's NT6 [I].
  311|     fm_nw = (d.AV0002 + d.AV0004) / (d.AV0001 + d.AV0003)
  312|     fm_fw = d.AV0006 / d.AV0005
  313|     fn = pd.concat([fm80.negro, fm00.negro], axis=1).mean(axis=1).reindex(d.index).fillna(d.AV0008 / d.AV0007)
  314|     fo = pd.concat([fm80.other_races, fm00.other_races], axis=1).mean(axis=1).reindex(d.index).fillna(1.0)
  315|     k = (d.AV0008 / d.AV0007) / ((fn * m.negro + fo * m.other) / d.AUP003.replace(0, 1)).replace(0, 1)
  316|     w = pd.DataFrame({'nw': m.nw * fm_nw, 'negro': m.negro * fn * k, 'other': m.other * fo * k, 'terr': m.terr})
  317|     out += emit(year, w, [('nw', 'F', 'native_white', 'White: Native-born')], t + ' x NT6',
  318|                  '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT6)')
  319|     out += emit(year, w, [('negro', 'F', 'negro', 'Colored: Negro'),
  320|                            ('other', 'F', 'other_races', 'Colored: Chinese, Japanese and Indian')], t + ' x NT6',
  321|                  '[I] women 21+ = men 21+ x mean 1880/1900 F/M of the group, scaled to NT6 colored F/M; ' + spl)
  322|     cz = ('[I] NT14 FB white men 21+ x citizenship shares interpolated 1870 (derived) -> 1900 (tabulated) at 1890 '
  323|           '(no 1890 citizenship table in the extract)')
  324|     out += _fw_rows(year, m.fw, m.fw * fm_fw, _interp_split(year), m.terr, t + '; 1870_sPHX NT48; 1900_cPHAM NT11', cz,
  325|                     cz + '; women = men x NT6 FB white F/M, men\'s split (wife followed husband before 1922)')
  326|     return pd.DataFrame(out, columns=COLS)
  327| 
  328| 
  329| # ---------------------------------------------------------------- 1910
  330| def year_1910(year=1910):
  331|     d = read('ds37')
  332|     assert_close(d[[f'A3200{i}' for i in range(1, 7)]].sum(axis=1), d.A31001, '1910 NT13 vs NT12')
  333|     assert_close(d[[f'A3300{i}' for i in range(1, 5)]].sum(axis=1), d.A32004, '1910 NT17 vs NT13 FB white')
  334|     assert_close(d[['A5B001', 'A5B002', 'A5B003', 'A5B004']].sum(axis=1), d.A30001 + d.A30002, '1910 NT8 vs NT11 white')
  335|     oth_m, oth_f = d.A3Z001 - d.A30001 - d.A30003, d.A3Z002 - d.A30002 - d.A30004
  336|     assert (oth_m > -1).all() and (oth_f > -1).all()
  337|     assert (d.A32005 <= d.A30003).all() and (d.A32001 + d.A32002 + d.A32003 + d.A32004 <= d.A30001).all()
  338|     t = 'NHGIS 1910_cPHA NT13'
  339|     m = d.copy()
  340|     m['nwf'] = (d.A32002 + d.A32003).astype(float)
  341|     out = []
  342|     out += emit(year, m, [('A32001', 'M', 'native_white_native_parentage', 'Native-Born White: Native parentage'),
  343|                            ('nwf', 'M', 'native_white_foreign_or_mixed_parentage', 'Native-Born White: Foreign or mixed parentage'),
  344|                            ('A32005', 'M', 'negro', 'Negro'),
  345|                            ('A32006', 'M', 'other_races', 'Indian, Chinese, Japanese and all other races')], t)
  346|     lbl = [('A33001', 'foreign_white_naturalized', 'Foreign-born white: Naturalized'),
  347|            ('A33002', 'foreign_white_first_papers', 'Foreign-born white: With first papers'),
  348|            ('A33003', 'foreign_white_alien', 'Foreign-born white: Alien'),
  349|            ('A33004', 'foreign_white_unknown', 'Foreign-born white: Unknown citizenship status')]
  350|     out += emit(year, m, [(c, 'M', g, lab) for c, g, lab in lbl], 'NHGIS 1910_cPHA NT17')
  351|     # Women: NT11 gives white/Negro by sex, other = NT10 - NT11. White nativity isn't by sex
  352|     # in 1910: native and FB white F/M = the state's 1900 ratios x (1910 white F/M / 1900 white F/M) [I].
  353|     fm00 = _men_1900()[2].reindex(d.index)
  354|     r_w = d.A30002 / d.A30001
  355|     k = r_w / fm00.white
  356|     r_nw = (fm00.native_white * k).fillna(r_w)
  357|     r_fw = (fm00.foreign_white * k).fillna(r_w)
  358|     w = pd.DataFrame({'np': d.A32001 * r_nw, 'nwf': m.nwf * r_nw, 'neg': d.A32005 * d.A30004 / d.A30003,
  359|                       'oth': d.A32006 * (oth_f / oth_m.replace(0, 1)), 'terr': d.terr})
  360|     for c in ('A33001', 'A33002', 'A33003', 'A33004'):
  361|         w[c] = d[c] * r_fw
  362|     fnote = '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT10/NT11)'
  363|     wnote = ('[I] women 21+ = men 21+ x white F/M by nativity: the state\'s 1900 native/FB white F/M scaled by '
  364|              '1910/1900 white F/M (NT11; 1910 white nativity not by sex)')
  365|     out += emit(year, w, [('np', 'F', 'native_white_native_parentage', 'Native-Born White: Native parentage'),
  366|                            ('nwf', 'F', 'native_white_foreign_or_mixed_parentage', 'Native-Born White: Foreign or mixed parentage')],
  367|                  t + ' x NT11; 1900_cPHAM NT4/NT6/NT7', wnote)
  368|     out += emit(year, w, [('neg', 'F', 'negro', 'Negro'), ('oth', 'F', 'other_races', 'Indian, Chinese, Japanese and all other races')],
  369|                  t + ' x NT10/NT11', fnote)
  370|     out += emit(year, w, [(c, 'F', g, lab) for c, g, lab in lbl], 'NHGIS 1910_cPHA NT17 x NT11; 1900_cPHAM NT4/NT6/NT7',
  371|                  wnote + '; men\'s citizenship split (wife followed husband before 1922)')
  372|     return pd.DataFrame(out, columns=COLS)
  373| 
  374| 
  375| BUILDERS = {1870: year_1870, 1880: year_1880, 1890: year_1890, 1900: year_1900, 1910: year_1910}
  376| 
  377| 
  378| def check_1910(nh: pd.DataFrame):
  379|     hand = pd.read_csv(CACHE / 'population/adults_1910_by_state.csv')
  380|     for sex in ('M', 'F'):
  381|         j = hand_vs_nhgis(hand[hand.sex == sex], nh[nh.sex == sex])
  382|         miss = j[j.isna().any(axis=1)]
  383|         j = j.fillna(0)
  384|         bad = off_cells(j)
  385|         print(f'{sex}: cells {len(j)} ({len(miss)} on one side only); total hand {j.hand.sum():,.0f} vs nhgis '
  386|               f'{j.nhgis.sum():,.0f}; exact {(j["diff"].abs() < 0.5).sum()}; off by >50 and >0.5%: {len(bad)}')
  387|         if len(miss):
  388|             print('  one side only:', sorted(set(s for s, _, _ in miss.index)))
  389|         print_worst(bad)
  390| 
  391| 
  392| if __name__ == '__main__':
  393|     if '--check-1910' in sys.argv:
  394|         check_1910(year_1910())
  395|     else:
  396|         for y, f in BUILDERS.items():
  397|             df = f(y)
  398|             assert set(df.group) <= set(GROUPS), set(df.group) - set(GROUPS)
  399|             print(y, len(df), df.state.nunique(), f'{df["count"].sum():,.0f}',
  400|                   f'women {df[df.sex == "F"]["count"].sum() / df["count"].sum():.3f}')
```

## `scripts/harness/build_population_mid.py`

```python
    1| """NHGIS 1940–1970 → population tables (21+ and 18+), long format like
    2| adults_1920_by_state.csv. build_population.py uses BUILDERS (21+).
    3| 
    4|     python3 scripts/harness/build_population.py 1950           # 21+ only, via the shared entry point
    5|     python3 scripts/harness/build_population_mid.py            # 21+ and 18+ for 1940 1950 1960 1970
    6|     python3 scripts/harness/build_population_mid.py 1960 1970  # just those years
    7| 
    8| Writes CACHE/population/adults_<y>_by_state_nhgis.csv (21+) and
    9| adults18_<y>_by_state_nhgis.csv (18+; 1950 onward). Every value that is not a
   10| straight tabulation carries an [I] note saying how it was estimated.
   11| 
   12| What each census gives (state level, NHGIS extract 1):
   13|   1940  21+ by race × sex (cAge NT7); white 21+ by nativity × sex (cAge NT10);
   14|         FB white 21+ by sex × citizenship (cPHAE NT12). Complete.
   15|   1950  race (white / nonwhite) × sex × 5-yr age (cAge NT18); total 21+ (NT6, cPHA NT8);
   16|         21+ by nativity, FB 21+ by citizenship, both sexes and all races (cPHA NT9A/9B);
   17|         nonwhite 21+ by sex (cPHA NT48). Hawaii is blank in every 1950 table → omitted.
   18|   1960  white / nonwhite × sex × 5-yr age (cAge1 NT11); nonwhite 21+ by sex (cPop NT14).
   19|   1970  sex × single years to 21 (Cnt1 NT18); Negro / other × sex × 10-yr age (NT19).
   20| """
   21| import functools
   22| import sys
   23| 
   24| import numpy as np
   25| import pandas as pd
   26| 
   27| from nhgis_common import CACHE, STATE_CODE, assert_close, frame, load, row
   28| 
   29| TERR = {'alaska': 'AK', 'alaska territory': 'AK', 'hawaii': 'HI', 'hawaii territory': 'HI'}
   30| 
   31| 
   32| def read(ds: str, territories: bool) -> pd.DataFrame:
   33|     d = load(ds)
   34|     code = {k: v for k, v in STATE_CODE.items() if v not in ('AK', 'HI')}  # geo may or may not list them yet
   35|     if territories:
   36|         code.update(TERR)
   37|     d = d[d.STATE.str.casefold().isin(code)].copy()
   38|     d['state'] = d.STATE.str.casefold().map(code)
   39|     assert d.state.is_unique and len(d) == (len(set(code.values()))), (ds, len(d))
   40|     return d.set_index('state')
   41| 
   42| 
   43| def cols(prefix, a, b):
   44|     return [f'{prefix}{i:03d}' for i in range(a, b + 1)]
   45| 
   46| 
   47| def tab(label, table, note='tabulated'):
   48|     return {'label': label, 'table': table, 'note': note}
   49| 
   50| 
   51| def emit(year, cells):
   52|     """cells: {(sex, group): (Series by state, meta)} → long DataFrame."""
   53|     return frame([row(year, st, sex, group, m['label'].split(':')[0], m['label'], round(float(v), 1), m['note'], m['table'])
   54|                   for (sex, group), (s, m) in cells.items() for st, v in s.dropna().items()])
   55| 
   56| 
   57| # ---------------------------------------------------------------- 1940 (complete)
   58| @functools.lru_cache(None)
   59| def y1940():
   60|     a, b = read('ds77', False), read('ds78', False)
   61|     sx = {'M': 0, 'F': 1}
   62|     for s, i in sx.items():
   63|         wh, ng, ot = a[f'BV300{1+i}'], a[f'BV300{3+i}'], a[f'BV300{5+i}']
   64|         nw, fw = a[f'BVV00{1+i}'], a[f'BVV00{3+i}']
   65|         assert_close(nw + fw, wh, f'1940 {s} white nativity vs NT7 white')
   66|         assert_close(wh + ng + ot, b[f'BYU00{1+i}'], f'1940 {s} NT7 races vs cPHAE NT8 total')
   67|         fbw = b[cols('BWN', 1 + 4 * i, 4 + 4 * i)].sum(axis=1)
   68|         assert_close(fbw, fw, f'1940 {s} cPHAE NT12 citizenship vs cAge NT10 foreign-born white')
   69|         fb = b[cols('BV8', 1 + 3 * i, 3 + 3 * i)].sum(axis=1)
   70|         assert_close(b[f'BY500{1+i}'] + fb, b[f'BYU00{1+i}'], f'1940 {s} native + foreign vs total')
   71|     cells = {}
   72|     for s, i in sx.items():
   73|         t7, t10, t12 = 'NHGIS 1940_cAge NT7', 'NHGIS 1940_cAge NT10', 'NHGIS 1940_cPHAE NT12'
   74|         nat, fp, al, unk = cols('BWN', 1 + 4 * i, 4 + 4 * i)
   75|         cells[(s, 'native_white')] = (a[f'BVV00{1+i}'], tab('White: Native-born', t10))
   76|         cells[(s, 'foreign_white_naturalized')] = (b[nat], tab('White: Foreign-born, naturalized', t12))
   77|         cells[(s, 'foreign_white_first_papers')] = (b[fp], tab('White: Foreign-born, with first papers', t12))
   78|         cells[(s, 'foreign_white_alien')] = (b[al], tab('White: Foreign-born, with no papers', t12))
   79|         cells[(s, 'foreign_white_unknown')] = (b[unk], tab('White: Foreign-born, citizenship not reported', t12))
   80|         cells[(s, 'negro')] = (a[f'BV300{3+i}'], tab('Negro: Negro', t7))
   81|         cells[(s, 'other_races')] = (a[f'BV300{5+i}'], tab('Other: Other races', t7))
   82|     return emit(1940, cells)
   83| 
   84| 
   85| # ---------------------------------------------------------------- helpers 1950–1970
   86| def neg_share_1940():
   87|     """Negro share of nonwhite 21+, by state and sex (states only; territories blank by race)."""
   88|     a = read('ds77', False)
   89|     return {s: (a[f'BV300{3+i}'] / (a[f'BV300{3+i}'] + a[f'BV300{5+i}'])) for s, i in (('M', 0), ('F', 1))}
   90| 
   91| 
   92| @functools.lru_cache(None)
   93| def c1970():
   94|     """1970 counts by sex: total, negro, other at 21+ and 18–20. NT19's 15–24 band
   95|     is split by the total population's single-year shape within 15–24 [I]."""
   96|     c = read('ds94', True)
   97|     r = {}
   98|     for s, o in (('M', 0), ('F', 22)):
   99|         t = c[cols('CBT', 1 + o, 22 + o)].fillna(0).to_numpy()
  100|         tot15_24 = t[:, 6:14].sum(axis=1)
  101|         f21 = t[:, 12:14].sum(axis=1) / tot15_24  # 21, 22–24 of 15–24
  102|         f18 = t[:, 9:12].sum(axis=1) / tot15_24   # 18, 19, 20
  103|         r[(s, 'tot21')] = pd.Series(t[:, 12:].sum(axis=1), c.index)
  104|         r[(s, 'tot18_20')] = pd.Series(t[:, 9:12].sum(axis=1), c.index)
  105|         for g, base in (('negro', 1 if s == 'M' else 9), ('other_races', 17 if s == 'M' else 25)):
  106|             u = c[cols('CBU', base, base + 7)].fillna(0).to_numpy()
  107|             assert (u[:, 2] <= tot15_24 + 1).all()
  108|             r[(s, g + '21')] = pd.Series(u[:, 3:].sum(axis=1) + u[:, 2] * f21, c.index)
  109|             r[(s, g + '18_20')] = pd.Series(u[:, 2] * f18, c.index)
  110|     return r
  111| 
  112| 
  113| def neg_share(year):
  114|     """[I] Negro share of nonwhite 21+: linear in time between 1940 (NT7) and 1970 (NT19);
  115|     1970 alone where 1940 has no race split (AK, HI)."""
  116|     c = c1970()
  117|     s40 = neg_share_1940()
  118|     w = (year - 1940) / 30
  119|     out = {}
  120|     for s in ('M', 'F'):
  121|         s70 = c[(s, 'negro21')] / (c[(s, 'negro21')] + c[(s, 'other_races21')])
  122|         out[s] = ((1 - w) * s40[s].reindex(s70.index) + w * s70).fillna(s70).fillna(1.0)
  123|     return out
  124| 
  125| 
  126| def ipf(seed, rows, colm, n=50):
  127|     t = seed.astype(float) + 1e-9
  128|     for _ in range(n):
  129|         t *= (rows / t.sum(1))[:, None]
  130|         t *= colm / t.sum(0)
  131|     return t
  132| 
  133| 
  134| # ---------------------------------------------------------------- 1950
  135| @functools.lru_cache(None)
  136| def y1950():
  137|     a, b = read('ds83', True), read('ds84', True)
  138|     a, b = a.drop('HI'), b.drop('HI')  # Hawaii Territory is blank in every 1950 table of the extract
  139|     assert_close(a.B14001, b.B37001, '1950 NT6 vs cPHA NT8 21+')
  140|     assert_close(b[['B4J001', 'B4J002']].sum(axis=1), b.B37001, '1950 nativity vs total 21+')
  141|     assert_close(b[cols('B4K', 1, 3)].sum(axis=1), b.B4J002, '1950 citizenship vs foreign-born 21+')
  142|     band = {}
  143|     for (race, s), o in ((('W', 'M'), 0), (('W', 'F'), 17), (('N', 'M'), 34), (('N', 'F'), 51)):
  144|         x = a[cols('B1W', 1 + o, 17 + o)].fillna(0).to_numpy()
  145|         band[(race, s, 21)] = pd.Series(x[:, 5:].sum(axis=1) + 0.8 * x[:, 4], a.index)
  146|         band[(race, s, 18)] = pd.Series(0.4 * x[:, 3] + 0.2 * x[:, 4], a.index)
  147|     est21 = sum(band[(r, s, 21)] for r in 'WN' for s in 'MF')
  148|     rel = (est21 / a.B14001 - 1)
  149|     print(f'1950 band-split 21+ vs NT6: national {est21.sum():,.0f} vs {a.B14001.sum():,.0f}; '
  150|           f'state rel. error max {rel.abs().max():.4f} ({rel.abs().idxmax()})')
  151|     nwx = b[['B3C001', 'B3C002']].sum(axis=1)
  152|     nwe = band[('N', 'M', 21)] + band[('N', 'F', 21)]
  153|     print(f'1950 nonwhite 21+: NT48 {nwx.sum():,.0f} vs band-split {nwe.sum():,.0f}')
  154|     # Nonwhite 21+ by sex: NT48 where present, else band split. White total: NT6 − nonwhite; sex split by bands.
  155|     nw, nw_note = {}, {}
  156|     for s, col in (('M', 'B3C001'), ('F', 'B3C002')):
  157|         nw[s] = b[col].fillna(band[('N', s, 21)])
  158|         nw_note[s] = b[col].isna()
  159|     wt = a.B14001 - nw['M'] - nw['F']
  160|     wsh = band[('W', 'M', 21)] / (band[('W', 'M', 21)] + band[('W', 'F', 21)])
  161|     wh = {'M': wt * wsh, 'F': wt * (1 - wsh)}
  162|     # Foreign-born white 21+ by sex: 1950 foreign-born 21+ (all races) × 1940's FB-white-by-sex / FB-total ratio.
  163|     e = read('ds78', True)
  164|     fb40 = e[cols('BV8', 1, 6)].sum(axis=1)
  165|     fbw40 = {'M': e[cols('BWN', 1, 4)].sum(axis=1), 'F': e[cols('BWN', 5, 8)].sum(axis=1)}
  166|     fbw = {s: b.B4J002 * (fbw40[s] / fb40).reindex(b.index) for s in 'MF'}
  167|     # Citizenship: rake 1940's FB-white sex × (naturalized, alien incl. first papers, not reported)
  168|     # to the 1950 sex totals above and 1950's citizenship split of all FB 21+.
  169|     cz = {(s, k): pd.Series(np.nan, b.index) for s in 'MF' for k in range(3)}
  170|     for st in b.index:
  171|         seed = np.array([[e.at[st, 'BWN001'], e.at[st, 'BWN002'] + e.at[st, 'BWN003'], e.at[st, 'BWN004']],
  172|                          [e.at[st, 'BWN005'], e.at[st, 'BWN006'] + e.at[st, 'BWN007'], e.at[st, 'BWN008']]])
  173|         r = np.array([fbw['M'][st], fbw['F'][st]])
  174|         if np.isnan(seed).any() or np.isnan(r).any():
  175|             continue
  176|         k = b.loc[st, cols('B4K', 1, 3)].to_numpy(float)
  177|         t = ipf(seed, r, k / k.sum() * r.sum())
  178|         for i, s in enumerate('MF'):
  179|             for j in range(3):
  180|                 cz[(s, j)][st] = t[i, j]
  181|     ns = neg_share(1950)
  182|     T6, T18, T48, T9 = 'NHGIS 1950_cAge NT6', 'NHGIS 1950_cAge NT18', 'NHGIS 1950_cPHA NT48', 'NHGIS 1950_cPHA NT9A/NT9B'
  183|     fbnote = ('[I] 1950 foreign-born 21+ (NT9A, all races, both sexes) × 1940 state ratio of FB white by sex to all FB '
  184|               '(1940_cPHAE NT12/NT10); citizenship raked (IPF) from 1940 FB-white sex × citizenship to 1950 NT9B '
  185|               'all-FB citizenship split; 1950 "alien" includes first papers')
  186|     c21, c18 = {}, {}
  187|     for s in 'MF':
  188|         nb = wh[s] - fbw[s]
  189|         assert (nb.dropna() > 0).all(), '1950 native white < 0'
  190|         wnote = ('[I] white 21+ = NT6 total 21+ − nonwhite 21+ (NT48); sex split by NT18 bands with 20–24 split '
  191|                  'evenly by single year; minus estimated foreign-born white')
  192|         c21[(s, 'native_white')] = (nb, tab('White: Native-born', f'{T6}; {T48}; {T18}; {T9}', wnote))
  193|         for j, (g, lab) in enumerate((('foreign_white_naturalized', 'naturalized'), ('foreign_white_alien', 'alien'),
  194|                                       ('foreign_white_unknown', 'citizenship not reported'))):
  195|             c21[(s, g)] = (cz[(s, j)], tab(f'White: Foreign-born, {lab}', f'{T9}; NHGIS 1940_cPHAE NT10/NT12', fbnote))
  196|         nnote = ('[I] nonwhite 21+ by sex from NT48 (Alaska: NT18 bands, 20–24 split evenly); Negro share of nonwhite '
  197|                  'interpolated linearly 1940 (cAge NT7) → 1970 (Cnt1 NT19); Alaska 1970 share')
  198|         c21[(s, 'negro')] = (nw[s] * ns[s].reindex(nw[s].index), tab('Negro: Negro (est. from nonwhite)', f'{T48}; {T18}', nnote))
  199|         c21[(s, 'other_races')] = (nw[s] * (1 - ns[s].reindex(nw[s].index)),
  200|                                    tab('Other: Other races (est. from nonwhite)', f'{T48}; {T18}', nnote))
  201|         # 18–20 add-on
  202|         w18, n18 = band[('W', s, 18)], band[('N', s, 18)]
  203|         fsh = (fbw[s] / wh[s])
  204|         c18[(s, 'native_white')] = w18 * (1 - fsh)
  205|         for j, g in enumerate(('foreign_white_naturalized', 'foreign_white_alien', 'foreign_white_unknown')):
  206|             c18[(s, g)] = w18 * fsh * (cz[(s, j)] / fbw[s])
  207|         c18[(s, 'negro')] = n18 * ns[s].reindex(n18.index)
  208|         c18[(s, 'other_races')] = n18 * (1 - ns[s].reindex(n18.index))
  209|     note18 = ('; 18–20 [I]: NT18 bands, 2/5 of 15–19 + 1/5 of 20–24 (even single-year split), '
  210|               'nativity/citizenship/Negro shares as 21+')
  211|     return emit(1950, c21), add18(1950, c21, c18, note18)
  212| 
  213| 
  214| def add18(year, c21, c18, note18):
  215|     cells = {}
  216|     for k, (s, m) in c21.items():
  217|         n = m['note'] + note18 if m['note'].startswith('[I]') else '[I] 21+ ' + m['note'] + note18
  218|         cells[k] = (s + c18[k].reindex(s.index), dict(m, note=n))
  219|     return emit(year, cells)
  220| 
  221| 
  222| # ---------------------------------------------------------------- 1950 shares carried to 1960, 1970
  223| def fb_shares_1950():
  224|     """FB white share of white 21+, and citizenship split of FB white, by state × sex from the 1950 build.
  225|     Hawaii (no 1950 data): national 1950 shares."""
  226|     d = y1950()[0]
  227|     p = d.pivot_table(index=['state', 'sex'], columns='group', values='count', aggfunc='sum')
  228|     fbg = ['foreign_white_naturalized', 'foreign_white_alien', 'foreign_white_unknown']
  229|     p.loc[('HI', 'M'), :] = p.xs('M', level='sex').sum()
  230|     p.loc[('HI', 'F'), :] = p.xs('F', level='sex').sum()
  231|     fb = p[fbg].sum(axis=1)
  232|     share = fb / (fb + p['native_white'])
  233|     split = p[fbg].div(fb, axis=0)
  234|     return share, split
  235| 
  236| 
  237| def white_split(year, wh, w18, src, wnote, has18=True):
  238|     share, split = fb_shares_1950()
  239|     fbnote = (f'[I] white 21+ ({wnote}) × 1950 FB-white share of white 21+ and 1950 citizenship split, carried '
  240|               f'forward by state × sex (Hawaii: national 1950 shares); 1950 "alien" includes first papers')
  241|     c21, c18 = {}, {}
  242|     for s in 'MF':
  243|         sh = share.xs(s, level='sex').reindex(wh[s].index)
  244|         sp = split.xs(s, level='sex').reindex(wh[s].index)
  245|         c21[(s, 'native_white')] = (wh[s] * (1 - sh), tab('White: Native-born (est.)', src, fbnote))
  246|         c18[(s, 'native_white')] = w18[s] * (1 - sh)
  247|         for g, lab in (('foreign_white_naturalized', 'naturalized'), ('foreign_white_alien', 'alien'),
  248|                        ('foreign_white_unknown', 'citizenship not reported')):
  249|             c21[(s, g)] = (wh[s] * sh * sp[g], tab(f'White: Foreign-born, {lab} (est.)', src, fbnote))
  250|             c18[(s, g)] = w18[s] * sh * sp[g]
  251|     return c21, c18
  252| 
  253| 
  254| # ---------------------------------------------------------------- 1960
  255| @functools.lru_cache(None)
  256| def y1960():
  257|     a, b = read('ds89', True), read('ds91', True)
  258|     band = {}
  259|     for (race, s), o in ((('W', 'M'), 0), (('W', 'F'), 18), (('N', 'M'), 36), (('N', 'F'), 54)):
  260|         x = a[cols('B49', 1 + o, 18 + o)].fillna(0).to_numpy()
  261|         band[(race, s)] = x
  262|     for s, o in (('M', 0), ('F', 18)):
  263|         t = a[cols('B5F', 1 + o, 18 + o)].fillna(0).to_numpy()
  264|         gap = np.abs(band[('W', s)] + band[('N', s)] - t).max()
  265|         assert gap < 1, f'1960 {s}: NT11 white+nonwhite vs NT5 sex×age differ by {gap}'
  266|     est = {k: pd.Series(x[:, 5:].sum(axis=1) + 0.8 * x[:, 4], a.index) for k, x in band.items()}
  267|     e18 = {k: pd.Series(0.4 * x[:, 3] + 0.2 * x[:, 4], a.index) for k, x in band.items()}
  268|     for s, col in (('M', 'B5T001'), ('F', 'B5T002')):
  269|         r = est[('N', s)] / b[col] - 1
  270|         print(f'1960 nonwhite 21+ {s}: NT14 {b[col].sum():,.0f} vs band-split {est[("N", s)].sum():,.0f} '
  271|               f'(state rel. max {r.abs().max():.4f} {r.abs().idxmax()})')
  272|     T11, T14 = 'NHGIS 1960_cAge1 NT11', 'NHGIS 1960_cPop NT14'
  273|     wh = {s: est[('W', s)] for s in 'MF'}
  274|     w18 = {s: e18[('W', s)] for s in 'MF'}
  275|     c21, c18 = white_split(1960, wh, w18, f'{T11}; NHGIS 1950_cPHA NT9A/NT9B',
  276|                            'NT11 bands, 25+ plus 4/5 of 20–24, even single-year split')
  277|     ns = neg_share(1960)
  278|     nnote = '[I] nonwhite 21+ by sex tabulated (NT14); Negro share interpolated linearly 1940 (cAge NT7) → 1970 (Cnt1 NT19); AK, HI 1970 share'
  279|     for s, col in (('M', 'B5T001'), ('F', 'B5T002')):
  280|         c21[(s, 'negro')] = (b[col] * ns[s], tab('Negro: Negro (est. from nonwhite)', T14, nnote))
  281|         c21[(s, 'other_races')] = (b[col] * (1 - ns[s]), tab('Other: Other races (est. from nonwhite)', T14, nnote))
  282|         c18[(s, 'negro')] = e18[('N', s)] * ns[s]
  283|         c18[(s, 'other_races')] = e18[('N', s)] * (1 - ns[s])
  284|     note18 = ('; 18–20 [I]: NT11 bands, 2/5 of 15–19 + 1/5 of 20–24 (even single-year split), '
  285|               'nativity/citizenship/Negro shares as 21+')
  286|     return emit(1960, c21), add18(1960, c21, c18, note18)
  287| 
  288| 
  289| # ---------------------------------------------------------------- 1970
  290| @functools.lru_cache(None)
  291| def y1970():
  292|     c = c1970()
  293|     T18, T19 = 'NHGIS 1970_Cnt1 NT18', 'NHGIS 1970_Cnt1 NT19'
  294|     wh = {s: c[(s, 'tot21')] - c[(s, 'negro21')] - c[(s, 'other_races21')] for s in 'MF'}
  295|     w18 = {s: c[(s, 'tot18_20')] - c[(s, 'negro18_20')] - c[(s, 'other_races18_20')] for s in 'MF'}
  296|     for s in 'MF':
  297|         assert (wh[s] > 0).all() and (w18[s] > 0).all()
  298|     c21, c18 = white_split(1970, wh, w18, f'{T18}; {T19}; NHGIS 1950_cPHA NT9A/NT9B',
  299|                            'NT18 total 21+ minus NT19 Negro and other')
  300|     rnote = ('[I] NT19 25+ tabulated; 21–24 = NT19 15–24 band × (NT18 total 21–24 / total 15–24), '
  301|              'i.e. the band split by the total population\'s single-year shape')
  302|     for s in 'MF':
  303|         c21[(s, 'negro')] = (c[(s, 'negro21')], tab('Negro: Negro', T19 + '; ' + T18, rnote))
  304|         c21[(s, 'other_races')] = (c[(s, 'other_races21')], tab('Other: Other races', T19 + '; ' + T18, rnote))
  305|         c18[(s, 'negro')] = c[(s, 'negro18_20')]
  306|         c18[(s, 'other_races')] = c[(s, 'other_races18_20')]
  307|     note18 = ('; 18–20 [I]: total tabulated (NT18 single years), Negro/other = NT19 15–24 band × total 18–20 / 15–24, '
  308|               'white nativity/citizenship shares as 21+')
  309|     return emit(1970, c21), add18(1970, c21, c18, note18)
  310| 
  311| 
  312| BUILDERS = {1940: lambda y: y1940(), 1950: lambda y: y1950()[0], 1960: lambda y: y1960()[0], 1970: lambda y: y1970()[0]}
  313| BUILDERS18 = {1950: lambda y: y1950()[1], 1960: lambda y: y1960()[1], 1970: lambda y: y1970()[1]}
  314| 
  315| 
  316| if __name__ == '__main__':
  317|     years = [int(y) for y in sys.argv[1:]] or [1940, 1950, 1960, 1970]
  318|     for y in years:
  319|         for name, B in ((f'adults_{y}_by_state_nhgis.csv', BUILDERS), (f'adults18_{y}_by_state_nhgis.csv', BUILDERS18)):
  320|             if y not in B:
  321|                 continue
  322|             df = B[y](y)
  323|             assert (df['count'] >= 0).all(), f'{name}: negative counts'
  324|             df.to_csv(CACHE / 'population' / name, index=False)
  325|             est = df[df.note.str.startswith('[I]')]['count'].sum()
  326|             print(f'wrote {name}: {len(df)} rows, {df.state.nunique()} states, {df["count"].sum():,.0f} '
  327|                   f'({df[df.sex == "F"]["count"].sum():,.0f} women; {est / df["count"].sum():.0%} of count in [I] rows)')
```

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

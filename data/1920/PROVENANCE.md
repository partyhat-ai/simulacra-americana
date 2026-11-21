# 1920 inputs: provenance and licences

These files are everything the 1920 backbone and its validation checks read
(R1, B1–B5, N1–N2 in `EVAL.md`). With them, anyone can rerun the 1920
results without the private cache, an NHGIS account or IPUMS:

```sh
SIMHARNESS_CACHE=data/1920 python3 -m simharness.run backbone --config configs/prototype-1920.json
SIMHARNESS_CACHE=data/1920 python3 -m simharness.run evaluate --config configs/prototype-1920.json
```

Checked on 2026-11-20: this folder and the full private cache give identical
results, and `EVAL.md`'s numbers come from this folder (`runs/1920-2c8ce73571`; its
"Run" note has the four commands that rerun the whole table).

Not here, because the backbone doesn't read them: the interviews' newspaper
corpus (`sources/corpus_1920.jsonl`) and party platforms
(`context/platforms_1920.json`). Nothing here comes from NHGIS or IPUMS; those
extracts stay out of the repo (`docs/DEPLOY.md`, "Census data").

## Licences

| File | Licence | Why |
|---|---|---|
| `population/*.csv` | Public domain | U.S. Census Bureau publications (works of the U.S. government, 17 U.S.C. § 105) |
| `franchise/state_franchise_1920.csv` | CC0 1.0 | Gray & Jenkins and Teele datasets (both CC0); notes cite National Park Service pages (public domain) |
| `franchise/women_suffrage_pre19th.csv` | CC0 1.0 | Teele dataset (CC0) |
| `benchmarks/corder_wolbrecht_turnout_by_sex.csv` | CC0 1.0 | Corder & Wolbrecht dataset (CC0) |
| `labels/state_pres_1916_1920_1924.csv` | **CC BY-SA 4.0** | Includes figures from Wikipedia (see below); its other columns come from Algara & Amlani (CC0), the House Clerk and NARA (public domain) |

The repo's MIT licence covers its code, not these files.

**Attribution for `labels/state_pres_1916_1920_1924.csv`.** The `wp_*`
columns, and the `total` (so `other`) in the state-years whose `value_source`
names Wikipedia (15 in 1920, 12 in 1924, 6 in 1916), are adapted from the
results-by-state tables of the English Wikipedia articles "1916 United States
presidential election" (revision 1375915930), "1920 United States presidential
election" (revision 1374763539) and "1924 United States presidential election"
(revision 1377402879), by Wikipedia contributors, licensed CC BY-SA 4.0
(https://creativecommons.org/licenses/by-sa/4.0/). Wikipedia credits those
tables to Dave Leip's Atlas of U.S. Presidential Elections. This file is shared
under the same licence.

## Sources

### Census: `population/`
U.S. Census Bureau, *Fourteenth Census of the United States Taken in the Year
1920*, Vol. III, Population: Composition and Characteristics (1922), and
*Abstract of the Fourteenth Census* (1923). PDFs from
https://www2.census.gov/library/publications/decennial/1920/ (retrieved 2026-09-30).

- **`adults_1920_by_state.csv`**: each state's Vol. III Table 5, "Population 21
  years of age and over, by sex, class of population, and citizenship": Male and
  Female 1920.
- **`adults_1910_by_state.csv`**: the 1910 columns those tables reprint (Male 1910),
  and each state's Table 4 for 1910 females. These are the 1910 enumeration counts,
  published in 1912–13.
- **`urban_rural_1920_by_state.csv`**: Abstract, Population Table 15 (urban and rural
  by state) and Agriculture Table 3 (farm population).

The scans have no usable text layer; machine OCR misread this typeface (3/8, 9/0,
5/6). Every number was transcribed cell by cell from the 300-dpi page images, and
none was typed from memory. Checks, all passing exactly with no tolerance:
- In every state and column: Total = sum of races, White = native + foreign-born,
  and foreign-born white = naturalized + first papers + alien + unknown.
- The 49 state sums equal the printed United States Table 5 in all 48 cells.
- The 1910 female totals equal the printed U.S. figure (24,555,754).
- Urban + rural = total in every state.
- The table also matches NHGIS's 1920 state tables exactly (`DISCLOSURES.md` C17).

National 1920 totals (21 and over): men 31,403,370; women 29,483,150.

### Returns: `labels/state_pres_1916_1920_1924.csv`
- **Algara, C. & Amlani, S.**, county presidential returns 1868–2020,
  doi:10.7910/DVN/DGUMFI (Harvard Dataverse v1.1, CC0). This is the default:
  the county sum.
- **U.S. House, Office of the Clerk**, *Statistics of the Presidential and
  Congressional Election* (1921, 1925), history.house.gov. Where the county sum
  differs from the Clerk by more than 0.5% on R or D, the Clerk's R and D are used
  (`value_source`). The transcribed recap columns sum exactly to the printed
  totals (1920: 16,147,249 R; 9,140,864 D; 531 EV).
- **National Archives**, Electoral College results 1920, archives.gov: the
  electoral votes (`nara_ev_*`).
- **Wikipedia**, as attributed above: the total vote where the Clerk is used (the
  Clerk prints no state totals), and the `wp_*` comparison columns.

Every discrepancy and the decision rule are recorded in the file's `note` and
`value_source` columns. National 1920 totals as chosen: Harding 16,145,577; Cox
9,142,289; other 1,511,118; total 26,798,984.

### Franchise: `franchise/`
- **Gray, T. & Jenkins, J.**, state-level franchise data, doi:10.7910/DVN/QIY9EM
  (CC0): poll tax, literacy test, secret ballot, ex-felon rules and women's vote,
  for 1920.
- **Teele, D.**, women's suffrage replication data, doi:10.7910/DVN/EVYI2H, checked
  against doi:10.7910/DVN/JZYGRB (both CC0). Teele hand-coded the dates from
  Keyssar (2000), Tables A.17–A.18. Arkansas and Texas granted only primary
  suffrage, so their presidential year is NA.
- **National Park Service**, "Georgia and the 19th Amendment" and "Mississippi and
  the 19th Amendment" (nps.gov): women in GA and MS could not register in time for
  November 1920 (`women_able_to_vote_nov1920 = 0`).

### Held-out benchmark: `benchmarks/`
**Corder, J. K. & Wolbrecht, C.**, turnout by sex, 1920 and 1924,
doi:10.7910/DVN/QB526J (CC0). Only the evaluate stage reads it
(`test_benchmarks_isolated`).

## File hashes

Written by `scripts/harness/data_1920_hashes.py --write`; checked by `tests/test_data_1920.py`.

<!-- hashes:start -->
| File | Bytes | sha256 |
|---|---|---|
| `benchmarks/corder_wolbrecht_turnout_by_sex.csv` | 7981 | `66bbd07dc8a5b5c6774cd2d2011e3d28e4a8bfe36fb121fee9ae89f23141897a` |
| `franchise/state_franchise_1920.csv` | 14998 | `e70f04ec2c75e64472de9c30d7d04fa888e2cf1d54726c2a8560ef060efb71c1` |
| `franchise/women_suffrage_pre19th.csv` | 10779 | `54da193f57a1e799d6bcd39a98d44b846ffccb29eb5505c6e3c7261ec0031a4d` |
| `labels/state_pres_1916_1920_1924.csv` | 29225 | `39b0dbc19249663ad64548d84e0bf1135506d11a82175c48f23d1c355e6d5794` |
| `population/adults_1910_by_state.csv` | 365922 | `78ec7a0ca2094430f5350cf04999fe9fe84249921f61fa40dd4bf9c9d4b87de1` |
| `population/adults_1920_by_state.csv` | 441664 | `3a760fb7fb5f976b8db8d76068b1e4de554495e6a330100c54339d0b0c9841ee` |
| `population/urban_rural_1920_by_state.csv` | 137287 | `c703c252af31ab600a3b7579e2e9e696aec1c69fae7d186ac63267153bdcd822` |
<!-- hashes:end -->

# synthetic-electorate-toy: source and docs, part 13 of 16

Generated from commit `c4694839a0a9` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `src/lib/simulacra/format.ts` to `src/lib/simulacra/runs.ts`. Lines are numbered as in the repository.

## `src/lib/simulacra/format.ts`

```ts
    1| // Number formats for Simulacra Americana.
    2| const compact = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
    3| 
    4| /** 4100000 → "4.1M"; a missing or non-finite number → "—". */
    5| export const fmtCompact = (n: number | null | undefined): string =>
    6|   n != null && Number.isFinite(n) ? compact.format(n) : '—';
```

## `src/lib/simulacra/geo.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { ELECTION_YEARS, GRID, STATE_BY_CODE, STATES } from './geo';
    3| import { segments } from './places';
    4| 
    5| describe('geo', () => {
    6|   test('60 elections, every four years from 1792, 1789 first', () => {
    7|     expect(ELECTION_YEARS.length).toBe(60);
    8|     expect(ELECTION_YEARS[0]).toBe(1789);
    9|     expect(ELECTION_YEARS.at(-1)).toBe(2024);
   10|     for (let i = 2; i < ELECTION_YEARS.length; i++) expect((ELECTION_YEARS[i] ?? 0) - (ELECTION_YEARS[i - 1] ?? 0)).toBe(4);
   11|   });
   12| 
   13|   test('the grid covers every state, one tile each', () => {
   14|     expect(STATES.length).toBe(51);
   15|     const cells = new Set<string>();
   16|     for (const s of STATES) {
   17|       expect(s.row, s.code).toBeGreaterThanOrEqual(0);
   18|       expect(s.row, s.code).toBeLessThan(GRID.rows);
   19|       expect(s.col, s.code).toBeGreaterThanOrEqual(0);
   20|       expect(s.col, s.code).toBeLessThan(GRID.cols);
   21|       cells.add(`${s.row},${s.col}`);
   22|     }
   23|     expect(cells.size).toBe(STATES.length);
   24|     expect(STATE_BY_CODE.size).toBe(STATES.length);
   25|   });
   26| });
   27| 
   28| describe('places', () => {
   29|   test('state names and regions become pointable runs', () => {
   30|     const parts = segments('New Hampshire and the Deep South went for him.');
   31|     expect(parts.map((p) => p.t)).toEqual(['New Hampshire', ' and the ', 'Deep South', ' went for him.']);
   32|     expect(parts[0]?.codes).toEqual(['NH']);
   33|     expect(parts[2]?.codes).toContain('MS');
   34|   });
   35| 
   36|   test('George Washington is a man; the District of Columbia is a district', () => {
   37|     expect(segments('George Washington won.').every((p) => !p.codes)).toBe(true);
   38|     expect(segments('District of Columbia voted.')[0]?.codes).toEqual(['DC']);
   39|     expect(segments('Washington state voted.')[0]?.codes).toEqual(['WA']);
   40|   });
   41| });
```

## `src/lib/simulacra/geo.ts`

```ts
    1| // Simulacra Americana's geography: every election year, and the tile map's
    2| // grid with the year each state first cast electoral votes. Who won what is
    3| // in history.ts.
    4| 
    5| /** Every presidential election, 1788–89 (drawn as 1789) to 2024. */
    6| export const ELECTION_YEARS: readonly number[] = [1789, ...Array.from({ length: 59 }, (_, i) => 1792 + i * 4)];
    7| 
    8| export interface UsState {
    9|   readonly code: string;
   10|   readonly name: string;
   11|   /** Tile row and column on the map grid. */
   12|   readonly row: number;
   13|   readonly col: number;
   14|   /** The first presidential election the state cast electoral votes in. */
   15|   readonly first: number;
   16| }
   17| 
   18| // [code, name, row, col, first presidential election cast]. A 12 × 8 square
   19| // tile grid, west to east, north to south; `first` is the first election
   20| // after admission (a state admitted before Election Day votes that year).
   21| type Raw = readonly [code: string, name: string, row: number, col: number, first: number];
   22| const RAW: readonly Raw[] = [
   23|   ['AK', 'Alaska', 0, 0, 1960], ['ME', 'Maine', 0, 11, 1820],
   24|   ['WI', 'Wisconsin', 1, 6, 1848], ['VT', 'Vermont', 1, 10, 1792], ['NH', 'New Hampshire', 1, 11, 1789],
   25|   ['WA', 'Washington', 2, 1, 1892], ['ID', 'Idaho', 2, 2, 1892], ['MT', 'Montana', 2, 3, 1892], ['ND', 'North Dakota', 2, 4, 1892],
   26|   ['MN', 'Minnesota', 2, 5, 1860], ['IL', 'Illinois', 2, 6, 1820], ['MI', 'Michigan', 2, 7, 1840], ['NY', 'New York', 2, 9, 1789],
   27|   ['MA', 'Massachusetts', 2, 10, 1789],
   28|   ['OR', 'Oregon', 3, 1, 1860], ['NV', 'Nevada', 3, 2, 1864], ['WY', 'Wyoming', 3, 3, 1892], ['SD', 'South Dakota', 3, 4, 1892],
   29|   ['IA', 'Iowa', 3, 5, 1848], ['IN', 'Indiana', 3, 6, 1816], ['OH', 'Ohio', 3, 7, 1804], ['PA', 'Pennsylvania', 3, 8, 1789],
   30|   ['NJ', 'New Jersey', 3, 9, 1789], ['CT', 'Connecticut', 3, 10, 1789], ['RI', 'Rhode Island', 3, 11, 1792],
   31|   ['CA', 'California', 4, 1, 1852], ['UT', 'Utah', 4, 2, 1896], ['CO', 'Colorado', 4, 3, 1876], ['NE', 'Nebraska', 4, 4, 1868],
   32|   ['MO', 'Missouri', 4, 5, 1824], ['KY', 'Kentucky', 4, 6, 1792], ['WV', 'West Virginia', 4, 7, 1864], ['VA', 'Virginia', 4, 8, 1789],
   33|   ['MD', 'Maryland', 4, 9, 1789], ['DE', 'Delaware', 4, 10, 1789],
   34|   ['AZ', 'Arizona', 5, 2, 1912], ['NM', 'New Mexico', 5, 3, 1912], ['KS', 'Kansas', 5, 4, 1864], ['AR', 'Arkansas', 5, 5, 1836],
   35|   ['TN', 'Tennessee', 5, 6, 1796], ['NC', 'North Carolina', 5, 7, 1792], ['SC', 'South Carolina', 5, 8, 1789],
   36|   ['DC', 'District of Columbia', 5, 9, 1964],
   37|   ['OK', 'Oklahoma', 6, 4, 1908], ['LA', 'Louisiana', 6, 5, 1812], ['MS', 'Mississippi', 6, 6, 1820], ['AL', 'Alabama', 6, 7, 1820],
   38|   ['GA', 'Georgia', 6, 8, 1789],
   39|   ['HI', 'Hawaii', 7, 0, 1960], ['TX', 'Texas', 7, 4, 1848], ['FL', 'Florida', 7, 8, 1848],
   40| ];
   41| 
   42| export const STATES: readonly UsState[] = RAW.map(([code, name, row, col, first]) => ({ code, name, row, col, first }));
   43| export const STATE_BY_CODE: ReadonlyMap<string, UsState> = new Map(STATES.map((s) => [s.code, s]));
   44| export const GRID = { cols: 12, rows: 8 } as const;
```

## `src/lib/simulacra/groups.ts`

```ts
    1| // The five voter groups every simulated year is built from, in the order the
    2| // page shows them, and why a year can be missing one. Thirteen years
    3| // (1789-1836) have no immigrant group; 1864 has no Southern ones. On a narrow
    4| // window the page holds a missing group's place with an AbsentRow, so every
    5| // year shows five rows and nothing under them moves with the year.
    6| import type { Slice } from './schemas';
    7| 
    8| export const GROUP_ORDER = ['men', 'women', 'south-white', 'black-south', 'immigrants'] as const;
    9| /** Each group is drawn as this many people, a row of dots (SliceRow; AbsentRow's rule spans as many). */
   10| export const DOTS = 50;
   11| const IN_ORDER: ReadonlySet<string> = new Set(GROUP_ORDER);
   12| 
   13| export interface Absent {
   14|   readonly key: string;
   15|   readonly label: string;
   16|   readonly why: string;
   17| }
   18| 
   19| // One line each, so a held row is as tall as a group's.
   20| const CONFEDERACY = 'Didn’t vote: the Confederacy had seceded.';
   21| 
   22| const ABSENT: Readonly<Record<string, Omit<Absent, 'key'>>> = {
   23|   immigrants: { label: 'Immigrants not yet citizens', why: 'Not counted in the census data before 1840.' },
   24|   'south-white': { label: 'White Southerners', why: CONFEDERACY },
   25|   'black-south': { label: 'Black Southerners, most of them enslaved', why: CONFEDERACY },
   26| };
   27| 
   28| /** The year's groups in GROUP_ORDER, each missing one replaced by its Absent (any group outside the order kept, last). */
   29| export function withAbsent(slices: readonly Slice[]): (Slice | Absent)[] {
   30|   const byKey = new Map(slices.map((s) => [s.key, s]));
   31|   const rows: (Slice | Absent)[] = [];
   32|   for (const key of GROUP_ORDER) {
   33|     const s = byKey.get(key);
   34|     if (s) rows.push(s);
   35|     else if (ABSENT[key]) rows.push({ key, ...ABSENT[key] });
   36|   }
   37|   for (const s of slices) if (!IN_ORDER.has(s.key)) rows.push(s);
   38|   return rows;
   39| }
   40| 
   41| export const isAbsent = (row: Slice | Absent): row is Absent => 'why' in row;
```

## `src/lib/simulacra/header.ts`

```ts
    1| // The election header's derived text and colours: who gets which paint, the
    2| // names the dots and map use, the "Also ran" line and the map's label.
    3| import type { Candidate, Election } from './history';
    4| import { candidateHues, onPaint, paint } from './palette';
    5| import type { Colors, MapState, Names } from './types';
    6| 
    7| export interface Paints {
    8|   readonly colors: Colors;
    9|   /** The check's colour on the winner's and runner-up's rings. */
   10|   readonly inks: Readonly<Record<'A' | 'B', string>>;
   11| }
   12| 
   13| /** The winner's and runner-up's party colours and everyone else's grey, for the mode. */
   14| export function paintsOf(election: Election, light: boolean): Paints {
   15|   const hues = candidateHues(
   16|     election.candidates.map((c) => ({ key: c.key, party: c.family })),
   17|     Object.fromEntries(election.candidates.map((c) => [c.key, c.ev])),
   18|   );
   19|   const a = hues.get('A');
   20|   const b = hues.get('B') ?? 'other';
   21|   return {
   22|     colors: { A: paint(a, light), B: paint(b, light), O: paint('other', light) },
   23|     inks: { A: onPaint(a, light), B: onPaint(b, light) },
   24|   };
   25| }
   26| 
   27| export function namesOf(election: Election): Names {
   28|   const [a, b, ...others] = election.candidates;
   29|   const only = others.length === 1 ? others[0] : undefined;
   30|   return { A: a.short, B: b?.short, O: only ? only.short : 'Others' };
   31| }
   32| 
   33| /** Everyone else who won electoral votes or a real share of the vote. */
   34| export function alsoRanOf(others: readonly Candidate[]): string {
   35|   const won = others.filter((c) => c.ev > 0).map((c) => `${c.name} ${c.ev}`);
   36|   const polled = others.filter((c) => !(c.ev > 0) && (c.popular ?? 0) >= 5).map((c) => `${c.name} ${c.popular}% of the vote`);
   37|   const one = won.length === 1 && others.find((c) => c.ev > 0)?.ev === 1;
   38|   return [won.length ? `${won.join(', ')} electoral vote${one ? '' : 's'}` : '', polled.join(', ')].filter(Boolean).join(' · ');
   39| }
   40| 
   41| /** The map's spoken label: how many states each candidate carried, and how many flipped. */
   42| export function mapLabelOf(year: number, rerun: boolean, election: Election, states: readonly MapState[], flips: number): string {
   43|   const carried = (c: Candidate) =>
   44|     states.filter((s) => (c.key === 'A' || c.key === 'B' ? s.won === c.key : s.won !== 'A' && s.won !== 'B' && s.won === c.key))
   45|       .length;
   46|   return (
   47|     `Map of ${rerun ? `your ${year}` : year}: ` +
   48|     election.candidates.map((c) => `${c.short} carried ${carried(c)} states`).join(', ') +
   49|     (flips ? `; ${flips} flipped` : '')
   50|   );
   51| }
```

## `src/lib/simulacra/history.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { assetUrl } from '$lib/robot/assets';
    3| import { ELECTION_YEARS, STATE_BY_CODE } from './geo';
    4| import { electionOf, FEATURED, wikiUrl } from './history';
    5| 
    6| // Years whose per-state electoral votes don't sum to the electoral votes cast,
    7| // with the per-state sum the table holds: these list the electors each state
    8| // was allotted, not those who voted (1789: New York chose none; 1864: one
    9| // Nevada elector didn't vote). Pinned so a data change shows.
   10| const ALLOTTED_NOT_CAST: Readonly<Record<number, number>> = {
   11|   1789: 73,
   12|   1792: 135,
   13|   1808: 176,
   14|   1812: 218,
   15|   1816: 221,
   16|   1820: 236,
   17|   1832: 288,
   18|   1864: 234,
   19| };
   20| 
   21| // States whose votes were counted before geo.ts's `first` year (both were
   22| // counted "in the alternative" before admission), so the map leaves their
   23| // tile empty that year. Pinned until the data owner decides which is right.
   24| const COUNTED_EARLY: ReadonlySet<string> = new Set(['1820 MO', '1836 MI']);
   25| 
   26| describe('electionOf', () => {
   27|   test.each(ELECTION_YEARS)('%i: 51 or fewer real states, a majority, electors summing to the total', (y) => {
   28|     const e = electionOf(y);
   29|     expect(e).not.toBeNull();
   30|     if (!e) return;
   31|     expect(e.year).toBe(y);
   32|     expect(e.states.length).toBeLessThanOrEqual(51);
   33|     expect(new Set(e.states.map((s) => s.code)).size).toBe(e.states.length);
   34|     for (const s of e.states) {
   35|       expect(STATE_BY_CODE.has(s.code), s.code).toBe(true);
   36|       // A state votes only once it's in the Union.
   37|       if (!COUNTED_EARLY.has(`${y} ${s.code}`)) expect(STATE_BY_CODE.get(s.code)?.first, s.code).toBeLessThanOrEqual(y);
   38|       expect(s.ev, s.code).toBeGreaterThan(0);
   39|     }
   40|     expect(e.majority).toBe(Math.floor(e.total / 2) + 1);
   41|     const sum = e.states.reduce((a, s) => a + s.ev, 0);
   42|     expect(sum).toBe(ALLOTTED_NOT_CAST[y] ?? e.total);
   43|   });
   44| 
   45|   test('the winner is A, the runner-up B, and unopposed years have no B', () => {
   46|     for (const y of ELECTION_YEARS) {
   47|       const e = electionOf(y);
   48|       if (!e) continue;
   49|       expect(e.candidates[0].key).toBe('A');
   50|       expect(e.unopposed).toBe(e.candidates[1]?.key !== 'B');
   51|     }
   52|     expect(ELECTION_YEARS.filter((y) => electionOf(y)?.unopposed)).toEqual([1789, 1792, 1820]);
   53|   });
   54| 
   55|   test('a year with no election is null; story years are elections', () => {
   56|     expect(electionOf(1790)).toBeNull();
   57|     for (const y of FEATURED) expect(electionOf(y)).not.toBeNull();
   58|   });
   59| 
   60|   test('every winner and runner-up has a name and a portrait on the assets host', () => {
   61|     for (const y of ELECTION_YEARS) {
   62|       for (const c of electionOf(y)?.candidates.slice(0, 2) ?? []) {
   63|         expect(c.name.length, `${y} ${c.key}`).toBeGreaterThan(0);
   64|         expect(c.portrait, `${y} ${c.key}`).toBe(assetUrl(`portraits/${c.id}.jpg`));
   65|       }
   66|     }
   67|   });
   68| 
   69|   test('every candidate links to the Wikipedia article titled with their name', () => {
   70|     for (const y of ELECTION_YEARS) {
   71|       for (const c of electionOf(y)?.candidates ?? []) {
   72|         expect(c.wiki, `${y} ${c.key}`).toMatch(/^https:\/\/en\.wikipedia\.org\/wiki\/[^\s/?#]+$/);
   73|         if (c.id !== 'stevenson') expect(decodeURIComponent(c.wiki.slice(30)).replace(/_/g, ' ')).toBe(c.name);
   74|       }
   75|     }
   76|   });
   77| 
   78|   test('a name that titles a disambiguation page links to the right article', () => {
   79|     expect(electionOf(1952)?.candidates[1]?.wiki).toBe('https://en.wikipedia.org/wiki/Adlai_Stevenson_II');
   80|     expect(wikiUrl(null, 'Adlai Stevenson')).toBe('https://en.wikipedia.org/wiki/Adlai_Stevenson');
   81|     expect(wikiUrl('lincoln', 'Abraham Lincoln')).toBe('https://en.wikipedia.org/wiki/Abraham_Lincoln');
   82|   });
   83| });
```

## `src/lib/simulacra/history.ts`

```ts
    1| // Every presidential election from 1789 to 2024 as it happened: who ran, who
    2| // won, the electoral and popular vote, and which party carried each state.
    3| // This is the page's starting point, the truth every rerun is measured
    4| // against, so it ships with the page rather than coming from the simulation
    5| // server, and the page can show who won before anything else answers.
    6| //
    7| // Sources: results and notes, the standard record (the National Archives'
    8| // Electoral College tables, each election's Wikipedia article); each state's
    9| // winner, Wikipedia's "List of United States presidential election results by
   10| // state"; electoral votes by state, the House apportionments plus two (D.C.
   11| // three). Portraits: the lead image of each candidate's Wikipedia article,
   12| // from Wikimedia Commons, mirrored to the assets bucket as portraits/<id>.jpg
   13| // by scripts/mirror-portraits.py; the portrait links to the article.
   14| import { assetUrl } from '$lib/robot/assets';
   15| import { STATES } from './geo';
   16| import type { Family } from './palette';
   17| 
   18| // Each candidate's Wikipedia article: their name is its exact title (checked
   19| // against the Wikipedia API), except where it names a
   20| // disambiguation page.
   21| const WIKI = 'https://en.wikipedia.org/wiki/';
   22| const WIKI_TITLE: Readonly<Partial<Record<PersonId, string>>> = { stevenson: 'Adlai Stevenson II' };
   23| /** The candidate's Wikipedia article. */
   24| export const wikiUrl = (id: PersonId | null, name: string): string =>
   25|   WIKI + encodeURIComponent(((id && WIKI_TITLE[id]) || name).replace(/ /g, '_'));
   26| 
   27| // Party codes (the by-state table's) → label and the palette family
   28| // (palette.ts candidateHues) that sets the colour.
   29| const PARTIES = {
   30|   GW: ['No party', null],
   31|   F: ['Federalist', 'federalist'],
   32|   DR: ['Democratic-Republican', 'democratic-republican'],
   33|   DR2: ['Democratic-Republican', 'democratic-republican'],
   34|   Adams: ['Democratic-Republican', 'democratic-republican'],
   35|   Jackson: ['Democratic-Republican', 'democratic-republican'],
   36|   Crawford: ['Democratic-Republican', 'democratic-republican'],
   37|   Clay: ['Democratic-Republican', 'democratic-republican'],
   38|   D: ['Democratic', 'democratic'],
   39|   NR: ['National Republican', 'national-republican'],
   40|   W: ['Whig', 'whig'], W2: ['Whig', 'whig'], W3: ['Whig', 'whig'], W4: ['Whig', 'whig'],
   41|   N: ['Nullifier', null],
   42|   AM: ['Anti-Masonic', null],
   43|   FS: ['Free Soil', null],
   44|   KN: ['American', null],
   45|   R: ['Republican', 'republican'],
   46|   SD: ['Southern Democratic', 'democratic'],
   47|   ND: ['Northern Democratic', 'democratic'],
   48|   CU: ['Constitutional Union', null],
   49|   LR: ['Liberal Republican', 'democratic'],
   50|   PO: ['Populist', null],
   51|   BM: ['Progressive', null],
   52|   PR: ['Progressive', null],
   53|   S: ['Socialist', null],
   54|   SR: ['States’ Rights', null],
   55|   PG: ['Progressive', null],
   56|   I: ['Unpledged electors', null],
   57|   AI: ['American Independent', null],
   58|   IA: ['Independent', null],
   59|   IP: ['Independent', null],
   60|   RF: ['Reform', null],
   61|   SP: ['Split', null],
   62| } as const satisfies Record<string, readonly [string, Family | null]>;
   63| type PartyCode = keyof typeof PARTIES;
   64| const PARTY_BY_CODE: ReadonlyMap<string, readonly [string, Family | null]> = new Map(Object.entries(PARTIES));
   65| 
   66| // [full name, surname, Commons thumbnail path (the source scripts/mirror-portraits.py
   67| // mirrors to portraits/<id>.jpg)].
   68| const PEOPLE = {
   69|   washington: ["George Washington", "Washington", "b/b6/Gilbert_Stuart_Williamstown_Portrait_of_George_Washington.jpg/330px-Gilbert_Stuart_Williamstown_Portrait_of_George_Washington.jpg"],
   70|   adams: ["John Adams", "Adams", "7/75/John_Adams_Portrait.jpg/330px-John_Adams_Portrait.jpg"],
   71|   jefferson: ["Thomas Jefferson", "Jefferson", "0/07/Official_Presidential_portrait_of_Thomas_Jefferson_%28by_Rembrandt_Peale%2C_1800%29.jpg/330px-Official_Presidential_portrait_of_Thomas_Jefferson_%28by_Rembrandt_Peale%2C_1800%29.jpg"],
   72|   pinckney: ["Charles Cotesworth Pinckney", "Pinckney", "4/45/James_Earl_-_General_Charles_Cotesworth_Pinckney_-_Google_Art_Project.jpg/330px-James_Earl_-_General_Charles_Cotesworth_Pinckney_-_Google_Art_Project.jpg"],
   73|   madison: ["James Madison", "Madison", "1/1d/James_Madison.jpg/330px-James_Madison.jpg"],
   74|   clinton: ["DeWitt Clinton", "Clinton", "6/63/DeWitt_Clinton_by_Rembrandt_Peale.jpg/330px-DeWitt_Clinton_by_Rembrandt_Peale.jpg"],
   75|   monroe: ["James Monroe", "Monroe", "5/5e/James_Monroe_White_House_portrait_1819_%28cropped%29%282%29.jpg/330px-James_Monroe_White_House_portrait_1819_%28cropped%29%282%29.jpg"],
   76|   king: ["Rufus King", "King", "5/59/Gilbert_Stuart_-_Portrait_of_Rufus_King_%281819-1820%29_-_Google_Art_Project.jpg/330px-Gilbert_Stuart_-_Portrait_of_Rufus_King_%281819-1820%29_-_Google_Art_Project.jpg"],
   77|   adams2: ["John Quincy Adams", "Adams", "3/3a/JQA_Photo_Crop_%28cropped%29.jpg/330px-JQA_Photo_Crop_%28cropped%29.jpg"],
   78|   jackson: ["Andrew Jackson", "Jackson", "2/2a/Andrew_jackson_head_%28cropped%29.jpg/330px-Andrew_jackson_head_%28cropped%29.jpg"],
   79|   clay: ["Henry Clay", "Clay", "6/67/Clay_1848.jpg/330px-Clay_1848.jpg"],
   80|   vanburen: ["Martin Van Buren", "Van Buren", "7/72/Martin_Van_Buren_by_Mathew_Brady_c1855-58-%284%29.jpg/330px-Martin_Van_Buren_by_Mathew_Brady_c1855-58-%284%29.jpg"],
   81|   harrison: ["William Henry Harrison", "Harrison", "2/2c/William_Henry_Harrison_crop.jpg/330px-William_Henry_Harrison_crop.jpg"],
   82|   polk: ["James K. Polk", "Polk", "f/f3/James_K._Polk_restored_%283x4_cropped%29.jpg/330px-James_K._Polk_restored_%283x4_cropped%29.jpg"],
   83|   taylor: ["Zachary Taylor", "Taylor", "3/35/Zachary_Taylor_restored_and_cropped_%283.5x4.5_cropped%29_%282%29.jpg/330px-Zachary_Taylor_restored_and_cropped_%283.5x4.5_cropped%29_%282%29.jpg"],
   84|   cass: ["Lewis Cass", "Cass", "a/ae/Lewis_Cass_circa_1855.jpg/330px-Lewis_Cass_circa_1855.jpg"],
   85|   pierce: ["Franklin Pierce", "Pierce", "7/74/Mathew_Brady_-_Franklin_Pierce_-_alternate_crop_%28cropped%29%282%29.jpg/330px-Mathew_Brady_-_Franklin_Pierce_-_alternate_crop_%28cropped%29%282%29.jpg"],
   86|   scott: ["Winfield Scott", "Scott", "5/5f/Winfield_Scott_by_Fredricks%2C_1862_crop.jpg/330px-Winfield_Scott_by_Fredricks%2C_1862_crop.jpg"],
   87|   buchanan: ["James Buchanan", "Buchanan", "2/21/James_Buchanan_%28cropped%29.jpg/330px-James_Buchanan_%28cropped%29.jpg"],
   88|   frmont: ["John C. Frémont", "Frémont", "b/b3/John_Charles_Fremont_Oval.png/330px-John_Charles_Fremont_Oval.png"],
   89|   lincoln: ["Abraham Lincoln", "Lincoln", "a/ab/Abraham_Lincoln_O-77_matte_collodion_print.jpg/330px-Abraham_Lincoln_O-77_matte_collodion_print.jpg"],
   90|   breckinridge: ["John C. Breckinridge", "Breckinridge", "6/65/John_C._Breckinridge_1860_portrait_%283x4_cropped%29.jpg/330px-John_C._Breckinridge_1860_portrait_%283x4_cropped%29.jpg"],
   91|   mcclellan: ["George B. McClellan", "McClellan", "8/86/George_B_McClellan_-_retouched%2C_cropped.jpg/330px-George_B_McClellan_-_retouched%2C_cropped.jpg"],
   92|   grant: ["Ulysses S. Grant", "Grant", "9/98/Ulysses_S._Grant_1870-1880_%28cropped%29.jpg/330px-Ulysses_S._Grant_1870-1880_%28cropped%29.jpg"],
   93|   seymour: ["Horatio Seymour", "Seymour", "6/6e/Horatio_Seymour_%28cropped%2C_retouched%29.jpg/330px-Horatio_Seymour_%28cropped%2C_retouched%29.jpg"],
   94|   greeley: ["Horace Greeley", "Greeley", "1/11/Horace_Greeley_restored.jpg/330px-Horace_Greeley_restored.jpg"],
   95|   hayes: ["Rutherford B. Hayes", "Hayes", "5/50/President_Rutherford_Hayes_1870_-_1880_Restored.jpg/330px-President_Rutherford_Hayes_1870_-_1880_Restored.jpg"],
   96|   tilden: ["Samuel J. Tilden", "Tilden", "e/e8/Samuel_Tilden._Portrait_of_the_American_politician%2C_who_served_as_the_25th_Governor_of_New_York%2C_Samuel_Jones_Tilden_%281814-1886%29%2C_by_Jos%C3%A9_Mar%C3%ADa_Mora%2C_c._1870.jpg/330px-thumbnail.jpg"],
   97|   garfield: ["James A. Garfield", "Garfield", "1/1f/James_Abram_Garfield%2C_photo_portrait_seated.jpg/330px-James_Abram_Garfield%2C_photo_portrait_seated.jpg"],
   98|   hancock: ["Winfield Scott Hancock", "Hancock", "5/5b/Gen._Winfield_S._Hancock_-_NARA_-_529369_%28cropped%2C_retouched%29.jpg/330px-Gen._Winfield_S._Hancock_-_NARA_-_529369_%28cropped%2C_retouched%29.jpg"],
   99|   cleveland: ["Grover Cleveland", "Cleveland", "3/36/StephenGroverCleveland.jpg/330px-StephenGroverCleveland.jpg"],
  100|   blaine: ["James G. Blaine", "Blaine", "f/fb/James_G._Blaine_-_Brady-Handy.jpg/330px-James_G._Blaine_-_Brady-Handy.jpg"],
  101|   harrison2: ["Benjamin Harrison", "Harrison", "4/49/Pach_Brothers_-_Benjamin_Harrison_%28cropped%29_%28cropped%29.jpg/330px-Pach_Brothers_-_Benjamin_Harrison_%28cropped%29_%28cropped%29.jpg"],
  102|   mckinley: ["William McKinley", "McKinley", "3/30/McKinley_%28cropped%29.jpg/330px-McKinley_%28cropped%29.jpg"],
  103|   bryan: ["William Jennings Bryan", "Bryan", "2/20/Portrait_of_Secretary_William_Jennings_Bryan_of_Nebraska%2C_1913.jpeg/330px-Portrait_of_Secretary_William_Jennings_Bryan_of_Nebraska%2C_1913.jpeg"],
  104|   roosevelt: ["Theodore Roosevelt", "Roosevelt", "6/69/Theodore_Roosevelt_by_the_Pach_Bros_%284x5_cropped%29_%282%29.jpg/330px-Theodore_Roosevelt_by_the_Pach_Bros_%284x5_cropped%29_%282%29.jpg"],
  105|   parker: ["Alton B. Parker", "Parker", "b/b4/Alton_Brooks_Parker_Portrait_%283x4_cropped%29.jpg/330px-Alton_Brooks_Parker_Portrait_%283x4_cropped%29.jpg"],
  106|   taft: ["William Howard Taft", "Taft", "1/11/William_Howard_Taft_by_Pach_Brothers_%283x4_ropped%29_%28cropped%29.jpg/330px-William_Howard_Taft_by_Pach_Brothers_%283x4_ropped%29_%28cropped%29.jpg"],
  107|   wilson: ["Woodrow Wilson", "Wilson", "9/96/President_Woodrow_Wilson_Harris_%26_Ewing_%283x4_cropped_b%29.jpg/330px-President_Woodrow_Wilson_Harris_%26_Ewing_%283x4_cropped_b%29.jpg"],
  108|   hughes: ["Charles Evans Hughes", "Hughes", "e/ee/Charles_Evans_Hughes_cph.3b15401.jpg/330px-Charles_Evans_Hughes_cph.3b15401.jpg"],
  109|   harding: ["Warren G. Harding", "Harding", "4/4e/Warren_G._Harding_1920s_portrait_%283x4_cropped%29.jpg/330px-Warren_G._Harding_1920s_portrait_%283x4_cropped%29.jpg"],
  110|   cox: ["James M. Cox", "Cox", "5/57/James_M._Cox_Portrait_%283x4_cropped_b%29.jpg/330px-James_M._Cox_Portrait_%283x4_cropped_b%29.jpg"],
  111|   coolidge: ["Calvin Coolidge", "Coolidge", "4/4c/President_Calvin_Coolidge%2C_1924_portrait_photograph_%283x4_cropped_2%29.jpeg/330px-President_Calvin_Coolidge%2C_1924_portrait_photograph_%283x4_cropped_2%29.jpeg"],
  112|   davis: ["John W. Davis", "Davis", "c/c5/DAVIS%2C_JOHN_W._HONORABLE_LCCN2016862563_%28cropped%29.jpg/330px-DAVIS%2C_JOHN_W._HONORABLE_LCCN2016862563_%28cropped%29.jpg"],
  113|   hoover: ["Herbert Hoover", "Hoover", "5/57/President_Hoover_portrait.jpg/330px-President_Hoover_portrait.jpg"],
  114|   smith: ["Al Smith", "Smith", "1/1f/SMITH%2C_ALFRED._HONORABLE_LCCN2016862532_Trim.jpg/330px-SMITH%2C_ALFRED._HONORABLE_LCCN2016862532_Trim.jpg"],
  115|   roosevelt2: ["Franklin D. Roosevelt", "Roosevelt", "f/fd/FDR-1944-Campaign-Portrait_%283x4_retouched%2C_cropped%29.jpg/330px-FDR-1944-Campaign-Portrait_%283x4_retouched%2C_cropped%29.jpg"],
  116|   landon: ["Alf Landon", "Landon", "3/37/Unsuccessful_1936.jpg/330px-Unsuccessful_1936.jpg"],
  117|   willkie: ["Wendell Willkie", "Willkie", "b/b5/Portrait_of_Wendell_Lewis_Willkie_Sitting_by_Wall_%28cropped%29.jpg/330px-Portrait_of_Wendell_Lewis_Willkie_Sitting_by_Wall_%28cropped%29.jpg"],
  118|   dewey: ["Thomas E. Dewey", "Dewey", "5/52/Thomas_Dewey_in_1944.jpg/330px-Thomas_Dewey_in_1944.jpg"],
  119|   truman: ["Harry S. Truman", "Truman", "0/0b/TRUMAN_58-766-06_%28cropped%29.jpg/330px-TRUMAN_58-766-06_%28cropped%29.jpg"],
  120|   eisenhower: ["Dwight D. Eisenhower", "Eisenhower", "0/02/Dwight_D._Eisenhower%2C_official_photo_portrait%2C_May_29%2C_1959_%28cropped%29%283%29.jpg/330px-Dwight_D._Eisenhower%2C_official_photo_portrait%2C_May_29%2C_1959_%28cropped%29%283%29.jpg"],
  121|   stevenson: ["Adlai Stevenson", "Stevenson", "c/ce/Portrait_of_Ambassador_Adlai_E._Stevenson_II_%28cropped%29.jpg/330px-Portrait_of_Ambassador_Adlai_E._Stevenson_II_%28cropped%29.jpg"],
  122|   kennedy: ["John F. Kennedy", "Kennedy", "c/c3/John_F._Kennedy%2C_White_House_color_photo_portrait.jpg/330px-John_F._Kennedy%2C_White_House_color_photo_portrait.jpg"],
  123|   nixon: ["Richard Nixon", "Nixon", "2/2c/Richard_Nixon_presidential_portrait_%281%29.jpg/330px-Richard_Nixon_presidential_portrait_%281%29.jpg"],
  124|   johnson: ["Lyndon B. Johnson", "Johnson", "5/54/Lyndon_B._Johnson%2C_photo_portrait%2C_color_%283x4_cropped%29%282%29.jpg/330px-Lyndon_B._Johnson%2C_photo_portrait%2C_color_%283x4_cropped%29%282%29.jpg"],
  125|   goldwater: ["Barry Goldwater", "Goldwater", "1/19/Senator_Goldwater_1960.jpg/330px-Senator_Goldwater_1960.jpg"],
  126|   humphrey: ["Hubert Humphrey", "Humphrey", "2/23/Hubert_Humphrey_vice_presidential_portrait.jpg/330px-Hubert_Humphrey_vice_presidential_portrait.jpg"],
  127|   mcgovern: ["George McGovern", "McGovern", "6/6f/George_McGovern_%28D-SD%29.jpg/330px-George_McGovern_%28D-SD%29.jpg"],
  128|   carter: ["Jimmy Carter", "Carter", "6/6a/Jimmy_Carter_Official_Portrait2_%283x4_cropped%29.jpg/330px-Jimmy_Carter_Official_Portrait2_%283x4_cropped%29.jpg"],
  129|   ford: ["Gerald Ford", "Ford", "3/36/Gerald_Ford_presidential_portrait_%28cropped%29.jpg/330px-Gerald_Ford_presidential_portrait_%28cropped%29.jpg"],
  130|   reagan: ["Ronald Reagan", "Reagan", "1/16/Official_Portrait_of_President_Reagan_1981.jpg/330px-Official_Portrait_of_President_Reagan_1981.jpg"],
  131|   mondale: ["Walter Mondale", "Mondale", "4/41/Walter_Mondale_1977_vice_presidential_portrait.jpg/330px-Walter_Mondale_1977_vice_presidential_portrait.jpg"],
  132|   bush: ["George H. W. Bush", "Bush", "d/dc/George_H._W._Bush_presidential_portrait_%28cropped%29_%282%29.jpg/330px-George_H._W._Bush_presidential_portrait_%28cropped%29_%282%29.jpg"],
  133|   dukakis: ["Michael Dukakis", "Dukakis", "0/0c/Michael_Dukakis_%283x4_cropped%29.jpg/330px-Michael_Dukakis_%283x4_cropped%29.jpg"],
  134|   clinton2: ["Bill Clinton", "Clinton", "d/d3/Bill_Clinton.jpg/330px-Bill_Clinton.jpg"],
  135|   dole: ["Bob Dole", "Dole", "a/a9/Ks_1996_dole.jpg/330px-Ks_1996_dole.jpg"],
  136|   bush2: ["George W. Bush", "Bush", "d/d4/George-W-Bush.jpeg/330px-George-W-Bush.jpeg"],
  137|   gore: ["Al Gore", "Gore", "c/c5/Al_Gore%2C_Vice_President_of_the_United_States%2C_official_portrait_1994.jpg/330px-Al_Gore%2C_Vice_President_of_the_United_States%2C_official_portrait_1994.jpg"],
  138|   kerry: ["John Kerry", "Kerry", "7/73/John_Kerry_portrait_of_Climate_Envoy_%28cropped%29.jpg/330px-John_Kerry_portrait_of_Climate_Envoy_%28cropped%29.jpg"],
  139|   obama: ["Barack Obama", "Obama", "8/8d/President_Barack_Obama.jpg/330px-President_Barack_Obama.jpg"],
  140|   mccain: ["John McCain", "McCain", "7/74/John_McCain_official_portrait_2009_%283x4_cropped%29.jpg/330px-John_McCain_official_portrait_2009_%283x4_cropped%29.jpg"],
  141|   romney: ["Mitt Romney", "Romney", "7/7f/Mitt_Romney_official_US_Senate_portrait.jpg/330px-Mitt_Romney_official_US_Senate_portrait.jpg"],
  142|   trump: ["Donald Trump", "Trump", "1/16/Official_Presidential_Portrait_of_President_Donald_J._Trump_%282025%29.jpg/330px-Official_Presidential_Portrait_of_President_Donald_J._Trump_%282025%29.jpg"],
  143|   clinton3: ["Hillary Clinton", "Clinton", "e/ec/Former_United_States_Secretary_of_State_Hillary_Rodham_Clinton_at_the_U.S._Department_of_State_on_September_26%2C_2023_in_Washington%2C_D.C._14_%28cropped%29.jpg/330px-Former_United_States_Secretary_of_State_Hillary_Rodham_Clinton_at_the_U.S._Department_of_State_on_September_26%2C_2023_in_Washington%2C_D.C._14_%28cropped%29.jpg"],
  144|   biden: ["Joe Biden", "Biden", "6/68/Joe_Biden_presidential_portrait.jpg/330px-Joe_Biden_presidential_portrait.jpg"],
  145|   harris: ["Kamala Harris", "Harris", "4/41/Kamala_Harris_Vice_Presidential_Portrait.jpg/330px-Kamala_Harris_Vice_Presidential_Portrait.jpg"],
  146| } as const satisfies Record<string, readonly [string, string, string]>;
  147| type PersonId = keyof typeof PEOPLE;
  148| 
  149| // winner / runner-up: [person, party, electoral votes, popular vote %]
  150| type Ran = readonly [id: PersonId, party: PartyCode, ev: number, popular: number | null];
  151| // others: [name, surname, party, electoral votes, popular vote %]
  152| type Other = readonly [name: string, short: string, party: PartyCode, ev: number, popular: number | null];
  153| // [year, electoral votes, needed to win, winner, runner-up, others, note,
  154| //  each state's winning party (geo.ts STATES order; - = no vote), each state's electoral votes]
  155| type Row = readonly [
  156|   year: number,
  157|   total: number,
  158|   majority: number,
  159|   winner: Ran,
  160|   runnerUp: Ran | null,
  161|   others: readonly Other[],
  162|   note: string,
  163|   parties: string,
  164|   evs: string,
  165| ];
  166| const RESULTS: readonly Row[] = [
  167|   [1789, 69, 35, ['washington', "GW", 69, null], null, [], "Unopposed. Every elector voted for him; John Adams came second and became vice president.",
  168|     "- - - - GW - - - - - - - - GW - - - - - - - GW GW GW - - - - - - - - GW GW GW - - - - - - GW - - - - - GW - - -",
  169|     "0 0 0 0 5 0 0 0 0 0 0 0 0 10 0 0 0 0 0 0 0 10 6 7 0 0 0 0 0 0 0 0 12 8 3 0 0 0 0 0 0 7 0 0 0 0 0 5 0 0 0"],
  170|   [1792, 132, 67, ['washington', "GW", 132, null], null, [], "Unopposed again. John Adams came second and stayed vice president.",
  171|     "- - - GW GW - - - - - - - GW GW - - - - - - - GW GW GW GW - - - - - GW - GW GW GW - - - - - GW GW - - - - - GW - - -",
  172|     "0 0 0 4 6 0 0 0 0 0 0 0 12 16 0 0 0 0 0 0 0 15 7 9 4 0 0 0 0 0 4 0 21 10 3 0 0 0 0 0 12 8 0 0 0 0 0 4 0 0 0"],
  173|   [1796, 138, 70, ['adams', "F", 71, null], ['jefferson', "DR", 68, null], [], "Jefferson came second and, under the rules then, became Adams’s vice president.",
  174|     "- - - F F - - - - - - - F F - - - - - - - DR F F F - - - - - DR - DR F F - - - - DR DR DR - - - - - DR - - -",
  175|     "0 0 0 4 6 0 0 0 0 0 0 0 12 16 0 0 0 0 0 0 0 15 7 9 4 0 0 0 0 0 4 0 21 10 3 0 0 0 0 3 12 8 0 0 0 0 0 4 0 0 0"],
  176|   [1800, 138, 70, ['jefferson', "DR", 73, null], ['adams', "F", 65, null], [], "Jefferson tied his own running mate, Aaron Burr, at 73. The House chose Jefferson on its 36th ballot.",
  177|     "- - - F F - - - - - - - DR F - - - - - - - DR F F F - - - - - DR - DR SP F - - - - DR DR DR - - - - - DR - - -",
  178|     "0 0 0 4 6 0 0 0 0 0 0 0 12 16 0 0 0 0 0 0 0 15 7 9 4 0 0 0 0 0 4 0 21 10 3 0 0 0 0 3 12 8 0 0 0 0 0 4 0 0 0"],
  179|   [1804, 176, 89, ['jefferson', "DR", 162, null], ['pinckney', "F", 14, null], [], "",
  180|     "- - - DR DR - - - - - - - DR DR - - - - - - DR DR DR F DR - - - - - DR - DR DR F - - - - DR DR DR - - - - - DR - - -",
  181|     "0 0 0 6 7 0 0 0 0 0 0 0 19 19 0 0 0 0 0 0 3 20 8 9 4 0 0 0 0 0 8 0 24 11 3 0 0 0 0 5 14 10 0 0 0 0 0 6 0 0 0"],
  182|   [1808, 175, 88, ['madison', "DR", 122, null], ['pinckney', "F", 47, null], [["George Clinton", "Clinton", "DR2", 6, null]], "",
  183|     "- - - DR F - - - - - - - DR F - - - - - - DR DR DR F F - - - - - DR - DR DR F - - - - DR DR DR - - - - - DR - - -",
  184|     "0 0 0 6 7 0 0 0 0 0 0 0 19 19 0 0 0 0 0 0 3 20 8 9 4 0 0 0 0 0 8 0 24 11 3 0 0 0 0 5 14 10 0 0 0 0 0 6 0 0 0"],
  185|   [1812, 217, 109, ['madison', "DR", 128, null], ['clinton', "F", 89, null], [], "Clinton, a Democratic-Republican, ran with the Federalists against the war with Britain.",
  186|     "- - - DR F - - - - - - - F F - - - - - - DR DR F F F - - - - - DR - DR DR F - - - - DR DR DR - - DR - - DR - - -",
  187|     "0 0 0 8 8 0 0 0 0 0 0 0 29 22 0 0 0 0 0 0 8 25 8 9 4 0 0 0 0 0 12 0 25 11 4 0 0 0 0 8 15 11 0 0 3 0 0 8 0 0 0"],
  188|   [1816, 217, 109, ['monroe', "DR", 183, null], ['king', "F", 34, null], [], "The Federalists’ last presidential campaign.",
  189|     "- - - DR DR - - - - - - - DR F - - - - - DR DR DR DR F DR - - - - - DR - DR DR F - - - - DR DR DR - - DR - - DR - - -",
  190|     "0 0 0 8 8 0 0 0 0 0 0 0 29 22 0 0 0 0 0 3 8 25 8 9 4 0 0 0 0 0 12 0 25 11 4 0 0 0 0 8 15 11 0 0 3 0 0 8 0 0 0"],
  191|   [1820, 232, 117, ['monroe', "DR", 231, null], null, [], "Unopposed. One elector voted for John Quincy Adams instead.",
  192|     "- DR - DR DR - - - - - DR - DR DR - - - - - DR DR DR DR DR DR - - - - DR DR - DR DR DR - - - - DR DR DR - - DR DR DR DR - - -",
  193|     "0 3 0 8 8 0 0 0 0 0 3 0 29 22 0 0 0 0 0 3 8 25 8 9 4 0 0 0 0 3 12 0 25 11 4 0 0 0 0 8 15 11 0 0 3 3 3 8 0 0 0"],
  194|   [1824, 261, 131, ['adams2', "Adams", 84, 30.9], ['jackson', "Jackson", 99, 41.4], [["William H. Crawford", "Crawford", "Crawford", 41, 11.2], ["Henry Clay", "Clay", "Clay", 37, 13.0]], "Jackson led but no one had a majority. The House chose Adams.",
  195|     "- Adams - Adams Adams - - - - - Jackson - Adams Adams - - - - - Jackson Clay Jackson Jackson Adams Adams - - - - Jackson Clay - Crawford Jackson Crawford - - - - Jackson Jackson Jackson - - Jackson Jackson Jackson Crawford - - -",
  196|     "0 9 0 7 8 0 0 0 0 0 3 0 36 15 0 0 0 0 0 5 16 28 8 8 4 0 0 0 0 3 14 0 24 11 3 0 0 0 0 11 15 11 0 0 5 3 5 9 0 0 0"],
  197|   [1828, 261, 131, ['jackson', "D", 178, 56.0], ['adams2', "NR", 83, 43.6], [], "",
  198|     "- NR - NR NR - - - - - D - D NR - - - - - D D D NR NR NR - - - - D D - D NR NR - - - - D D D - - D D D D - - -",
  199|     "0 9 0 7 8 0 0 0 0 0 3 0 36 15 0 0 0 0 0 5 16 28 8 8 4 0 0 0 0 3 14 0 24 11 3 0 0 0 0 11 15 11 0 0 5 3 5 9 0 0 0"],
  200|   [1832, 286, 144, ['jackson', "D", 219, 54.2], ['clay', "NR", 49, 37.4], [["John Floyd", "Floyd", "N", 11, null], ["William Wirt", "Wirt", "AM", 7, 7.8]], "",
  201|     "- D - AM D - - - - - D - D NR - - - - - D D D D NR NR - - - - D NR - D NR NR - - - - D D N - - D D D D - - -",
  202|     "0 10 0 7 7 0 0 0 0 0 5 0 42 14 0 0 0 0 0 9 21 30 8 8 4 0 0 0 0 4 15 0 23 10 3 0 0 0 0 15 15 11 0 0 5 4 7 11 0 0 0"],
  203|   [1836, 294, 148, ['vanburen', "D", 170, 50.8], ['harrison', "W", 73, 36.6], [["Hugh Lawson White", "White", "W2", 26, 9.7], ["Daniel Webster", "Webster", "W3", 14, 2.7], ["Willie P. Mangum", "Mangum", "W4", 11, null]], "The Whigs ran four regional candidates, hoping to force the race into the House.",
  204|     "- D - W D - - - - - D D D W - - - - - W W D W D D - - - - D W - D W W - - - D W D W - - D D D W - - -",
  205|     "0 10 0 7 7 0 0 0 0 0 5 3 42 14 0 0 0 0 0 9 21 30 8 8 4 0 0 0 0 4 15 0 23 10 3 0 0 0 3 15 15 11 0 0 5 4 7 11 0 0 0"],
  206|   [1840, 294, 148, ['harrison', "W", 234, 52.9], ['vanburen', "D", 60, 46.8], [], "",
  207|     "- W - W D - - - - - D W W W - - - - - W W W W W W - - - - D W - D W W - - - D W W D - - W W D W - - -",
  208|     "0 10 0 7 7 0 0 0 0 0 5 3 42 14 0 0 0 0 0 9 21 30 8 8 4 0 0 0 0 4 15 0 23 10 3 0 0 0 3 15 15 11 0 0 5 4 7 11 0 0 0"],
  209|   [1844, 275, 138, ['polk', "D", 170, 49.5], ['clay', "W", 105, 48.1], [], "New York, and the election, turned on about 5,000 votes.",
  210|     "- D - W D - - - - - D D D W - - - - - D W D W W W - - - - D W - D W W - - - D W W D - - D D D D - - -",
  211|     "0 9 0 6 6 0 0 0 0 0 9 5 36 12 0 0 0 0 0 12 23 26 7 6 4 0 0 0 0 7 12 0 17 8 3 0 0 0 3 13 11 9 0 0 6 6 9 10 0 0 0"],
  212|   [1848, 290, 146, ['taylor', "W", 163, 47.3], ['cass', "D", 127, 42.5], [["Martin Van Buren", "Van Buren", "FS", 0, 10.1]], "",
  213|     "- D D W D - - - - - D D W W - - - - D D D W W W W - - - - D W - D W W - - - D W W D - - W D D W - D W",
  214|     "0 9 4 6 6 0 0 0 0 0 9 5 36 12 0 0 0 0 4 12 23 26 7 6 4 0 0 0 0 7 12 0 17 8 3 0 0 0 3 13 11 9 0 0 6 6 9 10 0 4 3"],
  215|   [1852, 296, 149, ['pierce', "D", 254, 50.8], ['scott', "W", 42, 43.9], [], "The Whigs’ last presidential campaign.",
  216|     "- D D W D - - - - - D D D W - - - - D D D D D D D D - - - D W - D D D - - - D W D D - - D D D D - D D",
  217|     "0 8 5 5 5 0 0 0 0 0 11 6 35 13 0 0 0 0 4 13 23 27 7 6 4 4 0 0 0 9 12 0 15 8 3 0 0 0 4 12 10 8 0 0 6 7 9 10 0 4 3"],
  218|   [1856, 296, 149, ['buchanan', "D", 174, 45.3], ['frmont', "R", 114, 33.1], [["Millard Fillmore", "Fillmore", "KN", 8, 21.5]], "The new Republican Party’s first campaign.",
  219|     "- R R R R - - - - - D R R R - - - - R D R D D R R D - - - D D - D KN D - - - D D D D - - D D D D - D D",
  220|     "0 8 5 5 5 0 0 0 0 0 11 6 35 13 0 0 0 0 4 13 23 27 7 6 4 4 0 0 0 9 12 0 15 8 3 0 0 0 4 12 10 8 0 0 6 7 9 10 0 4 3"],
  221|   [1860, 303, 152, ['lincoln', "R", 180, 39.8], ['breckinridge', "SD", 72, 18.1], [["John Bell", "Bell", "CU", 39, 12.6], ["Stephen A. Douglas", "Douglas", "ND", 12, 29.5]], "The Democrats split in two. Lincoln won without a single Southern electoral vote.",
  222|     "- R R R R - - - - R R R R R R - - - R R R R R R R R - - - ND CU - CU SD SD - - - SD CU SD SD - - SD SD SD SD - SD SD",
  223|     "0 8 5 5 5 0 0 0 0 4 11 6 35 13 3 0 0 0 4 13 23 27 7 6 4 4 0 0 0 9 12 0 15 8 3 0 0 0 4 12 10 8 0 0 6 7 9 10 0 4 3"],
  224|   [1864, 233, 117, ['lincoln', "R", 212, 55.0], ['mcclellan', "D", 21, 45.0], [], "Held during the Civil War. The eleven Confederate states cast no votes.",
  225|     "- R R R R - - - - R R R R R R R - - R R R R D R R R - - - R D R - R D - - R - - - - - - - - - - - - -",
  226|     "0 7 8 5 5 0 0 0 0 4 16 8 33 12 3 3 0 0 8 13 21 26 7 6 4 5 0 0 0 11 11 5 0 7 3 0 0 3 0 0 0 0 0 0 0 0 0 0 0 0 0"],
  227|   [1868, 294, 148, ['grant', "R", 214, 52.7], ['seymour', "D", 80, 47.3], [], "The first election with Black men voting across the South.",
  228|     "- R R R R - - - - R R R D R D R - - R R R R D R R R - - R R D R - D D - - R R R R R - - D - R D - - R",
  229|     "0 7 8 5 5 0 0 0 0 4 16 8 33 12 3 3 0 0 8 13 21 26 7 6 4 5 0 0 3 11 11 5 0 7 3 0 0 3 5 10 9 6 0 0 7 0 8 9 0 0 3"],
  230|   [1872, 366, 184, ['grant', "R", 286, 55.6], ['greeley', "LR", 66, 43.8], [], "Greeley died three weeks after Election Day; his 66 electors voted for others.",
  231|     "- R R R R - - - - R R R R R R R - - R R R R R R R R - - R LR LR R R LR R - - R R LR R R - - R R R LR - LR R",
  232|     "0 7 10 5 5 0 0 0 0 5 21 11 35 13 3 3 0 0 11 15 22 29 9 6 4 6 0 0 3 15 12 5 11 8 3 0 0 5 6 12 10 7 0 0 8 8 10 11 0 8 4"],
  233|   [1876, 369, 185, ['hayes', "R", 185, 47.9], ['tilden', "D", 184, 51.0], [], "Tilden won the popular vote. A commission gave all 20 disputed electoral votes to Hayes.",
  234|     "- R R R R - - - - R R R D R R R - - R D R R D D R R - R R D D D D D D - - R D D D R - - R D D D - D R",
  235|     "0 7 10 5 5 0 0 0 0 5 21 11 35 13 3 3 0 0 11 15 22 29 9 6 4 6 0 3 3 15 12 5 11 8 3 0 0 5 6 12 10 7 0 0 8 8 10 11 0 8 4"],
  236|   [1880, 369, 185, ['garfield', "R", 214, 48.3], ['hancock', "D", 155, 48.2], [], "Decided by about 2,000 popular votes out of 9 million.",
  237|     "- R R R R - - - - R R R R R R D - - R R R R D R R D - R R D D D D D D - - R D D D D - - D D D D - D D",
  238|     "0 7 10 5 5 0 0 0 0 5 21 11 35 13 3 3 0 0 11 15 22 29 9 6 4 6 0 3 3 15 12 5 11 8 3 0 0 5 6 12 10 7 0 0 8 8 10 11 0 8 4"],
  239|   [1884, 401, 201, ['cleveland', "D", 219, 48.9], ['blaine', "R", 182, 48.3], [], "New York went to Cleveland by 1,047 votes.",
  240|     "- R R R R - - - - R R R D R R R - - R D R R D D R R - R R D D D D D D - - R D D D D - - D D D D - D D",
  241|     "0 6 11 4 4 0 0 0 0 7 22 13 36 14 3 3 0 0 13 15 23 30 9 6 4 8 0 3 5 16 13 6 12 8 3 0 0 9 7 12 11 9 0 0 8 9 10 12 0 13 4"],
  242|   [1888, 401, 201, ['harrison2', "R", 233, 47.8], ['cleveland', "D", 168, 48.6], [], "Cleveland won the popular vote.",
  243|     "- R R R R - - - - R R R R R R R - - R R R R D D R R - R R D D D D D D - - R D D D D - - D D D D - D D",
  244|     "0 6 11 4 4 0 0 0 0 7 22 13 36 14 3 3 0 0 13 15 23 30 9 6 4 8 0 3 5 16 13 6 12 8 3 0 0 9 7 12 11 9 0 0 8 9 10 12 0 13 4"],
  245|   [1892, 444, 223, ['cleveland', "D", 277, 46.0], ['harrison2', "R", 145, 43.0], [["James B. Weaver", "Weaver", "PO", 22, 8.5]], "",
  246|     "- R D R R R PO R SP R D R D R R PO R R R D R R D D R D - PO R D D D D D D - - PO D D D D - - D D D D - D D",
  247|     "0 6 12 4 4 4 3 3 3 9 24 14 36 15 4 3 3 4 13 15 23 32 10 6 4 9 0 4 8 17 13 6 12 8 3 0 0 10 8 12 11 9 0 0 8 9 11 13 0 15 4"],
  248|   [1896, 447, 224, ['mckinley', "R", 271, 51.0], ['bryan', "D", 176, 46.7], [], "Gold against silver, city against farm, three years into a depression.",
  249|     "- R R R R D D D R R R R R R R D D D R R R R R R R R D D D D R R D R R - - D D D D D - - D D D D - D D",
  250|     "0 6 12 4 4 4 3 3 3 9 24 14 36 15 4 3 3 4 13 15 23 32 10 6 4 9 3 4 8 17 13 6 12 8 3 0 0 10 8 12 11 9 0 0 8 9 11 13 0 15 4"],
  251|   [1900, 447, 224, ['mckinley', "R", 292, 51.6], ['bryan', "D", 155, 45.5], [], "",
  252|     "- R R R R R D D R R R R R R R D R R R R R R R R R R R D R D D R D R R - - R D D D D - - D D D D - D D",
  253|     "0 6 12 4 4 4 3 3 3 9 24 14 36 15 4 3 3 4 13 15 23 32 10 6 4 9 3 4 8 17 13 6 12 8 3 0 0 10 8 12 11 9 0 0 8 9 11 13 0 15 4"],
  254|   [1904, 476, 239, ['roosevelt', "R", 336, 56.4], ['parker', "D", 140, 37.6], [], "",
  255|     "- R R R R R R R R R R R R R R R R R R R R R R R R R R R R R D R D D R - - R D D D D - - D D D D - D D",
  256|     "0 6 13 4 4 5 3 3 4 11 27 14 39 16 4 3 3 4 13 15 23 34 12 7 4 10 3 5 8 18 13 7 12 8 3 0 0 10 9 12 12 9 0 0 9 10 11 13 0 18 5"],
  257|   [1908, 483, 242, ['taft', "R", 321, 51.6], ['bryan', "D", 162, 43.0], [], "",
  258|     "- R R R R R R R R R R R R R R D R R R R R R R R R R R D D R D R D D R - - R D D D D - D D D D D - D D",
  259|     "0 6 13 4 4 5 3 3 4 11 27 14 39 16 4 3 3 4 13 15 23 34 12 7 4 10 3 5 8 18 13 7 12 8 3 0 0 10 9 12 12 9 0 7 9 10 11 13 0 18 5"],
  260|   [1912, 531, 266, ['wilson', "D", 435, 41.8], ['roosevelt', "BM", 88, 27.4], [["William Howard Taft", "Taft", "R", 8, 23.2], ["Eugene V. Debs", "Debs", "S", 0, 6.0]], "Roosevelt split the Republicans, and Wilson won with 42% of the vote.",
  261|     "- D D R D BM D D D BM D BM D D D D D BM D D D BM D D D BM R D D D D D D D D D D D D D D D - D D D D D - D D",
  262|     "0 6 13 4 4 7 4 4 5 12 29 15 45 18 5 3 3 5 13 15 24 38 14 7 5 13 4 6 8 18 13 8 12 8 3 3 3 10 9 12 12 9 0 10 10 10 12 14 0 20 6"],
  263|   [1916, 531, 266, ['wilson', "D", 277, 49.2], ['hughes', "R", 254, 46.1], [], "California, and the election, went to Wilson by 3,773 votes.",
  264|     "- R R R D D D D D R R R R R R D D R R R D R R R R D D D D D D R D D R D D D D D D D - D D D D D - D D",
  265|     "0 6 13 4 4 7 4 4 5 12 29 15 45 18 5 3 3 5 13 15 24 38 14 7 5 13 4 6 8 18 13 8 12 8 3 3 3 10 9 12 12 9 0 10 10 10 12 14 0 20 6"],
  266|   [1920, 531, 266, ['harding', "R", 404, 60.3], ['cox', "D", 127, 34.1], [], "The first election after the 19th Amendment.",
  267|     "- R R R R R R R R R R R R R R R R R R R R R R R R R R R R R D R D R R R R R D R D D - R D D D D - D D",
  268|     "0 6 13 4 4 7 4 4 5 12 29 15 45 18 5 3 3 5 13 15 24 38 14 7 5 13 4 6 8 18 13 8 12 8 3 3 3 10 9 12 12 9 0 10 10 10 12 14 0 20 6"],
  269|   [1924, 531, 266, ['coolidge', "R", 382, 54.0], ['davis', "D", 136, 28.8], [["Robert M. La Follette", "La Follette", "PR", 13, 16.6]], "",
  270|     "- R PR R R R R R R R R R R R R R R R R R R R R R R R R R R R R R D R R R R R D D D D - D D D D D - D D",
  271|     "0 6 13 4 4 7 4 4 5 12 29 15 45 18 5 3 3 5 13 15 24 38 14 7 5 13 4 6 8 18 13 8 12 8 3 3 3 10 9 12 12 9 0 10 10 10 12 14 0 20 6"],
  272|   [1928, 531, 266, ['hoover', "R", 444, 58.2], ['smith', "D", 87, 40.8], [], "Smith, the first Catholic nominee, cracked the Solid South the wrong way.",
  273|     "- R R R R R R R R R R R R D R R R R R R R R R R D R R R R R R R R R R R R R D R R D - R D D D D - R R",
  274|     "0 6 13 4 4 7 4 4 5 12 29 15 45 18 5 3 3 5 13 15 24 38 14 7 5 13 4 6 8 18 13 8 12 8 3 3 3 10 9 12 12 9 0 10 10 10 12 14 0 20 6"],
  275|   [1932, 531, 266, ['roosevelt2', "D", 472, 57.4], ['hoover', "R", 59, 39.7], [], "Three years into the Great Depression.",
  276|     "- R D R R D D D D D D D D D D D D D D D D R D R D D D D D D D D D D R D D D D D D D - D D D D D - D D",
  277|     "0 5 12 3 4 8 4 4 4 11 29 19 47 17 5 3 3 4 11 14 26 36 16 8 4 22 4 6 7 15 11 8 11 8 3 3 3 9 9 11 13 8 0 11 10 9 11 12 0 23 7"],
  278|   [1936, 531, 266, ['roosevelt2', "D", 523, 60.8], ['landon', "R", 8, 36.5], [], "Landon carried Maine and Vermont.",
  279|     "- R D R D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D - D D D D D - D D",
  280|     "0 5 12 3 4 8 4 4 4 11 29 19 47 17 5 3 3 4 11 14 26 36 16 8 4 22 4 6 7 15 11 8 11 8 3 3 3 9 9 11 13 8 0 11 10 9 11 12 0 23 7"],
  281|   [1940, 531, 266, ['roosevelt2', "D", 449, 54.7], ['willkie', "R", 82, 44.8], [], "A third term, with war in Europe.",
  282|     "- R D R D D D D R D D R D D D D D R R R D D D D D D D R R D D D D D D D D R D D D D - D D D D D - D D",
  283|     "0 5 12 3 4 8 4 4 4 11 29 19 47 17 5 3 3 4 11 14 26 36 16 8 4 22 4 6 7 15 11 8 11 8 3 3 3 9 9 11 13 8 0 11 10 9 11 12 0 23 7"],
  284|   [1944, 531, 266, ['roosevelt2', "D", 432, 53.4], ['dewey', "R", 99, 45.9], [], "",
  285|     "- R R R D D D D R D D D D D D D R R R R R D D D D D D R R D D D D D D D D R D D D D - D D D D D - D D",
  286|     "0 5 12 3 4 8 4 4 4 11 28 19 47 16 6 3 3 4 10 13 25 35 16 8 4 25 4 6 6 15 11 8 11 8 3 4 4 8 9 12 14 8 0 10 10 9 11 12 0 23 8"],
  287|   [1948, 531, 266, ['truman', "D", 303, 49.6], ['dewey', "R", 189, 45.1], [["Strom Thurmond", "Thurmond", "SR", 39, 2.4], ["Henry A. Wallace", "Wallace", "PG", 0, 2.4]], "Every major poll had Dewey winning.",
  288|     "- R D R R D D D R D D R R D R D D R D R D R R R D D D D R D D D D R R D D R D D D SR - D SR SR SR D - D D",
  289|     "0 5 12 3 4 8 4 4 4 11 28 19 47 16 6 3 3 4 10 13 25 35 16 8 4 25 4 6 6 15 11 8 11 8 3 4 4 8 9 12 14 8 0 10 10 9 11 12 0 23 8"],
  290|   [1952, 531, 266, ['eisenhower', "R", 442, 55.2], ['stevenson', "D", 89, 44.3], [], "",
  291|     "- R R R R R R R R R R R R R R R R R R R R R R R R R R R R R D D R R R R R R D R D D - R D D D D - R R",
  292|     "0 5 12 3 4 9 4 4 4 11 27 20 45 16 6 3 3 4 10 13 25 32 16 8 4 32 4 6 6 13 10 8 12 9 3 4 4 8 8 11 14 8 0 8 10 8 11 12 0 24 10"],
  293|   [1956, 531, 266, ['eisenhower', "R", 457, 57.4], ['stevenson', "D", 73, 42.0], [], "",
  294|     "- R R R R R R R R R R R R R R R R R R R R R R R R R R R R D R R R R R R R R D R D D - R R D D D - R R",
  295|     "0 5 12 3 4 9 4 4 4 11 27 20 45 16 6 3 3 4 10 13 25 32 16 8 4 32 4 6 6 13 10 8 12 9 3 4 4 8 8 11 14 8 0 8 10 8 11 12 0 24 10"],
  296|   [1960, 537, 269, ['kennedy', "D", 303, 49.7], ['nixon', "R", 219, 49.5], [["Harry F. Byrd", "Byrd", "I", 15, null]], "Kennedy won the popular vote by about 112,000 out of 69 million.",
  297|     "R R R R R R R R R D D D D D R D R R R R R D D D D R R R R D R D R D D R D R D R D D - R D I I D D D R",
  298|     "3 5 12 3 4 9 4 4 4 11 27 20 45 16 6 3 3 4 10 13 25 32 16 8 4 32 4 6 6 13 10 8 12 9 3 4 4 8 8 11 14 8 0 8 10 8 11 12 3 24 10"],
  299|   [1964, 538, 270, ['johnson', "D", 486, 61.1], ['goldwater', "R", 52, 38.5], [], "",
  300|     "D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D D R D D D D D R D D R R R R D D D",
  301|     "3 4 12 3 4 9 4 4 4 10 26 21 43 14 6 3 3 4 9 13 26 29 17 8 4 40 4 6 5 12 9 7 12 10 3 5 4 7 6 11 13 8 3 8 10 7 10 12 4 25 14"],
  302|   [1968, 538, 270, ['nixon', "R", 301, 43.4], ['humphrey', "D", 191, 42.7], [["George Wallace", "Wallace", "AI", 46, 13.5]], "Wallace carried five Southern states.",
  303|     "R D R R R D R R R D R D D D R R R R R R R D R D D R R R R R R D R D R R R R AI R R R D R AI AI AI AI D D R",
  304|     "3 4 12 3 4 9 4 4 4 10 26 21 43 14 6 3 3 4 9 13 26 29 17 8 4 40 4 6 5 12 9 7 12 10 3 5 4 7 6 11 13 8 3 8 10 7 10 12 4 25 14"],
  305|   [1972, 538, 270, ['nixon', "R", 520, 60.7], ['mcgovern', "D", 17, 37.5], [], "The first election with 18-year-olds voting everywhere.",
  306|     "R R R R R R R R R R R R R D R R R R R R R R R R R R R R R R R R R R R R R R R R R R D R R R R R R R R",
  307|     "3 4 11 3 4 9 4 4 3 10 26 21 41 14 6 3 3 4 8 13 25 27 17 8 4 45 4 7 5 12 9 6 12 10 3 6 4 7 6 10 13 8 3 8 10 7 9 12 4 26 17"],
  308|   [1976, 538, 270, ['carter', "D", 297, 50.1], ['ford', "R", 240, 48.0], [], "",
  309|     "R R D R R R R R R D R R D D R R R R R R D D R R D R R R R D D D R D D R R R D D D D D R D D D D D D D",
  310|     "3 4 11 3 4 9 4 4 3 10 26 21 41 14 6 3 3 4 8 13 25 27 17 8 4 45 4 7 5 12 9 6 12 10 3 6 4 7 6 10 13 8 3 8 10 7 9 12 4 26 17"],
  311|   [1980, 538, 270, ['reagan', "R", 489, 50.7], ['carter', "D", 49, 41.0], [["John B. Anderson", "Anderson", "IA", 0, 6.6]], "",
  312|     "R R R R R R R R R D R R R R R R R R R R R R R R D R R R R R R D R D R R R R R R R R D R R R R D D R R",
  313|     "3 4 11 3 4 9 4 4 3 10 26 21 41 14 6 3 3 4 8 13 25 27 17 8 4 45 4 7 5 12 9 6 12 10 3 6 4 7 6 10 13 8 3 8 10 7 9 12 4 26 17"],
  314|   [1984, 538, 270, ['reagan', "R", 525, 58.8], ['mondale', "D", 13, 40.6], [], "Mondale carried Minnesota and D.C.",
  315|     "R R R R R R R R R D R R R R R R R R R R R R R R R R R R R R R R R R R R R R R R R R D R R R R R R R R",
  316|     "3 4 11 3 4 10 4 4 3 10 24 20 36 13 7 4 3 3 8 12 23 25 16 8 4 47 5 8 5 11 9 6 12 10 3 7 5 7 6 11 13 8 3 8 10 7 9 12 4 29 21"],
  317|   [1988, 538, 270, ['bush', "R", 426, 53.4], ['dukakis', "D", 111, 45.6], [], "",
  318|     "R R D R R D R R R D R R D D D R R R D R R R R R D R R R R R R D R R R R R R R R R R D R R R R R D R R",
  319|     "3 4 11 3 4 10 4 4 3 10 24 20 36 13 7 4 3 3 8 12 23 25 16 8 4 47 5 8 5 11 9 6 12 10 3 7 5 7 6 11 13 8 3 8 10 7 9 12 4 29 21"],
  320|   [1992, 538, 270, ['clinton2', "D", 370, 43.0], ['bush', "R", 168, 37.4], [["Ross Perot", "Perot", "IP", 0, 18.9]], "",
  321|     "R D D D D D R D R D D D D D D D R R D R D D D D D D R D R D D D R D D R D R D D R R D R D R R D D R R",
  322|     "3 4 11 3 4 11 4 3 3 10 22 18 33 12 7 4 3 3 7 12 21 23 15 8 4 54 5 8 5 11 8 5 13 10 3 8 5 6 6 11 14 8 3 8 9 7 9 13 4 32 25"],
  323|   [1996, 538, 270, ['clinton2', "D", 379, 49.2], ['dole', "R", 159, 40.7], [["Ross Perot", "Perot", "RF", 0, 8.4]], "",
  324|     "R D D D D D R R R D D D D D D D R R D R D D D D D D R R R D D D R D D D D R D D R R D R D R R R D R D",
  325|     "3 4 11 3 4 11 4 3 3 10 22 18 33 12 7 4 3 3 7 12 21 23 15 8 4 54 5 8 5 11 8 5 13 10 3 8 5 6 6 11 14 8 3 8 9 7 9 13 4 32 25"],
  326|   [2000, 538, 270, ['bush2', "R", 271, 47.9], ['gore', "D", 266, 48.4], [], "Gore won the popular vote. Florida was decided by 537 votes.",
  327|     "R D D D R D R R R D D D D D D R R R D R R D D D D D R R R R R R R D D R D R R R R R D R R R R R D R R",
  328|     "3 4 11 3 4 11 4 3 3 10 22 18 33 12 7 4 3 3 7 12 21 23 15 8 4 54 5 8 5 11 8 5 13 10 3 8 5 6 6 11 14 8 3 8 9 7 9 13 4 32 25"],
  329|   [2004, 538, 270, ['bush2', "R", 286, 50.7], ['kerry', "D", 251, 48.3], [], "",
  330|     "R D D D D D R R R D D D D D D R R R R R R D D D D D R R R R R R R D D R R R R R R R D R R R R R D R R",
  331|     "3 4 10 3 4 11 4 3 3 10 21 17 31 12 7 5 3 3 7 11 20 21 15 7 4 55 5 9 5 11 8 5 13 10 3 10 5 6 6 11 15 8 3 7 9 6 9 15 4 34 27"],
  332|   [2008, 538, 270, ['obama', "D", 365, 52.9], ['mccain', "R", 173, 45.7], [], "",
  333|     "R D D D D D R R R D D D D D D D R R D D D D D D D D R D R R R R D D D R D R R R D R D R R R R R D R D",
  334|     "3 4 10 3 4 11 4 3 3 10 21 17 31 12 7 5 3 3 7 11 20 21 15 7 4 55 5 9 5 11 8 5 13 10 3 10 5 6 6 11 15 8 3 7 9 6 9 15 4 34 27"],
  335|   [2012, 538, 270, ['obama', "D", 332, 51.1], ['romney', "R", 206, 47.2], [], "",
  336|     "R D D D D D R R R D D D D D D D R R D R D D D D D D R D R R R R D D D R D R R R R R D R R R R R D R D",
  337|     "3 4 10 3 4 12 4 3 3 10 20 16 29 11 7 6 3 3 6 11 18 20 14 7 4 55 6 9 5 10 8 5 13 10 3 11 5 6 6 11 15 9 3 7 8 6 9 16 4 38 29"],
  338|   [2016, 538, 270, ['trump', "R", 304, 46.1], ['clinton3', "D", 227, 48.2], [], "Clinton won the popular vote. Seven electors broke ranks.",
  339|     "R D R D D D R R R D D R D D D D R R R R R R D D D D R D R R R R D D D R D R R R R R D R R R R R D R R",
  340|     "3 4 10 3 4 12 4 3 3 10 20 16 29 11 7 6 3 3 6 11 18 20 14 7 4 55 6 9 5 10 8 5 13 10 3 11 5 6 6 11 15 9 3 7 8 6 9 16 4 38 29"],
  341|   [2020, 538, 270, ['biden', "D", 306, 51.3], ['trump', "R", 232, 46.8], [], "",
  342|     "R D D D D D R R R D D D D D D D R R R R R D D D D D R D R R R R D D D D D R R R R R D R R R R D D R R",
  343|     "3 4 10 3 4 12 4 3 3 10 20 16 29 11 7 6 3 3 6 11 18 20 14 7 4 55 6 9 5 10 8 5 13 10 3 11 5 6 6 11 15 9 3 7 8 6 9 16 4 38 29"],
  344|   [2024, 538, 270, ['trump', "R", 312, 49.8], ['harris', "D", 226, 48.3], [], "",
  345|     "R D R D D D R R R D D R D D D R R R R R R R D D D D R D R R R R D D D R D R R R R R D R R R R R D R R",
  346|     "3 4 10 3 4 12 4 4 3 10 19 15 28 11 8 6 3 3 6 11 17 19 14 7 4 54 6 10 5 10 8 4 13 10 3 11 5 6 6 11 16 9 3 7 8 6 9 16 4 40 30"],
  347| ];
  348| 
  349| /** One candidate: A the winner, B the runner-up, C, D, … everyone else. */
  350| export interface Candidate {
  351|   readonly key: string;
  352|   /** PEOPLE's id, for the winner and runner-up; null for the others. */
  353|   readonly id: PersonId | null;
  354|   readonly name: string;
  355|   readonly short: string;
  356|   readonly party: string;
  357|   readonly partyLabel: string;
  358|   readonly family: Family | null;
  359|   readonly ev: number;
  360|   readonly popular: number | null;
  361|   readonly portrait: string | null;
  362|   /** Their Wikipedia article. */
  363|   readonly wiki: string;
  364| }
  365| 
  366| /** A state that cast electoral votes, and who carried it ('O': a split delegation). */
  367| export interface ElectionState {
  368|   readonly code: string;
  369|   readonly ev: number;
  370|   readonly party: string;
  371|   readonly won: string;
  372| }
  373| 
  374| export interface Election {
  375|   readonly year: number;
  376|   readonly total: number;
  377|   readonly majority: number;
  378|   readonly note: string;
  379|   readonly candidates: readonly [Candidate, ...Candidate[]];
  380|   readonly winner: 'A';
  381|   readonly unopposed: boolean;
  382|   readonly states: readonly ElectionState[];
  383| }
  384| 
  385| // The geo.ts tile order the per-state strings above follow.
  386| const ORDER = STATES.map((s) => s.code);
  387| 
  388| const party = (code: string): Pick<Candidate, 'party' | 'partyLabel' | 'family'> => {
  389|   const [label, family] = PARTY_BY_CODE.get(code) ?? [code, null];
  390|   return { party: code, partyLabel: label, family };
  391| };
  392| 
  393| const person = ([id, code, ev, popular]: Ran, key: string): Candidate => {
  394|   const [name, short] = PEOPLE[id];
  395|   return { key, id, name, short, ...party(code), ev, popular, portrait: assetUrl(`portraits/${id}.jpg`), wiki: wikiUrl(id, name) };
  396| };
  397| 
  398| const cache = new Map<number, Election>();
  399| 
  400| /**
  401|  * One election as it happened, or null for a year with none.
  402|  * candidates: the winner (key A), the runner-up (B, absent when unopposed),
  403|  * then anyone else who won electoral votes or a real share of the vote
  404|  * (C, D, …). states: each state that cast electoral votes, with the
  405|  * candidate key that carried it ('O' for a split delegation).
  406|  */
  407| export function electionOf(year: number): Election | null {
  408|   const hit = cache.get(year);
  409|   if (hit) return hit;
  410|   const row = RESULTS.find((r) => r[0] === year);
  411|   if (!row) return null;
  412|   const [y, total, majority, a, b, others, note, codes, evs] = row;
  413|   const candidates: [Candidate, ...Candidate[]] = [person(a, 'A')];
  414|   if (b) candidates.push(person(b, 'B'));
  415|   others.forEach(([name, short, code, ev, popular], i) => {
  416|     candidates.push({ key: String.fromCharCode(67 + i), id: null, name, short, ...party(code), ev, popular, portrait: null, wiki: wikiUrl(null, name) });
  417|   });
  418|   const byParty = new Map<string, string>();
  419|   for (const c of candidates) if (!byParty.has(c.party)) byParty.set(c.party, c.key);
  420|   const code = codes.split(' ');
  421|   const ev = evs.split(' ').map(Number);
  422|   const states = ORDER.map((s, i) => {
  423|     const p = code[i] ?? '-';
  424|     return { code: s, ev: ev[i] ?? 0, party: p, won: byParty.get(p) ?? 'O' };
  425|   }).filter((s) => s.party !== '-');
  426|   const e: Election = { year: y, total, majority, note, candidates, winner: 'A', unopposed: !b, states };
  427|   cache.set(year, e);
  428|   return e;
  429| }
  430| 
  431| /** The years with a rich sample story: where a random start lands. */
  432| export const FEATURED: readonly number[] = [1800, 1860, 1876, 1896, 1912, 1948, 1960, 1968, 2000, 2016];
```

## `src/lib/simulacra/narrator.test.ts`

```ts
    1| import { readFileSync } from 'node:fs';
    2| import { join } from 'node:path';
    3| import { fileURLToPath } from 'node:url';
    4| import { describe, expect, test } from 'vitest';
    5| import { LIMITED_MESSAGE } from './api';
    6| import { type SayInput, say, sourcesOf, traceOf } from './narrator';
    7| import { type Bundle, BundleSchema, type RunResult } from './schemas';
    8| import { electionFor, type ShownRun } from './state';
    9| 
   10| const ROOT = fileURLToPath(new URL('../../..', import.meta.url));
   11| const bundle = BundleSchema.parse(JSON.parse(readFileSync(join(ROOT, 'tests', 'fixtures', 'bundle.example.json'), 'utf8')));
   12| 
   13| /** A run as the server answers it (serve/simulacra.ts compute): the bundle's run plus the briefs behind it. */
   14| function served(b: Bundle, keys: readonly string[]): RunResult {
   15|   const base = b.runs[[...keys].sort().join('+')];
   16|   if (!base) throw new Error(`no run for ${keys.join('+')}`);
   17|   const told = Object.fromEntries(keys.flatMap((k) => (b.told?.[k] ? [[k, b.told[k]]] : [])));
   18|   return { ...base, told, ...(b.pre ? { pre: b.pre } : {}) };
   19| }
   20| 
   21| describe('traceOf', () => {
   22|   test('two chosen what-ifs: applied, what changed, the brief, what voters were told, the interviews, the research, the count', () => {
   23|     const res = served(bundle, ['league', 'no-19th']);
   24|     expect(traceOf(res, '', ['league', 'no-19th'], 1920)).toEqual([
   25|       'Applied: The Senate Ratifies the League, The 19th Amendment Fails.',
   26|       'What changed: The Senate ratifies the peace treaty with its reservations in March 1920, and the League is no longer a campaign issue.',
   27|       'What changed: Tennessee votes the suffrage amendment down, so women can vote for president only where their own state already let them.',
   28|       'Briefed: Each voter got a life, a home state and the ballot, dated November 1, 1920. Each read 3 real newspaper items from that year. Candidates appeared as neutral letters, not names.',
   29|       'Pre-interviewed: 12 synthetic voters, in 1920 as it was. This set the baseline.',
   30|       'Told the voters: The Senate Ratifies the League. “In March 1920 the Senate ratified the peace treaty with its reservations, and the United States took its seat in the League of Nations this spring. The treaty is settled, and neither party proposes to reopen it.” Taken off the platforms: League of Nations.',
   31|       'Told the voters: The 19th Amendment Fails. “In August the Tennessee legislature voted the woman suffrage amendment down, and it has not been ratified.”',
   32|       'Asked again: 4 people in 2 groups, now with the change. Each heard one of 3 wordings of the question.',
   33|       'Measured: Each person’s answer with the change, minus their answer without it.',
   34|       "What historians found (9 findings, strong evidence): No source measures the League's effect on 1920 voting. Sources give qualitative accounts: the League and Wilson hurt Cox, Irish and German Americans left the Democrats (partly over wartime grievances), and Harding won 60.3% to 34.1% on low turnout. No group-level numbers.",
   35|       'Against history: On the Republican two-party share, the sources point the same way as the interviews (-0.1 points), without numbers.',
   36|       'The numbers: the 1920 census voting-age tables and certified returns; every draw reproduces 1920 exactly before the change.',
   37|       'How sure: I reran it 100 times with different population and parameter draws.',
   38|       "Low confidence: The interviews' answer changes sign with the question's wording, though the record points the same way.",
   39|       'Counted: 4 states.',
   40|     ]);
   41|   });
   42| 
   43|   test('typed words: how they were read, no Applied line, and one what-if told without a lead', () => {
   44|     const lines = traceOf(served(bundle, ['league']), 'what if the league passed', [], 1920);
   45|     expect(lines[0]).toBe('Read: “what if the league passed” as The Senate Ratifies the League.');
   46|     expect(lines.some((l) => l.startsWith('Applied:'))).toBe(false);
   47|     expect(lines.find((l) => l.startsWith('Told the voters:'))).toMatch(/^Told the voters: “In March 1920/);
   48|   });
   49| 
   50|   test('a staged what-if: the real items it takes out and the news from its world', () => {
   51|     const told = (removed: number) => ({
   52|       league: { facts: ['The treaty is settled.'], removed, items: [{ date: '1920-10-01', text: 'Geneva cheers.' }, { date: '1920-10-02', text: 'Delegates sail.' }] },
   53|     });
   54|     const line = (removed: number) =>
   55|       traceOf({ ...served(bundle, ['league']), told: told(removed) }, '', ['league'], 1920).find((l) => l.startsWith('Told the voters:'));
   56|     expect(line(2)).toBe(
   57|       'Told the voters: “The treaty is settled.” Took out 2 newspaper items the change makes false. Their newspapers also carried: “Geneva cheers.” “Delegates sail.”',
   58|     );
   59|     expect(line(1)).toContain(' Took out 1 newspaper item the change makes false.');
   60|     expect(line(0)).not.toContain('Took out');
   61|   });
   62| 
   63|   test('a reinterpreted change leads its explanation, with what changed', () => {
   64|     const base = served(bundle, ['league']);
   65|     const reread = 'Not quite what you asked: the League passing reads as the Senate ratifying the treaty.';
   66|     const lines = traceOf({ ...base, howIGotThis: [...(base.howIGotThis ?? []), reread] }, 'what if the league passed', [], 1920);
   67|     const at = lines.indexOf(reread);
   68|     expect(at).toBeGreaterThan(0);
   69|     expect(at).toBeLessThan(lines.findIndex((l) => l.startsWith('Briefed:')));
   70|     expect(lines.filter((l) => l === reread)).toHaveLength(1);
   71|   });
   72| 
   73|   test('no interviews: no brief and no pre-interview', () => {
   74|     const res = { ...served(bundle, ['no-19th']), cohortEffects: [] };
   75|     const lines = traceOf(res, '', ['no-19th'], 1920);
   76|     expect(lines.some((l) => l.startsWith('Briefed:') || l.startsWith('Pre-interviewed:') || l.startsWith('Asked again:'))).toBe(false);
   77|   });
   78| 
   79|   test('sources: the research behind the applied what-ifs, and the data not already cited', () => {
   80|     const s = sourcesOf(served(bundle, ['league']));
   81|     expect(s?.research.length).toBeGreaterThan(0);
   82|     expect(s?.research.every((r) => typeof r.text === 'string' && r.text.length > 0)).toBe(true);
   83|   });
   84| });
   85| 
   86| const ELECTION = electionFor(1920);
   87| const NAMES = { A: 'Harding', B: 'Cox', O: 'Others' };
   88| const BASE: SayInput = {
   89|   server: 'online',
   90|   year: 1920,
   91|   election: ELECTION,
   92|   run: null,
   93|   running: false,
   94|   runError: null,
   95|   simFailed: null,
   96|   sim: { slices: bundle.election.slices, whatIfs: bundle.election.whatIfs },
   97|   toggled: null,
   98|   whatIfs: bundle.election.whatIfs,
   99|   slice: null,
  100|   showing: 'history',
  101|   result: null,
  102|   names: NAMES,
  103|   person: null,
  104|   finding: false,
  105|   draft: '',
  106|   shown: Infinity,
  107|   sample: false,
  108| };
  109| 
  110| describe('say', () => {
  111|   test('the server first: connecting, no service, too many requests', () => {
  112|     expect(say({ ...BASE, server: 'connecting' })).toEqual({ text: 'Getting 1920’s voters ready.', busy: true });
  113|     const none = say({ ...BASE, server: 'unsupported' });
  114|     expect(none.text).toBe('This server has no simulation service yet, so I can’t rerun elections here.');
  115|     expect(none.actions?.map((a) => a.key)).toEqual(['sample', 'retry']);
  116|     const limited = say({ ...BASE, server: 'limited' });
  117|     expect(limited.text).toBe(LIMITED_MESSAGE);
  118|     expect(limited.actions?.map((a) => a.key)).toEqual(['retry']);
  119|   });
  120| 
  121|   test('the greeting, a tapped suggestion, then a rerun coming out step by step', () => {
  122|     expect(say(BASE).text).toBe('Change one thing about 1920 and I’ll rerun it.');
  123|     expect(say(BASE).detail).toBe('Pick a counterfactual or type your own.\nTap a group to meet someone in it.');
  124|     expect(say({ ...BASE, toggled: 'league' }).detail).toBe('What people care about, low confidence. Press Rerun to see what happens.');
  125|     const res = served(bundle, ['league']);
  126|     const trace = traceOf(res, '', ['league'], 1920);
  127|     const shown: ShownRun = { ...res, runId: 'r1', keys: ['league'], text: '', trace, ask: '', ran: ['league'] };
  128|     const working = say({ ...BASE, result: shown, showing: 'whatif', shown: 1 });
  129|     expect(working.busy).toBe(true);
  130|     expect(working.steps?.map((s) => s.state)).toEqual(['done', 'doing']);
  131|     const verdict = say({ ...BASE, result: shown, showing: 'whatif' });
  132|     expect(verdict.text).toBe(res.summary.replaceAll('the voters I interviewed', 'the voters'));
  133|     expect(verdict.text).toContain('the voters lean');
  134|     expect(verdict.steps).toHaveLength(trace.length);
  135|     expect(say({ ...BASE, result: shown }).text).toBe('This is 1920 as it happened. Switch to Rerun to see yours.');
  136|   });
  137| });
```

## `src/lib/simulacra/narrator.ts`

```ts
    1| // What the robot says (the Narrator's pure parts): a finished rerun's steps
    2| // (traceOf), what it drew on (sourcesOf), and the one line for the page's
    3| // state right now (say). say() checks, first match wins: the simulation
    4| // service, an unopposed year, a rerun working or failed, the year's voters
    5| // failed or loading, a tapped suggestion, a picked group, typed words, a rerun's steps
    6| // coming out, then its verdict, history, or the greeting.
    7| import { LIMITED_MESSAGE } from './api';
    8| import type { Election } from './history';
    9| import type { ActiveRun } from './runs';
   10| import type { Choice, Kind, RunResult, Slice, Step, Voter, WhatIf } from './schemas';
   11| import type { Server, ShownRun, Sim } from './state';
   12| import type { Names } from './types';
   13| import type { BubbleSources, Message } from './whatif';
   14| 
   15| /** A finished rerun's steps come out one at a time, this far apart, ms. */
   16| export const STEP_MS = 420;
   17| 
   18| export const CONFIDENCE: Readonly<Record<'high' | 'medium' | 'low', string>> = {
   19|   high: 'High confidence: who could vote is arithmetic on census counts.',
   20|   medium: 'Medium confidence: where people lived is on record; how they’d have voted there is inferred.',
   21|   low: 'Low confidence: what people cared about is the hardest thing to change and know.',
   22| };
   23| 
   24| export const KIND_NOTE: Readonly<Record<Kind, string>> = {
   25|   franchise: 'Who can vote, high confidence.',
   26|   population: 'Who lives where, medium confidence.',
   27|   issue: 'What people care about, low confidence.',
   28|   candidate: 'Who is on the ballot, low confidence.',
   29| };
   30| 
   31| const pct = (r: number) => `${Math.round(r * 100)}%`;
   32| 
   33| /**
   34|  * A rerun's steps, from what the server did: how your words were read, what
   35|  * changed, who was asked again, what it counted, and how sure it is. Each
   36|  * line is "Label: text", like the server's, so the bubble sets it as a row.
   37|  */
   38| export function traceOf(res: RunResult, text: string, keys: readonly string[], y: number): string[] {
   39|   const out: string[] = [];
   40|   const typedRead = res.applied.filter((a) => !keys.includes(a.key));
   41|   if (text) {
   42|     out.push(typedRead.length ? `Read: “${text}” as ${typedRead.map((a) => a.label).join(', ')}.` : `Read: “${text}”.`);
   43|   }
   44|   if (res.unknown) out.push(`Left out: “${res.unknown}”. I couldn’t model it.`);
   45|   const chosenLabels = res.applied.filter((a) => keys.includes(a.key)).map((a) => a.label);
   46|   if (chosenLabels.length) out.push(`Applied: ${chosenLabels.join(', ')}.`);
   47|   // The server's lines: what changed (and whose behaviour new voters
   48|   // borrow) first; the research, the numbers and how sure after the
   49|   // interviews.
   50|   const how = res.howIGotThis ?? [];
   51|   // A typed change the server reinterpreted ("Not quite what you asked") leads.
   52|   const isChange = (l: string) => /^(Not quite what you asked|What changed|New voters borrow)/.test(l);
   53|   out.push(...how.filter(isChange));
   54|   const applied = res.applied.map((a) => a.key);
   55|   const labelOf = (k: string) => res.applied.find((a) => a.key === k)?.label || k;
   56|   const asked = (res.cohortEffects ?? []).filter((c) => applied.includes(c.whatIf));
   57|   const interviewed = asked.length > 0 || !!res.interview?.byWhatIf.length;
   58|   const pre = res.pre;
   59|   if (pre?.voters && interviewed) {
   60|     // Each voter's brief, then the interview before any change: the
   61|     // baseline, and the leakage tests when the run had them.
   62|     const n = `${pre.voters} synthetic voters${pre.interviews > pre.voters ? ` (${pre.interviews} interviews)` : ''}`;
   63|     const leak: string[] = [];
   64|     if (pre.recall) leak.push(`In ${pre.recall.n} recall probes the model named the real winner ${pct(pre.recall.winnerRate)} of the time.`);
   65|     if (pre.swap) leak.push(`With party labels swapped, answers followed the platforms ${pct(pre.swap.platformRate)} of the time.`);
   66|     const asOf = pre.asOf
   67|       ? new Date(`${pre.asOf}T12:00:00`).toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' })
   68|       : '';
   69|     const [lo, hi] = pre.items ?? [];
   70|     let items = '';
   71|     if (hi) items = lo === hi ? `${lo}` : `${lo}–${hi}`;
   72|     out.push(
   73|       `Briefed: Each voter got a life, a home state and the ballot${asOf ? `, dated ${asOf}` : ''}. ` +
   74|         (items ? `Each read ${items} real newspaper items from that year. ` : `No period newspapers were available for ${y}. `) +
   75|         'Candidates appeared as neutral letters, not names.',
   76|     );
   77|     out.push(
   78|       `Pre-interviewed: ${n}, in ${y} as it was. This set the baseline${leak.length ? ' and tested for leakage' : ''}.${leak.length ? ` ${leak.join(' ')}` : ''}`,
   79|     );
   80|   }
   81|   // The exact words that put each change into the voters' world: settled
   82|   // facts, or news printed on the nominee's own ballot line.
   83|   const told = applied.filter((k) => res.told?.[k]);
   84|   for (const k of told) {
   85|     const t = res.told?.[k];
   86|     if (!t) continue;
   87|     const lead = told.length > 1 ? `${labelOf(k)}. ` : '';
   88|     const said = [...(t.facts ?? []), ...(t.news ?? [])].map((s) => `“${s}”`).join(' ');
   89|     const where = t.news?.length && !t.facts?.length ? ' Printed as recent news on the nominee’s ballot line.' : '';
   90|     const planks = [
   91|       t.added?.length ? ` Added to the platforms: ${t.added.map((p) => p.replace(/\.$/, '')).join('; ')}.` : '',
   92|       t.dropped?.length ? ` Taken off the platforms: ${t.dropped.join(', ')}.` : '',
   93|       // Staged: real items the change makes false come out; news from the changed world goes in.
   94|       t.removed ? ` Took out ${t.removed} newspaper item${t.removed === 1 ? '' : 's'} the change makes false.` : '',
   95|       t.items?.length ? ` Their newspapers also carried: ${t.items.map((i) => `“${i.text}”`).join(' ')}` : '',
   96|     ].join('');
   97|     out.push(`Told the voters: ${lead}${said}${where}${planks}`);
   98|   }
   99|   if (asked.length) {
  100|     const people = Math.max(
  101|       ...applied.map((k) => asked.filter((c) => c.whatIf === k).reduce((sum, c) => sum + (c.n || 0), 0)),
  102|     );
  103|     const wordings = (pre?.wordings ?? 0) > 1 ? ` Each heard one of ${pre?.wordings} wordings of the question.` : '';
  104|     out.push(`Asked again: ${people} people in ${new Set(asked.map((c) => c.cohort)).size} groups, now with the change.${wordings}`);
  105|     out.push('Measured: Each person’s answer with the change, minus their answer without it.');
  106|   }
  107|   // After the research, how the interviews compare with the closest real cases.
  108|   const rest = how.filter((l) => !isChange(l));
  109|   const lastFound = rest.map((l) => l.startsWith('What historians found')).lastIndexOf(true);
  110|   const against = (res.evidence ?? [])
  111|     .filter((e) => applied.includes(e.whatIf) && e.agreementDetail)
  112|     .map((e) => `Against history: ${e.agreementDetail}`);
  113|   rest.splice(lastFound + 1, 0, ...against);
  114|   out.push(...rest);
  115|   if (res.states.length) out.push(`Counted: ${res.states.length} states.`);
  116|   return out;
  117| }
  118| 
  119| /**
  120|  * What a rerun drew on, for the bubble's Sources: the dated newspapers in
  121|  * the voters' briefs, the research behind each applied what-if, and the data.
  122|  */
  123| export function sourcesOf(res: RunResult): BubbleSources | null {
  124|   const applied = res.applied.map((a) => a.key);
  125|   const ev = (res.evidence ?? []).filter((e) => applied.includes(e.whatIf));
  126|   const research = ev.flatMap((e) => e.findings.map((f) => ({ when: f.when || '', text: f.claim })));
  127|   const cited = new Set(ev.flatMap((e) => e.findings.flatMap((f) => f.sources.map((s) => s.title))));
  128|   const reading = res.reading ?? [];
  129|   const data = (res.sources ?? [])
  130|     .map((s) => s.title)
  131|     .filter((t) => !cited.has(t) && !(reading.length && /Chronicling America/.test(t)));
  132|   return reading.length || research.length || data.length ? { reading, research, data } : null;
  133| }
  134| 
  135| const lower = (label: string) =>
  136|   /^(Black|White|Latino|Southern|Northern|Irish|Catholic|Plains|New|Progressive|Loyal|Socialist|Northerners|\d)/.test(label)
  137|     ? label
  138|     : label.charAt(0).toLowerCase() + label.slice(1);
  139| 
  140| /** One line about a group: who couldn't vote, stayed home, or how those who voted chose. */
  141| export function aboutGroup(s: Slice, y: number, nm: Names): string {
  142|   const voted = s.A + s.B + s.O;
  143|   if (s.barred >= 0.95) return `${s.label} couldn’t vote in ${y}.`;
  144|   if (s.barred >= 0.5) return `${Math.round(s.barred * 10)} in 10 ${lower(s.label)} couldn’t vote in ${y}.`;
  145|   if (voted < 0.02) return `Most ${lower(s.label)} stayed home in ${y}.`;
  146|   let k: 'A' | 'B' | 'O' = 'O';
  147|   if (s.A >= s.B && s.A >= s.O) k = 'A';
  148|   else if (s.B >= s.O) k = 'B';
  149|   return `${Math.round((s[k] / voted) * 100)}% of ${lower(s.label)} who voted chose ${nm[k] ?? ''}.`;
  150| }
  151| 
  152| const did = (k: Choice, nm: Names): string => {
  153|   switch (k) {
  154|     case 'A':
  155|       return `voted for ${nm.A}`;
  156|     case 'B':
  157|       return `voted for ${nm.B ?? ''}`;
  158|     case 'O':
  159|       return `voted for ${nm.O === 'Others' ? 'a third party' : nm.O}`;
  160|     case 'home':
  161|       return 'stayed home';
  162|     case 'barred':
  163|       return 'couldn’t vote';
  164|     default:
  165|       return k satisfies never;
  166|   }
  167| };
  168| 
  169| /** Everything say() reads. */
  170| export interface SayInput {
  171|   readonly server: Server;
  172|   readonly year: number;
  173|   readonly election: Election;
  174|   readonly run: ActiveRun | null;
  175|   /** The run is this year's. */
  176|   readonly running: boolean;
  177|   readonly runError: string | null;
  178|   /** Why the year's groups didn't load. */
  179|   readonly simFailed: string | null;
  180|   readonly sim: Sim | null;
  181|   /** A just-tapped suggestion. */
  182|   readonly toggled: string | null;
  183|   readonly whatIfs: readonly WhatIf[];
  184|   /** The picked group. */
  185|   readonly slice: string | null;
  186|   readonly showing: 'history' | 'whatif';
  187|   readonly result: ShownRun | null;
  188|   readonly names: Names;
  189|   /** Someone from the picked group, once fetched. */
  190|   readonly person: Voter | null;
  191|   /** That person is being fetched. */
  192|   readonly finding: boolean;
  193|   /** The typed words. */
  194|   readonly draft: string;
  195|   /** How many of the rerun's steps are out (Infinity: all of them). */
  196|   readonly shown: number;
  197|   /** The sample stand-in is on. */
  198|   readonly sample: boolean;
  199| }
  200| 
  201| function running(y: number, r: ActiveRun): Message {
  202|   const steps: Step[] = [];
  203|   if (r.text) steps.push({ text: `Reading “${r.text}”.`, state: 'done' });
  204|   if (r.labels.length) steps.push({ text: `Applying ${r.labels.join(', ')}.`, state: 'done' });
  205|   if (r.steps?.length) {
  206|     return {
  207|       text: 'That’s new to me, so I’m modelling it. This will take a minute.',
  208|       steps: [...steps.slice(r.text ? 1 : 0), ...r.steps],
  209|       busy: true,
  210|     };
  211|   }
  212|   steps.push({ text: r.total ? `Rerunning ${y}: ${r.done} of ${r.total} states counted.` : `Rerunning ${y}.`, state: 'doing' });
  213|   return { text: `Rerunning ${y}…`, steps, busy: true };
  214| }
  215| 
  216| function verdict(res: ShownRun, sample: boolean): Message {
  217|   if (!res.applied.length && res.unknown) {
  218|     return {
  219|       text: `I couldn’t turn “${res.unknown}” into a change I can model${sample ? ' with sample data' : ''}.${res.unknownWhy ? ` ${res.unknownWhy}` : ''} Try one of the what-ifs below.`,
  220|     };
  221|   }
  222|   // Typed words the rerun understood: say how they were read.
  223|   const read = res.text ? res.applied.find((a) => !res.keys.includes(a.key)) : undefined;
  224|   // "the voters I interviewed" is "the voters" (publish.py says that now;
  225|   // bundles published before then still carry the old words).
  226|   const summary = res.summary.replaceAll('the voters I interviewed', 'the voters');
  227|   return {
  228|     steps: res.trace.map((t) => ({ text: t, state: 'done' })),
  229|     interview: res.interview ?? null, // shown when the bubble is opened (More)
  230|     sources: sourcesOf(res), // …and what it drew on
  231|     // The steps already say how the words were read.
  232|     text: `${read && !res.trace.length ? `I read “${res.text}” as ${read.label}. ` : ''}${summary}${res.unknown ? ` I left out “${res.unknown}”; I couldn’t model it.` : ''}`,
  233|     // The summary already names the tier when the server flags it (a built or very-low what-if).
  234|     detail:
  235|       res.confidence && !(res.confidenceLabel && res.summary.includes(res.confidenceLabel)) ? CONFIDENCE[res.confidence] : '',
  236|   };
  237| }
  238| 
  239| /** What the robot says about the simulation service, or null once it's answering. */
  240| function aboutServer(server: Server, y: number): Message | null {
  241|   const noService = (text: string): Message => ({
  242|     text,
  243|     detail: 'The elections themselves are all here. Sample data shows how a rerun works.',
  244|     actions: [
  245|       { key: 'sample', label: 'Use Sample Data', primary: true },
  246|       { key: 'retry', label: 'Try Again' },
  247|     ],
  248|   });
  249|   switch (server) {
  250|     case 'connecting':
  251|       return { text: `Getting ${y}’s voters ready.`, busy: true };
  252|     case 'unsupported':
  253|       return noService('This server has no simulation service yet, so I can’t rerun elections here.');
  254|     case 'offline':
  255|       return noService('I can’t reach the simulation server, so I can’t rerun elections yet.');
  256|     case 'limited':
  257|       return { text: LIMITED_MESSAGE, actions: [{ key: 'retry', label: 'Try Again' }] };
  258|     case 'online':
  259|       return null;
  260|     default:
  261|       return server satisfies never;
  262|   }
  263| }
  264| 
  265| /** What the robot says now. */
  266| export function say(i: SayInput): Message {
  267|   const { year: y, sim: s, result: res, showing: show, names: nm } = i;
  268|   const server = aboutServer(i.server, y);
  269|   if (server) return server;
  270|   if (i.election.unopposed) {
  271|     return {
  272|       text: `${i.election.candidates[0].name} ran unopposed in ${y}, so there’s nothing to rerun.`,
  273|       actions: [{ key: 'shuffle', label: 'Another Election', primary: true }],
  274|     };
  275|   }
  276|   if (i.running && i.run) return running(y, i.run);
  277|   if (i.runError) return { text: i.runError, actions: [{ key: 'rerun', label: 'Try Again', primary: true }] };
  278|   if (i.simFailed && !s) return { text: i.simFailed, actions: [{ key: 'retry', label: 'Try Again' }] };
  279|   if (!s) return { text: `Getting ${y}’s voters ready.`, busy: true };
  280|   const w = i.toggled ? i.whatIfs.find((x) => x.key === i.toggled) : undefined;
  281|   if (w) return { text: w.detail, detail: `${KIND_NOTE[w.kind]} Press Rerun to see what happens.` };
  282|   // A group picked: someone from it, in their own words, and what could
  283|   // change their fate.
  284|   const slice = i.slice;
  285|   if (slice) {
  286|     const g = (show === 'whatif' && res ? res.slices : s.slices).find((x) => x.key === slice);
  287|     const reach = i.whatIfs.filter((x) => x.slices.includes(slice)).map((x) => x.label);
  288|     const could = reach.length ? `What could change that: ${reach.join(', ')}.` : '';
  289|     const person = i.person;
  290|     if (person) {
  291|       const now = show === 'whatif' && person.now && person.now !== person.history ? ` In your ${y}, ${did(person.now, nm)}.` : '';
  292|       const fate = `In ${y}, ${did(person.history, nm)}.${now}`;
  293|       return {
  294|         quote: person.quote,
  295|         by: [person.name, person.line].filter(Boolean).join(', '),
  296|         text: `${fate}${could && show !== 'whatif' ? ` ${could}` : ''}`,
  297|       };
  298|     }
  299|     if (g) return { text: aboutGroup(g, y, nm), detail: i.finding ? 'Finding someone from this group…' : could };
  300|   }
  301|   // Typing: say what will happen to the words.
  302|   if (i.draft.trim() && !slice) {
  303|     return {
  304|       text: 'I’ll read that and turn it into a change I can model.',
  305|       steps: [{ text: `Reading “${i.draft.trim()}”…`, state: 'doing' }],
  306|       detail: 'Press Rerun to run it.',
  307|     };
  308|   }
  309|   if (res && show === 'whatif' && res.trace.length && i.shown < res.trace.length) {
  310|     return {
  311|       text: 'Working it through…',
  312|       steps: res.trace.slice(0, i.shown + 1).map((t, n) => ({ text: t, state: n < i.shown ? 'done' : 'doing' })),
  313|       busy: true,
  314|     };
  315|   }
  316|   if (res && show === 'whatif') return verdict(res, i.sample);
  317|   if (res) return { text: `This is ${y} as it happened. Switch to Rerun to see yours.` };
  318|   return {
  319|     opening: true,
  320|     text: `Change one thing about ${y} and I’ll rerun it.`,
  321|     // The newline breaks on a narrow window only (WhatIf .aside); a wide one reads it as a space.
  322|     detail: 'Pick a counterfactual or type your own.\nTap a group to meet someone in it.',
  323|   };
  324| }
```

## `src/lib/simulacra/palette.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { electionOf } from './history';
    3| import { candidateHues, onPaint, paint } from './palette';
    4| 
    5| describe('candidateHues', () => {
    6|   test('parties keep their colour; the 4th candidate and beyond fold into Other', () => {
    7|     // 1860: Lincoln (R), Breckinridge (Southern Democrat), Bell, Douglas.
    8|     const e = electionOf(1860);
    9|     expect(e).not.toBeNull();
   10|     if (!e) return;
   11|     const hues = candidateHues(
   12|       e.candidates.map((c) => ({ key: c.key, party: c.family })),
   13|       Object.fromEntries(e.candidates.map((c) => [c.key, c.ev])),
   14|     );
   15|     expect(hues.get('A')).toBe('red');
   16|     expect(hues.get('B')).toBe('blue');
   17|     // Bell (39 EV) takes the era's free hue; Douglas (12 EV), fourth, is Other.
   18|     expect(hues.get('C')).toBe('green');
   19|     expect(hues.get('D')).toBe('other');
   20|   });
   21| 
   22|   test('a party already holding its hue doesn’t take it twice', () => {
   23|     const hues = candidateHues([
   24|       { key: 'A', party: 'democratic' },
   25|       { key: 'B', party: 'democratic' },
   26|       { key: 'C', party: 'whig' },
   27|     ]);
   28|     expect(hues.get('A')).toBe('blue');
   29|     expect(hues.get('C')).toBe('orange');
   30|     expect(hues.get('B')).toBe('aqua');
   31|   });
   32| 
   33|   test('the founding era: Democratic-Republicans aqua, Federalists violet', () => {
   34|     const hues = candidateHues([
   35|       { key: 'A', party: 'democratic-republican' },
   36|       { key: 'B', party: 'federalist' },
   37|     ]);
   38|     expect([hues.get('A'), hues.get('B')]).toEqual(['aqua', 'violet']);
   39|   });
   40| });
   41| 
   42| describe('paint and onPaint', () => {
   43|   test('light and dark steps differ; no hue is Other', () => {
   44|     expect(paint('blue', true)).toBe('#2a78d6');
   45|     expect(paint('blue', false)).toBe('#5488c7');
   46|     expect(paint(undefined, true)).toBe(paint('other', true));
   47|   });
   48| 
   49|   test('label ink inverts with the mode', () => {
   50|     // Violet: white on screen in light mode, black on screen (authored white) in dark.
   51|     expect(onPaint('violet', true)).toBe('#ffffff');
   52|     expect(onPaint('violet', false)).toBe('#ffffff');
   53|     // Blue: black on screen in both, so authored black in light and white in dark.
   54|     expect(onPaint('blue', true)).toBe('#000000');
   55|     expect(onPaint('blue', false)).toBe('#ffffff');
   56|   });
   57| });
```

## `src/lib/simulacra/palette.ts`

```ts
    1| // Chart colour for Simulacra Americana.
    2| //
    3| // The host app's dark mode is a filter over the whole page (invert(1)
    4| // hue-rotate(180deg) saturate(1.5)), and light mode drops it. So a chart
    5| // colour is authored twice: light mode uses the palette's light step as-is;
    6| // dark mode uses the value that filter turns into the palette's dark step
    7| // (solved for, and checked against Chrome's rendered pixels). Everything
    8| // neutral — ink, hairlines, washes — is authored once in light values and
    9| // inverts on its own, like the rest of the page.
   10| //
   11| // Steps are the dataviz reference palette. The page colours the winner and
   12| // the runner-up and folds everyone else into "Other": every era's pair is
   13| // validated (CVD and normal-vision separation, both modes, on this page's
   14| // surfaces), and a third or fourth candidate never needs its own hue.
   15| 
   16| export type Hue =
   17|   | 'blue'
   18|   | 'orange'
   19|   | 'aqua'
   20|   | 'violet'
   21|   | 'green'
   22|   | 'red'
   23|   | 'other'
   24|   | 'good'
   25|   | 'warning'
   26|   | 'critical';
   27| 
   28| /** 'k' = black text on screen, 'w' = white. */
   29| type Ink = 'k' | 'w';
   30| 
   31| // hue: [light step, dark-mode authored, label ink on the fill: light, dark],
   32| // the ink by contrast with the fill.
   33| const HUES: Readonly<Record<Hue, readonly [string, string, Ink, Ink]>> = {
   34|   blue: ['#2a78d6', '#5488c7', 'k', 'k'],
   35|   orange: ['#eb6834', '#d47f5d', 'k', 'k'],
   36|   aqua: ['#1baf7a', '#3d9677', 'k', 'k'],
   37|   violet: ['#4a3aa7', '#716aad', 'w', 'k'],
   38|   green: ['#008300', '#63ba63', 'w', 'w'],
   39|   red: ['#e34948', '#c06b6b', 'k', 'k'],
   40|   // A neutral, authored once and left to invert: charcoal on the light page,
   41|   // a light grey on the dark one — apart from every hue in lightness, so it
   42|   // survives colour blindness beside red and aqua.
   43|   other: ['#4d4c48', '#4d4c48', 'w', 'k'],
   44|   // Status (fixed meaning; always with an icon and a label).
   45|   good: ['#0ca30c', '#3fa43f', 'w', 'w'],
   46|   warning: ['#fab219', '#764600', 'k', 'k'],
   47|   critical: ['#d03b3b', '#f28f8f', 'w', 'w'],
   48| };
   49| 
   50| /** The colour to author for `hue` in the current mode; no hue → "other". */
   51| export const paint = (hue: Hue | undefined, light: boolean): string => {
   52|   const h = HUES[hue ?? 'other'];
   53|   return light ? h[0] : h[1];
   54| };
   55| 
   56| /** Label ink to author on a `hue` fill: white or black on screen, whichever reads. */
   57| export function onPaint(hue: Hue | undefined, light: boolean): string {
   58|   const h = HUES[hue ?? 'other'];
   59|   const black = (light ? h[2] : h[3]) === 'k';
   60|   // Dark mode inverts what's authored: black on screen is authored white.
   61|   return black === light ? '#000000' : '#ffffff';
   62| }
   63| 
   64| /** The party families that own a hue somewhere on the timeline (history.ts). */
   65| export type Family =
   66|   | 'federalist'
   67|   | 'democratic-republican'
   68|   | 'democratic'
   69|   | 'national-republican'
   70|   | 'whig'
   71|   | 'republican';
   72| 
   73| interface Era {
   74|   readonly when: (parties: ReadonlySet<Family | null | undefined>) => boolean;
   75|   readonly hues: readonly Hue[];
   76|   readonly own: Readonly<Partial<Record<Family, Hue>>>;
   77| }
   78| 
   79| // The earliest era: everything before the Democrats, and the fallback.
   80| const FOUNDING: Era = {
   81|   when: () => true,
   82|   hues: ['aqua', 'violet', 'orange'],
   83|   own: { 'democratic-republican': 'aqua', federalist: 'violet' },
   84| };
   85| 
   86| // Each era's validated triple and the parties that own a hue in it.
   87| const ERAS: readonly Era[] = [
   88|   { when: (p) => p.has('republican'), hues: ['red', 'blue', 'green'], own: { republican: 'red', democratic: 'blue' } },
   89|   {
   90|     when: (p) => p.has('democratic') || p.has('whig') || p.has('national-republican'),
   91|     hues: ['blue', 'orange', 'aqua'],
   92|     own: { democratic: 'blue', whig: 'orange', 'national-republican': 'orange' },
   93|   },
   94|   FOUNDING,
   95| ];
   96| 
   97| export interface HueCandidate {
   98|   readonly key: string;
   99|   readonly party?: Family | null | undefined;
  100| }
  101| 
  102| /**
  103|  * Hue per candidate key for one election. Parties keep their colour across
  104|  * the timeline (Democrats blue, Republicans red); anyone else takes the era's
  105|  * free hue, largest share first; past three, "other".
  106|  * @param weight e.g. electoral votes by key
  107|  */
  108| export function candidateHues(
  109|   candidates: readonly HueCandidate[] = [],
  110|   weight: Readonly<Record<string, number>> = {},
  111| ): Map<string, Hue> {
  112|   const parties = new Set(candidates.map((c) => c.party));
  113|   const era = ERAS.find((e) => e.when(parties)) ?? FOUNDING;
  114|   const order = [...candidates].sort(
  115|     (a, b) => (weight[b.key] ?? 0) - (weight[a.key] ?? 0) || a.key.localeCompare(b.key),
  116|   );
  117|   const out = new Map<string, Hue>();
  118|   const used = new Set<Hue>();
  119|   for (const c of order) {
  120|     const h = c.party ? era.own[c.party] : undefined;
  121|     if (h && !used.has(h)) {
  122|       out.set(c.key, h);
  123|       used.add(h);
  124|     }
  125|   }
  126|   for (const c of order) {
  127|     if (out.has(c.key)) continue;
  128|     const h = era.hues.find((x) => !used.has(x));
  129|     if (h) {
  130|       out.set(c.key, h);
  131|       used.add(h);
  132|     } else out.set(c.key, 'other');
  133|   }
  134|   return out;
  135| }
```

## `src/lib/simulacra/places.ts`

```ts
    1| // Places named in the page's words — a state, a region, the colonies — found
    2| // by quick pattern matching, so pointing at the word can light its tiles on
    3| // the map (MiniMap's `highlight`). Regions are the harness's own
    4| // (simharness/geo.py), so "midwest" means the voters' midwest.
    5| import { writable } from 'svelte/store';
    6| import { STATES } from './geo';
    7| 
    8| const SOUTH = ['VA', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'LA', 'TX', 'AR', 'TN'];
    9| const BORDER = ['KY', 'MD', 'DE', 'MO', 'WV', 'OK'];
   10| const NORTHEAST = ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'];
   11| const NEW_ENGLAND = ['ME', 'NH', 'VT', 'MA', 'RI', 'CT'];
   12| const MIDWEST = ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'ND', 'SD', 'NE', 'KS'];
   13| const WEST = ['MT', 'ID', 'WY', 'CO', 'NM', 'AZ', 'UT', 'NV', 'WA', 'OR', 'CA'];
   14| const COLONIES = ['NH', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA', 'DE', 'MD', 'VA', 'NC', 'SC', 'GA'];
   15| 
   16| // "George Washington" is a man, not a state.
   17| const statePattern = (code: string, name: string): string =>
   18|   code === 'WA' ? '(?<!George )Washington(?! D\\.C\\.)' : name.replace(/ /g, '\\s');
   19| 
   20| // [pattern, codes]. Order matters where one name contains another: the
   21| // regex tries these left to right at each position, so longer names come first.
   22| const RULES: readonly (readonly [string, readonly string[]])[] = [
   23|   ['District of Columbia|Washington,? D\\.C\\.', ['DC']],
   24|   ...STATES.filter((s) => s.code !== 'DC')
   25|     .sort((a, b) => b.name.length - a.name.length)
   26|     .map((s) => [statePattern(s.code, s.name), [s.code]] as const),
   27|   ['(?:the\\s)?(?:thirteen|13|original)\\s(?:colonies|states)', COLONIES],
   28|   ['New\\sEngland(?:ers?)?', NEW_ENGLAND],
   29|   // Lowercase "south" only as a region ("the south", a group's ", south"), not "went south".
   30|   ['(?:Deep\\s)?South(?:erners?|ern)?|(?<=(?:the|,)\\s)south(?:ern)?|[Dd]ixie', SOUTH],
   31|   ['[Mm]id-?[Ww]est(?:erners?|ern)?|Middle\\sWest', MIDWEST],
   32|   ['[Nn]orth-?[Ee]ast(?:erners?|ern)?', NORTHEAST],
   33|   ['[Bb]order\\sstates?', BORDER],
   34|   ['(?:the\\s|Far\\s)West|Westerners?', WEST],
   35| ];
   36| const RE = new RegExp(`\\b(?:${RULES.map(([p], i) => `(?<r${i}>${p})`).join('|')})\\b`, 'g');
   37| 
   38| /** A run of text: plain, or a place with the state codes it names. */
   39| export interface Segment {
   40|   readonly t: string;
   41|   readonly codes?: readonly string[];
   42| }
   43| 
   44| /** text → plain runs, and the places in it with their state codes. */
   45| export function segments(text = ''): Segment[] {
   46|   const out: Segment[] = [];
   47|   let at = 0;
   48|   for (const m of text.matchAll(RE)) {
   49|     const groups = m.groups ?? {};
   50|     const i = Object.keys(groups).findIndex((k) => groups[k] !== undefined);
   51|     if (m.index > at) out.push({ t: text.slice(at, m.index) });
   52|     out.push({ t: m[0], codes: RULES[i]?.[1] ?? [] });
   53|     at = m.index + m[0].length;
   54|   }
   55|   if (at < text.length) out.push({ t: text.slice(at) });
   56|   return out;
   57| }
   58| 
   59| /** The codes of the place under the pointer, for the map to light. */
   60| export const hoverPlaces = writable<readonly string[]>([]);
```

## `src/lib/simulacra/runs.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import type { Outcome, SimulacraApi } from './api';
    3| import { type ActiveRun, createRunner, GAVE_UP, GIVE_UP_MS, type Finished, POLL_MODELLING_MS, POLL_MS, pollRun } from './runs';
    4| import type { RunResult, RunStatus, WhatIf } from './schemas';
    5| 
    6| const RESULT: RunResult = {
    7|   ev: { A: 300, B: 231, O: 0 },
    8|   winner: 'A',
    9|   states: [{ code: 'TN', won: 'B', flipped: true, margin: -0.4 }],
   10|   slices: [],
   11|   summary: 'Tennessee flips.',
   12|   confidence: 'low',
   13|   applied: [{ key: 'league', label: 'The Senate Ratifies the League', kind: 'issue' }],
   14|   unknown: null,
   15| };
   16| 
   17| const ok = <T>(value: T): Outcome<T> => ({ kind: 'ok', value });
   18| const running = (done: number, steps?: { text: string; state: 'done' | 'doing' }[]): Outcome<RunStatus> =>
   19|   ok({ status: 'running', done, total: 48, ...(steps ? { steps } : {}) });
   20| const done = (result: RunResult = RESULT): Outcome<RunStatus> => ok({ status: 'done', done: 48, total: 48, result });
   21| 
   22| /** A clock that only moves when the loop sleeps. */
   23| function fakeClock() {
   24|   let t = 0;
   25|   const waits: number[] = [];
   26|   return {
   27|     waits,
   28|     now: () => t,
   29|     sleep: async (ms: number) => {
   30|       waits.push(ms);
   31|       t += ms;
   32|     },
   33|   };
   34| }
   35| 
   36| /** api.run answers from `answers` in turn, repeating the last. */
   37| function fakeRun(answers: Outcome<RunStatus>[]) {
   38|   const ids: string[] = [];
   39|   return {
   40|     ids,
   41|     run: async (id: string): Promise<Outcome<RunStatus>> => {
   42|       ids.push(id);
   43|       const next = answers.length > 1 ? answers.shift() : answers[0];
   44|       if (!next) throw new Error('no answer');
   45|       return next;
   46|     },
   47|   };
   48| }
   49| 
   50| describe('pollRun', () => {
   51|   test('polls until done, slower while the server models new words', async () => {
   52|     const clock = fakeClock();
   53|     const api = fakeRun([running(10), running(20, [{ text: 'Reading.', state: 'doing' }]), running(30), done()]);
   54|     const progress: number[] = [];
   55|     const end = await pollRun(api, 'r1', { ...clock, startedAt: 0, current: () => true, onProgress: (r) => progress.push(r.done) });
   56|     expect(end).toEqual({ kind: 'done', result: RESULT });
   57|     expect(progress).toEqual([10, 20, 30]);
   58|     expect(clock.waits).toEqual([POLL_MS, POLL_MS, POLL_MODELLING_MS, POLL_MS]);
   59|     expect(api.ids).toEqual(['r1', 'r1', 'r1', 'r1']);
   60|   });
   61| 
   62|   test('an indeterminate answer keeps polling', async () => {
   63|     const clock = fakeClock();
   64|     const unsure: Outcome<RunStatus> = { kind: 'indeterminate', message: 'No answer in time.' };
   65|     const api = fakeRun([unsure, unsure, done()]);
   66|     const end = await pollRun(api, 'r1', { ...clock, startedAt: 0, current: () => true });
   67|     expect(end.kind).toBe('done');
   68|     expect(api.ids).toHaveLength(3);
   69|   });
   70| 
   71|   test('a rate-limited answer keeps polling, less often', async () => {
   72|     const clock = fakeClock();
   73|     const limited: Outcome<RunStatus> = { kind: 'error', reason: 'limited', message: 'Too many requests.', status: 429 };
   74|     const api = fakeRun([limited, done()]);
   75|     const end = await pollRun(api, 'r1', { ...clock, startedAt: 0, current: () => true });
   76|     expect(end.kind).toBe('done');
   77|     expect(clock.waits).toEqual([POLL_MS, POLL_MODELLING_MS]);
   78|   });
   79| 
   80|   test('a failed run and an error both end it, with the reason', async () => {
   81|     const clock = fakeClock();
   82|     const failed = await pollRun(fakeRun([ok({ status: 'failed', error: 'Stopped.' })]), 'r1', {
   83|       ...clock,
   84|       startedAt: 0,
   85|       current: () => true,
   86|     });
   87|     expect(failed).toEqual({ kind: 'failed', message: 'Stopped.' });
   88|     const offline: Outcome<RunStatus> = { kind: 'error', reason: 'offline', message: 'Can’t reach the simulation server.', status: 0 };
   89|     const lost = await pollRun(fakeRun([offline]), 'r1', { ...clock, startedAt: 0, current: () => true });
   90|     expect(lost).toEqual({ kind: 'failed', message: 'Can’t reach the simulation server.' });
   91|   });
   92| 
   93|   test('gives up after 10 minutes, saying why', async () => {
   94|     const clock = fakeClock();
   95|     const api = fakeRun([running(1)]);
   96|     const end = await pollRun(api, 'r1', { ...clock, startedAt: 0, current: () => true });
   97|     expect(end).toEqual({ kind: 'gave-up', message: GAVE_UP });
   98|     expect(clock.now()).toBeGreaterThanOrEqual(GIVE_UP_MS);
   99|     expect(clock.now()).toBeLessThan(GIVE_UP_MS + POLL_MODELLING_MS);
  100|     // It stopped asking once the time was up.
  101|     expect(api.ids.length).toBe(Math.ceil(GIVE_UP_MS / POLL_MS) - 1);
  102|   });
  103| 
  104|   test('a run the page dropped stops without another call', async () => {
  105|     const clock = fakeClock();
  106|     const api = fakeRun([running(1)]);
  107|     const end = await pollRun(api, 'r1', { ...clock, startedAt: 0, current: () => false });
  108|     expect(end).toEqual({ kind: 'dropped' });
  109|     expect(api.ids).toHaveLength(0);
  110|   });
  111| });
  112| 
  113| /** A page for the runner: its run, its years' what-ifs, and what it was told. */
  114| function fakePage(api: SimulacraApi, whatIfs: Map<number, WhatIf[]>, reload: () => WhatIf[] = () => []) {
  115|   const clock = fakeClock();
  116|   let run: ActiveRun | null = null;
  117|   const seen: (ActiveRun | null)[] = [];
  118|   const finished: Finished[] = [];
  119|   const failed: string[] = [];
  120|   let reloads = 0;
  121|   const runner = createRunner({
  122|     api,
  123|     ...clock,
  124|     getRun: () => run,
  125|     setRun: (r) => {
  126|       run = r;
  127|       seen.push(r);
  128|     },
  129|     reloadSim: async (y) => {
  130|       reloads += 1;
  131|       whatIfs.set(y, reload());
  132|     },
  133|     whatIfsOf: (y) => whatIfs.get(y) ?? [],
  134|     finished: (f) => {
  135|       run = null;
  136|       finished.push(f);
  137|     },
  138|     failed: (m) => failed.push(m),
  139|   });
  140|   return { runner, clock, seen, finished, failed, reloads: () => reloads, run: () => run };
  141| }
  142| 
  143| function fakeApi(runAnswers: Outcome<RunStatus>[], start: Outcome<{ id: string }> = ok({ id: 'r1' })) {
  144|   const stopped: string[] = [];
  145|   const asked: unknown[] = [];
  146|   const runs = fakeRun(runAnswers);
  147|   const api: SimulacraApi = {
  148|     sample: false,
  149|     election: async () => ok({ slices: [], whatIfs: [] }),
  150|     startRun: async (year, ask) => {
  151|       asked.push({ year, ...ask });
  152|       return start;
  153|     },
  154|     run: runs.run,
  155|     stopRun: async (id) => {
  156|       stopped.push(id);
  157|       return ok(null);
  158|     },
  159|     voter: async () => ({ kind: 'error', reason: 'missing', message: 'No one.', status: 404 }),
  160|   };
  161|   return { api, stopped, asked };
  162| }
  163| 
  164| const LEAGUE: WhatIf = { key: 'league', label: 'The Senate Ratifies the League', kind: 'issue', detail: '', slices: [] };
  165| const REQUEST = { year: 1920, keys: [], text: 'what if the league passed', edits: {}, total: 48, labels: [] };
  166| 
  167| describe('createRunner', () => {
  168|   test('on done, a what-if built from typed words reloads the year and comes back chosen', async () => {
  169|     const { api, asked } = fakeApi([running(10), done()]);
  170|     const page = fakePage(api, new Map([[1920, []]]), () => [LEAGUE]);
  171|     await page.runner.start(REQUEST);
  172|     expect(asked).toEqual([{ year: 1920, whatIfs: [], text: 'what if the league passed', edits: {} }]);
  173|     expect(page.reloads()).toBe(1);
  174|     expect(page.finished).toEqual([
  175|       { year: 1920, id: 'r1', result: RESULT, keys: [], text: 'what if the league passed', applied: ['league'] },
  176|     ]);
  177|     expect(page.seen.map((r) => r && { id: r.id, done: r.done })).toEqual([
  178|       { id: null, done: 0 },
  179|       { id: 'r1', done: 0 },
  180|       { id: 'r1', done: 10 },
  181|     ]);
  182|   });
  183| 
  184|   test('a known what-if needs no reload', async () => {
  185|     const { api } = fakeApi([done()]);
  186|     const page = fakePage(api, new Map([[1920, [LEAGUE]]]));
  187|     await page.runner.start({ ...REQUEST, keys: ['league'], text: '' });
  188|     expect(page.reloads()).toBe(0);
  189|     expect(page.finished[0]?.applied).toEqual(['league']);
  190|   });
  191| 
  192|   test('giving up stops the run on the server and says why', async () => {
  193|     const { api, stopped } = fakeApi([running(1)]);
  194|     const page = fakePage(api, new Map());
  195|     await page.runner.start(REQUEST);
  196|     expect(page.failed).toEqual([GAVE_UP]);
  197|     expect(stopped).toEqual(['r1']);
  198|     expect(page.run()).toBeNull();
  199|   });
  200| 
  201|   test('a start that may have landed is reported, not resubmitted', async () => {
  202|     const { api, asked } = fakeApi([done()], { kind: 'indeterminate', message: 'The simulation server didn’t answer in time.' });
  203|     const page = fakePage(api, new Map());
  204|     await page.runner.start(REQUEST);
  205|     expect(asked).toHaveLength(1);
  206|     expect(page.failed).toEqual(['The simulation server didn’t answer in time.']);
  207|     expect(page.run()).toBeNull();
  208|   });
  209| 
  210|   test('stop drops the run and tells the server', async () => {
  211|     const { api, stopped } = fakeApi([running(1)]);
  212|     const page = fakePage(api, new Map());
  213|     const started = page.runner.start(REQUEST);
  214|     // Let it start and poll once, then stop it.
  215|     await Promise.resolve();
  216|     await Promise.resolve();
  217|     page.runner.stop();
  218|     await started;
  219|     expect(page.run()).toBeNull();
  220|     expect(page.finished).toEqual([]);
  221|     expect(page.failed).toEqual([]);
  222|     expect(stopped.length).toBeLessThanOrEqual(1);
  223|   });
  224| });
```

## `src/lib/simulacra/runs.ts`

```ts
    1| // A rerun from start to finish: ask the server to start it, poll it until
    2| // it's done, failed or stopped, and hand the page the result. Plain
    3| // TypeScript: the page keeps the run on show in its own state and passes in
    4| // how to read and write it, so the loop can be driven by a fake API and a
    5| // fake clock in tests.
    6| import type { RunAsk, SimulacraApi } from './api';
    7| import type { RunResult, RunStatus, Step, WhatIf } from './schemas';
    8| 
    9| /** The run on show while it works. `id` is null until the server has started it. */
   10| export interface ActiveRun {
   11|   /** This start, among all of the page's starts. */
   12|   readonly token: number;
   13|   readonly id: string | null;
   14|   readonly year: number;
   15|   /** States counted so far, of `total`. */
   16|   readonly done: number;
   17|   readonly total: number;
   18|   /** The typed words, trimmed. */
   19|   readonly text: string;
   20|   /** The chosen what-ifs' labels. */
   21|   readonly labels: readonly string[];
   22|   /** New words being modelled on the server: its working so far. */
   23|   readonly steps: readonly Step[] | null;
   24| }
   25| 
   26| /** Poll this often, ms; less often while the server models new words (about a minute). */
   27| export const POLL_MS = 300;
   28| export const POLL_MODELLING_MS = 1000;
   29| /** Stop waiting on a run after this long, ms (= the server's own limit on modelling new words). */
   30| export const GIVE_UP_MS = 10 * 60 * 1000;
   31| export const GAVE_UP = 'I stopped waiting after 10 minutes: the server never finished this rerun. Try again.';
   32| 
   33| export type PollEnd =
   34|   | { readonly kind: 'done'; readonly result: RunResult }
   35|   | { readonly kind: 'failed'; readonly message: string }
   36|   | { readonly kind: 'gave-up'; readonly message: string }
   37|   /** The page stopped or replaced the run. */
   38|   | { readonly kind: 'dropped' };
   39| 
   40| export interface PollOptions {
   41|   readonly sleep: (ms: number) => Promise<void>;
   42|   readonly now: () => number;
   43|   /** When the run was started, on `now`'s clock. */
   44|   readonly startedAt: number;
   45|   /** Whether the page still wants this run. */
   46|   readonly current: () => boolean;
   47|   /** Each `running` answer. */
   48|   readonly onProgress?: (status: Extract<RunStatus, { status: 'running' }>) => void;
   49| }
   50| 
   51| /**
   52|  * Polls run `id` until it ends. An indeterminate answer keeps polling, and
   53|  * so does a rate-limited one (less often); any other error ends it; past
   54|  * GIVE_UP_MS it gives up, with the reason.
   55|  */
   56| export async function pollRun(api: Pick<SimulacraApi, 'run'>, id: string, o: PollOptions): Promise<PollEnd> {
   57|   let wait = POLL_MS;
   58|   for (;;) {
   59|     await o.sleep(wait);
   60|     if (!o.current()) return { kind: 'dropped' };
   61|     if (o.now() - o.startedAt >= GIVE_UP_MS) return { kind: 'gave-up', message: GAVE_UP };
   62|     const out = await api.run(id);
   63|     if (!o.current()) return { kind: 'dropped' };
   64|     switch (out.kind) {
   65|       case 'ok': {
   66|         const r = out.value;
   67|         switch (r.status) {
   68|           case 'running':
   69|             o.onProgress?.(r);
   70|             wait = r.steps ? POLL_MODELLING_MS : POLL_MS;
   71|             break;
   72|           case 'done':
   73|             return { kind: 'done', result: r.result };
   74|           case 'failed':
   75|             return { kind: 'failed', message: r.error || 'The rerun failed.' };
   76|           default:
   77|             r satisfies never;
   78|         }
   79|         break;
   80|       }
   81|       case 'indeterminate':
   82|         wait = POLL_MS;
   83|         break;
   84|       case 'error':
   85|         // Too many requests: the run goes on on the server; ask less often.
   86|         if (out.reason === 'limited') {
   87|           wait = POLL_MODELLING_MS;
   88|           break;
   89|         }
   90|         return { kind: 'failed', message: out.message || 'Lost track of the rerun.' };
   91|       case 'unsupported':
   92|         return { kind: 'failed', message: out.message || 'Lost track of the rerun.' };
   93|       default:
   94|         out satisfies never;
   95|     }
   96|   }
   97| }
   98| 
   99| /** A rerun that finished, for the page to keep. */
  100| export interface Finished {
  101|   readonly year: number;
  102|   readonly id: string;
  103|   readonly result: RunResult;
  104|   /** The what-ifs chosen when it started. */
  105|   readonly keys: readonly string[];
  106|   readonly text: string;
  107|   /** What it applied that the year now lists (a what-if built from typed words included). */
  108|   readonly applied: readonly string[];
  109| }
  110| 
  111| export interface RunnerDeps {
  112|   readonly api: SimulacraApi;
  113|   readonly sleep?: (ms: number) => Promise<void>;
  114|   readonly now?: () => number;
  115|   getRun(): ActiveRun | null;
  116|   setRun(run: ActiveRun | null): void;
  117|   /** Reloads a year's groups and what-ifs from the server. */
  118|   reloadSim(year: number): Promise<void>;
  119|   /** The what-ifs a year lists now. */
  120|   whatIfsOf(year: number): readonly WhatIf[];
  121|   finished(f: Finished): void;
  122|   failed(message: string): void;
  123| }
  124| 
  125| export interface StartRequest {
  126|   readonly year: number;
  127|   readonly keys: readonly string[];
  128|   readonly text: string;
  129|   readonly edits: NonNullable<RunAsk['edits']>;
  130|   readonly total: number;
  131|   readonly labels: readonly string[];
  132| }
  133| 
  134| export interface Runner {
  135|   /** Stops any run on show and starts this one. Resolves when it has ended. */
  136|   start(req: StartRequest): Promise<void>;
  137|   /** Stops the run on show, telling the server. */
  138|   stop(): void;
  139| }
  140| 
  141| const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));
  142| 
  143| export function createRunner(deps: RunnerDeps): Runner {
  144|   const sleep = deps.sleep ?? wait;
  145|   const now = deps.now ?? Date.now;
  146|   let tokens = 0;
  147| 
  148|   function stop(): void {
  149|     const r = deps.getRun();
  150|     deps.setRun(null);
  151|     if (r?.id) void deps.api.stopRun(r.id);
  152|   }
  153| 
  154|   async function start(req: StartRequest): Promise<void> {
  155|     if (deps.getRun()) stop();
  156|     tokens += 1;
  157|     const token = tokens;
  158|     const { year, keys, text, edits } = req;
  159|     deps.setRun({ token, id: null, year, done: 0, total: req.total, text, labels: req.labels, steps: null });
  160|     const startedAt = now();
  161|     const started = await deps.api.startRun(year, { whatIfs: [...keys], text, edits });
  162|     const mine = deps.getRun();
  163|     if (!mine || mine.token !== token) return;
  164|     if (started.kind !== 'ok') {
  165|       // Indeterminate: the run may have started, but with no id there's
  166|       // nothing to poll; it isn't resubmitted.
  167|       deps.setRun(null);
  168|       deps.failed(started.message || 'The rerun didn’t start.');
  169|       return;
  170|     }
  171|     const id = started.value.id;
  172|     deps.setRun({ ...mine, id });
  173|     const current = () => deps.getRun()?.id === id;
  174|     const end = await pollRun(deps.api, id, {
  175|       sleep,
  176|       now,
  177|       startedAt,
  178|       current,
  179|       onProgress: (r) => {
  180|         const run = deps.getRun();
  181|         if (run) deps.setRun({ ...run, done: r.done, total: r.total, steps: r.steps ?? null });
  182|       },
  183|     });
  184|     switch (end.kind) {
  185|       case 'dropped':
  186|         return;
  187|       case 'gave-up':
  188|         stop();
  189|         deps.failed(end.message);
  190|         return;
  191|       case 'failed':
  192|         deps.setRun(null);
  193|         deps.failed(end.message);
  194|         return;
  195|       case 'done':
  196|         break;
  197|       default:
  198|         end satisfies never;
  199|     }
  200|     const result = end.result;
  201|     // A what-if the server just built from typed words: reload the year's
  202|     // what-ifs so its chip appears, already chosen.
  203|     const listed = (ws: readonly WhatIf[], k: string) => ws.some((w) => w.key === k);
  204|     let known = deps.whatIfsOf(year);
  205|     if (result.applied.some((a) => !listed(known, a.key))) {
  206|       await deps.reloadSim(year);
  207|       if (!current()) return;
  208|       known = deps.whatIfsOf(year);
  209|     }
  210|     const applied = result.applied.map((a) => a.key).filter((k) => listed(known, k));
  211|     deps.finished({ year, id, result, keys, text, applied });
  212|   }
  213| 
  214|   return { start, stop };
  215| }
```

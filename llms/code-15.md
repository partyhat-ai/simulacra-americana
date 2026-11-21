# synthetic-electorate-toy: source and docs, part 15 of 17

Generated from commit `6a200effe03e` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `src/lib/simulacra/runs.test.ts` to `src/lib/simulacra/state.test.ts`. Lines are numbered as in the repository.

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

## `src/lib/simulacra/sample.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { ELECTION_YEARS } from './geo';
    3| import { electionOf } from './history';
    4| import { _model, createSampleApi, UNOPPOSED } from './sample';
    5| import { RunResultSchema, RunStatusSchema, VoterSchema } from './schemas';
    6| 
    7| const fast = () => Promise.resolve();
    8| 
    9| describe('the sample model', () => {
   10|   test.each(ELECTION_YEARS)('an unchanged rerun of %i reproduces history', (y) => {
   11|     const e = electionOf(y);
   12|     const r = _model.rerun(y);
   13|     expect(e).not.toBeNull();
   14|     expect(r).not.toBeNull();
   15|     if (!e || !r) return;
   16|     expect(r.winner).toBe(e.winner);
   17|     expect(r.ev.A).toBe(e.candidates[0].ev);
   18|     expect(r.ev.B).toBe(e.candidates[1]?.ev ?? 0);
   19|     expect(r.states.filter((s) => s.flipped)).toEqual([]);
   20|     expect(new Map(r.states.map((s) => [s.code, s.won]))).toEqual(new Map(e.states.map((s) => [s.code, s.won])));
   21|     expect(r.confidence).toBeNull();
   22|     // The sample's results satisfy the server's contract.
   23|     expect(RunResultSchema.safeParse(r).success).toBe(true);
   24|   });
   25| 
   26|   test('1789, unopposed, has no runner-up and doesn’t crash', async () => {
   27|     expect(electionOf(1789)?.unopposed).toBe(true);
   28|     expect(_model.national(1789)).toEqual(UNOPPOSED);
   29|     expect(_model.whatIfsFor(1789)).toEqual([]);
   30|     expect(_model.slicesFor(1789).length).toBeGreaterThan(0);
   31|     expect(_model.rerun(1789, ['women'], 'what if women could vote')?.winner).toBe('A');
   32| 
   33|     let t = 0;
   34|     const api = createSampleApi({ sleep: fast, now: () => t });
   35|     const election = await api.election(1789);
   36|     expect(election.kind === 'ok' && election.value.whatIfs).toEqual([]);
   37|     const started = await api.startRun(1789);
   38|     expect(started.kind).toBe('ok');
   39|     if (started.kind !== 'ok') return;
   40|     t = 1e6;
   41|     const done = await api.run(started.value.id);
   42|     expect(done.kind === 'ok' && done.value.status).toBe('done');
   43|     const slice = _model.slicesFor(1789)[0]?.key ?? '';
   44|     expect((await api.voter(1789, slice, started.value.id)).kind).toBe('ok');
   45|   });
   46| 
   47|   test('every what-if of every year runs and stays inside the contract', () => {
   48|     for (const y of ELECTION_YEARS) {
   49|       for (const w of _model.whatIfsFor(y)) {
   50|         const r = _model.rerun(y, [w.key]);
   51|         expect(RunResultSchema.safeParse(r).success, `${y} ${w.key}`).toBe(true);
   52|         expect(r?.applied.map((a) => a.key)).toEqual([w.key]);
   53|       }
   54|     }
   55|   });
   56| 
   57|   test('typed words are read as a what-if, or handed back as unknown', () => {
   58|     expect(_model.rerun(1912, [], 'what if Taft dropped out')?.applied.map((a) => a.key)).toEqual(['taft-out']);
   59|     expect(_model.rerun(1912, [], 'what if it rained')?.unknown).toBe('what if it rained');
   60|   });
   61| 
   62|   test('a dragged group changes the summary', () => {
   63|     const r = _model.rerun(2000, [], '', { felony: { B: 0.2, barred: -0.2 } });
   64|     expect(r?.summary).toMatch(/Among people with felony records, Gore gains 10 in 50/);
   65|   });
   66| });
   67| 
   68| describe('createSampleApi', () => {
   69|   test('a run counts states over time, then is done; a stopped run fails', async () => {
   70|     let t = 0;
   71|     const api = createSampleApi({ sleep: fast, now: () => t });
   72|     const started = await api.startRun(2000, { whatIfs: ['nader-out'] });
   73|     if (started.kind !== 'ok') throw new Error('the sample run didn’t start');
   74|     const id = started.value.id;
   75|     t = 45 * 10;
   76|     const running = await api.run(id);
   77|     expect(running).toMatchObject({ kind: 'ok', value: { status: 'running', done: 10 } });
   78|     t = 1e6;
   79|     const done = await api.run(id);
   80|     expect(done.kind === 'ok' && RunStatusSchema.safeParse(done.value).success).toBe(true);
   81|     expect(done.kind === 'ok' && done.value.status === 'done' && done.value.result.applied[0]?.key).toBe('nader-out');
   82|     const voter = await api.voter(2000, 'felony', id);
   83|     expect(voter.kind === 'ok' && VoterSchema.safeParse(voter.value).success).toBe(true);
   84|     await api.stopRun(id);
   85|     expect(await api.run(id)).toEqual({ kind: 'ok', value: { status: 'failed', error: 'That run was stopped.' } });
   86|   });
   87| 
   88|   test('an unknown group or year is a missing error, not an empty answer', async () => {
   89|     const api = createSampleApi({ sleep: fast });
   90|     expect((await api.voter(1912, 'nobody')).kind).toBe('error');
   91|     expect((await api.startRun(1790)).kind).toBe('error');
   92|   });
   93| });
```

## `src/lib/simulacra/sample.ts`

```ts
    1| // Sample mode: the simulation server's answers (api.ts), made up, so the page
    2| // can be reviewed without that server. The page says "Sample" while this is
    3| // on. The elections are real (history.ts): who ran, who won, which party
    4| // carried each state. What a simulation would work out — how groups of voters
    5| // split, what a what-if changes, how close each state was — is invented here
    6| // by a small deterministic model: plausible, never authoritative. Ten
    7| // elections have written stories (stories.ts); every other year gets the
    8| // groups every election has (sampleEras.ts), above all the people who
    9| // couldn't vote.
   10| import type { Edits, Outcome, RunAsk, SimulacraApi } from './api';
   11| import { ELECTION_YEARS, STATE_BY_CODE } from './geo';
   12| import { type Election, electionOf } from './history';
   13| import {
   14|   adultsIn,
   15|   BORDER,
   16|   blackShare,
   17|   ENSLAVED,
   18|   ERA_PEOPLE,
   19|   REGIONS,
   20|   SOUTH,
   21|   SPREAD,
   22|   southFactor,
   23|   votesIn,
   24| } from './sampleData';
   25| import { eraSlices, eraWhatIfs } from './sampleEras';
   26| import type {
   27|   DropTo,
   28|   Fractions,
   29|   Lean,
   30|   Region,
   31|   SampleContext,
   32|   SliceSpec,
   33|   StateWeights,
   34|   VoterSpec,
   35|   Votes,
   36| } from './sampleTypes';
   37| import type { Choice, Kind, RunResult, Slice, StateResult, Voter } from './schemas';
   38| import { STORIES } from './stories';
   39| import { type Bucket, bucketOf } from './types';
   40| 
   41| const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));
   42| /** A stable number in [0, 1) for a string. */
   43| const unit = (s: string) => {
   44|   let h = 2166136261;
   45|   for (const ch of s) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0;
   46|   return (h % 10007) / 10007;
   47| };
   48| const FIELDS = ['barred', 'home', 'A', 'B', 'O'] as const;
   49| const IDX = { A: 0, B: 1, O: 2 } as const;
   50| const round3 = (x: number) => Math.round(x * 1000) / 1000;
   51| 
   52| /** Who leads: A on a tie with anyone, then B over O. */
   53| function leaderOf(v: Votes): Bucket {
   54|   if (v.A >= v.B && v.A >= v.O) return 'A';
   55|   return v.B >= v.O ? 'B' : 'O';
   56| }
   57| const topOf = (l: Lean): Bucket => leaderOf({ A: l[0], B: l[1], O: l[2] });
   58| 
   59| /** Where a group lives → state → weight, summing to 1 over the states voting in e. */
   60| function weights(e: Election, where: Region, states?: StateWeights): Map<string, number> {
   61|   const ev = new Map(e.states.map((s) => [s.code, s.ev]));
   62|   const out = new Map<string, number>();
   63|   const add = (code: string, w: number) => {
   64|     if (ev.has(code) && w > 0) out.set(code, (out.get(code) ?? 0) + w);
   65|   };
   66|   if (states) for (const [c, w] of Object.entries(states)) add(c, w);
   67|   else {
   68|     switch (where) {
   69|       case 'immigrant':
   70|       case 'latino':
   71|       case 'felony':
   72|         for (const [c, w] of Object.entries(SPREAD[where])) add(c, w * (ev.get(c) ?? 0));
   73|         for (const [c, v] of ev) add(c, v * 0.08);
   74|         break;
   75|       case 'black':
   76|       case 'black-south':
   77|       case 'black-north':
   78|         for (const [c, v] of ev) {
   79|           const south = SOUTH.includes(c) || BORDER.includes(c);
   80|           if ((where === 'black-south' && !south) || (where === 'black-north' && south)) continue;
   81|           add(c, v * blackShare(c, e.year));
   82|         }
   83|         break;
   84|       case 'north':
   85|         for (const [c, v] of ev) if (!SOUTH.includes(c)) add(c, v);
   86|         break;
   87|       case 'south':
   88|       case 'new-england':
   89|       case 'middle':
   90|       case 'midwest':
   91|       case 'plains':
   92|       case 'industrial':
   93|         for (const c of REGIONS[where]) add(c, ev.get(c) ?? 0);
   94|         break;
   95|       case 'all':
   96|         for (const [c, v] of ev) add(c, v);
   97|         break;
   98|       default: {
   99|         const never: never = where;
  100|         throw new Error(`Unknown region ${String(never)}`);
  101|       }
  102|     }
  103|   }
  104|   const total = [...out.values()].reduce((a, b) => a + b, 0) || 1;
  105|   for (const [c, w] of out) out.set(c, w / total);
  106|   return out;
  107| }
  108| 
  109| // ── The election as modelled ──
  110| /** An unopposed election (1789, 1792, 1820): everyone who voted, voted for A. */
  111| export const UNOPPOSED: Readonly<Votes> = { A: 1, B: 0, O: 0 };
  112| 
  113| /** The country's split: the popular vote when there is one, else one guessed from the electoral vote. */
  114| function national(e: Election): Votes {
  115|   const [a, b] = e.candidates;
  116|   if (!b) return { ...UNOPPOSED };
  117|   if (a.popular != null && b.popular != null) {
  118|     const A = a.popular / 100;
  119|     const B = b.popular / 100;
  120|     return { A, B, O: Math.max(0, 1 - A - B) };
  121|   }
  122|   const A = 0.5 + (0.25 * (a.ev - b.ev)) / Math.max(1, a.ev + b.ev);
  123|   return { A, B: 0.98 - A, O: 0.02 };
  124| }
  125| 
  126| /** A state as modelled before any change: shares, votes cast (V, millions), electors, who carried it. */
  127| interface Base extends Votes {
  128|   readonly V: number;
  129|   readonly ev: number;
  130|   readonly won: string;
  131|   readonly split: boolean;
  132| }
  133| 
  134| function split(won: Bucket, lead: number, nat: Votes, h: number): Votes {
  135|   if (won === 'O') {
  136|     const o = Math.min(0.8, 0.46 + 0.14 * h + lead / 2);
  137|     const ra = nat.A / Math.max(0.01, nat.A + nat.B);
  138|     return { A: (1 - o) * ra, B: (1 - o) * (1 - ra), O: o };
  139|   }
  140|   let o = Math.min(0.3, nat.O * (0.5 + h));
  141|   let w = (1 - o + lead) / 2;
  142|   if (w - o < 0.03) {
  143|     o = Math.max(0, (1 + lead) / 3 - 0.03);
  144|     w = (1 - o + lead) / 2;
  145|   }
  146|   const r = Math.max(0, 1 - o - w);
  147|   return won === 'A' ? { A: w, B: r, O: o } : { A: r, B: w, O: o };
  148| }
  149| 
  150| // Each state's vote share by candidate. The winner is history's; how close
  151| // it was is modelled — a state that stayed with the same party in the
  152| // elections around this one was safe, one that swung was close — except for
  153| // the states the written stories carry real shares for.
  154| function baseline(e: Election): Map<string, Base> {
  155|   const nat = national(e);
  156|   const fixed = STORIES[e.year]?.states ?? {};
  157|   const i = ELECTION_YEARS.indexOf(e.year);
  158|   const near = [-2, -1, 1, 2].flatMap((d) => {
  159|     const y = ELECTION_YEARS[i + d];
  160|     const n = y === undefined ? null : electionOf(y);
  161|     return n ? [n] : [];
  162|   });
  163|   const weight = (s: { code: string; ev: number }) => s.ev * southFactor(s.code, e.year);
  164|   const total = e.states.reduce((a, s) => a + weight(s), 0);
  165|   const votes = votesIn(e.year);
  166|   const out = new Map<string, Base>();
  167|   for (const s of e.states) {
  168|     const h = unit(`${e.year}:${s.code}`);
  169|     const real = fixed[s.code];
  170|     let sh: Votes;
  171|     if (real) sh = { A: real[0], B: real[1], O: Math.max(0, 1 - real[0] - real[1]) };
  172|     else {
  173|       const same = near.filter((n) => n.states.find((x) => x.code === s.code)?.party === s.party).length;
  174|       const stable = near.length ? same / near.length : 0.5;
  175|       const lead = ((2 + stable * stable * 24) * (0.7 + 0.6 * h) + Math.abs(nat.A - nat.B) * 35) / 100;
  176|       sh = split(bucketOf(s.won), lead, nat, h);
  177|     }
  178|     out.set(s.code, { ...sh, V: (votes * weight(s)) / total, ev: s.ev, won: s.won, split: s.party === 'SP' });
  179|   }
  180|   return out;
  181| }
  182| 
  183| // ── The groups ──
  184| /** A group as the model carries it through a run. */
  185| interface ModelSlice extends Fractions {
  186|   readonly key: string;
  187|   readonly label: string;
  188|   readonly where: Region;
  189|   readonly states: StateWeights | undefined;
  190|   readonly mirror: boolean;
  191|   readonly tilt: number;
  192|   /** Millions. */
  193|   readonly adults: number;
  194|   readonly turnout: number;
  195|   readonly leanIf: Lean;
  196|   readonly voter: VoterSpec | null;
  197| }
  198| 
  199| function compose(barred: number, turnout: number, lean: Lean): Fractions {
  200|   const voting = (1 - barred) * turnout;
  201|   return { barred, home: 1 - barred - voting, A: voting * lean[0], B: voting * lean[1], O: voting * lean[2] };
  202| }
  203| 
  204| function build(e: Election, nat: Votes, s: SliceSpec): ModelSlice {
  205|   const tilt = s.tilt ?? 0;
  206|   const voted = s.lean.some((x) => x > 0);
  207|   let leanIf: Lean;
  208|   if (s.mirror) {
  209|     // A group that votes like its own state (women) splits like the country.
  210|     const m = [nat.A + tilt / 2, nat.B - tilt / 2, nat.O].map((x) => Math.max(0, x));
  211|     const sum = m.reduce((a, b) => a + b, 0) || 1;
  212|     leanIf = [(m[0] ?? 0) / sum, (m[1] ?? 0) / sum, (m[2] ?? 0) / sum];
  213|   } else if (s.leanIf) leanIf = s.leanIf;
  214|   else leanIf = voted ? s.lean : [0.5, 0.5, 0];
  215|   const lean = voted ? s.lean : leanIf;
  216|   return {
  217|     key: s.key,
  218|     label: s.label,
  219|     where: s.where,
  220|     states: s.states,
  221|     mirror: !!s.mirror,
  222|     tilt,
  223|     adults: adultsIn(e.year) * s.share,
  224|     turnout: s.turnout,
  225|     leanIf,
  226|     voter: s.voter ?? null,
  227|     ...compose(s.barred, s.turnout, lean),
  228|   };
  229| }
  230| 
  231| const slicesFor = (e: Election): ModelSlice[] => {
  232|   const nat = national(e);
  233|   return (STORIES[e.year]?.slices ?? eraSlices(e, nat)).map((s) => build(e, nat, s));
  234| };
  235| 
  236| // ── What-ifs ──
  237| export interface ModelWhatIf {
  238|   readonly key: string;
  239|   readonly label: string;
  240|   readonly kind: Kind;
  241|   readonly detail: string;
  242|   readonly slices: readonly string[];
  243|   readonly apply: (c: SampleContext) => void;
  244| }
  245| 
  246| function whatIfsFor(e: Election): ModelWhatIf[] {
  247|   if (e.unopposed) return [];
  248|   return (STORIES[e.year]?.whatIfs ?? eraWhatIfs(e.year)).map(([key, label, kind, detail, slices, apply]) => ({
  249|     key,
  250|     label,
  251|     kind,
  252|     detail,
  253|     slices,
  254|     apply,
  255|   }));
  256| }
  257| 
  258| // Words in a typed what-if → the what-if it most likely means. Sample mode
  259| // only; the server reads free text for real.
  260| const WORDS: readonly (readonly [RegExp, readonly string[]])[] = [
  261|   [/wom[ae]n|suffrag|19th/i, ['women', 'no-19th']],
  262|   [/15th|jim crow|poll tax|literacy|disenfranch|voting rights|black (men|voters|southerners)/i, ['fifteenth']],
  263|   [/emancipat|slave|abolit|freed/i, ['emancipation']],
  264|   [/three.?fifths|3\/5/i, ['three-fifths']],
  265|   [/propert|landless|freehold/i, ['no-property']],
  266|   [/\b18\b|eighteen|young|youth|26th/i, ['age18']],
  267|   [/felon|prison|convict|incarcerat/i, ['felons']],
  268|   [/migrat/i, ['migration']],
  269|   [/everyone|every adult|universal|compulsory|all adults/i, ['everyone']],
  270|   [/panic|depression|crash|economy|recession/i, ['panic']],
  271|   [/nader/i, ['nader-out']], [/wallace/i, ['wallace-out']], [/thurmond|dixiecrat/i, ['thurmond-out']],
  272|   [/taft/i, ['taft-out']], [/debs|socialist/i, ['debs-out']], [/comey|email/i, ['comey']],
  273|   [/debate|televis|\btv\b/i, ['debate']], [/sedition|alien/i, ['sedition']],
  274|   [/unite|split|douglas|breckinridge/i, ['unite']], [/ballot|butterfly|palm beach/i, ['ballot']],
  275|   [/money|spend|hanna|campaign/i, ['money']], [/peace|vietnam|paris/i, ['peace']], [/turnout/i, ['turnout', 'everyone']],
  276| ];
  277| function understand(text: string, available: readonly ModelWhatIf[]): string | null {
  278|   for (const [re, keys] of WORDS) {
  279|     if (!re.test(text)) continue;
  280|     const k = keys.find((x) => available.some((w) => w.key === x));
  281|     if (k) return k;
  282|   }
  283|   return null;
  284| }
  285| 
  286| // ── A run ──
  287| /** One change to the country's votes, applied state by state once every what-if has run. */
  288| type Delta =
  289|   | { readonly type: 'votes'; readonly where: ReadonlyMap<string, number>; readonly A: number; readonly B: number; readonly O: number }
  290|   | { readonly type: 'mirror'; readonly f: number; readonly tilt: number }
  291|   | { readonly type: 'swing'; readonly pts: number; readonly to: 'A' | 'B'; readonly where: ReadonlyMap<string, number> | null }
  292|   | { readonly type: 'drop'; readonly frac: number; readonly to: DropTo; readonly where: ReadonlyMap<string, number> | null }
  293|   | { readonly type: 'shift'; readonly states: StateWeights; readonly to: 'A' | 'B' };
  294| 
  295| function fmtM(m: number): string {
  296|   if (m >= 0.95) return `${m.toFixed(1).replace(/\.0$/, '')} million`;
  297|   if (m >= 0.001) return `${Math.round(m * 1000).toLocaleString('en-US')},000`;
  298|   return 'a few hundred';
  299| }
  300| // "Women" → "women" mid-sentence; proper adjectives and numbers stay.
  301| const lower = (label: string) =>
  302|   /^(Black|White|Latino|Southern|Northern|Irish|Catholic|Plains|New|Progressive|Loyal|Socialist|Northerners|\d)/.test(label)
  303|     ? label
  304|     : label.charAt(0).toLowerCase() + label.slice(1);
  305| function howMany(share: number): string {
  306|   if (share > 0.8) return 'nearly all';
  307|   if (share > 0.6) return 'most';
  308|   return 'more of them';
  309| }
  310| 
  311| function makeContext(e: Election, base: ReadonlyMap<string, Base>) {
  312|   const slices = new Map(slicesFor(e).map((s) => [s.key, s]));
  313|   const deltas: Delta[] = [];
  314|   const leads: string[] = [];
  315|   const evs = new Map<string, number>();
  316|   const name = (k: Bucket) =>
  317|     k === 'O' ? (e.candidates[2]?.short ?? 'third parties') : (e.candidates.find((c) => c.key === k)?.short ?? '');
  318|   const votes = votesIn(e.year);
  319|   const set = (s: ModelSlice, next: Partial<Fractions>) => slices.set(s.key, { ...s, ...next });
  320|   const at = (s: ModelSlice) => weights(e, s.where, s.states);
  321|   /** The share of a group living inside region weights w. */
  322|   const inside = (s: ModelSlice, w: ReadonlyMap<string, number> | null) =>
  323|     w ? [...at(s)].reduce((a, [c, x]) => a + (w.has(c) ? x : 0), 0) : 1;
  324|   const ctx: SampleContext = {
  325|     year: e.year,
  326|     has: (key) => slices.has(key),
  327|     // Some of a group's barred members (or all) can vote, at the group's
  328|     // turnout (or `turnout`), splitting like `lean` — or, for a group that
  329|     // votes like its own state (women), like each state's voters.
  330|     enfranchise(key, { barred = 0, turnout, lean } = {}) {
  331|       const s = slices.get(key);
  332|       if (!s) return;
  333|       const t = turnout ?? s.turnout;
  334|       const l = lean ?? s.leanIf;
  335|       const add = s.barred - barred;
  336|       const had = s.A + s.B + s.O > 0.01;
  337|       let next: Fractions;
  338|       if (add >= 0) {
  339|         next = { barred, home: s.home + add * (1 - t), A: s.A + add * t * l[0], B: s.B + add * t * l[1], O: s.O + add * t * l[2] };
  340|       } else {
  341|         const k = 1 + add / Math.max(0.001, 1 - s.barred);
  342|         next = { barred, home: s.home * k, A: s.A * k, B: s.B * k, O: s.O * k };
  343|       }
  344|       const d = { A: (next.A - s.A) * s.adults, B: (next.B - s.B) * s.adults, O: (next.O - s.O) * s.adults };
  345|       const total = d.A + d.B + d.O;
  346|       if (s.mirror) deltas.push({ type: 'mirror', f: total / votes, tilt: s.tilt });
  347|       else deltas.push({ type: 'votes', where: at(s), ...d });
  348|       set(s, next);
  349|       const who = key === 'enslaved' ? 'freed men' : lower(s.label);
  350|       const more = had ? 'more ' : '';
  351|       if (total < 0) leads.push(`${fmtM(-total)} ${who} lose the vote.`);
  352|       else if (s.mirror) leads.push(`${fmtM(total)} ${more}${who} vote, splitting much like the men of their states.`);
  353|       else {
  354|         const m = topOf(l);
  355|         const share = l[IDX[m]] / (l[0] + l[1] + l[2] || 1);
  356|         leads.push(`${fmtM(total)} ${more}${who} vote, ${howMany(share)} for ${name(m)}.`);
  357|       }
  358|     },
  359|     swing(key, pts, to) {
  360|       const s = slices.get(key);
  361|       if (!s) return;
  362|       const from = to === 'A' ? 'B' : 'A';
  363|       const moved = Math.min(s[from], (pts / 100) * (s.A + s.B + s.O));
  364|       const next = { ...s };
  365|       next[to] += moved;
  366|       next[from] -= moved;
  367|       slices.set(key, next);
  368|       const d = { A: 0, B: 0, O: 0 };
  369|       d[to] = moved * s.adults;
  370|       d[from] = -moved * s.adults;
  371|       deltas.push({ type: 'votes', where: at(s), ...d });
  372|       leads.push(`${name(to)} gains ${pts} points with ${lower(s.label)}.`);
  373|     },
  374|     swingAll(pts, to, region, text) {
  375|       const w = region ? weights(e, region) : null;
  376|       deltas.push({ type: 'swing', pts, to, where: w });
  377|       const from = to === 'A' ? 'B' : 'A';
  378|       for (const s of [...slices.values()]) {
  379|         const moved = Math.min(s[from], (pts / 100) * inside(s, w) * (s.A + s.B + s.O));
  380|         if (moved <= 0) continue;
  381|         const next = { ...s };
  382|         next[to] += moved;
  383|         next[from] -= moved;
  384|         slices.set(s.key, next);
  385|       }
  386|       leads.push(text);
  387|     },
  388|     drop(frac, to, text, region) {
  389|       const w = region ? weights(e, region) : null;
  390|       deltas.push({ type: 'drop', frac, to, where: w });
  391|       const toA = to.A ?? 0;
  392|       const toB = to.B ?? 0;
  393|       for (const s of [...slices.values()]) {
  394|         const moved = s.O * frac * inside(s, w);
  395|         if (moved > 0) set(s, { O: s.O - moved, A: s.A + moved * toA, B: s.B + moved * toB, home: s.home + moved * (1 - toA - toB) });
  396|       }
  397|       leads.push(text);
  398|     },
  399|     unite(frac, text) {
  400|       ctx.drop(frac, { B: 1 }, text);
  401|     },
  402|     shift(states, to, text) {
  403|       deltas.push({ type: 'shift', states, to });
  404|       leads.push(text);
  405|     },
  406|     move(key, frac, toKey) {
  407|       const s = slices.get(key);
  408|       const t = slices.get(toKey);
  409|       if (!s || !t) return;
  410|       const mix = (k: (typeof FIELDS)[number]) => (1 - frac) * s[k] + frac * t[k];
  411|       const mixed: Fractions = { barred: mix('barred'), home: mix('home'), A: mix('A'), B: mix('B'), O: mix('O') };
  412|       deltas.push({ type: 'votes', where: at(s), A: (mixed.A - s.A) * s.adults, B: (mixed.B - s.B) * s.adults, O: (mixed.O - s.O) * s.adults });
  413|       deltas.push({ type: 'votes', where: at(t), A: frac * t.A * s.adults, B: frac * t.B * s.adults, O: frac * t.O * s.adults });
  414|       const lost = (s.A + s.B + s.O - (mixed.A + mixed.B + mixed.O)) * s.adults;
  415|       set(s, mixed);
  416|       leads.push(`${fmtM(lost)} fewer Black votes are cast in the North, and almost none are added in the South.`);
  417|     },
  418|     turnout(key, t) {
  419|       const s = slices.get(key);
  420|       if (!s) return;
  421|       const was = (s.A + s.B + s.O) / Math.max(0.001, 1 - s.barred);
  422|       const k = t / Math.max(0.001, was);
  423|       const A = s.A * k;
  424|       const B = s.B * k;
  425|       const O = s.O * k;
  426|       const home = Math.max(0, 1 - s.barred - A - B - O);
  427|       deltas.push({ type: 'votes', where: at(s), A: (A - s.A) * s.adults, B: (B - s.B) * s.adults, O: (O - s.O) * s.adults });
  428|       set(s, { A, B, O, home });
  429|       leads.push(`${s.label.replace(/ voters$/, '')} turnout rises from ${Math.round(was * 100)}% to ${Math.round(t * 100)}%.`);
  430|     },
  431|     everyone() {
  432|       const before = leads.length;
  433|       let added = 0;
  434|       for (const key of [...slices.keys()]) {
  435|         const was = slices.get(key);
  436|         if (!was) continue;
  437|         if (was.barred > 0) {
  438|           ctx.enfranchise(key, { barred: 0, turnout: 1 });
  439|           const n = slices.get(key) ?? was;
  440|           added += (n.A + n.B + n.O - (was.A + was.B + was.O)) * was.adults;
  441|         }
  442|         // Those who could vote and stayed home vote too; they're counted
  443|         // with everyone else below.
  444|         const n = slices.get(key) ?? was;
  445|         if (n.home > 0.0005) {
  446|           const k = n.home / (n.A + n.B + n.O || 1);
  447|           set(n, { home: 0, A: n.A * (1 + k), B: n.B * (1 + k), O: n.O * (1 + k) });
  448|         }
  449|       }
  450|       // Every other adult who didn't vote does now — a little more
  451|       // Democratic from the New Deal on.
  452|       const rest = Math.max(0, adultsIn(e.year) - votes - added);
  453|       let dem = 0;
  454|       if (e.candidates[0].family === 'democratic') dem = 1;
  455|       else if (e.candidates[1]?.family === 'democratic') dem = -1;
  456|       deltas.push({ type: 'mirror', f: rest / votes, tilt: e.year >= 1936 ? 0.03 * dem : 0 });
  457|       added += rest;
  458|       leads.length = before;
  459|       leads.push(`Every adult votes: about ${fmtM(added)} more ballots.`);
  460|     },
  461|     apportion() {
  462|       const table = e.year <= 1830 ? ENSLAVED.early : ENSLAVED.late;
  463|       let lost = 0;
  464|       for (const [code, s] of base) {
  465|         const share = table[code];
  466|         if (!share) continue;
  467|         const cut = Math.round((s.ev - 2) * ((0.6 * share) / (1 - 0.4 * share)));
  468|         if (cut > 0) {
  469|           evs.set(code, s.ev - cut);
  470|           lost += cut;
  471|         }
  472|       }
  473|       leads.push(`The slave states lose ${lost} electoral votes.`);
  474|     },
  475|     enfranchiseBlackSouth({ lean }) {
  476|       const adults = adultsIn(e.year) * 0.04 * 0.9 * 0.6;
  477|       deltas.push({ type: 'votes', where: weights(e, 'black-south'), A: adults * lean[0], B: adults * lean[1], O: adults * lean[2] });
  478|       leads.push(`${fmtM(adults)} Black Southerners vote, most for ${name(topOf(lean))}.`);
  479|     },
  480|   };
  481|   return { ctx, deltas, leads, evs, slices };
  482| }
  483| 
  484| /** Each state's votes after every change. */
  485| function tally(base: ReadonlyMap<string, Base>, deltas: readonly Delta[]): Map<string, Votes> {
  486|   const now = new Map<string, Votes>();
  487|   for (const [code, s] of base) now.set(code, { A: s.A * s.V, B: s.B * s.V, O: s.O * s.V });
  488|   for (const d of deltas) {
  489|     switch (d.type) {
  490|       case 'votes':
  491|         for (const [code, w] of d.where) {
  492|           const s = now.get(code);
  493|           if (!s) continue;
  494|           s.A += d.A * w;
  495|           s.B += d.B * w;
  496|           s.O += d.O * w;
  497|         }
  498|         break;
  499|       case 'mirror':
  500|         for (const [code, b] of base) {
  501|           const s = now.get(code);
  502|           if (!s) continue;
  503|           const add = d.f * b.V;
  504|           s.A += add * clamp(b.A + d.tilt / 2, 0, 1);
  505|           s.B += add * clamp(b.B - d.tilt / 2, 0, 1);
  506|           s.O += add * b.O;
  507|         }
  508|         break;
  509|       case 'swing': {
  510|         const from = d.to === 'A' ? 'B' : 'A';
  511|         for (const [code, s] of now) {
  512|           if (d.where && !d.where.has(code)) continue;
  513|           const moved = Math.min(s[from], (d.pts / 100) * (s.A + s.B + s.O));
  514|           s[from] -= moved;
  515|           s[d.to] += moved;
  516|         }
  517|         break;
  518|       }
  519|       case 'drop':
  520|         for (const [code, s] of now) {
  521|           if (d.where && !d.where.has(code)) continue;
  522|           const moved = s.O * d.frac;
  523|           s.O -= moved;
  524|           s.A += moved * (d.to.A ?? 0);
  525|           s.B += moved * (d.to.B ?? 0);
  526|         }
  527|         break;
  528|       case 'shift':
  529|         for (const [code, f] of Object.entries(d.states)) {
  530|           const s = now.get(code);
  531|           if (!s) continue;
  532|           const moved = Math.min(s.O, f * (s.A + s.B + s.O));
  533|           s.O -= moved;
  534|           s[d.to] += moved;
  535|         }
  536|         break;
  537|       default: {
  538|         const never: never = d;
  539|         throw new Error(`Unknown change ${JSON.stringify(never)}`);
  540|       }
  541|     }
  542|   }
  543|   return now;
  544| }
  545| 
  546| const RANK: Readonly<Record<Kind, number>> = { franchise: 0, population: 1, issue: 2, candidate: 2 };
  547| const CONFIDENCE = ['high', 'medium', 'low'] as const;
  548| const stateName = (code: string) => STATE_BY_CODE.get(code)?.name ?? code;
  549| const list = (names: readonly string[]) =>
  550|   names.length <= 2 ? names.join(' and ') : `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
  551| function pts(m: number): string {
  552|   if (m < 0.1) return 'less than a tenth of a point';
  553|   const p = m.toFixed(1);
  554|   return `${p} point${p === '1.0' ? '' : 's'}`;
  555| }
  556| /** The gap between the first and second of three shares. */
  557| const gap = (v: Votes) => {
  558|   const [x = 0, y = 0] = [v.A, v.B, v.O].sort((p, q) => q - p);
  559|   return x - y;
  560| };
  561| 
  562| function rerunElection(e: Election, keys: readonly string[] = [], text = '', edits: Edits = {}): RunResult {
  563|   const year = e.year;
  564|   const base = baseline(e);
  565|   const available = whatIfsFor(e);
  566|   const { ctx, deltas, leads, evs, slices } = makeContext(e, base);
  567|   const chosen = keys.flatMap((k) => available.filter((w) => w.key === k).slice(0, 1));
  568|   let unknown: string | null = null;
  569|   const typed = text.trim();
  570|   if (typed) {
  571|     const meant = understand(typed, available);
  572|     const w = available.find((x) => x.key === meant);
  573|     if (!w) unknown = typed;
  574|     else if (!chosen.includes(w)) chosen.push(w);
  575|   }
  576|   for (const w of chosen) w.apply(ctx);
  577|   const shortOf = (k: string) => e.candidates.find((c) => c.key === k)?.short ?? '';
  578|   // Groups changed by hand: the new make-up, its votes spread over the
  579|   // group's states.
  580|   let edited = 0;
  581|   for (const [key, d] of Object.entries(edits)) {
  582|     const s = slices.get(key);
  583|     if (!s) continue;
  584|     const moved = (k: (typeof FIELDS)[number]) => Math.max(0, s[k] + (d[k] ?? 0));
  585|     const next: Fractions = { barred: moved('barred'), home: moved('home'), A: moved('A'), B: moved('B'), O: moved('O') };
  586|     deltas.push({
  587|       type: 'votes',
  588|       where: weights(e, s.where, s.states),
  589|       A: (next.A - s.A) * s.adults,
  590|       B: (next.B - s.B) * s.adults,
  591|       O: (next.O - s.O) * s.adults,
  592|     });
  593|     slices.set(key, { ...s, ...next });
  594|     const moves = (['A', 'B'] as const).flatMap((k) => {
  595|       const n = Math.round((d[k] ?? 0) * 50);
  596|       return n ? [`${shortOf(k)} ${n > 0 ? 'gains' : 'loses'} ${Math.abs(n)} in 50`] : [];
  597|     });
  598|     if (moves.length) {
  599|       leads.push(`Among ${lower(s.label)}, ${moves.join(' and ')}.`);
  600|       edited++;
  601|     }
  602|   }
  603| 
  604|   const now = tally(base, deltas);
  605|   const ev: Votes = {
  606|     A: e.candidates[0].ev,
  607|     B: e.candidates[1]?.ev ?? 0,
  608|     O: e.candidates.slice(2).reduce((a, c) => a + c.ev, 0),
  609|   };
  610|   const states: (StateResult & { ev: number })[] = [];
  611|   for (const [code, b] of base) {
  612|     const s = now.get(code) ?? { A: 0, B: 0, O: 0 };
  613|     // A state history split between candidates stays split.
  614|     const flipped = !b.split && leaderOf(s) !== leaderOf(b);
  615|     let won = b.won;
  616|     if (flipped) {
  617|       const to = leaderOf(s);
  618|       const from = bucketOf(b.won);
  619|       const moved = Math.min(b.ev, ev[from]);
  620|       ev[from] -= moved;
  621|       ev[to] += moved;
  622|       won = to;
  623|     }
  624|     const cutTo = evs.get(code);
  625|     if (cutTo !== undefined) {
  626|       const cut = cutTo - b.ev;
  627|       if (b.split) {
  628|         ev.A += Math.ceil(cut / 2);
  629|         ev.B += Math.floor(cut / 2);
  630|       } else ev[bucketOf(won)] += cut;
  631|     }
  632|     states.push({ code, won, flipped, ev: cutTo ?? b.ev, margin: (gap(s) / (s.A + s.B + s.O || 1)) * 100 });
  633|   }
  634|   const total = ev.A + ev.B + ev.O;
  635|   const best = leaderOf(ev);
  636|   const changed = states.some((s) => s.flipped) || evs.size > 0;
  637|   let winner: Bucket | null = 'A';
  638|   if (changed) winner = ev[best] > total / 2 ? best : null;
  639| 
  640|   // The verdict: what changed, then what it did.
  641|   const nameOf = (k: Bucket) => (k === 'O' ? (e.candidates[2]?.short ?? 'third parties') : shortOf(k));
  642|   const flips = states.filter((s) => s.flipped).sort((a, b) => b.ev - a.ev);
  643|   const score = (k: Bucket) => `${ev[k]}–${ev[k === 'A' ? 'B' : 'A']}`;
  644|   // Flips that cost history's winner a state, and ones that gave it one.
  645|   const lost = flips.filter((f) => base.get(f.code)?.won === 'A');
  646|   const gained = flips.filter((f) => f.won === 'A');
  647|   const names = (arr: readonly StateResult[], n: number) =>
  648|     arr.length > n
  649|       ? `${arr
  650|           .slice(0, n)
  651|           .map((f) => stateName(f.code))
  652|           .join(', ')} and ${arr.length - n} more`
  653|       : list(arr.map((f) => stateName(f.code)));
  654|   const to = (arr: readonly StateResult[]) => {
  655|     const [only, ...more] = [...new Set(arr.map((f) => bucketOf(f.won)))];
  656|     return only && !more.length ? ` to ${nameOf(only)}` : '';
  657|   };
  658|   const flipOf = (arr: readonly StateResult[]) => `${names(arr, 3)} flip${arr.length === 1 ? 's' : ''}${to(arr)}`;
  659|   // The closest state the change pushed toward losing, and how close.
  660|   const was = new Map([...base].map(([code, b]) => [code, gap(b) * 100] as const));
  661|   const squeezed = (k: Bucket) =>
  662|     states
  663|       .filter((f) => !f.flipped && f.won === k && f.margin < (was.get(f.code) ?? 0) - 0.05)
  664|       .sort((a, b) => a.margin - b.margin)[0];
  665|   const heldA = squeezed('A');
  666|   const holds = heldA ? `${stateName(heldA.code)} holds for ${nameOf('A')} by ${pts(heldA.margin)}.` : '';
  667|   let outcome: string;
  668|   if (!chosen.length && !edited) {
  669|     outcome = unknown ? '' : `Rerun with nothing changed, ${year} comes out as it did: ${nameOf('A')} wins, ${score('A')}.`;
  670|   } else if (winner && winner !== 'A') {
  671|     outcome = `That’s enough: ${nameOf(winner)} wins, ${score(winner)}${lost.length ? `, flipping ${names(lost, 4)}` : ''}.`;
  672|   } else if (!winner) {
  673|     outcome = `${lost.length ? `${flipOf(lost)}, and` : 'Now'} no one has a majority of electoral votes: the House would decide.`;
  674|   } else if (lost.length) {
  675|     outcome = `${flipOf(lost)}, but it isn’t enough: ${nameOf('A')} still wins, ${score('A')}. ${holds}`;
  676|   } else if (gained.length) {
  677|     outcome = `${nameOf('A')} wins bigger, ${score('A')}, taking ${names(gained, 4)}.`;
  678|   } else if (evs.size) {
  679|     outcome = `${nameOf('A')} still wins, ${score('A')}.`;
  680|   } else if (heldA) {
  681|     outcome = `It isn’t enough to flip a state. ${holds}`;
  682|   } else {
  683|     const heldB = e.candidates[1] ? squeezed('B') : undefined;
  684|     outcome = heldB
  685|       ? `No state changes hands; ${stateName(heldB.code)} stays with ${nameOf('B')} by ${pts(heldB.margin)}.`
  686|       : 'No state changes hands.';
  687|   }
  688|   const kinds = chosen.map((w) => RANK[w.kind]);
  689|   return {
  690|     ev,
  691|     winner,
  692|     states: states.map(({ code, won, flipped, margin }) => ({ code, won, flipped, margin: Math.round(margin * 10) / 10 })),
  693|     slices: [...slices.values()].map(display),
  694|     summary: [...leads, outcome].filter(Boolean).join(' '),
  695|     confidence: kinds.length ? (CONFIDENCE[Math.max(...kinds)] ?? 'low') : null,
  696|     applied: chosen.map(({ key, label, kind }) => ({ key, label, kind })),
  697|     unknown,
  698|   };
  699| }
  700| 
  701| const display = (s: ModelSlice): Slice => ({
  702|   key: s.key,
  703|   label: s.label,
  704|   adults: Math.round(s.adults * 100) / 100,
  705|   barred: round3(s.barred),
  706|   home: round3(Math.max(0, s.home)),
  707|   A: round3(s.A),
  708|   B: round3(s.B),
  709|   O: round3(s.O),
  710| });
  711| 
  712| // ── The people ──
  713| /** What most of a group did. */
  714| function most(c: Fractions): Choice {
  715|   if (c.barred >= 0.5) return 'barred';
  716|   if (c.home > c.A + c.B + c.O) return 'home';
  717|   return leaderOf(c);
  718| }
  719| 
  720| function voterOf(e: Election, key: string, result: RunResult | null): Voter | null {
  721|   const s = slicesFor(e).find((x) => x.key === key);
  722|   if (!s) return null;
  723|   const after = result?.slices.find((x) => x.key === key);
  724|   const changed = !!after && FIELDS.some((k) => Math.abs(after[k] - round3(s[k])) > 0.002);
  725|   if (s.voter) {
  726|     const [name, line, history, then, quote] = s.voter;
  727|     return { name, line, quote, history, now: changed ? then : history };
  728|   }
  729|   const pool = ERA_PEOPLE[key] ?? [];
  730|   const [name, line, quote] = pool[Math.floor(unit(`${e.year}:${key}`) * pool.length)] ?? ['A voter', '', ''];
  731|   const history = most(s);
  732|   const then = after ? most(after) : history;
  733|   return { name, line, quote, history, now: changed ? then : history };
  734| }
  735| 
  736| // ── The API (api.ts's shape) ──
  737| export interface SampleOptions {
  738|   /** Waits a while, as a server would; tests pass one that doesn't. */
  739|   readonly sleep?: (ms: number) => Promise<void>;
  740|   /** The clock a run's progress is measured on. */
  741|   readonly now?: () => number;
  742| }
  743| 
  744| const ok = <T>(value: T): Outcome<T> => ({ kind: 'ok', value });
  745| const missing = (message: string): Outcome<never> => ({ kind: 'error', reason: 'missing', message, status: 404 });
  746| /** A sample run counts one state every RUN_MS, so it takes a moment, like a server's. */
  747| const RUN_MS = 45;
  748| 
  749| export function createSampleApi(options: SampleOptions = {}): SimulacraApi {
  750|   const sleep = options.sleep ?? ((ms: number) => new Promise<void>((r) => setTimeout(r, ms)));
  751|   const clock = options.now ?? Date.now;
  752|   const runs = new Map<string, { at: number; total: number; result: RunResult }>();
  753|   let n = 0;
  754|   return {
  755|     sample: true,
  756|     async election(year) {
  757|       await sleep(220);
  758|       const e = electionOf(year);
  759|       if (!e) return ok({ slices: [], whatIfs: [], simulated: false });
  760|       return ok({
  761|         slices: slicesFor(e).map(display),
  762|         whatIfs: whatIfsFor(e).map(({ key, label, kind, detail, slices }) => ({ key, label, kind, detail, slices: [...slices] })),
  763|         simulated: true,
  764|       });
  765|     },
  766|     async startRun(year, { whatIfs = [], text = '', edits = {} }: RunAsk = {}) {
  767|       await sleep(120);
  768|       const e = electionOf(year);
  769|       if (!e) return missing('No simulation for this year.');
  770|       n += 1;
  771|       const id = `sample-${n}`;
  772|       runs.set(id, { at: clock(), total: e.states.length, result: rerunElection(e, whatIfs, text, edits) });
  773|       return ok({ id });
  774|     },
  775|     async run(id) {
  776|       await sleep(40);
  777|       const r = runs.get(id);
  778|       if (!r) return ok({ status: 'failed', error: 'That run was stopped.' });
  779|       const done = Math.min(r.total, Math.floor((clock() - r.at) / RUN_MS));
  780|       if (done < r.total) return ok({ status: 'running', done, total: r.total });
  781|       return ok({ status: 'done', done: r.total, total: r.total, result: r.result });
  782|     },
  783|     async stopRun(id) {
  784|       runs.delete(id);
  785|       return ok(null);
  786|     },
  787|     async voter(year, sliceKey, runId) {
  788|       await sleep(140);
  789|       const e = electionOf(year);
  790|       const result = runId ? (runs.get(runId)?.result ?? null) : null;
  791|       const v = e ? voterOf(e, sliceKey, result) : null;
  792|       return v ? ok(v) : missing('No one from that group.');
  793|     },
  794|   };
  795| }
  796| 
  797| /** The model, for checking it outside the page (scripts/model-check.ts, the tests). */
  798| export const _model = {
  799|   national: (year: number): Votes | null => {
  800|     const e = electionOf(year);
  801|     return e ? national(e) : null;
  802|   },
  803|   rerun: (year: number, keys: readonly string[] = [], text = '', edits: Edits = {}): RunResult | null => {
  804|     const e = electionOf(year);
  805|     return e ? rerunElection(e, keys, text, edits) : null;
  806|   },
  807|   slicesFor: (year: number): Slice[] => {
  808|     const e = electionOf(year);
  809|     return e ? slicesFor(e).map(display) : [];
  810|   },
  811|   whatIfsFor: (year: number): ModelWhatIf[] => {
  812|     const e = electionOf(year);
  813|     return e ? whatIfsFor(e) : [];
  814|   },
  815| };
```

## `src/lib/simulacra/sampleData.ts`

```ts
    1| // The sample model's numbers (sample.ts): the country, roughly, by year;
    2| // where groups live; and the people it quotes for years with no written
    3| // story. Rough on purpose: the sample is labelled, and only shows how a
    4| // rerun works.
    5| import type { Region } from './sampleTypes';
    6| 
    7| /** [[x, y], …], x ascending, for lerp(). */
    8| export type Table = readonly (readonly [number, number])[];
    9| 
   10| /** Piecewise-linear lookup in a table, flat past either end. */
   11| export function lerp(table: Table, x: number): number {
   12|   let prev: readonly [number, number] | undefined;
   13|   for (const pt of table) {
   14|     if (x <= pt[0]) {
   15|       if (!prev) return pt[1];
   16|       return prev[1] + ((pt[1] - prev[1]) * (x - prev[0])) / (pt[0] - prev[0]);
   17|     }
   18|     prev = pt;
   19|   }
   20|   return prev ? prev[1] : 0;
   21| }
   22| 
   23| // ── The country, roughly ──
   24| // Population, millions.
   25| const POPULATION: Table = [[1790, 3.9], [1800, 5.3], [1810, 7.2], [1820, 9.6], [1830, 12.9], [1840, 17.1], [1850, 23.2], [1860, 31.4], [1870, 38.6], [1880, 50.2], [1890, 63], [1900, 76.2], [1910, 92.2], [1920, 106], [1930, 123.2], [1940, 132.2], [1950, 151.3], [1960, 179.3], [1970, 203.2], [1980, 226.5], [1990, 248.7], [2000, 281.4], [2010, 308.7], [2020, 331.4], [2024, 340]];
   26| // Adults' share of it: 21 and over until the 26th Amendment, then 18.
   27| const ADULT: Table = [[1790, 0.43], [1850, 0.47], [1880, 0.5], [1900, 0.53], [1920, 0.58], [1940, 0.64], [1950, 0.64], [1960, 0.61], [1968, 0.61], [1972, 0.7], [1980, 0.72], [1990, 0.74], [2010, 0.76], [2024, 0.78]];
   28| /** Adults in year y, millions. */
   29| export const adultsIn = (y: number): number => lerp(POPULATION, y) * lerp(ADULT, y);
   30| // Popular votes cast, millions.
   31| const VOTES: Readonly<Record<number, number>> = { 1789: 0.044, 1792: 0.028, 1796: 0.066, 1800: 0.068, 1804: 0.143, 1808: 0.193, 1812: 0.278, 1816: 0.113, 1820: 0.109, 1824: 0.366, 1828: 1.148, 1832: 1.293, 1836: 1.503, 1840: 2.412, 1844: 2.703, 1848: 2.879, 1852: 3.162, 1856: 4.054, 1860: 4.686, 1864: 4.031, 1868: 5.723, 1872: 6.467, 1876: 8.413, 1880: 9.217, 1884: 10.058, 1888: 11.383, 1892: 12.057, 1896: 13.936, 1900: 13.97, 1904: 13.518, 1908: 14.884, 1912: 15.044, 1916: 18.536, 1920: 26.768, 1924: 29.095, 1928: 36.805, 1932: 39.758, 1936: 45.655, 1940: 49.9, 1944: 47.977, 1948: 48.794, 1952: 61.552, 1956: 62.027, 1960: 68.838, 1964: 70.645, 1968: 73.212, 1972: 77.744, 1976: 81.556, 1980: 86.515, 1984: 92.653, 1988: 91.595, 1992: 104.425, 1996: 96.278, 2000: 105.426, 2004: 122.295, 2008: 131.473, 2012: 129.085, 2016: 136.669, 2020: 158.429, 2024: 155.238 };
   32| // Before 1828 most states chose electors through their legislatures, so the
   33| // popular vote above understates who took part: the model uses the men who
   34| // voted for those legislatures.
   35| const EARLY: Readonly<Record<number, number>> = { 1789: 0.25, 1792: 0.3, 1796: 0.35, 1800: 0.45, 1804: 0.5, 1808: 0.6, 1812: 0.7, 1816: 0.75, 1820: 0.8, 1824: 0.85 };
   36| /** Votes cast in year y, millions. */
   37| export const votesIn = (y: number): number => Math.max(VOTES[y] ?? 0, EARLY[y] ?? 0);
   38| // Turnout of those who could vote.
   39| export const TURNOUT: Table = [[1789, 0.2], [1824, 0.27], [1828, 0.57], [1840, 0.8], [1860, 0.81], [1876, 0.82], [1896, 0.79], [1900, 0.73], [1912, 0.59], [1920, 0.49], [1936, 0.61], [1960, 0.63], [1972, 0.55], [1996, 0.49], [2008, 0.58], [2020, 0.66], [2024, 0.64]];
   40| 
   41| // ── Where groups live ──
   42| export const SOUTH: readonly string[] = ['VA', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'LA', 'TX', 'AR', 'TN'];
   43| export const BORDER: readonly string[] = ['KY', 'MD', 'DE', 'MO', 'WV', 'OK'];
   44| type Listed = Extract<Region, 'south' | 'new-england' | 'middle' | 'midwest' | 'plains' | 'industrial'>;
   45| export const REGIONS: Readonly<Record<Listed, readonly string[]>> = {
   46|   south: SOUTH,
   47|   'new-england': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT'],
   48|   middle: ['NY', 'NJ', 'PA', 'DE', 'MD'],
   49|   midwest: ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'KS', 'NE', 'ND', 'SD'],
   50|   plains: ['KS', 'NE', 'ND', 'SD', 'MN', 'IA', 'CO', 'MT', 'ID', 'WA', 'OK', 'WY', 'NV', 'UT'],
   51|   industrial: ['NY', 'PA', 'NJ', 'MA', 'OH', 'IL', 'MI', 'CT', 'RI', 'IN', 'WI'],
   52| };
   53| type Spread = Extract<Region, 'immigrant' | 'latino' | 'felony'>;
   54| export const SPREAD: Readonly<Record<Spread, Readonly<Record<string, number>>>> = {
   55|   immigrant: { NY: 3, PA: 2, MA: 2, IL: 2, OH: 1.5, WI: 1.5, MO: 1, NJ: 1, MI: 1, MN: 1, CA: 1, LA: 0.5 },
   56|   latino: { CA: 5, TX: 4, FL: 2, AZ: 2, NM: 2, NY: 1.5, NV: 1, CO: 1, IL: 1, NJ: 1 },
   57|   felony: { FL: 6, TX: 2, VA: 1.5, TN: 1.2, AL: 1, KY: 1, GA: 1.2, MS: 0.8, AZ: 0.8, WA: 0.4 },
   58| };
   59| // Black share of each state's population (census), 1900, 1960 and 2000.
   60| const BLACK = {
   61|   1900: { MS: 0.58, SC: 0.58, LA: 0.47, GA: 0.47, AL: 0.45, FL: 0.44, VA: 0.36, NC: 0.33, AR: 0.28, TN: 0.24, TX: 0.2, MD: 0.2, DE: 0.17, KY: 0.13, DC: 0.31, MO: 0.05, WV: 0.05, OK: 0.07, KS: 0.035, OH: 0.023, PA: 0.025, NY: 0.014, NJ: 0.037, IL: 0.018, IN: 0.023 },
   62|   1960: { MS: 0.42, SC: 0.35, LA: 0.32, GA: 0.28, AL: 0.3, FL: 0.18, VA: 0.21, NC: 0.25, AR: 0.22, TN: 0.16, TX: 0.12, MD: 0.17, DE: 0.14, KY: 0.07, DC: 0.54, MO: 0.09, WV: 0.05, OK: 0.07, KS: 0.04, OH: 0.08, PA: 0.075, NY: 0.084, NJ: 0.085, IL: 0.1, IN: 0.06, MI: 0.09, CA: 0.056, CT: 0.042, MA: 0.022, WI: 0.019 },
   63|   2000: { MS: 0.36, SC: 0.29, LA: 0.32, GA: 0.29, AL: 0.26, FL: 0.15, VA: 0.2, NC: 0.22, AR: 0.16, TN: 0.16, TX: 0.12, MD: 0.28, DE: 0.19, KY: 0.07, DC: 0.6, MO: 0.11, OK: 0.08, OH: 0.12, PA: 0.1, NY: 0.16, NJ: 0.14, IL: 0.15, IN: 0.08, MI: 0.14, CA: 0.07, CT: 0.09, MA: 0.05, WI: 0.06, NV: 0.07, CO: 0.04, MN: 0.035 },
   64| } as const satisfies Record<number, Readonly<Record<string, number>>>;
   65| export function blackShare(code: string, y: number): number {
   66|   const at = (t: keyof typeof BLACK): number => {
   67|     const table: Readonly<Record<string, number>> = BLACK[t];
   68|     return table[code] ?? 0.01;
   69|   };
   70|   if (y <= 1900) return at(1900);
   71|   if (y <= 1960) return at(1900) + ((at(1960) - at(1900)) * (y - 1900)) / 60;
   72|   return at(1960) + (at(2000) - at(1960)) * Math.min(1, (y - 1960) / 40);
   73| }
   74| // Share of each slave state's people held in slavery (1800 and 1860
   75| // censuses), for the three-fifths what-if.
   76| export const ENSLAVED: Readonly<Record<'early' | 'late', Readonly<Record<string, number>>>> = {
   77|   early: { VA: 0.39, SC: 0.42, GA: 0.37, NC: 0.28, MD: 0.31, KY: 0.18, TN: 0.13, DE: 0.06, LA: 0.45, MS: 0.42, AL: 0.33, MO: 0.15 },
   78|   late: { VA: 0.31, SC: 0.57, GA: 0.44, NC: 0.33, MD: 0.13, KY: 0.2, TN: 0.25, DE: 0.02, LA: 0.47, MS: 0.55, AL: 0.45, MO: 0.1, FL: 0.44, AR: 0.26, TX: 0.3 },
   79| };
   80| // Southern votes per electoral vote, against the North's: from the 1880s to
   81| // the 1960s the South cast far fewer, most of its Black citizens and many
   82| // poor whites kept from the polls — the Deep South fewest of all.
   83| const DEEP_SOUTH: readonly string[] = ['SC', 'MS', 'LA', 'GA', 'AL', 'FL'];
   84| export function southFactor(code: string, y: number): number {
   85|   // Before emancipation a slave state's electors counted three-fifths of its
   86|   // enslaved people, so it had fewer voters per elector.
   87|   if (y <= 1864) {
   88|     const share = (y <= 1830 ? ENSLAVED.early : ENSLAVED.late)[code] ?? 0;
   89|     return (1 - share) / (1 - 0.4 * share);
   90|   }
   91|   if (!SOUTH.includes(code) || y < 1880 || y > 1964) return 1;
   92|   const deep = DEEP_SOUTH.includes(code);
   93|   if (y < 1890) return deep ? 0.6 : 0.8;
   94|   if (y <= 1900) return deep ? 0.3 : 0.6;
   95|   return deep ? 0.2 : 0.4;
   96| }
   97| 
   98| // ── The people ──
   99| // Era groups' people, for years with no written story: [name, who, quote].
  100| export type EraPerson = readonly [name: string, line: string, quote: string];
  101| export const ERA_PEOPLE: Readonly<Record<string, readonly EraPerson[]>> = {
  102|   'property-men': [['Nathaniel Brooks', '45, farmer with ninety acres, Hampshire County, Massachusetts', 'I own my land free and clear. That gives me a stake in the country, and a vote to show for it.']],
  103|   'no-property': [['Patrick Doyle', '27, dockworker, New York City', 'New York lets a man vote for the Assembly only if he pays enough rent. I pay less, so I have no say in who picks our electors.'],
  104|     ['Samuel Tuttle', '31, journeyman cooper, Baltimore, Maryland', 'I pay my taxes in sweat. The law says a man needs fifty acres before his opinion counts.']],
  105|   enslaved: [['Hannah', '30, enslaved cook, Albemarle County, Virginia', 'The Constitution counts me as three-fifths of a person, so Virginia gets more electors for owning me. I get no say at all.'],
  106|     ['Cato', '40, enslaved blacksmith, Charleston, South Carolina', 'I am hired out, and my master keeps the wages. The men who make the laws own the men who live under them.']],
  107|   women: [['Abigail Foster', '36, farm wife, Litchfield County, Connecticut', 'My husband votes the way his father did. I read the newspapers aloud to him in the evening.'],
  108|     ['Harriet Lowell', '24, mill worker, Lowell, Massachusetts', 'I work thirteen hours a day at the looms and pay my board from my own wages. The men who set our hours are elected by men.'],
  109|     ['Nora Brennan', '41, laundress, Chicago, Illinois', 'The saloon on our corner takes half of what my husband earns. If I could vote, it would be gone by spring.'],
  110|     ['Ida Lindgren', '32, stenographer, Minneapolis, Minnesota', 'The boy who delivers my newspaper turns twenty-one this year and gets the vote before I do.']],
  111|   'north-men': [['Caleb Morse', '47, farmer, Oneida County, New York', 'My father voted, and his father fought the British for the right to. I haven’t missed an election.'],
  112|     ['Henry Voss', '39, carpenter, Cincinnati, Ohio', 'I vote for the party that fought for the Union. Most of the men in my ward do.']],
  113|   'south-men': [['William Hardee', '44, farmer, Wilkes County, Georgia', 'My people have voted Democratic since Jackson. I don’t see a reason to stop.']],
  114|   'south-white': [['Robert Dunn', '47, cotton farmer, Hill County, Texas', 'Cotton is cheap and the railroads take half of it. Down here the Democrats are the only party that counts.'],
  115|     ['Earl Cobb', '46, mill hand, Spartanburg, South Carolina', 'I paid my poll tax this year. Most of the men at the mill didn’t, and can’t vote.']],
  116|   freedmen: [['Jacob Wells', '30, sharecropper, Hinds County, Mississippi', 'I voted for Grant the first time anyone ever asked me anything. The Klan came to the schoolhouse the next week.']],
  117|   'black-south': [['Henry Toussaint', '48, dockworker, New Orleans, Louisiana', 'They moved the polling place three times this year and never told us where.'],
  118|     ['Albert Mayes', '50, farmer, Lowndes County, Alabama', 'The poll tax adds up for every year you missed, back to twenty-one. I would owe a month’s wages to vote once.'],
  119|     ['Ruth Jenkins', '34, schoolteacher, Sunflower County, Mississippi', 'The registrar asked me how many bubbles are in a bar of soap. I teach algebra. I did not get registered.']],
  120|   'black-north': [['Leon Carter', '29, packinghouse worker, Chicago, Illinois', 'My folks came up from Mississippi so we could vote. In Chicago nobody asks me to count the bubbles in a bar of soap.']],
  121|   immigrants: [['Michael Brennan', '31, canal laborer, Buffalo, New York', 'The ward boss found me work the week I landed. He’ll want my vote the day I’m naturalized.'],
  122|     ['Giuseppe Russo', '28, bricklayer, Providence, Rhode Island', 'Four years here. One more and I can be naturalized. Until then the ward boss talks to me like I already vote.']],
  123|   north: [['Helen Kowalski', '38, telephone operator, Cleveland, Ohio', 'My mother never got to vote. I haven’t missed an election since I could.']],
  124|   youth: [['Frank Doyle', '19, sailor, Norfolk, Virginia', 'I’ve been in the Navy a year. Old enough to fight, not old enough to vote.']],
  125|   white: [['Karen Mills', '51, insurance agent, Columbus, Ohio', 'I split my ticket most years. This time I went with whoever I trust on the economy.']],
  126|   black: [['James Whitfield', '58, bus driver, Atlanta, Georgia', 'My father couldn’t vote in this state. I have never missed an election, and neither has anyone in my house.']],
  127|   latino: [['Ana Morales', '34, dental hygienist, San Antonio, Texas', 'My parents became citizens when I was ten. They took me to the polls with them every time.']],
  128|   young: [['Kevin Tran', '22, line cook, San Jose, California', 'I registered at the DMV and forgot about it. My roommate dragged me to the polls.']],
  129|   felony: [['Marcus Webb', '41, roofer, Tallahassee, Florida', 'I served my time years ago. I pay taxes and coach Little League, and I still can’t vote.']],
  130| };
```

## `src/lib/simulacra/sampleEras.ts`

```ts
    1| // The groups and what-ifs every election has in the sample, by era, for the
    2| // years with no written story (stories.ts) — above all, who couldn't vote.
    3| import type { Election } from './history';
    4| import type { Family } from './palette';
    5| import { lerp, TURNOUT } from './sampleData';
    6| import type { Lean, Region, SliceSpec, Votes, WhatIfSpec } from './sampleTypes';
    7| 
    8| const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));
    9| 
   10| /** The first value whose test holds, else `otherwise`. */
   11| const firstOf = (cases: readonly (readonly [boolean, number])[], otherwise: number): number =>
   12|   cases.find(([holds]) => holds)?.[1] ?? otherwise;
   13| 
   14| /** The era's groups for election `e`, whose national split is `nat`. */
   15| export function eraSlices(e: Election, nat: Votes): SliceSpec[] {
   16|   const y = e.year;
   17|   const fam = (k: string) => e.candidates.find((c) => c.key === k)?.family;
   18|   // How a group leaning `pts` points toward `family` splits [A, B, O].
   19|   const lean = (family: Family | null, pts = 0, o = nat.O): Lean => {
   20|     let two = nat.A / Math.max(0.01, nat.A + nat.B);
   21|     if (family && fam('A') === family) two += pts / 100;
   22|     else if (family && fam('B') === family) two -= pts / 100;
   23|     two = clamp(two, 0.03, 0.97);
   24|     return [two * (1 - o), (1 - two) * (1 - o), o];
   25|   };
   26|   const T = lerp(TURNOUT, y);
   27|   const s: SliceSpec[] = [];
   28|   const add = (
   29|     key: string,
   30|     label: string,
   31|     share: number,
   32|     barred: number,
   33|     turnout: number,
   34|     l: Lean,
   35|     where: Region,
   36|     extra: { mirror?: boolean; tilt?: number } = {},
   37|   ) => s.push({ key, label, share, barred, turnout, lean: barred >= 1 ? [0, 0, 0] : l, leanIf: l, where, ...extra });
   38|   if (y <= 1824) {
   39|     add('property-men', 'Men who own property', 0.28, 0, T, lean(null), 'all');
   40|     add('no-property', 'Men without property', 0.14, lerp([[1789, 0.6], [1800, 0.5], [1812, 0.4], [1824, 0.25]], y), T, lean('democratic-republican', 12), 'all');
   41|     // Freed, they'd have voted against the planters' party (in 1824, against Jackson).
   42|     add('enslaved', 'Enslaved people', 0.16, 1, 0.6, y === 1824 ? [0.75, 0.05, 0.2] : lean('federalist', 10, 0), 'black');
   43|     add('women', 'Women', 0.47, y >= 1792 && y <= 1804 ? 0.995 : 1, 0.4, lean(null), 'all', { mirror: true });
   44|   } else if (y <= 1860) {
   45|     add('north-men', 'Northern white men', 0.27, 0.04, T, y >= 1856 ? lean('republican', 12) : lean('whig', 3), 'north');
   46|     add('south-men', 'White Southern men', 0.12, 0.03, T * 0.95, lean('democratic', y >= 1856 ? 30 : 6), 'south');
   47|     if (y >= 1844) add('immigrants', 'Irish and German immigrants', 0.05, 0.45, 0.75, lean('democratic', 20), 'immigrant');
   48|     add('enslaved', 'Enslaved people', 0.14, 1, 0.7, y >= 1856 ? lean('republican', 40, 0) : lean('whig', 15, 0), 'black');
   49|     add('women', 'Women', 0.48, 1, 0.5, lean(null), 'all', { mirror: true });
   50|   } else if (y <= 1876) {
   51|     add('north-men', 'Northern white men', 0.29, 0.04, T, lean('republican', 6), 'north');
   52|     if (y === 1864) add('enslaved', 'Black Americans', 0.1, 1, 0.8, lean('republican', 40, 0), 'black');
   53|     else {
   54|       add('south-men', 'White Southern men', 0.1, 0.02, T * 0.95, lean('democratic', 35), 'south');
   55|       add('freedmen', 'Black men in the South', 0.045, lerp([[1868, 0.2], [1872, 0.25], [1876, 0.45]], y), 0.85, lean('republican', 40, 0), 'black-south');
   56|     }
   57|     add('immigrants', 'Immigrants', 0.05, 0.45, 0.75, lean('democratic', 20), 'immigrant');
   58|     add('women', 'Women', 0.48, 1, 0.5, lean(null), 'all', { mirror: true });
   59|   } else if (y <= 1916) {
   60|     add('north-men', 'Northern men', 0.3, 0.06, T, lean('republican', 4), 'north');
   61|     add('south-white', 'White Southern men', 0.1, y >= 1900 ? 0.2 : 0.05, y >= 1900 ? 0.45 : 0.6, lean('democratic', 38), 'south');
   62|     add('black-south', 'Black men in the South', 0.04, lerp([[1880, 0.35], [1892, 0.5], [1896, 0.6], [1900, 0.75], [1904, 0.88], [1916, 0.94]], y), 0.6,
   63|       lean('republican', 40, 0), 'black-south');
   64|     add('women', 'Women', 0.48, lerp([[1888, 1], [1892, 0.999], [1896, 0.985], [1908, 0.985], [1912, 0.92], [1916, 0.88]], y), 0.5, lean(null), 'all', { mirror: true });
   65|     add('immigrants', 'Immigrants not yet citizens', 0.06, 0.85, 0.6, lean('democratic', 12), 'immigrant');
   66|   } else if (y <= 1968) {
   67|     add('north', 'Northerners', 0.5, 0.03, Math.min(0.8, T + 0.05), lean('republican', y <= 1928 ? 3 : 0), 'north');
   68|     const southBarred = firstOf([[y >= 1964, 0.03], [y >= 1948, 0.15]], 0.25);
   69|     const southDemPts = firstOf([[y >= 1952, 8], [y === 1928, 15]], 35);
   70|     const southLean = y === 1964 ? lean('republican', 15) : lean('democratic', southDemPts);
   71|     add('south-white', 'White Southerners', 0.18, southBarred, y >= 1948 ? 0.45 : 0.3, southLean, 'south');
   72|     const blackDemPts = y >= 1964 ? 45 : 20;
   73|     const blackSouthLean = y <= 1932 ? lean('republican', 25, 0) : lean('democratic', blackDemPts, 0);
   74|     add('black-south', 'Black Southerners', 0.05, lerp([[1944, 0.95], [1948, 0.88], [1952, 0.8], [1960, 0.7], [1964, 0.45], [1968, 0.3]], y), 0.6,
   75|       blackSouthLean, 'black-south');
   76|     const blackNorthLean = y <= 1932 ? lean('republican', 20, 0) : lean('democratic', blackDemPts, 0);
   77|     add('black-north', 'Black Northerners', lerp([[1920, 0.02], [1960, 0.045]], y), 0.05, 0.6, blackNorthLean, 'black-north');
   78|     if (y === 1920) add('women', 'Women', 0.48, 0.08, 0.35, lean('republican', 3), 'all', { mirror: true, tilt: 0.03 });
   79|     else add('youth', '18- to 20-year-olds', 0.075, firstOf([[y >= 1956, 0.95], [y >= 1944, 0.97]], 1), 0.5, lean(null), 'all');
   80|   } else {
   81|     add('white', 'White voters', lerp([[1972, 0.8], [2024, 0.6]], y), 0.02, T + 0.04, lean('republican', 10), 'all');
   82|     add('black', 'Black voters', 0.12, 0.08, T - 0.02, lean('democratic', 40, 0.02), 'black');
   83|     if (y >= 1980) add('latino', 'Latino voters', lerp([[1980, 0.04], [2024, 0.15]], y), 0.4, 0.45, lean('democratic', 15), 'latino');
   84|     add('young', 'Voters under 30', 0.22, 0.05, T - 0.15, lean('democratic', 6), 'all');
   85|     if (y >= 1976) add('felony', 'People with felony records', lerp([[1976, 0.01], [2016, 0.025], [2024, 0.021]], y), 0.75, 0.3, lean('democratic', 20, 0), 'felony');
   86|   }
   87|   return s;
   88| }
   89| 
   90| /** An era what-if: a WhatIfSpec, and the years it fits. */
   91| type EraWhatIf = readonly [...WhatIfSpec, when: (y: number) => boolean];
   92| 
   93| const ERA_WHAT_IFS: readonly EraWhatIf[] = [
   94|   ['women', 'Women Vote', 'franchise', 'Every woman can vote on the same terms as the men of her state.', ['women'],
   95|     (c) => c.enfranchise('women', { barred: c.year < 1868 ? 0.14 : 0.08 }), (y) => y < 1920],
   96|   ['no-19th', 'The 19th Amendment Fails', 'franchise', 'Women can vote only in the fifteen states that already let them.', ['women'],
   97|     (c) => c.enfranchise('women', { barred: 0.7 }), (y) => y === 1920],
   98|   ['fifteenth', 'Enforce the 15th Amendment', 'franchise', 'Black Southerners vote as freely as white Southerners: no literacy tests, poll taxes or terror.', ['black-south', 'freedmen'],
   99|     (c) => c.enfranchise(c.has('freedmen') ? 'freedmen' : 'black-south', { barred: 0.05 }), (y) => y >= 1868 && y <= 1964],
  100|   ['emancipation', 'Emancipation and the Vote', 'franchise', 'Slavery ends before the election, and freed men vote like other men in their states.', ['enslaved'],
  101|     (c) => c.enfranchise('enslaved', { barred: 0.5 }), (y) => y >= 1796 && y <= 1860],
  102|   ['three-fifths', 'No Three-Fifths Bonus', 'franchise', 'Slave states lose the electors they got for counting enslaved people as three-fifths of a person.', ['enslaved'],
  103|     (c) => c.apportion(), (y) => y >= 1796 && y <= 1860],
  104|   ['no-property', 'No Property Test', 'franchise', 'Every free man can vote, whether or not he owns land.', ['no-property'],
  105|     (c) => c.enfranchise('no-property', { barred: 0 }), (y) => y <= 1824],
  106|   ['age18', 'Vote at 18', 'franchise', 'Eighteen-year-olds can vote everywhere, as they could after 1971.', ['youth'],
  107|     (c) => c.enfranchise('youth', { barred: 0 }), (y) => y >= 1924 && y <= 1968 && y !== 1920],
  108|   ['felons', 'Felony Records Don’t Bar Voting', 'franchise', 'Everyone who has served a sentence can vote, as in Maine and Vermont.', ['felony'],
  109|     (c) => c.enfranchise('felony', { barred: 0 }), (y) => y >= 1976],
  110|   ['migration', 'No Great Migration', 'population', 'The Black Southerners who moved north after 1910 stay in the South, where most can’t vote.', ['black-north', 'black-south'],
  111|     (c) => c.move('black-north', 0.7, 'black-south'), (y) => y >= 1928 && y <= 1968],
  112|   ['everyone', 'Everyone Votes', 'franchise', 'Every adult can vote, and turns out.', [],
  113|     (c) => c.everyone(), () => true],
  114| ];
  115| 
  116| /** The era's what-ifs that fit year y: up to three, then Everyone Votes. */
  117| export function eraWhatIfs(y: number): WhatIfSpec[] {
  118|   const fits = ERA_WHAT_IFS.filter((w) => w[6](y));
  119|   return [...fits.filter((w) => w[0] !== 'everyone').slice(0, 3), ...fits.filter((w) => w[0] === 'everyone')].map(
  120|     ([key, label, kind, detail, slices, apply]) => [key, label, kind, detail, slices, apply] as const,
  121|   );
  122| }
```

## `src/lib/simulacra/sampleTypes.ts`

```ts
    1| // Types shared by the sample model (sample.ts) and its written stories
    2| // (stories.ts). Nothing here is read from outside the page.
    3| import type { Choice, Kind } from './schemas';
    4| 
    5| /** How a group's voters split: [winner, runner-up, everyone else], summing to 1. */
    6| export type Lean = readonly [number, number, number];
    7| 
    8| /**
    9|  * Where a group lives, as the sample model spreads its votes over the
   10|  * states: a region, a demographic spread, or every state by its electors.
   11|  */
   12| export type Region =
   13|   | 'all'
   14|   | 'north'
   15|   | 'south'
   16|   | 'new-england'
   17|   | 'middle'
   18|   | 'midwest'
   19|   | 'plains'
   20|   | 'industrial'
   21|   | 'immigrant'
   22|   | 'latino'
   23|   | 'felony'
   24|   | 'black'
   25|   | 'black-south'
   26|   | 'black-north';
   27| 
   28| /** Explicit weights by state code, overriding a region. */
   29| export type StateWeights = Readonly<Record<string, number>>;
   30| 
   31| /** One written person: [name, who they are, what they did in history, what they do once a what-if reaches them, quote]. */
   32| export type VoterSpec = readonly [name: string, line: string, history: Choice, then: Choice, quote: string];
   33| 
   34| /** A group of voters as written (a story) or as an era has it. */
   35| export interface SliceSpec {
   36|   readonly key: string;
   37|   readonly label: string;
   38|   /** Share of all adults. */
   39|   readonly share: number;
   40|   /** Share of the group that couldn't vote. */
   41|   readonly barred: number;
   42|   /** Turnout of those who could. */
   43|   readonly turnout: number;
   44|   /** How its voters split. */
   45|   readonly lean: Lean;
   46|   /** How its barred members would vote. */
   47|   readonly leanIf?: Lean;
   48|   readonly where: Region;
   49|   /** Explicit state weights, used instead of `where` when present. */
   50|   readonly states?: StateWeights;
   51|   /** Enfranchised, it votes like its own state… */
   52|   readonly mirror?: boolean;
   53|   /** …with this lean toward A. */
   54|   readonly tilt?: number;
   55|   readonly voter?: VoterSpec;
   56| }
   57| 
   58| /** Vote-share changes keyed by candidate bucket, for drop(). */
   59| export interface DropTo {
   60|   readonly A?: number;
   61|   readonly B?: number;
   62| }
   63| 
   64| /** The levers a what-if pulls (sample.ts implements them). */
   65| export interface SampleContext {
   66|   /** The election's year. */
   67|   readonly year: number;
   68|   /** Whether this election has a group with this key. */
   69|   has(key: string): boolean;
   70|   /** Some of a group's barred members (or all) can vote. */
   71|   enfranchise(key: string, opts?: { barred?: number; turnout?: number; lean?: Lean }): void;
   72|   /** A group's voters swing `pts` points to `to`. */
   73|   swing(key: string, pts: number, to: 'A' | 'B'): void;
   74|   /** Everyone in `region` (or everywhere) swings `pts` points to `to`. */
   75|   swingAll(pts: number, to: 'A' | 'B', region: Region | null, text: string): void;
   76|   /** A share of the other candidates' voters (in `region`) choose A or B instead; the rest stay home. */
   77|   drop(frac: number, to: DropTo, text: string, region?: Region): void;
   78|   /** The runner-up absorbs most of the others' voters (1860's Democrats). */
   79|   unite(frac: number, text: string): void;
   80|   /** Votes moved straight to `to` from the others, in given states. */
   81|   shift(states: StateWeights, to: 'A' | 'B', text: string): void;
   82|   /** A share of a group lives where another group does, and fares like it. */
   83|   move(key: string, frac: number, toKey: string): void;
   84|   /** A group turns out at `t`. */
   85|   turnout(key: string, t: number): void;
   86|   /** Every adult can vote, and does. */
   87|   everyone(): void;
   88|   /** The slave states lose their three-fifths bonus in electors. */
   89|   apportion(): void;
   90|   /** Black Southerners vote, where the story has no group for them (1912). */
   91|   enfranchiseBlackSouth(opts: { lean: Lean }): void;
   92| }
   93| 
   94| /** [key, label, kind, detail, the groups it reaches, how it changes the election]. */
   95| export type WhatIfSpec = readonly [
   96|   key: string,
   97|   label: string,
   98|   kind: Kind,
   99|   detail: string,
  100|   slices: readonly string[],
  101|   apply: (c: SampleContext) => void,
  102| ];
  103| 
  104| /** One written election. `states`: a few states' real vote shares [A, B]. */
  105| export interface Story {
  106|   readonly slices: readonly SliceSpec[];
  107|   readonly whatIfs: readonly WhatIfSpec[];
  108|   readonly states: Readonly<Record<string, readonly [number, number]>>;
  109| }
  110| 
  111| /** Votes or shares for the winner (A), the runner-up (B) and everyone else (O). */
  112| export interface Votes {
  113|   A: number;
  114|   B: number;
  115|   O: number;
  116| }
  117| 
  118| /** A group's make-up, as fractions of its adults: barred (couldn't vote), home (could, didn't), A / B / O (voted for). */
  119| export interface Fractions extends Votes {
  120|   barred: number;
  121|   home: number;
  122| }
```

## `src/lib/simulacra/schemas.ts`

```ts
    1| // The simulation server's answers, parsed once where they enter the page
    2| // (api.ts). The schemas are the server's own (serve/contract.ts, one
    3| // definition for both sides), so the page's types can't drift from what the
    4| // server sends; every type the page uses for them derives from these.
    5| export * from '../../../serve/contract';
```

## `src/lib/simulacra/state.svelte.ts`

```ts
    1| // The page's state, reactive: per year, the groups and what-ifs the server
    2| // sent (sims), the chosen what-ifs, the dragged dots (edits) and the rerun on
    3| // show (results); the year and view (kept in the URL); and the run in hand.
    4| // The pure parts are state.ts; reruns are runs.ts.
    5| import { SvelteMap } from 'svelte/reactivity';
    6| import type { Edits, SimulacraApi, SliceEdit } from './api';
    7| import { ELECTION_YEARS } from './geo';
    8| import { traceOf } from './narrator';
    9| import { type ActiveRun, createRunner, type Finished, type Runner } from './runs';
   10| import type { Voter } from './schemas';
   11| import {
   12|   addEdit,
   13|   askOf,
   14|   chipOrder,
   15|   electionFor,
   16|   isDirty,
   17|   type Server,
   18|   serverAfter,
   19|   type ShownRun,
   20|   type Sim,
   21|   toggled,
   22|   urlForYear,
   23|   type View,
   24| } from './state';
   25| 
   26| export interface PageStateOptions {
   27|   readonly api: SimulacraApi;
   28|   readonly year: number;
   29|   /** Puts a URL in the address bar without navigating. */
   30|   readonly replaceUrl?: (url: string) => void;
   31|   /** The page's address now. */
   32|   readonly href?: () => string;
   33|   /** A rerun finished for the year on show: its steps start coming out. */
   34|   readonly onFresh?: (steps: number) => void;
   35|   readonly sleep?: (ms: number) => Promise<void>;
   36|   readonly now?: () => number;
   37| }
   38| 
   39| export class PageState {
   40|   readonly api: SimulacraApi;
   41|   year = $state(1789);
   42|   view = $state<View>('history');
   43|   server = $state<Server>('connecting');
   44|   /** Why the year's groups didn't load. */
   45|   simFailed = $state<string | null>(null);
   46|   readonly sims = new SvelteMap<number, Sim>();
   47|   readonly chosen = new SvelteMap<number, readonly string[]>();
   48|   /** Dots dragged by hand, per year: each group's change in its fractions, summed over drags. */
   49|   readonly edits = new SvelteMap<number, Edits>();
   50|   readonly results = new SvelteMap<number, ShownRun>();
   51|   /** Chips added this visit, per year, newest first: they lead the row. */
   52|   readonly added = new SvelteMap<number, readonly string[]>();
   53|   /** Bumped by Reset, so the rows drop any drag in hand. */
   54|   editEpoch = $state(0);
   55|   typed = $state('');
   56|   lastToggled = $state<string | null>(null);
   57|   run = $state<ActiveRun | null>(null);
   58|   runError = $state<string | null>(null);
   59|   openSlice = $state<string | null>(null);
   60|   readonly voters = new SvelteMap<string, Voter | null>();
   61|   voterLoading = $state<string | null>(null);
   62|   /** The URL is written once the router is ready. */
   63|   urlReady = false;
   64| 
   65|   readonly election = $derived(electionFor(this.year));
   66|   readonly sim = $derived(this.sims.get(this.year) ?? null);
   67|   readonly whatIfs = $derived(chipOrder(this.sim?.whatIfs ?? [], this.added.get(this.year)));
   68|   readonly selected = $derived(this.chosen.get(this.year) ?? []);
   69|   readonly result = $derived(this.results.get(this.year) ?? null);
   70|   /** The rerun on show: the year's result in the Rerun view. */
   71|   readonly rerun = $derived(this.view === 'whatif' ? this.result : null);
   72|   readonly showing = $derived<'history' | 'whatif'>(this.rerun ? 'whatif' : 'history');
   73|   readonly light = $derived(this.view !== 'whatif');
   74|   readonly running = $derived(!!this.run && this.run.year === this.year);
   75|   readonly canRun = $derived(this.server === 'online' && !!this.sim && this.whatIfs.length > 0 && !this.running);
   76|   readonly canEdit = $derived(this.server === 'online' && !!this.sim && !this.running && !this.election.unopposed);
   77|   readonly dirty = $derived(isDirty(this.result, this.selected, this.typed, this.edits.get(this.year)));
   78|   readonly voterKey = $derived(this.openSlice ? `${this.year}|${this.openSlice}|${this.rerun?.runId ?? ''}` : null);
   79|   readonly voter = $derived(this.voterKey ? (this.voters.get(this.voterKey) ?? null) : null);
   80| 
   81|   readonly #runner: Runner;
   82|   readonly #replaceUrl: ((url: string) => void) | undefined;
   83|   readonly #href: () => string;
   84|   readonly #onFresh: ((steps: number) => void) | undefined;
   85| 
   86|   constructor(o: PageStateOptions) {
   87|     this.api = o.api;
   88|     this.year = o.year;
   89|     this.#replaceUrl = o.replaceUrl;
   90|     this.#href = o.href ?? (() => location.href);
   91|     this.#onFresh = o.onFresh;
   92|     this.#runner = createRunner({
   93|       api: o.api,
   94|       ...(o.sleep ? { sleep: o.sleep } : {}),
   95|       ...(o.now ? { now: o.now } : {}),
   96|       getRun: () => this.run,
   97|       setRun: (r) => {
   98|         this.run = r;
   99|       },
  100|       reloadSim: async (y) => {
  101|         const before = new Set((this.sims.get(y)?.whatIfs ?? []).map((w) => w.key));
  102|         this.sims.delete(y);
  103|         await this.loadSim(y, true);
  104|         const fresh = (this.sims.get(y)?.whatIfs ?? []).map((w) => w.key).filter((k) => !before.has(k));
  105|         if (fresh.length) this.added.set(y, [...fresh, ...(this.added.get(y) ?? [])]);
  106|       },
  107|       whatIfsOf: (y) => this.sims.get(y)?.whatIfs ?? [],
  108|       finished: (f) => this.#finish(f),
  109|       failed: (message) => {
  110|         this.runError = message;
  111|       },
  112|     });
  113|   }
  114| 
  115|   /** What a rerun of year `y` would send. */
  116|   askOf(y: number, keys: readonly string[], text: string): string {
  117|     return askOf(keys, text, this.edits.get(y));
  118|   }
  119| 
  120|   // ── Loading an election's groups and what-ifs ──
  121|   /** Loads a year once; `fresh` skips every cache (after a run). */
  122|   async loadSim(y: number, fresh = false): Promise<void> {
  123|     if (this.sims.has(y)) return;
  124|     this.simFailed = null;
  125|     const out = await this.api.election(y, { fresh });
  126|     switch (out.kind) {
  127|       case 'ok':
  128|         this.sims.set(y, { slices: out.value.slices, whatIfs: out.value.whatIfs });
  129|         this.server = 'online';
  130|         return;
  131|       case 'unsupported':
  132|         this.server = 'unsupported';
  133|         break;
  134|       case 'error':
  135|         this.server = serverAfter(this.server, out.reason);
  136|         break;
  137|       case 'indeterminate':
  138|         if (this.server === 'connecting') this.server = 'offline';
  139|         break;
  140|       default:
  141|         out satisfies never;
  142|     }
  143|     this.simFailed = out.message || 'Couldn’t load this election’s voters.';
  144|   }
  145| 
  146|   retry(): void {
  147|     this.server = 'connecting';
  148|     this.sims.delete(this.year);
  149|     void this.loadSim(this.year);
  150|   }
  151| 
  152|   setYear(y: number): void {
  153|     if (!ELECTION_YEARS.includes(y) || y === this.year) return;
  154|     this.year = y;
  155|     this.openSlice = null;
  156|     this.typed = '';
  157|     this.lastToggled = null;
  158|     this.runError = null;
  159|     this.view = this.results.has(y) ? 'whatif' : 'history';
  160|     this.syncUrl();
  161|   }
  162| 
  163|   step(d: number): void {
  164|     const i = ELECTION_YEARS.indexOf(this.year);
  165|     const y = ELECTION_YEARS[Math.max(0, Math.min(ELECTION_YEARS.length - 1, i + d))];
  166|     if (y !== undefined) this.setYear(y);
  167|   }
  168| 
  169|   syncUrl(): void {
  170|     if (!this.urlReady || !this.#replaceUrl) return;
  171|     const url = urlForYear(this.#href(), this.year);
  172|     if (url) this.#replaceUrl(url);
  173|   }
  174| 
  175|   // ── What-ifs and reruns ──
  176|   toggle(key: string): void {
  177|     const next = toggled(this.chosen.get(this.year) ?? [], key);
  178|     this.chosen.set(this.year, next);
  179|     this.lastToggled = next.includes(key) ? key : null;
  180|     this.runError = null;
  181|   }
  182| 
  183|   rerunNow(): void {
  184|     if (!this.canRun) return;
  185|     // Nothing changed since this year's last rerun: show it again rather than
  186|     // running (and walking the robot) for the same answer.
  187|     const r = this.results.get(this.year);
  188|     if (r && !this.typed.trim() && this.askOf(this.year, this.chosen.get(this.year) ?? [], '') === r.ask) {
  189|       this.view = 'whatif';
  190|       this.lastToggled = null;
  191|       return;
  192|     }
  193|     void this.startRerun();
  194|   }
  195| 
  196|   /** A drag on a group's dots: added to the year's edits, then rerun at once. */
  197|   editSlice(key: string, d: SliceEdit): void {
  198|     if (!this.canEdit) return;
  199|     this.edits.set(this.year, addEdit(this.edits.get(this.year), key, d));
  200|     void this.startRerun();
  201|   }
  202| 
  203|   startRerun(): Promise<void> {
  204|     const y = this.year;
  205|     const keys = [...(this.chosen.get(y) ?? [])];
  206|     const labels = keys.flatMap((k) => this.whatIfs.find((w) => w.key === k)?.label ?? []);
  207|     const text = this.typed.trim();
  208|     this.runError = null;
  209|     this.openSlice = null;
  210|     const edits = this.edits.get(y) ?? {};
  211|     return this.#runner.start({ year: y, keys, text, edits, total: this.election.states.length, labels });
  212|   }
  213| 
  214|   stop(): void {
  215|     this.#runner.stop();
  216|   }
  217| 
  218|   #finish(f: Finished): void {
  219|     const { year: y, id, result, keys, text, applied } = f;
  220|     // ask: the page's state right after this run, so pressing Rerun again
  221|     // with nothing changed just shows this.
  222|     const trace = traceOf(result, text, keys, y);
  223|     this.results.set(y, { ...result, runId: id, keys, text, trace, ask: this.askOf(y, applied, ''), ran: applied });
  224|     if (y === this.year) this.#onFresh?.(trace.length);
  225|     // What was applied, typed words included, shows as the chosen what-ifs.
  226|     this.chosen.set(y, applied);
  227|     this.run = null;
  228|     if (y === this.year) {
  229|       this.typed = '';
  230|       this.lastToggled = null;
  231|       this.view = 'whatif';
  232|     }
  233|   }
  234| 
  235|   reset(): void {
  236|     this.chosen.set(this.year, []);
  237|     this.results.delete(this.year);
  238|     this.edits.delete(this.year);
  239|     this.editEpoch += 1;
  240|     this.typed = '';
  241|     this.lastToggled = null;
  242|     this.runError = null;
  243|     this.view = 'history';
  244|   }
  245| 
  246|   // ── One person from a group ──
  247|   toggleSlice(key: string): void {
  248|     this.openSlice = this.openSlice === key ? null : key;
  249|     this.lastToggled = null;
  250|   }
  251| 
  252|   /** Fetches the open group's person, once per year, group and rerun. */
  253|   fetchVoter(): void {
  254|     const key = this.voterKey;
  255|     const slice = this.openSlice;
  256|     if (!key || !slice || this.voters.has(key) || this.voterLoading === key) return;
  257|     this.voterLoading = key;
  258|     void this.api.voter(this.year, slice, this.rerun?.runId ?? null).then((out) => {
  259|       this.voters.set(key, out.kind === 'ok' ? out.value : null);
  260|       if (this.voterLoading === key) this.voterLoading = null;
  261|     });
  262|   }
  263| 
  264|   /** Stops the run on show (the page is going away). */
  265|   dispose(): void {
  266|     this.run = null;
  267|   }
  268| }
```

## `src/lib/simulacra/state.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import type { Outcome, SimulacraApi } from './api';
    3| import type { ElectionResponse } from './schemas';
    4| import { addEdit, apiOptionsFor, askOf, isDirty, randomStory, readParams, serverAfter, toggled, urlForYear } from './state';
    5| import { PageState } from './state.svelte';
    6| 
    7| describe('askOf', () => {
    8|   test('the same what-ifs in any order, the same words with any spacing: the same ask', () => {
    9|     expect(askOf(['no-19th', 'league'], '  women stay home ', undefined)).toBe(askOf(['league', 'no-19th'], 'women stay home', undefined));
   10|   });
   11| 
   12|   test('different what-ifs, words or dots: a different ask', () => {
   13|     const base = askOf(['league'], '', undefined);
   14|     expect(askOf(['league', 'no-19th'], '', undefined)).not.toBe(base);
   15|     expect(askOf(['league'], 'and more', undefined)).not.toBe(base);
   16|     expect(askOf(['league'], '', { women: { A: 0.1, home: -0.1 } })).not.toBe(base);
   17|   });
   18| 
   19|   test('no edits and empty edits ask the same; the keys passed in are left alone', () => {
   20|     const keys = ['b', 'a'];
   21|     expect(askOf(keys, '', undefined)).toBe(askOf(keys, '', {}));
   22|     expect(keys).toEqual(['b', 'a']);
   23|   });
   24| });
   25| 
   26| describe('the pure parts', () => {
   27|   test('isDirty: typed words always; with no rerun, anything chosen or dragged; else anything changed since', () => {
   28|     expect(isDirty(null, [], ' x ', undefined)).toBe(true);
   29|     expect(isDirty(null, [], '', undefined)).toBe(false);
   30|     expect(isDirty(null, ['league'], '', undefined)).toBe(true);
   31|     const shown = { ask: askOf(['league'], '', undefined) };
   32|     expect(isDirty(shown, ['league'], '  ', undefined)).toBe(false);
   33|     expect(isDirty(shown, ['league', 'no-19th'], '', undefined)).toBe(true);
   34|   });
   35| 
   36|   test('addEdit sums each fraction over drags, per group', () => {
   37|     const one = addEdit(undefined, 'women', { A: 0.1, home: -0.1 });
   38|     const two = addEdit(one, 'women', { A: 0.05, B: -0.05 });
   39|     const three = addEdit(two, 'men', { O: 0.02, home: -0.02 });
   40|     expect(three).toEqual({ women: { A: 0.15000000000000002, home: -0.1, B: -0.05 }, men: { O: 0.02, home: -0.02 } });
   41|     expect(one).toEqual({ women: { A: 0.1, home: -0.1 } });
   42|   });
   43| 
   44|   test('toggled adds or removes one key', () => {
   45|     expect(toggled(['a'], 'b')).toEqual(['a', 'b']);
   46|     expect(toggled(['a', 'b'], 'a')).toEqual(['b']);
   47|   });
   48| 
   49|   test('the URL: sample, simapi in dev only, an election year or none', () => {
   50|     const p = (q: string, dev = true) => readParams(new URLSearchParams(q), dev);
   51|     expect(p('sample=1&year=1896')).toEqual({ sample: true, simapi: null, year: 1896 });
   52|     expect(p('sample=true&year=1897').year).toBeNull();
   53|     expect(p('simapi=http://localhost:8787').simapi).toBe('http://localhost:8787');
   54|     expect(p('simapi=http://localhost:8787', false).simapi).toBeNull();
   55|     expect(apiOptionsFor('http://localhost:8787')).toEqual({ base: 'http://localhost:8787/api/simulacra' });
   56|     expect(apiOptionsFor(null)).toEqual({});
   57|     expect(apiOptionsFor(null, 'k'.repeat(16))).toEqual({ accessKey: 'k'.repeat(16) });
   58|     expect(urlForYear('http://x.test/?sample=1&year=1896', 1896)).toBeNull();
   59|     expect(urlForYear('http://x.test/?sample=1', 1912)).toBe('http://x.test/?sample=1&year=1912');
   60|   });
   61| 
   62|   test('serverAfter: offline is offline; too many requests is limited until the service has answered; others stay', () => {
   63|     expect(serverAfter('online', 'offline')).toBe('offline');
   64|     expect(serverAfter('connecting', 'limited')).toBe('limited');
   65|     expect(serverAfter('online', 'limited')).toBe('online');
   66|     expect(serverAfter('connecting', 'failed')).toBe('offline');
   67|     expect(serverAfter('online', 'malformed')).toBe('online');
   68|     expect(serverAfter('limited', 'missing')).toBe('limited');
   69|   });
   70| 
   71|   test('randomStory never repeats the year it leaves', () => {
   72|     for (const r of [0, 0.3, 0.6, 0.999]) expect(randomStory(1896, () => r)).not.toBe(1896);
   73|   });
   74| });
   75| 
   76| const ELECTION: ElectionResponse = {
   77|   slices: [{ key: 'women', label: 'Women', adults: 27, barred: 0, home: 0.5, A: 0.3, B: 0.15, O: 0.05 }],
   78|   whatIfs: [{ key: 'league', label: 'The League', kind: 'issue', detail: 'The Senate ratifies.', slices: ['women'] }],
   79|   simulated: true,
   80| };
   81| 
   82| /** A server that answers every year and never starts a run. */
   83| function fakeApi(): SimulacraApi & { elections: number[] } {
   84|   const elections: number[] = [];
   85|   const no: Outcome<never> = { kind: 'error', reason: 'failed', message: 'The simulation server answered 500.', status: 500 };
   86|   return {
   87|     sample: false,
   88|     elections,
   89|     election: async (y) => {
   90|       elections.push(y);
   91|       return { kind: 'ok', value: ELECTION };
   92|     },
   93|     startRun: async () => no,
   94|     run: async () => no,
   95|     stopRun: async () => ({ kind: 'ok', value: null }),
   96|     voter: async () => no,
   97|   };
   98| }
   99| 
  100| describe('PageState', () => {
  101|   test('edits and chosen what-ifs per year survive switching years', async () => {
  102|     const api = fakeApi();
  103|     const page = new PageState({ api, year: 1920 });
  104|     await page.loadSim(1920);
  105|     expect(page.server).toBe('online');
  106|     page.toggle('league');
  107|     page.editSlice('women', { A: 0.1, home: -0.1 });
  108|     await new Promise((resolve) => setTimeout(resolve, 0));
  109|     expect(page.runError).toBe('The simulation server answered 500.');
  110|     const asked = page.askOf(1920, ['league'], '');
  111| 
  112|     page.setYear(1896);
  113|     expect(page.year).toBe(1896);
  114|     expect(page.view).toBe('history');
  115|     expect(page.runError).toBeNull();
  116|     expect(page.edits.get(1896)).toBeUndefined();
  117|     expect(page.selected).toEqual([]);
  118| 
  119|     page.setYear(1920);
  120|     expect(page.edits.get(1920)).toEqual({ women: { A: 0.1, home: -0.1 } });
  121|     expect(page.selected).toEqual(['league']);
  122|     expect(page.askOf(1920, ['league'], '')).toBe(asked);
  123|     expect(page.dirty).toBe(true);
  124|   });
  125| 
  126|   test('reset clears only the year on show', async () => {
  127|     const page = new PageState({ api: fakeApi(), year: 1920 });
  128|     await page.loadSim(1920);
  129|     page.toggle('league');
  130|     page.setYear(1896);
  131|     await page.loadSim(1896);
  132|     page.toggle('league');
  133|     page.reset();
  134|     expect(page.chosen.get(1896)).toEqual([]);
  135|     expect(page.chosen.get(1920)).toEqual(['league']);
  136|   });
  137| 
  138|   test('the URL follows the year once it is ready', () => {
  139|     const urls: string[] = [];
  140|     let href = 'http://x.test/?sample=1';
  141|     const page = new PageState({
  142|       api: fakeApi(),
  143|       year: 1920,
  144|       href: () => href,
  145|       replaceUrl: (u) => {
  146|         urls.push(u);
  147|         href = u;
  148|       },
  149|     });
  150|     page.setYear(1912);
  151|     expect(urls).toEqual([]);
  152|     page.urlReady = true;
  153|     page.syncUrl();
  154|     page.setYear(1916);
  155|     page.syncUrl();
  156|     expect(urls).toEqual(['http://x.test/?sample=1&year=1912', 'http://x.test/?sample=1&year=1916']);
  157|   });
  158| 
  159|   test('no simulation service: the page says so, and a year loads once', async () => {
  160|     const api = fakeApi();
  161|     const page = new PageState({
  162|       api: { ...api, election: async () => ({ kind: 'unsupported', message: 'This server has no simulation service yet.' }) },
  163|       year: 1920,
  164|     });
  165|     await page.loadSim(1920);
  166|     expect(page.server).toBe('unsupported');
  167|     expect(page.simFailed).toBe('This server has no simulation service yet.');
  168|     const ok = new PageState({ api, year: 1920 });
  169|     await ok.loadSim(1920);
  170|     await ok.loadSim(1920);
  171|     expect(api.elections).toEqual([1920]);
  172|   });
  173| });
```

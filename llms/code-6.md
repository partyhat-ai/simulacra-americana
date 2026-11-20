# synthetic-electorate-toy: source and docs, part 6 of 15

Generated from commit `be1682104fbe` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy. Regenerate whenever the code changes.
Files `serve/guard.test.ts` to `simharness/aggregate.py`. Lines are numbered as in the repository.

## `serve/guard.test.ts`

```ts
    1| import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
    2| import { tmpdir } from 'node:os';
    3| import path from 'node:path';
    4| import { describe, expect, it } from 'vitest';
    5| import { parseKeyRing, pruneJsonl, RateLimiter } from './guard';
    6| 
    7| const dir = mkdtempSync(path.join(tmpdir(), 'simulacra-guard-'));
    8| const DAY = 86_400_000;
    9| 
   10| describe('parseKeyRing', () => {
   11|   const ring = parseKeyRing(JSON.stringify({ ana: 'a'.repeat(24), ben: 'b'.repeat(40) }));
   12| 
   13|   it('names the key a bearer header carries', () => {
   14|     expect(ring.size).toBe(2);
   15|     expect(ring.identify(`Bearer ${'a'.repeat(24)}`)).toBe('ana');
   16|     expect(ring.identify(`Bearer ${'b'.repeat(40)}`)).toBe('ben');
   17|   });
   18| 
   19|   it('names nobody for a missing, wrong or malformed header', () => {
   20|     for (const h of [undefined, '', 'Bearer ', `Basic ${'a'.repeat(24)}`, `Bearer ${'a'.repeat(23)}`, `Bearer ${'a'.repeat(24)} `]) {
   21|       expect(ring.identify(h)).toBeNull();
   22|     }
   23|   });
   24| 
   25|   it('is empty when unset, and refuses short keys or bad names at startup', () => {
   26|     expect(parseKeyRing(undefined).size).toBe(0);
   27|     expect(parseKeyRing('  ').identify(`Bearer ${'a'.repeat(24)}`)).toBeNull();
   28|     expect(() => parseKeyRing(JSON.stringify({ ana: 'short' }))).toThrow();
   29|     expect(() => parseKeyRing(JSON.stringify({ 'Bad Name': 'a'.repeat(24) }))).toThrow();
   30|     expect(() => parseKeyRing('{not json')).toThrow();
   31|   });
   32| });
   33| 
   34| describe('RateLimiter', () => {
   35|   it('admits max per window, then says when to retry', () => {
   36|     let t = 0;
   37|     const rl = new RateLimiter({ max: 2, windowMs: 10_000 }, () => t);
   38|     expect(rl.admit('ip').ok).toBe(true);
   39|     expect(rl.admit('ip').ok).toBe(true);
   40|     t = 4_000;
   41|     expect(rl.admit('ip')).toEqual({ ok: false, retryAfterS: 6 });
   42|     expect(rl.admit('other').ok).toBe(true);
   43|     t = 10_000;
   44|     expect(rl.admit('ip').ok).toBe(true);
   45|   });
   46| 
   47|   it('holds at most maxKeys windows', () => {
   48|     let t = 0;
   49|     const rl = new RateLimiter({ max: 1, windowMs: 1_000_000 }, () => t, 3);
   50|     for (const ip of ['a', 'b', 'c', 'd', 'e']) {
   51|       t += 1;
   52|       rl.admit(ip);
   53|     }
   54|     // The oldest windows were dropped: 'a' starts afresh, 'e' is still limited.
   55|     expect(rl.admit('a').ok).toBe(true);
   56|     expect(rl.admit('e').ok).toBe(false);
   57|   });
   58| });
   59| 
   60| describe('pruneJsonl', () => {
   61|   it('keeps lines inside the retention, whatever their timestamp style', () => {
   62|     const now = Date.parse('2026-10-01T12:00:00Z');
   63|     const f = path.join(dir, 'log.jsonl');
   64|     const rows = [
   65|       { ts: '2026-09-20T00:00:00Z', text: 'old iso' },
   66|       { ts: '2026-09-30T10:00:00', text: 'new, no zone' },
   67|       { ts: '2026-09-30T10:00:00+00:00', text: 'new, offset' },
   68|       { at: (now - 9 * DAY) / 1000, text: 'old epoch' },
   69|       { at: (now - DAY) / 1000, text: 'new epoch' },
   70|       { text: 'no stamp' }
   71|     ];
   72|     writeFileSync(f, `${rows.map((r) => JSON.stringify(r)).join('\n')}\n`);
   73|     expect(pruneJsonl(f, 7 * DAY, now)).toBe(3);
   74|     expect(readFileSync(f, 'utf8').trim().split('\n').map((l) => JSON.parse(l).text)).toEqual(['new, no zone', 'new, offset', 'new epoch']);
   75|     expect(pruneJsonl(f, 7 * DAY, now)).toBe(0);
   76|     expect(pruneJsonl(path.join(dir, 'missing.jsonl'), DAY, now)).toBe(0);
   77|   });
   78| 
   79|   it('with scrub, keeps old lines without the named fields', () => {
   80|     const now = Date.parse('2026-10-01T12:00:00Z');
   81|     const f = path.join(dir, 'spend.jsonl');
   82|     writeFileSync(
   83|       f,
   84|       `${[
   85|         { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 1.5, note: 'a visitor typed this' },
   86|         { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 0.5 },
   87|         { ts: '2026-09-30T00:00:00Z', day: '2026-09-30', dollars: 2, note: 'recent' }
   88|       ]
   89|         .map((r) => JSON.stringify(r))
   90|         .join('\n')}\n`
   91|     );
   92|     expect(pruneJsonl(f, 7 * DAY, now, ['note'])).toBe(1);
   93|     expect(readFileSync(f, 'utf8').trim().split('\n').map((l) => JSON.parse(l))).toEqual([
   94|       { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 1.5 },
   95|       { ts: '2026-09-01T00:00:00Z', day: '2026-09-01', dollars: 0.5 },
   96|       { ts: '2026-09-30T00:00:00Z', day: '2026-09-30', dollars: 2, note: 'recent' }
   97|     ]);
   98|   });
   99| });
```

## `serve/guard.ts`

```ts
    1| // What stands between a visitor and the API: per-IP rate limits, access keys
    2| // (whose names the spend ledger records), and how long session logs keep
    3| // visitors' words.
    4| //
    5| // Only typed text the page doesn't already know costs anything (the intake
    6| // worker's compile, research and interviews). Nothing caps those dollars: any
    7| // visitor may queue text, a few texts per IP an hour.
    8| import { createHash, timingSafeEqual } from 'node:crypto';
    9| import { readFileSync, renameSync, statSync, truncateSync, writeFileSync } from 'node:fs';
   10| import { z } from 'zod';
   11| 
   12| // ── Access keys ──
   13| 
   14| /** SIMULACRA_ACCESS_KEYS: a JSON object of key name → key. Names are what the spend ledger records. */
   15| const AccessKeys = z.record(z.string().regex(/^[a-z0-9][a-z0-9_-]{0,39}$/), z.string().regex(/^[A-Za-z0-9_-]{24,128}$/));
   16| 
   17| const digest = (s: string): Buffer => createHash('sha256').update(s).digest();
   18| 
   19| export interface KeyRing {
   20|   /** The name of the key a request's Authorization header carries, or null. */
   21|   identify(authorization: string | undefined): string | null;
   22|   readonly size: number;
   23| }
   24| 
   25| /** Parses SIMULACRA_ACCESS_KEYS; unset is an empty ring (nobody may queue), malformed throws at startup. */
   26| export function parseKeyRing(raw: string | undefined): KeyRing {
   27|   const keys = raw?.trim() ? Object.entries(AccessKeys.parse(JSON.parse(raw))) : [];
   28|   const hashed = keys.map(([name, key]) => ({ name, hash: digest(key) }));
   29|   return {
   30|     size: hashed.length,
   31|     identify(authorization) {
   32|       const m = /^Bearer ([A-Za-z0-9_-]{1,256})$/.exec(authorization ?? '');
   33|       if (!m?.[1]) return null;
   34|       const h = digest(m[1]);
   35|       // Every key is compared, in constant time, whichever matches.
   36|       let found: string | null = null;
   37|       for (const k of hashed) if (timingSafeEqual(h, k.hash)) found = k.name;
   38|       return found;
   39|     }
   40|   };
   41| }
   42| 
   43| // ── Rate limits ──
   44| 
   45| export interface Limit {
   46|   /** Requests allowed per window. */
   47|   readonly max: number;
   48|   readonly windowMs: number;
   49| }
   50| 
   51| export type Admit = { readonly ok: true } | { readonly ok: false; readonly retryAfterS: number };
   52| 
   53| /** A fixed window per key (an IP). Memory is bounded: expired windows are dropped as new keys arrive. */
   54| export class RateLimiter {
   55|   private readonly windows = new Map<string, { start: number; count: number }>();
   56| 
   57|   constructor(
   58|     private readonly limit: Limit,
   59|     private readonly now: () => number = Date.now,
   60|     private readonly maxKeys = 50_000
   61|   ) {}
   62| 
   63|   admit(key: string): Admit {
   64|     const t = this.now();
   65|     const w = this.windows.get(key);
   66|     if (w && t - w.start < this.limit.windowMs) {
   67|       if (w.count >= this.limit.max) return { ok: false, retryAfterS: Math.ceil((w.start + this.limit.windowMs - t) / 1000) };
   68|       w.count += 1;
   69|       return { ok: true };
   70|     }
   71|     // A new window goes to the back, so the oldest windows are at the front.
   72|     this.windows.delete(key);
   73|     this.windows.set(key, { start: t, count: 1 });
   74|     for (const [k, old] of this.windows) {
   75|       if (t - old.start < this.limit.windowMs && this.windows.size <= this.maxKeys) break;
   76|       this.windows.delete(k);
   77|     }
   78|     return { ok: true };
   79|   }
   80| }
   81| 
   82| // ── Session log retention ──
   83| 
   84| const Stamped = z.looseObject({ ts: z.string().optional(), at: z.number().optional() });
   85| 
   86| function stampOf(line: string): number | null {
   87|   let row: unknown;
   88|   try {
   89|     row = JSON.parse(line);
   90|   } catch {
   91|     return null;
   92|   }
   93|   const r = Stamped.safeParse(row);
   94|   if (!r.success) return null;
   95|   if (r.data.at !== undefined) return r.data.at * 1000;
   96|   if (r.data.ts === undefined) return null;
   97|   // Timestamps without a zone were written in the container's zone, UTC.
   98|   const t = Date.parse(/[zZ]|[+-]\d\d:\d\d$/.test(r.data.ts) ? r.data.ts : `${r.data.ts}Z`);
   99|   return Number.isNaN(t) ? null : t;
  100| }
  101| 
  102| /**
  103|  * Drops lines older than `maxAgeMs` (and unreadable ones) from a JSONL log, by
  104|  * writing a copy and renaming it over the original; with `scrub`, an old line
  105|  * is kept without the named fields instead. Only call it while no worker is
  106|  * running: the worker appends to these files. Returns lines dropped or scrubbed.
  107|  */
  108| export function pruneJsonl(file: string, maxAgeMs: number, now: number = Date.now(), scrub?: readonly string[]): number {
  109|   let text: string;
  110|   try {
  111|     text = readFileSync(file, 'utf8');
  112|   } catch {
  113|     return 0;
  114|   }
  115|   const lines = text.split('\n').filter(Boolean);
  116|   let changed = 0;
  117|   const keep = lines.flatMap((l) => {
  118|     const t = stampOf(l);
  119|     if (t !== null && now - t <= maxAgeMs) return [l];
  120|     if (t === null || !scrub) {
  121|       changed += 1;
  122|       return [];
  123|     }
  124|     const row = Stamped.parse(JSON.parse(l));
  125|     if (!scrub.some((k) => k in row)) return [l];
  126|     changed += 1;
  127|     return [JSON.stringify(Object.fromEntries(Object.entries(row).filter(([k]) => !scrub.includes(k))))];
  128|   });
  129|   if (!changed) return 0;
  130|   const tmp = `${file}.${process.pid}.tmp`;
  131|   writeFileSync(tmp, keep.length ? `${keep.join('\n')}\n` : '');
  132|   renameSync(tmp, file);
  133|   return changed;
  134| }
  135| 
  136| /** Empties a plain-text log past `maxBytes` (the worker's log; CloudWatch keeps its own copy). */
  137| export function capLog(file: string, maxBytes: number): boolean {
  138|   try {
  139|     if (statSync(file).size <= maxBytes) return false;
  140|     truncateSync(file, 0);
  141|     return true;
  142|   } catch {
  143|     return false;
  144|   }
  145| }
```

## `serve/index.ts`

```ts
    1| // `pnpm serve`: the page and its API on PORT (default 8787).
    2| import { createApp } from './app';
    3| 
    4| const port = Number(process.env.PORT || 8787);
    5| createApp().listen(port, () => {
    6|   console.log(`simulacra on http://localhost:${port} (bundles from ${process.env.SIMULACRA_BUNDLES || 'serve/bundles'})`);
    7| });
```

## `serve/server.ts`

```ts
    1| // The production entry (the API container's CMD, bundled to dist/server.mjs).
    2| // `pnpm serve` (index.ts) stays the local entry. This adds what a host behind
    3| // a load balancer needs and the local server doesn't:
    4| //   - GET /healthz: 200 "ok", no dependencies, registered before the app so a
    5| //     broken bundle or router can't fail the ALB health check;
    6| //   - trust proxy TRUST_PROXY_HOPS (default 2: the request comes through
    7| //     Vercel's proxy, then the ALB), so req.ip is the visitor's address for
    8| //     the per-IP rate limits. A request sent to the ALB directly can forge
    9| //     X-Forwarded-For; the dollar caps hang on access keys, not IPs;
   10| //   - SIGTERM: stop accepting, let in-flight requests finish, exit. A running
   11| //     worker is killed with the container; its queue item stays un-done and is
   12| //     retried by the next worker.
   13| import express from 'express';
   14| import { createApp } from './app';
   15| 
   16| const port = Number(process.env.PORT || 8080);
   17| const app = express();
   18| app.disable('x-powered-by');
   19| app.set('trust proxy', Number(process.env.TRUST_PROXY_HOPS || 2));
   20| app.get('/healthz', (_req, res) => {
   21|   res.set('Cache-Control', 'no-store').type('text/plain').send('ok');
   22| });
   23| app.use(createApp());
   24| 
   25| const server = app.listen(port, () => {
   26|   console.log(`simulacra api on :${port} (bundles from ${process.env.SIMULACRA_BUNDLES || 'serve/bundles'})`);
   27| });
   28| 
   29| function shutdown(signal: string): void {
   30|   console.log(`simulacra: ${signal}, closing`);
   31|   server.close(() => process.exit(0));
   32|   server.closeIdleConnections();
   33|   // ECS's stopTimeout is 30s; leave room to exit on our own terms.
   34|   setTimeout(() => process.exit(0), 20_000).unref();
   35| }
   36| process.on('SIGTERM', () => shutdown('SIGTERM'));
   37| process.on('SIGINT', () => shutdown('SIGINT'));
```

## `serve/simulacra.test.ts`

```ts
    1| // The real router and app, in process, over real HTTP, reading the real bundles in serve/bundles/.
    2| import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
    3| import type { AddressInfo } from 'node:net';
    4| import { tmpdir } from 'node:os';
    5| import path from 'node:path';
    6| import type { Server } from 'node:http';
    7| import { afterAll, beforeAll, describe, expect, it } from 'vitest';
    8| import { z } from 'zod';
    9| import { createApp } from './app';
   10| import { Bundle } from './bundle';
   11| import { parseKeyRing } from './guard';
   12| import { DEFAULT_LIMITS, IMMUTABLE, SHORT_CACHE, type SimulacraOptions } from './simulacra';
   13| 
   14| const ROOT = path.resolve(import.meta.dirname, '..');
   15| const scratch = mkdtempSync(path.join(tmpdir(), 'simulacra-test-'));
   16| const options: SimulacraOptions = {
   17|   bundles: path.join(ROOT, 'serve', 'bundles'),
   18|   sessions: path.join(scratch, 'sessions'),
   19|   devLog: false,
   20|   autorun: null,
   21|   python: 'python3',
   22|   root: ROOT,
   23|   keys: parseKeyRing(undefined),
   24|   retainDays: 7,
   25|   limits: DEFAULT_LIMITS
   26| };
   27| 
   28| let server: Server;
   29| let base = '';
   30| 
   31| beforeAll(async () => {
   32|   const build = path.join(scratch, 'build');
   33|   mkdirSync(build, { recursive: true });
   34|   writeFileSync(path.join(build, 'index.html'), '<!doctype html><title>page</title>');
   35|   server = createApp({ simulacra: options, build }).listen(0);
   36|   await new Promise<void>((resolve) => server.once('listening', resolve));
   37|   // SAFETY: listen(0) on a TCP port always reports an AddressInfo, never a pipe name.
   38|   const { port } = server.address() as AddressInfo;
   39|   base = `http://127.0.0.1:${port}`;
   40| });
   41| 
   42| afterAll(async () => {
   43|   await new Promise<void>((resolve) => server.close(() => resolve()));
   44|   rmSync(scratch, { recursive: true, force: true });
   45| });
   46| 
   47| const Election = z.object({ simulated: z.boolean(), slices: z.array(z.object({ key: z.string() })), whatIfs: z.array(z.object({ key: z.string() })) });
   48| const RunId = z.object({ id: z.string() });
   49| const Done = z.object({
   50|   status: z.literal('done'),
   51|   result: z.looseObject({
   52|     applied: z.array(z.object({ key: z.string() })),
   53|     unknown: z.string().nullable(),
   54|     range: z.unknown().optional(),
   55|     howIGotThis: z.array(z.string())
   56|   })
   57| });
   58| 
   59| async function run(body: unknown) {
   60|   const posted = await fetch(`${base}/api/simulacra/runs`, {
   61|     method: 'POST',
   62|     headers: { 'content-type': 'application/json' },
   63|     body: JSON.stringify(body)
   64|   });
   65|   expect(posted.status).toBe(200);
   66|   const { id } = RunId.parse(await posted.json());
   67|   const got = await fetch(`${base}/api/simulacra/runs/${id}`);
   68|   return Done.parse(await got.json()).result;
   69| }
   70| 
   71| describe('/api/simulacra', () => {
   72|   it('a simulated year answers simulated: true with its slices and what-ifs', async () => {
   73|     const res = await fetch(`${base}/api/simulacra/elections/1920`);
   74|     expect(res.status).toBe(200);
   75|     const e = Election.parse(await res.json());
   76|     expect(e.simulated).toBe(true);
   77|     expect(e.slices.map((s) => s.key)).toContain('women');
   78|     expect(e.whatIfs.map((w) => w.key)).toContain('league');
   79|   });
   80| 
   81|   it('a year with no bundle answers 200 with simulated: false', async () => {
   82|     const res = await fetch(`${base}/api/simulacra/elections/1999`);
   83|     expect(res.status).toBe(200);
   84|     expect(await res.json()).toEqual({ slices: [], whatIfs: [], simulated: false });
   85|   });
   86| 
   87|   it('the manifest names each published year and its run', async () => {
   88|     const res = await fetch(`${base}/api/simulacra/manifest`);
   89|     expect(res.headers.get('cache-control')).toBe(SHORT_CACHE);
   90|     const { years } = z.object({ years: z.record(z.string(), z.string()) }).parse(await res.json());
   91|     const runId = readFileSync(path.join(ROOT, 'serve', 'bundles', '1920.json'), 'utf8').match(/"runId": ?"([^"]+)"/)?.[1];
   92|     expect(years['1920']).toBe(runId);
   93|     expect(years['1999']).toBeUndefined();
   94|   });
   95| 
   96|   it("a year's answer carries its run and is immutable only at its versioned URL", async () => {
   97|     const plain = await fetch(`${base}/api/simulacra/elections/1920`);
   98|     expect(plain.headers.get('cache-control')).toBe(SHORT_CACHE);
   99|     const { runId } = z.object({ runId: z.string() }).parse(await plain.json());
  100|     const pinned = await fetch(`${base}/api/simulacra/elections/1920?v=${encodeURIComponent(runId)}`);
  101|     expect(pinned.headers.get('cache-control')).toBe(IMMUTABLE);
  102|     const stale = await fetch(`${base}/api/simulacra/elections/1920?v=not-this-run`);
  103|     expect(stale.headers.get('cache-control')).toBe(SHORT_CACHE);
  104|     const missing = await fetch(`${base}/api/simulacra/elections/1999?v=${encodeURIComponent(runId)}`);
  105|     expect(missing.headers.get('cache-control')).toBe(SHORT_CACHE);
  106|   });
  107| 
  108|   it('matches keywords as whole words: "flu" is not in "influence"', async () => {
  109|     const miss = await run({ year: 1920, text: 'the influence of the press' });
  110|     expect(miss.applied).toEqual([]);
  111|     expect(miss.unknown).toBe('the influence of the press');
  112|     const hit = await run({ year: 1920, text: 'the flu comes back' });
  113|     expect(hit.applied.map((a) => a.key)).toEqual(['influenza-returns-in-october-1920']);
  114|     expect(hit.unknown).toBeNull();
  115|   });
  116| 
  117|   it('hand edits re-tally one run with no range', async () => {
  118|     const r = await run({ year: '1920', whatIfs: ['league', 'not-a-what-if'], edits: { women: { home: -0.1, B: 0.1 } } });
  119|     expect(r.applied.map((a) => a.key)).toEqual(['league']);
  120|     expect(r.range).toBeUndefined();
  121|     expect(r.howIGotThis.at(-1)).toMatch(/by hand/);
  122|   });
  123| 
  124|   it('rejects a malformed body at the boundary', async () => {
  125|     const res = await fetch(`${base}/api/simulacra/runs`, {
  126|       method: 'POST',
  127|       headers: { 'content-type': 'application/json' },
  128|       body: JSON.stringify({ year: 'soon' })
  129|     });
  130|     expect(res.status).toBe(400);
  131|   });
  132| 
  133|   it('serves the static build with an SPA fallback', async () => {
  134|     const res = await fetch(`${base}/some/page`);
  135|     expect(res.status).toBe(200);
  136|     expect(await res.text()).toContain('<title>page</title>');
  137|   });
  138| 
  139|   it('parses the shared bundle example', () => {
  140|     const raw: unknown = JSON.parse(readFileSync(path.join(ROOT, 'tests/fixtures/bundle.example.json'), 'utf8'));
  141|     const b = Bundle.parse(raw);
  142|     expect(Object.keys(b.runs)).toContain('');
  143|     expect(Object.keys(b.tables).sort()).toEqual(Object.keys(b.runs).sort());
  144|   });
  145| });
  146| 
  147| // The intake path: SIMULACRA_LOG on, open to every visitor, a key's name recorded, per-IP limits.
  148| describe('/api/simulacra intake guard', () => {
  149|   const KEY = 'k'.repeat(32);
  150|   const sessions = path.join(scratch, 'intake-sessions');
  151|   let guarded: Server;
  152|   let url = '';
  153| 
  154|   beforeAll(async () => {
  155|     mkdirSync(sessions, { recursive: true });
  156|     const old = new Date(Date.now() - 30 * 86_400_000).toISOString();
  157|     writeFileSync(path.join(sessions, 'requests.jsonl'), `${JSON.stringify({ ts: old, text: 'a month ago' })}\n${JSON.stringify({ ts: new Date().toISOString(), text: 'today' })}\n`);
  158|     const opts: SimulacraOptions = {
  159|       ...options,
  160|       sessions,
  161|       devLog: true,
  162|       keys: parseKeyRing(JSON.stringify({ ana: KEY })),
  163|       limits: { ...DEFAULT_LIMITS, intake: { max: 3, windowMs: 60_000 } }
  164|     };
  165|     guarded = createApp({ simulacra: opts, build: path.join(scratch, 'none') }).listen(0);
  166|     await new Promise<void>((resolve) => guarded.once('listening', resolve));
  167|     // SAFETY: listen(0) on a TCP port always reports an AddressInfo, never a pipe name.
  168|     url = `http://127.0.0.1:${(guarded.address() as AddressInfo).port}/api/simulacra`;
  169|   });
  170| 
  171|   afterAll(async () => {
  172|     await new Promise<void>((resolve) => guarded.close(() => resolve()));
  173|   });
  174| 
  175|   const Unknown = z.looseObject({ unknown: z.string().nullable(), unknownWhy: z.string().optional(), queued: z.unknown().optional() });
  176| 
  177|   async function ask(text: string, key?: string): Promise<{ status: number; result: z.infer<typeof Unknown> | null }> {
  178|     const posted = await fetch(`${url}/runs`, {
  179|       method: 'POST',
  180|       headers: { 'content-type': 'application/json', ...(key ? { authorization: `Bearer ${key}` } : {}) },
  181|       body: JSON.stringify({ year: 1920, text })
  182|     });
  183|     if (posted.status !== 200) return { status: posted.status, result: null };
  184|     const { id } = RunId.parse(await posted.json());
  185|     const got = z.object({ result: Unknown }).parse(await (await fetch(`${url}/runs/${id}`)).json());
  186|     return { status: 200, result: got.result };
  187|   }
  188| 
  189|   const queue = (): string[] => {
  190|     try {
  191|       return readFileSync(path.join(sessions, 'queue.jsonl'), 'utf8').split('\n').filter(Boolean);
  192|     } catch {
  193|       return [];
  194|     }
  195|   };
  196| 
  197|   it('drops session lines older than the retention at startup', () => {
  198|     const lines = readFileSync(path.join(sessions, 'requests.jsonl'), 'utf8');
  199|     expect(lines).not.toContain('a month ago');
  200|     expect(lines).toContain('today');
  201|   });
  202| 
  203|   it('queues text without a key, or with one it does not know, under no name', async () => {
  204|     for (const [text, key] of [['the moon votes', undefined], ['mars votes', 'x'.repeat(32)]] as const) {
  205|       const r = await ask(text, key);
  206|       expect(r.result?.queued).toBeDefined();
  207|       expect(r.result?.unknownWhy).toBeUndefined();
  208|     }
  209|     expect(queue().map((l) => JSON.parse(l))).toEqual([
  210|       expect.objectContaining({ text: 'the moon votes', who: null }),
  211|       expect.objectContaining({ text: 'mars votes', who: null })
  212|     ]);
  213|   });
  214| 
  215|   it("records a valid key's name with its text", async () => {
  216|     const r = await ask('venus votes', KEY);
  217|     expect(r.result?.queued).toBeDefined();
  218|     expect(JSON.parse(queue().at(-1) ?? '{}')).toEqual(expect.objectContaining({ text: 'venus votes', who: 'ana' }));
  219|   });
  220| 
  221|   it('limits how often one IP may queue', async () => {
  222|     expect((await ask('jupiter votes')).status).toBe(429);
  223|     expect(queue()).toHaveLength(3);
  224|   });
  225| 
  226|   it('answers a year outside any election without caching it', async () => {
  227|     const res = await fetch(`${url}/elections/123456`);
  228|     expect(await res.json()).toEqual({ slices: [], whatIfs: [], simulated: false });
  229|   });
  230| });
```

## `serve/simulacra.ts`

```ts
    1| // /api/simulacra: serves precomputed harness bundles in the page's contract.
    2| //
    3| // Bundles are the harness's `published/<year>.json` files (serve/bundles/ by
    4| // default; SIMULACRA_BUNDLES points elsewhere). Everything expensive
    5| // (population draws, the backbone, LLM agents) runs offline. Online work is
    6| // lookup plus arithmetic:
    7| //   - every combination of a year's what-ifs is precomputed (with draws);
    8| //   - typed text is matched to a what-if by keyword, or returned as `unknown`;
    9| //   - hand edits (the page's dragged dots) are applied to the point run's
   10| //     state × group table and re-tallied; an edited run carries no draws, and
   11| //     says so in `howIGotThis`.
   12| // Reading is open to everyone: the demo has to work without an account. Every
   13| // client IP is rate limited (guard.ts).
   14| //
   15| // With SIMULACRA_LOG set (production sets it, and SIMULACRA_AUTORUN):
   16| //   - every POST /runs appends one line to sessions/requests.jsonl
   17| //     (ts, year, text, whatIfs, matched, unknown, combo, exists; no IPs, no ids);
   18| //   - unmatched text is queued in sessions/queue.jsonl for
   19| //     `python -m simharness.run whatif --queue`, with the name of the access key
   20| //     the request carried (SIMULACRA_ACCESS_KEYS), if any, for the spend ledger.
   21| //     Nothing caps the dollars; each IP may queue a few texts an hour (guard.ts);
   22| //   - a queued text holds its run `running` (with the worker's `steps`) when
   23| //     SIMULACRA_AUTORUN=<config path> starts that worker in the background from
   24| //     the repo root (one at a time); otherwise the result says `queued`;
   25| //   - session logs drop lines older than SIMULACRA_RETAIN_DAYS (default 7), and
   26| //     the spend ledger keeps old lines without their `note`, so visitors'
   27| //     words aren't kept for good;
   28| //   - a bundle file that changed on disk is reloaded, so a publish needs no restart.
   29| import { type ChildProcess, spawn } from 'node:child_process';
   30| import { randomUUID } from 'node:crypto';
   31| import { appendFileSync, createWriteStream, existsSync, mkdirSync, readdirSync, readFileSync, statSync } from 'node:fs';
   32| import { homedir } from 'node:os';
   33| import path from 'node:path';
   34| import express, { type ErrorRequestHandler, type RequestHandler, type Router } from 'express';
   35| import type { z } from 'zod';
   36| import {
   37|   Bundle,
   38|   type Edits,
   39|   FIELDS,
   40|   type Field,
   41|   IntakeStatus,
   42|   type PageKey,
   43|   QueueDone,
   44|   QueueFailed,
   45|   type Result,
   46|   RunRequest,
   47|   type Slice,
   48|   type Step,
   49|   type TableRow,
   50|   type Told
   51| } from './bundle';
   52| import { capLog, type KeyRing, type Limit, parseKeyRing, pruneJsonl, RateLimiter } from './guard';
   53| 
   54| const ROOT = path.resolve(import.meta.dirname, '..');
   55| 
   56| export interface SimulacraOptions {
   57|   /** Folder of `<year>.json` bundles. */
   58|   bundles: string;
   59|   /** Where dev logs, the queue and the worker's status live. */
   60|   sessions: string;
   61|   /** Dev logging and queueing (SIMULACRA_LOG). */
   62|   devLog: boolean;
   63|   /** Config path for the background intake worker (SIMULACRA_AUTORUN), relative to `root`. */
   64|   autorun: string | null;
   65|   /** Python with the harness installed (SIMULACRA_PYTHON). */
   66|   python: string;
   67|   /** The repo root: the worker runs `python -m simharness.run` from here. */
   68|   root: string;
   69|   /** Access keys whose names the spend ledger records (SIMULACRA_ACCESS_KEYS). */
   70|   keys: KeyRing;
   71|   /** Days session logs keep a line (SIMULACRA_RETAIN_DAYS). */
   72|   retainDays: number;
   73|   /** Per-IP rate limits. */
   74|   limits: Limits;
   75| }
   76| 
   77| export interface Limits {
   78|   /** Every request to the router. */
   79|   readonly any: Limit;
   80|   /** POST /runs. */
   81|   readonly runs: Limit;
   82|   /** POST /runs whose text would be queued. */
   83|   readonly intake: Limit;
   84| }
   85| 
   86| const MINUTE = 60_000;
   87| // The page polls a run every 300 ms (1 s while a new what-if is modelled).
   88| export const DEFAULT_LIMITS: Limits = {
   89|   any: { max: 1200, windowMs: 10 * MINUTE },
   90|   runs: { max: 120, windowMs: 10 * MINUTE },
   91|   intake: { max: 10, windowMs: 60 * MINUTE }
   92| };
   93| 
   94| export function optionsFromEnv(env: NodeJS.ProcessEnv = process.env): SimulacraOptions {
   95|   return {
   96|     bundles: env.SIMULACRA_BUNDLES || path.join(ROOT, 'serve', 'bundles'),
   97|     sessions: path.join(ROOT, 'sessions'),
   98|     devLog: Boolean(env.SIMULACRA_LOG),
   99|     autorun: env.SIMULACRA_AUTORUN || null,
  100|     python: env.SIMULACRA_PYTHON || path.join(homedir(), '.venvs/simharness/bin/python'),
  101|     root: ROOT,
  102|     keys: parseKeyRing(env.SIMULACRA_ACCESS_KEYS),
  103|     retainDays: env.SIMULACRA_RETAIN_DAYS ? Number(env.SIMULACRA_RETAIN_DAYS) : 7,
  104|     limits: DEFAULT_LIMITS
  105|   };
  106| }
  107| 
  108| /** The result the page receives: a bundle result plus the brief and interviews behind it. */
  109| export type RunResult = Result & {
  110|   told?: Record<string, Told>;
  111|   reading?: Record<string, unknown>[];
  112|   pre?: Record<string, unknown>;
  113|   interview?: { questions: string[] | undefined; byWhatIf: { whatIf: string; answers: unknown[] }[] };
  114|   queued?: { text: string; worker: boolean };
  115|   unknownWhy?: string;
  116| };
  117| 
  118| interface Pending {
  119|   text: string;
  120|   keys: string[];
  121|   edits: Edits;
  122|   /** The name of the access key that queued the text, if any. */
  123|   who: string | null;
  124| }
  125| 
  126| type RunEntry =
  127|   | { state: 'done'; year: number; created: number; key: string; result: RunResult }
  128|   | { state: 'pending'; year: number; created: number; pending: Pending };
  129| 
  130| type Settled =
  131|   | { status: 'running'; steps: Step[] }
  132|   | { status: 'failed'; error: string }
  133|   | { status: 'done'; key: string; result: RunResult };
  134| 
  135| type Totals = Record<PageKey, number>;
  136| 
  137| const RUN_TTL_MS = 60 * 60 * 1000;
  138| const PENDING_MS = 10 * 60 * 1000;
  139| /** Runs held at once; past it the oldest go first. */
  140| const MAX_RUNS = 10_000;
  141| /** The worker's plain-text log is emptied past this (CloudWatch keeps a copy). */
  142| const MAX_WORKER_LOG_BYTES = 20 * 1024 * 1024;
  143| const SESSION_LOGS = ['requests.jsonl', 'queue.jsonl', 'queue-done.jsonl', 'queue-failed.jsonl'];
  144| /** The spend ledger outlives the retention, without the visitor's words in `note`. */
  145| const LEDGER_SCRUB = ['note'];
  146| /** Years a bundle can exist for; any other year is answered without touching the cache. */
  147| const FIRST_YEAR = 1789;
  148| const LAST_YEAR = 2100;
  149| 
  150| const KEYS: readonly PageKey[] = ['A', 'B', 'O'];
  151| 
  152| export const comboKey = (keys: readonly string[]): string => [...new Set(keys)].sort().join('+');
  153| 
  154| const escapeRegExp = (s: string): string => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  155| 
  156| /** Whole words only: compiled what-ifs bring short keywords ("flu" must not match "influence"). */
  157| export function readText(b: Bundle, text: string): { keys: string[]; unknown: string | null } {
  158|   if (!text.trim()) return { keys: [], unknown: null };
  159|   const lower = text.toLowerCase();
  160|   const has = (w: string): boolean => new RegExp(`(^|[^a-z0-9])${escapeRegExp(w)}($|[^a-z0-9])`).test(lower);
  161|   const keys = b.words.filter(({ words }) => words.some(has)).map(({ key }) => key);
  162|   return keys.length ? { keys, unknown: null } : { keys: [], unknown: text };
  163| }
  164| 
  165| function edited(row: Record<Field, number>, e: Edits[string] | undefined): Record<Field, number> {
  166|   const f = Object.fromEntries(FIELDS.map((k) => [k, Math.max(0, row[k] + (e?.[k] ?? 0))]));
  167|   // SAFETY: built from FIELDS, so every Field key is present.
  168|   return f as Record<Field, number>;
  169| }
  170| 
  171| const total = (f: Record<Field, number>): number => FIELDS.reduce((s, k) => s + f[k], 0) || 1;
  172| 
  173| /** Apply hand edits to the point run's state × group table, then re-tally states and EV. */
  174| export function applyEdits(b: Bundle, result: Result, table: readonly TableRow[], edits: Edits): RunResult {
  175|   const byState = new Map<string, Totals>();
  176|   for (const row of table) {
  177|     const f = edited(row, edits[row.slice]);
  178|     const sum = total(f);
  179|     const st = byState.get(row.state) ?? { A: 0, B: 0, O: 0 };
  180|     for (const k of KEYS) st[k] += (row.adults * f[k]) / sum;
  181|     byState.set(row.state, st);
  182|   }
  183|   const ev: Totals = { A: 0, B: 0, O: 0 };
  184|   const states = result.states.map((s) => {
  185|     const v = byState.get(s.code) ?? { A: 0, B: 0, O: 0 };
  186|     const [first = 'A', second = 'B'] = [...KEYS].sort((x, y) => v[y] - v[x]);
  187|     const votes = v.A + v.B + v.O || 1;
  188|     ev[first] += b.ev[s.code] ?? 0;
  189|     return {
  190|       code: s.code,
  191|       won: first,
  192|       flipped: first !== b.historyWinner[s.code],
  193|       margin: Math.round(((v[first] - v[second]) / votes) * 1000) / 10
  194|     };
  195|   });
  196|   const need = Object.values(b.ev).reduce((s, x) => s + x, 0) / 2;
  197|   const winner = KEYS.find((k) => ev[k] > need) ?? null;
  198|   const slices = result.slices.map((s): Slice => {
  199|     const e = edits[s.key];
  200|     if (!e) return s;
  201|     const f = edited(s, e);
  202|     const sum = total(f);
  203|     return { ...s, ...Object.fromEntries(FIELDS.map((k) => [k, f[k] / sum])) };
  204|   });
  205|   const { range: _range, drawsWon: _drawsWon, ...rest } = result;
  206|   return {
  207|     ...rest,
  208|     ev,
  209|     winner,
  210|     states,
  211|     slices,
  212|     howIGotThis: [...(result.howIGotThis ?? []), 'You moved some groups by hand, so this is one run with no range.']
  213|   };
  214| }
  215| 
  216| /** One computed result for a year's what-if keys, or null when the combination wasn't precomputed. */
  217| export function compute(
  218|   b: Bundle,
  219|   keys: readonly string[],
  220|   edits: Edits,
  221|   unknown: string | null
  222| ): { key: string; result: RunResult } | null {
  223|   const key = comboKey(keys);
  224|   const base = b.runs[key];
  225|   if (!base) return null;
  226|   const result = Object.keys(edits).length ? applyEdits(b, base, b.tables[key] ?? [], edits) : base;
  227|   // Additive: the interviews behind each applied what-if, when the bundle has them.
  228|   const byWhatIf = b.interviews.byWhatIf ?? {};
  229|   const interviews = keys.flatMap((k) => {
  230|     const answers = byWhatIf[k];
  231|     return answers ? [{ whatIf: k, answers }] : [];
  232|   });
  233|   // What the voters were told for each applied what-if, and the dated newspaper items in their briefs.
  234|   const told = Object.fromEntries(keys.flatMap((k) => (b.told?.[k] ? [[k, b.told[k]]] : [])));
  235|   return {
  236|     key,
  237|     result: {
  238|       ...result,
  239|       unknown,
  240|       ...(Object.keys(told).length ? { told } : {}),
  241|       ...(b.reading?.length ? { reading: b.reading } : {}),
  242|       ...(b.pre ? { pre: b.pre } : {}),
  243|       ...(interviews.length ? { interview: { questions: b.interviews.questions, byWhatIf: interviews } } : {})
  244|     }
  245|   };
  246| }
  247| 
  248| const norm = (t: string): string => t.toLowerCase().split(/\s+/).filter(Boolean).join(' ');
  249| 
  250| function readJsonl<T>(file: string, schema: z.ZodType<T>): T[] {
  251|   let text: string;
  252|   try {
  253|     text = readFileSync(file, 'utf8');
  254|   } catch {
  255|     return [];
  256|   }
  257|   return text
  258|     .split('\n')
  259|     .filter(Boolean)
  260|     .flatMap((line) => {
  261|       try {
  262|         const parsed = schema.safeParse(JSON.parse(line));
  263|         return parsed.success ? [parsed.data] : [];
  264|       } catch {
  265|         return [];
  266|       }
  267|     });
  268| }
  269| 
  270| /** A year's answer at a URL that names its run never changes. */
  271| export const IMMUTABLE = 'public, max-age=31536000, s-maxage=31536000, immutable';
  272| /** Unversioned answers and the manifest: a minute fresh, then revalidated. */
  273| export const SHORT_CACHE = 'public, max-age=60, s-maxage=60, stale-while-revalidate=300';
  274| 
  275| export function createSimulacraRouter(opts: SimulacraOptions = optionsFromEnv()): Router {
  276|   const bundles = new Map<number, { bundle: Bundle | null; mtime: number }>();
  277|   const runs = new Map<string, RunEntry>();
  278|   let worker: ChildProcess | null = null;
  279|   let queuedWhileBusy = false;
  280| 
  281|   const mtimeOf = (file: string): number => (existsSync(file) ? statSync(file).mtimeMs : 0);
  282| 
  283|   function loadBundle(year: number): Bundle | null {
  284|     if (!Number.isInteger(year) || year < FIRST_YEAR || year > LAST_YEAR) return null;
  285|     const file = path.join(opts.bundles, `${year}.json`);
  286|     const cached = bundles.get(year);
  287|     if (cached && (!opts.devLog || cached.mtime === mtimeOf(file))) return cached.bundle;
  288|     let bundle: Bundle | null = null;
  289|     if (existsSync(file)) {
  290|       const parsed = Bundle.safeParse(JSON.parse(readFileSync(file, 'utf8')));
  291|       if (parsed.success) bundle = parsed.data;
  292|       else console.warn(`simulacra: ${file} doesn't fit the bundle contract`, parsed.error.issues.slice(0, 3));
  293|     }
  294|     bundles.set(year, { bundle, mtime: mtimeOf(file) });
  295|     return bundle;
  296|   }
  297| 
  298|   function appendLine(name: string, row: unknown): void {
  299|     try {
  300|       mkdirSync(opts.sessions, { recursive: true });
  301|       appendFileSync(path.join(opts.sessions, name), `${JSON.stringify(row)}\n`);
  302|     } catch (e) {
  303|       console.warn('simulacra: session log failed', e instanceof Error ? e.message : e);
  304|     }
  305|   }
  306| 
  307|   function startWorker(): void {
  308|     if (!opts.autorun) return;
  309|     if (worker) {
  310|       queuedWhileBusy = true;
  311|       return;
  312|     }
  313|     queuedWhileBusy = false;
  314|     mkdirSync(opts.sessions, { recursive: true });
  315|     const child = spawn(opts.python, ['-m', 'simharness.run', 'whatif', '--queue', '--limit', '5', '--config', opts.autorun], {
  316|       cwd: opts.root,
  317|       stdio: ['ignore', 'pipe', 'pipe']
  318|     });
  319|     const out = createWriteStream(path.join(opts.sessions, 'intake.log'), { flags: 'a' });
  320|     child.stdout?.pipe(out);
  321|     child.stderr?.pipe(out);
  322|     child.on('error', (e) => out.write(`simulacra: worker failed to start: ${e.message}\n`));
  323|     // Text typed while a worker ran is picked up by a fresh one (a worker that
  324|     // stopped on a cap leaves its text queued and isn't restarted by itself).
  325|     child.on('exit', () => {
  326|       worker = null;
  327|       if (queuedWhileBusy) startWorker();
  328|     });
  329|     worker = child;
  330|   }
  331| 
  332|   // Runs are added in creation order (an entry replaced in place keeps its
  333|   // slot), so the oldest are at the front: pruning stops at the first live one.
  334|   function newRun(entry: RunEntry): string {
  335|     const id = randomUUID();
  336|     runs.set(id, entry);
  337|     for (const [k, r] of runs) {
  338|       if (Date.now() - r.created <= RUN_TTL_MS && runs.size <= MAX_RUNS) break;
  339|       runs.delete(k);
  340|     }
  341|     return id;
  342|   }
  343| 
  344|   // Session logs keep SIMULACRA_RETAIN_DAYS of lines. The worker appends to
  345|   // them, so they're rewritten only while no worker runs.
  346|   function prune(): void {
  347|     if (!opts.devLog || worker) return;
  348|     const maxAge = opts.retainDays * 24 * 60 * MINUTE;
  349|     for (const name of [...SESSION_LOGS, 'spend.jsonl']) {
  350|       try {
  351|         const scrub = name === 'spend.jsonl' ? LEDGER_SCRUB : undefined;
  352|         const n = pruneJsonl(path.join(opts.sessions, name), maxAge, Date.now(), scrub);
  353|         if (n) console.log(`simulacra: ${scrub ? 'scrubbed' : 'dropped'} ${n} lines older than ${opts.retainDays} days in ${name}`);
  354|       } catch (e) {
  355|         console.warn(`simulacra: pruning ${name} failed`, e instanceof Error ? e.message : e);
  356|       }
  357|     }
  358|     capLog(path.join(opts.sessions, 'intake.log'), MAX_WORKER_LOG_BYTES);
  359|   }
  360|   prune();
  361|   setInterval(prune, 60 * MINUTE).unref();
  362| 
  363|   const limiters = {
  364|     any: new RateLimiter(opts.limits.any),
  365|     runs: new RateLimiter(opts.limits.runs),
  366|     intake: new RateLimiter(opts.limits.intake)
  367|   };
  368|   const limited = (res: express.Response, retryAfterS: number): void => {
  369|     res.set('Retry-After', String(retryAfterS)).status(429).json({ error: 'Too many requests just now. Try again in a few minutes.' });
  370|   };
  371|   const rateLimit =
  372|     (which: keyof typeof limiters): RequestHandler =>
  373|     (req, res, next) => {
  374|       const a = limiters[which].admit(req.ip ?? 'unknown');
  375|       if (a.ok) next();
  376|       else limited(res, a.retryAfterS);
  377|     };
  378| 
  379|   // Where the worker is with a pending run's text.
  380|   function settle(r: Extract<RunEntry, { state: 'pending' }>): Settled {
  381|     const t = norm(r.pending.text);
  382|     const sameYear = (x: { year?: number | null }): boolean => (x.year ?? 1920) === r.year;
  383|     const outcome = readJsonl(path.join(opts.sessions, 'queue-done.jsonl'), QueueDone)
  384|       .filter((x) => x.text === t && sameYear(x))
  385|       .pop();
  386|     const failed = readJsonl(path.join(opts.sessions, 'queue-failed.jsonl'), QueueFailed)
  387|       .filter((x) => x.text === t && sameYear(x) && x.at * 1000 >= r.created)
  388|       .pop();
  389|     const b = loadBundle(r.year);
  390|     if (outcome && (outcome.status === 'modelled' || outcome.status === 'keyword') && outcome.key && b) {
  391|       const done =
  392|         compute(b, [...new Set([...r.pending.keys, outcome.key])], r.pending.edits, null) ??
  393|         compute(b, [outcome.key], r.pending.edits, null);
  394|       if (done) return { status: 'done', key: done.key, result: done.result };
  395|       return { status: 'failed', error: 'The new what-if was modelled, but not in this combination. Try it on its own.' };
  396|     }
  397|     const stopped = outcome ?? failed;
  398|     if (stopped) {
  399|       // Not modellable, or the worker stopped: the run finishes unchanged, saying why.
  400|       const done = b ? compute(b, r.pending.keys, r.pending.edits, r.pending.text) : null;
  401|       const why = stopped.why ?? '';
  402|       if (!done) return { status: 'failed', error: why || 'Couldn’t model that.' };
  403|       return { status: 'done', key: done.key, result: { ...done.result, unknownWhy: why } };
  404|     }
  405|     if (Date.now() - r.created > PENDING_MS) return { status: 'failed', error: 'Modelling that took too long. Try again in a minute.' };
  406|     if (!worker) startWorker();
  407|     let steps: Step[] = [{ text: 'Waiting for the what-ifs typed before this one.', state: 'doing' }];
  408|     try {
  409|       const st = IntakeStatus.safeParse(JSON.parse(readFileSync(path.join(opts.sessions, 'intake-status.json'), 'utf8')));
  410|       if (st.success && st.data.text === t) steps = st.data.steps;
  411|     } catch {
  412|       // not started
  413|     }
  414|     return { status: 'running', steps: [{ text: `Reading “${r.pending.text}”: it’s new to me.`, state: 'done' }, ...steps] };
  415|   }
  416| 
  417|   const router = express.Router();
  418|   router.use(rateLimit('any'));
  419|   router.use(express.json({ limit: '64kb' }));
  420| 
  421|   // Every published year and the run its bundle came from. The page reads it
  422|   // first and asks for each year at /elections/<year>?v=<runId>, so a year's
  423|   // answer can be cached for good: a new run means a new URL.
  424|   router.get('/manifest', (_req, res) => {
  425|     const years: Record<string, string> = {};
  426|     const files = existsSync(opts.bundles) ? readdirSync(opts.bundles) : [];
  427|     for (const f of files.filter((name) => /^\d{4}\.json$/.test(name)).sort()) {
  428|       const b = loadBundle(Number(f.slice(0, 4)));
  429|       if (b) years[f.slice(0, 4)] = b.runId;
  430|     }
  431|     res.set('Cache-Control', SHORT_CACHE).json({ years });
  432|   });
  433| 
  434|   // A year without a bundle answers 200 with `simulated: false`, not 404: the
  435|   // page reads a 404 before any answer as "there is no simulation service".
  436|   router.get('/elections/:year', (req, res) => {
  437|     const b = loadBundle(Number(req.params.year));
  438|     if (!b) {
  439|       res.set('Cache-Control', SHORT_CACHE).json({ slices: [], whatIfs: [], simulated: false });
  440|       return;
  441|     }
  442|     // Immutable only when the URL names the run being served.
  443|     res.set('Cache-Control', req.query.v === b.runId ? IMMUTABLE : SHORT_CACHE);
  444|     res.json({ ...b.election, simulated: true, runId: b.runId });
  445|   });
  446| 
  447|   router.post('/runs', rateLimit('runs'), (req, res) => {
  448|     const body = RunRequest.safeParse(req.body ?? {});
  449|     if (!body.success) {
  450|       res.status(400).json({ error: 'bad request', issues: body.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`) });
  451|       return;
  452|     }
  453|     const { year, whatIfs, text, edits } = body.data;
  454|     const b = loadBundle(year);
  455|     if (!b) {
  456|       res.status(404).json({ error: 'no simulation for this year' });
  457|       return;
  458|     }
  459|     const known = new Set(b.election.whatIfs.map((w) => w.key));
  460|     const chosen = whatIfs.filter((k) => known.has(k));
  461|     const read = readText(b, text);
  462|     const keys = [...chosen, ...read.keys];
  463|     const done = compute(b, keys, edits, read.unknown);
  464|     let queued = false;
  465|     // The access key's name, if the request carried one: the spend ledger records it.
  466|     let who: string | null = null;
  467|     if (opts.devLog) {
  468|       const ts = new Date().toISOString();
  469|       appendLine('requests.jsonl', { ts, year, text, whatIfs, matched: read.keys, unknown: read.unknown, combo: comboKey(keys), exists: Boolean(done) });
  470|       if (read.unknown) {
  471|         const a = limiters.intake.admit(req.ip ?? 'unknown');
  472|         if (!a.ok) {
  473|           limited(res, a.retryAfterS);
  474|           return;
  475|         }
  476|         who = opts.keys.identify(req.get('authorization'));
  477|         appendLine('queue.jsonl', { ts, year, text: read.unknown, who });
  478|         queued = true;
  479|         startWorker();
  480|       }
  481|     }
  482|     // With the worker on, new words hold the run open (GET reports the
  483|     // worker's steps) until they are compiled, researched, interviewed and
  484|     // published; then the run finishes with the new what-if applied.
  485|     if (queued && read.unknown && opts.autorun) {
  486|       const pending = { text: read.unknown, keys: chosen, edits, who };
  487|       res.json({ id: newRun({ state: 'pending', year, created: Date.now(), pending }) });
  488|       return;
  489|     }
  490|     if (!done) {
  491|       res.status(422).json({ error: 'That combination has not been computed.' });
  492|       return;
  493|     }
  494|     let result: RunResult = done.result;
  495|     if (queued && read.unknown) result = { ...result, queued: { text: read.unknown, worker: Boolean(worker) } };
  496|     res.json({ id: newRun({ state: 'done', year, created: Date.now(), key: done.key, result }) });
  497|   });
  498| 
  499|   router.get('/runs/:id', (req, res) => {
  500|     const r = runs.get(req.params.id);
  501|     if (!r) {
  502|       res.status(404).json({ error: 'no such run' });
  503|       return;
  504|     }
  505|     let result: RunResult;
  506|     if (r.state === 'pending') {
  507|       const s = settle(r);
  508|       if (s.status === 'running') {
  509|         res.json({ status: 'running', done: 0, total: 0, error: null, steps: s.steps });
  510|         return;
  511|       }
  512|       if (s.status === 'failed') {
  513|         runs.delete(req.params.id);
  514|         res.json({ status: 'failed', error: s.error });
  515|         return;
  516|       }
  517|       runs.set(req.params.id, { state: 'done', year: r.year, created: r.created, key: s.key, result: s.result });
  518|       result = s.result;
  519|     } else {
  520|       result = r.result;
  521|     }
  522|     const count = result.states.length;
  523|     res.json({ status: 'done', done: count, total: count, error: null, result });
  524|   });
  525| 
  526|   router.post('/runs/:id/cancel', (req, res) => {
  527|     runs.delete(req.params.id);
  528|     res.json({ ok: true });
  529|   });
  530| 
  531|   router.get('/elections/:year/voters/:slice', (req, res) => {
  532|     const b = loadBundle(Number(req.params.year));
  533|     if (!b) {
  534|       res.status(404).json({ error: 'no simulation for this year' });
  535|       return;
  536|     }
  537|     const run = typeof req.query.run === 'string' ? runs.get(req.query.run) : undefined;
  538|     const key = run?.state === 'done' ? run.key : '';
  539|     const voter = b.voters[key]?.[req.params.slice] ?? b.voters['']?.[req.params.slice];
  540|     if (!voter) {
  541|       res.status(404).json({ error: 'no voter for this group' });
  542|       return;
  543|     }
  544|     res.json(voter);
  545|   });
  546| 
  547|   // A body that isn't JSON answers in JSON too.
  548|   const onError: ErrorRequestHandler = (err: unknown, _req, res, next) => {
  549|     if (res.headersSent) {
  550|       next(err);
  551|       return;
  552|     }
  553|     const status = err instanceof SyntaxError ? 400 : 500;
  554|     res.status(status).json({ error: status === 400 ? 'bad request' : 'server error' });
  555|   };
  556|   router.use(onError);
  557| 
  558|   return router;
  559| }
```

## `simharness/__init__.py`

```python
    1| """Simulacra Americana simulation harness.
    2| 
    3| A calibrated statistical backbone decides the counts; LLM agents supply the
    4| counterfactual response (as a within-agent paired difference) and the quotes.
    5| See ../METHOD.md.
    6| """
```

## `simharness/agentlayer.py`

```python
    1| """Builds every model request for a run (control, counterfactuals, label swap,
    2| recall probe, second-model check) and reads the answers back.
    3| 
    4| Request id: <arm>|<agent id>|<model short>   arm ∈ control, cf:<what-if>, swap, probe
    5| """
    6| from __future__ import annotations
    7| 
    8| import random
    9| 
   10| from . import prompts, scenario, world
   11| from .agents import persona_lines, sample_agents
   12| from .geo import SOUTH, STATE_NAME
   13| from .whatifs import ELECTION_YEARS  # noqa: F401 (re-exported: the table of election years)
   14| 
   15| SHORT = {'claude-sonnet-5-5': 'sonnet', 'claude-opus-5-5': 'opus', 'claude-haiku-4-5': 'haiku'}
   16| 
   17| R_DESCRIPTOR = 'nominee of the party that has held a majority in Congress since the 1918 elections'
   18| D_DESCRIPTOR = 'nominee of the party of the administration in office since 1913'
   19| 
   20| 
   21| ORDER_1920 = ['League of Nations', 'cost of living', 'labor', 'agriculture', 'women', 'immigration', 'Prohibition']
   22| 
   23| 
   24| def party_planks(platforms: dict, party: str, drop_topics: set = frozenset(), k: int = 3, order: list = ORDER_1920) -> list[str]:
   25|     """The control's k planks, minus any dropped topic (never replaced, so a
   26|     counterfactual ballot differs from the control only by the change)."""
   27|     planks = [p for p in platforms.get('planks', []) if p['party'] == party
   28|               and 'silent' not in p['neutral_paraphrase'].lower()]
   29|     planks.sort(key=lambda p: next((i for i, t in enumerate(order) if t.lower() in p['topic'].lower()), 99))
   30|     planks = [p for p in planks[:k] if not any(d.lower() in p['topic'].lower() for d in drop_topics)]
   31|     return [p['neutral_paraphrase'].rstrip('.') + '.' for p in planks]
   32| 
   33| 
   34| # ── Eras: what the five backbone slots mean, and how briefs and the page name them ──
   35| #
   36| # The backbone always has five groups per state × sex. Their meaning shifts:
   37| #   early    1789–1864  white men (no nativity before 1850); Black adults free and enslaved;
   38| #                       American Indians (rarely citizens)
   39| #   classic  1868–1968  the 1920 meanings (native-born white, naturalized, alien, Black, other)
   40| #   modern   1972–      native_white = white non-Hispanic US-born; foreign_white_naturalized =
   41| #                       naturalized citizens of any race; foreign_white_alien = noncitizens;
   42| #                       black = Black US-born; other = US-born Hispanic, Asian, American Indian
   43| #                       and others
   44| SLAVE_STATES = {'AL', 'AR', 'DE', 'FL', 'GA', 'KY', 'LA', 'MD', 'MS', 'MO', 'NC', 'SC', 'TN', 'TX', 'VA', 'DC'}
   45| # [I] Modern 'other' (US-born, not white non-Hispanic, not Black): persona origin only, never counted.
   46| OTHER_ORIGIN = {'Hispanic': 0.6, 'Asian American': 0.15, 'American Indian': 0.1, 'multiracial': 0.15}
   47| # [I] Share of adults barred by a felony conviction (Uggen, Larson & Shannon / Sentencing Project
   48| # national estimates, rounded; Black adults about 3.5×). Used only to decide a persona's line,
   49| # never counted. A state table in franchise['felony_share'] replaces it.
   50| FELONY_SHARE = {1972: 0.008, 1976: 0.008, 1980: 0.009, 1984: 0.010, 1988: 0.012, 1992: 0.014, 1996: 0.017,
   51|                 2000: 0.023, 2004: 0.024, 2008: 0.024, 2012: 0.025, 2016: 0.025, 2020: 0.023, 2024: 0.017}
   52| NO_FELONY_BAN = {'ME', 'VT', 'DC'}
   53| 
   54| 
   55| def era(year: int) -> str:
   56|     return 'early' if year < 1868 else 'modern' if year >= 1972 else 'classic'
   57| 
   58| 
   59| def groups_for(year: int = 1920) -> dict:
   60|     """The one table of era meanings: persona words, cohort labels, page slice labels,
   61|     which groups are interviewed, and the phrase prompts use for the groups."""
   62|     from .agents import GROUP_WORDS
   63|     from .cohorts import GROUP_LABEL
   64|     from .serialize import SLICES
   65|     e = era(year)
   66|     if e == 'classic':
   67|         return {'era': e, 'words': dict(GROUP_WORDS), 'labels': dict(GROUP_LABEL), 'slices': dict(SLICES),
   68|                 'interview': ['native_white', 'foreign_white_naturalized', 'foreign_white_alien', 'black'],
   69|                 'phrase': 'native-born white, naturalized immigrant, non-citizen immigrant and Black',
   70|                 'min_age': 21}
   71|     if e == 'early':
   72|         nativity = year >= 1850
   73|         return {'era': e,
   74|                 'words': {'native_white': 'a white {noun} born in the United States' if nativity else 'a white {noun}',
   75|                           'foreign_white_naturalized': 'a white {noun} born abroad and naturalized as a United States citizen',
   76|                           'foreign_white_alien': 'a white {noun} born abroad who is not a United States citizen',
   77|                           'black': 'a Black {noun}', 'other': 'an American Indian {noun}'},
   78|                 'labels': {'native_white': 'native-born white' if nativity else 'white',
   79|                            'foreign_white_naturalized': 'naturalized immigrant', 'foreign_white_alien': 'immigrant non-citizen',
   80|                            'black': 'Black (free and enslaved)', 'other': 'American Indian'},
   81|                 'slices': {**dict(SLICES), 'black-south': 'Black Southerners, most of them enslaved'},
   82|                 'interview': ['native_white', 'foreign_white_naturalized', 'foreign_white_alien', 'black'],
   83|                 'phrase': ('native-born white, naturalized immigrant, non-citizen immigrant and Black (free and enslaved)'
   84|                            if nativity else 'white and Black (free and enslaved); there is no nativity before 1850'),
   85|                 'min_age': 21}
   86|     return {'era': e,
   87|             'words': {'native_white': 'a non-Hispanic white {noun} born in the United States',
   88|                       'foreign_white_naturalized': 'a {noun} born abroad and naturalized as a United States citizen',
   89|                       'foreign_white_alien': 'a {noun} born abroad who is not a United States citizen',
   90|                       'black': 'a Black {noun} born in the United States',
   91|                       'other': 'a {origin} {noun} born in the United States'},
   92|             'labels': {'native_white': 'US-born non-Hispanic white', 'foreign_white_naturalized': 'naturalized citizen',
   93|                        'foreign_white_alien': 'noncitizen', 'black': 'US-born Black',
   94|                        'other': 'US-born Hispanic, Asian, American Indian and other'},
   95|             'slices': {'men': 'Men outside the South (citizens)', 'women': 'Women outside the South (citizens)',
   96|                        'south-white': 'White and other Southerners (citizens)', 'black-south': 'Black Southerners (US-born)',
   97|                        'immigrants': 'Noncitizens'},
   98|             'interview': ['native_white', 'foreign_white_naturalized', 'foreign_white_alien', 'black', 'other'],
   99|             'phrase': ('US-born non-Hispanic white, naturalized citizens of any race, noncitizens, US-born Black, and '
  100|                        'US-born Hispanic, Asian, American Indian and other'),
  101|             'min_age': 18}
  102| 
  103| 
  104| def _draw(agent: dict, what: str) -> float:
  105|     return random.Random(f'{agent["id"]}:{what}').random()
  106| 
  107| 
  108| def describe_agent(agent: dict, fr: dict, year: int, inp=None):
  109|     """Era facts about one invented person that the cohort doesn't fix (status, origin).
  110|     Classic years add nothing, so their agents and briefs are unchanged."""
  111|     e = era(year)
  112|     if e == 'early' and agent['group'] == 'black':
  113|         es = (fr.get('enslaved_share') or getattr(inp, 'enslaved_share', None) or {}).get(agent['state'])
  114|         if es is not None:
  115|             agent['status'] = 'enslaved' if _draw(agent, 'enslaved') < es else 'free'
  116|         else:
  117|             agent['status'] = 'free' if agent['state'] not in SLAVE_STATES else 'unknown'
  118|     if e == 'modern' and agent['group'] == 'other':
  119|         u, acc = _draw(agent, 'origin'), 0.0
  120|         for k, w in OTHER_ORIGIN.items():
  121|             acc += w
  122|             if u < acc:
  123|                 agent['origin'] = k
  124|                 break
  125|         else:
  126|             agent['origin'] = 'multiracial'
  127|     return agent
  128| 
  129| 
  130| def _felony(agent: dict, fr: dict, year: int) -> bool:
  131|     if agent['state'] in NO_FELONY_BAN:
  132|         return False
  133|     tab = fr.get('felony_share') or {}
  134|     p = tab.get(agent['state'])
  135|     if p is None:
  136|         p = FELONY_SHARE.get(year, FELONY_SHARE[min(FELONY_SHARE, key=lambda y: abs(y - year))])
  137|         if agent['group'] == 'black':
  138|             p *= 3.5
  139|         if agent['sex'] == 'F':
  140|             p *= 0.25
  141|     return _draw(agent, 'felony') < p
  142| 
  143| 
  144| def eligibility_line(agent: dict, fr: dict, year: int = 1920, inp=None) -> str:
  145|     s, name = agent['state'], STATE_NAME.get(agent['state'], agent['state'])
  146|     e = era(year)
  147|     table = fr['table']
  148|     poll = bool(table.loc[s].get('poll_tax', 0)) if s in table.index else False
  149|     lit = bool(table.loc[s].get('literacy_test', 0)) if s in table.index else False
  150|     if year < 1890:
  151|         poll = lit = False  # the franchise table describes the disfranchisement era (data has no earlier devices)
  152|     if year >= 1964:
  153|         poll = False  # Twenty-fourth Amendment
  154|     if year >= (1968 if s in SOUTH else 1972):
  155|         lit = False  # Voting Rights Act (1965), nationwide ban (1970)
  156|     alien_ok = fr.get('alien_voting', set()) if year < 1928 else set()
  157|     no_popular = set(getattr(inp, 'no_popular', None) or fr.get('no_popular') or ())
  158|     if s in no_popular:
  159|         return f'The {name} legislature chooses the state\'s presidential electors, so no one in {name} votes for president this year.'
  160|     if agent['group'] == 'foreign_white_alien' and s not in alien_ok:
  161|         return 'This person is not a United States citizen and cannot vote.'
  162|     if agent['sex'] == 'F' and s in fr.get('closed_1920', ()) and year == 1920:
  163|         return f'Registration in {name} closed before women could enrol, so this person cannot vote for president this year.'
  164|     if agent['group'] == 'other' and e != 'modern':
  165|         oc = (getattr(inp, 'other_citizen', None) or {}).get(s, 1.0 if year >= 1924 else 0.0)
  166|         if year < 1924 and _draw(agent, 'citizen') >= oc:
  167|             return 'This person is not counted a United States citizen, and cannot vote.'
  168|     if agent['sex'] == 'F' and year < 1920:
  169|         wv = set(getattr(inp, 'women_vote', None) or ())
  170|         pres = fr.get('pres_year', {})
  171|         if not wv:
  172|             wv = {x for x, y in pres.items() if y and y == y and int(y) <= year}
  173|         if s not in wv:
  174|             return f'Women cannot vote for president in {name}.'
  175|     if e == 'early' and agent['group'] == 'black':
  176|         if agent.get('status') == 'enslaved':
  177|             return 'This person is enslaved and cannot vote.'
  178|         bc = (getattr(inp, 'black_can', None) or {}).get(s)
  179|         if bc is None:
  180|             bc = 0.0 if s in SLAVE_STATES else 1.0
  181|         es = (fr.get('enslaved_share') or getattr(inp, 'enslaved_share', None) or {}).get(s)
  182|         free_can = min(1.0, bc / max(1e-9, 1 - es)) if es is not None and agent.get('status') == 'free' else bc
  183|         if free_can <= 0:
  184|             return f'{name} law does not let Black people vote.'
  185|         if free_can < 1 and _draw(agent, 'legal') >= free_can:
  186|             return f'{name} law lets few Black men vote (a property requirement, or the right to vote taken away), and this person cannot vote.'
  187|     parts = []
  188|     devices = ' and '.join(x for x, on in (('a poll tax', poll), ('a literacy or "understanding" test', lit)) if on)
  189|     if agent['group'] == 'black' and s in SOUTH and 1868 <= year < 1972:
  190|         if year <= 1876:
  191|             return (f'This person is a citizen. Black men in {name} have registered and voted since 1867, though threats '
  192|                     'and violence have kept many from the polls in some counties.')
  193|         if year < 1890:
  194|             return ('This person is a citizen and the law lets them vote, but in this county fraud, threats and violence '
  195|                     'keep many Black men from the polls.')
  196|         if year >= 1968:
  197|             return (f'This person can vote. Since the Voting Rights Act of 1965, Black citizens in {name} register and vote '
  198|                     'in growing numbers.')
  199|         line = 'This person is a citizen.'
  200|         if devices:
  201|             line += f' {name} requires {devices} to register,'
  202|         else:
  203|             line += f' In {name}'
  204|         return line + ' and in this county few Black citizens have been allowed to register or vote.'
  205|     if e == 'early' and agent['group'] != 'black' and agent['sex'] == 'M':
  206|         wc = (getattr(inp, 'white_can', None) or {}).get(s, 1.0)
  207|         if wc < 1:
  208|             if _draw(agent, 'legal') >= wc:
  209|                 return f'{name} lets only men who own property or pay taxes vote, and this person does not qualify, so cannot vote.'
  210|             parts.append(f'{name} lets only men who own property or pay taxes vote; this person qualifies and can vote.')
  211|     if e == 'modern' and _felony(agent, fr, year):
  212|         return f'This person is a citizen, but a felony conviction bars them from voting under {name} law.'
  213|     if parts:
  214|         pass
  215|     elif agent['sex'] == 'F' and year < 1920:
  216|         y = fr.get('pres_year', {}).get(s)
  217|         if y and y == y and int(y) <= year - 4:
  218|             parts.append(f'Women have voted for president in {name} since {int(y)}.')
  219|         elif y and y == y and int(y) <= year:
  220|             parts.append(f'{name} law gave women the vote for president in {int(y)}, so this is the first presidential '
  221|                          'election this person can vote in.')
  222|         else:
  223|             parts.append(f'{name} law lets women who meet its requirements vote, and this person can vote.')
  224|     elif e == 'modern':
  225|         if agent.get('age', 99) < 21:
  226|             parts.append('Since the Twenty-sixth Amendment lowered the voting age to 18 in 1971, this person can vote.')
  227|         else:
  228|             parts.append('This person can vote.')
  229|     elif agent['sex'] == 'F' and year > 1920:
  230|         y = fr['pres_year'].get(s)
  231|         since = int(y) if s in fr['women_pre19'] and y and y == y and int(y) <= 1920 else 1920
  232|         parts.append(f'Women have voted for president in {name} since {since}.')
  233|     elif agent['sex'] == 'F':
  234|         y = fr['pres_year'].get(s)
  235|         if s in fr['women_pre19'] and y and y == y and int(y) <= 1916:
  236|             parts.append(f'Women have voted for president in {name} since {int(y)}.')
  237|         elif s in fr['women_pre19'] and y and y == y:
  238|             # No presidential election fell between 1917 and 1919.
  239|             parts.append(f'{name} law gave women the vote for president in {int(y)}, so this is the first presidential '
  240|                          'election this person can vote in.')
  241|         else:
  242|             parts.append('With the suffrage amendment ratified in August, this person can vote for president for the first time.')
  243|     else:
  244|         parts.append('This person can vote.')
  245|     if devices:
  246|         parts.append(f'{name} requires {devices} to vote.')
  247|     return ' '.join(parts)
  248| 
  249| 
  250| def items_for(agent: dict, drop_topics=frozenset(), drop_after: str | None = None) -> list[dict]:
  251|     out = []
  252|     for it in agent['items']:
  253|         if it['identifying']:
  254|             continue
  255|         if it['topic'] in drop_topics and (drop_after is None or it['date'] >= drop_after):
  256|             continue
  257|         out.append(it)
  258|     return out
  259| 
  260| 
  261| def build_requests(cfg, cohorts: dict, extras: dict, inp, registry: dict) -> tuple[list, list]:
  262|     ag = cfg.agents
  263|     fr, corpus, platforms = extras['franchise'], [c for c in extras['corpus'] if not c['identifying']], extras['platforms']
  264|     prof = extras.get('profile') or {'year': 1920, 'descriptors': {'R': R_DESCRIPTOR, 'D': D_DESCRIPTOR}, 'third': None,
  265|                                      'label_pool': prompts.LABEL_POOL, 'others_line': prompts.OTHERS_1920,
  266|                                      'plank_order': ORDER_1920, 'day_phrase': 'Tuesday, 2 November'}
  267|     # An unopposed year (1789, 1792, 1820) has no second line: its descriptor is null.
  268|     keys = [k for k in ('R', 'D') if prof['descriptors'].get(k)] + ([prof['third']] if prof['third'] else [])
  269|     year = prof['year']
  270|     era_groups = groups_for(year)
  271|     qs = prompts.questions(prof['day_phrase'])
  272|     agents, reqs = [], []
  273|     asof = cfg.context_cutoff  # p1 used '1920-10-30' with items to 1 Nov
  274|     no_popular = set(getattr(inp, 'no_popular', None) or ())
  275|     this_year = [wk for wk in cfg.what_ifs if wk in registry and registry[wk]['facts'] is not None
  276|                  and year in (registry[wk].get('years') or [registry[wk].get('year', 1920)])]
  277|     facts_failed: set[str] = set()
  278| 
  279|     def can_vote_somewhere(a: dict) -> bool:
  280|         """D33: whether this person can vote in the world as it was or in some what-if's world."""
  281|         describe_agent(a, fr, year, inp)
  282|         if not world.barred(eligibility_line(a, fr, year, inp)):
  283|             return True
  284|         for wk in this_year:
  285|             try:
  286|                 e = registry[wk]['facts'](a, inp, year=year).get('eligibility')
  287|             except Exception as err:  # a compiled what-if's facts; one failing mustn't stop the draw
  288|                 if wk not in facts_failed:
  289|                     facts_failed.add(wk)
  290|                     print(f'plan: {wk} facts failed for {a.get("state")}/{a.get("group")} ({err!r}); '
  291|                           'its world is ignored when deciding who can vote', flush=True)
  292|                 continue
  293|             if e and not world.barred(e):
  294|                 return True
  295|         return False
  296| 
  297|     def draw(key: str) -> list[dict]:
  298|         """The people interviewed in one cohort (none where no one can be)."""
  299|         co = cohorts[key]
  300|         if co['group'] not in era_groups['interview']:
  301|             return []  # 1868–1968: too few adults per region for a cohort; counted by the backbone only
  302|         if no_popular:
  303|             # No one votes for president where the legislature chose the electors: nobody to interview there.
  304|             by_state = {s: n for s, n in co['adults_by_state'].items() if s not in no_popular}
  305|             if not by_state:
  306|                 return []
  307|             co = {**co, 'adults_by_state': by_state}
  308|         if not ag.replace_barred:
  309|             return sample_agents(co, ag.per_cohort, corpus, cfg.seed, extras['urban'], year=year, min_age=era_groups['min_age'])
  310|         # D33: a slot spent on someone who can't vote in either world measures nothing (the
  311|         # backbone already counts them as barred), so draw on until per_cohort people can.
  312|         # The first draws are the same people as before; the cohort's effect then describes
  313|         # the people it can move, which is where the backbone applies it.
  314|         pool = sample_agents(co, ag.per_cohort * 8, corpus, cfg.seed, extras['urban'], year=year, min_age=era_groups['min_age'])
  315|         got = [a for a in pool if can_vote_somewhere(a)][:ag.per_cohort]
  316|         for a in got:
  317|             a['weight'] = co['adults'] / len(got)
  318|         return got
  319| 
  320|     for key in sorted(cohorts):
  321|         if not ag.only_cohorts or key in ag.only_cohorts:
  322|             agents += draw(key)
  323| 
  324|     # D33: the groups a staged what-if names as decisive are interviewed for it even when
  325|     # only_cohorts leaves them out. The focus_cohorts slots go round the named groups in turn
  326|     # (newest what-if first; within a group, its largest cohort first), so every named group
  327|     # is reached before any gets a second; a cohort no one in which can vote takes no slot.
  328|     if ag.focus_cohorts and ag.only_cohorts:
  329|         queues = []
  330|         for wk in reversed(this_year):
  331|             for f in (registry[wk].get('world') or {}).get('focus') or []:
  332|                 queues.append((wk, sorted((k for k, c in cohorts.items() if k not in ag.only_cohorts
  333|                                            and c['group'] != 'foreign_white_alien' and world.cohort_matches(c, f)),
  334|                                           key=lambda k: -cohorts[k]['adults'])))
  335|         chosen, drawn = {}, {}
  336|         while len(chosen) < ag.focus_cohorts and any(q for _, q in queues):
  337|             for wk, q in queues:
  338|                 while q and len(chosen) < ag.focus_cohorts:
  339|                     k = q.pop(0)
  340|                     if k in chosen:
  341|                         chosen[k].add(wk)  # already named by another group: it counts for this what-if too
  342|                         continue
  343|                     if k not in drawn:
  344|                         drawn[k] = draw(k)
  345|                     if drawn[k]:
  346|                         chosen[k] = {wk}
  347|                         break
  348|         for k, wks in chosen.items():
  349|             for a in drawn[k]:
  350|                 a['focus_for'] = sorted(wks)
  351|             agents += drawn[k]
  352|     for n, a in enumerate(agents):
  353|         rng = random.Random(f'{cfg.seed}:{a["id"]}')
  354|         label_of, order = prompts.assign_labels(rng, keys, prof['label_pool'])
  355|         labels = [label_of[p] for p in order]
  356|         a['label_of'] = label_of
  357|         a['paraphrase'] = n % ag.paraphrases
  358|         describe_agent(a, fr, year, inp)
  359|         elig = eligibility_line(a, fr, year, inp)
  360|         a['eligibility'] = elig
  361|         q = qs[a['paraphrase']]
  362| 
  363|         def parties(drop=frozenset(), swap=False, add=(), news=None):
  364|             desc = dict(prof['descriptors'])
  365|             plank = {p: party_planks(platforms, p, drop, order=prof['plank_order']) for p in keys}
  366|             for x in add:  # a compiled what-if's added plank, after the party's own
  367|                 plank[x['party']] = plank[x['party']] + [x['text'].rstrip('.') + '.']
  368|             if swap:
  369|                 plank = {**plank, 'R': plank['D'], 'D': plank['R']}
  370|                 desc = {**desc, 'R': desc['D'], 'D': desc['R']}
  371|             return [{'key': p, 'descriptor': desc[p], 'planks': plank[p], **({'news': news[p]} if news and news.get(p) else {})}
  372|                     for p in order]
  373| 
  374|         def request(arm, model, persona_elig, world, items, ballot_parties, disp_labels, system=prompts.SYSTEM,
  375|                     question=q, schema=None, meta=None):
  376|             text = prompts.brief({'lines': persona_lines(a, persona_elig, year)}, world, items,
  377|                                  prompts.ballot_block(STATE_NAME.get(a['state'], a['state']), ballot_parties, disp_labels, prof['others_line'],
  378|                                                      (prof.get('ballot_notes') or {}).get(a['state'])),
  379|                                  asof, prof['day_phrase'])
  380|             return {
  381|                 'id': f'{arm}|{a["id"]}|{SHORT.get(model, model)}',
  382|                 'model': model, 'system': system, 'user': f'{text}\n\n{question}',
  383|                 'schema': schema or prompts.answer_schema(disp_labels),
  384|                 'meta': {'kind': arm.split(':')[0], 'arm': arm, 'agent': a['id'], 'cohort': a['cohort'],
  385|                          'labels': disp_labels, 'label_of': label_of, 'paraphrase': a['paraphrase'],
  386|                          'prompt_version': prompts.PROMPT_VERSION, 'context_date': asof,
  387|                          'sources': [i['id'] for i in items], **(meta or {})},
  388|             }
  389| 
  390|         models = [ag.bulk_model] + ([ag.check_model] if rng.random() < ag.check_share else [])
  391|         ctl_items = items_for(a)
  392|         for model in models:
  393|             reqs.append(request('control', model, elig, {}, ctl_items, parties(), labels))
  394|         # Counterfactuals: the same persona, labels, order, paraphrase and model.
  395|         for wk in cfg.what_ifs:
  396|             spec = registry[wk]
  397|             if spec['facts'] is None or year not in (spec.get('years') or [spec.get('year', 1920)]):
  398|                 continue
  399|             if spec['mode'] == 'backbone' and not reached(spec, a, wk):
  400|                 continue
  401|             if a['group'] == 'foreign_white_alien' and spec['mode'] == 'agents':
  402|                 continue  # can't vote in either world; no effect to measure
  403|             if a.get('focus_for') and wk not in a['focus_for']:
  404|                 continue  # interviewed only for the what-if that named this group as decisive (D33)
  405|             f = spec['facts'](a, inp, year=year)
  406|             if not f['facts'] and f.get('eligibility') is None and not f.get('nominee_news'):
  407|                 continue
  408|             if ag.replace_barred and world.barred(elig) and world.barred(f.get('eligibility') or elig):
  409|                 continue  # D33: can't vote in either world; no effect to measure
  410|             items = items_for(a, f.get('drop_topics', set()), f.get('drop_after'))
  411|             staged = f.get('world') or {}
  412|             if f.get('drop_items'):
  413|                 items = [i for i in items if i['id'] not in f['drop_items']]  # D33: items the change makes false
  414|             added = world.items_for_agent(staged, a, STATE_NAME.get(a['state'], a['state'])) if staged else []
  415|             items = items + added
  416|             drop_planks = set(f.get('drop_planks') or ()) or ({'League of Nations'} if 'platform_override' in f else frozenset())
  417|             change = {'what_if': wk, 'facts': f['facts'], 'eligibility': f.get('eligibility'),
  418|                       'dropped_sources': [i['id'] for i in ctl_items if i not in items], 'dropped_planks': sorted(drop_planks),
  419|                       'added_planks': list(f.get('add_planks') or []),
  420|                       **({'added_items': [{'id': i['id'], 'date': i['date'], 'text': i['text']} for i in added]} if added else {})}
  421|             about = f.get('about') if f.get('about') in ('R', 'D') else None
  422|             news = {about: f['nominee_news']} if about and f.get('nominee_news') else None
  423|             ballot, cf_labels, extra = parties(drop_planks, add=f.get('add_planks') or (), news=news), labels, {}
  424|             q_cf = q
  425|             if news:
  426|                 # p5 manipulation check: whose news did the person take it to be?
  427|                 extra = {'news_check': {'expected': label_of[about], 'about': about}}
  428|                 q_cf = f'{q} {prompts.NEWS_CHECK}'
  429|             check = staged.get('check')
  430|             if check:
  431|                 # p6 belief check (D33), asked first: does the person take the change as true?
  432|                 extra = {**extra, 'world_check': {'expected': check['expected'], 'control': check['control'],
  433|                                                   'question': check['question']}}
  434|                 q_cf = f'{prompts.world_check_line(check)} {q_cf}'
  435|             if f.get('withdraws') and f['withdraws'] in label_of:
  436|                 # The third candidate leaves the race: his line comes off this ballot (labels and order otherwise kept).
  437|                 gone = label_of[f['withdraws']]
  438|                 ballot = [p for p in ballot if p['key'] != f['withdraws']]
  439|                 cf_labels = [l for l in labels if l != gone]
  440|                 extra = {**extra, 'withdrawn': {'label': gone, 'party': f['withdraws']}}
  441|             cand = f.get('candidate')
  442|             if cand:
  443|                 # p4: a third labelled line, after the two parties (their order and labels as in the control).
  444|                 third = scenario.third_label(random.Random(f'{cfg.seed}:{a["id"]}:{wk}'), labels, cand['name'], prof['label_pool'])
  445|                 line = f'{cand["name"]}, {cand["descriptor"].rstrip(".")}, running as an independent'
  446|                 ballot = ballot + [{'key': 'X', 'descriptor': line, 'planks': [p.rstrip('.') + '.' for p in cand['positions']]}]
  447|                 cf_labels = labels + [third]
  448|                 extra = {**extra, 'candidate': {'label': third, 'name': cand['name']}}
  449|             for model in (models if spec['mode'] == 'agents' else [ag.bulk_model]):
  450|                 reqs.append(request(f'cf:{wk}', model, f.get('eligibility') or elig, {'facts': f['facts']}, items,
  451|                                     ballot, cf_labels, question=q_cf,
  452|                                     schema=prompts.answer_schema(cf_labels, news_check=bool(news),
  453|                                                                  world_options=check['options'] if check else None)
  454|                                     if news or check else None,
  455|                                     meta={'change': change, **extra}))
  456|         # L2: the platform descriptions trade labels, and the display order flips.
  457|         if n % 2 == 0 and 'R' in label_of and 'D' in label_of:
  458|             swapped_labels = list(reversed(labels))
  459|             swap_parties = parties(swap=True)
  460|             reqs.append(request('swap', ag.bulk_model, elig, {}, ctl_items, list(reversed(swap_parties)), swapped_labels,
  461|                                 meta={'swap': True, 'displayed': [{'label': l, 'platform_of': {'R': 'D', 'D': 'R'}.get(p['key'], p['key'])}
  462|                                                                   for l, p in zip(swapped_labels, reversed(swap_parties))]}))
  463|         # L1: a separate instance, the same blinded brief, asked to identify.
  464|         if n % 2 == 1:
  465|             reqs.append(request('probe', ag.bulk_model, elig, {}, ctl_items, parties(), labels, system=prompts.PROBE_SYSTEM,
  466|                                 question=prompts.PROBE_QUESTION, schema=prompts.probe_schema(labels)))
  467|     if ag.arms:
  468|         reqs = [r for r in reqs if r['meta']['kind'] in ag.arms]
  469|     return agents, reqs
  470| 
  471| 
  472| def reached(spec: dict, a: dict, what_if: str) -> bool:
  473|     """Whether a backbone-mode what-if's cross-check interviews this person."""
  474|     if spec.get('generated'):
  475|         return scenario.agent_reached(spec, a)
  476|     return agent_reached(a, what_if)
  477| 
  478| 
  479| def agent_reached(a: dict, what_if: str) -> bool:
  480|     if a['group'] == 'foreign_white_alien':
  481|         return False  # can't vote in either world
  482|     if what_if == 'no-19th':
  483|         return a['sex'] == 'F' or a['group'] == 'native_white'  # women, plus native men as a cross-check
  484|     if what_if == 'fifteenth':
  485|         return a['state'] in SOUTH and a['group'] in ('black', 'native_white')
  486|     return True
```

## `simharness/agents.py`

```python
    1| """Agents: invented people drawn from a cohort's documented makeup.
    2| 
    3| A cohort is a stratum (region × sex × race/nativity/citizenship). Each agent
    4| gets:
    5| - a state, drawn in proportion to the cohort's adults there;
    6| - urban or rural, from that state's published urban share;
    7| - an age, from the cohort's published age distribution when there is one;
    8| - a household economy, imputed [I] and used only for persona diversity (it is
    9|   never a cohort dimension, and nothing is counted by it);
   10| - two to four dated items from the period corpus, preferring its own state.
   11| 
   12| The person is invented; the circumstances come from the census row and the
   13| dated items. Names come from small, plain lists and carry no information.
   14| """
   15| from __future__ import annotations
   16| 
   17| import random
   18| 
   19| from .geo import REGION_OF, STATE_NAME
   20| 
   21| GROUP_WORDS = {
   22|     'native_white': 'a white {noun} born in the United States',
   23|     'foreign_white_naturalized': 'a white {noun} born abroad and naturalized as a United States citizen',
   24|     'foreign_white_alien': 'a white {noun} born abroad who is not a United States citizen',
   25|     'black': 'a Black {noun}',
   26|     'other': 'an American Indian or Asian American {noun}',
   27| }
   28| 
   29| FIRST = {
   30|     'M': ['John', 'William', 'James', 'George', 'Charles', 'Frank', 'Joseph', 'Henry', 'Robert', 'Thomas',
   31|           'Edward', 'Harry', 'Walter', 'Arthur', 'Fred', 'Albert', 'Samuel', 'Clarence', 'Louis', 'Ernest'],
   32|     'F': ['Mary', 'Anna', 'Margaret', 'Helen', 'Elizabeth', 'Ruth', 'Florence', 'Ethel', 'Emma', 'Clara',
   33|           'Bertha', 'Minnie', 'Alice', 'Grace', 'Edna', 'Ida', 'Mabel', 'Lillian', 'Rose', 'Sarah'],
   34| }
   35| # Surnames: common American surnames for native-born and Black agents; for
   36| # foreign-born agents, surnames of the largest 1920 immigrant origins. p1 drew
   37| # every agent from one mixed list, which gave a Black North Carolina farmer a
   38| # Swedish surname; p2 separates them. Names still carry no modelled meaning.
   39| LAST_COMMON = ['Adams', 'Baker', 'Carter', 'Dawson', 'Ellis', 'Foster', 'Graham', 'Hayes', 'Irwin', 'Jordan',
   40|                'Lawson', 'Mercer', 'Owens', 'Porter', 'Reed', 'Sutton', 'Tate', 'Walker', 'Young', 'Johnson',
   41|                'Williams', 'Brown', 'Jones', 'Davis', 'Harris', 'Jackson', 'Thomas', 'Robinson', 'Green', 'Hill']
   42| LAST_IMMIGRANT = ['Brandt', 'Weber', 'Schmidt', 'Rossi', 'Esposito', 'Russo', 'Kowalski', 'Nowak', 'Novak',
   43|                   'Lindqvist', 'Johansson', 'Olsen', 'Murphy', 'Kelly', 'Sullivan', 'Cohen', 'Levy', 'Kaplan',
   44|                   'Horvath', 'Kovac', 'Dubois', 'Papadopoulos', 'Garcia', 'Lopez', 'Svoboda', 'Petrov']
   45| LAST = LAST_COMMON + LAST_IMMIGRANT  # p1's list, kept for reproducing p1 runs
   46| 
   47| ECONOMY = {
   48|     'farm': 'The household lives by farming.',
   49|     'wage': 'The household lives on wages from a mill, shop, mine or railroad.',
   50|     'trade': 'The household lives by a trade, a store or office work.',
   51|     'proprietor': 'The household lives by a business or a profession.',
   52| }
   53| 
   54| 
   55| # Other eras' wording (1920's ECONOMY is unchanged so its briefs stay byte-identical).
   56| ECONOMY_EARLY = {**ECONOMY, 'wage': 'The household lives on wages from a mill, workshop, the docks or hired farm work.'}
   57| ECONOMY_MODERN = {
   58|     'farm': 'The household lives by farming.',
   59|     'wage': 'The household lives on wages from a factory, warehouse, store or hospital.',
   60|     'trade': 'The household lives by a trade, a small business or office work.',
   61|     'proprietor': 'The household lives by a business or a profession.',
   62| }
   63| 
   64| 
   65| def economy_for(year: int = 1920) -> dict:
   66|     return ECONOMY_EARLY if year < 1868 else ECONOMY_MODERN if year >= 1972 else ECONOMY
   67| 
   68| 
   69| def economy_weights(urban: bool, year: int = 1920) -> dict:
   70|     # [I] imputed for persona diversity only. Replace with OCC1950 × FARM from
   71|     # the IPUMS 1920 full count (extracts/ipums-1920-fullcount.json).
   72|     if year >= 1972:  # [I] farm households are a small share of rural America by the 1970s
   73|         return {'farm': 0.01, 'wage': 0.5, 'trade': 0.34, 'proprietor': 0.15} if urban else \
   74|                {'farm': 0.15, 'wage': 0.45, 'trade': 0.3, 'proprietor': 0.1}
   75|     if year < 1868:
   76|         return {'farm': 0.1, 'wage': 0.5, 'trade': 0.25, 'proprietor': 0.15} if urban else \
   77|                {'farm': 0.85, 'wage': 0.08, 'trade': 0.05, 'proprietor': 0.02}
   78|     return {'farm': 0.05, 'wage': 0.5, 'trade': 0.3, 'proprietor': 0.15} if urban else \
   79|            {'farm': 0.7, 'wage': 0.15, 'trade': 0.1, 'proprietor': 0.05}
   80| 
   81| 
   82| def pick(rng: random.Random, weights: dict):
   83|     keys = list(weights)
   84|     return rng.choices(keys, weights=[weights[k] for k in keys])[0]
   85| 
   86| 
   87| def sample_agents(cohort: dict, n: int, corpus: list[dict], seed: int, urban_share: dict,
   88|                   age_bands: dict | None = None, year: int = 1920, min_age: int = 21) -> list[dict]:
   89|     """cohort: {key, region, sex, group, adults_by_state: {state: n}, adults}."""
   90|     rng = random.Random(f'{seed}:{cohort["key"]}')
   91|     out = []
   92|     for i in range(n):
   93|         state = pick(rng, cohort['adults_by_state'])
   94|         urban = rng.random() < urban_share.get(state, 0.5)
   95|         if age_bands:
   96|             band = pick(rng, age_bands)
   97|             lo, hi = band
   98|             age = rng.randint(lo, hi)
   99|         else:
  100|             age = rng.choice(range(min_age, 76 if year < 1972 else 81))  # [I] uniform when no age table
  101|         econ = pick(rng, economy_weights(urban, year))
  102|         sex = cohort['sex']
  103|         surnames = LAST_IMMIGRANT if cohort['group'].startswith('foreign') else LAST_COMMON
  104|         name = f'{rng.choice(FIRST[sex])} {rng.choice(surnames)}'
  105|         items = choose_items(rng, corpus, state, cohort)
  106|         out.append({
  107|             'id': f'{cohort["key"]}-{i}',
  108|             'cohort': cohort['key'],
  109|             'state': state,
  110|             'region': REGION_OF.get(state, 'west'),
  111|             'sex': sex,
  112|             'group': cohort['group'],
  113|             'age': age,
  114|             'urban': urban,
  115|             'economy': econ,
  116|             'name': name,
  117|             'items': items,
  118|             'weight': cohort['adults'] / n,
  119|         })
  120|     return out
  121| 
  122| 
  123| TOPIC_PRIORITY = {
  124|     # Which dated topics a cohort's people are likeliest to have met, by group.
  125|     'F': ['T1', 'T7', 'T8', 'T3', 'T2', 'T4'],
  126|     'black': ['T5', 'T3', 'T2'],
  127|     'foreign_white_naturalized': ['T6', 'T3', 'T2'],
  128|     'foreign_white_alien': ['T6', 'T3'],
  129|     'default': ['T3', 'T2', 'T4', 'T6'],
  130| }
  131| 
  132| 
  133| TOPIC_CODES = {t for ts in TOPIC_PRIORITY.values() for t in ts}
  134| 
  135| 
  136| def choose_items(rng: random.Random, corpus: list[dict], state: str, cohort: dict, k: int = 3) -> list[dict]:
  137|     order = TOPIC_PRIORITY.get(cohort['group']) or (TOPIC_PRIORITY['F'] if cohort['sex'] == 'F' else TOPIC_PRIORITY['default'])
  138|     if cohort['sex'] == 'F' and cohort['group'] == 'black':
  139|         order = ['T5', 'T1', 'T3']
  140|     region = REGION_OF.get(state, 'west')
  141|     chosen, used = [], set()
  142|     if corpus and not any(c['topic'] in TOPIC_CODES for c in corpus):
  143|         # Another year's corpus with its own topics: nearest items first, any topic.
  144|         own = [c for c in corpus if c.get('state') == state]
  145|         near = [c for c in corpus if REGION_OF.get(c.get('state')) == region and c not in own]
  146|         rest = [c for c in corpus if c not in own and c not in near]
  147|         for src in (own, near, rest):
  148|             src = src[:]
  149|             rng.shuffle(src)
  150|             chosen += src[:k - len(chosen)]
  151|         return chosen
  152|     for topic in order:
  153|         if len(chosen) >= k:
  154|             break
  155|         pool = [c for c in corpus if c['topic'] == topic and c['id'] not in used]
  156|         if topic == 'T8':  # women already voting in the West: only relevant where it is local
  157|             pool = [c for c in pool if REGION_OF.get(c.get('state')) == region]
  158|         own = [c for c in pool if c.get('state') == state]
  159|         near = [c for c in pool if REGION_OF.get(c.get('state')) == region]
  160|         src = own or near or pool
  161|         if src:
  162|             it = rng.choice(src)
  163|             chosen.append(it)
  164|             used.add(it['id'])
  165|     return chosen
  166| 
  167| 
  168| STATUS_WORDS = {'enslaved': 'an enslaved Black {noun}', 'free': 'a free Black {noun}'}
  169| 
  170| 
  171| def persona_lines(agent: dict, eligibility_line: str, year: int = 1920) -> list[str]:
  172|     noun = 'man' if agent['sex'] == 'M' else 'woman'
  173|     if 1868 <= year < 1972:
  174|         who = GROUP_WORDS[agent['group']].format(noun=noun)
  175|     else:
  176|         from .agentlayer import groups_for
  177|         words = groups_for(year)['words']
  178|         tmpl = STATUS_WORDS.get(agent.get('status'), words[agent['group']]) if agent['group'] == 'black' else words[agent['group']]
  179|         who = tmpl.format(noun=noun, origin=agent.get('origin', 'Hispanic'))
  180|         if who.startswith('a A'):
  181|             who = 'an ' + who[2:]
  182|     place = f'{"a city or town" if agent["urban"] else "the countryside"} in {STATE_NAME.get(agent["state"], agent["state"])}'
  183|     return [
  184|         f'{agent["name"]}, {agent["age"]}, {who}, living in {place}.',
  185|         economy_for(year)[agent['economy']],
  186|         eligibility_line,
  187|     ]
```

## `simharness/aggregate.py`

```python
    1| """From cell draws to states, electoral votes, ranges and the draw count.
    2| 
    3| A World is a set of draw-major arrays over cells (state × sex × group):
    4|     adults [D, C]   adults 21+
    5|     can    [D, C]   the fraction who can vote (legally and in practice)
    6|     t      [D, C]   turnout among those who can
    7|     share  [D, C, 3] R, D, O shares among voters
    8| """
    9| from __future__ import annotations
   10| 
   11| from dataclasses import dataclass, replace
   12| 
   13| import numpy as np
   14| 
   15| PARTIES = ['R', 'D', 'O']
   16| 
   17| 
   18| @dataclass
   19| class World:
   20|     adults: np.ndarray
   21|     can: np.ndarray
   22|     t: np.ndarray
   23|     share: np.ndarray
   24|     # Split of the barred fraction by reason, for slices: {reason: [D, C]}
   25|     barred_by: dict
   26| 
   27|     def copy(self) -> 'World':
   28|         return replace(self, adults=self.adults.copy(), can=self.can.copy(), t=self.t.copy(),
   29|                        share=self.share.copy(), barred_by={k: v.copy() for k, v in self.barred_by.items()})
   30| 
   31|     def votes(self) -> np.ndarray:
   32|         """[D, C, 3] votes by cell."""
   33|         return (self.adults * self.can * self.t)[..., None] * self.share
   34| 
   35| 
   36| def by_state(world: World, state_index: np.ndarray, n_states: int) -> np.ndarray:
   37|     """[D, S, 3] votes by state."""
   38|     v = world.votes()
   39|     out = np.zeros((v.shape[0], n_states, 3))
   40|     for p in range(3):
   41|         np.add.at(out[:, :, p], (slice(None), state_index), v[:, :, p])
   42|     return out
   43| 
   44| 
   45| def outcome(state_votes: np.ndarray, ev: np.ndarray, fixed: np.ndarray | None = None,
   46|             split: np.ndarray | None = None, o_single: np.ndarray | None = None) -> dict:
   47|     """state_votes [D, S, 3]; ev [S] (or [D, S] for reapportionment).
   48|     A state with no votes in a draw (its legislature chose the electors) casts no
   49|     electoral votes, unless fixed [S, 3] gives its electors by party (NaN rows: none):
   50|     then they count as given, and its winner is the party with the most.
   51|     split [S, 3] (NaN rows: none): a state whose electors historically divided (district
   52|     systems, split tickets, ME/NE) divides them as it did while its plurality winner is
   53|     the historical one; a state that flips goes winner-take-all. A fourth column in
   54|     split, when present, is the historical popular winner (MD 1908 went R by 605 votes
   55|     while 6 of its 8 electors were D).
   56|     o_single [S]: the largest single candidate's share of "other" (O lumps several:
   57|     Bell and Breckinridge in 1860); only that candidate can carry a state."""
   58|     if o_single is not None:
   59|         ranked = state_votes * np.concatenate([np.ones((len(o_single), 2)), np.asarray(o_single, dtype=float)[:, None]], axis=1)[None]
   60|         winner = ranked.argmax(axis=2)
   61|     else:
   62|         winner = state_votes.argmax(axis=2)                       # [D, S]
   63|     total = state_votes.sum(axis=2)
   64|     srt = np.sort(state_votes, axis=2)
   65|     margin = (srt[:, :, -1] - srt[:, :, -2]) / np.maximum(total, 1) * 100
   66|     ev = np.broadcast_to(ev, winner.shape)
   67|     none = total <= 0
   68|     if none.any():
   69|         ev = np.where(none, 0, ev)
   70|     ev_by = np.stack([(ev * (winner == p)).sum(axis=1) for p in range(3)], axis=1)  # [D, 3]
   71|     if split is not None:
   72|         sp = np.asarray(split, dtype=float)
   73|         has = ~np.isnan(sp).all(axis=1)
   74|         if has.any():
   75|             sp0 = np.nan_to_num(sp)
   76|             hist = sp0[:, :3].argmax(axis=1)                  # [S] the party with most of the split electors
   77|             if sp.shape[1] > 3:
   78|                 hist = np.where(np.isnan(sp[:, 3]), hist, np.nan_to_num(sp[:, 3])).astype(int)
   79|                 sp0 = sp0[:, :3]
   80|             keep = has[None, :] & (winner == hist[None, :]) & ~none   # [D, S]
   81|             # Replace those states' winner-take-all electors with the historical division.
   82|             wta = np.stack([(ev * keep * (winner == p)) for p in range(3)], axis=2).sum(axis=1)
   83|             ev_by = ev_by - wta.astype(ev_by.dtype) + (keep[:, :, None] * sp0[None, :, :]).sum(axis=1).astype(ev_by.dtype)
   84|     if fixed is not None and none.any():
   85|         fx = np.nan_to_num(np.asarray(fixed, dtype=float))
   86|         has = ~np.isnan(np.asarray(fixed, dtype=float)).all(axis=1)
   87|         use = none & has[None, :]                             # [D, S]
   88|         ev_by = ev_by + (use[:, :, None] * fx[None, :, :]).sum(axis=1).astype(ev_by.dtype)
   89|         winner = np.where(use, fx.argmax(axis=1)[None, :], winner)
   90|         ev = np.where(use, fx.sum(axis=1)[None, :], ev)
   91|     need = ev.sum(axis=1)[:, None] / 2
   92|     nat_winner = np.where((ev_by > need).any(axis=1), ev_by.argmax(axis=1), -1)
   93|     return {'winner': winner, 'margin': margin, 'ev': ev_by, 'national_winner': nat_winner,
   94|             'popular': state_votes.sum(axis=1), 'total': total}
   95| 
   96| 
   97| def summarize(out: dict, base_winner: np.ndarray, level: float = 0.8) -> dict:
   98|     """Point = median draw; ranges = central `level` interval; draw counts."""
   99|     lo, hi = (1 - level) / 2, 1 - (1 - level) / 2
  100|     ev = out['ev']
  101|     D = ev.shape[0]
  102|     # The point run: the draw whose EV split is closest to the median split.
  103|     med = np.median(ev, axis=0)
  104|     point = int(np.argmin(np.abs(ev - med).sum(axis=1)))
  105|     flipped = out['winner'] != base_winner[None, :]
  106|     return {
  107|         'draws': D,
  108|         'point': point,
  109|         'ev_point': ev[point].tolist(),
  110|         'ev_range': {p: [float(np.quantile(ev[:, i], lo)), float(np.quantile(ev[:, i], hi))] for i, p in enumerate(PARTIES)},
  111|         'draws_won': {p: int((out['national_winner'] == i).sum()) for i, p in enumerate(PARTIES)},
  112|         'draws_no_majority': int((out['national_winner'] == -1).sum()),
  113|         'state_winner_point': out['winner'][point].tolist(),
  114|         'state_margin_point': out['margin'][point].tolist(),
  115|         # additive: states with no popular vote in the point draw (legislature-chosen electors)
  116|         'state_no_vote_point': (out['total'][point] <= 0).tolist() if 'total' in out else None,
  117|         'state_margin_range': np.stack([np.quantile(out['margin'], lo, axis=0), np.quantile(out['margin'], hi, axis=0)], axis=1).tolist(),
  118|         'state_p_flip': flipped.mean(axis=0).tolist(),
  119|         'popular_point': out['popular'][point].tolist(),
  120|         'popular_range': np.stack([np.quantile(out['popular'], lo, axis=0), np.quantile(out['popular'], hi, axis=0)], axis=1).tolist(),
  121|         # Signed margin (R minus D, points) for flips and near misses
  122|         'rd_margin': None,
  123|     }
  124| 
  125| 
  126| def rd_margin(state_votes: np.ndarray) -> np.ndarray:
  127|     total = np.maximum(state_votes.sum(axis=2), 1)
  128|     return (state_votes[:, :, 0] - state_votes[:, :, 1]) / total * 100
```

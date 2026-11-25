# simulacra-americana: source and docs, part 13 of 17

Generated from commit `7f181fc6d5be` (2026-11-24) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `src/lib/simulacra/MiniMap.svelte` to `src/lib/simulacra/api.test.ts`. Lines are numbered as in the repository.

## `src/lib/simulacra/MiniMap.svelte`

```svelte
    1| <script lang="ts">
    2|   // The election's map, small: one tile per state, in the colour of whoever
    3|   // carried it. After a rerun, a flipped state carries a dot (black at 50%) inside its
    4|   // tile (the page's "● n flipped" beside the map is its key). A figure, not a
    5|   // control — the words around it carry the detail. Pointing at a tile names
    6|   // it: a flat black label over it, set flush left (Vignelli: one face, two
    7|   // weights, no ornament) — the state, then its electoral votes and who won.
    8|   // The hover follows the grid cell under the pointer, so the gaps between
    9|   // tiles never drop it; a tap does the same on touch.
   10|   import { GRID, STATES } from './geo';
   11|   import { bucketOf, type Colors, type MapState, type Names } from './types';
   12| 
   13|   interface Props {
   14|     year: number;
   15|     states?: readonly MapState[];
   16|     /** Candidate bucket → fill. */
   17|     colors: Colors;
   18|     /** Candidate bucket → surname. */
   19|     names: Names;
   20|     label?: string;
   21|     tile?: number;
   22|     gap?: number;
   23|     /** State codes lit from outside (a place named in the text, places.ts). */
   24|     highlight?: readonly string[];
   25|   }
   26|   let { year, states = [], colors, names, label = '', tile = 13, gap = 2, highlight = [] }: Props = $props();
   27| 
   28|   function detailOf(r: MapState | undefined): string {
   29|     if (!r) return 'No electoral votes';
   30|     const key = bucketOf(r.won);
   31|     const who = key === 'O' ? names.O || 'Other' : (names[key] ?? '');
   32|     const votes = r.ev ? `${r.ev} electoral vote${r.ev === 1 ? '' : 's'}` : '';
   33|     return [votes, r.flipped ? `flipped to ${who}` : who].filter(Boolean).join(' · ');
   34|   }
   35| 
   36|   const byCode = $derived(new Map(states.map((s) => [s.code, s])));
   37|   const tiles = $derived(
   38|     STATES.filter((s) => s.first <= year).map((s) => {
   39|       const r = byCode.get(s.code);
   40|       return {
   41|         ...s,
   42|         x: s.col * (tile + gap),
   43|         y: s.row * (tile + gap),
   44|         fill: r ? colors[bucketOf(r.won)] : null,
   45|         flipped: !!r?.flipped,
   46|         detail: detailOf(r),
   47|       };
   48|     }),
   49|   );
   50|   const w = $derived(GRID.cols * (tile + gap) - gap);
   51|   const h = $derived(GRID.rows * (tile + gap) - gap);
   52|   const byCell = $derived(new Map(tiles.map((t) => [`${t.row},${t.col}`, t])));
   53| 
   54|   let svg = $state<SVGSVGElement | null>(null);
   55|   /** A tile's code. */
   56|   let hovered = $state<string | null>(null);
   57|   // Lit: the tile under the pointer, else any named from outside (those that
   58|   // exist this year). One lit tile gets its label.
   59|   const lit = $derived(hovered ? [hovered] : highlight.filter((c) => tiles.some((t) => t.code === c)));
   60|   const hot = $derived(lit.length === 1 ? (tiles.find((t) => t.code === lit[0]) ?? null) : null);
   61|   function point(e: PointerEvent) {
   62|     if (!svg) return;
   63|     const r = svg.getBoundingClientRect();
   64|     const col = Math.floor(((e.clientX - r.left) * (w / r.width) + gap / 2) / (tile + gap));
   65|     const row = Math.floor(((e.clientY - r.top) * (h / r.height) + gap / 2) / (tile + gap));
   66|     hovered = byCell.get(`${row},${col}`)?.code ?? null;
   67|   }
   68|   // The label hangs over the tile, flush with its left edge — or its right,
   69|   // for tiles in the east, so it stays over the map.
   70|   const flushRight = $derived(!!hot && hot.col >= GRID.cols / 2);
   71| </script>
   72| 
   73| <!-- svelte-ignore a11y_no_static_element_interactions -->
   74| <span class="map" onpointermove={point} onpointerdown={point} onpointerleave={() => (hovered = null)}>
   75|   <!-- Pointing at a tile fades the rest back; nothing draws outside a tile. -->
   76|   <svg bind:this={svg} class:hovering={lit.length > 0} viewBox="0 0 {w} {h}" width={w} height={h} role="img" aria-label={label}>
   77|     {#each tiles as t (t.code)}
   78|       <g class="cell" class:hot={lit.includes(t.code)}>
   79|         {#if t.fill}
   80|           <rect x={t.x} y={t.y} width={tile} height={tile} rx="2.5" style:fill={t.fill} class="tile" />
   81|         {:else}
   82|           <rect x={t.x + 0.5} y={t.y + 0.5} width={tile - 1} height={tile - 1} rx="2.5" class="tile none" />
   83|         {/if}
   84|         {#if t.flipped}
   85|           <circle cx={t.x + tile / 2} cy={t.y + tile / 2} r={tile * 0.17} class="flip" />
   86|         {/if}
   87|       </g>
   88|     {/each}
   89|   </svg>
   90|   {#if hot}
   91|     <span
   92|       class="label"
   93|       class:right={flushRight}
   94|       style:left={flushRight ? null : `${hot.x - 2}px`}
   95|       style:right={flushRight ? `${w - hot.x - tile - 2}px` : null}
   96|       style:bottom="{h - hot.y + 6}px"
   97|       aria-hidden="true"
   98|     >
   99|       <span class="name">{hot.name}</span>
  100|       <span class="detail">{hot.detail}</span>
  101|     </span>
  102|   {/if}
  103| </span>
  104| 
  105| <style>
  106|   .map { position: relative; display: block; cursor: default; touch-action: manipulation; }
  107|   svg { display: block; overflow: visible; }
  108|   .tile { transition: fill 0.4s ease; }
  109|   .none { fill: none; stroke: rgba(0, 0, 0, 0.18); stroke-width: 1; }
  110|   .flip { fill: #00000080; }
  111|   .cell { transition: opacity 0.12s ease; }
  112|   .hovering .cell:not(.hot) { opacity: 0.28; }
  113|   /* The label: black, white type, square, flush left; name over detail. */
  114|   .label {
  115|     position: absolute;
  116|     z-index: 5;
  117|     display: flex;
  118|     flex-direction: column;
  119|     align-items: flex-start;
  120|     gap: 2px;
  121|     padding: 6px 9px 7px;
  122|     background: #000;
  123|     color: #fff;
  124|     white-space: nowrap;
  125|     text-align: left;
  126|     pointer-events: none;
  127|     font-family: 'Geist', -apple-system, 'Helvetica Neue', Helvetica, sans-serif;
  128|   }
  129|   .label.right { align-items: flex-end; text-align: right; }
  130|   .name { font-size: 13px; font-weight: 600; line-height: 1.15; letter-spacing: -0.01em; }
  131|   .detail { font-size: 11px; font-weight: 400; line-height: 1.2; color: rgba(255, 255, 255, 0.7); font-variant-numeric: tabular-nums; }
  132|   @media (prefers-reduced-motion: reduce) {
  133|     .tile, .cell { transition: none; }
  134|   }
  135| </style>
```

## `src/lib/simulacra/Narrator.svelte`

```svelte
    1| <script lang="ts">
    2|   // The narrator: the harness robot's bubble and the what-if composer
    3|   // (WhatIf, which owns the bubble's 7-line clamp and More / Less), with
    4|   // what it says worked out from the page's state (narrator.ts say()). A
    5|   // finished rerun's steps come out one at a time (startReveal), and the
    6|   // robot walks while they do (`revealing`).
    7|   import { onDestroy } from 'svelte';
    8|   import { say, STEP_MS } from './narrator';
    9|   import type { WhatIf as WhatIfItem } from './schemas';
   10|   import type { PageState } from './state.svelte';
   11|   import type { Names } from './types';
   12|   import WhatIf from './WhatIf.svelte';
   13|   import type { Still } from './whatif';
   14| 
   15|   interface Props {
   16|     page: PageState;
   17|     names: Names;
   18|     /** The live robot is drawn and settled. */
   19|     robotShown: boolean;
   20|     still: Still;
   21|     /** The robot's spot, for RobotStage to measure. */
   22|     slot?: HTMLElement | null;
   23|     /** The chips, held from the last loaded year while scrubbing. */
   24|     chips: readonly WhatIfItem[];
   25|     closed: boolean;
   26|     /** A finished rerun's steps are still coming out. */
   27|     revealing?: boolean;
   28|     onaction: (key: string) => void;
   29|     /** The year in words ("1920 · Harding over Cox"), shown under the opening message on a narrow window. */
   30|     caption?: string;
   31|   }
   32|   let {
   33|     page,
   34|     names,
   35|     robotShown,
   36|     still,
   37|     slot = $bindable(null),
   38|     chips,
   39|     closed,
   40|     revealing = $bindable(false),
   41|     onaction,
   42|     caption = '',
   43|   }: Props = $props();
   44| 
   45|   // The robot's name, for the what-if field's label.
   46|   const NAME = 'ChatPro';
   47| 
   48|   // Steps shown so far; Infinity once they're all out.
   49|   let reveal = $state(Infinity);
   50|   let revealTimer: ReturnType<typeof setInterval> | undefined;
   51| 
   52|   /** A finished rerun's n steps come out one at a time. */
   53|   export function startReveal(n: number): void {
   54|     clearInterval(revealTimer);
   55|     reveal = 0;
   56|     revealing = true;
   57|     revealTimer = setInterval(() => {
   58|       reveal += 1;
   59|       if (reveal >= n) {
   60|         clearInterval(revealTimer);
   61|         reveal = Infinity;
   62|         revealing = false;
   63|       }
   64|     }, STEP_MS);
   65|   }
   66|   onDestroy(() => clearInterval(revealTimer));
   67| 
   68|   const message = $derived(
   69|     say({
   70|       server: page.server,
   71|       year: page.year,
   72|       election: page.election,
   73|       run: page.run,
   74|       running: page.running,
   75|       runError: page.runError,
   76|       simFailed: page.simFailed,
   77|       sim: page.sim,
   78|       toggled: page.lastToggled,
   79|       whatIfs: page.whatIfs,
   80|       slice: page.openSlice,
   81|       showing: page.showing,
   82|       result: page.result,
   83|       names,
   84|       person: page.voter,
   85|       finding: !!page.voterKey && page.voterLoading === page.voterKey,
   86|       draft: page.typed,
   87|       shown: reveal,
   88|       sample: page.api.sample,
   89|     }),
   90|   );
   91| </script>
   92| 
   93| <WhatIf
   94|   name={NAME}
   95|   {robotShown}
   96|   bind:slot
   97|   {still}
   98|   {message}
   99|   whatIfs={chips}
  100|   selected={page.selected}
  101|   slice={page.openSlice}
  102|   bind:value={page.typed}
  103|   running={page.running}
  104|   canRun={page.canRun}
  105|   canReset={!!page.result || page.selected.length > 0 || !!page.edits.get(page.year)}
  106|   ran={page.result?.ran ?? []}
  107|   dirty={page.dirty}
  108|   {closed}
  109|   ontoggle={(key) => page.toggle(key)}
  110|   onrun={() => page.rerunNow()}
  111|   onstop={() => page.stop()}
  112|   onreset={() => page.reset()}
  113|   {onaction}
  114|   {caption}
  115| />
```

## `src/lib/simulacra/Places.svelte`

```svelte
    1| <script lang="ts">
    2|   // A run of text with its places (places.ts) made pointable: hovering one
    3|   // lights its tiles on the map. The text stays ink; a blue dotted underline says so.
    4|   import { onDestroy } from 'svelte';
    5|   import { hoverPlaces, segments } from './places';
    6| 
    7|   let { text = '' }: { text?: string } = $props();
    8|   const parts = $derived(segments(text));
    9|   let mine = false;
   10|   const on = (codes: readonly string[]) => {
   11|     mine = true;
   12|     hoverPlaces.set(codes);
   13|   };
   14|   const off = () => {
   15|     if (mine) {
   16|       mine = false;
   17|       hoverPlaces.set([]);
   18|     }
   19|   };
   20|   onDestroy(off);
   21| </script>
   22| 
   23| {#each parts as p, i (i)}{#if p.codes}{@const codes = p.codes}<!-- svelte-ignore a11y_no_static_element_interactions --><span class="place" class:region={codes.length > 1} onmouseenter={() => on(codes)} onmouseleave={off}>{p.t}</span>{:else}{p.t}{/if}{/each}
   24| 
   25| <style>
   26|   /* A blue dotted underline (systemBlue), heavier than a hairline, solid on hover. */
   27|   .place {
   28|     text-decoration: underline dotted #007aff;
   29|     text-decoration-thickness: 2px;
   30|     text-underline-offset: 3px;
   31|     text-decoration-skip-ink: none;
   32|     cursor: default;
   33|   }
   34|   .place:hover { text-decoration-style: solid; }
   35|   /* A region (several states): the dots in the text's own colour, not blue. */
   36|   .place.region, :global(.sa.dark) .place.region { text-decoration-color: currentColor; }
   37|   /* Under the Rerun view's filter (.sa.dark .main: invert, hue-rotate 180°,
   38|      saturate 1.5) #4696f5 comes out as dark mode's systemBlue #0a84ff
   39|      (solved through the filter matrices; #007aff itself would read cyan). */
   40|   :global(.sa.dark) .place { text-decoration-color: #4696f5; }
   41| </style>
```

## `src/lib/simulacra/Portrait.svelte`

```svelte
    1| <script lang="ts">
    2|   // A candidate's portrait (the lead image of their Wikipedia article), or
    3|   // their initials while it loads or if it can't. The winner's frame wears a
    4|   // ring and a check in their party's colour. With a Wikipedia article, the
    5|   // portrait links to it: a click opens it in a new window, a modified or
    6|   // middle click in a tab.
    7|   import { Check } from 'lucide-svelte';
    8| 
    9|   interface Props {
   10|     candidate: { readonly name: string; readonly portrait: string | null; readonly wiki?: string | null } | null;
   11|     /** The party colour, authored for the mode. */
   12|     color?: string;
   13|     /** The check's colour on it. */
   14|     ink?: string;
   15|     won?: boolean;
   16|     light?: boolean;
   17|     /** Frame width, px (4:5). */
   18|     size?: number;
   19|   }
   20|   let { candidate, color = '#898781', ink = '#ffffff', won = false, light = false, size = 104 }: Props = $props();
   21| 
   22|   const src = $derived(candidate?.portrait ?? null);
   23|   // Which source loaded or failed: a new source starts over.
   24|   let loadedSrc = $state<string | null>(null);
   25|   let failedSrc = $state<string | null>(null);
   26|   const loaded = $derived(src !== null && loadedSrc === src);
   27|   const failed = $derived(src !== null && failedSrc === src);
   28| 
   29|   function initialsOf(name: string): string {
   30|     const words = name.split(/\s+/).filter((w) => /^[A-Z]/.test(w));
   31|     const first = words[0] ?? '';
   32|     const last = words[words.length - 1] ?? '';
   33|     if (words.length > 1) return first.charAt(0) + last.charAt(0);
   34|     return first.charAt(0);
   35|   }
   36|   const initials = $derived(initialsOf(candidate?.name ?? ''));
   37|   const wiki = $derived(candidate?.wiki ?? null);
   38| 
   39|   // A plain click opens the article in a new window; the link itself still
   40|   // works for a middle click, a new tab or a screen reader.
   41|   function openWiki(e: MouseEvent) {
   42|     if (!wiki || e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return;
   43|     e.preventDefault();
   44|     window.open(wiki, '_blank', 'noopener,noreferrer,width=1100,height=850');
   45|   }
   46| </script>
   47| 
   48| {#snippet face()}
   49| <div class="frame" class:won style:width="{size}px" style:height="{Math.round(size * 1.25)}px">
   50|   <span class="initials" aria-hidden="true">{initials}</span>
   51|   {#if src && !failed}
   52|     {#key src}
   53|       <img {src} alt="" class:shown={loaded} class:dark={!light} draggable="false" decoding="async" referrerpolicy="no-referrer"
   54|         onload={() => (loadedSrc = src)} onerror={() => (failedSrc = src)} />
   55|     {/key}
   56|   {/if}
   57| </div>
   58| {#if won}
   59|   <span class="badge" style:--ink={ink} aria-hidden="true"><Check size={13} strokeWidth={3} /></span>
   60| {/if}
   61| {/snippet}
   62| 
   63| {#if wiki}
   64|   <a class="portrait" style:--c={color} href={wiki} target="_blank" rel="noopener noreferrer"
   65|     aria-label="{candidate?.name} on Wikipedia (opens in a new window)" title="{candidate?.name} on Wikipedia" onclick={openWiki}>{@render face()}</a>
   66| {:else}
   67|   <div class="portrait" style:--c={color}>{@render face()}</div>
   68| {/if}
   69| 
   70| <style>
   71|   .portrait { position: relative; display: inline-flex; color: inherit; text-decoration: none; border-radius: 14px; }
   72|   a.portrait { cursor: pointer; }
   73|   a.portrait .frame { transition: transform 0.15s ease, filter 0.15s ease; }
   74|   a.portrait:hover .frame { transform: translateY(-1px); filter: brightness(1.04); }
   75|   a.portrait:focus-visible { outline: 2px solid #3876b7; outline-offset: 4px; }
   76|   .frame {
   77|     position: relative;
   78|     overflow: hidden;
   79|     border-radius: 14px;
   80|     background: rgba(0, 0, 0, 0.07);
   81|     flex: none;
   82|   }
   83|   /* The winner: a 2px surface gap, then the party's ring. */
   84|   .frame.won { box-shadow: 0 0 0 2px #e5e5e5, 0 0 0 4px var(--c); }
   85|   .initials {
   86|     position: absolute;
   87|     inset: 0;
   88|     display: flex;
   89|     align-items: center;
   90|     justify-content: center;
   91|     font-size: 30px;
   92|     font-weight: 600;
   93|     letter-spacing: 0.02em;
   94|     color: rgba(0, 0, 0, 0.4);
   95|   }
   96|   img {
   97|     position: absolute;
   98|     inset: 0;
   99|     width: 100%;
  100|     height: 100%;
  101|     object-fit: cover;
  102|     object-position: 50% 20%;
  103|     opacity: 0;
  104|     transition: opacity 0.35s ease;
  105|   }
  106|   img.shown { opacity: 1; }
  107|   /* Dark mode inverts the whole page; a photo is turned back. */
  108|   img.dark { filter: invert(1) hue-rotate(180deg) saturate(66.7%); }
  109|   .badge {
  110|     position: absolute;
  111|     right: -7px;
  112|     bottom: -7px;
  113|     width: 24px;
  114|     height: 24px;
  115|     display: flex;
  116|     align-items: center;
  117|     justify-content: center;
  118|     border-radius: 999px;
  119|     background: var(--c);
  120|     color: var(--ink);
  121|     box-shadow: 0 0 0 2px #e5e5e5;
  122|   }
  123|   @media (prefers-reduced-motion: reduce) { img, a.portrait .frame { transition: none; } }
  124| </style>
```

## `src/lib/simulacra/RobotStage.svelte`

```svelte
    1| <script lang="ts" module>
    2|   import type { Still } from './whatif';
    3| 
    4|   // Stills of the robot, one per paint, rendered from this page (paint,
    5|   // lighting, 40° yaw, framing): shown in the slot the moment the page loads
    6|   // and faded out when the live robot draws. dx/db/w: CSS px from the slot's
    7|   // bottom-centre (see WhatIf `still`). Re-shoot if the framing or look changes.
    8|   export const STILLS: Readonly<Record<'history' | 'rerun', Still>> = {
    9|     history: { src: '/simulacra/chatpro-history.png?v=1', dx: -79, db: -11, w: 153.2 },
   10|     rerun: { src: '/simulacra/chatpro-rerun.png?v=1', dx: -79, db: -11, w: 153.2 },
   11|   };
   12| </script>
   13| 
   14| <script lang="ts">
   15|   // The robot's layer: the frame (RobotFrame) over the page's content,
   16|   // scrolling with it, click-through. The page measures the WhatIf slot and
   17|   // stands the robot in it; once drawn, the robot's anchors nudge its box
   18|   // once, so its feet sit on the slot's floor. Until then (and SETTLE_MS
   19|   // after the nudge) the layer stays invisible over the still, so its first
   20|   // frames, drawn before the nudge, never show; then one cross-fade.
   21|   //
   22|   // Dragged across, the robot turns with the pointer and, let go, eases back;
   23|   // tapped (pressed and let go without turning it), it calls `ontap`, and the
   24|   // page fires its chest reactor with `blast`.
   25|   import { onDestroy, untrack } from 'svelte';
   26|   import type { Paint } from '$lib/robot/characters';
   27|   import type { RobotAnchors, RobotStage } from '$lib/robot/messages';
   28|   import RobotFrame from '$lib/robot/RobotFrame.svelte';
   29|   import { dragTurn, easeToward, type Nudge, nudgeToSlot, ROBOT_YAW, sameStage, stageInSlot, YAW_EASE_RATE, yawForYear } from '$lib/robot/stage';
   30|   import { ELECTION_YEARS } from './geo';
   31| 
   32|   interface Props {
   33|     /** The WhatIf slot the robot stands in. */
   34|     spot: HTMLElement | null;
   35|     /** The time bar is being dragged: the robot holds still. */
   36|     scrubbing: boolean;
   37|     year: number;
   38|     paint: Paint;
   39|     walking: boolean;
   40|     /** Re-measured whenever this resizes (the page's content). */
   41|     observe?: HTMLElement | null;
   42|     /** The robot is drawn, nudged and settled. */
   43|     shown?: boolean;
   44|     /** The robot was tapped (not dragged). */
   45|     ontap?: () => void;
   46|     /** Its resting turn, degrees, which the time bar sways around (stage.ts ROBOT_YAW). */
   47|     restYaw?: number;
   48|   }
   49|   let { spot, scrubbing, year, paint, walking, observe = null, shown = $bindable(false), ontap, restYaw = ROBOT_YAW }: Props = $props();
   50| 
   51|   const SETTLE_MS = 150;
   52|   let host = $state<HTMLElement | null>(null);
   53|   let robotShown = $state(false);
   54|   let robotReady = $state(false);
   55|   let readyTimer: ReturnType<typeof setTimeout> | undefined;
   56|   /** The robot's box, before its turn. */
   57|   let box = $state<RobotStage | null>(null);
   58|   let measureFrame = 0;
   59|   let nudge: Nudge = { x: 0, y: 0 };
   60|   let nudged = false;
   61|   let frame = $state<ReturnType<typeof RobotFrame> | null>(null);
   62|   /** The turn from a drag across the robot, degrees; 0 when let go. */
   63|   let dragYaw = $state(0);
   64|   let dragFrom: number | null = null;
   65|   let dragged = false;
   66|   /** The turn a new drag starts from (mid-way through a snap back). */
   67|   let dragBase = 0;
   68|   // Let go, the robot eases back three times slower than it follows the
   69|   // time bar: the page eases the drag's turn to 0 at a third of the
   70|   // renderer's rate, and the renderer follows that.
   71|   const SNAP_RATE = YAW_EASE_RATE / 3;
   72|   let snapFrame = 0;
   73|   function snapBack(): void {
   74|     cancelAnimationFrame(snapFrame);
   75|     let last = performance.now();
   76|     const step = (now: number) => {
   77|       dragYaw = easeToward(dragYaw, 0, (now - last) / 1000, SNAP_RATE);
   78|       last = now;
   79|       if (Math.abs(dragYaw) < 0.05) {
   80|         dragYaw = 0;
   81|         snapFrame = 0;
   82|         return;
   83|       }
   84|       snapFrame = requestAnimationFrame(step);
   85|     };
   86|     snapFrame = requestAnimationFrame(step);
   87|   }
   88| 
   89|   // The robot turns a little with the time bar (yawForYear) and by hand,
   90|   // eased in the renderer.
   91|   const yawNow = $derived(yawForYear(ELECTION_YEARS.indexOf(year), ELECTION_YEARS.length, restYaw) + dragYaw);
   92|   const stage = $derived(box ? { ...box, yaw: yawNow } : null);
   93| 
   94|   /** A shot from the robot's chest reactor in `color` (#rrggbb). */
   95|   export function blast(color: string): void {
   96|     frame?.blast(color);
   97|   }
   98| 
   99|   // Turning the robot by hand. Listened for on the window and hit-tested
  100|   // against the slot: the frame lets clicks through, and the slot is a
  101|   // button that's disabled while a rerun runs.
  102|   function robotDown(e: PointerEvent): void {
  103|     if (!box || !spot || e.button !== 0) return;
  104|     const r = spot.getBoundingClientRect();
  105|     if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) return;
  106|     // A press on something drawn over the robot (the what-if's chips, field
  107|     // or bubble, moved onto it) is that thing's, not the robot's.
  108|     const t = e.target instanceof Element ? e.target : null;
  109|     if (t && !spot.contains(t) && t.closest('button, input, a, label, [role="status"], [role="group"]')) return;
  110|     dragFrom = e.clientX;
  111|     dragged = false;
  112|     cancelAnimationFrame(snapFrame);
  113|     snapFrame = 0;
  114|     dragBase = dragYaw;
  115|     e.preventDefault(); // no text selection while turning
  116|   }
  117|   function robotMove(e: PointerEvent): void {
  118|     if (dragFrom === null) return;
  119|     const turn = dragTurn(e.clientX - dragFrom, dragged);
  120|     if (turn === null) return;
  121|     dragged = true;
  122|     dragYaw = dragBase + turn;
  123|   }
  124|   function robotUp(): void {
  125|     if (dragFrom === null) return;
  126|     if (!dragged) ontap?.();
  127|     dragFrom = null;
  128|     snapBack();
  129|     // The click (if any) lands before this; a drag released off the page leaves none.
  130|     setTimeout(() => (dragged = false));
  131|   }
  132|   // A drag isn't a press: the click that ends one doesn't talk to the robot.
  133|   function robotClick(e: MouseEvent): void {
  134|     if (!dragged) return;
  135|     dragged = false;
  136|     e.stopPropagation();
  137|     e.preventDefault();
  138|   }
  139| 
  140|   $effect(() => {
  141|     shown = robotReady && robotShown;
  142|   });
  143| 
  144|   function measureStage(): void {
  145|     measureFrame = 0;
  146|     // Dragging the time bar: no restaging; it's placed once more on release.
  147|     if (scrubbing && box) return;
  148|     if (!spot) {
  149|       box = null;
  150|       return;
  151|     }
  152|     const r = spot.getBoundingClientRect();
  153|     // The layer ends just under the robot's slot, not at the page's bottom:
  154|     // a taller bubble or chip row then never resizes the robot's frame (which
  155|     // clears its canvas) or shifts the stage's bottom, so the robot holds still.
  156|     const page = host?.parentElement?.getBoundingClientRect();
  157|     if (host && page) {
  158|       const want = `${Math.ceil(r.bottom - page.top + 40)}px`;
  159|       if (host.style.height !== want) host.style.height = want;
  160|     }
  161|     // From the robot's layer's bottom-right, not the window's: the layer
  162|     // scrolls with the page, so scrolling never moves the stage.
  163|     const h = host?.getBoundingClientRect() ?? new DOMRect(0, 0, innerWidth, innerHeight);
  164|     const next = stageInSlot(h, r, nudge, 0);
  165|     if (!sameStage(box, next)) box = next;
  166|   }
  167| 
  168|   /** Measures on the next frame (once, however often it's asked). */
  169|   export function measureSoon(): void {
  170|     if (!measureFrame) measureFrame = requestAnimationFrame(measureStage);
  171|   }
  172| 
  173|   $effect(() => {
  174|     void spot;
  175|     untrack(measureSoon);
  176|   });
  177|   $effect(() => {
  178|     if (!observe) return;
  179|     const ro = new ResizeObserver(measureSoon);
  180|     ro.observe(observe);
  181|     return () => ro.disconnect();
  182|   });
  183| 
  184|   function onRobot(anchors: RobotAnchors | null): void {
  185|     const on = !!anchors;
  186|     if (on !== robotShown) robotShown = on;
  187|     if (!anchors || nudged || !spot || !box) return;
  188|     const d = nudgeToSlot(spot.getBoundingClientRect(), anchors);
  189|     nudged = true;
  190|     if (Math.abs(d.x) > 3 || Math.abs(d.y) > 3) {
  191|       nudge = { x: nudge.x + d.x, y: nudge.y + d.y };
  192|       measureStage();
  193|     }
  194|     // The nudged stage reaches the frame a frame or two later: show after that.
  195|     clearTimeout(readyTimer);
  196|     readyTimer = setTimeout(() => (robotReady = true), SETTLE_MS);
  197|   }
  198| 
  199|   onDestroy(() => {
  200|     clearTimeout(readyTimer);
  201|     cancelAnimationFrame(measureFrame);
  202|     cancelAnimationFrame(snapFrame);
  203|   });
  204| </script>
  205| 
  206| <svelte:head>
  207|   <link rel="preload" as="image" href={STILLS.history.src} fetchpriority="high" />
  208|   <link rel="preload" as="image" href={STILLS.rerun.src} />
  209| </svelte:head>
  210| <svelte:window onresize={measureSoon} onpointerdown={robotDown} onpointermove={robotMove} onpointerup={robotUp} onpointercancel={robotUp} onclickcapture={robotClick} />
  211| 
  212| <div class="robot-host" class:ready={robotReady && robotShown} bind:this={host} aria-hidden="true">
  213|   <RobotFrame bind:this={frame} {stage} visible={!!stage} {walking} {paint} {onRobot} />
  214| </div>
  215| 
  216| <style>
  217|   .robot-host { opacity: 0; transition: opacity 0.18s ease; position: absolute; inset: 0 0 auto 0; height: 100%; z-index: 3; overflow: hidden; pointer-events: none; }
  218|   .robot-host.ready { opacity: 1; }                /* one cross-fade with the still (WhatIf .still, same 0.18s) */
  219| </style>
```

## `src/lib/simulacra/SliceRow.svelte`

```svelte
    1| <script lang="ts">
    2|   // One group of voters as a row of fifty people: the winner's voters from
    3|   // the left, the runner-up's from the right, and between them everyone else
    4|   // — third parties, those who stayed home, those who couldn't vote. A rerun
    5|   // recolours the dots in place, so a franchise change reads as the gap in
    6|   // the middle filling in. Tapping a row picks the group: the harness then
    7|   // introduces someone from it (the page's bubble).
    8|   import type { SliceEdit } from './api';
    9|   import { fmtCompact } from './format';
   10|   import GroupLabel from './GroupLabel.svelte';
   11|   import { DOTS } from './groups';
   12|   import type { Slice } from './schemas';
   13|   import type { Colors, Names } from './types';
   14| 
   15|   interface Props {
   16|     slice: Slice;
   17|     /** The same group in history, to show what changed. */
   18|     base?: Slice | null | undefined;
   19|     colors: Colors;
   20|     names: Names;
   21|     /** The group the harness is talking about. */
   22|     open?: boolean;
   23|     /** Showing a rerun, not history. */
   24|     rerun?: boolean;
   25|     /** A chosen what-if reaches this group. */
   26|     lit?: boolean;
   27|     /** The dots can be dragged (a rerun follows). */
   28|     editable?: boolean;
   29|     /** The row was tapped. */
   30|     ontoggle?: () => void;
   31|     /** Dots were dragged: the change in each fraction of the group's adults. */
   32|     onedit?: (d: SliceEdit) => void;
   33|   }
   34|   let {
   35|     slice,
   36|     base = null,
   37|     colors,
   38|     names,
   39|     open = false,
   40|     rerun = false,
   41|     lit = false,
   42|     editable = false,
   43|     ontoggle,
   44|     onedit,
   45|   }: Props = $props();
   46| 
   47|   const N = DOTS;
   48|   /** Left to right: A, O, home, barred, B. */
   49|   const KINDS = ['A', 'O', 'home', 'barred', 'B'] as const;
   50|   type Kind5 = (typeof KINDS)[number];
   51|   type Counts = readonly [number, number, number, number, number];
   52| 
   53|   // Largest-remainder counts, left to right: A, O, home, barred, B.
   54|   function counts(s: Slice): Counts {
   55|     const parts = KINDS.map((k) => Math.max(0, s[k] || 0));
   56|     const total = parts.reduce((a, b) => a + b, 0) || 1;
   57|     const raw = parts.map((x) => (x / total) * N);
   58|     const out = raw.map(Math.floor);
   59|     let left = N - out.reduce((a, b) => a + b, 0);
   60|     const order = raw.map((x, i) => [x - Math.floor(x), i] as const).sort((a, b) => b[0] - a[0]);
   61|     for (const [, i] of order) {
   62|       if (left > 0) {
   63|         out[i] = (out[i] ?? 0) + 1;
   64|         left--;
   65|       }
   66|     }
   67|     return [out[0] ?? 0, out[1] ?? 0, out[2] ?? 0, out[3] ?? 0, out[4] ?? 0];
   68|   }
   69|   // Dragging a colour's run: its edge follows the pointer. Dots it takes come
   70|   // from those who stayed home, then those who couldn't vote, then third
   71|   // parties; dots it gives up stay home. Held here (draft) until the rerun
   72|   // brings the group back: a draft belongs to the slice it was drawn on.
   73|   let held = $state<{ slice: Slice; counts: Counts } | null>(null);
   74|   const draft = $derived(held && held.slice === slice ? held.counts : null);
   75|   let drag: { start: Counts; side: 'A' | 'B'; id: number } | null = null;
   76|   let swallowClick = false;
   77|   function at(e: PointerEvent, svg: SVGSVGElement) {
   78|     const m = svg.getScreenCTM();
   79|     return m ? (e.clientX - m.e) / m.a : 0;
   80|   }
   81|   function reshape(start: Counts, side: 'A' | 'B', want: number): Counts {
   82|     const [a, o, home, barred, b] = start;
   83|     const cap = N - (side === 'A' ? b : a);
   84|     const n = Math.max(0, Math.min(cap, want));
   85|     const next = { A: a, O: o, home, barred, B: b };
   86|     let d = n - next[side];
   87|     next[side] = n;
   88|     if (d < 0) next.home -= d;
   89|     for (const k of ['home', 'barred', 'O'] as const) {
   90|       if (d <= 0) break;
   91|       const take = Math.min(d, next[k]);
   92|       next[k] -= take;
   93|       d -= take;
   94|     }
   95|     return [next.A, next.O, next.home, next.barred, next.B];
   96|   }
   97|   function press(e: PointerEvent & { currentTarget: SVGSVGElement }) {
   98|     if (!editable || e.button !== 0) return;
   99|     const svg = e.currentTarget;
  100|     const start = draft ?? counts(slice);
  101|     const x = at(e, svg);
  102|     const i = Math.max(0, Math.min(N - 1, Math.floor(x / 10)));
  103|     const mid = start[0] + (N - start[0] - start[4]) / 2;
  104|     const dot = dots[i];
  105|     let side: 'A' | 'B' = i < mid ? 'A' : 'B';
  106|     if (dot === 'A' || dot === 'B') side = dot;
  107|     drag = { start, side, id: e.pointerId };
  108|     svg.setPointerCapture?.(e.pointerId);
  109|     e.preventDefault();
  110|     follow(e);
  111|   }
  112|   function follow(e: PointerEvent & { currentTarget: SVGSVGElement }) {
  113|     if (!drag || e.pointerId !== drag.id) return;
  114|     const x = at(e, e.currentTarget);
  115|     const want = drag.side === 'A' ? Math.round(x / 10) : Math.round((N * 10 - x) / 10);
  116|     held = { slice, counts: reshape(drag.start, drag.side, want) };
  117|   }
  118|   function release(e: PointerEvent) {
  119|     if (!drag || e.pointerId !== drag.id) return;
  120|     const start = drag.start;
  121|     const now = counts(slice);
  122|     const moved = draft?.some((n, k) => n !== start[k]) ?? false;
  123|     drag = null;
  124|     swallowClick = true;
  125|     setTimeout(() => (swallowClick = false), 0);
  126|     if (!draft || !moved) {
  127|       if (draft?.every((n, k) => n === now[k])) held = null;
  128|       return;
  129|     }
  130|     const d: SliceEdit = {};
  131|     KINDS.forEach((k: Kind5, j) => {
  132|       const was = now[j] ?? 0;
  133|       const is = draft[j] ?? 0;
  134|       if (is !== was) d[k] = (is - was) / N;
  135|     });
  136|     if (Object.keys(d).length) onedit?.(d);
  137|   }
  138|   function tap() {
  139|     if (swallowClick) {
  140|       swallowClick = false;
  141|       return;
  142|     }
  143|     ontoggle?.();
  144|   }
  145|   const dots = $derived(KINDS.flatMap((k, j) => Array.from({ length: (draft ?? counts(slice))[j] ?? 0 }, () => k)));
  146| 
  147|   const voted = (s: Slice) => (s.A || 0) + (s.B || 0) + (s.O || 0);
  148|   const pct = (x: number) => `${Math.round(x * 100)}%`;
  149|   function lead(s: Slice): string {
  150|     const v = voted(s);
  151|     if (v < 0.02) return s.barred >= 0.5 ? 'Couldn’t vote' : 'Stayed home';
  152|     let k: 'A' | 'B' | 'O' = 'O';
  153|     if (s.A >= s.B && s.A >= s.O) k = 'A';
  154|     else if (s.B >= s.O) k = 'B';
  155|     return `${names[k] || 'Other'} ${pct(s[k] / v)}`;
  156|   }
  157|   function caption(s: Slice): string {
  158|     const people = `${fmtCompact((s.adults || 0) * 1e6)} adults`;
  159|     if (s.barred >= 0.95) return `${people} · couldn’t vote`;
  160|     if (s.barred >= 0.5) return `${people} · ${Math.round(s.barred * 10)} in 10 couldn’t vote`;
  161|     if (s.barred >= 0.1) return `${people} · ${pct(s.barred)} couldn’t vote`;
  162|     return `${people} · ${pct(voted(s))} voted`;
  163|   }
  164|   // How many could vote, and did.
  165|   function turnout(s: Slice): string {
  166|     if (s.barred >= 0.95) return 'couldn’t vote';
  167|     if (s.barred >= 0.5) return `${Math.round(s.barred * 10)} in 10 couldn’t vote`;
  168|     return `${pct(voted(s))} voted`;
  169|   }
  170|   const main = $derived(lead(slice));
  171|   // Under a rerun, what this group was in history: its split if that
  172|   // changed, else its turnout if that did.
  173|   function wasOf(): string {
  174|     if (!rerun || !base) return '';
  175|     if (lead(base) !== main) return `was ${lead(base)}`;
  176|     if (Math.abs(voted(base) - voted(slice)) > 0.02) return `was ${turnout(base)}`;
  177|     return '';
  178|   }
  179|   const was = $derived(wasOf());
  180| </script>
  181| 
  182| <div class="row" class:open class:lit style:--a={colors.A} style:--b={colors.B} style:--o={colors.O}>
  183|   <button type="button" class="head" aria-pressed={open} onclick={tap}>
  184|     <span class="who">
  185|       <span class="label"><GroupLabel label={slice.label} /></span>
  186|       <span class="cap">{caption(slice)}</span>
  187|     </span>
  188|     <!-- svelte-ignore a11y_no_static_element_interactions -->
  189|     <svg class="strip" class:editable viewBox="0 0 {N * 10} 10" preserveAspectRatio="xMinYMid meet" aria-hidden="true"
  190|       onpointerdown={press} onpointermove={follow} onpointerup={release} onpointercancel={release}>
  191|       {#each dots as d, i (i)}
  192|         <circle cx={i * 10 + 5} cy="5" class="dot {d}" style:transition-delay="{Math.min(i, N - 1 - i) * 9}ms" />
  193|       {/each}
  194|     </svg>
  195|     <span class="val">
  196|       <span class="main">{main}</span>
  197|       {#if was}<span class="was">{was}</span>{/if}
  198|     </span>
  199|   </button>
  200| </div>
  201| 
  202| <style>
  203|   .row { position: relative; border-radius: 12px; transition: background-color 0.15s ease; }
  204|   .row.open .head { background: rgba(0, 0, 0, 0.07); }
  205|   /* A chosen what-if reaches this group: a mark at its leading edge. */
  206|   .row.lit::before {
  207|     content: '';
  208|     position: absolute;
  209|     left: -10px;
  210|     top: 14px;
  211|     width: 3px;
  212|     height: 22px;
  213|     border-radius: 2px;
  214|     background: rgba(0, 0, 0, 0.7);
  215|   }
  216|   .head {
  217|     display: grid;
  218|     grid-template-columns: minmax(160px, 212px) minmax(0, 1fr) 124px;
  219|     align-items: center;
  220|     gap: 16px;
  221|     width: 100%;
  222|     min-height: var(--row-min);
  223|     padding: var(--row-pad-y) var(--row-pad-x);
  224|     border: none;
  225|     border-radius: 12px;
  226|     background: transparent;
  227|     color: inherit;
  228|     font: inherit;
  229|     text-align: left;
  230|     cursor: pointer;
  231|   }
  232|   .head:hover { background: rgba(0, 0, 0, 0.04); }
  233|   .head:focus-visible { outline: 2px solid #3876b7; outline-offset: 1px; }
  234|   .who { display: flex; flex-direction: column; gap: var(--who-gap); min-width: 0; }
  235|   .label { font-size: var(--name-size); font-weight: 600; line-height: var(--name-leading); }
  236|   .cap { font-size: var(--note-size); line-height: var(--note-leading); color: rgba(0, 0, 0, 0.55); font-variant-numeric: tabular-nums; }
  237|   .strip { width: 100%; height: auto; display: block; overflow: visible; }
  238|   /* Tall enough to grab: the dots' band, padded. */
  239|   .strip.editable { cursor: ew-resize; touch-action: pan-y; padding: 8px 0; margin: -8px 0; box-sizing: content-box; }
  240|   .dot {
  241|     r: 3.9;
  242|     transition: fill 0.4s ease, stroke 0.4s ease, r 0.4s ease;
  243|   }
  244|   .dot.A { fill: var(--a); stroke: transparent; }
  245|   .dot.B { fill: var(--b); stroke: transparent; }
  246|   .dot.O { fill: var(--o); stroke: transparent; }
  247|   .dot.home { fill: transparent; stroke: rgba(0, 0, 0, 0.42); stroke-width: 1.2; r: 3.3; }
  248|   .dot.barred { fill: rgba(0, 0, 0, 0.2); stroke: transparent; r: 1.7; }
  249|   .val { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; text-align: right; }
  250|   .main { font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; white-space: nowrap; }
  251|   .was { font-size: 12px; color: rgba(0, 0, 0, 0.5); font-variant-numeric: tabular-nums; white-space: nowrap; }
  252|   @media (max-width: 700px) {
  253|     .head { grid-template-columns: minmax(0, 1fr) auto; row-gap: var(--strip-gap); }
  254|     .strip { grid-column: 1 / -1; grid-row: 2; }
  255|     .row.lit::before { left: -6px; }
  256|   }
  257|   @media (prefers-reduced-motion: reduce) {
  258|     .dot, .row { transition: none !important; }
  259|   }
  260| </style>
```

## `src/lib/simulacra/TimeBar.svelte`

```svelte
    1| <script lang="ts">
    2|   // The timeline along the bottom: every election from 1789 to 2024 as a
    3|   // detent on one slider. Drag or click anywhere on it (it snaps to the
    4|   // nearest election), or step with the arrow keys (Home and End for the
    5|   // ends). The story years are the taller ticks.
    6| 
    7|   interface Props {
    8|     years?: readonly number[];
    9|     value: number;
   10|     featured?: readonly number[];
   11|     /** A year's spoken / tooltip text. */
   12|     describe?: (y: number) => string;
   13|     disabled?: boolean;
   14|     /** The Rerun view: iOS dark colours. */
   15|     dark?: boolean;
   16|     /** A year was picked (dragged to, clicked, keyed). */
   17|     onchange?: (year: number) => void;
   18|     /** Dragging started (true) or stopped (false). */
   19|     onscrub?: (on: boolean) => void;
   20|   }
   21|   let {
   22|     years = [],
   23|     value,
   24|     featured = [],
   25|     describe = (y) => String(y),
   26|     disabled = false,
   27|     dark = false,
   28|     onchange,
   29|     onscrub,
   30|   }: Props = $props();
   31| 
   32|   const LABELS = [1800, 1850, 1900, 1950, 2000];
   33|   const first = $derived(years[0] ?? 0);
   34|   const last = $derived(years[years.length - 1] ?? 0);
   35|   const pos = (y: number) => ((y - first) / (last - first)) * 100;
   36| 
   37|   let rail = $state<HTMLElement | null>(null);
   38|   let thumb = $state<HTMLElement | null>(null);
   39|   let dragging = $state(false);
   40|   let hover = $state<number | null>(null);
   41|   const nearest = (x: number) => {
   42|     if (!rail) return value;
   43|     const r = rail.getBoundingClientRect();
   44|     const y = first + ((x - r.left) / r.width) * (last - first);
   45|     return years.reduce((b, e) => (Math.abs(e - y) < Math.abs(b - y) ? e : b), first);
   46|   };
   47|   const set = (y: number | undefined) => {
   48|     if (y !== undefined && y !== value && !disabled) onchange?.(y);
   49|   };
   50|   function down(e: PointerEvent & { currentTarget: HTMLElement }) {
   51|     if (e.button !== 0 || disabled) return;
   52|     dragging = true;
   53|     onscrub?.(true);
   54|     e.currentTarget.setPointerCapture?.(e.pointerId);
   55|     set(nearest(e.clientX));
   56|     thumb?.focus({ preventScroll: true });
   57|   }
   58|   function move(e: PointerEvent) {
   59|     const y = nearest(e.clientX);
   60|     if (dragging) set(y);
   61|     else hover = y;
   62|   }
   63|   function up() {
   64|     if (dragging) onscrub?.(false);
   65|     dragging = false;
   66|   }
   67|   function leave() {
   68|     if (!dragging) hover = null;
   69|   }
   70|   const step = (d: number) => {
   71|     const i = years.indexOf(value);
   72|     set(years[Math.max(0, Math.min(years.length - 1, i + d))]);
   73|   };
   74|   const STEPS: Readonly<Record<string, number>> = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1, PageDown: -5, PageUp: 5 };
   75|   function key(e: KeyboardEvent) {
   76|     const by = STEPS[e.key];
   77|     if (by) {
   78|       e.preventDefault();
   79|       e.stopPropagation();
   80|       step(by);
   81|     } else if (e.key === 'Home') {
   82|       e.preventDefault();
   83|       set(first);
   84|     } else if (e.key === 'End') {
   85|       e.preventDefault();
   86|       set(last);
   87|     }
   88|   }
   89|   function tipOf(): number | null {
   90|     if (dragging) return value;
   91|     return hover != null && hover !== value ? hover : null;
   92|   }
   93|   const tip = $derived(tipOf());
   94| </script>
   95| 
   96| <div class="bar" class:disabled class:dark>
   97|   <!-- svelte-ignore a11y_no_static_element_interactions -->
   98|   <div class="slider" class:dragging onpointerdown={down} onpointermove={move} onpointerup={up} onpointercancel={up} onpointerleave={leave}>
   99|     <div class="rail" bind:this={rail}>
  100|       <div class="fill" style:width="{pos(value)}%"></div>
  101|       {#each years as y (y)}
  102|         <span class="tick" class:story={featured.includes(y)} style:left="{pos(y)}%"></span>
  103|       {/each}
  104|       {#each LABELS as l (l)}
  105|         <span class="label" class:minor={l % 100 === 50} style:left="{pos(l)}%">{l}</span>
  106|       {/each}
  107|       <div
  108|         class="thumb"
  109|         bind:this={thumb}
  110|         role="slider"
  111|         tabindex={disabled ? -1 : 0}
  112|         aria-label="Election"
  113|         aria-valuemin={first}
  114|         aria-valuemax={last}
  115|         aria-valuenow={value}
  116|         aria-valuetext={describe(value)}
  117|         aria-disabled={disabled || undefined}
  118|         style:left="{pos(value)}%"
  119|         onkeydown={key}
  120|       ></div>
  121|       {#if tip != null}
  122|         <span class="tip" style:left="{pos(tip)}%">{describe(tip)}</span>
  123|       {/if}
  124|     </div>
  125|   </div>
  126| </div>
  127| 
  128| <style>
  129|   /* The tuned sizes (settled with the old ?tuneTimeline panel), in one place. */
  130|   .bar {
  131|     --thumb: 28px;
  132|     --track: 4px;
  133|     --tick: 4px;
  134|     --story-tick: 8px;
  135|     --label-size: 11px;
  136|     --label-gap: 20px;
  137|     --bar-height: 68px;
  138|     display: flex;
  139|     align-items: center;
  140|     gap: 14px;
  141|     max-width: 980px;
  142|     margin: 0 auto;
  143|     padding: 0 16px;
  144|     height: var(--bar-height);
  145|   }
  146|   /* The hit area is the whole band, not just the rail. */
  147|   .slider {
  148|     position: relative;
  149|     flex: 1;
  150|     min-width: 0;
  151|     height: 56px;
  152|     padding: 0 10px;
  153|     display: flex;
  154|     align-items: center;
  155|     cursor: pointer;
  156|     touch-action: none;
  157|     user-select: none;
  158|     -webkit-user-select: none;
  159|   }
  160|   .slider.dragging { cursor: grabbing; }
  161|   .rail {
  162|     position: relative;
  163|     width: 100%;
  164|     height: var(--track);
  165|     margin-top: -12px;
  166|     border-radius: 999px;
  167|     background: rgba(120, 120, 128, 0.2);   /* systemFill: the track */
  168|   }
  169|   /* The minimum track, in the tint (UISlider). */
  170|   .fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px; background: #007aff; }
  171|   .tick {
  172|     position: absolute;
  173|     top: 9px;
  174|     width: 1px;
  175|     height: var(--tick);
  176|     margin-left: -0.5px;
  177|     background: rgba(60, 60, 67, 0.29);    /* separator */
  178|     pointer-events: none;
  179|   }
  180|   .tick.story { height: var(--story-tick); width: 2px; margin-left: -1px; background: rgba(60, 60, 67, 0.6); border-radius: 1px; }
  181|   .label {
  182|     position: absolute;
  183|     top: var(--label-gap);
  184|     transform: translateX(-50%);
  185|     font-size: var(--label-size);
  186|     color: rgba(60, 60, 67, 0.6);           /* secondaryLabel */
  187|     font-variant-numeric: tabular-nums;
  188|     pointer-events: none;
  189|   }
  190|   .thumb {
  191|     position: absolute;
  192|     top: 50%;
  193|     /* UISlider's thumb: 28pt, white, a hairline and a soft double shadow. */
  194|     width: var(--thumb);
  195|     height: var(--thumb);
  196|     margin: calc(var(--thumb) / -2) 0 0 calc(var(--thumb) / -2);
  197|     border-radius: 999px;
  198|     background: #fff;
  199|     box-shadow: 0 0 0 0.5px rgba(0, 0, 0, 0.04), 0 3px 8px rgba(0, 0, 0, 0.15), 0 3px 1px rgba(0, 0, 0, 0.06);
  200|     cursor: grab;
  201|   }
  202|   .thumb:focus-visible { outline: 2px solid #3876b7; outline-offset: 2px; }
  203|   .tip {
  204|     position: absolute;
  205|     bottom: 20px;
  206|     transform: translateX(-50%);
  207|     padding: 4px 9px;
  208|     border-radius: 8px;
  209|     background: #fff;
  210|     color: #000;
  211|     white-space: nowrap;
  212|     font-size: 12px;
  213|     font-weight: 500;
  214|     font-variant-numeric: tabular-nums;
  215|     pointer-events: none;
  216|     box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12), 0 0 0 0.5px rgba(0, 0, 0, 0.06);
  217|   }
  218|   .disabled .slider { cursor: default; opacity: 0.5; }
  219|   /* Dark (Rerun): the same parts in iOS dark system colours — systemBlue
  220|      #0A84FF, the dark systemFill track, separator ticks, secondaryLabel. */
  221|   .dark .rail { background: rgba(120, 120, 128, 0.36); }
  222|   .dark .fill { background: #0a84ff; }
  223|   .dark .tick { background: rgba(84, 84, 88, 0.65); }
  224|   .dark .tick.story { background: rgba(235, 235, 245, 0.6); }
  225|   .dark .label { color: rgba(235, 235, 245, 0.6); }
  226|   .dark .tip { background: #2c2c2e; color: #fff; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4), 0 0 0 0.5px rgba(255, 255, 255, 0.08); }
  227|   /* A narrow window shows the year under the robot's opening message
  228|      instead (WhatIf .year-pill), not floating over the bar. */
  229|   @media (max-width: 760px) {
  230|     .tip { display: none; }
  231|   }
  232|   @media (max-width: 560px) {
  233|     .bar { gap: 4px; padding: 0 8px; }
  234|     .label.minor { display: none; }
  235|   }
  236| </style>
```

## `src/lib/simulacra/WhatIf.svelte`

```svelte
    1| <script lang="ts">
    2|   // Where you talk to the harness: it stands at the left (the page frames the
    3|   // 3D robot into the slot; a still of it stands in until the robot draws),
    4|   // says what it's doing in its bubble, and takes a what-if — a suggestion
    5|   // tapped, or your own words — and reruns the election with it. The
    6|   // bubble's working is WhatIfWorking; the chips, field and Rerun are
    7|   // WhatIfComposer.
    8|   import { onDestroy, untrack } from 'svelte';
    9|   import { STAGE_SIZE } from '$lib/robot/stage';
   10|   import Places from './Places.svelte';
   11|   import { hoverPlaces } from './places';
   12|   import type { WhatIf } from './schemas';
   13|   import type { Message, Still } from './whatif';
   14|   import WhatIfComposer from './WhatIfComposer.svelte';
   15|   import WhatIfWorking from './WhatIfWorking.svelte';
   16| 
   17|   interface Props {
   18|     name?: string;
   19|     /** The live robot is drawn in the slot. */
   20|     robotShown?: boolean;
   21|     /** A still of the robot, shown in the slot until the live robot draws. */
   22|     still?: Still | null;
   23|     /** The robot's spot (for the page to measure). */
   24|     slot?: HTMLElement | null;
   25|     message?: Message;
   26|     whatIfs?: readonly WhatIf[];
   27|     selected?: readonly string[];
   28|     /** An open group: its what-ifs stand out. */
   29|     slice?: string | null;
   30|     /** The typed what-if. */
   31|     value?: string;
   32|     running?: boolean;
   33|     canRun?: boolean;
   34|     canReset?: boolean;
   35|     /** The what-ifs in the rerun on show. */
   36|     ran?: readonly string[];
   37|     /** Something to run since that rerun. */
   38|     dirty?: boolean;
   39|     /** Nothing to rerun: no chips, no field. */
   40|     closed?: boolean;
   41|     /** The field. */
   42|     input?: HTMLInputElement | null;
   43|     ontoggle?: (key: string) => void;
   44|     onrun?: () => void;
   45|     onstop?: () => void;
   46|     onreset?: () => void;
   47|     /** A bubble action's key. */
   48|     onaction?: (key: string) => void;
   49|     onfocus?: (on: boolean) => void;
   50|     /** The year in words, shown under the opening message on a narrow window. */
   51|     caption?: string;
   52|   }
   53|   let {
   54|     name = 'Harness',
   55|     robotShown = false,
   56|     still = null,
   57|     slot = $bindable(null),
   58|     message = { text: '' },
   59|     whatIfs = [],
   60|     selected = [],
   61|     slice = null,
   62|     value = $bindable(''),
   63|     running = false,
   64|     canRun = true,
   65|     canReset = false,
   66|     ran = [],
   67|     dirty = true,
   68|     closed = false,
   69|     input = $bindable(null),
   70|     ontoggle,
   71|     onrun,
   72|     onstop,
   73|     onreset,
   74|     onaction,
   75|     onfocus,
   76|     caption = '',
   77|   }: Props = $props();
   78| 
   79|   // A long bubble: the Test Chat's More / Less (MechaHud .msg). Past CLAMP
   80|   // lines it shows its last CLAMP lines, the top fading out (the HUD's peek); a click opens it to its full
   81|   // height (capped at 46vh, then it scrolls, each edge feathering while
   82|   // there's more past it) and a click folds it back. A new message folds.
   83|   const CLAMP = 7;
   84|   // The tail only on a bubble no taller than the default one ("Change one
   85|   // thing about … / Pick a counterfactual…", 66px): anything bigger drops it.
   86|   const TAIL_MAX = 68;
   87|   // Less: one quiet move. The bubble shrinks while it's still lifted (its
   88|   // bottom fixed, so only its top eases down), the content held to its end as
   89|   // it goes; once it's at the folded height it drops back into the flow, where
   90|   // the room kept for it is exactly that height, so nothing jumps.
   91|   const CLOSE_MS = 240; // = .clip's max-height transition
   92|   // The clip's line height when it reads as `normal`, px.
   93|   const LINE_PX = 21;
   94| 
   95|   let clipEl = $state<HTMLElement | null>(null);
   96|   let bubbleEl = $state<HTMLElement | null>(null);
   97|   let over = $state(false);
   98|   let opened = $state(false);
   99|   let closing = $state(false);
  100|   let moreAbove = $state(false);
  101|   let moreBelow = $state(false);
  102|   /** The folded bubble's height, kept while it's opened. */
  103|   let holdH = $state(0);
  104|   /** CLAMP lines, px: the folded bubble's most (.clip), and the room a narrow window keeps for it (.hold). */
  105|   let lim = $state(CLAMP * LINE_PX);
  106|   let tall = $state(false);
  107|   let ro: ResizeObserver | null = null;
  108|   let closeTimer: ReturnType<typeof setTimeout> | undefined;
  109|   let pinFrame = 0;
  110| 
  111|   function sized(node: HTMLElement) {
  112|     const r = new ResizeObserver(() => {
  113|       tall = node.offsetHeight > TAIL_MAX;
  114|     });
  115|     r.observe(node);
  116|     return { destroy: () => r.disconnect() };
  117|   }
  118|   function measure() {
  119|     if (!clipEl) return;
  120|     const lh = Number.parseFloat(getComputedStyle(clipEl).lineHeight) || LINE_PX;
  121|     lim = Math.round(lh * CLAMP);
  122|     clipEl.style.setProperty('--full', `${clipEl.scrollHeight}px`);
  123|     over = clipEl.scrollHeight > lh * CLAMP + 2;
  124|     // Folded, it's the HUD's peek: the newest (the answer, or the step in
  125|     // hand) at the bottom, the earlier working fading out above it.
  126|     if (!opened) clipEl.scrollTop = clipEl.scrollHeight;
  127|     edges();
  128|   }
  129|   function edges() {
  130|     if (!clipEl || !opened) {
  131|       moreAbove = false;
  132|       moreBelow = false;
  133|       return;
  134|     }
  135|     moreAbove = clipEl.scrollTop > 1;
  136|     moreBelow = clipEl.scrollHeight - clipEl.scrollTop - clipEl.clientHeight > 1;
  137|   }
  138|   function clampable(node: HTMLElement) {
  139|     ro = new ResizeObserver(measure);
  140|     ro.observe(node);
  141|     for (const c of node.children) ro.observe(c);
  142|     document.fonts?.ready?.then(measure);
  143|     return { destroy: () => ro?.disconnect() };
  144|   }
  145|   const msgKey = $derived((message.text ?? '') + (message.quote ?? ''));
  146|   // Folded and finished, the bubble is just the answer: the working (steps,
  147|   // interviews) waits behind More. While the robot is working it shows live.
  148|   const working = $derived(!!message.busy);
  149|   const tucked = $derived(!working && !!(message.steps?.length || message.interview?.byWhatIf.length));
  150|   const canMore = $derived(over || tucked);
  151|   // A new message folds the bubble and lets go of any lit place.
  152|   $effect.pre(() => {
  153|     void msgKey;
  154|     untrack(() => {
  155|       opened = false;
  156|       closing = false;
  157|       hoverPlaces.set([]);
  158|       queueMicrotask(measure);
  159|     });
  160|   });
  161|   $effect.pre(() => {
  162|     void message.steps;
  163|     queueMicrotask(measure);
  164|   });
  165|   function pinEnd() {
  166|     if (clipEl) clipEl.scrollTop = clipEl.scrollHeight;
  167|     if (closing) pinFrame = requestAnimationFrame(pinEnd);
  168|   }
  169|   function toggleOpen() {
  170|     if (!canMore || closing || window.getSelection()?.toString()) return;
  171|     if (!opened) {
  172|       holdH = (bubbleEl?.getBoundingClientRect().height ?? 0) + 5; // exact (sub-pixel) + its 5px margin (the tail's room)
  173|       opened = true;
  174|       // Open: the newest (the end) stays in view; the bubble grows upward.
  175|       // The working appears now, so measure its full height, then hold the end in view.
  176|       requestAnimationFrame(() => {
  177|         measure();
  178|         if (clipEl) clipEl.scrollTop = clipEl.scrollHeight;
  179|         edges();
  180|       });
  181|       return;
  182|     }
  183|     closing = true;
  184|     moreAbove = false;
  185|     moreBelow = false;
  186|     pinEnd();
  187|     clearTimeout(closeTimer);
  188|     closeTimer = setTimeout(() => {
  189|       cancelAnimationFrame(pinFrame);
  190|       closing = false;
  191|       opened = false;
  192|       requestAnimationFrame(measure);
  193|     }, CLOSE_MS);
  194|   }
  195|   function more(e: MouseEvent) {
  196|     e.stopPropagation();
  197|     toggleOpen();
  198|   }
  199|   onDestroy(() => {
  200|     ro?.disconnect();
  201|     clearTimeout(closeTimer);
  202|     cancelAnimationFrame(pinFrame);
  203|   });
  204| </script>
  205| 
  206| <section class="whatif" aria-label="What if" style:--stage-w="{STAGE_SIZE.width}px">
  207|   <!-- The robot stands over this spot (drawn by the page's overlay, which
  208|        lets clicks through): pressing it is talking to it. -->
  209|   <button type="button" class="bot" bind:this={slot} aria-label="Election Sim Harness" title="Election Sim Harness"
  210|     disabled={closed || running} onclick={() => input?.focus()}>
  211|     {#if still}
  212|       <img class="still" class:gone={robotShown} src={still.src} alt="" draggable="false" decoding="async" fetchpriority="high"
  213|         style:left="calc(50% + {still.dx}px)" style:bottom="{still.db}px" style:width="{still.w}px" />
  214|     {/if}
  215|   </button>
  216|   <div class="talk">
  217|     <div class="hold" class:lifted={opened} style:height={opened ? `${holdH}px` : null} style:--lim="{lim}px">
  218|     <!-- svelte-ignore a11y_click_events_have_key_events -->
  219|     <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  220|     <div class="bubble" class:busy={message.busy} class:over={canMore} class:clamped={over} class:opened class:closing class:tall role="status" aria-live="polite" onclick={toggleOpen} bind:this={bubbleEl} use:sized>
  221|       <div class="clip" class:above={moreAbove} class:below={moreBelow} bind:this={clipEl} use:clampable onscroll={edges}>
  222|       <WhatIfWorking {message} {whatIfs} {working} {opened} onfold={() => requestAnimationFrame(() => { measure(); edges(); })} />
  223|       {#key msgKey}<div class="lines">
  224|       {#if message.quote}
  225|         <blockquote>“<Places text={message.quote} />”</blockquote>
  226|         {#if message.by}<p class="by"><Places text={message.by} /></p>{/if}
  227|       {/if}
  228|       {#if message.text}<p class="say" class:after={!!message.quote}><Places text={message.text} /></p>{/if}
  229|       {#if message.detail}<p class="aside"><Places text={message.detail} /></p>{/if}
  230|       {#if message.actions?.length}
  231|         <div class="acts">
  232|           {#each message.actions as a (a.key)}
  233|             <button type="button" class="act" class:primary={a.primary} onclick={() => onaction?.(a.key)}>{a.label}</button>
  234|           {/each}
  235|         </div>
  236|       {/if}
  237|       </div>{/key}
  238|       </div>
  239|       {#if canMore}<button type="button" class="more" aria-expanded={opened} onclick={more}>{opened ? 'Less' : 'More'}</button>{/if}
  240|     </div>
  241|     <!-- Narrow only: the time bar's tooltip, held here under the opening message. -->
  242|     {#if message.opening && caption}<span class="year-pill" aria-hidden="true">{caption}</span>{/if}
  243|     </div>
  244|     {#if !closed}
  245|       <WhatIfComposer {name} {whatIfs} {selected} {slice} {ran} bind:value bind:input {running} {canRun} {canReset} {dirty}
  246|         {ontoggle} {onrun} {onstop} {onreset} {onfocus} />
  247|     {:else}
  248|       <!-- An unopposed year: no chips or field, but on a narrow window their room stays. -->
  249|       <div class="composer-room" aria-hidden="true"></div>
  250|     {/if}
  251|   </div>
  252| </section>
  253| 
  254| <style>
  255|   /* Room for the robot to stand in, feet on the field's baseline. */
  256|   .whatif {
  257|     margin-top: -10px;
  258|     display: grid;
  259|     grid-template-columns: 168px minmax(0, 1fr);
  260|     align-items: end;
  261|     gap: 12px;
  262|     min-height: 220px;
  263|   }
  264|   /* The robot keeps its spot: a tall bubble grows the talk column downward, never moves the bot. */
  265|   .bot {
  266|     position: relative;
  267|     align-self: start;
  268|     height: 220px;
  269|     padding: 0;
  270|     border: none;
  271|     border-radius: 16px;
  272|     background: transparent;
  273|     cursor: pointer;
  274|   }
  275|   /* Tapping or clicking the robot is talking to it, not selecting it: no
  276|      tap highlight, no selection or callout on a long press, no focus ring
  277|      from a pointer (the keyboard's stays, below). */
  278|   .bot {
  279|     -webkit-tap-highlight-color: transparent;
  280|     -webkit-user-select: none;
  281|     user-select: none;
  282|     -webkit-touch-callout: none;
  283|   }
  284|   .bot:focus:not(:focus-visible) { outline: none; }
  285|   .bot:disabled { cursor: default; }
  286|   .bot:focus-visible { outline: 2px solid #3876b7; outline-offset: 2px; }
  287|   /* The still: under the live robot, faded out once it draws. */
  288|   .still { position: absolute; height: auto; max-width: none; pointer-events: none; transition: opacity 0.18s ease; }   /* = the page's .robot-host fade */
  289|   .still.gone { opacity: 0; }
  290|   :global(.sa.dark) .still { filter: invert(1) hue-rotate(180deg) saturate(66.7%); }
  291|   /* The what-if section in HIG light mode, after iOS Messages: the robot's
  292|      bubble is an incoming message, the what-ifs and field are Messages'
  293|      white capsules and hairlines, and the one accent is iMessage blue
  294|      (#007AFF), on Rerun as on the send button. Messages sets its grey
  295|      incoming bubble (#E9E9EB) on white; this page is already about that
  296|      grey (#e5e5e5, systemGray5), so the bubble takes the white step up
  297|      instead. Tokens (iOS system colours), read by the pieces too:
  298|        --label / --label-2 / --label-3   label, secondaryLabel, tertiaryLabel
  299|        --separator                       opaqueSeparator
  300|        --tint                            systemBlue */
  301|   .whatif {
  302|     --bubble: #fff;
  303|     --label: #000;
  304|     --label-2: rgba(60, 60, 67, 0.6);
  305|     --label-3: rgba(60, 60, 67, 0.3);
  306|     --separator: #c6c6c8;
  307|     --fill: #f2f2f7;             /* systemGray6: chips at rest, hovers */
  308|     --fill-press: #e5e5ea;       /* systemGray5: press */
  309|     --tint: #007aff;
  310|     /* Metrics, read by the pieces too. */
  311|     --control-h: 36px;           /* a chip, Rerun, and the field inside its hairline */
  312|     --hairline: 1px;             /* the field's ring */
  313|     --compose-gap: 8px;          /* the chips over the field */
  314|     --bubble-pad-top: 10px;
  315|     --bubble-pad-bottom: 11px;
  316|     --more-gap: 8px;             /* More / Less under the bubble's text */
  317|     --more-size: 12px;
  318|     --more-leading: 1.2;
  319|   }
  320|   /* The talk column fills the robot's height: the bubble pins to the top and
  321|      the composer to the floor, so a year with more chips or a longer line
  322|      never moves either while the time bar is scrubbed; a long bubble grows
  323|      the column downward, like any message. */
  324|   .talk { display: flex; flex-direction: column; gap: 12px; min-width: 0; align-self: stretch; }
  325|   .composer-room, .year-pill { display: none; }
  326|   /* Narrow windows (phones, or a narrow desktop window): the what-if takes
  327|      the full width and the robot stands above it. Every part of the what-if
  328|      that varies holds its most, so nothing moves with the year or the
  329|      message. Opened, the bubble grows over the chips and field. */
  330|   @media (max-width: 760px) {
  331|     /* Narrow: Who voted, then the robot, then the bubble, the chips and the
  332|        field, top to bottom; the robot --robot-gap under the last group and
  333|        over the bubble, whatever the screen. The robot's figure doesn't fill
  334|        its slot: --figure-head is how far under the slot's top its head reads,
  335|        seen from the last group's dots, and --figure-toes how far past the
  336|        slot's floor its toes reach, seen from the bubble. Both were measured
  337|        on screen at its narrow rest (stage.ts NARROW_ROBOT_YAW); re-measure
  338|        them if the model, its framing (RobotStage STILLS) or that turn
  339|        changes. The slot is the robot's width (STAGE_SIZE) by --slot-h. */
  340|     .whatif {
  341|       --robot-gap: 12px;
  342|       --figure-head: 50px;
  343|       --figure-toes: 8px;
  344|       --slot-h: 236px;
  345|       display: flex;
  346|       flex-direction: column;
  347|       align-items: stretch;
  348|       gap: 0;
  349|       min-height: 0;
  350|       margin-top: 0;
  351|       /* A horizontal drag on the robot turns it; a vertical one scrolls. */
  352|       touch-action: pan-y pinch-zoom;
  353|       /* The robot stands over this area too: no tap highlight on it. */
  354|       -webkit-tap-highlight-color: transparent;
  355|     }
  356|     .bot { width: var(--stage-w); height: var(--slot-h); margin: calc(var(--robot-gap) - var(--figure-head)) 0 0; align-self: center; }
  357|     .talk { position: relative; z-index: 1; min-width: 0; margin-top: calc(var(--robot-gap) + var(--figure-toes)); }
  358|     /* The bubble's room is its folded most (CLAMP lines and More) and it sits
  359|        at the room's top, just under the robot, so the robot's gap holds for
  360|        any message; a shorter one leaves the room under it, so the chips and
  361|        field never move. Opened, it grows down over them. */
  362|     .hold {
  363|       min-height: calc(var(--bubble-pad-top) + var(--lim) + var(--more-gap) + var(--more-size) * var(--more-leading) + var(--bubble-pad-bottom));
  364|       justify-content: flex-start;
  365|     }
  366|     .hold.lifted .bubble { top: 0; bottom: auto; }
  367|     /* As tall as the chips and the field (WhatIfComposer). */
  368|     .composer-room { display: block; height: calc(2 * var(--control-h) + 2 * var(--hairline) + var(--compose-gap)); }
  369|     /* The time bar's tooltip (TimeBar .tip, same size, padding and look),
  370|        solid under the opening message instead of floating over the bar.
  371|        It fits in the bubble's room, so nothing moves when it goes. */
  372|     .year-pill {
  373|       display: inline-block;
  374|       align-self: center;
  375|       margin-top: 8px;
  376|       padding: 4px 9px;
  377|       border-radius: 8px;
  378|       background: #fff;
  379|       color: #000;
  380|       white-space: nowrap;
  381|       font-size: 12px;
  382|       font-weight: 500;
  383|       font-variant-numeric: tabular-nums;
  384|       box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12), 0 0 0 0.5px rgba(0, 0, 0, 0.06);
  385|     }
  386|     /* A newline in the bubble's aside breaks here (a wide window reads it as a space). */
  387|     .aside { white-space: pre-line; }
  388|     /* The tail pointed at the robot beside the bubble; it stands above now. */
  389|     .bubble::after { display: none; }
  390|   }
  391|   /* Opened (More), the bubble leaves the flow: its slot keeps the folded
  392|      height, so nothing below or around moves, and the bubble grows upward
  393|      from the slot's bottom, over the page above. The bubble's column is the
  394|      container its sections query (the bubble itself shrinks to fit, so it
  395|      can't be one): 472px = 440px of text + its padding. */
  396|   .hold { position: relative; container-type: inline-size; display: flex; flex-direction: column; align-items: flex-start; width: 100%; }
  397|   .hold.lifted .bubble { position: absolute; left: 0; right: 0; bottom: 5px; z-index: 2; margin-bottom: 0; }
  398|   /* The robot's bubble: Messages' shape and tail, flat (no shadow). */
  399|   /* Always the column's full width, however short the message. */
  400|   .bubble {
  401|     position: relative;
  402|     align-self: stretch;
  403|     margin-bottom: 5px;
  404|     padding: var(--bubble-pad-top) 16px var(--bubble-pad-bottom);
  405|     border-radius: 20px;
  406|     background: var(--bubble);
  407|     color: var(--label);
  408|     transition: opacity 0.2s ease;
  409|   }
  410|   .bubble.busy { opacity: 0.85; }
  411|   /* Rerun: lit from above. The page is inverted there (theme.css), so a
  412|      dark inset and sheen on the white bubble render as a white top hairline
  413|      and a faint highlight on the dark one. */
  414|   :global(.sa.dark) .bubble {
  415|     box-shadow: inset 0 1px 0 rgba(0, 0, 0, 0.22);
  416|     background-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.045), rgba(0, 0, 0, 0) 45%);
  417|   }
  418|   .bubble.tall::after { display: none; }
  419|   /* The Test Chat's tail (MechaHud .msg--you.tail), mirrored to the left,
  420|      filled with --bubble (#fff). */
  421|   .bubble::after {
  422|     content: '';
  423|     position: absolute;
  424|     left: 6px;
  425|     bottom: -5px;
  426|     width: 14px;
  427|     height: 8px;
  428|     transform: scaleX(-1);
  429|     background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 93 76'%3E%3Cpath d='M-0.000,27.000 C12.839,31.371 39.956,53.698 40.1000,53.1000 C47.980,58.824 74.560,73.398 80.000,75.000 C85.440,76.602 89.403,76.321 92.156,73.836 C92.113,73.760 94.162,69.566 91.1000,64.1000 C88.060,59.218 84.265,53.211 82.000,49.000 C78.871,45.122 75.825,34.278 76.000,30.000 C75.936,25.444 77.127,19.864 78.1000,15.1000 C80.494,12.811 79.838,10.855 87.1000,2.1000 C64.644,-3.831 32.484,7.267 -0.000,27.000 Z' fill='%23fff'/%3E%3C/svg%3E") no-repeat 0 0 / 100% 100%;
  430|     pointer-events: none;
  431|   }
  432|   /* More / Less (MechaHud .msg): clamped with a fade; opened to its height,
  433|      then scrolling with feathered edges (@property, so they ease). */
  434|   @property --ft { syntax: '<length>'; inherits: false; initial-value: 0px; }
  435|   @property --fb { syntax: '<length>'; inherits: false; initial-value: 0px; }
  436|   .clip { max-height: var(--lim, none); overflow: hidden; transition: max-height 0.24s cubic-bezier(0.2, 0.9, 0.3, 1), --ft 0.3s ease, --fb 0.3s ease; }
  437|   .bubble.over { cursor: pointer; }
  438|   .bubble.clamped:not(.opened) .clip { -webkit-mask-image: linear-gradient(to top, #000 55%, transparent); mask-image: linear-gradient(to top, #000 55%, transparent); }
  439|   .bubble.opened .clip {
  440|     --band: 28px;
  441|     max-height: min(var(--full), 46vh);
  442|     overflow-y: auto;
  443|     overscroll-behavior: contain;
  444|     scrollbar-width: none;
  445|     -webkit-mask-image: linear-gradient(to bottom, transparent calc(var(--ft) - var(--band)), #000 var(--ft), #000 calc(100% - var(--fb)), transparent calc(100% - var(--fb) + var(--band)));
  446|     mask-image: linear-gradient(to bottom, transparent calc(var(--ft) - var(--band)), #000 var(--ft), #000 calc(100% - var(--fb)), transparent calc(100% - var(--fb) + var(--band)));
  447|   }
  448|   .bubble.opened .clip::-webkit-scrollbar { display: none; }
  449|   .clip.above { --ft: var(--band); }
  450|   .clip.below { --fb: var(--band); }
  451|   /* Less: back to the folded height, still lifted, on the same ease. */
  452|   .bubble.closing .clip { transition: max-height 0.24s cubic-bezier(0.4, 0, 0.2, 1); max-height: var(--lim); overflow: hidden; -webkit-mask-image: linear-gradient(to top, #000 55%, transparent); mask-image: linear-gradient(to top, #000 55%, transparent); }
  453|   .more { display: block; margin: var(--more-gap) 0 0; padding: 0; border: none; background: none; font: inherit; font-size: var(--more-size); font-weight: 500; line-height: var(--more-leading); color: var(--tint); cursor: pointer; }
  454|   .more:hover { opacity: 0.7; }
  455|   .more:focus-visible { outline: 2px solid #3876b7; outline-offset: 2px; border-radius: 4px; }
  456|   .lines { animation: float-in 0.32s cubic-bezier(0.2, 0.9, 0.3, 1.2); }
  457|   @keyframes float-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
  458|   .say { position: relative; margin: 0; font-size: 15px; line-height: 1.42; letter-spacing: -0.005em; color: var(--label); }
  459|   .say.after { margin-top: 8px; font-size: 13px; color: var(--label-2); }
  460|   blockquote { margin: 2px 0 0; font-size: 15px; line-height: 1.45; font-style: italic; color: var(--label); }
  461|   .by { margin: 6px 0 0; font-size: 12.5px; color: var(--label-2); }
  462|   .aside { margin: 6px 0 0; font-size: 12.5px; line-height: 1.4; color: var(--label-2); }
  463|   .acts { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
  464|   /* In the bubble: tinted text buttons on a hairline, the primary filled. */
  465|   .act {
  466|     height: 30px;
  467|     padding: 0 13px;
  468|     border: 1px solid var(--separator);
  469|     border-radius: 999px;
  470|     background: transparent;
  471|     color: var(--tint);
  472|     font: inherit;
  473|     font-size: 13px;
  474|     cursor: pointer;
  475|   }
  476|   .act:hover { background: var(--fill); }
  477|   .act:active { background: var(--fill-press); }
  478|   .act.primary { background: var(--tint); border-color: var(--tint); color: #fff; }
  479|   .act.primary:hover { background: #0071eb; }
  480|   .act.primary:active { background: #0062cc; }
  481|   .act:focus-visible { outline: 2px solid #3876b7; outline-offset: 2px; }
  482|   /* Under the Rerun view's invert (.sa.dark) the tint would come out cyan
  483|      and white labels black: the accent-coloured parts are turned back (as
  484|      the photos are) and take dark mode's systemBlue. */
  485|   :global(.sa.dark) .whatif { --tint: #0a84ff; }
  486|   :global(.sa.dark) .act.primary { filter: invert(1) hue-rotate(180deg) saturate(66.7%); }
  487|   @media (prefers-reduced-motion: reduce) {
  488|     .bubble { transition: none; }
  489|     .lines { animation: none; }
  490|     .clip { transition: none; }
  491|   }
  492| </style>
```

## `src/lib/simulacra/WhatIfComposer.svelte`

```svelte
    1| <script lang="ts">
    2|   // The what-if composer: the suggestions (KindChips) on one row, scrolled
    3|   // sideways, its edges fading where there's more past them (the right edge
    4|   // is Rerun's); your own what-if, the field and Rerun, on the row beneath.
    5|   import { Square } from 'lucide-svelte';
    6|   import KindChips from './KindChips.svelte';
    7|   import { RUN_LIMITS, type WhatIf } from './schemas';
    8| 
    9|   interface Props {
   10|     /** The harness's name, for the field's label. */
   11|     name: string;
   12|     whatIfs?: readonly WhatIf[];
   13|     selected?: readonly string[];
   14|     slice?: string | null;
   15|     ran?: readonly string[];
   16|     /** The typed what-if. */
   17|     value?: string;
   18|     /** The field, for the page to focus. */
   19|     input?: HTMLInputElement | null;
   20|     running?: boolean;
   21|     canRun?: boolean;
   22|     canReset?: boolean;
   23|     /** Something to run since the rerun on show. */
   24|     dirty?: boolean;
   25|     ontoggle?: (key: string) => void;
   26|     onrun?: () => void;
   27|     onstop?: () => void;
   28|     onreset?: () => void;
   29|     onfocus?: (on: boolean) => void;
   30|   }
   31|   let {
   32|     name,
   33|     whatIfs = [],
   34|     selected = [],
   35|     slice = null,
   36|     ran = [],
   37|     value = $bindable(''),
   38|     input = $bindable(null),
   39|     running = false,
   40|     canRun = true,
   41|     canReset = false,
   42|     dirty = true,
   43|     ontoggle,
   44|     onrun,
   45|     onstop,
   46|     onreset,
   47|     onfocus,
   48|   }: Props = $props();
   49| 
   50|   function submit(e: SubmitEvent) {
   51|     e.preventDefault();
   52|     if (running) onstop?.();
   53|     else onrun?.();
   54|   }
   55| </script>
   56| 
   57| <form class="compose" aria-label="What-ifs" onsubmit={submit}>
   58|   <KindChips {whatIfs} {selected} {ran} {slice} {running} {ontoggle} />
   59|   <span class="ask">
   60|     <input
   61|       bind:this={input}
   62|       bind:value
   63|       type="text"
   64|       placeholder="What if…"
   65|       maxlength={RUN_LIMITS.text}
   66|       aria-label="Tell {name} what to change"
   67|       autocomplete="off"
   68|       enterkeyhint="go"
   69|       disabled={running}
   70|       onfocus={() => onfocus?.(true)}
   71|       onblur={() => onfocus?.(false)}
   72|     />
   73|     {#if canReset && !running}
   74|       <button type="button" class="reset" onclick={() => onreset?.()}>Reset</button>
   75|     {/if}
   76|     <button type="submit" class="run" class:rest={!dirty && !running} disabled={!running && !canRun}>
   77|       {#if running}<Square size={11} strokeWidth={0} fill="currentColor" aria-hidden="true" /> Stop{:else}Rerun{/if}
   78|     </button>
   79|   </span>
   80| </form>
   81| 
   82| <style>
   83|   /* The suggestions above, the field and Rerun beneath: both rows the
   84|      column's full width, so the chip row ends at Rerun's right edge. */
   85|   /* The composer pins to the column's floor (WhatIf .talk). */
   86|   .compose { display: flex; flex-direction: column; align-items: stretch; gap: var(--compose-gap); min-width: 0; margin-top: auto; }
   87|   .ask { display: flex; align-items: center; gap: 8px; min-width: 0; }
   88|   /* The field: Messages' entry capsule — white, an opaqueSeparator
   89|      hairline, a blue caret — whose ring turns the tint while typing (the
   90|      creator-rows search field's behaviour). */
   91|   input {
   92|     flex: 1;
   93|     min-width: 0;
   94|     height: var(--control-h);
   95|     padding: 0 14px;
   96|     border: var(--hairline) solid var(--separator);
   97|     border-radius: 999px;
   98|     background: #fff;
   99|     color: var(--label);
  100|     caret-color: var(--tint);
  101|     font: inherit;
  102|     font-size: 15px;
  103|     transition: border-color 0.15s ease;
  104|   }
  105|   input::placeholder { color: var(--label-3); }
  106|   input:focus { outline: none; border-color: var(--tint); }
  107|   input:disabled { opacity: 0.6; }
  108|   /* Rerun: the send button — filled systemBlue, white, regular weight. */
  109|   .run {
  110|     display: inline-flex;
  111|     align-items: center;
  112|     gap: 6px;
  113|     height: var(--control-h);
  114|     padding: 0 18px;
  115|     border: none;
  116|     border-radius: 999px;
  117|     background: var(--tint);
  118|     color: #fff;
  119|     font: inherit;
  120|     font-size: 15px;
  121|     font-weight: 400;
  122|     cursor: pointer;
  123|     transition: background-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1.3); /* = KindChips .chip */
  124|   }
  125|   /* Hover and press as the chips have them (KindChips): a hairline ring on
  126|      hover, a press that shrinks it. On blue the ring is light, to show. */
  127|   @media (hover: hover) {
  128|     .run:hover:not(:disabled) { box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.45); }
  129|     .run.rest:hover:not(:disabled) { box-shadow: inset 0 0 0 1px rgba(0, 122, 255, 0.2); }
  130|   }
  131|   .run:active:not(:disabled) { background: #0062cc; transform: scale(0.97); box-shadow: none; }
  132|   .run:disabled { opacity: 0.35; cursor: default; background: var(--tint); }
  133|   /* Nothing new to run: at rest, a gray button (pressing it shows the rerun
  134|      already made). It fills blue again as soon as there's a change. */
  135|   .run.rest { background: var(--fill); color: var(--label); }
  136|   .run.rest:active:not(:disabled) { background: var(--fill-press); }
  137|   /* Reset: a plain text button in the tint. */
  138|   .reset {
  139|     height: var(--control-h);
  140|     padding: 0 10px;
  141|     border: none;
  142|     background: transparent;
  143|     color: var(--tint);
  144|     font: inherit;
  145|     font-size: 12px;
  146|     cursor: pointer;
  147|     border-radius: 10px;
  148|   }
  149|   .reset:hover { background: rgba(0, 122, 255, 0.08); }
  150|   .reset:active { opacity: 0.6; }
  151|   .run:focus-visible, .reset:focus-visible { outline: 2px solid #3876b7; outline-offset: 2px; }
  152|   /* Under the Rerun view's invert the accent-coloured parts are turned back
  153|      (as the photos are) and take dark mode's systemBlue. */
  154|   :global(.sa.dark) .run:not(.rest),
  155|   :global(.sa.dark) .reset { filter: invert(1) hue-rotate(180deg) saturate(66.7%); }
  156|   @media (prefers-reduced-motion: reduce) { .run { transition: none; } }
  157| </style>
```

## `src/lib/simulacra/WhatIfWorking.svelte`

```svelte
    1| <script lang="ts">
    2|   // The robot's working, inside its bubble (WhatIf.svelte): the steps (live,
    3|   // a mark per step; finished and opened, label / text rows), and, opened,
    4|   // the interviews behind the rerun and what it drew on.
    5|   import { Check, ChevronDown } from 'lucide-svelte';
    6|   import Places from './Places.svelte';
    7|   import type { InterviewAnswer, WhatIf } from './schemas';
    8|   import { day, type Message, peopleIn, splitStep } from './whatif';
    9| 
   10|   interface Props {
   11|     message: Message;
   12|     whatIfs?: readonly WhatIf[];
   13|     /** The robot is working: the steps show live. */
   14|     working?: boolean;
   15|     /** The bubble is opened (More). */
   16|     opened?: boolean;
   17|     /** The Sources fold opened or closed: the bubble's height changed. */
   18|     onfold?: () => void;
   19|   }
   20|   let { message, whatIfs = [], working = false, opened = false, onfold }: Props = $props();
   21| 
   22|   // The Sources fold: closed until asked for, and kept as left across messages.
   23|   let sourcesOpen = $state(false);
   24| 
   25|   const labelOf = (key: string) => whatIfs.find((x) => x.key === key)?.label || key;
   26|   /** A person's two rows: as it was, and in the rerun. */
   27|   const sides = (a: InterviewAnswer) =>
   28|     [
   29|       { tag: 'Historic', x: a.before },
   30|       { tag: 'Rerun', x: a.after },
   31|     ] as const;
   32| </script>
   33| 
   34| {#if message.steps?.length && (working || opened)}
   35|   <!-- The working: while live, a mark per step; opened and finished, a
   36|        section of label / text rows (a step's "Label: text" split). -->
   37|   <section class="sec" class:live={working} aria-label="How I got this">
   38|     {#if !working}<h3 class="sec-h">How I got this</h3>{/if}
   39|     <ol class="steps">
   40|       {#each message.steps as st, i (i + st.text)}
   41|         {@const s = splitStep(st.text)}
   42|         <li class={st.state} class:bare={!s.label}>
   43|           {#if working}<span class="mark" aria-hidden="true">{#if st.state === 'done'}<Check size={11} strokeWidth={2.6} />{:else}<i></i>{/if}</span>{/if}
   44|           {#if s.label}<span class="k">{s.label}</span>{/if}
   45|           <span class="v"><Places text={s.body} /></span>
   46|         </li>
   47|       {/each}
   48|     </ol>
   49|   </section>
   50| {/if}
   51| {#if opened && message.interview?.byWhatIf.length}
   52|   <!-- The interviews behind the rerun: grouped by what-if (when there's
   53|        more than one), then by the wording of the question; each person a
   54|        header line and two rows, Historic and Rerun. -->
   55|   {@const iv = message.interview}
   56|   {@const many = iv.byWhatIf.length > 1}
   57|   <section class="sec iv" aria-label="Interviews">
   58|     <h3 class="sec-h">Interviews<span class="sec-n">{peopleIn(iv)} people</span></h3>
   59|     {#each iv.byWhatIf as w (w.whatIf)}
   60|       <div class="iv-w">
   61|       {#if many}<h4 class="iv-wh">{labelOf(w.whatIf)}</h4>{/if}
   62|       {#each iv.questions as q, qi (qi)}
   63|         {@const asked = w.answers.filter((a) => a.question === qi)}
   64|         {#if asked.length}
   65|           <div class="iv-g">
   66|             <p class="iv-q">“{q}”</p>
   67|             <ul class="iv-a">
   68|               {#each asked as a (a.name + a.line)}
   69|                 {@const moved = a.after.choice !== a.before.choice}
   70|                 <li class:misread={a.misread}>
   71|                   <p class="iv-who">
   72|                     <span><b>{a.name}</b> <Places text={a.line} /> · <Places text={a.cohort} /></span>
   73|                     {#if a.misread}<em class="iv-flag">Misread the news</em>{:else if moved}<em class="iv-flag moved">Changed</em>{/if}
   74|                   </p>
   75|                   <dl class="iv-rows">
   76|                     {#each sides(a) as { tag, x } (tag)}
   77|                       <dt>{tag}</dt>
   78|                       <dd class="iv-c">{x.choice}{#if x.pVote != null}<small>{x.pVote}% likely</small>{/if}</dd>
   79|                       <dd class="iv-say">“<Places text={x.quote} />”</dd>
   80|                     {/each}
   81|                   </dl>
   82|                 </li>
   83|               {/each}
   84|             </ul>
   85|           </div>
   86|         {/if}
   87|       {/each}
   88|       </div>
   89|     {/each}
   90|   </section>
   91| {/if}
   92| {#if opened && message.sources}
   93|   <!-- What the rerun drew on: the dated newspapers in the voters' briefs
   94|        (each summarized in a line), the research behind the change, and
   95|        the data. A short key column (date, year) and the line beside it. -->
   96|   {@const src = message.sources}
   97|   <details class="sec src" aria-label="Sources" bind:open={sourcesOpen} ontoggle={() => onfold?.()}>
   98|     <!-- A click here folds the list, not the whole bubble. -->
   99|     <summary class="sec-h src-sum" onclick={(e) => e.stopPropagation()}>
  100|       <span>Sources</span><span class="src-chev" aria-hidden="true"><ChevronDown size={12} strokeWidth={2.25} /></span>
  101|     </summary>
  102|     {#if src.reading.length}
  103|       <div class="src-g">
  104|         <h4 class="src-h">Newspapers the voters read<span class="sec-n">{src.reading.length}</span></h4>
  105|         <ul class="src-l">
  106|           {#each src.reading as r, i (i)}
  107|             <li><span class="src-k">{day(r.date)}</span><span class="src-v"><Places text={r.summary || r.newspaper} /><small>{r.newspaper}, {r.place}</small></span></li>
  108|           {/each}
  109|         </ul>
  110|       </div>
  111|     {/if}
  112|     {#if src.research.length}
  113|       <div class="src-g">
  114|         <h4 class="src-h">Research<span class="sec-n">{src.research.length} findings</span></h4>
  115|         <ul class="src-l">
  116|           {#each src.research as r, i (i)}
  117|             <li><span class="src-k">{r.when}</span><span class="src-v"><Places text={r.text} /></span></li>
  118|           {/each}
  119|         </ul>
  120|       </div>
  121|     {/if}
  122|     {#if src.data.length}
  123|       <div class="src-g">
  124|         <h4 class="src-h">Data</h4>
  125|         <ul class="src-l plain">
  126|           {#each src.data as t, i (i)}<li><span class="src-v">{t}</span></li>{/each}
  127|         </ul>
  128|       </div>
  129|     {/if}
  130|   </details>
  131| {/if}
  132| 
  133| <style>
  134|   /* The opened bubble's sections (the working, the interviews), each closed
  135|      by a hairline above the answer. One type scale throughout:
  136|        section title   13 / 600 / label
  137|        row label       12 / 500 / label-2   (step labels, Historic / Rerun)
  138|        text            13 / 400 / label
  139|        meta            12 / 400 / label-2 */
  140|   .sec { margin: 0 0 14px; padding: 2px 0 14px; border-bottom: 0.5px solid var(--separator); }
  141|   .sec.live { margin-bottom: 10px; padding: 0 0 10px; }
  142|   .sec-h { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: 0 0 10px; font-size: 13px; font-weight: 600; line-height: 1.3; letter-spacing: -0.005em; color: var(--label); }
  143|   .sec-n { font-size: 12px; font-weight: 400; color: var(--label-2); font-variant-numeric: tabular-nums; }
  144|   /* The working: label / text rows on one grid, so every label shares a
  145|      column. Live, a mark leads each row: a check when done, a breathing dot
  146|      on the step in hand. */
  147|   .steps {
  148|     list-style: none;
  149|     margin: 0;
  150|     padding: 0;
  151|     display: grid;
  152|     grid-template-columns: fit-content(10em) minmax(0, 1fr);
  153|     column-gap: 14px;
  154|     row-gap: 7px;
  155|     align-items: baseline;
  156|   }
  157|   .live .steps { grid-template-columns: 14px fit-content(10em) minmax(0, 1fr); column-gap: 8px; row-gap: 4px; }
  158|   .steps li { display: contents; }
  159|   .steps .k { grid-column: -3; font-size: 12px; font-weight: 500; line-height: 1.45; color: var(--label-2); }
  160|   .steps .v { grid-column: -2; font-size: 13px; line-height: 1.45; color: var(--label); }
  161|   .steps .bare .v { grid-column: -3 / -1; }
  162|   .live .steps .k, .live .steps .v { font-size: 12.5px; line-height: 1.4; color: var(--label-2); }
  163|   .live .steps .doing .k, .live .steps .doing .v { color: var(--label); }
  164|   .steps .k, .steps .v, .steps .mark { animation: float-in 0.28s cubic-bezier(0.2, 0.9, 0.3, 1.2); }
  165|   .sec:not(.live) .steps .k, .sec:not(.live) .steps .v { animation: none; }
  166|   .steps .mark { grid-column: 1; align-self: start; display: inline-flex; align-items: center; justify-content: center; height: 17.5px; color: var(--tint); }
  167|   /* Narrow, finished: each label over its text (the bubble's column, WhatIf .hold, is the container). */
  168|   @container (max-width: 472px) {
  169|     .sec:not(.live) .steps { grid-template-columns: minmax(0, 1fr); row-gap: 1px; }
  170|     .sec:not(.live) .steps .k, .sec:not(.live) .steps .v, .sec:not(.live) .steps .bare .v { grid-column: 1; }
  171|     .sec:not(.live) .steps li:not(:first-child) > :first-child { margin-top: 8px; }
  172|   }
  173|   .steps .mark i { width: 6px; height: 6px; border-radius: 999px; background: var(--tint); animation: breathe 1s ease-in-out infinite; }
  174|   @keyframes breathe { 50% { opacity: 0.25; transform: scale(0.7); } }
  175|   @keyframes float-in { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
  176|   /* The interviews. A what-if (when there's more than one) heads its own
  177|      block; each wording of the question heads its people, in italics; each
  178|      person is a header line (name, who they are, and — right-aligned, the
  179|      only accent — Changed) over a three-column grid: Historic / Rerun, the
  180|      vote and its likelihood, then their words. Hairlines between people. */
  181|   .iv-w + .iv-w { margin-top: 18px; }
  182|   .iv-wh { margin: 0 0 2px; font-size: 12px; font-weight: 600; line-height: 1.3; color: var(--label-2); }
  183|   .iv-g + .iv-g { margin-top: 20px; }
  184|   .iv-q { margin: 0 0 2px; font-size: 12.5px; line-height: 1.4; font-style: italic; color: var(--label-2); }
  185|   .iv-a { list-style: none; margin: 0; padding: 0; }
  186|   .iv-a li { padding: 10px 0; }
  187|   .iv-a li + li { border-top: 0.5px solid var(--separator); }
  188|   .iv-a li:last-child { padding-bottom: 0; }
  189|   .iv-a li.misread { opacity: 0.5; }
  190|   .iv-who { display: flex; align-items: baseline; gap: 12px; margin: 0 0 6px; font-size: 12px; line-height: 1.4; color: var(--label-2); }
  191|   .iv-who > span { min-width: 0; }
  192|   .iv-who b { margin-right: 2px; font-size: 13px; font-weight: 600; color: var(--label); }
  193|   .iv-flag { flex: none; margin-left: auto; font-size: 12px; font-style: normal; font-weight: 500; color: var(--label-2); }
  194|   .iv-flag.moved { color: var(--tint); }
  195|   .iv-rows { display: grid; grid-template-columns: 52px 84px minmax(0, 1fr); column-gap: 12px; row-gap: 6px; align-items: baseline; margin: 0; }
  196|   .iv-rows dt { font-size: 12px; font-weight: 500; line-height: 1.45; color: var(--label-2); }
  197|   .iv-rows dd { margin: 0; }
  198|   .iv-c { font-size: 13px; font-weight: 500; line-height: 1.45; color: var(--label); }
  199|   .iv-c small { display: block; font-size: 11.5px; font-weight: 400; line-height: 1.3; color: var(--label-2); font-variant-numeric: tabular-nums; }
  200|   .iv-say { font-size: 13px; line-height: 1.45; color: var(--label); }
  201|   /* Narrow: the words drop under the vote, in the vote's column. */
  202|   @container (max-width: 472px) {
  203|     .iv-rows { grid-template-columns: 52px minmax(0, 1fr); row-gap: 2px; }
  204|     .iv-say { grid-column: 2; margin-bottom: 6px; }
  205|     .iv-c small { display: inline; margin-left: 6px; }
  206|   }
  207|   /* Sources: subsections under the section title, each a quiet header (and
  208|      count) over key / line rows: a newspaper's date, its one-line summary and,
  209|      beneath, the paper; a finding's year and claim; the data, one per row. */
  210|   .src-g + .src-g { margin-top: 18px; }
  211|   .src-sum { cursor: pointer; list-style: none; user-select: none; align-items: center; gap: 6px; margin: 0; }
  212|   .src-sum::-webkit-details-marker { display: none; }
  213|   .src-sum:hover { opacity: 0.75; }
  214|   .src-sum:focus-visible { outline: 2px solid #3876b7; outline-offset: 2px; border-radius: 4px; }
  215|   .src-chev { display: inline-flex; color: var(--label-2); transition: transform 0.18s ease; }
  216|   details[open] > .src-sum { margin-bottom: 10px; }
  217|   details[open] > .src-sum .src-chev { transform: rotate(180deg); }
  218|   .src-h { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: 0 0 8px; font-size: 12px; font-weight: 600; line-height: 1.3; color: var(--label-2); }
  219|   .src-l { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: fit-content(6.5em) minmax(0, 1fr); column-gap: 14px; row-gap: 9px; align-items: baseline; }
  220|   .src-l li { display: contents; }
  221|   .src-k { grid-column: 1; font-size: 12px; font-weight: 500; line-height: 1.45; color: var(--label-2); font-variant-numeric: tabular-nums; }
  222|   .src-v { grid-column: 2; font-size: 13px; line-height: 1.45; color: var(--label); }
  223|   .src-v small { display: block; margin-top: 1px; font-size: 12px; line-height: 1.35; color: var(--label-2); }
  224|   .src-l.plain { grid-template-columns: minmax(0, 1fr); row-gap: 5px; }
  225|   .src-l.plain .src-v { grid-column: 1; font-size: 12.5px; color: var(--label-2); }
  226|   /* In the working (steps, interviews) every place is dotted in the text's own
  227|      colour; blue is kept for states in the message itself. */
  228|   :global(.sa .whatif) .steps :global(.place), :global(.sa .whatif) .iv :global(.place), :global(.sa .whatif) .src :global(.place) { text-decoration-color: currentColor; }
  229|   @media (prefers-reduced-motion: reduce) {
  230|     .src-chev { transition: none; }
  231|     .steps .k, .steps .v, .steps .mark { animation: none; }
  232|     .steps .mark i { animation: none; }
  233|   }
  234| </style>
```

## `src/lib/simulacra/accessKey.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { ACCESS_KEY_STORAGE, findAccessKey, type KeyStorage, splitHash } from './accessKey';
    3| 
    4| const KEY = 'abcDEF0123456789_-xy';
    5| 
    6| /** sessionStorage's two calls over a Map. */
    7| function memoryStorage(initial: Record<string, string> = {}) {
    8|   const items = new Map(Object.entries(initial));
    9|   const storage: KeyStorage = {
   10|     getItem: (k) => items.get(k) ?? null,
   11|     setItem: (k, v) => {
   12|       items.set(k, v);
   13|     },
   14|   };
   15|   return { items, storage: () => storage };
   16| }
   17| 
   18| const blocked = (): KeyStorage => {
   19|   throw new DOMException('The operation is insecure.', 'SecurityError');
   20| };
   21| 
   22| describe('splitHash', () => {
   23|   test('takes out the key= part and keeps the rest as written', () => {
   24|     expect(splitHash(`#key=${KEY}`)).toEqual({ value: KEY, rest: '' });
   25|     expect(splitHash(`#a=1&key=${KEY}&b`)).toEqual({ value: KEY, rest: '#a=1&b' });
   26|     expect(splitHash('#about')).toEqual({ value: null, rest: '#about' });
   27|     expect(splitHash('')).toEqual({ value: null, rest: '' });
   28|   });
   29| });
   30| 
   31| describe('findAccessKey', () => {
   32|   test('a key in the hash is kept for the tab and leaves the hash', () => {
   33|     const { items, storage } = memoryStorage();
   34|     expect(findAccessKey(`#key=${KEY}`, storage)).toEqual({ key: KEY, hash: '' });
   35|     expect(items.get(ACCESS_KEY_STORAGE)).toBe(KEY);
   36|   });
   37| 
   38|   test('without one in the hash, the stored key; the hash is left alone', () => {
   39|     const { storage } = memoryStorage({ [ACCESS_KEY_STORAGE]: KEY });
   40|     expect(findAccessKey('', storage)).toEqual({ key: KEY, hash: null });
   41|     expect(findAccessKey('#about', storage)).toEqual({ key: KEY, hash: null });
   42|   });
   43| 
   44|   test('a malformed key is never used or stored, but still leaves the hash', () => {
   45|     const { items, storage } = memoryStorage();
   46|     for (const bad of ['short', `${KEY}!`, 'x'.repeat(129), '']) {
   47|       expect(findAccessKey(`#key=${bad}&a`, storage)).toEqual({ key: null, hash: '#a' });
   48|     }
   49|     expect(items.size).toBe(0);
   50|   });
   51| 
   52|   test('a stored value that is not a key is ignored', () => {
   53|     expect(findAccessKey('', memoryStorage({ [ACCESS_KEY_STORAGE]: 'nope' }).storage).key).toBeNull();
   54|   });
   55| 
   56|   test('blocked storage: the hash key still serves this load; nothing stored is nothing', () => {
   57|     expect(findAccessKey(`#key=${KEY}`, blocked)).toEqual({ key: KEY, hash: '' });
   58|     expect(findAccessKey('', blocked)).toEqual({ key: null, hash: null });
   59|   });
   60| });
```

## `src/lib/simulacra/accessKey.ts`

```ts
    1| // The key that lets typed what-ifs be modelled (POST /runs sends it, api.ts).
    2| // It arrives once in a link's hash (#key=<value>), is kept for the tab in
    3| // sessionStorage, and leaves the address bar at once, so it isn't passed on
    4| // with a copied link. Without one the page works as before; the server says
    5| // why typed words weren't modelled.
    6| import { z } from 'zod';
    7| 
    8| export const ACCESS_KEY_STORAGE = 'simulacra.accessKey';
    9| 
   10| const AccessKeySchema = z.string().regex(/^[A-Za-z0-9_-]{16,128}$/);
   11| 
   12| /** The parts of sessionStorage this reads and writes. */
   13| export type KeyStorage = Pick<Storage, 'getItem' | 'setItem'>;
   14| 
   15| export interface FoundKey {
   16|   /** The key for this tab, or null. */
   17|   readonly key: string | null;
   18|   /** The hash without its `key=` part ('' when nothing else is left), or null when there was none to take out. */
   19|   readonly hash: string | null;
   20| }
   21| 
   22| /** The hash with any `key=` part taken out, and that part's value. Other parts are kept as written. */
   23| export function splitHash(hash: string): { readonly value: string | null; readonly rest: string } {
   24|   const parts = hash.replace(/^#/, '').split('&');
   25|   const at = parts.findIndex((p) => p.startsWith('key='));
   26|   if (at < 0) return { value: null, rest: hash };
   27|   const value = parts[at]?.slice('key='.length) ?? '';
   28|   const others = parts.filter((p, i) => i !== at && p !== '');
   29|   return { value, rest: others.length ? `#${others.join('&')}` : '' };
   30| }
   31| 
   32| /**
   33|  * The tab's access key: a well-formed one in the hash (stored for the tab),
   34|  * else the stored one. Any `key=` part leaves the hash, well formed or not.
   35|  * `storage` is a getter: sessionStorage itself can throw (storage blocked),
   36|  * as can each read and write; a key that can't be stored still serves this load.
   37|  */
   38| export function findAccessKey(hash: string, storage: () => KeyStorage): FoundKey {
   39|   const { value, rest } = splitHash(hash);
   40|   const given = AccessKeySchema.safeParse(value);
   41|   if (given.success) {
   42|     try {
   43|       storage().setItem(ACCESS_KEY_STORAGE, given.data);
   44|     } catch {
   45|       // Not kept: this load still has it.
   46|     }
   47|     return { key: given.data, hash: rest };
   48|   }
   49|   let stored: string | null = null;
   50|   try {
   51|     stored = storage().getItem(ACCESS_KEY_STORAGE);
   52|   } catch {
   53|     // No storage: no key.
   54|   }
   55|   const kept = AccessKeySchema.safeParse(stored);
   56|   return { key: kept.success ? kept.data : null, hash: value === null ? null : rest };
   57| }
```

## `src/lib/simulacra/actions.ts`

```ts
    1| // Svelte actions the page uses.
    2| import type { Action } from 'svelte/action';
    3| 
    4| /**
    5|  * Moves the element to <body> while it's mounted. The time bar lives there,
    6|  * beside the robot's frame and above it, so its frosted glass blurs the
    7|  * robot the way it blurs the page; an open InfoPopover too, above both.
    8|  */
    9| export const toBody: Action<HTMLElement> = (node) => {
   10|   document.body.appendChild(node);
   11|   return {
   12|     destroy() {
   13|       node.remove();
   14|     },
   15|   };
   16| };
   17| 
   18| /**
   19|  * Reports the tallest the element has been since the window last changed
   20|  * width (each change starts over), as it resizes.
   21|  */
   22| export const tallest: Action<HTMLElement, (px: number) => void> = (node, report) => {
   23|   let onHeight = report;
   24|   let width = innerWidth;
   25|   let most = 0;
   26|   const ro = new ResizeObserver(() => {
   27|     if (innerWidth !== width) {
   28|       width = innerWidth;
   29|       most = 0;
   30|     }
   31|     const h = node.offsetHeight;
   32|     if (h <= most) return;
   33|     most = h;
   34|     onHeight(most);
   35|   });
   36|   ro.observe(node);
   37|   return {
   38|     update(next) {
   39|       onHeight = next;
   40|     },
   41|     destroy() {
   42|       ro.disconnect();
   43|     },
   44|   };
   45| };
```

## `src/lib/simulacra/api.test.ts`

```ts
    1| import { describe, expect, test } from 'vitest';
    2| import { createSimulacraApi, type Fetch, LIMITED_MESSAGE } from './api';
    3| 
    4| const json = (body: unknown, status = 200) =>
    5|   new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
    6| 
    7| /** A fake server: answers each call from `reply`, and records what was asked. */
    8| function fakeFetch(reply: (url: string, init?: RequestInit) => Response | Promise<Response>) {
    9|   const calls: { url: string; init?: RequestInit | undefined }[] = [];
   10|   const fetch: Fetch = async (url, init) => {
   11|     calls.push({ url, init });
   12|     return reply(url, init);
   13|   };
   14|   return { fetch, calls };
   15| }
   16| 
   17| const SLICE = { key: 'women', label: 'Women', adults: 27.1, barred: 0.92, home: 0.04, A: 0.02, B: 0.01, O: 0.01 };
   18| const ELECTION = {
   19|   slices: [SLICE],
   20|   whatIfs: [{ key: 'women', label: 'Women Vote', kind: 'franchise', detail: 'Every woman can vote.', slices: ['women'] }],
   21|   simulated: true,
   22| };
   23| 
   24| describe('createSimulacraApi', () => {
   25|   test('a valid election parses to ok', async () => {
   26|     const { fetch, calls } = fakeFetch(() => json(ELECTION));
   27|     const api = createSimulacraApi({ fetch });
   28|     const out = await api.election(1912);
   29|     expect(calls.map((c) => c.url)).toEqual(['/api/simulacra/manifest', '/api/simulacra/elections/1912']);
   30|     expect(out.kind).toBe('ok');
   31|     if (out.kind === 'ok') {
   32|       expect(out.value.slices[0]?.label).toBe('Women');
   33|       expect(out.value.whatIfs[0]?.kind).toBe('franchise');
   34|     }
   35|   });
   36| 
   37|   test('a year without a bundle answers empty lists, not an error', async () => {
   38|     const { fetch } = fakeFetch(() => json({ slices: [], whatIfs: [], simulated: false }));
   39|     const out = await createSimulacraApi({ fetch }).election(1789);
   40|     expect(out).toEqual({ kind: 'ok', value: { slices: [], whatIfs: [], simulated: false } });
   41|   });
   42| 
   43|   test('malformed JSON is an error', async () => {
   44|     const { fetch } = fakeFetch(() => new Response('{"slices": [', { status: 200 }));
   45|     const out = await createSimulacraApi({ fetch }).election(1912);
   46|     expect(out.kind).toBe('error');
   47|     if (out.kind === 'error') expect(out.reason).toBe('malformed');
   48|   });
   49| 
   50|   test('JSON outside the contract is an error', async () => {
   51|     const { fetch } = fakeFetch(() => json({ slices: [{ key: 'women' }], whatIfs: [] }));
   52|     const out = await createSimulacraApi({ fetch }).election(1912);
   53|     expect(out.kind).toBe('error');
   54|     if (out.kind === 'error') expect(out.reason).toBe('malformed');
   55|   });
   56| 
   57|   test('a first 404 means no simulation service; a later one is just missing', async () => {
   58|     let answered = false;
   59|     const { fetch } = fakeFetch((url) => {
   60|       if (url.endsWith('/manifest')) return json({ error: 'not found' }, 404);
   61|       if (url.endsWith('/elections/1912') && answered) return json(ELECTION);
   62|       answered = true;
   63|       return json({ error: 'not found' }, 404);
   64|     });
   65|     const api = createSimulacraApi({ fetch });
   66|     expect((await api.election(1912)).kind).toBe('unsupported');
   67|     expect((await api.election(1912)).kind).toBe('ok');
   68|     const later = await api.voter(1912, 'nobody');
   69|     expect(later.kind).toBe('error');
   70|     if (later.kind === 'error') expect([later.reason, later.status]).toEqual(['missing', 404]);
   71|   });
   72| 
   73|   test('years are asked for at the run the manifest names, so a CDN can keep them', async () => {
   74|     const { fetch, calls } = fakeFetch((url) =>
   75|       url.endsWith('/manifest') ? json({ years: { '1920': '1920-abc' } }) : json({ ...ELECTION, runId: '1920-abc' }),
   76|     );
   77|     const api = createSimulacraApi({ fetch });
   78|     await api.election(1920);
   79|     await api.election(1912);
   80|     expect(calls.map((c) => c.url)).toEqual([
   81|       '/api/simulacra/manifest',
   82|       '/api/simulacra/elections/1920?v=1920-abc',
   83|       '/api/simulacra/elections/1912',
   84|     ]);
   85|   });
   86| 
   87|   test('a fresh load skips the cache and moves the year to the run it returns', async () => {
   88|     const { fetch, calls } = fakeFetch((url) =>
   89|       url.endsWith('/manifest') ? json({ years: { '1920': 'old' } }) : json({ ...ELECTION, runId: 'new' }),
   90|     );
   91|     const api = createSimulacraApi({ fetch });
   92|     await api.election(1920, { fresh: true });
   93|     await api.election(1920);
   94|     expect(calls[1]?.url).toMatch(/^\/api\/simulacra\/elections\/1920\?v=fresh-/);
   95|     expect(calls[2]?.url).toBe('/api/simulacra/elections/1920?v=new');
   96|   });
   97| 
   98|   test('without a manifest, years load unversioned', async () => {
   99|     const { fetch, calls } = fakeFetch((url) => (url.endsWith('/manifest') ? json({ nope: 1 }) : json(ELECTION)));
  100|     const out = await createSimulacraApi({ fetch }).election(1912);
  101|     expect(out.kind).toBe('ok');
  102|     expect(calls[1]?.url).toBe('/api/simulacra/elections/1912');
  103|   });
  104| 
  105|   test('a POST that times out is indeterminate: the run may have started', async () => {
  106|     // Answers nothing until the caller gives up, like a server that took the write and hung.
  107|     const { fetch } = fakeFetch(
  108|       (_url, init) =>
  109|         new Promise<Response>((_resolve, reject) => {
  110|           init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
  111|         }),
  112|     );
  113|     const out = await createSimulacraApi({ fetch, timeoutMs: 10 }).startRun(1912, { whatIfs: ['women'] });
  114|     expect(out.kind).toBe('indeterminate');
  115|   });
  116| 
  117|   test('a GET that times out is an error, not indeterminate', async () => {
  118|     const { fetch } = fakeFetch(
  119|       (_url, init) =>
  120|         new Promise<Response>((_resolve, reject) => {
  121|           init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')));
  122|         }),
  123|     );
  124|     const out = await createSimulacraApi({ fetch, timeoutMs: 10 }).election(1912);
  125|     expect(out.kind).toBe('error');
  126|     if (out.kind === 'error') expect(out.reason).toBe('offline');
  127|   });
  128| 
  129|   test('an unreachable server is offline', async () => {
  130|     const { fetch } = fakeFetch(() => Promise.reject(new TypeError('fetch failed')));
  131|     const out = await createSimulacraApi({ fetch }).startRun(1912);
  132|     expect(out.kind).toBe('error');
  133|     if (out.kind === 'error') expect(out.reason).toBe('offline');
  134|   });
  135| 
  136|   test('startRun posts the ask and returns the run id; run parses each status', async () => {
  137|     const statuses = [
  138|       { status: 'running', done: 0, total: 0, error: null, steps: [{ text: 'Reading.', state: 'doing' }] },
  139|       { status: 'failed', error: 'That combination has not been computed.' },
  140|     ];
  141|     const { fetch, calls } = fakeFetch((url) => (url.endsWith('/runs') ? json({ id: 'r1' }) : json(statuses.shift())));
  142|     const api = createSimulacraApi({ fetch, base: 'http://localhost:8787/api/simulacra' });
  143|     const started = await api.startRun(1912, { whatIfs: ['women'], text: 'taft out', edits: { women: { A: 0.02, home: -0.02 } } });
  144|     expect(started).toEqual({ kind: 'ok', value: { id: 'r1' } });
  145|     expect(calls[0]?.url).toBe('http://localhost:8787/api/simulacra/runs');
  146|     expect(calls[0]?.init?.method).toBe('POST');
  147|     expect(JSON.parse(String(calls[0]?.init?.body))).toEqual({
  148|       year: 1912,
  149|       whatIfs: ['women'],
  150|       text: 'taft out',
  151|       edits: { women: { A: 0.02, home: -0.02 } },
  152|     });
  153|     const running = await api.run('r1');
  154|     expect(running.kind === 'ok' && running.value.status).toBe('running');
  155|     const failed = await api.run('r1');
  156|     expect(failed.kind === 'ok' && failed.value.status === 'failed' && failed.value.error).toContain('not been computed');
  157|   });
  158| 
  159|   test('401 and 403 are ordinary failures', async () => {
  160|     for (const status of [401, 403]) {
  161|       const { fetch } = fakeFetch(() => json({ error: 'no' }, status));
  162|       const out = await createSimulacraApi({ fetch }).election(1912);
  163|       expect(out.kind === 'error' && [out.reason, out.status]).toEqual(['failed', status]);
  164|     }
  165|   });
  166| 
  167|   test('429 is limited, with a message to wait', async () => {
  168|     const { fetch } = fakeFetch((url) => (url.endsWith('/runs') ? json({ error: 'slow down' }, 429) : json(ELECTION)));
  169|     const out = await createSimulacraApi({ fetch }).startRun(1912, { text: 'taft out' });
  170|     expect(out).toEqual({ kind: 'error', reason: 'limited', message: LIMITED_MESSAGE, status: 429 });
  171|   });
  172| 
  173|   test('the access key goes with POST /runs only, as a bearer token', async () => {
  174|     const accessKey = 'abcdefghij0123456789';
  175|     const { fetch, calls } = fakeFetch((url) => {
  176|       if (url.endsWith('/runs')) return json({ id: 'r1' });
  177|       if (url.endsWith('/cancel')) return json({ ok: true });
  178|       return url.includes('/voters/') ? json({ name: 'A', line: 'b', quote: 'c', history: 'A', now: 'A' }) : json(ELECTION);
  179|     });
  180|     const api = createSimulacraApi({ fetch, accessKey });
  181|     await api.election(1912);
  182|     await api.startRun(1912, { text: 'taft out' });
  183|     await api.stopRun('r1');
  184|     await api.voter(1912, 'women');
  185|     const auth = calls.map((c) => [c.url.replace('/api/simulacra', ''), new Headers(c.init?.headers).get('Authorization')]);
  186|     expect(auth).toEqual([
  187|       ['/manifest', null],
  188|       ['/elections/1912', null],
  189|       ['/runs', `Bearer ${accessKey}`],
  190|       ['/runs/r1/cancel', null],
  191|       ['/elections/1912/voters/women', null],
  192|     ]);
  193|     const { fetch: plain, calls: unkeyed } = fakeFetch(() => json({ id: 'r1' }));
  194|     await createSimulacraApi({ fetch: plain }).startRun(1912);
  195|     expect(new Headers(unkeyed[0]?.init?.headers).has('Authorization')).toBe(false);
  196|   });
  197| });
```

# synthetic-electorate-toy: source and docs, part 16 of 16

Generated from commit `8d299e47f067` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `tests/test_whatif.py` to `vite.config.ts`. Lines are numbered as in the repository.

## `tests/test_whatif.py`

```python
    1| """What-ifs and their evidence: source tiers, grounding, blending and confidence (evidence.py)."""
    2| import numpy as np
    3| 
    4| from simharness.evidence import blend, combine_tiers, confidence, ground, tier_of
    5| 
    6| 
    7| def test_source_tiers():
    8|     assert tier_of('https://www.jstor.org/stable/1') == 'A'
    9|     assert tier_of('https://history.house.gov/x') == 'A'
   10|     assert tier_of('https://www.britannica.com/event/x') == 'B'
   11|     assert tier_of('https://en.wikipedia.org/wiki/X') == 'C'
   12|     assert tier_of('https://example.com/x') == 'C'
   13| 
   14| 
   15| def test_ground_drops_unreturned_sources_and_flips_reversed():
   16|     notes = {'sources': [{'id': 'S1', 'url': 'https://www.jstor.org/x', 'title': 't', 'tier': 'A', 'cited': []}]}
   17|     pop = {'sex': 'any', 'group': 'any', 'region': 'any'}
   18|     f = {'claim': 'c', 'population': pop, 'situation': '', 'when': '', 'match': 'same-event', 'limits': '', 'effects': [{'measure': 'r2', 'pp': 3.0, 'pm': 1.0}]}
   19|     ev = ground({'findings': [f | {'source_ids': ['S9'], 'relation': 'like-scenario', 'direction': 'toward-R'},
   20|                               f | {'source_ids': ['S1'], 'relation': 'reverses-scenario', 'direction': 'toward-R'}]}, notes)
   21|     assert ev['dropped_ungrounded'] == 1 and len(ev['findings']) == 1
   22|     assert ev['findings'][0]['direction'] == 'toward-D' and ev['findings'][0]['effects'][0]['pp'] == -3.0
   23| 
   24| 
   25| def test_confidence_tiers():
   26|     fantasy = {'kind': 'candidate', 'mode': 'agents', 'plausibility': 'fantastical', 'candidate': None}
   27|     assert confidence(fantasy, None, None, None, True)['tier'] == 'very-low'
   28|     franchise = {'kind': 'franchise', 'mode': 'backbone', 'plausibility': 'documented'}
   29|     shaky = {'n': 2, 'spans_zero': True, 'paraphrase_flip': True}
   30|     assert confidence(franchise, None, None, shaky, False)['tier'] == 'high'  # cross-check interviews move nothing
   31|     both = combine_tiers([confidence(franchise, None, None, None, False), confidence(fantasy, None, None, None, True)])
   32|     assert both['tier'] == 'very-low'
   33| 
   34| 
   35| def test_blend_weak_evidence_barely_moves():
   36|     d = np.full(200, 0.3) + np.linspace(-0.05, 0.05, 200)
   37|     out = blend({'draws': {'dt': d.copy(), 'dr': d.copy(), 'do': d.copy()}}, {'dr': (2.0, 5.0, 1)})
   38|     assert abs(out['draws']['dr'].mean() - 0.3) < 0.01 and out['evidence_blend']['dr']['evidence_weight'] < 0.01
   39| 
   40| 
   41| def test_misread_forces_very_low():
   42|     """When half or more of the people interviewed took the news to be about the
   43|     other candidate, the tier is very-low whatever it started at; fewer misreads
   44|     only flag it (and over a quarter costs one step)."""
   45|     spec = {'kind': 'franchise', 'mode': 'agents', 'plausibility': 'documented'}
   46|     steady = {'n': 40, 'spans_zero': False, 'paraphrase_flip': False, 'exposed': False}
   47|     assert confidence(spec, None, None, steady | {'checked': 40, 'misread': 0}, False)['tier'] == 'high'
   48|     for wrong in (20, 31, 40):
   49|         c = confidence(spec, None, None, steady | {'checked': 40, 'misread': wrong}, False)
   50|         assert c['tier'] == 'very-low', (wrong, c)
   51|         assert 'misread-change' in c['flags']
   52|     c = confidence(spec, None, None, steady | {'checked': 40, 'misread': 4}, False)
   53|     assert c['tier'] == 'high' and 'misread-change' in c['flags']
   54|     assert confidence(spec, None, None, steady | {'checked': 40, 'misread': 12}, False)['tier'] == 'medium'
   55|     # A combination is as sure as its least sure what-if.
   56|     assert combine_tiers([confidence(spec, None, None, steady | {'checked': 4, 'misread': 2}, False),
   57|                           confidence(spec, None, None, steady, False)])['tier'] == 'very-low'
```

## `tsconfig.json`

```json
    1| {
    2|   "extends": "./.svelte-kit/tsconfig.json",
    3|   "compilerOptions": {
    4|     "strict": true,
    5|     "noUncheckedIndexedAccess": true,
    6|     "noImplicitOverride": true,
    7|     "noFallthroughCasesInSwitch": true,
    8|     "exactOptionalPropertyTypes": false,
    9|     "allowJs": false,
   10|     "checkJs": false,
   11|     "resolveJsonModule": true,
   12|     "esModuleInterop": true,
   13|     "skipLibCheck": true,
   14|     "sourceMap": true,
   15|     "moduleResolution": "bundler",
   16|     "module": "esnext",
   17|     "target": "es2022",
   18|     "verbatimModuleSyntax": true
   19|   },
   20|   "include": [
   21|     ".svelte-kit/types/**/$types.d.ts",
   22|     ".svelte-kit/non-ambient.d.ts",
   23|     ".svelte-kit/ambient.d.ts",
   24|     "src/**/*.ts",
   25|     "src/**/*.svelte",
   26|     "serve/**/*.ts",
   27|     "scripts/**/*.ts",
   28|     "tests/**/*.ts",
   29|     "vite.config.ts",
   30|     "svelte.config.js"
   31|   ]
   32| }
```

## `vercel.json`

```json
    1| {
    2|   "$schema": "https://openapi.vercel.sh/vercel.json",
    3|   "framework": null,
    4|   "installCommand": "pnpm install --frozen-lockfile",
    5|   "buildCommand": "pnpm build",
    6|   "outputDirectory": "build",
    7|   "rewrites": [
    8|     { "source": "/api/simulacra/:path*", "destination": "https://api.simulacraamericana.com/api/simulacra/:path*" },
    9|     { "source": "/((?!api/).*)", "destination": "/index.html" }
   10|   ]
   11| }
```

## `vite.config.ts`

```ts
    1| import { sveltekit } from '@sveltejs/kit/vite';
    2| import { defineConfig } from 'vitest/config';
    3| 
    4| // In development the page calls /api/simulacra on the local server (pnpm serve).
    5| export default defineConfig({
    6|   plugins: [sveltekit()],
    7|   server: { proxy: { '/api': 'http://localhost:8787' } },
    8|   test: { include: ['src/**/*.test.ts', 'serve/**/*.test.ts'] }
    9| });
```

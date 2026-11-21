# simulacra-americana: source and docs, part 1 of 17

Generated from commit `63ce42152a8f` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `.dockerignore` to `Dockerfile`. Lines are numbered as in the repository.

## `.dockerignore`

```
    1| # Build context hygiene: the API image needs serve/, simharness/, extracts/,
    2| # profiles/, the lockfiles and docker/. Everything else stays out.
    3| .git
    4| .github
    5| node_modules
    6| .svelte-kit
    7| build
    8| dist
    9| static
   10| src
   11| tests
   12| scripts
   13| infra
   14| docs
   15| *.md
   16| 
   17| # Mutable state lives on EFS, seeded by the seed task, never baked in.
   18| runs/
   19| sessions/
   20| serve/bundles/
   21| whatifs/
   22| configs/
   23| *.pkl
   24| 
   25| # Secrets must never enter a layer.
   26| .env
   27| .env.*
   28| **/anthropic.env
   29| 
   30| __pycache__/
   31| .pytest_cache/
   32| .venv/
   33| *.egg-info/
   34| .DS_Store
```

## `.env.example`

```
    1| # Base URL for the robot model, paint textures and portraits.
    2| PUBLIC_ASSET_BASE=https://assets.simulacraamericana.com/
    3| # Anthropic key for the harness (python). Never committed; ~/.config/simulacra/anthropic.env also works.
    4| ANTHROPIC_API_KEY=
```

## `.github/workflows/ci.yml`

```yaml
    1| name: CI
    2| on:
    3|   pull_request:
    4|   push:
    5|     branches: [main]
    6| concurrency:
    7|   group: ci-${{ github.ref }}
    8|   cancel-in-progress: true
    9| jobs:
   10|   web:
   11|     runs-on: ubuntu-latest
   12|     steps:
   13|       - uses: actions/checkout@v4
   14|       - uses: pnpm/action-setup@v4
   15|       - uses: actions/setup-node@v4
   16|         with: { node-version: 22, cache: pnpm }
   17|       - run: pnpm install --frozen-lockfile
   18|       - run: pnpm lint
   19|       - run: pnpm check
   20|       - run: pnpm size
   21|       - run: pnpm test
   22|       - run: pnpm audit --audit-level=high
   23|   harness:
   24|     runs-on: ubuntu-latest
   25|     steps:
   26|       - uses: actions/checkout@v4
   27|       - uses: actions/setup-python@v5
   28|         with: { python-version: '3.13', cache: pip }
   29|       - run: pip install -e '.[test]'
   30|       - run: python -m pytest -q
```

## `.github/workflows/deploy-api.yml`

```yaml
    1| name: Deploy API
    2| 
    3| # Builds the API image and rolls the ECS service behind
    4| # api.simulacraamericana.com. Mirrors the Partyhat auth server's deploy-aws.yml,
    5| # with one deliberate difference: the task definition is RENDERED from
    6| # infra/taskdef.json.tftpl on every deploy, never derived from the running
    7| # one, so an env var or secret can't silently drop (the auth server lost
    8| # ALLOW_LEGACY_INTERNAL_KEY that way after a rollback).
    9| #
   10| # MANUAL ONLY. A merge never ships. Only main ships, and only a SHA whose CI
   11| # run succeeded: the deploy role trusts main's OIDC subject alone
   12| # (infra/terraform.tfvars, from terraform.tfvars.example), and the first steps refuse any other ref or a SHA
   13| # without a green CI run.
   14| #   gh workflow run "Deploy API" -R partyhat-ai/synthetic-voters-toy --ref main -f confirm=DEPLOY
   15| # First image only (stand-up, before the ECS service exists):
   16| #   ... -f confirm=DEPLOY -f image_only=true
   17| #
   18| # Repo variables (from `terraform output`, docs/DEPLOY.md "CI setup"):
   19| #   AWS_DEPLOY_ROLE_ARN  deploy_role_arn
   20| #   TASKDEF_VARS         taskdef_vars, as JSON
   21| # No long-lived AWS keys live in GitHub.
   22| on:
   23|   workflow_dispatch:
   24|     inputs:
   25|       confirm:
   26|         description: Type DEPLOY to roll production
   27|         required: true
   28|         default: ''
   29|       image_only:
   30|         description: Build and push the image only (the first image, before the service exists)
   31|         type: boolean
   32|         default: false
   33| 
   34| concurrency:
   35|   group: api-deploy
   36|   cancel-in-progress: false
   37| 
   38| env:
   39|   AWS_REGION: us-east-1
   40|   # <account-id>.dkr.ecr.us-east-1.amazonaws.com/simulacra-api, set as a repository variable.
   41|   ECR_REPO: ${{ vars.ECR_REPO }}
   42|   CLUSTER: simulacra
   43|   SERVICE: simulacra-api
   44|   API: https://api.simulacraamericana.com
   45| 
   46| permissions:
   47|   id-token: write   # OIDC
   48|   contents: read
   49|   actions: read     # the CI run for the SHA being shipped
   50| 
   51| jobs:
   52|   deploy:
   53|     # ARM64 native: the task runs on Graviton, and numpy/pandas/scipy install
   54|     # from ARM wheels instead of building under QEMU.
   55|     runs-on: ubuntu-24.04-arm
   56|     steps:
   57|       - name: Require explicit confirmation
   58|         run: |
   59|           if [ "${{ github.event.inputs.confirm }}" != "DEPLOY" ]; then
   60|             echo "::error::Refusing to deploy: pass -f confirm=DEPLOY to roll production."
   61|             exit 1
   62|           fi
   63| 
   64|       - name: Require main
   65|         run: |
   66|           if [ "$GITHUB_REF" != "refs/heads/main" ]; then
   67|             echo "::error::Refusing to deploy $GITHUB_REF: only main ships (run with --ref main)."
   68|             exit 1
   69|           fi
   70| 
   71|       - name: Require green CI on this SHA
   72|         env:
   73|           GH_TOKEN: ${{ github.token }}
   74|         run: |
   75|           set -euo pipefail
   76|           # The CI workflow's push run for exactly this commit, finished and successful.
   77|           ok=$(gh api "repos/$GITHUB_REPOSITORY/actions/workflows/ci.yml/runs?head_sha=$GITHUB_SHA&event=push&status=success&per_page=1" \
   78|             --jq '.total_count')
   79|           if [ "$ok" -lt 1 ]; then
   80|             echo "::error::CI has not passed on $GITHUB_SHA. Wait for it (or fix it), then deploy again."
   81|             exit 1
   82|           fi
   83|           echo "CI passed on $GITHUB_SHA" >> "$GITHUB_STEP_SUMMARY"
   84| 
   85|       - uses: actions/checkout@v4
   86| 
   87|       - name: Render the task definition (fails on any missing variable)
   88|         env:
   89|           TASKDEF_VARS: ${{ vars.TASKDEF_VARS }}
   90|         run: |
   91|           set -euo pipefail
   92|           python3 - "${ECR_REPO}:${GITHUB_SHA}" <<'PY'
   93|           import json, os, re, sys
   94|           raw = os.environ.get('TASKDEF_VARS') or ''
   95|           if not raw:
   96|               sys.exit('::error::repo variable TASKDEF_VARS is not set')
   97|           v = json.loads(raw)
   98|           v['image'] = sys.argv[1]
   99|           tpl = open('infra/taskdef.json.tftpl').read()
  100|           names = set(re.findall(r'\$\{(\w+)\}', tpl))
  101|           missing = sorted(n for n in names if not str(v.get(n, '')).strip())
  102|           if missing:
  103|               sys.exit(f'::error::TASKDEF_VARS is missing {missing}')
  104|           td = json.loads(re.sub(r'\$\{(\w+)\}', lambda m: str(v[m.group(1)]), tpl))
  105|           c = td['containerDefinitions'][0]
  106|           env = {e['name'] for e in c['environment']}
  107|           sec = {s['name'] for s in c['secrets']}
  108|           required_env = {'NODE_ENV', 'PORT', 'SIMULACRA_LOG', 'SIMULACRA_AUTORUN', 'SIMULACRA_PYTHON', 'SIMULACRA_BUNDLES', 'SIMHARNESS_CACHE',
  109|                           'SIMULACRA_DAILY_USD', 'SIMULACRA_MONTHLY_USD', 'SIMULACRA_RETAIN_DAYS', 'TRUST_PROXY_HOPS'}
  110|           required_sec = {'ANTHROPIC_API_KEY', 'SIMULACRA_ACCESS_KEYS'}
  111|           if required_env - env or required_sec - sec:
  112|               sys.exit(f'::error::task def lacks env {sorted(required_env - env)} / secrets {sorted(required_sec - sec)}')
  113|           if env & sec:
  114|               sys.exit(f'::error::{sorted(env & sec)} in both environment and secrets (ECS rejects it)')
  115|           json.dump(td, open('td.json', 'w'))
  116|           print('rendered', td['family'], c['image'])
  117|           PY
  118| 
  119|       - name: Configure AWS credentials (OIDC)
  120|         uses: aws-actions/configure-aws-credentials@v4
  121|         with:
  122|           role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
  123|           aws-region: ${{ env.AWS_REGION }}
  124| 
  125|       - name: Log in to ECR
  126|         uses: aws-actions/amazon-ecr-login@v2
  127| 
  128|       - uses: docker/setup-buildx-action@v3
  129| 
  130|       - name: Build and push
  131|         uses: docker/build-push-action@v6
  132|         with:
  133|           context: .
  134|           platforms: linux/arm64
  135|           push: true
  136|           tags: ${{ env.ECR_REPO }}:${{ github.sha }}
  137|           cache-from: type=registry,ref=${{ env.ECR_REPO }}:buildcache
  138|           cache-to: type=registry,ref=${{ env.ECR_REPO }}:buildcache,mode=max,image-manifest=true
  139|           provenance: false
  140| 
  141|       - name: Register the task definition and roll the service
  142|         if: ${{ !inputs.image_only }}
  143|         run: |
  144|           set -euo pipefail
  145|           ARN=$(aws ecs register-task-definition --cli-input-json file://td.json \
  146|             --query 'taskDefinition.taskDefinitionArn' --output text)
  147|           aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" \
  148|             --task-definition "$ARN" >/dev/null
  149|           echo "rolled $SERVICE -> $ARN" >> "$GITHUB_STEP_SUMMARY"
  150|           # One task, stopped before its replacement starts. The circuit
  151|           # breaker rolls back a revision that never gets healthy; then the
  152|           # service is stable on the OLD revision, so check which one runs.
  153|           aws ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE"
  154|           RUNNING=$(aws ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" \
  155|             --query 'services[0].deployments[?status==`PRIMARY`].taskDefinition | [0]' --output text)
  156|           if [ "$RUNNING" != "$ARN" ]; then
  157|             echo "::error::The new revision did not take; the circuit breaker rolled back to $RUNNING"
  158|             exit 1
  159|           fi
  160| 
  161|       - name: Verify through the load balancer
  162|         if: ${{ !inputs.image_only }}
  163|         run: |
  164|           set -euo pipefail
  165|           code=$(curl -s -o /dev/null -w '%{http_code}' "$API/healthz")
  166|           echo "healthz: $code" >> "$GITHUB_STEP_SUMMARY"
  167|           test "$code" = "200"
  168|           curl -sf "$API/api/simulacra/elections/1920" | python3 -c '
  169|           import json, sys
  170|           d = json.load(sys.stdin)
  171|           assert d.get("simulated") is True, "1920 is not simulated"
  172|           assert len(d.get("slices") or []) > 0, "1920 has no slices"
  173|           print("1920: simulated, %d slices" % len(d["slices"]))
  174|           ' | tee -a "$GITHUB_STEP_SUMMARY"
```

## `.github/workflows/llms-digest.yml`

```yaml
    1| name: llms digest
    2| 
    3| # Keeps llms.txt and llms/ (a plain-text copy of this repository for tools that
    4| # read text at a URL) matching the code. On every push to main that changes
    5| # anything besides the digest, it rebuilds them and commits the result. Pushes
    6| # made with GITHUB_TOKEN don't start workflows, so the commit doesn't loop.
    7| on:
    8|   push:
    9|     branches: [main]
   10|     paths-ignore: ['llms.txt', 'llms/**']
   11|   workflow_dispatch:
   12| 
   13| concurrency:
   14|   group: llms-digest
   15|   cancel-in-progress: false
   16| 
   17| permissions:
   18|   contents: write
   19| 
   20| jobs:
   21|   digest:
   22|     runs-on: ubuntu-latest
   23|     steps:
   24|       - uses: actions/checkout@v4
   25|         with:
   26|           fetch-depth: 0  # the history page needs every commit
   27|       - name: Rebuild
   28|         run: python3 scripts/llms_digest.py
   29|       - name: Commit if it changed
   30|         run: |
   31|           if [ -z "$(git status --porcelain -- llms.txt llms)" ]; then
   32|             echo "Digest already matches the code."
   33|             exit 0
   34|           fi
   35|           git config user.name "github-actions[bot]"
   36|           git config user.email "41898732+github-actions[bot]@users.noreply.github.com"
   37|           git add llms.txt llms
   38|           git commit -m "Regenerate llms digest for ${GITHUB_SHA::12}"
   39|           git pull --rebase --quiet origin main
   40|           git push origin HEAD:main
```

## `.gitignore`

```
    1| node_modules/
    2| .svelte-kit/
    3| build/
    4| .env
    5| .env.*
    6| !.env.example
    7| __pycache__/
    8| .pytest_cache/
    9| .venv/
   10| runs/*/fit.pkl
   11| runs/*/effects.pkl
   12| runs/_cache/
   13| sessions/
   14| notes/
   15| .DS_Store
   16| *.egg-info/
```

## `AGENTS.md`

```markdown
    1| # Rules for coding agents
    2| 
    3| These are gates, not advice. CI enforces every one of them on the head SHA.
    4| 
    5| ## Code
    6| - TypeScript `strict`. No `any`. No `as` casts unless a `// SAFETY:` comment directly
    7|   above states the invariant that was checked. Prefer `satisfies`. Use `never` for
    8|   exhaustive switches.
    9| - No file over 1,000 lines (`pnpm size`).
   10| - No nested ternaries. One level of `a ? b : c` is fine.
   11| - Parse at the boundary: every server response, `postMessage` payload, `localStorage`
   12|   read and bundle file is parsed once, with zod, where it enters. Types derive from the
   13|   schemas. Inside the boundary, branch on domain values, not `typeof`.
   14| - Typed outcomes: API calls return `{ kind: 'ok' | 'error' | 'indeterminate' | 'unsupported' }`.
   15|   `indeterminate` means a write may have landed (poll, don't resubmit). Never return an
   16|   empty object as a stand-in for failure.
   17| - No new runtime dependency without a one-line justification in the PR.
   18| 
   19| ## Tests
   20| - `pnpm test` (vitest) and `pnpm test:py` (pytest) run every suite. No module mocks:
   21|   inject real interfaces.
   22| - A test that needs raw data outside the repo skips with a stated reason. It never passes silently.
   23| 
   24| ## Data and provenance
   25| - Provenance hashes are computed by script, never typed.
   26| - Only evaluate-stage code reads held-out benchmarks (`test_benchmarks_isolated`).
   27| - Add to `DISCLOSURES.md` the moment an inaccuracy or assumption is found.
   28| - No secrets in the repo. The harness reads `ANTHROPIC_API_KEY` or
   29|   `~/.config/simulacra/anthropic.env`.
   30| 
   31| ## Commits and merges
   32| - Imperative subject under 70 characters that names the change. A body only when the
   33|   reason isn't obvious. No hype words, no emoji.
   34| - Squash merges only, with CI green on the head SHA.
```

## `CONTEXT.md`

```markdown
    1| # Vocabulary
    2| 
    3| - **Election:** one presidential year (1789–2024), with its certified state results.
    4| - **Slice:** one group of adults in an election (e.g. women in the old suffrage states),
    5|   drawn as a row of dots: who voted for whom, who stayed home, who couldn't vote.
    6| - **Barred:** adults who couldn't legally vote, kept as agents with a reason code. Their vote is never simulated.
    7| - **What-if:** a typed counterfactual change of one kind: *franchise* (who can vote),
    8|   *population* (who lives where), *issue* (what people care about) or *candidate* (who is on the ballot).
    9| - **Rerun:** an election recomputed under one or more what-ifs. An unchanged rerun reproduces history.
   10| - **Backbone:** the calibrated statistical model that decides the counts and reproduces
   11|   certified returns in every draw.
   12| - **Agent / interview:** a synthetic voter answering in both worlds. It supplies only paired,
   13|   within-person changes and quotes, never counts.
   14| - **Bundle:** the per-year JSON the server publishes and the page reads.
   15| - **Profile:** one election's year-specific facts: candidates, blinded descriptors, ballot wording, sources.
   16| - **Narrator:** the robot whose bubble explains a rerun step by step.
   17| 
   18| Avoid: "prediction" (the page reproduces, then reruns), "AI voters" (they're agents with a stated
   19| role), "accuracy" for R1 (it is enforced by construction, so it isn't validation).
```

## `DISCLOSURES.md`

```markdown
    1| # Disclosures: inaccuracies and intellectual-honesty flags
    2| 
    3| This is a running log. Every known inaccuracy, weak spot and judgment call
    4| behind Simulacra Americana's numbers and words goes here: our own mistakes,
    5| the data's, and the model's.
    6| 
    7| Two uses:
    8| 1. **To improve.** Each entry has a next step. When it's done, mark it fixed;
    9|    don't delete it.
   10| 2. **To disclose.** The summary just below is written to be lifted into the
   11|    page's About popover or a public method page.
   12| 
   13| **How to add an entry:**
   14| - Give it the next ID in its section, a severity, a status and a location.
   15| - Say what is wrong, why it matters, and what would fix it.
   16| - Log it when it's found, not when it's convenient. An entry that makes us
   17|   look bad is the point of this file.
   18| 
   19| **Severity:**
   20| - **High:** it can change a headline number or mislead a reader.
   21| - **Medium:** it biases a detail, or weakens a claim we make.
   22| - **Low:** cosmetic, or already contained.
   23| 
   24| **Status:** open, mitigated, fixed or by design (a deliberate choice that must
   25| stay disclosed).
   26| 
   27| ---
   28| 
   29| ## Public disclosure summary (draft copy)
   30| 
   31| > Every rerun starts from the real 1920 result and reproduces it exactly. The
   32| > counts come from a statistical model of the 1920 census and the certified
   33| > returns, not from an AI.
   34| >
   35| > AI stand-ins are used for two things: how people's minds would change, and
   36| > the quotes. The people are invented. Their circumstances come from dated
   37| > 1920 newspapers.
   38| >
   39| > The AI already knows who won in 1920, and our tests show it can't be made
   40| > to forget. So we only use how its answers change, never what they are.
   41| >
   42| > Some things we can't measure well:
   43| > - How Black voters split in 1920. This alone moves the "Enforce the 15th
   44| >   Amendment" rerun by about 30 electoral votes.
   45| > - Exactly how many women voted in each state.
   46| > - Anything about what people cared about. Those reruns are low confidence.
   47| >
   48| > The ranges we show cover the uncertainty we can measure, not all of it.
   49| 
   50| ---
   51| 
   52| ## A. Intellectual honesty: process
   53| 
   54| **A1 · Medium · by design · `evaluate.py`, `benchmarks.py`**
   55| The 1920 checks aren't blind. Their author knew the standard 1920
   56| literature: a Harding landslide, women voting below men, Black Southerners
   57| excluded. The thresholds were set with that knowledge.
   58| 
   59| **A2 · High · open · `backbone.py`, `paired.py`, `evaluate.py`**
   60| Nine modelling and analysis changes were made after seeing the output they
   61| changed (EVAL.md, deviations 1–9). None moved a threshold, and each is
   62| logged, but together they are a large garden of forking paths. Three of them
   63| changed a result's direction or its pass/fail status:
   64| - the B2 bug fix, fail → pass;
   65| - β_B's region intercepts, which flipped its sign from −1.5 to +0.5;
   66| - the Black Southern choice rule.
   67| 
   68| **Next:** freeze the model code by hash in the run manifest, and require a
   69| written, logged amendment before any backbone change.
   70| 
   71| **A3 · Medium · open · `EVAL.md` N1**
   72| N1's denominator was realigned after the first result: citizens → all adults
   73| 21+, to match Corder–Wolbrecht. The realignment is correct, since the
   74| benchmark's own counts prove its definition. But it was found because the
   75| first result looked bad. It still fails, and both versions are reported.
   76| 
   77| **A4 · High · open · β_B, `EVAL.md`**
   78| We chose the region-intercept specification partly because its answer looked
   79| more plausible. It lands between the regression, which is implausible, and
   80| the prior, which is documented history. It is the least-bad choice, not a
   81| neutral one.
   82| 
   83| **Next:** publish both versions, or get a real estimate (see C1).
   84| 
   85| **A5 · Medium · open · `result.drawsWon`**
   86| "Cox wins in 0 of 400 draws" sounds more certain than it is. The draws cover
   87| parameter and population noise only. They don't cover model-structure
   88| choices:
   89| - the κ assumption
   90| - the β_B prior
   91| - the 80% accounting bound
   92| - the smoothing
   93| 
   94| N1's failed coverage is direct evidence that the intervals are too narrow.
   95| 
   96| **Next:** add structural variants to the draws, or say "0 of 400 draws of
   97| this model".
   98| 
   99| **A6 · Medium · open · A4 stereotype audit**
  100| The "pass" (0 of 66 flagged) comes from a regex. No person read the 66
  101| reasons. Don't cite it as an audit until someone has.
  102| 
  103| **A7 · Low · fixed · the harness's note to the UI (since removed)**
  104| The first draft of the UI note showed invented example numbers ("fails 2 of
  105| 17 checks", "318–352") that looked like results. They were replaced with the
  106| real figures.
  107| 
  108| **A8 · Low · fixed · session summary**
  109| The first research prompt pointed to a data folder that doesn't exist
  110| (`resetion_sim_data`). The data used is in
  111| `research_notes/historical_election_sim_data`.
  112| 
  113| **A9 · High · fixed (requests already sent) · data-fetch scripts**
  114| During the all-years build, three agents (G, C and E) put the user's email
  115| address in the HTTP User-Agent of requests to Wikipedia and loc.gov, as a
  116| "contact" string. E also sent it in two manual curl probes. The user's
  117| address must never go to an unrelated service. It was removed from every
  118| script, which now send a generic User-Agent, and E's running 1932 corpus
  119| build was restarted from its HTTP cache. The requests already sent can't be
  120| recalled.
  121| 
  122| **Next:** no contact address in any fetcher; check the User-Agent whenever a
  123| fetch script is reviewed.
  124| 
  125| **A10 · Medium · fixed · `pipeline.py` verify, `benchmarks.py`**
  126| `Run.verify` read the Corder–Wolbrecht held-out benchmark file directly,
  127| outside the evaluate stage, so `test_benchmarks_isolated` failed. Found while
  128| porting to the clean repo. The read now goes through
  129| `benchmarks.corder_wolbrecht_any_year()`, and `check.json` is byte-identical.
  130| The isolation test allows benchmark imports in exactly two places in
  131| `pipeline.py`: verify and evaluate.
  132| 
  133| **Next:** decide whether verify should see the benchmark at all, or move that
  134| check into evaluate.
  135| 
  136| **A11 · Medium · fixed · `backbone.CW_PRIOR_KNOTS`, `Run.verify`**
  137| The women's-turnout prior for `general_fit` years has knots at 1928
  138| (−1.0 ± 0.3) and 1940 (−0.7 ± 0.25) taken from Corder–Wolbrecht (2016), and
  139| `Run.verify` scored any year's women's turnout against the Corder–Wolbrecht
  140| file as a held-out benchmark. For 1928–1948, whose prior interpolates from
  141| those knots, that comparison would check the prior against its own source.
  142| It never ran: the benchmark file holds 1920 and 1924 only. But nothing
  143| stopped it, and the docs called the comparison held out. `verify` now
  144| refuses it for any year where `backbone.cw_held_out` is false (a
  145| `general_fit` year interpolating from a Corder–Wolbrecht knot) and records
  146| `corder_wolbrecht_skipped` instead. 1920 (natural experiment) and 1924
  147| (carried forward) use no prior knots, so their comparisons stand, with N1's
  148| caveat in A3. The what-if research prompt no longer names Corder–Wolbrecht
  149| as a source to look for.
  150| 
  151| **Next:** for a held-out women's-turnout check in 1928–1936, either take the
  152| knots from another source or score against a source the prior doesn't use.
  153| 
  154| **A12 · Medium · fixed · `tests/test_isolation.py`**
  155| `test_benchmarks_isolated` was a regex over each module's lines. It missed
  156| `from .benchmarks import x`, `simharness.benchmarks`, `importlib`, a path
  157| built as `CACHE / 'benchmarks' / f`, and anything in `scripts/`. It now
  158| parses every module and script (`ast`), allows the benchmark only inside
  159| `Run.verify` and `Run.evaluate`, refuses dynamic imports and listings of the
  160| cache root, scans config and profile JSON for benchmark paths, and is itself
  161| tested against each known bypass.
  162| 
  163| ---
  164| 
  165| ## B. Assumptions standing in for evidence
  166| 
  167| **B1 · High · open · `backbone.py` T1–T2**
  168| Men's turnout is assumed to have changed from 1916 to 1920 by the same amount
  169| everywhere as it did in the 12 Western states where women already voted.
  170| Women's votes are whatever is left. This is the key identifying assumption,
  171| and N1 shows it pushes women's turnout 4–6 points high in CT and MA.
  172| 
  173| **Next:** a regional κ from county returns.
  174| 
  175| **B2 · Medium · open · T3**
  176| In the 12 old-suffrage states, women's turnout relative to men's is borrowed
  177| from the newer-suffrage states. There is no within-state evidence for it.
  178| 
  179| **B3 · Medium · open · T4**
  180| Within a state and sex, native-born, naturalized and Northern Black voters
  181| are assumed to turn out at the same rate.
  182| 
  183| **B4 · Medium · open · C1 (δ)**
  184| Women's partisan tilt (δ = −0.66, toward Cox) comes from a regression that is
  185| identified mostly by the West-versus-East contrast. Region may confound it.
  186| The `no-19th` result (helps Harding) depends on its sign.
  187| 
  188| **Next:** region intercepts, a sensitivity table, and the literature.
  189| 
  190| **B5 · Medium · by design · C3b**
  191| The 80% accounting bound on Black Southern votes is a chosen number. Other
  192| choices would change South Carolina and Mississippi.
  193| 
  194| **B6 · Medium · open · population noise**
  195| The undercount CVs (2–8%) are assumptions, not estimates. The Black 1920
  196| undercount is documented in demographic literature we didn't retrieve.
  197| 
  198| **B7 · Low · open · `agents.py`**
  199| Personas carry imputed details:
  200| - the household economy (farm, wage, trade or proprietor);
  201| - a uniform age from 21 to 75, because no age table was built.
  202| 
  203| Neither drives any count, but both shape the quotes. Since the all-years
  204| build, economy wording and weights are set per era [I] and ages run 18–80
  205| from 1972. First names come from 1920-era lists in every year: they carry no
  206| information, but they read as period names.
  207| 
  208| **Next:** OCC1950, FARM and AGE from the IPUMS full count.
  209| 
  210| **B8 · Medium · open · franchise**
  211| Non-citizens who had declared their intent are treated as barred
  212| everywhere. No dataset we found codes which states still let them vote in
  213| 1920. HANDOFF-SIMULATION (the original repo's, not ported) says several did until 1926. The all-years
  214| franchise file now codes IN, MO, TX and AR as still letting declarant
  215| aliens vote in 1920, from unchecked memory of Keyssar A.12 (C25). The legacy
  216| 1916–1924 files are left blank to keep those years byte-identical (G9), so
  217| they still run with no alien voting.
  218| 
  219| **Next:** Keyssar, Table A.12.
  220| 
  221| **B9 · Low · open · naturalized choice**
  222| Naturalized voters share their state's partisan split. The model has no
  223| separate estimate.
  224| 
  225| **B10 · High · by design · `backbone.general_fit`**
  226| Every year outside 1916–1924 is fitted by `general_fit`, which has no
  227| natural experiment. Nothing is identified within the year. Each group's
  228| turnout gap and partisan tilt is a literature prior, a (year, mean, sd) knot
  229| table interpolated between knots, and exact calibration to the state returns
  230| does the rest. The priors are not updated from the data. A fit's values are
  231| in `fit.diagnostics['priors']`, and all are [I]:
  232| - **Women's turnout:** Corder–Wolbrecht to 1936, ANES 1952, CPS P20 and CAWP
  233|   from 1964. Before 1920, the 1920 gap with a wider sd. So Corder–Wolbrecht
  234|   is not held out for 1928–1948 (A11).
  235| - **Naturalized turnout:** Merriam–Gosnell and CPS. Declarant aliens and
  236|   `other` have no source.
  237| - **Black Southern exclusion:** Foner and Kousser for 1868–1900, the 1920
  238|   posterior for 1904–44, registration ratios for 1948–76.
  239| - **Black turnout:** CPS national gaps, which partly double-count the
  240|   Southern exclusion in 1964–76.
  241| - **β_B:** Fox, Foner, Weiss, Gallup, ANES and exit polls. Before 1856 it
  242|   assumes slot R is the anti-Democratic party.
  243| - **Naturalized tilt:** Kleppner, Lubell and Pew. `other` has none.
  244| 
  245| A what-if's shift lands on groups in proportion to these priors, so they
  246| shape every what-if outside 1916–1924.
  247| 
  248| **Next:** in-year updating where county returns exist (`bayes_ols`), and a
  249| sensitivity table per prior.
  250| 
  251| **B11 · Medium · open · women's tilt δ, 1936–1940**
  252| As briefed, `general_fit` uses the 1920 posterior δ (−0.66 ± 0.27, toward
  253| D) for every year to 1940. Gallup's 1936 and 1940 vote-by-sex tables show
  254| women slightly *more* Republican than men. The prior contradicts the only
  255| direct evidence for those two years. From 1944 it follows Gallup, then exit
  256| polls.
  257| 
  258| **Next:** use Gallup for 1936–40, or publish both.
  259| 
  260| **B12 · Medium · open · `general_fit` repairs (`fit_flags`)**
  261| When the data and the rules disagree, the fit repairs the inputs instead of
  262| failing:
  263| - If a state's votes exceed 97% of its eligible adults, its adults are
  264|   scaled up for that draw (`adults_scaled_share`; e.g. 1876 SC).
  265| - If returns exist where the coded rules bar every adult, the rules lose and
  266|   the state's men are opened (`legal_rules_contradicted`).
  267| - A state with votes but no population cells gets synthetic native-white
  268|   cells at votes ÷ 0.6 (`cells.synthetic`).
  269| 
  270| Each one signals an undercount or a coding error, and each makes
  271| reproduction exact by construction. They are reported per fit, not on the
  272| page.
  273| 
  274| **Next:** list each year's repaired states here and in the page's sources.
  275| 
  276| **B13 · Medium · by design · 60-election reproduction (`aggregate.outcome`)**
  277| The unchanged rerun of every one of the 60 elections, 1789–2024, now
  278| reproduces every state's certified R/D/O exactly and matches history's
  279| electoral votes. Four kinds of fix were needed:
  280| - **Legislature-chosen states** keep their history's electors (`ev_fixed`).
  281| - **Split or slate states** keep their historical division while the
  282|   recorded plurality winner holds (`ev_split`).
  283| - **A lumped "other"** can carry a state only if its largest single
  284|   candidate would. This fixes 1860 (Bell and Breckinridge together beat
  285|   Douglas in MO), 1892 and 1912.
  286| - **Before 1868**, electoral votes count the electors who actually voted,
  287|   not those appointed.
  288| 
  289| These are rules, not estimates. A what-if can't move a legislature's
  290| electors, a split state's division changes only when its plurality winner
  291| does, and O's candidates remain one slot, so a what-if can't say which of
  292| them gains.
  293| 
  294| ---
  295| 
  296| ## C. Data inaccuracies and conflicts
  297| 
  298| **C1 · High · open · Black voters' choice (β_B)**
  299| State returns can't identify it. The regression says Black voters leaned
  300| toward Cox (−3.4 ± 1.9 logit), which contradicts the documented history. The
  301| published estimate leans on a subjective prior. The research agents found no
  302| documented 1920 estimate; the only source was Du Bois (1928), with no
  303| counts.
  304| 
  305| **C2 · Medium · by design · labels**
  306| The Algara–Amlani county sums don't match official totals in 14 states for
  307| 1920:
  308| - Maryland's Baltimore row double-counts, inflating the state 40–53%.
  309| - In Vermont, the Republican vote sits in "other".
  310| - New Mexico is missing a county.
  311| - Maine's Cox vote is 17.6% high.
  312| 
  313| The House Clerk's 1921 table was used instead. **1916 has only one
  314| cross-check source (Wikipedia)**, and 1916 anchors the whole natural
  315| experiment.
  316| 
  317| **C3 · Medium · open · franchise conflict**
  318| Gray–Jenkins codes women as able to vote in Georgia and Mississippi in 1920.
  319| National Park Service pages say they couldn't. We follow NPS. A Smithsonian
  320| snippet also names Arkansas and South Carolina; it's unverified and not
  321| coded.
  322| 
  323| **C4 · Medium · open · Teele suffrage dates**
  324| - Ohio is coded as presidential suffrage from 1917. We believe, **without
  325|   verification**, that Ohio's 1917 law was overturned by referendum, which
  326|   would make 1919 the real date. It doesn't affect 1920 eligibility.
  327| - Arizona is coded 1910, before statehood in 1912.
  328| - Arkansas and Texas's 1917 primary-only suffrage is excluded.
  329| 
  330| **C5 · Medium · by design · census transcription**
  331| The 1920 voting-age tables were read by eye from scans, because OCR confused
  332| 3/8, 9/0 and 5/6. Thirteen ambiguous digits were resolved against the
  333| tables' own sums. Every state matches its printed totals, but a
  334| compensating pair of errors would pass that check.
  335| 
  336| **C6 · Medium · open · 1910 women**
  337| Citizenship wasn't asked of women in 1910. The split is borrowed from men of
  338| the same state (wives took their husbands' status before 1922).
  339| 
  340| **C7 · Low · open · census gaps**
  341| - Delaware, New Hampshire and Vermont print no "all other races" row; those
  342|   cells are 0.
  343| - There is no age-band table.
  344| - DC is excluded, since it had no electors in 1920.
  345| 
  346| **C8 · Medium · by design · Corder–Wolbrecht**
  347| The state and pooled women's-turnout figures we compare against are **our
  348| own aggregation** of their unit-level estimates, not numbers they published.
  349| Their deposit covers only CT, IL, MA, MI and NY.
  350| 
  351| **C9 · Low · open · platforms**
  352| - The American Presidency Project dates are convention start dates, not
  353|   adoption dates.
  354| - The Socialist text is a pre-adoption newspaper draft.
  355| - The Farmer-Labor planks are an AP summary.
  356| 
  357| **C10 · Low · open · treaty facts**
  358| Sources disagree on:
  359| - the date of one November 1919 vote;
  360| - whether the March 1920 vote carried the reservations. FRUS says yes, and
  361|   one senate.gov page says no.
  362| 
  363| **C11 · Medium · by design · corpus**
  364| - 87 of 89 excerpts have bracketed OCR fixes, so they aren't verbatim.
  365| - 29 items were excluded for naming a candidate or party.
  366| - Coverage is thin: 1 usable Kansas item for women already voting in the
  367|   West; no Midwestern or Western items on Black registration.
  368| - Some items quote officials stating white-supremacist aims. They are kept
  369|   as documents of the barriers, and are period voices, not neutral fact.
  370| 
  371| **C12 · Low · open · leakage labelling**
  372| 1920 uses the 1920 census, published 1921–23, after the election. Results
  373| are labelled `mode: truth`. Strict mode (1910 aged) isn't run.
  374| 
  375| ---
  376| 
  377| **C13 · Medium · by design · 1924 population**
  378| There is no 1924 census. Each cell's 1920 count is aged to 4 November 1924
  379| along its own 1910→1920 trend (`data.population(1924)`). Things this misses:
  380| - the Cable Act (1922, married women's citizenship);
  381| - naturalizations after 1920;
  382| - the Indian Citizenship Act (June 1924).
  383| 
  384| **C14 · Medium · by design · 1924 backbone (`backbone.carry_forward`)**
  385| 1924 has no natural experiment of its own, so it carries 1920's structure
  386| forward:
  387| - the 1920 fit's per-cell turnout, women's tilt δ, Black voters' β_B and
  388|   Black Southern exclusion;
  389| - one turnout shift per state, across all groups;
  390| - the same exact share calibration as 1920.
  391| 
  392| Checks:
  393| - **Reproduction:** every 1924 state within 0.41 votes, 382–136–13 in
  394|   every draw.
  395| - **Held-out benchmark:** Corder–Wolbrecht 1924 women's turnout on their
  396|   denominator gives MAE 3.6 points, against 3.2 for 1920. CT and MA women
  397|   run high and men low, as in 1920.
  398| 
  399| Within a state, La Follette's share is spread evenly across groups. Who
  400| his voters were inside a state isn't identified.
  401| 
  402| **C15 · Medium · open · 1924 briefs have no dated newspaper items**
  403| There is no 1924 corpus yet, so 1924 people know only their circumstances
  404| and the ballot. Pulling Chronicling America items for October 1924 is the
  405| next step. The all-years corpus build stopped before 1924 was done (C30).
  406| 
  407| **C16 · Low · open · 1924 platforms (`context/platforms_1924.json`)**
  408| - Quotes come from American Presidency Project pages and the paraphrases
  409|   were written by the harness session.
  410| - The Progressive platform's date is entered as 4 July 1924 (the
  411|   Cleveland conference). APP files it under 4 November [I].
  412| - The fetched Republican text had no Prohibition passage.
  413| 
  414| **C17 · Medium · by design · NHGIS populations (`scripts/harness/build_population.py`)**
  415| State tables for 1870–1970 come from NHGIS extract 1 (cache:
  416| `population/nhgis/`; not redistributable).
  417| 
  418| - **The 1920 conversion reproduces the hand-keyed 1920 table exactly:**
  419|   60,886,520 adults, 0 of 588 cells off.
  420| - **1930's race/nativity-by-sex table (NT10) is mislabelled.** Its codebook
  421|   labels interleave the sexes, but the values run all male groups first.
  422|   Taking the labels at face value gave New York 15,184 foreign-born men.
  423|   The mapping now follows the values, and the build asserts it against two
  424|   independent 1930 tables (race by sex; white nativity by sex).
  425| - **1930's "Other race" includes Mexican Americans.** The 1930 census
  426|   counted "Mexican" as a race, so 1930's `other` group is 1.01 million
  427|   adults, against 0.25 million in 1920. Most were citizens.
  428|   `Inputs.other_citizen` must not treat them as 1920's American Indian and
  429|   Asian adults.
  430| 
  431| **C18 · Medium · open · 1870–1910 women (`scripts/harness/build_population_early.py`)**
  432| The 1870–1900 tables have no women 21+ by group. Women are each group's men
  433| × its whole-population F/M ratio [I]. 1870 has no table by sex at all, so it
  434| borrows 1880's ratios. Checked against the hand-keyed 1910 table, the method
  435| runs **2.0% high** (25.05M against 24.56M):
  436| - native white −0.6%, Negro +2.1%, foreign white +10.4%, other +21%;
  437| - per-state errors are wide (foreign white: mean |error| 12%).
  438| 
  439| Whole-population ratios overstate foreign-born adult women.
  440| 
  441| **Next:** a per-group 1910 factor (hand ÷ estimate), applied to 1870–1900.
  442| 
  443| **C19 · Medium · by design · other 1870–1910 estimates**
  444| - **1900's NT7 is mislabelled.** "Other colored" holds all colored people,
  445|   Negro included. Other races = AZ3001 − AZ3003, asserted in the build.
  446| - **1890 has no citizenship table** in extract 1, so 1880 and 1890
  447|   citizenship are interpolated 1870 → 1900 [I].
  448| - **1870 men 21+** come only as separate race and nativity margins, raked
  449|   with IPF [I]. 1870 naturalized = citizens − native-born, clipped to
  450|   [0, foreign-born white]. That gives 61% nationally, but AR and NC clip to
  451|   0, and VT (14%), ME (16%), IN (84%) and AL (81%) are implausible.
  452| - **1880 and 1890 "colored" includes Chinese and Indians.** It is split with
  453|   fixed weights (0.420; 0.95 for Chinese and Japanese, a guess), and for 1890
  454|   with the mean of 1880's and 1900's Negro shares [I].
  455| - **Territories** are kept as their later states. Consumers must filter to
  456|   the states that voted.
  457| 
  458| **C20 · Medium · by design · 1940 race break**
  459| The 1940 census counted Mexican Americans as white; 1930 counted them as a
  460| race (C17). `other_races` 21+ falls from 1.01M to 0.33M, and `native_white`
  461| rises by the same people. That is a change of classification, not of
  462| population. 1932 and 1936 interpolate across it, and their profiles say the
  463| 1930 "Mexican" count is folded into white; the population build must match.
  464| 
  465| **C21 · Medium · open · 1960 and 1970 nativity (`build_population_mid.py`)**
  466| The extract has no 1960 or 1970 nativity table, so both carry 1950's
  467| foreign-born share of whites forward [I]. Foreign-born white adults then rise
  468| from 9.9M (1950) to 10.8M (1960) and 11.9M (1970), while the real
  469| foreign-born population (all ages) fell from 10.3M to 9.6M. 1970's
  470| foreign-born whites are probably about 3M too high, and native whites 3M too
  471| low. White totals are unaffected.
  472| 
  473| **Next:** NHGIS 1960 and 1970 nativity and citizenship tables (requests
  474| drafted in `notes/A2.md`, not submitted).
  475| 
  476| **C22 · Low · open · other 1940–1970 estimates**
  477| - 1950 and 1960 have only white/nonwhite. The Negro share of nonwhite adults
  478|   is interpolated 1940 → 1970 by state and sex [I].
  479| - 1950 foreign-born whites by sex use 1940's ratios, and citizenship is
  480|   raked to 1950's all-foreign-born split. 1950 has no "first papers"
  481|   category.
  482| - The 18–20 add-on for 1950–60 uses the 21+ nativity shares, which
  483|   overstates the foreign-born among 18–20s.
  484| - Hawaii is blank in every 1950 table and omitted (it first voted in 1960).
  485|   Its 1960–70 nativity uses national 1950 shares.
  486| - There is no 1940 age-band table, so Georgia's 18–20s in 1944 and 1948 are
  487|   21+ × the 1950 18+/21+ ratio [I].
  488| 
  489| **C23 · Medium · by design · returns 1868–2024 (`scripts/harness/build_returns.py`)**
  490| Algara–Amlani county sums are used only where both party shares are within
  491| 0.5 points of the state file. 153 state-years fail and fall back to
  492| Wikipedia. The failures extend C2 to every year:
  493| - Missouri's county total is about 1.2× too high in nearly every year.
  494|   Alaska has no county data.
  495| - Fusion tickets (1884 and 1892 Weaver/Butler, 1896 Bryan), and unpledged or
  496|   Dixiecrat lines counted as Democratic (1948 AL, 1952 SC, 1964 AL).
  497| - Garbage rows: 1872 MI and IL, 1896 MI, 1900 WA, 1912 ID.
  498| - Algara–Amlani's state file has the wrong electoral votes for 1968 NC and
  499|   2020 NE (539 in total).
  500| 
  501| In 10 state-years Wikipedia also differs from the state file by more than
  502| 1.5 points (fusion allocation); Wikipedia is kept and flagged in `source`.
  503| 1872 GA's 3 rejected Greeley votes stay in `ev_dem` (352 nationally, not the
  504| 349 counted). 1868 MO's total is set to R + D.
  505| 
  506| **C24 · Medium · by design · pre-1868 adults (`build_population_republic.py`, `data.population`)**
  507| No census before 1870 tabulates age 21, so every adult count for 1789–1864
  508| is an estimate [I]:
  509| - **Age bands** are split on a stationary 3%-growth profile. 46% of 16–25s,
  510|   69% of 19–25s, 89% of 20–29s, 37% of 14–25s and 18% of 10–23s count as
  511|   21+.
  512| - **1790** counts only white males 16+, converted with the state's 1800
  513|   ratio.
  514| - **1790–1810 free colored and enslaved people** have totals only, split by
  515|   1820's adult shares.
  516| - **Nativity.** None before 1850. In 1850–60, foreign-born white adults are
  517|   72% (men) and 70% (women) of all foreign-born whites, and citizenship
  518|   isn't split.
  519| - **Dates.** Before 1848 election day is taken as 1 November, and 1790–1820
  520|   census days as 2 August. A cell found in only one bracketing census takes
  521|   that count, which double-counts some native whites in 1844 and 1848.
  522| 
  523| **C25 · High · open · franchise rules from memory (`build_republic.py`, `build_franchise.py`)**
  524| Gray–Jenkins starts in 1870 and has no alien-voting field. The rules it
  525| doesn't cover were coded from the agents' memory of Keyssar (Tables A.1–A.4,
  526| A.12) and Hayduk, **not checked against the books** [I]:
  527| - **Alien voting, 1789–1968:** e.g. NJ 1789–1804, IL 1820–48, MI from 1836,
  528|   IN from 1852, MN and OR from 1860; IN, MO, TX and AR still in 1920 (B8).
  529| - **Property and taxpaying tests, 1789–1864,** as the share who could vote:
  530|   0.95 under manhood suffrage, 0.88 under a taxpaying test, 0.55–0.75 under a
  531|   freehold (VA 0.55 before 1830; RI down to 0.40). Georgia 1840 then turns
  532|   out 102% of its eligible men, so 0.88 is too strict there.
  533| - **Free Black men:** the free share × 0.95, 0.6, 0.25 or 0.08 (NY's $250
  534|   rule), by regime.
  535| - **New Jersey women, 1792–1804:** about 10% of adult women.
  536| - **1868:** each state's 1870 Gray–Jenkins row. Ex-Confederate test oaths
  537|   as MO 0.80, TN 0.70, WV 0.85, AR 0.85. NY's Black men 0.1.
  538| - **American Indians** (`other_citizen`): 0.2 before 1888, 0.6 for
  539|   1888–1920, then 1 (AZ and NM 0.2 to 1944).
  540| 
  541| Before 1868, `poll_tax=1` marks any taxpaying test, not only a capitation
  542| tax.
  543| 
  544| **Next:** check every rule against Keyssar's printed tables.
  545| 
  546| **C26 · Medium · open · felony disenfranchisement (`franchise/state_franchise_1972_2024.csv`)**
  547| State rates exist only for 1980 (map bins) and from 2010 (Sentencing
  548| Project, Uggen). 1972–2008 is interpolated between the 1980 bin midpoints
  549| and the 2010 table, then scaled to the national series [I]. That smooths
  550| over law changes: TX 1997, NM and CT 2001, NE 2005, IA 2005–11, RI 2006, MD
  551| 2007, WA 2009. Also:
  552| - The 2022 and 2024 reports use VEP denominators; earlier ones use VAP.
  553| - `white_can` is 1 − the non-Black rate. No white-specific rate exists.
  554| - DC is a hand estimate (incarcerated only), 0 from 2020.
  555| - Before 1972 the share is blank, and 1789–1864 uses a flat 0.0005.
  556| - Where a year has no state table, agents' eligibility lines use national
  557|   rates (`FELONY_SHARE`), with Black adults at 3.5× and women at 0.25× [I].
  558| 
  559| **C27 · Low · open · 1980–2024 adults 18+ (`build_population_modern.py`, NHGIS extract 3)**
  560| - 1980 and 1990 foreign-born adults by race are all-ages counts × the
  561|   foreign-born adult share. 1980's share comes from 1990, and both years'
  562|   sex split from 2000 [I].
  563| - 1990 totals come from MARS, because STF1's table covered Hispanics only.
  564|   They aren't raked (−0.17% nationally).
  565| - 2020 is ACS 2016–20 raked to the PL count, a −1.96% gap (ID −4.8%).
  566| - Suppressed ACS cells use a fallback in a few small states (MT and WY in
  567|   most years).
  568| - Black non-Hispanic native adults = Black native × the all-ages
  569|   non-Hispanic share [I].
  570| - Years without their own file borrow [I]: 1972 and 1976 from 1980; 1984
  571|   from 1980/1990; 1988 and 1992 from 1990; 1996 from 2000; 2004 from
  572|   2000/2008.
  573| 
  574| **C28 · Medium · by design · 1789–1824 popular votes (`labels/state_pres_1789_1864.csv`)**
  575| Every number is parsed from Wikipedia's results tables (Tufts' *A New Nation
  576| Votes* to 1824; Dubin, CQ or Leip after). None was re-keyed from the
  577| sources. The early record is fragmentary:
  578| - About 20 rows in 1792–1824 are partial ("do not use for turnout") or not
  579|   extant.
  580| - 1789's slates were for or against the Constitution. 1792's ~7,800 votes
  581|   were on uncontested slates. 1820's ~109,000 were effectively uncontested,
  582|   20,660 of them for unpledged or Federalist-leaning slates.
  583| - How electors were chosen is hand-keyed, and some methods are ambiguous (MA
  584|   1789–96, KY 1792/96, TN 1796/1800).
  585| - There are no county returns before 1868.
  586| 
  587| A share model of these years measures turnout and dissent, not a contest.
  588| 
  589| **C29 · Low · open · platforms 1789–2024 (`context/platforms_<year>.json`)**
  590| Quotes are substring-checked against fetched pages, except:
  591| - Founders Online refused bulk fetches. Its 1789–1816 quotes were copied by
  592|   hand from a browser and not compared by script.
  593| - archive.org OCR sources (1808, 1816, 1824, 1831–32, Harrison) were
  594|   normalised for hyphens and spacing.
  595| 
  596| Weak or odd sources:
  597| - Before 1840 there were no platforms. Those files hold documented
  598|   positions, some from private letters or diaries (1796, 1824). 1812 R rests
  599|   on the Federalist House minority's address.
  600| - APP dates the 1912 Progressive platform 5 November; it was adopted 7
  601|   August [I].
  602| - APP typos are kept verbatim (1968 D, 1972 R).
  603| - 2020 R adopted no platform: the RNC resolution, plus four 2016 planks
  604|   marked as carried.
  605| - 2024 D was drafted while Biden was the presumptive nominee and says "his
  606|   second term".
  607| - Some quotes start mid-sentence, and some paraphrases summarise
  608|   neighbouring passages.
  609| 
  610| **C30 · Medium · open · newspaper corpora beyond 1920 (`scripts/harness/build_corpus.py`)**
  611| The per-year corpus build was stopped by the user before it finished. Other
  612| years' people know their circumstances and the ballot, and a corpus with
  613| non-1920 topic codes falls back to the items nearest the person. For
  614| whatever was written:
  615| - **The schema is inferred.** The permission classifier refused agent E's
  616|   reads of the 1920 corpus and the corpus code, and E didn't work around
  617|   it. The field names come from `PROVENANCE-sources.md`, and nobody has
  618|   diffed them against a 1920 line.
  619| - **Topics are per year** (`topic`, plus `topic_code` T1–T8 in 1920's slot
  620|   order). Code keyed on 1920's fixed topic list would mislabel them.
  621| 
  622| **Next:** diff the keys against 1920 (the rerun is offline, from the HTTP
  623| cache), then finish the years.
  624| 
  625| **C31 · Low · open · first election years (`history.ts`, `geo.ts`)**
  626| `history.ts` gives Missouri electoral votes in 1820 and Michigan in 1836, but
  627| `geo.ts` dates their first elections 1824 and 1840. The mini map leaves their
  628| tiles empty in those years. Pinned by `history.test.ts`.
  629| 
  630| **Next:** check the sources for each state's first counted electoral votes and
  631| make the two files agree.
  632| 
  633| **C32 · Low · open · state electoral votes vs. totals (`history.ts`)**
  634| In 8 years (1789, 1792, 1808, 1812, 1816, 1820, 1832, 1864) the state
  635| electoral votes don't sum to the year's total: the table lists electors
  636| allotted, not electors who voted. Pinned by `history.test.ts`.
  637| 
  638| **Next:** add the number who voted per state, or label the column as allotted.
  639| 
  640| **C33 · Low · open · faithless and abstaining electors (`history.ts`)**
  641| In 1956, 1972, 1976, 1988, 2000, 2004 and 2016, minor faithless or abstaining
  642| electors aren't listed as candidates, so the candidates' electoral votes fall
  643| short of the total. See also F8 (2000's abstaining DC elector).
  644| 
  645| **Next:** list them under Other, or note the shortfall wherever totals appear.
  646| 
  647| ## D. The AI agents
  648| 
  649| **D1 · High · open · backend**
  650| The prototype's answers came from 9 Claude Code subagents, not independent
  651| API calls:
  652| - 18–59 prompts shared one context;
  653| - the Claude Code system prompt surrounded them;
  654| - the model version behind "sonnet" and "opus" isn't recorded;
  655| - one subagent **scripted 28 of 56 probe answers**;
  656| - one built answers with a helper script;
  657| - one says its later answers got generic.
  658| 
  659| **No agent-layer number should be cited until it is rerun on the API.**
  660| 
  661| **D2 · High · by design · memorization**
  662| 56 of 56 probes identified 1920, both candidates and Harding's win.
  663| Blinding doesn't work for 1920. The control answers are exposed, and only
  664| their paired changes are used.
  665| 
  666| **D3 · High · open · homogenization**
  667| In 90% of cohorts with a mixed real split, every agent gave the same answer.
  668| The agents compress variation, so they can't stand in for how a group split.
  669| 
  670| **D4 · Medium · open · turnout overstatement**
  671| Agents say they'd vote about 12 points more often than the calibrated
  672| backbone. For women in the benchmark states it is 15.5 points.
  673| 
  674| **D5 · Medium · open · self-de-blinding**
  675| 25% of answers name a party that the blinded briefs never named. Quotes are
  676| published with names restored, so a reader can't tell which words the model
  677| supplied from memory.
  678| 
  679| **Next:** flag quotes that contain inferred party names.
  680| 
  681| **D6 · Medium · open · sample size**
  682| With 4–5 agents per cohort, the shrinkage (pseudo-count 8)
  683| pulls every cohort's effect 57–67% toward its region. Cohort differences
  684| are mostly unmeasured.
  685| 
  686| **D7 · Low · fixed in p2 · prompt bugs**
  687| Three bugs in the p1 prompts:
  688| - **Non-citizen women's briefs contradicted themselves.** They were told
  689|   "state law lets women vote". Subagents caught it; those pairs are
  690|   excluded.
  691| - **Dates didn't line up.** Briefs were dated 30 October but included items
  692|   up to 1 November.
  693| - **Surnames didn't fit their groups.** One agent is "Mary Lindqvist", a
  694|   Black North Carolina woman.
  695| 
  696| The p1 answers stand as recorded.
  697| 
  698| **D8 · Medium · open · Opus disagreement**
  699| On the League what-if, Sonnet's shift toward Cox is −0.18 logit and Opus's
  700| is −0.03 on the same people. They agree on sign, not size. The published
  701| effect pools them.
  702| 
  703| **D14 · Medium · open · paraphrase assignment**
  704| An agent's question wording is `n % paraphrases`, where n is its place in the
  705| run's sorted agent list. Adding a cohort renumbers everyone after it, so each
  706| of them gets a different question. The live config
  707| (`configs/live-1920.json`) keeps rung 1's six cohorts so answers stay
  708| comparable and cached. Fix before widening: key the paraphrase on the
  709| agent id.
  710| 
  711| **D15 · Medium · fixed · evidence extraction**
  712| - **Haiku extracted nothing.** Given rich research notes (Christensen's
  713|   19% in Washington, Roosevelt 1912, La Follette 1924), it returned zero
  714|   findings. It judged every analogue unreliable itself.
  715| - **Sonnet ran out of room.** At 4,000 tokens its JSON was truncated, and
  716|   the crash lost the call's usage. About $0.052 is entered in the ledger as
  717|   an estimate.
  718| 
  719| Now: Sonnet with 8,000 tokens, at most 12 findings, and an instruction not
  720| to judge reliability, since the pipeline grades it. A truncated answer keeps
  721| its usage.
  722| 
  723| **D16 · Medium · fixed · research without searching**
  724| The first League research call ran no searches and answered from memory
  725| ($0.02). Grounding correctly dropped every claim, since none had a source.
  726| The prompt now requires at least two searches, and a turn with none is
  727| retried once.
  728| 
  729| **D17 · Medium · fixed (c2), hand-edited · compiler dropped topics**
  730| The flu what-if's compile dropped T2 (League) and T3 (prices) as "crowded
  731| out". Its counterfactual brief then differed from the control by more than
  732| the change. The spec was edited by hand to drop nothing, and its 12
  733| interviews were re-asked. Compiler c2 drops only topics that the settled
  734| facts make false.
  735| 
  736| **D18 · Medium · open · a quote named a nominee**
  737| A flu counterfactual quote said "That fellow Cox" (south:M:native_white-1)
  738| from a blinded brief. This is more evidence of D2 and L1: the model knows
  739| 1920. Quotes aren't scanned for real names before publishing.
  740| 
  741| **D19 · Low · open · choice and quote disagree**
  742| Haiku sometimes picks one candidate and quotes for the other:
  743| - Chaplin run, midwest man: choice Harding, quote "I'm going with the
  744|   Democrat".
  745| - Flu run, Arthur Hayes: choice Cox, quote praising "the Republican".
  746| 
  747| The counts use the choice and p_choice; the page shows the quote.
  748| 
  749| **D20 · Medium · fixed · evidence sign**
  750| The extractor recorded the historical direction as the scenario's effect.
  751| "The League hurt Cox" became toward-R for a scenario that removes the
  752| League. Findings now carry a `relation` field (like-scenario,
  753| reverses-scenario or context), and the code flips reversed findings. Context
  754| findings (who won, overall turnout) inform the reader but not the numbers.
  755| 
  756| **D21 · High · fixed (p5, compiler c3) · voters misread whom the news was about**
  757| In the first Harding-disclosure run, the brief identified the nominee only
  758| by descriptor ("the candidate of the party that has held a majority in
  759| Congress…"). Most of the 12 interviewed people blamed the other candidate.
  760| The result was a spurious 7.8-point move *toward* Harding.
  761| 
  762| Now:
  763| - **News on the line.** News about one nominee is printed on that
  764|   nominee's own ballot line (`about`, `nominee_news`).
  765| - **Manipulation check.** Each such counterfactual answers `news_about`.
  766|   Misreaders are left out of the counts, kept in the interviews with
  767|   `misread: true`, and flagged in confidence (`misread-change`). At least
  768|   half misreading forces "extremely low".
  769| 
  770| The rerun: 0 of 12 misread. The spec was recompiled with c3 and its key,
  771| label and words kept, a post-hoc edit.
  772| 
  773| **D22 · Medium · fixed · evidence read by party, not role**
  774| Findings from other elections were signed by that year's party. Cleveland
  775| in 1884, a scandal-hit *Democrat*, therefore counted as "toward D" for a
  776| scenario about a scandal-hit *Republican*. Findings now carry
  777| `role_direction` (toward or away from the candidate in the same role, plus
  778| an `affected` measure), and the code maps them onto the scenario's
  779| nominee.
  780| 
  781| **D23 · Medium · open · Harding-disclosure rerun: one uniform swing, quotes elsewhere**
  782| - **The swing is uniform.** Midwestern men go from 0.70 to 0.32 (Harding's
  783|   two-party share), Southern men from 0.68 to 0.31, and every region falls
  784|   to about 0.31–0.33. That looks like one model reaction stamped on everyone
  785|   (A2 homogenization), not differences between groups.
  786| - **The quotes mostly talk about prices.** Several switchers' quotes never
  787|   mention the news, even though their choice changed.
  788| - **Some quotes back the candidate the person didn't choose.** Albert
  789|   Jackson and Lillian Jones each chose Cox but quoted "the Republican" with
  790|   approval. This is D19 again: "the Republican" in a blinded quote is the
  791|   model guessing which label is which.
  792| 
  793| **D24 · Medium · open · 1924 withdrawal transfer**
  794| "No La Follette" moves his voters by one national transfer, estimated from
  795| 12 people: 80% to Davis, 8% to Coolidge, 11% stay home. The same transfer
  796| is applied in every state.
  797| 
  798| The record is mixed:
  799| - In 1920 the upper-Midwest farm and labor vote was heavily Republican.
  800| - In 1928 his former voters split between the parties.
  801| 
  802| So the Davis share is probably too high, and region matters. The evidence
  803| check says "untested" because no source gives a number. Fix: regional
  804| transfers, plus a prior from the 1928 split.
  805| 
  806| **D25 · High · by design · modern descriptors name offices (`profiles/1988–2024`)**
  807| From 1988 the descriptors give the nominee's office where voters plainly
  808| knew it: "the sitting President", "the sitting Vice President", "a former
  809| President seeking a second, non-consecutive term". That blinds the name, not
  810| the identity. With the year in the brief, any current model identifies every
  811| nominee, so **contamination is total for 1988–2020**. 2024 has holdout value
  812| only for a model whose training ends early in 2024.
  813| 
  814| Earlier years leak the same way through the record itself: "former
  815| commander-in-chief of the Continental Army" (1789), "the general … at New
  816| Orleans" (1824, 1828), "a former President" (1848, 1856), "the sitting
  817| Vice-President" (1860), "a longtime newspaper editor" (1872). This is D2
  818| for every year.
  819| 
  820| **D26 · Medium · open · 1928 and 1952 descriptors leave out what drove votes**
  821| Descriptors are party-role only, as in 1920/1924:
  822| - 1928's leave out Smith's Catholicism and his wet stance. Both 1928
  823|   platforms pledge Prohibition enforcement, so the brief hides the wet/dry
  824|   split Smith ran on.
  825| - 1952's leave out Eisenhower's war record.
  826| 
  827| Agents who recognise the year (D25) may supply these from memory. Agents who
  828| don't can't.
  829| 
  830| **D27 · Medium · open · 1948 Wallace voters**
  831| Thurmond is 1948's labelled third line. Wallace has none: `others_line`
  832| names his party, his voters can only answer "other", and his planks sit
  833| under party "O2", which `party_planks` never selects. In the counts, Wallace
  834| and Thurmond share the O slot.
  835| 
  836| **D28 · Medium · open · ballot access**
  837| One ballot for the whole country can't show a nominee missing from some
  838| states:
  839| - 1860: the Republican was on no ballot in 10 Southern states.
  840| - 1948: Truman wasn't on Alabama's ballot, and Thurmond held the Democratic
  841|   line in AL, LA, MS and SC.
  842| - 1964: Johnson wasn't on Alabama's ballot. `others_line` says so, but the
  843|   ballot still shows a D line. The `ballot_notes` key exists and isn't set.
  844| 
  845| Some candidates reach agents only through `others_line` or a shared
  846| descriptor: Bell (1860), Crawford and Clay (1824), the four Whigs (1836).
  847| 
  848| **D29 · Low · open · planks that aren't platforms**
  849| Some text that agents see as planks is something else:
  850| - **1980 Anderson:** his answers in the 21 September Baltimore debate (APP).
  851| - **1992 Perot:** the 15 October Richmond debate transcript (APP).
  852| - **1996 Perot:** the Reform Party's "Principles of Reform" from janda.org,
  853|   not APP. Re-spaced and undated.
  854| - **1840 Whigs:** campaign positions from secondary sources
  855|   (`verbatim: false`).
  856| - **1844 Whig Texas plank:** Clay's Raleigh letter. The platform says
  857|   nothing on Texas.
  858| - **Before 1840:** documented positions, not platforms (C29).
  859| 
  860| **D30 · Medium · by design · unopposed years**
  861| 1789 and 1792 have no D side, and 1820 has no R side. Those years get one
  862| ballot line and no swap arm, and their verdicts omit the runner-up. Their
  863| interviews measure turnout and dissent, not a contest (C28).
  864| 
  865| **D31 · Low · open · masks and label letters**
  866| - Common-word surnames (Clay, King, White, Grant, Bell, Smith and others)
  867|   are matched case-sensitively, or only with a first name or title, so
  868|   ordinary words don't count as leaks. A lower-case mention isn't caught.
  869| - Generic modern surnames (Dean, Clark, Harris, Stein, Ryan) cause false
  870|   naming violations in compiled specs. A false hit forces a recompile, not a
  871|   leak.
  872| - Masks run in sequence and produced "the the administration party". The
  873|   doubled "the" now collapses.
  874| - Label pools leave out initials of candidates, parties and prominent
  875|   figures. Questionable picks: P in 1936 and 1940 (Perkins; it may read as
  876|   "President"), E in 1932.
  877| 
  878| **D32 · Low · fixed · 1920 wording in other years**
  879| Found while building profiles, and fixed in the pipeline generalisation:
  880| - Every brief said "Election Day is Tuesday", which is wrong for 1789–1844,
  881|   when states chose on their own days.
  882| - `compile_system` called any third candidate "the independent Progressive
  883|   candidate" (Wirt, Van Buren, Fillmore, Breckinridge, Wallace, Anderson,
  884|   Perot).
  885| - `run._lead` always named R as the winner, which is wrong in every D year.
  886| 
  887| **D33 · High · fixed (p6) · interviews that didn't measure the change**
  888| A 1916 what-if ("war after the Lusitania") showed the interviews mostly never
  889| took the change in: voters at war since 1915 still praised the President for
  890| keeping the country out of war, because the real 1916 newspapers in their
  891| briefs said so (non-1920 years could drop no item: `drop_topics` only knows
  892| 1920's codes). Half the twelve slots went to women who could not vote in either
  893| world, no German-American, Irish-American or Western voter was asked (the
  894| live configs' `only_cohorts`), cohorts nobody was interviewed in got exactly
  895| zero effect, and one or two people per cohort bootstrapped to almost no spread
  896| ("Hughes wins in 0 of 100 draws"). Compiled what-ifs now get, in the live
  897| configs:
  898| - **Stronger once-per-change passes.** Compile and extract on Opus at high
  899|   effort; research on Sonnet at medium. They run once per change, not once
  900|   per voter, so they are the cheapest place to buy judgement.
  901| - **Staging** (`world.py`, Opus, high): the year's items the change makes
  902|   false leave the counterfactual brief (by id, any year); up to two in-world
  903|   items ("a local newspaper") and up to three consequences join it; a belief
  904|   check is designed; the groups history says the change moves are named.
  905| - **A belief check, asked first** in each counterfactual interview (p6). Its
  906|   two worlds must answer it differently, or it is discarded. A wrong answer
  907|   leaves the interview out.
  908| - **An audit** (Opus, medium) of each counterfactual answer's reason and
  909|   quote, without its vote: reasoning from the world as it was leaves the
  910|   interview out, whichever way it voted.
  911| - **Escalation**: a bulk-model (Haiku) answer that fails either check is
  912|   asked again, control and counterfactual, on Sonnet; the pair is compared
  913|   within itself as always. Failures are counted and shown as confidence
  914|   reasons whether or not escalation rescued them.
  915| - **No wasted slots**: someone who cannot vote in either world is replaced by
  916|   the next person drawn from the cohort (the first draws are unchanged), so
  917|   each cohort's effect describes the people it can move, which is where the
  918|   backbone applies it.
  919| - **Focus cohorts**: up to six cohorts the staging pass names are interviewed
  920|   for that what-if even when `only_cohorts` leaves them out.
  921| - **Borrowed cohorts**: a cohort the change reaches but nobody was asked in
  922|   takes the interviewed cohorts' effect (same sex and group first), per draw,
  923|   plus between-cohort noise (their spread, at least 0.15 logit), and the
  924|   evidence prior applies to it.
  925| - **Spread from who was drawn**: each cohort's draws are widened to at least
  926|   the person-to-person spread of a mean of its n people, estimated from every
  927|   pair in the run.
  928| Hand-written what-ifs and their runs are unchanged: every new behaviour is off
  929| in the config defaults and gated to compiled what-ifs. Costs: about $1–2 per
  930| typed what-if instead of about $0.50. The same day every dollar ceiling was
  931| removed: the daily cap (SIMULACRA_DAILY_DOLLARS), the per-what-if cap
  932| (`whatif_dollars`) and the interview caps (`max_dollars`, `max_requests`).
  933| Every paid call is still priced first and recorded in sessions/spend.jsonl.
  934| Caps later returned for the live intake: $100 per access key per day and $150
  935| in all. On 2026-10-02 they were removed again, with the access-key requirement
  936| and the stop for a stage costing over 1.5x its estimate: any visitor may queue
  937| a typed what-if. On 2026-11-20 caps returned without the access-key
  938| requirement: $20 a day and $200 a month, counted across every visitor
  939| together, checked before a text is queued and again by the worker before and
  940| during each text; a text that fails twice is given up instead of retried
  941| (docs/DEPLOY.md, Spend).
  942| 
  943| **D34 · High · fixed (compiler c4) · a typed what-if silently replaced**
  944| "America loses WW2", typed into 1940, was compiled as "Britain Falls, America
  945| Stands Alone": the United States wasn't at war by that election, and the
  946| compile prompt (never decline; no way to say "not what you asked") let the
  947| model substitute the nearest possible change and rename it. Everything after
  948| compile measured the substitute; only the "What changed" line hinted at it.
  949| Since c4 the compiler models the change as asked: a change that could not have
  950| happened by the context date gets the world in which it did, with the earlier
  951| departures from history it needs stated as fact, graded a-stretch or
  952| fantastical. It records `fidelity`; a reinterpreted change leads its result,
  953| its "how I got this" and the progress steps with a sentence saying what was
  954| asked and what was modelled, and never takes the reader's own words as its
  955| keywords. The 1940 substitute is kept as its own what-if, marked
  956| reinterpreted, without the words "america loses ww2".
  957| 
  958| **D35 · Medium · fixed (staging w2) · focus slots and an easy check**
  959| In the first staged run (1940, "Britain Falls"), the six focus slots all went to
  960| the first named group ("anyone in the Northeast"), and two of them to
  961| non-citizen cohorts that yield no interviews: the Pacific Coast and the
  962| Midwest's naturalized immigrants, also named, were never asked. The slots now
  963| go round the named groups in turn (largest cohort first), and a cohort in
  964| which no one can vote takes no slot. The belief check was answered right by
  965| 30 of 30 because its answer was printed in the brief; it now asks about a
  966| consequence the brief never states, with three or four plausible options. The
  967| audit now counts a passing phrase that relies on a state of affairs the change
  968| ended (an ally "still fighting" after it surrendered) as contradicting it.
  969| 
  970| ---
  971| 
  972| ## E. Counterfactual fictions
  973| 
  974| These are deliberate. Readers must still know they are invented.
  975| 
  976| **E1 · by design · `whatifs.py` `fifteenth`**
  977| The brief says the Supreme Court struck down Southern poll taxes and
  978| registration tests in 1919, and federal registrars were sent. This mechanism
  979| is invented to make the world internally consistent. It happened in no form
  980| in 1919.
  981| 
  982| **E2 · by design · `league`**
  983| "The United States took its seat in the League of Nations this spring" is
  984| invented. The real Senate vote on 19 March 1920 failed, 49–35. We also
  985| assume both parties would drop the League from their platforms.
  986| 
  987| **E3 · by design · `no-19th`**
  988| "Tennessee voted it down" is invented. Tennessee ratified on 18 August 1920.
  989| Women in 27 states keep the presidential vote under their own state laws.
  990| 
  991| **E4 · by design · the people**
  992| Every person, name and quote is invented. Only their circumstances (census
  993| cells, dated newspaper items) are documented. Quotes are voiced by a model
  994| that knows the outcome (D2).
  995| 
  996| **E5 · by design · compiled what-ifs (`harness/whatifs/*.json`)**
  997| A typed what-if's facts, ballot line and assumption are written by a model
  998| (`scenario.py`, compiler c1/c2). They are checked for nominee and party
  999| names, and are exploratory. Post-hoc edits:
 1000| - **`charlie-chaplin-runs`**: the positions carried "(documented)" and
 1001|   "(inferred…)" notes, which voters saw in the brief. The notes were
 1002|   stripped, "Would likely speak for" became "Speaks for", and the
 1003|   interviews were re-asked.
 1004| - **`influenza-returns-in-october-1920`**: see D17.
 1005| 
 1006| **E6 · by design · `charlie-chaplin-runs`**
 1007| Chaplin was born in England and was not a citizen, so the Constitution
 1008| barred him. The ballot line is modelled anyway, flagged
 1009| `ineligible-candidate`. His positions are inferred, since nothing on record
 1010| predates 1920, and flagged `positions-inferred`.
 1011| 
 1012| **E7 · by design · what-ifs in other years (`whatifs.py` `years`, `text_for`)**
 1013| The 1920 what-ifs now run in other years: `everyone` in all of them,
 1014| `fifteenth` in 1892–1964, `no-19th` from 1920, and `league` in 1920 only.
 1015| Their invented facts (E1–E3) were written for 1920. Other years get them by
 1016| rewriting "1920" in the assumption and borrowed text; 1924 is kept as it
 1017| was. Nobody has read the rewritten text year by year.
 1018| 
 1019| ---
 1020| 
 1021| **E8 · fixed · the 31 example what-ifs**
 1022| Thirty-one example what-ifs were run as chips across 28 years (about $7.80 in all). Four compiled specs were wrong and were fixed by hand or rebuilt. Each fix is recorded in the spec's `hand_edited`:
 1023| - **1972, no voting under 21:** the spec barred every adult. The cells have no age split, so `franchise.share` now bars a uniform 8.1% slice of every cell (the 18–20 share of 18+ in 1970 [I]). That slice votes like the rest of its cell, which understates the change, because young voters turned out less and leaned toward the challenger.
 1024| - **2000, Florida restores felons' rights:** the spec enfranchised every Southern adult. The spec now reaches Florida only (new `reach.state`), and the action lifts only the felony bar (new `franchise.reason: felony`). Newly eligible voters vote like their cell. Uggen & Manza assume lower turnout but a strong lean toward the administration party, so the cell assumption understates the change.
 1025| - **2000, Nader doesn't run:** with no named third in 2000, the compiler invented a candidate whose positions came from Perot's 1992 run. Nader is now 2000's named third: his per-state votes come from Wikipedia (2,882,955 nationally), and the profile has a blinded descriptor. The 2000 returns changed only in the `third` column, and every other year is byte-identical.
 1026| - **1932, no crash:** an earlier batch was killed mid-run, which left the key in the config but not in the bundle. The bundle was republished.
 1027| 
 1028| Four what-ifs (1844, 1856, 1860, 1916 Hughes) stopped at the research cost check: about $0.27–0.28 against a $0.175 estimate, because 19th-century searches return longer pages. The saved evidence was reused, so no search was repeated. The research estimate is probably low for pre-1900 topics.
 1029| 
 1030| Two code fixes:
 1031| - Parallel what-if runs collided on `sessions/intake-status.tmp`. The temporary file now carries the process id.
 1032| - When the winner changes, the headline now puts the new winner's electoral votes first (`serialize.winner_ev`). Before, it printed "Blaine wins, 129–272".
 1033| 
 1034| ## F. Product and copy
 1035| 
 1036| **F1 · Medium · open · `sampleEras.ts` (the sample model)**
 1037| The `no-19th` detail, "fifteen states that already let them", counts only
 1038| full-suffrage states. Twenty-seven states had given women the presidential
 1039| vote. Not edited.
 1040| 
 1041| **F2 · Medium · open · the sample model's women slice**
 1042| It treats Georgia and Mississippi women as voting in 1920.
 1043| 
 1044| **F3 · Medium · open · `stories.ts` / HANDOFF-SIMULATION (the original repo's, not ported)**
 1045| HANDOFF-SIMULATION lists story facts that are still unverified: 1800, 1860,
 1046| 1876, 1896, 1912, 1948 ("bubbles in a bar of soap"), 1960, 1968, 2000 and
 1047| 2016. This harness didn't check them.
 1048| 
 1049| **F4 · Low · open · `history.ts`**
 1050| Its known approximations are listed in HANDOFF-SIMULATION: split
 1051| delegations, 1836, 1872, 1864, faithless electors. The totals aren't yet
 1052| checked against NARA for every year. For 1920, 404–127 matches NARA.
 1053| 
 1054| **F5 · Medium · open · page slices**
 1055| The five 1920 groups are a partition, but they carry small misfits:
 1056| - "White Southerners" includes the few American Indian and Asian adults in
 1057|   the South.
 1058| - "Men outside the South" includes Black Northern men.
 1059| - Poor white Southerners kept out by poll taxes show as "stayed home", not
 1060|   "couldn't vote".
 1061| 
 1062| **F6 · Low · open · verdict copy**
 1063| - A multi-what-if verdict concatenates single-what-if sentences, so a
 1064|   combination can say "3.5 million women" measured in a different world
 1065|   from the combined one.
 1066| - The League verdict's "2.7 points" is measured in the point draw only.
 1067| 
 1068| **F7 · Medium · open · slice-source sentences (`profiles/<year>.json`)**
 1069| Each profile's `slice_sources` names the census vintages its year uses
 1070| (e.g. 1952 "the 1950 census aged", 2020 "ACS 2019/2021"). They were written
 1071| before most populations existed, so they describe the intended build, not
 1072| what `data.population` does. 1932 and 1936 promise the 1930 Mexican count
 1073| folded into white (C20). 1972–2024 cite vintages that differ from the files
 1074| actually used (C27).
 1075| 
 1076| **Next:** generate each sentence from the population build's own
 1077| provenance.
 1078| 
 1079| **F8 · Low · open · electoral-vote labels (`ev_label`)**
 1080| Some labels are conventions a reader could dispute (see also F4):
 1081| - **1789–1800:** before the 12th Amendment only each side's top man counts.
 1082|   Second votes (Adams 1789–92, Pinckney, Burr) aren't O. 1800 was a 73–73
 1083|   Jefferson–Burr tie decided by the House.
 1084| - **1824:** Adams won the House contingent election, not the electoral vote
 1085|   (84–99–78).
 1086| - **1832:** O is Wirt's 7 plus Floyd's 11 from South Carolina's legislature.
 1087| - **1860:** O is Breckinridge plus Bell.
 1088| - **1872:** 286–63 counts the D-ticket votes counted after Greeley's death.
 1089|   286–66 is also defensible.
 1090| - **2000:** one DC elector abstained, which isn't an O vote.
 1091| - **Order varies.** 1948 and 1956–1984 put the winner first (1948
 1092|   303–189–39, 1960 303–219–15). 1789–1836 and 1988–2024 are R–D(–O).
 1093| 
 1094| 
 1095| **F9 · Low · open · place matching in typed text (`places.ts`)**
 1096| "Washington, D.C." in a typed what-if lights up Washington state. The D.C.
 1097| rule ends in `\b`, which can't match after the final period. Carried over
 1098| from the source and kept as is during the port.
 1099| 
 1100| **Next:** end the D.C. pattern with a lookahead for a non-word character or the
 1101| end of the text, and add a test.
 1102| ---
 1103| 
 1104| ## G. Reproducibility
 1105| 
 1106| **G1 · Medium · fixed · `config.py`**
 1107| A run's id used to hash its config and data, **not the code**. The
 1108| `1920-bcbd86b43f` bundle was produced by code changed after its requests
 1109| were planned and answered (p1 → p2, deviations 1–9), so that run id can't be
 1110| regenerated from today's code with identical results.
 1111| 
 1112| **Fixed:** `run_id` now also hashes `simharness/*.py`, so a code change gives a
 1113| new run id. Runs recorded before the change keep their old ids. The prototype's
 1114| interviews were re-scored with today's code as `1920-2c8ce73571` (EVAL.md), which commits
 1115| its `agents/` and reads only `data/1920/`, so it reruns from the repo.
 1116| 
 1117| **G2 · Low · open · timing**
 1118| The backbone was refitted after the agent answers existed. The cohort bias
 1119| (A1) and shrinkage use the final backbone, not the one in place when the
 1120| requests were planned.
 1121| 
 1122| **G3 · Low · fixed · environment**
 1123| The installed Anthropic SDK was 0.46, which predates `output_config`. The API
 1124| backends need `anthropic>=1.0`, which the `llm` extra now requires
 1125| (`pyproject.toml`). They have since run live, from the quick and rung 1 runs
 1126| on.
 1127| 
 1128| **G4 · Low · by design · answer cache (`llm.AnswerCache`)**
 1129| Identical requests reuse earlier live answers across runs. A request is
 1130| identical when it has the same model, system, user text and schema; meta,
 1131| run id and prompt-version labels are ignored. So p4 requests whose text
 1132| equals p3's reuse p3 answers. Transcript answers are never cached.
 1133| Each answer records `cached_from`.
 1134| 
 1135| **G5 · Medium · open · evidence reproducibility**
 1136| Web search results change over time. The saved
 1137| `whatifs/evidence/<key>.json` is the record: queries, every source, the
 1138| cited text and the notes. It is hashed into the run id. Re-researching
 1139| (`--refresh`) makes a new instrument.
 1140| 
 1141| **G6 · Low · open · spend ledger**
 1142| `sessions/spend.jsonl` started mid-day. The earlier sessions' $0.26 is
 1143| backfilled from runs' usage, and D15's $0.052 is estimated. Since the intake
 1144| caps, each line also records the access key's name (`who`) and its `ts` and
 1145| `day` are UTC (earlier lines are local time), and the server drops a line's
 1146| `note`, which holds the typed words, after 7 days.
 1147| 
 1148| **G7 · Medium · open · generators outside the repo**
 1149| The all-years profiles, configs and platform files were written by scratch
 1150| scripts kept in session scratchpads (`gen_d1.py`, `d3_build.py`,
 1151| `d3_planks.py` and unnamed ones for the other years). So was the 1920/1924
 1152| invariant capture (`inv/capture.py`). The felony-rate parsers live in the
 1153| cache beside their PDFs. None can be rerun from the repo; the outputs are
 1154| the record.
 1155| 
 1156| **Next:** move the generators into `scripts/`.
 1157| 
 1158| **G8 · Low · open · holdout states**
 1159| Holdout sets were drawn three ways. live-1924 reuses 1920's draw. 1789–1836
 1160| take a quarter of the hand-listed popular-vote states, some of them
 1161| uncertain (TN 1800). 1880–2024 take
 1162| `sorted(random.Random(year).sample(states, 12))`.
 1163| 
 1164| **Next:** one formula, written down before any holdout check is run.
 1165| 
 1166| **G9 · Low · by design · 1920/1924 invariant**
 1167| The generalisation was checked against a capture taken before any edit.
 1168| Every plan request, compile request and publish bundle for 1920 and 1924 is
 1169| byte-identical, except 1924's compile prompt: its list of existing what-ifs
 1170| now includes `no-19th`. Each typed 1924 text misses the compile cache once
 1171| (about $0.02); no brief changes. Legacy 1916–1924 data still goes through
 1172| the untouched loaders.
 1173| 
 1174| **G10 · Medium · open · which run is served (`intake.run_pipeline`)**
 1175| A year can have many run folders (a code change makes a new one, G1; 1920
 1176| has 23). The served bundle, `serve/bundles/<year>.json`, is whichever run
 1177| published last: `run_pipeline` copies it over the previous one. Nothing
 1178| records why a run is the served one, and nothing requires it to have been
 1179| validated. 1920 serves `1920-1a2dcd24ad`, which has no `validation.json`;
 1180| EVAL.md scores `1920-2c8ce73571`, the prototype's interviews re-scored with today's code. `serve/bundles/RUN_ID`
 1181| holds only the last run published for any year.
 1182| 
 1183| **Next:** a registry of served runs (year, run id, date, why), and evaluate
 1184| or verify the served run before it replaces the last one.
 1185| 
 1186| **G11 · Low · by design · dependency audit (`package.json` `auditConfig`)**
 1187| CI's `pnpm audit --audit-level=high` ignores one advisory:
 1188| GHSA-3r8g-jcqq-3p5j (CVE-2026-128120), a denial of service while SvelteKit
 1189| parses form data for remote functions' `form`. It is fixed only in SvelteKit
 1190| 3.1.1, a major upgrade. It doesn't apply here: the page is a static,
 1191| client-only build (`adapter-static`, `ssr = false`) with no SvelteKit server
 1192| and no remote functions. The other SvelteKit 2 advisories still reported
 1193| (GHSA-6cf5-gc4q-fm3x, moderate: remote `query.batch`; GHSA-pfhg-q3qv-9q6r and
 1194| GHSA-27mw-82g8-phjj, low: enhanced forms and prerendered pages; and cookie
 1195| GHSA-pxg6-pf52-xh8x, low) concern features the page doesn't use either.
 1196| 
 1197| **Next:** upgrade to SvelteKit 3 and drop the ignore if the page is ever
 1198| developed again.
 1199| 
 1200| ---
 1201| 
 1202| ## H. Historical evidence
 1203| 
 1204| **H1 · by design · evidence never enters a brief**
 1205| Research results are used only after the interviews:
 1206| - **Agreement:** do the interviews move votes or turnout the way the record
 1207|   does?
 1208| - **Blend:** a prior on cohort effects, for compiled, exploratory what-ifs
 1209|   only.
 1210| - **Confidence tier.**
 1211| 
 1212| Hand-written what-ifs are never blended; their numbers follow
 1213| METHOD.md.
 1214| 
 1215| **H2 · Medium · open · source grading**
 1216| Tiers come from a domain list (`evidence.TIER_A`, `TIER_B`; everything else,
 1217| including Wikipedia, is C). A .edu course page counts as A. A finding's
 1218| grade is its tier × the extractor's match judgement (same-event …
 1219| distant). Neither is validated.
 1220| 
 1221| **H3 · Medium · open · blend weights**
 1222| Evidence sd grows as 1/√grade. The interview sd is floored at 0.2 logit,
 1223| because a bootstrap over two or three people understates model error. Weak
 1224| evidence barely moves numbers: Chaplin's evidence weight is under 1%.
 1225| 
 1226| **H4 · Medium · open · confidence tiers**
 1227| `evidence.confidence` is a rule set:
 1228| - a kind's base tier;
 1229| - plausibility and anachronism;
 1230| - evidence strength;
 1231| - agreement;
 1232| - interview stability, for agent-mode what-ifs only;
 1233| - the number of interviews.
 1234| 
 1235| "Extremely low" (very-low) reaches the page as `confidence: low`, plus
 1236| `confidenceTier` and a sentence in the summary. The rules were written
 1237| after seeing the first three results, and nothing calibrates them.
 1238| 
 1239| ---
 1240| 
 1241| ## Log
 1242| 
 1243| | Entry | Change |
 1244| |---|---|
 1245| | all | File started from EVAL.md, METHOD.md, the agents' reports and the session's own mistakes |
 1246| | G2 | Analysis paired control/cf/swap answers on a hardcoded `|sonnet` request id, so any run on another bulk model (the Haiku quick run) silently yielded no effects, no L2 and no voters. Now keyed on the configured bulk/check models. |
 1247| | D9 | Quick run (Haiku, 2 agents): the recall probe named 1920, both candidates and the winner at 95% confidence from the blinded brief. One probe, but it matches L1's standing exposure. |
 1248| | D10 | Quick run: in the no-19th counterfactual the Indiana woman still answered able_to_vote=yes, reasoning from Indiana's 1919 presidential-suffrage law; the Black North Carolina woman answered no in control, no-19th and league, yes only under fifteenth. Plausible, but the no-19th brief should say explicitly whether state-law suffrage survives. |
 1249| | D11 | Rung 1 (run 1920-4502a6f977): a quote named the blinded ballot label ("K says the money got too loose…", south:M:native_white-0). The page would show a meaningless letter to readers. The prompt should tell agents to name candidates by description, not label, in `quote`; or quotes need a label→name pass before publish. |
 1250| | D12 | Rung 1: the League effect's sign flips by paraphrase (dr −0.61, +0.49, +0.03 for paraphrases 0/1/2, n=12 agents). Two single-agent flips go in opposite directions (midwest woman R→D; northeast man D→R). The national dr CI [−0.19, +0.15] spans zero. At this n the paraphrase spread (A3) is larger than any effect. |
 1251| | D13 | Prompt p3 (run 1920-423843d9ec): no quote used a letter label (0/24, fixes D11). Haiku ignored the 25-word cap (mean 30.5, max 40 words). A hard limit needs a trim at publish or a schema maxLength, not prompt wording. |
 1252| | D14 | Live config: adding two cohorts reassigned every later agent's paraphrase (0 of 48 cache hits); reverted to rung 1's six cohorts. |
 1253| | D15 | Chaplin research: Haiku extract gave 0 findings from rich notes; Sonnet extract truncated at 4,000 tokens (~$0.052 lost usage, estimated in ledger). |
 1254| | D16 | League research, first call: 0 searches, answered from memory; grounding dropped all claims. Now ≥2 searches, one retry. |
 1255| | D17 | Flu what-if compiled with T2/T3 dropped; hand-edited to none and re-asked; compiler c2. |
 1256| | D18 | Flu cf quote named "Cox" from a blinded brief. |
 1257| | D19 | Haiku choice/quote contradictions (Chaplin, flu runs). |
 1258| | D20 | Extractor gave League findings the historical sign; `relation` field added, flip done in code. |
 1259| | E5, E6 | Chaplin positions hand-edited (annotations visible to voters); ineligible candidate modelled and flagged. |
 1260| | G4–G6 | Answer cache, evidence reproducibility, spend ledger. |
 1261| | H1–H4 | New stage: historical evidence (research → extract → agreement, blend, confidence tiers). All exploratory. |
 1262| | D21–D23 | Harding disclosure: misattribution fixed (ballot-line news + manipulation check, p5/c3; 0/12 misread on rerun); evidence by role; homogenized swing logged. |
 1263| | C13–C16, D24 | 1924 added: population aged from 1920, carried-forward backbone (R1 exact; C–W women MAE 3.6), no 1924 corpus, platforms from APP; La Follette withdrawal via interview transfer (80% Davis). |
 1264| | C17 | NHGIS extract 1 (1870–1970 state tables); 1920 rebuild matches exactly; 1930 NT10 label misalignment caught and fixed; 1930 Mexican race in `other`. |
 1265| | A9 | All-years build: agents G, C and E sent the user's email in User-Agent headers to Wikipedia and loc.gov; removed from every script; sent requests can't be recalled. |
 1266| | B7, B8 | Amended: per-era economy wording, ages 18–80 from 1972, 1920-era first names; IN/MO/TX/AR alien voting coded [I] for 1920 but not applied to legacy years. |
 1267| | B10 | general_fit: every non-1916–24 year runs on literature priors plus exact calibration; no in-year identification. |
 1268| | B11 | Gallup 1936/1940 show women slightly more R, contradicting the 1920 δ used to 1940. |
 1269| | B12 | general_fit repairs (scaled adults, overridden rules, synthetic cells) make reproduction exact by construction; not on the page. |
 1270| | B13 | All 60 elections, 1789–2024, reproduce certified R/D/O and history's EV: ev_fixed, ev_split, lumped-O rule (1860, 1892, 1912), pre-1868 EV counts electors who voted. |
 1271| | C15 | Amended: corpus build stopped before 1924 (C30). |
 1272| | C18 | 1870–1910 women from F/M ratios run 2.0% high against the 1910 hand table (foreign white +10.4%). |
 1273| | C19 | 1870–1910 estimates: 1900 NT7 mislabel asserted; 1890 citizenship interpolated; 1870 IPF and clipped naturalized; colored splits. |
 1274| | C20 | 1940 counts Mexican Americans as white: `other_races` 1.01M → 0.33M is classification, not population. |
 1275| | C21 | 1960/1970 nativity carried from 1950: 1970 foreign-born whites ~3M high. |
 1276| | C22 | 1940–1970 Negro share interpolated, 18–20 add-on, HI 1950 missing, GA 1944/48 18+ from 1950 ratio. |
 1277| | C23 | Returns 1868–2024: 153 state-years fail the county-sum check (MO ~1.2×); A–A state file wrong for 1968 NC and 2020 NE. |
 1278| | C24 | Pre-1868 adults all [I]: age-band splits, 1790 16+ conversion, no nativity before 1850. |
 1279| | C25 | Alien-voting, property and taxpaying rules coded from memory of Keyssar/Hayduk; unchecked; GA 1840 turnout 102%. |
 1280| | C26 | Felony rates 1972–2008 interpolated between 1980 bins and 2010; law changes smoothed; national fallback rates in agents. |
 1281| | C27 | 1980–2024 adults: FB-by-race estimates, 1990 unraked, 2020 −1.96% to PL, borrowed files for 1972–2004. |
 1282| | C28 | 1789–1824 popular votes fragmentary (~20 partial or lost rows; 1789, 1792, 1820 uncontested). |
 1283| | C29 | Platforms 1789–2024: hand-copied Founders Online quotes, OCR sources, no platforms before 1840, 2020 R, 2024 D. |
 1284| | C30 | Corpus build stopped by the user; schema inferred after blocked reads; per-year topics. |
 1285| | D25 | Modern descriptors name offices: contamination total for 1988–2020. |
 1286| | D26 | 1928 descriptors omit Catholicism and the wet stance; 1952 omits the war record. |
 1287| | D27 | 1948 Wallace voters can only answer "other"; his planks never shown. |
 1288| | D28 | Ballot access not expressible (1860, 1948 AL/LA/MS/SC, 1964 AL). |
 1289| | D29 | Anderson 1980 and Perot 1992 planks from debates; Perot 1996 from janda.org; 1840/1844 Whig non-platform text. |
 1290| | D30 | Unopposed 1789, 1792, 1820: one ballot line, no swap arm. |
 1291| | D31 | Case-sensitive short-name masks, generic modern surnames, "the the", questionable label letters. |
 1292| | D32 | Fixed: "Election Day is Tuesday" pre-1845, "independent Progressive" for every third candidate, `_lead` naming R. |
 1293| | E7 | 1920 what-ifs run in other years by rewriting "1920"; text not reviewed per year. |
 1294| | F7 | Profiles' slice-source sentences describe intended census builds, not the files used. |
 1295| | F8 | Disputable ev_label conventions (pre-12th Amendment, 1824, 1832, 1860, 1872, 2000) and mixed slot order. |
 1296| | G7 | Profile, config, platform and invariant generators live in scratchpads, not the repo. |
 1297| | G8 | Holdout sets drawn three different ways. |
 1298| | G9 | 1920/1924 byte-identity held except 1924's compile prompt (~$0.02 cache miss per typed text). |
 1299| | E8 | 31 example what-ifs as chips; 1972/2000-FL specs hand-fixed, Nader made 2000's named third, 4 research cost stops, headline winner-first. |
 1300| | A10 | Held-out benchmark read moved out of `Run.verify` into `benchmarks.py`; `test_benchmarks_isolated` passes again. |
 1301| | C31 | Missouri 1820 and Michigan 1836 have electoral votes but no map tile. |
 1302| | C32 | State electoral votes are electors allotted, not cast, in 8 years. |
 1303| | C33 | Minor faithless and abstaining electors aren't listed in 7 years. |
 1304| | F9 | "Washington, D.C." in typed text matches Washington state. |
 1305| | G1 | Entry still said run ids don't hash the code; `run_id` already hashes `simharness/*.py`. Marked fixed. |
 1306| | D33 | Staging, belief check (p6), reasoning audit, escalation, barred-slot replacement, focus and borrowed cohorts, spread floor; Opus at high effort for the once-per-change passes. |
 1307| | D34 | Compiler c4: what-ifs modelled as asked (impossible timing gets its own world, graded fantastical); reinterpretations said first; substitutes never take the reader's words. |
 1308| | D35 | Focus slots round-robin, unvotable cohorts skipped; belief check asks an unstated consequence; audit counts passing slips (staging w2). |
 1309| | D36 | Live configs: interviews on Sonnet 5.5 at medium effort (was Haiku), escalations on Opus 5.5; fast mode (2x price) on every Opus call. Every year's controls are re-asked once on the new model. |
 1310| | A11 | `verify` won't score Corder–Wolbrecht as held out where the women's-turnout prior uses its knots (1928–1948); it never had, since the file holds 1920 and 1924 only. |
 1311| | A12 | `test_benchmarks_isolated` parses modules and scripts instead of grepping lines; each known bypass is tested. |
 1312| | G6 | Ledger lines carry `who` and UTC days; old lines lose `note`. |
 1313| | G10 | Which run each year serves is the one published last; 1920 serves `1920-1a2dcd24ad`, which has no `validation.json`. |
 1314| | G11 | Dependency refresh (zod, express, vite, SvelteKit 2.70.4, adapter-static, vitest 4); audit ignores CVE-2026-128120, which doesn't apply to a static build. |
```

## `Dockerfile`

```
    1| # syntax=docker/dockerfile:1
    2| 
    3| # The simulation API: the Express router (Node 22) and the harness worker it
    4| # spawns (Python 3.13) in one container. ARM64 (Fargate Graviton), built on a
    5| # native ARM runner by .github/workflows/deploy-api.yml.
    6| #
    7| # The image holds code only. Everything the worker writes (serve/bundles,
    8| # sessions, runs, whatifs, configs) and the census-derived cache live on EFS
    9| # at /state; see "State" below. No secrets and no cache data are in any layer:
   10| # ANTHROPIC_API_KEY arrives from Secrets Manager at runtime.
   11| 
   12| # ---------------------------------------------------------------------------
   13| # Stage 1: the server bundle (dev dependencies, esbuild)
   14| # ---------------------------------------------------------------------------
   15| FROM node:22-bookworm-slim AS build
   16| WORKDIR /app
   17| RUN corepack enable
   18| COPY package.json pnpm-lock.yaml ./
   19| RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
   20|     pnpm install --frozen-lockfile --ignore-scripts
   21| COPY serve ./serve
   22| # express and zod stay external and come from the prod install below.
   23| # esbuild is vite's dependency; pnpm hoists it into .pnpm/node_modules.
   24| RUN node node_modules/.pnpm/node_modules/esbuild/bin/esbuild serve/server.ts \
   25|       --bundle --platform=node --format=esm --target=node22 --packages=external \
   26|       --outfile=dist/server.mjs
   27| 
   28| # ---------------------------------------------------------------------------
   29| # Stage 2: production node_modules only (express, zod, ...)
   30| # ---------------------------------------------------------------------------
   31| FROM node:22-bookworm-slim AS prod-deps
   32| WORKDIR /app
   33| RUN corepack enable
   34| COPY package.json pnpm-lock.yaml ./
   35| RUN --mount=type=cache,target=/root/.local/share/pnpm/store \
   36|     pnpm install --frozen-lockfile --prod --ignore-scripts
   37| 
   38| # ---------------------------------------------------------------------------
   39| # Stage 3: the harness venv
   40| # ---------------------------------------------------------------------------
   41| FROM python:3.13-slim-bookworm AS pydeps
   42| COPY requirements.lock /tmp/requirements.lock
   43| RUN --mount=type=cache,target=/root/.cache/pip \
   44|     python -m venv /opt/venv && /opt/venv/bin/pip install -r /tmp/requirements.lock
   45| 
   46| # ---------------------------------------------------------------------------
   47| # Stage 4: runtime
   48| # ---------------------------------------------------------------------------
   49| FROM python:3.13-slim-bookworm AS runtime
   50| 
   51| # Node comes from the official image (same major as CI); no npm, no toolchain.
   52| COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
   53| COPY --from=pydeps /opt/venv /opt/venv
   54| 
   55| RUN apt-get update \
   56|  && apt-get install -y --no-install-recommends ca-certificates \
   57|  && rm -rf /var/lib/apt/lists/* \
   58|  && useradd --uid 1000 --create-home app
   59| 
   60| WORKDIR /app
   61| COPY --from=prod-deps /app/node_modules ./node_modules
   62| COPY --from=build /app/dist ./dist
   63| COPY package.json pyproject.toml ./
   64| COPY simharness ./simharness
   65| COPY extracts ./extracts
   66| COPY profiles ./profiles
   67| COPY docker/entrypoint.sh /usr/local/bin/simulacra-entrypoint
   68| 
   69| # State. The harness derives every path from its own location (config.py
   70| # ROOT = the folder above simharness/), and intake.py writes ROOT/serve/bundles
   71| # whatever SIMULACRA_BUNDLES says. So the code-relative folders are symlinks
   72| # onto the EFS mount, and both the router and the worker see the same files.
   73| # EFS is seeded once by the seed task (scripts/sync-data.sh), never from here.
   74| RUN mkdir -p serve \
   75|  && ln -s /state/bundles  serve/bundles \
   76|  && ln -s /state/sessions sessions \
   77|  && ln -s /state/runs     runs \
   78|  && ln -s /state/whatifs  whatifs \
   79|  && ln -s /state/configs  configs
   80| 
   81| ENV NODE_ENV=production \
   82|     PORT=8080 \
   83|     SIMULACRA_LOG=1 \
   84|     SIMULACRA_AUTORUN=configs/live-1920.json \
   85|     SIMULACRA_PYTHON=/opt/venv/bin/python \
   86|     SIMULACRA_BUNDLES=/app/serve/bundles \
   87|     SIMHARNESS_CACHE=/state/cache \
   88|     PYTHONUNBUFFERED=1
   89| EXPOSE 8080
   90| USER app
   91| 
   92| # Exec form. In ECS, initProcessEnabled puts tini at PID 1; the entrypoint
   93| # execs node, so node receives SIGTERM directly (serve/server.ts handles it).
   94| ENTRYPOINT ["/usr/local/bin/simulacra-entrypoint"]
   95| CMD ["node", "dist/server.mjs"]
```

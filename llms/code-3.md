# simulacra-americana: source and docs, part 3 of 17

Generated from commit `caf86112f396` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `docs/harness/README.md` to `requirements.lock`. Lines are numbered as in the repository.

## `docs/harness/README.md`

```markdown
    1| # Simulacra Americana harness
    2| 
    3| This is the simulation behind `/api/simulacra`. Its code and data sit at the repo
    4| root (`simharness/`, `configs/`, `profiles/`, `whatifs/`, `extracts/`, `runs/`,
    5| `serve/`); this README lives in `docs/harness/`, and the method documents stay
    6| at the root.
    7| 
    8| - **The statistical backbone** decides the counts.
    9| - **LLM agents** supply the counterfactual response and the quotes.
   10| 
   11| Read [`METHOD.md`](../../METHOD.md) first. Then read [`EVAL.md`](../../EVAL.md) (the 1920 prototype's results, failures included).
   12| 
   13| **[`VALIDITY.md`](../../VALIDITY.md)** takes stock of what the harness can and can't claim: contamination by the language model's knowledge, leakage, historical bias, the held-out checks that exist and the ones that don't, and the next steps in order.
   14| 
   15| **[`DISCLOSURES.md`](../../DISCLOSURES.md)** is the running log of every known inaccuracy and honesty flag.
   16| Add to it the moment something is found.
   17| 
   18| Nothing here is imported by the page; the page reads bundles through the
   19| server. The bundle's shape is `simharness.serialize.Bundle`, with a shared
   20| example at `tests/fixtures/bundle.example.json`; the server's zod schema
   21| (`serve/bundle.ts`) parses the same file, and the page's side of the contract
   22| is `src/lib/simulacra/schemas.ts`.
   23| 
   24| ## Layout
   25| 
   26| | Path | What |
   27| |---|---|
   28| | `simharness/config.py` | Run config. A run's id hashes the config and the data manifest. |
   29| | `simharness/data.py` | Loaders for the cache (labels, census, franchise, corpus, platforms) |
   30| | `simharness/backbone.py` | Turnout and choice by cell, 400 posterior draws, exact calibration |
   31| | `simharness/whatifs.py` | The what-ifs: what each changes, its assumption, and the facts a counterfactual brief states |
   32| | `simharness/cohorts.py`, `agents.py` | Agent cohorts (merge rule) and invented people drawn from them |
   33| | `simharness/prompts.py` | The versioned prompts: blinded control, non-hypothetical counterfactual, probe, schemas |
   34| | `simharness/agentlayer.py` | Every model request for a run |
   35| | `simharness/llm.py` | Backends: `anthropic`, `anthropic-batch`, `transcript` |
   36| | `simharness/paired.py` | Paired differences, cohort bias, the shrinkage |
   37| | `simharness/quotes.py` | Quote selection and the stereotype audit |
   38| | `simharness/aggregate.py`, `serialize.py` | Draws → states, EV and ranges → the page's shape |
   39| | `simharness/evaluate.py`, `benchmarks.py` | The validation checks. Only these read held-out benchmarks. |
   40| | `simharness/scenario.py` | Any typed what-if → a spec of one of five kinds (franchise, population, issue, event, candidate) with generic mechanics |
   41| | `simharness/world.py` | The staging pass for a compiled what-if's world, and the audit of the interviews' reasoning (DISCLOSURES D33) |
   42| | `simharness/evidence.py` | Historical evidence: web-search research, grounded extraction, source tiers, agreement, blend, confidence tiers |
   43| | `simharness/intake.py` | Typed what-if intake: compile → research → register → run → `serve/bundles/`; the router's queue |
   44| | `simharness/agent.py` | The research agent: the same stages as tools a model chooses, behind a permission gate; replay and approval |
   45| | `simharness/trace.py` | Step-level traces of the agent (`sessions/traces/`), their summaries and retention |
   46| | `simharness/agent_eval.py` | Golden tasks for the agent from the compiled what-ifs, scored field by field |
   47| | `simharness/profiles.py` | Loads one profile per election (names, blinded descriptors, label letters, ballot wording, sources): 1920 and 1924 in code, the other 58 from `profiles/<year>.json` |
   48| | `simharness/run.py` | The command line (`python3 -m simharness.run <stage>`) |
   49| | `simharness/pipeline.py` | The stages: backbone, plan, ask, analyze, verify, dryrun, evaluate (`Run`) |
   50| | `simharness/publish.py` | The publish stage: every what-if combination → the bundle |
   51| | `serve/simulacra.ts`, `serve/index.ts` | The Express router that serves the bundles, and the server that mounts it at `/api/simulacra` next to the static page |
   52| | `serve/bundles/<year>.json` | The bundles the server serves (`SIMULACRA_BUNDLES` overrides the folder) |
   53| | `extracts/` | IPUMS extract definitions: we ship definitions, never microdata |
   54| | `data/1920/` | The public 1920 inputs (census tables, returns, franchise, a held-out benchmark), so `SIMHARNESS_CACHE=data/1920` reruns the 1920 backbone and checks; licences and sources in its `PROVENANCE.md` |
   55| | `runs/<id>/` | Everything a run wrote: config, fit, requests, answers, analysis, validation, `published/1920.json`. The repo keeps only `config.json`, `analysis.json`, `validation.json` and `published/`; `fit.pkl`, `effects.pkl` and `agents/` are regenerable and stay local |
   56| | `runs/_cache/` | Identical-request answer cache (regenerable from `runs/*`; gitignored) |
   57| | `whatifs/<key>.json`, `whatifs/evidence/<key>.json` | Compiled what-ifs (exploratory) and every what-if's researched evidence; both hashed into run ids |
   58| | `sessions/` | Dev only, gitignored: typed requests, the unknown-text queue, intake outcomes, the spend ledger |
   59| | `scripts/harness/` | The cache build scripts (returns, franchise, population, corpus, NHGIS extracts) and `bundle_fixture.py` |
   60| | `scripts/harness/nhgis_common.py` | The NHGIS extract client and the population builders' shared helpers |
   61| | `scripts/harness/sessions-report.py` | What people typed, the share unmodelled, unknowns by kind, today's spend |
   62| 
   63| The raw data lives outside the repo, in `SIMHARNESS_CACHE`. It defaults to
   64| `~/research_notes/historical_election_sim_data/harness_cache`, and each folder
   65| there has a `PROVENANCE-*.md`.
   66| 
   67| Some sources can't be redistributed (IPUMS, NHGIS), so the cache stays
   68| outside the repo. Only aggregates reach `runs/`.
   69| 
   70| ## Run it
   71| 
   72| From the repo root (`pip install -e '.[test]'` once; add `'.[llm]'` for the paid stages):
   73| 
   74| ```sh
   75| python3 -m simharness.run backbone      # fit + unchanged-run reproduction
   76| python3 -m simharness.run plan          # agents and requests (no model calls)
   77| python3 -m simharness.run ask           # send requests (backend from the config)
   78| python3 -m simharness.run analyze       # paired effects, probes, bias, audit
   79| python3 -m simharness.run evaluate      # validation checks → validation.json
   80| python3 -m simharness.run publish       # every what-if combination → published/1920.json
   81| python3 -m pytest -q                    # fast unit checks (tests/)
   82| ```
   83| 
   84| Typed what-ifs and historical evidence (all paid stages priced first and recorded in
   85| `sessions/spend.jsonl`; see `simharness/intake.py`):
   86| 
   87| ```sh
   88| H=~/.venvs/simharness/bin/python
   89| $H -m simharness.run whatif --text "charlie chaplin ran as an independent" --config configs/live-1920.json
   90| $H -m simharness.run whatif --queue --config configs/live-1920.json     # what the page couldn't model
   91| $H -m simharness.run research --config configs/live-1920.json           # evidence for the config's what-ifs
   92| $H -m simharness.run research --key league --refresh | --reextract ...  # one what-if; search again, or re-read saved notes
   93| ```
   94| 
   95| How a typed what-if is modelled:
   96| 1. **Compile** (`research.compile_model`; Opus in the live configs): the words become a settled-fact change of one kind,
   97|    with who it reaches, a plausibility grade, keywords and research questions.
   98|    Nominee and party names are sent back and masked. A request that means an
   99|    existing what-if only adds keywords.
  100| 2. **Research** (`research.research_model`, Sonnet, + web search): scholarship, official statistics and
  101|    archives on the change itself, the same groups in the most similar
  102|    situations, and any named person's record before the context date.
  103| 3. **Extract** (`research.extract_model`; Opus in the live configs): findings grounded in the sources the
  104|    search returned. Each is graded by source tier × match, and signed for the
  105|    scenario (a situation the change undoes counts the other way).
  106| 4. **Stage** (`world.py`, when `research.world_model` is set): the year's
  107|    items the change makes false leave the counterfactual brief, in-world news
  108|    and a belief check are added, and the groups to interview are named.
  109| 5. **Interview**: the usual paired control/counterfactual briefs. A candidate
  110|    gets a third labelled ballot line (p4). Identical earlier requests are
  111|    reused, so only the new arm is paid for.
  112|    Answers that fail the belief check or the reasoning audit are left out, or
  113|    re-asked on `agents.escalate_model`.
  114| 6. **Evaluate**: the interviews against the record on votes and turnout
  115|    (corroborated, consistent, contradicted, untested). For exploratory
  116|    what-ifs, the evidence is also a precision-weighted prior on each cohort's
  117|    effect.
  118| 7. **Confidence**: high, medium, low or very low ("Extremely low
  119|    confidence"), with the reasons. The tier reaches the page as
  120|    `confidenceTier`, `confidenceFlags` and `confidenceReasons`, and as a
  121|    sentence in the summary.
  122| 
  123| ### The research agent
  124| 
  125| `simharness/agent.py` runs the same stages as tools, in an order a model chooses:
  126| it can compile again with a note when a reading is wrong, research again with
  127| sharper questions when the evidence is thin, take an existing what-if, or stop
  128| before any interview. It is off unless asked for.
  129| 
  130| ```sh
  131| $H -m simharness.run whatif --agent --text "..." --year 1920                 # held for approval (--publish ask)
  132| $H -m simharness.run whatif --agent --publish gate --text "..." --year 1920  # live if the bundle's checks pass
  133| $H -m simharness.run whatif --agent --dry-run --text "..." --year 1920       # no writes, interviews or publishing
  134| $H -m simharness.run trace                                                    # recent traces, and what is held
  135| $H -m simharness.run trace --id <trace>                                       # one trace: path, refusals, dollars
  136| $H -m simharness.run approve --id <trace>                                     # put a held bundle live
  137| $H -m simharness.run replay --id <trace> --model claude-sonnet-5-5            # recorded tool results, new model
  138| $H -m simharness.run agent-eval --year 1920 --limit 3                         # golden tasks, dry run (~$1-3 each)
  139| ```
  140| 
  141| Permissions are enforced in code, never by the prompt. Each tool has a tier (read,
  142| spend, write, publish), and the gate checks preconditions before it runs:
  143| - `register` needs a spec that passed `validate` unchanged since, plus evidence and,
  144|   for interviewed changes, a staged world.
  145| - `use_existing` attaches the reader's words only to the what-if the compiler matched.
  146| - `run_interviews` prices the uncached requests first, and refuses to run if the
  147|   typical cost exceeds what the text has left.
  148| - `publish` puts a bundle live only if it passes `bundle_checks` (the new what-if is
  149|   in it, no served result is missing, and the unchanged rerun is identical to the
  150|   served one) and the policy is `gate`. Otherwise the bundle is held in
  151|   `sessions/pending-publish/` for `approve`.
  152| 
  153| The reader's words and anything from the web reach the model only as data. Raw
  154| pages never do: research returns graded findings that cite returned sources.
  155| Every model turn and tool call (arguments, decision, full result, dollars, time)
  156| is written to `sessions/traces/<id>.jsonl`. Traces are kept as long as the session
  157| logs (`SIMULACRA_RETAIN_DAYS`). A replay re-serves a trace's recorded tool results
  158| to a new model or prompt and compares the paths.
  159| 
  160| The queue worker uses the agent when `SIMULACRA_AGENT=1`. `SIMULACRA_AGENT_PUBLISH`
  161| is `gate` by default; with `ask`, every new what-if waits for approval, and the
  162| waiting page is told it will go live once reviewed.
  163| 
  164| Untrusted text is fenced in every pass: the reader's words reach compile and research inside
  165| `<reader_text>`, and the search's notes and source titles reach extraction inside `<research_notes>`
  166| and `<sources>` (`scenario.fence` swaps angle brackets so the text can't close its fence). Each system
  167| prompt says fenced text is material, never instructions. A text that tries to instruct the compiler
  168| is answered as not modelable.
  169| 
  170| With `SIMULACRA_LOG=1`, the server (`pnpm serve`) logs requests to `sessions/`, queues unknown text,
  171| and reloads a changed bundle without a restart. `SIMULACRA_AUTORUN=configs/live-1920.json`
  172| also starts the queue worker as text arrives (`SIMULACRA_PYTHON` picks the interpreter;
  173| it runs from the repo root).
  174| 
  175| The `ask` stage depends on the backend:
  176| - **`anthropic` or `anthropic-batch`:** needs `pip install -e '.[llm]'`
  177|   (`anthropic>=1.0`; older SDKs lack `output_config`). The key comes from
  178|   `ANTHROPIC_API_KEY`, else `~/.config/simulacra/anthropic.env`
  179|   (`ANTHROPIC_API_KEY=…`, mode 600; `llm.api_key()`), and is never written to
  180|   the repo, a run folder or a log. The commands above use a venv outside the
  181|   repo, `~/.venvs/simharness`, with that extra installed.
  182| - **`transcript`:** writes `runs/<id>/agents/transcript/requests.jsonl` and
  183|   reads `responses.jsonl`, one `{"id", "model", "answer"}` per line. Any
  184|   runner can fill it.
  185| 
  186| ### Interview runs
  187| 
  188| Every stage takes `--config`; the default is `configs/prototype-1920.json`.
  189| Two small 1920 configs exist for cheap runs on the API:
  190| - `configs/quick-1920.json`: two cohorts, one agent each, all four arms, on
  191|   Haiku 4.5 (a few cents).
  192| - `configs/rung1-1920.json`: six cohorts × 2 agents, `league` only, control
  193|   and counterfactual arms (under a dime).
  194| 
  195| The `agents` block's knobs (`config.AgentConfig`) select what is sent: `arms`
  196| (any of `control`, `cf`, `swap`, `probe`), `only_cohorts`, `per_cohort`,
  197| `check_share` (0 skips the check-model subsample), `bulk_model`,
  198| `check_model`, `effort` and `max_tokens`. `plan` prints the request counts and
  199| the dollar estimate before anything is sent. Model constraints the backend
  200| handles: Haiku 4.5 rejects `output_config.effort` (it is stripped), and
  201| Sonnet 5.5 rejects non-default sampling parameters, so spread comes from
  202| persona diversity, not temperature.
  203| 
  204| A run's id hashes the config, the data and all of `simharness/*.py`
  205| (DISCLOSURES G1), so any code change starts a new run folder and a fresh
  206| `ask`; identical requests are still answered from the cache (G4).
  207| 
  208| **Changing what the interviews collect.** A new answer field touches, together:
  209| `prompts.SYSTEM` (what the field is), `prompts.answer_schema` (add it to
  210| `required`; keep `additionalProperties: false`), `prompts.QUESTIONS` only if
  211| the field needs asking (keep the paraphrases parallel), `paired.normalize`
  212| only if it feeds a count, and `publish._voters` to put it in the voter
  213| payload (plus the zod schemas in `serve/bundle.ts` and
  214| `src/lib/simulacra/schemas.ts` if the page is to read it). Bump `PROMPT_VERSION` in `prompts.py`; answers from two prompt
  215| versions are never mixed in one analysis.
  216| 
  217| Serve the bundles:
  218| 1. `pnpm build` (the static page, into `build/`), then `pnpm serve` (`serve/index.ts`, `PORT`, default 8787).
  219| 2. The router reads `serve/bundles/<year>.json`; set `SIMULACRA_BUNDLES` to serve another folder, such as `runs/<id>/published`.
  220| 
  221| ## Years
  222| 
  223| - **1920** is the original fit, identified by the 1916→1920 suffrage
  224|   experiment.
  225| - **1924** is carried forward from it (`backbone.carry_forward`; DISCLOSURES
  226|   C13–C16). It has its own `configs/live-1924.json`.
  227| - **All 60 elections, 1789–2024, are built.** Each other year has
  228|   `profiles/<year>.json` and `configs/live-<year>.json`. Years other than 1916–1924 use
  229|   `backbone.general_fit` (DISCLOSURES B10–B13). The unchanged rerun of every
  230|   year reproduces each state's certified returns and history's electoral votes.
  231| - `run dryrun --year Y [--all-cohorts] [--samples N]` runs backbone → verify →
  232|   plan for any year with no model calls, and prints sample briefs, counts and
  233|   the cost estimate (`runs/<id>/dryrun.json`).
  234| - `run verify` checks any year: exact reproduction, plus Corder–Wolbrecht
  235|   where it exists. `evaluate` stays 1920's check set.
  236| - **Adding a year:**
  237|   - a `profiles/<year>.json`;
  238|   - returns, voting rules and platforms in the cache;
  239|   - a `live-<year>.json` config.
  240| 
  241|   The queue sends typed what-ifs to their year's config.
```

## `infra/.gitignore`

```
    1| .terraform/
    2| *.tfstate
    3| *.tfstate.*
    4| *.tfplan
    5| terraform.tfvars
```

## `infra/.terraform.lock.hcl`

```
    1| # This file is maintained automatically by "terraform init".
    2| # Manual edits may be lost in future updates.
    3| 
    4| provider "registry.terraform.io/hashicorp/aws" {
    5|   version     = "6.67.0"
    6|   constraints = "~> 6.0"
    7|   hashes = [
    8|     "h1:OgdIUAQDtJBxlKjoPgChD1w57vl6hm6PyJHiBYgsgQA=",
    9|     "zh:111d5686a1f4ccbc888bb5e2229308bcdd9149898c6af97969fcdfb0e7bd2aa0",
   10|     "zh:21b3b7693bd9754c039fd546f03ed09e7510c6189aa5ee37176f144cf8dd5f95",
   11|     "zh:25e03c7f025ff4851889537605aa560d2e39bd738b33a5204b8037eb164b475f",
   12|     "zh:2817a046f1060e25bf04b0eb78f4e251130bb92dc82ec1264ce156dc9bf78e67",
   13|     "zh:2d318d674c3ec9dbd97ddb10b12ad4827be4f508c43ba2ae1e0523baa9e367e3",
   14|     "zh:2f07ab356718267299e10b6072472ded29d82753883027bf43bcd687ac72feb2",
   15|     "zh:32307e67f83bc0dc94d38cfcd23d782166a09e0e975e2a5aa7d7a3e7ca5d3da8",
   16|     "zh:4ce94853264097dd7f4542b3cfd18d2b98b06d23321db45d5e384ea275a57f63",
   17|     "zh:869656c41cc7c7412f213e488f98167cff61deafcb8cf245d25d056e8dfdc263",
   18|     "zh:8fd8c814e9d8edf152552047db23bf5b5d63f22e6b0b5d47b2af851376e99349",
   19|     "zh:9b12af85486a96aedd8d7984b0ff811a4b42e3d88dad1a3fb4c0b580d04fa425",
   20|     "zh:9cbc02ceef9bd469da497a1e7065ff984bdacfbe919ac3cce804a86c13b6e2c6",
   21|     "zh:9ea55dda2767acfc1f6337fc7d29b1d4d79d6f8f04871f8ad99a6078d2865994",
   22|     "zh:d7149df0819fb57a160489db45d33951765b8f0118daa3b4cd549a0135bc97a1",
   23|     "zh:e5819937bb7043d08c9829b32d52d9fb55a5b9a4d8d55d550d47a3d7392db546",
   24|     "zh:f93bc38dbc0ad53842303f30eec7a22c525c4d56209b54ec33a8d375cfc4e4fd",
   25|   ]
   26| }
```

## `infra/acm.tf`

```hcl
    1| # Certificates for api. (ALB) and assets. (CloudFront; must be us-east-1,
    2| # which this whole stack is). DNS is at Vercel, so validation is two-step:
    3| #   1. terraform apply -target=aws_acm_certificate.api -target=aws_acm_certificate.assets
    4| #   2. infra/vercel-dns.sh certs --apply   (CAA for amazon.com + the validation CNAMEs)
    5| #   3. terraform apply                     (the validation resources wait for ISSUED)
    6| # The zone's CAA records allow only pki.goog, sectigo.com and letsencrypt.org
    7| # today; without an amazon.com CAA record ACM never issues.
    8| 
    9| resource "aws_acm_certificate" "api" {
   10|   domain_name       = "api.${var.domain}"
   11|   validation_method = "DNS"
   12|   lifecycle { create_before_destroy = true }
   13| }
   14| 
   15| resource "aws_acm_certificate" "assets" {
   16|   domain_name       = "assets.${var.domain}"
   17|   validation_method = "DNS"
   18|   lifecycle { create_before_destroy = true }
   19| }
   20| 
   21| resource "aws_acm_certificate_validation" "api" {
   22|   certificate_arn         = aws_acm_certificate.api.arn
   23|   validation_record_fqdns = [for o in aws_acm_certificate.api.domain_validation_options : o.resource_record_name]
   24|   timeouts { create = "15m" }
   25| }
   26| 
   27| resource "aws_acm_certificate_validation" "assets" {
   28|   certificate_arn         = aws_acm_certificate.assets.arn
   29|   validation_record_fqdns = [for o in aws_acm_certificate.assets.domain_validation_options : o.resource_record_name]
   30|   timeouts { create = "15m" }
   31| }
```

## `infra/alb.tf`

```hcl
    1| resource "aws_lb" "api" {
    2|   name               = "${local.name}-api"
    3|   load_balancer_type = "application"
    4|   security_groups    = [aws_security_group.alb.id]
    5|   subnets            = var.subnet_ids
    6|   # Default 60s idle timeout: every route answers fast (runs are polled).
    7|   drop_invalid_header_fields = true
    8| }
    9| 
   10| resource "aws_lb_target_group" "api" {
   11|   name        = "${local.name}-api"
   12|   port        = 8080
   13|   protocol    = "HTTP"
   14|   target_type = "ip"
   15|   vpc_id      = local.vpc_id
   16|   # One task, stopped before its replacement starts: a long drain only
   17|   # lengthens the 503 window.
   18|   deregistration_delay = 10
   19|   health_check {
   20|     path                = "/healthz"
   21|     matcher             = "200"
   22|     interval            = 15
   23|     timeout             = 5
   24|     healthy_threshold   = 2
   25|     unhealthy_threshold = 3
   26|   }
   27| }
   28| 
   29| resource "aws_lb_listener" "http" {
   30|   load_balancer_arn = aws_lb.api.arn
   31|   port              = 80
   32|   protocol          = "HTTP"
   33|   default_action {
   34|     type = "redirect"
   35|     redirect {
   36|       protocol    = "HTTPS"
   37|       port        = "443"
   38|       status_code = "HTTP_301"
   39|     }
   40|   }
   41| }
   42| 
   43| resource "aws_lb_listener" "https" {
   44|   load_balancer_arn = aws_lb.api.arn
   45|   port              = 443
   46|   protocol          = "HTTPS"
   47|   ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
   48|   certificate_arn   = aws_acm_certificate_validation.api.certificate_arn
   49|   default_action {
   50|     type             = "forward"
   51|     target_group_arn = aws_lb_target_group.api.arn
   52|   }
   53| }
```

## `infra/backup.tf`

```hcl
    1| # Daily EFS backups, 35 days. Production state diverges from git the moment
    2| # the worker models anything, and 46 of the 60 bundles can't be regenerated.
    3| 
    4| resource "aws_backup_vault" "state" {
    5|   name = "${local.name}-state"
    6| }
    7| 
    8| resource "aws_backup_plan" "state" {
    9|   name = "${local.name}-state-daily"
   10|   rule {
   11|     rule_name         = "daily"
   12|     target_vault_name = aws_backup_vault.state.name
   13|     schedule          = "cron(0 7 * * ? *)"
   14|     lifecycle { delete_after = 35 }
   15|   }
   16| }
   17| 
   18| data "aws_iam_policy_document" "backup_assume" {
   19|   statement {
   20|     actions = ["sts:AssumeRole"]
   21|     principals {
   22|       type        = "Service"
   23|       identifiers = ["backup.amazonaws.com"]
   24|     }
   25|   }
   26| }
   27| 
   28| resource "aws_iam_role" "backup" {
   29|   name               = "${local.name}-backup"
   30|   assume_role_policy = data.aws_iam_policy_document.backup_assume.json
   31| }
   32| 
   33| resource "aws_iam_role_policy_attachment" "backup" {
   34|   role       = aws_iam_role.backup.name
   35|   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
   36| }
   37| 
   38| resource "aws_iam_role_policy_attachment" "restore" {
   39|   role       = aws_iam_role.backup.name
   40|   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
   41| }
   42| 
   43| resource "aws_backup_selection" "state" {
   44|   name         = "${local.name}-efs"
   45|   plan_id      = aws_backup_plan.state.id
   46|   iam_role_arn = aws_iam_role.backup.arn
   47|   resources    = [aws_efs_file_system.state.arn]
   48| }
```

## `infra/bootstrap.sh`

```bash
    1| #!/usr/bin/env bash
    2| # One-time: the Terraform state bucket. Re-runnable (every step is idempotent).
    3| # Run before the first `terraform init`.
    4| set -euo pipefail
    5| 
    6| B=simulacra-americana-tfstate
    7| test "$(aws sts get-caller-identity --query Account --output text)" = "${AWS_ACCOUNT_ID:?set AWS_ACCOUNT_ID to the target AWS account}"
    8| 
    9| if ! aws s3api head-bucket --bucket "$B" 2>/dev/null; then
   10|   aws s3api create-bucket --bucket "$B" --region us-east-1 --object-ownership BucketOwnerEnforced >/dev/null
   11| fi
   12| aws s3api put-public-access-block --bucket "$B" --public-access-block-configuration \
   13|   BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
   14| aws s3api put-bucket-encryption --bucket "$B" --server-side-encryption-configuration \
   15|   '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'
   16| aws s3api put-bucket-versioning --bucket "$B" --versioning-configuration Status=Enabled
   17| aws s3api put-bucket-tagging --bucket "$B" --tagging 'TagSet=[{Key=project,Value=simulacra-americana}]'
   18| echo "state bucket $B ready"
```

## `infra/cloudfront.tf`

```hcl
    1| # assets.simulacraamericana.com: CloudFront over the private assets bucket.
    2| # Only the robot assets and portraits; the site itself is served by Vercel.
    3| 
    4| resource "aws_cloudfront_origin_access_control" "assets" {
    5|   name                              = "${local.name}-assets"
    6|   origin_access_control_origin_type = "s3"
    7|   signing_behavior                  = "always"
    8|   signing_protocol                  = "sigv4"
    9| }
   10| 
   11| # Assets are versioned with ?v=, so the query string is part of the key.
   12| resource "aws_cloudfront_cache_policy" "assets" {
   13|   name        = "${local.name}-assets"
   14|   min_ttl     = 0
   15|   default_ttl = 86400
   16|   max_ttl     = 31536000
   17|   parameters_in_cache_key_and_forwarded_to_origin {
   18|     enable_accept_encoding_brotli = true
   19|     enable_accept_encoding_gzip   = true
   20|     cookies_config { cookie_behavior = "none" }
   21|     headers_config { header_behavior = "none" }
   22|     query_strings_config { query_string_behavior = "all" }
   23|   }
   24| }
   25| 
   26| resource "aws_cloudfront_response_headers_policy" "assets" {
   27|   name = "${local.name}-assets-cors"
   28|   cors_config {
   29|     access_control_allow_credentials = false
   30|     access_control_allow_headers { items = ["*"] }
   31|     access_control_allow_methods { items = ["GET", "HEAD"] }
   32|     access_control_allow_origins { items = var.cors_origins }
   33|     access_control_max_age_sec = 86400
   34|     origin_override            = true
   35|   }
   36| }
   37| 
   38| resource "aws_cloudfront_distribution" "assets" {
   39|   enabled         = true
   40|   is_ipv6_enabled = true
   41|   comment         = "Simulacra Americana robot assets and portraits"
   42|   aliases         = ["assets.${var.domain}"]
   43|   price_class     = "PriceClass_100"
   44|   http_version    = "http2and3"
   45| 
   46|   origin {
   47|     origin_id                = "assets-s3"
   48|     domain_name              = aws_s3_bucket.assets.bucket_regional_domain_name
   49|     origin_access_control_id = aws_cloudfront_origin_access_control.assets.id
   50|   }
   51| 
   52|   default_cache_behavior {
   53|     target_origin_id           = "assets-s3"
   54|     viewer_protocol_policy     = "redirect-to-https"
   55|     allowed_methods            = ["GET", "HEAD", "OPTIONS"]
   56|     cached_methods             = ["GET", "HEAD", "OPTIONS"]
   57|     compress                   = true
   58|     cache_policy_id            = aws_cloudfront_cache_policy.assets.id
   59|     response_headers_policy_id = aws_cloudfront_response_headers_policy.assets.id
   60|   }
   61| 
   62|   restrictions {
   63|     geo_restriction { restriction_type = "none" }
   64|   }
   65| 
   66|   viewer_certificate {
   67|     acm_certificate_arn      = aws_acm_certificate_validation.assets.certificate_arn
   68|     ssl_support_method       = "sni-only"
   69|     minimum_protocol_version = "TLSv1.2_2021"
   70|   }
   71| }
```

## `infra/ecs.tf`

```hcl
    1| # One cluster, one service, ONE task, on purpose: run state is an in-process
    2| # Map, the worker lock is a PID file (PIDs aren't unique across containers),
    3| # and two tasks would run two workers against the same EFS queue. So
    4| # desiredCount 1 and the old task stops before the new one starts
    5| # (minimumHealthyPercent 0 / maximumPercent 100): a few seconds of 503 per
    6| # deploy. The circuit breaker rolls back a revision that never gets healthy.
    7| #
    8| # The task definition is rendered from infra/taskdef.json.tftpl, here for the
    9| # first revision and by deploy-api.yml for every later one, so env and secrets
   10| # can't silently drop on a deploy. The service ignores task-definition drift.
   11| 
   12| resource "aws_ecr_repository" "api" {
   13|   name = "simulacra-api"
   14|   # SHA tags are immutable; the one moving tag is the registry layer cache
   15|   # deploy-api.yml writes on every build.
   16|   image_tag_mutability = "IMMUTABLE_WITH_EXCLUSION"
   17|   image_tag_mutability_exclusion_filter {
   18|     filter      = "buildcache"
   19|     filter_type = "WILDCARD"
   20|   }
   21|   image_scanning_configuration { scan_on_push = true }
   22| }
   23| 
   24| resource "aws_ecr_lifecycle_policy" "api" {
   25|   repository = aws_ecr_repository.api.name
   26|   policy = jsonencode({
   27|     rules = [{
   28|       rulePriority = 1
   29|       description  = "Keep the last 30 images (rollback depth)"
   30|       selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 30 }
   31|       action       = { type = "expire" }
   32|     }]
   33|   })
   34| }
   35| 
   36| resource "aws_ecs_cluster" "main" {
   37|   name = local.name
   38|   setting {
   39|     name  = "containerInsights"
   40|     value = "disabled"
   41|   }
   42| }
   43| 
   44| locals {
   45|   taskdef_vars = {
   46|     image              = var.image
   47|     cpu                = var.task_cpu
   48|     memory             = var.task_memory
   49|     execution_role_arn = aws_iam_role.execution.arn
   50|     task_role_arn      = aws_iam_role.task.arn
   51|     efs_id             = aws_efs_file_system.state.id
   52|     access_point_id    = aws_efs_access_point.state.id
   53|     secret_arn         = aws_secretsmanager_secret.prod.arn
   54|     log_group          = aws_cloudwatch_log_group.api.name
   55|     region             = local.region
   56|   }
   57|   taskdef = jsondecode(templatefile("${path.module}/taskdef.json.tftpl", local.taskdef_vars))
   58| }
   59| 
   60| resource "aws_ecs_task_definition" "api" {
   61|   family                   = local.taskdef.family
   62|   network_mode             = local.taskdef.networkMode
   63|   requires_compatibilities = local.taskdef.requiresCompatibilities
   64|   cpu                      = local.taskdef.cpu
   65|   memory                   = local.taskdef.memory
   66|   execution_role_arn       = local.taskdef.executionRoleArn
   67|   task_role_arn            = local.taskdef.taskRoleArn
   68|   container_definitions    = jsonencode(local.taskdef.containerDefinitions)
   69|   runtime_platform {
   70|     cpu_architecture        = "ARM64"
   71|     operating_system_family = "LINUX"
   72|   }
   73|   volume {
   74|     name = "state"
   75|     efs_volume_configuration {
   76|       file_system_id     = aws_efs_file_system.state.id
   77|       transit_encryption = "ENABLED"
   78|       authorization_config {
   79|         access_point_id = aws_efs_access_point.state.id
   80|         iam             = "ENABLED"
   81|       }
   82|     }
   83|   }
   84|   # Only the first revision comes from here (var.image at stand-up); CI
   85|   # registers every later one from the same template.
   86|   lifecycle { ignore_changes = [container_definitions] }
   87| }
   88| 
   89| resource "aws_ecs_service" "api" {
   90|   name                               = "simulacra-api"
   91|   cluster                            = aws_ecs_cluster.main.id
   92|   task_definition                    = aws_ecs_task_definition.api.arn
   93|   desired_count                      = 1
   94|   launch_type                        = "FARGATE"
   95|   platform_version                   = "LATEST"
   96|   deployment_minimum_healthy_percent = 0
   97|   deployment_maximum_percent         = 100
   98|   health_check_grace_period_seconds  = 60
   99|   enable_execute_command             = false
  100| 
  101|   deployment_circuit_breaker {
  102|     enable   = true
  103|     rollback = true
  104|   }
  105| 
  106|   network_configuration {
  107|     subnets          = var.subnet_ids
  108|     security_groups  = [aws_security_group.task.id]
  109|     assign_public_ip = true
  110|   }
  111| 
  112|   load_balancer {
  113|     target_group_arn = aws_lb_target_group.api.arn
  114|     container_name   = "api"
  115|     container_port   = 8080
  116|   }
  117| 
  118|   lifecycle { ignore_changes = [task_definition] }
  119|   depends_on = [aws_lb_listener.https, aws_efs_mount_target.state]
  120| }
  121| 
  122| # A one-off task (scripts/sync-data.sh) that copies from the private data
  123| # bucket onto EFS: `seed` once, `cache` whenever the census data changes.
  124| resource "aws_ecs_task_definition" "seed" {
  125|   family                   = "simulacra-seed"
  126|   network_mode             = "awsvpc"
  127|   requires_compatibilities = ["FARGATE"]
  128|   cpu                      = 256
  129|   memory                   = 512
  130|   execution_role_arn       = aws_iam_role.execution.arn
  131|   task_role_arn            = aws_iam_role.task.arn
  132|   runtime_platform {
  133|     cpu_architecture        = "ARM64"
  134|     operating_system_family = "LINUX"
  135|   }
  136|   volume {
  137|     name = "state"
  138|     efs_volume_configuration {
  139|       file_system_id     = aws_efs_file_system.state.id
  140|       transit_encryption = "ENABLED"
  141|       authorization_config {
  142|         access_point_id = aws_efs_access_point.state.id
  143|         iam             = "ENABLED"
  144|       }
  145|     }
  146|   }
  147|   container_definitions = jsonencode([{
  148|     name       = "seed"
  149|     image      = "public.ecr.aws/aws-cli/aws-cli:latest"
  150|     essential  = true
  151|     entryPoint = ["sh", "-c"]
  152|     # MODE=seed copies only into an unseeded volume (marker file), so it can
  153|     # never overwrite what production has written. MODE=cache replaces the
  154|     # census-derived cache wholesale (read-only data).
  155|     command = [<<-EOT
  156|       set -eu
  157|       case "$MODE" in
  158|         seed)
  159|           if [ -e /state/.seeded ]; then echo "already seeded; refusing"; exit 0; fi
  160|           aws s3 sync "s3://${aws_s3_bucket.data.bucket}/seed/" /state/ --only-show-errors
  161|           aws s3 sync "s3://${aws_s3_bucket.data.bucket}/cache/" /state/cache/ --only-show-errors
  162|           date -u +%FT%TZ > /state/.seeded ;;
  163|         cache)
  164|           aws s3 sync "s3://${aws_s3_bucket.data.bucket}/cache/" /state/cache/ --delete --only-show-errors ;;
  165|         *) echo "MODE must be seed or cache"; exit 2 ;;
  166|       esac
  167|       find /state -maxdepth 1 | sort
  168|     EOT
  169|     ]
  170|     environment = [{ name = "MODE", value = "seed" }]
  171|     mountPoints = [{ sourceVolume = "state", containerPath = "/state" }]
  172|     logConfiguration = {
  173|       logDriver = "awslogs"
  174|       options = {
  175|         "awslogs-group"         = aws_cloudwatch_log_group.api.name
  176|         "awslogs-region"        = local.region
  177|         "awslogs-stream-prefix" = "seed"
  178|       }
  179|     }
  180|   }])
  181| }
```

## `infra/efs.tf`

```hcl
    1| # The service's state: serve/bundles, sessions, runs, whatifs, configs and
    2| # the census-derived cache, all under one access point owned by the image's
    3| # `app` user (uid 1000). The image symlinks the code-relative folders here.
    4| 
    5| resource "aws_efs_file_system" "state" {
    6|   creation_token   = "${local.name}-state"
    7|   encrypted        = true
    8|   performance_mode = "generalPurpose"
    9|   throughput_mode  = "elastic"
   10|   lifecycle_policy {
   11|     transition_to_ia = "AFTER_30_DAYS"
   12|   }
   13|   tags = { Name = "${local.name}-state" }
   14| }
   15| 
   16| resource "aws_efs_mount_target" "state" {
   17|   for_each        = toset(var.subnet_ids)
   18|   file_system_id  = aws_efs_file_system.state.id
   19|   subnet_id       = each.value
   20|   security_groups = [aws_security_group.efs.id]
   21| }
   22| 
   23| resource "aws_efs_access_point" "state" {
   24|   file_system_id = aws_efs_file_system.state.id
   25|   posix_user {
   26|     uid = 1000
   27|     gid = 1000
   28|   }
   29|   root_directory {
   30|     path = "/simulacra"
   31|     creation_info {
   32|       owner_uid   = 1000
   33|       owner_gid   = 1000
   34|       permissions = "0755"
   35|     }
   36|   }
   37|   tags = { Name = "${local.name}-state" }
   38| }
   39| 
   40| # Only through the access point, only over TLS, only by the task role.
   41| resource "aws_efs_file_system_policy" "state" {
   42|   file_system_id = aws_efs_file_system.state.id
   43|   policy = jsonencode({
   44|     Version = "2012-10-17"
   45|     Statement = [
   46|       {
   47|         Sid       = "TaskRoleViaAccessPoint"
   48|         Effect    = "Allow"
   49|         Principal = { AWS = aws_iam_role.task.arn }
   50|         Action    = ["elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite"]
   51|         Resource  = aws_efs_file_system.state.arn
   52|         Condition = {
   53|           StringEquals = { "elasticfilesystem:AccessPointArn" = aws_efs_access_point.state.arn }
   54|           Bool         = { "aws:SecureTransport" = "true" }
   55|         }
   56|       }
   57|     ]
   58|   })
   59| }
```

## `infra/iam.tf`

```hcl
    1| # Three roles, no static keys anywhere.
    2| #   execution: ECS pulls the image, writes logs, reads the one secret.
    3| #   task:      the running container: EFS client, read of the data bucket (seed/sync).
    4| #   deploy:    GitHub Actions via OIDC: push to this ECR repo, register task
    5| #              defs, roll this one service, read this log group.
    6| 
    7| data "aws_iam_policy_document" "ecs_tasks_assume" {
    8|   statement {
    9|     actions = ["sts:AssumeRole"]
   10|     principals {
   11|       type        = "Service"
   12|       identifiers = ["ecs-tasks.amazonaws.com"]
   13|     }
   14|     condition {
   15|       test     = "StringEquals"
   16|       variable = "aws:SourceAccount"
   17|       values   = [local.account_id]
   18|     }
   19|   }
   20| }
   21| 
   22| resource "aws_iam_role" "execution" {
   23|   name               = "${local.name}-execution"
   24|   assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
   25| }
   26| 
   27| resource "aws_iam_role_policy_attachment" "execution_managed" {
   28|   role       = aws_iam_role.execution.name
   29|   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
   30| }
   31| 
   32| resource "aws_iam_role_policy" "execution_secret" {
   33|   name = "read-prod-secret"
   34|   role = aws_iam_role.execution.id
   35|   policy = jsonencode({
   36|     Version = "2012-10-17"
   37|     Statement = [{
   38|       Effect   = "Allow"
   39|       Action   = ["secretsmanager:GetSecretValue"]
   40|       Resource = aws_secretsmanager_secret.prod.arn
   41|     }]
   42|   })
   43| }
   44| 
   45| resource "aws_iam_role" "task" {
   46|   name               = "${local.name}-task"
   47|   assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
   48| }
   49| 
   50| resource "aws_iam_role_policy" "task" {
   51|   name = "efs-and-data-read"
   52|   role = aws_iam_role.task.id
   53|   policy = jsonencode({
   54|     Version = "2012-10-17"
   55|     Statement = [
   56|       {
   57|         Sid      = "EfsClient"
   58|         Effect   = "Allow"
   59|         Action   = ["elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite"]
   60|         Resource = aws_efs_file_system.state.arn
   61|         Condition = {
   62|           StringEquals = { "elasticfilesystem:AccessPointArn" = aws_efs_access_point.state.arn }
   63|         }
   64|       },
   65|       {
   66|         Sid      = "DataBucketRead"
   67|         Effect   = "Allow"
   68|         Action   = ["s3:GetObject", "s3:ListBucket"]
   69|         Resource = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
   70|       }
   71|     ]
   72|   })
   73| }
   74| 
   75| # The account's GitHub OIDC provider already exists (the auth server's deploy
   76| # uses it). Read it; never manage it from this stack.
   77| data "aws_iam_openid_connect_provider" "github" {
   78|   url = "https://token.actions.githubusercontent.com"
   79| }
   80| 
   81| resource "aws_iam_role" "deploy" {
   82|   name = "${local.name}-gha-deploy"
   83|   assume_role_policy = jsonencode({
   84|     Version = "2012-10-17"
   85|     Statement = [{
   86|       Effect    = "Allow"
   87|       Principal = { Federated = data.aws_iam_openid_connect_provider.github.arn }
   88|       Action    = "sts:AssumeRoleWithWebIdentity"
   89|       # Exact match, no wildcard: one repo, one branch (var.github_oidc_sub).
   90|       Condition = {
   91|         StringEquals = {
   92|           "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
   93|           "token.actions.githubusercontent.com:sub" = var.github_oidc_sub
   94|         }
   95|       }
   96|     }]
   97|   })
   98| }
   99| 
  100| resource "aws_iam_role_policy" "deploy" {
  101|   name = "deploy-api"
  102|   role = aws_iam_role.deploy.id
  103|   policy = jsonencode({
  104|     Version = "2012-10-17"
  105|     Statement = [
  106|       { Sid = "EcrAuth", Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
  107|       {
  108|         Sid    = "EcrRepo"
  109|         Effect = "Allow"
  110|         Action = ["ecr:BatchCheckLayerAvailability", "ecr:CompleteLayerUpload", "ecr:InitiateLayerUpload",
  111|           "ecr:PutImage", "ecr:UploadLayerPart", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer",
  112|         "ecr:DescribeImages", "ecr:ListImages"]
  113|         Resource = aws_ecr_repository.api.arn
  114|       },
  115|       # RegisterTaskDefinition and Describe* don't support resource scoping.
  116|       {
  117|         Sid      = "EcsRegister"
  118|         Effect   = "Allow"
  119|         Action   = ["ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition", "ecs:DescribeServices", "ecs:DescribeTasks", "ecs:ListTasks"]
  120|         Resource = "*"
  121|       },
  122|       # The service's ARN is built, not referenced, so this role can exist
  123|       # (and push the first image) before the service does.
  124|       {
  125|         Sid      = "EcsRoll"
  126|         Effect   = "Allow"
  127|         Action   = ["ecs:UpdateService"]
  128|         Resource = "arn:aws:ecs:${local.region}:${local.account_id}:service/${aws_ecs_cluster.main.name}/simulacra-api"
  129|       },
  130|       {
  131|         Sid       = "PassTaskRoles"
  132|         Effect    = "Allow"
  133|         Action    = "iam:PassRole"
  134|         Resource  = [aws_iam_role.execution.arn, aws_iam_role.task.arn]
  135|         Condition = { StringEquals = { "iam:PassedToService" = "ecs-tasks.amazonaws.com" } }
  136|       },
  137|       {
  138|         Sid      = "ReadDeployLogs"
  139|         Effect   = "Allow"
  140|         Action   = ["logs:FilterLogEvents", "logs:DescribeLogStreams"]
  141|         Resource = "${aws_cloudwatch_log_group.api.arn}:*"
  142|       }
  143|     ]
  144|   })
  145| }
```

## `infra/network.tf`

```hcl
    1| # The auth server's network pattern: default-VPC public subnets, tasks with a
    2| # public IP, no NAT gateway (~$32/mo saved). Only the ALB is reachable from
    3| # the internet; the task accepts its port from the ALB alone, EFS accepts NFS
    4| # from the tasks alone.
    5| 
    6| data "aws_subnet" "selected" {
    7|   for_each = toset(var.subnet_ids)
    8|   id       = each.value
    9| }
   10| 
   11| locals {
   12|   vpc_id = one(distinct([for s in data.aws_subnet.selected : s.vpc_id]))
   13| }
   14| 
   15| resource "aws_security_group" "alb" {
   16|   name        = "${local.name}-alb"
   17|   description = "Simulacra API load balancer: HTTP/HTTPS from anywhere"
   18|   vpc_id      = local.vpc_id
   19| }
   20| 
   21| resource "aws_vpc_security_group_ingress_rule" "alb_https" {
   22|   security_group_id = aws_security_group.alb.id
   23|   cidr_ipv4         = "0.0.0.0/0"
   24|   ip_protocol       = "tcp"
   25|   from_port         = 443
   26|   to_port           = 443
   27| }
   28| 
   29| resource "aws_vpc_security_group_ingress_rule" "alb_http" {
   30|   security_group_id = aws_security_group.alb.id
   31|   cidr_ipv4         = "0.0.0.0/0"
   32|   ip_protocol       = "tcp"
   33|   from_port         = 80
   34|   to_port           = 80
   35| }
   36| 
   37| resource "aws_vpc_security_group_egress_rule" "alb_to_task" {
   38|   security_group_id            = aws_security_group.alb.id
   39|   referenced_security_group_id = aws_security_group.task.id
   40|   ip_protocol                  = "tcp"
   41|   from_port                    = 8080
   42|   to_port                      = 8080
   43| }
   44| 
   45| resource "aws_security_group" "task" {
   46|   name        = "${local.name}-task"
   47|   description = "Simulacra API task: app port from the ALB only"
   48|   vpc_id      = local.vpc_id
   49| }
   50| 
   51| resource "aws_vpc_security_group_ingress_rule" "task_from_alb" {
   52|   security_group_id            = aws_security_group.task.id
   53|   referenced_security_group_id = aws_security_group.alb.id
   54|   ip_protocol                  = "tcp"
   55|   from_port                    = 8080
   56|   to_port                      = 8080
   57| }
   58| 
   59| # Out to Anthropic, ECR, Secrets Manager, S3, logs (no NAT: via the public IP).
   60| resource "aws_vpc_security_group_egress_rule" "task_all" {
   61|   security_group_id = aws_security_group.task.id
   62|   cidr_ipv4         = "0.0.0.0/0"
   63|   ip_protocol       = "-1"
   64| }
   65| 
   66| resource "aws_security_group" "efs" {
   67|   name        = "${local.name}-efs"
   68|   description = "Simulacra state: NFS from the API and seed tasks only"
   69|   vpc_id      = local.vpc_id
   70| }
   71| 
   72| resource "aws_vpc_security_group_ingress_rule" "efs_from_task" {
   73|   security_group_id            = aws_security_group.efs.id
   74|   referenced_security_group_id = aws_security_group.task.id
   75|   ip_protocol                  = "tcp"
   76|   from_port                    = 2049
   77|   to_port                      = 2049
   78| }
```

## `infra/observability.tf`

```hcl
    1| resource "aws_cloudwatch_log_group" "api" {
    2|   name              = "/ecs/simulacra"
    3|   retention_in_days = 30
    4| }
    5| 
    6| # A real subscriber this time (the auth server's topic had none). SNS emails a
    7| # confirmation link; alarms go nowhere until it's clicked.
    8| resource "aws_sns_topic" "alarms" {
    9|   name = "${local.name}-alarms"
   10| }
   11| 
   12| resource "aws_sns_topic_subscription" "email" {
   13|   topic_arn = aws_sns_topic.alarms.arn
   14|   protocol  = "email"
   15|   endpoint  = var.alert_email
   16| }
   17| 
   18| locals {
   19|   alb_dims = { LoadBalancer = aws_lb.api.arn_suffix, TargetGroup = aws_lb_target_group.api.arn_suffix }
   20| }
   21| 
   22| resource "aws_cloudwatch_metric_alarm" "no_healthy_target" {
   23|   alarm_name          = "${local.name}-no-healthy-target"
   24|   alarm_description   = "The API has had no healthy task for 3 minutes."
   25|   namespace           = "AWS/ApplicationELB"
   26|   metric_name         = "HealthyHostCount"
   27|   dimensions          = local.alb_dims
   28|   statistic           = "Minimum"
   29|   period              = 60
   30|   evaluation_periods  = 3
   31|   comparison_operator = "LessThanThreshold"
   32|   threshold           = 1
   33|   treat_missing_data  = "breaching"
   34|   alarm_actions       = [aws_sns_topic.alarms.arn]
   35|   ok_actions          = [aws_sns_topic.alarms.arn]
   36| }
   37| 
   38| resource "aws_cloudwatch_metric_alarm" "target_5xx" {
   39|   alarm_name          = "${local.name}-target-5xx"
   40|   alarm_description   = "The API returned 5xx responses (more than 5 in 5 minutes)."
   41|   namespace           = "AWS/ApplicationELB"
   42|   metric_name         = "HTTPCode_Target_5XX_Count"
   43|   dimensions          = { LoadBalancer = aws_lb.api.arn_suffix }
   44|   statistic           = "Sum"
   45|   period              = 300
   46|   evaluation_periods  = 1
   47|   comparison_operator = "GreaterThanThreshold"
   48|   threshold           = 5
   49|   treat_missing_data  = "notBreaching"
   50|   alarm_actions       = [aws_sns_topic.alarms.arn]
   51| }
   52| 
   53| resource "aws_cloudwatch_metric_alarm" "elb_5xx" {
   54|   alarm_name          = "${local.name}-elb-5xx"
   55|   alarm_description   = "The load balancer itself returned 5xx (no target, or target timeouts)."
   56|   namespace           = "AWS/ApplicationELB"
   57|   metric_name         = "HTTPCode_ELB_5XX_Count"
   58|   dimensions          = { LoadBalancer = aws_lb.api.arn_suffix }
   59|   statistic           = "Sum"
   60|   period              = 300
   61|   evaluation_periods  = 1
   62|   comparison_operator = "GreaterThanThreshold"
   63|   threshold           = 10
   64|   treat_missing_data  = "notBreaching"
   65|   alarm_actions       = [aws_sns_topic.alarms.arn]
   66| }
   67| 
   68| # The worker's log (sessions/intake.log) is echoed to stdout with a
   69| # "[worker]" prefix by docker/entrypoint.sh.
   70| resource "aws_cloudwatch_log_metric_filter" "worker_failure" {
   71|   name           = "${local.name}-worker-failure"
   72|   log_group_name = aws_cloudwatch_log_group.api.name
   73|   pattern        = "?\"[worker] STOP:\" ?\"[worker] Traceback\" ?refusing ?\"worker failed to start\""
   74|   metric_transformation {
   75|     name          = "WorkerFailures"
   76|     namespace     = "Simulacra"
   77|     value         = "1"
   78|     default_value = "0"
   79|   }
   80| }
   81| 
   82| resource "aws_cloudwatch_metric_alarm" "worker_failure" {
   83|   alarm_name          = "${local.name}-worker-failure"
   84|   alarm_description   = "The what-if worker stopped, refused, or raised. Read /ecs/simulacra for [worker] lines."
   85|   namespace           = "Simulacra"
   86|   metric_name         = "WorkerFailures"
   87|   statistic           = "Sum"
   88|   period              = 300
   89|   evaluation_periods  = 1
   90|   comparison_operator = "GreaterThanOrEqualToThreshold"
   91|   threshold           = 1
   92|   treat_missing_data  = "notBreaching"
   93|   alarm_actions       = [aws_sns_topic.alarms.arn]
   94| }
   95| 
   96| # Budgets filter on the project tag, which must be an active cost-allocation tag.
   97| resource "aws_ce_cost_allocation_tag" "project" {
   98|   tag_key = "project"
   99|   status  = "Active"
  100| }
  101| 
  102| resource "aws_budgets_budget" "stack" {
  103|   name         = "${local.name}-monthly"
  104|   budget_type  = "COST"
  105|   limit_amount = tostring(var.monthly_budget_usd)
  106|   limit_unit   = "USD"
  107|   time_unit    = "MONTHLY"
  108|   cost_filter {
  109|     name   = "TagKeyValue"
  110|     values = ["user:project$simulacra-americana"]
  111|   }
  112|   notification {
  113|     comparison_operator       = "GREATER_THAN"
  114|     threshold                 = 80
  115|     threshold_type            = "PERCENTAGE"
  116|     notification_type         = "FORECASTED"
  117|     subscriber_sns_topic_arns = [aws_sns_topic.alarms.arn]
  118|   }
  119|   notification {
  120|     comparison_operator       = "GREATER_THAN"
  121|     threshold                 = 100
  122|     threshold_type            = "PERCENTAGE"
  123|     notification_type         = "ACTUAL"
  124|     subscriber_sns_topic_arns = [aws_sns_topic.alarms.arn]
  125|   }
  126| }
  127| 
  128| # Budgets publishes to the topic only if the topic lets it.
  129| resource "aws_sns_topic_policy" "alarms" {
  130|   arn = aws_sns_topic.alarms.arn
  131|   policy = jsonencode({
  132|     Version = "2012-10-17"
  133|     Statement = [
  134|       {
  135|         Sid       = "AccountOwner"
  136|         Effect    = "Allow"
  137|         Principal = { AWS = "arn:aws:iam::${local.account_id}:root" }
  138|         Action    = ["SNS:Publish", "SNS:Subscribe", "SNS:GetTopicAttributes", "SNS:SetTopicAttributes", "SNS:ListSubscriptionsByTopic"]
  139|         Resource  = aws_sns_topic.alarms.arn
  140|       },
  141|       {
  142|         Sid       = "CloudWatchAlarms"
  143|         Effect    = "Allow"
  144|         Principal = { Service = "cloudwatch.amazonaws.com" }
  145|         Action    = "SNS:Publish"
  146|         Resource  = aws_sns_topic.alarms.arn
  147|       },
  148|       {
  149|         Sid       = "Budgets"
  150|         Effect    = "Allow"
  151|         Principal = { Service = "budgets.amazonaws.com" }
  152|         Action    = "SNS:Publish"
  153|         Resource  = aws_sns_topic.alarms.arn
  154|       }
  155|     ]
  156|   })
  157| }
```

## `infra/outputs.tf`

```hcl
    1| # infra/vercel-dns.sh reads these (terraform output -json); deploy-api.yml's
    2| # repo variables are set from them (docs/DEPLOY.md, "CI setup").
    3| 
    4| output "acm_validation_records" {
    5|   description = "CNAMEs to add in Vercel DNS before the certificates can issue."
    6|   value = {
    7|     for o in concat(tolist(aws_acm_certificate.api.domain_validation_options), tolist(aws_acm_certificate.assets.domain_validation_options)) :
    8|     o.domain_name => { name = o.resource_record_name, type = o.resource_record_type, value = o.resource_record_value }
    9|   }
   10| }
   11| 
   12| output "api_alb_dns_name" {
   13|   description = "Target of the api. CNAME."
   14|   value       = aws_lb.api.dns_name
   15| }
   16| 
   17| output "assets_cloudfront_domain" {
   18|   description = "Target of the assets. CNAME."
   19|   value       = aws_cloudfront_distribution.assets.domain_name
   20| }
   21| 
   22| output "assets_distribution_id" {
   23|   value = aws_cloudfront_distribution.assets.id
   24| }
   25| 
   26| output "deploy_role_arn" {
   27|   description = "Repo variable AWS_DEPLOY_ROLE_ARN."
   28|   value       = aws_iam_role.deploy.arn
   29| }
   30| 
   31| output "ecr_repository_url" {
   32|   value = aws_ecr_repository.api.repository_url
   33| }
   34| 
   35| # Everything deploy-api.yml needs to render infra/taskdef.json.tftpl
   36| # (repo variable TASKDEF_VARS, as JSON). Image is filled in per deploy.
   37| output "taskdef_vars" {
   38|   value = { for k, v in local.taskdef_vars : k => v if k != "image" }
   39| }
   40| 
   41| output "seed_task" {
   42|   description = "For scripts/sync-data.sh: aws ecs run-task parameters."
   43|   value = {
   44|     cluster         = aws_ecs_cluster.main.name
   45|     task_definition = aws_ecs_task_definition.seed.family
   46|     subnets         = var.subnet_ids
   47|     security_group  = aws_security_group.task.id
   48|   }
   49| }
```

## `infra/s3.tf`

```hcl
    1| # Two private buckets.
    2| #
    3| # simulacra-americana-data: the census-derived cache (NHGIS/IPUMS extracts are
    4| # "not for redistribution"), the EFS seed, and data backups. Created by hand to
    5| # take the pre-migration backups before anything else; adopted
    6| # here by the import block below.
    7| #
    8| # simulacra-americana-assets: the robot model, its paint set and the mirrored
    9| # portraits. Readable only by the CloudFront distribution (OAC).
   10| 
   11| import {
   12|   to = aws_s3_bucket.data
   13|   id = "simulacra-americana-data"
   14| }
   15| 
   16| resource "aws_s3_bucket" "data" {
   17|   bucket = "simulacra-americana-data"
   18|   tags   = { data = "census-derived-private" }
   19| }
   20| 
   21| resource "aws_s3_bucket_ownership_controls" "data" {
   22|   bucket = aws_s3_bucket.data.id
   23|   rule { object_ownership = "BucketOwnerEnforced" }
   24| }
   25| 
   26| resource "aws_s3_bucket_public_access_block" "data" {
   27|   bucket                  = aws_s3_bucket.data.id
   28|   block_public_acls       = true
   29|   block_public_policy     = true
   30|   ignore_public_acls      = true
   31|   restrict_public_buckets = true
   32| }
   33| 
   34| resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
   35|   bucket = aws_s3_bucket.data.id
   36|   rule {
   37|     apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
   38|     bucket_key_enabled = true
   39|   }
   40| }
   41| 
   42| resource "aws_s3_bucket_versioning" "data" {
   43|   bucket = aws_s3_bucket.data.id
   44|   versioning_configuration { status = "Enabled" }
   45| }
   46| 
   47| # Only the task role (seed/sync) and this account's admins; never public, never
   48| # over plain HTTP.
   49| resource "aws_s3_bucket_policy" "data" {
   50|   bucket = aws_s3_bucket.data.id
   51|   policy = jsonencode({
   52|     Version = "2012-10-17"
   53|     Statement = [{
   54|       Sid       = "DenyInsecureTransport"
   55|       Effect    = "Deny"
   56|       Principal = "*"
   57|       Action    = "s3:*"
   58|       Resource  = [aws_s3_bucket.data.arn, "${aws_s3_bucket.data.arn}/*"]
   59|       Condition = { Bool = { "aws:SecureTransport" = "false" } }
   60|     }]
   61|   })
   62|   depends_on = [aws_s3_bucket_public_access_block.data]
   63| }
   64| 
   65| resource "aws_s3_bucket" "assets" {
   66|   bucket = "simulacra-americana-assets"
   67| }
   68| 
   69| resource "aws_s3_bucket_ownership_controls" "assets" {
   70|   bucket = aws_s3_bucket.assets.id
   71|   rule { object_ownership = "BucketOwnerEnforced" }
   72| }
   73| 
   74| resource "aws_s3_bucket_public_access_block" "assets" {
   75|   bucket                  = aws_s3_bucket.assets.id
   76|   block_public_acls       = true
   77|   block_public_policy     = true
   78|   ignore_public_acls      = true
   79|   restrict_public_buckets = true
   80| }
   81| 
   82| resource "aws_s3_bucket_server_side_encryption_configuration" "assets" {
   83|   bucket = aws_s3_bucket.assets.id
   84|   rule {
   85|     apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
   86|   }
   87| }
   88| 
   89| resource "aws_s3_bucket_versioning" "assets" {
   90|   bucket = aws_s3_bucket.assets.id
   91|   versioning_configuration { status = "Enabled" }
   92| }
   93| 
   94| resource "aws_s3_bucket_policy" "assets" {
   95|   bucket = aws_s3_bucket.assets.id
   96|   policy = jsonencode({
   97|     Version = "2012-10-17"
   98|     Statement = [
   99|       {
  100|         Sid       = "CloudFrontOAC"
  101|         Effect    = "Allow"
  102|         Principal = { Service = "cloudfront.amazonaws.com" }
  103|         Action    = "s3:GetObject"
  104|         Resource  = "${aws_s3_bucket.assets.arn}/*"
  105|         Condition = { StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.assets.arn } }
  106|       },
  107|       {
  108|         Sid       = "DenyInsecureTransport"
  109|         Effect    = "Deny"
  110|         Principal = "*"
  111|         Action    = "s3:*"
  112|         Resource  = [aws_s3_bucket.assets.arn, "${aws_s3_bucket.assets.arn}/*"]
  113|         Condition = { Bool = { "aws:SecureTransport" = "false" } }
  114|       }
  115|     ]
  116|   })
  117|   depends_on = [aws_s3_bucket_public_access_block.assets]
  118| }
```

## `infra/secrets.tf`

```hcl
    1| # The shell only. The value is put by hand, never through Terraform, so it
    2| # never lands in state or git. It is JSON with two fields:
    3| #   ANTHROPIC_API_KEY      the model key
    4| #   SIMULACRA_ACCESS_KEYS  a JSON object (as a string) of name → access key; a
    5| #                          request needs one to queue new text (serve/guard.ts)
    6| # docs/DEPLOY.md "Access keys" has the command.
    7| # The IPUMS/NHGIS key is only for rebuilding the cache on a laptop; never here.
    8| 
    9| resource "aws_secretsmanager_secret" "prod" {
   10|   name                    = "simulacra/prod"
   11|   description             = "Simulacra API runtime secrets (ANTHROPIC_API_KEY, SIMULACRA_ACCESS_KEYS)"
   12|   recovery_window_in_days = 7
   13| }
```

## `infra/taskdef.json.tftpl`

```
    1| {
    2|   "family": "simulacra-api",
    3|   "networkMode": "awsvpc",
    4|   "requiresCompatibilities": ["FARGATE"],
    5|   "runtimePlatform": { "cpuArchitecture": "ARM64", "operatingSystemFamily": "LINUX" },
    6|   "cpu": "${cpu}",
    7|   "memory": "${memory}",
    8|   "executionRoleArn": "${execution_role_arn}",
    9|   "taskRoleArn": "${task_role_arn}",
   10|   "volumes": [
   11|     {
   12|       "name": "state",
   13|       "efsVolumeConfiguration": {
   14|         "fileSystemId": "${efs_id}",
   15|         "transitEncryption": "ENABLED",
   16|         "authorizationConfig": { "accessPointId": "${access_point_id}", "iam": "ENABLED" }
   17|       }
   18|     }
   19|   ],
   20|   "containerDefinitions": [
   21|     {
   22|       "name": "api",
   23|       "image": "${image}",
   24|       "essential": true,
   25|       "portMappings": [{ "containerPort": 8080, "protocol": "tcp" }],
   26|       "linuxParameters": { "initProcessEnabled": true },
   27|       "stopTimeout": 30,
   28|       "mountPoints": [{ "sourceVolume": "state", "containerPath": "/state" }],
   29|       "environment": [
   30|         { "name": "NODE_ENV", "value": "production" },
   31|         { "name": "PORT", "value": "8080" },
   32|         { "name": "SIMULACRA_LOG", "value": "1" },
   33|         { "name": "SIMULACRA_AUTORUN", "value": "configs/live-1920.json" },
   34|         { "name": "SIMULACRA_PYTHON", "value": "/opt/venv/bin/python" },
   35|         { "name": "SIMULACRA_BUNDLES", "value": "/app/serve/bundles" },
   36|         { "name": "SIMHARNESS_CACHE", "value": "/state/cache" },
   37|         { "name": "SIMULACRA_DAILY_USD", "value": "20" },
   38|         { "name": "SIMULACRA_MONTHLY_USD", "value": "200" },
   39|         { "name": "SIMULACRA_RETAIN_DAYS", "value": "7" },
   40|         { "name": "TRUST_PROXY_HOPS", "value": "2" }
   41|       ],
   42|       "secrets": [
   43|         { "name": "ANTHROPIC_API_KEY", "valueFrom": "${secret_arn}:ANTHROPIC_API_KEY::" },
   44|         { "name": "SIMULACRA_ACCESS_KEYS", "valueFrom": "${secret_arn}:SIMULACRA_ACCESS_KEYS::" }
   45|       ],
   46|       "logConfiguration": {
   47|         "logDriver": "awslogs",
   48|         "options": {
   49|           "awslogs-group": "${log_group}",
   50|           "awslogs-region": "${region}",
   51|           "awslogs-stream-prefix": "api"
   52|         }
   53|       }
   54|     }
   55|   ]
   56| }
```

## `infra/terraform.tfvars.example`

```
    1| # Copy to terraform.tfvars (gitignored) and fill in.
    2| 
    3| # The AWS account this stack deploys to. The provider refuses any other account.
    4| aws_account_id = "123456789012"
    5| 
    6| alert_email = "alerts@example.com"
    7| 
    8| # The deploy role's trusted sub: the repo's immutable subject prefix, as GitHub
    9| # reports it (GET repos/<owner>/<repo>/actions/oidc/customization/sub), plus main.
   10| # Only a workflow running on main can assume the role; a branch, tag, pull
   11| # request or environment gets a different sub.
   12| github_oidc_sub = "repo:<owner>@<owner-id>/<repo>@<repo-id>:ref:refs/heads/main"
```

## `infra/variables.tf`

```hcl
    1| variable "domain" {
    2|   description = "The site's apex domain (DNS hosted at Vercel)."
    3|   type        = string
    4|   default     = "simulacraamericana.com"
    5| }
    6| 
    7| variable "subnet_ids" {
    8|   description = "Default-VPC public subnets for the ALB, the task and EFS (the auth server's two AZs, us-east-1a/b)."
    9|   type        = list(string)
   10|   default     = ["subnet-8c3db5ea", "subnet-35f36514"]
   11| }
   12| 
   13| variable "image" {
   14|   description = "The API image for the FIRST task-definition revision only. CI registers every later one from infra/taskdef.json.tftpl; the service ignores task-definition drift."
   15|   type        = string
   16|   default     = "public.ecr.aws/docker/library/busybox:latest"
   17| }
   18| 
   19| variable "task_cpu" {
   20|   type    = number
   21|   default = 1024
   22| }
   23| 
   24| variable "task_memory" {
   25|   description = "MiB. The worker loads pandas/scipy plus a run's draws alongside Node."
   26|   type        = number
   27|   default     = 4096
   28| }
   29| 
   30| variable "aws_account_id" {
   31|   description = "The AWS account this stack deploys to; the provider refuses any other."
   32|   type        = string
   33|   validation {
   34|     condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
   35|     error_message = "aws_account_id must be a 12-digit AWS account ID."
   36|   }
   37| }
   38| 
   39| variable "alert_email" {
   40|   description = "Subscriber for the alarm topic. SNS emails a confirmation link that must be clicked."
   41|   type        = string
   42| }
   43| 
   44| variable "monthly_budget_usd" {
   45|   description = "AWS Budgets alert threshold for this stack (AWS spend only; Anthropic spend is alerted in the Anthropic console)."
   46|   type        = number
   47|   default     = 150
   48| }
   49| 
   50| variable "github_oidc_sub" {
   51|   description = "The deploy role's trusted OIDC sub, matched exactly: repo:<owner>@<owner-id>/<repo>@<repo-id>:ref:refs/heads/main. Read the prefix from GET repos/<owner>/<repo>/actions/oidc/customization/sub; repo:owner/name:... silently never matches."
   52|   type        = string
   53|   validation {
   54|     condition     = !strcontains(var.github_oidc_sub, "*") && endswith(var.github_oidc_sub, ":ref:refs/heads/main")
   55|     error_message = "github_oidc_sub must name main exactly (…:ref:refs/heads/main), with no wildcard."
   56|   }
   57| }
   58| 
   59| variable "cors_origins" {
   60|   description = "Origins allowed to fetch robot assets (three.js fetches GLBs and textures cross-origin)."
   61|   type        = list(string)
   62|   # The site, plus local builds (pnpm serve :8790, vite dev :5173, vite preview :4173)
   63|   # so the 3D robot loads when the page is run on a laptop.
   64|   default = ["https://simulacraamericana.com", "http://localhost:8790", "http://localhost:5173", "http://localhost:4173"]
   65| }
```

## `infra/vercel-dns.sh`

```bash
    1| #!/usr/bin/env bash
    2| # Every DNS record the AWS side needs, added in Vercel DNS (the zone lives
    3| # there; scope camerons-projects-2a650f0d). Prints the commands by default;
    4| # --apply runs them. These change production DNS, so check the dry run first.
    5| #
    6| #   infra/vercel-dns.sh certs [--apply]      before the full apply: CAA + ACM validation
    7| #   infra/vercel-dns.sh endpoints [--apply]  after it: api. -> ALB, assets. -> CloudFront
    8| #
    9| # The zone before any change:
   10| #   CAA   @  0 issue "pki.goog" | "sectigo.com" | "letsencrypt.org"   (Vercel defaults)
   11| #   ALIAS @  cname.vercel-dns-016.com.
   12| #   ALIAS *  cname.vercel-dns-016.com.
   13| # The explicit api/assets/_validation names below take precedence over the *
   14| # wildcard. Without the amazon.com CAA record ACM never issues.
   15| set -euo pipefail
   16| 
   17| DOMAIN=simulacraamericana.com
   18| MODE=${1:-}
   19| APPLY=${2:-}
   20| cd "$(dirname "$0")"
   21| out() { terraform output -json "$1"; }
   22| 
   23| run() {
   24|   if [ "$APPLY" = "--apply" ]; then "$@"; else printf '%q ' "$@"; echo; fi
   25| }
   26| 
   27| # A name relative to the zone ("_abc.api.simulacraamericana.com." -> "_abc.api").
   28| rel() { local n=${1%.}; echo "${n%.$DOMAIN}"; }
   29| 
   30| case "$MODE" in
   31|   certs)
   32|     run vercel dns add "$DOMAIN" '@' CAA '0 issue "amazon.com"'
   33|     out acm_validation_records | python3 -c '
   34| import json, sys
   35| for r in json.load(sys.stdin).values():
   36|     print(r["name"], r["value"])' | while read -r name value; do
   37|       run vercel dns add "$DOMAIN" "$(rel "$name")" CNAME "${value%.}"
   38|     done
   39|     ;;
   40|   endpoints)
   41|     run vercel dns add "$DOMAIN" api CNAME "$(out api_alb_dns_name | tr -d '"')"
   42|     run vercel dns add "$DOMAIN" assets CNAME "$(out assets_cloudfront_domain | tr -d '"')"
   43|     ;;
   44|   *)
   45|     echo "usage: $0 certs|endpoints [--apply]" >&2
   46|     exit 2
   47|     ;;
   48| esac
   49| if [ "$APPLY" = "--apply" ]; then vercel dns ls "$DOMAIN"; fi
```

## `infra/versions.tf`

```hcl
    1| # Simulacra Americana's AWS stack: the simulation API (ECS Fargate behind an
    2| # ALB, state on EFS), the assets CDN (CloudFront over a private S3 bucket) and
    3| # the private census-derived data bucket. Same account and region as the
    4| # Partyhat auth server, but nothing here references or modifies its resources;
    5| # the only shared object read is the account's GitHub OIDC provider.
    6| #
    7| # State lives in s3://simulacra-americana-tfstate (infra/bootstrap.sh creates it).
    8| # Apply order and the DNS steps between applies: docs/DEPLOY.md, "Stand-up".
    9| 
   10| terraform {
   11|   required_version = ">= 1.10"
   12|   required_providers {
   13|     aws = { source = "hashicorp/aws", version = "~> 6.0" }
   14|   }
   15|   backend "s3" {
   16|     bucket       = "simulacra-americana-tfstate"
   17|     key          = "prod/terraform.tfstate"
   18|     region       = "us-east-1"
   19|     encrypt      = true
   20|     use_lockfile = true
   21|   }
   22| }
   23| 
   24| provider "aws" {
   25|   region              = "us-east-1"
   26|   allowed_account_ids = [var.aws_account_id]
   27|   default_tags {
   28|     tags = { project = "simulacra-americana", managed-by = "terraform" }
   29|   }
   30| }
   31| 
   32| data "aws_caller_identity" "current" {}
   33| data "aws_region" "current" {}
   34| 
   35| locals {
   36|   account_id = data.aws_caller_identity.current.account_id
   37|   region     = data.aws_region.current.region
   38|   name       = "simulacra"
   39| }
```

## `package.json`

```json
    1| {
    2|   "name": "synthetic-voters-toy",
    3|   "private": true,
    4|   "version": "0.1.0",
    5|   "type": "module",
    6|   "packageManager": "pnpm@9.3.0",
    7|   "engines": { "node": ">=22" },
    8|   "scripts": {
    9|     "dev": "vite dev",
   10|     "build": "vite build",
   11|     "serve": "tsx serve/index.ts",
   12|     "prepare": "svelte-kit sync || true",
   13|     "check": "svelte-kit sync && svelte-check --tsconfig ./tsconfig.json --fail-on-warnings",
   14|     "lint": "biome lint --error-on-warnings .",
   15|     "size": "tsx scripts/size-check.ts",
   16|     "test": "vitest run",
   17|     "test:py": "python3 -m pytest -q",
   18|     "gate": "pnpm lint && pnpm check && pnpm size && pnpm test && pnpm test:py"
   19|   },
   20|   "dependencies": {
   21|     "express": "^5.3.0",
   22|     "lucide-svelte": "^0.562.0",
   23|     "three": "^0.181.2",
   24|     "zod": "^4.6.7"
   25|   },
   26|   "devDependencies": {
   27|     "@biomejs/biome": "^2.2.0",
   28|     "@sveltejs/adapter-static": "^3.0.11",
   29|     "@sveltejs/kit": "^2.70.4",
   30|     "@sveltejs/vite-plugin-svelte": "^5.0.0",
   31|     "@types/express": "^5.0.3",
   32|     "@types/node": "^22.15.0",
   33|     "@types/three": "^0.181.0",
   34|     "svelte": "^5.0.0",
   35|     "svelte-check": "^4.1.0",
   36|     "tsx": "^4.20.0",
   37|     "typescript": "^5.8.0",
   38|     "vite": "^6.4.6",
   39|     "vitest": "^4.1.12"
   40|   },
   41|   "pnpm": {
   42|     "onlyBuiltDependencies": ["esbuild", "@biomejs/biome"],
   43|     "auditConfig": { "ignoreCves": ["CVE-2026-128120"] }
   44|   }
   45| }
```

## `pyproject.toml`

```toml
    1| [build-system]
    2| requires = ["setuptools>=69"]
    3| build-backend = "setuptools.build_meta"
    4| 
    5| [project]
    6| name = "synthetic-voters-toy-harness"
    7| version = "0.1.0"
    8| description = "The simulation harness behind /api/simulacra: a calibrated backbone decides the counts, LLM agents supply paired changes and quotes."
    9| requires-python = ">=3.12"
   10| dependencies = [
   11|     "numpy>=2.0",
   12|     "pandas>=2.2",
   13|     "scipy>=1.13",
   14| ]
   15| 
   16| [project.optional-dependencies]
   17| test = ["pytest>=8.0"]
   18| # Only the paid stages (ask, research, whatif) import the SDK, lazily; CI never needs it.
   19| llm = ["anthropic>=1.0"]
   20| build = ["pyreadr>=0.5"]
   21| 
   22| [tool.setuptools]
   23| packages = ["simharness"]
   24| 
   25| [tool.pytest.ini_options]
   26| testpaths = ["tests"]
```

## `requirements.lock`

```
    1| # The harness's runtime dependencies for the API image (pyproject.toml plus the llm extra),
    2| # frozen from a clean Python 3.13 venv. anthropic must support speed='fast'.
    3| annotated-types==0.8.0
    4| anthropic==1.10.0
    5| anyio==4.15.1
    6| docstring_parser==0.18.0
    7| h11==0.16.0
    8| httpcore2==2.13.1
    9| httpx2==2.13.1
   10| idna==3.20
   11| jiter==0.17.0
   12| numpy==2.5.3
   13| pandas==3.0.6
   14| pydantic==2.13.5
   15| pydantic_core==2.46.5
   16| python-dateutil==2.9.0.post0
   17| scipy==1.18.1
   18| six==1.17.0
   19| sniffio==1.3.1
   20| truststore==0.10.4
   21| typing-inspection==0.4.4
   22| typing_extensions==4.16.0
```

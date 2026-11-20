# synthetic-electorate-toy: file map

Generated from commit `93f19ca29232` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.

1097 tracked files. 187 are reproduced in full in the `code-N.md` parts; the rest are listed with the reason they are not.

Every path below is relative to https://raw.githubusercontent.com/partyhat-ai/synthetic-electorate-toy/main/ (append the path to fetch the raw file).

| File | Bytes | Lines | Description | In digest |
|---|---|---|---|---|
| `.dockerignore` | 485 | 34 | Build context hygiene: the API image needs serve/, simharness/, extracts/, | code-1.md |
| `.env.example` | 243 | 4 | Base URL for the robot model, paint textures and portraits. | code-1.md |
| `.github/workflows/ci.yml` | 757 | 30 |  | code-1.md |
| `.github/workflows/deploy-api.yml` | 7,543 | 174 | Builds the API image and rolls the ECS service behind | code-1.md |
| `.github/workflows/llms-digest.yml` | 1,287 | 40 | Keeps llms.txt and llms/ (a plain-text copy of this repository for tools that | code-1.md |
| `.gitignore` | 181 | 16 |  | code-1.md |
| `AGENTS.md` | 1,723 | 34 | Rules for coding agents | code-1.md |
| `CONTEXT.md` | 1,382 | 19 | Vocabulary | code-1.md |
| `DISCLOSURES.md` | 72,502 | 1,312 | Disclosures: inaccuracies and intellectual-honesty flags | code-1.md |
| `Dockerfile` | 4,134 | 95 | syntax=docker/dockerfile:1 | code-1.md |
| `EVAL.md` | 18,600 | 336 | EVAL: the 1920 prototype | code-2.md |
| `METHOD.md` | 24,001 | 489 | Simulacra Americana: how the harness works | code-2.md |
| `README.md` | 2,087 | 49 | Synthetic voters (toy example) | code-2.md |
| `VALIDITY.md` | 25,202 | 341 | Validity: goals, contamination, leakage and historical bias | code-2.md |
| `biome.json` | 775 | 40 |  | code-2.md |
| `docker/entrypoint.sh` | 652 | 17 | The API container's entrypoint: check the state mount, surface the worker's | code-2.md |
| `docs/DEPLOY.md` | 17,170 | 327 | Deploying Simulacra Americana | code-2.md |
| `docs/harness/README.md` | 12,296 | 190 | Simulacra Americana harness | code-2.md |
| `infra/.gitignore` | 60 | 5 |  | code-2.md |
| `infra/.terraform.lock.hcl` | 1,481 | 26 | This file is maintained automatically by "terraform init". | code-2.md |
| `infra/acm.tf` | 1,386 | 31 | Certificates for api. (ALB) and assets. (CloudFront; must be us-east-1, | code-2.md |
| `infra/alb.tf` | 1,465 | 53 | Default 60s idle timeout: every route answers fast (runs are polled). | code-2.md |
| `infra/backup.tf` | 1,424 | 48 | Daily EFS backups, 35 days. Production state diverges from git the moment | code-3.md |
| `infra/bootstrap.sh` | 1,092 | 18 | One-time: the Terraform state bucket. Re-runnable (every step is idempotent). | code-3.md |
| `infra/cloudfront.tf` | 2,568 | 71 | assets.simulacraamericana.com: CloudFront over the private assets bucket. | code-3.md |
| `infra/ecs.tf` | 6,546 | 181 | One cluster, one service, ONE task, on purpose: run state is an in-process | code-3.md |
| `infra/efs.tf` | 1,781 | 59 | The service's state: serve/bundles, sessions, runs, whatifs, configs and | code-3.md |
| `infra/iam.tf` | 4,927 | 145 | Three roles, no static keys anywhere. | code-3.md |
| `infra/network.tf` | 2,567 | 78 | The auth server's network pattern: default-VPC public subnets, tasks with a | code-3.md |
| `infra/observability.tf` | 5,467 | 157 | A real subscriber this time (the auth server's topic had none). SNS emails a | code-3.md |
| `infra/outputs.tf` | 1,630 | 49 | infra/vercel-dns.sh reads these (terraform output -json); deploy-api.yml's | code-3.md |
| `infra/s3.tf` | 3,553 | 118 | Two private buckets. | code-3.md |
| `infra/secrets.tf` | 691 | 13 | The shell only. The value is put by hand, never through Terraform, so it | code-3.md |
| `infra/taskdef.json.tftpl` | 2,071 | 56 |  | code-3.md |
| `infra/terraform.tfvars.example` | 570 | 12 | Copy to terraform.tfvars (gitignored) and fill in. | code-3.md |
| `infra/variables.tf` | 2,538 | 65 |  | code-3.md |
| `infra/vercel-dns.sh` | 1,801 | 49 | Every DNS record the AWS side needs, added in Vercel DNS (the zone lives | code-3.md |
| `infra/versions.tf` | 1,275 | 39 | Simulacra Americana's AWS stack: the simulation API (ECS Fargate behind an | code-3.md |
| `package.json` | 1,328 | 45 |  | code-3.md |
| `pnpm-lock.yaml` | 75,611 | 2,356 |  | skip: lockfile |
| `pyproject.toml` | 693 | 26 |  | code-3.md |
| `requirements.lock` | 525 | 22 | The harness's runtime dependencies for the API image (pyproject.toml plus the llm extra), | code-3.md |
| `scripts/harness/build_corpus.py` | 53,631 | 885 | build_corpus.py — dated Chronicling America corpus for one election year. | code-3.md |
| `scripts/harness/build_franchise.py` | 6,229 | 126 | Build franchise/state_franchise_all.csv: the legal franchise by state, presidential years 1868–1968. | code-3.md |
| `scripts/harness/build_population.py` | 5,235 | 94 | NHGIS extract → population/adults_<year>_by_state_nhgis.csv in the harness's | code-4.md |
| `scripts/harness/build_population_early.py` | 23,254 | 400 | NHGIS 1870-1910 -> population/adults_<year>_by_state_nhgis.csv (long format, | code-4.md |
| `scripts/harness/build_population_mid.py` | 18,198 | 327 | NHGIS 1940–1970 → population tables (21+ and 18+), long format like | code-4.md |
| `scripts/harness/build_population_modern.py` | 20,528 | 385 | NHGIS extract (nhgis_extract_modern.py) -> population/adults18_<year>_by_state_nhgis.csv | code-4.md |
| `scripts/harness/build_population_republic.py` | 12,694 | 276 | 1790–1860 censuses → population/adults_<year>_by_state_nhgis.csv (same long | code-4.md |
| `scripts/harness/build_republic.py` | 28,675 | 474 | Early-republic labels and franchise, 1789–1864. | code-5.md |
| `scripts/harness/build_returns.py` | 16,952 | 321 | Build labels/state_pres_all.csv: certified presidential returns by state, 1868–2024. | code-5.md |
| `scripts/harness/bundle_fixture.py` | 2,422 | 57 | Trim a published bundle into the shared contract example. | code-5.md |
| `scripts/harness/nhgis_common.py` | 8,612 | 186 | NHGIS, shared by the harness scripts. | code-5.md |
| `scripts/harness/nhgis_extract.py` | 2,572 | 40 | Submit, wait for and download the NHGIS state-level population extract | code-5.md |
| `scripts/harness/nhgis_extract_modern.py` | 2,728 | 52 | Submit, wait for and download the NHGIS state-level extract behind the | code-5.md |
| `scripts/harness/nhgis_extract_republic.py` | 1,702 | 29 | Submit, wait for and download the NHGIS state-level extract behind the | code-5.md |
| `scripts/harness/sessions-report.py` | 3,727 | 86 | What people typed into the page, and what the robot couldn't model. | code-5.md |
| `scripts/llms_digest.py` | 12,022 | 238 | Build llms.txt and llms/: a plain-text copy of this repository for tools that | code-5.md |
| `scripts/mirror-portraits.py` | 5,354 | 139 | Mirror the candidates' Wikimedia Commons portraits for the assets bucket. | code-5.md |
| `scripts/model-check.ts` | 1,242 | 24 | Prints the sample model's outcome for every what-if of every story | code-5.md |
| `scripts/publish-assets.sh` | 2,895 | 52 | Publish the robot assets and mirrored portraits to s3://simulacra-americana-assets | code-5.md |
| `scripts/size-check.ts` | 700 | 18 | Fails when any tracked source file is over the line limit. | code-5.md |
| `scripts/sync-data.sh` | 3,921 | 68 | Census-derived data and service state: laptop -> private data bucket -> EFS. | code-5.md |
| `serve/app.ts` | 1,055 | 29 | The server: /api/simulacra plus the static SvelteKit build, with an SPA | code-5.md |
| `serve/bundle.ts` | 2,144 | 71 | What enters the server, parsed once with zod: the bundle contract and the | code-5.md |
| `serve/bundles/RUN_ID` | 16 | 1 |  | code-5.md |
| `serve/contract.test.ts` | 4,015 | 78 | Published bundles write State.flipped as 0 / 1: parsed, it is a boolean. | code-5.md |
| `serve/contract.ts` | 13,642 | 343 | The page's contract with the simulation server, one definition for both | code-6.md |
| `serve/guard.test.ts` | 5,757 | 134 |  | code-6.md |
| `serve/guard.ts` | 7,742 | 211 | What stands between a visitor and the API: the intake's dollar caps, per-IP | code-6.md |
| `serve/index.ts` | 305 | 7 | `pnpm serve`: the page and its API on PORT (default 8787). | code-6.md |
| `serve/server.ts` | 1,765 | 37 | The production entry (the API container's CMD, bundled to dist/server.mjs). | code-6.md |
| `serve/simulacra.test.ts` | 12,885 | 297 | The real router and app, in process, over real HTTP, reading the real bundles in serve/bundles/. | code-6.md |
| `serve/simulacra.ts` | 23,956 | 573 | /api/simulacra: serves precomputed harness bundles in the page's contract. | code-6.md |
| `simharness/__init__.py` | 220 | 6 | Simulacra Americana simulation harness. | code-6.md |
| `simharness/agentlayer.py` | 29,408 | 486 | Builds every model request for a run (control, counterfactuals, label swap, | code-6.md |
| `simharness/agents.py` | 8,964 | 187 | Agents: invented people drawn from a cohort's documented makeup. | code-7.md |
| `simharness/aggregate.py` | 6,449 | 128 | From cell draws to states, electoral votes, ranges and the draw count. | code-7.md |
| `simharness/backbone.py` | 41,720 | 800 | The statistical backbone: turnout and choice by cell, calibrated exactly. | code-7.md |
| `simharness/benchmarks.py` | 9,433 | 150 | Held-out benchmarks. Only the validation stages (Run.evaluate, and | code-7.md |
| `simharness/cohorts.py` | 3,405 | 76 | Agent cohorts: strata of the cell table, merged to a cost cap. | code-7.md |
| `simharness/config.py` | 5,344 | 101 | Run configuration: everything that determines a run, hashed into its id. | code-7.md |
| `simharness/data.py` | 28,589 | 602 | Loaders for the harness cache. Benchmarks are not loaded here (see | code-7.md |
| `simharness/evaluate.py` | 8,202 | 150 | Validation of the 1920 prototype (EVAL.md). Benchmarks are read only here. | code-8.md |
| `simharness/evidence.py` | 37,527 | 605 | Historical evidence for a what-if: what reliable sources say about how the | code-8.md |
| `simharness/geo.py` | 3,224 | 52 | States, regions and 1920 electoral votes (and AK, HI, DC for 1960 on). | code-8.md |
| `simharness/intake.py` | 25,014 | 480 | Typed what-if intake: a reader's words → a what-if the page can serve. | code-8.md |
| `simharness/llm.py` | 16,770 | 376 | The voice layer's model calls, behind one interface with three backends. | code-8.md |
| `simharness/paired.py` | 8,367 | 180 | Paired control/counterfactual answers → per-cohort effects on the backbone. | code-8.md |
| `simharness/pipeline.py` | 45,929 | 767 | The pipeline's stages other than publish (publish.py): backbone, plan, ask, | code-9.md |
| `simharness/profiles.py` | 7,064 | 122 | Everything about one election that the pipeline needs and the data can't say: | code-9.md |
| `simharness/prompts.py` | 10,316 | 183 | Versioned prompts: the blinded control brief, the non-hypothetical | code-9.md |
| `simharness/publish.py` | 32,179 | 528 | The publish stage: every what-if combination → the page's result shape and bundle. | code-9.md |
| `simharness/quotes.py` | 4,074 | 80 | Choosing whose words the page shows, and auditing the reasons behind them. | code-9.md |
| `simharness/run.py` | 4,582 | 85 | The pipeline. `python -m simharness.run <stage> --config configs/prototype-1920.json` | code-9.md |
| `simharness/scenario.py` | 31,927 | 562 | Any typed what-if → a what-if the pipeline can run. | code-10.md |
| `simharness/serialize.py` | 13,632 | 368 | The page's contract (api.js), plus additive fields the page may ignore. | code-10.md |
| `simharness/stats.py` | 4,715 | 140 | Small numeric tools: raking, apportionment, logit arithmetic, metrics. | code-10.md |
| `simharness/whatifs.py` | 12,364 | 236 | The what-ifs: each edits one layer of the calibrated world and names its | code-10.md |
| `simharness/world.py` | 16,346 | 224 | Staging a compiled what-if's world, and auditing whether the voices lived in it (D33). | code-10.md |
| `src/app.d.ts` | 49 | 4 |  | code-10.md |
| `src/app.html` | 6,907 | 65 | The four weights the page renders, fetched at parse time to avoid a late font swap. --> | code-10.md |
| `src/app.html.test.ts` | 1,825 | 43 | The plain-text copy of the page in app.html is for crawlers and agents only. It must never be | code-10.md |
| `src/lib/robot/RobotFrame.svelte` | 4,404 | 125 | The narrator robot, framed into the page. Mount it inside the element the | code-10.md |
| `src/lib/robot/assets.ts` | 757 | 19 | Where the robot's model, paint textures and the candidates' portraits live | code-10.md |
| `src/lib/robot/blast.test.ts` | 1,513 | 38 |  | code-10.md |
| `src/lib/robot/blast.ts` | 7,101 | 200 | Shots from the robot's chest reactor, on demand (a tap on the robot): one | code-10.md |
| `src/lib/robot/camera.test.ts` | 5,838 | 144 |  | code-11.md |
| `src/lib/robot/camera.ts` | 7,757 | 203 | The robot's camera: where it stands for the framed shot, the lens shift that | code-11.md |
| `src/lib/robot/characters.ts` | 3,134 | 85 | The narrator: ChatPro (character atlas-09) in its Americana model. The values | code-11.md |
| `src/lib/robot/lighting.ts` | 2,395 | 70 | The robot's lights: the room environment, a hemisphere fill and three | code-11.md |
| `src/lib/robot/messages.test.ts` | 3,272 | 72 |  | code-11.md |
| `src/lib/robot/messages.ts` | 3,077 | 71 | Every postMessage between the page (RobotFrame) and the robot's frame | code-11.md |
| `src/lib/robot/motion.ts` | 8,528 | 238 | The robot's motion: its idle, exaggerated and sped up for the small framed | code-11.md |
| `src/lib/robot/paint.test.ts` | 2,603 | 62 | The shape of the Rerun paint's overrides.json as published. | code-11.md |
| `src/lib/robot/paint.ts` | 7,636 | 220 | The robot's two paints on one loaded model. History is the GLB's own; Rerun | code-11.md |
| `src/lib/robot/scene.ts` | 11,327 | 314 | The robot's scene, drawn into a transparent canvas that fills the frame. | code-11.md |
| `src/lib/robot/stage.test.ts` | 4,919 | 143 |  | code-11.md |
| `src/lib/robot/stage.ts` | 4,178 | 105 | Pure placement math: the robot's box, its turn with the time bar and by | code-11.md |
| `src/lib/robot/style.css` | 492 | 21 | The robot's frame (/robot) is its own document: nothing but the canvas on | code-11.md |
| `src/lib/simulacra/AboutSources.svelte` | 6,921 | 62 | The About popover's Sources: every data source the page and the | code-11.md |
| `src/lib/simulacra/AbsentRow.svelte` | 1,987 | 46 | A group the year has no simulation for, held in its usual place on a | code-11.md |
| `src/lib/simulacra/ElectionHeader.svelte` | 8,119 | 162 | The election at the top of the page: the two candidates with their | code-11.md |
| `src/lib/simulacra/GroupLabel.svelte` | 826 | 18 | A group's name. On a narrow window the word "citizens" is set small and | code-11.md |
| `src/lib/simulacra/InfoPopover.svelte` | 3,346 | 101 | An ⓘ button that opens a short explanation — for terms (backtest, held | code-11.md |
| `src/lib/simulacra/KindChips.svelte` | 6,130 | 144 | The what-if suggestions: one row of chips, scrolled sideways (a vertical | code-11.md |
| `src/lib/simulacra/MiniMap.svelte` | 5,681 | 135 | The election's map, small: one tile per state, in the colour of whoever | code-11.md |
| `src/lib/simulacra/Narrator.svelte` | 3,284 | 115 | The narrator: the harness robot's bubble and the what-if composer | code-12.md |
| `src/lib/simulacra/Places.svelte` | 1,666 | 41 | A run of text with its places (places.ts) made pointable: hovering one | code-12.md |
| `src/lib/simulacra/Portrait.svelte` | 4,546 | 124 | A candidate's portrait (the lead image of their Wikipedia article), or | code-12.md |
| `src/lib/simulacra/RobotStage.svelte` | 9,028 | 219 | Stills of the robot, one per paint, rendered from this page (paint, | code-12.md |
| `src/lib/simulacra/SliceRow.svelte` | 10,439 | 260 | One group of voters as a row of fifty people: the winner's voters from | code-12.md |
| `src/lib/simulacra/TimeBar.svelte` | 7,673 | 236 | The timeline along the bottom: every election from 1789 to 2024 as a | code-12.md |
| `src/lib/simulacra/WhatIf.svelte` | 22,948 | 492 | Where you talk to the harness: it stands at the left (the page frames the | code-12.md |
| `src/lib/simulacra/WhatIfComposer.svelte` | 5,567 | 157 | The what-if composer: the suggestions (KindChips) on one row, scrolled | code-12.md |
| `src/lib/simulacra/WhatIfWorking.svelte` | 12,937 | 234 | The robot's working, inside its bubble (WhatIf.svelte): the steps (live, | code-12.md |
| `src/lib/simulacra/accessKey.test.ts` | 2,425 | 60 | sessionStorage's two calls over a Map. | code-12.md |
| `src/lib/simulacra/accessKey.ts` | 2,402 | 57 | The key that lets typed what-ifs be modelled (POST /runs sends it, api.ts). | code-12.md |
| `src/lib/simulacra/actions.ts` | 1,104 | 45 | Svelte actions the page uses. | code-12.md |
| `src/lib/simulacra/api.test.ts` | 9,372 | 197 | A fake server: answers each call from `reply`, and records what was asked. | code-12.md |
| `src/lib/simulacra/api.ts` | 8,438 | 203 | Simulacra Americana's connection to the simulation server, under | code-12.md |
| `src/lib/simulacra/format.ts` | 343 | 6 | Number formats for Simulacra Americana. | code-13.md |
| `src/lib/simulacra/geo.test.ts` | 1,750 | 41 |  | code-13.md |
| `src/lib/simulacra/geo.ts` | 2,964 | 44 | Simulacra Americana's geography: every election year, and the tile map's | code-13.md |
| `src/lib/simulacra/groups.ts` | 1,874 | 41 | The five voter groups every simulated year is built from, in the order the | code-13.md |
| `src/lib/simulacra/header.ts` | 2,449 | 51 | The election header's derived text and colours: who gets which paint, the | code-13.md |
| `src/lib/simulacra/history.test.ts` | 3,631 | 83 | Years whose per-state electoral votes don't sum to the electoral votes cast, | code-13.md |
| `src/lib/simulacra/history.ts` | 42,092 | 432 | Every presidential election from 1789 to 2024 as it happened: who ran, who | code-13.md |
| `src/lib/simulacra/narrator.test.ts` | 8,494 | 137 | A run as the server answers it (serve/simulacra.ts compute): the bundle's run plus the briefs behind | code-13.md |
| `src/lib/simulacra/narrator.ts` | 15,944 | 324 | What the robot says (the Narrator's pure parts): a finished rerun's steps | code-13.md |
| `src/lib/simulacra/palette.test.ts` | 2,224 | 57 | 1860: Lincoln (R), Breckinridge (Southern Democrat), Bell, Douglas. | code-13.md |
| `src/lib/simulacra/palette.ts` | 4,850 | 135 | Chart colour for Simulacra Americana. | code-13.md |
| `src/lib/simulacra/places.ts` | 2,957 | 60 | Places named in the page's words — a state, a region, the colonies — found | code-13.md |
| `src/lib/simulacra/runs.test.ts` | 8,908 | 224 |  | code-13.md |
| `src/lib/simulacra/runs.ts` | 7,536 | 215 | A rerun from start to finish: ask the server to start it, poll it until | code-13.md |
| `src/lib/simulacra/sample.test.ts` | 4,289 | 93 |  | code-14.md |
| `src/lib/simulacra/sample.ts` | 32,839 | 815 | Sample mode: the simulation server's answers (api.ts), made up, so the page | code-14.md |
| `src/lib/simulacra/sampleData.ts` | 12,451 | 130 | The sample model's numbers (sample.ts): the country, roughly, by year; | code-14.md |
| `src/lib/simulacra/sampleEras.ts` | 9,002 | 122 | The groups and what-ifs every election has in the sample, by era, for the | code-14.md |
| `src/lib/simulacra/sampleTypes.ts` | 4,434 | 122 | Types shared by the sample model (sample.ts) and its written stories | code-14.md |
| `src/lib/simulacra/schemas.ts` | 333 | 5 | The simulation server's answers, parsed once where they enter the page | code-14.md |
| `src/lib/simulacra/state.svelte.ts` | 9,866 | 268 | The page's state, reactive: per year, the groups and what-ifs the server | code-14.md |
| `src/lib/simulacra/state.test.ts` | 7,346 | 173 |  | code-14.md |
| `src/lib/simulacra/state.ts` | 6,714 | 174 | The page's state, the pure parts: what the URL asks for, what a rerun of a | code-14.md |
| `src/lib/simulacra/stories.ts` | 32,190 | 324 | The sample's ten written elections: for each, the groups of voters worth | code-15.md |
| `src/lib/simulacra/tabIcon.test.ts` | 3,619 | 105 | A clock the test winds by hand: one interval at a time. | code-15.md |
| `src/lib/simulacra/tabIcon.ts` | 3,773 | 120 | The tab icon follows the robot's chest blasts: the colour of the last one | code-15.md |
| `src/lib/simulacra/theme.css` | 2,678 | 62 | Simulacra Americana's page-level look: the scrolling layer, the Rerun | code-15.md |
| `src/lib/simulacra/types.ts` | 996 | 29 | Small view types shared by the page and its components. | code-15.md |
| `src/lib/simulacra/whatif.ts` | 3,247 | 86 | The what-if section's pure parts (WhatIf.svelte and its pieces): what the | code-15.md |
| `src/routes/+layout.ts` | 138 | 3 | Client-only app: the view and year come from the URL, nothing to pre-render. | code-15.md |
| `src/routes/+page.svelte` | 21,186 | 458 | Simulacra Americana: rerun an American presidential election with one | code-15.md |
| `src/routes/robot/+page.svelte` | 2,631 | 74 | The robot's frame: RobotFrame loads this page in an iframe and talks to it | code-15.md |
| `static/favicon-blue.png` | 5,117 | 0 |  | skip: binary |
| `static/favicon-red.png` | 5,466 | 0 |  | skip: binary |
| `static/favicon-white.png` | 5,296 | 0 |  | skip: binary |
| `static/favicon.png` | 6,595 | 0 |  | skip: binary |
| `static/fonts/Geist-Regular.woff2` | 39,060 | 0 |  | skip: binary |
| `static/fonts/Geist-SemiBold.woff2` | 40,220 | 0 |  | skip: binary |
| `static/fonts/GeistMono-Light.woff2` | 50,740 | 0 |  | skip: binary |
| `static/fonts/GeistMono-Medium.woff2` | 51,424 | 0 |  | skip: binary |
| `static/fonts/GeistMono-Regular.woff2` | 50,284 | 0 |  | skip: binary |
| `static/fonts/OFL.txt` | 4,368 | 92 |  | code-15.md |
| `static/harness-faces/atlas-09.png` | 120,174 | 0 |  | skip: binary |
| `static/llms.txt` | 2,847 | 33 | Simulacra Americana | code-15.md |
| `static/robots.txt` | 290 | 8 | Simulacra Americana: every American presidential election, replayed and rerun with one thing changed | code-15.md |
| `static/simulacra/chatpro-history.png` | 30,050 | 0 |  | skip: binary |
| `static/simulacra/chatpro-rerun.png` | 29,388 | 0 |  | skip: binary |
| `static/sitemap.xml` | 245 | 8 |  | code-15.md |
| `svelte.config.js` | 266 | 8 | @type {import('@sveltejs/kit').Config} | code-15.md |
| `tests/test_agents.py` | 2,308 | 49 | Agent cohorts, invented people and their quotes (cohorts.py, quotes.py, scenario.py). | code-15.md |
| `tests/test_backbone.py` | 1,423 | 33 | The statistical backbone's building blocks (stats.py). | code-15.md |
| `tests/test_contract.py` | 5,425 | 109 | The page's contract: what serialize emits and the bundle the server reads. | code-15.md |
| `tests/test_evaluate.py` | 3,400 | 60 | The evaluate-stage checks (EVAL.md). | code-15.md |
| `tests/test_intake_spend.py` | 5,214 | 118 | The intake's spend: daily and monthly caps across every visitor, and how a | code-15.md |
| `tests/test_isolation.py` | 7,700 | 150 | Held-out benchmark isolation. | code-15.md |
| `tests/test_whatif.py` | 3,554 | 57 | What-ifs and their evidence: source tiers, grounding, blending and confidence (evidence.py). | code-16.md |
| `tsconfig.json` | 795 | 32 |  | code-16.md |
| `vercel.json` | 396 | 11 |  | code-16.md |
| `vite.config.ts` | 359 | 9 | In development the page calls /api/simulacra on the local server (pnpm serve). | code-16.md |

### Data files (not reproduced; one sample per folder in `data-samples.md`)

| Folder | Files | Bytes |
|---|---|---|
| `configs/` | 63 | 92,494 |
| `extracts/` | 2 | 47,047 |
| `profiles/` | 58 | 235,910 |
| `runs/` | 604 | 42,649,170 |
| `serve/` | 60 | 13,024,850 |
| `tests/` | 1 | 54,943 |
| `whatifs/` | 109 | 1,623,304 |

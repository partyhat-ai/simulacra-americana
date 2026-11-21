# simulacra-americana: source and docs, part 2 of 17

Generated from commit `4f68c2b917aa` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `EVAL.md` to `docs/DEPLOY.md`. Lines are numbered as in the repository.

## `EVAL.md`

```markdown
    1| # EVAL: the 1920 prototype
    2| 
    3| **Run.** `runs/1920-bcbd86b43f`, seed 1920, 400 draws, truth mode, prompt p1.
    4| 
    5| Every number below is copied from `runs/1920-bcbd86b43f/validation.json`,
    6| `analysis.json` and `published/1920.json`.
    7| 
    8| This is not the run the server publishes. `serve/bundles/1920.json` comes
    9| from a later run (its `runId`), with typed what-ifs added, 100 draws, two
   10| Haiku 4.5 interviews in each of six cohorts, and no `validation.json`. The
   11| scores below are the prototype's and haven't been rerun.
   12| 
   13| ## Summary
   14| 
   15| - **Reproduction is exact.** Every one of 400 draws reproduces each state's
   16|   certified R, D and other vote to within 0.33 votes. Every draw gives 404–127.
   17| - **The backbone beats its baselines on held-out states:**
   18|   - two-party RMSE 7.6 points (uniform swing 8.7, persistence 17.4);
   19|   - turnout RMSE 2.9 points (persistence 16.5);
   20|   - Spearman 0.92;
   21|   - Brier 0.052 (uniform swing 0.069).
   22| - **It fails two backbone checks:**
   23|   - **B5.** It calls North Carolina for Harding.
   24|   - **N1.** Its women's-turnout intervals are too narrow and run high in CT,
   25|     MA and NY.
   26| - **The 19th Amendment placebo passes.** In Georgia and Mississippi, where
   27|   women couldn't register in time, the implied women's turnout is 2.1% and
   28|   3.5%, near zero as it should be.
   29| - **The agent layer:**
   30|   - It is fully memorization-exposed: 56 of 56 probes named 1920, both
   31|     candidates and the winner.
   32|   - It follows platforms, not labels (label swap 0%).
   33|   - It is **badly homogenized**: 90% of eligible cohorts answered unanimously.
   34|   - It **overstates turnout** by about 12 points on average (15.5 points for
   35|     women, N3).
   36|   - Its paired effect for the League what-if has a stable sign across three
   37|     paraphrases and two models.
   38| - **The biggest uncertainty is β_B**, how Black voters split. The state
   39|   returns can't identify it. It swings the `fifteenth` result from 416 to 449
   40|   Harding electoral votes (see "The biggest uncertainty" below).
   41| 
   42| ## What-if results (the prototype's bundle)
   43| 
   44| Harding is A; Cox is B. Ranges are the central 80% of Harding's electoral
   45| votes across 400 draws.
   46| 
   47| | What-if | Harding EV (point, 80% range) | Cox wins in | States flipped (point) | States with P(flip) > 10% | Popular vote, Harding / Cox |
   48| |---|---|---|---|---|---|
   49| | None (history) | 404 (404–404) | 0 / 400 | none | none | 60.2% / 34.1% of 26.80M |
   50| | `no-19th` (franchise, high) | 429 (417–429) | 0 / 400 | KY, NC | KY 0.99, NC 0.64 | 62.2% / 32.0% of 23.66M |
   51| | `fifteenth` (franchise, high) | 416 (404–475) | 0 / 400 | NC | NC 0.51, AR 0.29, VA 0.20, AL 0.19, FL 0.16, LA 0.16 | 60.8% / 33.6% of 27.41M |
   52| | `league` (issue, low) | 404 (392–404) | 0 / 400 | none (TN holds by 0.3 points) | TN 0.12 | 57.8% / 36.7% of 26.36M |
   53| | `everyone` (franchise) | 416 (392–455) | 0 / 400 | NC | NC 0.52, AL 0.20, VA 0.16 | 58.1% / 36.0% of 61.75M |
   54| 
   55| Combinations are in the bundle. For example, `fifteenth+no-19th` gives 441
   56| (417–488) and flips KY, NC and VA.
   57| 
   58| Verdicts as the robot says them:
   59| 
   60| > **`no-19th`:** 3.1 million women who voted can't, outside the states that
   61| > already let them. Kentucky, North Carolina flip, but Harding still wins,
   62| > 429–102. The closest call is Tennessee, which holds for Harding by 3.0
   63| > points. Cox wins in 0 of 400 draws.
   64| 
   65| > **`league`:** With the treaty settled, the voters I interviewed lean 2.7
   66| > points further toward Cox than the same people did in the world as it was.
   67| > No state flips. Harding wins, 404–127. The closest call is Tennessee, which
   68| > holds for Harding by 0.3 points. Cox wins in 0 of 400 draws.
   69| 
   70| **How to read these:**
   71| - **`no-19th`** helps Harding. The backbone's women's tilt δ is −0.67 logit
   72|   (80% interval −0.98 to −0.35), meaning women leaned *toward Cox* relative to
   73|   men of their state, so removing them helps Harding. This comes from a
   74|   regression of the 1916 → 1920 swing on the new-women share. It is
   75|   identified mostly by the West/East contrast, which region can confound (see
   76|   limitations).
   77| - **`league`** moves every group toward Cox. The simulated voters lose a
   78|   reason to vote against the administration's party. Nothing flips.
   79| 
   80| ## Validation checks
   81| 
   82| To rerun these with the repo alone (no private cache), use the 1920 inputs in `data/1920/`
   83| (`data/1920/PROVENANCE.md`): `SIMHARNESS_CACHE=data/1920 python3 -m simharness.run backbone`, then
   84| `evaluate`, both with `--config configs/prototype-1920.json`. Today's code gives B1 7.47, B3 0.93 and B4 0.047
   85| where the table below has 7.55, 0.923 and 0.052. That comes from code changes since this run, not the data;
   86| every other figure is the same.
   87| 
   88| | ID | Check | Value | Threshold | Result |
   89| |---|---|---|---|---|
   90| | R1 | Unchanged rerun reproduces every state | max error 0.33 votes; EV 404–127 in 400/400 draws | ≤ 1 vote; exact EV | **Pass** |
   91| | B1 | Holdout two-party RMSE | backbone 7.55; uniform swing 8.68; persistence 17.41; demographic 7.62 | ≤ uniform swing and persistence | **Pass** |
   92| | B2 | Holdout turnout RMSE | backbone 2.92; persistence 16.46 | ≤ persistence | **Pass** (after a bug fix: see deviation 1) |
   93| | B3 | Holdout Spearman | 0.923 | ≥ 0.8 | **Pass** |
   94| | B4 | Holdout Brier | backbone 0.052; uniform swing 0.069 | ≤ uniform swing | **Pass** |
   95| | B5 | Holdout EV error | 12 (predicted 160, actual 148; NC called for Harding: 55.1% predicted, 43.3% actual) | ≤ 0 (no holdout state was decided by < 5 points) | **Fail** |
   96| | N1 | Women's turnout vs Corder–Wolbrecht | MAE 3.3 points; 3 of 5 inside the 90% interval | MAE ≤ 8 and ≥ 70% inside | **Fail** (coverage 60%) |
   97| | N2 | Placebo, GA and MS | GA 2.1% (−1.8 to 5.5); MS 3.5% (−0.2 to 6.3) | within ±5 points of 0 | **Pass** |
   98| | N3 | Agents' stated women's turnout vs Corder–Wolbrecht | MAE 15.5 points (11 women agents in 5 states) | ≤ 10 | **Fail** |
   99| | L1 | Recall probe | year 100%; candidates 100%; winner 100% (n = 56) | reported | 1920 is **memorization-exposed**, as expected |
  100| | L2 | Label swap | follows label 0%; follows platform 100% (n = 39) | < 20% | **Pass** |
  101| | A1 | Cohort bias | median \|bias\| 0.41 logit; 0 cohorts over 1 logit (after smoothing); mean TVD 0.43 | reported | See below |
  102| | A2 | Homogenization index | 0.90 (21 eligible cohorts) | ≤ 25% | **Fail** |
  103| | A3 (`league`) | Paraphrase and model sensitivity | effect −0.091; paraphrase SD 0.054; Sonnet −0.18 vs Opus −0.03 (shared subsample) | SD < \|effect\|; signs agree | **Pass** (the models agree on sign, not size) |
  104| | A3 (franchise) | same | no Opus arm for backbone-mode what-ifs | — | Not run (not applicable: these effects aren't applied) |
  105| | A4 | Stereotype audit | 0 of 66 reasons flagged by the heuristic | ≤ 10% | **Pass** (heuristic only; not read by a person) |
  106| 
  107| **Score:** 9 passed, 4 failed (B5, N1, N3, A2); L1 and A1 are report-only.
  108| 
  109| ### N1 detail
  110| 
  111| Women's turnout, as a share of all women 21+ (Corder–Wolbrecht's
  112| denominator):
  113| 
  114| | State | Backbone (90% interval) | Corder–Wolbrecht (95% interval) | Method |
  115| |---|---|---|---|
  116| | CT | 36.7 (32.7–41.4) | 32.6 (28.1–35.9) | residual |
  117| | IL | 46.3 (33.1–55.5) | 45.6 (44.3–46.8) | ratio (IL women voted in 1916) |
  118| | MA | 39.3 (34.6–44.1) | 33.6 (32.2–34.9) | residual |
  119| | MI | 37.2 (32.0–43.2) | 40.6 (38.5–42.4) | residual |
  120| | NY | 37.7 (33.1–42.7) | 35.2 (33.8–36.3) | residual |
  121| 
  122| - **The residual method runs high in the East.** κ, the men's-turnout change
  123|   from 1916 to 1920, comes from the western "old" states, where turnout per
  124|   eligible adult fell 0.31 logit. If men's turnout fell further in the East,
  125|   the residual hands too many votes to women.
  126| - **This is the key identifying assumption, and N1 is where it shows.** The
  127|   fix is to estimate κ with regional variation, with county returns: the
  128|   Corder–Wolbrecht approach.
  129| 
  130| ## Leakage
  131| 
  132| - **Probes (L1).** A separate instance, given the blinded brief, named 1920,
  133|   Cox for the administration's party, Harding for the other, and Harding as
  134|   the winner in 56 of 56 probes.
  135|   - Blinding does not hide 1920 from a current model, and no current model
  136|     will be clean for 1920.
  137|   - Every quote is therefore flagged `memorizationExposed: true`, and cohort
  138|     bias uses the national bias (the rule in `paired.py`).
  139| - **Label swap (L2).** In all 39 usable pairs, the agent followed the platform
  140|   to its new label. Answers track positions, not letters.
  141| - **De-blinding in the voice.** 98 of 386 voter answers (25%) name a party
  142|   ("I'll vote Republican", "the Lincoln ticket") that no brief ever named.
  143|   - None names a candidate.
  144|   - None uses hindsight language ("landslide", "will win").
  145|   - Quotes are published with `namesRestored: true`. A party name in a quote
  146|     is the model's own inference, now documented.
  147| - **Dates.**
  148|   - Every source item is dated 1920-06-01 to 1920-11-01.
  149|   - p1 briefs were dated 30 October but could include items from 31 October
  150|     and 1 November (deviation 11). A subagent noticed one and didn't use it.
  151| 
  152| ## Agent layer, beyond the thresholds
  153| 
  154| - **Turnout overstatement.** Agents' stated turnout exceeds the backbone's
  155|   calibrated turnout by 11.8 points on average.
  156|   - Northeastern native men: 0.76 vs 0.60.
  157|   - Southern white men: 0.61 vs 0.36.
  158|   - Figures are half-count smoothed (deviation 8).
  159| 
  160|   This is the survey self-report bias in a new form. It's harmless here,
  161|   because levels come from the backbone, but it's why agents must never set
  162|   levels.
  163| - **Cohort bias (A1).** Agents' Republican two-party share is within ±0.5
  164|   logit of the backbone for most white cohorts.
  165| 
  166|   | Cohort | Bias (logit) |
  167|   |---|---|
  168|   | border:F:black | +0.92 |
  169|   | south:F:black | −0.86 |
  170|   | south:M:native_white | −0.76 |
  171|   | south:M:black | −0.61 |
  172| 
  173|   - Before half-count smoothing (see deviation 8), Black cohorts outside the
  174|     South ran +0.8 to +1.6. The agents say "strongly Republican", which fits
  175|     the documented history better than the backbone's weakly identified β_B.
  176|     See the next section.
  177|   - Southern white men: agents 23% Republican (smoothed) vs backbone 39%. The agents
  178|     voice the Solid South; the backbone averages in Tennessee and North
  179|     Carolina, where Harding took about 43% or more.
  180| - **Homogenization (A2).** In 19 of 21 cohorts whose backbone share lies
  181|   between 0.2 and 0.8, every agent gave the same choice. With four agents at
  182|   a 60/40 split, chance unanimity is about 15%, so this is strong variance
  183|   compression. The Bisbee et al. failure is present. Persona diversity at
  184|   four agents per cohort didn't fix it, and Sonnet 5.5 has no temperature
  185|   lever.
  186|   - Consequences for this design: the agents' choices are not usable as
  187|     distributions. Their *paired changes* can still be. Production should
  188|     ask for `p_choice` (done), weight by it rather than by the discrete
  189|     choice (done), and raise agents per cohort to 12 or more to measure
  190|     compression properly.
  191| - **Paired effect, `league`.**
  192|   - The national two-party effect is −0.091 logit, 80% interval −0.129 to
  193|     −0.047, adult-weighted.
  194|   - Cohort effects run from −0.24 (naturalized men in the Northeast) to +0.13
  195|     (Southern white men).
  196|   - The shrinkage weights are 0.33–0.43, because four or five agents per
  197|     cohort is small against the shrinkage pseudo-count of 8. Every
  198|     cohort's effect is therefore pulled strongly toward its region.
  199| - **Cross-checks on the franchise what-ifs.** These are not applied.
  200|   - In `fifteenth`, Black Southern agents who could now register raised their
  201|     stated turnout sharply: +0.93 logit nationally for the reached cohorts.
  202|     Their quotes back the borrowed assumption: "I'm registered. I'll vote
  203|     Republican Tuesday, same as my people."
  204|   - In `no-19th`, women who lost the vote said so. The men asked showed a
  205|     small shift toward Cox (−0.12 logit), which the backbone ignores by
  206|     design.
  207| 
  208| ## The biggest uncertainty: how Black voters split
  209| 
  210| - **The data can't pin β_B.** Across the 37 states outside the South, a
  211|   Goodman regression puts Black voters' shift toward Harding at −3.4 ± 1.9
  212|   logit (region intercepts, 1916 lag). That runs against the documented
  213|   history, and it is carried by six border states with larger Black shares
  214|   and smaller swings.
  215| - **What the published run uses.** The prior, N(1.5, 1),
  216|   updated by that regression, gives a median of 0.50 (80% interval −0.70 to
  217|   1.68).
  218| - **The sensitivity**, same seed:
  219| 
  220| | β_B from | Black voters outside the South, Harding share | `fifteenth` Harding EV (80% range) | P(flip) > 10% |
  221| |---|---|---|---|
  222| | Prior updated by Goodman (published) | 73% (48–88%) | 416 (404–475) | NC 0.51, AR 0.29, VA 0.20, AL 0.19, FL 0.16, LA 0.16 |
  223| | Prior only, N(1.5, 1) | 88% (67–96%) | 449 (404–489) | NC 0.82, AR 0.66, VA 0.55, AL 0.52, LA 0.48, FL 0.47, GA 0.35, MS 0.34 |
  224| 
  225| - **Which is closer to history?** The prior-only row encodes the
  226|   documented loyalty of Black voters to the Republican party before 1932. The
  227|   published row lets the confounded regression pull it down.
  228| - **What would settle it:** county returns against county composition (NHGIS,
  229|   needs registration), or a documented estimate of Black voters' choice in
  230|   1920 from the literature (not found by the research agents).
  231| 
  232| The page should present `fifteenth` with its range, as the bundle does:
  233| "Harding carries 404–475". The flips in AR, VA, AL, FL and LA are live
  234| possibilities, not results.
  235| 
  236| ## Uncertainty budget
  237| 
  238| These are standard deviations across draws.
  239| 
  240| | What-if | National R two-party (points), full | Backbone parameters only (population noise off) | Agents only (one backbone draw) | Harding EV SD, full / params only |
  241| |---|---|---|---|---|
  242| | `no-19th` | 0.48 | 0.51 | — | 6.6 / 7.0 |
  243| | `fifteenth` | 0.55 | 0.56 | — | 27.4 / 22.9 |
  244| | `league` | 0.78 | 0.78 | 0.79 | 6.6 / 6.5 |
  245| 
  246| **How to read this:**
  247| - **Population noise is a small part of every what-if.** Turning it off
  248|   barely changes the spread, and the full-draw SD for `fifteenth`'s EV
  249|   (27.4) exceeds the params-only SD (22.9) only by what the flip-prone
  250|   Southern states add.
  251| - **For `league`, almost all the spread comes from the agent layer.** The
  252|   calibrated baseline has no national spread, so only the agent bootstrap
  253|   varies.
  254| - **For `fifteenth`, β_B dominates.**
  255| 
  256| ## Deviations from the plan, in order
  257| 
  258| Each change was made after seeing the output it fixes. Each is listed with
  259| its effect. None changes a threshold.
  260| 
  261| 1. **B2 predictor bug.** The holdout turnout predictor counted old-suffrage
  262|    states' 1916 votes, which included women's, as men's.
  263|    - First value: 16.90 (fail).
  264|    - Fixed to project turnout per eligible adult by κ, as the backbone does:
  265|      2.92 (pass).
  266|    - Both values are reported here.
  267| 2. **N1 denominator.** Corder–Wolbrecht's "eligible" counts equal the census
  268|    21+ totals, non-citizens included. The backbone had divided by citizens.
  269|    - Citizen-denominator result: MAE 9.6, coverage 40%.
  270|    - Like-for-like result: MAE 3.3, coverage 60%.
  271|    - Fail either way.
  272| 3. **β_B specification.**
  273|    - The first fit's Goodman regression (intercept, lag) gave β_B = −1.5
  274|      after the prior, driven by region.
  275|    - Changed to region intercepts: 0.50 after the prior.
  276|    - The sensitivity table above covers the choice.
  277| 4. **Black Southern turnout.** The first fit clipped a negative Goodman
  278|    estimate to 0 in every draw. Changed to the regression posterior truncated
  279|    to [0, white rate], which is Goodman with Duncan–Davis bounds: median 9%
  280|    of the white rate (1–25%).
  281| 5. **Black Southern choice.** The first fit gave Black Southern voters a
  282|    shift relative to white Southerners, which made them lean Cox, against the
  283|    `fifteenth` assumption.
  284|    - Changed to the borrowed Northern split, with an accounting bound: their
  285|      votes for either party are at most 80% of its certified vote.
  286|    - The bound binds in South Carolina (70% of draws) and Mississippi (18%).
  287| 6. **Sex turnout cap.** R1 first failed in Utah in 4 of 400 draws: a drawn
  288|    men/women ratio implied men's turnout above 100%. Each sex is now capped at
  289|    98%, and the excess moves to the other sex, so state totals stay exact.
  290| 7. **Minor-party ledger.** R1 failed again after deviation 5: in NC and GA,
  291|    whose certified minor-party vote is 0, the borrowed Black split carried a
  292|    minor-party share. Fixed; R1 passes.
  293| 8. **Paired smoothing.** Cohorts whose agents all said "won't vote" produced
  294|    effects of −10 logit. A half-count (Jeffreys-style) smoothing was added,
  295|    and the national effect is now adult-weighted.
  296| 9. **A1 denominator.** Backbone turnout for A1 is now per legally eligible
  297|    adult (exclusion included), matching what an agent's `p_vote` means.
  298| 10. **The agents were answered by Claude Code subagents, not the Messages
  299|     API.**
  300|     - No `ANTHROPIC_API_KEY` was available. Credential exploration was
  301|       declined, correctly.
  302|     - The 442 requests went through the `transcript` backend to 9
  303|       subagents: 7 Sonnet and 2 Opus, via the Agent tool's `model`
  304|       setting. The exact model versions behind those settings aren't
  305|       recorded by the tool.
  306|     - Each subagent answered 18–59 requests in one context. No subagent saw
  307|       both arms of the same person.
  308|     - The subagents' own reports:
  309|       - The probe subagent answered 28 of 56 probes by script, having read
  310|         the first 28. All 56 name Harding.
  311|       - The control-sonnet-2 subagent built answers with a helper script.
  312|         All 56 reasons and quotes are distinct.
  313|       - The control-sonnet-1 subagent says its later answers are shorter and
  314|         more generic. Its quotes fall from 26 to 16 words.
  315|     - This is a weaker instrument than independent API calls. The
  316|       homogenization in A2 may be partly an artifact of batching.
  317|     - **The production path is `anthropic-batch`**, and this pilot should be
  318|       rerun on it before any agent-layer number is cited.
  319| 11. **p1 prompt bugs,** found after the answers came back and fixed in p2.
  320|     The p1 requests that were answered are unchanged on disk.
  321|     - Non-citizen women were given the `no-19th` counterfactual, and their
  322|       brief contradicted itself. Two subagents flagged it. Those pairs are
  323|       excluded from the analysis.
  324|     - Briefs were dated 30 October while admitting items dated up to
  325|       1 November.
  326|     - Surnames were drawn from one mixed list ("Mary Lindqvist", a Black
  327|       North Carolina woman).
  328|     - Before any answer, the Ohio line "women have voted for president since
  329|       1917" was corrected: no presidential election fell in 1917–19.
  330| 
  331| ## What wasn't done
  332| 
  333| - **County-level ecological inference.** County returns are cached; county
  334|   composition needs NHGIS registration.
  335| - **Strict mode.** The 1910 census would be aged ten years.
  336| - **Other holdouts.** The 26th Amendment, VRA and Amendment 4 holdouts are
  337|   designed but not run.
  338| - **Population what-ifs.** Huntington–Hill and Webster are implemented and
  339|   unit-tested, but not exercised.
  340| - **Reading the stereotype audit.** A4 used the regex pass only.
  341| - **Alien declarant voting in 1920.** Not coded in any dataset found; treated
  342|   as barred everywhere.
```

## `LICENSE`

```
    1| MIT License
    2| 
    3| Copyright (c) 2026 Partyhat
    4| 
    5| Permission is hereby granted, free of charge, to any person obtaining a copy
    6| of this software and associated documentation files (the "Software"), to deal
    7| in the Software without restriction, including without limitation the rights
    8| to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    9| copies of the Software, and to permit persons to whom the Software is
   10| furnished to do so, subject to the following conditions:
   11| 
   12| The above copyright notice and this permission notice shall be included in all
   13| copies or substantial portions of the Software.
   14| 
   15| THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   16| IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   17| FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   18| AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   19| LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   20| OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   21| SOFTWARE.
```

## `METHOD.md`

```markdown
    1| # Simulacra Americana: how the harness works
    2| 
    3| This covers the harness behind `/api/simulacra`.
    4| 
    5| - **This document:** every assumption, data source, equation and limitation,
    6|   plus the confidence tier for each kind of what-if.
    7| - **`EVAL.md`:** what the 1920 prototype got right and wrong.
    8| - **`DISCLOSURES.md`:** every known flaw, by ID.
    9| 
   10| Sections A–F describe 1920, the year the method was built on. B.4 says how
   11| the other 59 elections are fitted.
   12| 
   13| Tags follow the research package:
   14| - **[V]** verified by download or fetched page
   15| - **[S]** snippet or secondary
   16| - **[I]** inference or assumption
   17| 
   18| ## 0. The one design decision
   19| 
   20| **The counts come from a statistical model, and the language model is only the
   21| voice.**
   22| 
   23| - **The backbone decides every number the page shows.** It is a calibrated
   24|   statistical model of who could vote, who turned out and how they chose.
   25| - **Every draw of the backbone reproduces each state's certified 1920 result
   26|   exactly** (product promise 1).
   27| - **The LLM agents do three jobs:**
   28|   1. They supply the *response* to an issue what-if, as a within-agent paired
   29|      difference.
   30|   2. They supply the quotes.
   31|   3. They cross-check the franchise what-ifs.
   32| 
   33|   They never supply a level: a count, a turnout rate or a vote share.
   34| 
   35| This matches what Aaru describes publicly: population and aggregate models
   36| that are not language models, with LLMs as the reasoning and voice layer. It
   37| goes further in two places:
   38| - held-out tests with pass/fail thresholds
   39| - error bars on every result
   40| 
   41| ```
   42| census tables ──► cells (state × sex × race/nativity/citizenship) ──► franchise rules ──► who can vote
   43|                                    │
   44| certified returns 1916, 1920 ──► backbone (turnout, choice; exact calibration; 400 posterior draws)
   45|                                    │
   46|                     ┌──────────────┼───────────────────────────┐
   47|              franchise what-if   issue what-if             population what-if
   48|              (backbone only:     (agents: control vs       (backbone + reapportion
   49|               borrow a named      counterfactual, paired    from the counterfactual
   50|               observed group)     difference, shrunk)       census)
   51|                     └──────────────┼───────────────────────────┘
   52|                                    ▼
   53|                   draws → states, EV, ranges, "wins in n of D draws"
   54|                                    ▼
   55|                   the bundle's result shape (serialize.py) ◄── quotes (selected, grounded, cited)
   56| ```
   57| 
   58| ## A. Population
   59| 
   60| ### A.1 Sources, 1920
   61| 
   62| **Adults 21+ by state × sex × race/nativity/citizenship.**
   63| - The 1920 census (Fourteenth Census): the published "voting age" tables by
   64|   colour, nativity and citizenship [V]. See the
   65|   `harness_cache/population/PROVENANCE-population.md` for the pages and the
   66|   checks.
   67| - This is the published joint distribution of exactly the dimensions the 1920
   68|   franchise turned on.
   69| - The 1920 census was enumerated on 1 January 1920 and published in 1921–23,
   70|   after the election. That makes it **truth mode**.
   71|   - Strict mode would use the 1910 tables aged ten years (`extracts/`). It is
   72|     designed but not run.
   73| 
   74| **1916 adults.**
   75| - Geometric interpolation of each cell between the 1910 and 1920 counts, to
   76|   7 November 1916.
   77| - The 1920 counts are extrapolated to 2 November 1920 by the same rate.
   78| - Interpolation between bracketing censuses is truth mode only; strict mode
   79|   forbids it (toy_dataset_recipe §5.2).
   80| 
   81| **Urban share by state.** Used only for persona diversity.
   82| 
   83| ### A.2 Cohorts
   84| 
   85| **Cells:** state (48) × sex × {native-born white, naturalized white, white
   86| non-citizen (alien or first papers), Black, American Indian and Asian}.
   87| 
   88| **Why these dimensions in 1920:**
   89| 1. **Sex.** The 19th Amendment was the franchise shift of the year. Where women
   90|    voted, they turned out at different rates from men, and possibly chose
   91|    differently.
   92| 2. **Citizenship.** Non-citizens were barred almost everywhere. Naturalized
   93|    voters were a distinct constituency.
   94| 3. **Race.** Black Southerners were kept from voting in practice, and Black
   95|    voters elsewhere were a distinct, strongly Republican constituency.
   96| 4. **Region.** Region carried the parties' coalitions: the Solid South, the
   97|    Republican North and the progressive West.
   98| 
   99| **Why not age or urban/rural.** Age, urban/rural and occupation vary within a
  100| cohort's agents but don't define cohorts. No 1920 source identifies their
  101| effect on turnout or choice, and a cohort nobody can calibrate adds cost and
  102| no information.
  103| 
  104| **Agent cohorts** are region (5) × sex × group, merged to a cap of 36:
  105| - **The merge rule** (`cohorts.py`): fold the smallest cohort into the same
  106|   sex and group in the nearest region.
  107| - The rule is deterministic, and the merged cohort's key names every region it
  108|   holds.
  109| - American Indian and Asian adults are too few per region to interview. They
  110|   are counted by the backbone and have no agents.
  111| 
  112| ### A.3 Eligibility
  113| 
  114| Every adult is a cell member. Nobody is dropped. Each cell has:
  115| - a legally barred fraction, with a reason code;
  116| - a practically excluded fraction, with a reason code.
  117| 
  118| | Reason | Rule, 1920 | Source |
  119| |---|---|---|
  120| | `noncitizen` | Aliens and first-paper declarants can't vote | Census citizenship tables [V]. Alien suffrage by state is **not coded** in the data. The harness assumes no state allowed declarant voting in November 1920 [I]. See the limitations. |
  121| | `sex` | Only in the `no-19th` what-if, and only where the state had no presidential suffrage of its own | Teele (Keyssar tables) [V] |
  122| | `registration_closed` | Georgia and Mississippi women couldn't register in time for November 1920 | NPS state pages, cited in `franchise/state_franchise_1920.csv` [V] |
  123| | `native_status` | American Indian and Asian adults not counted as citizens | The census table where given; otherwise treated as eligible [I] |
  124| | `extralegal_exclusion` (additive to the recipe's 13 codes) | Black Southerners kept from voting by poll taxes, literacy and "understanding" tests, white primaries and violence | Estimated. See B.1, T4. The legal devices by state come from Gray–Jenkins (`poll_tax`, `literacy_test`) [V]. |
  125| 
  126| Poll taxes also kept poor white Southerners from voting. The data can't
  127| separate that from abstention, so for white Southerners it is counted as
  128| "home", not "barred" (limitation 4).
  129| 
  130| ### A.4 Uncertainty in the population
  131| 
  132| Each draw multiplies every cell by lognormal noise, standing in for census
  133| undercount and interpolation error [I]. The coefficients of variation are
  134| assumptions, not estimates:
  135| 
  136| | Group | CV |
  137| |---|---|
  138| | Native white | 2% |
  139| | Naturalized | 4% |
  140| | Non-citizen | 5% |
  141| | Black | 5% |
  142| | American Indian and Asian | 8% |
  143| | 1916 interpolation (additional) | 2% |
  144| 
  145| The full-count path (`extracts/ipums-1920-fullcount.json`) replaces this with
  146| bootstrap draws of the microdata tabulation.
  147| 
  148| ## B. The backbone
  149| 
  150| ### B.1 Turnout
  151| 
  152| For draw d, "adults" means legally eligible adults.
  153| 
  154| - **T1: the men's-turnout change, κ.** In the 12 "old" states (AZ CA CO ID IL
  155|   KS MT NV OR UT WA WY), women could already vote for president in 1916 [V], so
  156|   the legal electorate's makeup didn't change between 1916 and 1920. The
  157|   change there is
  158| 
  159|   `k_s = logit(T20/E20) − logit(T16/E16)`
  160| 
  161|   κ is drawn from the predictive distribution: the mean across old states,
  162|   plus the between-state spread.
  163| - **T2: new states.** In the other 36, men's 1920 turnout is
  164| 
  165|   `m20 = expit(logit(T16 / M16) + κ)`
  166| 
  167|   Women's votes are the residual, `W = T20 − m20·M20`, and women's turnout is
  168|   `w = W / F20`. This is the 1916 → 1920 natural experiment written as a
  169|   model. Negative residuals are floored at zero and counted (diagnostic
  170|   `women_negative_share`).
  171| - **T3: old states.** Men and women are split with a ratio w/m drawn from the
  172|   new states outside the South. There is no within-state evidence for it [I].
  173| - **T4: Black Southerners.**
  174|   - Run a Goodman regression of 1916 men's turnout on the Black share of
  175|     eligible men across the eleven former Confederate states.
  176|   - The implied Black rate is drawn from the regression posterior truncated
  177|     to [0, white rate] (Goodman with Duncan–Davis bounds). The unbounded
  178|     estimate is −0.18 ± 0.15.
  179|   - The Black rate relative to the white rate is `t_rel`: median 0.09, 80%
  180|     interval 0.01–0.25.
  181|   - The fraction `1 − t_rel` of Black Southern adults is counted as excluded
  182|     (`extralegal_exclusion`). The rest turn out at the white rate of their own
  183|     state and sex.
  184| - **T5: calibration.** A shift per state and sex makes the state's total votes
  185|   match certified returns exactly.
  186|   - Neither sex's turnout may exceed 98%; any excess moves to the other sex,
  187|     so the state total holds.
  188|   - Found when Utah failed R1 in 4 of 400 draws.
  189| 
  190| **Assumptions named here:**
  191| 1. Men's turnout changed from 1916 to 1920 by the same logit amount in new
  192|    states as in old ones, give or take the old states' spread [I]. This is the
  193|    key identifying assumption.
  194| 2. Within a state and sex, native-born, naturalized and Black voters outside
  195|    the South turn out at the same rate [I].
  196| 3. Old states' women vote at the same ratio to men as women in new
  197|    non-Southern states [I].
  198| 
  199| ### B.2 Choice
  200| 
  201| - **C1: women's tilt, δ.** A regression across all 48 states of the change in
  202|   logit Republican two-party share, 1916 → 1920, on f, the share of each
  203|   state's 1920 votes cast by newly enfranchised women. It has South and
  204|   non-South intercepts. It is re-fitted in every draw, because f depends on
  205|   the turnout draw. δ is women's logit shift toward Harding relative to men of
  206|   the same state (first-order).
  207| - **C2: Black voters' shift, β_B.** This is the logit shift toward the
  208|   Republicans relative to white voters of the same state.
  209|   - Prior: N(1.5, 1.0) [I]. The literature documents Black voters' loyalty to
  210|     the Republican party before 1932; the prior's size is an assumption.
  211|   - The prior is updated by a Goodman regression across non-Southern states.
  212|     The regression has **region intercepts** (Northeast, Midwest, West,
  213|     Border) and the 1916 share.
  214|   - The region intercepts were added after the first fit, whose single
  215|     intercept let border-state swings stand in for race (β_B = −1.5; EVAL.md,
  216|     deviation 3).
  217|   - Posterior median 0.50 (80% interval −0.70 to 1.68). The state returns
  218|     barely identify it, and it is the prototype's largest uncertainty (EVAL.md
  219|     reports the sensitivity).
  220| - **C3: calibration.** Per state, a Republican intercept and an "other"
  221|   intercept are solved by iterative scaling. Each state's R, D and other votes
  222|   then match the certified returns to within 1e-7 of the vote.
  223| - **C3b: Black Southern voters.** They split like Black voters outside the
  224|   South: the same borrowed group `fifteenth` uses. The split is limited to
  225|   parties on the state's certified ledger.
  226|   - **Accounting bound.** Their votes for either party may not exceed 80% of
  227|     that party's certified vote in the state.
  228|   - Where the bound binds, their turnout is lowered, the difference is
  229|     counted as exclusion, and the state's other voters of the same sex make up
  230|     the total.
  231|   - The rest of the state is then recalibrated.
  232|   - The bound binds in South Carolina in 70% of draws (Harding got 2,610
  233|     votes there) and in Mississippi in 18%.
  234| - Naturalized voters' choice isn't separately identified in 1920. They share
  235|   their state's intercept [I].
  236| 
  237| ### B.3 Why these are the right tools for 1920
  238| 
  239| There is no survey before 1936, so MRP isn't available. The design follows the
  240| recipe's rule for pre-survey elections: hierarchical ecological inference on
  241| returns against census makeup, post-stratified exactly.
  242| 
  243| - **County EI (King's EI or a hierarchical model) is the next step.** It needs
  244|   1920 county composition from NHGIS, which requires registration.
  245| - **The state-level version here is honest about its identification:**
  246|   - Every between-group difference is either identified by the 1916 → 1920
  247|     change or labelled as an assumption.
  248|   - Draws carry the uncertainty.
  249| 
  250| ### B.4 Other years
  251| 
  252| - **1924** carries 1920's fit forward (`backbone.carry_forward`): 1920's
  253|   per-cell turnout, δ, β_B and Black Southern exclusion, one turnout shift
  254|   per state, and the same exact calibration (DISCLOSURES C13–C16).
  255| - **Every year outside 1916–1924** is fitted by `backbone.general_fit`. It
  256|   has no natural experiment: each group's turnout gap and partisan tilt is an
  257|   era prior from the literature [I], not updated from the data, and exact
  258|   calibration to the state returns does the rest (DISCLOSURES B10–B13).
  259| - **Not built:** MRP on Gallup and Roper (1936–47) and on ANES and CPS (1948
  260|   on), post-stratified exactly to certified state returns. The surveys would
  261|   replace the priors for those years.
  262| 
  263| ## C. The agents
  264| 
  265| ### C.1 Persona
  266| 
  267| An agent carries:
  268| - its cohort's real attributes: state, sex, race/nativity/citizenship;
  269| - an age and urban/rural status drawn within the cohort;
  270| - a household economy [I] (persona diversity only);
  271| - its legal and practical eligibility, stated in plain words;
  272| - two to four dated items from the corpus, preferring its own state.
  273| 
  274| The person is invented and the circumstances are documented. Names come from a
  275| plain list and carry no information.
  276| 
  277| ### C.2 The control question (leakage-controlled)
  278| 
  279| - **Blinding.**
  280|   - Candidates are neutral letters (K M N P T V: no candidate's or party's
  281|     initial), assigned at random per agent, in random display order.
  282|   - Party *positions* and the circumstances of the day stay:
  283|     - "the party that has held a majority in Congress since the 1918 elections"
  284|     - "the party of the administration in office since 1913"
  285|     - platform planks paraphrased from the 1920 platforms (APP) [V]
  286|   - Items that name a candidate or party are excluded from the brief.
  287| - **Cutoff.** Every item is dated on or before 1 November 1920 (Chronicling
  288|   America, date-filtered). The brief is dated Saturday, 30 October 1920. Every
  289|   answer records its context date and the ids of the items it saw.
  290| - **The prompt says:** the person "does not know anything that happens after
  291|   [the date], including how any election turns out".
  292| - **Recall probe (L1).** A separate instance, a different system prompt and
  293|   the same brief. It asks for the year, the real candidates behind the labels,
  294|   and the winner.
  295|   - If more than half the probes in a cohort name the winner, the cohort is
  296|     "memorization-exposed". Its control answers are left out of its own bias
  297|     estimate, and its quotes carry the flag.
  298| - **Label swap (L2).** The same agent's brief is repeated with:
  299|   - the two platforms attached to the opposite labels;
  300|   - the display order flipped.
  301| 
  302|   If the choice follows the label rather than the platform, the answer is
  303|   tracking something other than the positions.
  304| 
  305| Blinding can't stop a model from knowing 1920. The paired design is what makes
  306| that tolerable: a constant "I know who won" bias cancels in the control-minus-
  307| counterfactual difference, and the probe measures how much there is.
  308| 
  309| ### C.3 The counterfactual (non-hypothetical)
  310| 
  311| The counterfactual brief is the control brief with one settled fact changed:
  312| - The change is written into the person's world as fact: "In March 1920 the
  313|   Senate ratified the peace treaty with its reservations…". It is never framed
  314|   as a question or a supposition.
  315| - Anything it would contradict is removed:
  316|   - dated items about the treaty fight;
  317|   - both parties' League planks;
  318|   - for women in a no-19th world, items about registering after 18 August.
  319| - Everything else is identical: persona, labels, order, paraphrase, model and
  320|   seed.
  321| - The exact change is logged in the request's `meta.change` for audit, and
  322|   never shown to the model as a change:
  323|   - the what-if key
  324|   - the facts
  325|   - the eligibility line
  326|   - the dropped sources and planks
  327| 
  328| **Causal consistency** is handled by `whatifs.facts_*`:
  329| - The world facts are written to be internally consistent.
  330| - The `fifteenth` world names a mechanism: a Supreme Court ruling plus federal
  331|   registrars. It is invented, and it is marked counterfactual in the log.
  332| 
  333| ### C.4 From answers to counts
  334| 
  335| For cohort k, both arms are answered by the same agents. The change is taken
  336| on the logit scale.
  337| 
  338| - **Turnout:** `Δt_k = logit(E[p_vote] cf) − logit(E[p_vote] control)`
  339| - **Two-party share:** `Δr_k = logit(R2 cf) − logit(R2 control)`, where
  340|   `R2 = Σ p_vote·p_R / Σ p_vote·(p_R+p_D)`
  341| - **Minor parties:** `Δo_k`, likewise.
  342| - **Bias:** `b_k = logit(R2 control) − logit(r_k backbone)`
  343| 
  344| **Smoothing.** Cohort means are half-count smoothed (Jeffreys-style) before
  345| the logit, so a cohort whose agents all say "won't vote" can't produce an
  346| infinite difference. This was added after the first analysis showed −10 logit
  347| artifacts.
  348| 
  349| **The national effect** is the adult-weighted mean of cohort effects.
  350| 
  351| **Shrinkage**: `w_k = n/(n+8) · 1/(1+b²)`. The effect is
  352| shrunk toward the regional effect, and the regional effect toward the national
  353| effect, in the same way.
  354| 
  355| **Uncertainty:** the cohort effect's draws come from bootstrapping agents
  356| within the cohort, which carries paraphrase and model variation because they
  357| are mixed in the sample.
  358| 
  359| **Applying the effect:** `logit t' = logit t + Δt*`, `logit R2' = logit R2 + Δr*`
  360| and `logit O' = logit O + Δo*`, applied cell by cell to the calibrated
  361| baseline in every draw.
  362| 
  363| **Franchise what-ifs** use no agent effect. The backbone computes them, and new
  364| voters borrow a named, observed group:
  365| - `fifteenth`: turnout like white Southerners of the same state and sex, and
  366|   choice like Black voters outside the South, per draw.
  367| - `everyone`: non-citizens choose like naturalized citizens of the same state
  368|   and sex.
  369| 
  370| Agent answers for these what-ifs are cross-checks and quotes only.
  371| 
  372| ### C.5 Known LLM failure modes
  373| 
  374| | Failure | Measured by | Corrected by |
  375| |---|---|---|
  376| | Variance compression and homogenized subgroups (Bisbee et al.) | A2: within-cohort SD of stated Republican probability; the homogenization index | Persona diversity within the cohort. Sonnet 5.5 rejects non-default temperature, so temperature isn't a lever. Levels never come from agents. |
  377| | Ideological drift and left bias (Santurkar et al.; Parikh, Cen & Podimata 2026) | A1: control vs calibrated backbone, per cohort | The paired difference cancels the common part; shrinkage by \|b_k\| |
  378| | Prompt sensitivity | A3: three paraphrases rotated across agents; Opus 5.5 on a 20% subsample | Spread reported; effect draws pool paraphrases and models |
  379| | Stereotype voting | A4: audit of reasons for label-driven logic (heuristic first pass, then read) | Persona lines state circumstances, not traits; the system prompt forbids answering "as a type" |
  380| | Memorization | L1, L2 | Paired difference; exposure flags on quotes |
  381| 
  382| ## D. Uncertainty
  383| 
  384| A draw is:
  385| 1. a population draw (A.4);
  386| 2. a backbone parameter draw: κ, the old-state ratio, t_rel, δ, β_B and
  387|    residual noise;
  388| 3. for issue what-ifs, an agent-bootstrap draw, which mixes paraphrases and
  389|    models.
  390| 
  391| There are 400 draws per run. Reported:
  392| - `result.range`: the central 80% of each candidate's EV.
  393| - `result.drawsWon`: "Cox wins in 3 of 400 draws".
  394| - `states[].marginRange` and `states[].pFlip`.
  395| - popular vote point and range.
  396| 
  397| The unchanged run is exact in every draw. Its range is a point, by
  398| construction.
  399| 
  400| **Uncertainty budget.** `EVAL.md` reports how much of the EV and margin
  401| spread each source contributes. It reruns with each source frozen:
  402| - population only
  403| - backbone parameters only
  404| - agents only
  405| 
  406| ## E. Validation
  407| 
  408| The metrics and thresholds are in `simharness/evaluate.py` and `benchmarks.py`;
  409| `EVAL.md` has the results.
  410| 
  411| - **R1:** exact reproduction.
  412| - **B1–B5:** 12 holdout states against persistence, uniform swing and a
  413|   demographic regression.
  414| - **N1–N3:** the 19th Amendment as a natural experiment, against
  415|   Corder–Wolbrecht's hierarchical EI of women's turnout in CT, IL, MA, MI and
  416|   NY. The benchmark is read only by `benchmarks.py`, and a test enforces that.
  417| - **L1–L2:** leakage.
  418| - **A1–A4:** agent-layer failure modes.
  419| 
  420| Failures are published in `result.validation`, in `EVAL.md` and here (§G).
  421| 
  422| ## F. Quotes
  423| 
  424| - **Selection** (`quotes.py`):
  425|   - A cohort is drawn in proportion to its adults.
  426|   - Within the cohort, the agent whose change is nearest the cohort median is
  427|     chosen.
  428|   - At least one person whose vote didn't change is shown across a run's
  429|     picks.
  430| - **Every quote carries:**
  431|   - its cohort and the adults it stands for
  432|   - both answers
  433|   - its context date
  434|   - the dated items it cites, with loc.gov URLs
  435|   - its model and prompt version
  436|   - whether it is memorization-exposed
  437|   - `namesRestored: true`: the interview was blinded, and "Candidate K" is
  438|     replaced with "Harding" afterwards
  439| - **Real people appear only as events.** Candidates are letters in the
  440|   interview, and briefs never have a real person speak.
  441| - **Tone** (the system prompt): plain period English, specific to the person's
  442|   circumstances, no slurs, no melodrama. Slavery, disenfranchisement and
  443|   violence are described plainly.
  444| 
  445| ## G. Confidence tiers, and what each kind of what-if rests on
  446| 
  447| | Kind | Tier | What it rests on | What could make it wrong |
  448| |---|---|---|---|
  449| | Franchise (who can vote) | High | Census counts; certified returns; one named borrowed group | The borrowed group's behaviour (T4, C2), i.e. `fifteenth` rests on β_B, whose prior dominates. `no-19th` rests on the women's-turnout split (N1 tests it). |
  450| | Population (who lives where) | Medium | Census counts moved between states; reapportionment (Huntington–Hill for the 1940s on; Webster, as used in 1911, for 1910s-style counts) | How movers would vote where they arrive. Not in the 1920 prototype. |
  451| | Issue (what people cared about), event, or candidate (who is on the ballot) | Low | Agent paired differences, shrunk by bias | Everything in C.5. In 1920, memorization. |
  452| 
  453| These are the base tiers by kind (`evidence.BASE_TIER`). Each what-if's tier
  454| is then adjusted by `evidence.confidence` for plausibility, evidence,
  455| agreement with the record, interview stability and the number of
  456| interviews, down to "very low" (DISCLOSURES H4).
  457| 
  458| ## H. Known limitations (read before citing)
  459| 
  460| 1. **State-level only.**
  461|    - There is no county composition without NHGIS registration.
  462|    - Between-group differences in choice are weakly identified (δ, β_B), and
  463|      their ranges are wide.
  464|    - County returns are in the cache and unused, except as labels.
  465| 2. **Alien suffrage in 1920 isn't coded.** Declarant aliens are treated as
  466|    barred everywhere. Keyssar's Table A.12 would settle it.
  467| 3. **Old states' women** (T3) borrow a ratio from new states; no within-state
  468|    evidence.
  469| 4. **Poor white Southerners kept out by poll taxes** are counted as "home",
  470|    not "barred".
  471| 5. **Truth mode.**
  472|    - The 1920 census postdates the election.
  473|    - Strict mode (1910 aged) is designed, not run.
  474| 6. **1920 is memorized by every current model.** The control answers are
  475|    "memorization-exposed" if L1 says so. Only the paired difference is used.
  476| 7. **The prototype's agents were answered through the transcript backend,
  477|    by 9 Claude Code subagents**, not the Messages API:
  478|    - batched prompts, 18–59 per context;
  479|    - the Claude Code system prompt around them;
  480|    - schemas checked on merge, not enforced per request;
  481|    - some answers produced with helper scripts.
  482| 
  483|    `EVAL.md` (deviation 10) says which. The production path is
  484|    `anthropic-batch`, and the agent-layer numbers should be rerun there
  485|    before they are cited.
  486| 8. **The household economy is imputed** until the IPUMS full count is pulled.
  487| 9. **β_B**, how Black voters split, is barely identified from state returns.
  488|    It moves the `fifteenth` result from 416 to 449 Harding electoral votes
  489|    (EVAL.md).
```

## `README.md`

```markdown
    1| # Synthetic voters
    2| 
    3| Live at https://simulacraamericana.com
    4| 
    5| Developed in a private repository from September 2026; this is a snapshot of main as of 20 November 2026.
    6| 
    7| A page that replays American presidential elections and reruns them with one
    8| thing changed: who could vote, who lived where, what people cared about, or
    9| who was on the ballot.
   10| 
   11| Every election opens as it happened. A calibrated statistical backbone decides
   12| the counts and reproduces the certified returns. Synthetic voters, interviewed
   13| in both worlds, supply only within-person changes and the quotes. Every result
   14| carries a confidence tier, and `DISCLOSURES.md` records what is assumed rather
   15| than known.
   16| 
   17| Read `VALIDITY.md` for what the system can and cannot claim.
   18| 
   19| ## Layout
   20| 
   21| | Path | What |
   22| |---|---|
   23| | `src/` | The SvelteKit page (TypeScript, Svelte 5) and the robot narrator (`src/lib/robot`) |
   24| | `serve/` | The API server: serves the published per-year bundles under `/api/simulacra` |
   25| | `simharness/` | The simulation harness (Python): backbone, interviews, what-ifs, evaluation |
   26| | `tests/` | Harness tests (pytest). Page and server tests sit next to their code (vitest) |
   27| | `configs/`, `profiles/`, `whatifs/` | Run configs, per-election profiles, compiled what-ifs and their evidence |
   28| | `METHOD.md`, `EVAL.md` | How the backbone works, and the 1920 prototype's results, failures included |
   29| | `VALIDITY.md`, `DISCLOSURES.md` | What the system can claim, and the log of every known flaw |
   30| | `docs/harness/README.md` | Running the harness: stages, typed what-ifs, interview runs |
   31| 
   32| ## Run it
   33| 
   34| ```sh
   35| pnpm install
   36| pnpm serve          # API on :8787
   37| pnpm dev            # page on :5173, proxies /api to :8787
   38| ```
   39| 
   40| `?sample=1` runs the page on an invented stand-in model, with no server, and
   41| `?year=1896` opens a given year. `pnpm tsx scripts/model-check.ts` prints the
   42| stand-in model's outcome for every story what-if.
   43| 
   44| ## Checks
   45| 
   46| ```sh
   47| pnpm lint && pnpm check && pnpm size && pnpm test
   48| python -m pip install -e '.[test]' && python -m pytest -q
   49| ```
   50| 
   51| The rules every change follows are in `AGENTS.md`, and the vocabulary is in `CONTEXT.md`.
```

## `VALIDITY.md`

```markdown
    1| # Validity: goals, contamination, leakage and historical bias
    2| 
    3| This document takes stock of the Simulacra Americana harness:
    4| - what it is trying to do;
    5| - what is currently claimed;
    6| - what can and can't be known about whether those claims hold;
    7| - what would make them stronger.
    8| 
    9| It was written after the work that made typed what-ifs, historical evidence and 1924 run end to end; all 60 elections have since been built (§3). It complements:
   10| - `METHOD.md`: how the model works;
   11| - `EVAL.md`: the 1920 prototype's scores;
   12| - `DISCLOSURES.md`: the running log of every known flaw.
   13| 
   14| IDs in brackets (D21, C14, H4…) refer to `DISCLOSURES.md`.
   15| 
   16| ---
   17| 
   18| ## 1. The goal
   19| 
   20| A reader picks a past presidential election, changes one thing about it, and asks what would have happened. The harness should:
   21| 
   22| 1. **Model any change a reader can type,** however far-fetched.
   23| 2. **Ground every answer in the record.** Use real populations, real voting rules and real certified results. Use evidence of how the same people behaved in the same or similar situations.
   24| 3. **Say how much to trust the answer.** "Extremely low confidence, and here is why" is an acceptable answer. A confident wrong one is not.
   25| 
   26| The third goal is the hard one. Everything below is about whether the harness can honestly meet it.
   27| 
   28| ---
   29| 
   30| ## 2. What the system is
   31| 
   32| Two layers, plus an evidence step.
   33| 
   34| ### 2.1 The statistical layer (the backbone)
   35| 
   36| Each election is about 600 cells: state × sex × group (native-born white, naturalized, non-citizen immigrant, Black, American Indian and Asian). Each cell carries, for each of 100 posterior draws:
   37| 
   38| > adults × share who could vote × share who turned out × the split between candidates
   39| 
   40| It is built from four kinds of input:
   41| - **Census counts:** 1920 from the census volumes; other years from NHGIS (C17).
   42| - **Each state's voting rules:** Gray–Jenkins, Teele.
   43| - **Certified returns:** Algara–Amlani, Clerk of the House, NARA.
   44| - **A source of identification for group differences:** what lets the model tell how groups differed.
   45|   - **1920:** the 1916 → 1920 natural experiment. Women could already vote for president in some states in 1916 and not in others.
   46|   - **1924:** carries 1920's structure forward (C14).
   47|   - **Every other year:** none. Group differences are era priors from the literature, not estimated from the year's data (B10).
   48| 
   49| **Exact reproduction.** Every draw is calibrated so that the unchanged world reproduces each state's certified votes, to within half a vote:
   50| - 1920: worst error 0.32 votes, 404–127 in every draw;
   51| - 1924: worst error 0.41 votes, 382–136–13 in every draw.
   52| 
   53| Everything a what-if changes is therefore measured from the real result. The draws differ only in how a state's known total breaks down by group. That breakdown is inferred, and the uncertainty lives there.
   54| 
   55| **What exact reproduction proves: very little.** It is enforced by construction. A model could match Ohio exactly with a badly wrong split between men and women. Only checks the model never sees can test the splits (§4).
   56| 
   57| ### 2.2 The interview layer (the voters)
   58| 
   59| Invented people are drawn from documented groups, in proportion to real counts. Each gets a brief dated the day before the election. The brief contains:
   60| - **Circumstances:** age, place, household economy, eligibility under their state's rules.
   61| - **News:** two to four dated newspaper excerpts, in 1920 and in the other years the corpus build reached (C15, C30).
   62| - **A blinded ballot:** neutral letters in a random order, each with a neutral description and three platform planks paraphrased from the parties' own texts.
   63| 
   64| Each person answers twice:
   65| - **in the world as it was;**
   66| - **with the change written into their world as settled fact.**
   67| 
   68| The answer is never phrased as a hypothesis. The paired difference, per group, becomes a shift on that group's cells:
   69| - shrunk toward the region's average when there are few people;
   70| - shrunk further when the group's control answers stray from the calibrated record.
   71| 
   72| ### 2.3 The evidence step (per typed what-if)
   73| 
   74| 1. **Compile.** A model call turns typed words into a structured change of one of these kinds:
   75|    - who can vote;
   76|    - how many people;
   77|    - an issue or event;
   78|    - news about one nominee;
   79|    - a new candidate;
   80|    - a third candidate withdrawing.
   81| 2. **Research.** A second call searches the web for scholarship, official statistics and archives. It looks for how the same people behaved in the same or similar situations.
   82| 3. **Extract and grade.** A third call extracts findings. Each must cite a page the search returned. Each is graded by source tier × similarity, and mapped by role, not party label (D20, D22).
   83| 4. **Use the evidence:**
   84|    - **Compare.** Set it against the interviews (corroborated, consistent, contradicted or untested).
   85|    - **Prior.** Use it as a weak prior on the effect, for exploratory what-ifs only.
   86|    - **Confidence.** Set a confidence tier (high, medium, low, very low) with reasons.
   87| 
   88| The evidence never enters a voter's brief.
   89| 
   90| ---
   91| 
   92| ## 3. What each year's data does
   93| 
   94| | Data | Election analysis | Interviews | What-ifs |
   95| |---|---|---|---|
   96| | **Certified returns** (state; county held for checks) | The calibration target; the baseline every change is measured from | None | Flips are crossings of real margins |
   97| | **Population cells** | Denominators; how a state's total is composed | Who is drawn, from where, and how many people each stands for | Changes to who can vote act on specific cells |
   98| | **Voting rules** | Who could vote; the barred share | The eligibility line in each brief | Franchise changes switch rules on or off |
   99| | **Identification** (the natural experiment, or the base year) | How a state's total splits between groups | None | Decides how much a group change matters |
  100| | **Profile** (names, descriptors, labels, day) | Names restored on output | The blinded ballot | Names masked in compiled facts |
  101| | **Platforms** | None | Ballot planks | Planks dropped or added |
  102| | **Dated newspaper corpus** | None | What each person has lately read | Contradicted items removed |
  103| | **Benchmarks** (Corder–Wolbrecht, held-out states) | Scoring only, never fitting; but two women's-turnout prior knots (1928, 1940) come from Corder–Wolbrecht's book, so it isn't scored as held out for 1928–1948 (DISCLOSURES A11) | Scoring only | None |
  104| | **Historical evidence** (per what-if) | A weak prior; the confidence tier | Never shown | Agreement and reasons |
  105| 
  106| A year's data quality sets its confidence ceiling:
  107| - **1920:** has a natural experiment, its own census, a newspaper corpus and held-out checks.
  108| - **1924:** borrows its structure and has no newspapers.
  109| - **Every other year:** runs on era priors, with no identification of its own, no held-out checks beyond reproduction, and newspapers only where the corpus build reached (C30).
  110| 
  111| ---
  112| 
  113| ## 4. Checks the model never sees (held-out validation)
  114| 
  115| ### 4.1 Principles
  116| 
  117| 1. **What is held out.** Real observations kept from everything used to build or tune the model.
  118| 2. **How it is kept out:**
  119|    - **Fixed in config and code.** The held-out set (`configs/`), the metrics and the thresholds (`evaluate.py`, `benchmarks.py`) are set before a run reads them. For 1920 there is no verified record of when they were fixed.
  120|    - **Kept apart in code.** The fit runs where it cannot read benchmark files. Today a unit test enforces that only `evaluate` reads `benchmarks/`.
  121|    - **Inputs that encode the outcome are removed** by allowing known-good columns by name, not by blocking known-bad ones. Gray–Jenkins carries `turnout` and `gopresult`.
  122|    - **A final test set** is opened once, at the end.
  123|    - **Changes after looking are logged.** Every change made after looking is a deviation and goes in `DISCLOSURES.md`, and whatever was tuned on stops counting as unseen.
  124| 3. **How it is scored:**
  125|    - **Score whole distributions,** not just point errors: a log score or CRPS for shares, a Brier score for state winners.
  126|    - **Measure coverage:** do the stated 80% ranges contain the truth about 80% of the time?
  127|    - **Compare with simple baselines:** "same as last time", uniform swing, a demographic regression. Report the gain over them, not raw error.
  128|    - **Report every check, including failures.**
  129| 
  130| ### 4.2 Inventory: what exists and what doesn't
  131| 
  132| | Check | Tests | Status |
  133| |---|---|---|
  134| | R1 exact reproduction | Calibration only | Built, any year (`run verify`) |
  135| | Held-out states (B1–B5) | Model structure | Built for 1920; some fail (`EVAL.md`) |
  136| | Corder–Wolbrecht women's turnout (N1) | The men/women split | 1920: MAE 3.2 points; 1924: 3.6 (held out) |
  137| | Held-out counties | The group splits, about 3,000 tests | **Not built.** County returns are on disk; county census tables need one free NHGIS extract |
  138| | Forecast mode for carried-forward years (1924 before calibration) | Whether the borrowed structure holds | **Not built** |
  139| | Survey benchmarks (Gallup 1936+, ANES 1948+, CPS 1964+) | Group splits directly | **Not built.** Applies to later years only |
  140| | Statistical-layer backtests (fit on 1916, predict 1920 group turnout) | The backbone's what-if machinery | **Not built.** Clean (§5.5) |
  141| | Interview diagnostics | The interview layer's behaviour (not its accuracy) | Built: recall check L1, label swap L2, interview–record gap A1, sameness A2, wording stability A3, stereotype audit A4, Sonnet/Opus comparison D8 |
  142| | Calibration of the confidence tiers | Whether "low" errs more than "high" | **Not built.** The tiers are hand-written rules (H4) |
  143| 
  144| ---
  145| 
  146| ## 5. Contamination: the language model knows how it ended
  147| 
  148| ### 5.1 The problem
  149| 
  150| A brief dated "Monday, 1 November 1920" restricts what the model is told. It does not restrict what the model knows. A language model cannot unlearn; "you don't know the future" is a request, and it leaks.
  151| 
  152| "A world before the event" in this harness is therefore an information-restricted prompt. It is not a knowledge-restricted voter. **It has not been shown that the interviews behave like uncontaminated 1920 people. The evidence says they don't.**
  153| 
  154| ### 5.2 Evidence of contamination we have seen
  155| 
  156| | Observation | Where | What it shows |
  157| |---|---|---|
  158| | The recall check named 1920, both candidates and the winner at 95% confidence from a blinded brief | D9, L1 | Blinding by letters and descriptors is defeated by context |
  159| | A flu-scenario quote said "That fellow Cox" from a blinded brief | D18 | Names leak into answers |
  160| | In the first Harding-disclosure run, most interviewed people blamed Cox for Harding's disclosure, a spurious 7.8-point move toward Harding | D21 | The outcome can shape reasoning: a disqualifying scandal "fits" the loser |
  161| | Quotes say "the Republican" while the brief only gives letters | D19, D23 | The model maps labels to parties itself, sometimes wrongly |
  162| | Every region's reaction to the Harding disclosure lands at about the same Harding share (0.31–0.33) | D23 | One model-level reaction stamped on everyone, not group behaviour (sameness, A2) |
  163| | Interview answers for "No La Follette" send 80% of his voters to Davis; the record is mixed | D24 | Possibly the model's narrative of 1924, not voters' behaviour |
  164| 
  165| ### 5.3 How contamination can bias results
  166| 
  167| - **Anchoring on the outcome:** control answers lean toward the real winner. This is measured as the interview–record gap (A1).
  168| - **Outcome-shaped reactions:** a change is read through what the model knows came next. Unlike constant biases, this does not cancel in the paired difference.
  169| - **Narrative substitution:** the model reproduces the textbook story ("return to normalcy", "the League hurt Cox") instead of reasoning from the person's circumstances.
  170| - **Sameness:** one modern model voices every group, flattening differences between groups (A2, D23).
  171| - **Modern values projected backwards:** reactions to sexuality, race, religion or women's roles may reflect current norms, or caricatured past ones, rather than period attitudes.
  172| 
  173| ### 5.4 Compensating measures in place
  174| 
  175| They reduce or measure the bias; none removes it.
  176| 
  177| 1. **Paired differences.** A bias common to both answers (leaning toward Harding because the model knows he won) largely cancels. Interactions between knowledge and the change do not.
  178| 2. **The statistical layer carries the counts.** Vote totals, turnout and exact reproduction use no model answers. Interviews only supply shifts.
  179| 3. **Shrinkage by interview–record gap.** A group whose control answers stray from the calibrated record has its shift pulled toward its region's average (`paired.py`).
  180| 4. **Blinding.** Letters instead of names, neutral descriptors, and corpus items that name a candidate excluded. Partial at best (D9).
  181| 5. **Manipulation check (p5).** For news about one nominee, each answer states which candidate the news concerns. Misreaders are dropped, counted and flagged; half or more forces "extremely low" (D21).
  182| 6. **Label swap (L2).** Platforms trade labels and the order flips; choices should follow the platform, not the label.
  183| 7. **Disclosure.** The page carries `memorizationExposed`, and every result carries its confidence tier and reasons.
  184| 
  185| ### 5.5 What this means for backtests
  186| 
  187| - **Statistical-layer backtests are clean.** Fitting the population model on 1916 and predicting 1920 involves no language model. The remaining risk is choices made by people who know history (§9.5).
  188| - **Interview-layer backtests on events before the model's training cutoff are not clean.** Running "women can vote" through the 1916 world, the model already knows about a third of women voted in 1920. A good score could be memory, not modelling.
  189| 
  190| So the interview layer cannot be validated on most of American history with today's models. It can be tested in other ways (§7).
  191| 
  192| ---
  193| 
  194| ## 6. Leakage (beyond the model's memory)
  195| 
  196| | Kind | Where it enters | Status |
  197| |---|---|---|
  198| | **Data published after the election** | Truth mode uses later census tables and compilations; strict mode would use only what existed before election day | 1920 runs in truth mode. The research notes define strict mode (`toy_dataset_recipe.md` §5); not implemented |
  199| | **Outcome-encoding input columns** | Gray–Jenkins `turnout` and `gopresult`; County Data Book election variables | The harness reads only named columns. Formalize as an allowlist test |
  200| | **Evidence describing what happened** | Research for a what-if reads historians who know the outcome (e.g. "the League hurt Cox") | Evidence never enters briefs, but it does set priors and confidence. Acceptable for an evidence prior; it must not be mistaken for an independent check |
  201| | **People choosing after looking** | Prompt versions (p1→p5), compiler versions (c1→c3), confidence rules and hand-edited specs were all changed after seeing results | Every one is logged (D11–D24, E5, H4). These choices can't also count as validation |
  202| | **Shared answers across runs** | The answer cache reuses identical requests | By design (G4). Harmless for estimates; a test set must not be re-asked until it looks right |
  203| | **Benchmarks used to tune** | Corder–Wolbrecht guided the N1 denominator fix in 1920 | Logged in `EVAL.md`. N1 for 1920 is no longer fully held out; 1924's comparison was made once, after the fit |
  204| 
  205| ---
  206| 
  207| ## 7. Historical bias (the record itself)
  208| 
  209| Clean statistics on a biased record give clean-looking bias.
  210| 
  211| 1. **Who was counted:**
  212|    - **Census undercount.** The census undercounted Black, immigrant and poor rural people. Population draws add noise by group (e.g. 5% for Black adults) but not a directional correction.
  213|    - **Changing categories.** 1930 counted "Mexican" as a race (C17), which changes what `other` means across years.
  214| 2. **Who could vote, and who is invisible:**
  215|    - **Disenfranchised groups.** Black Southerners and non-citizens appear mostly as "couldn't vote". Their political preferences are borrowed from other groups ("split like Black voters outside the South").
  216|    - **Borrowing is an assumption.** It is the harness's assumption, not something observed.
  217| 3. **What the newspapers say.** Chronicling America over-represents some papers, places and owners. Its selection, by topic and by keyword, was made by the harness.
  218| 4. **What historians emphasize.**
  219|    - **Narratives.** Scholarship carries its own framings and emphasizes some groups, such as German and Irish defections over the League.
  220|    - **Popular sites.** The research step weights sources by type, but much of what it finds is popular history or Wikipedia (H2), which repeats familiar stories.
  221| 5. **What the language model learned.**
  222|    - **Popular retellings.** Its knowledge of 1920 comes mostly from modern retellings, not period sources. It is likely to reproduce the dominant narrative and modern framings.
  223|    - **Stereotyped voice.** Period-voice quotes risk caricature. The stereotype audit (A4) flags reasoning from group labels, and the system prompt forbids it; neither guarantees period realism.
  224| 6. **Values.**
  225|    - **Period attitudes are part of the history.** Hostility to homosexuality in 1920, for example, belongs in the model.
  226|    - **The risk runs both ways.** Reproducing period prejudice as if it were the voters' own words, or erasing it with modern sensibilities. The pipeline doesn't distinguish these yet.
  227| 7. **Selection of what-ifs.** Readers ask about famous people and dramatic changes. The evidence base, and the model's fluency, are strongest exactly where the textbook narrative is strongest.
  228| 
  229| ---
  230| 
  231| ## 8. What's claimed, honestly
  232| 
  233| | Claim | Status |
  234| |---|---|
  235| | The unchanged rerun reproduces each election | **True by construction;** verified every run |
  236| | The population, voting rules and returns are the documented record | **True, with sources.** NHGIS 1920 reproduces the hand-keyed table exactly (C17) |
  237| | The split of each state's vote between groups is right | **Partly tested.** Women's turnout is within about 3–4 points in five states (1920 and 1924); other groups are mostly untested |
  238| | Franchise and population what-ifs are reliable | **As reliable as their stated borrowing assumption** (e.g. "split like Black voters outside the South"). High confidence is about the arithmetic, not the assumption |
  239| | Issue, event and candidate what-ifs reflect 1920 voters | **Not shown.** They reflect a knowledgeable model reasoning about documented circumstances, with contamination measured, partly cancelled and disclosed |
  240| | The confidence tiers are calibrated | **No.** Hand-written rules (H4), not yet scored against outcomes |
  241| | Historical evidence corroborates an answer | **Sometimes, for direction** (flu turnout: interviews −7.4 points, 1918 about −11 ± 5). Rarely for size; often untested |
  242| 
  243| ---
  244| 
  245| ## 9. Next steps
  246| 
  247| ### 9.1 Prove what the interviews respond to (contamination)
  248| 
  249| 1. **Planted-truth tests (synthetic worlds).**
  250|    - **Setup.** Build an invented country with invented parties, history, newspapers and an electorate whose group behaviour we design and bury in their circumstances.
  251|    - **Test.** Does the pipeline recover the planted behaviour, and the planted effect of a planted change?
  252|    - **Why it works.** No model can remember a world that never existed, so this measures reasoning from the brief rather than recall.
  253|    - **Cost.** A few dollars per round.
  254| 2. **Cue-shift tests.**
  255|    - **Setup.** Give the same people briefs with the historical cues altered: dates shifted, fictional newspapers, planks swapped, a fictional state.
  256|    - **Test.** If answers don't move when the brief does, they come from memory.
  257|    - **Scale.** The label swap (L2) is a small version of this.
  258| 3. **Outcome-flip test.** Give one arm a brief whose fictional backdrop implies the opposite outcome, such as polls and newspapers favouring the real loser. Then measure how far answers follow the brief versus the known history.
  259| 4. **Recall check on every run, every year,** with results shown per group and fed into confidence as a standing reason, not an occasional flag.
  260| 5. **Score memory against reasoning per what-if.** Combine the above into a per-change index ("how much of this answer could be recall"). Make it an input to the confidence tier.
  261| 
  262| ### 9.2 Test the statistical layer (clean)
  263| 
  264| 1. **Held-out counties** for 1920 and 1924. This is the strongest available test of group splits. It needs an NHGIS county extract; the returns are on disk.
  265| 2. **Forecast mode for carried-forward years.** Score 1924's prediction from 1920's structure before calibration.
  266| 3. **Backbone backtests on real changes,** with no language model involved:
  267|    - suffrage 1916 → 1920;
  268|    - the VRA, 1964 → 1968/72;
  269|    - the 26th Amendment, 1968 → 1972.
  270| 4. **Survey benchmarks for later years:** Gallup 1936+, ANES 1948+, CPS 1964+, as benchmarks only.
  271| 5. **Baselines and proper scoring.** Every check reports skill over "same as last time" and uniform swing, plus coverage of the 80% ranges.
  272| 
  273| ### 9.3 Tests that can't be contaminated
  274| 
  275| 1. **Prospective forecasts.** Before a future election, primary or known upcoming change, commit a prediction made by the full pipeline, then score it afterwards. This is the gold standard.
  276| 2. **Elections after a model's training cutoff.** For 2024, run the interviews with a model whose training ended before November 2024 (the research notes cite some Llama models). It would be weaker, but clean.
  277| 3. **Period-only language models (research).** Train or fine-tune only on text dated before the event (e.g. Chronicling America to 1920).
  278|    - **Limits.** Fine-tuning a modern model doesn't erase what it knows; training from scratch on period text gives a much weaker model.
  279|    - **Status.** Worth tracking, not building now.
  280| 
  281| ### 9.4 Reduce bias where it's known
  282| 
  283| 1. **Less sameness.**
  284|    - More people per group: the served 1920 run interviews 2, against the prototype's 4 and the config default of 6.
  285|    - Several models: Sonnet, Opus, Haiku and a non-Anthropic model.
  286|    - Persona detail from IPUMS microdata (occupation, literacy, home ownership) instead of imputed economy.
  287|    - Measure group spread (A2) on every run.
  288| 2. **Regional, evidence-anchored transfers** for candidate withdrawals and entries (D24). Use where La Follette's voters actually went (1928) as a prior.
  289| 3. **Period corpora for every year:** pull Chronicling America items for each year (C15), with balance across regions, parties and the Black and immigrant press.
  290| 4. **Separate period attitudes from model attitudes:**
  291|    - give briefs explicit, sourced period context on contested issues;
  292|    - audit quotes for both anachronistic modern framing and caricature.
  293| 5. **Correct for undercount:** apply published undercount estimates by group as a directional prior, not just noise.
  294| 6. **Strict mode:** implement before-election-only data (`toy_dataset_recipe.md` §5), at least for the population and the briefs.
  295| 
  296| ### 9.5 Process
  297| 
  298| 1. **Commit each year's held-out sets before scoring it:** held-out states, counties and benchmarks, metrics and thresholds, so the history shows they were set before the results were seen. No year has this record today (G8).
  299| 2. **Calibrate the confidence tiers** against the backtests and planted-truth tests, then freeze the rules. Until then, keep calling them uncalibrated (H4).
  300| 3. **Keep the working modes separate.** Shipping fixes fast and validation runs are different activities. Validation is run deliberately, once, on locked sets, and is never re-run until it passes.
  301| 4. **Keep logging.** Every post-hoc change goes in `DISCLOSURES.md`.
  302| 
  303| ### 9.6 Suggested order
  304| 
  305| | # | Step | Why first | Rough cost |
  306| |---|---|---|---|
  307| | 1 | Planted-truth test | The only direct answer to "is it reasoning or remembering?" | A few dollars; a day |
  308| | 2 | Cue-shift test on the 1920 interviews | Cheap; quantifies memory against brief | Under $1 |
  309| | 3 | Held-out counties, 1920 and 1924 | Strongest test of the statistical layer | Free (NHGIS); a day |
  310| | 4 | A committed held-out set and thresholds per year | Makes later checks count as unseen | An hour |
  311| | 5 | Backbone backtest 1916 → 1920 | Clean test of what-if machinery | Free |
  312| | 6 | Confidence-tier calibration | Turns hand-written rules into measured ones | Follows 1, 3 and 5 |
  313| | 7 | More people and models per group | Reduces sameness | Scales with budget |
  314| | 8 | Period corpora for 1924+ | Fills C15 | A day per year |
  315| | 9 | One prospective forecast | The only fully uncontaminated test | Waits for an event |
  316| 
  317| ---
  318| 
  319| ## 10. Bottom line
  320| 
  321| The harness is solid where it touches the documented record:
  322| - exact reproduction;
  323| - sourced populations, rules and returns;
  324| - women's turnout within a few points on checks it never saw.
  325| 
  326| Its interview layer is useful but not shown to be clean:
  327| - **What it is:** a knowledgeable model reasoning about documented circumstances.
  328| - **What it is not:** an uncontaminated electorate.
  329| - **Its contamination:** measured, partly cancelled and disclosed.
  330| - **Its historical evidence:** often thin and narrative-shaped.
  331| 
  332| What it can claim today:
  333| - the arithmetic of who could vote;
  334| - the direction, but not yet the size, of how people reacted.
  335| 
  336| What would let it claim more:
  337| - planted-truth and cue-shift tests;
  338| - held-out counties;
  339| - backtests that don't involve the language model;
  340| - calibrated confidence;
  341| - prospective forecasts.
```

## `biome.json`

```json
    1| {
    2| 	"$schema": "https://biomejs.dev/schemas/2.5.15/schema.json",
    3| 	"files": {
    4| 		"includes": [
    5| 			"**",
    6| 			"!**/.svelte-kit",
    7| 			"!**/build",
    8| 			"!**/node_modules",
    9| 			"!**/serve/bundles",
   10| 			"!**/runs",
   11| 			"!**/whatifs",
   12| 			"!**/profiles",
   13| 			"!**/configs",
   14| 			"!**/*.json"
   15| 		]
   16| 	},
   17| 	"formatter": { "enabled": false },
   18| 	"linter": {
   19| 		"enabled": true,
   20| 		"rules": {
   21| 			"preset": "recommended",
   22| 			"suspicious": { "noExplicitAny": "error" },
   23| 			"style": { "noNonNullAssertion": "error", "noNestedTernary": "error" }
   24| 		}
   25| 	},
   26| 	"overrides": [
   27| 		{
   28| 			"includes": ["**/*.svelte"],
   29| 			"linter": {
   30| 				"rules": {
   31| 					"style": { "useConst": "off", "useImportType": "off" },
   32| 					"correctness": {
   33| 						"noUnusedVariables": "off",
   34| 						"noUnusedImports": "off"
   35| 					}
   36| 				}
   37| 			}
   38| 		}
   39| 	]
   40| }
```

## `data/1920/PROVENANCE.md`

```markdown
    1| # 1920 inputs: provenance and licences
    2| 
    3| These files are everything the 1920 backbone and its validation checks read
    4| (R1, B1–B5, N1–N2 in `EVAL.md`). With them, anyone can rerun the 1920
    5| results without the private cache, an NHGIS account or IPUMS:
    6| 
    7| ```sh
    8| SIMHARNESS_CACHE=data/1920 python3 -m simharness.run backbone --config configs/prototype-1920.json
    9| SIMHARNESS_CACHE=data/1920 python3 -m simharness.run evaluate --config configs/prototype-1920.json
   10| ```
   11| 
   12| Checked on 2026-11-20: this folder and the full private cache give identical
   13| results (B1 7.47, B2 2.92, B3 0.93, B4 0.047, R1 0.33; uniform swing 8.68,
   14| persistence 17.41). `EVAL.md` reports B1 7.55 and B4 0.052 from an earlier run
   15| (`runs/1920-bcbd86b43f`); the difference comes from code changes since then, not from the data.
   16| 
   17| Not here, because the backbone doesn't read them: the interviews' newspaper
   18| corpus (`sources/corpus_1920.jsonl`) and party platforms
   19| (`context/platforms_1920.json`). Nothing here comes from NHGIS or IPUMS; those
   20| extracts stay out of the repo (`docs/DEPLOY.md`, "Census data").
   21| 
   22| ## Licences
   23| 
   24| | File | Licence | Why |
   25| |---|---|---|
   26| | `population/*.csv` | Public domain | U.S. Census Bureau publications (works of the U.S. government, 17 U.S.C. § 105) |
   27| | `franchise/state_franchise_1920.csv` | CC0 1.0 | Gray & Jenkins and Teele datasets (both CC0); notes cite National Park Service pages (public domain) |
   28| | `franchise/women_suffrage_pre19th.csv` | CC0 1.0 | Teele dataset (CC0) |
   29| | `benchmarks/corder_wolbrecht_turnout_by_sex.csv` | CC0 1.0 | Corder & Wolbrecht dataset (CC0) |
   30| | `labels/state_pres_1916_1920_1924.csv` | **CC BY-SA 4.0** | Includes figures from Wikipedia (see below); its other columns come from Algara & Amlani (CC0), the House Clerk and NARA (public domain) |
   31| 
   32| The repo's MIT licence covers its code, not these files.
   33| 
   34| **Attribution for `labels/state_pres_1916_1920_1924.csv`.** The `wp_*`
   35| columns, and the `total` (so `other`) in the state-years whose `value_source`
   36| names Wikipedia (15 in 1920, 12 in 1924, 6 in 1916), are adapted from the
   37| results-by-state tables of the English Wikipedia articles "1916 United States
   38| presidential election" (revision 1375915930), "1920 United States presidential
   39| election" (revision 1374763539) and "1924 United States presidential election"
   40| (revision 1377402879), by Wikipedia contributors, licensed CC BY-SA 4.0
   41| (https://creativecommons.org/licenses/by-sa/4.0/). Wikipedia credits those
   42| tables to Dave Leip's Atlas of U.S. Presidential Elections. This file is shared
   43| under the same licence.
   44| 
   45| ## Sources
   46| 
   47| ### Census: `population/`
   48| U.S. Census Bureau, *Fourteenth Census of the United States Taken in the Year
   49| 1920*, Vol. III, Population: Composition and Characteristics (1922), and
   50| *Abstract of the Fourteenth Census* (1923). PDFs from
   51| https://www2.census.gov/library/publications/decennial/1920/ (retrieved 2026-09-30).
   52| 
   53| - **`adults_1920_by_state.csv`**: each state's Vol. III Table 5, "Population 21
   54|   years of age and over, by sex, class of population, and citizenship": Male and
   55|   Female 1920.
   56| - **`adults_1910_by_state.csv`**: the 1910 columns those tables reprint (Male 1910),
   57|   and each state's Table 4 for 1910 females. These are the 1910 enumeration counts,
   58|   published in 1912–13.
   59| - **`urban_rural_1920_by_state.csv`**: Abstract, Population Table 15 (urban and rural
   60|   by state) and Agriculture Table 3 (farm population).
   61| 
   62| The scans have no usable text layer; machine OCR misread this typeface (3/8, 9/0,
   63| 5/6). Every number was transcribed cell by cell from the 300-dpi page images, and
   64| none was typed from memory. Checks, all passing exactly with no tolerance:
   65| - In every state and column: Total = sum of races, White = native + foreign-born,
   66|   and foreign-born white = naturalized + first papers + alien + unknown.
   67| - The 49 state sums equal the printed United States Table 5 in all 48 cells.
   68| - The 1910 female totals equal the printed U.S. figure (24,555,754).
   69| - Urban + rural = total in every state.
   70| - The table also matches NHGIS's 1920 state tables exactly (`DISCLOSURES.md` C17).
   71| 
   72| National 1920 totals (21 and over): men 31,403,370; women 29,483,150.
   73| 
   74| ### Returns: `labels/state_pres_1916_1920_1924.csv`
   75| - **Algara, C. & Amlani, S.**, county presidential returns 1868–2020,
   76|   doi:10.7910/DVN/DGUMFI (Harvard Dataverse v1.1, CC0). This is the default:
   77|   the county sum.
   78| - **U.S. House, Office of the Clerk**, *Statistics of the Presidential and
   79|   Congressional Election* (1921, 1925), history.house.gov. Where the county sum
   80|   differs from the Clerk by more than 0.5% on R or D, the Clerk's R and D are used
   81|   (`value_source`). The transcribed recap columns sum exactly to the printed
   82|   totals (1920: 16,147,249 R; 9,140,864 D; 531 EV).
   83| - **National Archives**, Electoral College results 1920, archives.gov: the
   84|   electoral votes (`nara_ev_*`).
   85| - **Wikipedia**, as attributed above: the total vote where the Clerk is used (the
   86|   Clerk prints no state totals), and the `wp_*` comparison columns.
   87| 
   88| Every discrepancy and the decision rule are recorded in the file's `note` and
   89| `value_source` columns. National 1920 totals as chosen: Harding 16,145,577; Cox
   90| 9,142,289; other 1,511,118; total 26,798,984.
   91| 
   92| ### Franchise: `franchise/`
   93| - **Gray, T. & Jenkins, J.**, state-level franchise data, doi:10.7910/DVN/QIY9EM
   94|   (CC0): poll tax, literacy test, secret ballot, ex-felon rules and women's vote,
   95|   for 1920.
   96| - **Teele, D.**, women's suffrage replication data, doi:10.7910/DVN/EVYI2H, checked
   97|   against doi:10.7910/DVN/JZYGRB (both CC0). Teele hand-coded the dates from
   98|   Keyssar (2000), Tables A.17–A.18. Arkansas and Texas granted only primary
   99|   suffrage, so their presidential year is NA.
  100| - **National Park Service**, "Georgia and the 19th Amendment" and "Mississippi and
  101|   the 19th Amendment" (nps.gov): women in GA and MS could not register in time for
  102|   November 1920 (`women_able_to_vote_nov1920 = 0`).
  103| 
  104| ### Held-out benchmark: `benchmarks/`
  105| **Corder, J. K. & Wolbrecht, C.**, turnout by sex, 1920 and 1924,
  106| doi:10.7910/DVN/QB526J (CC0). Only the evaluate stage reads it
  107| (`test_benchmarks_isolated`).
  108| 
  109| ## File hashes
  110| 
  111| Written by `scripts/harness/data_1920_hashes.py --write`; checked by `tests/test_data_1920.py`.
  112| 
  113| <!-- hashes:start -->
  114| | File | Bytes | sha256 |
  115| |---|---|---|
  116| | `benchmarks/corder_wolbrecht_turnout_by_sex.csv` | 7981 | `66bbd07dc8a5b5c6774cd2d2011e3d28e4a8bfe36fb121fee9ae89f23141897a` |
  117| | `franchise/state_franchise_1920.csv` | 14998 | `e70f04ec2c75e64472de9c30d7d04fa888e2cf1d54726c2a8560ef060efb71c1` |
  118| | `franchise/women_suffrage_pre19th.csv` | 10779 | `54da193f57a1e799d6bcd39a98d44b846ffccb29eb5505c6e3c7261ec0031a4d` |
  119| | `labels/state_pres_1916_1920_1924.csv` | 29225 | `39b0dbc19249663ad64548d84e0bf1135506d11a82175c48f23d1c355e6d5794` |
  120| | `population/adults_1910_by_state.csv` | 365922 | `78ec7a0ca2094430f5350cf04999fe9fe84249921f61fa40dd4bf9c9d4b87de1` |
  121| | `population/adults_1920_by_state.csv` | 441664 | `3a760fb7fb5f976b8db8d76068b1e4de554495e6a330100c54339d0b0c9841ee` |
  122| | `population/urban_rural_1920_by_state.csv` | 137287 | `c703c252af31ab600a3b7579e2e9e696aec1c69fae7d186ac63267153bdcd822` |
  123| <!-- hashes:end -->
```

## `docker/entrypoint.sh`

```bash
    1| #!/bin/sh
    2| # The API container's entrypoint: check the state mount, surface the worker's
    3| # log, then exec the server (so it, not this shell, gets SIGTERM).
    4| set -eu
    5| 
    6| if [ ! -d /state/bundles ] || [ ! -d /state/configs ]; then
    7|   echo "simulacra: /state is not seeded (no bundles/ or configs/). Run scripts/sync-data.sh seed." >&2
    8|   exit 1
    9| fi
   10| mkdir -p /state/sessions /state/runs /state/whatifs
   11| 
   12| # The worker writes only to sessions/intake.log. Echo it to stdout so it
   13| # reaches CloudWatch, where the worker-failure alarm reads it.
   14| touch /state/sessions/intake.log
   15| tail -n 0 -F /state/sessions/intake.log 2>/dev/null | sed -u 's/^/[worker] /' &
   16| 
   17| exec "$@"
```

## `docs/DEPLOY.md`

```markdown
    1| # Deploying Simulacra Americana
    2| 
    3| https://simulacraamericana.com. The page is a static SvelteKit build on
    4| Vercel. The simulation API runs on AWS ECS Fargate at
    5| api.simulacraamericana.com, which the page reaches through a same-origin
    6| Vercel rewrite of `/api/simulacra/*`. The robot assets and portraits come
    7| from CloudFront at assets.simulacraamericana.com. The census-derived data
    8| stays in a private S3 bucket and on EFS. one AWS account (set as `aws_account_id`), us-east-1.
    9| 
   10| ```
   11| simulacraamericana.com, www (Vercel DNS)
   12|   └─ Vercel project: static build on Vercel's CDN
   13|        └─ rewrite /api/simulacra/:path* → https://api.simulacraamericana.com/api/simulacra/:path*
   14| api.     CNAME → ALB (ACM) → ECS service simulacra-api (1 task, ARM64; Node + Python worker)
   15|                               EFS /state: bundles, sessions, runs, whatifs, configs, cache
   16|                               Secrets Manager simulacra/prod: ANTHROPIC_API_KEY, SIMULACRA_ACCESS_KEYS
   17| assets.  CNAME → CloudFront (ACM, OAC) → private S3 simulacra-americana-assets
   18| private S3 simulacra-americana-data: cache/, seed/, backups/
   19| ```
   20| 
   21| Everything on the AWS side is Terraform in `infra/`, with state in
   22| `s3://simulacra-americana-tfstate`. DNS is at Vercel: `infra/vercel-dns.sh`
   23| lists every record. Nothing here touches the Partyhat stacks. The only shared
   24| object is the account's GitHub OIDC provider, which this stack reads but
   25| doesn't manage.
   26| 
   27| ## Why one task
   28| 
   29| Several things assume a single process:
   30| - Run state is an in-process `Map`.
   31| - The per-IP rate limits are counted in process.
   32| - The worker lock (`sessions/intake.lock`) is a PID file, and PIDs aren't
   33|   unique across containers.
   34| - Each process runs one worker.
   35| 
   36| Two tasks would run two workers on the same EFS queue. So the service runs
   37| `desiredCount 1` with `minimumHealthyPercent 0` and `maximumPercent 100`:
   38| the old task stops before the new one starts. That gives a few seconds of
   39| 503s per deploy. The deployment circuit breaker rolls back a revision that
   40| never becomes healthy. Don't scale this service out until the lock and run
   41| state move off the process (to DynamoDB conditional writes, or `flock` on
   42| EFS).
   43| 
   44| ## State on EFS
   45| 
   46| The harness derives every path from its own location. `intake.py` also writes
   47| `ROOT/serve/bundles` whatever `SIMULACRA_BUNDLES` says. So the image has no
   48| state of its own. Instead, `/app/{runs,sessions,whatifs,configs}` and
   49| `/app/serve/bundles` are symlinks onto the EFS mount at `/state`, and the
   50| census cache is at `/state/cache` (`SIMHARNESS_CACHE`).
   51| 
   52| Production diverges from git as soon as the worker models anything: it
   53| republishes bundles and edits `configs/live-<year>.json`. EFS is the record
   54| from then on, backed up daily by AWS Backup (35 days). A code deploy never
   55| overwrites state. To bring a git change to configs or whatifs into
   56| production, copy it onto EFS on purpose.
   57| 
   58| ## Stand-up (once)
   59| 
   60| Steps marked (production) change production. Review the plan or dry-run output before running them.
   61| 
   62| 1. `infra/bootstrap.sh` creates the state bucket.
   63| 2. `cd infra && terraform init && terraform plan`.
   64| 3. (production) Certificates first: `terraform apply -target=aws_acm_certificate.api -target=aws_acm_certificate.assets -target=aws_ecr_repository.api`.
   65| 4. (production) DNS for the certificates: `infra/vercel-dns.sh certs`, then
   66|    `--apply`. This adds the `amazon.com` CAA record (without it ACM never
   67|    issues; the zone allows only pki.goog, sectigo and letsencrypt) and the two
   68|    validation CNAMEs.
   69| 5. The first image: build and push `linux/arm64` to
   70|    `<ecr>/simulacra-api:<sha>`, either locally (`docker buildx build
   71|    --platform linux/arm64 --push`) or from the workflow's build step.
   72| 6. Put the secret value, which never goes through Terraform:
   73|    `aws secretsmanager put-secret-value --secret-id simulacra/prod --secret-string '{"ANTHROPIC_API_KEY":"…","SIMULACRA_ACCESS_KEYS":"{}"}'`.
   74|    Both fields must exist or the task can't start; `"{}"` means no one can
   75|    queue new text yet (see "Access keys").
   76|    Terraform creates the empty secret in step 7. If you want the value in
   77|    place before the task first starts, run
   78|    `terraform apply -target=aws_secretsmanager_secret.prod` first.
   79| 7. (production) `terraform apply -var image=<ecr>/simulacra-api:<sha>`. This waits for
   80|    the certificates to issue, then creates everything else, including the
   81|    bill-monthly items: ALB, EFS, CloudFront. Pass `-var image` on the very
   82|    apply that FIRST creates `aws_ecs_task_definition.api`: the task def
   83|    ignores later container changes, so a revision created with the
   84|    placeholder image stays a placeholder. If that happens, roll a real
   85|    revision with `Deploy API` (as with this stack: revision 1 was busybox, and
   86|    revision 2 was rendered from the template and rolled by hand).
   87| 8. Seed state:
   88|    - `scripts/sync-data.sh upload-cache` (270 objects, 15 MB).
   89|    - `scripts/sync-data.sh upload-seed`.
   90|    - `scripts/sync-data.sh seed`. It refuses if the volume is already seeded.
   91| 
   92|    The service's task exits with "not seeded" until this has run. ECS keeps
   93|    retrying, so seed right after step 7.
   94| 9. Assets: `python3 scripts/mirror-portraits.py --out ../simulacra-assets`,
   95|    then `scripts/publish-assets.sh`.
   96| 10. (production) DNS for the endpoints: `infra/vercel-dns.sh endpoints`, then `--apply`.
   97| 11. Confirm the SNS subscription email to cam@partyhat.ai. Until it's
   98|     confirmed, alarms reach nobody.
   99| 12. Free reproducibility check on the server: a one-off task running
  100|     `python -m simharness.run dryrun --year 1920` should plan without errors.
  101|     New run ids mean the cache bytes differ from the laptop's.
  102| 
  103| ## CI setup
  104| 
  105| 1. Create `partyhat-ai/synthetic-voters-toy` and push.
  106| 2. The deploy role trusts exactly one `sub`, `var.github_oidc_sub`: this
  107|    repo's main branch. For this org the claim carries numeric ids, so it is
  108|    `repo:<owner>@<owner-id>/<repo>@<repo-id>:ref:refs/heads/main`;
  109|    the documented `repo:owner/name:...` silently never matches. The prefix
  110|    comes from `gh api repos/partyhat-ai/synthetic-voters-toy/actions/oidc/customization/sub`.
  111|    The variable refuses a wildcard. A workflow on any other branch, a tag, a
  112|    pull request or an environment gets a different `sub` and can't assume
  113|    the role.
  114| 3. Set the repo variables from Terraform's outputs:
  115|    ```
  116|    gh variable set AWS_DEPLOY_ROLE_ARN -b "$(terraform -chdir=infra output -raw deploy_role_arn)"
  117|    gh variable set TASKDEF_VARS -b "$(terraform -chdir=infra output -json taskdef_vars)"
  118|    ```
  119| 4. A `workflow_dispatch` workflow can only be dispatched once its file is on
  120|    the default branch.
  121| 5. Merges are squash-only (repo settings: merge commits and rebase merges
  122|    off). Branch protection and rulesets need GitHub Team or Pro for a private
  123|    repo, and this org is on the free plan, so nothing yet stops a direct push
  124|    to main or a merge with CI red. The deploy gate below holds regardless:
  125|    only a main SHA with a green CI run ships.
  126| 
  127| ## Deploying
  128| 
  129| **API** (manual only; a merge never ships):
  130| ```
  131| gh workflow run "Deploy API" -R partyhat-ai/synthetic-voters-toy --ref main -f confirm=DEPLOY
  132| ```
  133| The workflow:
  134| - refuses any ref but main, and any SHA without a successful CI push run
  135|   (`ci.yml`) for that exact commit;
  136| - renders the task definition from `infra/taskdef.json.tftpl` and fails if
  137|   any variable, required env var or secret is missing;
  138| - builds on an ARM runner and tags the image with the full commit SHA;
  139| - registers the revision, updates the service and waits until it's stable;
  140| - fails if the circuit breaker rolled back;
  141| - checks through the load balancer: `/healthz` returns 200, and
  142|   `/api/simulacra/elections/1920` is `simulated: true` with slices.
  143| 
  144| To change an env var or secret, edit the template; that is the only place
  145| it's defined.
  146| 
  147| **Web:** the Vercel project is `simulacra-americana` in scope
  148| `camerons-projects-2a650f0d`, deployed from the CLI (`vercel deploy`, then
  149| `vercel promote <url>`). `vercel.json` holds the build, the SPA fallback and
  150| the same-origin rewrite to `api.`. `PUBLIC_ASSET_BASE` is a project env var
  151| (production and preview). `www.` redirects 308 to the apex as a domain
  152| setting (`vercel api /v9/projects/simulacra-americana/domains/www.simulacraamericana.com -X PATCH`).
  153| Once the repo is connected to Vercel's Git integration, Vercel builds a preview from every push. Promoting to production is
  154| manual (`vercel promote <url>`) and needs the owner's sign-off. After a promotion,
  155| check that the site loads, a year opens through the rewrite, and the robot
  156| loads from `assets.`.
  157| 
  158| ## Rolling back
  159| 
  160| - **API:** run `aws ecs update-service --cluster simulacra --service simulacra-api --task-definition simulacra-api:<previous>`.
  161|   Every revision was rendered from the full template, so an older revision
  162|   still carries its env and secrets. This is unlike the auth server's
  163|   derive-from-running deploys. An image's revision can be redeployed as long
  164|   as ECR keeps the image (the last 30).
  165| - **Web:** `vercel rollback`, or "Instant Rollback" to a previous production
  166|   deployment in the dashboard.
  167| - **State (EFS):**
  168|   1. In AWS Backup, open vault `simulacra-state` and restore a recovery point
  169|      to a new directory on the same filesystem.
  170|   2. Stop the service (`desired-count 0`) and swap the directories.
  171|   3. Start the service again.
  172| 
  173|   An EFS restore puts the files in `aws-backup-restore_<ts>/` at the
  174|   filesystem root, outside the access point. Move them with a one-off task
  175|   that mounts the root.
  176| - **Bundles only:** the repo's committed `serve/bundles` and the tarballs in
  177|   `s3://simulacra-americana-data/backups/<date>/` are the fallbacks. Copy the
  178|   year's `<year>.json` onto `/state/bundles`. The router reloads it by mtime
  179|   without a restart.
  180| 
  181| ## Assets
  182| 
  183| Edit or add assets in the assets folder outside the repo, then run
  184| `scripts/publish-assets.sh`, which uploads them and invalidates `/*`.
  185| 
  186| The robot files are copied, never moved, from the shared Partyhat bucket.
  187| Only what the page loads is copied: `models/atlas-09-americana.glb` and
  188| `models/atlas-09-americana-rerun/`.
  189| 
  190| The page versions assets with `?v=`, and CloudFront's cache key includes the
  191| query string, so a new `?v=` takes effect immediately.
  192| 
  193| ## Portraits and credits
  194| 
  195| `scripts/mirror-portraits.py` resolves each portrait through the Commons API
  196| and writes `portraits/credits.json` with the author, licence and licence URL
  197| taken from the API. 76 of the 77 are public domain. One
  198| needs attribution: `roosevelt2`, CC BY 2.0, Leon Perskie. The About sources
  199| must show that credit.
  200| 
  201| ## Rotating the Anthropic key
  202| 
  203| 1. Create a new key in the Anthropic console.
  204| 2. Replace the one field, keeping `SIMULACRA_ACCESS_KEYS`:
  205|    ```
  206|    cur=$(aws secretsmanager get-secret-value --secret-id simulacra/prod --query SecretString --output text)
  207|    aws secretsmanager put-secret-value --secret-id simulacra/prod \
  208|      --secret-string "$(jq -c --arg k "<new>" '.ANTHROPIC_API_KEY=$k' <<<"$cur")"
  209|    ```
  210| 3. Force a new deployment so the task picks up the key:
  211|    `aws ecs update-service --cluster simulacra --service simulacra-api --force-new-deployment`.
  212|    This brings a few seconds of 503s, and it kills a running worker, whose
  213|    what-if is retried.
  214| 4. Revoke the old key once the new task is healthy.
  215| 5. Move the console usage alert to the new key.
  216| 
  217| ## Access keys
  218| 
  219| Reading is open: every year, every precomputed what-if and every combination
  220| of them is free to serve. Only text the page doesn't recognise costs money
  221| (compile, web research, staging, interviews). The API queues it for every
  222| visitor, with or without an access key; a key (`Authorization: Bearer <key>`)
  223| only puts its name on that text's lines in the spend ledger.
  224| 
  225| Keys live in the secret's `SIMULACRA_ACCESS_KEYS` field: a JSON object, as a
  226| string, of name → key. Names are lowercase (`[a-z0-9_-]`, up to 40); keys
  227| are 24–128 characters of `[A-Za-z0-9_-]`. The name is what the spend ledger
  228| records. To add one:
  229| ```
  230| key=$(openssl rand -base64 36 | tr '+/' '-_' | tr -d '=')
  231| cur=$(aws secretsmanager get-secret-value --secret-id simulacra/prod --query SecretString --output text)
  232| aws secretsmanager put-secret-value --secret-id simulacra/prod --secret-string "$(
  233|   jq -c --arg name "<name>" --arg key "$key" \
  234|     '.SIMULACRA_ACCESS_KEYS = ((.SIMULACRA_ACCESS_KEYS // "{}" | fromjson) + {($name): $key} | tojson)' <<<"$cur")"
  235| aws ecs update-service --cluster simulacra --service simulacra-api --force-new-deployment
  236| echo "https://simulacraamericana.com/#key=$key"
  237| ```
  238| The link sets the key for that browser tab (the page keeps it in
  239| `sessionStorage` and drops it from the address bar; a fragment never reaches
  240| a server log). To revoke a key, delete its name the same way and redeploy.
  241| 
  242| ## Spend
  243| 
  244| **Two dollar caps bound the intake, counted across every visitor together:**
  245| `SIMULACRA_DAILY_USD` per UTC day (20 in the task definition) and
  246| `SIMULACRA_MONTHLY_USD` per UTC calendar month (200). The worker records each
  247| stage in `/state/sessions/spend.jsonl` (priced before it is sent and recorded
  248| after, with the access key's name when the request carried one; every line
  249| counts toward the caps, keyed or not).
  250| 
  251| - **Before queuing** (`serve/guard.ts`, `checkCaps`): once today's or this
  252|   month's recorded spend reaches its cap, POST /runs queues nothing and the
  253|   run answers at once with `unknownWhy` saying the budget is spent.
  254| - **Before each text** (`simharness/intake.py`, `left`): the worker checks the
  255|   same ledger. With nothing left, the text is settled as `over-cap` in
  256|   `queue-done.jsonl` and the waiting page is told why.
  257| - **During a text** (`intake.Budget`): the text runs with what is left as its
  258|   ceiling and stops at the first stage that reaches it. A stage is priced when
  259|   it finishes, so a cap can be passed by at most the one stage that crosses
  260|   it (at most about $2, the cost of one text's interviews).
  261| 
  262| A text that fails is retried once. After two failures it is settled as
  263| `gave-up` and copied to `/state/sessions/queue-dead.jsonl`, so a text that
  264| always fails is billed at most twice and never holds up the texts behind it.
  265| 
  266| To change a cap, edit its value in `infra/taskdef.json.tftpl` and deploy.
  267| 
  268| The research agent (`simharness/agent.py`) is off in production. It runs only
  269| when the task definition sets `SIMULACRA_AGENT=1`. It spends under the same caps
  270| and `Budget`, and its own model turns are recorded in the ledger as stage `agent`.
  271| With `SIMULACRA_AGENT_PUBLISH=ask`, nothing it builds goes live until
  272| `python -m simharness.run approve --id <trace>` is run in a one-off task.
  273| 
  274| The per-IP limits (`serve/simulacra.ts`, `DEFAULT_LIMITS`): 1,200
  275| requests per 10 minutes, 120 runs per 10 minutes, and 10 queued texts an
  276| hour; past the last, POST /runs answers 429. The rate limits read the
  277| visitor's address from `X-Forwarded-For` two proxies deep (`TRUST_PROXY_HOPS`:
  278| Vercel, then the ALB). A request sent to the ALB directly can forge that
  279| header, so the per-IP limits can be dodged; the dollar caps can't, since they
  280| count every visitor together. To stop the spending at once,
  281| remove or revoke the Anthropic key, or stop the service
  282| (`aws ecs update-service --cluster simulacra --service simulacra-api --desired-count 0`).
  283| 
  284| Session logs (`requests.jsonl` and the queue files) keep 7 days of lines
  285| (`SIMULACRA_RETAIN_DAYS`), pruned at start and hourly while no worker runs.
  286| `spend.jsonl` keeps every line, but drops a line's `note` (the visitor's
  287| words) after the same 7 days. The worker's `intake.log` is emptied past 20 MB (CloudWatch keeps its
  288| copy). To read them, run a one-off task, or download the latest AWS Backup
  289| recovery point.
  290| 
  291| AWS can't see Anthropic spend. Set a usage alert on the production key in the
  292| Anthropic console.
  293| 
  294| ## Census data
  295| 
  296| The NHGIS/IPUMS extracts and the derived `population/*_nhgis.csv` files are
  297| not for redistribution. They live only in `s3://simulacra-americana-data/cache/`
  298| (the derived part, everything except `*/raw/`) and on EFS. They are never in
  299| git, an image, Vercel or the assets bucket.
  300| 
  301| The 1920 inputs in `data/1920/` are different: they are transcribed from the census
  302| volumes (public domain) or come from CC0 datasets, plus one CC BY-SA returns file, and are
  303| committed so the 1920 results can be rerun from the repo (`data/1920/PROVENANCE.md`).
  304| 
  305| To re-sync after rebuilding the cache on a laptop, run
  306| `scripts/sync-data.sh upload-cache`, then `scripts/sync-data.sh cache`. Run
  307| ids hash the cache manifest, so a changed cache means new run ids.
  308| 
  309| ## Alarms
  310| 
  311| All alarms go to SNS `simulacra-alarms`, which emails cam@partyhat.ai:
  312| - no healthy target for 3 minutes;
  313| - more than 5 target 5xx in 5 minutes;
  314| - more than 10 ELB 5xx in 5 minutes;
  315| - any worker STOP, refusal or traceback (the entrypoint echoes worker lines
  316|   to the log with a `[worker]` prefix);
  317| - the AWS Budget forecast passing 80%, and actual spend passing 100% of $150
  318|   a month. The budget filters on the `project` cost-allocation tag. AWS can
  319|   take up to 24 hours to see a new tag, so activating it may fail on the
  320|   first apply; re-apply the next day.
  321| 
  322| ## Cost estimate (us-east-1, October 2026 list prices)
  323| 
  324| | Item | Basis | ~/month |
  325| |---|---|---|
  326| | ALB | $16.43 base plus about 1 LCU | $22 |
  327| | Fargate | 1 vCPU, 4 GB, ARM, 24/7 | $34 |
  328| | Public IPv4 | Task plus 2 ALB addresses at $3.65 each | $11 |
  329| | EFS (elastic) | About 1–2 GB, growing 5–7 MB per new what-if, plus I/O | $1–3 |
  330| | AWS Backup | EFS warm storage | <$1 |
  331| | CloudFront | About 19 MB per first-time visitor; inside the 1 TB/month free tier up to about 50k visitors | $0 |
  332| | S3, ECR, logs, alarms, Secrets Manager | | $3–5 |
  333| | **AWS total** | | **≈ $75–80** |
  334| | Vercel | Hobby is $0, but its terms exclude commercial use; Pro is $20 per member | $0–20 |
  335| | Anthropic | $0.74–$1.91 per new typed what-if, from any visitor. Repeats and precomputed combinations are free | At most $200, by the monthly cap ($20 a day) |
  336| 
  337| The Anthropic line dominates. The daily and monthly caps (Spend, above) bound it.
```

# synthetic-electorate-toy: data samples

Generated from commit `6a200effe03e` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.

Data files are not reproduced in full. One sample per top-level folder, first 40 lines:

## `configs/` (63 files)

Sample: `configs/live-1789.json`

```json
{
  "election": 1789,
  "election_day": "1788-12-15",
  "context_cutoff": "1788-12-14",
  "mode": "truth",
  "what_ifs": [
    "everyone"
  ],
  "seed": 1920,
  "draws": 100,
  "prompt_version": "p5",
  "holdout": [
    "VA"
  ],
  "agents": {
    "bulk_model": "claude-sonnet-5-5",
    "check_model": "claude-haiku-4-5",
    "check_share": 0,
    "per_cohort": 3,
    "paraphrases": 3,
    "effort": "medium",
    "backend": "anthropic",
    "max_cohorts": 36,
    "only_cohorts": [
      "midwest:M:native_white",
      "midwest:F:native_white",
      "northeast:F:native_white",
      "northeast:M:native_white",
      "south:M:native_white",
      "south:F:native_white"
    ],
    "arms": [
      "control",
      "cf"
    ],
    "max_tokens": 6000,
    "replace_barred": true,
    "focus_cohorts": 6,
    "escalate_model": "claude-opus-5-5",
    "escalate_max": 24,
```

## `data/` (7 files)

Sample: `data/1920/benchmarks/corder_wolbrecht_turnout_by_sex.csv`

```
year,state,women_turnout,women_turnout_lo95,women_turnout_hi95,men_turnout,men_turnout_lo95,men_turnout_hi95,women_turnout_from_unit_medians,men_turnout_from_unit_medians,overall_turnout_obs,n_units,eligible_women_f,eligible_men_m,votes_v,method,states_covered,source
1920,CT,0.3258,0.2813,0.3595,0.537,0.505,0.5797,0.3266,0.5348,0.4332,177,416883.0,426761.0,365478.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1920,IL,0.4564,0.4431,0.4676,0.5984,0.5872,0.6113,0.458,0.5979,0.5304,234,1915293.9,2028851.0,2092059.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1920,MA,0.3363,0.3225,0.3486,0.5165,0.5033,0.5316,0.3372,0.5162,0.4273,447,1238781.0,1172126.0,1030147.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1920,MI,0.4061,0.3854,0.4236,0.5501,0.5347,0.5671,0.4067,0.5496,0.4785,1236,1022702.0,1192173.0,1059894.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1920,NY,0.3519,0.3381,0.3631,0.5157,0.5041,0.5298,0.3527,0.5162,0.4401,865,3258350.0,3255078.0,2866684.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1920,ALL_POOLED,0.3804,0.3712,0.3886,0.5429,0.5347,0.552,0.3816,0.5426,0.4655,2959,7852010.0,8074988.5,7414262.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1924,CT,0.3204,0.2767,0.3574,0.5536,0.5168,0.5968,0.3219,0.5524,0.4404,177,447211.97,453370.0,396627.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1924,IL,0.4803,0.4606,0.4961,0.6592,0.6437,0.6778,0.4818,0.6587,0.5736,294,2097659.0,2207733.0,2469738.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1924,MA,0.3937,0.3783,0.4072,0.5771,0.5628,0.5935,0.3947,0.5759,0.4826,447,1302610.0,1218164.0,1216504.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1924,MI,0.3487,0.3288,0.3667,0.5517,0.5361,0.5697,0.3503,0.5515,0.4635,1257,1163178.0,1340845.0,1160728.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1924,NY,0.3555,0.3415,0.368,0.5398,0.5272,0.5536,0.3566,0.5398,0.4547,872,3584202.0,3578954.2,3257362.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
1924,ALL_POOLED,0.3888,0.3794,0.3972,0.5777,0.5692,0.587,0.3903,0.5771,0.4887,3047,8594861.0,8799066.0,8500959.0,"Corder & Wolbrecht (2006 JOP) hierarchical Bayesian ecological inference (MCMChierEXC, female<male constraint) on sub-county units (MCDs/wards/counties); state value = eligible-population-weighted aggregate of unit posterior draws (f for women, m for men); 95% interval = 2.5/97.5 pct of 2500 posterior draws of the aggregate. Aggregation by harness, not published by authors.","CT, IL, MA, MI, NY (only states in this Dataverse deposit)",doi:10.7910/DVN/QB526J JOP_merge{yy}.dta + JOP_results{yy}.dta + jop_{yyyy}_full_posterior.Rdata
```

## `extracts/` (2 files)

Sample: `extracts/ipums-1920-fullcount.json`

```json
{
  "_comment": "IPUMS USA extract definition for the full-count path (not run in the prototype: no IPUMS API key on this machine). IPUMS microdata can't be redistributed; the harness ships this definition and serves only aggregates. Submit with the IPUMS API (https://developer.ipums.org/docs/v2/workflows/create_extracts/usa/) under your own registration, then point SIMHARNESS_IPUMS_1920 at the downloaded CSV. Variable names marked confirm were not confirmed on IPUMS variable pages by the research agents (toy_dataset_recipe.md §1.2); check them in the extract system first.",
  "description": "Simulacra Americana: 1920 full count, adults 21+, for the 1920 electorate (truth mode). Strict mode uses the same definition on us1910m.",
  "dataStructure": { "rectangular": { "on": "P" } },
  "dataFormat": "csv",
  "samples": { "us1920c": {} },
  "variables": {
    "YEAR": {}, "SERIAL": {}, "PERNUM": {}, "STATEFIP": {}, "STATEICP": {}, "COUNTYICP": {}, "COUNTYNHG": {},
    "AGE": { "caseSelections": { "general": ["021-120"] } },
    "SEX": {}, "RACE": {}, "BPL": {}, "OCC1950": {},
    "NATIVITY": { "_confirm": true }, "URBAN": { "_confirm": true }, "FARM": { "_confirm": true },
    "RELATE": { "_confirm": true }, "MARST": { "_confirm": true }, "GQ": { "_confirm": true },
    "LIT": {}, "CITIZEN": {}, "OWNERSHP": {}
  },
  "_never_ship": ["HISTID", "any name field", "any record-level row"],
  "_harness_use": {
    "cells": "STATEFIP × SEX × RACE(harmonized: white/Black/other) × NATIVITY(native/foreign) × CITIZEN(naturalized/first papers/alien) × AGE band (21–24, 25–34, 35–44, 45–54, 55–64, 65+) × URBAN × FARM",
    "joint": "weighted tabulation of the cells above replaces the IPF seed in population.py; the published state tables (voting age by color, nativity and citizenship) stay the raking targets, so the full count and the published volumes must agree to rounding before a run",
    "persona": "OCC1950 and FARM replace the imputed household economy in agents.py"
  },
  "strict_mode_samples": { "1920": "us1910m", "1896": "us1880e (reweighted to NHGIS 1890 margins)" }
}
```

## `profiles/` (58 files)

Sample: `profiles/1789.json`

```json
{
  "base": null,
  "day_phrase": "the day this person's state has set for choosing presidential electors (states choose on different days, from 15 December 1788 until the electors meet on 4 February 1789)",
  "names": {
    "R": "Washington",
    "D": null,
    "O": "another candidate"
  },
  "full_names": {
    "R": "George Washington",
    "D": null
  },
  "descriptors": {
    "R": "the man the Constitution's supporters expect every elector to name: the former commander-in-chief of the Continental Army who presided over the Constitutional Convention",
    "D": null
  },
  "compile_desc": {
    "R": "the supporters of the new Constitution",
    "D": "the opponents of the new Constitution, who run no one for the first office",
    "president": "no one yet (the first President is being chosen)"
  },
  "third": null,
  "label_pool": [
    "K",
    "N",
    "V",
    "X",
    "Z",
    "Y"
  ],
  "others_line": "Some elector tickets are run by opponents of the new Constitution who want it amended before it takes hold (answer \"other\").",
  "plank_order": [
    "union",
    "public credit",
    "defense",
    "amendments"
  ],
  "names_re": "\\b(Washington|Adams|(?-i:Jay)|Hancock|Rutledge|Clinton|Hamilton|Madison|Jefferson|Patrick Henry|Anti-?Federalist|Federalist)",
  "never_name": "Washington, Adams, Jay, Hancock, Rutledge, Clinton, Hamilton, Madison, Jefferson or Patrick Henry",
  "corpus": null,
```

## `runs/` (604 files)

Sample: `runs/1789-1fe17615d3/analysis.json`

```json
{
 "l1": {
  "n": 0,
  "year_rate": null,
  "names_rate": null,
  "winner_rate": null,
  "exposed_cohorts": [],
  "by_cohort": {}
 },
 "l2": {
  "n": 0,
  "label_rate": null,
  "platform_rate": null
 },
 "a1": [
  {
   "cohort": "northeast:F:native_white",
   "label": "White women, northeast",
   "n": 2,
   "agent_turnout": 0.16666666666666666,
   "backbone_turnout": 0.0,
   "agent_r2": NaN,
   "backbone_r2": 0.0,
   "bias_logit": null,
   "tvd": 0.0,
   "exposed": false
  },
  {
   "cohort": "northeast:M:native_white",
   "label": "White men, northeast",
   "n": 2,
   "agent_turnout": 0.6566666666666666,
   "backbone_turnout": 0.07541820892223812,
   "agent_r2": 0.7777283840853523,
   "backbone_r2": 1.0,
   "bias_logit": -12.563032344549466,
   "tvd": 0.9245817910777618,
   "exposed": false
  },
  {
```

## `serve/` (60 files)

Sample: `serve/bundles/1789.json`

```json
{
 "year": 1789,
 "runId": "1789-1fe17615d3",
 "election": {
  "slices": [
   {
    "key": "men",
    "label": "Men outside the South",
    "adults": 0.397,
    "barred": 0.3034,
    "home": 0.6284,
    "A": 0.0546,
    "B": 0.0,
    "O": 0.0137,
    "source": "1790 census back-projected to late 1788, free adult men outside the Southern states; the 1790 census gives only free white males 16 and over, so men 21+ are estimated. Voters were men meeting each state's rules: most states required a freehold, property or taxpaying qualification. Electors were chosen by popular vote in 6 states; elsewhere (Connecticut, Georgia and South Carolina, whose legislatures chose, and New Jersey, whose governor and council chose; New York failed to appoint, and North Carolina and Rhode Island had not yet ratified) men cast no presidential vote. Free Black men could vote in some Northern states on the same or stricter terms."
   },
   {
    "key": "women",
    "label": "Women outside the South",
    "adults": 0.391,
    "barred": 1.0,
    "home": 0.0,
    "A": 0.0,
    "B": 0.0,
    "O": 0.0,
    "source": "1790 census back-projected to late 1788, women 21+ (estimated from age bands). No woman could vote for president this year: New Jersey's women with \u00a350 of property could vote in state elections under its 1776 constitution, but its electors were named by the governor and council. Turnout is zero by law, not by estimate."
   },
   {
    "key": "south-white",
    "label": "White Southerners",
    "adults": 0.264,
    "barred": 0.6878,
    "home": 0.288,
    "A": 0.0176,
    "B": 0.0,
    "O": 0.0066,
    "source": "1790 census back-projected to late 1788, white adults in Virginia, North Carolina, South Carolina and Georgia; only men meeting their state's property or taxpaying rules could vote (Virginia required a freehold). The South Carolina and Georgia legislatures chose their electors, so people there cast no presidential vote. North Carolina had not yet ratified the Constitution."
   },
   {
    "key": "black-south",
```

## `tests/` (1 files)

Sample: `tests/fixtures/bundle.example.json`

```json
{
 "year": 1920,
 "runId": "1920-1a2dcd24ad",
 "election": {
  "slices": [
   {
    "key": "men",
    "label": "Men outside the South",
    "adults": 21.894,
    "barred": 0.0,
    "home": 0.3508,
    "A": 0.4859,
    "B": 0.1373,
    "O": 0.026,
    "source": "1920 census (Fourteenth Census, voting-age tables), men 21+ outside the eleven Southern states; turnout and choice from the backbone (1916→1920 natural experiment, calibrated to certified returns)."
   },
   {
    "key": "women",
    "label": "Women outside the South",
    "adults": 21.249,
    "barred": 0.0,
    "home": 0.5337,
    "A": 0.2151,
    "B": 0.2121,
    "O": 0.0392,
    "source": "1920 census, women 21+ outside the South; turnout is each state's 1920 vote minus the men's predicted vote (1916 men's turnout × the change in states where women already voted)."
   },
   {
    "key": "south-white",
    "label": "White Southerners",
    "adults": 8.544,
    "barred": 0.0743,
    "home": 0.6151,
    "A": 0.1079,
    "B": 0.1901,
    "O": 0.0127,
    "source": "1920 census, white adults in the eleven former Confederate states (includes a small number of American Indian and Asian adults); calibrated to certified returns."
   },
   {
    "key": "black-south",
```

## `whatifs/` (109 files)

Sample: `whatifs/america-loses-the-second-world-war.json`

```json
{
 "key": "america-loses-the-second-world-war",
 "label": "America Loses The Second World War",
 "kind": "issue",
 "subkind": "event",
 "mode": "agents",
 "detail": "By election eve, Allied defeats have gone so badly that the United States faces military collapse and a negotiated or imposed settlement.",
 "assumption": "Voters are interviewed in a country facing military defeat, which weakens confidence in the wartime leadership and raises the weight of war weariness and peace sentiment; turnout and vote choice shift accordingly, and the observed 1944 baseline is adjusted rather than replaced.",
 "plausibility": "a-stretch",
 "anachronism": false,
 "anachronism_note": "",
 "year": 1944,
 "years": [
  1944
 ],
 "withdraws": null,
 "facts_text": [
  "Allied armies have suffered repeated major defeats in Europe and the Pacific, and American forces have been driven back from the positions they held in 1943.",
  "Enemy forces threaten the American coasts, and the government is weighing terms to end the war.",
  "Casualty lists and shortages of war goods dominate the news at home."
 ],
 "reach": {},
 "about": null,
 "nominee_news": [],
 "drop_topics": [],
 "drop_planks": [
  "postwar jobs"
 ],
 "add_planks": [
  {
   "party": "R",
   "text": "Call for an immediate inquiry into the conduct of the war and new leadership to negotiate the best possible peace."
  },
  {
   "party": "D",
   "text": "Call for national unity and continued resistance, and rebuilding the armed forces to restore the nation's security."
  }
 ],
 "candidate": null,
 "franchise": null,
```

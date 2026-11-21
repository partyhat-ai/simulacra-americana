# synthetic-electorate-toy: data samples

Generated from commit `e5e4f20fbaeb` (2026-11-20) of github.com/partyhat-ai/synthetic-electorate-toy by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.

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

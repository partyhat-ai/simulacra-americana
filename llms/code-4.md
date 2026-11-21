# simulacra-americana: source and docs, part 4 of 17

Generated from commit `caf86112f396` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `scripts/harness/build_corpus.py` to `scripts/harness/build_population_mid.py`. Lines are numbered as in the repository.

## `scripts/harness/build_corpus.py`

```python
    1| #!/usr/bin/env python3
    2| """build_corpus.py — dated Chronicling America corpus for one election year.
    3| 
    4| Builds C/sources/corpus_<year>.jsonl in the 1920 corpus format (see
    5| C/sources/PROVENANCE-sources.md): page-level items from the loc.gov
    6| Chronicling America collection, each with a ~120-word excerpt cut
    7| programmatically from the fetched OCR, dated from 1 September of the election
    8| year through the day before election day (no item after the cutoff).
    9| 
   10| Usage:
   11|   python scripts/harness/build_corpus.py 1896 [1932 ...] --cache-dir DIR [--out-dir DIR]
   12|   python scripts/harness/build_corpus.py --provenance 1896 1932 --cache-dir DIR  # markdown
   13| 
   14| Politeness: single-threaded; >=3.2 s between www.loc.gov searches, >=1.1 s
   15| between tile.loc.gov OCR fetches; exponential backoff (honouring Retry-After)
   16| on 429/5xx/Cloudflare errors; every HTTP response is cached on disk so reruns
   17| make no new requests. Descriptive User-Agent.
   18| 
   19| Selection is fully automatic (no LLM): per topic, one national search plus the
   20| best-covered state in each census region (from the national query's
   21| location_state facet), plus a second national query. The top hits are fetched,
   22| the densest topic-keyword window of the OCR is excerpted, scored for OCR
   23| readability, ad/patent-medicine noise, prediction talk and candidate mentions,
   24| and items are then picked round-robin across regions with per-paper caps and
   25| near-duplicate (shingle Jaccard) rejection.
   26| """
   27| from __future__ import annotations
   28| 
   29| import argparse
   30| import datetime as dt
   31| import hashlib
   32| import http.client
   33| import json
   34| import math
   35| import os
   36| import re
   37| import sys
   38| import tempfile
   39| import time
   40| import urllib.error
   41| import urllib.parse
   42| import urllib.request
   43| 
   44| UA = ("SimulacraHarness-corpus-builder/1.0 (historical election research; "
   45|       "single-threaded, cached, backs off on 429)")
   46| SEARCH = "https://www.loc.gov/collections/chronicling-america/"
   47| DEFAULT_CACHE = os.environ.get("CORPUS_BUILD_CACHE") or os.path.join(
   48|     tempfile.gettempdir(), "simharness_corpus_build_cache")
   49| DEFAULT_OUT = os.path.expanduser(
   50|     "~/research_notes/historical_election_sim_data/harness_cache/sources")
   51| 
   52| # ---------------------------------------------------------------- geography
   53| REGION = {}
   54| for _r, _ss in {
   55|     "Northeast": ["maine", "new hampshire", "vermont", "massachusetts", "rhode island",
   56|                   "connecticut", "new york", "new jersey", "pennsylvania"],
   57|     "Midwest": ["ohio", "indiana", "illinois", "michigan", "wisconsin", "minnesota", "iowa",
   58|                 "missouri", "north dakota", "south dakota", "nebraska", "kansas", "dakota"],
   59|     "South": ["delaware", "maryland", "district of columbia", "virginia", "west virginia",
   60|               "north carolina", "south carolina", "georgia", "florida", "kentucky",
   61|               "tennessee", "alabama", "mississippi", "arkansas", "louisiana", "oklahoma",
   62|               "texas", "indian territory"],
   63|     "West": ["montana", "idaho", "wyoming", "colorado", "new mexico", "arizona", "utah",
   64|              "nevada", "washington", "oregon", "california", "alaska", "hawaii"],
   65| }.items():
   66|     for _s in _ss:
   67|         REGION[_s] = _r
   68| REGIONS = ["Northeast", "Midwest", "South", "West"]
   69| 
   70| # ------------------------------------------------------------- year configs
   71| # topics: (label, human description, [search queries], [extra window keywords])
   72| # names: candidate / running-mate / incumbent / party words (case-sensitive).
   73| Y: dict[int, dict] = {}
   74| 
   75| 
   76| def year(y, election, names, topics, cutoff=None):
   77|     e = dt.date.fromisoformat(election)
   78|     Y[y] = dict(election=e, cutoff=dt.date.fromisoformat(cutoff) if cutoff else e - dt.timedelta(days=1),
   79|                 names=names, topics=topics)
   80| 
   81| 
   82| GENERIC_PARTY = ["Republican", "Republicans", "Democrat", "Democrats", "Democratic", "Democracy"]
   83| 
   84| year(1840, "1840-10-30", ["Harrison", "Tyler", "Van Buren", "Johnson", "Birney", "Whig", "Whigs",
   85|                           "Loco Foco", "Locofoco", "Locofocos", "Tippecanoe", "Liberty party"] + GENERIC_PARTY, [
   86|     ("hard_times", "Hard times after the Panic of 1837", ["hard times", "times money scarce"], ["distress", "wages", "credit", "failures"]),
   87|     ("sub_treasury", "Independent Treasury (sub-treasury)", ["sub treasury", "independent treasury"], ["specie", "treasury"]),
   88|     ("banks_currency", "Banks, specie payments and paper money", ["specie payments banks", "bank notes currency"], ["suspension", "specie", "currency"]),
   89|     ("national_bank", "A national bank", ["national bank"], ["bank", "charter"]),
   90|     ("standing_army", "Militia plan / standing army", ["standing army", "militia"], ["poinsett", "army"]),
   91|     ("abolition", "Abolition and slavery", ["abolition", "abolitionists slavery"], ["slaves", "slavery"]),
   92|     ("tariff", "Tariff and home industry", ["tariff", "protection home industry"], ["duties", "manufactures"]),
   93|     ("public_lands", "Public lands and pre-emption", ["public lands", "pre-emption"], ["lands", "settlers"]),
   94| ], cutoff="1840-10-29")
   95| year(1844, "1844-11-01", ["Polk", "Dallas", "Clay", "Frelinghuysen", "Birney", "Tyler", "Whig", "Whigs",
   96|                           "Loco Foco", "Locofoco", "Locofocos", "Liberty party"] + GENERIC_PARTY, [
   97|     ("texas_annexation", "Annexation of Texas", ["annexation texas"], ["annex", "texas", "mexico"]),
   98|     ("tariff_1842", "The tariff of 1842", ["tariff of 1842", "tariff protection"], ["duties", "manufactures"]),
   99|     ("oregon", "The Oregon question", ["oregon territory", "oregon"], ["british", "boundary"]),
  100|     ("national_bank", "A national bank", ["national bank"], ["bank", "currency"]),
  101|     ("slavery_abolition", "Slavery and abolition", ["abolition slavery", "abolitionists"], ["slaves", "slavery"]),
  102|     ("nativism", "Native Americanism and naturalization", ["native american", "naturalization foreigners"], ["catholic", "riots", "foreigners"]),
  103|     ("distribution_lands", "Distribution of public land revenue", ["distribution public lands"], ["lands", "states"]),
  104|     ("hard_money", "Currency and banks", ["currency banks specie"], ["specie", "paper"]),
  105| ], cutoff="1844-10-31")
  106| year(1848, "1848-11-07", ["Taylor", "Fillmore", "Cass", "Butler", "Van Buren", "Adams", "Polk", "Whig", "Whigs",
  107|                           "Free Soil", "Free Soilers", "Barnburner", "Barnburners", "Loco Foco", "Locofoco",
  108|                           "Locofocos"] + GENERIC_PARTY, [
  109|     ("wilmot_proviso", "Slavery in the new territories (Wilmot Proviso)", ["wilmot proviso", "slavery territories"], ["slavery", "territory", "proviso"]),
  110|     ("mexican_war", "The Mexican War and its costs", ["mexican war", "war debt mexico"], ["war", "mexico", "soldiers"]),
  111|     ("tariff", "The tariff of 1846", ["tariff of 1846", "tariff"], ["duties", "manufactures"]),
  112|     ("california_gold", "California and the gold discovery", ["california gold"], ["gold", "mines"]),
  113|     ("internal_improvements", "Rivers, harbors and internal improvements", ["rivers and harbors", "internal improvements"], ["harbor", "river"]),
  114|     ("immigration_ireland", "Irish famine and immigration", ["ireland famine", "emigrants"], ["irish", "emigrants"]),
  115|     ("public_lands", "Public lands and homesteads", ["public lands settlers"], ["lands", "settlers"]),
  116|     ("europe_revolutions", "Revolutions in Europe", ["revolution france", "revolution europe"], ["republic", "france"]),
  117| ])
  118| year(1852, "1852-11-02", ["Pierce", "King", "Scott", "Graham", "Hale", "Julian", "Fillmore", "Whig", "Whigs",
  119|                           "Free Soil", "Free Soilers", "Free Democracy"] + GENERIC_PARTY, [
  120|     ("fugitive_slave_law", "The Fugitive Slave Law", ["fugitive slave law", "fugitive slave"], ["slave", "fugitive"]),
  121|     ("compromise_1850", "Finality of the Compromise of 1850", ["compromise measures", "compromise finality"], ["compromise", "agitation"]),
  122|     ("tariff", "The tariff", ["tariff", "protection iron"], ["duties", "iron"]),
  123|     ("foreigners", "Immigration and naturalization", ["foreigners naturalization", "adopted citizens"], ["foreign", "germans", "irish"]),
  124|     ("temperance", "Temperance and the Maine Law", ["maine law", "liquor law temperance"], ["liquor", "temperance"]),
  125|     ("internal_improvements", "Rivers, harbors and railroads", ["rivers and harbors", "railroad"], ["harbor", "railroad"]),
  126|     ("homestead", "Homestead / free land", ["homestead bill", "public lands"], ["lands", "homestead"]),
  127|     ("cuba", "Cuba and filibusters", ["cuba"], ["spain", "filibuster"]),
  128| ])
  129| year(1856, "1856-11-04", ["Buchanan", "Breckinridge", "Fremont", "Frémont", "Dayton", "Fillmore", "Donelson",
  130|                           "Pierce", "Know Nothing", "Know Nothings", "American party", "Black Republican",
  131|                           "Whig", "Whigs"] + GENERIC_PARTY, [
  132|     ("kansas", "Violence and slavery in Kansas", ["kansas border ruffians", "kansas"], ["lawrence", "free state", "ruffians"]),
  133|     ("slavery_extension", "Extension of slavery into the territories", ["slavery extension territories", "nebraska bill"], ["slavery", "territories"]),
  134|     ("sumner_assault", "The assault on Sumner", ["sumner brooks assault"], ["senate", "assault"]),
  135|     ("disunion", "Threats of disunion", ["disunion", "dissolution of the union"], ["union", "south"]),
  136|     ("foreigners_catholics", "Foreigners and Catholics (nativism)", ["foreigners naturalization", "catholics"], ["foreign", "catholic"]),
  137|     ("temperance", "Temperance / Maine Law", ["maine law", "liquor law"], ["liquor", "temperance"]),
  138|     ("pacific_railroad", "A Pacific railroad", ["pacific railroad"], ["railroad", "pacific"]),
  139|     ("cuba_ostend", "Cuba and the Ostend Manifesto", ["cuba ostend", "cuba"], ["spain", "cuba"]),
  140| ])
  141| year(1860, "1860-11-06", ["Lincoln", "Hamlin", "Douglas", "Johnson", "Breckinridge", "Lane", "Bell", "Everett",
  142|                           "Buchanan", "Constitutional Union", "Black Republican", "Wide Awake", "Wide Awakes",
  143|                           "Fusion"] + GENERIC_PARTY, [
  144|     ("slavery_territories", "Slavery in the territories", ["slavery territories", "slave code territories"], ["slavery", "territories"]),
  145|     ("secession", "Secession and disunion", ["secession", "disunion"], ["union", "dissolution"]),
  146|     ("homestead", "The homestead bill", ["homestead bill", "free homes"], ["lands", "settlers"]),
  147|     ("tariff", "Protective tariff", ["protective tariff", "tariff"], ["duties", "iron"]),
  148|     ("john_brown", "John Brown and slave insurrection fears", ["john brown", "insurrection"], ["harper", "insurrection"]),
  149|     ("pacific_railroad", "A Pacific railroad", ["pacific railroad"], ["railroad", "pacific"]),
  150|     ("slave_trade", "Reopening the slave trade", ["african slave trade"], ["slave", "trade"]),
  151|     ("hard_times", "Crops, money and business", ["crops prices money market"], ["crop", "prices"]),
  152| ])
  153| year(1864, "1864-11-08", ["Lincoln", "Johnson", "McClellan", "Pendleton", "Fremont", "Frémont", "Union party",
  154|                           "Copperhead", "Copperheads"] + GENERIC_PARTY, [
  155|     ("war_peace", "Peace negotiations vs. continuing the war", ["peace negotiations", "armistice"], ["peace", "war"]),
  156|     ("draft", "The draft and substitutes", ["draft conscription", "drafted substitutes"], ["draft", "quota"]),
  157|     ("emancipation", "Emancipation and abolition", ["emancipation", "abolition slavery"], ["slaves", "freedom"]),
  158|     ("soldiers_vote", "Soldiers voting in the field", ["soldiers vote"], ["soldiers", "field"]),
  159|     ("prices_currency", "Prices, gold and greenbacks", ["gold premium", "high prices"], ["greenbacks", "currency"]),
  160|     ("arbitrary_arrests", "Arbitrary arrests and civil liberties", ["arbitrary arrests", "habeas corpus"], ["arrest", "military"]),
  161|     ("war_news", "The military campaigns (Atlanta, Shenandoah)", ["atlanta sherman", "sheridan valley"], ["army", "rebels"]),
  162|     ("taxes_debt", "War taxes and the debt", ["taxes war debt", "internal revenue"], ["tax", "debt"]),
  163| ])
  164| year(1868, "1868-11-03", ["Grant", "Colfax", "Seymour", "Blair", "Johnson"] + GENERIC_PARTY, [
  165|     ("reconstruction", "Reconstruction of the South", ["reconstruction acts", "reconstruction"], ["military", "southern"]),
  166|     ("negro_suffrage", "Black suffrage", ["negro suffrage", "colored voters"], ["negro", "suffrage", "colored"]),
  167|     ("bonds_greenbacks", "Paying the bonds in greenbacks", ["bonds greenbacks", "five-twenty bonds"], ["bonds", "greenbacks", "currency"]),
  168|     ("taxes", "Taxes and the public debt", ["taxation public debt", "internal revenue tax"], ["tax", "debt"]),
  169|     ("ku_klux", "Ku Klux violence", ["ku klux", "outrages"], ["klan", "murdered"]),
  170|     ("impeachment", "The impeachment of the president", ["impeachment"], ["senate", "acquittal"]),
  171|     ("indian_war", "Indian wars on the plains", ["indian war", "indians"], ["indians", "frontier"]),
  172|     ("tariff", "Tariff and protection", ["tariff", "protection"], ["duties", "wool"]),
  173| ])
  174| year(1872, "1872-11-05", ["Grant", "Wilson", "Greeley", "Brown", "O'Conor", "Liberal Republican",
  175|                           "Liberal Republicans", "Liberals"] + GENERIC_PARTY, [
  176|     ("amnesty", "Amnesty for former Confederates", ["amnesty"], ["disabilities", "southern"]),
  177|     ("ku_klux", "Ku Klux prosecutions and violence", ["ku klux"], ["klan", "outrages"]),
  178|     ("civil_service_reform", "Civil service reform", ["civil service reform"], ["office", "reform"]),
  179|     ("credit_mobilier", "Corruption: Credit Mobilier", ["credit mobilier"], ["congress", "stock"]),
  180|     ("tammany", "The Tammany Ring", ["tammany ring", "tweed"], ["ring", "frauds"]),
  181|     ("tariff_free_trade", "Tariff vs. free trade", ["free trade", "tariff"], ["duties", "protection"]),
  182|     ("currency", "Specie payments and currency", ["specie payments", "greenbacks"], ["currency", "gold"]),
  183|     ("eight_hour", "Labor and the eight-hour day", ["eight hour", "workingmen"], ["labor", "hours"]),
  184| ])
  185| year(1876, "1876-11-07", ["Hayes", "Wheeler", "Tilden", "Hendricks", "Cooper", "Grant", "Greenback party",
  186|                           "Greenbackers"] + GENERIC_PARTY, [
  187|     ("southern_violence", "Southern elections, rifle clubs and violence", ["rifle clubs", "hamburg massacre"], ["negroes", "colored"]),
  188|     ("reconstruction", "Carpet-bag rule and Reconstruction", ["carpet bag", "carpet-baggers"], ["southern", "state government"]),
  189|     ("hard_times", "Hard times and unemployment", ["hard times", "out of employment"], ["work", "wages"]),
  190|     ("currency", "Resumption and greenbacks", ["resumption act", "greenbacks"], ["specie", "currency"]),
  191|     ("corruption", "Corruption and reform (Whisky Ring, Belknap)", ["whisky ring", "belknap"], ["fraud", "reform"]),
  192|     ("indian_war", "The Sioux war", ["sioux war", "custer"], ["indians", "sioux"]),
  193|     ("schools_sectarian", "Public schools and sectarian funds", ["public schools sectarian"], ["schools", "catholic"]),
  194|     ("tariff", "Tariff", ["tariff"], ["duties", "protection"]),
  195| ])
  196| year(1880, "1880-11-02", ["Garfield", "Arthur", "Hancock", "English", "Weaver", "Hayes", "Greenback party",
  197|                           "Greenbackers", "Morey"] + GENERIC_PARTY, [
  198|     ("tariff", "Tariff for revenue vs. protection", ["tariff for revenue", "protective tariff"], ["duties", "protection"]),
  199|     ("solid_south", "The Solid South and southern elections", ["solid south"], ["southern", "bourbon"]),
  200|     ("chinese", "Chinese immigration", ["chinese immigration", "chinese"], ["chinese", "coolie"]),
  201|     ("currency", "Greenbacks and resumption", ["greenbacks resumption", "national banks"], ["currency", "specie"]),
  202|     ("civil_service", "Civil service reform", ["civil service reform"], ["office", "reform"]),
  203|     ("exodus", "The Black exodus from the South", ["negro exodus", "exodusters"], ["colored", "kansas"]),
  204|     ("state_rights", "State rights and federal elections", ["state rights", "federal elections"], ["states", "constitution"]),
  205|     ("labor", "Workingmen and wages", ["workingmen wages"], ["labor", "wages"]),
  206| ])
  207| year(1884, "1884-11-04", ["Cleveland", "Hendricks", "Blaine", "Logan", "Butler", "St. John", "Arthur",
  208|                           "Mugwump", "Mugwumps", "Greenback party", "Prohibition party"] + GENERIC_PARTY, [
  209|     ("tariff", "Tariff and protection", ["tariff", "protection american industry"], ["duties", "wool"]),
  210|     ("civil_service", "Civil service reform", ["civil service reform"], ["office", "spoils"]),
  211|     ("labor", "Labor and contract labor", ["contract labor", "workingmen wages"], ["labor", "wages"]),
  212|     ("chinese", "Chinese immigration", ["chinese immigration"], ["chinese", "coolies"]),
  213|     ("prohibition", "Prohibition", ["prohibition"], ["liquor", "temperance"]),
  214|     ("monopolies", "Railroads and monopolies", ["monopolies", "railroad monopoly"], ["corporations", "rates"]),
  215|     ("solid_south", "The Solid South and the colored vote", ["solid south", "colored voters"], ["southern", "negro"]),
  216|     ("silver", "Silver coinage", ["silver coinage", "silver dollar"], ["silver", "currency"]),
  217| ])
  218| year(1888, "1888-11-06", ["Harrison", "Morton", "Cleveland", "Thurman", "Fisk", "Prohibition party",
  219|                           "Union Labor"] + GENERIC_PARTY, [
  220|     ("tariff_reform", "Tariff reform / the Mills bill", ["tariff reform", "mills bill"], ["duties", "protection"]),
  221|     ("surplus", "The Treasury surplus", ["treasury surplus"], ["surplus", "taxation"]),
  222|     ("wool_protection", "Wool, wages and protection", ["wool tariff", "free wool"], ["wool", "wages"]),
  223|     ("pensions", "Soldiers' pensions", ["pension veto", "soldiers pensions"], ["pension", "veterans"]),
  224|     ("trusts", "Trusts", ["trusts"], ["trust", "monopoly"]),
  225|     ("chinese", "Chinese exclusion", ["chinese exclusion"], ["chinese", "coolies"]),
  226|     ("prohibition", "Prohibition", ["prohibition"], ["liquor", "saloon"]),
  227|     ("civil_service", "Civil service reform", ["civil service reform"], ["office", "reform"]),
  228| ])
  229| year(1892, "1892-11-08", ["Cleveland", "Stevenson", "Harrison", "Reid", "Weaver", "Field", "Bidwell",
  230|                           "Populist", "Populists", "People's party", "Peoples party", "Prohibition party"]
  231|      + GENERIC_PARTY, [
  232|     ("tariff", "The McKinley tariff", ["mckinley tariff", "tariff reform"], ["duties", "protection"]),
  233|     ("force_bill", "The Force Bill / federal elections", ["force bill"], ["federal", "elections"]),
  234|     ("silver", "Free silver", ["free silver", "silver coinage"], ["silver", "currency"]),
  235|     ("homestead_strike", "The Homestead strike and labor", ["homestead strike", "pinkertons"], ["strikers", "labor"]),
  236|     ("farmers_alliance", "Farmers' Alliance and the sub-treasury", ["farmers alliance", "sub-treasury"], ["farmers", "alliance"]),
  237|     ("pensions", "Pensions", ["pensions"], ["pension", "soldiers"]),
  238|     ("prohibition", "Prohibition", ["prohibition"], ["liquor", "saloon"]),
  239|     ("railroads_monopolies", "Railroads and monopolies", ["railroad monopolies", "trusts"], ["rates", "corporations"]),
  240| ])
  241| year(1896, "1896-11-03", ["McKinley", "Hobart", "Bryan", "Sewall", "Watson", "Palmer", "Buckner", "Cleveland",
  242|                           "Populist", "Populists", "People's party", "Peoples party", "Popocrat", "Popocrats"]
  243|      + GENERIC_PARTY, [
  244|     ("free_silver", "Free silver at 16 to 1", ["free coinage silver", "free silver"], ["silver", "coinage", "16 to 1"]),
  245|     ("gold_standard", "The gold standard / sound money", ["gold standard", "sound money"], ["gold", "money"]),
  246|     ("tariff", "Protective tariff", ["protective tariff", "protection"], ["duties", "tariff"]),
  247|     ("farm_prices", "Farm prices and mortgages", ["price of wheat", "farmers mortgages"], ["wheat", "cotton", "prices"]),
  248|     ("trusts_railroads", "Trusts and railroads", ["trusts monopolies", "railroad rates"], ["corporations", "trust"]),
  249|     ("labor_injunctions", "Labor and government by injunction", ["government by injunction", "workingmen wages"], ["labor", "injunction"]),
  250|     ("income_tax", "The income tax and the Supreme Court", ["income tax"], ["income", "court"]),
  251|     ("bonds_reserve", "Bond issues and the gold reserve", ["bond issue gold reserve", "bonds"], ["bonds", "reserve"]),
  252| ])
  253| year(1900, "1900-11-06", ["McKinley", "Roosevelt", "Bryan", "Stevenson", "Debs", "Woolley", "Populist",
  254|                           "Populists"] + GENERIC_PARTY, [
  255|     ("imperialism", "Imperialism and the Philippines", ["imperialism", "philippines"], ["filipinos", "colonies"]),
  256|     ("trusts", "Trusts", ["trusts"], ["trust", "monopoly"]),
  257|     ("free_silver", "Free silver", ["free silver"], ["silver", "coinage"]),
  258|     ("prosperity", "Prosperity and wages (full dinner pail)", ["full dinner pail", "prosperity wages"], ["wages", "work"]),
  259|     ("coal_strike", "The anthracite coal strike", ["anthracite strike", "coal miners strike"], ["miners", "strike"]),
  260|     ("china", "China and the Boxer crisis", ["china boxers", "pekin"], ["china", "troops"]),
  261|     ("boers", "The Boer War", ["boers"], ["boer", "england"]),
  262|     ("disfranchisement", "Black disfranchisement in the South", ["disfranchise negro", "suffrage amendment"], ["negro", "suffrage"]),
  263| ])
  264| year(1904, "1904-11-08", ["Roosevelt", "Fairbanks", "Parker", "Davis", "Debs", "Swallow", "Watson",
  265|                           "Populist", "Populists"] + GENERIC_PARTY, [
  266|     ("trusts", "Trusts and corporations", ["trusts", "beef trust"], ["trust", "corporations"]),
  267|     ("tariff", "Tariff revision", ["tariff revision", "tariff"], ["duties", "protection"]),
  268|     ("philippines", "The Philippines", ["philippines"], ["filipinos", "islands"]),
  269|     ("panama_canal", "The Panama Canal", ["panama canal"], ["canal", "isthmus"]),
  270|     ("labor_strikes", "Strikes and labor (Colorado, packinghouse)", ["strike miners", "packing house strike"], ["strike", "union"]),
  271|     ("race_suffrage", "Race and the suffrage in the South", ["negro question", "disfranchisement"], ["negro", "suffrage"]),
  272|     ("pensions", "Pensions (Order No. 78)", ["pension order"], ["pension", "veterans"]),
  273|     ("cost_of_living", "Prices and wages", ["cost of living", "prices wages"], ["prices", "wages"]),
  274| ])
  275| year(1908, "1908-11-03", ["Taft", "Sherman", "Bryan", "Kern", "Debs", "Chafin", "Roosevelt", "Hisgen",
  276|                           "Independence party"] + GENERIC_PARTY, [
  277|     ("trusts", "Trusts and corporations", ["trusts", "standard oil"], ["trust", "corporations"]),
  278|     ("tariff_revision", "Tariff revision", ["tariff revision"], ["duties", "schedules"]),
  279|     ("bank_guaranty", "Bank deposit guaranty after the 1907 panic", ["guaranty of bank deposits", "guarantee deposits"], ["deposits", "banks"]),
  280|     ("labor_injunctions", "Labor and injunctions", ["injunction labor", "injunctions"], ["labor", "courts"]),
  281|     ("railroad_rates", "Railroad rates and regulation", ["railroad rates"], ["rates", "commission"]),
  282|     ("prohibition", "Local and county option", ["local option", "county option"], ["saloon", "liquor"]),
  283|     ("campaign_contributions", "Publicity of campaign contributions", ["campaign contributions publicity"], ["contributions", "funds"]),
  284|     ("conservation", "Conservation of forests and water", ["conservation natural resources", "forests irrigation"], ["forests", "water"]),
  285| ])
  286| year(1912, "1912-11-05", ["Wilson", "Marshall", "Taft", "Sherman", "Butler", "Roosevelt", "Johnson", "Debs",
  287|                           "Seidel", "Chafin", "Progressive party", "Progressives", "Bull Moose",
  288|                           "Bull Moosers"] + GENERIC_PARTY, [
  289|     ("trusts", "Trusts and monopoly", ["trusts", "anti-trust"], ["trust", "monopoly"]),
  290|     ("tariff_cost_of_living", "Tariff and the high cost of living", ["high cost of living", "tariff revision"], ["prices", "duties"]),
  291|     ("direct_democracy", "Initiative, referendum and recall", ["initiative referendum recall"], ["recall", "referendum"]),
  292|     ("woman_suffrage", "Votes for women", ["woman suffrage", "votes for women"], ["suffrage", "women"]),
  293|     ("labor", "Child labor, wages and hours", ["child labor", "minimum wage"], ["labor", "wages"]),
  294|     ("income_tax", "The income tax amendment", ["income tax amendment"], ["income", "amendment"]),
  295|     ("currency_banking", "Currency reform and the money trust", ["currency reform", "money trust"], ["banks", "currency"]),
  296|     ("prohibition", "Saloons and local option", ["local option saloon", "prohibition"], ["saloon", "liquor"]),
  297| ])
  298| year(1916, "1916-11-07", ["Wilson", "Marshall", "Hughes", "Fairbanks", "Benson", "Hanly", "Roosevelt",
  299|                           "Progressive party", "Progressives", "Bull Moose"] + GENERIC_PARTY, [
  300|     ("preparedness", "Military preparedness", ["preparedness army navy"], ["preparedness", "navy"]),
  301|     ("european_war", "The European war and neutrality", ["neutrality", "submarine"], ["war", "neutral"]),
  302|     ("mexico", "Mexico and the border", ["mexican border", "villa"], ["mexico", "border", "guardsmen"]),
  303|     ("eight_hour_law", "The eight-hour railroad law", ["eight hour law", "adamson"], ["railroad", "brotherhoods"]),
  304|     ("hyphenates", "German-Americans and the hyphen", ["hyphenated", "german american"], ["hyphen", "german"]),
  305|     ("woman_suffrage", "Woman suffrage", ["woman suffrage"], ["suffrage", "women"]),
  306|     ("tariff", "Tariff", ["tariff"], ["duties", "protection"]),
  307|     ("prohibition", "Prohibition amendments", ["prohibition amendment", "dry"], ["saloon", "liquor"]),
  308| ])
  309| year(1928, "1928-11-06", ["Hoover", "Curtis", "Smith", "Robinson", "Thomas", "Coolidge", "Raskob",
  310|                           "Tammany"] + GENERIC_PARTY, [
  311|     ("prohibition", "Prohibition and enforcement", ["prohibition enforcement", "wet dry"], ["liquor", "eighteenth"]),
  312|     ("religion", "Religion in the campaign", ["catholic religious issue", "religious intolerance"], ["catholic", "protestant"]),
  313|     ("farm_relief", "Farm relief (McNary-Haugen)", ["farm relief", "mcnary-haugen"], ["farmers", "surplus"]),
  314|     ("prosperity", "Prosperity and business", ["prosperity", "business conditions"], ["prosperity", "employment"]),
  315|     ("tariff", "Tariff", ["tariff"], ["duties", "protection"]),
  316|     ("water_power", "Water power and Muscle Shoals", ["muscle shoals", "water power"], ["power", "utilities"]),
  317|     ("immigration", "Immigration restriction", ["immigration restriction", "national origins"], ["immigration", "quota"]),
  318|     ("women_voters", "Women voters", ["women voters"], ["women", "register"]),
  319| ])
  320| year(1932, "1932-11-08", ["Roosevelt", "Garner", "Hoover", "Curtis", "Thomas", "Foster", "Coolidge",
  321|                           "Raskob"] + GENERIC_PARTY, [
  322|     ("unemployment_relief", "Unemployment and relief", ["unemployment relief", "jobless"], ["unemployed", "relief"]),
  323|     ("farm_crisis", "Farm prices and foreclosures", ["farm holiday", "farm mortgage foreclosure"], ["farmers", "prices"]),
  324|     ("prohibition_repeal", "Repeal of prohibition", ["prohibition repeal", "repeal eighteenth amendment"], ["repeal", "liquor"]),
  325|     ("banks", "Bank failures and hoarding", ["bank failure depositors", "hoarding"], ["bank", "deposits"]),
  326|     ("veterans_bonus", "The veterans' bonus and the Bonus Army", ["bonus army", "veterans bonus"], ["bonus", "veterans"]),
  327|     ("tariff", "Tariff", ["tariff"], ["duties", "smoot"]),
  328|     ("rfc_public_works", "Federal loans and public works (RFC)", ["reconstruction finance corporation", "public works"], ["loans", "works"]),
  329|     ("taxes_economy", "Taxes and government economy", ["sales tax", "taxes economy"], ["tax", "budget"]),
  330| ])
  331| year(1936, "1936-11-03", ["Roosevelt", "Garner", "Landon", "Knox", "Lemke", "Thomas", "Browder", "Hoover",
  332|                           "Union party", "New Deal", "New Dealers"] + GENERIC_PARTY, [
  333|     ("social_security", "Social security and old-age pensions", ["social security", "old age pension"], ["pension", "security"]),
  334|     ("townsend_plan", "The Townsend plan", ["townsend plan"], ["townsend", "pension"]),
  335|     ("relief_wpa", "Relief and the WPA", ["works progress administration", "relief"], ["relief", "wpa"]),
  336|     ("drought_farm", "Drought and farm programs", ["drought", "agricultural adjustment"], ["farmers", "drought"]),
  337|     ("labor_organizing", "Labor organizing (CIO)", ["labor union organize", "cio"], ["union", "labor"]),
  338|     ("spending_debt", "Spending and the national debt", ["national debt", "government spending"], ["debt", "spending"]),
  339|     ("trade_agreements", "Reciprocal trade agreements", ["reciprocal trade agreements"], ["trade", "tariff"]),
  340|     ("supreme_court", "The Supreme Court and the NRA/AAA", ["supreme court decision", "nra"], ["court", "constitution"]),
  341| ])
  342| year(1940, "1940-11-05", ["Roosevelt", "Wallace", "Willkie", "McNary", "Thomas", "Browder", "Garner",
  343|                           "New Deal", "New Dealers"] + GENERIC_PARTY, [
  344|     ("aid_to_britain", "Aid to Britain / destroyers deal", ["aid to britain", "destroyers"], ["britain", "aid"]),
  345|     ("draft", "The peacetime draft", ["selective service registration", "conscription"], ["draft", "registration"]),
  346|     ("third_term", "The third-term tradition", ["third term"], ["tradition", "term"]),
  347|     ("defense_jobs", "Defense spending and jobs", ["national defense contracts", "unemployment"], ["defense", "jobs"]),
  348|     ("keep_out_of_war", "Keeping out of the war", ["keep out of war", "isolation"], ["war", "peace"]),
  349|     ("farm_prices", "Farm prices", ["farm prices"], ["farmers", "prices"]),
  350|     ("labor", "Labor, wages and hours", ["wages hours", "labor union"], ["labor", "wages"]),
  351|     ("relief_wpa", "Relief and the WPA", ["wpa relief"], ["relief", "wpa"]),
  352| ])
  353| year(1944, "1944-11-07", ["Roosevelt", "Truman", "Dewey", "Bricker", "Thomas", "Wallace",
  354|                           "New Deal", "New Dealers"] + GENERIC_PARTY, [
  355|     ("soldier_vote", "Servicemen voting", ["soldier vote", "absentee ballots servicemen"], ["ballots", "servicemen"]),
  356|     ("postwar_jobs", "Postwar jobs and reconversion", ["postwar jobs", "reconversion"], ["jobs", "postwar"]),
  357|     ("world_organization", "A postwar world organization", ["dumbarton oaks", "world organization peace"], ["peace", "nations"]),
  358|     ("rationing_prices", "Rationing and price control", ["rationing", "price control opa"], ["ration", "prices"]),
  359|     ("labor_pac", "Labor and the CIO-PAC", ["political action committee", "labor union"], ["labor", "union"]),
  360|     ("taxes", "Taxes", ["taxes"], ["tax", "income"]),
  361|     ("veterans", "Veterans' benefits (GI Bill)", ["veterans benefits", "gi bill"], ["veterans", "benefits"]),
  362|     ("farm_prices", "Farm prices", ["farm prices"], ["farmers", "prices"]),
  363| ])
  364| year(1948, "1948-11-02", ["Truman", "Barkley", "Dewey", "Warren", "Thurmond", "Wright", "Wallace", "Taylor",
  365|                           "Dixiecrat", "Dixiecrats", "States' Rights", "States Rights", "Progressive party",
  366|                           "Progressives"] + GENERIC_PARTY, [
  367|     ("inflation", "High prices and inflation", ["high prices inflation", "cost of living"], ["prices", "inflation"]),
  368|     ("housing", "The housing shortage", ["housing shortage"], ["housing", "homes"]),
  369|     ("taft_hartley", "Taft-Hartley and labor", ["taft-hartley"], ["labor", "union"]),
  370|     ("civil_rights", "Civil rights and the poll tax", ["civil rights", "poll tax"], ["negro", "rights"]),
  371|     ("berlin_cold_war", "Berlin and the Soviet Union", ["berlin airlift", "russia"], ["soviet", "berlin"]),
  372|     ("communism_home", "Communists at home", ["un-american activities", "communists"], ["communist", "spy"]),
  373|     ("farm_price_supports", "Farm price supports", ["price supports", "farm prices"], ["farmers", "supports"]),
  374|     ("draft", "The peacetime draft", ["draft registration", "selective service"], ["draft", "registration"]),
  375| ])
  376| year(1952, "1952-11-04", ["Eisenhower", "Ike", "Nixon", "Stevenson", "Sparkman", "Truman", "Hallinan",
  377|                           "Taft", "Kefauver"] + GENERIC_PARTY, [
  378|     ("korea", "The Korean War", ["korea war", "korea truce"], ["korea", "troops"]),
  379|     ("communism", "Communists in government", ["communists in government", "communism"], ["communist", "loyalty"]),
  380|     ("corruption", "Corruption in government", ["corruption", "mink coat"], ["corruption", "scandal"]),
  381|     ("inflation_controls", "Prices, inflation and controls", ["price controls", "inflation"], ["prices", "controls"]),
  382|     ("taxes", "Taxes", ["taxes"], ["tax", "income"]),
  383|     ("tidelands_oil", "Tidelands oil", ["tidelands oil"], ["tidelands", "oil"]),
  384|     ("civil_rights", "Civil rights and FEPC", ["fepc", "civil rights"], ["rights", "negro"]),
  385|     ("farm_prices", "Farm price supports", ["farm price supports", "farm prices"], ["farmers", "prices"]),
  386| ])
  387| year(1956, "1956-11-06", ["Eisenhower", "Ike", "Nixon", "Stevenson", "Kefauver", "Truman"] + GENERIC_PARTY, [
  388|     ("suez_hungary", "Suez and Hungary", ["suez", "hungary"], ["egypt", "soviet"]),
  389|     ("h_bomb_tests", "H-bomb tests and the draft", ["h-bomb tests", "hydrogen bomb tests"], ["bomb", "tests"]),
  390|     ("school_desegregation", "School desegregation", ["desegregation", "integration schools"], ["segregation", "schools"]),
  391|     ("farm_soil_bank", "Farm prices and the soil bank", ["soil bank", "farm prices"], ["farmers", "prices"]),
  392|     ("highways", "The highway program", ["highway program", "interstate highway"], ["highway", "roads"]),
  393|     ("labor", "Labor and wages", ["labor union wages"], ["union", "wages"]),
  394|     ("taxes", "Taxes and the budget", ["taxes balanced budget"], ["tax", "budget"]),
  395|     ("cost_of_living", "Cost of living", ["cost of living"], ["prices", "living"]),
  396| ])
  397| year(1960, "1960-11-08", ["Kennedy", "Johnson", "Nixon", "Lodge", "Eisenhower", "Ike", "Jack",
  398|                           "Kennedy-Johnson", "Nixon-Lodge"] + GENERIC_PARTY, [
  399|     ("cuba_castro", "Castro and Cuba", ["castro cuba"], ["castro", "cuba"]),
  400|     ("khrushchev_cold_war", "Khrushchev and the cold war", ["khrushchev", "soviet"], ["soviet", "khrushchev"]),
  401|     ("defense_missiles", "Missiles and national defense", ["missile gap", "missiles defense"], ["missile", "defense"]),
  402|     ("civil_rights", "Civil rights and sit-ins", ["sit-in", "civil rights"], ["negro", "rights"]),
  403|     ("religion", "Religion and the presidency", ["catholic president", "religious issue"], ["catholic", "religion"]),
  404|     ("economy_jobs", "Recession and unemployment", ["unemployment recession"], ["jobs", "unemployment"]),
  405|     ("farm_surplus", "Farm surplus and prices", ["farm surplus", "farm prices"], ["farmers", "surplus"]),
  406|     ("medical_care_aged", "Medical care for the aged", ["medical care aged", "social security medical"], ["aged", "medical"]),
  407| ])
  408| 
  409| # --------------------------------------------------------------------- http
  410| _last = {}
  411| INTERVAL = {"www.loc.gov": 3.2, "tile.loc.gov": 1.5}
  412| LOG: list = []
  413| 
  414| 
  415| def _sleep_for(host):
  416|     gap = INTERVAL.get(host, 1.5)
  417|     t = _last.get(host, 0)
  418|     now = time.time()
  419|     if now - t < gap:
  420|         time.sleep(gap - (now - t))
  421|     _last[host] = time.time()
  422| 
  423| 
  424| def fetch_json(url, cache_dir):
  425|     key = hashlib.sha1(url.encode()).hexdigest()
  426|     p = os.path.join(cache_dir, "http", key[:2], key + ".json")
  427|     if os.path.exists(p):
  428|         with open(p) as f:
  429|             rec = json.load(f)
  430|         return rec["body"], rec["ts"]
  431|     host = urllib.parse.urlparse(url).netloc
  432|     delay = 15
  433|     for attempt in range(8):
  434|         _sleep_for(host)
  435|         try:
  436|             req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
  437|             with urllib.request.urlopen(req, timeout=60) as r:
  438|                 raw = r.read().decode("utf-8", "replace")
  439|             body = json.loads(raw)
  440|             ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
  441|             os.makedirs(os.path.dirname(p), exist_ok=True)
  442|             with open(p, "w") as f:
  443|                 json.dump({"url": url, "ts": ts, "body": body}, f)
  444|             return body, ts
  445|         except urllib.error.HTTPError as e:
  446|             if e.code in (429, 500, 502, 503, 504, 520, 521, 522, 524, 525):
  447|                 ra = e.headers.get("Retry-After") if e.headers else None
  448|                 wait = max(delay, int(ra) if ra and ra.isdigit() else 0)
  449|                 print(f"  [http {e.code}] backoff {wait}s {url[:100]}", file=sys.stderr)
  450|                 time.sleep(wait)
  451|                 delay = min(delay * 2, 300)
  452|                 continue
  453|             if e.code == 404:
  454|                 return None, None
  455|             print(f"  [http {e.code}] giving up {url[:100]}", file=sys.stderr)
  456|             return None, None
  457|         except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, http.client.HTTPException) as e:
  458|             print(f"  [err {type(e).__name__}] backoff {delay}s {url[:100]}", file=sys.stderr)
  459|             time.sleep(delay)
  460|             delay = min(delay * 2, 300)
  461|     return None, None
  462| 
  463| 
  464| def search(q, y, state, cache_dir, c=20, facets=False):
  465|     cfg = Y[y]
  466|     params = [("q", q), ("dates", f"{y}-09-01/{cfg['cutoff'].isoformat()}"), ("fo", "json"), ("c", str(c)),
  467|               ("at", "results,pagination" + (",facets" if facets else ""))]
  468|     if state:
  469|         params.append(("fa", f"location_state:{state}"))
  470|     url = SEARCH + "?" + urllib.parse.urlencode(params)
  471|     body, ts = fetch_json(url, cache_dir)
  472|     total = None
  473|     res, fac = [], {}
  474|     if body:
  475|         total = (body.get("pagination") or {}).get("of")
  476|         res = body.get("results") or []
  477|         for f in body.get("facets") or []:
  478|             if f.get("field") == "location_state" or "location_state" in str(f.get("type", "")):
  479|                 for it in f.get("filters", []):
  480|                     fac[it.get("title", "").lower()] = it.get("count", 0)
  481|     LOG.append(dict(ts=ts, q=q, state=state or "—", total=total, returned=len(res)))
  482|     return res, fac
  483| 
  484| 
  485| def ocr_url_for(r):
  486|     w = r.get("word_coordinates_url") or ""
  487|     qs = urllib.parse.parse_qs(urllib.parse.urlparse(w).query)
  488|     seg = (qs.get("segment") or [None])[0]
  489|     if not seg:
  490|         return None
  491|     return ("https://tile.loc.gov/text-services/word-coordinates-service?segment="
  492|             + urllib.parse.quote(seg, safe="") + "&format=alto_xml&full_text=1")
  493| 
  494| 
  495| def fetch_ocr(url, cache_dir):
  496|     body, ts = fetch_json(url, cache_dir)
  497|     if not body or not isinstance(body, dict):
  498|         return None, ts
  499|     for v in body.values():
  500|         if isinstance(v, dict) and "full_text" in v:
  501|             return v["full_text"], ts
  502|     return None, ts
  503| 
  504| 
  505| # ------------------------------------------------------------------- text
  506| _DICT = None
  507| 
  508| 
  509| def words_dict():
  510|     global _DICT
  511|     if _DICT is None:
  512|         s = set()
  513|         for p in ("/usr/share/dict/words", "/usr/share/dict/web2"):
  514|             if os.path.exists(p):
  515|                 with open(p, errors="ignore") as f:
  516|                     s.update(w.strip().lower() for w in f)
  517|         s.update("a i the of and to in is was for on that by with as at from are be this which it "
  518|                  "he his they their has have had not but or an its were been will would who all".split())
  519|         _DICT = s
  520|     return _DICT
  521| 
  522| 
  523| def in_dict(w):
  524|     d = words_dict()
  525|     if w in d:
  526|         return True
  527|     for suf in ("'s", "s", "es", "ed", "d", "ing", "ly", "ies", "ers", "er", "ment", "ments"):
  528|         if w.endswith(suf) and len(w) - len(suf) >= 2:
  529|             b = w[: -len(suf)]
  530|             if b in d or (suf == "ies" and b + "y" in d) or (suf in ("ed", "ing") and b + "e" in d):
  531|                 return True
  532|     return False
  533| 
  534| 
  535| def normalize_ocr(t):
  536|     t = t.replace("^^", "").replace("^", " ").replace("\n", " ")
  537|     t = re.sub(r"(\w)- (\w)", r"\1\2", t)  # remaining line-break hyphens
  538|     return re.sub(r"\s+", " ", t).strip()
  539| 
  540| 
  541| STRAY = re.compile(r"^[\|■•»«\*\^_~`ijI!l1;:,\.'\"]{1,2}$")
  542| 
  543| 
  544| def clean_tokens(toks):
  545|     """Light cleaning: drop stray margin chars silently; collapse runs of garbage
  546|     tokens to [OCR illegible]. Returns (tokens, changed_with_brackets)."""
  547|     out, changed = [], False
  548|     for w in toks:
  549|         if STRAY.match(w) and w.lower() not in ("i", "a"):
  550|             continue
  551|         letters = sum(ch.isalpha() for ch in w)
  552|         bad = len(w) >= 3 and letters / len(w) < 0.5 and not re.match(r"^[\$\d,\.%-]+$", w)
  553|         if bad:
  554|             if not out or out[-1] != "[OCR illegible]":
  555|                 out.append("[OCR illegible]")
  556|                 changed = True
  557|             continue
  558|         out.append(w)
  559|     return out, changed
  560| 
  561| 
  562| def quality(toks):
  563|     al = [re.sub(r"[^a-z']", "", w.lower()).strip("'") for w in toks]
  564|     al = [w for w in al if len(w) >= 2]
  565|     if not al:
  566|         return 0.0
  567|     return sum(in_dict(w) for w in al) / len(al)
  568| 
  569| 
  570| AD_RX = re.compile(r"\b(pills?|sarsaparilla|druggists?|cures?d?|liniment|bitters|remedy|per bottle|"
  571|                    r"for sale|bargains?|ladies'? (?:hats|suits)|catarrh|rheumatism|kidney|dyspepsia|"
  572|                    r"sale price|special sale)\b", re.I)
  573| PRED_RX = re.compile(r"\b(electoral votes?|will carry|carry the state|majority of \d|plurality|"
  574|                      r"straw vote|poll shows|betting odds|even money)\b", re.I)
  575| 
  576| 
  577| def kw_list(topic):
  578|     """Search and extra keywords, cut to 7 letters so they match as word prefixes."""
  579|     _, _, queries, extra = topic
  580|     stop = {"the", "of", "and", "to", "in", "for", "by", "a", "on", "with", "out", "is"}
  581|     kws = {w[:7] for q in queries for w in re.split(r"[\s\-]+", q.lower()) if w and w not in stop and len(w) > 2}
  582|     kws.update(w.lower()[:7] for w in extra)
  583|     return sorted(kws)
  584| 
  585| 
  586| def best_window(toks, kws, W=125):
  587|     lows = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in toks]
  588|     hit = [1 if any(l.startswith(k.replace(" ", "")) for k in kws) and l else 0 for l in lows]
  589|     if len(toks) <= W:
  590|         return 0, len(toks), sum(hit)
  591|     pref = [0]
  592|     for h in hit:
  593|         pref.append(pref[-1] + h)
  594|     best, bs = -1, 0
  595|     for s in range(0, len(toks) - W + 1):
  596|         v = pref[s + W] - pref[s]
  597|         if v > best:
  598|             best, bs = v, s
  599|     # centre the window on the hits a little: shift start back to a sentence start
  600|     s = bs
  601|     for j in range(bs, max(bs - 25, -1), -1):
  602|         if j > 0 and re.search(r"[\.\?!]['\"]?$", toks[j - 1]) and toks[j][:1].isupper():
  603|             s = j
  604|             break
  605|     e = min(len(toks), s + 120)
  606|     for j in range(e, min(len(toks), s + 160)):
  607|         if re.search(r"[\.\?!]['\"]?$", toks[j - 1]):
  608|             e = j
  609|             break
  610|     else:
  611|         for j in range(e, max(s + 90, e - 30), -1):
  612|             if re.search(r"[\.\?!]['\"]?$", toks[j - 1]):
  613|                 e = j
  614|                 break
  615|     return s, e, pref[e] - pref[s]
  616| 
  617| 
  618| def cand_regex(y):
  619|     names = Y[y]["names"]
  620|     pat = r"\b(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + r")\b"
  621|     rx_names = re.compile(pat)
  622|     rx_gen = re.compile(r"\b(ticket|nominee|nominees|presidential candidate)\b", re.I)
  623|     return lambda t: bool(rx_names.search(t) or rx_gen.search(t))
  624| 
  625| 
  626| def lean_of(paper, y):
  627|     p = paper.lower()
  628|     if "springfield republican" in p:
  629|         return "ind"
  630|     if re.search(r"\b(labor|socialist|appeal to reason|worker|toiler|union record)\b", p):
  631|         return "ind"
  632|     if y >= 1856 and re.search(r"\brepublican\b", p) and "democrat" not in p:
  633|         return "R"
  634|     if re.search(r"\bdemocrat", p) and "republican" not in p:
  635|         return "D"
  636|     return "unknown"
  637| 
  638| 
  639| def shingles(text, n=5):
  640|     w = re.findall(r"[a-z]+", text.lower())
  641|     return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}
  642| 
  643| 
  644| # ------------------------------------------------------------------- build
  645| def first(v):
  646|     if isinstance(v, list):
  647|         return v[0] if v else None
  648|     return v
  649| 
  650| 
  651| def select(cands, topics, target):
  652|     """Up to `target` items: per topic, round-robin across the least-covered regions (candidate
  653|     mentions only once half the topic's quota is filled), then the leftovers by score; at most
  654|     4 items per paper and no near-duplicates (shingle overlap > 0.3)."""
  655|     per_topic = math.ceil(target / len(topics))
  656|     chosen, paper_n = [], {}
  657|     reg_n = {r: 0 for r in REGIONS + ["unknown"]}
  658| 
  659|     def ok(c):
  660|         if paper_n.get(c["lccn"], 0) >= 4:
  661|             return False
  662|         for o in chosen:
  663|             if o["lccn"] == c["lccn"] and o["date"] == c["date"] and o["page"] == c["page"]:
  664|                 return False
  665|             a, b = c["_sh"], o["_sh"]
  666|             if a and b and len(a & b) / max(1, min(len(a), len(b))) > 0.3:
  667|                 return False
  668|         return True
  669| 
  670|     leftovers = []
  671|     for topic in topics:
  672|         pool = sorted([c for c in cands if c["topic"] == topic[0]], key=lambda c: -c["_score"])
  673|         got = 0
  674|         while got < per_topic and pool:
  675|             regs = sorted(REGIONS, key=lambda r: reg_n[r])
  676|             pick = None
  677|             for reg in regs:
  678|                 for c in pool:
  679|                     if c["region"] == reg and ok(c) and not (c["mentions_candidates"] and got < per_topic // 2):
  680|                         pick = c
  681|                         break
  682|                 if pick:
  683|                     break
  684|             if not pick:
  685|                 for c in pool:
  686|                     if ok(c):
  687|                         pick = c
  688|                         break
  689|             if not pick:
  690|                 break
  691|             pool.remove(pick)
  692|             chosen.append(pick)
  693|             paper_n[pick["lccn"]] = paper_n.get(pick["lccn"], 0) + 1
  694|             reg_n[pick["region"]] = reg_n.get(pick["region"], 0) + 1
  695|             got += 1
  696|         leftovers += pool
  697|     for c in sorted(leftovers, key=lambda c: -c["_score"]):
  698|         if len(chosen) >= target:
  699|             break
  700|         if ok(c):
  701|             chosen.append(c)
  702|             paper_n[c["lccn"]] = paper_n.get(c["lccn"], 0) + 1
  703|     return chosen
  704| 
  705| 
  706| def build_year(y, cache_dir, out_dir, target=88, verbose=True):
  707|     cfg = Y[y]
  708|     LOG.clear()
  709|     start, cutoff = dt.date(y, 9, 1), cfg["cutoff"]
  710|     is_cand = cand_regex(y)
  711|     topics = cfg["topics"]
  712|     seen_pages = set()
  713|     cands = []
  714|     rejected = {"date": 0, "no_ocr": 0, "low_quality": 0, "few_hits": 0, "territory": 0}
  715|     used_states = {r: {} for r in REGIONS}
  716| 
  717|     def consider(r, ti, q):
  718|         rid = r.get("id") or ""
  719|         if rid in seen_pages:
  720|             return
  721|         seen_pages.add(rid)
  722|         d = r.get("date")
  723|         try:
  724|             dd = dt.date.fromisoformat(d)
  725|         except (TypeError, ValueError):  # missing or malformed date
  726|             rejected["date"] += 1
  727|             return
  728|         if not (start <= dd <= cutoff):
  729|             rejected["date"] += 1
  730|             return
  731|         state = (first(r.get("location_state")) or "").lower()
  732|         if state in ("hawaii", "alaska") and y < 1960:
  733|             rejected["territory"] += 1
  734|             return
  735|         ou = ocr_url_for(r)
  736|         if not ou:
  737|             rejected["no_ocr"] += 1
  738|             return
  739|         txt, ts = fetch_ocr(ou, cache_dir)
  740|         if not txt:
  741|             rejected["no_ocr"] += 1
  742|             return
  743|         toks = normalize_ocr(txt).split(" ")
  744|         kws = kw_list(topics[ti])
  745|         s, e, hits = best_window(toks, kws)
  746|         raw = toks[s:e]
  747|         qual = quality(raw)
  748|         if qual < 0.70:
  749|             rejected["low_quality"] += 1
  750|             return
  751|         if hits < 3:
  752|             rejected["few_hits"] += 1
  753|             return
  754|         ctoks, changed = clean_tokens(raw)
  755|         excerpt = " ".join(ctoks).strip()
  756|         nwords = len(excerpt.split())
  757|         if nwords < 60:
  758|             rejected["few_hits"] += 1
  759|             return
  760|         mc = is_cand(excerpt)
  761|         ads = len(AD_RX.findall(excerpt))
  762|         preds = len(PRED_RX.findall(excerpt))
  763|         score = hits / max(1, nwords) * 40 + (qual - 0.7) * 20 - 4 * mc - 2.5 * ads - 2 * preds
  764|         m = re.search(r"[?&]sp=(\d+)", rid)
  765|         sp = m.group(1) if m else "1"
  766|         lccn = first(r.get("number_lccn")) or ""
  767|         paper = first(r.get("partof_title")) or (r.get("title") or "")
  768|         url = re.sub(r"&q=.*$", "", r.get("url") or rid).replace("http://", "https://")
  769|         cands.append(dict(
  770|             id=f"ca-{lccn}-{d}-{sp}", year=y, date=d, paper=paper,
  771|             city=(first(r.get("location_city")) or "").title(), state=state.title(),
  772|             region=REGION.get(state, "unknown"), lccn=lccn, page=int(sp),
  773|             url=url, ocr_url=ou, topic=topics[ti][0], topic_code=f"T{ti + 1}",
  774|             topic_label=topics[ti][1], query=q, excerpt=excerpt, excerpt_words=nwords,
  775|             excerpt_is_verbatim=not changed, mentions_candidates=mc, leans=lean_of(paper, y),
  776|             ocr_quality=round(qual, 3), retrieved_at=ts, _score=score, _sh=shingles(excerpt)))
  777| 
  778|     for ti, topic in enumerate(topics):
  779|         label, desc, queries, extra = topic
  780|         if verbose:
  781|             print(f"[{y}] T{ti + 1} {label}", file=sys.stderr)
  782|         # loc.gov searches take ~30 s each server-side, so: national searches with
  783|         # larger pages first, then a state-facet search only for regions that
  784|         # are still short of candidates for this topic.
  785|         res, fac = search(queries[0], y, None, cache_dir, c=40, facets=True)
  786|         for r in res[:10]:
  787|             consider(r, ti, queries[0])
  788|         for q in queries[1:]:
  789|             rs, _ = search(q, y, None, cache_dir, c=30)
  790|             for r in rs[:8]:
  791|                 consider(r, ti, q)
  792|         for reg in REGIONS:
  793|             have = sum(1 for c in cands if c["topic"] == label and c["region"] == reg)
  794|             if have >= 2:
  795|                 continue
  796|             opts = [(c, s) for s, c in fac.items() if REGION.get(s) == reg and c > 0
  797|                     and not (s in ("hawaii", "alaska") and y < 1960)]
  798|             if not opts:
  799|                 continue
  800|             opts.sort(key=lambda cs: (used_states[reg].get(cs[1], 0), -cs[0]))
  801|             st = opts[0][1]
  802|             used_states[reg][st] = used_states[reg].get(st, 0) + 1
  803|             rs, _ = search(queries[0], y, st, cache_dir, c=15)
  804|             for r in rs[:6]:
  805|                 consider(r, ti, queries[0])
  806| 
  807|     chosen = select(cands, topics, target)
  808|     chosen.sort(key=lambda c: (c["topic_code"], c["date"], c["id"]))
  809|     assert all(c["date"] <= cutoff.isoformat() for c in chosen)
  810|     os.makedirs(out_dir, exist_ok=True)
  811|     outp = os.path.join(out_dir, f"corpus_{y}.jsonl")
  812|     with open(outp, "w") as f:
  813|         for c in chosen:
  814|             f.write(json.dumps({k: v for k, v in c.items() if not k.startswith("_")}, ensure_ascii=False) + "\n")
  815|     meta = dict(year=y, election=cfg["election"].isoformat(), cutoff=cutoff.isoformat(),
  816|                 n_items=len(chosen), n_candidates=len(cands), n_queries=len(LOG),
  817|                 pages_seen=len(seen_pages), rejected=rejected,
  818|                 topics=[dict(code=f"T{i + 1}", label=t[0], desc=t[1], queries=t[2],
  819|                              n=sum(c["topic"] == t[0] for c in chosen),
  820|                              regions={r: sum(c["topic"] == t[0] and c["region"] == r for c in chosen)
  821|                                       for r in REGIONS}) for i, t in enumerate(topics)],
  822|                 mentions_candidates=sum(c["mentions_candidates"] for c in chosen),
  823|                 verbatim=sum(c["excerpt_is_verbatim"] for c in chosen),
  824|                 leans={k: sum(c["leans"] == k for c in chosen) for k in ("R", "D", "ind", "unknown")},
  825|                 states=sorted({c["state"] for c in chosen}),
  826|                 date_range=[min((c["date"] for c in chosen), default=None),
  827|                             max((c["date"] for c in chosen), default=None)],
  828|                 queries=list(LOG))
  829|     with open(os.path.join(cache_dir, f"meta_{y}.json"), "w") as f:
  830|         json.dump(meta, f, indent=1, default=str)
  831|     print(f"[{y}] wrote {len(chosen)} items ({len(cands)} candidates, {len(LOG)} queries) -> {outp}",
  832|           file=sys.stderr)
  833|     return meta
  834| 
  835| 
  836| def provenance_md(years, cache_dir):
  837|     out = []
  838|     for y in years:
  839|         p = os.path.join(cache_dir, f"meta_{y}.json")
  840|         if not os.path.exists(p):
  841|             continue
  842|         with open(p) as f:
  843|             m = json.load(f)
  844|         ts = [q["ts"] for q in m["queries"] if q.get("ts")]
  845|         out.append(f"\n### corpus_{y}.jsonl\n")
  846|         out.append(f"- Election {m['election']}; cutoff {m['cutoff']}; search filter "
  847|                    f"`dates={y}-09-01/{m['cutoff']}`. Item dates {m['date_range'][0]} to {m['date_range'][1]}.")
  848|         out.append(f"- **{m['n_items']} items** from {m['n_candidates']} scored candidates "
  849|                    f"({m['pages_seen']} distinct pages returned); {m['n_queries']} searches"
  850|                    + (f", retrieved {min(ts)} to {max(ts)} UTC" if ts else "") + ".")
  851|         out.append(f"- Rejected before scoring: {m['rejected']}.")
  852|         out.append(f"- `mentions_candidates=true`: {m['mentions_candidates']}; verbatim: {m['verbatim']}; "
  853|                    f"leans: {m['leans']}; states ({len(m['states'])}): {', '.join(m['states'])}.")
  854|         out.append("\n| Code | topic | Items | NE | MW | S | W | Queries |\n|---|---|---|---|---|---|---|---|")
  855|         for t in m["topics"]:
  856|             r = t["regions"]
  857|             out.append(f"| {t['code']} | `{t['label']}` — {t['desc']} | {t['n']} | {r['Northeast']} | "
  858|                        f"{r['Midwest']} | {r['South']} | {r['West']} | {'; '.join('`'+q+'`' for q in t['queries'])} |")
  859|     return "\n".join(out)
  860| 
  861| 
  862| def main():
  863|     ap = argparse.ArgumentParser()
  864|     ap.add_argument("years", nargs="+", type=int)
  865|     ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
  866|     ap.add_argument("--out-dir", default=DEFAULT_OUT)
  867|     ap.add_argument("--target", type=int, default=88)
  868|     ap.add_argument("--provenance", action="store_true")
  869|     a = ap.parse_args()
  870|     os.makedirs(a.cache_dir, exist_ok=True)
  871|     if a.provenance:
  872|         print(provenance_md(a.years, a.cache_dir))
  873|         return
  874|     for y in a.years:
  875|         if y not in Y:
  876|             print(f"no config for {y}", file=sys.stderr)
  877|             continue
  878|         try:
  879|             build_year(y, a.cache_dir, a.out_dir, target=a.target)
  880|         except Exception as e:  # keep going across years
  881|             print(f"[{y}] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
  882| 
  883| 
  884| if __name__ == "__main__":
  885|     main()
```

## `scripts/harness/build_franchise.py`

```python
    1| """Build franchise/state_franchise_all.csv: the legal franchise by state, presidential years 1868–1968.
    2| 
    3| Columns: year,state,poll_tax,literacy_test,alien_voting,women_vote,white_can,black_can,
    4|          felony_disenfranchised_share,voting_age,chosen_by,source,note
    5| 
    6| Sources:
    7|   poll_tax, literacy_test: Gray & Jenkins (2024) State-Level Data File, doi:10.7910/DVN/QIY9EM,
    8|     rows elec_type==1 (presidential), 1872–1968. 1868 uses the state's 1870 row [I]
    9|     (the file starts in 1870). DC (1964, 1968): no poll tax, no literacy test.
   10|   women_vote: Teele (2018) presidential-suffrage year (franchise/women_suffrage_pre19th.csv)
   11|     <= election year; every state from 1920 (19th Amendment).
   12|   alien_voting: declarant-alien voting, Keyssar (2000) The Right to Vote, Table A.12, and
   13|     Hayduk (2006) Democracy for All, ch. 2 — year ranges transcribed from those tables
   14|     without the book to hand, so tagged [I] (Gray & Jenkins has no alien-voting field).
   15|   voting_age: 21; GA 18 from 1944 (1943 amendment); KY 18 from 1956 (1955 amendment);
   16|     AK 19 and HI 20 from 1960 (statehood constitutions).
   17|   black_can / white_can: 1 from 1870 (15th Amendment). 1868: Black men barred by law
   18|     outside New England (except CT), WI, NE, and the reconstructed South; NY's $250
   19|     property test for Black men [I]; ex-Confederate test oaths in MO, TN, WV, AR [I].
   20|   felony_disenfranchised_share: blank (no state-level estimate before 1970; Gray &
   21|     Jenkins' exfelon law flag is kept in the note).
   22|   chosen_by: from labels/state_pres_all.csv.
   23| 
   24| Run: ~/.venvs/simharness/bin/python scripts/harness/build_franchise.py
   25| """
   26| from __future__ import annotations
   27| 
   28| import sys
   29| from pathlib import Path
   30| 
   31| import numpy as np
   32| import pandas as pd
   33| 
   34| HERE = Path(__file__).resolve().parent
   35| sys.path.insert(0, str(HERE.parents[1]))  # the repo root
   36| from simharness.config import CACHE  # noqa: E402
   37| 
   38| FR = CACHE / 'franchise'
   39| OUT = FR / 'state_franchise_all.csv'
   40| YEARS = list(range(1868, 1969, 4))
   41| 
   42| # Declarant-alien voting for president: state → (first, last) election year it applied.
   43| # Keyssar (2000) Table A.12; Hayduk (2006) [I].
   44| ALIEN = {
   45|     'WI': (1848, 1908), 'MI': (1850, 1894), 'IN': (1851, 1921), 'MN': (1857, 1896), 'OR': (1859, 1914),
   46|     'KS': (1861, 1918), 'NE': (1867, 1918), 'MO': (1865, 1921), 'TX': (1869, 1921), 'AR': (1868, 1926),
   47|     'AL': (1867, 1901), 'FL': (1868, 1894), 'GA': (1868, 1877), 'SC': (1868, 1895), 'LA': (1879, 1898),
   48|     'CO': (1876, 1902), 'ND': (1889, 1909), 'SD': (1889, 1918),
   49| }
   50| # 1868: Black men legally able to vote (share of adult Black men) [I].
   51| BLACK_1868 = {s: 0.0 for s in ['CA', 'CT', 'DE', 'IL', 'IN', 'KS', 'KY', 'MD', 'MI', 'MO', 'NJ', 'NV', 'OH', 'OR',
   52|                                'PA', 'WV', 'IA', 'MN']}
   53| BLACK_1868['NY'] = 0.1  # $250 freehold test for Black men only [I]
   54| # 1868: whites barred by ex-Confederate test oaths [I].
   55| WHITE_1868 = {'MO': 0.80, 'TN': 0.70, 'WV': 0.85, 'AR': 0.85}
   56| 
   57| 
   58| def voting_age(state: str, year: int) -> int:
   59|     if year >= 1972:
   60|         return 18
   61|     if state == 'GA' and year >= 1944:
   62|         return 18
   63|     if state == 'KY' and year >= 1956:
   64|         return 18
   65|     if state == 'AK' and year >= 1960:
   66|         return 19
   67|     if state == 'HI' and year >= 1960:
   68|         return 20
   69|     return 21
   70| 
   71| 
   72| def main():
   73|     gj = pd.read_csv(FR / 'raw/GrayJenkins_State-Level_Data_File.tab', sep='\t')
   74|     icp = pd.read_csv(FR / 'grayjenkins_state_franchise_1916_1920_1924.csv').drop_duplicates('state')
   75|     code = dict(zip(icp.icpsr_state.astype(int), icp.state))
   76|     gj['st'] = gj.state.astype(int).map(code)
   77|     pres = gj[gj.elec_type == 1].set_index(['year', 'st'])
   78|     first70 = gj[gj.year == 1870].sort_values('elec_type').drop_duplicates('st').set_index('st')
   79|     w = pd.read_csv(FR / 'women_suffrage_pre19th.csv').set_index('state')
   80|     wy = w.presidential_suffrage_year.combine_first(w.full_suffrage_year).to_dict()
   81|     ret = pd.read_csv(CACHE / 'labels/state_pres_all.csv')
   82|     rows = []
   83|     for _, r in ret[ret.year.isin(YEARS)].iterrows():
   84|         y, s = int(r.year), r.state
   85|         notes, src = [], []
   86|         if s == 'DC':
   87|             pt, lt, ex = 0, 0, np.nan
   88|             src.append('DC: no poll tax or literacy test')
   89|         elif y == 1868:
   90|             g = first70.loc[s] if s in first70.index else None
   91|             pt, lt, ex = (np.nan, np.nan, np.nan) if g is None else (g.poll_tax, g.lit_test, g.exfelon)
   92|             src.append('Gray&Jenkins doi:10.7910/DVN/QIY9EM 1870 row [I]')
   93|         else:
   94|             g = pres.loc[(y, s)]
   95|             pt, lt, ex = g.poll_tax, g.lit_test, g.exfelon
   96|             src.append('Gray&Jenkins doi:10.7910/DVN/QIY9EM elec_type 1')
   97|         py = wy.get(s)
   98|         wv = int(y >= 1920 or (py is not None and pd.notna(py) and float(py) <= y))
   99|         if y == 1920 and s in ('GA', 'MS'):
  100|             notes.append('women could not register in time for Nov 1920 (closed_1920)')
  101|         src.append('women: Teele doi:10.7910/DVN/EVYI2H')
  102|         a = ALIEN.get(s)
  103|         av = int(a is not None and a[0] <= y <= a[1])
  104|         if a is not None:
  105|             src.append('alien: Keyssar 2000 Table A.12 / Hayduk 2006 [I]')
  106|         bc = BLACK_1868.get(s, 1.0) if y == 1868 else 1.0
  107|         wc = WHITE_1868.get(s, 1.0) if y == 1868 else 1.0
  108|         if y == 1868 and (s in BLACK_1868 or s in WHITE_1868):
  109|             notes.append('pre-15th Amendment exclusions [I]')
  110|         if pd.notna(ex):
  111|             notes.append(f'exfelon law (GJ)={int(ex)}')
  112|         rows.append({'year': y, 'state': s, 'poll_tax': pt, 'literacy_test': lt, 'alien_voting': av, 'women_vote': wv,
  113|                      'white_can': wc, 'black_can': bc, 'felony_disenfranchised_share': np.nan,
  114|                      'voting_age': voting_age(s, y), 'chosen_by': r.chosen_by, 'source': '; '.join(src),
  115|                      'note': '; '.join(notes)})
  116|     out = pd.DataFrame(rows)
  117|     for c in ('poll_tax', 'literacy_test'):
  118|         out[c] = out[c].astype('Int64')
  119|     out.to_csv(OUT, index=False)
  120|     print(f'wrote {OUT} ({len(out)} rows)')
  121|     print(out.groupby('year')[['poll_tax', 'literacy_test', 'alien_voting', 'women_vote']].sum().T.to_string())
  122|     print('missing poll_tax:', out[out.poll_tax.isna()][['year', 'state']].values.tolist())
  123| 
  124| 
  125| if __name__ == '__main__':
  126|     main()
```

## `scripts/harness/build_population.py`

```python
    1| """NHGIS extract → population/adults_<year>_by_state_nhgis.csv in the harness's
    2| long format (the columns of adults_1920_by_state.csv), one census at a time,
    3| 1790–1970. The 1920 and 1930 builder is here; the other censuses come from
    4| build_population_republic (1790–1860), _early (1870–1910) and _mid (1940–1970).
    5| The 1980+ tables are 18+ and only build_population_modern.py writes them.
    6| 
    7|     python3 scripts/harness/build_population.py 1930            # writes the table
    8|     python3 scripts/harness/build_population.py 1920 --check    # compares with the hand-keyed 1920 table
    9| 
   10| Every row says how it was made in `note`: "tabulated" (straight from a census
   11| table) or an [I]-tagged estimate (and from what).
   12| """
   13| import argparse
   14| 
   15| import pandas as pd
   16| 
   17| import build_population_early
   18| import build_population_mid
   19| import build_population_republic
   20| from nhgis_common import CACHE, COLS, STATE_CODE, assert_close, hand_vs_nhgis, load, off_cells, print_worst, rows
   21| 
   22| 
   23| def read(ds: str) -> pd.DataFrame:
   24|     d = load(ds)
   25|     d = d[d.STATE.str.casefold().isin(STATE_CODE)].copy()
   26|     d['state'] = d.STATE.str.casefold().map(STATE_CODE)
   27|     return d.set_index('state')
   28| 
   29| 
   30| def year_1920_1930(year: int) -> pd.DataFrame:
   31|     """Both censuses tabulate 21+ by sex × race/nativity and the foreign-born
   32|     white by sex × citizenship: complete, no estimates."""
   33|     if year == 1920:
   34|         d = read('ds43')
   35|         rn = {'M': ['A7P001', 'A7P002', 'A7P003', 'A7P004', 'A7P005'], 'F': ['A7P006', 'A7P007', 'A7P008', 'A7P009', 'A7P010']}
   36|         cz = {'M': ['A7Q001', 'A7Q002', 'A7Q003', 'A7Q004'], 'F': ['A7Q005', 'A7Q006', 'A7Q007', 'A7Q008']}
   37|         t_rn, t_cz = 'NHGIS 1920_cPHAM NT13', 'NHGIS 1920_cPHAM NT15'
   38|     else:
   39|         d = read('ds54')
   40|         # NT10's codebook labels interleave the sexes (BDQ001 NN male, BDQ002 NN female…), but
   41|         # the values run sex-major like 1920's: males BDQ001–005, females BDQ006–010. Checked
   42|         # below against NT7 (race by sex) and NT10 of 1930_cAge30 (white nativity by sex).
   43|         rn = {'M': ['BDQ001', 'BDQ002', 'BDQ003', 'BDQ004', 'BDQ005'], 'F': ['BDQ006', 'BDQ007', 'BDQ008', 'BDQ009', 'BDQ010']}
   44|         x = read('ds53')
   45|         for sex, (nn, nf, fb, ng, ot), (wn, wf, b, o) in (('M', rn['M'], ('BDD001', 'BDD003', 'BDL003', 'BDL005')),
   46|                                                           ('F', rn['F'], ('BDD002', 'BDD004', 'BDL004', 'BDL006'))):
   47|             for mine, theirs in (((nn, nf), (wn,)), ((fb,), (wf,)), ((ng,), (b,)), ((ot,), (o,))):
   48|                 assert_close(d[list(mine)].sum(axis=1), x[list(theirs)].sum(axis=1), f'1930 {sex}: {mine} vs {theirs}')
   49|         cz = {'M': ['BDR001', 'BDR002', 'BDR003', 'BDR004'], 'F': ['BDR005', 'BDR006', 'BDR007', 'BDR008']}
   50|         t_rn, t_cz = 'NHGIS 1930_cPAE NT10', 'NHGIS 1930_cPAE NT12'
   51|     out = []
   52|     for sex in ('M', 'F'):
   53|         nn, nf, fb, ng, ot = rn[sex]
   54|         out += rows(year, d, [(nn, sex, 'native_white_native_parentage', 'White: Native-born with native parentage'),
   55|                               (nf, sex, 'native_white_foreign_or_mixed_parentage', 'White: Native-born with foreign or mixed parentage'),
   56|                               (ng, sex, 'negro', 'Negro: Negro'),
   57|                               (ot, sex, 'other_races', 'Other: Indian, Chinese, Japanese and all other races')], t_rn)
   58|         nat, fp, al, unk = cz[sex]
   59|         out += rows(year, d, [(nat, sex, 'foreign_white_naturalized', 'White: Foreign-born, naturalized'),
   60|                               (fp, sex, 'foreign_white_first_papers', 'White: Foreign-born, first papers'),
   61|                               (al, sex, 'foreign_white_alien', 'White: Foreign-born, alien'),
   62|                               (unk, sex, 'foreign_white_unknown', 'White: Foreign-born, citizenship unknown')], t_cz)
   63|         assert_close(d[fb], d[[nat, fp, al, unk]].sum(axis=1), f'{year} {sex}: foreign-born total vs citizenship split')
   64|     return pd.DataFrame(out, columns=COLS)
   65| 
   66| 
   67| BUILDERS = {**build_population_republic.BUILDERS, **build_population_early.BUILDERS,
   68|             1920: year_1920_1930, 1930: year_1920_1930, **build_population_mid.BUILDERS}
   69| 
   70| 
   71| def check_1920(nh: pd.DataFrame):
   72|     j = hand_vs_nhgis(pd.read_csv(CACHE / 'population/adults_1920_by_state.csv'), nh).fillna(0)
   73|     bad = off_cells(j)
   74|     print(f'cells {len(j)}; total hand {j.hand.sum():,.0f} vs nhgis {j.nhgis.sum():,.0f}; '
   75|           f'cells off by >50 and >0.5%: {len(bad)}')
   76|     print_worst(bad)
   77| 
   78| 
   79| if __name__ == '__main__':
   80|     ap = argparse.ArgumentParser()
   81|     ap.add_argument('year', type=int)
   82|     ap.add_argument('--check', action='store_true')
   83|     a = ap.parse_args()
   84|     if a.year not in BUILDERS:
   85|         ap.error(f'no 21+ builder for {a.year}' + (' (1980 on: build_population_modern.py writes the 18+ tables)'
   86|                                                    if a.year >= 1980 else ''))
   87|     df = BUILDERS[a.year](a.year)
   88|     if a.check and a.year == 1920:
   89|         check_1920(df)
   90|     else:
   91|         out = CACHE / f'population/adults_{a.year}_by_state_nhgis.csv'
   92|         df.to_csv(out, index=False)
   93|         print(f'wrote {out.name}: {len(df)} rows, {df.state.nunique()} states, {df["count"].sum():,.0f} adults '
   94|               f'({df[df.sex == "F"]["count"].sum():,.0f} women)')
```

## `scripts/harness/build_population_early.py`

```python
    1| """NHGIS 1870-1910 -> population/adults_<year>_by_state_nhgis.csv (long format,
    2| the columns of adults_1920_by_state.csv). build_population.py writes the tables
    3| through BUILDERS:
    4| 
    5|     python3 scripts/harness/build_population.py 1880
    6|     python3 scripts/harness/build_population_early.py               # prints a summary per census
    7|     python3 scripts/harness/build_population_early.py --check-1910  # vs the hand-keyed 1910 table
    8| 
    9| What the censuses give (codebooks in the extract):
   10|   1870 sPHX NT45-48: men 21+ total, by nativity, by race (separate margins), male
   11|        citizens 21+. sRN NT4: race x nativity, no sex.
   12|   1880 sPHX NT1 race x nativity x sex; NT7 men 21+ native white / FB white / colored.
   13|   1890 cPHAM NT5/NT6/NT9 sex tables; NT14 men 21+ native white / FB white / colored.
   14|        (No citizenship table was requested for 1890.)
   15|   1900 cPHAM NT4/NT6/NT7/NT62 sex tables; NT9 men 21+; NT10 native men 21+ by race;
   16|        NT11 FB men 21+ (all races) by citizenship.
   17|   1910 cPHA NT8/NT10/NT11 sex & white nativity; NT12/NT13 men of voting age by
   18|        race/nativity; NT17 FB white men of voting age by citizenship.
   19| Women 21+ were not tabulated before 1920: every women's row is an [I] estimate.
   20| Territories whose name (minus " Territory") is in geo.STATE_NAME are kept and say so
   21| in `note`; Dakota/Indian/Alaska/Hawaii Territory and "Persons in the Military" drop.
   22| """
   23| import sys
   24| from functools import lru_cache
   25| 
   26| import pandas as pd
   27| 
   28| from nhgis_common import (CACHE, COLS, STATE_CODE, assert_close, hand_vs_nhgis, load, off_cells, print_worst,
   29|                                rows)
   30| 
   31| TAB = 'tabulated'
   32| GROUPS = ['native_white', 'native_white_native_parentage', 'native_white_foreign_or_mixed_parentage',
   33|           'foreign_white_naturalized', 'foreign_white_first_papers', 'foreign_white_alien', 'foreign_white_unknown',
   34|           'negro', 'other_races']
   35| CZ = ['foreign_white_naturalized', 'foreign_white_first_papers', 'foreign_white_alien', 'foreign_white_unknown']
   36| # Alaska and Hawaii (statehood 1959) are territories in every census here: drop them
   37| # even though geo.STATE_NAME lists them for the modern elections.
   38| NOT_YET = {'AK', 'HI'}
   39| 
   40| 
   41| def read(ds: str) -> pd.DataFrame:
   42|     """Like build_population.read, but keeps territories that later became a
   43|     STATE_NAME state (e.g. 'Arizona Territory' -> AZ) and records that they were."""
   44|     d = load(ds)
   45|     base = d.STATE.str.replace(r'\s+Territory$', '', regex=True).str.casefold()
   46|     keep = base.isin(STATE_CODE) & ~base.map(STATE_CODE).isin(NOT_YET)
   47|     d = d[keep].copy()
   48|     d['state'] = base[keep].map(STATE_CODE)
   49|     d['terr'] = d.STATE.str.endswith('Territory')
   50|     assert d.state.is_unique, f'{ds}: duplicate state codes'
   51|     return d.set_index('state')
   52| 
   53| 
   54| def emit(year, d, spec, table, note=TAB):
   55|     """rows(), with territories saying so in `note`."""
   56|     out = rows(year, d, spec, table, note)
   57|     for r in out:
   58|         if d.at[r['state'], 'terr']:
   59|             r['note'] = (r['note'] + '; ' if r['note'] else '') + f'territory in {year}, not yet a state'
   60|     return out
   61| 
   62| 
   63| # ---------------------------------------------------------------- 1870
   64| @lru_cache
   65| def _men_1870():
   66|     d, rn = read('ds19'), read('ds21')
   67|     # Independent checks: nativity and race margins both add to the total.
   68|     assert_close(d.AMS001 + d.AMS002, d.AMR001, '1870 NT46 vs NT45')
   69|     assert_close(d[['AMT001', 'AMT002', 'AMT003', 'AMT004']].sum(axis=1), d.AMR001, '1870 NT47 vs NT45')
   70|     # Race x nativity of men 21+: IPF of the total-population race x nativity cross
   71|     # (sRN NT4) to the men-21+ race and nativity margins [I].
   72|     races = [('W', 'AMT001', 'AN8001', 'AN8002'), ('C', 'AMT002', 'AN8003', 'AN8004'),
   73|              ('I', 'AMT004', 'AN8005', 'AN8006'), ('Z', 'AMT003', 'AN8007', 'AN8008')]
   74|     out = {}
   75|     for st in d.index:
   76|         seed = {r: [float(rn.at[st, n]) + 1e-6, float(rn.at[st, f]) + 1e-6] for r, _, n, f in races}
   77|         rm = {r: float(d.at[st, c]) for r, c, _, _ in races}
   78|         cm = [float(d.at[st, 'AMS001']), float(d.at[st, 'AMS002'])]
   79|         x = {r: v[:] for r, v in seed.items()}
   80|         for _ in range(200):
   81|             for r in x:
   82|                 s = sum(x[r])
   83|                 x[r] = [v * rm[r] / s for v in x[r]] if s else [0.0, 0.0]
   84|             for j in (0, 1):
   85|                 s = sum(x[r][j] for r in x)
   86|                 for r in x:
   87|                     x[r][j] = x[r][j] * cm[j] / s if s else 0.0
   88|         out[st] = x
   89|     m = pd.DataFrame({st: {'nw': x['W'][0], 'fw': x['W'][1], 'negro': sum(x['C']), 'other': sum(x['I']) + sum(x['Z']),
   90|                            'nb': float(d.at[st, 'AMS001']), 'cit': float(d.at[st, 'AMU001'])} for st, x in out.items()}).T
   91|     # Naturalized = male citizens 21+ - native-born men 21+, clipped to [0, FB white] [I].
   92|     m['nat_raw'] = m.cit - m.nb
   93|     m['nat'] = m.nat_raw.clip(lower=0).clip(upper=m.fw)
   94|     m['alien'] = m.fw - m.nat
   95|     m['terr'] = d.terr
   96|     return m
   97| 
   98| 
   99| def _split_1870():
  100|     m = _men_1870()
  101|     s = pd.DataFrame({'foreign_white_naturalized': m.nat / m.fw, 'foreign_white_alien': m.alien / m.fw,
  102|                       'foreign_white_first_papers': 0.0, 'foreign_white_unknown': 0.0}).fillna(0)
  103|     return s[CZ]
  104| 
  105| 
  106| def year_1870(year=1870):
  107|     m = _men_1870()
  108|     fm = _fm_1880()  # 1870 has no table by sex at all
  109|     out = []
  110|     lbl = {'nw': 'White: Native-born', 'negro': 'Colored: Native and foreign-born',
  111|            'other': 'Indian and Chinese: Native and foreign-born'}
  112|     grp = {'nw': 'native_white', 'negro': 'negro', 'other': 'other_races'}
  113|     ipf = '[I] men 21+ race x nativity: NT47 race and NT46 nativity margins raked (IPF) on the sRN NT4 total-population cross'
  114|     t = 'NHGIS 1870_sPHX NT45-NT47 (+1870_sRN NT4 seed)'
  115|     for k in ('nw', 'negro', 'other'):
  116|         out += emit(year, m, [(k, 'M', grp[k], lbl[k])], t, ipf)
  117|         w = m[[k, 'terr']].copy()
  118|         w[k] = m[k] * fm[grp[k]].reindex(m.index)
  119|         out += emit(year, w, [(k, 'F', grp[k], lbl[k])], t + '; 1880_sPHX NT1',
  120|                      '[I] women 21+ = men 21+ x the 1880 whole-population F/M ratio of the same state and group '
  121|                      '(1870 has no table by sex)')
  122|     tc = 'NHGIS 1870_sPHX NT46-NT48'
  123|     cz_note = ('[I] FB white men 21+ (IPF) split: naturalized = NT48 male citizens 21+ - NT46 native-born men 21+, '
  124|                'clipped to [0, FB white]; alien = the rest')
  125|     for sex in ('M', 'F'):
  126|         w = m[['nat', 'alien', 'terr']].copy()
  127|         n = cz_note
  128|         if sex == 'F':
  129|             fr = fm['foreign_white'].reindex(m.index)
  130|             w['nat'], w['alien'] = w.nat * fr, w.alien * fr
  131|             n = cz_note + '; women = men x 1880 FB white F/M, men\'s citizenship split (wife followed husband before 1922)'
  132|             tc2 = tc + '; 1880_sPHX NT1'
  133|         else:
  134|             tc2 = tc
  135|         out += emit(year, w, [('nat', sex, 'foreign_white_naturalized', 'White: Foreign-born, naturalized'),
  136|                                ('alien', sex, 'foreign_white_alien', 'White: Foreign-born, alien')], tc2, n)
  137|     return pd.DataFrame(out, columns=COLS)
  138| 
  139| 
  140| # ---------------------------------------------------------------- 1880
  141| A_CHINESE = 0.95  # [I] share of Chinese/Japanese males who were 21+ (an almost all-adult male labour migration)
  142| 
  143| 
  144| @lru_cache
  145| def _fm_1880():
  146|     d = read('ds25')
  147|     p = lambda cols: d[cols].sum(axis=1)  # noqa: E731
  148|     return pd.DataFrame({
  149|         'native_white': d.AR0002 / d.AR0001,
  150|         'foreign_white': d.AR0004 / d.AR0003,
  151|         'negro': p(['AR0006', 'AR0008']) / p(['AR0005', 'AR0007']),
  152|         'other_races': p(['AR0010', 'AR0012', 'AR0014', 'AR0016']) / p(['AR0009', 'AR0011', 'AR0013', 'AR0015']),
  153|     }).fillna(1.0)
  154| 
  155| 
  156| @lru_cache
  157| def _men_1880():
  158|     d = read('ds25')
  159|     neg = d.AR0005 + d.AR0007
  160|     chi = d.AR0009 + d.AR0011
  161|     ind = d.AR0013 + d.AR0015
  162|     # NT7 "Colored" men 21+ includes Chinese and Indians (CA: 66,809 colored men 21+
  163|     # vs 3,467 Negro males of all ages). Split it by males weighted by adult share:
  164|     # Negro and Indian at the national colored-men-21+/Negro-males ratio of states
  165|     # where they're >99% of colored males, Chinese/Japanese at A_CHINESE [I].
  166|     pure = (chi + ind) < 0.01 * (neg + chi + ind)
  167|     a_n = d.ASU003[pure].sum() / neg[pure].sum()
  168|     wn, wc, wi = neg * a_n, chi * A_CHINESE, ind * a_n
  169|     tot = (wn + wc + wi).replace(0, 1)
  170|     m = pd.DataFrame({'nw': d.ASU001.astype(float), 'fw': d.ASU002.astype(float),
  171|                       'negro': d.ASU003 * wn / tot, 'other': d.ASU003 * (wc + wi) / tot, 'terr': d.terr})
  172|     # Independent check: men 21+ can't exceed males of all ages in any group.
  173|     assert (m.nw <= d.AR0001).all() and (m.fw <= d.AR0003).all() and (d.ASU003 <= neg + chi + ind).all()
  174|     m.attrs['a_n'] = a_n
  175|     return m
  176| 
  177| 
  178| def _interp_split(year):
  179|     """Citizenship shares of FB white men 21+ for a census with none: linear in
  180|     time between the 1870 derivation and the 1900 tabulation (1890's citizenship
  181|     table wasn't in the extract), 1900 alone where the unit wasn't in 1870 [I]."""
  182|     s70, s00 = _split_1870(), _split_1900()
  183|     w = (year - 1870) / 30
  184|     s = s70.reindex(s00.index) * (1 - w) + s00 * w
  185|     return s.fillna(s00)
  186| 
  187| 
  188| def _fw_rows(year, fw_m, fw_f, split, terr, table, note_m, note_f):
  189|     out = []
  190|     lbl = {'foreign_white_naturalized': 'White: Foreign-born, naturalized',
  191|            'foreign_white_first_papers': 'White: Foreign-born, first papers',
  192|            'foreign_white_alien': 'White: Foreign-born, alien',
  193|            'foreign_white_unknown': 'White: Foreign-born, citizenship unknown'}
  194|     for sex, tot, note in (('M', fw_m, note_m), ('F', fw_f, note_f)):
  195|         w = pd.DataFrame({g: tot * split[g].reindex(tot.index) for g in CZ})
  196|         w['terr'] = terr
  197|         out += emit(year, w, [(g, sex, g, lbl[g]) for g in CZ], table, note)
  198|     return out
  199| 
  200| 
  201| def year_1880(year=1880):
  202|     m, fm = _men_1880(), _fm_1880()
  203|     t = 'NHGIS 1880_sPHX NT7'
  204|     tf = 'NHGIS 1880_sPHX NT7 x NT1'
  205|     fnote = '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT1)'
  206|     out = emit(year, m, [('nw', 'M', 'native_white', 'White: Native-born')], t)
  207|     split = (f'[I] NT7 colored men 21+ split Negro vs Chinese/Indian by NT1 males weighted by adult share '
  208|              f'(Negro & Indian {m.attrs["a_n"]:.3f}, Chinese/Japanese {A_CHINESE})')
  209|     out += emit(year, m, [('negro', 'M', 'negro', 'Colored: Negro'),
  210|                            ('other', 'M', 'other_races', 'Colored: Chinese, Japanese and Indian')], t + '; NT1', split)
  211|     w = pd.DataFrame({'nw': m.nw * fm.native_white, 'negro': m.negro * fm.negro, 'other': m.other * fm.other_races,
  212|                       'terr': m.terr})
  213|     out += emit(year, w, [('nw', 'F', 'native_white', 'White: Native-born')], tf, fnote)
  214|     out += emit(year, w, [('negro', 'F', 'negro', 'Colored: Negro'),
  215|                            ('other', 'F', 'other_races', 'Colored: Chinese, Japanese and Indian')], tf, fnote + '; ' + split)
  216|     cz = '[I] NT7 FB white men 21+ x citizenship shares interpolated 1870 (derived) -> 1900 (tabulated) at 1880'
  217|     out += _fw_rows(year, m.fw, m.fw * fm.foreign_white, _interp_split(year), m.terr, t + '; 1870_sPHX NT48; 1900_cPHAM NT11',
  218|                     cz, cz + '; women = men x NT1 FB white F/M, men\'s split (wife followed husband before 1922)')
  219|     return pd.DataFrame(out, columns=COLS)
  220| 
  221| 
  222| # ---------------------------------------------------------------- 1900
  223| @lru_cache
  224| def _men_1900():
  225|     d = read('ds31')
  226|     nat = d[[f'AYN00{i}' for i in range(1, 7)]].sum(axis=1)
  227|     fb = d[[f'AYO00{i}' for i in range(1, 9)]].sum(axis=1)
  228|     assert_close(nat + fb, d.AZ4001, '1900 NT10+NT11 vs NT9')
  229|     assert_close(d.AZF001 + d.AZF003, d.AZ0001, '1900 NT4 vs NT62')
  230|     # NT7's codebook says "Other Colored" for AZ3001/2, but the values are ALL colored
  231|     # (Negro + other): nationally 4.71M vs 4.39M Negro males, and FL 120,518 vs
  232|     # 120,199. Check: colored minus Negro must hold the native "Colored" men 21+ (NT10).
  233|     oth_m, oth_f = d.AZ3001 - d.AZ3003, d.AZ3002 - d.AZ3004
  234|     assert (oth_m >= 0).all() and (oth_m >= d.AYN005 + d.AYN006).all(), '1900 NT7 not colored-total'
  235|     assert (d.AZX001 <= d.AZF003).all()
  236|     fbnw_males = d.AZF003 - d.AZX001          # FB non-white males, all ages (NT4 - NT6)
  237|     fbnw_f = d.AZF004 - d.AZX002
  238|     fbnw = fbnw_males * fb / d.AZF003.replace(0, 1)   # [I] at the FB adult share
  239|     # FB "other" can't exceed other-colored males less native other men 21+; the rest is FB Negro [I].
  240|     fb_oth = pd.concat([fbnw, (oth_m - d.AYN005 - d.AYN006).clip(lower=0) * fb / d.AZF003.replace(0, 1)],
  241|                        axis=1).min(axis=1)
  242|     fb_neg = fbnw - fb_oth
  243|     cz = pd.DataFrame({'foreign_white_naturalized': d.AYO001 + d.AYO002, 'foreign_white_first_papers': d.AYO003 + d.AYO004,
  244|                        'foreign_white_alien': d.AYO005 + d.AYO006, 'foreign_white_unknown': d.AYO007 + d.AYO008}).astype(float)
  245|     # FB non-whites (mostly Chinese, barred from naturalizing) come out of alien, then unknown [I].
  246|     take = pd.concat([fbnw, cz.foreign_white_alien], axis=1).min(axis=1)
  247|     cz['foreign_white_alien'] -= take
  248|     cz['foreign_white_unknown'] -= (fbnw - take)
  249|     assert (cz.foreign_white_unknown > -1).all(), '1900: FB non-white exceeds alien + unknown'
  250|     m = pd.DataFrame({'nw': (d.AYN001 + d.AYN002).astype(float), 'negro_nb': (d.AYN003 + d.AYN004).astype(float),
  251|                       'other_nb': (d.AYN005 + d.AYN006).astype(float), 'fb_neg': fb_neg, 'fb_oth': fb_oth,
  252|                       'fw': cz.sum(axis=1), 'terr': d.terr})
  253|     m['negro'] = m.negro_nb + m.fb_neg
  254|     m['other'] = m.other_nb + m.fb_oth
  255|     nw_m = d.AZF001 - (d.AZ3001 - fbnw_males)
  256|     nw_f = d.AZF002 - (d.AZ3002 - fbnw_f)
  257|     fm = pd.DataFrame({'native_white': nw_f / nw_m, 'foreign_white': d.AZX002 / d.AZX001,
  258|                        'negro': d.AZ3004 / d.AZ3003, 'other_races': oth_f / oth_m.replace(0, 1),
  259|                        'white': (nw_f + d.AZX002) / (nw_m + d.AZX001)}).fillna(1.0)
  260|     return m, cz, fm
  261| 
  262| 
  263| def _split_1900():
  264|     _, cz, _ = _men_1900()
  265|     return cz.div(cz.sum(axis=1).replace(0, 1), axis=0)
  266| 
  267| 
  268| def year_1900(year=1900):
  269|     m, cz, fm = _men_1900()
  270|     t = 'NHGIS 1900_cPHAM NT10'
  271|     out = emit(year, m, [('nw', 'M', 'native_white', 'White: Native-born')], t)
  272|     fbn = ('[I] native-born (NT10, tabulated) + FB non-white men 21+ = (NT4 FB males - NT6 FB white males) x FB '
  273|            'adult share (NT11/NT4); FB "other" capped at NT7 other-colored males, the rest FB Negro')
  274|     out += emit(year, m, [('negro', 'M', 'negro', 'Negro'),
  275|                            ('other', 'M', 'other_races', 'Colored: Indian, Chinese, Japanese')], t + '; NT4; NT6; NT7; NT11', fbn)
  276|     fnote = '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT4/NT6/NT7)'
  277|     w = pd.DataFrame({'nw': m.nw * fm.native_white, 'negro': m.negro * fm.negro, 'other': m.other * fm.other_races,
  278|                       'terr': m.terr})
  279|     out += emit(year, w, [('nw', 'F', 'native_white', 'White: Native-born'), ('negro', 'F', 'negro', 'Negro'),
  280|                            ('other', 'F', 'other_races', 'Colored: Indian, Chinese, Japanese')],
  281|                  'NHGIS 1900_cPHAM NT10 x NT4/NT6/NT7', fnote)
  282|     czn = ('[I] NT11 FB men 21+ by citizenship (all races) less the FB non-white estimate, taken from alien '
  283|            'then unknown')
  284|     out += _fw_rows(year, m.fw, m.fw * fm.foreign_white, _split_1900(), m.terr, 'NHGIS 1900_cPHAM NT11; NT4; NT6', czn,
  285|                     czn + '; women = men x NT6 FB white F/M, men\'s split (wife followed husband before 1922)')
  286|     return pd.DataFrame(out, columns=COLS)
  287| 
  288| 
  289| # ---------------------------------------------------------------- 1890
  290| def year_1890(year=1890):
  291|     d = read('ds27')
  292|     assert_close(d.AVP001 + d.AVP003, d.AV3001, '1890 NT5 vs NT9 (male)')
  293|     assert_close(d[['AV0001', 'AV0003', 'AV0005', 'AV0007']].sum(axis=1), d.AV3001, '1890 NT6 vs NT9 (male)')
  294|     assert_close(d[['AV0002', 'AV0004', 'AV0006', 'AV0008']].sum(axis=1), d.AV3002, '1890 NT6 vs NT9 (female)')
  295|     assert (d.AUP001 <= d.AV0001 + d.AV0003).all() and (d.AUP002 <= d.AV0005).all() and (d.AUP003 <= d.AV0007).all()
  296|     m80, m00 = _men_1880(), _men_1900()[0]
  297|     fm80, fm00 = _fm_1880(), _men_1900()[2]
  298|     # NT14 "Colored" men 21+ (incl. Chinese/Indian, CA 72,061) split by the mean of the
  299|     # 1880 and 1900 Negro shares of colored men 21+ in the state [I].
  300|     sh = pd.concat([(m80.negro / (m80.negro + m80.other)), (m00.negro / (m00.negro + m00.other))], axis=1).mean(axis=1)
  301|     sh = sh.reindex(d.index).fillna(1.0)
  302|     m = pd.DataFrame({'nw': d.AUP001.astype(float), 'fw': d.AUP002.astype(float),
  303|                       'negro': d.AUP003 * sh, 'other': d.AUP003 * (1 - sh), 'terr': d.terr})
  304|     t = 'NHGIS 1890_cPHAM NT14'
  305|     out = emit(year, m, [('nw', 'M', 'native_white', 'White: Native-born')], t)
  306|     spl = '[I] NT14 colored men 21+ split Negro vs other by the mean of the state\'s 1880 and 1900 Negro shares'
  307|     out += emit(year, m, [('negro', 'M', 'negro', 'Colored: Negro'),
  308|                            ('other', 'M', 'other_races', 'Colored: Chinese, Japanese and Indian')], t, spl)
  309|     # Women: NT6 F/M for native white; Negro/other F/M = mean of 1880 and 1900, scaled so the
  310|     # implied colored F/M matches 1890's NT6 [I].
  311|     fm_nw = (d.AV0002 + d.AV0004) / (d.AV0001 + d.AV0003)
  312|     fm_fw = d.AV0006 / d.AV0005
  313|     fn = pd.concat([fm80.negro, fm00.negro], axis=1).mean(axis=1).reindex(d.index).fillna(d.AV0008 / d.AV0007)
  314|     fo = pd.concat([fm80.other_races, fm00.other_races], axis=1).mean(axis=1).reindex(d.index).fillna(1.0)
  315|     k = (d.AV0008 / d.AV0007) / ((fn * m.negro + fo * m.other) / d.AUP003.replace(0, 1)).replace(0, 1)
  316|     w = pd.DataFrame({'nw': m.nw * fm_nw, 'negro': m.negro * fn * k, 'other': m.other * fo * k, 'terr': m.terr})
  317|     out += emit(year, w, [('nw', 'F', 'native_white', 'White: Native-born')], t + ' x NT6',
  318|                  '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT6)')
  319|     out += emit(year, w, [('negro', 'F', 'negro', 'Colored: Negro'),
  320|                            ('other', 'F', 'other_races', 'Colored: Chinese, Japanese and Indian')], t + ' x NT6',
  321|                  '[I] women 21+ = men 21+ x mean 1880/1900 F/M of the group, scaled to NT6 colored F/M; ' + spl)
  322|     cz = ('[I] NT14 FB white men 21+ x citizenship shares interpolated 1870 (derived) -> 1900 (tabulated) at 1890 '
  323|           '(no 1890 citizenship table in the extract)')
  324|     out += _fw_rows(year, m.fw, m.fw * fm_fw, _interp_split(year), m.terr, t + '; 1870_sPHX NT48; 1900_cPHAM NT11', cz,
  325|                     cz + '; women = men x NT6 FB white F/M, men\'s split (wife followed husband before 1922)')
  326|     return pd.DataFrame(out, columns=COLS)
  327| 
  328| 
  329| # ---------------------------------------------------------------- 1910
  330| def year_1910(year=1910):
  331|     d = read('ds37')
  332|     assert_close(d[[f'A3200{i}' for i in range(1, 7)]].sum(axis=1), d.A31001, '1910 NT13 vs NT12')
  333|     assert_close(d[[f'A3300{i}' for i in range(1, 5)]].sum(axis=1), d.A32004, '1910 NT17 vs NT13 FB white')
  334|     assert_close(d[['A5B001', 'A5B002', 'A5B003', 'A5B004']].sum(axis=1), d.A30001 + d.A30002, '1910 NT8 vs NT11 white')
  335|     oth_m, oth_f = d.A3Z001 - d.A30001 - d.A30003, d.A3Z002 - d.A30002 - d.A30004
  336|     assert (oth_m > -1).all() and (oth_f > -1).all()
  337|     assert (d.A32005 <= d.A30003).all() and (d.A32001 + d.A32002 + d.A32003 + d.A32004 <= d.A30001).all()
  338|     t = 'NHGIS 1910_cPHA NT13'
  339|     m = d.copy()
  340|     m['nwf'] = (d.A32002 + d.A32003).astype(float)
  341|     out = []
  342|     out += emit(year, m, [('A32001', 'M', 'native_white_native_parentage', 'Native-Born White: Native parentage'),
  343|                            ('nwf', 'M', 'native_white_foreign_or_mixed_parentage', 'Native-Born White: Foreign or mixed parentage'),
  344|                            ('A32005', 'M', 'negro', 'Negro'),
  345|                            ('A32006', 'M', 'other_races', 'Indian, Chinese, Japanese and all other races')], t)
  346|     lbl = [('A33001', 'foreign_white_naturalized', 'Foreign-born white: Naturalized'),
  347|            ('A33002', 'foreign_white_first_papers', 'Foreign-born white: With first papers'),
  348|            ('A33003', 'foreign_white_alien', 'Foreign-born white: Alien'),
  349|            ('A33004', 'foreign_white_unknown', 'Foreign-born white: Unknown citizenship status')]
  350|     out += emit(year, m, [(c, 'M', g, lab) for c, g, lab in lbl], 'NHGIS 1910_cPHA NT17')
  351|     # Women: NT11 gives white/Negro by sex, other = NT10 - NT11. White nativity isn't by sex
  352|     # in 1910: native and FB white F/M = the state's 1900 ratios x (1910 white F/M / 1900 white F/M) [I].
  353|     fm00 = _men_1900()[2].reindex(d.index)
  354|     r_w = d.A30002 / d.A30001
  355|     k = r_w / fm00.white
  356|     r_nw = (fm00.native_white * k).fillna(r_w)
  357|     r_fw = (fm00.foreign_white * k).fillna(r_w)
  358|     w = pd.DataFrame({'np': d.A32001 * r_nw, 'nwf': m.nwf * r_nw, 'neg': d.A32005 * d.A30004 / d.A30003,
  359|                       'oth': d.A32006 * (oth_f / oth_m.replace(0, 1)), 'terr': d.terr})
  360|     for c in ('A33001', 'A33002', 'A33003', 'A33004'):
  361|         w[c] = d[c] * r_fw
  362|     fnote = '[I] women 21+ = men 21+ x the whole-population F/M ratio of the same state and group (NT10/NT11)'
  363|     wnote = ('[I] women 21+ = men 21+ x white F/M by nativity: the state\'s 1900 native/FB white F/M scaled by '
  364|              '1910/1900 white F/M (NT11; 1910 white nativity not by sex)')
  365|     out += emit(year, w, [('np', 'F', 'native_white_native_parentage', 'Native-Born White: Native parentage'),
  366|                            ('nwf', 'F', 'native_white_foreign_or_mixed_parentage', 'Native-Born White: Foreign or mixed parentage')],
  367|                  t + ' x NT11; 1900_cPHAM NT4/NT6/NT7', wnote)
  368|     out += emit(year, w, [('neg', 'F', 'negro', 'Negro'), ('oth', 'F', 'other_races', 'Indian, Chinese, Japanese and all other races')],
  369|                  t + ' x NT10/NT11', fnote)
  370|     out += emit(year, w, [(c, 'F', g, lab) for c, g, lab in lbl], 'NHGIS 1910_cPHA NT17 x NT11; 1900_cPHAM NT4/NT6/NT7',
  371|                  wnote + '; men\'s citizenship split (wife followed husband before 1922)')
  372|     return pd.DataFrame(out, columns=COLS)
  373| 
  374| 
  375| BUILDERS = {1870: year_1870, 1880: year_1880, 1890: year_1890, 1900: year_1900, 1910: year_1910}
  376| 
  377| 
  378| def check_1910(nh: pd.DataFrame):
  379|     hand = pd.read_csv(CACHE / 'population/adults_1910_by_state.csv')
  380|     for sex in ('M', 'F'):
  381|         j = hand_vs_nhgis(hand[hand.sex == sex], nh[nh.sex == sex])
  382|         miss = j[j.isna().any(axis=1)]
  383|         j = j.fillna(0)
  384|         bad = off_cells(j)
  385|         print(f'{sex}: cells {len(j)} ({len(miss)} on one side only); total hand {j.hand.sum():,.0f} vs nhgis '
  386|               f'{j.nhgis.sum():,.0f}; exact {(j["diff"].abs() < 0.5).sum()}; off by >50 and >0.5%: {len(bad)}')
  387|         if len(miss):
  388|             print('  one side only:', sorted(set(s for s, _, _ in miss.index)))
  389|         print_worst(bad)
  390| 
  391| 
  392| if __name__ == '__main__':
  393|     if '--check-1910' in sys.argv:
  394|         check_1910(year_1910())
  395|     else:
  396|         for y, f in BUILDERS.items():
  397|             df = f(y)
  398|             assert set(df.group) <= set(GROUPS), set(df.group) - set(GROUPS)
  399|             print(y, len(df), df.state.nunique(), f'{df["count"].sum():,.0f}',
  400|                   f'women {df[df.sex == "F"]["count"].sum() / df["count"].sum():.3f}')
```

## `scripts/harness/build_population_mid.py`

```python
    1| """NHGIS 1940–1970 → population tables (21+ and 18+), long format like
    2| adults_1920_by_state.csv. build_population.py uses BUILDERS (21+).
    3| 
    4|     python3 scripts/harness/build_population.py 1950           # 21+ only, via the shared entry point
    5|     python3 scripts/harness/build_population_mid.py            # 21+ and 18+ for 1940 1950 1960 1970
    6|     python3 scripts/harness/build_population_mid.py 1960 1970  # just those years
    7| 
    8| Writes CACHE/population/adults_<y>_by_state_nhgis.csv (21+) and
    9| adults18_<y>_by_state_nhgis.csv (18+; 1950 onward). Every value that is not a
   10| straight tabulation carries an [I] note saying how it was estimated.
   11| 
   12| What each census gives (state level, NHGIS extract 1):
   13|   1940  21+ by race × sex (cAge NT7); white 21+ by nativity × sex (cAge NT10);
   14|         FB white 21+ by sex × citizenship (cPHAE NT12). Complete.
   15|   1950  race (white / nonwhite) × sex × 5-yr age (cAge NT18); total 21+ (NT6, cPHA NT8);
   16|         21+ by nativity, FB 21+ by citizenship, both sexes and all races (cPHA NT9A/9B);
   17|         nonwhite 21+ by sex (cPHA NT48). Hawaii is blank in every 1950 table → omitted.
   18|   1960  white / nonwhite × sex × 5-yr age (cAge1 NT11); nonwhite 21+ by sex (cPop NT14).
   19|   1970  sex × single years to 21 (Cnt1 NT18); Negro / other × sex × 10-yr age (NT19).
   20| """
   21| import functools
   22| import sys
   23| 
   24| import numpy as np
   25| import pandas as pd
   26| 
   27| from nhgis_common import CACHE, STATE_CODE, assert_close, frame, load, row
   28| 
   29| TERR = {'alaska': 'AK', 'alaska territory': 'AK', 'hawaii': 'HI', 'hawaii territory': 'HI'}
   30| 
   31| 
   32| def read(ds: str, territories: bool) -> pd.DataFrame:
   33|     d = load(ds)
   34|     code = {k: v for k, v in STATE_CODE.items() if v not in ('AK', 'HI')}  # geo may or may not list them yet
   35|     if territories:
   36|         code.update(TERR)
   37|     d = d[d.STATE.str.casefold().isin(code)].copy()
   38|     d['state'] = d.STATE.str.casefold().map(code)
   39|     assert d.state.is_unique and len(d) == (len(set(code.values()))), (ds, len(d))
   40|     return d.set_index('state')
   41| 
   42| 
   43| def cols(prefix, a, b):
   44|     return [f'{prefix}{i:03d}' for i in range(a, b + 1)]
   45| 
   46| 
   47| def tab(label, table, note='tabulated'):
   48|     return {'label': label, 'table': table, 'note': note}
   49| 
   50| 
   51| def emit(year, cells):
   52|     """cells: {(sex, group): (Series by state, meta)} → long DataFrame."""
   53|     return frame([row(year, st, sex, group, m['label'].split(':')[0], m['label'], round(float(v), 1), m['note'], m['table'])
   54|                   for (sex, group), (s, m) in cells.items() for st, v in s.dropna().items()])
   55| 
   56| 
   57| # ---------------------------------------------------------------- 1940 (complete)
   58| @functools.lru_cache(None)
   59| def y1940():
   60|     a, b = read('ds77', False), read('ds78', False)
   61|     sx = {'M': 0, 'F': 1}
   62|     for s, i in sx.items():
   63|         wh, ng, ot = a[f'BV300{1+i}'], a[f'BV300{3+i}'], a[f'BV300{5+i}']
   64|         nw, fw = a[f'BVV00{1+i}'], a[f'BVV00{3+i}']
   65|         assert_close(nw + fw, wh, f'1940 {s} white nativity vs NT7 white')
   66|         assert_close(wh + ng + ot, b[f'BYU00{1+i}'], f'1940 {s} NT7 races vs cPHAE NT8 total')
   67|         fbw = b[cols('BWN', 1 + 4 * i, 4 + 4 * i)].sum(axis=1)
   68|         assert_close(fbw, fw, f'1940 {s} cPHAE NT12 citizenship vs cAge NT10 foreign-born white')
   69|         fb = b[cols('BV8', 1 + 3 * i, 3 + 3 * i)].sum(axis=1)
   70|         assert_close(b[f'BY500{1+i}'] + fb, b[f'BYU00{1+i}'], f'1940 {s} native + foreign vs total')
   71|     cells = {}
   72|     for s, i in sx.items():
   73|         t7, t10, t12 = 'NHGIS 1940_cAge NT7', 'NHGIS 1940_cAge NT10', 'NHGIS 1940_cPHAE NT12'
   74|         nat, fp, al, unk = cols('BWN', 1 + 4 * i, 4 + 4 * i)
   75|         cells[(s, 'native_white')] = (a[f'BVV00{1+i}'], tab('White: Native-born', t10))
   76|         cells[(s, 'foreign_white_naturalized')] = (b[nat], tab('White: Foreign-born, naturalized', t12))
   77|         cells[(s, 'foreign_white_first_papers')] = (b[fp], tab('White: Foreign-born, with first papers', t12))
   78|         cells[(s, 'foreign_white_alien')] = (b[al], tab('White: Foreign-born, with no papers', t12))
   79|         cells[(s, 'foreign_white_unknown')] = (b[unk], tab('White: Foreign-born, citizenship not reported', t12))
   80|         cells[(s, 'negro')] = (a[f'BV300{3+i}'], tab('Negro: Negro', t7))
   81|         cells[(s, 'other_races')] = (a[f'BV300{5+i}'], tab('Other: Other races', t7))
   82|     return emit(1940, cells)
   83| 
   84| 
   85| # ---------------------------------------------------------------- helpers 1950–1970
   86| def neg_share_1940():
   87|     """Negro share of nonwhite 21+, by state and sex (states only; territories blank by race)."""
   88|     a = read('ds77', False)
   89|     return {s: (a[f'BV300{3+i}'] / (a[f'BV300{3+i}'] + a[f'BV300{5+i}'])) for s, i in (('M', 0), ('F', 1))}
   90| 
   91| 
   92| @functools.lru_cache(None)
   93| def c1970():
   94|     """1970 counts by sex: total, negro, other at 21+ and 18–20. NT19's 15–24 band
   95|     is split by the total population's single-year shape within 15–24 [I]."""
   96|     c = read('ds94', True)
   97|     r = {}
   98|     for s, o in (('M', 0), ('F', 22)):
   99|         t = c[cols('CBT', 1 + o, 22 + o)].fillna(0).to_numpy()
  100|         tot15_24 = t[:, 6:14].sum(axis=1)
  101|         f21 = t[:, 12:14].sum(axis=1) / tot15_24  # 21, 22–24 of 15–24
  102|         f18 = t[:, 9:12].sum(axis=1) / tot15_24   # 18, 19, 20
  103|         r[(s, 'tot21')] = pd.Series(t[:, 12:].sum(axis=1), c.index)
  104|         r[(s, 'tot18_20')] = pd.Series(t[:, 9:12].sum(axis=1), c.index)
  105|         for g, base in (('negro', 1 if s == 'M' else 9), ('other_races', 17 if s == 'M' else 25)):
  106|             u = c[cols('CBU', base, base + 7)].fillna(0).to_numpy()
  107|             assert (u[:, 2] <= tot15_24 + 1).all()
  108|             r[(s, g + '21')] = pd.Series(u[:, 3:].sum(axis=1) + u[:, 2] * f21, c.index)
  109|             r[(s, g + '18_20')] = pd.Series(u[:, 2] * f18, c.index)
  110|     return r
  111| 
  112| 
  113| def neg_share(year):
  114|     """[I] Negro share of nonwhite 21+: linear in time between 1940 (NT7) and 1970 (NT19);
  115|     1970 alone where 1940 has no race split (AK, HI)."""
  116|     c = c1970()
  117|     s40 = neg_share_1940()
  118|     w = (year - 1940) / 30
  119|     out = {}
  120|     for s in ('M', 'F'):
  121|         s70 = c[(s, 'negro21')] / (c[(s, 'negro21')] + c[(s, 'other_races21')])
  122|         out[s] = ((1 - w) * s40[s].reindex(s70.index) + w * s70).fillna(s70).fillna(1.0)
  123|     return out
  124| 
  125| 
  126| def ipf(seed, rows, colm, n=50):
  127|     t = seed.astype(float) + 1e-9
  128|     for _ in range(n):
  129|         t *= (rows / t.sum(1))[:, None]
  130|         t *= colm / t.sum(0)
  131|     return t
  132| 
  133| 
  134| # ---------------------------------------------------------------- 1950
  135| @functools.lru_cache(None)
  136| def y1950():
  137|     a, b = read('ds83', True), read('ds84', True)
  138|     a, b = a.drop('HI'), b.drop('HI')  # Hawaii Territory is blank in every 1950 table of the extract
  139|     assert_close(a.B14001, b.B37001, '1950 NT6 vs cPHA NT8 21+')
  140|     assert_close(b[['B4J001', 'B4J002']].sum(axis=1), b.B37001, '1950 nativity vs total 21+')
  141|     assert_close(b[cols('B4K', 1, 3)].sum(axis=1), b.B4J002, '1950 citizenship vs foreign-born 21+')
  142|     band = {}
  143|     for (race, s), o in ((('W', 'M'), 0), (('W', 'F'), 17), (('N', 'M'), 34), (('N', 'F'), 51)):
  144|         x = a[cols('B1W', 1 + o, 17 + o)].fillna(0).to_numpy()
  145|         band[(race, s, 21)] = pd.Series(x[:, 5:].sum(axis=1) + 0.8 * x[:, 4], a.index)
  146|         band[(race, s, 18)] = pd.Series(0.4 * x[:, 3] + 0.2 * x[:, 4], a.index)
  147|     est21 = sum(band[(r, s, 21)] for r in 'WN' for s in 'MF')
  148|     rel = (est21 / a.B14001 - 1)
  149|     print(f'1950 band-split 21+ vs NT6: national {est21.sum():,.0f} vs {a.B14001.sum():,.0f}; '
  150|           f'state rel. error max {rel.abs().max():.4f} ({rel.abs().idxmax()})')
  151|     nwx = b[['B3C001', 'B3C002']].sum(axis=1)
  152|     nwe = band[('N', 'M', 21)] + band[('N', 'F', 21)]
  153|     print(f'1950 nonwhite 21+: NT48 {nwx.sum():,.0f} vs band-split {nwe.sum():,.0f}')
  154|     # Nonwhite 21+ by sex: NT48 where present, else band split. White total: NT6 − nonwhite; sex split by bands.
  155|     nw, nw_note = {}, {}
  156|     for s, col in (('M', 'B3C001'), ('F', 'B3C002')):
  157|         nw[s] = b[col].fillna(band[('N', s, 21)])
  158|         nw_note[s] = b[col].isna()
  159|     wt = a.B14001 - nw['M'] - nw['F']
  160|     wsh = band[('W', 'M', 21)] / (band[('W', 'M', 21)] + band[('W', 'F', 21)])
  161|     wh = {'M': wt * wsh, 'F': wt * (1 - wsh)}
  162|     # Foreign-born white 21+ by sex: 1950 foreign-born 21+ (all races) × 1940's FB-white-by-sex / FB-total ratio.
  163|     e = read('ds78', True)
  164|     fb40 = e[cols('BV8', 1, 6)].sum(axis=1)
  165|     fbw40 = {'M': e[cols('BWN', 1, 4)].sum(axis=1), 'F': e[cols('BWN', 5, 8)].sum(axis=1)}
  166|     fbw = {s: b.B4J002 * (fbw40[s] / fb40).reindex(b.index) for s in 'MF'}
  167|     # Citizenship: rake 1940's FB-white sex × (naturalized, alien incl. first papers, not reported)
  168|     # to the 1950 sex totals above and 1950's citizenship split of all FB 21+.
  169|     cz = {(s, k): pd.Series(np.nan, b.index) for s in 'MF' for k in range(3)}
  170|     for st in b.index:
  171|         seed = np.array([[e.at[st, 'BWN001'], e.at[st, 'BWN002'] + e.at[st, 'BWN003'], e.at[st, 'BWN004']],
  172|                          [e.at[st, 'BWN005'], e.at[st, 'BWN006'] + e.at[st, 'BWN007'], e.at[st, 'BWN008']]])
  173|         r = np.array([fbw['M'][st], fbw['F'][st]])
  174|         if np.isnan(seed).any() or np.isnan(r).any():
  175|             continue
  176|         k = b.loc[st, cols('B4K', 1, 3)].to_numpy(float)
  177|         t = ipf(seed, r, k / k.sum() * r.sum())
  178|         for i, s in enumerate('MF'):
  179|             for j in range(3):
  180|                 cz[(s, j)][st] = t[i, j]
  181|     ns = neg_share(1950)
  182|     T6, T18, T48, T9 = 'NHGIS 1950_cAge NT6', 'NHGIS 1950_cAge NT18', 'NHGIS 1950_cPHA NT48', 'NHGIS 1950_cPHA NT9A/NT9B'
  183|     fbnote = ('[I] 1950 foreign-born 21+ (NT9A, all races, both sexes) × 1940 state ratio of FB white by sex to all FB '
  184|               '(1940_cPHAE NT12/NT10); citizenship raked (IPF) from 1940 FB-white sex × citizenship to 1950 NT9B '
  185|               'all-FB citizenship split; 1950 "alien" includes first papers')
  186|     c21, c18 = {}, {}
  187|     for s in 'MF':
  188|         nb = wh[s] - fbw[s]
  189|         assert (nb.dropna() > 0).all(), '1950 native white < 0'
  190|         wnote = ('[I] white 21+ = NT6 total 21+ − nonwhite 21+ (NT48); sex split by NT18 bands with 20–24 split '
  191|                  'evenly by single year; minus estimated foreign-born white')
  192|         c21[(s, 'native_white')] = (nb, tab('White: Native-born', f'{T6}; {T48}; {T18}; {T9}', wnote))
  193|         for j, (g, lab) in enumerate((('foreign_white_naturalized', 'naturalized'), ('foreign_white_alien', 'alien'),
  194|                                       ('foreign_white_unknown', 'citizenship not reported'))):
  195|             c21[(s, g)] = (cz[(s, j)], tab(f'White: Foreign-born, {lab}', f'{T9}; NHGIS 1940_cPHAE NT10/NT12', fbnote))
  196|         nnote = ('[I] nonwhite 21+ by sex from NT48 (Alaska: NT18 bands, 20–24 split evenly); Negro share of nonwhite '
  197|                  'interpolated linearly 1940 (cAge NT7) → 1970 (Cnt1 NT19); Alaska 1970 share')
  198|         c21[(s, 'negro')] = (nw[s] * ns[s].reindex(nw[s].index), tab('Negro: Negro (est. from nonwhite)', f'{T48}; {T18}', nnote))
  199|         c21[(s, 'other_races')] = (nw[s] * (1 - ns[s].reindex(nw[s].index)),
  200|                                    tab('Other: Other races (est. from nonwhite)', f'{T48}; {T18}', nnote))
  201|         # 18–20 add-on
  202|         w18, n18 = band[('W', s, 18)], band[('N', s, 18)]
  203|         fsh = (fbw[s] / wh[s])
  204|         c18[(s, 'native_white')] = w18 * (1 - fsh)
  205|         for j, g in enumerate(('foreign_white_naturalized', 'foreign_white_alien', 'foreign_white_unknown')):
  206|             c18[(s, g)] = w18 * fsh * (cz[(s, j)] / fbw[s])
  207|         c18[(s, 'negro')] = n18 * ns[s].reindex(n18.index)
  208|         c18[(s, 'other_races')] = n18 * (1 - ns[s].reindex(n18.index))
  209|     note18 = ('; 18–20 [I]: NT18 bands, 2/5 of 15–19 + 1/5 of 20–24 (even single-year split), '
  210|               'nativity/citizenship/Negro shares as 21+')
  211|     return emit(1950, c21), add18(1950, c21, c18, note18)
  212| 
  213| 
  214| def add18(year, c21, c18, note18):
  215|     cells = {}
  216|     for k, (s, m) in c21.items():
  217|         n = m['note'] + note18 if m['note'].startswith('[I]') else '[I] 21+ ' + m['note'] + note18
  218|         cells[k] = (s + c18[k].reindex(s.index), dict(m, note=n))
  219|     return emit(year, cells)
  220| 
  221| 
  222| # ---------------------------------------------------------------- 1950 shares carried to 1960, 1970
  223| def fb_shares_1950():
  224|     """FB white share of white 21+, and citizenship split of FB white, by state × sex from the 1950 build.
  225|     Hawaii (no 1950 data): national 1950 shares."""
  226|     d = y1950()[0]
  227|     p = d.pivot_table(index=['state', 'sex'], columns='group', values='count', aggfunc='sum')
  228|     fbg = ['foreign_white_naturalized', 'foreign_white_alien', 'foreign_white_unknown']
  229|     p.loc[('HI', 'M'), :] = p.xs('M', level='sex').sum()
  230|     p.loc[('HI', 'F'), :] = p.xs('F', level='sex').sum()
  231|     fb = p[fbg].sum(axis=1)
  232|     share = fb / (fb + p['native_white'])
  233|     split = p[fbg].div(fb, axis=0)
  234|     return share, split
  235| 
  236| 
  237| def white_split(year, wh, w18, src, wnote, has18=True):
  238|     share, split = fb_shares_1950()
  239|     fbnote = (f'[I] white 21+ ({wnote}) × 1950 FB-white share of white 21+ and 1950 citizenship split, carried '
  240|               f'forward by state × sex (Hawaii: national 1950 shares); 1950 "alien" includes first papers')
  241|     c21, c18 = {}, {}
  242|     for s in 'MF':
  243|         sh = share.xs(s, level='sex').reindex(wh[s].index)
  244|         sp = split.xs(s, level='sex').reindex(wh[s].index)
  245|         c21[(s, 'native_white')] = (wh[s] * (1 - sh), tab('White: Native-born (est.)', src, fbnote))
  246|         c18[(s, 'native_white')] = w18[s] * (1 - sh)
  247|         for g, lab in (('foreign_white_naturalized', 'naturalized'), ('foreign_white_alien', 'alien'),
  248|                        ('foreign_white_unknown', 'citizenship not reported')):
  249|             c21[(s, g)] = (wh[s] * sh * sp[g], tab(f'White: Foreign-born, {lab} (est.)', src, fbnote))
  250|             c18[(s, g)] = w18[s] * sh * sp[g]
  251|     return c21, c18
  252| 
  253| 
  254| # ---------------------------------------------------------------- 1960
  255| @functools.lru_cache(None)
  256| def y1960():
  257|     a, b = read('ds89', True), read('ds91', True)
  258|     band = {}
  259|     for (race, s), o in ((('W', 'M'), 0), (('W', 'F'), 18), (('N', 'M'), 36), (('N', 'F'), 54)):
  260|         x = a[cols('B49', 1 + o, 18 + o)].fillna(0).to_numpy()
  261|         band[(race, s)] = x
  262|     for s, o in (('M', 0), ('F', 18)):
  263|         t = a[cols('B5F', 1 + o, 18 + o)].fillna(0).to_numpy()
  264|         gap = np.abs(band[('W', s)] + band[('N', s)] - t).max()
  265|         assert gap < 1, f'1960 {s}: NT11 white+nonwhite vs NT5 sex×age differ by {gap}'
  266|     est = {k: pd.Series(x[:, 5:].sum(axis=1) + 0.8 * x[:, 4], a.index) for k, x in band.items()}
  267|     e18 = {k: pd.Series(0.4 * x[:, 3] + 0.2 * x[:, 4], a.index) for k, x in band.items()}
  268|     for s, col in (('M', 'B5T001'), ('F', 'B5T002')):
  269|         r = est[('N', s)] / b[col] - 1
  270|         print(f'1960 nonwhite 21+ {s}: NT14 {b[col].sum():,.0f} vs band-split {est[("N", s)].sum():,.0f} '
  271|               f'(state rel. max {r.abs().max():.4f} {r.abs().idxmax()})')
  272|     T11, T14 = 'NHGIS 1960_cAge1 NT11', 'NHGIS 1960_cPop NT14'
  273|     wh = {s: est[('W', s)] for s in 'MF'}
  274|     w18 = {s: e18[('W', s)] for s in 'MF'}
  275|     c21, c18 = white_split(1960, wh, w18, f'{T11}; NHGIS 1950_cPHA NT9A/NT9B',
  276|                            'NT11 bands, 25+ plus 4/5 of 20–24, even single-year split')
  277|     ns = neg_share(1960)
  278|     nnote = '[I] nonwhite 21+ by sex tabulated (NT14); Negro share interpolated linearly 1940 (cAge NT7) → 1970 (Cnt1 NT19); AK, HI 1970 share'
  279|     for s, col in (('M', 'B5T001'), ('F', 'B5T002')):
  280|         c21[(s, 'negro')] = (b[col] * ns[s], tab('Negro: Negro (est. from nonwhite)', T14, nnote))
  281|         c21[(s, 'other_races')] = (b[col] * (1 - ns[s]), tab('Other: Other races (est. from nonwhite)', T14, nnote))
  282|         c18[(s, 'negro')] = e18[('N', s)] * ns[s]
  283|         c18[(s, 'other_races')] = e18[('N', s)] * (1 - ns[s])
  284|     note18 = ('; 18–20 [I]: NT11 bands, 2/5 of 15–19 + 1/5 of 20–24 (even single-year split), '
  285|               'nativity/citizenship/Negro shares as 21+')
  286|     return emit(1960, c21), add18(1960, c21, c18, note18)
  287| 
  288| 
  289| # ---------------------------------------------------------------- 1970
  290| @functools.lru_cache(None)
  291| def y1970():
  292|     c = c1970()
  293|     T18, T19 = 'NHGIS 1970_Cnt1 NT18', 'NHGIS 1970_Cnt1 NT19'
  294|     wh = {s: c[(s, 'tot21')] - c[(s, 'negro21')] - c[(s, 'other_races21')] for s in 'MF'}
  295|     w18 = {s: c[(s, 'tot18_20')] - c[(s, 'negro18_20')] - c[(s, 'other_races18_20')] for s in 'MF'}
  296|     for s in 'MF':
  297|         assert (wh[s] > 0).all() and (w18[s] > 0).all()
  298|     c21, c18 = white_split(1970, wh, w18, f'{T18}; {T19}; NHGIS 1950_cPHA NT9A/NT9B',
  299|                            'NT18 total 21+ minus NT19 Negro and other')
  300|     rnote = ('[I] NT19 25+ tabulated; 21–24 = NT19 15–24 band × (NT18 total 21–24 / total 15–24), '
  301|              'i.e. the band split by the total population\'s single-year shape')
  302|     for s in 'MF':
  303|         c21[(s, 'negro')] = (c[(s, 'negro21')], tab('Negro: Negro', T19 + '; ' + T18, rnote))
  304|         c21[(s, 'other_races')] = (c[(s, 'other_races21')], tab('Other: Other races', T19 + '; ' + T18, rnote))
  305|         c18[(s, 'negro')] = c[(s, 'negro18_20')]
  306|         c18[(s, 'other_races')] = c[(s, 'other_races18_20')]
  307|     note18 = ('; 18–20 [I]: total tabulated (NT18 single years), Negro/other = NT19 15–24 band × total 18–20 / 15–24, '
  308|               'white nativity/citizenship shares as 21+')
  309|     return emit(1970, c21), add18(1970, c21, c18, note18)
  310| 
  311| 
  312| BUILDERS = {1940: lambda y: y1940(), 1950: lambda y: y1950()[0], 1960: lambda y: y1960()[0], 1970: lambda y: y1970()[0]}
  313| BUILDERS18 = {1950: lambda y: y1950()[1], 1960: lambda y: y1960()[1], 1970: lambda y: y1970()[1]}
  314| 
  315| 
  316| if __name__ == '__main__':
  317|     years = [int(y) for y in sys.argv[1:]] or [1940, 1950, 1960, 1970]
  318|     for y in years:
  319|         for name, B in ((f'adults_{y}_by_state_nhgis.csv', BUILDERS), (f'adults18_{y}_by_state_nhgis.csv', BUILDERS18)):
  320|             if y not in B:
  321|                 continue
  322|             df = B[y](y)
  323|             assert (df['count'] >= 0).all(), f'{name}: negative counts'
  324|             df.to_csv(CACHE / 'population' / name, index=False)
  325|             est = df[df.note.str.startswith('[I]')]['count'].sum()
  326|             print(f'wrote {name}: {len(df)} rows, {df.state.nunique()} states, {df["count"].sum():,.0f} '
  327|                   f'({df[df.sex == "F"]["count"].sum():,.0f} women; {est / df["count"].sum():.0%} of count in [I] rows)')
```

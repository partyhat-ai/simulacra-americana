# simulacra-americana: source and docs, part 8 of 17

Generated from commit `caf86112f396` (2026-11-20) of github.com/partyhat-ai/simulacra-americana by `scripts/llms_digest.py`, which `.github/workflows/llms-digest.yml` reruns on every push to `main`, so this text matches the code at that commit.
Files `simharness/backbone.py` to `simharness/evaluate.py`. Lines are numbered as in the repository.

## `simharness/backbone.py`

```python
    1| """The statistical backbone: turnout and choice by cell, calibrated exactly.
    2| 
    3| 1920 has no survey, so the backbone is hierarchical ecological inference on
    4| state returns against census makeup, identified by the 1916 → 1920 suffrage
    5| natural experiment. Every step has a posterior draw; every draw is calibrated
    6| so that the unchanged world reproduces each state's certified R, D and other
    7| votes exactly (product promise 1).
    8| 
    9| Turnout, per draw d:
   10|   T1  κ: the change in logit turnout per eligible adult from 1916 to 1920 in
   11|       the "old" states, where women could already vote for president in 1916
   12|       and the legal electorate's makeup didn't change. Drawn from the
   13|       predictive distribution across those states (mean and between-state
   14|       spread).
   15|   T2  In the "new" states, men's 1920 turnout = expit(logit(1916 turnout) + κ);
   16|       women's votes are the residual, W = T20 − m20·M20, and women's turnout
   17|       w = W / F20. Georgia and Mississippi, where women couldn't register in
   18|       time, are a placebo: W there should be about 0.
   19|   T3  In the old states, men and women are split with the ratio w/m drawn
   20|       from the new states outside the South (no within-state evidence).
   21|   T4  Within a state and sex, groups differ by a logit offset. Black
   22|       Southerners' turnout comes from a Goodman regression of 1916 men's
   23|       turnout on the Black share of eligible men across the eleven Southern
   24|       states; elsewhere groups share the state-sex rate (an assumption, named).
   25|       Black Southerners' shortfall against white turnout in their own state and
   26|       sex is counted as exclusion (reason: extralegal_exclusion), not choice.
   27|   T5  Calibration: a logit shift per state and sex so the state's total votes
   28|       match exactly.
   29| 
   30| Choice, per draw d:
   31|   C1  δ, women's logit tilt toward R: regression across states of the 1916 →
   32|       1920 change in logit two-party R share on f, the share of 1920 votes cast
   33|       by newly enfranchised women (0 in old states), with South/non-South
   34|       intercepts. Re-fitted per draw because f depends on the turnout draw.
   35|   C2  β_B, Black voters' logit shift toward R relative to white voters of the
   36|       same state: prior N(1.5, 1.0) [I], updated by a Goodman regression across
   37|       non-Southern states. The prior encodes the documented loyalty of Black
   38|       voters to the Republican party before 1932; its size is an assumption.
   39|   C3  Calibration: per state, intercepts for R and for other are solved by
   40|       iterative scaling so R, D and other match the certified votes exactly.
   41| """
   42| from __future__ import annotations
   43| 
   44| from dataclasses import dataclass, field
   45| 
   46| import numpy as np
   47| import pandas as pd
   48| 
   49| from .aggregate import World
   50| from .geo import REGION_OF, SOUTH
   51| from .stats import bayes_ols, expit, logit
   52| 
   53| GROUPS = ['native_white', 'foreign_white_naturalized', 'foreign_white_alien', 'black', 'other']
   54| 
   55| 
   56| @dataclass
   57| class Inputs:
   58|     cells: pd.DataFrame      # state, sex, group, adults20, adults16
   59|     returns: pd.DataFrame    # index state; R16 D16 O16 T16 R20 D20 O20 T20
   60|     women16: set             # states where women could vote for president in Nov 1916
   61|     women_pre19: set         # states where women could vote for president in Nov 1920 without the 19th
   62|     closed_1920: set         # states where women couldn't register in time for Nov 1920
   63|     alien_voting: set        # states where declarant aliens could vote in 1920
   64|     ev: pd.Series            # 1920 electoral votes by state
   65|     other_citizen: dict = field(default_factory=dict)  # state → citizen share of 'other' adults
   66|     # General years (general_fit): the election year, the states where women could
   67|     # vote for president at that election, and the voting age (21; 18 from 1972).
   68|     year: int = 1920
   69|     women_vote: set = field(default_factory=set)
   70|     voting_age: int = 21
   71|     # state → fraction of that state's Black / white adults legally able to vote
   72|     # (slavery, free-Black exclusion, property and taxpaying tests; empty = 1).
   73|     black_can: dict = field(default_factory=dict)
   74|     white_can: dict = field(default_factory=dict)
   75|     # States whose electors the legislature chose (no popular vote that year).
   76|     no_popular: set = field(default_factory=set)
   77| 
   78| 
   79| @dataclass
   80| class Fit:
   81|     world: World             # the calibrated unchanged world, all draws
   82|     cells: pd.DataFrame
   83|     params: dict             # per-draw parameter arrays
   84|     diagnostics: dict
   85| 
   86| 
   87| def _solve(v, shift, tR, tO, iters=300):
   88|     """Intercepts for R and other so a group of cells casts exactly tR and tO
   89|     of its votes v (iterative scaling on a multinomial logit, D as base)."""
   90|     aR, aO = 0.0, 0.0
   91|     total = v.sum()
   92|     for _ in range(iters):
   93|         eR = np.exp(aR + shift)
   94|         eO = np.exp(aO) * np.ones_like(eR)
   95|         den = 1 + eR + eO
   96|         pR, pO = eR / den, eO / den
   97|         curR, curO = (v * pR).sum(), (v * pO).sum()
   98|         if abs(curR - tR) < 1e-7 * total and abs(curO - tO) < 1e-7 * total + 1e-9:
   99|             break
  100|         aR += np.log(max(tR, 1e-12) / max(curR, 1e-12))
  101|         aO += np.log(max(tO, 1e-12) / max(curO, 1e-12)) if tO > 0 else -50
  102|     return pR, pO
  103| 
  104| 
  105| def _black_south_bound(D, S, sidx, south_state, black, south_cell, female, votes_cell, share, can_eff, t, R, Dm, O, T, shift_R,
  106|                        solver=None):
  107|     """C3b (in place): Black Southern voters split like Black voters outside the
  108|     South, bounded by the state's certified ledger; the rest of the state is
  109|     re-calibrated. Returns how many draws hit the bound, per state.
  110|     solver: (v, shift, tR, tO) → (pR, pO); _solve by default (fit, carry_forward)."""
  111|     solver = solver or _solve
  112|     nsb, bsc = black & ~south_cell, black & south_cell
  113|     bound_hits = np.zeros(S)
  114|     for d in range(D):
  115|         vn = votes_cell[d, nsb]
  116|         nb_nat = (vn[:, None] * share[d, nsb, :]).sum(axis=0) / max(vn.sum(), 1e-9)
  117|         for s in np.where(south_state)[0]:
  118|             nb = nb_nat
  119|             idx = np.where(sidx == s)[0]
  120|             b_idx, o_idx = idx[bsc[idx]], idx[~bsc[idx]]
  121|             vb = votes_cell[d, b_idx]
  122|             if vb.sum() <= 0:
  123|                 continue
  124|             # Only parties on the state's certified ledger; minor-party share
  125|             # capped at 80% of the state's minor-party vote.
  126|             nb_s = nb.copy()
  127|             if R[s] <= 0 or Dm[s] <= 0:
  128|                 # A major party off the state's ballot (general years only).
  129|                 nb_s[0] *= R[s] > 0
  130|                 nb_s[1] *= Dm[s] > 0
  131|                 nb_s = nb_s / nb_s.sum() if nb_s.sum() > 0 else np.array([0.0, 0.0, 1.0])
  132|             o_cap = 0.8 * O[s] / max(vb.sum(), 1e-9)
  133|             if nb_s[2] > o_cap:
  134|                 nb_s[:2] *= (1 - o_cap) / max(nb_s[0] + nb_s[1], 1e-9)
  135|                 nb_s[2] = o_cap
  136|             nb = nb_s
  137|             scale = min(1.0, 0.8 * R[s] / max(vb.sum() * nb[0], 1e-9), 0.8 * Dm[s] / max(vb.sum() * nb[1], 1e-9))
  138|             if scale < 1.0:
  139|                 bound_hits[s] += 1
  140|                 for sex_m in (female, ~female):
  141|                     bi = b_idx[sex_m[b_idx]]
  142|                     oi = o_idx[sex_m[o_idx]]
  143|                     lost = votes_cell[d, bi].sum() * (1 - scale)
  144|                     can_eff[d, bi] *= scale
  145|                     votes_cell[d, bi] *= scale
  146|                     vo = votes_cell[d, oi].sum()
  147|                     if vo > 0:
  148|                         t[d, oi] *= 1 + lost / vo
  149|                         votes_cell[d, oi] *= 1 + lost / vo
  150|                 vb = votes_cell[d, b_idx]
  151|             share[d, b_idx, :] = nb
  152|             v = votes_cell[d, o_idx]
  153|             tR = R[s] / T[s] * votes_cell[d, idx].sum() - vb.sum() * nb[0]
  154|             tO = O[s] / T[s] * votes_cell[d, idx].sum() - vb.sum() * nb[2]
  155|             pR, pO = solver(v, shift_R[d, o_idx], tR, max(tO, 0.0))
  156|             share[d, o_idx, 0], share[d, o_idx, 2], share[d, o_idx, 1] = pR, pO, 1 - pR - pO
  157|     return bound_hits
  158| 
  159| 
  160| WHITE_GROUPS = ('native_white', 'foreign_white_naturalized', 'foreign_white_alien')
  161| 
  162| 
  163| def legal_can(inp: Inputs, year: int) -> tuple[np.ndarray, list]:
  164|     """Fraction of each cell legally able to vote, and the reason for the rest.
  165| 
  166|     Any year: aliens only where inp.alien_voting; 'other' × inp.other_citizen;
  167|     Black adults × inp.black_can[state] (slavery, free-Black exclusion); white
  168|     adults × inp.white_can[state] (property and taxpaying tests). Women: 1916
  169|     by women16, 1920 barred only where registration closed (closed_1920);
  170|     any other year only in inp.women_vote — except that after 1920 an empty
  171|     women_vote means the 19th Amendment everywhere (so 1916/1920/1924 calls
  172|     return exactly what they did before general years existed)."""
  173|     c = inp.cells
  174|     can = np.ones(len(c))
  175|     reason = [''] * len(c)
  176|     women_rule = year not in (1916, 1920) and (year < 1920 or bool(inp.women_vote))
  177|     for i, r in enumerate(c.itertuples()):
  178|         if r.group == 'foreign_white_alien' and r.state not in inp.alien_voting:
  179|             can[i], reason[i] = 0.0, 'noncitizen'
  180|         elif r.group == 'other':
  181|             can[i] = inp.other_citizen.get(r.state, 1.0)
  182|             reason[i] = 'native_status' if can[i] < 1 else ''
  183|         f = inp.black_can.get(r.state, 1.0) if r.group == 'black' else (
  184|             inp.white_can.get(r.state, 1.0) if r.group in WHITE_GROUPS else 1.0)
  185|         if f != 1.0:
  186|             can[i] *= f
  187|             reason[i] = reason[i] or ('race_law' if r.group == 'black' else 'property_tax')
  188|         if r.sex == 'F':
  189|             if year == 1916 and r.state not in inp.women16:
  190|                 can[i], reason[i] = 0.0, 'sex'
  191|             if year == 1920 and r.state in inp.closed_1920:
  192|                 can[i], reason[i] = 0.0, 'registration_closed'
  193|             if women_rule and r.state not in inp.women_vote:
  194|                 can[i], reason[i] = 0.0, 'sex'
  195|     return can, reason
  196| 
  197| 
  198| def fit(inp: Inputs, draws: int, seed: int, pop_cv: dict | None = None, beta_b_prior_only: bool = False) -> Fit:
  199|     rng = np.random.default_rng(seed)
  200|     c = inp.cells.reset_index(drop=True)
  201|     states = sorted(inp.returns.index)
  202|     S, C, D = len(states), len(c), draws
  203|     sidx = np.array([states.index(s) for s in c.state])
  204|     female = (c.sex == 'F').to_numpy()
  205|     south_state = np.array([s in SOUTH for s in states])
  206|     south_cell = south_state[sidx]
  207|     black = (c.group == 'black').to_numpy()
  208|     ret = inp.returns.loc[states]
  209| 
  210|     # ── Population draws: census undercount and interpolation error [I] ──
  211|     cv = pop_cv or {'native_white': 0.02, 'foreign_white_naturalized': 0.04, 'foreign_white_alien': 0.05,
  212|                     'black': 0.05, 'other': 0.08}
  213|     cv_c = c.group.map(cv).to_numpy()
  214|     noise = np.exp(rng.normal(0, 1, (D, C)) * cv_c - cv_c ** 2 / 2)
  215|     a20 = c.adults20.to_numpy()[None, :] * noise
  216|     a16 = c.adults16.to_numpy()[None, :] * noise * np.exp(rng.normal(0, 0.02, (D, C)))
  217| 
  218|     can16, _ = legal_can(inp, 1916)
  219|     can20, reason20 = legal_can(inp, 1920)
  220| 
  221|     def per_state(x, mask=None):
  222|         """Sum [D, C] over cells into [D, S]."""
  223|         m = np.ones(C, bool) if mask is None else mask
  224|         out = np.zeros((x.shape[0], S))
  225|         np.add.at(out, (slice(None), sidx[m]), x[:, m])
  226|         return out
  227| 
  228|     E16 = per_state(a16 * can16)
  229|     E20 = per_state(a20 * can20)
  230|     M16 = per_state(a16 * can16, ~female)
  231|     M20 = per_state(a20 * can20, ~female)
  232|     F20 = per_state(a20 * can20, female)
  233|     T16 = ret.T16.to_numpy()[None, :]
  234|     T20 = ret.T20.to_numpy()[None, :]
  235| 
  236|     old = np.array([s in inp.women16 for s in states])
  237|     new = ~old
  238|     closed = np.array([s in inp.closed_1920 for s in states])
  239| 
  240|     # T1: κ from the old states, predictive draw per state
  241|     k_old = logit(T20 / E20)[:, old] - logit(T16 / E16)[:, old]           # [D, n_old]
  242|     k_mean = k_old.mean(axis=1)
  243|     k_sd = k_old.std(axis=1, ddof=1)
  244|     n_old = old.sum()
  245|     kappa_mean = k_mean + rng.standard_t(max(n_old - 1, 1), D) * k_sd / np.sqrt(n_old)
  246|     kappa = kappa_mean[:, None] + rng.normal(0, 1, (D, S)) * k_sd[:, None]   # state-level predictive
  247| 
  248|     # T2: men's and women's turnout in new states
  249|     m16 = T16 / np.maximum(M16, 1)
  250|     m20_pred = expit(logit(m16) + kappa)
  251|     W = T20 - m20_pred * M20
  252|     w_raw = W / np.maximum(F20, 1)
  253|     women_resid = w_raw.copy()                                               # kept for N1/N2
  254|     # ρ = w/m, used for the old states (T3) from new non-Southern states
  255|     ref = new & ~south_state & ~closed
  256|     rho_new = np.clip(w_raw[:, ref] / m20_pred[:, ref], 0.05, 1.5)
  257|     rho_draw = rho_new[np.arange(D), rng.integers(0, ref.sum(), D)]
  258| 
  259|     # State-sex turnout targets (votes cast by men, by women)
  260|     votes_M = np.where(new, np.clip(m20_pred * M20, 0, T20), 0.0)
  261|     votes_M = np.where(closed[None, :], T20, votes_M)
  262|     # Old states: split with the drawn ratio
  263|     m_old = T20 / np.maximum(M20 + rho_draw[:, None] * F20, 1)
  264|     votes_M = np.where(old[None, :], m_old * M20, votes_M)
  265|     # Neither sex may exceed 98% turnout of its eligible adults; any excess
  266|     # (a draw of the old-state ratio that doesn't fit a high-turnout state)
  267|     # moves to the other sex, so the state total stays exact.
  268|     cap_M, cap_F = 0.98 * M20, 0.98 * F20
  269|     votes_M = np.minimum(votes_M, cap_M)
  270|     votes_M = np.maximum(votes_M, T20 - cap_F)
  271|     votes_F = T20 - votes_M
  272|     clipped = ((W < 0) & new[None, :] & ~closed[None, :]).mean(axis=0)
  273| 
  274|     # T4: Black Southern turnout (Goodman on 1916 men, 11 Southern states),
  275|     # drawn from the regression posterior truncated to its logical bounds
  276|     # [0, white rate] (Goodman with Duncan–Davis bounds).
  277|     from scipy.stats import truncnorm
  278|     blk_men16 = per_state(a16 * can16, ~female & black) / np.maximum(M16, 1)
  279|     t_bs = np.empty(D)
  280|     goodman_south = {}
  281|     for d in range(D):
  282|         X = np.column_stack([np.ones(south_state.sum()), blk_men16[d, south_state]])
  283|         y = m16[d, south_state]
  284|         _, _, info = bayes_ols(X, y, 1, rng)
  285|         b0, b1 = info['beta_hat']
  286|         cov = info['resid_sd'] ** 2 * np.linalg.inv(X.T @ X)
  287|         white = max(b0, 1e-3)
  288|         mu, sd = b0 + b1, float(np.sqrt(cov[0, 0] + cov[1, 1] + 2 * cov[0, 1]))
  289|         a_, b_ = (0 - mu) / sd, (white - mu) / sd
  290|         black_rate = float(truncnorm.rvs(a_, b_, loc=mu, scale=sd, random_state=rng))
  291|         t_bs[d] = black_rate / white
  292|         if d == 0:
  293|             goodman_south = {'white_rate': float(b0), 'black_rate_unbounded': float(mu), 'black_rate_se': sd}
  294| 
  295|     # Build the world: can, t, and the exclusion split
  296|     can = np.broadcast_to(can20, (D, C)).copy()
  297|     excluded = np.zeros((D, C))
  298|     bs = black & south_cell
  299|     excluded[:, bs] = can[:, bs] * (1 - t_bs[:, None])
  300|     can_eff = can - excluded
  301|     # Calibrate a logit shift per state and sex so votes match exactly.
  302|     t = np.zeros((D, C))
  303|     for d in range(D):
  304|         for sex, target in (('M', votes_M[d]), ('F', votes_F[d])):
  305|             m = (c.sex == sex).to_numpy()
  306|             for s in range(S):
  307|                 cells_s = np.where(m & (sidx == s))[0]
  308|                 elig = a20[d, cells_s] * can_eff[d, cells_s]
  309|                 if elig.sum() <= 0 or target[s] <= 0:
  310|                     t[d, cells_s] = 0.0
  311|                     continue
  312|                 t[d, cells_s] = min(target[s] / elig.sum(), 1.0)
  313|     # Cells with all eligible voting at t>1 would be clipped; flag them
  314|     over = (votes_M / np.maximum(M20, 1) > 1).mean(axis=0)
  315| 
  316|     # C1: women's tilt δ (per draw, re-fitted on this draw's f)
  317|     rd16 = logit(ret.R16 / (ret.R16 + ret.D16)).to_numpy()
  318|     rd20 = logit(ret.R20 / (ret.R20 + ret.D20)).to_numpy()
  319|     y = rd20 - rd16
  320|     delta = np.empty(D)
  321|     swing_ns = np.empty(D)
  322|     swing_s = np.empty(D)
  323|     for d in range(D):
  324|         f = np.where(new & ~closed, votes_F[d] / T20[0], 0.0)
  325|         X = np.column_stack([~south_state, south_state, f]).astype(float)
  326|         b, _, _ = bayes_ols(X, y, 1, rng)
  327|         swing_ns[d], swing_s[d], delta[d] = b[0]
  328| 
  329|     # C2: Black voters' shift β_B: prior N(1.5, 1.0) [I] updated by a Goodman
  330|     # regression across non-Southern states with region intercepts (so region
  331|     # doesn't stand in for race) and the 1916 share as a covariate.
  332|     blk_votes = per_state((a20 * can_eff * t), black) / T20
  333|     ns = ~south_state
  334|     reg_dummies = np.column_stack([[REGION_OF[s] == g for s in states] for g in ('northeast', 'midwest', 'west', 'border')]).astype(float)
  335|     beta_B = np.empty(D)
  336|     for d in range(D):
  337|         X = np.column_stack([reg_dummies[ns], rd16[ns], blk_votes[d, ns]])
  338|         b, _, _ = bayes_ols(X, rd20[ns], 1, rng, prior_mean=[0, 0, 0, 0, 1, 1.5], prior_sd=[10, 10, 10, 10, 10, 1.0])
  339|         beta_B[d] = b[0, -1] if not beta_b_prior_only else rng.normal(1.5, 1.0)  # sensitivity: prior only
  340| 
  341|     # C3: exact calibration of shares
  342|     share = np.zeros((D, C, 3))
  343|     shift_R = np.where(female, 1, 0)[None, :] * delta[:, None] + black[None, :] * beta_B[:, None]
  344|     votes_cell = a20 * can_eff * t
  345|     R20, O20 = ret.R20.to_numpy(), ret.O20.to_numpy()
  346|     D20 = ret.D20.to_numpy()
  347|     for d in range(D):
  348|         for s in range(S):
  349|             idx = np.where(sidx == s)[0]
  350|             v = votes_cell[d, idx]
  351|             if v.sum() <= 0:
  352|                 continue
  353|             pR, pO = _solve(v, shift_R[d, idx], R20[s] / T20[0, s] * v.sum(), O20[s] / T20[0, s] * v.sum())
  354|             share[d, idx, 0], share[d, idx, 2], share[d, idx, 1] = pR, pO, 1 - pR - pO
  355| 
  356|     # C3b: Black Southern voters split like Black voters outside the South
  357|     # (the assumption `fifteenth` borrows), subject to an accounting bound:
  358|     # their votes for either major party can't exceed 80% of that party's
  359|     # certified vote in the state (in South Carolina Harding got 2,610 votes).
  360|     # Where the bound binds, Black Southern turnout is lowered, the difference
  361|     # is counted as exclusion, and the state's other voters of the same sex
  362|     # make up the total. The rest of the state is then re-calibrated.
  363|     bound_hits = _black_south_bound(D, S, sidx, south_state, black, south_cell, female, votes_cell, share, can_eff, t,
  364|                                     R20, D20, O20, T20[0], shift_R)
  365|     excluded = can - can_eff
  366| 
  367|     barred_by = {
  368|         'legal': a20 * 0 + (1 - can),
  369|         'excluded': excluded,
  370|     }
  371|     world = World(adults=a20, can=can_eff, t=t, share=share, barred_by=barred_by)
  372|     cells = c.assign(region=c.state.map(REGION_OF), south=south_cell, legal_reason=reason20)
  373|     params = {'kappa_mean': kappa_mean, 'rho': rho_draw, 't_black_south_rel': t_bs, 'delta': delta,
  374|               'beta_B': beta_B, 'swing_nonsouth': swing_ns, 'swing_south': swing_s}
  375|     diag = {
  376|         'states': states,
  377|         'old_states': [s for s, o in zip(states, old) if o],
  378|         'women_turnout_resid': women_resid,      # [D, S] women's implied turnout (N1/N2)
  379|         'men_turnout_pred': m20_pred,
  380|         'women_negative_share': dict(zip(states, clipped.tolist())),
  381|         'men_turnout_over_1': dict(zip(states, over.tolist())),
  382|         'goodman_south_first_draw': goodman_south,
  383|         'black_south_bound_share': dict(zip(states, (bound_hits / D).tolist())),
  384|         'E16': E16, 'E20': E20, 'T16': T16[0], 'T20': T20[0], 'm16': m16,
  385|         'votes_F': votes_F, 'votes_M': votes_M, 'F20': F20, 'M20': M20,
  386|     }
  387|     return Fit(world=world, cells=cells, params=params, diagnostics=diag)
  388| 
  389| 
  390| def carry_forward(base: Fit, inp: Inputs, year: int, seed: int) -> Fit:
  391|     """A later election with no natural experiment of its own (1924): the base
  392|     year's fit supplies the group structure, and the new year's returns
  393|     calibrate it exactly.
  394| 
  395|     Per draw d (the base fit's draw d):
  396|       P   adults: the base cells aged to election day (data.population) with
  397|           fresh census noise.
  398|       X   Black Southern exclusion: the base year's relative turnout t_bs.
  399|       T   turnout: the base year's cell turnout in logits, plus one shift per
  400|           state (all groups and both sexes alike) solved so the state's total
  401|           votes match. So the base year's women-to-men and group ratios carry
  402|           forward [I]; Corder–Wolbrecht 1924 is held out to check that.
  403|           Cells that couldn't vote in the base year (Georgia and Mississippi
  404|           women in 1920) start from their state's men times the median
  405|           women-to-men turnout ratio of the other Southern states.
  406|       C   choice: the base year's tilts (women δ, Black voters β_B), then the
  407|           same exact calibration (C3, C3b) to the year's R, D and other votes.
  408|           A third candidate's vote (La Follette) is spread evenly across a
  409|           state's groups: within-state differences in it aren't identified.
  410|     """
  411|     rng = np.random.default_rng(seed + year)
  412|     c = inp.cells.reset_index(drop=True)
  413|     assert (c[['state', 'sex', 'group']].to_numpy() == base.cells[['state', 'sex', 'group']].to_numpy()).all()
  414|     states = base.diagnostics['states']
  415|     S, C = len(states), len(c)
  416|     D = base.world.t.shape[0]
  417|     sidx = np.array([states.index(s) for s in c.state])
  418|     female = (c.sex == 'F').to_numpy()
  419|     black = (c.group == 'black').to_numpy()
  420|     south_state = np.array([s in SOUTH for s in states])
  421|     south_cell = south_state[sidx]
  422|     y = year % 100
  423|     ret = inp.returns.loc[states]
  424|     T, R, Dm, O = (ret[f'{k}{y}'].to_numpy() for k in ('T', 'R', 'D', 'O'))
  425| 
  426|     def per_state(x):
  427|         out = np.zeros((x.shape[0], S))
  428|         np.add.at(out, (slice(None), sidx), x)
  429|         return out
  430| 
  431|     cv = {'native_white': 0.02, 'foreign_white_naturalized': 0.04, 'foreign_white_alien': 0.05, 'black': 0.05, 'other': 0.08}
  432|     cv_c = c.group.map(cv).to_numpy()
  433|     a = c.adults20.to_numpy()[None, :] * np.exp(rng.normal(0, 1, (D, C)) * cv_c - cv_c ** 2 / 2)
  434| 
  435|     can1, reason = legal_can(inp, year)
  436|     can = np.broadcast_to(can1, (D, C)).copy()
  437|     t_bs = base.params['t_black_south_rel']
  438|     excluded = np.zeros((D, C))
  439|     bs = black & south_cell
  440|     excluded[:, bs] = can[:, bs] * (1 - t_bs[:, None])
  441|     can_eff = can - excluded
  442| 
  443|     # T: turnout prior from the base year, one logit shift per state.
  444|     t0 = base.world.t.copy()
  445|     male_of = {(r.state, r.group): i for i, r in c.iterrows() if r.sex == 'M'}
  446|     mate = np.array([male_of.get((r.state, r.group), i) for i, r in c.iterrows()])
  447|     sw = female & south_cell & (t0.mean(axis=0) > 0)
  448|     ratio = np.median(np.where(sw[None, :], t0 / np.maximum(t0[:, mate], 1e-6), np.nan)[:, sw], axis=1)
  449|     gap = (t0 <= 0) & (can_eff > 0) & female[None, :]
  450|     t0 = np.where(gap, t0[:, mate] * ratio[:, None], t0)
  451|     lt = logit(np.clip(t0, 1e-4, 0.995))
  452|     elig = a * can_eff
  453|     lo, hi = np.full((D, S), -8.0), np.full((D, S), 8.0)
  454|     for _ in range(60):
  455|         mid = (lo + hi) / 2
  456|         v = per_state(elig * expit(lt + mid[:, sidx]))
  457|         over = v > T[None, :]
  458|         hi, lo = np.where(over, mid, hi), np.where(over, lo, mid)
  459|     k = (lo + hi) / 2
  460|     t = np.where(elig > 0, expit(lt + k[:, sidx]), 0.0)
  461|     votes_cell = elig * t
  462| 
  463|     # C: the base year's tilts, recalibrated exactly.
  464|     delta, beta_B = base.params['delta'], base.params['beta_B']
  465|     shift_R = female[None, :] * delta[:, None] + black[None, :] * beta_B[:, None]
  466|     share = np.zeros((D, C, 3))
  467|     for d in range(D):
  468|         for s in range(S):
  469|             idx = np.where(sidx == s)[0]
  470|             v = votes_cell[d, idx]
  471|             if v.sum() <= 0:
  472|                 continue
  473|             pR, pO = _solve(v, shift_R[d, idx], R[s] / T[s] * v.sum(), O[s] / T[s] * v.sum())
  474|             share[d, idx, 0], share[d, idx, 2], share[d, idx, 1] = pR, pO, 1 - pR - pO
  475|     bound_hits = _black_south_bound(D, S, sidx, south_state, black, south_cell, female, votes_cell, share, can_eff, t,
  476|                                     R, Dm, O, T, shift_R)
  477|     world = World(adults=a, can=can_eff, t=t, share=share, barred_by={'legal': 1 - can, 'excluded': can - can_eff})
  478|     cells = c.assign(region=c.state.map(REGION_OF), south=south_cell, legal_reason=reason)
  479|     F = per_state(a * can_eff * female[None, :])
  480|     diag = {'states': states, 'base_year': base.diagnostics.get('year', 1920), 'turnout_shift': k,
  481|             'women_turnout': per_state(votes_cell * female[None, :]) / np.maximum(F, 1),
  482|             'men_turnout': per_state(votes_cell * ~female[None, :]) / np.maximum(per_state(a * can_eff * ~female[None, :]), 1),
  483|             'black_south_bound_share': dict(zip(states, (bound_hits / D).tolist())), 'gap_ratio': ratio}
  484|     params = {'delta': delta, 'beta_B': beta_B, 't_black_south_rel': t_bs, 'turnout_shift': k}
  485|     return Fit(world=world, cells=cells, params=params, diagnostics=diag)
  486| 
  487| 
  488| # ── General years (general_fit): every year without 1920's natural experiment or a base year ──
  489| #
  490| # Priors are (year, mean, sd) knots, linear between knots and flat beyond the
  491| # ends; every one is [I] (an assumption from the literature, not estimated
  492| # here). Sources and judgement calls: notes/B.md.
  493| 
  494| # Turnout, logit offset against native white adults of the same state and sex.
  495| WOMEN_TURNOUT = [(1789, -1.3, 0.4), (1916, -1.3, 0.4), (1920, -1.3, 0.3), (1928, -1.0, 0.3), (1940, -0.7, 0.25),
  496|                  (1952, -0.45, 0.2), (1964, -0.24, 0.1), (1972, -0.09, 0.08), (1980, 0.0, 0.08), (1992, 0.09, 0.06),
  497|                  (2008, 0.18, 0.06), (2024, 0.16, 0.06)]       # against men: C–W 2016; ANES; CPS P20
  498| # The WOMEN_TURNOUT knots taken from Corder–Wolbrecht (2016). A general_fit year
  499| # whose prior interpolates from one of them can't be scored against
  500| # Corder–Wolbrecht as held out: that would check the prior against its own source.
  501| CW_PRIOR_KNOTS = (1928, 1940)
  502| NAT_TURNOUT = [(1789, -0.3, 0.3), (2024, -0.3, 0.25)]          # Merriam–Gosnell 1924; CPS naturalized vs native
  503| ALIEN_TURNOUT = [(1789, -0.6, 0.4), (2024, -0.6, 0.4)]         # declarant aliens where legal (to 1926)
  504| OTHER_TURNOUT = [(1789, -0.3, 0.4), (2024, -0.3, 0.4)]
  505| BLACK_TURNOUT = [(1789, 0.0, 0.4), (1960, 0.0, 0.3), (1964, -0.5, 0.2), (1976, -0.5, 0.15), (1984, -0.25, 0.15),
  506|                  (1992, -0.4, 0.15), (2000, -0.2, 0.15), (2004, -0.3, 0.15), (2008, -0.06, 0.12), (2012, 0.09, 0.12),
  507|                  (2016, -0.24, 0.12), (2020, -0.37, 0.12), (2024, -0.45, 0.2)]   # CPS P20, citizen basis
  508| # Black Southern exclusion: share of legally eligible Black adults in the
  509| # eleven ex-Confederate states kept from voting (beta draws; 0 = none).
  510| BLACK_SOUTH_EXCLUDED = [(1866, 0.0, 0.0), (1868, 0.15, 0.1), (1872, 0.1, 0.08), (1876, 0.2, 0.1), (1880, 0.35, 0.12),
  511|                         (1888, 0.4, 0.12), (1892, 0.55, 0.12), (1896, 0.6, 0.12), (1900, 0.75, 0.1),
  512|                         (1904, 0.884, 0.104), (1944, 0.884, 0.104),     # 1920 fit's t_bs posterior (0.116 ± 0.104)
  513|                         (1948, 0.77, 0.08), (1952, 0.67, 0.08), (1956, 0.6, 0.08), (1960, 0.52, 0.08),
  514|                         (1964, 0.41, 0.08), (1968, 0.25, 0.07), (1972, 0.15, 0.06), (1976, 0.1, 0.05), (1980, 0.0, 0.0)]
  515| BOUND_YEARS = (1892, 1964)     # C3b accounting bound (_black_south_bound) applies in these years
  516| 
  517| # Choice, logit tilt toward R (vs D) against white / native voters of the same state.
  518| DELTA_1920 = (-0.662, 0.272)   # backbone.fit(1920), 400 draws: posterior mean, sd of δ (DISCLOSURES B4)
  519| WOMEN_TILT = [(1789, *DELTA_1920), (1940, *DELTA_1920), (1944, 0.0, 0.3), (1948, 0.05, 0.25), (1952, 0.2, 0.2),
  520|               (1956, 0.25, 0.2), (1960, 0.1, 0.2), (1964, -0.08, 0.2), (1968, 0.0, 0.2), (1972, 0.0, 0.2),
  521|               (1976, 0.15, 0.2), (1980, -0.38, 0.15), (1984, -0.28, 0.15), (1988, -0.31, 0.15), (1992, -0.12, 0.15),
  522|               (1996, -0.37, 0.15), (2000, -0.46, 0.15), (2004, -0.28, 0.15), (2008, -0.24, 0.15), (2012, -0.37, 0.15),
  523|               (2016, -0.52, 0.15), (2020, -0.47, 0.15), (2024, -0.43, 0.15)]   # Gallup 1944–76; exit polls 1980–
  524| BLACK_TILT = [(1789, 0.5, 1.0), (1852, 0.5, 1.0), (1856, 1.5, 1.0), (1864, 1.5, 1.0), (1868, 2.5, 1.0), (1876, 2.5, 1.0),
  525|               (1880, 1.5, 1.0), (1928, 1.5, 1.0), (1932, 1.0, 0.7), (1936, -0.4, 0.6), (1940, -0.55, 0.5),
  526|               (1944, -0.6, 0.5), (1948, -1.1, 0.5), (1952, -1.6, 0.5), (1956, -0.8, 0.5), (1960, -0.8, 0.5),
  527|               (1964, -2.4, 0.4), (1968, -2.2, 0.4), (1972, -2.65, 0.4), (1976, -1.7, 0.4), (1980, -2.2, 0.4),
  528|               (1984, -2.9, 0.4), (1988, -2.6, 0.4), (1992, -2.15, 0.4), (1996, -2.0, 0.4), (2000, -2.55, 0.4),
  529|               (2004, -2.4, 0.4), (2008, -3.4, 0.4), (2012, -3.15, 0.4), (2016, -2.9, 0.4), (2020, -2.5, 0.4),
  530|               (2024, -2.1, 0.4)]
  531| NAT_TILT = [(1789, -0.5, 0.6), (1892, -0.5, 0.5), (1896, 0.0, 0.5), (1924, 0.0, 0.5), (1928, -0.6, 0.4),
  532|             (1960, -0.6, 0.4), (1964, -0.2, 0.4), (1988, -0.2, 0.4), (1992, -0.4, 0.4), (2024, -0.3, 0.4)]
  533| OTHER_TILT = [(1789, 0.0, 0.7), (2024, 0.0, 0.7)]
  534| 
  535| POP_CV = {'native_white': 0.02, 'foreign_white_naturalized': 0.04, 'foreign_white_alien': 0.05, 'black': 0.05, 'other': 0.08}
  536| 
  537| 
  538| def prior_at(table, year):
  539|     """(mean, sd) of a knot table at `year`."""
  540|     ys = np.array([k[0] for k in table], float)
  541|     return float(np.interp(year, ys, [k[1] for k in table])), float(np.interp(year, ys, [k[2] for k in table]))
  542| 
  543| 
  544| def cw_held_out(year: int, method: str | None) -> bool:
  545|     """Whether Corder–Wolbrecht is held out from this year's fit: always, except a
  546|     general_fit year whose women's-turnout prior uses a CW_PRIOR_KNOTS knot."""
  547|     if method != 'general_fit':
  548|         return True
  549|     ys = [k[0] for k in WOMEN_TURNOUT]
  550|     if year in ys:
  551|         return year not in CW_PRIOR_KNOTS
  552|     lo = max((y for y in ys if y < year), default=None)
  553|     hi = min((y for y in ys if y > year), default=None)
  554|     return not ({lo, hi} & set(CW_PRIOR_KNOTS))
  555| 
  556| 
  557| def _draw_normal(rng, table, year, D):
  558|     m, s = prior_at(table, year)
  559|     return m + s * rng.normal(0, 1, D)
  560| 
  561| 
  562| def _draw_beta(rng, table, year, D):
  563|     m, s = prior_at(table, year)
  564|     if m <= 0:
  565|         return np.zeros(D)
  566|     s = min(s, 0.99 * np.sqrt(m * (1 - m)))
  567|     k = m * (1 - m) / s ** 2 - 1
  568|     return rng.beta(m * k, (1 - m) * k, D)
  569| 
  570| 
  571| def _solve_ledger(v, shift, tgt, iters=1000, tol=1e-11):
  572|     """_solve for any ledger, vectorised over draws: v [D, n] votes, shift [D, n]
  573|     the R tilt (D as reference), tgt [D, 3] R, D, O votes. A party with no votes
  574|     gets share exactly 0; the base is the state's largest party, so near-unanimous
  575|     and minor-party-majority states converge. Returns shares [D, n, 3]."""
  576|     Dn, n = v.shape
  577|     tgt = np.maximum(tgt, 0.0)
  578|     act = tgt[0] > 0
  579|     P = np.zeros((Dn, n, 3))
  580|     if not act.any():
  581|         P[..., 1] = 1.0
  582|         return P
  583|     base = int(np.argmax(tgt[0]))
  584|     if act.sum() == 1:
  585|         P[..., base] = 1.0
  586|         return P
  587|     sh = np.zeros((Dn, n, 3))
  588|     sh[..., 0] = shift
  589|     a = np.zeros((Dn, 3))
  590|     upd = [j for j in range(3) if act[j] and j != base]
  591|     total = v.sum(axis=1)
  592|     for _ in range(iters):
  593|         u = a[:, None, :] + sh
  594|         u = np.where(act[None, None, :], u - u[..., base:base + 1], -np.inf)
  595|         e = np.exp(u - u.max(axis=2, keepdims=True))
  596|         P = e / e.sum(axis=2, keepdims=True)
  597|         cur = (v[..., None] * P).sum(axis=1)
  598|         if (np.abs(cur - tgt)[:, act] <= tol * total[:, None] + 1e-9).all():
  599|             break
  600|         for j in upd:
  601|             a[:, j] += np.log(tgt[:, j] / np.maximum(cur[:, j], 1e-300))
  602|     return P
  603| 
  604| 
  605| def _solve_scalar(v, shift, tR, tO):
  606|     """_solve's signature on _solve_ledger (for _black_south_bound in general years)."""
  607|     tgt = np.array([[tR, max(v.sum() - tR - tO, 0.0), tO]])
  608|     P = _solve_ledger(v[None, :], shift[None, :], tgt)[0]
  609|     return P[:, 0], P[:, 2]
  610| 
  611| 
  612| def general_fit(inp: Inputs, year: int, draws: int, seed: int, delta_draws: np.ndarray | None = None,
  613|                 pop_cv: dict | None = None) -> Fit:
  614|     """Any year with neither 1920's natural experiment nor a base year.
  615| 
  616|     Per draw d:
  617|       L   legal: legal_can(inp, year) (women_vote, black_can, white_can,
  618|           alien_voting, other_citizen); legislature states (no_popular) cast 0.
  619|       X   Black Southern exclusion (1868–1976): a beta draw of the share kept
  620|           from voting, era prior BLACK_SOUTH_EXCLUDED [I]; Reconstruction low.
  621|       T   turnout: group logit offsets drawn from era priors (women, naturalized,
  622|           aliens, Black, other) [I], plus one shift per state (bisection) so the
  623|           state's votes are exactly R + D + O. If the ledger exceeds 97% of the
  624|           eligible, the state's adults are scaled up (flagged).
  625|       C   choice: R tilts drawn from era priors (women δ, Black β_B, naturalized
  626|           β_N, other β_O) [I]; per state the R, D and O intercepts are solved
  627|           exactly (_solve_ledger: zero-vote parties get 0). O is spread like
  628|           carry_forward (one intercept per state). 1892–1964: the C3b bound.
  629|       delta_draws: optional δ draws from a 1920 fit to use for 1920–1940 in
  630|           place of the summary prior DELTA_1920.
  631|       pop_cv: census-noise CVs by group (POP_CV by default; zeros for run.uncertainty_budget).
  632|     """
  633|     rng = np.random.default_rng(seed + year)
  634|     D = draws
  635|     yy = year % 100
  636|     c0 = inp.cells.reset_index(drop=True)
  637|     acol = 'adults20' if 'adults20' in c0 else 'adults'
  638|     can0, reason0 = legal_can(inp, year)
  639| 
  640|     # ── Ledger: R, D, O per state; targets are R + D + O (verify checks those) ──
  641|     rr = inp.returns
  642|     col = lambda k: rr[f'{k}{yy}'] if f'{k}{yy}' in rr else pd.Series(0.0, index=rr.index)
  643|     led = pd.DataFrame({k: pd.to_numeric(col(k), errors='coerce') for k in 'RDOTP'}).fillna(0.0)
  644|     if f'O{yy}' not in rr:
  645|         led['O'] = (led['T'] - led['R'] - led['D']).clip(lower=0)
  646|     ev_idx = set(map(str, getattr(inp.ev, 'index', [])))
  647|     keep = set(map(str, led.index)) | ev_idx | set(inp.no_popular)
  648|     dropped = sorted(set(c0.state) - keep)
  649|     c0 = c0[~c0.state.isin(dropped)].reset_index(drop=True) if dropped else c0
  650|     if dropped:
  651|         m_keep = ~inp.cells.reset_index(drop=True).state.isin(dropped).to_numpy()
  652|         can0, reason0 = can0[m_keep], [r for r, k in zip(reason0, m_keep) if k]
  653|     states = sorted(set(map(str, led.index)) | set(c0.state) | (ev_idx & set(inp.no_popular)))
  654|     missing = sorted(set(states) - set(map(str, led.index)))
  655|     led = led.reindex(states).fillna(0.0)
  656|     for s in inp.no_popular:
  657|         if s in led.index:
  658|             led.loc[s, ['R', 'D', 'O', 'T', 'P']] = 0.0
  659|     R, Dm, O = (led[k].to_numpy(float) for k in 'RDO')
  660|     R, Dm, O = np.maximum(R, 0), np.maximum(Dm, 0), np.maximum(O, 0)
  661|     T = R + Dm + O
  662|     t_mismatch = {s: float(a - b) for s, a, b in zip(states, led['T'], T) if abs(a - b) > 0.5 and a > 0}
  663| 
  664|     # ── Synthetic cells: a state with votes but no population cells ──
  665|     women_ok = lambda s: year >= 1920 or s in inp.women_vote
  666|     pop_s = c0.groupby('state')[acol].sum()
  667|     syn_rows = []
  668|     for s, tv in zip(states, T):
  669|         if tv > 0 and pop_s.get(s, 0.0) <= 0:
  670|             sexes = ['M', 'F'] if women_ok(s) else ['M']
  671|             for x in sexes:
  672|                 syn_rows.append({'state': s, 'sex': x, 'group': 'native_white', acol: tv / 0.6 / len(sexes)})
  673|     c = c0.assign(synthetic=False)
  674|     if syn_rows:
  675|         c = pd.concat([c, pd.DataFrame(syn_rows).assign(synthetic=True)], ignore_index=True)
  676|         can0 = np.concatenate([can0, np.ones(len(syn_rows))])
  677|         reason0 = list(reason0) + [''] * len(syn_rows)
  678|     S, C = len(states), len(c)
  679|     sidx = np.array([states.index(s) for s in c.state])
  680|     female = (c.sex == 'F').to_numpy()
  681|     grp = c.group.to_numpy()
  682|     black, nat, alien, other = (grp == 'black'), (grp == 'foreign_white_naturalized'), (grp == 'foreign_white_alien'), (grp == 'other')
  683|     south_state = np.array([s in SOUTH for s in states])
  684|     south_cell = south_state[sidx]
  685|     no_pop = np.array([s in inp.no_popular for s in states])
  686| 
  687|     def per_state(x):
  688|         out = np.zeros((x.shape[0], S))
  689|         np.add.at(out, (slice(None), sidx), x)
  690|         return out
  691| 
  692|     # ── P: population draws ──
  693|     cv_c = c.group.map(pop_cv or POP_CV).fillna(0.0 if pop_cv else 0.05).to_numpy()
  694|     a = c[acol].fillna(0.0).to_numpy(float)[None, :] * np.exp(rng.normal(0, 1, (D, C)) * cv_c - cv_c ** 2 / 2)
  695| 
  696|     # ── L, X: legal and practical eligibility ──
  697|     can = np.broadcast_to(can0, (D, C)).copy()
  698|     reason = list(reason0)
  699|     contradict = []
  700|     for s in np.where((T > 0) & ((a * can).sum(axis=0) @ np.eye(S)[sidx] <= 0))[0]:
  701|         # Votes cast where the coded rules bar everyone: the rules lose (men first).
  702|         m = (sidx == s) & ~female if ((sidx == s) & ~female & (a[0] > 0)).any() else (sidx == s)
  703|         can[:, m] = 1.0
  704|         for i in np.where(m)[0]:
  705|             reason[i] = ''
  706|         contradict.append(states[s])
  707|     x_bs = _draw_beta(rng, BLACK_SOUTH_EXCLUDED, year, D) if year >= 1868 else np.zeros(D)
  708|     bs = black & south_cell
  709|     excluded = np.zeros((D, C))
  710|     excluded[:, bs] = can[:, bs] * x_bs[:, None]
  711|     can_eff = can - excluded
  712| 
  713|     # ── T: turnout ──
  714|     pri = {'women_turnout': WOMEN_TURNOUT, 'naturalized_turnout': NAT_TURNOUT, 'alien_turnout': ALIEN_TURNOUT,
  715|            'black_turnout': BLACK_TURNOUT, 'other_turnout': OTHER_TURNOUT}
  716|     dr = {k: _draw_normal(rng, tab, year, D) for k, tab in pri.items()}
  717|     off = (female[None, :] * dr['women_turnout'][:, None] + nat[None, :] * dr['naturalized_turnout'][:, None]
  718|            + alien[None, :] * dr['alien_turnout'][:, None] + black[None, :] * dr['black_turnout'][:, None]
  719|            + other[None, :] * dr['other_turnout'][:, None])
  720|     elig = a * can_eff
  721|     E = per_state(elig)
  722|     cap = 0.97
  723|     need = np.where(E > 0, T[None, :] / np.maximum(cap * E, 1e-9), 1.0)
  724|     grow = np.maximum(need, 1.0)
  725|     scaled = (grow > 1).mean(axis=0)
  726|     a = a * grow[:, sidx]
  727|     elig = a * can_eff
  728|     lo, hi = np.full((D, S), -30.0), np.full((D, S), 30.0)
  729|     for _ in range(100):
  730|         mid = (lo + hi) / 2
  731|         v = per_state(elig * expit(off + mid[:, sidx]))
  732|         over = v > T[None, :]
  733|         hi, lo = np.where(over, mid, hi), np.where(over, lo, mid)
  734|     k = (lo + hi) / 2
  735|     t = np.where(elig > 0, expit(off + k[:, sidx]), 0.0)
  736|     t[:, (T <= 0)[sidx]] = 0.0
  737|     V = per_state(elig * t)
  738|     t = np.minimum(t * np.where(V > 0, T[None, :] / np.maximum(V, 1e-300), 0.0)[:, sidx], 1.0)
  739|     votes_cell = elig * t
  740| 
  741|     # ── C: choice ──
  742|     if delta_draws is not None and 1920 <= year <= 1940:
  743|         delta = np.asarray(delta_draws, float)[np.arange(D) % len(delta_draws)]
  744|     else:
  745|         delta = _draw_normal(rng, WOMEN_TILT, year, D)
  746|     beta_B = _draw_normal(rng, BLACK_TILT, year, D)
  747|     beta_N = _draw_normal(rng, NAT_TILT, year, D)
  748|     beta_O = _draw_normal(rng, OTHER_TILT, year, D)
  749|     shift_R = (female[None, :] * delta[:, None] + black[None, :] * beta_B[:, None]
  750|                + (nat | alien)[None, :] * beta_N[:, None] + other[None, :] * beta_O[:, None])
  751|     share = np.zeros((D, C, 3))
  752|     share[..., 1] = 1.0
  753|     ledger = np.stack([R, Dm, O], axis=1)
  754|     for s in range(S):
  755|         idx = np.where(sidx == s)[0]
  756|         if len(idx) == 0 or T[s] <= 0:
  757|             continue
  758|         v = votes_cell[:, idx]
  759|         tgt = ledger[s][None, :] / T[s] * v.sum(axis=1, keepdims=True)
  760|         share[:, idx, :] = _solve_ledger(v, shift_R[:, idx], tgt)
  761|     bound_hits = np.zeros(S)
  762|     nsb_votes = votes_cell[:, black & ~south_cell].sum(axis=1)
  763|     bound_on = BOUND_YEARS[0] <= year <= BOUND_YEARS[1] and bs.any() and bool((nsb_votes > 0).all())
  764|     if bound_on:
  765|         bound_hits = _black_south_bound(D, S, sidx, south_state & (T > 0), black, south_cell, female, votes_cell, share,
  766|                                         can_eff, t, R, Dm, O, np.maximum(T, 1e-9), shift_R, solver=_solve_scalar)
  767| 
  768|     world = World(adults=a, can=can_eff, t=t, share=share, barred_by={'legal': 1 - can, 'excluded': can - can_eff})
  769|     # AK and HI (from 1960) aren't in geo.REGION_OF yet: 'west' so cohort merging has a region.
  770|     cells = c.assign(region=c.state.map(REGION_OF).fillna('west'), south=south_cell, legal_reason=reason)
  771|     F = per_state(a * can_eff * female[None, :])
  772|     M = per_state(a * can_eff * ~female[None, :])
  773|     vF, vM = per_state(votes_cell * female[None, :]), per_state(votes_cell * ~female[None, :])
  774|     prior_used = {k: prior_at(tab, year) for k, tab in
  775|                   {**pri, 'black_south_excluded': BLACK_SOUTH_EXCLUDED, 'women_tilt': WOMEN_TILT,
  776|                    'black_tilt': BLACK_TILT, 'naturalized_tilt': NAT_TILT, 'other_tilt': OTHER_TILT}.items()}
  777|     P = led['P'].to_numpy(float)
  778|     diag = {
  779|         'states': states, 'year': year, 'method': 'general_fit', 'old_states': sorted(inp.women_vote),
  780|         'priors': prior_used,
  781|         'no_popular': sorted(s for s, n in zip(states, no_pop) if n),
  782|         'missing_returns': missing,
  783|         'dropped_cell_states': dropped,
  784|         'synthetic_cell_states': sorted({r['state'] for r in syn_rows}),
  785|         'legal_rules_contradicted': contradict,
  786|         'T_column_mismatch': t_mismatch,
  787|         'zero_party': {p: [s for s, x, tv in zip(states, arr, T) if tv > 0 and x <= 0]
  788|                        for p, arr in (('R', R), ('D', Dm), ('O', O))},
  789|         'other_majority': [s for s, o, tv in zip(states, O, T) if tv > 0 and o > 0.5 * tv],
  790|         'third_candidate_share_of_O': {s: float(p / o) for s, p, o in zip(states, P, O) if o > 0 and p > 0},
  791|         'adults_scaled_share': dict(zip(states, scaled.tolist())),
  792|         'turnout_shift': k,
  793|         'women_turnout': vF / np.maximum(F, 1), 'men_turnout': vM / np.maximum(M, 1),
  794|         'votes_F': vF, 'votes_M': vM, 'F20': F, 'M20': M, 'T20': T,
  795|         'black_south_bound_on': bound_on,
  796|         'black_south_bound_share': dict(zip(states, (bound_hits / D).tolist())),
  797|     }
  798|     params = {'delta': delta, 'beta_B': beta_B, 'beta_N': beta_N, 'beta_O': beta_O,
  799|               't_black_south_rel': 1 - x_bs, 'turnout_shift': k, **{f'off_{k_}': v_ for k_, v_ in dr.items()}}
  800|     return Fit(world=world, cells=cells, params=params, diagnostics=diag)
```

## `simharness/benchmarks.py`

```python
    1| """Held-out benchmarks. Only the validation stages (Run.evaluate, and
    2| Run.verify's Corder–Wolbrecht comparison) import this module; the backbone,
    3| the agents and the publisher never do (checked by test_benchmarks_isolated in
    4| tests/test_isolation.py, which parses every module and script).
    5| """
    6| from __future__ import annotations
    7| 
    8| import numpy as np
    9| import pandas as pd
   10| 
   11| from .config import CACHE
   12| from .evaluate import check
   13| 
   14| CW_STATES = ['CT', 'IL', 'MA', 'MI', 'NY']
   15| 
   16| 
   17| def corder_wolbrecht_any_year() -> pd.DataFrame:
   18|     """Every year and state in the Corder–Wolbrecht file (for `run verify`); empty when it isn't in the cache."""
   19|     f = CACHE / 'benchmarks/corder_wolbrecht_turnout_by_sex.csv'
   20|     return pd.read_csv(f) if f.exists() else pd.DataFrame(columns=['year', 'state'])
   21| 
   22| 
   23| def corder_wolbrecht() -> pd.DataFrame:
   24|     b = pd.read_csv(CACHE / 'benchmarks/corder_wolbrecht_turnout_by_sex.csv')
   25|     return b[(b.year == 1920) & b.state.isin(CW_STATES)].set_index('state')
   26| 
   27| 
   28| def natural_experiment(fit, inp, extras) -> list:
   29|     dg = fit.diagnostics
   30|     states = dg['states']
   31|     idx = {s: i for i, s in enumerate(states)}
   32|     cw = corder_wolbrecht()
   33|     # Corder–Wolbrecht's "eligible" counts are all adults 21+ (they equal the
   34|     # census 21+ totals, non-citizens included), so the like-for-like
   35|     # comparison divides the backbone's women's votes by all women 21+. The
   36|     # citizen-denominator rate is reported alongside (`backbone_citizen`).
   37|     c = fit.cells
   38|     all_f = np.zeros((fit.world.adults.shape[0], len(states)))
   39|     fem = (c.sex == 'F').to_numpy()
   40|     sidx = np.array([idx[s] for s in c.state])
   41|     np.add.at(all_f, (slice(None), sidx[fem]), fit.world.adults[:, fem])
   42|     wt = dg['votes_F'] / np.maximum(all_f, 1)
   43|     wt_cit = dg['votes_F'] / np.maximum(dg['F20'], 1)
   44|     rows, inside = [], []
   45|     for s in CW_STATES:
   46|         d = wt[:, idx[s]]
   47|         lo, hi = np.quantile(d, 0.05), np.quantile(d, 0.95)
   48|         est = float(cw.loc[s, 'women_turnout'])
   49|         rows.append({'state': s, 'backbone': round(float(np.median(d)) * 100, 1), 'lo90': round(lo * 100, 1),
   50|                      'hi90': round(hi * 100, 1), 'corder_wolbrecht': round(est * 100, 1),
   51|                      'cw_lo95': round(float(cw.loc[s, 'women_turnout_lo95']) * 100, 1),
   52|                      'cw_hi95': round(float(cw.loc[s, 'women_turnout_hi95']) * 100, 1),
   53|                      'backbone_citizen': round(float(np.median(wt_cit[:, idx[s]])) * 100, 1),
   54|                      'method': 'ratio (women voted in 1916)' if s in inp.women16 else 'residual (1916 men-only)'})
   55|         inside.append(lo <= est <= hi)
   56|     mae = float(np.mean([abs(r['backbone'] - r['corder_wolbrecht']) for r in rows]))
   57|     cover = float(np.mean(inside))
   58|     out = [check('N1', 'Backbone women\'s turnout vs Corder–Wolbrecht (1920)', {'mae_points': round(mae, 1), 'coverage_90': cover, 'rows': rows},
   59|                  'MAE ≤ 8 points and ≥ 70% inside the 90% interval', mae <= 8 and cover >= 0.7)]
   60| 
   61|     # N2 placebo: GA and MS, where women couldn't register in time
   62|     if inp.closed_1920:
   63|         c = fit.cells
   64|         fem_cit = ((c.sex == 'F') & (c.group != 'foreign_white_alien')).to_numpy()
   65|         prow = []
   66|         ok = True
   67|         for s in sorted(inp.closed_1920):
   68|             m = fem_cit & (c.state == s).to_numpy()
   69|             Fc = fit.world.adults[:, m].sum(axis=1)
   70|             W = dg['T20'][idx[s]] - dg['men_turnout_pred'][:, idx[s]] * dg['M20'][:, idx[s]]
   71|             w = W / Fc
   72|             med = float(np.median(w))
   73|             prow.append({'state': s, 'implied_women_turnout': round(med * 100, 1),
   74|                          'lo90': round(float(np.quantile(w, 0.05)) * 100, 1), 'hi90': round(float(np.quantile(w, 0.95)) * 100, 1)})
   75|             ok = ok and abs(med) <= 0.05
   76|         out.append(check('N2', 'Placebo: implied women\'s turnout where women couldn\'t register (GA, MS)', prow, 'within ±5 points of 0', ok,
   77|                          'Documented: franchise/state_franchise_1920.csv women_nov1920_note (NPS).'))
   78|     else:
   79|         out.append(check('N2', 'Placebo (GA, MS)', None, '±5 points', None, 'not run: the registration closure is not documented in the data'))
   80|     return out
   81| 
   82| 
   83| def agent_checks(an, fit, run, extras) -> list:
   84|     if not an:
   85|         return [check(i, n, None, t, None, 'not run: no agent answers') for i, n, t in [
   86|             ('N3', 'Agent women\'s turnout vs Corder–Wolbrecht', 'MAE ≤ 10'), ('L1', 'Recall probe', 'reported'),
   87|             ('L2', 'Label swap', '< 20% follow the label'), ('A1', 'Cohort bias', 'reported'),
   88|             ('A2', 'Homogenization index', '≤ 25%'), ('A3', 'Prompt and model sensitivity', 'SD < |effect|; signs agree'),
   89|             ('A4', 'Stereotype audit', '≤ 10%')]]
   90|     out = []
   91|     # N3: agents' stated turnout, women in the C-W states (control, sonnet)
   92|     import json
   93|     agents = json.loads((run.dir / 'agents/agents.json').read_text())
   94|     ans = run.answers()
   95|     cw = corder_wolbrecht()
   96|     rows = []
   97|     for s in CW_STATES:
   98|         pv = [ans[f'control|{a["id"]}|{run.bulk}']['data'].get('p_vote', 0) / 100 for a in agents
   99|               if a['state'] == s and a['sex'] == 'F' and a['group'] != 'foreign_white_alien' and f'control|{a["id"]}|{run.bulk}' in ans]
  100|         if pv:
  101|             c = fit.cells
  102|             f = c[(c.state == s) & (c.sex == 'F')]
  103|             cit = f[f.group != 'foreign_white_alien'].adults20.sum() / f.adults20.sum()
  104|             rows.append({'state': s, 'n': len(pv), 'agents': round(float(np.mean(pv)) * cit * 100, 1),
  105|                          'agents_citizen': round(float(np.mean(pv)) * 100, 1),
  106|                          'corder_wolbrecht': round(float(cw.loc[s, 'women_turnout']) * 100, 1)})
  107|     if rows:
  108|         mae = float(np.mean([abs(r['agents'] - r['corder_wolbrecht']) for r in rows]))
  109|         out.append(check('N3', 'Agents\' stated turnout, women, vs Corder–Wolbrecht', {'mae_points': round(mae, 1), 'rows': rows}, 'MAE ≤ 10 points', mae <= 10,
  110|                          f'{sum(r["n"] for r in rows)} women agents in {len(rows)} of 5 states'))
  111|     else:
  112|         out.append(check('N3', 'Agents\' stated turnout, women, vs Corder–Wolbrecht', None, 'MAE ≤ 10 points', None, 'not run: no women agents drawn in those states'))
  113| 
  114|     l1 = an['l1']
  115|     out.append(check('L1', 'Recall probe: identifies year / candidates / winner',
  116|                      {'n': l1['n'], 'year': l1['year_rate'], 'candidates': l1['names_rate'], 'winner': l1['winner_rate'],
  117|                       'exposed_cohorts': len(l1['exposed_cohorts'])},
  118|                      'reported; > 50% winner ⇒ memorization-exposed', None,
  119|                      'memorization-exposed nationally' if an['nationally_exposed'] else 'not exposed nationally'))
  120|     l2 = an['l2']
  121|     out.append(check('L2', 'Label swap: choices that follow the label, not the platform', {'n': l2['n'], 'label': l2['label_rate'], 'platform': l2['platform_rate']},
  122|                      '< 20% follow the label', (l2['label_rate'] is not None and l2['label_rate'] < 0.2) if l2['n'] else None,
  123|                      'With the order flipped too, following the display position is the same as following the platform here; the test separates label from platform.'))
  124|     a1 = an['a1']
  125|     big = [x for x in a1 if x['bias_logit'] is not None and abs(x['bias_logit']) > 1.0]
  126|     out.append(check('A1', 'Cohort bias (control vs calibrated backbone, logit)',
  127|                      {'cohorts': len(a1), 'median_abs_bias': round(float(np.median([abs(x['bias_logit']) for x in a1 if x['bias_logit'] is not None])), 3) if a1 else None,
  128|                       'over_1_logit': len(big), 'mean_tvd': round(float(np.mean([x['tvd'] for x in a1])), 3) if a1 else None},
  129|                      'reported; |bias| > 1 ⇒ shrunk', None, f'{len(big)} cohorts shrunk for bias'))
  130|     a2 = an['a2']
  131|     out.append(check('A2', 'Homogenization index', {'index': a2['homogenization_index'], 'eligible_cohorts': a2['eligible_cohorts']},
  132|                      '≤ 25%', (a2['homogenization_index'] <= 0.25) if a2['homogenization_index'] is not None else None))
  133|     for wk, e in an['effects'].items():
  134|         paras = [v['dr'] for v in e['by_paraphrase'].values()]
  135|         sd = float(np.std(paras, ddof=1)) if len(paras) > 1 else None
  136|         shared = e.get('shared_subsample') or {}
  137|         signs = None
  138|         if 'sonnet' in shared and 'opus' in shared:
  139|             signs = bool(np.sign(shared['sonnet']['dr']) == np.sign(shared['opus']['dr']))
  140|         eff = e['national']['dr']['mean']
  141|         ok = (sd is not None and sd < abs(eff) and signs is True) if (sd is not None and signs is not None) else None
  142|         out.append(check(f'A3:{wk}', f'Prompt and model sensitivity, {wk} (two-party logit effect)',
  143|                          {'national_effect': round(eff, 3), 'paraphrase_sd': round(sd, 3) if sd is not None else None,
  144|                           'by_paraphrase': {k: round(v, 3) for k, v in zip(e['by_paraphrase'], paras)},
  145|                           'sonnet_vs_opus': {m: round(v['dr'], 3) for m, v in shared.items()}},
  146|                          'paraphrase SD < |effect| and Sonnet/Opus agree on sign', ok))
  147|     a4 = an['a4']
  148|     out.append(check('A4', 'Stereotype audit: reasons resting on a group label', {'audited': a4['audited'], 'flagged': a4['flagged'], 'rate': a4['rate']},
  149|                      '≤ 10%', a4['rate'] <= 0.10, 'Heuristic first pass (quotes.LABEL_DRIVEN); flagged examples in analysis.json.'))
  150|     return out
```

## `simharness/cohorts.py`

```python
    1| """Agent cohorts: strata of the cell table, merged to a cost cap.
    2| 
    3| Stratification for 1920 (justified in METHOD.md §A.2): region × sex ×
    4| race/nativity/citizenship. These are the dimensions the franchise turned on in
    5| 1920 (sex, citizenship, race in practice) plus region, which carried the
    6| parties' coalitions. Age and urban/rural vary within a cohort's agents (persona
    7| diversity) but don't define cohorts: no 1920 source identifies their effect.
    8| 
    9| Merge rule: while there are more cohorts than the cap, or any cohort holds
   10| under `min_share` of eligible-or-barred adults, fold the smallest into the same
   11| sex and group in the nearest region (geo.NEAREST_REGION); a cohort with no
   12| same-(sex, group) neighbour left folds into the national cohort for that sex
   13| and group. The rule is deterministic, so a cohort's key names every region it
   14| holds.
   15| """
   16| from __future__ import annotations
   17| 
   18| import pandas as pd
   19| 
   20| from .geo import NEAREST_REGION
   21| 
   22| GROUP_LABEL = {
   23|     'native_white': 'native-born white', 'foreign_white_naturalized': 'naturalized immigrant',
   24|     'foreign_white_alien': 'immigrant non-citizen', 'black': 'Black', 'other': 'American Indian and Asian',
   25| }
   26| SEX_LABEL = {'M': 'men', 'F': 'women'}
   27| 
   28| 
   29| def build(cells: pd.DataFrame, cap: int = 40, min_share: float = 0.004, year: int = 1920) -> tuple[dict, dict]:
   30|     """Returns ({cohort key: cohort}, {cell index: cohort key}). year picks the era's group labels
   31|     (agentlayer.groups_for); 1868–1968 use GROUP_LABEL."""
   32|     labels, upper = GROUP_LABEL, str.capitalize
   33|     if not 1868 <= year < 1972:
   34|         from .agentlayer import groups_for
   35|         labels, upper = groups_for(year)['labels'], lambda x: x[0].upper() + x[1:]
   36|     total = cells.adults20.sum()
   37|     groups = {}
   38|     for i, r in cells.iterrows():
   39|         k = (r.region, r.sex, r.group)
   40|         groups.setdefault(k, []).append(i)
   41|     members = {k: set([k[0]]) for k in groups}
   42| 
   43|     def size(k):
   44|         return cells.loc[groups[k], 'adults20'].sum()
   45| 
   46|     while True:
   47|         # A national cohort can't merge further, so it's never picked.
   48|         keys = [k for k in sorted(groups, key=size) if k[0] != 'national']
   49|         small = [k for k in keys if size(k) < min_share * total]
   50|         if (len(groups) <= cap and not small) or not keys:
   51|             break
   52|         k = small[0] if small else keys[0]
   53|         region, sex, group = k
   54|         target = next(((r, sex, group) for r in NEAREST_REGION.get(region, []) if (r, sex, group) in groups and (r, sex, group) != k), None)
   55|         if target is None:
   56|             target = ('national', sex, group)
   57|             groups.setdefault(target, [])
   58|             members.setdefault(target, set())
   59|         groups[target] += groups.pop(k)
   60|         members[target] |= members.pop(k)
   61| 
   62|     cohorts, cell_to = {}, {}
   63|     for k, idx in groups.items():
   64|         regions = '+'.join(sorted(members[k]))
   65|         key = f'{regions}:{k[1]}:{k[2]}'
   66|         sub = cells.loc[idx]
   67|         by_state = sub.groupby('state').adults20.sum().to_dict()
   68|         cohorts[key] = {
   69|             'key': key, 'region': k[0] if len(members[k]) == 1 else 'mixed', 'regions': sorted(members[k]),
   70|             'sex': k[1], 'group': k[2], 'adults': float(sub.adults20.sum()),
   71|             'adults_by_state': by_state,
   72|             'label': f'{upper(labels[k[2]])} {SEX_LABEL[k[1]]}, {regions.replace("+", ", ")}',
   73|         }
   74|         for i in idx:
   75|             cell_to[i] = key
   76|     return cohorts, cell_to
```

## `simharness/config.py`

```python
    1| """Run configuration: everything that determines a run, hashed into its id.
    2| 
    3| A run is re-hashed by (election, what-ifs, seed, models, prompt version, draw
    4| counts, agent counts, data manifest). Two runs with the same hash must produce
    5| the same numbers; the run directory is named by it.
    6| """
    7| from __future__ import annotations
    8| 
    9| import hashlib
   10| import json
   11| import os
   12| from dataclasses import asdict, dataclass, field
   13| from pathlib import Path
   14| 
   15| HERE = Path(__file__).resolve().parent
   16| # The repo root: configs/, profiles/, whatifs/, extracts/, runs/, sessions/ and serve/bundles/
   17| # all sit next to the simharness package.
   18| ROOT = HERE.parent
   19| RUNS = ROOT / 'runs'
   20| 
   21| # Raw downloads live outside the web repo: some carry terms that forbid
   22| # redistribution, and the UI agent's dev server shouldn't watch them.
   23| CACHE = Path(os.environ.get(
   24|     'SIMHARNESS_CACHE',
   25|     str(Path.home() / 'research_notes/historical_election_sim_data/harness_cache'),
   26| ))
   27| 
   28| 
   29| @dataclass
   30| class AgentConfig:
   31|     bulk_model: str = 'claude-sonnet-5-5'
   32|     check_model: str = 'claude-opus-5-5'
   33|     check_share: float = 0.2          # share of agents also asked on check_model
   34|     per_cohort: int = 6               # agents per agent cohort
   35|     paraphrases: int = 3              # control and counterfactual paraphrases
   36|     effort: str = 'low'               # output_config.effort for the voice layer
   37|     backend: str = 'anthropic'        # anthropic | anthropic-batch | transcript
   38|     max_cohorts: int = 40             # cost cap; the merge rule folds the smallest
   39|     arms: list | None = None          # subset of control, cf, swap, probe; None sends all
   40|     only_cohorts: list | None = None  # cohort keys to interview; None interviews all
   41|     max_tokens: int = 4000            # per-request output ceiling (also the estimate's worst case)
   42|     # Compiled what-ifs only; the defaults leave hand-written what-ifs' runs as they were (D33):
   43|     replace_barred: bool = False      # someone who can't vote in either world takes no interview slot
   44|     focus_cohorts: int = 0            # extra cohorts the staging pass names as the change's decisive groups
   45|     escalate_model: str | None = None  # re-ask, on this model, anyone whose answer didn't take the change as true
   46|     escalate_max: int = 24            # cap on escalated requests per run
   47|     fast: bool = False                # fast mode for this layer's Opus requests (escalations); 2x price
   48| 
   49| 
   50| @dataclass
   51| class ResearchConfig:
   52|     """The once-per-what-if calls behind a typed what-if: compile → research → extract → stage
   53|     (scenario.py, evidence.py, world.py), and the audit of the interviews' reasoning. They run
   54|     once per change, not once per voter, so they can afford the strongest model and effort (D33)."""
   55|     compile_model: str = 'claude-sonnet-5-5'
   56|     research_model: str = 'claude-sonnet-5-5'
   57|     extract_model: str = 'claude-sonnet-5-5'  # Haiku judged every analogue unreliable and extracted none (D15)
   58|     world_model: str | None = None     # the staging pass (world.py); None skips it
   59|     audit_model: str | None = None     # the reasoning audit (world.py); None skips it
   60|     compile_effort: str = 'low'
   61|     research_effort: str = 'low'
   62|     extract_effort: str = 'low'
   63|     world_effort: str = 'high'
   64|     audit_effort: str = 'medium'
   65|     pass_max_tokens: int = 3000        # compile/stage/audit output ceiling; Opus thinking counts toward it
   66|     fast: bool = False                 # fast mode for the Opus passes (compile, extract, stage, audit); 2x price
   67|     max_searches: int = 4              # web_search max_uses per research call
   68|     research_max_tokens: int = 4000
   69| 
   70| 
   71| @dataclass
   72| class RunConfig:
   73|     election: int = 1920
   74|     election_day: str = '1920-11-02'
   75|     context_cutoff: str = '1920-11-01'  # last admissible source date
   76|     mode: str = 'truth'                 # truth | strict
   77|     what_ifs: list = field(default_factory=lambda: ['no-19th', 'fifteenth', 'league'])
   78|     seed: int = 1920
   79|     draws: int = 400
   80|     prompt_version: str = 'p1'
   81|     holdout: list = field(default_factory=lambda: 'CA FL ID IN LA MI MO MT NC NY OH OK'.split())
   82|     agents: AgentConfig = field(default_factory=AgentConfig)
   83|     research: ResearchConfig = field(default_factory=ResearchConfig)
   84|     max_combo: int = 3                  # largest what-if combination published (2^n grows fast)
   85| 
   86|     @classmethod
   87|     def load(cls, path: str | Path) -> 'RunConfig':
   88|         raw = json.loads(Path(path).read_text())
   89|         # Spending caps were removed; older configs that still carry them load as before.
   90|         agents = AgentConfig(**{k: v for k, v in raw.pop('agents', {}).items() if k not in ('max_requests', 'max_dollars')})
   91|         research = ResearchConfig(**{k: v for k, v in raw.pop('research', {}).items() if k != 'whatif_dollars'})
   92|         return cls(**raw, agents=agents, research=research)
   93| 
   94|     def to_dict(self) -> dict:
   95|         return asdict(self)
   96| 
   97|     def run_id(self, data_manifest: dict | None = None) -> str:
   98|         # G1: the code is part of the instrument, so a changed prompt or module gets a new run folder.
   99|         code = hashlib.sha256(b''.join(p.read_bytes() for p in sorted(HERE.glob('*.py')))).hexdigest()
  100|         blob = json.dumps({'config': self.to_dict(), 'data': data_manifest or {}, 'code': code}, sort_keys=True)
  101|         return f'{self.election}-{hashlib.sha256(blob.encode()).hexdigest()[:10]}'
```

## `simharness/data.py`

```python
    1| """Loaders for the harness cache. Benchmarks are not loaded here (see
    2| benchmarks.py): the fitting code never imports them.
    3| 
    4| Files (all under config.CACHE; provenance in each folder's PROVENANCE-*.md):
    5|   labels/state_pres_1916_1920_1924.csv     certified returns (labels)
    6|   population/adults_1920_by_state.csv      1920 census, 21+, sex × race/nativity/citizenship
    7|   population/adults_1910_by_state.csv      the same for 1910 (1916 interpolation)
    8|   population/urban_rural_1920_by_state.csv urban share (persona diversity)
    9|   franchise/state_franchise_1920.csv       poll tax, literacy test, alien voting
   10|   franchise/women_suffrage_pre19th.csv     women's presidential suffrage before the 19th
   11|   sources/corpus_1920.jsonl                dated Chronicling America items
   12|   context/platforms_1920.json              verified platform planks
   13| 
   14| General years (every election 1789–2024 except 1916/1920/1924, which keep the
   15| files above and load exactly as before):
   16|   labels/state_pres_all.csv                1868–2024 returns (scripts/build_returns.py)
   17|   labels/state_pres_1789_1864.csv          1789–1864 returns (same columns)
   18|   population/adults_<census>_by_state_nhgis.csv    21+ by census
   19|   population/adults18_<census>_by_state_nhgis.csv  18+ (1950 on)
   20|   franchise/state_franchise_all.csv        1868–1968 (scripts/build_franchise.py)
   21|   franchise/state_franchise_1789_1864.csv, franchise/state_franchise_1972_2024.csv
   22| """
   23| from __future__ import annotations
   24| 
   25| import hashlib
   26| import json
   27| import re
   28| 
   29| import numpy as np
   30| import pandas as pd
   31| 
   32| from .backbone import Inputs
   33| from .config import CACHE
   34| from .geo import ALL_STATES, CODE_OF, STATES_1920
   35| 
   36| LEGACY = (1916, 1920, 1924)
   37| 
   38| GROUP_MAP = {
   39|     'native_white': 'native_white',
   40|     'native_white_native_parentage': 'native_white',
   41|     'native_white_foreign_parentage': 'native_white',
   42|     'native_white_foreign_or_mixed_parentage': 'native_white',
   43|     'native_white_mixed_parentage': 'native_white',
   44|     'foreign_white_naturalized': 'foreign_white_naturalized',
   45|     'foreign_white_first_papers': 'foreign_white_alien',
   46|     'foreign_white_alien': 'foreign_white_alien',
   47|     'foreign_white_unknown': 'foreign_white_unknown',
   48|     'negro': 'black',
   49|     'black': 'black',
   50|     'other_races': 'other',
   51|     'other': 'other',
   52|     # 1910 women: citizenship wasn't asked of women in 1910.
   53|     'foreign_white_citizenship_not_tabulated': 'foreign_white_unknown',
   54|     # Modern (ACS / decennial 1980 on).
   55|     'white_nh_native': 'native_white',
   56|     'naturalized': 'foreign_white_naturalized',
   57|     'noncitizen': 'foreign_white_alien',
   58|     'black_nh_native': 'black',
   59|     'other_native': 'other',
   60|     # Early republic (1790–1860).
   61|     'white': 'native_white',
   62|     'free_colored': 'black',
   63|     'enslaved': 'black',
   64| }
   65| 
   66| 
   67| def manifest(paths: list) -> dict:
   68|     out = {}
   69|     for p in paths:
   70|         f = CACHE / p
   71|         if f.exists():
   72|             out[p] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
   73|     return out
   74| 
   75| 
   76| def _returns_legacy(year: int = 1920) -> pd.DataFrame:
   77|     d = pd.read_csv(CACHE / 'labels/state_pres_1916_1920_1924.csv')
   78|     out = {}
   79|     for y in (1916, 1920, 1924):
   80|         x = d[d.year == y].set_index('state')
   81|         out[f'R{y % 100}'] = x.rep
   82|         out[f'D{y % 100}'] = x.dem
   83|         out[f'O{y % 100}'] = x.total - x.rep - x.dem
   84|         out[f'T{y % 100}'] = x.total
   85|         if y == 1924:
   86|             out['P24'] = x.wp_progressive.fillna(0)  # La Follette's own votes within `other` (Wikipedia per-party column)
   87|     r = pd.DataFrame(out).loc[STATES_1920].astype(float)
   88|     x = d[d.year == year].set_index('state').loc[STATES_1920]
   89|     # 1920: NARA's count; 1924: Algara–Amlani's electoral votes by party (same 1910 apportionment).
   90|     ev = (x.nara_ev_total if year == 1920 else x.aa_state_ev_dem + x.aa_state_ev_rep + x.aa_state_ev_other).astype(int)
   91|     assert int(ev.sum()) == 531
   92|     return r, ev
   93| 
   94| 
   95| def _long_pop(path) -> pd.DataFrame:
   96|     p = pd.read_csv(path)
   97|     p = p[p.state.isin(STATES_1920) & (p.group != 'TOTAL')].copy()
   98|     p['group'] = p.group.map(lambda g: GROUP_MAP.get(g, g))
   99|     return p.groupby(['state', 'sex', 'group'], as_index=False)['count'].sum()
  100| 
  101| 
  102| def _population_legacy(year: int = 1920) -> pd.DataFrame:
  103|     """Cells state × sex × group with adults20 and adults16 (1916 by geometric
  104|     interpolation between the 1910 and 1920 counts, truth mode). adults20 holds
  105|     the election year's adults (the name is 1920's): for 1924, the 1920 count
  106|     aged along the cell's 1910→1920 trend to November 1924 [I] (DISCLOSURES C13)."""
  107|     p20 = _long_pop(CACHE / 'population/adults_1920_by_state.csv')
  108|     f10 = CACHE / 'population/adults_1910_by_state.csv'
  109|     p10 = _long_pop(f10) if f10.exists() else None
  110|     # Unknown citizenship: split between naturalized and alien in the state-sex ratio.
  111|     def resolve(p):
  112|         """Unknown citizenship → naturalized/alien in the state-sex ratio; where a
  113|         sex has no split at all (1910 women), the same state's men's ratio [I]:
  114|         before 1922 a wife's citizenship followed her husband's."""
  115|         rows = []
  116|         split = {}
  117|         for (s, x), g in p.groupby(['state', 'sex']):
  118|             d = dict(zip(g.group, g['count']))
  119|             nat, ali = d.get('foreign_white_naturalized', 0.0), d.get('foreign_white_alien', 0.0)
  120|             if nat + ali > 0:
  121|                 split[s] = nat / (nat + ali)
  122|         for (s, x), g in p.groupby(['state', 'sex']):
  123|             d = dict(zip(g.group, g['count']))
  124|             unk = d.pop('foreign_white_unknown', 0.0)
  125|             nat, ali = d.get('foreign_white_naturalized', 0.0), d.get('foreign_white_alien', 0.0)
  126|             share = nat / (nat + ali) if nat + ali > 0 else split.get(s, 0.5)
  127|             if unk:
  128|                 d['foreign_white_naturalized'] = nat + unk * share
  129|                 d['foreign_white_alien'] = ali + unk * (1 - share)
  130|             for k, v in d.items():
  131|                 rows.append({'state': s, 'sex': x, 'group': k, 'count': v})
  132|         return pd.DataFrame(rows)
  133|     p20 = resolve(p20)
  134|     cells = p20.rename(columns={'count': 'adults20'})
  135|     if p10 is not None:
  136|         p10 = resolve(p10).rename(columns={'count': 'adults10'})
  137|         cells = cells.merge(p10, on=['state', 'sex', 'group'], how='left')
  138|         # Census days: 15 Apr 1910 and 1 Jan 1920 (9.71 years apart). Election
  139|         # days: 7 Nov 1916 (6.56 years after the 1910 count) and 2 Nov 1920
  140|         # (0.84 years after the 1920 count).
  141|         ratio = (cells.adults20 / cells.adults10).where(cells.adults10 > 0)
  142|         cells['adults16'] = np.where(ratio.notna(), cells.adults10 * ratio ** (6.56 / 9.71), cells.adults20 * 0.94)
  143|         # Election day, in years after the 1 Jan 1920 count: 0.84 for 1920, 4.84 for 1924.
  144|         after = 0.84 + (year - 1920)
  145|         cells['adults20'] = np.where(ratio.notna(), cells.adults20 * ratio.clip(0.5, 2.0) ** (after / 9.71), cells.adults20)
  146|         cells['interp'] = np.where(ratio.notna(), 'geometric 1910→1920, extrapolated to Nov 1920', 'fallback')
  147|     else:
  148|         cells['adults16'] = cells.adults20 * 0.94
  149|         cells['interp'] = 'fallback: 1920 × 0.94 [I]'
  150|     return cells.sort_values(['state', 'sex', 'group']).reset_index(drop=True)
  151| 
  152| 
  153| def _franchise_legacy(year: int = 1920) -> dict:
  154|     f = pd.read_csv(CACHE / 'franchise/state_franchise_1920.csv')
  155|     f = f[f.state.isin(STATES_1920)].set_index('state')
  156|     if year != 1920:
  157|         # The year's poll tax and literacy test from Gray & Jenkins (presidential rows).
  158|         gj = pd.read_csv(CACHE / 'franchise/grayjenkins_state_franchise_1916_1920_1924.csv')
  159|         gj = gj[(gj.year == year) & gj.state.isin(STATES_1920)].set_index('state')
  160|         f['poll_tax'] = gj.poll_tax.reindex(f.index).fillna(f.poll_tax)
  161|         f['literacy_test'] = gj.lit_test.reindex(f.index).fillna(f.literacy_test)
  162|     w = pd.read_csv(CACHE / 'franchise/women_suffrage_pre19th.csv').set_index('state')
  163|     pres = w.presidential_suffrage_year.combine_first(w.full_suffrage_year) if 'full_suffrage_year' in w else w.presidential_suffrage_year
  164|     women16 = {s for s, y in pres.items() if pd.notna(y) and float(y) <= 1916}
  165|     women_pre19 = {s for s, y in pres.items() if pd.notna(y) and float(y) <= 1920}
  166|     alien = set(f.index[f.get('alien_declarant_voting', pd.Series(0, index=f.index)).fillna(0).astype(int) == 1])
  167|     # Georgia and Mississippi: registration closed before women could enrol
  168|     # (sources in franchise/state_franchise_1920.csv, women_nov1920_note).
  169|     closed = set(f.index[f.women_able_to_vote_nov1920.fillna(1).astype(int) == 0]) if year == 1920 else set()
  170|     return {'table': f, 'women16': women16, 'women_pre19': women_pre19, 'alien_voting': alien,
  171|             'closed_1920': closed, 'pres_year': pres.to_dict()}
  172| 
  173| 
  174| # ---------------------------------------------------------------- general years
  175| 
  176| RETURNS_FILES = ['labels/state_pres_1789_1864.csv', 'labels/state_pres_all.csv']
  177| FRANCHISE_FILES = ['franchise/state_franchise_1789_1864.csv', 'franchise/state_franchise_all.csv',
  178|                    'franchise/state_franchise_1972_2024.csv']
  179| # Electoral votes counted by Congress, 1868–2024 (scripts/build_returns.py KNOWN_EV).
  180| KNOWN_EV = {1868: 294, 1872: 352, 1876: 369, 1880: 369, 1884: 401, 1888: 401, 1892: 444, 1896: 447, 1900: 447,
  181|             1904: 476, 1908: 483, 1960: 537, **{y: 531 for y in range(1912, 1960, 4)},
  182|             **{y: 538 for y in range(1964, 2025, 4)}}
  183| 
  184| 
  185| def _year_rows(files: list, year: int, what: str) -> pd.DataFrame:
  186|     frames = [pd.read_csv(CACHE / f) for f in files if (CACHE / f).exists()]
  187|     d = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=['year', 'state'])
  188|     x = d[d.year == year]
  189|     if x.empty:
  190|         missing = [f for f in files if not (CACHE / f).exists()]
  191|         raise FileNotFoundError(f'no {what} rows for {year}; missing file(s): {missing}' if missing else
  192|                                 f'no {what} rows for {year} in {files}')
  193|     return x.drop_duplicates('state', keep='last').set_index('state').sort_index()
  194| 
  195| 
  196| def _returns_rows(year: int) -> pd.DataFrame:
  197|     x = _year_rows(RETURNS_FILES, year, 'returns')
  198|     ev = x.ev_total.fillna(0)
  199|     return x[(x.chosen_by != 'none') | (ev > 0)]
  200| 
  201| 
  202| def states(year: int) -> list:
  203|     """States with a popular vote or electors that year."""
  204|     if year in LEGACY:
  205|         return list(STATES_1920)
  206|     return list(_returns_rows(year).index)
  207| 
  208| 
  209| def returns(year: int = 1920):
  210|     """(R/D/O/T/P{yy} by state, electoral votes by state). Legislature states carry 0 votes."""
  211|     if year in LEGACY:
  212|         return _returns_legacy(year)
  213|     x = _returns_rows(year)
  214|     yy = year % 100
  215|     v = x[['rep', 'dem', 'total', 'third']].astype(float).fillna(0.0)
  216|     r = pd.DataFrame({f'R{yy}': v.rep, f'D{yy}': v.dem, f'O{yy}': (v.total - v.rep - v.dem).clip(lower=0),
  217|                       f'T{yy}': v.total, f'P{yy}': v.third}).astype(float)
  218|     r.index.name = None
  219|     ev = x.ev_total.fillna(0).astype(int)
  220|     if year < 1868:
  221|         # Before 1868 count the electors who voted (1864 NV cast 2 of 3; 1820 MS 2 of 3).
  222|         ev = x[['ev_rep', 'ev_dem', 'ev_other']].fillna(0).sum(axis=1).astype(int)
  223|     ev.name = None
  224|     ev.index.name = None
  225|     if year in KNOWN_EV:
  226|         # 1789–1864 (agent G's file) can have electors who didn't vote, so the
  227|         # slot identity and the national total are checked from 1868 on.
  228|         slots = x[['ev_rep', 'ev_dem', 'ev_other']].fillna(0).sum(axis=1).astype(int)
  229|         assert (slots == ev).all(), f'{year}: ev_total != ev_rep + ev_dem + ev_other in {list(ev.index[slots != ev])}'
  230|         assert int(ev.sum()) == KNOWN_EV[year], f'{year}: {int(ev.sum())} electoral votes, expected {KNOWN_EV[year]}'
  231|     return r, ev
  232| 
  233| 
  234| def _voting_age_rule(state: str, year: int) -> int:
  235|     if year >= 1972:
  236|         return 18
  237|     if (state == 'GA' and year >= 1944) or (state == 'KY' and year >= 1956):
  238|         return 18
  239|     if year >= 1960 and state in ('AK', 'HI'):
  240|         return {'AK': 19, 'HI': 20}[state]
  241|     return 21
  242| 
  243| 
  244| def _election_day(year: int) -> pd.Timestamp:
  245|     """First Tuesday after the first Monday in November (1848 on); 1 Nov before [I]."""
  246|     if year < 1848:
  247|         return pd.Timestamp(year, 11, 1)
  248|     d = pd.Timestamp(year, 11, 2)
  249|     return d + pd.Timedelta(days=(1 - d.weekday()) % 7)
  250| 
  251| 
  252| def _census_day(c: int) -> pd.Timestamp:
  253|     if c % 10:
  254|         return pd.Timestamp(c, 7, 1)  # ACS year: mid-year estimate [I]
  255|     if c <= 1820:
  256|         return pd.Timestamp(c, 8, 2)  # first Monday in August (1790–1820)
  257|     if c <= 1900:
  258|         return pd.Timestamp(c, 6, 1)
  259|     return {1910: pd.Timestamp(1910, 4, 15), 1920: pd.Timestamp(1920, 1, 1)}.get(c, pd.Timestamp(c, 4, 1))
  260| 
  261| 
  262| def _pop_path(c: int, age: int):
  263|     """The census file for year c and age floor (21 or 18), or None."""
  264|     names = [f'population/adults18_{c}_by_state_nhgis.csv'] if age == 18 else \
  265|         ([f'population/adults_{c}_by_state.csv'] if c in (1910, 1920) else []) + [f'population/adults_{c}_by_state_nhgis.csv']
  266|     for n in names:
  267|         if (CACHE / n).exists():
  268|             return n
  269|     return None
  270| 
  271| 
  272| def _census_years(age: int) -> list:
  273|     """Decennial censuses 1790–2020 plus any ACS years with a file."""
  274|     import glob
  275|     pat = 'adults18_*_by_state_nhgis.csv' if age == 18 else 'adults_*_by_state_nhgis.csv'
  276|     found = {int(m.group(1)) for f in glob.glob(str(CACHE / 'population' / pat))
  277|              if (m := re.search(r'_(\d{4})_by_state', f))}
  278|     return sorted(set(range(1790, 2021, 10)) | found)
  279| 
  280| 
  281| def _resolve(p: pd.DataFrame) -> pd.DataFrame:
  282|     """Unknown citizenship → naturalized/alien in the state-sex ratio; else the same
  283|     state's other sex; else 0.5 [I] (1850–1860, before citizenship was asked)."""
  284|     rows, split = [], {}
  285|     for (s, x), g in p.groupby(['state', 'sex']):
  286|         d = dict(zip(g.group, g['count']))
  287|         nat, ali = d.get('foreign_white_naturalized', 0.0), d.get('foreign_white_alien', 0.0)
  288|         if nat + ali > 0:
  289|             split[s] = nat / (nat + ali)
  290|     for (s, x), g in p.groupby(['state', 'sex']):
  291|         d = dict(zip(g.group, g['count']))
  292|         unk = d.pop('foreign_white_unknown', 0.0)
  293|         nat, ali = d.get('foreign_white_naturalized', 0.0), d.get('foreign_white_alien', 0.0)
  294|         share = nat / (nat + ali) if nat + ali > 0 else split.get(s, 0.5)
  295|         if unk:
  296|             d['foreign_white_naturalized'] = nat + unk * share
  297|             d['foreign_white_alien'] = ali + unk * (1 - share)
  298|         for k, v in d.items():
  299|             rows.append({'state': s, 'sex': x, 'group': k, 'count': v})
  300|     return pd.DataFrame(rows)
  301| 
  302| 
  303| _POP_CACHE: dict = {}
  304| 
  305| 
  306| def _census(c: int, age: int) -> pd.Series:
  307|     """Resolved counts by (state, sex, group) for census c, age floor 21 or 18."""
  308|     key = (c, age)
  309|     if key not in _POP_CACHE:
  310|         rel = _pop_path(c, age)
  311|         if rel is None:
  312|             raise FileNotFoundError(f'population file missing: population/adults{"18" if age == 18 else ""}_{c}_by_state_nhgis.csv')
  313|         p = pd.read_csv(CACHE / rel)
  314|         p = p[p.state.isin(ALL_STATES) & (p.group != 'TOTAL')].copy()
  315|         p['group'] = p.group.map(lambda g: GROUP_MAP.get(g, g))
  316|         p = p.groupby(['state', 'sex', 'group'], as_index=False)['count'].sum()
  317|         _POP_CACHE[key] = (_resolve(p).groupby(['state', 'sex', 'group'])['count'].sum(), rel)
  318|     return _POP_CACHE[key][0]
  319| 
  320| 
  321| def _brackets(year: int, age: int) -> tuple[int, int]:
  322|     """The two censuses to interpolate (or extrapolate) from for election day."""
  323|     t = _election_day(year)
  324|     cs = [c for c in _census_years(age) if c % 10 == 0 or _pop_path(c, age)]
  325|     before = [c for c in cs if _census_day(c) <= t]
  326|     after = [c for c in cs if _census_day(c) > t]
  327|     if before and after:
  328|         return before[-1], after[0]
  329|     if before:  # after the last census: the last two (an ACS year counts)
  330|         have = [c for c in before if _pop_path(c, age)]
  331|         if before[-1] not in have:
  332|             raise FileNotFoundError(f'population file missing: {_missing(before[-1], age)}')
  333|         return have[-2], have[-1]
  334|     return after[0], after[1]  # before 1790
  335| 
  336| 
  337| def _missing(c, age):
  338|     return f'population/adults{"18" if age == 18 else ""}_{c}_by_state_nhgis.csv'
  339| 
  340| 
  341| def _interp(year: int, age: int) -> tuple[pd.Series, pd.Series, list]:
  342|     """Counts at election day by (state, sex, group): geometric between the two
  343|     bracketing censuses; beyond them, the decade's trend with the ratio capped to
  344|     [0.5, 2] [I]. A cell missing from one census carries the other's count [I]."""
  345|     c0, c1 = _brackets(year, age)
  346|     a, b = _census(c0, age), _census(c1, age)
  347|     t, t0, t1 = _election_day(year), _census_day(c0), _census_day(c1)
  348|     f = (t - t0).days / (t1 - t0).days
  349|     idx = a.index.union(b.index)
  350|     a, b = a.reindex(idx), b.reindex(idx)
  351|     ratio = (b / a).where((a > 0) & (b > 0))
  352|     inside = 0 <= f <= 1
  353|     rr = ratio if inside else ratio.clip(0.5, 2.0)
  354|     geo = a * rr ** f
  355|     lin = a.fillna(0) + (b.fillna(0) - a.fillna(0)) * f
  356|     first, second = (b, a) if f >= 0.5 else (a, b)
  357|     near = first.fillna(second)
  358|     out = geo.where(ratio.notna(), lin.where(a.notna() & b.notna(), near)).clip(lower=0)
  359|     how = pd.Series(np.where(ratio.notna(), f'geometric {c0}→{c1}' + ('' if inside else ', extrapolated'),
  360|                              np.where(a.notna() & b.notna(), f'linear {c0}→{c1} [I]', f'fallback: one census of {c0}/{c1} [I]')),
  361|                     index=idx)
  362|     return out, how, [_POP_CACHE[(c0, age)][1], _POP_CACHE[(c1, age)][1]]
  363| 
  364| 
  365| def _ages(year: int, sts: list) -> dict:
  366|     try:
  367|         fr = _year_rows(FRANCHISE_FILES, year, 'franchise')
  368|         va = fr.voting_age.reindex(sts)
  369|     except (FileNotFoundError, AttributeError):
  370|         va = pd.Series(np.nan, index=sts)
  371|     return {s: int(va[s]) if pd.notna(va.get(s)) else _voting_age_rule(s, year) for s in sts}
  372| 
  373| 
  374| def _pop_general(year: int) -> tuple[pd.DataFrame, list]:
  375|     sts = states(year)
  376|     ages = _ages(year, sts)
  377|     need21 = any(a > 18 for a in ages.values())
  378|     need18 = any(a < 21 for a in ages.values())
  379|     files = []
  380|     p21 = p18 = None
  381|     if need21:
  382|         p21, h21, f = _interp(year, 21)
  383|         files += f
  384|     if need18:
  385|         try:
  386|             p18, h18, f = _interp(year, 18)
  387|             files += f
  388|         except FileNotFoundError:
  389|             if year >= 1952 or p21 is None:
  390|                 raise
  391|             # No 18+ census before 1950: 21+ × the 1950 18+/21+ ratio of the cell [I].
  392|             r50 = (_census(1950, 18) / _census(1950, 21)).replace([np.inf], np.nan)
  393|             p18 = p21 * r50.reindex(p21.index).fillna(1.065)
  394|             h18 = h21 + ' × 1950 18+/21+ ratio [I]'
  395|             files += [_POP_CACHE[(1950, 18)][1], _POP_CACHE[(1950, 21)][1]]
  396|     rows = []
  397|     for s in sts:
  398|         a = ages[s]
  399|         if a >= 21:
  400|             n, h = p21, h21
  401|         elif a == 18:
  402|             n, h = p18, h18
  403|         else:  # 19, 20: linear between the 18+ and 21+ counts [I]
  404|             n = p21 + (p18.reindex(p21.index) - p21) * (21 - a) / 3
  405|             h = h21 + f' / {a}+ linear between 18+ and 21+ [I]'
  406|         if s not in n.index.get_level_values(0):
  407|             raise FileNotFoundError(f'{year}: no census cells for {s} in {sorted(set(files))}')
  408|         x = n.loc[s]
  409|         hh = h.loc[s]
  410|         for (sex, g), v in x.items():
  411|             rows.append({'state': s, 'sex': sex, 'group': g, 'adults20': float(v), 'interp': hh.loc[(sex, g)]})
  412|     cells = pd.DataFrame(rows)
  413|     cells['adults16'] = cells.adults20
  414|     cells = cells[['state', 'sex', 'group', 'adults20', 'adults16', 'interp']]
  415|     return cells.sort_values(['state', 'sex', 'group']).reset_index(drop=True), sorted(set(files))
  416| 
  417| 
  418| def population(year: int = 1920) -> pd.DataFrame:
  419|     """Cells state × sex × group. adults20 = adults at the election (the name is
  420|     1920's); adults16 = adults20 for general years."""
  421|     if year in LEGACY:
  422|         return _population_legacy(year)
  423|     return _pop_general(year)[0]
  424| 
  425| 
  426| def _other_citizen(year: int, sts: list) -> dict:
  427|     """Citizen (legally voting) share of 'other' adults, mostly American Indians [I]:
  428|     before the 1887 Dawes Act few were citizens; by 1924 about two-thirds were;
  429|     the 1924 Indian Citizenship Act made all citizens, but AZ and NM barred
  430|     reservation Indians until 1948. 1916/1920/1924 keep the legacy (none)."""
  431|     if year < 1888:
  432|         v = 0.2
  433|     elif year < 1924:
  434|         v = 0.6
  435|     else:
  436|         v = 1.0
  437|     out = {s: v for s in sts} if v < 1 else {}
  438|     if 1924 <= year < 1948:
  439|         out.update({s: 0.2 for s in ('AZ', 'NM') if s in sts})
  440|     return out
  441| 
  442| 
  443| def franchise(year: int = 1920) -> dict:
  444|     if year in LEGACY:
  445|         return _franchise_legacy(year)
  446|     sts = states(year)
  447|     try:
  448|         f = _year_rows(FRANCHISE_FILES, year, 'franchise')
  449|         fallback = False
  450|     except FileNotFoundError:
  451|         if year < 1972:
  452|             raise
  453|         # Modern rules are uniform enough to default [I]: all adults 18+, no tests.
  454|         f = pd.DataFrame({'poll_tax': 0, 'literacy_test': 0, 'alien_voting': 0, 'women_vote': 1, 'white_can': 1.0,
  455|                           'black_can': 1.0, 'felony_disenfranchised_share': np.nan, 'voting_age': 18,
  456|                           'chosen_by': 'popular', 'source': 'default [I]', 'note': ''}, index=pd.Index(sts, name='state'))
  457|         fallback = True
  458|     f = f.reindex(sts)
  459|     w = pd.read_csv(CACHE / 'franchise/women_suffrage_pre19th.csv').set_index('state')
  460|     pres = w.presidential_suffrage_year.combine_first(w.full_suffrage_year) if 'full_suffrage_year' in w else w.presidential_suffrage_year
  461|     women16 = {s for s, y in pres.items() if pd.notna(y) and float(y) <= 1916}
  462|     women_pre19 = {s for s, y in pres.items() if pd.notna(y) and float(y) <= 1920}
  463| 
  464|     def flag(col):
  465|         return set(f.index[f[col].fillna(0).astype(float) == 1]) if col in f else set()
  466|     rows = _returns_rows(year)
  467|     slots = rows[['ev_rep', 'ev_dem', 'ev_other']].fillna(0).astype(int)
  468|     leg = rows.chosen_by == 'legislature'
  469|     # Electors by party where the legislature chose them, and where a popular-vote
  470|     # state divided them (district plans, split slates, faithless electors).
  471|     # A popular-vote state with no surviving count (KY 1792, PA 1812…) keeps its history's electors too.
  472|     novote = rows.total.fillna(0) <= 0
  473|     ev_fixed = {s: tuple(int(v) for v in slots.loc[s]) for s in rows.index[leg | novote] if slots.loc[s].sum() > 0}
  474|     # A divided state, or one whose electors went against the recorded plurality (before
  475|     # 1824 voters often chose slates, not candidates: MA 1820's "other" slate voted Monroe),
  476|     # keeps the historical division while the recorded plurality winner holds.
  477|     v = rows[['rep', 'dem']].fillna(0).astype(float)
  478|     oth, thr = rows.other.fillna(0).astype(float), rows.third.fillna(0).astype(float).clip(upper=rows.other.fillna(0))
  479|     vote_win = pd.concat([v.rep, v.dem, pd.concat([thr, oth - thr], axis=1).max(axis=1)], axis=1).to_numpy().argmax(axis=1)
  480|     ev_split = {s: tuple(int(x) for x in slots.loc[s]) for i, s in enumerate(rows.index)
  481|                 if not leg.iloc[i] and not novote.iloc[i] and slots.loc[s].sum() > 0
  482|                 and ((slots.loc[s] > 0).sum() > 1 or int(slots.loc[s].to_numpy().argmax()) != int(vote_win[i]))}
  483|     felony = {}
  484|     if 'felony_disenfranchised_share' in f:
  485|         felony = {s: float(v) for s, v in f.felony_disenfranchised_share.items() if pd.notna(v)}
  486|     return {'table': f, 'women16': women16, 'women_pre19': women_pre19, 'alien_voting': flag('alien_voting'),
  487|             'closed_1920': set(), 'pres_year': pres.to_dict(), 'women_vote': flag('women_vote'),
  488|             'fallback': fallback, 'ev_fixed': ev_fixed, 'ev_split': ev_split, 'felony_share': felony,
  489|             'enslaved_share': _enslaved_share(year)}
  490| 
  491| 
  492| def _enslaved_share(year: int) -> dict:
  493|     """state → enslaved share of Black adults, from the last census before the
  494|     election (1790–1860); empty from 1868 on."""
  495|     if year >= 1866:
  496|         return {}
  497|     c = max([1790] + [c for c in range(1790, 1861, 10) if c <= year])
  498|     f = CACHE / f'population/adults_{c}_by_state_nhgis.csv'
  499|     if not f.exists():
  500|         return {}
  501|     p = pd.read_csv(f)
  502|     b = p[p.group.isin(['enslaved', 'free_colored'])].pivot_table(index='state', columns='group', values='count', aggfunc='sum').fillna(0)
  503|     if 'enslaved' not in b:
  504|         return {}
  505|     tot = b.sum(axis=1)
  506|     return {s: float(b.enslaved[s] / tot[s]) for s in b.index if tot[s] > 0}
  507| 
  508| 
  509| def urban_share() -> dict:
  510|     f = CACHE / 'population/urban_rural_1920_by_state.csv'
  511|     if not f.exists():
  512|         return {}
  513|     u = pd.read_csv(f)
  514|     u = u[(u.year == 1920) & u.state.isin(STATES_1920)].pivot_table(index='state', columns='area', values='count', aggfunc='sum')
  515|     return (u['urban'] / u['total']).to_dict()
  516| 
  517| 
  518| NAMES = re.compile(r'\b(Harding|Cox|Coolidge|Roosevelt|Debs|Christensen|Republican|Democrat|G\.\s?O\.\s?P|Wilson)', re.I)
  519| 
  520| 
  521| def corpus(cutoff: str, rel: str | None = 'sources/corpus_1920.jsonl', names=NAMES) -> list[dict]:
  522|     rows = []
  523|     path = CACHE / rel if rel else None
  524|     if not path or not path.exists():
  525|         return rows
  526|     for line in path.read_text().splitlines():
  527|         if not line.strip():
  528|             continue
  529|         it = json.loads(line)
  530|         if it['date'] > cutoff:
  531|             continue
  532|         text = it['excerpt'].strip()
  533|         it['identifying'] = bool(it.get('mentions_candidates')) or bool(names.search(text))
  534|         it['text'] = ' '.join(text.split()[:120])
  535|         rows.append(it)
  536|     return rows
  537| 
  538| 
  539| def platforms(rel: str = 'context/platforms_1920.json') -> dict:
  540|     path = CACHE / rel
  541|     return json.loads(path.read_text()) if path.exists() else {}
  542| 
  543| 
  544| def inputs(year: int) -> tuple[Inputs, dict]:
  545|     ret, ev = returns(year)
  546|     cells = population(year)
  547|     fr = franchise(year)
  548|     if year in LEGACY:
  549|         return Inputs(cells=cells, returns=ret, women16=fr['women16'], women_pre19=fr['women_pre19'],
  550|                       closed_1920=fr['closed_1920'], alien_voting=fr['alien_voting'], ev=ev, year=year), fr
  551|     t = fr['table']
  552|     sts = list(ret.index)
  553| 
  554|     def can(col):
  555|         v = t[col].astype(float) if col in t else pd.Series(1.0, index=t.index)
  556|         return {s: float(x) for s, x in v.items() if pd.notna(x) and float(x) < 1}
  557|     no_pop = set(t.index[t.chosen_by == 'legislature']) if 'chosen_by' in t else set()
  558|     rows = _returns_rows(year)
  559|     no_pop |= set(rows.index[rows.chosen_by == 'legislature'])
  560|     return Inputs(cells=cells, returns=ret, women16=fr['women16'], women_pre19=fr['women_pre19'],
  561|                   closed_1920=set(), alien_voting=fr['alien_voting'], ev=ev,
  562|                   other_citizen=_other_citizen(year, sts), year=year, women_vote=fr['women_vote'],
  563|                   voting_age=18 if year >= 1972 else 21, black_can=can('black_can'), white_can=can('white_can'),
  564|                   no_popular=no_pop), fr
  565| 
  566| 
  567| def _files(year: int) -> list:
  568|     """Cache files a general year reads (for the manifest)."""
  569|     out = [RETURNS_FILES[0] if year < 1868 else RETURNS_FILES[1],
  570|            FRANCHISE_FILES[0] if year < 1868 else FRANCHISE_FILES[1] if year < 1972 else FRANCHISE_FILES[2]]
  571|     out = [f for f in out if (CACHE / f).exists()]
  572|     try:
  573|         out += _pop_general(year)[1]
  574|     except FileNotFoundError:
  575|         pass
  576|     return out + ['franchise/women_suffrage_pre19th.csv']
  577| 
  578| 
  579| def load(cfg) -> tuple[Inputs, dict]:
  580|     from . import profiles
  581|     prof = profiles.get(cfg.election)
  582|     inp, fr = inputs(cfg.election)
  583|     files = ['labels/state_pres_1916_1920_1924.csv', 'population/adults_1920_by_state.csv',
  584|              'population/adults_1910_by_state.csv', 'franchise/state_franchise_1920.csv',
  585|              'franchise/women_suffrage_pre19th.csv', 'sources/corpus_1920.jsonl', 'context/platforms_1920.json']
  586|     if cfg.election not in LEGACY:
  587|         files = _files(cfg.election) + [prof['platforms']] + ([prof['corpus']] if prof['corpus'] else [])
  588|     elif cfg.election != 1920:
  589|         files += ['franchise/grayjenkins_state_franchise_1916_1920_1924.csv', prof['platforms']] + ([prof['corpus']] if prof['corpus'] else [])
  590|         files.remove('sources/corpus_1920.jsonl')
  591|         files.remove('context/platforms_1920.json')
  592|     extras = {
  593|         'franchise': fr,
  594|         'urban': urban_share(),
  595|         'corpus': corpus(cfg.context_cutoff, prof['corpus'], profiles.names_re(cfg.election)),
  596|         'platforms': platforms(prof['platforms']),
  597|         'profile': prof,
  598|         # A carried-forward year fits its base year first (backbone.carry_forward).
  599|         'base_inp': inputs(prof['base'])[0] if prof['base'] else None,
  600|         'manifest': manifest(files),
  601|     }
  602|     return inp, extras
```

## `simharness/evaluate.py`

```python
    1| """Validation of the 1920 prototype (EVAL.md). Benchmarks are read only here.
    2| 
    3| Every check returns {id, name, value, threshold, pass, note}. `pass` is True,
    4| False, or None ("not run", with the reason in `note`).
    5| """
    6| from __future__ import annotations
    7| 
    8| import numpy as np
    9| 
   10| from .geo import SOUTH
   11| from .stats import bayes_ols, brier, expit, logit, rmse, spearman
   12| 
   13| 
   14| def check(id_, name, value, threshold, ok, note=''):
   15|     return {'id': id_, 'name': name, 'value': value, 'threshold': threshold, 'pass': ok, 'note': note}
   16| 
   17| 
   18| def r1_reproduction(fit, inp, state_votes) -> dict:
   19|     """state_votes [D, S, 3] from the unchanged world."""
   20|     states = fit.diagnostics['states']
   21|     cert = np.array(inp.returns.reindex(states)[['R20', 'D20', 'O20']].fillna(0), dtype=float)
   22|     cert[[st in (getattr(inp, 'no_popular', None) or ()) for st in states]] = 0.0
   23|     err = np.abs(state_votes - cert[None, :, :])
   24|     worst = float(err.max())
   25|     ev = inp.ev.reindex(states).fillna(0).to_numpy()
   26|     winners = state_votes.argmax(axis=2)
   27|     ev_r = (ev[None, :] * (winners == 0)).sum(axis=1)
   28|     ev_d = (ev[None, :] * (winners == 1)).sum(axis=1)
   29|     ok = worst <= 1.0 and bool(np.all(ev_r == 404)) and bool(np.all(ev_d == 127))
   30|     return check('R1', 'Unchanged rerun reproduces every state exactly', round(worst, 4),
   31|                  '≤ 1 vote per state and party in every draw; EV 404–127 in every draw', ok,
   32|                  f'EV R range {int(ev_r.min())}–{int(ev_r.max())}, D range {int(ev_d.min())}–{int(ev_d.max())}; {state_votes.shape[0]} draws')
   33| 
   34| 
   35| def holdout(fit, inp, holdout_states: list, draws: int, seed: int) -> dict:
   36|     """B1–B5: predict held-out states from training states only."""
   37|     rng = np.random.default_rng(seed + 7)
   38|     dg = fit.diagnostics
   39|     states = dg['states']
   40|     idx = {s: i for i, s in enumerate(states)}
   41|     H = [idx[s] for s in holdout_states]
   42|     Tr = [i for i in range(len(states)) if states[i] not in holdout_states]
   43|     ret = inp.returns.loc[states]
   44|     old = np.array([s in inp.women16 for s in states])
   45|     closed = np.array([s in inp.closed_1920 for s in states])
   46|     south = np.array([s in SOUTH for s in states])
   47|     E16, E20 = dg['E16'], dg['E20']
   48|     T16, T20 = dg['T16'], dg['T20']
   49|     M20, F20, m16 = dg['M20'], dg['F20'], dg['m16']
   50|     D = E16.shape[0]
   51| 
   52|     # κ from training old states only
   53|     tr_old = [i for i in Tr if old[i]]
   54|     k = logit(T20[None, tr_old] / E20[:, tr_old]) - logit(T16[None, tr_old] / E16[:, tr_old])
   55|     kap = k.mean(axis=1)[:, None] + rng.normal(0, 1, (D, len(states))) * k.std(axis=1, ddof=1)[:, None]
   56|     m20 = expit(logit(m16) + kap)
   57|     # ρ from training new non-Southern states
   58|     tr_new = [i for i in Tr if not old[i] and not south[i] and not closed[i]]
   59|     W = T20[None, tr_new] - m20[:, tr_new] * M20[:, tr_new]
   60|     rho = np.clip(W / np.maximum(F20[:, tr_new], 1) / m20[:, tr_new], 0.05, 1.5)
   61|     rho_d = rho[np.arange(D), rng.integers(0, len(tr_new), D)]
   62|     votes_hat = m20 * M20 + np.where(closed, 0, rho_d[:, None] * m20 * F20)
   63|     # Old states: 1916 votes already included women's, so project turnout per
   64|     # eligible adult by κ, as the backbone's T1 does. (Fixed after the first
   65|     # evaluation used men's-only m16 here; see EVAL.md, deviations.)
   66|     t_old = expit(logit(T16[None, :] / E16) + kap) * E20
   67|     votes_hat = np.where(old[None, :], t_old, votes_hat)
   68|     sidx = np.array([idx[s] for s in fit.cells.state])
   69|     A = np.zeros((D, len(states)))
   70|     np.add.at(A, (slice(None), sidx), fit.world.adults)
   71|     turn_hat = votes_hat / A
   72|     turn_act = T20[None, :] / A
   73|     # Persistence: 1916 votes ÷ 1916 adults
   74|     A16 = np.zeros(len(states))
   75|     np.add.at(A16, sidx, fit.cells.adults16.to_numpy())
   76|     turn_persist = T16 / A16
   77| 
   78|     # Two-party share: swing + women's tilt, fitted on training states
   79|     rd16 = logit((ret.R16 / (ret.R16 + ret.D16)).to_numpy())
   80|     rd20 = logit((ret.R20 / (ret.R20 + ret.D20)).to_numpy())
   81|     f_hat = np.where(~old & ~closed, 1 - (m20 * M20) / np.maximum(votes_hat, 1), 0.0)
   82|     pred = np.empty((D, len(H)))
   83|     for d in range(D):
   84|         f_tr = np.where(~old & ~closed, dg['votes_F'][d] / T20, 0.0)
   85|         X = np.column_stack([~south, south, f_tr]).astype(float)[Tr]
   86|         b, sig, _ = bayes_ols(X, (rd20 - rd16)[Tr], 1, rng)
   87|         Xh = np.column_stack([~south, south, f_hat[d]]).astype(float)[H]
   88|         pred[d] = rd16[H] + Xh @ b[0] + rng.normal(0, sig[0], len(H))
   89|     share_hat = expit(np.median(pred, axis=0)) * 100
   90|     actual = expit(rd20[H]) * 100
   91|     # Baselines
   92|     w = (ret.R20 + ret.D20).to_numpy()
   93|     persist = expit(rd16[H]) * 100
   94|     swing = np.average((rd20 - rd16)[Tr], weights=w[Tr])
   95|     uniform = expit(rd16[H] + swing) * 100
   96|     us_sd = float(np.std((rd20 - rd16)[Tr] - swing, ddof=1))
   97|     # Demographic regression (no lag)
   98|     comp = composition(fit, states)
   99|     Xd = np.column_stack([np.ones(len(states)), south, comp['black'], comp['foreign'], comp['new_women']])
  100|     bd, *_ = np.linalg.lstsq(Xd[Tr], rd20[Tr], rcond=None)
  101|     demo = expit(Xd[H] @ bd) * 100
  102| 
  103|     p_win = (pred > 0).mean(axis=0)
  104|     p_us = 1 - _norm_cdf(-(rd16[H] + swing) / us_sd)
  105|     won = (rd20[H] > 0).astype(float)
  106|     ev = inp.ev.loc[holdout_states].to_numpy()
  107|     ev_pred = float(np.sum(ev * (share_hat > 50)))
  108|     ev_act = float(np.sum(ev * won))
  109|     close = [s for s, a in zip(holdout_states, actual) if abs(a - 50) * 2 < 5]
  110|     ev_tol = float(min(inp.ev.loc[close])) if close else 0.0
  111| 
  112|     b1 = rmse(share_hat, actual)
  113|     b2 = rmse(np.median(turn_hat[:, H], axis=0) * 100, np.median(turn_act[:, H], axis=0) * 100)
  114|     b2p = rmse(turn_persist[H] * 100, np.median(turn_act[:, H], axis=0) * 100)
  115|     rows = [{'state': s, 'actual': round(float(a), 2), 'backbone': round(float(p), 2), 'persistence': round(float(q), 2),
  116|              'uniform_swing': round(float(u), 2), 'demographic': round(float(g), 2), 'p_R_win': round(float(pw), 3),
  117|              'turnout_actual': round(float(np.median(turn_act[:, i]) * 100), 1),
  118|              'turnout_backbone': round(float(np.median(turn_hat[:, i]) * 100), 1),
  119|              'turnout_persistence': round(float(turn_persist[i] * 100), 1)}
  120|             for s, a, p, q, u, g, pw, i in zip(holdout_states, actual, share_hat, persist, uniform, demo, p_win, H)]
  121|     checks = [
  122|         check('B1', 'Holdout two-party RMSE (points)', {'backbone': round(b1, 2), 'uniform_swing': round(rmse(uniform, actual), 2),
  123|               'persistence': round(rmse(persist, actual), 2), 'demographic': round(rmse(demo, actual), 2)},
  124|               'backbone ≤ uniform swing and ≤ persistence', b1 <= rmse(uniform, actual) and b1 <= rmse(persist, actual)),
  125|         check('B2', 'Holdout turnout RMSE (points of adults 21+)', {'backbone': round(b2, 2), 'persistence': round(b2p, 2)},
  126|               'backbone ≤ persistence', b2 <= b2p),
  127|         check('B3', 'Holdout Spearman ρ, two-party share', round(spearman(share_hat, actual), 3), '≥ 0.8',
  128|               spearman(share_hat, actual) >= 0.8),
  129|         check('B4', 'Holdout Brier score, state winner', {'backbone': round(brier(p_win, won), 4), 'uniform_swing': round(brier(p_us, won), 4)},
  130|               'backbone ≤ uniform swing', brier(p_win, won) <= brier(p_us, won)),
  131|         check('B5', 'Holdout electoral-vote error (Harding)', abs(ev_pred - ev_act), f'≤ {ev_tol:g}',
  132|               abs(ev_pred - ev_act) <= ev_tol, f'predicted {ev_pred:g}, actual {ev_act:g}; states decided by < 5 points: {close or "none"}'),
  133|     ]
  134|     return {'checks': checks, 'rows': rows}
  135| 
  136| 
  137| def _norm_cdf(x):
  138|     from scipy.stats import norm
  139|     return norm.cdf(x)
  140| 
  141| 
  142| def composition(fit, states) -> dict:
  143|     c = fit.cells
  144|     a = c.groupby('state').adults20.sum()
  145|     blk = c[c.group == 'black'].groupby('state').adults20.sum().reindex(states, fill_value=0) / a.reindex(states)
  146|     fb = c[c.group.str.startswith('foreign')].groupby('state').adults20.sum().reindex(states, fill_value=0) / a.reindex(states)
  147|     nw = c[(c.sex == 'F') & (c.group != 'foreign_white_alien')].groupby('state').adults20.sum().reindex(states, fill_value=0) / a.reindex(states)
  148|     old = fit.diagnostics['old_states']
  149|     nw = nw.where(~nw.index.isin(old), 0.0)
  150|     return {'black': blk.to_numpy(), 'foreign': fb.to_numpy(), 'new_women': nw.to_numpy()}
```

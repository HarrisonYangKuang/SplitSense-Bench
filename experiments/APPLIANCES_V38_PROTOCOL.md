# Appliances delayed-lag pilot v38 — prospective protocol

Status: FEASIBILITY_PILOT_ONLY. Written after v37 metadata, before fitting or viewing candidate losses. This is a bounded temporal ranking pilot, not formal Agent evaluation or a replication of the original energy paper. Existing user authorization covers free private CPU pilot work. No full run or GPU is requested.

## Evidence and gate

v37 established the source hash and continuous ordinal grid; see `evidence/appliances_v37_inventory.json`. Five complete fixed episodes are available from one house. The temporal-refit source screen identified a reason to distinguish selection from final training membership. Phenomenon and candidate ranking reliability are unknown; this pilot is their bounded test. Timestamp timezone and interval anchoring are unknown: exclude clock/calendar features. Novelty is NOT_ASSESSED; no novel-method claim is made. A positive result is only a reason to seek independent-source replication, never a final validity pass.

## Data and prediction event

Require CSV SHA-256 `2820bf712ad0275cb18b85a05250926100d8e65ebb9f4d2d016ca91ea152a25d`, 19,735 rows, all adjacent intervals 600 seconds, no duplicate times or nonfinite targets. Read from the pinned author URL in v37. Download cap 16 MiB; data and predictions stay cloud-side.

For ordinal target row j, features are target values at j minus [2,3,6,12,18,36,72,144,288,1008]. These are ten declared ordinal lags, with no learned feature selection. Each input is observed before j under a one-record reporting delay. Labels through j-2 are available, including delayed earlier deployment outcomes during rolling prediction; weights never update during an episode's deployment. This is an explicit archive replay assumption, not measured production latency. No same-row sensors, calendar, weather, or random columns.

Use exactly the five 21-day episodes recorded in v37. Each first 14 days is historical pool, last 7 days is deployment. At deployment start J, common refit targets stop at J-2: exclude the last historical target J-1. Lag history may precede the episode and remains available as covariates; it is not extra fitting-target data. No timestamp reordering or filling. All five episode coverage and lag-index checks precede the first fit.

## Internal selection

Forward validation uses the last 288 rows of the common pool. Its fitting set is earlier rows, excluding the single row immediately preceding that validation interval so all fitting labels are available at its first prediction. Random validation uses 288 rows selected by sorting the common pool's row indices on SHA-256 of `appliances-v38:<row_index>`; reserve the next hash-ranked row as the unused gap counterpart, and fit on the rest. Fit and validation counts therefore match across strategies. Keep fit indices chronologically sorted for deterministic estimators.

Random partitioning may place a validation target value in a later training row's lagged covariates. Record this overlap count explicitly. It is a property of this random-row comparator, not a claim that the comparator is a valid forward simulation. Forward fitting must have zero such overlap. Do not silently mask lag values after seeing results. Thus any observed difference is not attributed solely to distribution drift.

## Frozen candidate library and fitting

Candidate order: mean, delayed_persistence, seasonal_144, ridge_1, ridge_100, hist_boost, extra_trees. Ties choose the earlier name in this list.

- mean: mean of fitting targets.
- delayed_persistence: target j-2.
- seasonal_144: target j-144.
- ridge_1 / ridge_100: StandardScaler on fitting features then sklearn Ridge with alpha 1 / 100, all other defaults in the fixed version.
- hist_boost: HistGradientBoostingRegressor(max_iter=200,max_leaf_nodes=15,learning_rate=0.05,l2_regularization=1,early_stopping=False,random_state=3800+episode).
- extra_trees: ExtraTreesRegressor(n_estimators=200,min_samples_leaf=5,max_features=1.0,n_jobs=2,random_state=3800+episode).

No hyperparameter search, clipping, target transform or early stopping. Mean counts as a fit; the two direct lag baselines do not. Each episode fits five estimators on each of two internal splits and once on the common pool: 15 fits, at most 75 total. Retain internal models to score their unrefitted deployment predictions as the secondary arm. The common-pool candidate predictions are shared by both selection strategies. Do not double-fit identical final candidates.

## Frozen measurement and stop rule

Compute training-internal MSE for all seven candidates; lock both choices before any deployment loss is computed. MSE is mean squared target error, in Wh squared. The primary statistic per episode is D = rho_forward - rho_random, where each rho is Spearman correlation between seven internal validation losses and the seven common-refit deployment losses. Average ranks for exact ties; if either ranking is constant, report undefined and fail complete coverage rather than dropping the episode.

Screen passes only if all five episodes are valid, at least four have D > 0, and median D >= 0.20, preserving the prior temporal-ranking pilot criterion. This is a screening rule, not a significance test. Report all D values. Failure stops this version: no new seeds, changed lags, additional trees, replacement episodes or threshold revision to rescue it.

Secondary: normalized selection effect E = (MSE_random_choice - MSE_forward_choice)/V, with V the population variance of common-pool training targets; finite-library regret for each selected candidate; both selected losses under retained-subset final fitting; internal validation optimism gaps. V=0 invalidates the episode. These cannot rescue the primary gate. Five episodes are not independent houses; no row-bootstrap confidence interval or population prevalence claim. Positive pilot still needs independent-source confirmation and other validity evidence before Agent/Skill evaluation.

## Execution and evidence

Use the v37 pinned Kaggle image, Python 3.12.13, numpy 2.0.2, sklearn 1.6.1, threadpoolctl 3.6.0. Limit numeric libraries to two threads, hard program budget 300 seconds and platform timeout 600 seconds; cash cap 0, private CPU only, no automatic retry. Save source/environment hashes, actual indices and lag-overlap counts, choice-lock file, every validation and deployment prediction with targets, per-candidate losses, D/E, gate and failures. Cloud raw predictions may be compressed; local summary max 1 MiB. Independently recompute reported losses from saved predictions before accepting scientific output. Code and a small deterministic lag-index check must be inspected before dispatch; that check is engineering evidence only.

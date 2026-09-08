# Temporal split and final-training lag: transfer screen

2026-09-08. Profile: rapid-scan; targeted orientation, not a systematic review or novelty clearance. Searches: temporal model-selection validation benchmark; exact title of the paper below. OpenReview required browser verification; primary author repository and arXiv HTML were accessible. Canonical publication identity was checked in PMLR. No datasets, weights, or environments were downloaded.

Cai and Ye, [Understanding the Limits of Deep Tabular Methods with Temporal Shift, ICML 2025](https://proceedings.mlr.press/v267/cai25j.html), report benefits from random splitting and a revised temporal protocol. The inspected [arXiv v2, sections 4.1–4.4](https://arxiv.org/html/2502.20260v2) distinguishes training lag from validation bias. This later manuscript version is not assumed byte-identical to the conference PDF.

## Inspected source and bounded finding

Official [repository](https://github.com/LAMDA-Tabular/Tabular-Temporal-Shift), commit `adbffb0bde86c0722ce5eea6b8f4679e0ea119fb`:

- `model/lib/data.py:211–221`: original temporal training/validation partitions retained.
- `model/lib/data.py:224–246`: a foremost-validation option moves later observations into the training partition.
- `model/lib/data.py:491–504`: random mode repartitions the combined historical pool using saved indices.
- `train_model_classical.py:15–30`: passes selected partitions into the fitting method before test prediction.

These branches change training membership as well as validation membership. Terminal fitting behavior inside each estimator has not yet been traced; no assertion that every method omits full-history refitting is established here.

## Decision for SplitSense

Do not import the paper's performance differences as evidence of a pure validation-selection effect. Our inference is that a transfer experiment must separate model selection from the data used to fit the final predictor. Existing SplitSense runs refit candidates on a common historical pool, so their contrast is not automatically equivalent.

Next bounded step: trace a CPU-compatible estimator's final fitting and early-stopping path at the pinned commit, then specify a paired contrast with common final training data. Check prediction-time feature legitimacy independently; this paper does not resolve Cooking's anonymous-feature uncertainty. No new source, model run, validity pass, or Agent evaluation is authorized by this screen. Prior failed versions remain stopped.

## Terminal CatBoost path verified

At the same pinned commit, `model/classical_methods/catboost.py:45–61` constructs separate training and validation matrices, supplies validation as `eval_set`, and fits only the training matrix. Lines 69–70 persist that model. Lines 78–91 reload it and predict without a second fit. `train_model_classical.py:25–30` calls this fit/predict sequence. The default CatBoost configuration sets `early_stopping_rounds=50` and `n_estimators=2000`; runtime overrides may differ. The helper preprocessing implementation was not exhaustively audited, and this is static source inspection, not a replay of published scores.

Conclusion limited to this path: no final train-plus-validation refit occurs. Thus changing the split changes both the final fitted sample and the selection signal. This is a legitimate end-to-end training-protocol comparison, but cannot by itself isolate validation-selection quality under a common final training pool. It does not invalidate the paper.

## Concrete contrast required before a transfer pilot

Use the same historical pool, deployment set, candidate hyperparameters, initialization policy and compute cap in all arms. Vary two factors independently:

| Internal selection split | Final predictor fit |
|---|---|
| Random historical rows | Original fitting subset retained |
| Forward historical split | Original fitting subset retained |
| Random historical rows | Refit using the whole historical pool |
| Forward historical split | Refit using the whole historical pool |

For the refit arms, lock the selected candidate and its iteration count using only internal validation, then fit from scratch for that fixed count on the common historical pool. Do not early-stop on deployment labels. Refit preprocessing on that pool as part of the final pipeline. For retained-subset arms, preserve the originally selected checkpoint. Compare selection splits within the common-refit arms for the principal SplitSense question; report retained-subset arms as the combined training-protocol contrast. Iteration-count selection remains part of the selection intervention.

This is a design constraint, not a launched experiment or a frozen quantitative protocol. Before any fitting, specify an eligible data source, label-availability contract, complete candidate list, instance boundaries, primary metric, uncertainty unit, budget and stop rule. Prior rejected instances cannot serve as unseen confirmation. Do not claim this two-factor comparison alone identifies a pure causal training-lag effect: sample membership, size and early stopping may also differ.

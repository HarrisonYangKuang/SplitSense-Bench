# Candidate-menu decomposition (post-hoc)

Run `python3 evidence/candidate_menu_analysis.py`. Uses all 40 original development records, evaluating the original five, each of four single additions, and the augmented nine. Every menu preserves original tie order. Selection uses saved training-internal MSE; deployment utilities only score the locked selections. Each candidate was fitted independently in the original experiment, so restricting the menu does not require refitting.

The output reports the two difficult deployment tasks separately in each five-seed development group. It does not pool groups. Original and augmented choices are checked against the original records. The 0.05 effect count is only one component of the historical gate, not a complete gate decision.

This decomposition was chosen after viewing the original failure. It describes dependence on candidate availability on these instances, not prospective replication, a causal generalization, or permission to remove strong candidates to recover a positive benchmark. No new seeds, training, model calls, or new task family are introduced. Full interaction effects between additions are not estimated.

## Observed result

Cloud execution and original-choice checks passed. In each temporal group, adding only `time_linear_interaction` or only `time_hinge_interaction` to the original five reduced the effect-threshold count from 5/5 to 0/5, with identical random/aligned choices in all five instances. For unseen entities, adding only `global_linear_entity_residual` reduced the count from 4/5 and 5/5 to 0/5 in both groups. Thus the disappearance does not require all four additions simultaneously. See `candidate_menu_results.json` for every menu and both groups; this is a post-hoc, finite-instance conclusion.

Decision: do not revive these task versions by removing the added candidates or changing seeds. They remain candidate-library sensitivity cases. Any future task needs a justified deployment contract and a credible candidate library before its outcomes are inspected. No new family or formal Agent experiment is opened by this analysis.

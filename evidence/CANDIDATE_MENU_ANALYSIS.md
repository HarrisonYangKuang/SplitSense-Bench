# Candidate-menu decomposition (post-hoc)

Run `python3 evidence/candidate_menu_analysis.py`. Uses all 40 original development records, evaluating the original five, each of four single additions, and the augmented nine. Every menu preserves original tie order. Selection uses saved training-internal MSE; deployment utilities only score the locked selections. Each candidate was fitted independently in the original experiment, so restricting the menu does not require refitting.

The output reports the two difficult deployment tasks separately in each five-seed development group. It does not pool groups. Original and augmented choices are checked against the original records. The 0.05 effect count is only one component of the historical gate, not a complete gate decision.

This decomposition was chosen after viewing the original failure. It describes dependence on candidate availability on these instances, not prospective replication, a causal generalization, or permission to remove strong candidates to recover a positive benchmark. No new seeds, training, model calls, or new task family are introduced. Full interaction effects between additions are not estimated.

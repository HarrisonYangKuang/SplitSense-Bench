# Research status at v0.1.7-dev

This is a public runnable development benchmark and evidence package. The long-term research objective remains incomplete.

| Requirement | Public evidence | Remaining gap |
|---|---|---|
| Versioned generators and candidates | `tasks/`, four task settings, nine-candidate runner | These task constructions failed the stronger-library validity challenge |
| Evaluation workflow | `harness/`: training-only interaction, explicit commit, transcript replay, post-commit grading | No authenticated model identity or deployed security isolation |
| Baselines and finite-library reference | `benchmark.py`, candidate utilities | Finite sample best is not a population oracle; legacy wrappers have a smaller library |
| Agent trajectories and comparisons | No formal capability results in this release | Valid tasks, frozen protocol, verified model access, matched repeated runs, and public eligible trajectories |
| SplitSense Skill | `skills/` checklist and usage contract | No measured benefit; tokenizer-matched neutral control absent |
| Experimental evidence | `evidence/`: original 40-instance challenge; v26/v28/v36 aggregates; v33 independent implementation | Aggregate losses are not all raw predictions; Cooking, Seoul and Beijing evidence is not fully bundled |
| Reproduction | Frozen source files, saved-score checks, 90-loss v33 comparison | Same-AI implementation is not external replication; CI arithmetic is not retraining |
| Analysis | Tables, paired-history boundary, single-candidate additions | Post-hoc analyses do not pass original gates or establish a general Agent defect |
| Report and figures | Earlier eight-page PDF and addendum linked from README | Frozen report predates newest public analyses; not a final integrated submission |
| External review | None claimed | Human review is not required to continue internal work, but remains absent evidence |
| Formal frozen v1 / new-model blind evaluation | Not reached | No unseen-instance formal Agent or Skill comparison |
| Kaggle benchmark page | Not published | Optional; current public distribution is GitHub |

## Research decision

The original temporal and entity constructions remain stopped for formal capability evaluation. Single-candidate menu restrictions show that their earlier gains disappear without needing all four added candidates together. The paired-history study also illustrates why identical observable histories do not determine an unannounced future. These findings constrain future task design; they do not answer whether modern Agents generally have the proposed deficiency.

Do not remove strong candidates, retune thresholds, recycle development instances as holdouts, or count implementation checks as validity. Continue research only with a justified temporal deployment contract and credible candidates fixed before examining new outcomes. No additional task family is admitted here. Free-cloud resource constraints and the original scientific goal remain unchanged.

## Reproduce the evidence without fitting

From this release's root, run each command:

```sh
python3 evidence/reproduce.py
python3 evidence/verify_legacy.py
python3 evidence/history_ambiguity.py
python3 evidence/check_capital_reproduction.py
python3 evidence/candidate_menu_analysis.py
python3 experiments/verify_sources.py
```

Each command has a limited claim documented beside its inputs. The candidate-menu command prints its recomputed table; the stored `candidate_menu_results.json` also records its original cloud run. No paid API, model download, or training is needed for these commands.

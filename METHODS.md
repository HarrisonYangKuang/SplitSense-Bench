# Methods

## Research question

Diagnostic-D2 asked whether numerical execution support changes strict end-to-end delivery when a frozen Agent must use validation-risk evidence under an explicit deployment mixture. It did not test model selection or hidden deployment performance.

## Task

Each synthetic world contained 12 fixed candidate predictors and two visible validation-risk pools. A deployment contract stated the fraction `alpha` of deployment records represented in training. The visible target for candidate `c` was

`T_c = alpha * r_seen,c + (1 - alpha) * r_unseen,c`,

where `r_seen,c` and `r_unseen,c` are the serialized validation risks shown to the Agent. The target used those visible decimals, not an undisclosed higher-precision value.

## Execution conditions

- **N0 direct output:** the Agent selected the evidence and weights and wrote the complete 12-value vector.
- **N1 calculator:** the Agent selected evidence and weights, submitted bounded arithmetic, and then wrote the vector.
- **N2 declarative execution:** the Agent locked evidence references, candidate mappings, and weights. A bounded executor evaluated that exact plan and produced an immutable vector. It did not infer or repair the correct semantics.

N0 is `AGENT_OUTPUT`; N1 and N2 are `AGENT_PLUS_EXECUTOR`.

## Endpoint

The strict endpoint was

`J_D2 = valid_lock AND P AND max_c(e_c) <= tau`,

where `P` means correct evidence references, candidate binding, and deployment weights; `e_c = abs(R_hat_c - T_c) / V`; `R_hat_c` is the submitted or executed risk; `V` is the positive training variance; and the frozen normalized tolerance `tau` is `1e-4`. Every assigned session remained in its condition denominator. Invalid continuous metrics were missing rather than zero-filled.

## Design

The jointly frozen formal design contained 32 main worlds, 16 independent replication worlds, and second runs on 8 preselected main worlds. Every world had two deployment settings and three execution conditions: 192 main, 96 replication, and 48 repeat sessions, totaling 336. Condition scores were not disclosed until all sessions were terminal. Unknown deliveries were terminal and never retried.

## Statistics

The independent unit was the world. For each world and comparison, the two deployment-level differences in `J_D2` were averaged. The report gives the mean difference in percentage points and a paired-world percentile interval from 20,000 bootstrap resamples. Frozen random seeds were 2026092102 for main and 2026092103 for replication. Main and replication were analyzed separately.

## Public-data boundary

The public CSV files contain batch, anonymized world, anonymized deployment, execution mode, terminal category, valid-lock indicator, semantic-plan indicator `P`, and strict endpoint `J_D2`. They exclude task-generation seeds, hidden outcomes, raw prompts, raw responses, private account data, and private cloud material. This is sufficient to reproduce the registered public comparisons but not to reconstruct private formal episodes.

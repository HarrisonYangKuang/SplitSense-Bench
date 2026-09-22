# Benchmark-B1: Evidence Use & Numerical Execution

Benchmark-B1 is an open, deterministic Kaggle evaluation of whether a model can use validation-risk evidence under an explicit deployment mixture and deliver the resulting candidate risk vector. It contains 12 synthetic base tasks in six paired designs and three execution modes, exposed as 36 native Kaggle tasks.

## Public Kaggle collections

- [Direct](https://www.kaggle.com/benchmarks/yangkuangou/splitsense-b1-direct-v1): the model returns the semantic plan and complete numerical vector without tools.
- [Calculator](https://www.kaggle.com/benchmarks/yangkuangou/splitsense-b1-calculator-v1): the model returns the semantic plan and candidate-keyed arithmetic expressions; a bounded evaluator executes each expression once.
- [Declarative](https://www.kaggle.com/benchmarks/yangkuangou/splitsense-b1-declarative-v1): the model submits one locked semantic plan; a restricted executor applies that exact plan without semantic correction.

Each collection has 12 tasks. Every task opens two isolated model chats and returns the mean of their two end-to-end indicators, so a native task score is 0, 0.5, or 1.

## Visible target and metrics

For task `t` and candidate `c`, the visible target is

`T[t,c] = alpha[t] * r[seen,t,c] + (1 - alpha[t]) * r[unseen,t,c]`.

`alpha[t]` is the fraction of deployment records represented in training; `r[seen,t,c]` and `r[unseen,t,c]` are the visible validation MSE values. `T[t,c]` is a deterministic target computed from displayed evidence. It is not hidden deployment loss.

Each session records:

- `S`: semantic decision success. Pool membership, record-level weights, candidate binding, and aggregation must all be correct.
- `X`: numerical execution success. The complete vector must be within normalized tolerance `1e-4`.
- `J = S * X`: end-to-end success, which is the Kaggle task score component.

The public scorer is [scorer.py](scorer.py), the accepted inputs are [b1-1.0.1](task_inputs_b1_1_0_1.json) and [b1-1.0.2](task_inputs_b1_1_0_2.json), and the exact 36 task sources and hashes are in [TASK_MANIFEST.json](TASK_MANIFEST.json).

## Frozen reference

One platform reference used `google/gemini-3.7-flash` for 36 native runs and 72 sessions. Direct, Calculator, and Declarative each recorded `SA = 1.0`, `EA = 1.0`, and `E2E = 1.0`. All platform scores matched an independent recomputation. The maximum observed session used 2 model requests, 5,445 tokens, and 1 LLM tool call.

Direct and Declarative use the accepted `b1-1.0.1 v1r2` sources. Calculator uses the separately frozen `b1-1.0.2 v1r3` repair, which reduced the interaction to one model response plus one bounded local evaluation. The rejected older Calculator batch is not part of the public task set.

This reference shows that one model/platform version completed this small open fixture suite. It does not establish cross-model ranking, hidden deployment-risk accuracy, model-selection reliability, real-world transfer, or general data-science capability.

## Local verification

Only Python's standard library is needed to verify the public source inventory:

```bash
python benchmark/verify_b1_release.py
python -m py_compile benchmark/tasks/*.py
```

Running the tasks themselves requires the Kaggle Benchmarks SDK and platform model access. The task source is released under the repository's MIT License.

# SplitSense-Bench

**SplitSense studies whether data-science agents can correctly use validation evidence under explicit deployment settings, and whether separating semantic decisions from numerical execution improves reliable delivery.**

## Public Benchmark-B1

Benchmark-B1 is the runnable Kaggle suite for **Evidence Use & Numerical Execution**. It has 12 deterministic synthetic base tasks, three execution modes, 36 native tasks, and three public collections:

- [Direct](https://www.kaggle.com/benchmarks/yangkuangou/splitsense-b1-direct-v1)
- [Calculator](https://www.kaggle.com/benchmarks/yangkuangou/splitsense-b1-calculator-v1)
- [Declarative](https://www.kaggle.com/benchmarks/yangkuangou/splitsense-b1-declarative-v1)

The frozen reference used `google/gemini-3.7-flash` for 36 runs and 72 sessions. All three modes recorded `SA = 1.0`, `EA = 1.0`, and `E2E = 1.0`; all platform scores matched an independent recomputation and every session passed the frozen request, token, and tool budgets. See [benchmark/README.md](benchmark/README.md) for the task contract, source, hashes, and limits.

B1 is a small, open, deterministic synthetic suite. Its reference is one model/platform result. It does not establish cross-model ranking, real-world deployment-risk accuracy, model-selection reliability, or general data-science capability.

## Frozen Diagnostic-D2 result

| Batch | N0 direct | N1 calculator | N2 declarative | N2 − N0 paired-world difference |
|---|---:|---:|---:|---:|
| Main | 0/64 (0.00%) | 13/64 (20.31%) | 14/64 (21.88%) | **+21.88 pp**, 95% CI [12.50, 32.81] |
| Independent replication | 0/32 (0.00%) | 7/32 (21.88%) | 12/32 (37.50%) | **+37.50 pp**, 95% CI [18.75, 56.25] |

N0 required the Agent to output the full risk vector. N1 let the Agent use a bounded calculator before submitting the vector. N2 required the Agent to lock evidence references, candidate bindings, and weights; a restricted executor then produced the vector without correcting semantic choices. The N2-versus-N1 intervals cross zero, so D2 does not show that declarative execution is better than calculator assistance.

## Reproduce offline

No API key, Kaggle account, network connection, or GPU is required for the public checks.

```bash
python reproduce_public_results.py
python demo.py
python benchmark/verify_b1_release.py
python -m unittest discover -s tests -v
python analysis/build_release_manifest.py --check
```

## Repository map

- `benchmark/`: B1 task inputs, independent scorer, exact 36 Kaggle task sources, hashes, and reference summary.
- `public_results/`: anonymized D2 main and replication endpoint records plus metadata.
- `executors/`: bounded declarative executor used by the toy demo.
- `analysis/`: deterministic figure and release verification utilities.
- `reports/`: frozen D2 technical report.
- `RELEASE_MANIFEST.json`: byte sizes and SHA-256 hashes for every public file.

Private D2 prompts, raw responses, hidden outcomes, generation seeds, credentials, and restricted evidence remain excluded. B1 publishes its open task inputs and code; the public reference summary excludes account and credential material.

## Status

This is SplitSense-Bench v1.1.0: the frozen D2 research package plus public Benchmark-B1. Track A remains `INACTIVE_UNRESOLVED`; B1 does not start D3 or claim real-world validation-risk reliability.

# SplitSense-Bench

**An auditable benchmark for the path from validation evidence to a complete numerical decision.** SplitSense tests whether an AI agent selects the right evidence, binds it to the right candidates, and delivers a risk vector under an explicit deployment mixture.

Project author: **Ouyang Kuang**. This repository contains a frozen synthetic diagnostic study, a public Kaggle task suite, a bounded arithmetic executor, and an offline reproduction package.

**Start here:** [technical report](reports/SPLITSENSE_D2_REPORT.md) · [methods](METHODS.md) · [claims and limitations](CLAIMS_AND_LIMITATIONS.md) · [contribution and AI-assistance disclosure](CONTRIBUTIONS.md).

## Try it locally

Python 3.10 or later; standard library only. No API key, Kaggle account, network connection, or GPU is required.

```bash
python3 demo.py                           # toy plan -> sealed 12-value artifact
python3 -m benchmark.demo_scorer          # correct numbers can still fail semantics
python3 reproduce_public_results.py      # recompute the published D2 statistics
python3 -m unittest discover -s tests -v
```

The scorer walkthrough uses only an open B1 synthetic fixture. It shows a valid submission, a wrong candidate binding with correct numbers, and an incomplete vector. It is a local scoring example, not a new model experiment. Full checks and expected outputs are in [REPRODUCE.md](REPRODUCE.md).

## What to inspect

- **Evidence contracts and scoring:** [B1 scorer](benchmark/scorer.py) separates semantic correctness (`S`) from numerical completeness (`X`), with end-to-end success `J = S * X`.
- **Bounded execution:** [executor](executors/core.py) supports restricted arithmetic and locked evidence plans, with artifact hashes and no semantic repair.
- **Research discipline:** [public endpoint records](public_results/) retain failures; [reproduction script](reproduce_public_results.py) recomputes paired-world confidence intervals; [claims ledger](CLAIMS_AND_LIMITATIONS.md) states unresolved comparisons and transfer limits.

These are the project-specific implementation and packaging contributions visible in this repository. Execution assistance itself has prior art; the project does not claim a new general reasoning algorithm or sole manual authorship of every line.

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
| Registered replication batch | 0/32 (0.00%) | 7/32 (21.88%) | 12/32 (37.50%) | **+37.50 pp**, 95% CI [18.75, 56.25] |

N0 required the Agent to output the full risk vector. N1 let the Agent use a bounded calculator before submitting the vector. N2 required the Agent to lock evidence references, candidate bindings, and weights; a restricted executor then produced the vector without correcting semantic choices. The N2-versus-N1 intervals cross zero, so D2 does not show that declarative execution is better than calculator assistance.

The replication batch used new synthetic worlds within the same registered task family; it was not an external researcher's replication. D2 and B1 use different interfaces and endpoints, so B1's perfect reference score is not evidence of an improvement over D2. No independent public reproduction or external human review is claimed.

## Reproduce offline

No API key, Kaggle account, network connection, or GPU is required for the public checks.

```bash
python3 reproduce_public_results.py
python3 demo.py
python3 -m benchmark.demo_scorer
python3 benchmark/verify_b1_release.py
python3 -m unittest discover -s tests -v
python3 analysis/build_release_manifest.py --check
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

The scientific package is SplitSense-Bench v1.1.0: the frozen D2 research package plus public Benchmark-B1. Documentation and an offline scorer walkthrough were refreshed on 2026-10-01 without changing the frozen results, task sources, scorer, or executor. Track A remains `INACTIVE_UNRESOLVED`; B1 does not start D3 or claim real-world validation-risk reliability.

## License and citation

This GitHub repository is distributed under the [MIT License](LICENSE). Kaggle backing Notebooks use the platform's **Apache 2.0** license; the earlier D2 Kaggle data artifact uses **CC0-1.0**. These platform choices do not replace the MIT terms of this repository. See [provenance and privacy boundary](PRIVACY_AND_PROVENANCE.md) and [CITATION.cff](CITATION.cff).

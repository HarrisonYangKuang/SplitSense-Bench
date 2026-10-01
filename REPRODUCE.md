# Offline reproduction

Requirements: Python 3.10 or later. The offline checks below use only the standard library. Optional PDF rebuilding with `reports/build_report.py` requires ReportLab; the prebuilt PDF is included, and rebuilding it is not required to reproduce the statistics or demos.

Reproduce the frozen Diagnostic-D2 public statistics:

```bash
python3 reproduce_public_results.py
```

Expected strict successes are Main N0 `0/64`, N1 `13/64`, N2 `14/64`; Replication N0 `0/32`, N1 `7/32`, N2 `12/32`. Expected N2-minus-N0 differences are `+21.875` points with interval `[12.5, 32.8125]` and `+37.5` points with interval `[18.75, 56.25]`.

Verify the public Benchmark-B1 inventory and the independent toy demonstration:

```bash
python3 benchmark/verify_b1_release.py
python3 -m py_compile benchmark/tasks/*.py
python3 demo.py
python3 -m benchmark.demo_scorer
python3 -m unittest discover -s tests -v
python3 analysis/build_release_manifest.py --check
```

The B1 inventory check verifies all 36 task-source hashes, the 12/12/12 mode split, accepted source revisions, and the 72-session reference summary. Executing fresh model runs requires the Kaggle Benchmarks SDK and platform access. Offline reproduction does not replay private D2 model calls or B1 reference trajectories.

## Expected offline walkthrough

`demo.py` prints `status: PASS`, `sealed: true`, and `risk_count: 12` for a public toy D2 plan. It is not a formal D2 episode.

`python3 -m benchmark.demo_scorer` uses B1 task `ss-b1-t10-v1`, whose pool identifiers deliberately do not reveal membership. It produces three outcomes:

| Constructed submission | S | X | J |
|---|---:|---:|---:|
| Correct plan and complete vector | 1 | 1 | 1 |
| Wrong candidate binding, correct vector | 0 | 1 | 0 |
| Correct plan, incomplete vector | 1 | 0 | 0 |

The independently readable first-candidate calculation is `0.75 * 3.545 + 0.25 * 0.955 = 2.8975`. The walkthrough also checks that a function-call expression is rejected by the Calculator language. It constructs a response from visible fixture data, so it verifies scoring behavior without claiming an AI model solved the task.

The test suite covers the frozen D2 counts and intervals, the sealed toy artifact, B1 semantic/numeric separation, candidate coverage, pool-membership binding, invalid locks, and arithmetic-language rejection. Compilation of Kaggle task sources checks syntax only; it does not import the SDK or run platform tasks.

All commands above are local checks of public artifacts. They do not provide an external reproduction, new model score, or verification of private experimental provenance.

# Offline reproduction

Requirements: Python 3.10 or later. Only the standard library is used.

Reproduce the frozen Diagnostic-D2 public statistics:

```bash
python reproduce_public_results.py
```

Expected strict successes are Main N0 `0/64`, N1 `13/64`, N2 `14/64`; Replication N0 `0/32`, N1 `7/32`, N2 `12/32`. Expected N2-minus-N0 differences are `+21.875` points with interval `[12.5, 32.8125]` and `+37.5` points with interval `[18.75, 56.25]`.

Verify the public Benchmark-B1 inventory and the independent toy demonstration:

```bash
python benchmark/verify_b1_release.py
python -m py_compile benchmark/tasks/*.py
python demo.py
python -m unittest discover -s tests -v
python analysis/build_release_manifest.py --check
```

The B1 inventory check verifies all 36 task-source hashes, the 12/12/12 mode split, accepted source revisions, and the 72-session reference summary. Executing fresh model runs requires the Kaggle Benchmarks SDK and platform access. Offline reproduction does not replay private D2 model calls or B1 reference trajectories.

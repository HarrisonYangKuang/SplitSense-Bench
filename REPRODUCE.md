# Offline reproduction

Requirements: Python 3.10 or later. Only the standard library is used.

From the release root, run:

```bash
python reproduce_public_results.py
```

Expected strict successes:

- Main: N0 `0/64`, N1 `13/64`, N2 `14/64`.
- Replication: N0 `0/32`, N1 `7/32`, N2 `12/32`.

Expected N2-minus-N0 results:

- Main: `+21.875` percentage points, 95% interval `[12.5, 32.8125]`.
- Replication: `+37.5` percentage points, 95% interval `[18.75, 56.25]`.

Run the independent toy demonstration and tests:

```bash
python demo.py
python -m unittest discover -s tests -v
```

The toy demo is deterministic and is not a formal D2 episode. Public reproduction covers the aggregated frozen endpoint and bootstrap analysis. It does not reproduce private model calls, raw trajectories, hidden outcomes, or task-generation seeds; those remain `PRIVATE_EVIDENCE_NOT_PUBLIC`.

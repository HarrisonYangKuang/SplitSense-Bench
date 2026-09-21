# SplitSense-Bench

**SplitSense studies whether data-science agents can correctly use validation evidence under explicit deployment settings, and whether separating semantic decisions from numerical execution improves reliable delivery.**

## Frozen Diagnostic-D2 result

| Batch | N0 direct | N1 calculator | N2 declarative | N2 − N0 paired-world difference |
|---|---:|---:|---:|---:|
| Main | 0/64 (0.00%) | 13/64 (20.31%) | 14/64 (21.88%) | **+21.88 pp**, 95% CI [12.50, 32.81] |
| Independent replication | 0/32 (0.00%) | 7/32 (21.88%) | 12/32 (37.50%) | **+37.50 pp**, 95% CI [18.75, 56.25] |

N0 required the Agent to output the full risk vector. N1 let the Agent use a bounded calculator before submitting the vector. N2 required the Agent to lock evidence references, candidate bindings, and weights; a restricted executor then produced the vector without correcting semantic choices.

## What this does not prove

The N2-versus-N1 intervals cross zero, so the study does not show that declarative execution is better than calculator assistance. It also does not establish stronger underlying model reasoning, real-world deployment-risk accuracy, Track A model-selection reliability, cross-model generalization, or cross-domain generalization. See [CLAIMS_AND_LIMITATIONS.md](CLAIMS_AND_LIMITATIONS.md).

## Reproduce offline

No API key, Kaggle account, network connection, or GPU is required.

```bash
python reproduce_public_results.py
python demo.py
python -m unittest discover -s tests -v
python analysis/build_release_manifest.py --check
```

The first command reconstructs absolute counts, percentages, paired-world differences, and the frozen 20,000-draw percentile bootstrap intervals from anonymized aggregate episode records. The second runs a public toy example through the key-free declarative executor.

## Repository map

- `public_results/`: anonymized main and replication endpoint records plus metadata.
- `executors/`: bounded declarative executor used by the toy demo.
- `examples/`: public toy task and plan; these are not formal D2 episodes.
- `analysis/`: deterministic figure and verification utilities.
- `tests/`: public reproduction and demo checks.
- `reports/`: public technical report.
- `benchmark/`: future Benchmark-B1 schema material; no public benchmark is claimed yet.
- `RELEASE_MANIFEST.json`: byte sizes and SHA-256 hashes for every public file.

Private cloud prompts, raw responses, hidden outcomes, generation seeds, credentials, and restricted evidence are intentionally excluded. Their status is `PRIVATE_EVIDENCE_NOT_PUBLIC`; frozen hashes and the local completion audit preserve the evidence boundary.

## Status

This is the frozen SplitSense-Bench v1.0.0 public research package. It reports Diagnostic-D2 without reopening Track A, starting D3, or treating future Benchmark-B1 work as completed.

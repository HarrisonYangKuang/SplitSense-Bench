# SplitSense-Bench · Development release

A runnable diagnostic toolkit for studying how deployment descriptions and validation choices affect model selection.

**Status: development tasks, not a validated Agent leaderboard.** The four synthetic tasks failed our stronger-candidate validity gate. No claim of systematic Agent failure or Skill improvement is supported. This release makes the implementations inspectable and runnable; it does not turn negative research results into a successful benchmark.

## Quick start

Python 3.10+; standard library only. No API keys, installation, GPU or network required after cloning.

```sh
git clone https://github.com/HarrisonYangKuang/SplitSense-Bench.git
cd SplitSense-Bench
python3 benchmark.py list
python3 benchmark.py demo --task temporal_future --seed 101
```

The demo uses all nine fixed candidates and reports random/aligned validation choices plus future MSE. Aligned means a deployment-matched reference, not an infallible oracle. The finite-sample best candidate is computed after scoring and is not available to the selection step. Smaller MSE is better. These are trusted-script demonstrations, not Agent results.

## Export a task and grade predictions

```sh
python3 -m tasks.temporal_future.data_generator --seed 101 --agent-dir run/agent --evaluator-dir run/evaluator
python3 benchmark.py grade --submission run/agent/sample_submission.csv --hidden run/evaluator/hidden_labels.csv
```

The second command scores a zero-prediction format example. Replace it with the model's CSV containing exactly row_id,target. Duplicate, missing, extra or nonfinite predictions are rejected.

Give an Agent only the exported agent directory. Keep evaluator files, generator source and seed outside its access. Separate directories alone are NOT permission isolation. Public generators and demo seeds do not provide a secret test set; this release contains no secure hosted evaluator and does not execute untrusted code.

## Tasks and versions

Development tasks: temporal_iid, temporal_future, entity_seen, entity_unseen. Paired tasks share training construction but differ in deployment. The temporal_iid identifier denotes historical sampling, not a proof of IID observations.

Generator: 0.1.0-prototype. Default demo candidate library: 0.2.0-strong-candidate-challenge. Legacy task baseline/oracle modules retain the original five-candidate implementation for reproducibility; use benchmark.py for the nine-candidate demo. Names containing oracle are historical reference names, not access to future answers.

## Known limitations and research record

The original 9-candidate/40-development-instance challenge did not pass the frozen gate. Subsequent Cooking, Seoul, Capital and multi-window diagnostics also did not establish stable task validity. No formal Agent/Skill comparison or external human review has been completed. Thus no leaderboard or model capability ranking is provided.

The current public package contains synthetic generators and scoring code only, not credentials, private datasets, private trajectories or proprietary weights. Broader evidence publication and validated tasks remain ongoing work. Do not use this development score as a model capability claim.

中文：这是可运行的开发版，包含任务生成、九候选演示和提交评分。任务尚未通过科研有效性门；不代表已证明Agent缺陷或Skill有效。完整研究目标仍在进行。

## Automated interface verification

[CI runs](https://github.com/HarrisonYangKuang/SplitSense-Bench/actions/workflows/interface.yml) execute all four development demos, check paired training and exported file boundaries, and reject malformed submissions. These checks establish software behavior, not research validity or OS-level isolation. Run locally with `python3 -m unittest discover -s tests -v`; research sweeps should use cloud resources.

## Inspect the experimental evidence

[Public evidence capsule](evidence/README.md) includes 30 saved cases and a standard-library table reproducer. Run `python3 evidence/reproduce.py`. Coverage and raw-data limitations are explicit; this is not a model leaderboard.

## Re-run original experiments

[Cloud reproduction guide](experiments/README.md) provides four original executed scripts, source hashes and the recorded runtime. Source verification is automated; cloud training reproduction has additional environment requirements and is not silently replaced by table arithmetic.

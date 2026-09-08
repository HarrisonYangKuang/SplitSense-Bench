# Text Agent interface (development)

The public bridge accepts a training CSV and visible deployment brief, then exchanges newline-delimited JSON with an external text responder. It has no API keys, model SDK, hidden-label input, arbitrary-code tool or network client. You supply the responder; its model identity and cost are not established by this interface. No model call is automatically purchased or launched.

```sh
python3 -m harness.pipe_session --train run/agent/train.csv --brief run/agent/task_description.md --receipt run/session.json
```

It prints an instructions/history JSON line. Send one JSON action line through stdin. First evaluate a listed split, for example:

```json
{"action":"evaluate","split":"forward_time"}
```

The next prompt includes the resulting training-internal candidate losses. Then explicitly select and seal a candidate, for example:

```json
{"action":"commit","split":"forward_time","candidate_id":"train_mean","reason":"Example choice; not an Agent result."}
```

There are at most three response opportunities, including invalid responses, and at most two distinct split evaluations. Commit requires a previously evaluated split. No choice is inferred if the responder fails or exhausts its budget. The trusted receipt records the transcript, evaluations and commit hash. A final session_finished line reports committed or incomplete status. An existing receipt is never overwritten.

Only training summaries and training-internal losses are sent to the responder. Keep this Python process and its files outside the Agent's execution environment. A callback in the same Python process is NOT an OS security boundary, and stdin/stdout alone does not stop a local malicious process reading other accessible files. Use separately controlled hosts/permissions for actual isolation. The bridge currently has no wall-clock deadline for stdin; the orchestrator must enforce one and record timeout failures. No secure hosted evaluator is included.

The selection step receives no hidden scores. After commit, a trusted evaluator can use the committed candidate_id with tasks.strong_candidates_v02.candidate_predictions on its own train/test inputs, then graders.metrics.grade_submission against its hidden labels. This is a fixed-library selection interface, not unrestricted model development. Public demo seeds must not be called hidden test instances.

The inherited v03/v04 docstrings identify their historical engineering versions; later engineering validation did not establish scientific task validity. CI checks phase behavior and failure handling only. Formal Agent evaluation remains gated on task validity; the project has not established an Agent or Skill effectiveness result.

## Post-commit scoring command

Run this in a separate trusted evaluator process after the session finishes:

```sh
python3 -m harness.grade_session --train run/agent/train.csv --brief run/agent/task_description.md --receipt run/session.json --test run/agent/test.csv --hidden run/evaluator/hidden_labels.csv
```

The grader replays every action using the supplied training data and brief, compares the recorded feedback and sealed session, and only then opens test features and hidden labels. A mismatched or uncommitted receipt is rejected. The report includes chosen MSE, all nine candidate MSE values, finite-library regret and the validation optimism gap (deployment MSE minus validation MSE). Normalized regret divides by training target variance; it is null for zero variance. Regret references the best candidate on the finite scoring set, not a population oracle.

The receipt is not a cryptographic signature or proof of model identity: a caller can construct its own valid action sequence. Replay establishes internal consistency only. Keep grader outputs unavailable during selection and run the Agent outside the grader's permissions. The CLI does not itself enforce cross-host isolation. It remains a development workflow, not an authorized formal Agent effectiveness experiment.

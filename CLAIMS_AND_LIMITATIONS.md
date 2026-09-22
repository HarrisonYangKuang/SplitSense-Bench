# SplitSense Publication-P1 public claims ledger

Status: `FROZEN_PUBLIC_V1`  
Source boundary: Diagnostic-D2 `COMPLETE_DIAGNOSTIC`, frozen by `D2_PUBLICATION_FREEZE.json`.

## SUPPORTED

- In the registered Diagnostic-D2 task family, N2 declarative execution improved strict complete delivery relative to N0 direct output.
- Main study: N0 0/64 (0.00%), N1 13/64 (20.31%), N2 14/64 (21.88%). N2 minus N0 was +21.88 percentage points with a paired-world bootstrap 95% interval of [12.50, 32.81].
- Independent replication: N0 0/32 (0.00%), N1 7/32 (21.88%), N2 12/32 (37.50%). N2 minus N0 was +37.50 points with interval [18.75, 56.25].
- The restricted declarative executor can run deterministically without a model key, network access, or human scoring.
- The observed intervention is an Agent-plus-executor system: the Agent selected evidence, candidate bindings, and weights; the executor applied the locked plan without semantic correction.

## SUPPORTED_WITH_LIMITATIONS

- The positive direction reproduced in a second batch of new synthetic worlds, but both batches used the same registered generator, fixed 12-candidate library, frozen model, task interface, and execution environment.
- N1 calculator assistance also improved strict complete delivery over N0 in both batches. The experiment therefore supports execution assistance broadly within this task, not a unique benefit of N2.
- D1's zero complete-vector outcome was not explained by the tested precision, scoring, ordering, or binding defects. Unlogged internal reasoning remains unobservable.
- Continuous error summaries apply only to valid locks and are subject to selection bias. Invalid and unknown-delivery sessions remain in the strict endpoint denominator.

## NOT_SUPPORTED

- N2 is better than N1. The N2-minus-N1 95% intervals cross zero in both main and replication batches.
- SplitSense improves the frozen model's underlying reasoning ability.
- SplitSense reliably predicts hidden real-world deployment risk.
- SplitSense improves model selection or proves Track A.
- The result generalizes across models, domains, production environments, or all data-science tasks.
- A calculator or declarative executor is a new general algorithm introduced by this project.

## NOT_TESTED

- GPT-6, Claude, Gemini, or open-weight model comparisons.
- Multiple real-world domains or production deployments.
- Large-scale community benchmark use.
- Skill-prompt effectiveness.
- Public user adoption, external reproduction, or independent human review.

## Frozen interpretation rules

D2 raw results, registered worlds, model identifier, endpoint, bootstrap procedure, failures, and comparison definitions are read-only. Publication may improve explanation and packaging but may not rescore, add worlds, tune prompts, change thresholds, or reinterpret Track A.

## Benchmark-B1 v1.0.0 addition

### SUPPORTED

- B1 is a public runnable suite with 12 deterministic synthetic base tasks, 36 native task sources, and separate Direct, Calculator, and Declarative collections.
- The frozen `google/gemini-3.7-flash` reference contains 36 native runs and 72 sessions. Each mode has 24 sessions and recorded `SA = EA = E2E = 1.0`.
- Independent recomputation matched every platform score. All effective sessions passed the frozen limits; the observed maxima were 2 model requests, 5,445 tokens, and 1 LLM tool call per session.

### LIMITS

- The B1 result is a single-model, single-platform reference over open deterministic synthetic fixtures. A perfect reference score indicates saturation for this model under this interface; it is not evidence of model superiority.
- B1 targets use visible validation-risk evidence. They are not hidden deployment outcomes and do not validate risk estimates against real deployment loss.
- B1 does not complete Track A, compare models, establish cross-domain or production generalization, or show that Declarative is better than Calculator.
- The public task code makes the deterministic targets derivable. B1 supports transparent reproduction, not permanent contamination resistance.

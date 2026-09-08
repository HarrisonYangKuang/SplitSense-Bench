# SplitSense Skill: development intervention

This is an unvalidated guidance artifact, not an effective intervention established by experiment. The checklist is in Chinese; changing its language creates another intervention version.

## Use with the public session

For a development integration, supply `validation_checklist.md` once as an additional instruction to your external responder, before its first session prompt. Keep the deployment brief and training data identical to the vanilla condition. Do not append the checklist to the deployment brief: that would change the task input itself. The bundled pipe bridge does not call a model or automatically inject a skill.

Follow the action schema in the session prompt. The interface accepts evaluation and commit actions, not `validation_plan`. Inspection and interpretation belong in the responder's decision process; return only a valid action to the pipe. The same three-response budget applies to both conditions. A final reason is a short decision justification, not a requirement to disclose private reasoning.

## Conditions and provenance

- A: same task, model, model settings, tool budget, and common instructions; no checklist.
- B: identical setup plus the exact checklist text supplied once at the same fixed instruction position.
- C: reserved for a tokenizer-matched neutral control; currently unavailable. Character or byte equality does not establish token matching.

Before any formal comparison, freeze the full rendered prompts, model identifier, tokenizer/version, token and reasoning budgets, instance set, repetition policy, exclusion rules, and scoring protocol. Record their hashes, the instruction roles/order, model responses, and completion failures. The current session receipt records tool interaction but does not authenticate the external prompt or model identity. A separate runner record is needed; this document is not that record.

## What the present interface can measure

The fixed candidate/tool library supports deployment interpretation, validation choice, interpretation of returned losses, and explicit selection. It does not measure unrestricted preprocessing or model implementation. A checklist item about preprocessing therefore asks the responder to inspect available evidence, not claim it wrote or audited an arbitrary training pipeline.

Task validity remains unestablished. Do not run a formal capability or Skill-effect study on these development tasks and label it validated. No control prompt, token-match result, human review, or Skill benefit is claimed here. Historical experiments and previous checklist versions are not retroactively assigned this intervention.

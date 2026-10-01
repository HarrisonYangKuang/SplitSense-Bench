# Privacy, license, and provenance boundary

The public release contains anonymized aggregate endpoint records, public toy examples, original project code, documentation, figures, and a technical report.

Excluded as `PRIVATE_EVIDENCE_NOT_PUBLIC`:

- raw model prompts and responses;
- private cloud transport records and account information;
- task-generation seeds and registered private world identifiers;
- hidden outcomes or deployment labels;
- credentials, API keys, session tokens, and local absolute paths;
- restricted or third-party raw datasets.

The public main and replication CSV files are derived from the sealed Diagnostic-D2 score bundle. World and deployment identifiers were replaced with release-local identifiers. They retain only the terminal category and the three registered endpoint indicators needed to reconstruct published counts and paired-world comparisons.

All included code and prose were produced within the SplitSense-Bench project. No third-party source code or dataset is redistributed. External papers are cited by bibliographic reference and link. This GitHub repository is distributed under the MIT License; the earlier Diagnostic-D2 Kaggle data artifact uses CC0-1.0. See [CONTRIBUTIONS.md](CONTRIBUTIONS.md) for AI-assistance and attribution limits.

## Benchmark-B1 addition

B1 publishes its deterministic synthetic inputs, independent scorer, exact Kaggle task sources, source hashes, platform URLs, and aggregate reference summary. The task inputs contain no private user data or third-party dataset. Private account metadata, credentials, transport details, and raw reference conversations are excluded from the GitHub package.

The repository source remains **MIT-licensed**. Kaggle backing Notebooks display **Apache 2.0** as their platform license. The owner accepted that platform license on 2026-09-23; it is distinct from this repository's MIT distribution. The compact publication scope retained 14 public backing Notebooks and 22 intentionally private backing Notebooks, while this repository includes all 36 exact task source files. The 2026-10-01 GitHub documentation update does not change those platform visibility settings.

## Offline walkthrough update

The new scorer walkthrough derives an illustrative response from an already-public B1 synthetic fixture. Its counterexamples are constructed locally, not taken from private model responses. It does not expose internal research directories, private prompts, hidden outcomes, or additional account records.

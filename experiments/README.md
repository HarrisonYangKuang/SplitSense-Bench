# Re-run the saved experiments

Four original executed scripts are now public. FROZEN.json records their exact SHA256 and original runtime. The v26 script is the original design.py plus one newline plus worker.py; its combined hash matches the executed source. Other scripts are byte-identical copies. No raw private data, weights or credentials are bundled.

|Script|Purpose|Original observed fitting time|Fit count|
|---|---|---:|---:|
|synthetic_v26.py|20 synthetic mechanism cases|87.1 s|360 including means|
|capital_v28.py|5 Capital ranking blocks|17.8 s|90 including means|
|capital_independent_v33.py|Independent implementation of the same Capital instances|11.8 s|90 including means|
|multiwindow_v36.py|5 fixed time-series entries, repeated validation|46.0 s|225; persistence has no fit|

These times are historical observations, not runtime promises. The scientific screens failed; rerunning is for reproduction, not searching for a passing seed.

## Cloud runtime

Use a CPU cloud session. The original Python version is 3.12.13 with the package versions in requirements.txt. Scripts intentionally reject incompatible recorded versions. The immutable original Kaggle image identifier is in FROZEN.json; availability on a new account or platform has not been verified. Do not download a container image or install a large environment on a storage-constrained laptop. Dependencies beyond the listed packages were supplied by the original image; requirements.txt alone is not a complete lockfile.

Capital scripts download the public UCI Bike Sharing day.csv archive and verify its digest. Multiwindow downloads the author's public serialized data at a fixed Git commit and requires Rscript (base R); it does not require the author's tsensembler packages because it is an explicit sklearn adaptation. Respect the upstream dataset terms. Synthetic v26 generates data in the cloud and requires no external dataset. Network is needed for the download-based scripts only.

Run each script in a fresh output directory, since artifact names overlap. For example, from the repository root in the matching cloud runtime:

```sh
python3 experiments/verify_sources.py
mkdir -p run/capital-v28
cd run/capital-v28
python3 ../../experiments/capital_v28.py
```

Inspect summary.json.gz: a platform COMPLETE status is insufficient. Expected successful execution status is pilot_complete_not_family_validity for v28/v36 or mechanism_complete_not_family_validity for v26. Independent v33 writes independent_results.json.gz instead. Preserve all failure outputs; do not modify the frozen scripts in place.

The source creates raw prediction, loss and selection artifacts in the cloud. Public evidence/cases.json provides saved candidate losses and choices for v26/v28/v36; compare by study and instance. Separate reproduction of model fits from arithmetic checking with evidence/reproduce.py. No hosted secret evaluator or new blind dataset is provided by these scripts. Any source, preprocessing, seed or runtime change must be disclosed as an adaptation.

The original protocols include assumptions that remain unverified in real deployment: feature release timing for observed series and source independence. The scripts cannot establish Agent failure or Skill effectiveness. A CI source-hash check verifies provenance and syntax only, not scientific validity or complete runtime portability.

# Public aggregate evidence

This capsule publishes 30 saved experimental cases: 20 synthetic v26 cases (four paired conditions, five seeds), five Capital v28 blocks and five multi-window v36 series. These are NOT 30 independent datasets. All selected source cases are retained, including negative and zero effects. No Agent was evaluated in these experiments.

Run `python3 evidence/reproduce.py`. It recomputes 30 normalized selection differences and the 10 ranking differences originally reported for v28/v36, comparing the generated table byte-for-byte with results.csv. It does not retrain models or verify the underlying predictions against raw labels.

E = (future MSE of random-validation choice - future MSE of time-validation choice) / training target variance. MSE means mean squared error; lower is better. Positive E favors time validation. D is Spearman rank correlation for time validation minus the corresponding random-validation correlation, both against future candidate losses. Average ranks handle ties. D is left blank for v26, where it was not the registered primary metric.

Capital v28: positive D in 3/5 blocks, median 0.171429. Multi-window v36: positive D in 1/5 series, median 0. Both missed the frozen requirement of at least 4/5 positive and median at least 0.20. Synthetic v26 did not establish stable superiority across conditions. These are development screens, not significance tests or proof that validation never matters. Never pool different studies into one pass rate.

The capsule is a schema-whitelisted derivative of saved loss reports. Each original compressed report's SHA256 appears in cases.json for provenance. Original data/prediction files are not bundled: these hashes alone do not make independent training reproduction possible. No credentials or private raw datasets are included.

Coverage is explicitly partial: the earlier 40-instance challenge, Cooking v21, Seoul v25, failed Beijing v31 and independent-implementation v33 evidence are not in this capsule. They must not be treated as absent failures or zero-valued results. Broader public reproducibility remains incomplete.

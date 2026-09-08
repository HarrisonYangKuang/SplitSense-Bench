# v38 saved prediction evidence

Original cloud artifacts, byte-preserved after checking the source-run SHA-256 values. Run `python3 evidence/check_appliances_predictions.py` from the repository root to recompute 175 losses and inspect basic split/lock consistency. This does not prove operating-system isolation, authenticate chronology of the lock file, or retrain models.

`coverage.json` maps ordered prediction arrays to original CSV row indices. `choice_lock.json` records selected candidates. `predictions.json.gz` contains all validation, retained-model, and common-refit predictions and targets. Raw source features are not bundled; the pinned source URL and CSV hash are in the experiment script.

Target measurements derive from Luis Candanedo (2017), Appliances Energy Prediction, UCI Machine Learning Repository, DOI https://doi.org/10.24432/C5VC8G, licensed CC BY 4.0 according to the UCI record. Original paper: Candanedo, Feldheim and Deramaix, Energy and Buildings 140 (2017), 81–97, DOI 10.1016/j.enbuild.2017.01.083. These files reorganize target values by our fixed splits and add our model predictions; they do not reproduce the paper's evaluation.

The primary pilot gate failed. The data are public development evidence, never a secret holdout for future Agent evaluation.

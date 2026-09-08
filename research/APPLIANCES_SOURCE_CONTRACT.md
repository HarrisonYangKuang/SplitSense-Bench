# Appliances energy: source eligibility draft

2026-09-08. Metadata-only screen within the existing temporal family, not a new admitted benchmark task. No data download, model fitting or effect inspection has occurred for this candidate.

## Primary source

[Candanedo (2017), UCI dataset 374](https://archive.ics.uci.edu/dataset/374/appliances+energy+prediction), DOI 10.24432/C5VC8G. UCI describes 19,735 observations at ten-minute intervals over about 4.5 months in one low-energy house. `Appliances` is the energy target in Wh (watt-hours); UCI lists no missing values. The data page identifies the original paper and [author repository](https://github.com/LuisM78/Appliances-energy-prediction-data). Metadata statements still require file-level checks.

## Proposed information contract

The candidate is an offline replay of predicting the next ten-minute target record, not reproduction of the original paper's contemporaneous regression. A feature row for target index j may use energy values only through j-2, leaving one whole recorded interval between the latest input and the target. This is a deliberately declared observation-delay assumption, not evidence of actual meter delivery latency. Use ordinal ten-minute steps initially; the timezone and whether timestamps label interval starts or ends remain unverified. Do not claim a production service-level guarantee.

Eligible inputs: strictly historical target lags and deterministic clock/calendar features once timestamp semantics are checked. Exclude same-row energy, lights, room conditions, airport weather, and the synthetic random columns. This avoids relying on contemporaneous measurements or retrospective weather availability. Historical labels become inputs only after the declared delay; final model updates, if any, must be specified separately.

The file covers one house. Disjoint time blocks would be repeated deployment episodes, not independent houses or datasets. Any eventual positive pilot must be replicated on another source before a cross-source claim.

## Next zero-fit check

On free private Kaggle CPU, inspect the authoritative CSV with a bounded download, record its SHA-256, row count, timestamp order, duplicate timestamps, interval histogram, date range, and finite target coverage. Do not inspect predictive loss or choose intervals using target magnitude. Check whether five non-overlapping 21-day episodes exist after a seven-day initial lag-history allowance; all boundaries derive from the first complete day and remain fixed. Do not fill gaps, reorder duplicates, or discard blocks to rescue coverage. Raw CSV remains cloud-side; retain only a small summary.

Eligibility is still pending. A separate quantitative protocol must define candidates, validation splits, refit arms, primary metric, effect gate and CPU budget before fitting. This source is a feasibility candidate because its measured variable and historical-input construction are interpretable, not because temporal drift or useful split effects have been demonstrated. Do not replace previous negative results or label this a validity pass.

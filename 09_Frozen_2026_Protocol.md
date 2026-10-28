# Frozen 2026 final-test protocol

Written before downloading or scoring 2026 player totals. The chosen model is the **calibrated shrinkage baseline** selected from the 2023 and 2024 forward checks. Its saved selection artifact is `selected_pitch_model_2025_summary.json`, SHA-256 `09a0388f4d50af0ce9daeef9c1556d301a3fc55b322bc27278279ab4696f03e8`. This protocol and that artifact must not be changed in response to the 2026 outcome.

## Inputs available by June 30, 2026

Use MLB Stats API regular-season player pitching totals (`sportIds=1`, `gameType=R`, `playerPool=ALL`) for January 1–June 30, 2026. For each pitcher with at least **100 first-half batters faced**, compute `first_kbb = (first_K - first_BB) / first_BF`. Compute the first-half league rate `L` by summing K, BB, and BF across **all** first-half MLB pitchers, including those with fewer than 100 BF.

The prediction is fixed:

`prediction = (first_K - first_BB + 100 × L) / (first_BF + 100) + 0.006677184582860313`

The 100-BF weight and added constant come from the earlier work. No 2026 pitch traits, July outcomes, or full-season 2026 statistics enter the prediction.

## Outcome and scoring

Fetch official regular-season player totals for July 1–December 31, 2026. The outcome is `(second_K - second_BB) / second_BF`. Score only June-30-eligible pitchers who also faced at least **100 batters** from July onward. Report all June-30-eligible pitchers, the evaluable count, the non-evaluable count, and how many had zero July BF. This makes the playing-time selection visible.

Primary metric: equal-pitcher mean absolute error (MAE), in percentage points. Compare the frozen model with (a) unchanged first-half K-BB%, (b) first-half league K-BB% for everyone, and (c) the same 100-BF shrinkage prediction *without* the learned constant. Secondary metrics: RMSE in percentage points and Spearman rank correlation across the same evaluable pitchers. For MAE difference versus raw shrinkage, report a paired pitcher bootstrap 95% interval using 10,000 resamples and seed 2026. Positive improvement means the frozen model has lower MAE.

## Apparent-breakout report

Separately, use official **2025 full-season** K-BB% as the prior reference. A 2026 apparent breakout is a pitcher with at least 100 BF in 2025, at least 100 BF by June 30, 2026, and a first-half 2026 K-BB rate **at least 3 percentage points above** his 2025 rate. This +3-point reporting threshold is descriptive and was chosen before 2026 data were examined; it does not train or change the model. Report the number of apparent breakouts, how many have at least 100 July BF, and among those how many finish July onward above their 2025 rate. Show the top five by June-30 improvement with their July status, including those with too little July BF. Do not call this proof of a skill change.

## Data integrity and stopping rule

Save raw API responses in this project folder. Check the response is complete, player IDs are unique, and each player's 2026 first-half plus second-half K, BB, and BF equals the official 2026 full-season total. Check the same additivity for 2025 before using its prior rates. If any check fails, investigate before scoring; do not alter the prediction or thresholds to improve the result. Run the final test once and preserve the output and code.

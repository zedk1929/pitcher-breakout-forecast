# Plan set before the next model screen

The question is whether one first-half pitch trait improves July-onward K-BB% prediction beyond a calibrated 100-BF shrinkage baseline. All outcomes and K-BB rates use official MLB player totals; pitch traits use June-30 Statcast data. Pitchers must have at least 100 BF in each half to be scored.

**Candidate models:** calibrated baseline alone, or calibrated baseline plus exactly one of `swinging_strike_rate`, `primary_fastball_speed_mph`, `breaking_share`, or `primary_fastball_pfx_z_inches`. Each trait gets a single linear slope fitted to the training residuals. We are not trying multiple weights, feature transformations, or interactions in this screen.

**Forward checks:** train on 2022 and score 2023; then train on 2022–23 and score 2024. Every candidate is compared on the same pitchers in each validation season. The choice is based only on these 2023 and 2024 results.

**Choice rule:** Keep the calibrated baseline unless one trait improves mean absolute error (MAE) in **both** forward checks and improves pooled 2023–24 MAE by at least **0.05 percentage points**. If several qualify, choose the one with the lowest pooled MAE; break a tie by the candidate order above. This practical threshold is a prespecified guard against chasing tiny validation differences, not a claim of statistical significance.

After choosing, refit that one model on all 2022–24 data and inspect its 2025 development score. Do not change the choice based on 2025. Freeze the code and choice before the separate 2026 final test. The 2025 score has already been seen for the swinging-strike candidate, so it is not untouched evidence.

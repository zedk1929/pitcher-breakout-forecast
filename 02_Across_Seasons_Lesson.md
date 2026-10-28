# Lesson 2: Does the baseline hold up across seasons?

## What we are testing

The null baseline predicts the same **first-half league K-BB%** for every pitcher. The next baseline predicts that each pitcher's first-half K-BB% will continue unchanged. The shrinkage baseline blends that pitcher rate with the same season's **first-half** league K-BB%, using an illustrative weight of 100 batters faced. All three predictions use only information available through June 30. We measure their absolute errors against July-onward K-BB%.

The key question is whether the shrinkage result we saw in 2025 appears in 2022, 2023, and 2024 too. We are not changing the 100-BF weight after seeing a season's score. MAE is an unweighted average across pitchers who have at least 100 BF in each half; it is not an average over all pitches or all June 30 eligible pitchers. The calculation now uses saved official MLB player-level K, BB, and BF totals for both halves.

## Your steps

1. Before running anything, write down your guess: will shrinkage have a lower mean absolute error (MAE) in every season?
2. In Terminal, go to this project folder and run `python3 evaluate_baselines_by_year.py`.
3. Open `baseline_comparison_2022_2025.csv`. Each row is a season. `league_only_mae_pp`, `unchanged_mae_pp`, and `shrunk_100bf_mae_pp` are errors in **percentage points**; smaller is better.
4. Compare the sign and size of `shrinkage_improvement_pp` across years. A positive number means shrinkage made the average error smaller for pitchers who met the sample-size thresholds.
5. Look at `first_half_eligible` versus `both_halves_evaluable` again. The MAE describes only the latter group.

## Questions to explain in your own words

- Did the same fixed shrinkage rule help in all four seasons? By how much?
- Does knowing a pitcher's own first-half rate help compared with predicting the league rate for everyone?
- Why is the first-half league average allowed in a June 30 prediction, while the full-season league average would be lookahead bias?
- If we try many weights and keep the one that performs best on 2025, can we still call the 2025 score an untouched test result?
- What does a lower MAE **not** tell us about predicting a pitcher's future playing time?

## Where this leads

After you can explain this table, we will decide how to select a shrinkage weight using earlier seasons, then add a small set of pitch-characteristic features. The final 2026 season remains reserved for a later test.

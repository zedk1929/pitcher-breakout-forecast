# Which Pitcher Breakouts Will Last?

**Question:** On June 30, can we predict an MLB pitcher's July-onward strikeout-minus-walk rate (K-BB%) more accurately than simply carrying his first-half rate forward?

**Short answer:** Yes, on the 2026 holdout, a simple prediction that pulls the first-half rate toward the league rate performed better. The frozen, calibrated version had a mean absolute error (MAE) of **4.431 percentage points**, versus **5.058** for carrying the first-half rate forward, among **275** pitchers with at least 100 batters faced (BF) in each half. Plain shrinkage scored **4.418** points, slightly better than the frozen calibrated version. The pitch traits tested in development did not meet the preset rule for adding them. This project does **not** show that a specific pitch change caused a breakout.

## Start here

1. Read [the final 2026 results](10_Final_2026_Test_Results.md) for the findings, sample, examples, and limitations.
2. Read [the frozen test protocol](09_Frozen_2026_Protocol.md) to see what was decided before the 2026 outcomes were fetched.
3. Inspect [the per-pitcher predictions](frozen_2026_predictions.csv) and [the machine-readable scores](frozen_2026_results.json).
4. To follow the learning path, start with [the first baseline lesson](01_Baseline_Lesson.md), then read the numbered lessons in order.
5. For a presentation-ready example, read [the five-pitcher scouting report](11_Pitcher_Scouting_Report.md) and view [the 2026 model comparison chart](2026_model_comparison.svg).

## Method in plain language

K-BB% is `(strikeouts - walks) / batters faced`. A June 30 first-half rate can be noisy, especially with fewer batters faced. The main baseline adds the equivalent of **100 league-average BF** to each pitcher's first-half record before predicting July onward. The frozen version also adds a constant learned from 2022–24. Its full formula and eligibility rules are in [the protocol](09_Frozen_2026_Protocol.md).

Pitch-level Statcast data from 2022–25 were used for feature work. Official MLB player pitching totals supplied the historical K-BB% comparisons and the 2026 final outcome. The model selection plan used earlier years for training and forward checks, tested pitch traits against shrinkage, and reserved 2026 for a final test. See [the selection plan](07_Model_Selection_Plan.md), [forward-check lesson](08_Forward_Model_Check_Lesson.md), and [data audit](Statcast_Data_Check.md).

| Same 275 pitchers in 2026 | MAE, percentage points |
|---|---:|
| Carry first-half K-BB% forward | 5.058 |
| Give everyone the first-half league rate | 5.192 |
| 100-BF shrinkage | **4.418** |
| Frozen calibrated 100-BF shrinkage | 4.431 |

The frozen model was **0.013 points worse** than plain shrinkage on MAE. A paired bootstrap interval for its improvement over plain shrinkage spans zero (−0.089 to +0.065 points). There is no supported claim here that the calibration or tested pitch traits beat plain shrinkage. Of 382 pitchers eligible on June 30, only 275 reached the 100-BF July threshold; the score does not cover the other 107.

## Reproduce the final check

The project uses Python's standard library. With the saved official MLB responses already in `data/`, run this from the project folder:

```sh
python3 evaluate_frozen_2026.py
```

The script checks the frozen model artifact, reconciles half-season and full-season official totals, and verifies that regenerated outputs match the saved `frozen_2026_predictions.csv` and `frozen_2026_results.json`. It refuses to overwrite differing final outputs. The original first run used `python3 evaluate_frozen_2026.py --download` to fetch missing official responses; rerunning from the saved inputs does not require a download.

Rebuild the vector chart from the saved final scores with `python3 make_2026_results_chart.py`. The SVG is the editable, resolution-independent chart; `2026_model_comparison.png` is a preview.

The raw 2022–25 Statcast files are in `data/raw/` and take roughly 603 MB. The download scripts are [training years](download_training_statcast.py) and [2025](download_2025_statcast.py). The smaller derived files in the root show the feature and outcome tables. Source URLs and checks are recorded in the manifests and audit. No 2026 pitch-level Statcast download was needed for the selected final model.

## Sharing this project

The `.gitignore` keeps the 603 MB `data/raw/` archive, two root-level Statcast sample CSVs, and local Python cache files out of Git. Those files stay on this computer. The shareable repository includes the code, lessons, report, chart, derived CSVs, result JSON, manifests, and smaller cached official MLB responses. That makes the **final 2026 check runnable without a new download**. Regenerating the earlier pitch-level feature tables from scratch requires the raw Statcast downloads; use the included download scripts if you need to repeat that stage. External data availability may change.

## What the result means

The project provides a reproducible example of prediction with a time cutoff, simple baselines, forward model selection, and a frozen final test. It does not establish a permanent change in pitcher skill. Pitchers who lose playing time are less likely to enter the scored group, and K-BB% does not capture every part of pitching value. The 2026 result should remain a final test of this frozen approach; selecting a revised model using it would make 2026 development data for that new approach.

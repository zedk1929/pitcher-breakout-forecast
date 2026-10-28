# Lesson 6: Did swinging-strike rate improve the prediction?

We tested one pitch trait at a time. The outcome is **July-onward K-BB%**. Each model made its prediction using only information available by June 30.

1. **Shrinkage baseline:** blend each pitcher's June-30 K-BB% with that season's June-30 league rate using the fixed 100-BF weight from earlier lessons.
2. **Calibrated baseline:** add one constant to the shrinkage prediction. The constant is learned only from 2022–2024.
3. **Swinging-strike model:** add a term for the pitcher's June-30 swinging-strike rate to the calibrated baseline. The slope is learned only from 2022–2024.

The code is in `test_swinging_strike_model.py`. It uses 841 pitcher-seasons from 2022–2024 with at least 100 BF in both halves. The 2025 development check uses the **same 262 pitchers** for all three methods. The rate called `swinging_strike_rate` is misses divided by tracked pitches, **not** official whiff rate (misses divided by swings).

## Results

Mean absolute error (MAE) is in percentage points; lower is better.

| Method | 2022–24 training MAE | 2025 development MAE |
|---|---:|---:|
| Shrinkage baseline | 4.416 | 4.713 |
| Calibrated baseline | 4.405 | **4.639** |
| Calibrated + swinging-strike rate | **4.381** | 4.651 |

The fitted slope is positive: a pitcher with a swinging-strike rate one percentage point higher receives a predicted K-BB rate about **0.21 percentage points** higher, holding the baseline fixed. That is an association learned from the training seasons, not a causal effect.

The pitch trait lowered training error, but on 2025 it **increased MAE by about 0.013 percentage points relative to calibration alone**. A paired bootstrap over the 262 pitchers gives a 95% interval for the trait's MAE improvement of **−0.078 to +0.055 percentage points**. That interval includes zero. We do **not** have convincing evidence from this check that this single trait adds useful predictive accuracy beyond the calibrated baseline. It still beat the uncalibrated baseline, but the simpler calibration explains that gain.

The comparison is limited to pitchers who also faced at least 100 batters from July onward. It says nothing about predicting who stays healthy or keeps a roster spot. The interval reflects variation among these 2025 pitchers; it does not resolve selection effects or model search. This is a development check, not a final untouched test. The 2026 season remains reserved.

## Work with the results

Open `swinging_strike_predictions_2025.csv` and sort by `swing_model_abs_error`. Look at one pitcher where the pitch trait helps and one where it hurts. The summary and bootstrap result are saved in `swinging_strike_model_2025_summary.json`. Run `python3 test_swinging_strike_model.py` to reproduce both files; it uses saved local data and downloads nothing.

**Next:** Compare a small, predeclared set of other June-30 traits with the same calibrated baseline. Avoid selecting whichever looks best on 2025 and then calling 2025 an untouched test; only 2026 can serve that role after the model is frozen.

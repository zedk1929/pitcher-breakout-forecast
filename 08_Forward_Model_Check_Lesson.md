# Lesson 8: Did any pitch trait survive the forward checks?

The candidates and choice rule were recorded in `07_Model_Selection_Plan.md` **before** this screen ran. We fit each candidate on 2022 and predicted 2023; then fit on 2022–23 and predicted 2024. All candidates used the same pitchers and the same calibrated shrinkage baseline. The code and detailed scores are in `screen_pitch_traits.py` and `pitch_trait_forward_checks_2023_2024.csv`.

| Candidate | 2023 MAE | 2024 MAE | Pooled MAE |
|---|---:|---:|---:|
| Calibrated baseline | 4.438 | 4.645 | 4.541 |
| + Swinging-strike rate | 4.458 | 4.607 | 4.532 |
| + Primary fastball speed | 4.433 | 4.628 | 4.530 |
| + Breaking-ball share | 4.462 | 4.647 | 4.554 |
| + Raw primary-fastball vertical movement | **4.400** | **4.588** | **4.494** |

MAE is in percentage points; lower is better. The movement feature improved pooled MAE by **0.047 points** compared with calibration alone. It improved both validation seasons, but missed our preset **0.05-point** minimum. We keep the rule unchanged and select the **calibrated baseline**. This is a conservative decision, not proof that movement has no predictive value. Raw movement also differs by pitch type and is not adjusted relative to league norms, so its coefficient would need careful interpretation.

After this choice, the selected model was refit on 2022–24 and checked on 2025: **4.639-point MAE** among 262 evaluable pitchers. That was already the calibrated baseline's 2025 score; it is a development readout, not a new independent test. No unselected trait was scored on 2025 in this screen. The result and fitted parameters are saved in `selected_pitch_model_2025_summary.json`; player-level 2025 predictions are in `selected_pitch_model_predictions_2025.csv`.

## What the result means

- The simplest calibrated prediction remains the most defensible choice under the fixed rule.
- A better training score alone did not justify adding a trait.
- The near miss for movement is a useful research lead, but changing the threshold after seeing it would make the choice rule meaningless.
- These MAEs describe pitchers with at least 100 BF in both halves. The project still needs to study who lacks a July-onward outcome, ranking quality, and player-level cases.

Run `python3 screen_pitch_traits.py` from this folder to reproduce the screen without downloading anything. Before the final test, freeze the model code and define exactly how the 2026 cohort, predictions, and scoring will work. Then obtain 2026 data and score it once.

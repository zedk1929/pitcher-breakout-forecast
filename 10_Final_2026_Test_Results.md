# Final 2026 holdout: Which Pitcher Breakouts Will Last?

**Run date:** October 27, 2026. The 2026 MLB regular season ended September 27 ([MLB schedule](https://www.mlb.com/schedule/2026-09-27)). The model, eligibility rule, comparisons, and metrics were frozen in `09_Frozen_2026_Protocol.md` before 2026 totals were downloaded. The raw official MLB Stats API responses and the exact scored outputs are saved in this project folder. Re-running `python3 evaluate_frozen_2026.py` reproduced both final output files byte for byte without overwriting them.

## Decision and prediction

Earlier forward checks selected a **calibrated 100-BF shrinkage baseline**. For each pitcher with at least 100 batters faced by June 30, it blends his first-half K-BB% with the first-half league rate, then adds a fixed 0.668-percentage-point calibration learned from 2022–24. No 2026 second-half information or pitch traits were used in the prediction. The outcome is July-onward K-BB% from official MLB player totals.

Of **382** first-half-eligible pitchers, **275** faced at least 100 batters from July onward and could be scored. **107** did not meet that outcome threshold, including **22** with no July BF. All four methods below are scored on the same 275 pitchers. The 2025 and 2026 official half-season K, BB, and BF totals each reconciled exactly to their full-season player totals.

| Method | 2026 MAE (pp) | RMSE (pp) | Spearman rank correlation |
|---|---:|---:|---:|
| First-half rate unchanged | 5.058 | 6.398 | 0.476 |
| First-half league rate for everyone | 5.192 | 6.668 | Undefined (same prediction for all) |
| 100-BF shrinkage without calibration | **4.418** | 5.686 | **0.484** |
| Frozen calibrated shrinkage | 4.431 | **5.683** | **0.484** |

The frozen model improved MAE by **0.627 percentage points** versus carrying the first-half rate forward. It was **0.013 points worse** than plain shrinkage on MAE and 0.003 points better on RMSE. A paired bootstrap over the 275 pitchers put the frozen model's MAE improvement over plain shrinkage between **−0.089 and +0.065 points** (95% interval). This small difference is inconclusive. Adding a constant does not change the ranking, which is why the two shrinkage methods have the same Spearman correlation. The final test does not justify claiming that calibration or any pitch trait improved on plain shrinkage.

## Apparent breakouts

The frozen reporting rule called a pitcher an **apparent breakout** if he faced at least 100 batters in 2025 and by June 30, 2026, and his first-half 2026 K-BB% exceeded his full-season 2025 rate by at least 3 percentage points. There were **72** such pitchers. **60** had at least 100 July BF; **40 of those 60** finished July onward above their 2025 rate. The other 12 lack enough July playing time for this comparison.

“Above last year” is a lenient definition of persistence. In an additional descriptive check after the frozen test, only **23 of the 60** retained at least half of their June improvement. This check was not part of the prespecified scoring rule and should be treated as exploratory. It illustrates why a binary persistence label can hide substantial regression.

## Three pitcher examples

These are examples, not proof of a mechanism. Rates are K-BB%.

| Pitcher | 2025 full season | Through June 2026 | Frozen prediction for July onward | Actual July onward | What happened |
|---|---:|---:|---:|---:|---|
| Tanner Scott | 17.6% | 31.0% | 23.7% | 22.4% | Stayed above 2025; prediction missed by 1.3 points. |
| Bryce Miller | 10.2% | 30.1% | 24.3% | 9.9% | Early jump did not persist; prediction missed by 14.3 points. |
| Colin Holderman | 1.6% | 22.4% | 18.8% | 3.8% | Technically above 2025, but most of the June gain vanished; prediction missed by 15.0 points. |

## What this supports on a resume

This project built and audited multi-season MLB pitching data, fixed prediction cutoffs before outcomes, compared simple and pitch-trait models with forward validation, and tested a frozen choice on 2026. The strongest defensible finding is that **simple shrinkage substantially improved 2026 prediction accuracy over assuming first-half performance would continue unchanged**. The tested pitch traits did not clear the preset selection rule, and calibration did not meaningfully beat uncalibrated shrinkage on the final MAE.

## Limits and reproducibility

The MAE applies only to pitchers with at least 100 BF in both halves. Health, role changes, and roster decisions affect who has an observable July outcome. A K-BB% difference does not establish why it occurred. The project measured future rate accuracy and rank correlation, not the value of a baseball transaction. Further models may be explored, but 2026 must remain the final test of the frozen approach reported here; it cannot also be used to choose a revised model and still be called untouched.

- Frozen protocol: `09_Frozen_2026_Protocol.md`
- Final code: `evaluate_frozen_2026.py`
- Per-pitcher predictions and outcomes: `frozen_2026_predictions.csv`
- Scores, uncertainty, cohort counts, and source URLs: `frozen_2026_results.json`

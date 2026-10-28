# Lesson 1: Can a first-half rate predict the second half?

## The idea

Our **unit of analysis** is one pitcher in one season. For each pitcher, we make a prediction using information available by June 30, then compare it with July-onward performance. The target is K-BB%: `(strikeouts - walks) / batters faced`.

This is a 2025 practice run to learn the evaluation method. The final project will train on earlier seasons and reserve a later season for a proper holdout test.

## Try it yourself before running the script

Open `pitcher_splits_2025.csv` and find Justin Verlander. Calculate:

1. First-half K-BB% from 55 strikeouts, 25 walks, and 294 batters faced.
2. Second-half K-BB% from 82 strikeouts, 27 walks, and 368 batters faced.
3. The **absolute error** if your prediction is simply the first-half rate: `abs(prediction - actual)`.

Your answers should be about 10.20%, 14.95%, and 4.74 percentage points. The error is measured in percentage **points**, because it is the difference between two percentages.

## Run the same calculation for every eligible pitcher

In Terminal, go to the baseball project folder and run `python3 baseline_2025.py`. The script reads the saved official MLB player-level first- and second-half totals in `data/` and writes `baseline_predictions_2025.csv` in this same folder. It uses no new downloads or external packages. The example counts above match those official totals.

The script keeps pitchers with at least 100 batters faced in the first half and at least 100 in the second half. It reports **mean absolute error (MAE)**: the average of each pitcher's absolute error. A smaller MAE means the predictions are closer to the observed rates.

The second baseline pulls each first-half rate toward the first-half league average. It treats 100 batters faced at the league rate as a simple, illustrative prior. That number is **not tuned or validated** yet. Notice that the prediction only uses first-half information; second-half data appears only when scoring it.

## Questions to answer in your own words

1. Why is it unfair to use July statistics when making a June 30 prediction?
2. Why might a pitcher's first-half rate be less reliable with 100 BF than with 400 BF?
3. Why do we report how many first-half-eligible pitchers lack enough second-half playing time?
4. Does a lower 2025 MAE prove the shrinkage rule will work in a future season? Why or why not?

## What comes next

After you can explain these results, we will download earlier seasons **into this same project folder**, build one pitcher-season row per year, and compare baselines across years. Then we will add pitch characteristics and test whether they improve predictions over the simple baselines.

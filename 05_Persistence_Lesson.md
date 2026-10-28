# Lesson 5: Did the apparent improvement last?

The June 30 comparison and July-onward outcome live in separate files:

- `prior_season_comparison_2022_2025.csv` contains only prior-season and June-30 information.
- `second_half_outcomes_2022_2025.csv` contains July-onward results from the [official MLB Stats API](https://statsapi.mlb.com/api/v1/stats?stats=byDateRange&group=pitching&season=2022&sportIds=1&playerPool=ALL&gameType=R&startDate=2022-07-01&endDate=2022-12-31&limit=2000).

Match rows using both `season` and `pitcher_id`. The outcome rate is `(second_k - second_bb) / second_bf`. We consider a pitcher evaluable when he faced at least 100 batters after June 30. This excludes some June-30-eligible pitchers; they may differ from those who kept pitching, so any measured accuracy applies only to the evaluable group.

## Your problems

1. Find Kenley Jansen's 2022 row in each file. Compare his 2021, first-half 2022, and July-onward 2022 K-BB rates. Did the early increase persist? Say what the data show without claiming to know the cause.
2. Find a row with `evaluable_100_bf = 0`. Why can't we treat its missing or noisy July outcome as evidence that the pitcher regressed?
3. Imagine a model uses `second_kbb_rate` as an input to predict that same rate. What would be wrong with its evaluation?

## Rebuild

Run `python3 build_second_half_outcomes.py --download` from this project folder. Later runs can omit `--download` and use the saved official data. The script does not touch 2026.

**Next:** The baseline and feature calculations now use official player-level K-BB attribution. Fit and compare a small model with the shrinkage baseline. The July table is for evaluation, never for June-30 features. The original `pitcher_splits_<year>.csv` files remain as event-derived Statcast inspection artifacts and can differ by a BF and walk for a few pitchers after a mid-at-bat pitching change.

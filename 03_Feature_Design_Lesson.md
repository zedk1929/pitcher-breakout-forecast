# Lesson 3: Build a June 30 pitcher profile

## The job

Our model will make a prediction at the end of June 30. A **feature** is a number available at that moment that might help make the prediction. `first_half_features_2022_2025.csv` has one row per pitcher-season with at least 100 first-half batters faced. It contains 1,489 rows across 2022–2025. The later outcome remains in the separate `pitcher_splits_<year>.csv` files.

The source columns and units are described in [Baseball Savant's CSV documentation](https://baseballsavant.mlb.com/csv-docs). For a quick picture of how Statcast collects information, watch MLB's [1-minute-25-second Statcast technology video](https://www.mlb.com/video/learn-about-statcast).

## What the first features mean

| Column | Meaning |
|---|---|
| `first_kbb_rate` | First-half `(strikeouts - walks) / batters faced` from official MLB player totals; our established performance baseline. |
| `swinging_strike_rate` | Pitches described as `swinging_strike` or `swinging_strike_blocked`, divided by pitches with a known pitch type. This is **not** official whiff rate, whose denominator is swings. |
| `fastball_share` | Share of tracked pitches labeled FF, SI, FC, or FA. This is a project-defined pitch family. |
| `breaking_share` | Share of tracked pitches labeled SL, ST, SV, CU, or KC. This is a project-defined pitch family. |
| `primary_fastball_type` | The most common first-half fastball type among FF, SI, FC, and FA. |
| `primary_fastball_speed_mph` | Average release speed of that one primary fastball type, in mph. |
| `primary_fastball_pfx_z_inches` | Average raw `pfx_z` of that same pitch type, converted from feet to inches. It is not an MLB leaderboard movement-above-average statistic. |

`tracked_pitches` excludes rows with no pitch type. The four seasons each have less than half a percent of first-half rows missing pitch type, release speed, or `pfx_z`. Every eligible pitcher threw at least 20 pitches of his primary fastball type and has nonmissing speed and movement averages. The detailed counts are in `data/first_half_feature_audit.json`.

## Your problems

1. Find Justin Verlander's **2022** row. His `swinging_strike_rate` is about 0.113 and he has 1,414 tracked pitches. About how many pitches were swinging strikes? Why should we **not** call 0.113 his whiff rate?
2. Which of these can be used for a June 30 prediction: (a) average release speed through June 30, (b) full-season pitch mix, (c) the CSV column `pitcher_days_until_next_game`? Explain your choices. Hint: some values in (c) can reveal what happened after June 30.
3. A pitcher changes from mostly fastballs to mostly breaking balls. Why might his average velocity across **all** pitches fall even if each individual pitch type is thrown at the same speed? How does `primary_fastball_speed_mph` help?

## Rebuild the table

From this project folder, run `python3 build_first_half_features.py`. Pitch traits use only pitches dated on or before June 30; first-half K-BB% uses official player totals through that same date. We have not fitted a model or claimed that these features improve accuracy yet. The prior-season comparison table now measures apparent improvements; we still need to test whether these pitch measurements add predictive value beyond the shrinkage baseline.

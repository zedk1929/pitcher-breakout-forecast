# Statcast data check

## June 30 feature audit

`build_first_half_features.py` creates `first_half_features_2022_2025.csv` from pitches dated on or before June 30 and saves `data/first_half_feature_audit.json`. The table contains 1,489 eligible pitcher-season rows: 348, 381, 387, and 373 for 2022–2025. Its first-half pitch totals match the existing pitcher split summaries. For each season, fewer than 0.5% of first-half pitch rows lack pitch type, release speed, or `pfx_z`; every eligible pitcher threw at least 20 pitches of a primary fastball type and has nonmissing speed and movement averages. `03_Feature_Design_Lesson.md` defines the features and their limitations. No second-half outcome is included in the feature table.

## Earlier training seasons: 2022–2024

The 2022, 2023, and 2024 MLB regular-season Statcast CSVs are downloaded as compressed batches under `data/raw/<year>/`. These are the seasons intended for training; 2025 remains the model-selection season, and 2026 remains untouched for final evaluation. The dates follow MLB's [2022 revised schedule](https://www.mlb.com/press-release/press-release-mlb-announces-revised-2022-regular-season-schedule), [2023 schedule](https://www.mlb.com/news/mlb-announces-2023-regular-season-game-times), and [2024 schedule](https://www.mlb.com/press-release/press-release-mlb-announces-2024-regular-season-schedule). The 2024 range includes the [September 30 Mets–Braves makeup doubleheader](https://www.mlb.com/press-release/press-release-tonight-s-and-tomorrow-s-braves-mets-games-postponed).

| Season | Date range | Batches | Pitch rows | Pitchers | First-half ≥100 BF | Both halves ≥100 BF |
|---|---|---:|---:|---:|---:|---:|
| 2022 | Apr 7–Oct 5 | 37 | 710,210 | 871 | 348 | 279 |
| 2023 | Mar 30–Oct 1 | 38 | 720,684 | 863 | 381 | 282 |
| 2024 | Mar 20–Sep 30 | 39 | 711,899 | 855 | 387 | 280 |

Each batch was checked for the required columns, regular-season game type, expected date range, duplicate pitch keys within the batch, and the Baseball Savant 25,000-row result cap. The largest batch has 22,367 rows. The manifests are `data/statcast_<year>_manifest.json`. There are no partial download files. The reproducible pitcher-level summaries are `pitcher_splits_2022.csv`, `pitcher_splits_2023.csv`, and `pitcher_splits_2024.csv`.

For each of the three seasons, event-derived strikeouts, walks, and batters faced match the [official MLB team pitching season statistics](https://statsapi.mlb.com/api/v1/teams/119/stats?stats=season&group=pitching&season=2024) for **all 30 teams**. The comparison reports are `data/season_reconciliation_<year>.json`. As in 2025, Statcast pitch rows exceed the official `numberOfPitches` total; the differences are 1,670 (2022), 2,739 (2023), and 2,387 (2024). We do not treat those counts as interchangeable.

Two source-specific details are recorded in the processing code rather than changing the raw CSVs:

- Baseball Savant labels the historical Oakland team `ATH`, whereas MLB's official 2022–2024 summaries use `OAK`. `reconcile_training_seasons.py` normalizes that team code for the comparison.
- In the May 28, 2022 Pirates–Padres game, the [official play-by-play](https://statsapi.mlb.com/api/v1/game/662280/playByPlay) records a hit-by-pitch at plate appearance 69. The corresponding Statcast pitch (game 662280, at-bat 69, pitch 5) has `description=hit_by_pitch` but a blank `events` value. `reconcile_training_seasons.py` and `build_training_pitcher_splits.py` count that one documented plate appearance in BF. Without the correction, San Diego's 2022 BF total is short by one. K and BB are unaffected.

These checks support the outcome counts at team level. They do not yet validate every pitch-characteristic feature or eliminate the selection issue created by pitchers with little second-half playing time.

Rebuild or recheck from this folder:

```bash
python3 download_training_statcast.py 2022 2023 2024
python3 reconcile_training_seasons.py 2022 2023 2024
python3 build_training_pitcher_splits.py 2022 2023 2024
```

## Full 2025 season

The complete 2025 MLB regular season has been downloaded from March 18 through September 28, including the Tokyo opening games and the final day of the season ([MLB schedule](https://www.mlb.com/press-release/press-release-mlb-announces-2025-regular-season-schedule)). The data is stored in 39 compressed CSV batches under `data/raw/2025/`; the manifest is `data/statcast_2025_manifest.json`. The batches contain **712,528 Statcast pitch rows**. Each batch was checked for required fields, regular-season status, date range, duplicate pitch keys, and the 25,000-row download cap.

The 2025 pitcher summary is `pitcher_splits_2025.csv` in this folder. It contains 873 pitchers. With a provisional threshold of at least 100 batters faced by June 30, 373 pitchers qualify; 262 also have at least 100 batters faced from July 1 onward. Of the other 111, 26 have no second-half batters faced and 85 have 1–99. This loss of pitchers is a selection issue for later modeling, not evidence that their performance worsened.

### Official-total check

`reconcile_2025_season.py` compares the Statcast event totals with [MLB team pitching statistics](https://statsapi.mlb.com/api/v1/teams/119/stats?stats=season&group=pitching&season=2025) for all 30 teams. Strikeouts (**40,645**), walks (**15,379**), and batters faced (**182,926**) match exactly for every team. MLB's `numberOfPitches` total is 710,084 while the Statcast CSV has 712,528 rows; the two counts are therefore not interchangeable. The detailed differences are saved in `data/season_reconciliation_2025.json`.

This verifies the K-BB% outcome counts for 2025 at team level. It does not validate the pitch-shape features or prove every row is complete. The earlier training seasons are documented above. The next modeling step is to define features using only information available by June 30 and compare baselines across years before evaluating a fitted model. The separate 2026 test season remains held out.

## What was downloaded

Two pitch-level, regular-season CSVs were downloaded from [Baseball Savant Statcast Search](https://baseballsavant.mlb.com/statcast_search) and saved beside this note:

| Date | Pitches | Pitchers | Games | Missing velocity | Duplicate pitch keys |
|---|---:|---:|---:|---:|---:|
| April 1, 2025 | 3,704 | 113 | 13 | 13 (0.4%) | 0 |
| July 1, 2025 | 3,434 | 93 | 12 | 18 (0.5%) | 0 |

Both files have 119 columns. All fields required by the inspection script are present. The [Statcast CSV documentation](https://baseballsavant.mlb.com/csv-docs) defines the pitch-level fields used here.

## Outcome reconciliation

For all 25 games in these CSVs, recorded strikeout, walk, and batters-faced totals matched the corresponding MLB game box scores exactly: **430 strikeouts, 153 walks, and 1,802 batters faced; zero games with a mismatch.** The comparison counts `intent_walk` as a walk, `strikeout_double_play` as a strikeout, and excludes `truncated_pa` from batters faced. The reproducible comparison is in `reconcile_statcast_sample.py`.

This supports using the pitch-level records to construct K-BB% on these two dates. It does not establish that every season or date has complete coverage. The full-season pipeline should repeat this reconciliation and report missing or truncated plate appearances.

## Run the checks

From this folder:

```bash
python3 inspect_statcast_sample.py --csv statcast_2025-04-01.csv
python3 inspect_statcast_sample.py --csv statcast_2025-07-01.csv
python3 reconcile_statcast_sample.py statcast_2025-04-01.csv statcast_2025-07-01.csv
```

For a fresh 2025 download, run `python3 download_2025_statcast.py`. To rebuild the pitcher summary, run `python3 build_2025_pitcher_splits.py`. The sample checks above remain useful for debugging individual dates.

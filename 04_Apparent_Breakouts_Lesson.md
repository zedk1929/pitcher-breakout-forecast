# Lesson 4: What counts as an apparent breakout?

`prior_season_comparison_2022_2025.csv` compares a pitcher's **previous full regular season** with his current season **through June 30**. Both are known when the prediction is made. Both sets of K, BB, and BF totals come from the official MLB Stats API: [full-season example](https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching&season=2021&sportIds=1&playerPool=ALL&gameType=R&limit=2000) and [June 30 example](https://statsapi.mlb.com/api/v1/stats?stats=byDateRange&group=pitching&season=2022&sportIds=1&playerPool=ALL&gameType=R&startDate=2022-01-01&endDate=2022-06-30&limit=2000). The list of eligible pitcher IDs comes from our Statcast splits; the script confirms each still meets the 100-BF cutoff in the official totals.

Each row has at least 100 first-half batters faced. `change_pp` is first-half K-BB% minus prior-season K-BB%, in **percentage points**. For example, 18% minus 12% is +6 points. We calculate that comparison only when the pitcher also faced at least 100 batters in the prior season. The raw `prior_kbb_rate` is still shown for smaller prior-season samples; it can be very noisy. A blank `change_pp` means the prior sample failed our comparison cutoff or there were no prior-year MLB stats. It does not mean zero improvement. We have **not** chosen a breakout threshold yet.

More batters faced makes a measured rate less noisy. But batters faced also reflects role, health, innings, and team decisions; it is not a pure measure of pitcher quality. The table says which pitchers *appear* to improve, not which improvements will last.

## Your problems

1. Open the CSV and find a pitcher with a positive `change_pp`. Calculate it from the two rate columns. Explain why the unit is percentage points.
2. Find a pitcher with a blank `change_pp`. Use `prior_bf` and `prior_eligible_100_bf` to explain why it is blank. Do you think removing these pitchers from a portfolio analysis could hide an interesting group?
3. The CSV has no July-onward rate. Why is that useful for a table meant to represent what we knew on June 30? Where in this project is the July-onward outcome stored?

## Rebuild

From this project folder, run `python3 build_prior_season_comparison.py --download`. This downloads the official prior-year and June-30 player totals into this folder's `data/` directory. Later runs can omit `--download` and use those local files. The script checks that MLB returned the complete, unique player list for each period.

**Data-quality note:** Statcast records the pitcher who threw the final pitch of a walk, but MLB can charge the walk and batter faced to the preceding pitcher after a mid-at-bat pitching change ([Official Baseball Rules, Rule 9.16(h)](https://content.mlb.com/documents/2/2/4/305750224/2019_Official_Baseball_Rules_FINAL_.pdf)). This affects a small number of player-level rows even though our team totals reconcile. This table uses official player totals for the K-BB comparison. Before modeling, align the existing Statcast-based split and feature tables with official pitcher-level attribution and recheck the baselines.

**Next:** Inspect the distribution of `change_pp`, then set a transparent rule for reporting apparent breakouts. Model evaluation should still use the continuous change and compare against the existing shrinkage baseline. Keep 2026 untouched for the final holdout.

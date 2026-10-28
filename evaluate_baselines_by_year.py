"""Compare fixed, June-30-safe K-BB% baselines across 2022-2025.

Run: python3 evaluate_baselines_by_year.py
This is an exploratory comparison, not the final 2026 holdout evaluation.
"""

import csv
from pathlib import Path
from statistics import mean

from official_pitching_totals import load_half


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "baseline_comparison_2022_2025.csv"
YEARS = (2022, 2023, 2024, 2025)
MIN_BF = 100
PRIOR_BF = 100  # Fixed illustrative choice; not optimized on these results.


def evaluate(year):
    first = load_half(year, "first_half")
    second = load_half(year, "second_half")

    first_bf_total = sum(p["bf"] for p in first.values())
    first_net_k_total = sum(p["k"] - p["bb"] for p in first.values())
    league_rate = first_net_k_total / first_bf_total

    eligible = [(pid, p) for pid, p in first.items() if p["bf"] >= MIN_BF]
    evaluable = [(pid, p, second[pid]) for pid, p in eligible
                 if pid in second and second[pid]["bf"] >= MIN_BF]
    league_only_errors = []
    unchanged_errors = []
    shrunk_errors = []
    for _, p, later in evaluable:
        first_bf = p["bf"]
        first_net_k = p["k"] - p["bb"]
        second_bf = later["bf"]
        second_net_k = later["k"] - later["bb"]

        actual = second_net_k / second_bf
        unchanged = first_net_k / first_bf
        shrunk = (first_net_k + PRIOR_BF * league_rate) / (first_bf + PRIOR_BF)
        league_only_errors.append(abs(league_rate - actual))
        unchanged_errors.append(abs(unchanged - actual))
        shrunk_errors.append(abs(shrunk - actual))

    if not evaluable:
        raise ValueError(f"No evaluable pitchers in {year}")
    league_only_mae_pp = 100 * mean(league_only_errors)
    unchanged_mae_pp = 100 * mean(unchanged_errors)
    shrunk_mae_pp = 100 * mean(shrunk_errors)
    return {
        "season": year,
        "pitchers": len(set(first) | set(second)),
        "first_half_eligible": len(eligible),
        "both_halves_evaluable": len(evaluable),
        "not_evaluable": len(eligible) - len(evaluable),
        "first_half_league_kbb_pct": f"{100 * league_rate:.3f}",
        "league_only_mae_pp": f"{league_only_mae_pp:.3f}",
        "unchanged_mae_pp": f"{unchanged_mae_pp:.3f}",
        "shrunk_100bf_mae_pp": f"{shrunk_mae_pp:.3f}",
        "shrinkage_improvement_pp": f"{unchanged_mae_pp - shrunk_mae_pp:.3f}",
    }


def main():
    results = [evaluate(year) for year in YEARS]
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("year  eligible  evaluable  league MAE  unchanged MAE  shrinkage MAE  improvement")
    for r in results:
        print(f"{r['season']}  {r['first_half_eligible']:>8}  {r['both_halves_evaluable']:>9}  "
              f"{r['league_only_mae_pp']:>9} pp  {r['unchanged_mae_pp']:>11} pp  "
              f"{r['shrunk_100bf_mae_pp']:>11} pp  "
              f"{r['shrinkage_improvement_pp']:>10} pp")
    print(f"Saved {OUT.name}")


if __name__ == "__main__":
    main()

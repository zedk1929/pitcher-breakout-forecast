"""Test one June-30 pitch trait against a K-BB% shrinkage baseline.

Fit on 2022-2024; evaluate once on 2025 as a development check.
No 2026 data are read. Uses only the Python standard library.
"""

import csv
import json
import math
import random
from pathlib import Path
from statistics import mean

from official_pitching_totals import load_half


ROOT = Path(__file__).resolve().parent
TRAIN_YEARS = (2022, 2023, 2024)
DEV_YEAR = 2025
MIN_BF = 100
SHRINK_BF = 100  # The same illustrative weight used in earlier lessons.


def read_keyed(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    result = {(int(row["season"]), row["pitcher_id"]): row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f"Duplicate season/pitcher keys in {name}")
    return result


def league_rates():
    result = {}
    for year in (*TRAIN_YEARS, DEV_YEAR):
        first = load_half(year, "first_half")
        bf = sum(p["bf"] for p in first.values())
        net_k = sum(p["k"] - p["bb"] for p in first.values())
        result[year] = net_k / bf
    return result


def make_rows():
    features = read_keyed("first_half_features_2022_2025.csv")
    first = read_keyed("prior_season_comparison_2022_2025.csv")
    second = read_keyed("second_half_outcomes_2022_2025.csv")
    if features.keys() != first.keys() or first.keys() != second.keys():
        raise ValueError("Feature, June-30, and outcome tables have different pitcher-season keys")
    league = league_rates()
    result = []
    for (year, pitcher_id), f in sorted(features.items()):
        p = first[(year, pitcher_id)]
        s = second[(year, pitcher_id)]
        if f["first_bf"] != p["first_bf"] or f["first_kbb_rate"] != p["first_kbb_rate"]:
            raise ValueError(f"June-30 totals disagree for {year} {pitcher_id}")
        if int(s["second_bf"]) < MIN_BF:
            continue
        first_bf = int(p["first_bf"])
        net_k = int(p["first_k"]) - int(p["first_bb"])
        baseline = (net_k + SHRINK_BF * league[year]) / (first_bf + SHRINK_BF)
        second_bf = int(s["second_bf"])
        actual = (int(s["second_k"]) - int(s["second_bb"])) / second_bf
        result.append({
            "season": year,
            "pitcher_id": pitcher_id,
            "pitcher_name": f["pitcher_name"],
            "first_bf": first_bf,
            "second_bf": second_bf,
            "swinging_strike_rate": float(f["swinging_strike_rate"]),
            "baseline": baseline,
            "actual": actual,
        })
    return result


def score(rows, field):
    errors = [row[field] - row["actual"] for row in rows]
    return {
        "mae_pp": round(100 * mean(abs(e) for e in errors), 3),
        "rmse_pp": round(100 * math.sqrt(mean(e * e for e in errors)), 3),
    }


def paired_bootstrap_improvement(rows, simpler, added, draws=10000, seed=2025):
    """Positive values mean the added model lowers MAE on the same pitchers."""
    differences = [abs(r[simpler] - r["actual"]) - abs(r[added] - r["actual"]) for r in rows]
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        samples.append(100 * mean(rng.choices(differences, k=len(differences))))
    samples.sort()
    return {
        "mae_improvement_pp": round(100 * mean(differences), 3),
        "paired_bootstrap_95pct_interval_pp": [round(samples[int(0.025 * draws)], 3),
                                                 round(samples[int(0.975 * draws)], 3)],
        "bootstrap_draws": draws,
        "seed": seed,
    }


def main():
    rows = make_rows()
    train = [r for r in rows if r["season"] in TRAIN_YEARS]
    dev = [r for r in rows if r["season"] == DEV_YEAR]
    if len(train) < 100 or len(dev) < 100:
        raise ValueError("Unexpectedly small train or development cohort")

    # Fit July outcome minus the fixed shrinkage prediction using training only.
    x_mean = mean(r["swinging_strike_rate"] for r in train)
    residual_mean = mean(r["actual"] - r["baseline"] for r in train)
    variance = sum((r["swinging_strike_rate"] - x_mean) ** 2 for r in train)
    if variance == 0:
        raise ValueError("Swinging-strike rate has no training variation")
    slope = sum(
        (r["swinging_strike_rate"] - x_mean)
        * (r["actual"] - r["baseline"] - residual_mean)
        for r in train
    ) / variance

    for row in rows:
        row["calibrated"] = row["baseline"] + residual_mean
        row["swing_model"] = row["calibrated"] + slope * (row["swinging_strike_rate"] - x_mean)

    results = {
        "train_seasons": list(TRAIN_YEARS),
        "development_season": DEV_YEAR,
        "first_half_min_bf": MIN_BF,
        "second_half_min_bf": MIN_BF,
        "shrinkage_bf": SHRINK_BF,
        "train_pitchers": len(train),
        "development_pitchers": len(dev),
        "feature": "Statcast first-half swinging_strike_rate (misses / tracked pitches)",
        "mean_train_swinging_strike_rate": round(x_mean, 6),
        "mean_train_baseline_residual": round(residual_mean, 6),
        "slope": round(slope, 6),
        "training": {name: score(train, name) for name in ("baseline", "calibrated", "swing_model")},
        "development": {name: score(dev, name) for name in ("baseline", "calibrated", "swing_model")},
        "swinging_strike_increment_over_calibration": paired_bootstrap_improvement(
            dev, "calibrated", "swing_model"
        ),
    }
    (ROOT / "swinging_strike_model_2025_summary.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )

    fields = (
        "season", "pitcher_id", "pitcher_name", "first_bf", "second_bf",
        "swinging_strike_rate", "baseline", "calibrated", "swing_model", "actual",
        "baseline_abs_error", "calibrated_abs_error", "swing_model_abs_error",
    )
    with (ROOT / "swinging_strike_predictions_2025.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in dev:
            writer.writerow({
                **{key: row[key] for key in ("season", "pitcher_id", "pitcher_name", "first_bf", "second_bf")},
                **{key: f"{row[key]:.6f}" for key in ("swinging_strike_rate", "baseline", "calibrated", "swing_model", "actual")},
                **{f"{key}_abs_error": f"{abs(row[key] - row['actual']):.6f}" for key in ("baseline", "calibrated", "swing_model")},
            })

    print(f"Training: {len(train)} pitcher-seasons from 2022-2024")
    print(f"2025 development: {len(dev)} pitchers")
    print(f"Slope: {slope:.3f} K-BB rate units per swinging-strike-rate unit")
    for name, metrics in results["development"].items():
        print(f"2025 {name}: MAE {metrics['mae_pp']:.3f} pp; RMSE {metrics['rmse_pp']:.3f} pp")
    increment = results["swinging_strike_increment_over_calibration"]
    print(f"Swing feature's 2025 MAE improvement vs calibration: {increment['mae_improvement_pp']:+.3f} pp "
          f"(paired bootstrap 95% interval: {increment['paired_bootstrap_95pct_interval_pp']})")
    print("Saved swinging_strike_model_2025_summary.json and swinging_strike_predictions_2025.csv")


if __name__ == "__main__":
    main()

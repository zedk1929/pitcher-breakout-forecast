"""Choose one fixed pitch-trait model using forward 2023/2024 checks.

The plan and decision rule are recorded in 07_Model_Selection_Plan.md.
2025 is scored only after the 2023/2024-based choice. 2026 is not read.
"""

import csv
import json
import math
from pathlib import Path
from statistics import mean

from official_pitching_totals import load_half


ROOT = Path(__file__).resolve().parent
CANDIDATES = (
    "calibrated",
    "swinging_strike_rate",
    "primary_fastball_speed_mph",
    "breaking_share",
    "primary_fastball_pfx_z_inches",
)
MIN_BF = 100
SHRINK_BF = 100
MIN_POOLED_GAIN_PP = 0.05
FOLDS = ((2023, (2022,)), (2024, (2022, 2023)))


def read_keyed(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    keyed = {(int(row["season"]), row["pitcher_id"]): row for row in records}
    if len(keyed) != len(records):
        raise ValueError(f"Duplicate season/pitcher key in {path}")
    return keyed


def modeling_rows(years):
    features = read_keyed("first_half_features_2022_2025.csv")
    first = read_keyed("prior_season_comparison_2022_2025.csv")
    second = read_keyed("second_half_outcomes_2022_2025.csv")
    league = {}
    for year in years:
        all_first = load_half(year, "first_half")
        league[year] = sum(p["k"] - p["bb"] for p in all_first.values()) / sum(p["bf"] for p in all_first.values())
    rows = []
    for (year, pitcher_id), f in sorted(features.items()):
        if year not in years:
            continue
        p = first[(year, pitcher_id)]
        s = second[(year, pitcher_id)]
        if f["first_bf"] != p["first_bf"] or f["first_kbb_rate"] != p["first_kbb_rate"]:
            raise ValueError(f"June-30 totals disagree for {year} {pitcher_id}")
        if int(s["second_bf"]) < MIN_BF:
            continue
        if int(p["first_bf"]) < MIN_BF:
            raise ValueError(f"First-half BF below threshold for {year} {pitcher_id}")
        trait_values = {name: float(f[name]) for name in CANDIDATES[1:]}
        if not all(math.isfinite(value) for value in trait_values.values()):
            raise ValueError(f"Nonfinite trait for {year} {pitcher_id}")
        bf = int(p["first_bf"])
        net_k = int(p["first_k"]) - int(p["first_bb"])
        second_bf = int(s["second_bf"])
        rows.append({
            "season": year,
            "pitcher_id": pitcher_id,
            "pitcher_name": f["pitcher_name"],
            "first_bf": bf,
            "second_bf": second_bf,
            "baseline": (net_k + SHRINK_BF * league[year]) / (bf + SHRINK_BF),
            "actual": (int(s["second_k"]) - int(s["second_bb"])) / second_bf,
            **trait_values,
        })
    return rows


def fit(rows, candidate):
    residual_mean = mean(row["actual"] - row["baseline"] for row in rows)
    if candidate == "calibrated":
        return {"residual_mean": residual_mean, "feature_mean": None, "slope": 0.0}
    x_mean = mean(row[candidate] for row in rows)
    spread = sum((row[candidate] - x_mean) ** 2 for row in rows)
    if spread == 0:
        raise ValueError(f"No training variation in {candidate}")
    slope = sum((row[candidate] - x_mean) * (row["actual"] - row["baseline"] - residual_mean)
                for row in rows) / spread
    return {"residual_mean": residual_mean, "feature_mean": x_mean, "slope": slope}


def predict(row, candidate, fitted):
    value = row["baseline"] + fitted["residual_mean"]
    if candidate != "calibrated":
        value += fitted["slope"] * (row[candidate] - fitted["feature_mean"])
    return value


def mae_pp(rows, candidate, fitted):
    return 100 * mean(abs(predict(row, candidate, fitted) - row["actual"]) for row in rows)


def main():
    # The decision reads only 2022-2024 data. Load 2025 only after selection.
    past = modeling_rows({2022, 2023, 2024})
    fold_rows = []
    for validation_year, training_years in FOLDS:
        train = [row for row in past if row["season"] in training_years]
        validation = [row for row in past if row["season"] == validation_year]
        for candidate in CANDIDATES:
            fitted = fit(train, candidate)
            fold_rows.append({
                "candidate": candidate,
                "train_years": "+".join(map(str, training_years)),
                "validation_year": validation_year,
                "train_pitchers": len(train),
                "validation_pitchers": len(validation),
                "mae_pp": mae_pp(validation, candidate, fitted),
                "absolute_errors": [abs(predict(row, candidate, fitted) - row["actual"]) for row in validation],
            })

    def pooled_mae(candidate):
        errors = [error for fold in fold_rows if fold["candidate"] == candidate
                  for error in fold["absolute_errors"]]
        return 100 * mean(errors)

    calibrated = {fold["validation_year"]: fold["mae_pp"]
                  for fold in fold_rows if fold["candidate"] == "calibrated"}
    baseline_pooled = pooled_mae("calibrated")
    eligible_traits = []
    for candidate in CANDIDATES[1:]:
        by_year = {fold["validation_year"]: fold["mae_pp"]
                   for fold in fold_rows if fold["candidate"] == candidate}
        if (all(by_year[year] < calibrated[year] for year, _ in FOLDS)
                and baseline_pooled - pooled_mae(candidate) >= MIN_POOLED_GAIN_PP):
            eligible_traits.append(candidate)
    selected = min(eligible_traits, key=lambda name: (pooled_mae(name), CANDIDATES.index(name))) \
        if eligible_traits else "calibrated"

    cv_path = ROOT / "pitch_trait_forward_checks_2023_2024.csv"
    with cv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "candidate", "train_years", "validation_year", "train_pitchers",
            "validation_pitchers", "mae_pp", "pooled_2023_2024_mae_pp",
        ))
        writer.writeheader()
        for fold in fold_rows:
            writer.writerow({
                **{key: fold[key] for key in ("candidate", "train_years", "validation_year", "train_pitchers", "validation_pitchers")},
                "mae_pp": f"{fold['mae_pp']:.3f}",
                "pooled_2023_2024_mae_pp": f"{pooled_mae(fold['candidate']):.3f}",
            })

    # No candidate changes after this point. 2025 is a development readout.
    fitted = fit(past, selected)
    dev = modeling_rows({2025})
    dev_mae = mae_pp(dev, selected, fitted)
    calibrated_fitted = fit(past, "calibrated")
    calibrated_dev_mae = mae_pp(dev, "calibrated", calibrated_fitted)
    results = {
        "candidate_order": list(CANDIDATES),
        "choice_rule": "Improve 2023 and 2024 MAE and pooled MAE by at least 0.05 pp; otherwise calibrated baseline",
        "pooled_calibrated_mae_pp": round(baseline_pooled, 3),
        "pooled_candidate_mae_pp": {name: round(pooled_mae(name), 3) for name in CANDIDATES},
        "qualified_traits": eligible_traits,
        "selected": selected,
        "fit_years": [2022, 2023, 2024],
        "fit_pitcher_seasons": len(past),
        "fit_parameters": fitted,
        "development_year": 2025,
        "development_pitchers": len(dev),
        "development_calibrated_mae_pp": round(calibrated_dev_mae, 3),
        "development_selected_mae_pp": round(dev_mae, 3),
        "final_holdout_year": 2026,
        "final_holdout_evaluated": False,
    }
    (ROOT / "selected_pitch_model_2025_summary.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )

    pred_path = ROOT / "selected_pitch_model_predictions_2025.csv"
    with pred_path.open("w", newline="", encoding="utf-8") as handle:
        fields = ("season", "pitcher_id", "pitcher_name", "first_bf", "second_bf",
                  "calibrated_prediction", "selected_prediction", "actual", "selected_abs_error")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in dev:
            prediction = predict(row, selected, fitted)
            writer.writerow({
                "season": 2025,
                "pitcher_id": row["pitcher_id"],
                "pitcher_name": row["pitcher_name"],
                "first_bf": row["first_bf"],
                "second_bf": row["second_bf"],
                "calibrated_prediction": f"{predict(row, 'calibrated', calibrated_fitted):.6f}",
                "selected_prediction": f"{prediction:.6f}",
                "actual": f"{row['actual']:.6f}",
                "selected_abs_error": f"{abs(prediction - row['actual']):.6f}",
            })

    print("Forward validation MAE (percentage points):")
    for candidate in CANDIDATES:
        scores = [next(fold["mae_pp"] for fold in fold_rows
                       if fold["candidate"] == candidate and fold["validation_year"] == year)
                  for year, _ in FOLDS]
        print(f"  {candidate:34s} 2023 {scores[0]:.3f}  2024 {scores[1]:.3f}  pooled {pooled_mae(candidate):.3f}")
    print(f"Selected from 2023/2024 only: {selected}")
    print(f"2025 calibrated MAE {calibrated_dev_mae:.3f} pp; selected MAE {dev_mae:.3f} pp")
    print("Saved pitch_trait_forward_checks_2023_2024.csv and selected_pitch_model_2025_summary.json")


if __name__ == "__main__":
    main()

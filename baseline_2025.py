"""A learning baseline: predict July-onward K-BB% from data through June 30.

Run from any directory: python3 baseline_2025.py
Uses only the Python standard library. This is a 2025 pilot, not a final model.
"""

import csv
from pathlib import Path
from statistics import mean

from official_pitching_totals import load_half


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "baseline_predictions_2025.csv"
MIN_BF = 100
PRIOR_BF = 100  # Illustrative choice; do not treat this as a tuned setting.


def kbb_rate(strikeouts, walks, batters_faced):
    """A rate, such as 0.12 for 12%, using unrounded event counts."""
    return (strikeouts - walks) / batters_faced


def main():
    first = load_half(2025, "first_half")
    second = load_half(2025, "second_half")

    # The first-half league rate is known at the June 30 prediction cutoff.
    league_bf = sum(row["bf"] for row in first.values())
    league_net_k = sum(row["k"] - row["bb"] for row in first.values())
    league_rate = league_net_k / league_bf

    predictions = []
    unchanged_errors = []
    shrunk_errors = []
    eligible = 0
    no_second_half = 0
    for pitcher_id, row in sorted(first.items(), key=lambda pair: int(pair[0])):
        first_bf = row["bf"]
        if first_bf < MIN_BF:
            continue
        eligible += 1

        later = second.get(pitcher_id)
        second_bf = later["bf"] if later else 0
        if second_bf == 0:
            no_second_half += 1
        if second_bf < MIN_BF:
            continue

        first_net_k = row["k"] - row["bb"]
        first_rate = first_net_k / first_bf
        actual = kbb_rate(later["k"], later["bb"], second_bf)

        # Baseline 1: assume the first-half rate continues unchanged.
        unchanged = first_rate

        # Baseline 2: blend the pitcher's first-half record with 100
        # hypothetical batters faced at the first-half league rate.
        shrunk = (first_net_k + PRIOR_BF * league_rate) / (first_bf + PRIOR_BF)
        unchanged_errors.append(abs(unchanged - actual))
        shrunk_errors.append(abs(shrunk - actual))

        predictions.append({
            "pitcher_id": pitcher_id,
            "pitcher_name": row["pitcher_name"],
            "first_bf": first_bf,
            "second_bf": second_bf,
            "first_kbb_rate": f"{first_rate:.6f}",
            "second_kbb_rate": f"{actual:.6f}",
            "unchanged_prediction": f"{unchanged:.6f}",
            "shrunk_prediction": f"{shrunk:.6f}",
            "unchanged_absolute_error": f"{abs(unchanged - actual):.6f}",
            "shrunk_absolute_error": f"{abs(shrunk - actual):.6f}",
        })

    if not predictions:
        raise SystemExit("No pitchers meet both sample-size thresholds")

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=predictions[0].keys())
        writer.writeheader()
        writer.writerows(predictions)

    print(f"First-half league K-BB%: {100 * league_rate:.2f}%")
    print(f"First-half eligible (at least {MIN_BF} BF): {eligible}")
    print(f"Evaluable in both halves (at least {MIN_BF} BF each): {len(predictions)}")
    print(f"Eligible pitchers with no second-half BF: {no_second_half}")
    print(f"Unchanged-rate MAE: {100 * mean(unchanged_errors):.2f} percentage points")
    print(f"Illustrative shrinkage MAE: {100 * mean(shrunk_errors):.2f} percentage points")
    print(f"Saved {OUTPUT.name}")


if __name__ == "__main__":
    main()

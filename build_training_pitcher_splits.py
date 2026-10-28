"""Build one pitcher-season summary per downloaded training season.

Run after download and reconciliation:
python3 build_training_pitcher_splits.py 2022 2023 2024
"""

import argparse
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

from download_training_statcast import SEASONS, date_ranges


ROOT = Path(__file__).resolve().parent
MISSING_HBP = ("662280", "69", "5")  # 2022-05-28, verified in MLB game play-by-play.
FIELDS = [
    "season", "pitcher_id", "pitcher_name", "first_pitches", "first_bf",
    "first_k", "first_bb", "first_kbb_rate", "second_pitches",
    "second_bf", "second_k", "second_bb", "second_kbb_rate",
    "eligible_first_100_bf", "evaluable_second_100_bf",
]


def rate(numerator, denominator):
    return f"{numerator / denominator:.6f}" if denominator else ""


def run_year(year):
    manifest = json.loads((ROOT / "data" / f"statcast_{year}_manifest.json").read_text(encoding="utf-8"))
    expected = [(start.isoformat(), end.isoformat()) for start, end in date_ranges(year)]
    if [(batch["start"], batch["end"]) for batch in manifest] != expected:
        raise ValueError(f"{year} manifest is incomplete")

    pitchers = defaultdict(lambda: {
        "name": "", "first_pitches": 0, "first_bf": 0,
        "first_k": 0, "first_bb": 0, "second_pitches": 0,
        "second_bf": 0, "second_k": 0, "second_bb": 0,
    })
    for batch in manifest:
        with gzip.open(ROOT / batch["file"], "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                p = pitchers[row["pitcher"]]
                p["name"] = row["player_name"]
                half = "first" if row["game_date"] <= f"{year}-06-30" else "second"
                p[f"{half}_pitches"] += 1
                event = row["events"]
                missing_hbp = (row["game_pk"], row["at_bat_number"], row["pitch_number"]) == MISSING_HBP
                if missing_hbp and (row["description"] != "hit_by_pitch" or event):
                    raise ValueError("The documented 2022 HBP exception no longer matches the source row")
                if (event and event != "truncated_pa") or missing_hbp:
                    p[f"{half}_bf"] += 1
                    p[f"{half}_k"] += event in ("strikeout", "strikeout_double_play")
                    p[f"{half}_bb"] += event in ("walk", "intent_walk")

    output = ROOT / f"pitcher_splits_{year}.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for pitcher_id, p in sorted(pitchers.items(), key=lambda pair: int(pair[0])):
            writer.writerow({
                "season": year, "pitcher_id": pitcher_id, "pitcher_name": p["name"],
                "first_pitches": p["first_pitches"], "first_bf": p["first_bf"],
                "first_k": p["first_k"], "first_bb": p["first_bb"],
                "first_kbb_rate": rate(p["first_k"] - p["first_bb"], p["first_bf"]),
                "second_pitches": p["second_pitches"], "second_bf": p["second_bf"],
                "second_k": p["second_k"], "second_bb": p["second_bb"],
                "second_kbb_rate": rate(p["second_k"] - p["second_bb"], p["second_bf"]),
                "eligible_first_100_bf": int(p["first_bf"] >= 100),
                "evaluable_second_100_bf": int(p["second_bf"] >= 100),
            })
    print(f"{year}: {len(pitchers)} pitchers; "
          f"{sum(p['first_bf'] >= 100 for p in pitchers.values())} first-half eligible; "
          f"{sum(p['first_bf'] >= 100 and p['second_bf'] >= 100 for p in pitchers.values())} evaluable")
    print(f"Saved {output.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("years", type=int, nargs="+", choices=sorted(SEASONS))
    args = parser.parse_args()
    for year in args.years:
        run_year(year)


if __name__ == "__main__":
    main()

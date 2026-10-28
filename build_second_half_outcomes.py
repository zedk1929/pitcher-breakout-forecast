"""Build official July-onward K-BB% outcomes for June-30-eligible pitchers.

Run from this project folder:
    python3 build_second_half_outcomes.py --download

Keep this file separate from June-30 predictors to prevent lookahead leakage.
"""

import argparse
import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SEASONS = (2022, 2023, 2024, 2025)
MIN_BF = 100
FIELDS = (
    "season", "pitcher_id", "pitcher_name", "second_bf", "second_k",
    "second_bb", "second_kbb_rate", "evaluable_100_bf",
)


def source_url(year):
    query = urllib.parse.urlencode({
        "stats": "byDateRange", "group": "pitching", "season": year,
        "sportIds": 1, "playerPool": "ALL", "gameType": "R", "limit": 2000,
        "startDate": f"{year}-07-01", "endDate": f"{year}-12-31",
    })
    return f"https://statsapi.mlb.com/api/v1/stats?{query}"


def load_second_half(year, download=False):
    path = DATA / f"official_second_half_pitching_{year}.json"
    if download and not path.exists():
        with urllib.request.urlopen(source_url(year), timeout=60) as response:
            payload = json.load(response)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Downloaded {path.name}")
    if not path.exists():
        raise FileNotFoundError(f"Missing {path.name}; rerun with --download")
    payload = json.loads(path.read_text(encoding="utf-8"))
    blocks = payload.get("stats", [])
    if len(blocks) != 1:
        raise ValueError(f"Unexpected MLB response structure for {year}")
    block = blocks[0]
    splits = block.get("splits", [])
    if not splits or len(splits) != block.get("totalSplits"):
        raise ValueError(f"Incomplete MLB player totals for {year}")
    ids = [str(row["player"]["id"]) for row in splits]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate MLB player IDs for {year}")
    result = {}
    for row in splits:
        if int(row["season"]) != year:
            raise ValueError(f"Wrong season in {year} totals")
        stat = row["stat"]
        result[str(row["player"]["id"])] = {
            "bf": int(stat["battersFaced"]),
            "k": int(stat["strikeOuts"]),
            "bb": int(stat["baseOnBalls"]),
        }
    return result


def build(download=False):
    output = []
    for season in SEASONS:
        second_half = load_second_half(season, download)
        with (ROOT / "prior_season_comparison_2022_2025.csv").open(newline="", encoding="utf-8") as handle:
            cohort = [row for row in csv.DictReader(handle) if int(row["season"]) == season]
        for row in cohort:
            stat = second_half.get(row["pitcher_id"], {"bf": 0, "k": 0, "bb": 0})
            bf = stat["bf"]
            output.append({
                "season": season,
                "pitcher_id": row["pitcher_id"],
                "pitcher_name": row["pitcher_name"],
                "second_bf": bf,
                "second_k": stat["k"],
                "second_bb": stat["bb"],
                "second_kbb_rate": f"{(stat['k'] - stat['bb']) / bf:.6f}" if bf else "",
                "evaluable_100_bf": int(bf >= MIN_BF),
            })
        evaluable = sum(row["evaluable_100_bf"] for row in output if row["season"] == season)
        print(f"{season}: {len(cohort)} June-30 eligible; {evaluable} with at least {MIN_BF} July-onward BF")

    path = ROOT / "second_half_outcomes_2022_2025.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    print(f"Saved {path.name} ({len(output)} rows)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch missing official MLB July-onward totals")
    args = parser.parse_args()
    build(args.download)


if __name__ == "__main__":
    main()

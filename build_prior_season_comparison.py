"""Compare June 30 K-BB% with the previous full MLB regular season.

Run from this project folder:
    python3 build_prior_season_comparison.py --download

The generated table contains only information available by June 30 of each
season. July-onward outcomes remain in pitcher_splits_<season>.csv.
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
    "season", "pitcher_id", "pitcher_name", "prior_season", "prior_bf",
    "prior_k", "prior_bb", "prior_kbb_rate", "first_bf", "first_k",
    "first_bb", "first_kbb_rate", "change_pp", "prior_eligible_100_bf",
)


def source_url(year, first_half=False):
    query = urllib.parse.urlencode({
        "stats": "byDateRange" if first_half else "season", "group": "pitching", "season": year,
        "sportIds": 1, "playerPool": "ALL", "gameType": "R", "limit": 2000,
        **({"startDate": f"{year}-01-01", "endDate": f"{year}-06-30"} if first_half else {}),
    })
    return f"https://statsapi.mlb.com/api/v1/stats?{query}"


def stats_path(year, first_half=False):
    label = "first_half" if first_half else "player"
    return DATA / f"official_{label}_pitching_{year}.json"


def read_stats(year, first_half=False, download=False):
    path = stats_path(year, first_half)
    if download and not path.exists():
        with urllib.request.urlopen(source_url(year, first_half), timeout=60) as response:
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
    prior_by_year = {year: read_stats(year, download=download) for year in range(2021, 2025)}
    first_by_year = {year: read_stats(year, first_half=True, download=download) for year in SEASONS}
    output = []
    audit = []
    for season in SEASONS:
        with (ROOT / f"pitcher_splits_{season}.csv").open(newline="", encoding="utf-8") as handle:
            first_half = list(csv.DictReader(handle))
        eligible = [row for row in first_half if int(row["first_bf"]) >= MIN_BF]
        matched = 0
        comparable = 0
        for row in eligible:
            prior = prior_by_year[season - 1].get(row["pitcher_id"])
            first = first_by_year[season].get(row["pitcher_id"])
            if first is None or first["bf"] < MIN_BF:
                raise ValueError(f"Official June-30 eligibility does not match Statcast for {season} {row['pitcher_id']}")
            first_bf = first["bf"]
            first_k = first["k"]
            first_bb = first["bb"]
            first_rate = (first_k - first_bb) / first_bf
            prior_bf = prior["bf"] if prior else None
            prior_eligible = prior_bf is not None and prior_bf >= MIN_BF
            matched += prior is not None
            comparable += prior_eligible
            prior_rate = (prior["k"] - prior["bb"]) / prior_bf if prior_bf else None
            output.append({
                "season": season,
                "pitcher_id": row["pitcher_id"],
                "pitcher_name": row["pitcher_name"],
                "prior_season": season - 1,
                "prior_bf": prior_bf if prior else "",
                "prior_k": prior["k"] if prior else "",
                "prior_bb": prior["bb"] if prior else "",
                "prior_kbb_rate": f"{prior_rate:.6f}" if prior_rate is not None else "",
                "first_bf": first_bf,
                "first_k": first_k,
                "first_bb": first_bb,
                "first_kbb_rate": f"{first_rate:.6f}",
                "change_pp": f"{100 * (first_rate - prior_rate):.3f}" if prior_eligible else "",
                "prior_eligible_100_bf": int(prior_eligible),
            })
        audit.append((season, len(eligible), matched, comparable))

    path = ROOT / "prior_season_comparison_2022_2025.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    for season, eligible, matched, comparable in audit:
        print(f"{season}: {eligible} June-30 eligible; {matched} had prior-year MLB stats; "
              f"{comparable} had at least {MIN_BF} prior-year BF")
    print(f"Saved {path.name} ({len(output)} rows)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch missing official MLB prior-season totals")
    args = parser.parse_args()
    build(args.download)


if __name__ == "__main__":
    main()

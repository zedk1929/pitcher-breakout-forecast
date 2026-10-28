"""Check downloaded season K, BB, and BF against official MLB team totals.

Run: python3 reconcile_training_seasons.py 2022 2023 2024
Official summaries and reports are saved only in this project folder.
"""

import argparse
import csv
import gzip
import json
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from download_training_statcast import SEASONS, date_ranges


ROOT = Path(__file__).resolve().parent
MISSING_HBP = ("662280", "69", "5")  # 2022-05-28, verified in MLB game play-by-play.


def read_json(url):
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.load(response)


def official_teams(year):
    path = ROOT / "data" / f"official_team_pitching_{year}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    teams = read_json(f"https://statsapi.mlb.com/api/v1/teams?sportId=1&season={year}")["teams"]

    def fetch(team):
        url = f"https://statsapi.mlb.com/api/v1/teams/{team['id']}/stats?stats=season&group=pitching&season={year}"
        stats = read_json(url)["stats"][0]["splits"][0]["stat"]
        return team["abbreviation"], {
            "team": team["name"], "K": stats["strikeOuts"],
            "BB": stats["baseOnBalls"], "BF": stats["battersFaced"],
            "pitches": stats["numberOfPitches"],
        }

    with ThreadPoolExecutor(max_workers=5) as pool:
        official = dict(pool.map(fetch, teams))
    path.write_text(json.dumps(official, indent=2) + "\n", encoding="utf-8")
    return official


def run_year(year):
    manifest = json.loads((ROOT / "data" / f"statcast_{year}_manifest.json").read_text(encoding="utf-8"))
    expected = [(start.isoformat(), end.isoformat()) for start, end in date_ranges(year)]
    observed = [(batch["start"], batch["end"]) for batch in manifest]
    if observed != expected:
        raise ValueError(f"{year} manifest is incomplete or out of order")

    derived = defaultdict(Counter)
    unknown_inning = Counter()
    pitch_rows = 0
    for batch in manifest:
        with gzip.open(ROOT / batch["file"], "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                pitch_rows += 1
                inning = row["inning_topbot"]
                if inning not in ("Top", "Bot"):
                    unknown_inning[inning] += 1
                    continue
                team = row["home_team"] if inning == "Top" else row["away_team"]
                if team == "ATH":
                    team = "OAK"  # Historical Oakland seasons use OAK in MLB Stats API.
                derived[team]["pitches"] += 1
                event = row["events"]
                missing_hbp = (row["game_pk"], row["at_bat_number"], row["pitch_number"]) == MISSING_HBP
                if missing_hbp and (row["description"] != "hit_by_pitch" or event):
                    raise ValueError("The documented 2022 HBP exception no longer matches the source row")
                if (event and event != "truncated_pa") or missing_hbp:
                    derived[team]["BF"] += 1
                    derived[team]["K"] += event in ("strikeout", "strikeout_double_play")
                    derived[team]["BB"] += event in ("walk", "intent_walk")
    if pitch_rows != sum(batch["pitches"] for batch in manifest):
        raise ValueError(f"{year} pitch rows do not match manifest")

    official = official_teams(year)
    report = {"season": year, "source_files": len(manifest),
              "pitch_rows": pitch_rows, "unknown_inning_rows": dict(unknown_inning),
              "teams": {}}
    for team in sorted(set(official) | set(derived)):
        actual = official.get(team, {})
        observed = dict(derived.get(team, {}))
        report["teams"][team] = {
            "official": actual, "statcast": observed,
            "difference": {key: observed.get(key, 0) - actual.get(key, 0)
                           for key in ("K", "BB", "BF", "pitches")},
        }

    path = ROOT / "data" / f"season_reconciliation_{year}.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{year}: {pitch_rows:,} pitches in {len(manifest)} batches; {len(report['teams'])} teams")
    for metric in ("K", "BB", "BF", "pitches"):
        differences = [item["difference"][metric] for item in report["teams"].values()]
        print(f"  {metric}: total difference {sum(differences):+,}; mismatched teams {sum(value != 0 for value in differences)}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("years", type=int, nargs="+", choices=sorted(SEASONS))
    args = parser.parse_args()
    for year in args.years:
        run_year(year)


if __name__ == "__main__":
    main()

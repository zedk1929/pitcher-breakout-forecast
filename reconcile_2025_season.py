"""Compare full-season Statcast event totals with MLB team pitching totals.

Run: python3 reconcile_2025_season.py
"""

import csv
import gzip
import json
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "data" / "statcast_2025_manifest.json"
OFFICIAL = ROOT / "data" / "official_team_pitching_2025.json"
REPORT = ROOT / "data" / "season_reconciliation_2025.json"


def read_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def official_teams():
    if OFFICIAL.exists():
        return json.loads(OFFICIAL.read_text(encoding="utf-8"))
    teams = read_json("https://statsapi.mlb.com/api/v1/teams?sportId=1&season=2025")["teams"]
    def fetch(team):
        result = read_json(f"https://statsapi.mlb.com/api/v1/teams/{team['id']}/stats?stats=season&group=pitching&season=2025")
        stats = result["stats"][0]["splits"][0]["stat"]
        return team["abbreviation"], {
            "team": team["name"], "K": stats["strikeOuts"],
            "BB": stats["baseOnBalls"], "BF": stats["battersFaced"],
            "pitches": stats["numberOfPitches"],
        }
    with ThreadPoolExecutor(max_workers=5) as pool:
        official = dict(pool.map(fetch, teams))
    OFFICIAL.write_text(json.dumps(official, indent=2) + "\n", encoding="utf-8")
    return official


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    derived = defaultdict(Counter)
    unknown_inning = Counter()
    for batch in manifest:
        with gzip.open(ROOT / batch["file"], "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                inning = row["inning_topbot"]
                if inning not in ("Top", "Bot"):
                    unknown_inning[inning] += 1
                    continue
                team = row["home_team"] if inning == "Top" else row["away_team"]
                derived[team]["pitches"] += 1
                event = row["events"]
                if event and event != "truncated_pa":
                    derived[team]["BF"] += 1
                    derived[team]["K"] += event in ("strikeout", "strikeout_double_play")
                    derived[team]["BB"] += event in ("walk", "intent_walk")
    official = official_teams()
    report = {"season": 2025, "source_files": len(manifest),
              "unknown_inning_rows": dict(unknown_inning), "teams": {}}
    for team in sorted(set(official) | set(derived)):
        actual = official.get(team, {})
        observed = dict(derived.get(team, {}))
        report["teams"][team] = {"official": actual, "statcast": observed,
                                "difference": {key: observed.get(key, 0) - actual.get(key, 0)
                                               for key in ("K", "BB", "BF", "pitches")}}
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Teams:", len(report["teams"]))
    for metric in ("K", "BB", "BF", "pitches"):
        difference = sum(item["difference"][metric] for item in report["teams"].values())
        mismatched = sum(item["difference"][metric] != 0 for item in report["teams"].values())
        print(f"{metric}: total difference {difference:+,}; mismatched teams {mismatched}")
    print("Saved", REPORT)


if __name__ == "__main__":
    main()

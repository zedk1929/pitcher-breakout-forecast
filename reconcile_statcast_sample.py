import csv
import json
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

rows = []
for arg in sys.argv[1:]:
    with Path(arg).open(encoding="utf-8-sig", newline="") as handle:
        rows.extend(csv.DictReader(handle))

by_game = defaultdict(list)
for row in rows:
    by_game[row["game_pk"]].append(row)

total = Counter()
mismatches = []
for game_pk, game_rows in sorted(by_game.items()):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    with urllib.request.urlopen(url, timeout=20) as response:
        box = json.load(response)
    official = Counter()
    for side in ("home", "away"):
        for pitcher in box["teams"][side]["pitchers"]:
            stats = box["teams"][side]["players"][f"ID{pitcher}"]["stats"].get("pitching", {})
            official["K"] += int(stats.get("strikeOuts", 0))
            official["BB"] += int(stats.get("baseOnBalls", 0))
            official["BF"] += int(stats.get("battersFaced", 0))
    events = Counter(row["events"] for row in game_rows if row["events"])
    derived = Counter({
        "K": events["strikeout"] + events["strikeout_double_play"],
        "BB": events["walk"] + events["intent_walk"],
        "BF": sum(events.values()) - events["truncated_pa"],
    })
    total.update({f"official_{k}": v for k, v in official.items()})
    total.update({f"derived_{k}": v for k, v in derived.items()})
    if official != derived:
        mismatches.append((game_pk, dict(official), dict(derived), dict(events)))

print("Games", len(by_game))
print(dict(total))
print("Mismatched games", len(mismatches))
for item in mismatches:
    print(item)

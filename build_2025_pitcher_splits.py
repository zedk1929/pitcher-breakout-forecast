"""Aggregate downloaded 2025 pitches into pitcher first-half and second-half results.

Run: python3 build_2025_pitcher_splits.py
The CSV is descriptive data for cohort design; it is not a trained model.
"""

from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "data" / "statcast_2025_manifest.json"
OUT = ROOT / "pitcher_splits_2025.csv"
STRIKEOUTS = {"strikeout", "strikeout_double_play"}
WALKS = {"walk", "intent_walk"}


def rate(numerator: int, denominator: int) -> str:
    return f"{numerator / denominator:.6f}" if denominator else ""


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not manifest or manifest[0]["start"] != "2025-03-18" or manifest[-1]["end"] != "2025-09-28":
        raise SystemExit("Manifest does not cover the entire 2025 regular season")
    for left, right in zip(manifest, manifest[1:]):
        from datetime import date, timedelta
        if date.fromisoformat(left["end"]) + timedelta(days=1) != date.fromisoformat(right["start"]):
            raise SystemExit("Manifest has a date gap")

    pitchers = defaultdict(lambda: {"name": "", "first_pitches": 0, "first_bf": 0,
                                   "first_k": 0, "first_bb": 0, "second_pitches": 0,
                                   "second_bf": 0, "second_k": 0, "second_bb": 0})
    for batch in manifest:
        path = ROOT / batch["file"]
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                pitcher = pitchers[row["pitcher"]]
                pitcher["name"] = row["player_name"]
                half = "first" if row["game_date"] <= "2025-06-30" else "second"
                pitcher[f"{half}_pitches"] += 1
                event = row["events"]
                if event and event != "truncated_pa":
                    pitcher[f"{half}_bf"] += 1
                    pitcher[f"{half}_k"] += event in STRIKEOUTS
                    pitcher[f"{half}_bb"] += event in WALKS

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["pitcher_id", "pitcher_name", "first_pitches", "first_bf", "first_k",
              "first_bb", "first_kbb_rate", "second_pitches", "second_bf", "second_k",
              "second_bb", "second_kbb_rate", "eligible_first_100_bf", "evaluable_second_100_bf"]
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for pitcher_id, p in sorted(pitchers.items(), key=lambda item: int(item[0])):
            writer.writerow({
                "pitcher_id": pitcher_id, "pitcher_name": p["name"],
                "first_pitches": p["first_pitches"], "first_bf": p["first_bf"],
                "first_k": p["first_k"], "first_bb": p["first_bb"],
                "first_kbb_rate": rate(p["first_k"] - p["first_bb"], p["first_bf"]),
                "second_pitches": p["second_pitches"], "second_bf": p["second_bf"],
                "second_k": p["second_k"], "second_bb": p["second_bb"],
                "second_kbb_rate": rate(p["second_k"] - p["second_bb"], p["second_bf"]),
                "eligible_first_100_bf": int(p["first_bf"] >= 100),
                "evaluable_second_100_bf": int(p["second_bf"] >= 100),
            })
    print(f"Saved {OUT}: {len(pitchers)} pitcher rows")
    print("First-half >=100 BF:", sum(p["first_bf"] >= 100 for p in pitchers.values()))
    print("Both halves >=100 BF:", sum(p["first_bf"] >= 100 and p["second_bf"] >= 100 for p in pitchers.values()))


if __name__ == "__main__":
    main()

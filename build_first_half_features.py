"""Create June-30-only pitcher-season features from verified Statcast batches.

Run: python3 build_first_half_features.py
Output contains predictors only. Official second-half outcomes stay in
second_half_outcomes_2022_2025.csv.
"""

import csv
import gzip
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from official_pitching_totals import load_half


ROOT = Path(__file__).resolve().parent
YEARS = (2022, 2023, 2024, 2025)
FASTBALL = {"FF", "SI", "FC", "FA"}
BREAKING = {"SL", "ST", "SV", "CU", "KC"}
SWINGING_STRIKES = {"swinging_strike", "swinging_strike_blocked"}
MIN_BF = 100
FIELDS = [
    "season", "pitcher_id", "pitcher_name", "first_bf", "first_pitches",
    "first_kbb_rate", "tracked_pitches", "swinging_strike_rate",
    "fastball_share", "breaking_share", "primary_fastball_type",
    "primary_fastball_count", "primary_fastball_speed_mph",
    "primary_fastball_pfx_z_inches",
]


def valid_manifest(year):
    manifest = json.loads((ROOT / "data" / f"statcast_{year}_manifest.json").read_text(encoding="utf-8"))
    if not manifest or manifest[0]["start"][:4] != str(year) or manifest[-1]["end"][:4] != str(year):
        raise ValueError(f"{year} manifest is missing or has the wrong season")
    for left, right in zip(manifest, manifest[1:]):
        if date.fromisoformat(left["end"]) + timedelta(days=1) != date.fromisoformat(right["start"]):
            raise ValueError(f"{year} manifest has a date gap")
    return manifest


def new_pitcher():
    return {
        "pitch_rows": 0, "tracked": 0, "swinging_strikes": 0,
        "fastballs": 0, "breaking": 0, "fastball_types": Counter(),
        "speed_sum": Counter(), "speed_count": Counter(),
        "pfx_z_sum": Counter(), "pfx_z_count": Counter(),
    }


def feature_rows(year):
    cutoff = f"{year}-06-30"
    official = load_half(year, "first_half")
    with (ROOT / f"pitcher_splits_{year}.csv").open(newline="", encoding="utf-8") as handle:
        splits = {row["pitcher_id"]: row for row in csv.DictReader(handle)}
    local_eligible = {pid for pid, row in splits.items() if int(row["first_bf"]) >= MIN_BF}
    official_eligible = {pid for pid, row in official.items() if row["bf"] >= MIN_BF}
    if local_eligible != official_eligible:
        raise ValueError(f"{year} official and Statcast first-half eligibility differ")
    pitchers = defaultdict(new_pitcher)
    audit = Counter()

    for batch in valid_manifest(year):
        if batch["start"] > cutoff:
            break
        with gzip.open(ROOT / batch["file"], "rt", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["game_date"] > cutoff:
                    continue
                audit["pitch_rows"] += 1
                for field in ("pitch_type", "release_speed", "pfx_z", "description"):
                    if not row[field]:
                        audit[f"missing_{field}"] += 1

                p = pitchers[row["pitcher"]]
                p["pitch_rows"] += 1
                kind = row["pitch_type"]
                if not kind:
                    continue
                p["tracked"] += 1
                p["swinging_strikes"] += row["description"] in SWINGING_STRIKES
                p["breaking"] += kind in BREAKING
                if kind in FASTBALL:
                    p["fastballs"] += 1
                    p["fastball_types"][kind] += 1
                    if row["release_speed"]:
                        p["speed_sum"][kind] += float(row["release_speed"])
                        p["speed_count"][kind] += 1
                    if row["pfx_z"]:
                        p["pfx_z_sum"][kind] += float(row["pfx_z"])
                        p["pfx_z_count"][kind] += 1

    if audit["pitch_rows"] != sum(int(s["first_pitches"]) for s in splits.values()):
        raise ValueError(f"{year} first-half pitch count does not match pitcher splits")

    result = []
    for pitcher_id, split in sorted(splits.items(), key=lambda pair: int(pair[0])):
        if pitcher_id not in official_eligible:
            continue
        official_stat = official[pitcher_id]
        p = pitchers[pitcher_id]
        if p["pitch_rows"] != int(split["first_pitches"]):
            raise ValueError(f"{year} pitch count mismatch for pitcher {pitcher_id}")
        if not p["tracked"]:
            raise ValueError(f"{year} eligible pitcher {pitcher_id} has no tracked pitches")
        primary = max(sorted(p["fastball_types"]), key=lambda kind: p["fastball_types"][kind]) if p["fastball_types"] else ""
        speed_count = p["speed_count"][primary]
        movement_count = p["pfx_z_count"][primary]
        result.append({
            "season": year,
            "pitcher_id": pitcher_id,
            "pitcher_name": split["pitcher_name"],
            "first_bf": official_stat["bf"],
            "first_pitches": split["first_pitches"],
            "first_kbb_rate": f"{(official_stat['k'] - official_stat['bb']) / official_stat['bf']:.6f}",
            "tracked_pitches": p["tracked"],
            "swinging_strike_rate": f"{p['swinging_strikes'] / p['tracked']:.6f}",
            "fastball_share": f"{p['fastballs'] / p['tracked']:.6f}",
            "breaking_share": f"{p['breaking'] / p['tracked']:.6f}",
            "primary_fastball_type": primary,
            "primary_fastball_count": p["fastball_types"][primary],
            "primary_fastball_speed_mph": f"{p['speed_sum'][primary] / speed_count:.3f}" if speed_count else "",
            "primary_fastball_pfx_z_inches": f"{12 * p['pfx_z_sum'][primary] / movement_count:.3f}" if movement_count else "",
        })

    audit["eligible_pitchers"] = len(result)
    audit["missing_primary_fastball_speed"] = sum(not r["primary_fastball_speed_mph"] for r in result)
    audit["missing_primary_fastball_pfx_z"] = sum(not r["primary_fastball_pfx_z_inches"] for r in result)
    audit["primary_fastball_under_20"] = sum(int(r["primary_fastball_count"]) < 20 for r in result)
    return result, dict(audit)


def main():
    all_rows = []
    audits = {}
    for year in YEARS:
        rows, audit = feature_rows(year)
        all_rows.extend(rows)
        audits[str(year)] = audit
        print(f"{year}: {audit['pitch_rows']:,} first-half rows; {len(rows)} eligible pitchers; "
              f"{audit['missing_primary_fastball_speed']} missing primary fastball speed")

    output = ROOT / "first_half_features_2022_2025.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)
    (ROOT / "data" / "first_half_feature_audit.json").write_text(
        json.dumps(audits, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Saved {output.name}: {len(all_rows)} pitcher-season rows")


if __name__ == "__main__":
    main()

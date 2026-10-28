"""Inspect a small Baseball Savant pitch-level CSV before building the model.

Usage:
  python3 inspect_statcast_sample.py --download --date 2025-04-01 --save statcast_2025-04-01.csv
  python3 inspect_statcast_sample.py --csv path/to/statcast.csv

This uses only Python's standard library. It does not train a model.
"""

from __future__ import annotations

import argparse
import csv
import io
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path


REQUIRED = {
    "game_date", "game_type", "pitcher", "game_pk", "at_bat_number",
    "pitch_number", "events", "description", "pitch_type", "release_speed",
    "pfx_x", "pfx_z",
}
KEY = ("game_pk", "at_bat_number", "pitch_number")
MEASURES = ("release_speed", "pfx_x", "pfx_z", "pitch_type", "events", "description")


def download_day(day: str) -> str:
    year = day[:4]
    query = urllib.parse.urlencode({
        "all": "true", "type": "details", "player_type": "pitcher",
        "hfGT": "R|", "hfSea": f"{year}|",
        "game_date_gt": day, "game_date_lt": day,
    })
    url = "https://baseballsavant.mlb.com/statcast_search/csv?" + query
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
    return body.decode("utf-8-sig")


def inspect(text: str) -> None:
    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or [])
    missing = sorted(REQUIRED - fields)
    print(f"Columns: {len(fields)}")
    print(f"Required columns missing: {', '.join(missing) if missing else 'none'}")
    if missing:
        raise SystemExit("Cannot inspect this as the expected pitch-level Statcast CSV.")

    rows = 0
    dates: set[str] = set()
    pitchers: set[str] = set()
    game_types: Counter[str] = Counter()
    nulls: Counter[str] = Counter()
    event_counts: Counter[str] = Counter()
    description_counts: Counter[str] = Counter()
    keys: set[tuple[str, str, str]] = set()
    duplicate_keys = 0

    for row in reader:
        rows += 1
        dates.add(row["game_date"])
        pitchers.add(row["pitcher"])
        game_types[row["game_type"]] += 1
        key = tuple(row[column] for column in KEY)
        if key in keys:
            duplicate_keys += 1
        keys.add(key)
        for column in MEASURES:
            if not row[column].strip():
                nulls[column] += 1
        if row["events"].strip():
            event_counts[row["events"]] += 1
        description_counts[row["description"]] += 1

    if rows == 0:
        raise SystemExit("CSV contains no pitch rows. Check the date and search filters.")

    print(f"Pitch rows: {rows:,}")
    print(f"Unique pitchers: {len(pitchers):,}")
    print(f"Date range: {min(dates)} to {max(dates)}")
    print(f"Game types: {dict(game_types)}")
    print(f"Duplicate pitch keys: {duplicate_keys:,}")
    print("Missing values in key analysis fields:")
    for column in MEASURES:
        print(f"  {column}: {nulls[column]:,} ({nulls[column] / rows:.1%})")
    print(f"Batters faced from recorded events: {sum(event_counts.values()) - event_counts['truncated_pa']:,}")
    print(f"Recorded strikeouts: {event_counts['strikeout'] + event_counts['strikeout_double_play']:,}")
    print(f"Recorded walks: {event_counts['walk'] + event_counts['intent_walk']:,}")
    print("Most common pitch descriptions:")
    for label, count in description_counts.most_common(8):
        print(f"  {label}: {count:,}")
    print("Note: Compare event totals with MLB box scores before modeling.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv", type=Path, help="Downloaded pitch-level Statcast CSV")
    source.add_argument("--download", action="store_true", help="Fetch one day from Baseball Savant")
    parser.add_argument("--date", default="2025-04-01", help="Date for --download (YYYY-MM-DD)")
    parser.add_argument("--save", type=Path, help="Save a downloaded CSV at this path")
    args = parser.parse_args()
    if args.save and not args.download:
        parser.error("--save requires --download")
    text = download_day(args.date) if args.download else args.csv.read_text(encoding="utf-8-sig")
    inspect(text)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(text, encoding="utf-8")
        print(f"Saved CSV: {args.save}")


if __name__ == "__main__":
    main()

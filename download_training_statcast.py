"""Download and verify 2022-2024 regular-season Statcast CSV batches.

Run: python3 download_training_statcast.py 2022 2023 2024
Files, temporary parts, and manifests stay inside this project folder.
Rerunning checks existing files and resumes missing batches.
"""

import argparse
import csv
import gzip
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEASONS = {
    2022: (date(2022, 4, 7), date(2022, 10, 5)),
    2023: (date(2023, 3, 30), date(2023, 10, 1)),
    # The Sept. 30 Mets-Braves makeup doubleheader extended the season.
    2024: (date(2024, 3, 20), date(2024, 9, 30)),
}
REQUIRED = {
    "game_date", "game_type", "game_pk", "pitcher", "at_bat_number",
    "pitch_number", "events", "description", "pitch_type",
    "release_speed", "pfx_x", "pfx_z", "inning_topbot", "home_team",
    "away_team", "player_name",
}
ROW_CAP = 25_000


def date_ranges(year):
    start, last = SEASONS[year]
    while start <= last:
        end = min(start + timedelta(days=4), last)
        yield start, end
        start = end + timedelta(days=1)


def fetch(year, start, end):
    query = urllib.parse.urlencode({
        "all": "true", "type": "details", "player_type": "pitcher",
        "hfGT": "R|", "hfSea": f"{year}|",
        "game_date_gt": start.isoformat(), "game_date_lt": end.isoformat(),
    })
    request = urllib.request.Request(
        "https://baseballsavant.mlb.com/statcast_search/csv?" + query,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read().decode("utf-8-sig")
        except (OSError, UnicodeError):
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def validate(source, year, start, end):
    reader = csv.DictReader(source)
    fields = set(reader.fieldnames or [])
    if REQUIRED - fields:
        raise ValueError(f"Missing columns: {sorted(REQUIRED - fields)}")
    count = 0
    games = set()
    keys = set()
    for row in reader:
        count += 1
        day = date.fromisoformat(row["game_date"])
        if not start <= day <= end or row["game_type"] != "R" or day.year != year:
            raise ValueError(f"Unexpected date or game type: {row['game_date']} {row['game_type']}")
        games.add(row["game_pk"])
        key = (row["game_pk"], row["at_bat_number"], row["pitch_number"])
        if key in keys:
            raise ValueError(f"Duplicate pitch key: {key}")
        keys.add(key)
    if count >= ROW_CAP:
        raise ValueError(f"{start} to {end} reached {count:,} rows; request smaller batches")
    return {"start": start.isoformat(), "end": end.isoformat(),
            "pitches": count, "games": len(games), "columns": len(fields)}


def one_batch(year, start, end):
    path = ROOT / "data" / "raw" / str(year) / f"statcast_{start}_{end}.csv.gz"
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
            entry = validate(handle, year, start, end)
        action = "Verified"
    else:
        content = fetch(year, start, end)
        entry = validate(io.StringIO(content), year, start, end)
        temp = path.with_suffix(path.suffix + ".part")
        with gzip.open(temp, "wt", encoding="utf-8", newline="") as handle:
            handle.write(content)
        temp.replace(path)
        action = "Saved"
    entry["file"] = str(path.relative_to(ROOT))
    print(f"{action} {year} {start} to {end}: {entry['pitches']:,} pitches", flush=True)
    return entry


def run_year(year):
    (ROOT / "data" / "raw" / str(year)).mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "data" / f"statcast_{year}_manifest.json"
    manifest = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(one_batch, year, start, end)
                   for start, end in date_ranges(year)]
        for future in as_completed(futures):
            manifest.append(future.result())
            manifest.sort(key=lambda item: item["start"])
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{year} complete: {sum(b['pitches'] for b in manifest):,} pitches in {len(manifest)} batches", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("years", type=int, nargs="+", choices=sorted(SEASONS))
    args = parser.parse_args()
    for year in args.years:
        run_year(year)


if __name__ == "__main__":
    main()

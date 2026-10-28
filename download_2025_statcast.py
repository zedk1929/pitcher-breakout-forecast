"""Download 2025 regular-season Statcast pitches in resumable short CSV batches.

Run: python3 download_2025_statcast.py
Files are kept inside this project folder as gzip-compressed CSVs.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw" / "2025"
START = date(2025, 3, 18)
END = date(2025, 9, 28)
REQUIRED = {"game_date", "game_type", "game_pk", "pitcher", "at_bat_number", "pitch_number", "events", "description", "pitch_type", "release_speed", "pfx_x", "pfx_z"}


def date_ranges():
    # These two opening batches were verified below the 25,000-row source cap.
    yield date(2025, 3, 18), date(2025, 3, 24)
    yield date(2025, 3, 25), date(2025, 3, 31)
    start = date(2025, 4, 1)
    while start <= END:
        end = min(start + timedelta(days=4), END)
        yield start, end
        start = end + timedelta(days=1)


def download(start: date, end: date) -> str:
    query = urllib.parse.urlencode({
        "all": "true", "type": "details", "player_type": "pitcher",
        "hfGT": "R|", "hfSea": "2025|",
        "game_date_gt": start.isoformat(), "game_date_lt": end.isoformat(),
    })
    request = urllib.request.Request(
        "https://baseballsavant.mlb.com/statcast_search/csv?" + query,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read().decode("utf-8-sig")
        except (OSError, UnicodeError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def validate(text: str, start: date, end: date) -> dict:
    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or [])
    missing = REQUIRED - fields
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    rows = 0
    games = set()
    keys = set()
    for row in reader:
        rows += 1
        game_date = date.fromisoformat(row["game_date"])
        if not start <= game_date <= end or row["game_type"] != "R":
            raise ValueError(f"Out-of-range or non-regular-season row: {row['game_date']} {row['game_type']}")
        games.add(row["game_pk"])
        key = (row["game_pk"], row["at_bat_number"], row["pitch_number"])
        if key in keys:
            raise ValueError(f"Duplicate pitch key: {key}")
        keys.add(key)
    if rows >= 25000:
        raise ValueError(f"Batch has {rows} pitches; split this request to avoid the Savant 25,000-row result cap")
    return {"start": start.isoformat(), "end": end.isoformat(), "pitches": rows, "games": len(games), "columns": len(fields)}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    def fetch_one(start: date, end: date) -> dict:
        path = RAW / f"statcast_{start}_{end}.csv.gz"
        if path.exists():
            with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
                entry = validate(handle.read(), start, end)
            print(f"Verified existing {path.name}: {entry['pitches']:,} pitches", flush=True)
        else:
            text = download(start, end)
            entry = validate(text, start, end)
            temp = path.with_suffix(path.suffix + ".part")
            with gzip.open(temp, "wt", encoding="utf-8", newline="") as handle:
                handle.write(text)
            temp.replace(path)
            print(f"Saved {path.name}: {entry['pitches']:,} pitches", flush=True)
        entry["file"] = str(path.relative_to(ROOT))
        return entry

    manifest = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(fetch_one, start, end) for start, end in date_ranges()]
        for future in as_completed(futures):
            manifest.append(future.result())
            manifest.sort(key=lambda item: item["start"])
            (ROOT / "data" / "statcast_2025_manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
    print(f"Complete: {sum(item['pitches'] for item in manifest):,} pitches in {len(manifest)} batch files")


if __name__ == "__main__":
    main()

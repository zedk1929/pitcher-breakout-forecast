"""Read locally saved MLB player pitching totals by June/July period."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_half(year, half):
    if half not in ("first_half", "second_half"):
        raise ValueError(f"Unknown half: {half}")
    path = ROOT / "data" / f"official_{half}_pitching_{year}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    blocks = payload.get("stats", [])
    if len(blocks) != 1:
        raise ValueError(f"Unexpected MLB response structure in {path.name}")
    block = blocks[0]
    splits = block.get("splits", [])
    if not splits or len(splits) != block.get("totalSplits"):
        raise ValueError(f"Incomplete MLB response in {path.name}")
    result = {}
    for row in splits:
        if int(row["season"]) != year:
            raise ValueError(f"Wrong season in {path.name}")
        pitcher_id = str(row["player"]["id"])
        if pitcher_id in result:
            raise ValueError(f"Duplicate pitcher ID in {path.name}: {pitcher_id}")
        stat = row["stat"]
        result[pitcher_id] = {
            "pitcher_name": row["player"]["fullName"],
            "bf": int(stat["battersFaced"]),
            "k": int(stat["strikeOuts"]),
            "bb": int(stat["baseOnBalls"]),
        }
    return result

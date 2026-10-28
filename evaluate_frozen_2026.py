"""Run the frozen 2026 final test described in 09_Frozen_2026_Protocol.md.

First run: python3 evaluate_frozen_2026.py --download
Later runs verify the saved result without overwriting it.
"""

import argparse
import csv
import hashlib
import io
import json
import math
import random
import urllib.parse
import urllib.request
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
MODEL_PATH = ROOT / "selected_pitch_model_2025_summary.json"
MODEL_SHA256 = "09a0388f4d50af0ce9daeef9c1556d301a3fc55b322bc27278279ab4696f03e8"
MIN_BF = 100
SHRINK_BF = 100
BREAKOUT_GAIN = 0.03
BOOTSTRAP_DRAWS = 10000
BOOTSTRAP_SEED = 2026
CSV_PATH = ROOT / "frozen_2026_predictions.csv"
JSON_PATH = ROOT / "frozen_2026_results.json"


def source_url(year, period):
    query = {
        "stats": "season" if period == "full" else "byDateRange",
        "group": "pitching", "season": year, "sportIds": 1,
        "playerPool": "ALL", "gameType": "R", "limit": 2000,
    }
    if period != "full":
        start, end = ((f"{year}-01-01", f"{year}-06-30") if period == "first_half"
                      else (f"{year}-07-01", f"{year}-12-31"))
        query.update({"startDate": start, "endDate": end})
    return "https://statsapi.mlb.com/api/v1/stats?" + urllib.parse.urlencode(query)


def data_path(year, period):
    label = "player" if period == "full" else period
    return DATA / f"official_{label}_pitching_{year}.json"


def load_stats(year, period, download=False):
    path = data_path(year, period)
    if download and not path.exists():
        with urllib.request.urlopen(source_url(year, period), timeout=60) as response:
            payload = json.load(response)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Downloaded {path.name}")
    if not path.exists():
        raise FileNotFoundError(f"Missing {path.name}; run with --download")
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
        pid = str(row["player"]["id"])
        if pid in result:
            raise ValueError(f"Duplicate player ID {pid} in {path.name}")
        stat = row["stat"]
        result[pid] = {
            "name": row["player"]["fullName"],
            "bf": int(stat["battersFaced"]),
            "k": int(stat["strikeOuts"]),
            "bb": int(stat["baseOnBalls"]),
        }
    return result


def check_additivity(year, first, second, full):
    differences = []
    for pid in set(first) | set(second) | set(full):
        for field in ("bf", "k", "bb"):
            half_total = first.get(pid, {}).get(field, 0) + second.get(pid, {}).get(field, 0)
            season_total = full.get(pid, {}).get(field, 0)
            if half_total != season_total:
                differences.append((pid, field, half_total, season_total))
    if differences:
        raise ValueError(f"{year} official half/full mismatch: {differences[:5]} ({len(differences)} total)")


def frozen_intercept():
    raw = MODEL_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MODEL_SHA256:
        raise ValueError("Frozen model artifact changed since the 2026 protocol was written")
    model = json.loads(raw)
    if (model["selected"] != "calibrated" or model["fit_years"] != [2022, 2023, 2024]
            or model["final_holdout_evaluated"] is not False
            or model["fit_parameters"]["slope"] != 0):
        raise ValueError("Frozen model metadata do not match the protocol")
    return float(model["fit_parameters"]["residual_mean"])


def ranks(values):
    ordered = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    position = 0
    while position < len(values):
        end = position + 1
        while end < len(values) and values[ordered[end]] == values[ordered[position]]:
            end += 1
        average_rank = (position + 1 + end) / 2
        for at in range(position, end):
            result[ordered[at]] = average_rank
        position = end
    return result


def spearman(predicted, actual):
    x = ranks(predicted)
    y = ranks(actual)
    x_mean = mean(x)
    y_mean = mean(y)
    numerator = sum((a - x_mean) * (b - y_mean) for a, b in zip(x, y))
    denominator = math.sqrt(sum((a - x_mean) ** 2 for a in x) * sum((b - y_mean) ** 2 for b in y))
    return numerator / denominator if denominator else None


def metrics(rows, key):
    errors = [row[key] - row["actual"] for row in rows]
    return {
        "mae_pp": round(100 * mean(abs(e) for e in errors), 3),
        "rmse_pp": round(100 * math.sqrt(mean(e * e for e in errors)), 3),
        "spearman": round(spearman([row[key] for row in rows], [row["actual"] for row in rows]), 3)
        if key != "league_only" else None,
    }


def paired_bootstrap(rows):
    improvement = [abs(row["raw_shrinkage"] - row["actual"])
                   - abs(row["frozen_prediction"] - row["actual"]) for row in rows]
    rng = random.Random(BOOTSTRAP_SEED)
    draws = sorted(100 * mean(rng.choices(improvement, k=len(improvement)))
                   for _ in range(BOOTSTRAP_DRAWS))
    return {
        "improvement_pp": round(100 * mean(improvement), 3),
        "paired_bootstrap_95pct_interval_pp": [round(draws[int(0.025 * BOOTSTRAP_DRAWS)], 3),
                                                 round(draws[int(0.975 * BOOTSTRAP_DRAWS)], 3)],
        "draws": BOOTSTRAP_DRAWS,
        "seed": BOOTSTRAP_SEED,
    }


def result_content(download=False):
    intercept = frozen_intercept()
    prior_first = load_stats(2025, "first_half")
    prior_second = load_stats(2025, "second_half")
    prior_full = load_stats(2025, "full", download)
    check_additivity(2025, prior_first, prior_second, prior_full)
    first = load_stats(2026, "first_half", download)
    second = load_stats(2026, "second_half", download)
    full = load_stats(2026, "full", download)
    check_additivity(2026, first, second, full)

    league_bf = sum(row["bf"] for row in first.values())
    league_net_k = sum(row["k"] - row["bb"] for row in first.values())
    league_rate = league_net_k / league_bf
    rows = []
    for pid, p in sorted(first.items(), key=lambda pair: int(pair[0])):
        if p["bf"] < MIN_BF:
            continue
        later = second.get(pid, {"bf": 0, "k": 0, "bb": 0})
        previous = prior_full.get(pid)
        prior_bf = previous["bf"] if previous else 0
        prior_rate = ((previous["k"] - previous["bb"]) / prior_bf) if prior_bf else None
        first_rate = (p["k"] - p["bb"]) / p["bf"]
        raw_shrinkage = (p["k"] - p["bb"] + SHRINK_BF * league_rate) / (p["bf"] + SHRINK_BF)
        actual = (later["k"] - later["bb"]) / later["bf"] if later["bf"] else None
        change = first_rate - prior_rate if prior_bf >= MIN_BF else None
        apparent = change is not None and change >= BREAKOUT_GAIN
        rows.append({
            "season": 2026, "pitcher_id": pid, "pitcher_name": p["name"],
            "first_bf": p["bf"], "first_k": p["k"], "first_bb": p["bb"],
            "first_kbb_rate": first_rate, "league_first_kbb_rate": league_rate,
            "unchanged": first_rate, "league_only": league_rate,
            "raw_shrinkage": raw_shrinkage,
            "frozen_prediction": raw_shrinkage + intercept,
            "second_bf": later["bf"], "second_k": later["k"], "second_bb": later["bb"],
            "actual": actual, "evaluable": later["bf"] >= MIN_BF,
            "prior_2025_bf": prior_bf, "prior_2025_kbb_rate": prior_rate,
            "first_vs_prior_change_pp": 100 * change if change is not None else None,
            "apparent_breakout": apparent,
            "breakout_persisted": (actual > prior_rate) if apparent and later["bf"] >= MIN_BF else None,
        })

    evaluable = [row for row in rows if row["evaluable"]]
    apparent = [row for row in rows if row["apparent_breakout"]]
    apparent_evaluable = [row for row in apparent if row["evaluable"]]
    result = {
        "protocol": "09_Frozen_2026_Protocol.md",
        "model_artifact_sha256": MODEL_SHA256,
        "selected_model": "calibrated 100-BF shrinkage baseline",
        "frozen_intercept": intercept,
        "first_half_league_kbb_rate": round(league_rate, 6),
        "first_half_eligible": len(rows),
        "both_halves_evaluable": len(evaluable),
        "not_evaluable": len(rows) - len(evaluable),
        "zero_second_half_bf": sum(row["second_bf"] == 0 for row in rows),
        "metrics_on_same_evaluable_pitchers": {
            name: metrics(evaluable, name)
            for name in ("unchanged", "league_only", "raw_shrinkage", "frozen_prediction")
        },
        "frozen_vs_raw_shrinkage": paired_bootstrap(evaluable),
        "apparent_breakout_rule": "2025 full-season BF >=100 and 2026 first-half BF >=100 and K-BB% gain >=3 pp",
        "apparent_breakout_count": len(apparent),
        "apparent_breakout_evaluable": len(apparent_evaluable),
        "apparent_breakout_not_evaluable": len(apparent) - len(apparent_evaluable),
        "apparent_breakout_persisted": sum(row["breakout_persisted"] for row in apparent_evaluable),
        "top_five_apparent_by_june_gain": [
            {"pitcher_id": row["pitcher_id"], "pitcher_name": row["pitcher_name"],
             "first_vs_prior_change_pp": round(row["first_vs_prior_change_pp"], 3),
             "second_bf": row["second_bf"], "evaluable": row["evaluable"],
             "breakout_persisted": row["breakout_persisted"]}
            for row in sorted(apparent, key=lambda row: (-row["first_vs_prior_change_pp"], int(row["pitcher_id"])))[:5]
        ],
        "data_sources": [source_url(2025, "full"), source_url(2026, "first_half"),
                         source_url(2026, "second_half"), source_url(2026, "full")],
        "additivity_checks_passed": [2025, 2026],
    }

    fields = (
        "season", "pitcher_id", "pitcher_name", "first_bf", "first_k", "first_bb",
        "first_kbb_rate", "league_first_kbb_rate", "unchanged", "raw_shrinkage",
        "frozen_prediction", "second_bf", "second_k", "second_bb", "actual",
        "evaluable", "frozen_absolute_error", "prior_2025_bf", "prior_2025_kbb_rate",
        "first_vs_prior_change_pp", "apparent_breakout", "breakout_persisted",
    )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        def fmt(value, places=6):
            return "" if value is None else f"{value:.{places}f}"
        writer.writerow({
            **{key: row[key] for key in ("season", "pitcher_id", "pitcher_name", "first_bf", "first_k", "first_bb", "second_bf", "second_k", "second_bb", "prior_2025_bf")},
            **{key: fmt(row[key]) for key in ("first_kbb_rate", "league_first_kbb_rate", "unchanged", "raw_shrinkage", "frozen_prediction", "actual", "prior_2025_kbb_rate")},
            "evaluable": int(row["evaluable"]),
            "frozen_absolute_error": fmt(abs(row["frozen_prediction"] - row["actual"])) if row["evaluable"] else "",
            "first_vs_prior_change_pp": fmt(row["first_vs_prior_change_pp"], 3),
            "apparent_breakout": int(row["apparent_breakout"]),
            "breakout_persisted": "" if row["breakout_persisted"] is None else int(row["breakout_persisted"]),
        })
    return output.getvalue(), json.dumps(result, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Fetch missing official MLB files into this project folder")
    args = parser.parse_args()
    csv_content, json_content = result_content(args.download)
    if CSV_PATH.exists() or JSON_PATH.exists():
        if not CSV_PATH.exists() or not JSON_PATH.exists():
            raise FileExistsError("Only one final output exists; inspect before proceeding")
        if (CSV_PATH.read_bytes() != csv_content.encode("utf-8")
                or JSON_PATH.read_bytes() != json_content.encode("utf-8")):
            raise ValueError("Recomputed final result differs from the saved one; files were not overwritten")
        print("Recomputed result matches both frozen output files exactly")
    else:
        CSV_PATH.write_text(csv_content, encoding="utf-8")
        JSON_PATH.write_text(json_content, encoding="utf-8")
        print(f"Saved {CSV_PATH.name} and {JSON_PATH.name}")
    result = json.loads(json_content)
    print(f"Eligible: {result['first_half_eligible']}; evaluable: {result['both_halves_evaluable']}; "
          f"not evaluable: {result['not_evaluable']}")
    for name, measure in result["metrics_on_same_evaluable_pitchers"].items():
        print(f"{name}: MAE {measure['mae_pp']:.3f} pp; RMSE {measure['rmse_pp']:.3f} pp; "
              f"Spearman {measure['spearman']}")
    print(f"Apparent breakouts: {result['apparent_breakout_count']}; "
          f"evaluable: {result['apparent_breakout_evaluable']}; "
          f"persisted: {result['apparent_breakout_persisted']}")


if __name__ == "__main__":
    main()

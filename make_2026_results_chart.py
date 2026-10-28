"""Render the frozen 2026 MAE comparison from its saved JSON result.

Run: python3 make_2026_results_chart.py
Uses only the Python standard library; no data is downloaded.
"""

import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "frozen_2026_results.json"
OUTPUT = ROOT / "2026_model_comparison.svg"


def main():
    data = json.loads(SOURCE.read_text())
    metrics = data["metrics_on_same_evaluable_pitchers"]
    rows = [
        ("First-half rate unchanged", "unchanged", "#777D7A"),
        ("First-half league rate", "league_only", "#777D7A"),
        ("Plain 100-BF shrinkage", "raw_shrinkage", "#404846"),
        ("Frozen calibrated shrinkage", "frozen_prediction", "#1F6F5F"),
    ]
    cohort = data["both_halves_evaluable"]
    interval = data["frozen_vs_raw_shrinkage"]["paired_bootstrap_95pct_interval_pp"]
    low, high = 4.2, 5.4  # Explicitly narrowed dot-plot axis, not a bar baseline.
    x0, x1 = 470, 990

    def x(value):
        return x0 + (value - low) / (high - low) * (x1 - x0)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 1200 620" role="img" aria-labelledby="title desc">',
        '<title id="title">Simple shrinkage lowered 2026 K-BB% prediction error</title>',
        '<desc id="desc">Mean absolute error across 275 pitchers: unchanged first-half rate 5.058, league rate 5.192, plain shrinkage 4.418, and frozen calibrated shrinkage 4.431 percentage points. Lower is better.</desc>',
        '<rect width="1200" height="620" fill="#FFFFFF"/>',
        '<g font-family="Arial, Helvetica, sans-serif">',
        '<text x="62" y="64" font-size="28" font-weight="600" fill="#171717">Simple shrinkage lowered 2026 prediction error</text>',
        f'<text x="62" y="100" font-size="18" fill="#5E6462">July-onward K-BB% · Same {cohort} pitchers · Lower MAE is better</text>',
        '<line x1="62" y1="131" x2="1138" y2="131" stroke="#E4E7E5"/>',
    ]
    for tick in (4.2, 4.5, 4.8, 5.1, 5.4):
        xx = x(tick)
        parts.append(f'<line x1="{xx:.1f}" y1="174" x2="{xx:.1f}" y2="440" stroke="#E4E7E5"/>')
        parts.append(f'<text x="{xx:.1f}" y="470" text-anchor="middle" font-size="16" fill="#5E6462">{tick:.1f}</text>')
    for index, (label, key, color) in enumerate(rows):
        yy = 214 + index * 68
        value = metrics[key]["mae_pp"]
        xx = x(value)
        parts.append(f'<text x="62" y="{yy + 6}" font-size="19" fill="#171717">{escape(label)}</text>')
        parts.append(f'<circle cx="{xx:.1f}" cy="{yy}" r="8" fill="{color}"/>')
        parts.append(f'<text x="{xx + 22:.1f}" y="{yy + 6}" font-size="20" font-weight="600" fill="{color}">{value:.3f}</text>')
    parts.extend([
        '<text x="730" y="505" text-anchor="middle" font-size="17" fill="#404846">Mean absolute error (percentage points)</text>',
        '<line x1="62" y1="529" x2="1138" y2="529" stroke="#E4E7E5"/>',
        f'<text x="62" y="559" font-size="15" fill="#404846">Frozen vs plain shrinkage: 95% paired bootstrap interval for MAE improvement {interval[0]:+.3f} to {interval[1]:+.3f} pp.</text>',
        '<text x="62" y="584" font-size="15" fill="#5E6462">Axis begins at 4.2 pp to reveal small differences; dots show absolute MAE, not improvement.</text>',
        '</g></svg>',
    ])
    OUTPUT.write_text("\n".join(parts) + "\n")
    print(f"Wrote {OUTPUT.name} from {SOURCE.name}")


if __name__ == "__main__":
    main()

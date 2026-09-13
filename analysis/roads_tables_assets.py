#!/usr/bin/env python3
"""Forest-plot asset for the roads-tables study: seating-corrected effects of the
opponent_expansion and road_contention_gate switches under the learned tables leaf,
per stage and lineup. Every value is recomputed from the retained run games; nothing
here plays games. Run IDs are filled in from the filed run records."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

# (tick label, [(run half A, run half B), ...]) — run IDs from the filed run records.
ARMS: list[tuple[str, list[tuple[str, str]]]] = [
    ("block, tables, dev", [("4529da10-c5ab-49f8-be24-6bb5e7e317e1", "86136b36-66e2-49a8-aa95-e5de0d802e61")]),
    ("block, tables, confirm", [("4629e513-2dac-459e-a018-e5faef0ed50a", "044327fe-d6f2-4c0e-8ae3-cfa7b0492ab5")]),
    ("block, tables, population", [("36a7adfd-d1ce-49d3-a25f-ccec8f616c23", "4aa3d3a3-b395-4248-9837-ca3c09eb0ec1")]),
    ("block, blend, dev", [("f9113c62-9c89-4095-9e81-cbb6c06d5dc0", "ba368081-2db1-4998-9e81-902ef7a7bace")]),
    ("block, blend, confirm", [("c07b2268-3e6b-4055-93f1-bc6405019ca0", "3fb6583b-bc5c-4b8e-a19e-c62cf6c8f650")]),
    ("block, blend, population", [("bd42145a-ca36-457b-954b-46c298027787", "f95c0335-c77f-4d94-8026-b05cb06e855c")]),
    ("block, blend, ext builders", [("90d394ae-fc62-4426-aca0-5f04bd54f2a6", "4e5d2807-1875-431f-b3ea-60a88f1ed2d9")]),
    ("block, blend, ext population", [("66a398f5-9b69-442f-84f3-fd1fa219fd46", "ff3fe1b1-e62e-4271-8c35-4bb44e07764f")]),
    ("gate, tables, dev", [("10dead1d-160a-4c00-8b08-b1f77a5c75b3", "86184ec9-2a1a-4944-bca0-c6a983829794")]),
    ("gate, tables, confirm", [("82e6046b-1ba5-44d9-998c-fa4ec398244f", "773e53b5-26ce-42e4-8aa5-2565363f1f99")]),
    ("gate, tables, population", [("c29e9c07-6499-464c-9cb7-4aa7c090c159", "ad9a07b9-939c-49c4-99d2-df93b7b51b47")]),
    ("gate, blend, dev", [("eaec0233-a70b-4af4-8346-604a003e8f8c", "160505ec-d7fb-4c53-b8a0-59f6ecccad22")]),
    ("gate, blend, confirm", [("8d3680d8-d891-41be-a3e1-ca1ec203e7b2", "79e0863d-47ac-47c4-adc2-2ef8b800d544")]),
    ("gate, blend, population", [("4425d52b-8a9b-49f9-9c0d-1eecc7c4edb4", "5b51b4e0-633d-43ac-bf47-59d5ccd532e0")]),
]


def per_board_contrast(run: str) -> dict[int, float]:
    rows = [
        json.loads(line)
        for line in (ROOT / "runs" / run / "games.jsonl").read_text().splitlines()
        if line.strip()
    ]
    by_seed: dict[int, list[int]] = {}
    for row in rows:
        if row["game"].get("status") != "completed":
            continue
        wins = by_seed.setdefault(row["seed"], [0, 0, 0])
        wins[2] += 1
        if row["winner_slot"] == 0:
            wins[0] += 1
        elif row["winner_slot"] == 1:
            wins[1] += 1
    return {seed: (w0 - w1) / n for seed, (w0, w1, n) in by_seed.items()}


def corrected(pairs: list[tuple[str, str]]) -> tuple[float, float, float, int]:
    effects: list[float] = []
    for run_a, run_b in pairs:
        a = per_board_contrast(run_a)
        b = per_board_contrast(run_b)
        assert set(a) == set(b), f"halves {run_a} and {run_b} cover different boards"
        effects.extend((a[s] - b[s]) / 2 for s in sorted(a))
    n = len(effects)
    mean = sum(effects) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in effects) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    return mean, mean - half, mean + half, n


def main() -> None:
    if not ARMS:
        raise SystemExit("ARMS is empty; fill in run IDs from the filed run records")
    ticks = ["block dev", "block confirm", "block population", "block ext builders",
             "block ext population", "gate dev", "gate confirm", "gate population"]
    # x position of each ARMS entry within the shared axis.
    x_of = [0, 1, 2, 0, 1, 2, 3, 4, 5, 6, 7, 5, 6, 7]
    tables_points, blend_points = [], []
    for (label, pairs), x in zip(ARMS, x_of):
        mean, lo, hi, n = corrected(pairs)
        point = {"x": x, "y": round(mean, 4), "low": round(lo, 4), "high": round(hi, 4)}
        (tables_points if "tables" in label else blend_points).append(point)
    points = tables_points + blend_points
    lo = min(p["low"] for p in points) - 0.05
    hi = max(p["high"] for p in points) + 0.05
    data = {
        "schema": 1,
        "kind": "plot",
        "variant": "scatter",
        "title": "Road switches under the learned leaf",
        "evidence": "measured",
        "source": (
            "Engine-arena swapped pairs under expansion/roads-tables: the switch against the "
            "unchanged tables-leaf control, each half 64 deterministic seeds played once per "
            "rotation (256 games), seating-corrected as the per-seed half-difference of the two "
            "halves. Dev, confirm, and extension builders use the builders lineup; population "
            "stages seat a third tables search in slot 2. Run IDs are listed in the "
            "roads-tables report."
        ),
        "caption": "Seating-corrected effect of each road switch per stage, under the tables alone and on the quarter blend.",
        "x": {"label": "Switch and stage", "min": 0, "max": len(ticks) - 1, "ticks": ticks},
        "y": {"label": "Wins per game, switch minus control",
              "min": round(min(lo, -0.05), 2), "max": round(max(hi, 0.05), 2)},
        "series": [
            {"label": "Tables leaf alone (95% interval)", "points": tables_points},
            {"label": "Quarter blend, hand 0.25 in both seats (95% interval)", "points": blend_points},
        ],
        "reference": {"y": 0, "label": "no difference"},
    }
    write_json(ROOT / "content/assets" / "roads-tables-effects.json", data)
    print(f"wrote content/assets/roads-tables-effects.json with {len(points)} points")


if __name__ == "__main__":
    main()

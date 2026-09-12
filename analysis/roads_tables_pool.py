#!/usr/bin/env python3
"""After-the-fact pooling of seating-corrected effects across several swapped
pairs of the same arm, for study expansion/roads-tables.

Each argument pair is RUN_A RUN_B (candidate in slot 0, then candidate in
slot 1) on the same deterministic boards, as in analysis/roads_tables.py.
The pooled effect concatenates the per-board half-differences of every pair;
the interval is a normal approximation over all boards. Pooling across stages
is after the fact and is named as such in the report. Usage:

    python3 analysis/roads_tables_pool.py RUN_A RUN_B [RUN_A RUN_B]...
"""
import json
import math
import sys
from pathlib import Path

CANONICAL = Path(__file__).resolve().parents[3] / "runs"


def per_board_contrast(run: str) -> dict[int, float]:
    folder = Path("runs") / run
    if not folder.is_dir():
        folder = CANONICAL / run
    rows = [
        json.loads(line)
        for line in (folder / "games.jsonl").read_text().splitlines()
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


def main() -> None:
    args = sys.argv[1:]
    effects: list[float] = []
    seating: list[float] = []
    for i in range(0, len(args), 2):
        a = per_board_contrast(args[i])
        b = per_board_contrast(args[i + 1])
        assert set(a) == set(b), f"halves {args[i]} and {args[i + 1]} cover different boards"
        for s in sorted(a):
            effects.append((a[s] - b[s]) / 2)
            seating.append((a[s] + b[s]) / 2)
    n = len(effects)
    for label, values in [("pooled corrected effect", effects), ("pooled seating term", seating)]:
        mean = sum(values) / n
        sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
        half = 1.96 * sd / math.sqrt(n)
        print(f"{label}: {mean:+.4f} (95% interval {mean - half:+.4f} to {mean + half:+.4f}), {n} boards")


if __name__ == "__main__":
    main()

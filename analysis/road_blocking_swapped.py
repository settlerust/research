#!/usr/bin/env python3
"""Seating-corrected effects for the road-blocking swapped pairs.

Each arm is two runs on the same deterministic boards: contrast A had the
candidate in slot 0, contrast B in slot 1. Per board, the corrected effect is
half the difference of the two contrasts and the seating term half their sum.
Intervals are normal approximations over boards. Usage:

    python3 analysis/road_blocking_swapped.py RUN_A RUN_B [RUN_A RUN_B]...

Contrast A is candidate-minus-control; contrast B is control-minus-candidate.
"""
import json
import math
import sys
from pathlib import Path


def per_board_contrast(run: str) -> dict[int, float]:
    folder = Path("runs") / run
    if not folder.is_dir():  # integrated runs live in the canonical checkout
        folder = Path(__file__).resolve().parents[3] / "runs" / run
    rows = [
        json.loads(line)
        for line in (folder / "games.jsonl").read_text().splitlines()
        if line.strip()
    ]
    by_seed: dict[int, list[int]] = {}
    for row in rows:
        wins = by_seed.setdefault(row["seed"], [0, 0, 0])
        wins[2] += 1
        if row["winner_slot"] == 0:
            wins[0] += 1
        elif row["winner_slot"] == 1:
            wins[1] += 1
    return {seed: (w0 - w1) / n for seed, (w0, w1, n) in by_seed.items()}


def summarize(label: str, values: list[float]) -> None:
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    print(f"{label}: {mean:+.3f} (95% interval {mean - half:+.3f} to {mean + half:+.3f}), {n} boards")


def main() -> None:
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        run_a, run_b = args[i], args[i + 1]
        a = per_board_contrast(run_a)
        b = per_board_contrast(run_b)
        assert set(a) == set(b), "the two halves must cover the same boards"
        seeds = sorted(a)
        effect = [(a[s] - b[s]) / 2 for s in seeds]
        seating = [(a[s] + b[s]) / 2 for s in seeds]
        print(f"pair {run_a} (candidate slot 0) x {run_b} (candidate slot 1)")
        summarize("  corrected effect", effect)
        summarize("  seating term    ", seating)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Seating-corrected effects and road diagnostics for swapped pairs under the
learned tables leaf (study expansion/roads-tables).

Each pair is two runs on the same deterministic boards: half A seats the
candidate in slot 0 and the control in slot 1, half B the reverse. Per board
the corrected effect is half the difference of the two slot-0-minus-slot-1
contrasts and the seating term half their sum; intervals are normal
approximations over boards.

Diagnostics are per completed game over both halves pooled: roads built,
longest-road awards gained, the award held at game end, sites lost,
settlements built, and mean decision time, for the candidate and the control
seat separately. Usage:

    python3 analysis/roads_tables.py RUN_A RUN_B [RUN_A RUN_B]...
"""
import json
import math
import sys
from pathlib import Path

CANONICAL = Path(__file__).resolve().parents[3] / "runs"


def load_run(run: str) -> list[dict]:
    folder = Path("runs") / run
    if not folder.is_dir():
        folder = CANONICAL / run
    return [
        json.loads(line)
        for line in (folder / "games.jsonl").read_text().splitlines()
        if line.strip()
    ]


def per_board_contrast(rows: list[dict]) -> dict[int, float]:
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


def summarize(label: str, values: list[float]) -> None:
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    half = 1.96 * sd / math.sqrt(n)
    print(f"{label}: {mean:+.4f} (95% interval {mean - half:+.4f} to {mean + half:+.4f}), {n} boards")


def seat_rows(rows: list[dict], slot: int) -> list[dict]:
    out = []
    for row in rows:
        if row["game"].get("status") != "completed":
            continue
        seat_index = row["slots"].index(slot)
        out.append(row["game"]["seats"][seat_index])
    return out


def diagnostics(label: str, seats: list[dict]) -> None:
    n = len(seats)
    decisions = sum(s["decisions"] for s in seats)
    fields = {
        "wins": None,  # placeholder, wins need the winner slot
        "points": sum(s["points"] for s in seats) / n,
        "roads_built": sum(s["roads_built"] for s in seats) / n,
        "road_awards": sum(s["road_awards"] for s in seats) / n,
        "award_held_share": sum(1 for s in seats if s.get("longest_road")) / n,
        "road_blocks": sum(s.get("road_blocks", 0) for s in seats) / n,
        "expansion_denied": sum(s.get("expansion_denied", 0.0) for s in seats) / n,
        "sites_lost": sum(s["sites_lost"] for s in seats) / n,
        "settlements_built": sum(s["settlements_built"] for s in seats) / n,
        "mean_decision_ms": sum(s["decision_ms"] for s in seats) / decisions,
    }
    print(f"  {label} ({n} games): " + ", ".join(
        f"{k} {v:.3f}" if isinstance(v, float) else f"{k} {v}" for k, v in fields.items() if k != "wins"))


def wins_of(rows: list[dict], slot: int) -> int:
    return sum(1 for r in rows if r["game"].get("status") == "completed" and r["winner_slot"] == slot)


def main() -> None:
    args = sys.argv[1:]
    for i in range(0, len(args), 2):
        run_a, run_b = args[i], args[i + 1]
        rows_a, rows_b = load_run(run_a), load_run(run_b)
        a = per_board_contrast(rows_a)
        b = per_board_contrast(rows_b)
        assert set(a) == set(b), "the two halves must cover the same boards"
        seeds = sorted(a)
        effect = [(a[s] - b[s]) / 2 for s in seeds]
        seating = [(a[s] + b[s]) / 2 for s in seeds]
        print(f"pair {run_a} (candidate slot 0) x {run_b} (candidate slot 1)")
        print(f"  half A: slot0 {wins_of(rows_a, 0)} slot1 {wins_of(rows_a, 1)}; "
              f"half B: slot0 {wins_of(rows_b, 0)} slot1 {wins_of(rows_b, 1)}")
        summarize("  corrected effect", effect)
        summarize("  seating term    ", seating)
        # Candidate is slot 0 in half A and slot 1 in half B; control the reverse.
        diagnostics("candidate", seat_rows(rows_a, 0) + seat_rows(rows_b, 1))
        diagnostics("control  ", seat_rows(rows_a, 1) + seat_rows(rows_b, 0))


if __name__ == "__main__":
    main()

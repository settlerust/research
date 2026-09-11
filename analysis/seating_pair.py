"""Seating-corrected effect of a swapped pair of engine-arena cohorts: half A seats the
candidate in slot 0, half B seats it in slot 1, both on the same seeds. The effect of the
candidate is the per-seed half-difference of the two slot-0-minus-slot-1 contrasts and the
seating term their half-sum, each with a normal-approximation 95 percent interval over
seeds."""
import argparse
import json
import math
from pathlib import Path


def per_seed(path, focal=0):
    """Per-seed slot-0-minus-slot-1 win difference (wins per game, in [-1, 1])."""
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    seeds = {}
    rotations = {}
    for r in rows:
        if r['game'].get('status') != 'completed':
            continue
        seeds.setdefault(r['seed'], []).append(r['winner_slot'])
        rotations[r['seed']] = rotations.get(r['seed'], 0) + 1
    return {s: sum(1 for w in winners if w == 0) - sum(1 for w in winners if w == 1)
            for s, winners in seeds.items()}, rotations


def interval(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, [mean - 1.96 * se, mean + 1.96 * se]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('half_a', help='games.jsonl with the candidate in slot 0')
    parser.add_argument('half_b', help='games.jsonl with the candidate in slot 1')
    args = parser.parse_args()
    a, ra = per_seed(args.half_a)
    b, rb = per_seed(args.half_b)
    if set(a) != set(b):
        raise SystemExit('the halves must play the same seeds')
    effects, seating = [], []
    for s in sorted(a):
        d_a = a[s] / ra[s]
        d_b = b[s] / rb[s]
        effects.append((d_a - d_b) / 2)
        seating.append((d_a + d_b) / 2)
    effect, effect_ci = interval(effects)
    seat, seat_ci = interval(seating)
    print(f"seeds: {len(effects)}")
    print(f"seating-corrected effect: {effect:+.3f} wins per game "
          f"(95% interval {effect_ci[0]:+.3f} to {effect_ci[1]:+.3f})")
    print(f"seating term: {seat:+.3f} wins per game "
          f"(95% interval {seat_ci[0]:+.3f} to {seat_ci[1]:+.3f})")


if __name__ == '__main__':
    main()

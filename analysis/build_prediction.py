"""Order-cancelling contrasts for the build-prediction study and its diagnostics.

Each arm ran as two cohorts: treatment slot 0 against control slot 1, and the mirrored
lineup with the slots swapped. Slot 1 always sits immediately after slot 0 in engine seat
order, so a single cohort carries a slot asymmetry; the per-seed average of the two
order-paired contrasts cancels it. The script also reads per-seat `sites_lost` counters and,
from a run recorded with `--predict-diag`, the observer's build-prediction match rates.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(run_id, root=ROOT):
    rows = [
        json.loads(line)
        for line in (root / 'runs' / run_id / 'games.jsonl')
        .read_text()
        .splitlines()
        if line.strip()
    ]
    return rows


def per_seed(rows, treatment_slot):
    """Per-seed treatment-minus-control win difference over the four rotations."""
    by_seed = {}
    for r in rows:
        if r['game']['status'] != 'completed' or r['winner_slot'] is None:
            continue
        by_seed.setdefault(r['seed'], []).append(r['winner_slot'])
    diffs = {}
    for seed, winners in by_seed.items():
        diffs[seed] = sum(w == treatment_slot for w in winners) / len(winners) - sum(
            w == (1 - treatment_slot) for w in winners
        ) / len(winners)
    return diffs


def interval(values):
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, None
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, (mean - 1.96 * se, mean + 1.96 * se)


def combined(first, second):
    """Two runs of one arm: treatment slot 0, then treatment slot 1."""
    a = per_seed(load(first), 0)
    b = per_seed(load(second), 1)
    seeds = sorted(set(a) & set(b))
    if len(seeds) != len(a) or len(seeds) != len(b):
        raise SystemExit(f'seed mismatch between {first} and {second}')
    paired = [(a[s] + b[s]) / 2 for s in seeds]
    order_only = [(a[s] - b[s]) / 2 for s in seeds]
    mean, ci = interval(paired)
    slot_mean, slot_ci = interval(order_only)
    return {
        'seeds': len(seeds),
        'mean': mean,
        'interval95': ci,
        'slot_order_effect': slot_mean,
        'slot_order_interval95': slot_ci,
    }


def sites_lost(run_id, root=ROOT):
    """Mean sites lost per game for each lineup slot over completed games."""
    rows = [r for r in load(run_id, root) if r['game']['status'] == 'completed']
    totals = [0.0, 0.0, 0.0, 0.0]
    for r in rows:
        for record in r['game']['seats']:
            totals[r['slots'][record['seat']]] += record['sites_lost']
    games = len(rows)
    return [t / games for t in totals]


def prediction_matches(run_id, root=ROOT):
    """Match rates of the observer's next-build predictions, by lineup slot of the actor."""
    rows = [r for r in load(run_id, root) if r['game']['status'] == 'completed']
    per_slot = {0: [0, 0], 1: [0, 0], 2: [0, 0], 3: [0, 0]}
    for r in rows:
        diag = r['game'].get('predict_diag')
        if not diag:
            continue
        for entry in diag['per_seat']:
            slot = r['slots'][entry['seat']]
            per_slot[slot][0] += entry['matches']
            per_slot[slot][1] += entry['builds']
    return {slot: (m, b) for slot, (m, b) in per_slot.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    pair = sub.add_parser('contrast')
    pair.add_argument('treatment_first')
    pair.add_argument('control_first')
    diag = sub.add_parser('diag')
    diag.add_argument('run_id')
    args = parser.parse_args()
    if args.command == 'contrast':
        out = combined(args.treatment_first, args.control_first)
        low, high = out['interval95']
        print(
            f"combined {out['mean']:+.3f} wins per game over {out['seeds']} seeds "
            f"(95% interval {low:+.3f} to {high:+.3f}); slot-order effect "
            f"{out['slot_order_effect']:+.3f}"
        )
        print(json.dumps(out, indent=2))
    else:
        print('sites lost per game by slot:', [round(x, 2) for x in sites_lost(args.run_id)])
        print('prediction matches by slot:', prediction_matches(args.run_id))


if __name__ == '__main__':
    main()

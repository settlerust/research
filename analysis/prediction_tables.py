"""Seating-corrected contrasts and diagnostics for the prediction-tables study.

Each arm ran as a swapped pair of engine cohorts: half A seats the candidate in
slot 0 and the control in slot 1, half B the reverse, both on the same seeds. The
effect of the candidate is the per-seed half-difference of the two slot-0-minus-
slot-1 contrasts and the seating term their half-sum. The script also pools
per-slot diagnostics (decision time, trades, counters, declines, robber moves,
builds, sites lost, discards) over the candidate and control seats of a pair, and
pools per-seed effects across pairs (after-the-fact pooling) for stage summaries.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path, root=ROOT):
    if not Path(path).is_absolute():
        path = root / 'runs' / path / 'games.jsonl'
    return [
        json.loads(line)
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]


def per_seed(rows, focal=0):
    """Per-seed slot-0-minus-slot-1 win difference and rotation count."""
    seeds, rotations = {}, {}
    for r in rows:
        if r['game'].get('status') != 'completed' or r['winner_slot'] is None:
            continue
        seeds.setdefault(r['seed'], []).append(r['winner_slot'])
        rotations[r['seed']] = rotations.get(r['seed'], 0) + 1
    return {s: sum(1 for w in winners if w == 0) - sum(1 for w in winners if w == 1)
            for s, winners in seeds.items()}, rotations


def interval(values):
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, (mean, mean)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, (mean - 1.96 * se, mean + 1.96 * se)


def pair_effects(a_rows, b_rows):
    a, ra = per_seed(a_rows)
    b, rb = per_seed(b_rows)
    if set(a) != set(b):
        raise SystemExit('the halves must play the same seeds')
    effects, seating = {}, {}
    for s in a:
        d_a, d_b = a[s] / ra[s], b[s] / rb[s]
        effects[s] = (d_a - d_b) / 2
        seating[s] = (d_a + d_b) / 2
    return effects, seating


DIAG_KEYS = ['points', 'offers', 'offers_accepted', 'counters', 'counters_accepted',
             'declined', 'accepted_others', 'player_trades', 'bank_trades',
             'cards_discarded', 'development_bought', 'cities_built',
             'settlements_built', 'roads_built', 'sites_lost', 'times_robbed']


def diagnostics(rows, candidate_slot):
    """Mean per-game diagnostics per lineup slot over completed games."""
    slots = []
    games = 0
    robber = {s: {'moves': 0, 'leader_hex': 0, 'steal_leader': 0} for s in range(4)}
    for r in rows:
        if r['game'].get('status') != 'completed':
            continue
        games += 1
        if not slots:
            slots = [{k: [] for k in DIAG_KEYS + ['ms_per_decision']} for _ in r['slots']]
        for record in r['game']['seats']:
            slot = r['slots'][record['seat']]
            for k in DIAG_KEYS:
                slots[slot][k].append(record.get(k, 0))
            decisions = record.get('decisions', 0)
            if decisions:
                slots[slot]['ms_per_decision'].append(record['decision_ms'] / decisions)
        for move in r['game'].get('robber_moves', []):
            slot = r['slots'][move['player']]
            robber[slot]['moves'] += 1
            robber[slot]['leader_hex'] += int(move['hex'] == move['leader_hex'])
            robber[slot]['steal_leader'] += int(move['victim'] == move['leader'])
    out = []
    for slot, values in enumerate(slots):
        row = {'slot': slot}
        for k in DIAG_KEYS + ['ms_per_decision']:
            row[k] = sum(values[k]) / len(values[k]) if values[k] else None
        moves = robber[slot]['moves']
        row['robber_moves'] = moves / games if games else None
        row['share_leader_hex'] = robber[slot]['leader_hex'] / moves if moves else None
        row['share_steal_leader'] = robber[slot]['steal_leader'] / moves if moves else None
        out.append(row)
    for row in out:
        row['role'] = 'candidate' if row['slot'] == candidate_slot else (
            'control' if row['slot'] == (1 - candidate_slot) else 'other')
    return out, games


def pooled_diag(diags_a, diags_b):
    """Average candidate and control rows across the two halves of a pair."""
    pooled = {}
    for role in ('candidate', 'control'):
        a = next(d for d in diags_a if d['role'] == role)
        b = next(d for d in diags_b if d['role'] == role)
        pooled[role] = {k: (a[k] + b[k]) / 2 if a[k] is not None and b[k] is not None else None
                        for k in a if k not in ('slot', 'role')}
    return pooled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    pair = sub.add_parser('pair')
    pair.add_argument('half_a', help='run id or games.jsonl with the candidate in slot 0')
    pair.add_argument('half_b', help='run id or games.jsonl with the candidate in slot 1')
    pool = sub.add_parser('pool')
    pool.add_argument('runs', nargs=4, help='half A, half B of each pair, in order')
    args = parser.parse_args()
    if args.command == 'pair':
        a_rows, b_rows = load(args.half_a), load(args.half_b)
        effects, seating = pair_effects(a_rows, b_rows)
        effect, effect_ci = interval(list(effects.values()))
        seat, seat_ci = interval(list(seating.values()))
        print(f"seeds: {len(effects)}")
        print(f"seating-corrected effect: {effect:+.3f} wins per game "
              f"(95% interval {effect_ci[0]:+.3f} to {effect_ci[1]:+.3f})")
        print(f"seating term: {seat:+.3f} wins per game "
              f"(95% interval {seat_ci[0]:+.3f} to {seat_ci[1]:+.3f})")
        diags_a, games_a = diagnostics(a_rows, 0)
        diags_b, games_b = diagnostics(b_rows, 1)
        pooled = pooled_diag(diags_a, diags_b)
        print(f"games per half: {games_a}, {games_b}")
        for role in ('candidate', 'control'):
            d = pooled[role]
            print(f"{role}: {json.dumps({k: (round(v, 3) if v is not None else None) for k, v in d.items()})}")
    else:
        pairs = [(load(args.runs[i]), load(args.runs[i + 1])) for i in range(0, len(args.runs), 2)]
        all_effects = []
        for a_rows, b_rows in pairs:
            effects, _ = pair_effects(a_rows, b_rows)
            all_effects.extend(effects.values())
        seeds = len(all_effects)
        mean, ci = interval(all_effects)
        print(f"pooled over {len(pairs)} pairs, {seeds} seeds: {mean:+.3f} wins per game "
              f"(95% interval {ci[0]:+.3f} to {ci[1]:+.3f}); after-the-fact pooling")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Seating-corrected effects and robber diagnostics for the robber-tables arms.

Each pair is two runs of the same seeds: half A seats the arm in slot 0 with the
tables-leaf control in slot 1, half B the control in slot 0 with the arm in slot 1.
The seating-corrected effect is the per-seed half-difference of the two
slot-0-minus-slot-1 contrasts and the seating term their half-sum, each with a
normal-approximation 95 percent interval over seeds. Wins, points, and decision
times come from each run's summary. The robber diagnostics pool both halves and
count, for the arm seats and the control seats, the share of robber moves that
land on the points leader's highest-pip hex and the victim distribution by
opponent seat.
"""
import argparse
import json
import math
from collections import Counter
from pathlib import Path


def load_games(folder):
    rows = []
    for line in (Path(folder) / 'games.jsonl').read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if row['game'].get('status') == 'completed':
                rows.append(row)
    return rows


def load_summary(folder):
    return json.loads((Path(folder) / 'summary.json').read_text())


def per_seed(rows):
    diffs = Counter()
    counts = Counter()
    for row in rows:
        diffs[row['seed']] += (row['winner_slot'] == 0) - (row['winner_slot'] == 1)
        counts[row['seed']] += 1
    return {s: diffs[s] / counts[s] for s in diffs}


def mean_ci(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def robber_stats(rows, focal_slots):
    """Robber moves made by the focal slots: leader-hex share and victim distribution."""
    moves = 0
    on_leader_hex = 0
    robbed_leader = 0
    victims = Counter()
    for row in rows:
        seat_to_slot = {seat: slot for slot, seat in enumerate(row['slots'])}
        for move in row['game'].get('robber_moves', []):
            slot = seat_to_slot[move['player']]
            if slot not in focal_slots:
                continue
            moves += 1
            if move.get('leader_hex') is not None and move['hex'] == move['leader_hex']:
                on_leader_hex += 1
            if move.get('victim') is not None:
                if move['victim'] == move['leader']:
                    robbed_leader += 1
                victims[seat_to_slot[move['victim']]] += 1
    return {'moves': moves, 'on_leader_hex': on_leader_hex, 'robbed_leader': robbed_leader,
            'victims': victims}


def merge(*stats):
    out = {'moves': 0, 'on_leader_hex': 0, 'robbed_leader': 0, 'victims': Counter()}
    for s in stats:
        for key in ('moves', 'on_leader_hex', 'robbed_leader'):
            out[key] += s[key]
        out['victims'] += s['victims']
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pairs', nargs='+', help='label:halfA_run_dir:halfB_run_dir')
    args = parser.parse_args()
    print('| Arm | Effect | 95% interval | Seating term (95% interval) | Arm wins | Control wins | Arm ms | Control ms |')
    print('| --- | --- | --- | --- | ---: | ---: | ---: | ---: |')
    details = []
    for spec in args.pairs:
        label, half_a, half_b = spec.split(':')
        rows_a, rows_b = load_games(half_a), load_games(half_b)
        sum_a, sum_b = load_summary(half_a), load_summary(half_b)
        a, b = per_seed(rows_a), per_seed(rows_b)
        seeds = sorted(set(a) & set(b))
        effect, lo, hi = mean_ci([(a[s] - b[s]) / 2 for s in seeds])
        seat, slo, shi = mean_ci([(a[s] + b[s]) / 2 for s in seeds])
        arm_wins = sum(r['winner_slot'] == 0 for r in rows_a) + sum(r['winner_slot'] == 1 for r in rows_b)
        ctl_wins = sum(r['winner_slot'] == 1 for r in rows_a) + sum(r['winner_slot'] == 0 for r in rows_b)
        arm_ms = (sum_a['slots'][0]['mean_decision_ms'] * sum_a['completed']
                  + sum_b['slots'][1]['mean_decision_ms'] * sum_b['completed']) \
            / (sum_a['completed'] + sum_b['completed'])
        ctl_ms = (sum_a['slots'][1]['mean_decision_ms'] * sum_a['completed']
                  + sum_b['slots'][0]['mean_decision_ms'] * sum_b['completed']) \
            / (sum_a['completed'] + sum_b['completed'])
        print(f'| {label} | {effect:+.3f} | {lo:+.3f} to {hi:+.3f} | {seat:+.3f} ({slo:+.3f} to {shi:+.3f}) '
              f'| {arm_wins} | {ctl_wins} | {arm_ms:.0f} | {ctl_ms:.0f} |')
        arm_stats = merge(robber_stats(rows_a, {0}), robber_stats(rows_b, {1}))
        ctl_stats = merge(robber_stats(rows_a, {1}), robber_stats(rows_b, {0}))
        details.append((label, arm_stats, ctl_stats, len(seeds)))
    print()
    print('Robber moves of the focal seats, pooled over both halves of each pair.')
    print('| Arm | Seat | Moves | On leader best hex | Robbed the leader | Victim: other search | Victim: slot 2 | Victim: slot 3 |')
    print('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |')
    for label, arm_stats, ctl_stats, n in details:
        for name, s in (('arm', arm_stats), ('control', ctl_stats)):
            m = s['moves'] or 1
            v = s['victims']
            total_victims = sum(v.values()) or 1
            other = v[0] + v[1]
            print(f'| {label} | {name} | {s["moves"]} | {s["on_leader_hex"]} ({s["on_leader_hex"] / m:.1%}) '
                  f'| {s["robbed_leader"]} ({s["robbed_leader"] / m:.1%}) '
                  f'| {other} ({other / total_victims:.1%}) | {v[2]} ({v[2] / total_victims:.1%}) '
                  f'| {v[3]} ({v[3] / total_victims:.1%}) |')


if __name__ == '__main__':
    main()

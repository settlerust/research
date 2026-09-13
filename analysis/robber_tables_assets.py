#!/usr/bin/env python3
"""Assets for the robber-tables study: the pooled seating-corrected effect of each
arm in each lineup, and the robber-placement shares of the arm and control seats.
Every value is computed from the retained run folders named below."""
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

# (label, [(stage, half A run, half B run), ...]) — half A seats the arm in slot 0.
ARMS = [
    ("leader", [
        ("runs/00c2cbe1-592c-445c-a843-e44996943007", "runs/38728ce3-fa05-495d-97f2-58ff22f98b77"),
        ("runs/8129fb6c-36c6-495d-aee5-3771ffc81add", "runs/026bd4f5-7a8b-40b0-b4e3-239e17a3daa3"),
    ], [
        ("runs/6b0408e8-f320-4a9a-bb12-0dfe95ece0fb", "runs/44be36ac-3467-4caa-9ef7-d209f7dd5242"),
    ]),
    ("need", [
        ("runs/5c2f8ab4-bbe1-44e5-aed0-c9cc394c9f7d", "runs/c8749e28-9907-4ee7-a427-3ba033ac8943"),
        ("runs/20b15545-5d1a-4640-968c-77aae8aba3a9", "runs/3c579646-cf00-439f-937d-6a0e93122bcf"),
        ("runs/54d7090b-182d-402a-a8cd-3676029d2cb6", "runs/d55af6e8-087b-40a4-8d89-23b048cb3465"),
    ], [
        ("runs/a75e3de9-2103-4777-b6ef-536c2b6bd194", "runs/2b2182d5-1106-4372-84e4-0e2a9688d011"),
        ("runs/33d3b566-cab8-4f89-a773-f636998ee8f8", "runs/da3ec107-4a6d-48ec-8f63-fec5f70572d9"),
    ]),
    ("threat", [
        ("runs/47060353-4746-495b-bea5-dfbb485016af", "runs/e0c6acab-fc5c-4f6e-8c26-74f4e8c730dc"),
        ("runs/227b8813-f6db-467e-8097-209dd66c1323", "runs/059e8938-8aa0-48ef-9172-a5639f7a6149"),
    ], [
        ("runs/7a435890-2fcb-4d51-8770-d952f457ae39", "runs/8319a450-6849-42e7-b7c4-272c847b2f03"),
    ]),
    ("block leader", [
        ("runs/2321b99f-1592-480e-a057-4b76f6627586", "runs/56625a37-fd84-4006-9966-c4a0148b9f53"),
        ("runs/d8adbaf5-38ab-480b-a537-cab33ff0b188", "runs/6278b419-683c-40ac-b88d-0bcb277ed647"),
        ("runs/06d296f3-c13c-4853-9157-15ba7be1ad82", "runs/38ecd1ca-3d73-49a7-987a-90ba4d73907f"),
    ], [
        ("runs/f2207f5e-8fd8-4891-8be1-529e52d2611e", "runs/a626fe42-d01b-416a-bfd5-2edac7a9823c"),
        ("runs/3a4f4e34-a565-46c4-abb0-5574f3d326b1", "runs/844109d4-ad9d-446a-9970-c0e36661d689"),
    ]),
    ("need + block leader", [
        ("runs/9e11f6ff-3e1a-4000-9f4c-73fdb3e4de1d", "runs/ffc247e0-2b08-446f-9052-de608430f6e5"),
    ], [
        ("runs/97c0c56c-0b81-4972-ab29-961d3c4ff888", "runs/3d8efaee-2a46-459d-ae24-191ebdbc9b52"),
    ]),
]


def load(run):
    rows = []
    for line in (ROOT / run / 'games.jsonl').read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r['game'].get('status') == 'completed':
                rows.append(r)
    return rows


def per_seed(rows):
    diffs, counts = Counter(), Counter()
    for row in rows:
        diffs[row['seed']] += (row['winner_slot'] == 0) - (row['winner_slot'] == 1)
        counts[row['seed']] += 1
    return {s: diffs[s] / counts[s] for s in diffs}


def effects(pairs):
    vals = []
    for A, B in pairs:
        a, b = per_seed(load(A)), per_seed(load(B))
        vals += [(a[s] - b[s]) / 2 for s in sorted(set(a) & set(b))]
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / max(1, len(vals) - 1))
    se = sd / math.sqrt(len(vals))
    return len(vals), mean, mean - 1.96 * se, mean + 1.96 * se


def placement(pairs):
    """Share of robber moves on the leader's best hex and robbing the leader,
    pooled over the arm seats and the control seats of the pair halves."""
    arm = Counter()
    control = Counter()
    for A, B in pairs:
        for rows, focal in ((load(A), {0}), (load(B), {1})):
            for row in rows:
                s2s = {seat: slot for slot, seat in enumerate(row['slots'])}
                for move in row['game'].get('robber_moves', []):
                    if s2s[move['player']] not in focal:
                        continue
                    target = arm if s2s[move['player']] in focal else control
                    target['moves'] += 1
                    if move.get('leader_hex') is not None and move['hex'] == move['leader_hex']:
                        target['hex'] += 1
                    if move.get('victim') is not None and move['victim'] == move['leader']:
                        target['leader'] += 1
        for rows, focal in ((load(A), {1}), (load(B), {0})):
            for row in rows:
                s2s = {seat: slot for slot, seat in enumerate(row['slots'])}
                for move in row['game'].get('robber_moves', []):
                    if s2s[move['player']] not in focal:
                        continue
                    control['moves'] += 1
                    if move.get('leader_hex') is not None and move['hex'] == move['leader_hex']:
                        control['hex'] += 1
                    if move.get('victim') is not None and move['victim'] == move['leader']:
                        control['leader'] += 1
    return (arm['hex'] / arm['moves'], arm['leader'] / arm['moves'],
            control['hex'] / control['moves'], control['leader'] / control['moves'])


def main():
    ticks, points = [], []
    lo_all, hi_all = [], []
    for label, builders, population in ARMS:
        for lineup, pairs in (('builders', builders), ('population', population)):
            n, mean, lo, hi = effects(pairs)
            ticks.append(f'{label}, {lineup}')
            points.append({'x': len(ticks) - 1, 'y': round(mean, 4),
                           'low': round(lo, 4), 'high': round(hi, 4)})
            lo_all.append(lo)
            hi_all.append(hi)
    data = {
        'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'evidence': 'measured',
        'title': 'Robber-switch effects under the learned leaf',
        'source': (
            'Swapped-pair engine-arena cohorts under containment/robber-tables: each arm '
            'against the unchanged tables-leaf control, half A with the arm in slot 0 and '
            'half B with it in slot 1, both halves on the same 64 deterministic seeds per '
            'stage. The point is the pooled seating-corrected effect, half the per-seed '
            'difference of the two contrasts, over every stage of the arm in that lineup; '
            'run IDs are listed in the robber-tables report.'
        ),
        'caption': 'Wins per game of each arm over the unchanged tables-leaf control, pooled over its stages in each lineup; the builders lineup seats eta and fast, the population lineup a third search.',
        'x': {'label': 'Arm and lineup', 'min': 0, 'max': len(ticks) - 1, 'ticks': ticks},
        'y': {'label': 'Wins per game, arm minus control',
              'min': round(min(lo_all + [-0.05]) - 0.01, 2),
              'max': round(max(hi_all + [0.05]) + 0.01, 2)},
        'series': [{'label': 'Seating-corrected effect (95% interval)', 'points': points}],
        'reference': {'y': 0, 'label': 'no difference'},
    }
    write_json(ROOT / 'content/assets/robber-tables-effects.json', data)
    print(f'wrote content/assets/robber-tables-effects.json with {len(points)} points')

    ticks = [label for label, _, _ in ARMS]
    hex_arm, hex_ctl, lead_arm, lead_ctl = [], [], [], []
    for label, builders, population in ARMS:
        ah, al, ch, cl = placement(builders + population)
        hex_arm.append(ah)
        hex_ctl.append(ch)
        lead_arm.append(al)
        lead_ctl.append(cl)
    def series(label, values):
        return {'label': label, 'points': [{'x': i, 'y': round(v, 4)} for i, v in enumerate(values)]}
    data = {
        'schema': 1, 'kind': 'plot', 'variant': 'bar', 'evidence': 'measured',
        'title': 'Where the robber goes under each arm',
        'source': (
            'Robber-move records of the same swapped-pair cohorts, pooled over both halves '
            'and every stage of each arm: the share of the arm seats and control seats '
            'placing the robber on the points leader highest-pip hex (cities double) and '
            'robbing the points leader among the mover rivals.'
        ),
        'caption': 'Share of robber moves landing on the leader best hex and robbing the leader, arm seats against control seats.',
        'x': {'label': 'Arm', 'min': 0, 'max': len(ticks) - 1, 'ticks': ticks},
        'y': {'label': 'Share of robber moves', 'min': 0.0, 'max': 0.6},
        'series': [
            series('On the leader best hex, arm seat', hex_arm),
            series('On the leader best hex, control seat', hex_ctl),
            series('Robbed the leader, arm seat', lead_arm),
            series('Robbed the leader, control seat', lead_ctl),
        ],
    }
    write_json(ROOT / 'content/assets/robber-tables-placement.json', data)
    print('wrote content/assets/robber-tables-placement.json')


if __name__ == '__main__':
    main()

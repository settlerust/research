"""Seating-corrected effects and trade diagnostics of the bargaining switches under the learned leaf.

Every pair in the registry is two engine-arena cohorts on the same seeds: half A seats the arm
(the tables baseline with one bargaining switch off) in slot 0 and the control in slot 1, half B
the reverse. The effect of the arm is the per-seed half-difference of the two slot-0-minus-slot-1
contrasts and the seating term their half-sum, each with a normal 95% interval over seeds. The
diagnostics pool both halves and compare the arm's slot with the control's slot: offers made and
accepted, counters made and taken, declines, offers of others accepted, player and bank trades,
points, and mean decision time. Pooled estimates over stages are after-the-fact pooling.

    python3 analysis/bargaining_tables.py analysis/bargaining_tables.json [--assets]
"""
import argparse
import collections
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

COUNTS = ['offers', 'offers_accepted', 'counters', 'counters_accepted', 'declined', 'accepted_others',
          'player_trades', 'bank_trades', 'cards_discarded', 'cities_built', 'settlements_built',
          'development_bought', 'points']
STAGE_NAMES = {'l2-800': 'L2 800-863', 'l1-0': 'L1 0-63', 'l1-800': 'L1 800-863',
               'l2-864': 'L2 864-927', 'l1-864': 'L1 864-927'}
ARM_NAMES = {'all-off': 'all off', 'threat-off': 'threat pricing off', 'counters-off': 'counters off',
             'asks-off': 'asks off', 'stubborn': 'stubborn (refuses asks)'}


def latest_run(experiment):
    runs = []
    for manifest in (ROOT / 'runs').glob('*/manifest.json'):
        data = json.loads(manifest.read_text())
        if data.get('experiment') == experiment and (manifest.parent / 'summary.json').exists():
            summary = json.loads((manifest.parent / 'summary.json').read_text())
            if summary.get('status') == 'completed':
                runs.append((data['created_at'], manifest.parent.name, summary))
    return sorted(runs)[-1] if runs else None


def games(run_id):
    rows = [json.loads(line) for line in (ROOT / 'runs' / run_id / 'games.jsonl').read_text().splitlines() if line.strip()]
    return [r for r in rows if r['game']['status'] == 'completed']


def per_seed(rows):
    """Slot 0 wins minus slot 1 wins per seed, averaged over that seed's rotations."""
    by = {}
    for r in rows:
        by.setdefault(r['seed'], []).append((r['winner_slot'] == 0) - (r['winner_slot'] == 1))
    return {seed: sum(v) / len(v) for seed, v in by.items()}


def interval(values):
    xs = list(values)
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / max(1, len(xs) - 1))
    se = sd / math.sqrt(len(xs))
    return {'mean': mean, 'low': mean - 1.96 * se, 'high': mean + 1.96 * se, 'seeds': len(xs)}


def fmt(c):
    return f"{c['mean']:+.3f} ({c['low']:+.3f} to {c['high']:+.3f})"


def slot_means(rows, slot):
    """Means over completed games of the arena's per-seat counters for one slot."""
    totals = collections.Counter()
    ms = 0.0
    decisions = 0
    for r in rows:
        i = r['slots'].index(slot)
        seat = r['game']['seats'][i]
        for key in COUNTS:
            totals[key] += seat.get(key, 0)
        ms += seat['decision_ms']
        decisions += seat['decisions']
    out = {k: totals[k] / len(rows) for k in COUNTS}
    out['decision_ms'] = ms / decisions if decisions else 0.0
    out['games'] = len(rows)
    return out


def combine(a, b):
    """Pool two per-slot diagnostic means by their game counts."""
    n = a['games'] + b['games']
    out = {k: (a[k] * a['games'] + b[k] * b['games']) / n for k in a if k != 'games'}
    out['games'] = n
    return out


def pair(entry):
    a, b = latest_run(entry['half_a']), latest_run(entry['half_b'])
    if not (a and b):
        return None
    rows_a, rows_b = games(a[1]), games(b[1])
    sa, sb = per_seed(rows_a), per_seed(rows_b)
    seeds = sorted(set(sa) & set(sb))
    effects = {s: (sa[s] - sb[s]) / 2 for s in seeds}
    seating = {s: (sa[s] + sb[s]) / 2 for s in seeds}
    arm = combine(slot_means(rows_a, 0), slot_means(rows_b, 1))
    control = combine(slot_means(rows_a, 1), slot_means(rows_b, 0))
    return {**entry, 'runs': [a[1], b[1]], 'summaries': [a[2], b[2]],
            'contrast_a': interval(sa[s] for s in seeds), 'contrast_b': interval(sb[s] for s in seeds),
            'effect': interval(effects.values()), 'seating': interval(seating.values()),
            'per_seed_effect': effects,
            'arm_wins': a[2]['slots'][0]['wins'] + b[2]['slots'][1]['wins'],
            'control_wins': a[2]['slots'][1]['wins'] + b[2]['slots'][0]['wins'],
            'completed': a[2]['completed'] + b[2]['completed'],
            'planned': a[2]['planned'] + b[2]['planned'],
            'arm': entry['arm'], 'arm_diag': arm, 'control_diag': control}


def pooled(results):
    """After-the-fact pooling of per-seed effects over several pairs on disjoint seeds."""
    values = []
    for r in results:
        values.extend(r['per_seed_effect'].values())
    return interval(values) if values else None


def forest(results, name, title, caption, source):
    points, ticks = [], []
    for r in results:
        c = r['effect']
        points.append({'x': len(points), 'y': round(c['mean'], 4), 'low': round(c['low'], 4), 'high': round(c['high'], 4)})
        ticks.append(r['tick'])
    lo = min(p['low'] for p in points) - 0.05
    hi = max(p['high'] for p in points) + 0.05
    data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'title': title, 'evidence': 'measured',
            'source': source, 'caption': caption,
            'x': {'label': 'Arm and stage', 'min': 0, 'max': len(points) - 1, 'ticks': ticks},
            'y': {'label': 'Wins per game, arm minus control, seating corrected',
                  'min': round(min(lo, -0.05), 2), 'max': round(max(hi, 0.05), 2)},
            'series': [{'label': 'Seating-corrected effect (95% interval over seeds)', 'points': points}],
            'reference': {'y': 0, 'label': 'no difference'}}
    write_json(ROOT / 'content/assets' / f'{name}.json', data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry')
    parser.add_argument('--assets', action='store_true', help='write the plot assets under content/assets/')
    parser.add_argument('--tables', action='store_true', help='print the report tables as markdown')
    args = parser.parse_args()
    registry = json.load(open(args.registry))
    results = [p for p in (pair(e) for e in registry['pairs']) if p]
    stages = []
    for r in results:
        if r['stage'] not in stages:
            stages.append(r['stage'])
    for stage in stages:
        print(f"== {STAGE_NAMES.get(stage, stage)}")
        for r in [x for x in results if x['stage'] == stage]:
            print(f"{ARM_NAMES[r['arm']]:24} A {r['runs'][0][:8]} {fmt(r['contrast_a'])}  B {r['runs'][1][:8]} {fmt(r['contrast_b'])}")
            print(f"{'':24} effect {fmt(r['effect'])}  seating {fmt(r['seating'])}  arm {r['arm_wins']} control {r['control_wins']} "
                  f"of {r['completed']}/{r['planned']}")
            for label, d in (('arm', r['arm_diag']), ('control', r['control_diag'])):
                print(f"{'':24} {label:8} offers {d['offers']:.2f} accepted {d['offers_accepted']:.2f} counters {d['counters']:.2f} "
                      f"taken {d['counters_accepted']:.2f} declined {d['declined']:.2f} took-others {d['accepted_others']:.2f} "
                      f"trades {d['player_trades']:.2f} bank {d['bank_trades']:.2f} discards {d['cards_discarded']:.2f} "
                      f"cities {d['cities_built']:.2f} dev {d['development_bought']:.2f} points {d['points']:.2f} "
                      f"decision {d['decision_ms']:.0f} ms")
    print('== pooled after the fact')
    for arm in ARM_NAMES:
        l1 = [r for r in results if r['arm'] == arm and r['lineup'] == 'L1']
        every = [r for r in results if r['arm'] == arm]
        if l1:
            print(f"{ARM_NAMES[arm]:24} L1 pooled {fmt(pooled(l1))} over {pooled(l1)['seeds']} seeds; "
                  f"all stages {fmt(pooled(every))} over {pooled(every)['seeds']} seeds")
    if args.tables:
        print('== markdown: cohorts')
        print('| Stage | Arm | Half | Registration | Run | Arm wins | Control wins | Contrast (95% interval) |')
        print('| --- | --- | --- | --- | --- | ---: | ---: | --- |')
        for r in results:
            for half, exp, run, c, arm_slot in (('A', r['half_a'], r['runs'][0], r['contrast_a'], 0),
                                                ('B', r['half_b'], r['runs'][1], r['contrast_b'], 1)):
                s = r['summaries'][0 if half == 'A' else 1]['slots']
                print(f"| {STAGE_NAMES.get(r['stage'], r['stage'])} | {ARM_NAMES[r['arm']]} | {half} | `{exp}` | `{run}` | "
                      f"{s[arm_slot]['wins']} | {s[1 - arm_slot]['wins']} | {fmt(c)} |")
        print('== markdown: effects')
        print('| Stage | Arm | Effect (95% interval) | Seating term (95% interval) | Arm wins | Control wins |')
        print('| --- | --- | --- | --- | ---: | ---: |')
        for r in results:
            print(f"| {STAGE_NAMES.get(r['stage'], r['stage'])} | {ARM_NAMES[r['arm']]} | **{fmt(r['effect'])}** | "
                  f"{fmt(r['seating'])} | {r['arm_wins']} | {r['control_wins']} |")
        print('== markdown: diagnostics (arm / control, per game, both halves pooled)')
        print('| Stage | Arm | Offers | Accepted | Counters | Taken | Declined | Took others | Trades | Bank | Points | Decision |')
        print('| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |')
        for r in results:
            a, c = r['arm_diag'], r['control_diag']
            cell = lambda k, p=2: f"{a[k]:.{p}f} / {c[k]:.{p}f}"  # noqa: E731
            print(f"| {STAGE_NAMES.get(r['stage'], r['stage'])} | {ARM_NAMES[r['arm']]} | {cell('offers', 1)} | {cell('offers_accepted')} | "
                  f"{cell('counters')} | {cell('counters_accepted')} | {cell('declined', 1)} | {cell('accepted_others')} | "
                  f"{cell('player_trades')} | {cell('bank_trades')} | {cell('points')} | {a['decision_ms']:.0f} / {c['decision_ms']:.0f} ms |")
    if args.assets and results:
        source = ('Engine-arena swapped pairs under bargaining/tables-arms: the depth-2 search with learned tables and one '
                  'bargaining switch off against the unchanged tables baseline, 64 deterministic seeds per stage played once '
                  'per rotation in both seatings (512 games per point). L1 seats an ETA and a fast builder beside the two '
                  'searches; L2 seats a third tables search and an ETA. Run IDs are listed in the report.')
        for r in results:
            r['tick'] = f"{ARM_NAMES[r['arm']]}, {STAGE_NAMES.get(r['stage'], r['stage'])}"
        forest(results, 'bargaining-tables-effects', 'Bargaining switches under the learned leaf',
               'Each point is the seating-corrected effect of turning one bargaining switch off, arm minus control, with its 95% interval over 64 seeds; negative means the default mechanism wins games.',
               source)


if __name__ == '__main__':
    main()

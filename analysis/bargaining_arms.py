"""Assets and diagnostics for the bargaining one-change arms.

Every arm seats a depth-2 search with one switch changed in slot 0 and the unchanged default
in slot 1, with an ETA and a fast builder in the other seats. Slot 1 always sits one seat after
slot 0, so a null cohort of two identical defaults measures the slot-order bias; the adjusted
contrast subtracts the null's per-seed difference from each arm's on the same boards. A swapped
pair (the changed seat in slot 0 in one cohort and in slot 1 in the other, same boards) cancels
the bias without a null: its effect is the per-seed half-difference of the two contrasts.

Every value is read from a retained run folder under runs/; the registry names experiments and
the script picks each experiment's latest completed run."""
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


def diagnostics(rows, seats):
    """Per-slot means over completed games of the arena's trade and build counters."""
    totals = collections.defaultdict(collections.Counter)
    for r in rows:
        for i, slot in enumerate(r['slots']):
            seat = r['game']['seats'][i]
            for key in COUNTS:
                totals[slot][key] += seat[key]
    return [{'slot': slot, 'seat': seats[slot], **{k: totals[slot][k] / len(rows) for k in COUNTS}}
            for slot in sorted(totals)]


def fmt(c):
    return f"{c['mean']:+.3f} ({c['low']:+.3f} to {c['high']:+.3f})"


def arm_rows(arms, null_experiment=None):
    null = None
    if null_experiment:
        run = latest_run(null_experiment)
        if run:
            null = per_seed(games(run[1]))
    out = []
    for arm in arms:
        run = latest_run(arm['experiment'])
        if not run:
            continue
        _, run_id, summary = run
        rows = games(run_id)
        seeds = per_seed(rows)
        sign = -1 if arm.get('flip') else 1
        raw = interval(sign * d for d in seeds.values())
        adjusted = None
        if null and arm['experiment'] != null_experiment and set(seeds) == set(null):
            adjusted = interval(sign * (seeds[s] - null[s]) for s in seeds)
        changed, default = (1, 0) if arm.get('flip') else (0, 1)
        out.append({'label': arm['label'], 'experiment': arm['experiment'], 'run': run_id, 'raw': raw,
                    'adjusted': adjusted, 'changed': summary['slots'][changed], 'default': summary['slots'][default],
                    'diagnostics': diagnostics(rows, [s['seat'] for s in summary['slots']])})
    return out


def forest(rows, name, title, caption, source, key):
    points, ticks = [], []
    for r in rows:
        c = r[key]
        if not c:
            continue
        points.append({'x': len(points), 'y': round(c['mean'], 4), 'low': round(c['low'], 4), 'high': round(c['high'], 4)})
        ticks.append(r['label'])
    lo = min(p['low'] for p in points) - 0.05
    hi = max(p['high'] for p in points) + 0.05
    data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'title': title, 'evidence': 'measured',
            'source': source, 'caption': caption,
            'x': {'label': 'Arm', 'min': 0, 'max': len(points) - 1, 'ticks': ticks},
            'y': {'label': 'Wins per game, changed seat minus default', 'min': round(min(lo, -0.05), 2), 'max': round(max(hi, 0.05), 2)},
            'series': [{'label': 'Paired seed contrast (95% interval)', 'points': points}],
            'reference': {'y': 0, 'label': 'no difference'}}
    write_json(ROOT / 'content/assets' / f'{name}.json', data)


def pair(first, second):
    """A swapped pair: the changed seat in slot 0 of `first` and in slot 1 of `second`."""
    a, b = latest_run(first), latest_run(second)
    if not (a and b):
        return None
    sa, sb = per_seed(games(a[1])), per_seed(games(b[1]))
    seeds = sorted(set(sa) & set(sb))
    return {'runs': [a[1], b[1]], 'first': interval(sa[s] for s in seeds), 'second': interval(sb[s] for s in seeds),
            'effect': interval((sa[s] - sb[s]) / 2 for s in seeds), 'bias': interval((sa[s] + sb[s]) / 2 for s in seeds),
            'summaries': [a[2], b[2]]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry', help='JSON: {"null": experiment, "arms": [{label, experiment, flip?}], "pair": [first, second]}')
    parser.add_argument('--out', default='bargaining-arms')
    parser.add_argument('--seeds', default='boards 0 to 63')
    args = parser.parse_args()
    registry = json.load(open(args.registry))
    rows = arm_rows(registry['arms'], registry.get('null'))
    source = (f'Engine-arena cohorts on {args.seeds}, each played once per rotation of four slots: a depth-2 search '
              'with one bargaining switch changed, the unchanged default, an ETA builder, and a fast builder. '
              'Run IDs are listed in the bargaining arms report.')
    forest(rows, f'{args.out}-raw', 'One-change bargaining arms as registered',
           f'Each point is the registered contrast, the changed seat in slot 0 minus the unchanged default in slot 1, with its 95% interval over {args.seeds}; the null arm seats two identical defaults and shows the slot-order bias.',
           source, 'raw')
    if registry.get('null'):
        forest([r for r in rows if r['adjusted']], f'{args.out}-adjusted', 'One-change bargaining arms against the null',
               f'Each point is the per-seed difference between an arm\'s contrast and the null cohort\'s on the same board, with its 95% interval over {args.seeds}; this removes the slot-order bias but was not preregistered.',
               source, 'adjusted')
    for r in rows:
        print(f"{r['label']:28} run {r['run'][:8]} changed {r['changed']['wins']:3} default {r['default']['wins']:3} "
              f"raw {fmt(r['raw'])}" + (f"  adjusted {fmt(r['adjusted'])}" if r['adjusted'] else ''))
        for d in r['diagnostics']:
            print(f"    slot {d['slot']} offers {d['offers']:.2f} accepted {d['offers_accepted']:.2f} counters {d['counters']:.2f} "
                  f"taken {d['counters_accepted']:.2f} declined {d['declined']:.2f} took-others {d['accepted_others']:.2f} "
                  f"trades {d['player_trades']:.2f} bank {d['bank_trades']:.2f} discards {d['cards_discarded']:.2f} "
                  f"cities {d['cities_built']:.2f} settlements {d['settlements_built']:.2f} dev {d['development_bought']:.2f} "
                  f"points {d['points']:.2f}  {d['seat'][:44]}")
    if registry.get('pair'):
        p = pair(*registry['pair'])
        if p:
            print(f"pair runs {p['runs'][0][:8]} (changed in slot 0) {fmt(p['first'])} and {p['runs'][1][:8]} (changed in slot 1) {fmt(p['second'])}")
            print(f"  effect of the change {fmt(p['effect'])}   slot-order bias {fmt(p['bias'])}")
            for summary in p['summaries']:
                print('  ' + ' | '.join(f"{s['seat'][:36]} {s['wins']}" for s in summary['slots']))

"""Assets and diagnostics for the arena seating diagnosis (study log/arena-seating).

Every cohort is a paired engine-arena tournament on deterministic boards, each board played once
per rotation of the four slots. The contrast of a cohort is the wins per game of one slot minus
another, per board, averaged over that board's rotations, with a 95% interval over boards. The
registry names the two slots for each cohort because the run record only reports slot 0 minus
slot 1, which is not the contrast of interest when a builder sits between the two searches.

Every value is read from a retained run folder under runs/; the script picks each experiment's
latest completed run. A cohort with a `reference` experiment also reports its per-board difference
from that reference cohort on the same boards."""
import argparse
import collections
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

COUNTS = ['points', 'settlements_built', 'cities_built', 'roads_built', 'development_bought', 'bank_trades',
          'player_trades', 'offers', 'offers_accepted', 'accepted_others', 'counters', 'counters_accepted',
          'cards_discarded', 'times_robbed']


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


def per_seed(rows, a, b):
    """Slot `a` wins minus slot `b` wins per seed, averaged over that seed's rotations."""
    by = {}
    for r in rows:
        by.setdefault(r['seed'], []).append((r['winner_slot'] == a) - (r['winner_slot'] == b))
    return {seed: sum(v) / len(v) for seed, v in by.items()}


def interval(values):
    xs = list(values)
    mean = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / max(1, len(xs) - 1))
    se = sd / math.sqrt(len(xs))
    return {'mean': mean, 'low': mean - 1.96 * se, 'high': mean + 1.96 * se, 'seeds': len(xs)}


def wins_by_seat(rows, slot):
    """Wins of a slot split by the engine seat it sat at."""
    out = collections.Counter()
    for r in rows:
        if r['winner_slot'] == slot:
            out[r['slots'].index(slot)] += 1
    return [out[seat] for seat in range(len(rows[0]['slots']))]


def diagnostics(rows, seats):
    totals = collections.defaultdict(collections.Counter)
    for r in rows:
        for i, slot in enumerate(r['slots']):
            seat = r['game']['seats'][i]
            for key in COUNTS:
                totals[slot][key] += seat[key]
    return [{'slot': slot, 'seat': seats[slot], 'wins': sum(r['winner_slot'] == slot for r in rows),
             **{k: totals[slot][k] / len(rows) for k in COUNTS}} for slot in sorted(totals)]


def fmt(c):
    return f"{c['mean']:+.3f} ({c['low']:+.3f} to {c['high']:+.3f})"


def cohort_rows(cohorts):
    out = []
    for cohort in cohorts:
        run = latest_run(cohort['experiment'])
        if not run:
            continue
        _, run_id, summary = run
        rows = games(run_id)
        a, b = cohort['slots']
        seeds = per_seed(rows, a, b)
        entry = {'label': cohort['label'], 'experiment': cohort['experiment'], 'run': run_id, 'slots': [a, b],
                 'seats': [s['seat'] for s in summary['slots']], 'wins': [s['wins'] for s in summary['slots']],
                 'contrast': interval(seeds.values()), 'by_seat': [wins_by_seat(rows, a), wins_by_seat(rows, b)],
                 'diagnostics': diagnostics(rows, [s['seat'] for s in summary['slots']]), 'reference': None,
                 'plot': cohort.get('plot', True)}
        if cohort.get('reference'):
            ref = latest_run(cohort['reference'])
            if ref:
                ref_seeds = per_seed(games(ref[1]), *cohort.get('reference_slots', [0, 1]))
                if set(ref_seeds) == set(seeds):
                    entry['reference'] = {'run': ref[1], 'difference': interval(seeds[s] - ref_seeds[s] for s in seeds)}
        out.append(entry)
    return out


def forest(rows, name, title, caption, source):
    points, ticks = [], []
    for r in rows:
        if not r.get('plot', True):
            continue
        c = r['contrast']
        points.append({'x': len(points), 'y': round(c['mean'], 4), 'low': round(c['low'], 4), 'high': round(c['high'], 4)})
        ticks.append(r['label'])
    lo = min(p['low'] for p in points) - 0.05
    hi = max(p['high'] for p in points) + 0.05
    data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'title': title, 'evidence': 'measured',
            'source': source, 'caption': caption,
            'x': {'label': 'Cohort', 'min': 0, 'max': len(points) - 1, 'ticks': ticks},
            'y': {'label': 'Wins per game, earlier seat minus later seat', 'min': round(min(lo, -0.05), 2),
                  'max': round(max(hi, 0.05), 2)},
            'series': [{'label': 'Paired board contrast (95% interval)', 'points': points}],
            'reference': {'y': 0, 'label': 'no difference'}}
    write_json(ROOT / 'content/assets' / f'{name}.json', data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry', help='JSON: {"cohorts": [{label, experiment, slots: [a, b], reference?}]}')
    parser.add_argument('--out', default='arena-seating-nulls')
    parser.add_argument('--seeds', default='boards 0 to 63')
    args = parser.parse_args()
    registry = json.load(open(args.registry))
    rows = cohort_rows(registry['cohorts'])
    source = (f'Engine-arena cohorts on {args.seeds}, each board played once per rotation of four slots, depth-2 '
              'searches with fixed builders. Run IDs are listed in the arena seating report.')
    forest(rows, args.out, 'Identical seats at different distances in turn order',
           'Each point is the wins per game of the named earlier seat minus the identical later seat, with its '
           f'95% interval over {args.seeds}; the term needs the two seats to be adjacent in turn order and survives '
           'every trade switch.', source)
    for r in rows:
        a, b = r['slots']
        print(f"{r['label']:34} run {r['run'][:8]} slots {a}-{b} wins {r['wins']} contrast {fmt(r['contrast'])}"
              + (f"  vs reference {fmt(r['reference']['difference'])}" if r['reference'] else ''))
        print(f"    wins by seat: slot {a} {r['by_seat'][0]}  slot {b} {r['by_seat'][1]}")
        for d in r['diagnostics']:
            print(f"    slot {d['slot']} wins {d['wins']:3} points {d['points']:.2f} settlements {d['settlements_built']:.2f} "
                  f"cities {d['cities_built']:.2f} roads {d['roads_built']:.2f} dev {d['development_bought']:.2f} "
                  f"bank {d['bank_trades']:.2f} trades {d['player_trades']:.2f} offers {d['offers']:.2f} "
                  f"took-others {d['accepted_others']:.2f} discards {d['cards_discarded']:.2f} "
                  f"robbed {d['times_robbed']:.2f}  {d['seat'][:40]}")

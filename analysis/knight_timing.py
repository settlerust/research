"""Contrasts and the report asset for the development-card timing study (development/knight-timing).

Every cohort is a paired engine-arena tournament on deterministic boards, each board played once
per rotation of the four slots. Slots 0 and 1 hold the candidate and the unchanged depth-2 control
(in one order or the other), slots 2 and 3 an ETA and a fast builder. Two searches in adjacent
slots carry a turn-order seating term (reports/arena-seating.mdx), so a single-seating contrast is
not an effect estimate. The knight_play_value arm was run as a swapped pair on boards 64-127: with
c1 the forward run's slot-0-minus-slot-1 contrast (candidate ahead) and c2 the swapped run's
(control ahead), the effect is (c1 - c2) / 2 and the seating term (c1 + c2) / 2.

Every value is read from a retained run folder under runs/; the script picks each experiment's
latest completed run. Run it from the research checkout: `python3 analysis/knight_timing.py`.
"""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

# experiment id -> (arm label, boards, order); 'forward' has the candidate in slot 0, 'swapped'
# has the control in slot 0.
COHORTS = {
    '000e59d2-beb5-4ad4-aeac-4210c7e6d282': ('knight_play_value', '0-63', 'forward'),
    '0b22df5c-bcdf-40cd-923e-2e484dae499d': ('buy_tempo', '0-63', 'forward'),
    '119cbcf2-9791-4dd5-a1f7-c3766b60e44d': ('hold_knight', '0-63', 'forward'),
    '20360d5d-f450-4102-8af0-83a3797f7891': ('knight_play_value', '64-127', 'forward'),
    '8f739fd6-446d-4dfc-bd2d-80c838b82ec1': ('hold_knight', '64-127', 'forward'),
    'a6371eaf-cfc2-42fb-9bde-0f86b52af778': ('knight_play_value', '64-127', 'swapped'),
}


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
    rows = (ROOT / 'runs' / run_id / 'games.jsonl').read_text().splitlines()
    return [json.loads(line) for line in rows if line.strip() and json.loads(line)['game']['status'] == 'completed']


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
    return {'mean': mean, 'se': se, 'low': mean - 1.96 * se, 'high': mean + 1.96 * se, 'seeds': len(xs)}


def fmt(c):
    return f"{c['mean']:+.3f} (95% interval {c['low']:+.3f} to {c['high']:+.3f})"


def main():
    out = {}
    for experiment, (arm, boards, order) in COHORTS.items():
        run = latest_run(experiment)
        if not run:
            raise SystemExit(f'no completed run for {experiment}')
        _, run_id, summary = run
        rows = games(run_id)
        recorded = interval(per_seed(rows, 0, 1).values())  # slot 0 minus slot 1, as registered
        cand_slot = 0 if order == 'forward' else 1
        wins = {s['slot']: s['wins'] for s in summary['slots']}
        out[experiment] = {'arm': arm, 'boards': boards, 'order': order, 'run': run_id,
                           'candidate_wins': wins[cand_slot], 'control_wins': wins[1 - cand_slot],
                           'contrast': recorded, 'slots': [summary['slots'][0], summary['slots'][1]]}
        print(f"{arm} {boards} {order}: slot0 minus slot1 {fmt(recorded)} "
              f"(candidate {wins[cand_slot]}, control {wins[1 - cand_slot]} of 256, run {run_id[:8]})")

    fwd = out['20360d5d-f450-4102-8af0-83a3797f7891']['contrast']
    swp = out['a6371eaf-cfc2-42fb-9bde-0f86b52af778']['contrast']
    se = math.sqrt(fwd['se'] ** 2 + swp['se'] ** 2) / 2
    effect = {'mean': (fwd['mean'] - swp['mean']) / 2}
    effect['low'], effect['high'] = effect['mean'] - 1.96 * se, effect['mean'] + 1.96 * se
    seating = {'mean': (fwd['mean'] + swp['mean']) / 2}
    seating['low'], seating['high'] = seating['mean'] - 1.96 * se, seating['mean'] + 1.96 * se
    print(f"knight_play_value seating-corrected effect on boards 64-127: {fmt(effect)}")
    print(f"seating term measured by the pair: {fmt(seating)}")

    singles, combined, ticks = [], [], []
    for experiment, label in [
            ('000e59d2-beb5-4ad4-aeac-4210c7e6d282', 'knight value, boards 0-63'),
            ('20360d5d-f450-4102-8af0-83a3797f7891', 'knight value, boards 64-127'),
            ('a6371eaf-cfc2-42fb-9bde-0f86b52af778', 'knight value, boards 64-127, seats swapped'),
            ('0b22df5c-bcdf-40cd-923e-2e484dae499d', 'buy tempo, boards 0-63'),
            ('119cbcf2-9791-4dd5-a1f7-c3766b60e44d', 'hold knight, boards 0-63'),
            ('8f739fd6-446d-4dfc-bd2d-80c838b82ec1', 'hold knight, boards 64-127')]:
        c = out[experiment]['contrast']
        ticks.append(label)
        singles.append({'x': len(ticks) - 1, 'y': round(c['mean'], 4),
                        'low': round(c['low'], 4), 'high': round(c['high'], 4)})
    ticks.append('knight value, seating-corrected (boards 64-127)')
    combined.append({'x': len(ticks) - 1, 'y': round(effect['mean'], 4),
                     'low': round(effect['low'], 4), 'high': round(effect['high'], 4)})
    ticks.append('turn-order term measured by the pair')
    combined.append({'x': len(ticks) - 1, 'y': round(seating['mean'], 4),
                     'low': round(seating['low'], 4), 'high': round(seating['high'], 4)})
    lo = min(p['low'] for p in singles + combined) - 0.03
    hi = max(p['high'] for p in singles + combined) + 0.03
    data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter',
            'title': 'Development-card timing arms against the unchanged control',
            'evidence': 'measured',
            'source': ('Engine-arena cohorts of 256 games on deterministic boards played once per rotation, '
                       'the candidate and the unchanged depth-2 control in the named slots with an ETA and a '
                       'fast builder. Runs ef72f172, 647d321b, 30038304 on boards 0-63 and e79ea358, f83b1214, '
                       '1d91dbfa on boards 64-127; the corrected point is half the difference of the two '
                       'knight-value pair contrasts and the turn-order point half their sum.'),
            'caption': ('Each point is one cohort\u2019s slot-0-minus-slot-1 wins per game with its 95% interval '
                        'over boards; single-seating points carry the turn-order term and the swapped-pair '
                        'combination removes it.'),
            'x': {'label': 'Cohort', 'min': 0, 'max': len(ticks) - 1, 'ticks': ticks},
            'y': {'label': 'Wins per game, slot 0 minus slot 1', 'min': round(lo, 2), 'max': round(hi, 2)},
            'series': [{'label': 'Single-seating contrast (slot 0 minus slot 1)', 'points': singles},
                       {'label': 'Swapped-pair combination', 'points': combined}]}
    write_json(ROOT / 'content/assets/knight-timing-contrasts.json', data)
    print('wrote content/assets/knight-timing-contrasts.json')


if __name__ == '__main__':
    main()

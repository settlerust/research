"""Contrasts, diagnostics, and the report asset for the hand-management study (risk/hand-management).

Every cohort is a paired engine-arena tournament on deterministic boards 0-63, each board played
once per rotation of the four slots. Slots 0 and 1 hold the candidate and the unchanged depth-2
control (in one order or the other), slots 2 and 3 an ETA and a fast builder. Two searches in
adjacent slots carry a turn-order seating term (reports/arena-seating.mdx), so a single-seating
contrast is not an effect estimate. The discard_projection arm was run as a swapped pair: with c1
the forward run's slot-0-minus-slot-1 contrast (candidate ahead) and c2 the swapped run's (control
ahead), the effect is (c1 - c2) / 2 and the seating term (c1 + c2) / 2.

Every value is read from a retained run folder under runs/; the script picks each experiment's
latest completed run. Run it from the research checkout: `python3 analysis/hand_management.py`.
"""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402

# experiment id -> (arm label, order); 'forward' seats the candidate in slot 0, 'swapped' in slot 1.
COHORTS = {
    '47486c2e-9555-4c4f-a444-7a0097dce271': ('spend_down', 'forward'),
    'd09eaccb-ab3b-4d1f-9b2e-904cf4cf89e9': ('discard_projection', 'forward'),
    'a78e5220-68c6-4726-a1cc-3a6849ac19f6': ('hand_risk 0', 'forward'),
    'e79ff8a3-f22e-4590-b9cc-67e17a2b0c20': ('hand_risk 2', 'forward'),
    '1a506239-e401-4340-a08c-8c948248fc30': ('hand_risk 4', 'forward'),
    '945e89c0-4928-421b-82d3-f003526cb7ed': ('discard_projection', 'swapped'),
}
DIAGNOSTICS = ['cards_discarded', 'turns_over_limit', 'times_robbed', 'bank_trades']


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
    for experiment, (arm, order) in COHORTS.items():
        run = latest_run(experiment)
        if not run:
            raise SystemExit(f'no completed run for {experiment}')
        _, run_id, summary = run
        rows = games(run_id)
        diffs = per_seed(rows, 0, 1)
        recorded = interval(diffs.values())  # slot 0 minus slot 1, as registered
        cand_slot = 0 if order == 'forward' else 1
        wins = {s['slot']: s['wins'] for s in summary['slots']}
        diag = {k: (summary['slots'][cand_slot]['builds'].get(k),
                    summary['slots'][1 - cand_slot]['builds'].get(k)) for k in DIAGNOSTICS}
        out[experiment] = {'arm': arm, 'order': order, 'run': run_id, 'per_seed': diffs,
                           'candidate_wins': wins[cand_slot], 'control_wins': wins[1 - cand_slot],
                           'contrast': recorded, 'diagnostics': diag}
        print(f"{arm} {order}: slot0 minus slot1 {fmt(recorded)} "
              f"(candidate {wins[cand_slot]}, control {wins[1 - cand_slot]} of 256, run {run_id[:8]})")
        for k, (cand, ctrl) in diag.items():
            print(f"    {k}: candidate {cand:.2f}, control {ctrl:.2f} per game")

    fwd = out['d09eaccb-ab3b-4d1f-9b2e-904cf4cf89e9']['per_seed']
    swp = out['945e89c0-4928-421b-82d3-f003526cb7ed']['per_seed']
    assert set(fwd) == set(swp), 'the halves must play the same seeds'
    # Per seed: the effect is half the difference of the two contrasts, the term half their sum.
    effect = interval((fwd[s] - swp[s]) / 2 for s in sorted(fwd))
    seating = interval((fwd[s] + swp[s]) / 2 for s in sorted(fwd))
    print(f"discard_projection seating-corrected effect: {fmt(effect)}")
    print(f"seating term measured by the pair: {fmt(seating)}")

    singles, combined, ticks = [], [], []
    for experiment, label in [
            ('47486c2e-9555-4c4f-a444-7a0097dce271', 'spend down'),
            ('d09eaccb-ab3b-4d1f-9b2e-904cf4cf89e9', 'discard projection'),
            ('945e89c0-4928-421b-82d3-f003526cb7ed', 'discard projection, seats swapped'),
            ('a78e5220-68c6-4726-a1cc-3a6849ac19f6', 'hand_risk 0'),
            ('e79ff8a3-f22e-4590-b9cc-67e17a2b0c20', 'hand_risk 2'),
            ('1a506239-e401-4340-a08c-8c948248fc30', 'hand_risk 4')]:
        c = out[experiment]['contrast']
        ticks.append(label)
        singles.append({'x': len(ticks) - 1, 'y': round(c['mean'], 4),
                        'low': round(c['low'], 4), 'high': round(c['high'], 4)})
    ticks.append('discard projection, seating-corrected')
    combined.append({'x': len(ticks) - 1, 'y': round(effect['mean'], 4),
                     'low': round(effect['low'], 4), 'high': round(effect['high'], 4)})
    ticks.append('turn-order term measured by the pair')
    combined.append({'x': len(ticks) - 1, 'y': round(seating['mean'], 4),
                     'low': round(seating['low'], 4), 'high': round(seating['high'], 4)})
    lo = min(p['low'] for p in singles + combined) - 0.03
    hi = max(p['high'] for p in singles + combined) + 0.03
    data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter',
            'title': 'Hand-management arms against the unchanged control',
            'evidence': 'measured',
            'source': ('Engine-arena cohorts of 256 games on deterministic boards 0-63 played once per '
                       'rotation, the candidate and the unchanged depth-2 control in the named slots with '
                       'an ETA and a fast builder. Runs 901f81f4, dd2a5d1f, 2bae826e, 2f8fae6e, af6fcb03, '
                       'and 43215190 with the seats swapped; the corrected point is half the difference of '
                       'the two projection contrasts and the turn-order point half their sum.'),
            'caption': ('Each point is one cohort\u2019s slot-0-minus-slot-1 wins per game with its 95% interval '
                        'over boards; single-seating points carry the turn-order term and the swapped-pair '
                        'combination removes it.'),
            'x': {'label': 'Cohort', 'min': 0, 'max': len(ticks) - 1, 'ticks': ticks},
            'y': {'label': 'Wins per game, slot 0 minus slot 1', 'min': round(lo, 2), 'max': round(hi, 2)},
            'series': [{'label': 'Single-seating contrast (slot 0 minus slot 1)', 'points': singles},
                       {'label': 'Swapped-pair combination', 'points': combined}]}
    write_json(ROOT / 'content/assets/hand-management-contrasts.json', data)
    print('wrote content/assets/hand-management-contrasts.json')


if __name__ == '__main__':
    main()

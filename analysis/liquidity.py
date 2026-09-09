"""Recompute the first policy study from immutable, verified whole-game artifacts.

Usage: python3 -m analysis.liquidity RUN_UUID
Writes compact measured exhibits plus ignored per-game analysis rows. Never reads
participant credentials, observations, process logs, or authoritative hidden state.
"""
from collections import Counter
import json
import math
from pathlib import Path
import random
import statistics
import sys

from harness.publish import run_path, verified_inventory
from harness.records import digest, write_json


def exact_win_test(candidate, control):
    """One-sided conditional binomial test of equal focal-slot win probabilities."""
    n = candidate + control
    return sum(math.comb(n, k) for k in range(candidate, n + 1)) / 2**n if n else 1.0


def analyze(root, run_id):
    folder = run_path(root, run_id)
    verified_inventory(folder)
    summary = json.loads((folder / 'summary.json').read_text())
    if summary['status'] != 'completed' or summary['completed'] != summary['planned']:
        raise ValueError('Primary analysis requires the entire preregistered cohort; retain partial runs separately')
    manifest = json.loads((folder / 'manifest.json').read_text())
    if manifest['players'] != ['liquidity', 'eta-control', 'fast-control', 'fast-control']:
        raise ValueError('Unexpected competitor slot mapping')
    rows = []
    for path in sorted(folder.glob('match-*/result.json')):
        result = json.loads(path.read_text())
        if result['status'] != 'completed' or not result['history_complete']:
            raise ValueError('Incomplete match or spectator history')
        slots = result['slots']
        metrics = [Counter() for _ in slots]
        for line in (path.parent / 'events.jsonl').read_text().splitlines():
            for event in json.loads(line)['events']:
                if event['type'] != 'rule':
                    continue
                rule = event['event']
                if 'player' not in rule:
                    continue
                slot = slots[rule['player']]
                metrics[slot][rule['type']] += 1
                if rule['type'] == 'discarded':
                    metrics[slot]['discarded_cards'] += rule['count']
        points = [result['points'][slots.index(slot)] for slot in range(4)]
        winner = slots[result['winner']]
        rows.append(dict(index=result['index'], game_id=result['game_id'], slots=slots,
                         winner_slot=winner, points=points, metrics=metrics,
                         turns=result['turns'], duration_seconds=result['duration_seconds'],
                         contrast=1 if winner == 0 else -1 if winner == 1 else 0))
    n = len(rows)
    wins = Counter(r['winner_slot'] for r in rows)
    contrasts = [r['contrast'] for r in rows]
    # Analysis-only resampling RNG; it is never passed to a game or a policy.
    rng = random.Random(20260908)
    boot = sorted(statistics.mean(rng.choices(contrasts, k=n)) for _ in range(20000))
    means = [{metric: statistics.mean(r['metrics'][slot][metric] for r in rows)
              for metric in ['bank_traded', 'discarded_cards', 'built_city', 'built_road']}
             for slot in range(4)]
    result = dict(run_id=run_id, n=n, wins=[wins[i] for i in range(4)],
                  win_difference=statistics.mean(contrasts),
                  exploratory_bootstrap95=[boot[499], boot[19499]],
                  exact_one_sided_p=exact_win_test(wins[0], wins[1]),
                  mean_points=[statistics.mean(r['points'][s] for r in rows) for s in range(4)],
                  mean_metrics=means,
                  mean_point_difference=statistics.mean(r['points'][0]-r['points'][1] for r in rows),
                  score_ahead=sum(r['points'][0] > r['points'][1] for r in rows),
                  score_tied=sum(r['points'][0] == r['points'][1] for r in rows),
                  score_behind=sum(r['points'][0] < r['points'][1] for r in rows),
                  total_seconds=sum(r['duration_seconds'] for r in rows),
                  mean_turns=statistics.mean(r['turns'] for r in rows))
    result['meets_rule'] = result['win_difference'] >= .10 and result['exact_one_sided_p'] <= .05
    output = root / '.runtime/analysis' / run_id
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / 'games.json', rows)
    write_json(output / 'analysis.json', result)
    source = (f"Run {run_id}; verified inventory SHA-256 {digest(folder / 'inventory.json')}. "
              f"analysis/liquidity.py SHA-256 {digest(Path(__file__))}.")
    assets = root / 'content/assets'
    # Binning prevents a sparse grid of 100 tiny cells from obscuring the result.
    labels = ['2–4', '5–6', '7–8', '9', '10+']
    def bucket(points):
        return 0 if points <= 4 else 1 if points <= 6 else 2 if points <= 8 else 3 if points == 9 else 4
    cells = Counter((bucket(r['points'][1]), bucket(r['points'][0])) for r in rows)
    write_json(assets / 'liquidity-scores.json', dict(
        schema=1, kind='plot', variant='heatmap', evidence='measured',
        title='How did the two policies finish in the same game?', source=source,
        caption=f'{n} complete games. Each cell counts games in the two final-score bands. Above the diagonal favors Liquidity; below favors ETA. Blank cells contain zero games. Score bands are descriptive; winning remains the primary outcome.',
        x=dict(label='ETA control · final points', min=0, max=4, ticks=labels),
        y=dict(label='Liquidity · final points', min=0, max=4, ticks=labels),
        color=dict(label='number of games', min=0, max=max(cells.values())),
        series=[dict(label='Games in each score combination', points=[dict(x=x, y=y, value=count) for (x,y),count in sorted(cells.items())])]))
    max_trades = max(r['metrics'][s]['bank_traded'] for r in rows for s in [0,1])
    # Integer-threshold empirical CDF: line segments are visual guides, not a model.
    write_json(assets / 'liquidity-exchanges.json', dict(
        schema=1, kind='plot', variant='line', evidence='measured',
        title='Did exchange planning change bank use?', source=source,
        caption=f'Fraction of {n} games with at most the indicated number of bank/port exchanges. Higher curves mean fewer exchanges. Values are exact empirical proportions at integer thresholds; connecting segments are guides. More trading alone is not evidence of stronger play.',
        x=dict(label='Bank/port exchanges per game', min=0, max=max(1,max_trades)),
        y=dict(label='Fraction of completed games', min=0, max=1),
        series=[dict(label=label, points=[dict(x=t, y=sum(r['metrics'][slot]['bank_traded']<=t for r in rows)/n) for t in range(max_trades+1)]) for slot,label in [(0,'Liquidity'),(1,'ETA control')]]))
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    analyze(Path.cwd(), sys.argv[1])

"""Assets for the ablation program: one forest plot of paired seed contrasts across arms and
a cross-play win-rate chart. Every value is copied from a retained run summary."""
import argparse
import json
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402


def latest_run(experiment):
    runs = []
    for manifest in (ROOT / 'runs').glob('*/manifest.json'):
        data = json.loads(manifest.read_text())
        if data.get('experiment') == experiment and (manifest.parent / 'summary.json').exists():
            summary = json.loads((manifest.parent / 'summary.json').read_text())
            if summary.get('status') == 'completed':
                runs.append((data['created_at'], manifest.parent.name, summary))
    if not runs:
        return None
    return sorted(runs)[-1]


def forest(arms, name, title, caption):
    points, ticks = [], []
    rows = []
    for i, arm in enumerate(arms):
        run = latest_run(arm['experiment'])
        if not run:
            continue
        _, run_id, summary = run
        c = summary['paired_contrast']
        points.append({'x': i, 'y': round(c['mean_win_difference'], 4), 'low': round(c['interval95'][0], 4), 'high': round(c['interval95'][1], 4)})
        ticks.append(arm['label'])
        rows.append({'study': arm['study'], 'label': arm['label'], 'run': run_id, 'contrast': c,
                     'treatment': summary['slots'][0], 'control': summary['slots'][1]})
    lo = min(p['low'] for p in points) - 0.05
    hi = max(p['high'] for p in points) + 0.05
    data = {'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'title': title, 'evidence': 'measured',
            'source': 'Engine-arena ablation cohorts: 64 deterministic seeds each played once per rotation (256 games per arm); treatment in slot 0, the unchanged depth-2 control in slot 1, an ETA and a fast builder in the other seats. Run IDs are listed in the ablation report.',
            'caption': caption, 'x': {'label': 'Ablation arm', 'min': 0, 'max': len(points) - 1, 'ticks': ticks},
            'y': {'label': 'Wins per game, treatment minus control', 'min': round(min(lo, -0.05), 2), 'max': round(max(hi, 0.05), 2)},
            'series': [{'label': 'Paired seed contrast (95% interval)', 'points': points}], 'reference': {'y': 0, 'label': 'no difference'}}
    write_json(ROOT / 'content/assets' / f'{name}.json', data)
    return rows


def crossplay(arm, name, title, caption):
    run = latest_run(arm['experiment'])
    if not run:
        return None
    _, run_id, summary = run
    names = list(arm['presets'])
    rows = [{'label': f"{names[r['slot']]} (slot {r['slot']})", 'value': r['win_rate'], 'low': r['wilson95'][0], 'high': r['wilson95'][1], 'n': r['completed']} for r in summary['slots']]
    data = {'schema': 1, 'kind': 'chart', 'title': title, 'unit': 'fraction', 'rows': rows,
            'caption': f"{caption} Run {run_id}: {summary['completed']} of {summary['planned']} games completed; deterministic tapes, 64 seeds, four rotations."}
    write_json(ROOT / 'content/assets' / f'{name}.json', data)
    return {'run': run_id, 'summary': summary}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('registry', help='JSON list of registered arms')
    parser.add_argument('--out', default='ablation-contrasts')
    args = parser.parse_args()
    arms = json.load(open(args.registry))
    single = [dict(a, label=a['study'].split('/')[1]) for a in arms if a['treatment'] != 'presets']
    search_side = {'search', 'beliefs', 'bargaining', 'adaptation'}
    rows = forest([a for a in single if a['study'].split('/')[0] in search_side], f'{args.out}-search',
                  'Search, beliefs, trading, and opponent model',
                  'Each point is the mean per-seed difference in wins between a search with one change and the unchanged depth-2 control; the bar is the 95% interval over 64 seeds. Points below zero mean the change hurt.')
    rows += forest([a for a in single if a['study'].split('/')[0] not in search_side], f'{args.out}-terms',
                   'Leaf terms and style sliders',
                   'Each point is the mean per-seed difference in wins between a search with one leaf term switched off or one slider at its limit and the unchanged depth-2 control; the bar is the 95% interval over 64 seeds.')
    for r in rows:
        c = r['contrast']
        print(f"{r['study']:32} run {r['run'][:8]} contrast {c['mean_win_difference']:+.3f} [{c['interval95'][0]:+.3f}, {c['interval95'][1]:+.3f}] treatment {r['treatment']['win_rate']:.3f} control {r['control']['win_rate']:.3f}")
    cross = [a for a in arms if a['treatment'] == 'presets']
    if cross:
        result = crossplay(cross[0], 'ablation-crossplay-wins', 'Four search styles at one table', 'Per-preset win rates when four depth-2 searches with different inclination presets share a table.')
        if result:
            print('cross-play', result['run'][:8], [(r['seat'][:20], round(r['win_rate'], 3)) for r in result['summary']['slots']])
    json.dump({'arms': rows}, open('/tmp/claude-1001/-home-keshav-settlers/b832eb4f-75f4-44a8-a967-7ea9831303bf/scratchpad/ablation-rows.json', 'w'), indent=1)

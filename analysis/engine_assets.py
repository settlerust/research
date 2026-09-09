"""Chart and plot assets from engine-arena run summaries. Every number comes from a retained
`runs/<id>/summary.json`; the scripts never compute a new claim, only reshape recorded values."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402


def load(run_id):
    return json.loads((ROOT / 'runs' / run_id / 'summary.json').read_text())


def short(seat):
    if seat.startswith('v2:'):
        cfg = json.loads(seat[3:])
        depth = cfg.get('depth', 2)
        budget = cfg.get('time_budget_ms', 0)
        return f"expectimax-v2 depth {depth}" + (f", {budget / 1000:g} s" if budget else '')
    return {'v1': 'expectimax-v1 reference', 'eta': 'ETA builder', 'fast': 'fast builder', 'legal': 'legal-first'}.get(seat, seat)


def wins_chart(run_id, title, caption):
    s = load(run_id)
    rows = [{'label': f"{short(r['seat'])} (slot {r['slot']})", 'value': r['win_rate'], 'low': r['wilson95'][0],
             'high': r['wilson95'][1], 'n': r['completed']} for r in s['slots']]
    return {'schema': 1, 'kind': 'chart', 'title': title, 'unit': 'fraction', 'rows': rows,
            'caption': f"{caption} Run {run_id}: {s['completed']} of {s['planned']} planned games completed; engine arena, paired seeds."}


def contrast_plot(entries, title, caption, source):
    """entries: list of (run_id, label). Scatter of paired win differences with 95% intervals."""
    points = []
    ticks = []
    for i, (run_id, label) in enumerate(entries):
        c = load(run_id)['paired_contrast']
        points.append({'x': i, 'y': round(c['mean_win_difference'], 4), 'low': round(c['interval95'][0], 4), 'high': round(c['interval95'][1], 4)})
        ticks.append(label)
    lo = min(p['low'] for p in points) - 0.05
    hi = max(p['high'] for p in points) + 0.05
    return {'schema': 1, 'kind': 'plot', 'variant': 'scatter', 'title': title, 'evidence': 'measured', 'source': source,
            'caption': caption, 'x': {'label': 'Comparison', 'min': 0, 'max': len(entries) - 1, 'ticks': ticks},
            'y': {'label': 'Wins per game, candidate minus ETA', 'min': round(min(lo, -0.05), 2), 'max': round(max(hi, 0.05), 2)},
            'series': [{'label': 'Paired seed contrast', 'points': points}], 'reference': {'y': 0, 'label': 'no difference'}}


def builds_plot(run_id, title, caption):
    s = load(run_id)
    keys = ['settlements_built', 'cities_built', 'roads_built', 'development_bought', 'player_trades', 'bank_trades']
    labels = ['settlements', 'cities', 'roads', 'dev cards', 'player trades', 'bank trades']
    series = []
    seen = set()
    for r in s['slots']:
        name = short(r['seat'])
        if name in seen:
            continue
        seen.add(name)
        series.append({'label': name, 'points': [{'x': i, 'y': round(r['builds'][k], 2)} for i, k in enumerate(keys)]})
    ymax = max(p['y'] for se in series for p in se['points'])
    return {'schema': 1, 'kind': 'plot', 'variant': 'bar', 'title': title, 'evidence': 'measured',
            'source': f"Engine-arena run {run_id}; per-game means over {s['completed']} completed games per slot.",
            'caption': caption, 'x': {'label': 'Action', 'min': 0, 'max': len(keys) - 1, 'ticks': labels},
            'y': {'label': 'Per game', 'min': 0, 'max': float(int(ymax) + 1)}, 'series': series}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind', choices=['wins', 'builds'])
    parser.add_argument('run_id')
    parser.add_argument('name')
    parser.add_argument('--title', required=True)
    parser.add_argument('--caption', required=True)
    args = parser.parse_args()
    data = wins_chart(args.run_id, args.title, args.caption) if args.kind == 'wins' else builds_plot(args.run_id, args.title, args.caption)
    write_json(ROOT / 'content/assets' / f'{args.name}.json', data)
    print(ROOT / 'content/assets' / f'{args.name}.json')

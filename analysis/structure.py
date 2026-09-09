"""Game-tree structure measurements: run the server's `structure` tool and turn its rows into
research plot assets. Rows describe builder-game decisions (legal-action width by phase) and
sampled positions analysed by expectimax-v2 at fixed depths (afterstates, transitions, time)."""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import digest, git_state, now, write_json  # noqa: E402

PHASES = ['setup_settlement', 'setup_road', 'roll', 'main', 'discard', 'robber', 'free_roads']


def run_tool(server, seeds, every, depths, time_budget, folder, threads=None):
    binary = Path(server) / 'target/release/structure'
    if not binary.is_file():
        raise ValueError('Build the tool first: cargo build --release -p settlers-arena --bins')
    out = folder / 'structure.jsonl'
    command = [str(binary), '--seeds', seeds, '--every', str(every), '--depths', ','.join(map(str, depths)),
               '--time', str(time_budget), '--out', str(out)]
    if threads:
        command += ['--threads', str(threads)]
    with (folder / 'structure.log').open('w') as log:
        subprocess.run(command, cwd=server, check=True, stdout=log, stderr=subprocess.STDOUT)
    return out


def quantile(values, q):
    values = sorted(values)
    if not values:
        return 0.0
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def plot(variant, title, caption, source, x, y, series, **extra):
    data = {'schema': 1, 'kind': 'plot', 'variant': variant, 'title': title, 'evidence': 'measured',
            'source': source, 'caption': caption, 'x': x, 'y': y, 'series': series}
    data.update(extra)
    return data


def assets(rows, run_id, seeds):
    decisions = [r for r in rows if r['kind'] == 'decision' and r['turn'] > 0]
    searches = [r for r in rows if r['kind'] == 'search' and not r['aborted']]
    games = len({r['seed'] for r in decisions})
    source = f'Engine-arena structure run {run_id}: {games} builder games (fast, ETA, fast, ETA) on seeds {seeds}; {len(decisions)} decisions after setup and {len(searches)} sampled searches.'
    out = {}
    # 1. Legal-action width by phase (bar with 10th and 90th percentiles).
    phases = [p for p in PHASES if any(r['phase'] == p for r in decisions)]
    points = []
    for i, p in enumerate(phases):
        widths = [r['legal_actions'] for r in decisions if r['phase'] == p]
        points.append({'x': i, 'y': round(statistics.median(widths), 2), 'low': round(quantile(widths, .1), 2), 'high': round(quantile(widths, .9), 2)})
    ymax = max(pt['high'] for pt in points)
    out['tree-width-by-phase'] = plot('bar', 'Legal actions per decision, by phase',
        'Bars are medians over builder-game decisions; the interval marks the 10th to 90th percentile. The main phase lists every legal build, exchange, and card play the server enumerates.',
        source, {'label': 'Phase', 'min': 0, 'max': len(phases) - 1, 'ticks': [p.replace('_', ' ') for p in phases]},
        {'label': 'Legal actions', 'min': 0, 'max': float(int(ymax) + 5)},
        [{'label': 'Builder games', 'points': points}])
    # 2. Main-phase width over the game (line with interval), turn buckets of 8.
    buckets = {}
    for r in decisions:
        if r['phase'] == 'main':
            buckets.setdefault(min(r['turn'] // 8, 11), []).append(r['legal_actions'])
    pts = [{'x': b * 8 + 4, 'y': round(statistics.median(v), 2), 'low': round(quantile(v, .1), 2), 'high': round(quantile(v, .9), 2)}
           for b, v in sorted(buckets.items())]
    out['tree-width-by-turn'] = plot('line', 'Main-phase width through the game',
        'Median legal actions in the main phase per eight-turn window, with the 10th to 90th percentile; width grows as hands and road networks grow.',
        source, {'label': 'Turn', 'min': 0, 'max': 96}, {'label': 'Legal actions', 'min': 0, 'max': float(int(max(p['high'] for p in pts)) + 5)},
        [{'label': 'Main phase', 'points': pts}])
    # 3. Own-turn nodes explored and end-of-turn positions followed, by level, deepest depth.
    deepest = max((r['depth'] for r in searches), default=1)
    deep = [r for r in searches if r['depth'] == deepest]
    nodes_by, ends_by = {}, {}
    for r in deep:
        for level, (n, a) in enumerate(zip(r['per_level_nodes'], r['per_level_afterstates'])):
            if level >= 1:
                nodes_by.setdefault(level, []).append(n)
                ends_by.setdefault(level, []).append(a)
    if nodes_by:
        levels = sorted(nodes_by)
        series = [
            {'label': 'Own-turn nodes explored', 'points': [{'x': l, 'y': round(statistics.median(nodes_by[l]), 1), 'low': round(quantile(nodes_by[l], .1), 1), 'high': round(quantile(nodes_by[l], .9), 1)} for l in levels]},
            {'label': 'End-of-turn positions followed', 'points': [{'x': l, 'y': round(statistics.median(ends_by[l]), 1), 'low': round(quantile(ends_by[l], .1), 1), 'high': round(quantile(ends_by[l], .9), 1)} for l in levels]},
        ]
        top = max(p['high'] for se in series for p in se['points'])
        out['tree-afterstates-by-level'] = plot('bar', 'Work per search level',
            f'Median own-turn nodes explored and end-of-turn positions followed at each level of a depth-{deepest} analysis, with the 10th to 90th percentile; the current turn is a small tree, later levels multiply by the scenarios that lead to them.',
            source, {'label': 'Search level (own turn)', 'min': 1, 'max': max(levels), 'ticks': [str(l) for l in levels]},
            {'label': 'Count per analysis', 'min': 0, 'max': float(int(top * 1.1) + 1)}, series)
    # 4. Cost by depth: transitions and milliseconds (two plots to keep units honest).
    by_depth = {}
    for r in searches:
        by_depth.setdefault(r['depth'], []).append(r)
    trans = [{'x': d, 'y': round(statistics.median(x['transitions'] for x in v)), 'low': round(quantile([x['transitions'] for x in v], .1)), 'high': round(quantile([x['transitions'] for x in v], .9))} for d, v in sorted(by_depth.items())]
    ms = [{'x': d, 'y': round(statistics.median(x['time_ms'] for x in v), 2), 'low': round(quantile([x['time_ms'] for x in v], .1), 2), 'high': round(quantile([x['time_ms'] for x in v], .9), 2)} for d, v in sorted(by_depth.items())]
    out['tree-cost-transitions'] = plot('line', 'Engine transitions per analysis, by depth',
        'Median transitions applied per analysis with the 10th to 90th percentile; each additional planned turn multiplies the work by the scenario count and the inner beam.',
        source, {'label': 'Depth (planned own turns)', 'min': 0, 'max': max(by_depth) + 1}, {'label': 'Transitions', 'min': 0, 'max': float(max(p['high'] for p in trans) * 1.1)},
        [{'label': 'expectimax-v2, default budgets', 'points': trans}])
    out['tree-cost-time'] = plot('line', 'Native analysis time, by depth',
        'Median wall-clock milliseconds per analysis on one core with the 10th to 90th percentile; native release build, default scenario and sample counts.',
        source, {'label': 'Depth (planned own turns)', 'min': 0, 'max': max(by_depth) + 1}, {'label': 'Milliseconds', 'min': 0, 'max': float(max(p['high'] for p in ms) * 1.1)},
        [{'label': 'expectimax-v2, default budgets', 'points': ms}])
    # 5. Transposition share by depth.
    tp = [{'x': d, 'y': round(statistics.mean(x['transpositions'] / max(1, x['transpositions'] + x['own_nodes']) for x in v), 3)} for d, v in sorted(by_depth.items())]
    out['tree-transpositions'] = plot('line', 'Share of own-turn positions already seen',
        'Transpositions divided by transpositions plus expanded own-turn nodes; different action orders within a turn often reach the same position.',
        source, {'label': 'Depth (planned own turns)', 'min': 0, 'max': max(by_depth) + 1}, {'label': 'Fraction', 'min': 0, 'max': 1},
        [{'label': 'expectimax-v2', 'points': tp}])
    summary = {
        'games': games, 'decisions': len(decisions), 'searches': len(searches),
        'width_by_phase': {p: statistics.mean([r['legal_actions'] for r in decisions if r['phase'] == p]) for p in phases},
        'by_depth': {d: {'n': len(v), 'transitions': statistics.mean(x['transitions'] for x in v), 'leaves': statistics.mean(x['leaves'] for x in v),
                         'time_ms': statistics.mean(x['time_ms'] for x in v), 'afterstates': statistics.mean(x['afterstates'] for x in v)} for d, v in sorted(by_depth.items())},
    }
    return out, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default=os.environ.get('SETTLERS_SERVER_DIR', str(ROOT.parent / 'server')))
    parser.add_argument('--seeds', default='0-15')
    parser.add_argument('--every', type=int, default=7)
    parser.add_argument('--depths', default='1,2,3')
    parser.add_argument('--time', type=float, default=0.0)
    parser.add_argument('--rows', help='Reuse an existing structure.jsonl instead of running the tool')
    parser.add_argument('--write-assets', action='store_true')
    parser.add_argument('--threads', type=int)
    parser.add_argument('--reuse', help='Write the summary, record and assets for this existing structure run ID')
    args = parser.parse_args()
    run_id = args.reuse or str(uuid.uuid4())
    folder = ROOT / 'runs' / f'structure-{run_id}'
    if args.reuse:
        manifest = json.loads((folder / 'manifest.json').read_text())
        args.seeds, args.every, args.depths, args.time = manifest['seeds'], manifest['every'], ','.join(map(str, manifest['depths'])), manifest['time_budget_ms']
        args.rows = str(folder / 'structure.jsonl')
    else:
        folder.mkdir(parents=True)
    depths = [int(d) for d in args.depths.split(',')]
    if not args.reuse:
        write_json(folder / 'manifest.json', {'schema': 1, 'run_id': run_id, 'created_at': now(), 'kind': 'structure', 'seeds': args.seeds,
                                          'every': args.every, 'depths': depths, 'time_budget_ms': args.time, 'server': args.server,
                                          'research_git': git_state(ROOT), 'server_git': git_state(args.server)})
    rows_path = Path(args.rows) if args.rows else run_tool(args.server, args.seeds, args.every, depths, args.time, folder, args.threads)
    rows = [json.loads(line) for line in Path(rows_path).read_text().splitlines() if line.strip()]
    out, summary = assets(rows, run_id, args.seeds)
    summary['run_id'] = run_id
    summary['rows_sha256'] = digest(rows_path)
    write_json(folder / 'summary.json', summary)
    print(json.dumps(summary, indent=1))
    if args.write_assets:
        for name, data in out.items():
            write_json(ROOT / 'content/assets' / f'{name}.json', data)
        records = ROOT / 'records/structure'
        records.mkdir(parents=True, exist_ok=True)
        (records / f'{run_id}.md').write_text(
            f'# Structure run {run_id}\n\nTier: engine arena (structure measurement, not a policy comparison).\n\n'
            f"Seeds {args.seeds}; every {args.every}th decision analysed at depths {depths}; time budget {args.time} ms.\n\n"
            f"Games: {summary['games']}. Decisions after setup: {summary['decisions']}. Searches: {summary['searches']}.\n\n"
            + '| Depth | Searches | Mean transitions | Mean leaves | Mean afterstates | Mean ms |\n| ---: | ---: | ---: | ---: | ---: | ---: |\n'
            + '\n'.join(f"| {d} | {v['n']} | {v['transitions']:.0f} | {v['leaves']:.0f} | {v['afterstates']:.1f} | {v['time_ms']:.1f} |" for d, v in summary['by_depth'].items())
            + f"\n\nRows SHA-256: `{summary['rows_sha256']}`. Assets: {', '.join(sorted(out))}.\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())

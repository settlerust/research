"""Plot asset from a WASM-versus-native timing file produced by
`web/scripts/measure-expectimax-wasm.mjs`: median milliseconds by depth with 10th to 90th
percentile bands for both runtimes."""
import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import write_json  # noqa: E402


def quantile(values, q):
    values = sorted(values)
    k = (len(values) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (k - lo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('timing')
    parser.add_argument('name')
    parser.add_argument('--source', required=True)
    args = parser.parse_args()
    data = json.loads(Path(args.timing).read_text())
    rows = [r for r in data['results'] if not r['aborted']]
    depths = sorted({r['depth'] for r in rows})
    series = []
    for label, key in [('Native (release build)', 'nativeMs'), ('WASM in Node', 'wasmMs')]:
        points = []
        for d in depths:
            v = [r[key] for r in rows if r['depth'] == d]
            points.append({'x': d, 'y': round(statistics.median(v), 1), 'low': round(quantile(v, .1), 1), 'high': round(quantile(v, .9), 1)})
        series.append({'label': label, 'points': points})
    top = max(p['high'] for s in series for p in s['points'])
    ratio = {d: statistics.median([r['wasmMs'] / max(r['nativeMs'], 0.01) for r in rows if r['depth'] == d]) for d in depths}
    asset = {'schema': 1, 'kind': 'plot', 'variant': 'line', 'title': 'Search time by depth: native and WASM',
             'evidence': 'measured', 'source': args.source,
             'caption': 'Median milliseconds per analysis on ' + f"{data['views']} sampled main-phase positions with the 10th to 90th percentile; WASM to native ratio " + ', '.join(f'{ratio[d]:.2f} at depth {d}' for d in depths) + '.',
             'x': {'label': 'Depth (planned own turns)', 'min': 0, 'max': max(depths) + 1},
             'y': {'label': 'Milliseconds', 'min': 0, 'max': float(int(top * 1.1) + 1)}, 'series': series}
    write_json(ROOT / 'content/assets' / f'{args.name}.json', asset)
    print(json.dumps({'views': data['views'], 'medians': {s['label']: [(p['x'], p['y']) for p in s['points']] for s in series}, 'ratio': ratio}, indent=1))


if __name__ == '__main__':
    sys.exit(main())

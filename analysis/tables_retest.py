"""Recompute and pool every swapped pair of the learned-leaf retest program from the archived runs.

A pair is two registered engine experiments in one study on the same seeds whose first two seats
are swapped and whose other seats match. The control is the seat closest to the study's baseline
and the candidate is the other seat. The effect is the per-seed half-difference of the two
slot-0-minus-slot-1 contrasts, oriented so that a positive value favours the candidate; the half-sum
is the seating term. Pooling concatenates the seeds of every stage for one switch, leaf, and lineup
and takes a normal 95% interval over seeds; that pooling is after the fact and is labelled so.
Runs are read from runs/ and from the archives under artifacts/ of the canonical checkout
(extracted once into its .runtime/), so the script also works from a worktree.

    python3 analysis/tables_retest.py [--study OWNER/SLUG ...] [--out FILE.json]
"""
import argparse
import collections
import json
import math
import re
import sys
import tarfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.notebook import canonical_root  # noqa: E402

# Runs and archives are ignored local data kept only in the canonical checkout, so a worktree
# reads them from there.
DATA = canonical_root(ROOT)
CACHE = DATA / '.runtime' / 'tables-retest-cache'
STUDIES = ['bargaining/tables-arms', 'search/settings-tables', 'patterns/leaf-blend', 'opening/planner-tables',
           'development/timing-tables', 'risk/hand-tables', 'expansion/roads-tables', 'adaptation/prediction-tables',
           'containment/robber-tables']
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.tar\.gz$')


def spec(seat):
    return json.loads(seat[3:]) if seat.startswith('v2:') else seat


def flat(d, prefix=''):
    out = {}
    for k, v in (d.items() if isinstance(d, dict) else []):
        out.update(flat(v, f'{prefix}{k}.') if isinstance(v, dict) else {f'{prefix}{k}': v})
    return out


def diff(a, b):
    fa, fb = flat(spec(a)), flat(spec(b))
    return ', '.join(f'{k}={fa.get(k, "-")}' for k in sorted(set(fa) | set(fb)) if fa.get(k) != fb.get(k)) or '(identical)'


def extract_archives():
    CACHE.mkdir(parents=True, exist_ok=True)
    for archive in list((DATA / 'artifacts').glob('*.tar.gz')) + list((DATA / 'artifacts').glob('*/*.tar.gz')):
        run = archive.name[:-7]
        if not UUID.match(archive.name) or (CACHE / run / 'summary.json').exists():
            continue
        with tarfile.open(archive) as t:
            for member in t.getmembers():
                name = member.name.split('/')[-1]
                if name in ('manifest.json', 'summary.json', 'games.jsonl'):
                    member.name = f'{run}/{name}'
                    t.extract(member, CACHE, filter='data')


def completed_runs():
    extract_archives()
    found = {}
    for manifest in list((DATA / 'runs').glob('*/manifest.json')) + list(CACHE.glob('*/manifest.json')):
        summary = manifest.parent / 'summary.json'
        if not summary.exists() or json.loads(summary.read_text()).get('status') != 'completed':
            continue
        m = json.loads(manifest.read_text())
        found.setdefault(m['experiment'], []).append((m['created_at'], manifest.parent))
    return {e: sorted(v)[-1][1] for e, v in found.items()}


def per_seed(games):
    wins, count, ms = collections.defaultdict(int), collections.defaultdict(int), collections.defaultdict(list)
    for line in games.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r['game'].get('status') != 'completed':
            continue
        count[r['seed']] += 1
        wins[r['seed']] += 1 if r['winner_slot'] == 0 else (-1 if r['winner_slot'] == 1 else 0)
        for seat in r['game']['seats']:
            slot = r['slots'][seat['seat']]
            if slot in (0, 1) and seat.get('decisions'):
                ms[slot].append(seat['decision_ms'] / seat['decisions'])
    return {s: wins[s] / count[s] for s in count}, {k: sum(v) / len(v) for k, v in ms.items()}


def interval(values):
    n = len(values)
    mean = sum(values) / n
    se = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, n - 1)) / math.sqrt(n)
    return mean, mean - 1.96 * se, mean + 1.96 * se


def pairs(studies, done):
    base = 'v2:{"depth":2,"leaf":{"tables":"%s"}}' % (DATA / 'artifacts/ntuple/hex-portfolio-main.bin')
    experiments = collections.defaultdict(list)
    for path in (ROOT / 'experiments').glob('*.toml'):
        e = tomllib.loads(path.read_text())
        if e.get('arena') == 'engine' and e.get('study') in studies and e['id'] in done:
            experiments[e['study']].append(e)
    rows = []
    for study, group in experiments.items():
        seats = collections.Counter(s for e in group for s in e['players'][:2])
        root = min(seats, key=lambda s: (len(flat(spec(s))), -seats[s]))
        used = set()
        for x in group:
            for y in group:
                px, py = x['players'], y['players']
                if x['id'] >= y['id'] or {x['id'], y['id']} & used or x['seeds'] != y['seeds'] \
                        or px[0] != py[1] or px[1] != py[0] or px[2:] != py[2:]:
                    continue
                control = min(px[:2], key=lambda s: (len(diff(s, root).split(', ')) if diff(s, root) != '(identical)' else 0, -seats[s]))
                candidate = px[0] if control == px[1] else px[1]
                a, b = (x, y) if px[0] == candidate else (y, x)
                da, ta = per_seed(done[a['id']] / 'games.jsonl')
                db, tb = per_seed(done[b['id']] / 'games.jsonl')
                seeds = sorted(set(da) & set(db))
                ctrl_ms = (ta.get(1, 0) + tb.get(0, 0)) / 2
                rows.append({'study': study, 'change': diff(candidate, control), 'control': diff(control, base),
                             'lineup': 'L2' if 'tables' in px[2] else 'L1', 'seeds': x['seeds'],
                             'effects': {str(s): (da[s] - db[s]) / 2 for s in seeds},
                             'seating': interval([(da[s] + db[s]) / 2 for s in seeds]),
                             'cost': ((ta.get(0, 0) + tb.get(1, 0)) / 2) / ctrl_ms if ctrl_ms else None,
                             'runs': [done[a['id']].name, done[b['id']].name]})
                used |= {x['id'], y['id']}
    return rows


def pool(rows):
    groups = collections.defaultdict(lambda: {'effects': [], 'costs': [], 'stages': []})
    for r in rows:
        leaf = 'blend 0.25' if 'leaf.hand=0.25' in r['control'] else 'blend 1.0' if 'leaf.hand=1.0' in r['control'] else 'tables'
        g = groups[(r['study'], r['change'], leaf, r['lineup'])]
        g['effects'] += list(r['effects'].values())
        g['costs'].append(r['cost'] or 0)
        g['stages'].append(r['seeds'])
    out = []
    for (study, change, leaf, lineup), g in sorted(groups.items()):
        mean, lo, hi = interval(g['effects'])
        out.append({'study': study, 'change': change, 'leaf': leaf, 'lineup': lineup, 'boards': len(g['effects']),
                    'stages': sorted(set(g['stages'])), 'effect': [mean, lo, hi], 'cost': sum(g['costs']) / len(g['costs'])})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--study', action='append', help='study ID; repeat for several (default: the whole program)')
    parser.add_argument('--out', help='write the pairs and pooled rows as JSON')
    args = parser.parse_args()
    studies = args.study or STUDIES
    rows = pairs(set(studies), completed_runs())
    pooled = pool(rows)
    for p in pooled:
        m, lo, hi = p['effect']
        print(f"{p['study']:30} {p['change'][:44]:44} {p['leaf']:10} {p['lineup']} {p['boards']:3} boards "
              f"{m:+.3f} ({lo:+.3f} to {hi:+.3f}) time {p['cost']:.2f}x")
    print(f'{len(rows)} pairs, {len(rows) * 512} games, pooled after the fact per switch, leaf, and lineup')
    if args.out:
        Path(args.out).write_text(json.dumps({'pairs': rows, 'pooled': pooled}, indent=1))


if __name__ == '__main__':
    sys.exit(main())

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


NAMES = {
    'bargain=False': 'All bargaining off', 'counters=False': 'Counters off', 'asks=False': 'Two-for-one asks off',
    'threat_pricing=False': 'Threat pricing off', 'accept_asks=False': 'Refuse asks (stubborn seat)',
    'scenarios=4': 'Four dice scenarios (default 8)', 'scenarios=16': 'Sixteen dice scenarios',
    'samples=1': 'One sampled world (default 4)', 'samples=8': 'Eight sampled worlds',
    'inner_scenarios=2': 'Two deeper-level scenarios (inert at depth 2)', 'counts_only=True': 'Beliefs from public counts only',
    'propose=False': 'Never propose trades', 'reciprocity=True': 'Reciprocity scaling', 'leaf_opponents=True': 'Leaf-guided opponents',
    'leaf.hand=0.25': 'Blend: hand-written terms at 0.25', 'leaf.hand=0.5': 'Blend: hand-written terms at 0.5',
    'leaf.scale=500': 'Tables scale 500 (default 1000)', 'leaf.scale=2000': 'Tables scale 2000',
    'endgame.race=True': 'Endgame race leaf', 'endgame.hidden_points=True': 'Expected hidden points',
    'endgame.block_leader=True': 'Late leader bias', 'opening=search': 'Search-ranked opening instead of the planner',
    'opening_weights.balance=0.5, opening_weights.coverage=0.4': 'Planner coverage 0.4 and balance 0.5',
    'opening_weights.scarcity=0.0': 'Planner without scarcity markup', 'buy_tempo=True': 'Buy cards only when stalled',
    'hold_knight=True': 'Hold knights for the unblock', 'knight_play_value=True': 'Knight schedule in the leaf',
    'spend_down=True': 'Spend down over the discard limit', 'discard_projection=True': 'Project production when discarding',
    'weights.hand_risk=0.0': 'No seven-risk term', 'weights.opponent_expansion=0.5': "Block the leader's expansion",
    'weights.road_contention_gate=1.0': 'Gate the road race on production', 'predict.opponents=True': 'Opponents play their predicted build',
    'predict.threat=True': 'Threat from the predicted site', 'weights.denial=0.5': 'Deny predicted sites',
    'robber.leader=True': 'Robber blocks the leader', 'robber.need=True': 'Rob the card this seat needs',
    'robber.threat=True': 'Robber by threat, spare partners',
    'endgame.block_leader=True, robber.need=True': 'Late leader bias plus rob what you need',
}
STUDY_NAMES = {'bargaining/tables-arms': 'Bargaining', 'search/settings-tables': 'Search settings', 'patterns/leaf-blend': 'Leaf blend',
               'opening/planner-tables': 'Opening', 'development/timing-tables': 'Card timing', 'risk/hand-tables': 'Hand management',
               'expansion/roads-tables': 'Roads', 'adaptation/prediction-tables': 'Prediction', 'containment/robber-tables': 'Robber'}


def markdown(pooled):
    """Evidence table: one row per switch and leaf, the builder table (L1) and population table (L2) side by side.
    The full blend is left out because the program withdrew it as a baseline."""
    groups = collections.OrderedDict()
    order = list(STUDY_NAMES)
    for p in sorted(pooled, key=lambda p: (order.index(p['study']) if p['study'] in order else 99, p['change'], p['leaf'])):
        if p['leaf'] == 'blend 1.0':
            continue
        groups.setdefault((p['study'], p['change'], p['leaf']), {})[p['lineup']] = p

    def cell(p):
        if not p:
            return 'not run'
        m, lo, hi = p['effect']
        return f"{m:+.3f} ({lo:+.3f} to {hi:+.3f}), {p['boards']} boards"

    def reading(d):
        v = {k: ('helps' if p['effect'][1] > 0 else 'hurts' if p['effect'][2] < 0 else 'none') for k, p in d.items()}
        table = {'L1': 'builder', 'L2': 'population'}
        if set(v.values()) == {'hurts'}:
            return 'Hurts at both tables' if len(v) > 1 else f"Hurts at the {table[next(iter(v))]} table"
        if set(v.values()) == {'helps'}:
            return 'Helps at both tables' if len(v) > 1 else f"Helps at the {table[next(iter(v))]} table"
        if 'hurts' in v.values() and 'helps' not in v.values():
            return f"Hurts at the {table[[k for k in v if v[k] == 'hurts'][0]]} table"
        if 'helps' in v.values() and 'hurts' not in v.values():
            return f"Helps at the {table[[k for k in v if v[k] == 'helps'][0]]} table only"
        return 'No clear effect'
    lines = ['| Study | Switch | Leaf | Builder table | Population table | Time | Reading |',
             '| --- | --- | --- | --- | --- | ---: | --- |']
    for (study, change, leaf), d in groups.items():
        cost = sum(p['cost'] for p in d.values()) / len(d)
        lines.append(f"| {STUDY_NAMES.get(study, study)} | {NAMES.get(change, change)} | {leaf} | {cell(d.get('L1'))} | "
                     f"{cell(d.get('L2'))} | {cost:.2f}× | {reading(d)} |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--study', action='append', help='study ID; repeat for several (default: the whole program)')
    parser.add_argument('--out', help='write the pairs and pooled rows as JSON')
    parser.add_argument('--markdown', help='write the evidence table as Markdown')
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
    if args.markdown:
        Path(args.markdown).write_text(markdown(pooled))


if __name__ == '__main__':
    sys.exit(main())

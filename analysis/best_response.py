"""Best-response and population training against the frozen tables, and the analysis of the
swapped pairs that evaluate the frozen candidates (study population/best-response).

`train ARM` runs one arm of the server's `train` binary under `runs/best-response/ARM/` with a
manifest (binary digest, commits, argv), skipping an arm whose run is DONE and resuming one
whose checkpoint exists. `freeze ARM` copies the arm's best validation point to the canonical
`artifacts/ntuple/best-response-ARM.bin`, writes its SHA-256 receipt under `records/artifacts/`
and a compact training record under `records/training/best-response/ARM/`. `training ARM`
prints the learner's win share and the seat compositions per chunk. `pairs` computes the
seating-corrected effect of swapped pairs (per-board half-difference of the two
slot-0-minus-slot-1 contrasts, the seating term their half-sum, normal 95 percent intervals over
boards) with the play statistics of the candidate and the control. Training and its validation
tournaments are development-tier activity; only registered cohorts support a claim."""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.notebook import canonical_root  # noqa: E402
from harness.records import digest, git_state, now, write_json  # noqa: E402

CANONICAL = canonical_root(ROOT)
SERVER = Path(os.environ.get('SETTLERS_SERVER_DIR', CANONICAL.parent / 'server')).resolve()
FROZEN = CANONICAL / 'artifacts/ntuple/hex-portfolio-main.bin'
FROZEN_SHA256 = 'f8e61e66e0279b0fe67f5f4d6be0ad3ca0a86617e91ed24fe08a34a997b46f0c'

# One training process at a time, twelve threads, budgeted by games (never wall time).
COMMON = ['--threads', '12', '--chunk-games', '5000', '--validate-every', '1', '--validate-seeds', '48',
          '--no-direct', '--alpha', '0.5', '--validate-start', '560000', '--seeds-count', '200000']
ARMS = {
    'challenger': {'pool': f'self:1,frozen={FROZEN}:3', 'games': 40_000, 'seeds_start': 4_000_000},
    'control': {'pool': 'self', 'games': 40_000, 'seeds_start': 4_200_000},
    'population': {'pool': f'self:2,frozen={FROZEN}:1,eta:0.5,fast:0.5', 'games': 60_000, 'seeds_start': 4_400_000},
}
STAT_KEYS = ['cities_built', 'settlements_built', 'roads_built', 'development_bought', 'knights_played',
             'player_trades', 'bank_trades', 'offers', 'counters', 'cards_discarded', 'times_robbed']


def out_dir(arm):
    return ROOT / 'runs/best-response' / arm


def train(arm):
    spec = ARMS[arm]
    out = out_dir(arm)
    if (out / 'DONE').exists():
        print(f'== {arm}: already done, skipping', flush=True)
        return 0
    if digest(FROZEN) != FROZEN_SHA256:
        raise SystemExit(f'frozen tables digest mismatch at {FROZEN}')
    binary = SERVER / 'target/release/train'
    out.mkdir(parents=True, exist_ok=True)
    argv = [str(binary), '--out', str(out), '--init', str(FROZEN), '--pool', spec['pool'],
            '--games', str(spec['games']), '--seeds-start', str(spec['seeds_start'])] + COMMON
    resume = (out / 'checkpoint.bin').exists()
    if resume:
        argv.append('--resume')
    manifest_path = out / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest.setdefault('resumed', []).append({'at': now(), 'argv': argv})
    else:
        manifest = {'schema': 1, 'arm': arm, 'study': 'population/best-response', 'created_at': now(), 'argv': argv,
                    'init': str(FROZEN), 'init_sha256': FROZEN_SHA256, 'pool': spec['pool'],
                    'train_sha256': digest(binary), 'server_git': git_state(SERVER), 'research_git': git_state(ROOT),
                    'tier': 'training (development); validation tournaments are engine-arena games on fixed seeds'}
    write_json(manifest_path, manifest)
    print(f'== {arm}: {" ".join(argv)}', flush=True)
    started = time.time()
    with (out / 'train.log').open('a') as log:
        code = subprocess.call(argv, stdout=log, stderr=subprocess.STDOUT, cwd=SERVER)
    write_json(out / 'exit.json', {'code': code, 'seconds': time.time() - started, 'finished_at': now(), 'resumed': resume})
    print(f'== {arm} exit {code} after {time.time() - started:.0f}s', flush=True)
    return code


def progress_rows(out):
    return [json.loads(line) for line in (out / 'progress.jsonl').read_text().splitlines() if line.strip()]


def freeze(arm):
    out = out_dir(arm)
    if not (out / 'DONE').exists() or not (out / 'best.bin').exists():
        raise SystemExit(f'{arm} has no finished run with a best point under {out}')
    target = CANONICAL / 'artifacts/ntuple' / f'best-response-{arm}.bin'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and digest(target) != digest(out / 'best.bin'):
        raise SystemExit(f'{target} exists with different contents; not overwriting a frozen candidate')
    shutil.copyfile(out / 'best.bin', target)
    sha = digest(target)
    best = json.loads((out / 'best.json').read_text())
    config = json.loads((out / 'config.json').read_text())
    manifest = json.loads((out / 'manifest.json').read_text())
    record = ROOT / 'records/training/best-response' / arm
    record.mkdir(parents=True, exist_ok=True)
    for name in ['manifest.json', 'config.json', 'best.json', 'stop.json', 'exit.json']:
        shutil.copyfile(out / name, record / name)
    for path in sorted(out.glob('val-*.json')):
        shutil.copyfile(path, record / path.name)
    write_json(record / 'progress.json', progress_rows(out))
    receipt = ROOT / 'records/artifacts' / f'ntuple-best-response-{arm}.md'
    receipt.write_text(
        f'# Learned tables ntuple-best-response-{arm}\n\nVerified at {now()}.\n\n'
        f'Location: `{target}` ({target.stat().st_size:,} bytes, format CTNTUP01, layout `{config["layout"]}`, '
        f'{config["entries"]:,} entries).\n\nSHA-256: `{sha}`\n\n'
        f'Provenance: the best validation point ({best["games_total"]:,} games, chunk {best["chunk"]}, fingerprint '
        f'`{best["fingerprint"]}`) of the `{arm}` arm of study population/best-response, warm-started from the frozen '
        f'tables `{FROZEN.name}` (SHA-256 `{FROZEN_SHA256[:8]}`) and trained with pool `{config["pool"]}` for '
        f'{config["games"]:,} games, recorded under `records/training/best-response/{arm}/` (server commit '
        f'{manifest["server_git"]["commit"][:7]}, `train` binary SHA-256 prefix `{manifest["train_sha256"][:8]}`). '
        f'Engine-run manifests that seat these tables record this digest under `tables_sha256`.\n\n'
        'This receipt proves local copy integrity. A local path is not a public download or a remote backup. '
        'After uploading to an authorized immutable object store, append its verified URL and retain this digest.\n')
    print(f'{arm}: {target} sha256 {sha} (best point {best["games_total"]} games, margin {best["margin"]:+.3f})')


def training(arm):
    out = out_dir(arm)
    rows = progress_rows(out)
    compositions = {}
    print(f'{arm}: {len(rows)} chunks')
    print('| Chunk | Games | Learner win share | Capped | Turns | Validation margin (tables minus hand) | Tables wins | Games/s |')
    print('| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |')
    for r in rows:
        share = r['learner_wins'] / max(1, r['learner_seats']) * 4 if r.get('learner_seats') else float('nan')
        v = r.get('validation') or {}
        margin = (f"{v['margin']:+.3f} ({v['margin_interval'][0]:+.3f} to {v['margin_interval'][1]:+.3f})"
                  if v else '')
        wins = f"{v['tables_wins']} / {v['hand_wins']} / {v['eta_wins']} / {v['fast_wins']} of {v['completed']}" if v else ''
        print(f"| {r['chunk']} | {r['games_total']:,} | {r['learner_wins']}/{r['learner_seats']} seats "
              f"({share / 4:.1%}, {share:.2f}x even) | {r['capped']} | {r['mean_turns']:.1f} | {margin} | {wins} | "
              f"{r['games_per_second']:.1f} |")
        for k, n in (r.get('compositions') or {}).items():
            compositions[k] = compositions.get(k, 0) + n
    total = sum(compositions.values())
    if total:
        print('\nSeat compositions over the run:')
        for k, n in sorted(compositions.items(), key=lambda kv: -kv[1]):
            print(f'  {k}: {n:,} games ({n / total:.1%})')
    stop = json.loads((out / 'stop.json').read_text()) if (out / 'stop.json').exists() else {}
    best = json.loads((out / 'best.json').read_text()) if (out / 'best.json').exists() else {}
    print(f'\nstop: {stop}\nbest: {best}')


def rows(path):
    out = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return out, [r for r in out if r['game'].get('status') == 'completed']


def per_seed(done):
    by = {}
    for r in done:
        by.setdefault(r['seed'], []).append(r['winner_slot'])
    return {s: (sum(1 for w in ws if w == 0) - sum(1 for w in ws if w == 1)) / len(ws) for s, ws in by.items()}


def interval(values):
    mean = sum(values) / len(values)
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1))
    se = sd / math.sqrt(len(values))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def slot_stats(done, slot):
    recs = [r['game']['seats'][r['slots'].index(slot)] for r in done]
    decisions = sum(s['decisions'] for s in recs)
    moves = sum(1 for r in done for m in r['game'].get('robber_moves', []) if m['player'] == r['slots'].index(slot))
    return {'games': len(recs), 'wins': sum(r['winner_slot'] == slot for r in done),
            'mean_points': sum(s['points'] for s in recs) / len(recs),
            'mean_decision_ms': sum(s['decision_ms'] for s in recs) / decisions if decisions else None,
            'robber_moves': moves / len(recs),
            **{k: sum(s.get(k, 0) for s in recs) / len(recs) for k in STAT_KEYS}}


def games_path(run):
    path = Path(run)
    if path.is_file():
        return path
    for root in (ROOT, CANONICAL):
        candidate = root / 'runs' / run / 'games.jsonl'
        if candidate.is_file():
            return candidate
    raise SystemExit(f'no games.jsonl for {run}')


def pair(label, run_a, run_b):
    all_a, done_a = rows(games_path(run_a))
    all_b, done_b = rows(games_path(run_b))
    da, db = per_seed(done_a), per_seed(done_b)
    if set(da) != set(db):
        raise SystemExit(f'{label}: the halves must play the same boards')
    effects = {s: (da[s] - db[s]) / 2 for s in da}
    seating = {s: (da[s] + db[s]) / 2 for s in da}
    a_contrast = interval(list(da.values()))
    b_contrast = interval(list(db.values()))
    # The candidate sits in slot 0 in half A and slot 1 in half B; the control the other way.
    cand = {'A': slot_stats(done_a, 0), 'B': slot_stats(done_b, 1)}
    ctrl = {'A': slot_stats(done_a, 1), 'B': slot_stats(done_b, 0)}
    others = {'A': [slot_stats(done_a, k) for k in range(2, len(all_a[0]['slots']))],
              'B': [slot_stats(done_b, k) for k in range(2, len(all_b[0]['slots']))]}

    def pooled(halves):
        n = sum(h['games'] for h in halves)
        out = {'games': n, 'wins': sum(h['wins'] for h in halves)}
        for k in ['mean_points', 'mean_decision_ms', 'robber_moves'] + STAT_KEYS:
            out[k] = sum(h[k] * h['games'] for h in halves) / n
        return out
    return {'label': label, 'boards': len(effects), 'attempted': [len(all_a), len(all_b)],
            'completed': [len(done_a), len(done_b)],
            'effect': interval(list(effects.values())), 'seating': interval(list(seating.values())),
            'half_a_contrast': a_contrast, 'half_b_contrast': b_contrast,
            'effects': effects,
            'candidate': pooled([cand['A'], cand['B']]), 'control': pooled([ctrl['A'], ctrl['B']]),
            'candidate_halves': cand, 'control_halves': ctrl, 'others': others}


def fmt(x):
    return f'{x[0]:+.3f} ({x[1]:+.3f} to {x[2]:+.3f})'


def pairs(specs, json_out=None):
    results = []
    for label, a, b in specs:
        p = pair(label, a, b)
        results.append(p)
        c, k = p['candidate'], p['control']
        ratio = c['mean_decision_ms'] / k['mean_decision_ms'] if k['mean_decision_ms'] else float('nan')
        print(f"{p['label']}: {p['boards']} boards, completed {p['completed'][0]} and {p['completed'][1]} "
              f"of {p['attempted'][0]} and {p['attempted'][1]}")
        print(f"  effect {fmt(p['effect'])}; seating term {fmt(p['seating'])}; "
              f"half A {fmt(p['half_a_contrast'])}, half B {fmt(p['half_b_contrast'])}")
        print(f"  candidate {c['wins']}/{c['games']} wins, control {k['wins']}/{k['games']}; "
              f"decision {c['mean_decision_ms']:.0f} vs {k['mean_decision_ms']:.0f} ms ({ratio:.2f}x)")
        for name, s in (('candidate', c), ('control', k)):
            print(f"  {name}: points {s['mean_points']:.2f}, cities {s['cities_built']:.2f}, settlements "
                  f"{s['settlements_built']:.2f}, roads {s['roads_built']:.2f}, dev {s['development_bought']:.2f}, "
                  f"knights {s['knights_played']:.2f}, trades {s['player_trades']:.2f}, bank {s['bank_trades']:.2f}, "
                  f"offers {s['offers']:.2f}, counters {s['counters']:.2f}, discards {s['cards_discarded']:.2f}, "
                  f"robbed {s['times_robbed']:.2f}, robber moves {s['robber_moves']:.2f}")
        for half in ('A', 'B'):
            others = ', '.join(f"slot {i + 2}: {o['wins']}/{o['games']}" for i, o in enumerate(p['others'][half]))
            print(f"  other seats half {half}: {others}")
    if len(results) > 1:
        pooled = [e for p in results for e in p['effects'].values()]
        print(f'pooled after the fact over {len(pooled)} boards: {fmt(interval(pooled))}')
    if json_out:
        write_json(json_out, results)
    return results


def asset(results_path, out_path):
    """The effects plot of the report from the JSON written by `pairs --json`: one point per
    contrast with its 95 percent interval over boards, split by lineup."""
    results = json.loads(Path(results_path).read_text())
    ticks = []
    series = {'L1': [], 'L2': []}
    for p in results:
        label, lineup = p['label'], ('L1' if '-l1-' in p['label'] else 'L2')
        name = {'challenger-l2-dev': 'Challenger over frozen', 'challenger-l1-dev': 'Challenger over frozen',
                'control-l2-dev': 'Fine-tune over frozen', 'population-l1-conf': 'Population over frozen',
                'population-l2-conf': 'Population over frozen',
                'population-vs-challenger-l2-conf': 'Population over challenger'}.get(label, label)
        if name not in ticks:
            ticks.append(name)
        mean, lo, hi = p['effect']
        series[lineup].append({'x': ticks.index(name), 'y': round(mean, 3), 'low': round(lo, 3), 'high': round(hi, 3)})
    lows = [pt['low'] for s in series.values() for pt in s]
    highs = [pt['high'] for s in series.values() for pt in s]
    data = {
        'schema': 1, 'kind': 'plot', 'variant': 'scatter',
        'title': 'A challenger trained against the frozen tables, and the population remedy',
        'evidence': 'measured',
        'source': ('Source: reports/best-response.mdx, The evidence; analysis/best_response.py pairs. Seating-corrected '
                   'swapped pairs of 64 deterministic boards, four rotations in each half, 256 games per half, every '
                   'cohort complete unless the report says otherwise. 95% intervals over boards. Exploitability on '
                   'boards 1400-1463, the remedy on boards 1464-1527.'),
        'caption': 'Each point is the candidate\'s change in wins per game over its control at one table.',
        'x': {'label': 'Contrast', 'min': 0, 'max': max(1, len(ticks) - 1), 'ticks': ticks},
        'y': {'label': 'Change in wins per game', 'min': round(min(lows) - 0.02, 2), 'max': round(max(highs) + 0.02, 2)},
        'series': [{'label': 'Builders (L1)', 'points': series['L1']},
                   {'label': 'Population table (L2)', 'points': series['L2']}],
        'reference': {'y': 0, 'label': 'No difference'},
    }
    write_json(out_path, data)
    print(f'wrote {out_path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ['train', 'freeze', 'training']:
        commands.add_parser(name).add_argument('arm', choices=sorted(ARMS))
    p = commands.add_parser('pairs')
    p.add_argument('--pair', nargs=3, action='append', required=True, metavar=('LABEL', 'RUN_A', 'RUN_B'),
                   help='label, run (or games.jsonl) with the candidate in slot 0, run with it in slot 1')
    p.add_argument('--json', help='write the results as JSON')
    a = commands.add_parser('asset')
    a.add_argument('results', help='JSON written by pairs --json')
    a.add_argument('--out', default=str(ROOT / 'content/assets/best-response-effects.json'))
    args = parser.parse_args()
    if args.command == 'train':
        return train(args.arm)
    if args.command == 'freeze':
        return freeze(args.arm)
    if args.command == 'training':
        return training(args.arm)
    if args.command == 'asset':
        return asset(args.results, args.out)
    pairs(args.pair, args.json)
    return 0


if __name__ == '__main__':
    sys.exit(main())

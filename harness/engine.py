"""Engine-arena experiments: paired-seed tournaments played offline by the server's Rust
`tournament` binary. Seats receive only their redacted observation and participant events.
This is the development tier; protocol-arena runs remain the confirmation tier."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import uuid

from .notebook import canonical_root, require_study
from .records import digest, git_state, now, wilson, write_json

ROOT = Path(os.environ.get('SETTLERS_RESEARCH_DIR', Path(__file__).resolve().parents[1])).resolve()
SEAT = r'(fast|eta|legal|v1|v2)(:\{.*\})?'


def register(root, seats, seeds, hypothesis, decision_rule, *, study, points=10, rotations=None, max_turns=500, deterministic=False):
    require_study(root, study)
    if not 2 <= len(seats) <= 4 or any(not re.fullmatch(SEAT, s) for s in seats):
        raise ValueError('Use 2–4 engine seats: fast, eta, legal, v1, v2, or v1:{json}/v2:{json}')
    if not re.fullmatch(r'\d+-\d+', seeds):
        raise ValueError('Seeds must be a range like 0-63')
    first, last = map(int, seeds.split('-'))
    if last < first or not 3 <= points <= 20:
        raise ValueError('Seed range must be ascending and points 3–20')
    for seat in seats:
        if ':' in seat:
            json.loads(seat.split(':', 1)[1])
    identifier = str(uuid.uuid4())
    rotations = rotations or len(seats)
    folder = root / 'experiments'
    folder.mkdir(exist_ok=True)
    (folder / f'{identifier}.toml').write_text(
        f'id = {json.dumps(identifier)}\nstudy = {json.dumps(study)}\narena = "engine"\n'
        f'hypothesis = {json.dumps(hypothesis)}\ndecision_rule = {json.dumps(decision_rule)}\n'
        f'players = {json.dumps(seats)}\nseeds = {json.dumps(seeds)}\nrotations = {rotations}\n'
        f'games = {(last - first + 1) * rotations}\npoints_to_win = {points}\nmax_turns = {max_turns}\n'
        f'deterministic = {"true" if deterministic else "false"}\n'
    )
    return identifier


def table_digests(seats):
    """SHA-256 of every learned-table file a seat spec names, so a run pins the exact tables."""
    out = {}
    for seat in seats:
        if ':' not in seat:
            continue
        leaf = json.loads(seat.split(':', 1)[1]).get('leaf') or {}
        path = leaf.get('tables')
        if path:
            file = Path(path)
            if not file.is_file():
                raise ValueError(f'Learned tables not found: {path}')
            out[path] = digest(file)
    return out


def load(root, experiment):
    if not re.fullmatch(r'[a-z0-9-]+', experiment):
        raise ValueError('Invalid experiment ID')
    data = tomllib.loads((root / 'experiments' / f'{experiment}.toml').read_text())
    if data.get('arena') != 'engine':
        raise ValueError('Not an engine-arena experiment; use just run for protocol experiments')
    return data


def summarize(rows, seats):
    """Per-slot outcomes over completed games plus paired contrasts between slots."""
    completed = [r for r in rows if r['game']['status'] == 'completed']
    slots = []
    for slot, seat in enumerate(seats):
        games = [(r, r['slots'].index(slot)) for r in completed]
        wins = sum(r['winner_slot'] == slot for r, _ in games)
        pts = [r['game']['seats'][i]['points'] for r, i in games]
        recs = [r['game']['seats'][i] for r, i in games]
        decisions = sum(s['decisions'] for s in recs)
        first_cities = [s['first_city_turn'] for s in recs if s.get('first_city_turn') is not None]
        slots.append({
            'slot': slot, 'seat': seat, 'wins': wins, 'losses': len(games) - wins, 'completed': len(games),
            'win_rate': wins / len(games) if games else None, 'wilson95': wilson(wins, len(games)),
            'mean_points': sum(pts) / len(pts) if pts else None,
            'mean_decision_ms': sum(s['decision_ms'] for s in recs) / decisions if decisions else None,
            'max_decision_ms': max((s['max_decision_ms'] for s in recs), default=None),
            'builds': {k: sum(s.get(k, 0) for s in recs) / len(recs) if recs else None for k in
                       ['settlements_built', 'cities_built', 'roads_built', 'development_bought',
                        'knights_played', 'army_awards', 'bank_trades',
                        'player_trades', 'cards_discarded', 'times_robbed', 'turns_over_limit',
                        'offers', 'offers_accepted']},
            'first_city_turn_mean': sum(first_cities) / len(first_cities) if first_cities else None,
            'first_city_games': len(first_cities),
            'invalid': sum(s['invalid'] for s in recs), 'stalls': sum(s['stalls'] for s in recs),
            'forced': sum(s['forced'] for s in recs), 'search_errors': sum(s['effort']['errors'] for s in recs),
        })
    # Paired seed contrast: per seed, slot-0 wins minus slot-1 wins across rotations.
    contrast = None
    if len(seats) >= 2:
        by_seed = {}
        for r in completed:
            by_seed.setdefault(r['seed'], []).append(r)
        diffs = [sum((r['winner_slot'] == 0) - (r['winner_slot'] == 1) for r in games) / len(games)
                 for games in by_seed.values()]
        if diffs:
            mean = sum(diffs) / len(diffs)
            sd = math.sqrt(sum((d - mean) ** 2 for d in diffs) / max(1, len(diffs) - 1))
            se = sd / math.sqrt(len(diffs))
            contrast = {'slots': [0, 1], 'seeds': len(diffs), 'mean_win_difference': mean,
                        'standard_error': se, 'interval95': [mean - 1.96 * se, mean + 1.96 * se]}
    return {'attempted': len(rows), 'completed': len(completed), 'incomplete': len(rows) - len(completed),
            'mean_turns': sum(r['game']['turns'] for r in completed) / len(completed) if completed else None,
            'slots': slots, 'paired_contrast': contrast, 'tier': 'engine arena (paired seeds, redacted observations)'}


def table(summary):
    lines = ['| Slot / seat | Wins | Completed | Win rate | 95% Wilson interval | Mean points | Mean decision |',
             '| --- | ---: | ---: | ---: | --- | ---: | ---: |']
    for row in summary['slots']:
        i = row['wilson95']
        seat = row['seat'] if len(row['seat']) <= 60 else row['seat'][:57] + '...'
        lines.append(f"| {row['slot']} / `{seat}` | {row['wins']} | {row['completed']} | "
                     f"{row['win_rate']:.1%} | {i[0]:.1%}–{i[1]:.1%} | {row['mean_points']:.2f} | {row['mean_decision_ms']:.1f} ms |"
                     if i else f"| {row['slot']} / `{seat}` | 0 | 0 | — | — | — | — |")
    return '\n'.join(lines)


def run(root, experiment_id, server, threads=None):
    experiment = load(root, experiment_id)
    server = Path(server).resolve()
    binary = server / 'target/release/tournament'
    if not binary.is_file():
        raise ValueError('Build the arena first: cargo build --release -p settlers-arena (in the server checkout)')
    run_id = str(uuid.uuid4())
    folder = root / 'runs' / run_id
    folder.mkdir(parents=True)
    protocol = root / 'experiments' / f'{experiment_id}.toml'
    threads = threads or os.cpu_count() or 1
    plan = {'schema': 1, 'run_id': run_id, 'created_at': now(), 'experiment': experiment_id, 'arena': 'engine',
            'experiment_sha256': digest(protocol), 'seats': experiment['players'], 'seeds': experiment['seeds'],
            'rotations': experiment['rotations'], 'games': experiment['games'], 'points_to_win': experiment['points_to_win'],
            'max_turns': experiment['max_turns'], 'threads': threads, 'server': str(server),
            'deterministic': bool(experiment.get('deterministic')),
            'tournament_sha256': digest(binary), 'research_git': git_state(root), 'server_git': git_state(server),
            'tables_sha256': table_digests(experiment['players']),
            'seed_policy': 'explicit engine seeds; every seed played once per lineup rotation; policies never see seeds',
            'runtime': {'python': sys.version, 'platform': sys.platform}}
    write_json(folder / 'manifest.json', plan)
    (folder / 'experiment.toml').write_bytes(protocol.read_bytes())
    command = [str(binary), '--seeds', experiment['seeds'], '--rotations', str(experiment['rotations']),
               '--threads', str(threads), '--points', str(experiment['points_to_win']),
               '--max-turns', str(experiment['max_turns']), '--out', str(folder / 'games.jsonl')]
    for seat in experiment['players']:
        command += ['--seat', seat]
    if experiment.get('deterministic'):
        command.append('--deterministic')
    print(f'run_id={run_id}', flush=True)
    status = 'completed'
    try:
        with (folder / 'tournament.log').open('w') as log:
            subprocess.run(command, cwd=server, check=True, stdout=log, stderr=subprocess.STDOUT)
    except KeyboardInterrupt:
        status = 'interrupted'
    except subprocess.CalledProcessError as error:
        status = 'invalid'
        write_json(folder / 'failure.json', {'error': str(error), 'at': now()})
    rows = []
    games = folder / 'games.jsonl'
    if games.exists():
        rows = [json.loads(line) for line in games.read_text().splitlines() if line.strip()]
    summary = summarize(rows, experiment['players'])
    if status == 'completed' and summary['completed'] != experiment['games']:
        status = 'censored' if summary['attempted'] == experiment['games'] else 'invalid'
    summary.update(status=status, planned=experiment['games'], run_id=run_id,
                   unplayed=experiment['games'] - summary['attempted'])
    write_json(folder / 'summary.json', summary)
    inventory = {str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}
    write_json(folder / 'inventory.json', inventory)
    records = root / 'records/runs'
    records.mkdir(parents=True, exist_ok=True)
    contrast = summary['paired_contrast']
    contrast_text = (f"Paired contrast slot 0 minus slot 1: {contrast['mean_win_difference']:+.3f} wins per game over "
                     f"{contrast['seeds']} seeds (95% interval {contrast['interval95'][0]:+.3f} to {contrast['interval95'][1]:+.3f}).\n\n"
                     if contrast else '')
    mode = 'deterministic tapes' if experiment.get('deterministic') else 'paired boards, shared stream'
    (records / f'{run_id}.md').write_text(
        f'# Run {run_id}\n\nStatus: **{status}**. Experiment: `{experiment_id}`. Tier: engine arena (paired seeds, {mode}).\n\n'
        f"Planned: {experiment['games']}. Attempted: {summary['attempted']}. Completed: {summary['completed']}. "
        f"Incomplete: {summary['incomplete']}. Unplayed: {summary['unplayed']}.\n\n" + table(summary) + '\n\n' + contrast_text
        + f"Manifest SHA-256: `{digest(folder / 'manifest.json')}`. Inventory SHA-256: `{digest(folder / 'inventory.json')}`.\n\n"
        + 'Games were played offline by the engine arena with explicit seeds; every seed was played once per lineup '
        + 'rotation. Seats received only their own redacted observation and participant events. This tier supports '
        + 'development and diagnosis; it is not a protocol-arena confirmation.\n')
    print(table(summary), flush=True)
    if contrast_text:
        print(contrast_text.strip(), flush=True)
    return 0 if status == 'completed' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', default=os.environ.get('SETTLERS_SERVER_DIR', str(canonical_root(ROOT).parent / 'server')))
    commands = parser.add_subparsers(dest='command', required=True)
    reg = commands.add_parser('register')
    reg.add_argument('--seats', nargs='+', required=True)
    reg.add_argument('--seeds', required=True, help='Inclusive seed range, for example 0-63')
    reg.add_argument('--rotations', type=int)
    reg.add_argument('--points', type=int, default=10)
    reg.add_argument('--max-turns', type=int, default=500)
    reg.add_argument('--hypothesis', required=True)
    reg.add_argument('--decision-rule', required=True)
    reg.add_argument('--study', required=True)
    reg.add_argument('--deterministic', action='store_true', help='Deterministic mode: seed-indexed dice, theft, and deck tapes')
    runner = commands.add_parser('run')
    runner.add_argument('experiment')
    runner.add_argument('--threads', type=int)
    args = parser.parse_args()
    try:
        if args.command == 'register':
            print(register(ROOT, args.seats, args.seeds, args.hypothesis, args.decision_rule, study=args.study,
                           points=args.points, rotations=args.rotations, max_turns=args.max_turns,
                           deterministic=args.deterministic))
        else:
            return run(ROOT, args.experiment, args.server, args.threads)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

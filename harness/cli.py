import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import uuid

from .arena import run
from .protocol import Client
from .publish import archive, exhibit

DEFAULT_ROOT = Path.cwd() if (Path.cwd() / 'policies/registry.toml').is_file() else Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('SETTLERS_RESEARCH_DIR', DEFAULT_ROOT)).resolve()


def register(root, players, games, hypothesis, decision_rule, points=10):
    registry = tomllib.loads((root / 'policies/registry.toml').read_text())
    if not 2 <= len(players) <= 4 or any(p not in registry for p in players):
        raise ValueError('Choose 2–4 policies from the registry')
    if games < 1 or not 3 <= points <= 20:
        raise ValueError('Games must be positive and points must be 3–20')
    identifier = str(uuid.uuid4())
    folder = root / 'experiments'
    folder.mkdir(exist_ok=True)
    (folder / f'{identifier}.toml').write_text(
        f'id = {json.dumps(identifier)}\nhypothesis = {json.dumps(hypothesis)}\n'
        f'decision_rule = {json.dumps(decision_rule)}\nplayers = {json.dumps(players)}\n'
        f'games = {games}\npoints_to_win = {points}\nmatch_seconds = 600\n'
        'decision_seconds = 5\nmax_turns = 3000\n'
    )
    return identifier


def main():
    parser = argparse.ArgumentParser(description='Headless Settlers research')
    parser.add_argument('--base', default=os.environ.get('SETTLERS_SERVER_URL', 'http://127.0.0.1:5555'))
    parser.add_argument('--server', default=os.environ.get('SETTLERS_SERVER_DIR', str(ROOT.parent / 'server')))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('policies')
    commands.add_parser('doctor')
    commands.add_parser('setup')
    commands.add_parser('server')
    experiment = commands.add_parser('register')
    experiment.add_argument('--players', nargs='+', required=True)
    experiment.add_argument('--games', type=int, default=40)
    experiment.add_argument('--hypothesis', required=True)
    experiment.add_argument('--decision-rule', required=True)
    experiment.add_argument('--points', type=int, default=10)
    runner = commands.add_parser('run')
    runner.add_argument('experiment')
    smoke = commands.add_parser('match')
    smoke.add_argument('players', nargs='*', default=['fast', 'eta', 'fast', 'eta'])
    smoke.add_argument('--games', type=int, default=4)
    smoke.add_argument('--points', type=int, default=10)
    archiver = commands.add_parser('archive')
    archiver.add_argument('run_id')
    archiver.add_argument('destination')
    publisher = commands.add_parser('publish')
    publisher.add_argument('run_id')
    publisher.add_argument('--match', type=int, default=0)
    publisher.add_argument('--slug', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'policies':
            for name, spec in tomllib.loads((ROOT / 'policies/registry.toml').read_text()).items():
                print(f"{name:16} {spec['transport']:8} {spec['description']}")
        elif args.command == 'doctor':
            client = Client.guest(args.base, 'Research health check')
            print(json.dumps(client.request('GET', '/v1/health')))
        elif args.command == 'setup':
            subprocess.run(['cargo', 'build', '--release', '--locked', '-p', 'server', '--bin', 'server',
                            '-p', 'settlers-policies', '--bin', 'remote'], cwd=args.server, check=True)
        elif args.command == 'server':
            runtime = ROOT / '.runtime/server'
            runtime.mkdir(parents=True, exist_ok=True)
            env = dict(os.environ, SETTLERS_BIND=os.environ.get('SETTLERS_BIND', '127.0.0.1:5555'),
                       SETTLERS_MODE='local', SETTLERS_STORAGE='local', SETTLERS_DATA_DIR=str(runtime),
                       SETTLERS_ALLOWED_ORIGINS='http://127.0.0.1:3107,http://localhost:3107')
            binary = Path(args.server).resolve() / 'target/release/server'
            os.execve(binary, [str(binary)], env)
        elif args.command == 'register':
            print(register(ROOT, args.players, args.games, args.hypothesis, args.decision_rule, args.points))
        elif args.command in ('run', 'match'):
            if args.command == 'match':
                args.experiment = register(ROOT, args.players, args.games,
                                           'Check protocol plumbing for this lineup; no strength claim.',
                                           'Every game completes without invalid actions or server timeout moves.', args.points)
                print(f'experiment={args.experiment}', flush=True)
            if not re.fullmatch(r'[a-z0-9-]+', args.experiment):
                raise ValueError('Invalid experiment ID')
            experiment_data = tomllib.loads((ROOT / 'experiments' / f'{args.experiment}.toml').read_text())
            args.games = experiment_data['games']
            return run(ROOT, args)
        elif args.command == 'archive':
            archive(ROOT, args.run_id, args.destination)
        elif args.command == 'publish':
            exhibit(ROOT, args.run_id, args.match, args.slug)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

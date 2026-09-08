"""Run independent policy processes against one authoritative HTTP game server."""
from collections import Counter
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import tomllib
import uuid

from .protocol import Client, ServerError, public_frame
from .records import digest, git_state, now, summarize, summary_table, write_json


class PolicyProcess:
    def __init__(self, spec, variables, root, log_path):
        self.transport = spec['transport']
        self.log = log_path.open('wb')
        argv = [arg.format_map(variables) for arg in spec['command']]
        env = dict(os.environ, SETTLERS_MOVE_DELAY_MS='0', SETTLERS_TRADE_WAIT_MS='0')
        env.pop('SETTLERS_HUMAN_SEAT', None)
        try:
            self.process = subprocess.Popen(
                argv, cwd=root, env=env, start_new_session=True,
                stdin=subprocess.PIPE if self.transport == 'stdio' else subprocess.DEVNULL,
                stdout=subprocess.PIPE if self.transport == 'stdio' else self.log,
                stderr=self.log,
            )
        except BaseException:
            self.log.close()
            raise
        self.buffer = b''
        if self.transport == 'stdio':
            os.set_blocking(self.process.stdin.fileno(), False)

    def choose(self, message, timeout):
        deadline = time.monotonic() + timeout
        pending = memoryview(json.dumps(message).encode() + b'\n')
        while pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([], [self.process.stdin], [], remaining)[1]:
                raise TimeoutError('policy did not consume its observation before the deadline')
            written = os.write(self.process.stdin.fileno(), pending[:4096])
            pending = pending[written:]
        while b'\n' not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise TimeoutError('policy decision exceeded its time budget')
            chunk = os.read(self.process.stdout.fileno(), 4096)
            if not chunk:
                raise RuntimeError('policy closed stdout before returning a command')
            self.buffer += chunk
            if len(self.buffer) > 16384:
                raise ValueError('policy response exceeds the protocol 16 KiB limit')
        line, self.buffer = self.buffer.split(b'\n', 1)
        command = json.loads(line)
        if command is not None and (not isinstance(command, dict) or 'type' not in command):
            raise ValueError('policy must return a protocol Command object or null')
        return command

    def close(self):
        # Kill the owned process group, including descendants of policy wrappers.
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except PermissionError:
                self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGKILL)
            self.process.wait(timeout=3)
        for stream in [self.process.stdin, self.process.stdout]:
            if stream:
                stream.close()
        self.log.close()


def match(root, run_dir, index, slots, plan, registry, topology):
    folder = run_dir / f'match-{index:04d}'
    folder.mkdir()
    private = folder / 'private'
    private.mkdir(mode=0o700)
    result = {'index': index, 'slots': slots, 'status': 'running', 'started_at': now(),
              'game_id': None, 'winner': None, 'points': [], 'turns': 0,
              'event_counts': {}, 'history_complete': False, 'policy_decisions': 0,
              'decision_seconds': 0., 'conflicts': 0}
    processes, clients = [], []
    host, last_view = None, None
    cursor, last_version = 0, -1
    counts = Counter()
    started = time.monotonic()
    frames = (folder / 'frames.jsonl').open('w')
    events = (folder / 'events.jsonl').open('w')

    def drain(target=None):
        nonlocal cursor
        batches = []
        deadline = time.monotonic() + 15
        while True:
            page = host.history(result['game_id'], cursor)
            for batch in page['events']:
                if batch['sequence'] <= cursor:
                    raise ValueError('history sequence did not advance')
                events.write(json.dumps(batch) + '\n')
                batches.append(batch)
                for event in batch['events']:
                    kind = event['event']['type'] if event['type'] == 'rule' else event['type']
                    counts[kind] += 1
            cursor = page['next_after']
            bound = target if target is not None else page['current_version']
            if cursor >= bound:
                break
            if time.monotonic() > deadline:
                raise TimeoutError('public event archive did not catch up')
            if page['archive_pending'] or not page['events']:
                time.sleep(.05)
        events.flush()
        return batches

    try:
        host = Client.guest(plan['base'], 'Research observer')
        (private / 'host.jwt').write_text(host.token)
        created = host.request('POST', '/v1/games', {
            'name': f"{plan['run_id']} match {index}", 'settings': plan['settings'],
            'host_as_player': False, 'research': True,
        })
        result['game_id'] = created['id']
        write_json(folder / 'result.json', result)
        for seat, slot in enumerate(slots):
            name = f"{plan['players'][slot]} slot {slot}"
            client = Client.guest(plan['base'], name)
            client.command(created['id'], host.game(created['id'])['version'],
                           {'type': 'join_agent', 'name': name})
            clients.append(client)
            token_file = private / f'{seat}.jwt'
            token_file.write_text(client.token)
            token_file.chmod(0o600)
        # Seat ownership is established before any process can race to join.
        for seat, slot in enumerate(slots):
            name = f"{plan['players'][slot]} slot {slot}"
            variables = {'server': plan['server'], 'base': plan['base'], 'game': created['id'],
                         'token_file': str(private / f'{seat}.jwt'), 'name': name,
                         'python': sys.executable, 'root': str(root)}
            processes.append(PolicyProcess(registry[plan['players'][slot]], variables, root,
                                           private / f'policy-{seat}.log'))
        ready_by = time.monotonic() + 20
        while True:
            view = host.game(created['id'])
            connected = {m['seat'] for m in view['members'] if m['connected']}
            if all(p.transport == 'stdio' or seat in connected for seat, p in enumerate(processes)):
                try:
                    host.command(created['id'], view['version'], {'type': 'start'})
                    break
                except ServerError as error:
                    if error.data['code'] != 'conflict':
                        raise
            if any(p.process.poll() is not None for p in processes):
                raise RuntimeError('policy exited before the game started')
            if time.monotonic() >= ready_by:
                raise TimeoutError('remote policies did not connect before start')
            time.sleep(.05)

        # Each stdio policy has its own event cursor and receives its own filtered
        # history. Spectator history is never used as a substitute for private delivery.
        policy_cursors = [0] * len(slots)
        last_decision = [-1] * len(slots)
        while time.monotonic() - started < plan['match_seconds']:
            last_view = host.game(created['id'])
            game = last_view['game']
            if last_view['version'] != last_version:
                frames.write(json.dumps(public_frame(last_view)) + '\n')
                frames.flush()
                last_version = last_view['version']
                drain(last_version)
            if game['phase']['type'] == 'finished':
                result.update(status='completed', winner=game['phase']['winner'],
                              points=[p['points'] for p in game['players']], turns=game['turn'],
                              history_complete=cursor >= last_version)
                break
            if game['turn'] > plan['max_turns']:
                raise TimeoutError('match exceeded the preregistered turn cap')
            if any(p.process.poll() is not None for p in processes):
                # A remote may exit immediately after committing the winning move.
                if host.game(created['id'])['game']['phase']['type'] == 'finished':
                    continue
                raise RuntimeError('policy exited before a terminal game state')
            moved = False
            for seat, policy in enumerate(processes):
                if policy.transport != 'stdio':
                    continue
                view = clients[seat].game(created['id'])
                if view['version'] == last_decision[seat]:
                    continue
                last_decision[seat] = view['version']
                history = []
                history_deadline = time.monotonic() + 15
                while policy_cursors[seat] < view['version']:
                    page = clients[seat].history(created['id'], policy_cursors[seat])
                    history.extend(page['events'])
                    policy_cursors[seat] = page['next_after']
                    if time.monotonic() > history_deadline:
                        raise TimeoutError('policy event history did not catch up')
                    if page['archive_pending'] or not page['events']:
                        time.sleep(.05)
                decision_start = time.monotonic()
                command = policy.choose({'protocol': 1, 'view': view, 'topology': topology,
                                         'events': history}, plan['decision_seconds'])
                result['policy_decisions'] += 1
                result['decision_seconds'] += time.monotonic() - decision_start
                if result['policy_decisions'] > plan['max_decisions']:
                    raise TimeoutError('match exceeded the decision cap')
                if command is not None:
                    try:
                        clients[seat].command(created['id'], view['version'], command)
                        moved = True
                    except ServerError as error:
                        if error.data['code'] in ('conflict', 'trade_taken', 'trade_unavailable'):
                            result['conflicts'] += 1
                        else:
                            raise
            if not moved:
                time.sleep(.03)
        else:
            raise TimeoutError('match exceeded the preregistered wall-clock cap')
    except KeyboardInterrupt:
        result.update(status='interrupted', error='interrupted by operator')
    except Exception as error:
        result.update(status='censored' if isinstance(error, TimeoutError) else 'invalid',
                      error=str(error))
    finally:
        if last_view and last_view.get('game'):
            result['turns'] = last_view['game']['turn']
        cleanup_errors = []
        for policy in processes:
            try:
                policy.close()
            except Exception as error:
                cleanup_errors.append(str(error))
        if cleanup_errors:
            result.update(status='invalid', cleanup_errors=cleanup_errors)
        frames.close()
        events.close()
        result.update(event_counts=dict(counts), duration_seconds=time.monotonic() - started,
                      finished_at=now(), event_cursor=cursor)
        if counts['timed_out'] and result['status'] == 'completed':
            result.update(status='invalid', error='server timeout actions affected this game')
        write_json(folder / 'result.json', result)
    return result


def run(root, args):
    registry_path = root / 'policies/registry.toml'
    registry = tomllib.loads(registry_path.read_text())
    protocol_path = root / 'experiments' / f'{args.experiment}.toml'
    experiment = tomllib.loads(protocol_path.read_text())
    players = experiment['players']
    if not 2 <= len(players) <= 4 or args.games < 1 or any(p not in registry for p in players):
        raise ValueError('Use 2–4 registered policies and at least one game')
    if args.games != experiment['games']:
        raise ValueError('Game count must match the registered experiment; create a new experiment to change it')
    server = Path(args.server).resolve()
    run_id = str(uuid.uuid4())
    run_dir = root / 'runs' / run_id
    run_dir.mkdir(parents=True)
    source_paths = [p for directory in ['harness', 'policies'] for p in (root / directory).rglob('*')
                    if p.suffix in ('.py', '.rs', '.ts', '.tsx', '.toml')]
    plan = {'schema': 1, 'run_id': run_id, 'created_at': now(), 'experiment': args.experiment,
            'experiment_sha256': digest(protocol_path), 'players': players,
            'base': args.base, 'server': str(server), 'games': args.games,
            'settings': {'players': len(players), 'points_to_win': experiment['points_to_win'],
                         'discard_limit': 7, 'turn_seconds': 120},
            'match_seconds': experiment['match_seconds'], 'decision_seconds': experiment['decision_seconds'],
            'max_turns': experiment['max_turns'], 'max_decisions': 30000,
            'seed_policy': 'server-generated; unpaired; no seed exposed to policies',
            'research_git': git_state(root), 'server_git': git_state(server),
            'source_sha256': {str(p.relative_to(root)): digest(p) for p in sorted(source_paths)},
            'runtime': {'python': sys.version, 'platform': sys.platform},
            'native_binary_sha256': {name: digest(server / 'target/release' / name)
                                    for name in ['server', 'remote'] if (server / 'target/release' / name).exists()}}
    write_json(run_dir / 'manifest.json', plan)
    (run_dir / 'experiment.toml').write_bytes(protocol_path.read_bytes())
    # Retain the exact authored implementation even when the working tree is dirty.
    for source in source_paths:
        destination = run_dir / 'source' / source.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    results = []
    status = 'running'
    print(f'run_id={run_id}', flush=True)
    try:
        observer = Client.guest(args.base, 'Research preflight')
        health = observer.request('GET', '/v1/health')
        if health['protocol'] != 1:
            raise ValueError(f"Unsupported protocol version {health['protocol']}")
        topology = observer.request('GET', '/v1/topology')
        write_json(run_dir / 'topology.json', topology)
        for index in range(args.games):
            slots = [(seat + index) % len(players) for seat in range(len(players))]
            result = match(root, run_dir, index, slots, plan, registry, topology)
            results.append(result)
            write_json(run_dir / 'summary.json', summarize(results, players))
            print(f"match={index} game={result['game_id']} status={result['status']} winner={result['winner']} turns={result['turns']}", flush=True)
            if result['status'] != 'completed':
                status = result['status']
                break  # Investigate failure before spending the remaining budget.
        else:
            status = 'completed'
    except KeyboardInterrupt:
        status = 'interrupted'
    except Exception as error:
        status = 'invalid'
        write_json(run_dir / 'failure.json', {'error': str(error), 'at': now()})
        print(str(error), file=sys.stderr)
    finally:
        summary = summarize(results, players)
        summary.update(status=status, planned=args.games, unplayed=args.games - len(results), run_id=run_id)
        write_json(run_dir / 'summary.json', summary)
        inventory = {str(p.relative_to(run_dir)): digest(p) for p in sorted(run_dir.rglob('*'))
                     if p.is_file() and 'private' not in p.relative_to(run_dir).parts}
        write_json(run_dir / 'inventory.json', inventory)
        records = root / 'records/runs'
        records.mkdir(parents=True, exist_ok=True)
        record = (f'# Run {run_id}\n\nStatus: **{status}**. Experiment: `{args.experiment}`.\n\n'
                  f"Planned: {args.games}. Attempted: {summary['attempted']}. Completed: {summary['completed']}. "
                  f"Incomplete: {summary['incomplete']}. Unplayed: {summary['unplayed']}.\n\n"
                  + summary_table(summary) + '\n\n'
                  + f"Manifest SHA-256: `{digest(run_dir / 'manifest.json')}`.\n\n"
                  + f"Inventory SHA-256: `{digest(run_dir / 'inventory.json')}`.\n\n"
                  + 'Artifacts are local under `runs/' + run_id + '/`; no remote durability is claimed until an archive receipt exists.\n\n'
                  + 'Intervals are descriptive per competitor slot across completed games; outcomes within a game are dependent. '
                  + 'Incomplete games are not losses. Seat rotation does not pair random seeds.\n')
        (records / f'{run_id}.md').write_text(record)
        print(summary_table(summary), flush=True)
    return 0 if status == 'completed' else 1

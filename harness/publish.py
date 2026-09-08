"""Produce compact public exhibits and verified, credential-free archive bundles."""
import json
from pathlib import Path
import re
import tarfile

from .records import digest, now, summary_table, write_json


def run_path(root, run_id):
    if not re.fullmatch(r'[a-f0-9-]{36}', run_id):
        raise ValueError('Expected a run UUID')
    path = root / 'runs' / run_id
    if not path.is_dir():
        raise ValueError(f'Unknown run {run_id}')
    return path


def verified_inventory(folder):
    inventory = json.loads((folder / 'inventory.json').read_text())
    for name, expected in inventory.items():
        path = (folder / name).resolve()
        if not path.is_relative_to(folder.resolve()) or 'private' in Path(name).parts:
            raise ValueError('Invalid artifact inventory path')
        if digest(path) != expected:
            raise ValueError(f'Artifact changed after finalization: {name}')
    return inventory


def archive(root, run_id, destination):
    folder = run_path(root, run_id)
    inventory = verified_inventory(folder)
    destination = Path(destination).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / f'{run_id}.tar.gz'
    # Exclusive creation: an archive key is immutable. Only inventory-listed public
    # files enter it; private credentials and process logs are never bundled.
    with output.open('xb') as target:
        with tarfile.open(fileobj=target, mode='w:gz') as bundle:
            for name in [*inventory, 'inventory.json']:
                bundle.add(folder / name, arcname=f'{run_id}/{name}', recursive=False)
    with tarfile.open(output, 'r:gz') as bundle:
        import hashlib
        for name, expected in inventory.items():
            if hashlib.sha256(bundle.extractfile(f'{run_id}/{name}').read()).hexdigest() != expected:
                raise ValueError(f'Archive verification failed: {name}')
    receipt_dir = root / 'records/artifacts'
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / f'{run_id}.md'
    text = (f'# Archive {run_id}\n\nVerified at {now()}.\n\n'
            f'Location: `{output}`\n\nSHA-256: `{digest(output)}`\n\n'
            'This receipt proves local copy integrity. A local path is not a public download or a remote backup. '
            'After uploading to an authorized immutable object store, append its verified URL and retain this digest.\n')
    with receipt.open('x') as target:
        target.write(text)
    print(output)


def exhibit(root, run_id, match_index, slug):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug):
        raise ValueError('Use a lowercase hyphenated exhibit slug')
    folder = run_path(root, run_id)
    verified_inventory(folder)
    summary = json.loads((folder / 'summary.json').read_text())
    match_folder = folder / f'match-{match_index:04d}'
    result = json.loads((match_folder / 'result.json').read_text())
    if result['status'] != 'completed' or not result['history_complete']:
        raise ValueError('Select a completed game with complete public event history')
    chart = {'schema': 1, 'kind': 'chart', 'title': 'Win rate by competitor', 'unit': 'fraction',
             'caption': f"Run {run_id}. {summary['completed']} completed of {summary['planned']} planned games. 95% Wilson intervals; descriptive evidence only.",
             'rows': [{'label': f"{r['policy']} · slot {r['slot']}", 'value': r['win_rate'],
                       'low': r['wilson95'][0], 'high': r['wilson95'][1], 'n': r['completed']}
                      for r in summary['players'] if r['wilson95']]}
    source = [json.loads(line) for line in (match_folder / 'frames.jsonl').read_text().splitlines()]
    # Keep a bounded set of observed positions, including both endpoints. Never
    # interpolate or present sampled spectator snapshots as every command.
    count = min(120, len(source))
    indices = sorted({round(i * (len(source) - 1) / max(1, count - 1)) for i in range(count)})
    fields = ['turn', 'current', 'phase', 'hexes', 'ports', 'buildings', 'roads', 'robber', 'players']
    frames = []
    for i in indices:
        frame = source[i]
        if frame['game'].get('own') is not None or frame['game'].get('seat') is not None:
            raise ValueError('Player observations cannot become public exhibits')
        frames.append({'version': frame['version'], **{key: frame['game'][key] for key in fields}})
    replay = {'schema': 1, 'kind': 'replay', 'gameId': result['game_id'],
              'caption': f"Selected game {match_index} from run {run_id}. A narrative example, not aggregate evidence.",
              'sampling': f'{len(frames)} selected spectator snapshots from {len(source)} captured positions; intermediate actions may be omitted.',
              'topology': json.loads((folder / 'topology.json').read_text()), 'frames': frames}
    assets, reports = root / 'content/assets', root / 'reports'
    assets.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    outputs = [assets / f'{slug}-wins.json', assets / f'{slug}-game.json', reports / f'{slug}.mdx']
    if any(p.exists() for p in outputs):
        raise ValueError('Exhibit slug already exists; use a new slug')
    for value in [chart, replay]:
        if len(json.dumps(value).encode()) > 1_000_000:
            raise ValueError('Curated exhibit exceeds 1 MB; select fewer positions')
    write_json(outputs[0], chart)
    write_json(outputs[1], replay)
    outputs[2].write_text(
        f'---\ntitle: "{slug.replace("-", " ").title()}"\nsummary: "Recorded protocol matches and one selected game."\n---\n\n'
        f'# {slug.replace("-", " ").title()}\n\n'
        f"Run `{run_id}` has status **{summary['status']}**. "
        f"{summary['completed']} of {summary['planned']} planned matches completed. "
        'This is descriptive evidence from server-generated, unpaired games.\n\n'
        + summary_table(summary) + '\n\n'
        + f'<ResearchChart asset="{slug}-wins" />\n\n'
        + '## One game, viewed from above\n\n'
        + 'This game was selected to demonstrate the replay. It does not establish which policy is stronger.\n\n'
        + f'<GameReplay asset="{slug}-game" />\n\n'
        + f'[Run record](/research/records/runs/{run_id}) · '
        + f'Public frame source SHA-256: `{digest(match_folder / "frames.jsonl")}`.\n'
    )
    print(f'/research/reports/{slug}')

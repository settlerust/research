"""Guard source-only review scope and small, source-oriented Git contents."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
# Cited source papers are distinct from bulk experiment data. Pin this existing
# reference copy so the exception cannot silently admit a different large file.
REFERENCE_PAPERS = {
    'paper/2012-cowling-powley-whitehouse/CowlingPowleyWhitehouse2012.pdf':
        'd10cd576d33fca9af0b9c4d0ca1f12a72692691c8c77f1a82ecc2e3765f2a0c7',
}


def main():
    config = json.loads((ROOT / '.greptile/config.json').read_text())
    with tempfile.TemporaryDirectory(prefix='settlers-review-') as temporary:
        folder = Path(temporary)
        subprocess.run(['git', 'init', '-q', str(folder)], check=True)
        (folder / '.gitignore').write_text(config['ignorePatterns'] + '\n')
        included = ['harness/arena.py', 'policies/new/src/main.rs', 'policies/new/src/policy.ts', 'charts/View.tsx']
        excluded = [f'results/game-{i}.json' for i in range(150)] + [
            'README.md', 'reports/new.mdx', 'policies/registry.toml', 'runs/code.py',
            'node_modules/lib/index.ts', 'artifacts/analysis.py', '.worktrees/old/policy.py', 'client/types.py', 'client/protocol.ts',
        ]
        result = subprocess.run(['git', '-C', str(folder), 'check-ignore', '--no-index', '--stdin'],
                                input='\n'.join(included + excluded), text=True, capture_output=True)
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr)
        ignored = set(result.stdout.splitlines())
        if any(p in ignored for p in included) or any(p not in ignored for p in excluded):
            raise ValueError('Greptile source allowlist failed Git ignore semantics')
    registry = tomllib.loads((ROOT / 'policies/registry.toml').read_text())
    for name, policy in registry.items():
        if policy['transport'] not in ('remote', 'stdio') or not policy['command'] or not all(isinstance(a, str) for a in policy['command']):
            raise ValueError(f'Invalid policy registration: {name}')
    common = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                            text=True, capture_output=True, check=True)
    canonical = Path(common.stdout.strip()).resolve().parent
    worktrees = subprocess.run(['git', '-C', str(ROOT), 'worktree', 'list', '--porcelain', '-z'],
                               text=True, capture_output=True, check=True)
    for field in worktrees.stdout.split('\0'):
        if field.startswith('worktree '):
            path = Path(field.removeprefix('worktree ')).resolve()
            if path != canonical and not path.is_relative_to(canonical / '.worktrees'):
                raise ValueError(f'Research worktree is outside the canonical .worktrees directory: {path}')
    # Root-only data exclusions must not also hide the compact records/runs and
    # records/artifacts directories that form the durable Git evidence trail.
    for folder in ['records/runs', 'records/artifacts']:
        for record in (ROOT / folder).glob('*.md'):
            check = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '--no-index', str(record)],
                                   capture_output=True)
            if check.returncode == 0:
                raise ValueError(f'Durable record is accidentally ignored: {record.relative_to(ROOT)}')
    result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                            capture_output=True, check=True)
    for name in result.stdout.decode().split('\0'):
        if not name:
            continue
        path = ROOT / name
        if name.split('/')[0] in ('runs', 'artifacts', '.runtime', '.worktrees') or path.suffix in ('.jwt', '.jsonl', '.parquet'):
            raise ValueError(f'Bulk/private artifact in Git scope: {name}')
        if path.is_file() and path.stat().st_size > 1_000_000:
            if name not in REFERENCE_PAPERS or hashlib.sha256(path.read_bytes()).hexdigest() != REFERENCE_PAPERS[name]:
                raise ValueError(f'File exceeds compact repository limit: {name}')
    print('Research repository and Greptile source-only scope verified.')


if __name__ == '__main__':
    main()

"""Drive n-tuple training arms with the server's `train` binary. Each arm writes under
`runs/ntuple/<name>/` (ignored raw data) with a manifest naming the binary digest, the server
and research commits, and the exact argv. Training is a development-tier activity: its
validation tournaments guide the choice of a candidate and carry no evidential weight; the
frozen candidate is then registered and screened like any other policy."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.records import digest, git_state, now, write_json  # noqa: E402

SERVER = Path(os.environ.get('SETTLERS_SERVER_DIR', ROOT.parent / 'server')).resolve()


def run_arm(name, layout, extra, wall, out_root):
    binary = SERVER / 'target/release/train'
    out = (out_root / name).resolve()
    out.mkdir(parents=True, exist_ok=True)
    argv = [str(binary), '--out', str(out), '--layout', layout, '--wall-seconds', str(wall)] + extra
    manifest = {'schema': 1, 'arm': name, 'layout': layout, 'created_at': now(), 'argv': argv,
                'train_sha256': digest(binary), 'server_git': git_state(SERVER), 'research_git': git_state(ROOT),
                'tier': 'training (development); validation tournaments are engine-arena games on fixed seeds'}
    write_json(out / 'manifest.json', manifest)
    started = time.time()
    with (out / 'train.log').open('a') as log:
        code = subprocess.call(argv, stdout=log, stderr=subprocess.STDOUT, cwd=SERVER)
    write_json(out / 'exit.json', {'code': code, 'seconds': time.time() - started, 'finished_at': now()})
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(ROOT / 'runs/ntuple'))
    parser.add_argument('--wall', type=int, required=True, help='Wall seconds per arm')
    parser.add_argument('--arm', action='append', required=True, help='NAME=LAYOUT[;extra args]')
    parser.add_argument('extra', nargs='*', help='Arguments passed to every arm')
    args = parser.parse_args()
    for spec in args.arm:
        name, rest = spec.split('=', 1)
        layout, _, extra = rest.partition(';')
        extra = extra.split() + args.extra
        print(f'== {name}: {layout} {extra}', flush=True)
        code = run_arm(name, layout, extra, args.wall, Path(args.out))
        print(f'== {name} exit {code}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

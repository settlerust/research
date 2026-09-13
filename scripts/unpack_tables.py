"""Decompress the committed frozen tables into artifacts/ntuple/ and verify their digests."""

import hashlib
import lzma
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'tables'
TARGET = ROOT / 'artifacts' / 'ntuple'


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    failed = False
    for line in (SOURCE / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split()
        out = TARGET / name
        if out.exists() and hashlib.sha256(out.read_bytes()).hexdigest() == digest:
            print(f'ok       {out.relative_to(ROOT)}')
            continue
        data = lzma.decompress((SOURCE / f'{name}.xz').read_bytes())
        if hashlib.sha256(data).hexdigest() != digest:
            print(f'MISMATCH {name}: expected {digest}', file=sys.stderr)
            failed = True
            continue
        tmp = out.with_suffix('.tmp')
        tmp.write_bytes(data)
        tmp.replace(out)
        print(f'unpacked {out.relative_to(ROOT)}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())

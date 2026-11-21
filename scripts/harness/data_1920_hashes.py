#!/usr/bin/env python3
"""The sha256 of every file in data/1920/, as the table in data/1920/PROVENANCE.md.

  scripts/harness/data_1920_hashes.py           print the table
  scripts/harness/data_1920_hashes.py --write   rewrite it between the PROVENANCE markers
"""
import hashlib
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parents[2] / 'data/1920'
START, END = '<!-- hashes:start -->', '<!-- hashes:end -->'


def table() -> str:
    rows = ['| File | Bytes | sha256 |', '|---|---|---|']
    for p in sorted(DIR.rglob('*.csv')):
        rows.append(f'| `{p.relative_to(DIR)}` | {p.stat().st_size} | `{hashlib.sha256(p.read_bytes()).hexdigest()}` |')
    return '\n'.join(rows)


def main(argv: list[str]) -> None:
    if '--write' not in argv:
        print(table())
        return
    prov = DIR / 'PROVENANCE.md'
    text = prov.read_text()
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    prov.write_text(f'{head}{START}\n{table()}\n{END}{tail}')
    print(f'wrote {prov}')


if __name__ == '__main__':
    main(sys.argv[1:])

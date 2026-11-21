"""data/1920: the public inputs to the 1920 backbone match their provenance and load on their own."""
import hashlib
import re

import pytest

from simharness import data
from simharness.config import ROOT

DIR = ROOT / 'data/1920'


def test_every_file_matches_its_recorded_hash():
    rows = dict(re.findall(r'\| `([^`]+)` \| \d+ \| `([0-9a-f]{64})` \|', (DIR / 'PROVENANCE.md').read_text()))
    files = {str(p.relative_to(DIR)) for p in DIR.rglob('*.csv')}
    assert set(rows) == files, 'run scripts/harness/data_1920_hashes.py --write'
    for rel, want in rows.items():
        assert hashlib.sha256((DIR / rel).read_bytes()).hexdigest() == want, rel


def test_the_1920_inputs_load_from_the_repo_alone(monkeypatch):
    monkeypatch.setattr(data, 'CACHE', DIR)
    inp, fr = data.inputs(1920)
    assert int(inp.ev.sum()) == 531 and len(inp.ev) == 48
    assert int(inp.returns.R20.sum()) == 16145577 and int(inp.returns.D20.sum()) == 9142289
    # The census table: 21-and-over men and women in the 48 states (DC's adults are not in a state).
    by_sex = inp.cells.groupby('sex').adults20.sum()
    assert by_sex.sum() == pytest.approx(60.6e6, rel=0.02)
    assert fr['closed_1920'] == {'GA', 'MS'} and len(fr['women_pre19']) == 27
    assert data.urban_share()  # the urban share loads too

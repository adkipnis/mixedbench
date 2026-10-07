"""The Tier D draw at its seams: the practice survey's `papers.csv` and `texts/` in,
`deposits.csv` out (#21). A scratch practice root with six papers in two strata, four of
them naming a deposit, so that the regex, the `;`-lists and the seeded per-stratum draw can be
checked on known texts."""

import csv
from pathlib import Path

import pytest
from deposits import Drawer, findDeposits

TEXTS = {
    'a_2020': 'Data are at https://doi.org/10.5061/dryad.abc123. Code at osf.io/x9k2p/.',
    'b_2021': 'Deposited at Zenodo (https://zenodo.org/records/1234567) and zenodo.org/record/1234567.',
    'c_2022': 'See https://doi.org/10.6084/m9.figshare.987654.v2, and again figshare.com/s/abcDEF.',
    'd_2023': 'No deposit named here at all.',
    'e_2024': 'Preregistration: https://osf.io/q7w3e?view_only=1 and the data https://osf.io/q7w3e/files.',
    'f_2025': 'Nothing here either.',
}
STRATA = {
    'a_2020': 'eco',
    'b_2021': 'eco',
    'c_2022': 'eco',
    'd_2023': 'eco',
    'e_2024': 'psy',
    'f_2025': 'psy',
}


@pytest.fixture
def practice(tmp_path: Path) -> Path:
    """A practice survey root: two rows for one paper, as `papers.csv` holds one row per model."""
    with (tmp_path / 'papers.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['paper_id', 'model_index', 'stratum'])
        for paperId, stratum in STRATA.items():
            writer.writerow([paperId, '1', stratum])
        writer.writerow(['a_2020', '2', 'eco'])
    (tmp_path / 'texts').mkdir()
    for paperId, text in TEXTS.items():
        (tmp_path / 'texts' / f'{paperId}.txt').write_text(text)
    return tmp_path


def readRows(file: Path) -> list[dict[str, str]]:
    with file.open(newline='') as f:
        return list(csv.DictReader(f))


def test_links_are_normalised_and_listed_once() -> None:
    """One link per distinct deposit, identifiers without trailing punctuation, view
    parameters or duplicate forms, repositories in text order."""
    assert findDeposits(TEXTS['a_2020']) == [
        ('dryad', '10.5061/dryad.abc123'),
        ('osf', 'osf.io/x9k2p'),
    ]
    assert findDeposits(TEXTS['b_2021']) == [('zenodo', 'zenodo.org/records/1234567')]
    assert findDeposits(TEXTS['c_2022']) == [
        ('figshare', '10.6084/m9.figshare.987654.v2'),
        ('figshare', 'figshare.com/s/abcDEF'),
    ]
    assert findDeposits(TEXTS['e_2024']) == [('osf', 'osf.io/q7w3e')]
    assert findDeposits(TEXTS['d_2023']) == []


def test_draw_is_stratified_seeded_and_reproducible(practice: Path) -> None:
    """Two per stratum where the stratum has them, one row per paper with `;`-lists, the
    frame size recorded, and the same bytes on a second run."""
    out = practice / 'deposits.csv'
    Drawer(practice, out, perStratum=2, seed=0).run()
    first = out.read_bytes()
    rows = readRows(out)
    assert [r['stratum'] for r in rows] == ['eco', 'eco', 'psy']
    assert all(r['paper_id'] != 'd_2023' for r in rows)
    byPaper = {r['paper_id']: r for r in rows}
    assert byPaper['e_2024']['n_frame'] == '1' and byPaper['e_2024']['url'] == 'osf.io/q7w3e'
    assert all(r['seed'] == '0' for r in rows)
    eco = [r for r in rows if r['stratum'] == 'eco']
    assert all(r['n_frame'] == '3' for r in eco)
    if 'a_2020' in byPaper:
        assert byPaper['a_2020']['repository'] == 'dryad;osf'
        assert byPaper['a_2020']['url'] == '10.5061/dryad.abc123;osf.io/x9k2p'
        assert 'Data are at' in byPaper['a_2020']['context']
    Drawer(practice, out, perStratum=2, seed=0).run()
    assert out.read_bytes() == first

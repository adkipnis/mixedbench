"""The help page the pull copies for a reading agent: what documents a data object in its source's
tree, and the codebook a file carries itself. Served from memory from the loader's fixtures: the
CRAN-shaped package, a deposit zip, a GitHub archive and an OSF tarball of Arrow files."""

from pathlib import Path

import pytest
from conftest import sha
from help import HelpPage
from mixedbench.datasets import Loader, Source

FIXTURES = Path(__file__).resolve().parents[2] / 'tests' / 'datasets' / 'fixtures'
TARBALL = (FIXTURES / 'fixture_1.0.tar.gz').read_bytes()
DEPOSIT = (FIXTURES / 'deposit.zip').read_bytes()
DATASETS = (FIXTURES / 'datasets.tar.gz').read_bytes()
EXAMPLE = 'https://github.com/acme/example'
SERVED = {
    'https://cloud.r-project.org/src/contrib/fixture_1.0.tar.gz': TARBALL,
    'https://example.org/deposit.zip': DEPOSIT,
    'https://github.com/acme/example/archive/c0ffee1.tar.gz': (
        FIXTURES / 'example-c0ffee1.tar.gz'
    ).read_bytes(),
    'https://osf.io/abcde/download?version=9': DATASETS,
}


def gitSource(path: str) -> Source:
    return Source(kind='git', name=EXAMPLE, pin='c0ffee1', path=path)


@pytest.fixture
def help(tmp_path: Path) -> HelpPage:
    return HelpPage(Loader(tmp_path, fetch=SERVED.get))


def test_a_cran_objects_page_is_its_rd_page(help):
    page = help.page(Source(kind='cran', name='fixture', pin='1.0'), 'pets')
    assert page.startswith('\\name{pets}')
    assert 'Species, age in years and weight in kg of six pets.' in page


def test_a_deposits_codebook_is_found_walking_up_from_the_file(help):
    """A deposit's codebook at its root documents the file in `data/`; the dotfile beside it
    is no documentation."""
    url = 'https://example.org/deposit.zip'
    deposit = Source(kind='url', name=url, pin=sha(DEPOSIT), checksum=sha(DEPOSIT))
    page = help.page(deposit, 'data/schools.csv')
    assert page.startswith('# codebook.txt\n')
    assert 'school: one of three schools A, B, C' in page


def test_a_readme_beside_the_file_documents_it(help):
    page = help.page(gitSource('data'), 'data/radon.csv')
    assert page.startswith('# data/README.md\ncounty: county name')


def test_the_same_stem_info_file_counts_and_a_stan_dict_names_its_dropped_arrays(help):
    """posteriordb documents `data/data/radon.json.zip` in `data/info/radon.info.json`: a file
    named after the object's stem with a documentation suffix counts in a sibling folder. For a
    Stan data dict the page also says which entries are not in the table, so the reader knows
    the group-level data exist."""
    page = help.page(gitSource('stan/data'), 'stan/data/radon.json.zip')
    assert page.startswith('# stan/info/radon.info.json\n{"name": "radon"')
    assert (
        'not in the table: N (scalar), J (scalar), u (length 2), Z (5 x 1 x 2 array); '
        'X is a 5 x 2 matrix'
    ) in page


def test_a_stata_files_labels_are_its_codebook(help):
    """Stata's manual data ship no text beside them, but a `.dta` carries a data label,
    variable labels and value labels, which is the codebook a reader needs."""
    page = help.page(gitSource('formats'), 'formats/births.dta')
    # nothing documents the file within the pinned path: not the data `.txt` beside it, nor the
    # README above the path
    assert page.startswith('# Stata labels\nBirths\n')
    assert 'hospital: Hospital of birth\nweight: Birth weight (kg)\n' in page
    assert 'hospital values: north, south' in page


def test_an_spss_files_labels_are_rendered_as_the_stata_ones(help):
    page = help.page(gitSource('formats'), 'formats/popular.sav')
    assert page.startswith('# SPSS labels\nPupils\n')
    assert 'class: Class id\nsex: Pupil sex\nses: SES\npopular: Popularity score\n' in page
    assert 'sex values: boy, girl' in page


def test_a_sibling_description_documents_its_data_file(help):
    """Fitzmaurice's `lead.txt` beside `lead.dta` describes it; so does `schools.txt` here."""
    page = help.page(gitSource('formats'), 'formats/schools.dat')
    assert page.startswith('# formats/schools.txt\nEstimates of a coaching effect')


def test_a_banner_of_hash_lines_is_the_files_note(help):
    """Diggle's course files describe their columns in the `#` lines the reader skips."""
    page = help.page(gitSource('formats'), 'formats/cd4.txt')
    assert page == '# banner\n#\n# CD4 counts by subject\n#'


def test_a_workbooks_contents_sheet_is_the_page_of_its_data_sheets(help):
    page = help.page(gitSource('formats'), 'formats/chapters.xlsx!03B')
    assert page == '# sheet Contents\n03A\tschools\n03B\tpupils'


def test_the_page_is_empty_where_the_tree_holds_no_documentation(help):
    """MixedModels.jl's tarball and the PyMC data folder document nothing beside the files;
    the page is then empty rather than an error, the pull adds the first rows, and the
    reading agent is told where the source documents its data."""
    url = 'https://osf.io/abcde/download?version=9'
    datasets = Source(kind='url', name=url, pin=sha(DATASETS), checksum=sha(DATASETS), file='datasets.tar.gz')  # fmt: skip
    assert help.page(datasets, 'kb07.arrow') == ''

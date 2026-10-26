"""The verification script at its file seams: the registry and the candidate list in, the sample,
a batch's handoff and the agreement table out (#61)."""

import csv
from collections import Counter
from pathlib import Path

import pytest
from conftest import writeLinkedSources
from schema import REGISTRY
from verify import SAMPLE_COLUMNS, Links, Verifier, _allocate, renderHelpPage


def writeRegistry(registry: Path, rows: list[dict]) -> None:
    """A registry.csv of the real shape, every column not given left empty."""
    registry.mkdir(parents=True, exist_ok=True)
    with open(registry / 'registry.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY.columns, restval='', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def writeCandidates(path: Path, rows: list[dict]) -> None:
    """A candidate list naming each row by its problem id; the columns the draw ignores stay out."""
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(['id', 'verified'])
        for row in rows:
            writer.writerow([f'{row["source"]}/{row["object"]}/1', row['verified']])


def readRows(path: Path) -> list[dict]:
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def cellRows(tier: str, verified: str, n: int, source: str = '') -> list[dict]:
    """`n` registry rows of one stratum, each its own object, its response naming the row."""
    source = source or f'{tier.lower()}_{verified}'
    return [
        {'source': source, 'tier': tier, 'object': f'o{i}', 'model_index': '1',
         'response': f'{source}_y{i}', 'response_type': 'continuous', 'verified': verified}
        for i in range(n)
    ]  # fmt: skip


def strataFiles(registry: Path, candidates: Path) -> None:
    """Five strata of candidates over 190 rows, hand-checked candidates and registry rows that
    are no candidates. Worked by hand: 100 rows at 100/190 of each stratum's size, 40 + 20 + 30
    + 8.95 + 1.05, the one row left over going to the largest remainder, T/high's: 40, 20, 30, 9
    and 1 rows."""
    strata = (
        cellRows('R', 'high', 76)
        + cellRows('R', 'second-reading', 38)
        + cellRows('E', 'second-reading', 57)
        + cellRows('T', 'high', 17)
        + cellRows('O', 'second-reading', 2)
    )
    hand = cellRows('T', 'hand', 30)
    refused = cellRows('R', 'high', 40, source='refused')
    writeRegistry(registry, strata + hand + refused)
    writeCandidates(candidates, strata + hand)


def test_draw_allocates_the_unchecked_candidates_by_tier_and_verification(tmp_path):
    """The second hand sample is 100 of the candidates not yet hand-checked, proportional over
    tier x `verified`, in four batches of 25 in draw order. A registry row the admission refused
    is no candidate. Each row carries its reading at draw time, so the agreement step needs no
    git."""
    registry = tmp_path / 'registry'
    candidates = tmp_path / 'candidates.csv'
    survey = tmp_path / 'survey'
    survey.mkdir()
    strataFiles(registry, candidates)
    verifier = Verifier(registry, candidates, survey)

    verifier.draw()

    sample = readRows(survey / 'sample.csv')
    strata = Counter(row['stratum'] for row in sample)
    assert strata == {
        'R/high': 40,
        'R/second-reading': 20,
        'E/second-reading': 30,
        'T/high': 9,
        'O/second-reading': 1,
    }
    assert [row['batch'] for row in sample] == ['1'] * 25 + ['2'] * 25 + ['3'] * 25 + ['4'] * 25
    assert all(row['response'] == f'{row["source"]}_y{row["object"][1:]}' for row in sample)


def test_draw_is_a_function_of_the_registry_the_candidates_and_the_seed(tmp_path):
    """Two draws over the same files write the same sample file, so the sample can be redrawn
    from the committed files to check it."""
    registry = tmp_path / 'registry'
    candidates = tmp_path / 'candidates.csv'
    strataFiles(registry, candidates)
    texts = []
    for name in ('first', 'second'):
        survey = tmp_path / name
        survey.mkdir()
        Verifier(registry, candidates, survey).draw()
        texts.append((survey / 'sample.csv').read_text())

    assert texts[0] == texts[1]


@pytest.mark.parametrize(
    'sizes, size, quotas',
    [
        pytest.param(
            {'prescreened': 13, 'read/unflagged': 22, 'read/flagged': 18, 'read/integer': 27},
            50,
            {'prescreened': 8, 'read/unflagged': 14, 'read/flagged': 11, 'read/integer': 17},
            id='50/80 of each is 8.125, 13.75, 11.25 and 16.875, two left to the largest remainders',
        ),
        pytest.param(
            {'named': 20, 'none': 13},
            25,
            {'named': 15, 'none': 10},
            id='25/33 of each is 15.15 and 9.85, one left to the larger remainder',
        ),
    ],
)
def test_allocate_gives_each_stratum_its_share_by_largest_remainder(sizes, size, quotas):
    """The flat pass's hand checks draw through the same allocation as the registry's."""
    assert _allocate(sizes, tuple(sizes), size) == quotas


def writeHelp(registry: Path, source: str, object: str, text: str) -> None:
    """A git object's name is its path in the tree, so its help page sits in subdirectories."""
    page = registry / 'help' / source / f'{object}.txt'
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(text)


def handoffFiles(registry: Path, candidates: Path) -> None:
    """One candidate per source kind: a CRAN package, a git tree and a url archive, each with its
    `sources.yaml` entry, its manifest file and its cached help page."""
    rows = [
        {'source': 'pens', 'tier': 'R', 'object': 'herds', 'model_index': '1',
         'response': 'weight', 'response_type': 'continuous', 'grouping_factors': 'herd',
         'covariates': 'feed', 'random_slopes': 'feed||herd',
         'formula': 'weight ~ feed + (1 + feed || herd)', 'published_model': 'yes',
         'confidence': 'high', 'verified': 'high', 'notes': 'Help examples fm1.'},
        {'source': 'ros', 'tier': 'T', 'object': 'Beauty/data/beauty.csv', 'model_index': '1',
         'response': 'eval', 'response_type': 'continuous', 'confidence': 'medium',
         'verified': 'second-reading'},
        {'source': 'rabe_hesketh', 'tier': 'T', 'object': 'pig.dta', 'model_index': '1',
         'response': 'weight', 'response_type': 'continuous', 'confidence': 'low',
         'verified': 'second-reading'},
    ]  # fmt: skip
    writeRegistry(registry, rows)
    writeCandidates(candidates, rows)
    (registry / 'sources.yaml').write_text(
        'seed: 0\n'
        'tiers:\n'
        '  R:\n'
        "    pens: {kind: cran, pin: '1.0'}\n"
        '  T:\n'
        '    ros: {kind: git, name: https://github.com/avehtari/ROS-Examples, pin: abc123}\n'
        f'    rabe_hesketh: {{kind: url, name: https://www.stata-press.com/data/mlmus4/mlmus4.zip, pin: {"0" * 64}}}\n'
    )
    (registry / 'manifest.csv').write_text(
        'source,object,file,sha256,size\n'
        'pens,herds,data/herds.rda,0,1\n'
        'ros,Beauty/data/beauty.csv,Beauty/data/beauty.csv,0,1\n'
        'rabe_hesketh,pig.dta,pig.dta,0,1\n'
    )
    writeHelp(registry, 'pens', 'herds', '\\name{herds}\n\\title{Weights of pigs by herd}\n')
    writeHelp(registry, 'ros', 'Beauty/data/beauty.csv', '# first rows (of 463)\neval: float64\n')
    writeHelp(registry, 'rabe_hesketh', 'pig.dta', '# Stata labels\nweight: Weight in kg\n')


def test_handoff_names_page_and_download_urls_and_no_local_path(tmp_path):
    """Alex checks a batch in the browser against the source itself, so every row carries the
    source's page and the file's download at the pin, its reading and its help page, and no
    path of the local checkout or cache appears."""
    registry = tmp_path / 'registry'
    candidates = tmp_path / 'candidates.csv'
    survey = tmp_path / 'survey'
    survey.mkdir()
    handoffFiles(registry, candidates)
    verifier = Verifier(registry, candidates, survey)
    verifier.draw()

    text = verifier.handoff(1)

    urls = [
        'https://cran.r-project.org/package=pens',
        'https://github.com/cran/pens/blob/1.0/data/herds.rda',
        'https://github.com/avehtari/ROS-Examples/tree/abc123/Beauty/data',
        'https://github.com/avehtari/ROS-Examples/blob/abc123/Beauty/data/beauty.csv',
        'https://www.stata-press.com/data/mlmus4.html',
        'https://www.stata-press.com/data/mlmus4/mlmus4.zip',
    ]
    assert all(url in text for url in urls)
    assert 'weight ~ feed + (1 + feed || herd)' in text
    assert 'random_slopes: feed||herd' in text
    assert 'Help examples fm1.' in text
    assert '\\title{Weights of pigs by herd}' in text
    assert 'weight: Weight in kg' in text
    assert str(tmp_path) not in text
    assert 'registry/' not in text
    assert 'cache' not in text


@pytest.fixture
def links(tmp_path: Path) -> Links:
    writeLinkedSources(tmp_path, tmp_path)
    return Links(tmp_path, tmp_path)


@pytest.mark.parametrize(
    'label, object, file, page, download',
    [
        pytest.param(
            'pens', 'herds', 'data/herds.rda',
            'https://cran.r-project.org/package=pens',
            'https://github.com/cran/pens/blob/1.0/data/herds.rda',
            id='a CRAN file on GitHub\'s mirror, tagged by version',
        ),
        pytest.param(
            'ros', 'Beauty/data/beauty.csv', 'Beauty/data/beauty.csv',
            'https://github.com/avehtari/ROS-Examples/tree/abc123/Beauty/data',
            'https://github.com/avehtari/ROS-Examples/blob/abc123/Beauty/data/beauty.csv',
            id='a git file at its commit, its folder the page',
        ),
        pytest.param(
            'rabe_hesketh', 'pig.dta', 'pig.dta',
            'https://www.stata-press.com/data/mlmus4.html',
            'https://www.stata-press.com/data/mlmus4/mlmus4.zip',
            id='a url archive, its page by label prefix',
        ),
        pytest.param(
            'arriero_2017_dryad', 'voles.xlsx', 'voles.xlsx',
            'https://doi.org/10.5061/dryad.110pk',
            'https://datadryad.org/api/v2/files/51526/download',
            id='a deposit linked by a DOI, its page at doi.org',
        ),
        pytest.param(
            'leder_2020_osf', 'data.csv', 'data.csv',
            'https://osf.io/txb9c',
            'https://osf.io/download/znb6c/',
            id='a deposit without a DOI, its page the link',
        ),
    ],
)  # fmt: skip
def test_links_name_a_page_and_a_download_per_kind_of_source(
    links, label, object, file, page, download
):
    """A batch is checked in the browser against the source itself, at its pin."""
    assert links.resolveUrls(label, object, file) == (page, download)


def test_a_help_page_longer_than_twenty_thousand_characters_is_cut(tmp_path):
    """A help page can hold a whole table, one in the flat frame 20 MB of it, which would drown
    the prompt, so it is cut and says where."""
    writeHelp(tmp_path, 'pens', 'herds', 'x' * 20_000 + 'y')

    text = renderHelpPage(tmp_path, 'pens', 'herds')

    assert 'x' * 20_000 + '\n[cut at 20,000 characters]' in text
    assert 'xy' not in text


def reading(source: str, object: str, **fields: str) -> dict:
    """A row key with a plain reading; `fields` overrides the ones a test edits."""
    base = {'response': 'y', 'response_type': 'continuous', 'grouping_factors': 'g',
            'covariates': 'x', 'random_slopes': 'x|g', 'formula': 'y ~ x + (1 + x | g)',
            'published_model': 'yes'}  # fmt: skip
    return {'source': source, 'object': object, 'model_index': '1'} | base | fields


def writeSample(survey: Path, rows: list[dict]) -> None:
    with open(survey / 'sample.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SAMPLE_COLUMNS, restval='', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def agreement(registry: Path, survey: Path) -> dict[str, dict[str, float]]:
    """The agreement table as pool -> column -> number."""
    Verifier(registry, survey / 'candidates.csv', survey).agree()
    rows = readRows(survey / 'agreement.csv')
    return {row.pop('pool'): {k: float(v) for k, v in row.items()} for row in rows}


def test_agree_gives_the_share_of_rows_whose_reading_stood_per_stratum_tier_verification_and_overall(
    tmp_path,
):
    """The candidates' reading quality is the share of sampled rows whose draw-time reading the
    hand check left unchanged, per stratum and field, pooled per tier, per `verified` and
    overall. Worked by hand: R/high's `b` changed its response, R/second-reading's `c` its
    random slopes, T/second-reading's `e` its grouping factors."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    drawn = [
        reading('r', 'a') | {'stratum': 'R/high'},
        reading('r', 'b') | {'stratum': 'R/high'},
        reading('r', 'c') | {'stratum': 'R/second-reading'},
        reading('t', 'd') | {'stratum': 'T/second-reading'},
        reading('t', 'e') | {'stratum': 'T/second-reading'},
    ]
    writeSample(survey, drawn)
    writeRegistry(registry, [
        reading('r', 'a'),
        reading('r', 'b', response='log_y'),
        reading('r', 'c', random_slopes='x||g'),
        reading('t', 'd'),
        reading('t', 'e', grouping_factors='h'),
    ])  # fmt: skip

    table = agreement(registry, survey)

    assert list(table) == [
        'R/high', 'R/second-reading', 'T/second-reading', 'R', 'T', 'high', 'second-reading', 'all',
    ]  # fmt: skip
    assert [table[p]['rows'] for p in table] == [2, 1, 2, 3, 2, 2, 3, 5]
    assert table['R/high']['response'] == 0.5
    assert table['R/second-reading']['random_slopes'] == 0
    assert table['T/second-reading']['grouping_factors'] == 0.5
    assert table['R']['response'] == 0.667
    assert table['high']['response'] == 0.5
    assert table['second-reading']['random_slopes'] == 0.667
    assert table['second-reading']['grouping_factors'] == 0.667
    assert table['all']['response'] == 0.8
    assert table['all']['grouping_factors'] == 0.8
    assert table['all']['random_slopes'] == 0.8
    untouched = ('response_type', 'trials', 'covariates', 'interactions', 'formula', 'published_model')  # fmt: skip
    assert all(table[p][f] == 1 for p in table for f in untouched)


def test_agree_reads_lists_as_sets_terms_as_unordered_and_formulas_without_whitespace(tmp_path):
    """A reading the hand check rewrote in another order or spacing still stood: `;`-lists are
    sets, the random slopes too, `a:b` names the same term as `b:a`, and a formula's spaces carry
    no meaning. `b`'s added covariate is a real change."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    drawn = {'grouping_factors': 'site;plot:site', 'covariates': 'x;z', 'interactions': 'x:z',
             'random_slopes': 'x|site;z||site', 'formula': 'y ~ x * z + (1 | site/plot)'}  # fmt: skip
    stratum = {'stratum': 'R/high'}
    writeSample(survey, [reading('r', 'a') | drawn | stratum, reading('r', 'b') | drawn | stratum])
    rewritten = {'grouping_factors': 'site:plot;site', 'covariates': 'z;x', 'interactions': 'z:x',
                 'random_slopes': 'z||site;x|site', 'formula': 'y~x*z+(1|site/plot)'}  # fmt: skip
    writeRegistry(registry, [
        reading('r', 'a') | drawn | rewritten,
        reading('r', 'b') | drawn | rewritten | {'covariates': 'x;z;w'},
    ])  # fmt: skip

    shares = agreement(registry, survey)['R/high']

    assert shares['grouping_factors'] == 1
    assert shares['interactions'] == 1
    assert shares['random_slopes'] == 1
    assert shares['formula'] == 1
    assert shares['covariates'] == 0.5


def test_agree_counts_a_sampled_row_that_left_the_registry_as_disagreeing_everywhere(tmp_path):
    """A row the hand check took out of the registry was a reading that should not exist, so it
    counts against every field rather than dropping out of the rows compared."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    stratum = {'stratum': 'T/second-reading'}
    writeSample(survey, [reading('t', 'kept') | stratum, reading('t', 'gone') | stratum])
    writeRegistry(registry, [reading('t', 'kept')])

    shares = agreement(registry, survey)['T/second-reading']

    assert shares['rows'] == 2
    assert all(shares[f] == 0.5 for f in shares if f != 'rows')

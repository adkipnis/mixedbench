"""The verification script at its file seams: registry and help pages in, the scan's hits file
out (#10)."""

import csv
from collections import Counter
from pathlib import Path

from schema import REGISTRY
from verify import Verifier


def writeRegistry(registry: Path, rows: list[dict]) -> None:
    """A registry.csv of the real shape, every column not given left empty."""
    registry.mkdir(parents=True, exist_ok=True)
    with open(registry / 'registry.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=REGISTRY.columns, restval='', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def writeHelp(registry: Path, source: str, object: str, text: str) -> None:
    """A git object's name is its path in the tree, so its help page sits in subfolders."""
    page = registry / 'help' / source / f'{object}.txt'
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(text)


def readRows(path: Path) -> list[dict]:
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def hitKey(hit: dict) -> tuple[str, ...]:
    return (hit['source'], hit['object'], hit['model_index'], hit['field'], hit['keyword'])


def test_scan_lists_each_planted_keyword_once_with_its_snippet(tmp_path):
    """A keyword planted in `notes`, in `formula` and in a help page shows up once each, with the
    words around it, so the hand look reads snippets instead of rows. The two spellings of
    negative binomial in one note are two occurrences; `glmer.nb` matching both `glmer.nb` and
    `nb` is one, and "prior to" is not a prior."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    rows = [
        {'source': 'pens', 'object': 'herds', 'model_index': '1', 'formula': 'y ~ x + (1 | herd)',
         'notes': 'Fitted as a negative binomial in the book; the help page says neg. bin. too.'},
        {'source': 'pens', 'object': 'pigs', 'model_index': '1', 'formula': 'glmer.nb(y ~ x + (1 | pen))', 'notes': ''},
        {'source': 'pens', 'object': 'goats', 'model_index': '1', 'formula': 'y ~ x + (1 | farm)', 'notes': ''},
    ]  # fmt: skip
    writeRegistry(registry, rows)
    writeHelp(registry, 'pens', 'herds', 'A plain description of herds.')
    writeHelp(registry, 'pens', 'pigs', 'Weighed prior to slaughter.')
    writeHelp(registry, 'pens', 'goats', 'The authors put a Normal(0, 1) prior\non every slope.')
    verifier = Verifier(registry, survey)

    verifier.scan()

    hits = readRows(survey / 'scan_hits.csv')
    assert sorted(hitKey(h) for h in hits) == [
        ('pens', 'goats', '1', 'help', 'prior'),
        ('pens', 'herds', '1', 'notes', 'negative binomial'),
        ('pens', 'herds', '1', 'notes', 'negative binomial'),
        ('pens', 'pigs', '1', 'formula', 'negative binomial'),
    ]
    snippets = {h['snippet'] for h in hits}
    assert 'The authors put a Normal(0, 1) prior on every slope.' in snippets  # newline collapsed
    assert 'glmer.nb(y ~ x + (1 | pen))' in snippets


def test_scan_reads_a_shared_deposit_page_once(tmp_path):
    """A Tier D help page only points at its paper's deposit page, which holds the models and the
    code; the scan follows the pointer and lists the deposit page's hits once under the page,
    not once per object of the deposit."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    rows = [
        {'source': 'smith_2020_osf', 'object': 'a.csv', 'model_index': '1', 'formula': 'y ~ x + (1 | id)', 'notes': ''},
        {'source': 'smith_2020_osf_2', 'object': 'b.csv', 'model_index': '1', 'formula': 'y ~ x + (1 | id)', 'notes': ''},
    ]  # fmt: skip
    writeRegistry(registry, rows)
    pointer = '# deposit page: registry/help/deposits/smith_2020_osf_abcde.txt\n\n# first rows\n'
    writeHelp(registry, 'smith_2020_osf', 'a.csv', pointer)
    writeHelp(registry, 'smith_2020_osf_2', 'b.csv', pointer)
    writeHelp(
        registry, 'deposits', 'smith_2020_osf_abcde', 'model_index: 1\nfamily: Gamma\nlink: log\n'
    )
    verifier = Verifier(registry, survey)

    verifier.scan()

    hits = readRows(survey / 'scan_hits.csv')
    assert [hitKey(h) for h in hits] == [('smith_2020_osf_abcde', '', '', 'deposit', 'gamma')]


def cellRows(tier: str, confidence: str, n: int) -> list[dict]:
    """`n` registry rows of one stratum, each its own object, its response naming the row."""
    source = f'{tier.lower()}_{confidence}'
    return [
        {'source': source, 'tier': tier, 'object': f'o{i}', 'model_index': '1',
         'response': f'{source}_y{i}', 'confidence': confidence}
        for i in range(n)
    ]  # fmt: skip


def strataRegistry(registry: Path) -> None:
    """Five non-empty cells over 190 rows and a Tier D cell. Worked by hand: 100 rows at
    100/190 of each cell's size, 40 + 20 + 30 + 8.95 + 1.05, the one row left over going to
    the largest remainder, T/low's: 40, 20, 30, 9 and 1 rows."""
    rows = (
        cellRows('D', 'high', 30)
        + cellRows('R', 'high', 76)
        + cellRows('R', 'low', 38)
        + cellRows('E', 'medium', 57)
        + cellRows('T', 'low', 17)
        + cellRows('O', 'high', 2)
    )
    writeRegistry(registry, rows)


def test_draw_allocates_strata_by_size_without_tier_d(tmp_path):
    """The hand sample is 100 rows over tier x confidence, proportional with every non-empty
    cell kept, Tier D left out because Alex read all of it, in four batches of 25 in draw
    order, each row carrying its reading at draw time so the agreement step needs no git."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    strataRegistry(registry)
    verifier = Verifier(registry, survey)

    verifier.draw()

    sample = readRows(survey / 'sample.csv')
    strata = Counter(row['stratum'] for row in sample)
    assert strata == {'R/high': 40, 'R/low': 20, 'E/medium': 30, 'T/low': 9, 'O/high': 1}
    assert [row['batch'] for row in sample] == ['1'] * 25 + ['2'] * 25 + ['3'] * 25 + ['4'] * 25
    assert {row['seed'] for row in sample} == {'0'}
    assert all(row['response'] == f'{row["source"]}_y{row["object"][1:]}' for row in sample)


def test_draw_keeps_a_stratum_too_thin_for_its_share(tmp_path):
    """A stratum whose proportional share rounds to no row still gets one, so every stratum has
    a row in the agreement table; the sample then runs one row over 100."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    writeRegistry(registry, cellRows('R', 'high', 300) + cellRows('O', 'low', 1))
    verifier = Verifier(registry, survey)

    verifier.draw()

    strata = Counter(row['stratum'] for row in readRows(survey / 'sample.csv'))
    assert strata == {'R/high': 100, 'O/low': 1}


def rowKey(row: dict) -> tuple[str, str, str]:
    return (row['source'], row['object'], row['model_index'])


def test_draw_is_a_function_of_the_registry_and_the_seed(tmp_path):
    """Two draws over the same registry write the same sample file, so the sample can be redrawn
    from the committed registry to check it."""
    registry = tmp_path / 'registry'
    strataRegistry(registry)
    texts = []
    for name in ('first', 'second'):
        survey = tmp_path / name
        survey.mkdir()
        Verifier(registry, survey).draw()
        texts.append((survey / 'sample.csv').read_text())

    assert texts[0] == texts[1]


def test_a_further_draw_appends_one_batch_with_the_next_seed(tmp_path):
    """Where disagreement is high, a further batch of 25 is drawn with the next seed from the rows
    not yet sampled and appended under the next batch number, the first 100 rows untouched. It
    has no floor: O/high's one row left would otherwise push the batch to 26."""
    registry = tmp_path / 'registry'
    survey = tmp_path / 'survey'
    survey.mkdir()
    strataRegistry(registry)
    verifier = Verifier(registry, survey)
    verifier.draw()
    first = readRows(survey / 'sample.csv')

    verifier.draw()

    sample = readRows(survey / 'sample.csv')
    further = sample[100:]
    assert sample[:100] == first
    assert len(further) == 25
    assert {(row['seed'], row['batch']) for row in further} == {('1', '5')}
    assert len({rowKey(row) for row in sample}) == 125
    assert 'D' not in {row['stratum'][0] for row in further}


def handoffRegistry(registry: Path) -> None:
    """One row per source kind: a CRAN package, a git tree and a url archive, each with its
    `sources.yaml` entry, its manifest file and its cached help page."""
    rows = [
        {'source': 'pens', 'tier': 'R', 'object': 'herds', 'model_index': '1',
         'response': 'weight', 'response_type': 'continuous', 'grouping_factors': 'herd',
         'formula': 'weight ~ feed + (1 | herd)', 'published_model': 'yes',
         'confidence': 'high', 'notes': 'Help examples fm1.'},
        {'source': 'ros', 'tier': 'T', 'object': 'Beauty/data/beauty.csv', 'model_index': '1',
         'response': 'eval', 'confidence': 'medium'},
        {'source': 'rabe_hesketh', 'tier': 'T', 'object': 'pig.dta', 'model_index': '1',
         'response': 'weight', 'confidence': 'low'},
    ]  # fmt: skip
    writeRegistry(registry, rows)
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
    survey = tmp_path / 'survey'
    survey.mkdir()
    handoffRegistry(registry)
    verifier = Verifier(registry, survey)
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
    assert 'weight ~ feed + (1 | herd)' in text
    assert 'Help examples fm1.' in text
    assert '\\title{Weights of pigs by herd}' in text
    assert 'weight: Weight in kg' in text
    assert str(tmp_path) not in text
    assert 'registry/' not in text
    assert 'cache' not in text

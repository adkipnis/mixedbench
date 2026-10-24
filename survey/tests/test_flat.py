"""The flat module at its seams: the merged files in, the frame and `flat_screen.csv` out, and
the screen rule on hand-made tables (#116)."""

import io
import zipfile
from pathlib import Path

import dimensions
import pandas as pd
import pytest
import yaml
from columns import COLUMN_STATISTICS
from conftest import asOrdered, measuredColumns, parsed, readRows, scratchMerger, sha
from flat import FlatPass
from measure import Measurer
from mixedbench.datasets import Loader
from mixedbench.registry.row import writeCsv
from schema import CANDIDATE_COLUMNS, EXCLUDED, FLAT_VERDICTS
from sources import readFrame

# source, object, the pre-screen's verdict, the exclusion's reason and detail ('' for none)
SURVEY = [
    ('pens', 'grouped', 'pass', '', ''),
    ('pens', 'read', 'pass', 'no grouping structure', 'one row per school'),
    ('pens', 'unique', 'no repeated column', 'no grouping structure', 'no repeated column'),
    ('pens', 'single', 'one column', 'no grouping structure', 'one column'),
    ('pens', 'tiny', 'under 3 rows', 'no grouping structure', 'under 3 rows'),
    ('pens', 'broken', 'no frame', 'no grouping structure', 'help page only'),
    ('pens', 'copy', 'pass', 'derived or duplicated table', 'same table as read'),
]


@pytest.fixture
def flat(tmp_path: Path) -> FlatPass:
    """A flat pass over the scratch registry and survey of the merge's tests."""
    merger = scratchMerger(tmp_path / 'registry', tmp_path / 'survey')
    return FlatPass(merger.registry, merger.survey, loader=merger.loader)


def writeSurvey(flat: FlatPass, survey: list[tuple[str, str, str, str, str]]) -> None:
    """The objects as rows of `candidates.csv` and, where excluded, `excluded.csv`."""
    tiers = readFrame(flat.registry).tiers
    candidates, excluded = [], []
    for source, object, screen, reason, detail in survey:
        tier = tiers[source]
        candidates.append({'tier': tier, 'source': source, 'object': object, 'screen': screen, 'capped': 'no'})  # fmt: skip
        if reason != '':
            excluded.append({'source': source, 'tier': tier, 'object': object, 'reason': reason, 'detail': detail})  # fmt: skip
    candidates = pd.DataFrame(candidates).reindex(columns=CANDIDATE_COLUMNS, fill_value='')
    writeCsv(candidates, flat.survey / 'candidates.csv')
    writeCsv(pd.DataFrame(excluded, columns=EXCLUDED.columns), flat.registry / 'excluded.csv')


def test_the_frame_holds_the_read_and_the_prescreened_tables_filed_no_grouping_structure(flat):
    """The frame is derived from the merged files, never a hand list, so a re-filed table leaves
    it at the next run; the other screens' tables cannot be measured."""
    writeSurvey(flat, SURVEY)
    frame = flat.deriveFrame()
    assert list(zip(frame['object'], frame['stratum'])) == [
        ('read', 'read'),
        ('unique', 'prescreened'),
    ]


def _screening(words='', id_columns='', integer_columns='', flagged='no') -> dict[str, str]:
    return {
        'words': words,
        'id_columns': id_columns,
        'integer_columns': integer_columns,
        'flagged': flagged,
    }


ELEVEN_LEVELS = [float(i) for i in range(11)] + [0.0]  # R stores integer codes as doubles


@pytest.mark.parametrize(
    'detail, columns, screening',
    [
        pytest.param(
            'Wide format: four visits as columns, repeated in time',
            {'y1': [1.5, 2.5, 3.5], 'y2': [2.5, 3.5, 4.5]},
            _screening(words='repeated;visits;wide', flagged='yes'),
            id='a stem in the filing line flags, whole or as a stem',
        ),
        pytest.param(
            'one row per pupil',
            {'school': ['a', 'a', 'b'], 'Patient_ID': [1, 1, 2], 'score': [1.5, 2.5, 3.5]},
            _screening(id_columns='school;Patient_ID', flagged='yes'),
            id='a repeated column with an id-like stem or suffix flags, in any case',
        ),
        pytest.param(
            'one row per subject',
            {'id': [1, 2, 3], 'score': [1.5, 2.5, 3.5]},
            _screening(),
            id='an id column of all-distinct values could not index groups',
        ),
        pytest.param(
            'a nationwide cross-section, no model with a random effect',
            {'dose': [1, 1, 2], 'response': [0.5, 0.7, 0.9]},
            _screening(),
            id='a word that only ends in a stem flags nothing',
        ),
        pytest.param(
            'counts of a single survey',
            {'count': ELEVEN_LEVELS, 'rate': [i + 0.5 for i in ELEVEN_LEVELS]},
            _screening(integer_columns='count'),
            id='a repeated integer column of eleven levels is recorded but flags nothing',
        ),
    ],
)
def test_the_screen_flags_a_read_table_on_its_filing_line_or_a_repeated_id_like_column(
    detail, columns, screening
):
    """The two rules of the screen, read off its row: a filing line that says the data is wide
    or repeated, or a column that could index groups and is named like an id. Many integer
    levels caught field coordinates and counts, so they only mark a hand-sample stratum."""
    assert FlatPass.screenTable(detail, pd.DataFrame(columns)) == screening


def test_the_screen_step_writes_every_frame_table_with_its_stratum_and_its_flags(flat):
    """The worklist of the second reading, one row per frame table in frame order: a read
    table screened on its loaded table, a prescreened one left unscreened, since its filing line
    is the pre-screen's verdict and it holds no repeated column by construction."""
    writeSurvey(flat, [
        ('herds', 'herds.csv', 'pass', 'no grouping structure', 'one row per cow'),
        ('cattle', 'cattle.csv', 'pass', 'no grouping structure', 'Wide: calvings repeated as columns'),
        ('pens', 'herds', 'no repeated column', 'no grouping structure', 'no repeated column'),
    ])  # fmt: skip
    flat.screen()
    rows = readRows(flat.survey / 'flat_screen.csv')
    assert list(rows[0]) == [
        'source', 'object', 'tier', 'stratum', 'words', 'id_columns', 'integer_columns', 'flagged',
    ]  # fmt: skip
    assert [list(row.values())[1:] for row in rows] == [
        ['herds.csv', 'D', 'read', '', 'region;herd;trials', '', 'yes'],  # trial is a stem
        ['cattle.csv', 'R', 'read', 'repeated;wide', 'farm', '', 'yes'],
        ['herds', 'R', 'prescreened', '', '', '', 'no'],
    ]


# the herds table without model 2's response, trials, factor and ignored id
MODEL_2_COLUMNS = ['region', 'breed', 'feed', 'parity', 'weight', 'sick']


def test_a_flat_columns_statistics_equal_the_registrys_for_the_same_column(herds, rows):
    """One home per statistic: cut to model 2's covariate columns, the herds table is a flat
    table whose every column statistic equals the number columns.csv holds under model 2,
    whose response is observed on every row."""
    _, measured = FlatPass.measureTable(herds[MODEL_2_COLUMNS])
    statistics = ['type', 'K', 'missing_share', *COLUMN_STATISTICS]
    flat = pd.DataFrame(measured).set_index('column').reindex(columns=statistics)
    registry = measuredColumns(herds, rows[1])[statistics]
    pd.testing.assert_frame_equal(flat, registry, check_dtype=False)


def test_a_flat_tables_design_statistics_equal_the_registrys_over_the_same_columns(herds, rows):
    """d_all and condition_all count and code every measured column as dimensions.csv does,
    the design centered as the contract centers it, so the cut table gives model 2's."""
    measured, _ = FlatPass.measureTable(herds[MODEL_2_COLUMNS])
    dimension = dimensions.measure(Measurer(herds, parsed(rows[1])))[0]
    assert measured['d_all'] == dimension['d_all']
    assert measured['condition_all'] == dimension['condition_all']


def test_an_all_distinct_label_column_is_measured_but_left_out_of_the_design(herds):
    """A column of names or ids would make the design as wide as the table is long, so a
    categorical whose present values are all distinct is measured and counted, but left out of
    d_all and condition_all; its one missing name drops no row from the design."""
    cut = herds[MODEL_2_COLUMNS]
    names = [f'cow {i}' for i in range(len(cut))]
    names[0] = None
    measured, columns = FlatPass.measureTable(cut.assign(name=names))
    alone, _ = FlatPass.measureTable(cut)
    assert [c['column'] for c in columns] == [*MODEL_2_COLUMNS, 'name']
    assert (measured['n_id_columns'], alone['n_id_columns']) == (1, 0)
    assert measured['d_all'] == alone['d_all']
    assert measured['condition_all'] == alone['condition_all']


def test_a_flat_tables_sizes_count_every_row_and_every_column_by_its_type(herds):
    """A flat table has no response, so n_obs counts every row, a row missing a weight too.
    The labels count among the categoricals and among the columns."""
    table = herds[MODEL_2_COLUMNS].assign(
        parity=asOrdered(herds['parity'], [1, 2, 3, 4]),
        name=[f'cow {i}' for i in range(len(herds))],
    )
    table.loc[0, 'weight'] = float('nan')
    measured, _ = FlatPass.measureTable(table)
    sizes = ['n_obs', 'n_columns', 'n_continuous', 'n_binary', 'n_categorical', 'n_ordered']
    assert [measured[s] for s in sizes] == [14, 7, 1, 1, 4, 1]


def test_a_flat_table_without_a_complete_row_has_no_condition_index(herds):
    """A column missing on every row leaves no row complete in every designed column."""
    empty = pd.Categorical([None] * len(herds), categories=['low', 'high'], ordered=True)
    measured, _ = FlatPass.measureTable(herds[MODEL_2_COLUMNS].assign(empty=empty))
    assert 'condition_all' not in measured


# ---------------------------------------------------------------------------------
# the pass: the screen recomputed, the verdicts read, the sample measured into two files
# ---------------------------------------------------------------------------------
PLOTS_URL = 'https://example.org/plots.zip'
PLAIN = 'dose,response\n1.5,0.5\n2.5,0.7\n3.5,0.9\n'  # nothing repeats, so nothing flags
HERDED = 'herd,dose,response\na,1.5,0.5\na,2.5,0.7\nb,3.5,0.9\n'  # a repeated id-like column
DISTINCT = 'x,y\n1,4\n2,5\n3,6\n'  # every column all-unique, as the pre-screen stops at
PLOTS = {
    'plain.csv': PLAIN, 'stored.csv': PLAIN, 'decided.csv': PLAIN, 'herded.csv': HERDED,
    'hidden.csv': HERDED, 'distinct.csv': DISTINCT,
}  # fmt: skip
NO_GROUPING = 'no grouping structure'


def zippedFiles(folder: str, files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for filename, text in files.items():
            archive.writestr(f'{folder}/{filename}', text)
    return buffer.getvalue()


@pytest.fixture
def plots(tmp_path: Path) -> FlatPass:
    """A flat pass over the scratch registry and survey with one more url source, `plots`
    (Tier O), served from memory: every table the scratch sources pin has a repeated column
    named like an id, so none would pass the screen unflagged."""
    merger = scratchMerger(tmp_path / 'registry', tmp_path / 'survey')
    archive = zippedFiles('plots', PLOTS)
    pinned = {'kind': 'url', 'name': PLOTS_URL, 'pin': sha(archive), 'license': 'CC0 1.0 Universal'}  # fmt: skip
    sources = yaml.safe_load((merger.registry / 'sources.yaml').read_text())
    sources['tiers']['O'] = {'plots': pinned}
    (merger.registry / 'sources.yaml').write_text(yaml.safe_dump(sources, sort_keys=False))
    loader = Loader(merger.registry / 'cache', fetch={PLOTS_URL: archive}.get)
    return FlatPass(merger.registry, merger.survey, loader=loader)


def test_the_pass_refuses_naming_every_flagged_table_without_a_verdict(plots):
    """A half-read sample never ships: the pass recomputes the screen, so a table it flags
    waits for its second reading."""
    writeSurvey(plots, [
        ('plots', 'plain.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'herded.csv', 'pass', NO_GROUPING, 'one row per cow'),
        ('plots', 'stored.csv', 'pass', NO_GROUPING, 'wide: visits as columns'),
    ])  # fmt: skip
    with pytest.raises(ValueError, match='2 flagged .*\nplots herded.csv\nplots stored.csv$'):
        plots.measure()


def writeVerdicts(flat: FlatPass, verdicts: list[tuple[str, str, str, str]]) -> None:
    """The verdicts as the merge leaves them in `flat_verdicts.csv`, the tier filled."""
    tiers = readFrame(flat.registry).tiers
    rows = []
    for source, object, verdict, evidence in verdicts:
        rows.append({'source': source, 'tier': tiers[source], 'object': object, 'verdict': verdict, 'evidence': evidence})  # fmt: skip
    writeCsv(pd.DataFrame(rows, columns=FLAT_VERDICTS.columns), flat.survey / 'flat_verdicts.csv')


def test_a_verdict_decides_its_table_and_every_sample_table_records_how_it_got_in(plots):
    """A table is in the sample when it is prescreened, read and unflagged with no verdict,
    or judged `flat`, with the evidence of the reading that put it there. A verdict decides
    its table whatever the screen said, so a hand sample's correction of an unflagged table
    takes it out too."""
    writeSurvey(plots, [
        ('plots', 'plain.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'herded.csv', 'pass', NO_GROUPING, 'one row per cow'),
        ('plots', 'stored.csv', 'pass', NO_GROUPING, 'wide: visits as columns'),
        ('plots', 'hidden.csv', 'pass', NO_GROUPING, 'one row per cow'),
        ('plots', 'decided.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'distinct.csv', 'no repeated column', NO_GROUPING, 'no repeated column'),
    ])  # fmt: skip
    writeVerdicts(plots, [
        ('plots', 'herded.csv', 'flat', 'herd names the farm a dose came from, once each'),
        ('plots', 'stored.csv', 'wide', 'four visits as columns'),
        ('plots', 'hidden.csv', 'hidden grouping', 'cows repeat within herds'),
        ('plots', 'decided.csv', 'wide', 'two plots per row'),
    ])  # fmt: skip
    plots.measure()
    rows = readRows(plots.registry / 'flat.csv')
    assert [(r['object'], r['stratum'], r['basis'], r['evidence']) for r in rows] == [
        ('plain.csv', 'read', 'first reading', 'one row per plot'),
        ('herded.csv', 'read', 'second reading', 'herd names the farm a dose came from, once each'),
        ('distinct.csv', 'prescreened', 'prescreen', 'no repeated column'),
    ]


def test_the_pass_writes_a_row_per_sample_table_and_a_row_per_its_column(plots):
    """flat.csv keys a table by source and object, flat_columns.csv a column, in columns.csv's
    order less what a registry row's model binds. The plain table's response is linear in its
    dose, so its design is rank-deficient and its condition index written as `inf`."""
    writeSurvey(plots, [
        ('plots', 'plain.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'distinct.csv', 'no repeated column', NO_GROUPING, 'no repeated column'),
    ])  # fmt: skip
    plots.measure()
    tables = readRows(plots.registry / 'flat.csv')
    assert list(tables[0]) == [
        'source', 'object', 'tier', 'stratum', 'basis', 'evidence', 'n_obs', 'n_columns',
        'n_continuous', 'n_binary', 'n_categorical', 'n_ordered', 'n_id_columns', 'd_all',
        'condition_all',
    ]  # fmt: skip
    assert list(tables[0].values()) == [
        'plots', 'plain.csv', 'O', 'read', 'first reading', 'one row per plot',
        '3', '2', '2', '0', '0', '0', '0', '2', 'inf',
    ]  # fmt: skip
    columns = readRows(plots.registry / 'flat_columns.csv')
    assert list(columns[0]) == [
        'source', 'object', 'tier', 'column', 'type', 'K', 'missing_share', *COLUMN_STATISTICS,
    ]  # fmt: skip
    assert [(c['object'], c['column']) for c in columns] == [
        ('plain.csv', 'dose'), ('plain.csv', 'response'), ('distinct.csv', 'x'),
        ('distinct.csv', 'y'),
    ]  # fmt: skip

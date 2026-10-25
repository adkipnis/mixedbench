"""The flat module at its seams: the merged files in; the frame, `flat_screen.csv`, the two flat
files and the hand sample's files out; the screen rule and the measurer on hand-made tables."""

from collections import Counter
from pathlib import Path

import dimensions
import pandas as pd
import pytest
import yaml
from columns import COLUMN_STATISTICS
from conftest import asOrdered, measuredColumns, parsed, readRows, scratchMerger, sha, zippedFiles
from flat import FlatPass, ResponseCheck, VerdictCheck
from measure import Measurer
from mixedbench.datasets import Loader
from mixedbench.registry.row import writeCsv
from schema import CANDIDATE_COLUMNS, EXCLUDED, FLAT_RESPONSES, FLAT_VERDICTS
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


@pytest.fixture
def plots(tmp_path: Path) -> FlatPass:
    return plotsPass(tmp_path, PLOTS)


def plotsPass(tmp_path: Path, files: dict[str, str]) -> FlatPass:
    """A flat pass over the scratch registry and survey with one more url source, `plots`
    (Tier O), serving `files` from memory: every table the scratch sources pin has a repeated
    column named like an id, so none would pass the screen unflagged."""
    merger = scratchMerger(tmp_path / 'registry', tmp_path / 'survey')
    archive = zippedFiles('plots', files)
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


def writeResponses(flat: FlatPass, responses: list[tuple[str, str, str]]) -> None:
    """The responses as the merge leaves them in `flat_responses.csv`, the tier filled."""
    tiers = readFrame(flat.registry).tiers
    rows = []
    for source, object, response in responses:
        rows.append({'source': source, 'tier': tiers[source], 'object': object, 'response': response, 'evidence': 'its help page'})  # fmt: skip
    path = flat.survey / 'flat_responses.csv'
    writeCsv(pd.DataFrame(rows, columns=FLAT_RESPONSES.columns), path)


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
    writeResponses(plots, [
        ('plots', 'plain.csv', 'none'), ('plots', 'herded.csv', 'none'),
        ('plots', 'distinct.csv', 'none'),
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
    order less what a registry row's model binds. A table without a response keeps every
    column: the plain table's `response` is linear in its dose, so its design is rank-deficient
    and its condition index written as `inf`."""
    writeSurvey(plots, [
        ('plots', 'plain.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'distinct.csv', 'no repeated column', NO_GROUPING, 'no repeated column'),
    ])  # fmt: skip
    writeResponses(plots, [('plots', 'plain.csv', 'none'), ('plots', 'distinct.csv', 'none')])
    plots.measure()
    tables = readRows(plots.registry / 'flat.csv')
    assert list(tables[0]) == [
        'source', 'object', 'tier', 'stratum', 'basis', 'evidence', 'response', 'n_obs',
        'n_columns', 'n_continuous', 'n_binary', 'n_categorical', 'n_ordered', 'n_id_columns',
        'd_all', 'condition_all',
    ]  # fmt: skip
    assert list(tables[0].values()) == [
        'plots', 'plain.csv', 'O', 'read', 'first reading', 'one row per plot', 'none',
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


GAPPY = 'dose,response\n1.5,\n2.5,0.7\n3.5,0.9\n'  # a row without its response


def test_the_response_leaves_flat_columns_and_every_count_and_design_statistic_of_flat_csv(
    tmp_path,
):
    """A registry row's response is in neither columns.csv nor its design, so a flat table's
    response leaves both: the dose is left without a partner for max_abs_rho, and its design,
    the intercept and the standardized dose, is orthogonal, of condition index 1. Every row
    stays, the one without its response too."""
    flat = plotsPass(tmp_path, {'gappy.csv': GAPPY})
    writeSurvey(flat, [('plots', 'gappy.csv', 'pass', NO_GROUPING, 'one row per plot')])
    writeResponses(flat, [('plots', 'gappy.csv', 'response')])

    flat.measure()

    [table] = readRows(flat.registry / 'flat.csv')
    sizes = ['response', 'n_obs', 'n_columns', 'n_continuous', 'n_id_columns', 'd_all', 'condition_all']  # fmt: skip
    assert [table[s] for s in sizes] == ['response', '3', '1', '1', '0', '1', '1.0']
    columns = readRows(flat.registry / 'flat_columns.csv')
    assert [(c['column'], c['max_abs_rho']) for c in columns] == [('dose', '')]


def test_the_pass_refuses_naming_every_sample_table_without_a_response_or_with_one_its_table_lacks(
    plots,
):
    """A response arrives by shard, so a sample table can lack one, or name a column its table
    lacks once the shard is edited by hand. The pass then writes nothing."""
    writeSurvey(plots, [
        ('plots', 'plain.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'decided.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'distinct.csv', 'no repeated column', NO_GROUPING, 'no repeated column'),
    ])  # fmt: skip
    writeResponses(plots, [('plots', 'plain.csv', 'response'), ('plots', 'distinct.csv', 'z')])
    names = 'plots decided.csv: no response\nplots distinct.csv: no column z'
    with pytest.raises(ValueError, match=f'2 sample tables .*\n{names}$'):
        plots.measure()
    assert readRows(plots.registry / 'flat.csv') == []


# ---------------------------------------------------------------------------------
# the hand sample: the sample drawn, a batch handed off, the share that stood
# ---------------------------------------------------------------------------------
# a repeated integer column of eleven levels, which only the dropped integer rule would flag
INTEGER = 'count,rate\n' + ''.join(f'{c},{c + 0.5}\n' for c in [*range(11), 0])
# per stratum of the hand sample, its tables' size, file, filing line and verdict ('' for none)
STRATA = [
    ('prescreened', 13, DISTINCT, 'no repeated column', ''),
    ('read/unflagged', 22, PLAIN, 'one row per plot', ''),
    ('read/flagged', 18, HERDED, 'one row per cow', 'flat'),
    ('read/integer', 27, INTEGER, 'one row per survey', ''),
]


def strataPass(tmp_path: Path) -> FlatPass:
    """A flat sample of 80 tables over the four strata, and a flagged table judged wide."""
    files, survey, verdicts = {'stored.csv': HERDED}, [], []
    for stratum, size, text, detail, verdict in STRATA:
        screen = 'no repeated column' if stratum == 'prescreened' else 'pass'
        for i in range(size):
            object = f'{stratum.replace("/", "_")}_{i}.csv'
            files[object] = text
            survey.append(('plots', object, screen, NO_GROUPING, detail))
            if verdict != '':
                verdicts.append(('plots', object, verdict, 'herd names the farm, once each'))
    survey.append(('plots', 'stored.csv', 'pass', NO_GROUPING, 'one row per cow'))
    verdicts.append(('plots', 'stored.csv', 'wide', 'four visits as columns'))
    flat = plotsPass(tmp_path, files)
    writeSurvey(flat, survey)
    writeVerdicts(flat, verdicts)
    return flat


def test_draw_allocates_fifty_sample_tables_over_four_strata_in_two_batches(tmp_path):
    """The hand sample is 50 tables of the flat sample, proportional over its four strata.
    Worked by hand: 50/80 of 13, 22, 18 and 27 is 8.125, 13.75, 11.25 and 16.875, the two
    tables left over going to the largest remainders, read/integer's and read/unflagged's: 8,
    14, 11 and 17. A table judged wide is out of the sample, so never drawn. The draw is a
    function of the files and the seed, so drawing again writes the same file."""
    flat = strataPass(tmp_path)
    flat.draw(VerdictCheck())
    path = flat.survey / 'flat_sample.csv'
    sample = readRows(path)
    assert list(sample[0]) == [
        'source', 'object', 'tier', 'file', 'stratum', 'batch', 'basis', 'evidence', 'detail',
        'words', 'id_columns', 'integer_columns',
    ]  # fmt: skip
    assert Counter(row['stratum'] for row in sample) == {
        'prescreened': 8,
        'read/unflagged': 14,
        'read/flagged': 11,
        'read/integer': 17,
    }
    assert [row['batch'] for row in sample] == ['1'] * 25 + ['2'] * 25
    drawn = path.read_text()
    flat.draw(VerdictCheck())
    assert path.read_text() == drawn


ZEROS = '0' * 64
# one drawn table per kind of source; a row's columns as the verdict check's sample orders them
DRAWN = [
    ('pens', 'herds', 'R', 'data/herds.rda', 'read/unflagged', '1', 'first reading',
     'one row per cow', 'one row per cow', '', '', 'parity'),
    ('ros', 'Beauty/data/beauty.csv', 'T', 'Beauty/data/beauty.csv', 'read/flagged', '1',
     'second reading', 'prof names one instructor, once each', 'one row per course',
     'repeated', 'prof', ''),
    ('rabe_hesketh', 'pig.dta', 'T', 'pig.dta', 'prescreened', '1', 'prescreen',
     'no repeated column', 'no repeated column', '', '', ''),
    ('arriero_2017_dryad', 'voles.xlsx', 'D', 'voles.xlsx', 'read/integer', '1',
     'first reading', 'one row per vole', 'one row per vole', '', '', 'trap'),
    ('leder_2020_osf', 'data.csv', 'D', 'data.csv', 'read/unflagged', '1', 'first reading',
     'one row per participant', 'one row per participant', '', '', ''),
    ('pens', 'sows', 'R', 'data/sows.rda', 'read/unflagged', '2', 'first reading',
     'one row per sow', 'one row per sow', '', '', ''),
]  # fmt: skip


def handoffPass(tmp_path: Path) -> FlatPass:
    """A drawn sample with one table per kind of source, a CRAN package, a git tree, a url
    archive and two Tier D deposits, and the help pages of the first two."""
    registry, survey = tmp_path / 'registry', tmp_path / 'survey'
    registry.mkdir()
    survey.mkdir()
    (registry / 'sources.yaml').write_text(
        'seed: 0\n'
        'tiers:\n'
        '  R:\n'
        "    pens: {kind: cran, pin: '1.0'}\n"
        '  T:\n'
        '    ros: {kind: git, name: https://github.com/avehtari/ROS-Examples, pin: abc123}\n'
        f'    rabe_hesketh: {{kind: url, name: https://www.stata-press.com/data/mlmus4/mlmus4.zip, pin: {ZEROS}}}\n'
        '  D:\n'
        f'    arriero_2017_dryad: {{kind: url, name: https://datadryad.org/api/v2/files/51526/download, pin: {ZEROS}}}\n'
        f'    leder_2020_osf: {{kind: url, name: https://osf.io/download/znb6c/, pin: {ZEROS}}}\n'
    )
    (survey / 'deposit_files.csv').write_text(
        'label,link\n,osf.io/unlabelled\narriero_2017_dryad,10.5061/dryad.110pk\n'
        'leder_2020_osf,osf.io/txb9c\n'
    )
    writeCsv(pd.DataFrame(DRAWN, columns=VerdictCheck.COLUMNS), survey / 'flat_sample.csv')
    pages = {
        'pens/herds.txt': '\\name{herds}\n\\title{Weights of pigs by herd}\n',
        'ros/Beauty/data/beauty.csv.txt': '# first rows (of 463)\neval: float64\n',
    }
    for path, text in pages.items():
        (registry / 'help' / path).parent.mkdir(parents=True, exist_ok=True)
        (registry / 'help' / path).write_text(text)
    return FlatPass(registry, survey)


def test_handoff_names_each_tables_page_and_download_and_no_local_path(tmp_path):
    """The batch is checked in the browser against the source itself, so every table carries
    its page and its download at the pin, its filing line, the screen's reason, the second
    reading where one exists and the help page where one exists, and no path of the checkout.
    A Tier D page is its deposit's, at doi.org where the link is a DOI."""
    flat = handoffPass(tmp_path)

    text = flat.handoff(VerdictCheck(), 1)

    urls = [
        'https://cran.r-project.org/package=pens',
        'https://github.com/cran/pens/blob/1.0/data/herds.rda',
        'https://github.com/avehtari/ROS-Examples/tree/abc123/Beauty/data',
        'https://github.com/avehtari/ROS-Examples/blob/abc123/Beauty/data/beauty.csv',
        'https://www.stata-press.com/data/mlmus4.html',
        'https://www.stata-press.com/data/mlmus4/mlmus4.zip',
        'https://doi.org/10.5061/dryad.110pk',
        'https://datadryad.org/api/v2/files/51526/download',
        'https://osf.io/txb9c',
        'https://osf.io/download/znb6c/',
    ]
    assert [url for url in urls if url not in text] == []
    assert 'filing: one row per course' in text
    assert 'second reading: prof names one instructor, once each' in text
    assert '`prof`' in text and '`parity`' in text and '`trap`' in text
    assert '\\title{Weights of pigs by herd}' in text
    assert 'eval: float64' in text
    assert text.count('<details>') == 2  # the prescreened table and the deposits have no page
    assert 'sows' not in text  # batch 2
    assert str(tmp_path) not in text
    assert 'registry/' not in text
    assert 'cache' not in text


def test_handoff_cuts_a_help_page_longer_than_twenty_thousand_characters(tmp_path):
    """A help page can hold a whole table, one in the frame 20 MB of it, which would drown the
    prompt, so it is cut and says where."""
    flat = handoffPass(tmp_path)
    (flat.registry / 'help' / 'pens' / 'herds.txt').write_text('x' * 20_000 + 'y')

    text = flat.handoff(VerdictCheck(), 1)

    assert 'x' * 20_000 + '\n[cut at 20,000 characters]' in text
    assert 'xy' not in text


def test_agree_gives_the_share_of_drawn_tables_still_in_the_sample_per_stratum_and_overall(
    tmp_path,
):
    """A drawn table stood when the hand check left it in the flat sample. One re-filed into
    the registry has left the frame, and one judged wide or a hidden grouping has left the
    sample: neither stood."""
    flat = plotsPass(tmp_path, {
        'plain_0.csv': PLAIN, 'plain_1.csv': PLAIN, 'herded_0.csv': HERDED,
        'distinct_0.csv': DISTINCT, 'distinct_1.csv': DISTINCT, 'integer_0.csv': INTEGER,
    })  # fmt: skip
    writeSurvey(flat, [
        ('plots', 'plain_0.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'plain_1.csv', 'pass', NO_GROUPING, 'one row per plot'),
        ('plots', 'herded_0.csv', 'pass', NO_GROUPING, 'one row per cow'),
        ('plots', 'distinct_0.csv', 'no repeated column', NO_GROUPING, 'no repeated column'),
        ('plots', 'distinct_1.csv', 'no repeated column', 'derived or duplicated table', 'a copy'),
        ('plots', 'integer_0.csv', 'pass', NO_GROUPING, 'one row per survey'),
    ])  # fmt: skip
    writeVerdicts(flat, [
        ('plots', 'herded_0.csv', 'flat', 'herd names the farm, once each'),
        ('plots', 'plain_1.csv', 'wide', 'two plots per row'),
        ('plots', 'integer_0.csv', 'hidden grouping', 'counts repeat within surveys'),
    ])  # fmt: skip
    drawn = [
        ('plain_0.csv', 'read/unflagged'), ('plain_1.csv', 'read/unflagged'),
        ('herded_0.csv', 'read/flagged'), ('distinct_0.csv', 'prescreened'),
        ('distinct_1.csv', 'prescreened'), ('integer_0.csv', 'read/integer'),
    ]  # fmt: skip
    sample = pd.DataFrame(
        [{'source': 'plots', 'object': o, 'stratum': s, 'batch': '1'} for o, s in drawn]
    )
    columns = VerdictCheck.COLUMNS
    writeCsv(sample.reindex(columns=columns, fill_value=''), flat.survey / 'flat_sample.csv')

    flat.agree(VerdictCheck())

    rows = readRows(flat.survey / 'flat_agreement.csv')
    assert [list(row.values()) for row in rows] == [
        ['prescreened', '2', '0.5'],
        ['read/unflagged', '2', '0.5'],
        ['read/flagged', '1', '1.0'],
        ['read/integer', '1', '0.0'],
        ['all', '6', '0.5'],
    ]
    assert list(rows[0]) == ['stratum', 'tables', 'stood']


# ---------------------------------------------------------------------------------
# the response check: the sample drawn, a batch handed off, the share that stood
# ---------------------------------------------------------------------------------
def respondedPass(tmp_path: Path, named: int, unnamed: int) -> FlatPass:
    """A flat sample of plain tables, `named` with their response named and `unnamed` with
    `none`, and a table judged wide whose response was read before its verdict."""
    objects = [f'plain_{i}.csv' for i in range(named + unnamed)]
    flat = plotsPass(tmp_path, dict.fromkeys([*objects, 'stored.csv'], PLAIN))
    writeSurvey(flat, [('plots', o, 'pass', NO_GROUPING, 'one row per plot') for o in [*objects, 'stored.csv']])  # fmt: skip
    writeVerdicts(flat, [('plots', 'stored.csv', 'wide', 'two plots per row')])
    responses = [('plots', o, 'response') for o in objects[:named]]
    responses += [('plots', o, 'none') for o in objects[named:]]
    writeResponses(flat, [*responses, ('plots', 'stored.csv', 'response')])
    return flat


def test_the_response_check_draws_25_sample_tables_over_named_and_none_in_one_batch(tmp_path):
    """The response check is 25 tables of the flat sample, proportional over whether the reading
    named a response. Worked by hand: 25/33 of 20 and 13 is 15.15 and 9.85, the table left over
    going to the larger remainder, none's: 15 and 10. A table judged wide is out of the sample,
    so never drawn, and drawing again writes the same file."""
    flat = respondedPass(tmp_path, named=20, unnamed=13)

    flat.draw(ResponseCheck())

    path = flat.survey / 'flat_response_sample.csv'
    sample = readRows(path)
    assert list(sample[0]) == [
        'source', 'object', 'tier', 'file', 'stratum', 'batch', 'response', 'evidence',
    ]  # fmt: skip
    assert Counter(row['stratum'] for row in sample) == {'named': 15, 'none': 10}
    assert {row['batch'] for row in sample} == {'1'}
    assert 'stored.csv' not in {row['object'] for row in sample}
    drawn = path.read_text()
    flat.draw(ResponseCheck())
    assert path.read_text() == drawn


# a drawn table per kind of source; a row's columns as the response check's sample orders them
DRAWN_RESPONSES = [
    ('pens', 'herds', 'R', 'data/herds.rda', 'named', '1', 'weight',
     'lm(weight ~ breed + feed) in the help page examples'),
    ('ros', 'Beauty/data/beauty.csv', 'T', 'Beauty/data/beauty.csv', 'none', '1', 'none',
     'no model is documented: the help page only describes the columns'),
    ('arriero_2017_dryad', 'voles.xlsx', 'D', 'voles.xlsx', 'named', '1', 'mass',
     'NOT FLAT: trap indexes repeated captures; lm(mass ~ sex) in the paper'),
]  # fmt: skip


def test_the_response_check_hands_off_each_tables_response_its_evidence_and_its_urls(tmp_path):
    """The response check is read in the browser as the verdict check is: a self-contained
    prompt with the answers it takes, then per table its page and download at the pin, the
    response or `none`, the evidence and the help page where one exists, and no local path."""
    flat = handoffPass(tmp_path)
    sample = pd.DataFrame(DRAWN_RESPONSES, columns=ResponseCheck.COLUMNS)
    writeCsv(sample, flat.survey / 'flat_response_sample.csv')

    text = flat.handoff(ResponseCheck(), 1)

    urls = [
        'https://cran.r-project.org/package=pens',
        'https://github.com/cran/pens/blob/1.0/data/herds.rda',
        'https://github.com/avehtari/ROS-Examples/blob/abc123/Beauty/data/beauty.csv',
        'https://doi.org/10.5061/dryad.110pk',
    ]
    assert [url for url in urls if url not in text] == []
    assert ': response <column> — ' in text and ': none — ' in text
    assert '- response: weight\n- evidence: lm(weight ~ breed + feed)' in text
    assert '- response: none\n' in text
    assert 'NOT FLAT: trap indexes repeated captures' in text
    assert '\\title{Weights of pigs by herd}' in text
    assert text.count('<details>') == 2  # the deposit has no page
    assert str(tmp_path) not in text
    assert 'registry/' not in text


def test_the_response_check_agrees_where_a_drawn_tables_response_still_stands(tmp_path):
    """A drawn table stood when it is still in the flat sample and its response is the one
    drawn. plain_1 was drawn naming `dose`, which a hand correction replaced, and plain_2 was
    judged wide after the draw, which took it out of the sample: neither stood."""
    flat = respondedPass(tmp_path, named=3, unnamed=2)
    writeVerdicts(flat, [('plots', 'plain_2.csv', 'wide', 'two plots per row')])
    drawn = [
        ('plain_0.csv', 'named', 'response'), ('plain_1.csv', 'named', 'dose'),
        ('plain_2.csv', 'named', 'response'), ('plain_3.csv', 'none', 'none'),
        ('plain_4.csv', 'none', 'none'),
    ]  # fmt: skip
    rows = [{'source': 'plots', 'object': o, 'stratum': s, 'batch': '1', 'response': r} for o, s, r in drawn]  # fmt: skip
    sample = pd.DataFrame(rows).reindex(columns=ResponseCheck.COLUMNS, fill_value='')
    writeCsv(sample, flat.survey / 'flat_response_sample.csv')

    flat.agree(ResponseCheck())

    rows = readRows(flat.survey / 'flat_response_agreement.csv')
    assert list(rows[0]) == ['stratum', 'tables', 'stood']
    assert [list(row.values()) for row in rows] == [
        ['named', '3', '0.333'],
        ['none', '2', '1.0'],
        ['all', '5', '0.6'],
    ]


def test_the_wide_list_names_each_frame_table_judged_wide_with_its_source_and_evidence(flat):
    """The issue for the long forms lists every wide table once: a copy filed as derived has
    left the frame, and a table of another verdict is not listed."""
    writeSurvey(flat, SURVEY)
    writeVerdicts(flat, [
        ('pens', 'read', 'wide', 'four visits as columns'),
        ('pens', 'unique', 'flat', 'one row per pen'),
        ('pens', 'copy', 'wide', 'four visits as columns'),
    ])  # fmt: skip

    text = flat.listWide()

    assert text == '- **pens · read:** four visits as columns\n'

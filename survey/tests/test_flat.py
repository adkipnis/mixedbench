"""The flat module at its seams: the merged files in, the frame and `flat_screen.csv` out, and
the screen rule on hand-made tables (#116)."""

from pathlib import Path

import pandas as pd
import pytest
from conftest import readRows, scratchMerger
from flat import FlatPass
from mixedbench.registry.row import writeCsv
from schema import CANDIDATE_COLUMNS, EXCLUDED
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

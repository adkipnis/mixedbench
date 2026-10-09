"""The verification rule of ADR 0002 (#26): why each registry row counts as verified, assigned
once by script from the archived hand sample, the tier and the confidence."""

import pandas as pd
from verify import verification


def registryRows(rows: list[tuple[str, str, str, str, str]]) -> pd.DataFrame:
    """Registry rows as the dialect reads them, with only the columns the rule reads."""
    columns = ['source', 'tier', 'object', 'model_index', 'confidence']
    return pd.DataFrame(rows, columns=columns)


def test_the_hand_sample_and_tier_d_are_hand_then_high_confidence_then_second_reading() -> None:
    """A sampled row is `hand` whatever its confidence, and only the sampled model of its
    object; every Tier D row was hand-checked; the rest split on confidence,
    since every medium and low row had a blind second reading."""
    registry = registryRows(
        [
            ('lme4', 'R', 'sleepstudy', '1', 'medium'),  # sampled
            ('lme4', 'R', 'sleepstudy', '2', 'high'),  # same object, not sampled
            ('dryad_x', 'D', 'trial.csv', '1', 'low'),  # Tier D
            ('nlme', 'R', 'Orthodont', '1', 'high'),
            ('nlme', 'R', 'Rail', '1', 'low'),
        ]
    )
    sample = pd.DataFrame(
        [('lme4', 'sleepstudy', '1'), ('hox', 'SocsLong', '1')],  # one sampled row left
        columns=['source', 'object', 'model_index'],
    )
    verified = verification(registry, sample)
    assert list(verified) == ['hand', 'high', 'hand', 'high', 'second-reading']

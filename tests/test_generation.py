from __future__ import annotations

import pandas as pd

from scripts.generate_synthetic_telemetry import generate_events
from src.schema import ColumnNames, REQUIRED_COLUMNS


def test_generate_events_schema() -> None:
    df = generate_events(num_learners=1)
    assert not df.empty
    for col in REQUIRED_COLUMNS:
        assert col in df.columns


def test_generate_events_count() -> None:
    df = generate_events(num_learners=2)
    assert 12 <= len(df) <= 40
    assert df[ColumnNames.LEARNER_ID.value].nunique() == 2

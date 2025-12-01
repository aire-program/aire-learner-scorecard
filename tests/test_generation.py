import pandas as pd
from scripts.generate_synthetic_telemetry import generate_events
from src.schema import REQUIRED_COLUMNS

def test_generate_events_schema():
    df = generate_events(num_learners=1)
    assert not df.empty
    # Check all required columns are present
    for col in REQUIRED_COLUMNS:
        assert col in df.columns

def test_generate_events_count():
    df = generate_events(num_learners=2)
    # Each learner has between 6 and 20 events
    assert len(df) >= 12
    assert len(df) <= 40
    assert df["learner_id"].nunique() == 2

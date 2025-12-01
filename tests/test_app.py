import pandas as pd
import pytest
from src.schema import ColumnNames
from app import learner_summary, get_recommendations

@pytest.fixture
def sample_df():
    data = {
        ColumnNames.TIMESTAMP_UTC.value: pd.to_datetime(["2023-01-01", "2023-01-02"]),
        ColumnNames.LEARNER_ID.value: ["L-001", "L-001"],
        ColumnNames.RESOURCE_ID.value: ["R-01", "R-02"],
        ColumnNames.EVALUATION_SCORE.value: [4.0, 3.0],
        ColumnNames.USER_PROMPT_CHARACTER_COUNT.value: [100, 200],
        ColumnNames.PRIMARY_WEAKNESS.value: ["Clarity", "Clarity"],
        ColumnNames.RECOMMENDED_RESOURCE_ID.value: ["rec-01", "rec-01"]
    }
    return pd.DataFrame(data)

def test_learner_summary(sample_df):
    summary = learner_summary(sample_df)
    assert summary["events"] == 2
    assert summary["resources"] == 2
    assert summary["avg_score"] == 3.5
    assert summary["total_chars"] == 300

def test_get_recommendations(sample_df):
    recs = get_recommendations(sample_df)
    assert len(recs) == 3
    assert "Clarity" in recs[0]
    assert "rec-01" in recs[1]

def test_get_recommendations_empty():
    recs = get_recommendations(pd.DataFrame())
    assert recs == ["No data available for recommendations."]

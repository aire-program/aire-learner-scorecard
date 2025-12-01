from __future__ import annotations

from pathlib import Path
from typing import List, Dict

import pandas as pd
import plotly.express as px
import streamlit as st

from src.schema import REQUIRED_COLUMNS, ColumnNames

# Define path to data
DATA_PATH = Path(__file__).parent / "data" / "aire_telemetry_synthetic.csv"


@st.cache_data
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and validate telemetry data.

    Args:
        path: Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded and validated dataframe.
    """
    if not path.exists():
        st.error(f"Data file not found at {path}. Please run `python3 scripts/generate_synthetic_telemetry.py`.")
        st.stop()

    try:
        df = pd.read_csv(path)
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

    # Validate schema
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"Data schema mismatch. Missing columns: {', '.join(missing)}")
        st.stop()

    # Parse dates
    try:
        df[ColumnNames.TIMESTAMP_UTC.value] = pd.to_datetime(df[ColumnNames.TIMESTAMP_UTC.value])
    except Exception as e:
        st.error(f"Failed to parse timestamps: {e}")
        st.stop()

    return df


def learner_summary(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate summary metrics for a learner.

    Args:
        df: Dataframe containing learner events.

    Returns:
        Dict[str, float]: Summary metrics.
    """
    return {
        "events": len(df),
        "resources": df[ColumnNames.RESOURCE_ID.value].nunique(),
        "avg_score": df[ColumnNames.EVALUATION_SCORE.value].mean(),
        "total_chars": df[ColumnNames.USER_PROMPT_CHARACTER_COUNT.value].sum(),
    }


def get_recommendations(df: pd.DataFrame) -> List[str]:
    """Generate recommendations based on primary weaknesses.

    Args:
        df: Dataframe containing learner events.

    Returns:
        List[str]: List of recommendation strings.
    """
    if df.empty:
        return ["No data available for recommendations."]

    # Find most frequent weakness
    weakness_counts = df[ColumnNames.PRIMARY_WEAKNESS.value].value_counts()
    if weakness_counts.empty:
        return ["Keep practicing!"]

    top_weakness = weakness_counts.idxmax()
    
    # Get the recommended resource for this weakness (take the most common mapping in case of variance)
    rec_resource = df[df[ColumnNames.PRIMARY_WEAKNESS.value] == top_weakness][ColumnNames.RECOMMENDED_RESOURCE_ID.value].mode()
    rec_id = rec_resource[0] if not rec_resource.empty else "general-review"

    return [
        f"Primary Weakness: **{top_weakness}**",
        f"Recommended Action: Review **{rec_id}** to improve your skills in this area.",
        "Tip: Focus on consistent application of rubric criteria."
    ]


def score_trend_chart(df: pd.DataFrame):
    """Plot evaluation score over time.

    Args:
        df: Dataframe containing learner events.

    Returns:
        plotly.graph_objects.Figure: Line chart of scores.
    """
    df = df.sort_values(ColumnNames.TIMESTAMP_UTC.value)
    fig = px.line(
        df,
        x=ColumnNames.TIMESTAMP_UTC.value,
        y=ColumnNames.EVALUATION_SCORE.value,
        markers=True,
        title="Evaluation Score Trend",
        labels={ColumnNames.EVALUATION_SCORE.value: "Score (1-5)", ColumnNames.TIMESTAMP_UTC.value: "Date"},
        range_y=[0, 5.5]
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig


def resource_usage_chart(df: pd.DataFrame):
    """Plot usage by resource ID.

    Args:
        df: Dataframe containing learner events.

    Returns:
        plotly.graph_objects.Figure: Bar chart of resource usage.
    """
    counts = df[ColumnNames.RESOURCE_ID.value].value_counts().reset_index()
    counts.columns = [ColumnNames.RESOURCE_ID.value, "events"]
    fig = px.bar(
        counts, 
        x=ColumnNames.RESOURCE_ID.value, 
        y="events", 
        title="Resource Engagement",
        labels={ColumnNames.RESOURCE_ID.value: "Resource ID", "events": "Interactions"}
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig


def main():
    st.set_page_config(page_title="AIRE Learner Scorecard", layout="wide")
    st.title("AIRE Learner Scorecard")

    df = load_data()
    
    # Sidebar
    st.sidebar.header("Learner Profile")
    learners = sorted(df[ColumnNames.LEARNER_ID.value].unique())
    if not learners:
        st.warning("No learners found in dataset.")
        return

    selected_learner = st.sidebar.selectbox("Select Learner ID", learners)
    learner_df = df[df[ColumnNames.LEARNER_ID.value] == selected_learner]
    
    summary = learner_summary(learner_df)

    # Sidebar Metrics
    st.sidebar.markdown("---")
    st.sidebar.metric("Total Interactions", summary["events"])
    st.sidebar.metric("Resources Accessed", summary["resources"])
    st.sidebar.metric("Avg Evaluation Score", f"{summary['avg_score']:.2f}")
    
    # Main Dashboard
    
    # Row 1: Summary & Recommendations
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Performance Trend")
        st.plotly_chart(score_trend_chart(learner_df), use_container_width=True)

    with col2:
        st.subheader("AI Recommendations")
        for rec in get_recommendations(learner_df):
            st.info(rec)

    # Row 2: Detailed Breakdown
    st.subheader("Resource Engagement")
    st.plotly_chart(resource_usage_chart(learner_df), use_container_width=True)
    
    with st.expander("View Raw Telemetry"):
        st.dataframe(
            learner_df[[
                ColumnNames.TIMESTAMP_UTC.value, ColumnNames.RESOURCE_ID.value, ColumnNames.EVALUATION_SCORE.value, 
                ColumnNames.CLARITY_SCORE.value, ColumnNames.CONTEXT_SCORE.value, ColumnNames.CONSTRAINTS_SCORE.value, 
                ColumnNames.PRIMARY_WEAKNESS.value
            ]].sort_values(ColumnNames.TIMESTAMP_UTC.value, ascending=False)
        )


if __name__ == "__main__":
    main()

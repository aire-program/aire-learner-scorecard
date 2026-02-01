from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.schema import REQUIRED_COLUMNS, ColumnNames

# Define path to data
DATA_PATH = Path(__file__).parent / "data" / "aire_telemetry_synthetic.csv"


@st.cache_data
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and validate telemetry data from CSV."""
    if not path.exists():
        st.error(f"Data file not found at {path}. Run `python3 scripts/generate_synthetic_telemetry.py`.")
        st.stop()

    try:
        df = pd.read_csv(path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, OSError) as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        st.error(f"Data schema mismatch. Missing columns: {', '.join(missing)}")
        st.stop()

    try:
        df[ColumnNames.TIMESTAMP_UTC.value] = pd.to_datetime(df[ColumnNames.TIMESTAMP_UTC.value])
    except (ValueError, TypeError) as e:
        st.error(f"Failed to parse timestamps: {e}")
        st.stop()

    return df


def learner_summary(df: pd.DataFrame) -> dict[str, float]:
    """Calculate summary metrics for a learner."""
    return {
        "events": len(df),
        "resources": df[ColumnNames.RESOURCE_ID.value].nunique(),
        "avg_score": df[ColumnNames.EVALUATION_SCORE.value].mean(),
        "total_chars": df[ColumnNames.USER_PROMPT_CHARACTER_COUNT.value].sum(),
    }


def get_recommendations(df: pd.DataFrame) -> list[str]:
    """Generate recommendations based on primary weaknesses."""
    if df.empty:
        return ["No data available for recommendations."]

    weakness_counts = df[ColumnNames.PRIMARY_WEAKNESS.value].value_counts()
    if weakness_counts.empty:
        return ["Keep practicing!"]

    top_weakness = weakness_counts.idxmax()
    rec_resource = df.loc[
        df[ColumnNames.PRIMARY_WEAKNESS.value] == top_weakness,
        ColumnNames.RECOMMENDED_RESOURCE_ID.value
    ].mode()
    rec_id = rec_resource.iloc[0] if not rec_resource.empty else "general-review"

    return [
        f"Primary Weakness: **{top_weakness}**",
        f"Recommended Action: Review **{rec_id}** to improve in this area.",
        "Tip: Focus on consistent application of rubric criteria.",
    ]


def score_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Plot evaluation score over time."""
    sorted_df = df.sort_values(ColumnNames.TIMESTAMP_UTC.value)
    fig = px.line(
        sorted_df,
        x=ColumnNames.TIMESTAMP_UTC.value,
        y=ColumnNames.EVALUATION_SCORE.value,
        markers=True,
        title="Evaluation Score Trend",
        labels={
            ColumnNames.EVALUATION_SCORE.value: "Score (1-5)",
            ColumnNames.TIMESTAMP_UTC.value: "Date",
        },
        range_y=[0, 5.5],
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
    return fig


def resource_usage_chart(df: pd.DataFrame) -> go.Figure:
    """Plot usage by resource ID."""
    counts = (
        df[ColumnNames.RESOURCE_ID.value]
        .value_counts()
        .reset_index(name="events")
        .rename(columns={"index": ColumnNames.RESOURCE_ID.value})
    )
    fig = px.bar(
        counts,
        x=ColumnNames.RESOURCE_ID.value,
        y="events",
        title="Resource Engagement",
        labels={ColumnNames.RESOURCE_ID.value: "Resource ID", "events": "Interactions"},
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
    return fig


def main() -> None:
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

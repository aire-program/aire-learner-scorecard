from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st

# Define path to data
DATA_PATH = Path(__file__).parent / "data" / "aire_telemetry_synthetic.csv"

# Required columns for validation
REQUIRED_COLUMNS = [
    "timestamp_utc",
    "learner_id",
    "resource_id",
    "evaluation_score",
    "clarity_score",
    "context_score",
    "constraints_score",
    "primary_weakness",
    "recommended_resource_id",
    "user_prompt_character_count",
]


@st.cache_data
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and validate telemetry data."""
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
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"])
    except Exception as e:
        st.error(f"Failed to parse timestamps: {e}")
        st.stop()

    return df


def learner_summary(df: pd.DataFrame) -> dict[str, float]:
    """Calculate summary metrics for a learner."""
    return {
        "events": len(df),
        "resources": df["resource_id"].nunique(),
        "avg_score": df["evaluation_score"].mean(),
        "total_chars": df["user_prompt_character_count"].sum(),
    }


def get_recommendations(df: pd.DataFrame) -> List[str]:
    """Generate recommendations based on primary weaknesses."""
    if df.empty:
        return ["No data available for recommendations."]

    # Find most frequent weakness
    weakness_counts = df["primary_weakness"].value_counts()
    if weakness_counts.empty:
        return ["Keep practicing!"]

    top_weakness = weakness_counts.idxmax()
    
    # Get the recommended resource for this weakness (take the most common mapping in case of variance)
    rec_resource = df[df["primary_weakness"] == top_weakness]["recommended_resource_id"].mode()
    rec_id = rec_resource[0] if not rec_resource.empty else "general-review"

    return [
        f"Primary Weakness: **{top_weakness}**",
        f"Recommended Action: Review **{rec_id}** to improve your skills in this area.",
        "Tip: Focus on consistent application of rubric criteria."
    ]


def score_trend_chart(df: pd.DataFrame):
    """Plot evaluation score over time."""
    df = df.sort_values("timestamp_utc")
    fig = px.line(
        df,
        x="timestamp_utc",
        y="evaluation_score",
        markers=True,
        title="Evaluation Score Trend",
        labels={"evaluation_score": "Score (1-5)", "timestamp_utc": "Date"},
        range_y=[0, 5.5]
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig


def resource_usage_chart(df: pd.DataFrame):
    """Plot usage by resource ID."""
    counts = df["resource_id"].value_counts().reset_index()
    counts.columns = ["resource_id", "events"]
    fig = px.bar(
        counts, 
        x="resource_id", 
        y="events", 
        title="Resource Engagement",
        labels={"resource_id": "Resource ID", "events": "Interactions"}
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig


def main():
    st.set_page_config(page_title="AIRE Learner Scorecard", layout="wide")
    st.title("AIRE Learner Scorecard")

    df = load_data()
    
    # Sidebar
    st.sidebar.header("Learner Profile")
    learners = sorted(df["learner_id"].unique())
    if not learners:
        st.warning("No learners found in dataset.")
        return

    selected_learner = st.sidebar.selectbox("Select Learner ID", learners)
    learner_df = df[df["learner_id"] == selected_learner]
    
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
                "timestamp_utc", "resource_id", "evaluation_score", 
                "clarity_score", "context_score", "constraints_score", 
                "primary_weakness"
            ]].sort_values("timestamp_utc", ascending=False)
        )


if __name__ == "__main__":
    main()

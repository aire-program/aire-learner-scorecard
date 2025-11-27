from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path(__file__).parent / "data" / "aire_telemetry_synthetic.csv"


@st.cache_data
def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def learner_summary(df: pd.DataFrame) -> dict[str, float]:
    return {
        "events": len(df),
        "modules": df["module"].nunique(),
        "avg_rubric": df["rubric_score"].mean(),
        "tokens": df["input_tokens"].sum() + df["output_tokens"].sum(),
    }


def recommendations_for(df: pd.DataFrame) -> List[str]:
    recs: List[str] = []
    avg_score = df["rubric_score"].mean()
    low_dim = df.groupby("rubric_dimension")["rubric_score"].mean().sort_values().head(1)
    if avg_score < 3:
        recs.append("Focus on rubric alignment; revisit the rubric before drafting responses.")
    if not low_dim.empty:
        recs.append(f"Reinforce {low_dim.index[0]} by practicing with smaller prompts.")
    common_tag = df["recommendation_tag"].value_counts().idxmax()
    if common_tag == "ground_with_context":
        recs.append("Strengthen grounding by citing the provided context in every answer.")
    elif common_tag == "revise_prompt":
        recs.append("Iterate on prompts: start simple, add constraints, and verify outputs.")
    elif common_tag == "examples_needed":
        recs.append("Add concrete examples to clarify reasoning and expected outputs.")
    if not recs:
        recs.append("Maintain current approach; continue iterating and checking rubric fit.")
    return recs[:3]


def engagement_line_chart(df: pd.DataFrame):
    sorted_df = df.sort_values("timestamp")
    fig = px.line(
        sorted_df,
        x="timestamp",
        y="rubric_score",
        color="rubric_dimension",
        markers=True,
        title="Rubric Scores Over Time",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig


def resource_usage_chart(df: pd.DataFrame):
    counts = df["module"].value_counts().reset_index()
    counts.columns = ["module", "events"]
    fig = px.bar(counts, x="module", y="events", title="Resource Usage by Module")
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    return fig


def main():
    st.set_page_config(page_title="AIRE Learner Scorecard", layout="wide")
    st.title("AIRE Learner Scorecard")

    if not DATA_PATH.exists():
        st.error(
            f"Telemetry file not found at {DATA_PATH}. Run `python generate_synthetic_telemetry.py` to create it."
        )
        return

    df = load_data()
    learners = sorted(df["learner_id"].unique())

    st.sidebar.header("Learner")
    selected = st.sidebar.selectbox("Select learner", learners)
    learner_df = df[df["learner_id"] == selected]
    summary = learner_summary(learner_df)

    st.sidebar.metric("Interactions", summary["events"])
    st.sidebar.metric("Modules", summary["modules"])
    st.sidebar.metric("Avg Rubric", f"{summary['avg_rubric']:.2f}")
    st.sidebar.metric("Total Tokens", int(summary["tokens"]))

    st.subheader("Engagement Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Interactions", summary["events"])
    col2.metric("Modules", summary["modules"])
    col3.metric("Avg Rubric", f"{summary['avg_rubric']:.2f}")
    col4.metric("Tokens Used", int(summary["tokens"]))

    st.subheader("Rubric Performance")
    st.plotly_chart(engagement_line_chart(learner_df), use_container_width=True)

    st.subheader("Resource Usage")
    st.plotly_chart(resource_usage_chart(learner_df), use_container_width=True)

    st.subheader("Personalized Recommendations")
    for rec in recommendations_for(learner_df):
        st.write(f"• {rec}")


if __name__ == "__main__":
    main()

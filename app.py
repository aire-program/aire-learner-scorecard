from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.schema import REQUIRED_COLUMNS, ColumnNames

# Define path to data
DATA_PATH = Path(__file__).parent / "data" / "aire_telemetry_synthetic.csv"

# Feature flags / deployment controls
# - AIRE_FIXED_LEARNER_ID: if set, UI is locked to this learner (no selector shown)
# - AIRE_ALLOW_LEARNER_SWITCH: if "true", shows the selector to switch learners (dev/test only)
AIRE_FIXED_LEARNER_ID = os.environ.get("AIRE_FIXED_LEARNER_ID")
AIRE_ALLOW_LEARNER_SWITCH = os.environ.get("AIRE_ALLOW_LEARNER_SWITCH", "").lower() == "true"


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


def prompt_length_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter of prompt length vs score."""
    fig = px.scatter(
        df,
        x=ColumnNames.USER_PROMPT_CHARACTER_COUNT.value,
        y=ColumnNames.EVALUATION_SCORE.value,
        labels={
            ColumnNames.USER_PROMPT_CHARACTER_COUNT.value: "Prompt length (characters)",
            ColumnNames.EVALUATION_SCORE.value: "Score (1-5)",
        },
        title="Find Your Right-Sized Prompts",
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0})
    return fig


def practice_variety_chart(df: pd.DataFrame) -> go.Figure:
    """Distribution of resource usage."""
    return resource_usage_chart(df)


def best_time_chart(df: pd.DataFrame) -> go.Figure:
    """Best time to work by hour-of-day scores."""
    hours = df.copy()
    hours["hour"] = hours[ColumnNames.TIMESTAMP_UTC.value].dt.hour
    agg = hours.groupby("hour")[ColumnNames.EVALUATION_SCORE.value].mean().reset_index()
    fig = px.bar(
        agg,
        x="hour",
        y=ColumnNames.EVALUATION_SCORE.value,
        labels={"hour": "Hour of day", ColumnNames.EVALUATION_SCORE.value: "Avg score"},
        title="When You Usually Do Your Best (local hour)",
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0})
    return fig


def aggregate_score_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Plot average evaluation score over time (daily)."""
    daily = (
        df.assign(date=df[ColumnNames.TIMESTAMP_UTC.value].dt.date)
        .groupby("date")[ColumnNames.EVALUATION_SCORE.value]
        .mean()
        .reset_index()
    )
    fig = px.line(
        daily,
        x="date",
        y=ColumnNames.EVALUATION_SCORE.value,
        markers=True,
        title="Average Evaluation Score (All Learners)",
        labels={"date": "Date", ColumnNames.EVALUATION_SCORE.value: "Avg Score (1-5)"},
        range_y=[0, 5.5],
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
    return fig


def weakness_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Plot distribution of primary weaknesses."""
    counts = (
        df[ColumnNames.PRIMARY_WEAKNESS.value]
        .value_counts()
        .reset_index(name="events")
        .rename(columns={"index": ColumnNames.PRIMARY_WEAKNESS.value})
    )
    fig = px.bar(
        counts,
        x=ColumnNames.PRIMARY_WEAKNESS.value,
        y="events",
        title="Primary Weakness Distribution",
        labels={ColumnNames.PRIMARY_WEAKNESS.value: "Weakness", "events": "Count"},
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 40, "b": 0})
    return fig


def weakness_decay_chart(df: pd.DataFrame) -> go.Figure:
    """Rolling share of weaknesses over last 30 days."""
    if df.empty:
        return go.Figure()
    frame = df.copy()
    frame["date"] = frame[ColumnNames.TIMESTAMP_UTC.value].dt.date
    daily = (
        frame.groupby(["date", ColumnNames.PRIMARY_WEAKNESS.value])
        .size()
        .reset_index(name="count")
    )
    pivot = daily.pivot(index="date", columns=ColumnNames.PRIMARY_WEAKNESS.value, values="count").fillna(0)
    pivot = pivot.rolling(window=7, min_periods=1).mean()
    fig = px.area(
        pivot,
        title="Are Your Common Issues Fading?",
        labels={"value": "Avg issues (7-day)", "date": "Date"},
    )
    fig.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0}, legend_title_text="Weakness")
    return fig


def micro_skill_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap of rubric dimensions by session order."""
    subset = df[
        [
            ColumnNames.CLARITY_SCORE.value,
            ColumnNames.CONTEXT_SCORE.value,
            ColumnNames.CONSTRAINTS_SCORE.value,
            ColumnNames.EVALUATION_SCORE.value,
        ]
    ].reset_index(drop=True)
    subset.index = subset.index + 1
    fig = px.imshow(
        subset.T,
        aspect="auto",
        labels={"x": "Session #", "color": "Score (1-5)"},
        title="Which Rubric Parts Need Attention",
    )
    fig.update_yaxes(ticktext=["Clarity", "Context", "Constraints", "Overall"], tickvals=list(range(4)))
    fig.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0})
    return fig


def surprise_dips(df: pd.DataFrame) -> pd.DataFrame:
    """Identify sessions with drops below personal median - 1."""
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "score", "note"])
    median = df[ColumnNames.EVALUATION_SCORE.value].median()
    dips = df[df[ColumnNames.EVALUATION_SCORE.value] < median - 1]
    return dips[[ColumnNames.TIMESTAMP_UTC.value, ColumnNames.EVALUATION_SCORE.value]].rename(
        columns={ColumnNames.TIMESTAMP_UTC.value: "timestamp", ColumnNames.EVALUATION_SCORE.value: "score"}
    )


def consistency_score(df: pd.DataFrame) -> float:
    """Lower std dev = steadier performance."""
    return float(df[ColumnNames.EVALUATION_SCORE.value].std(ddof=0))


def bounce_back_prompts(df: pd.DataFrame) -> float | None:
    """Average prompts needed to recover above personal average after a dip."""
    scores = df[ColumnNames.EVALUATION_SCORE.value].tolist()
    if not scores:
        return None
    avg = sum(scores) / len(scores)
    recoveries: list[int] = []
    for i, s in enumerate(scores[:-1]):
        if s < avg - 0.5:
            for j in range(i + 1, len(scores)):
                if scores[j] >= avg:
                    recoveries.append(j - i)
                    break
    if not recoveries:
        return None
    return sum(recoveries) / len(recoveries)


def goal_progress(df: pd.DataFrame, target_score: float, target_interactions: int) -> Tuple[float, float]:
    """Return current average and remaining interactions to target."""
    recent = df.tail(target_interactions)
    current_avg = recent[ColumnNames.EVALUATION_SCORE.value].mean() if not recent.empty else 0
    return current_avg, max(0, target_interactions - len(recent))


def resource_effect(df: pd.DataFrame) -> pd.DataFrame:
    """Estimate before/after score lift for resources used by the learner."""
    if df.empty:
        return pd.DataFrame(columns=["resource", "before", "after", "delta"])
    rows = []
    for resource, group in df.groupby(ColumnNames.RESOURCE_ID.value):
        first_ts = group[ColumnNames.TIMESTAMP_UTC.value].min()
        before = df[df[ColumnNames.TIMESTAMP_UTC.value] < first_ts][ColumnNames.EVALUATION_SCORE.value]
        after = df[df[ColumnNames.TIMESTAMP_UTC.value] >= first_ts][ColumnNames.EVALUATION_SCORE.value]
        if after.empty:
            continue
        rows.append(
            {
                "resource": resource,
                "before": before.mean() if not before.empty else None,
                "after": after.mean(),
                "delta": (after.mean() - before.mean()) if not before.empty else None,
            }
        )
    return pd.DataFrame(rows).sort_values("delta", ascending=False)


def acted_on_feedback(df: pd.DataFrame) -> pd.DataFrame:
    """When learner used the recommended resource next."""
    records: list[dict[str, str]] = []
    df_sorted = df.sort_values(ColumnNames.TIMESTAMP_UTC.value)
    rec_col = ColumnNames.RECOMMENDED_RESOURCE_ID.value
    for i in range(len(df_sorted) - 1):
        rec = df_sorted.iloc[i][rec_col]
        next_res = df_sorted.iloc[i + 1][ColumnNames.RESOURCE_ID.value]
        if rec == next_res:
            records.append(
                {
                    "timestamp": df_sorted.iloc[i + 1][ColumnNames.TIMESTAMP_UTC.value],
                    "resource": rec,
                    "note": "Followed recommendation next session",
                }
            )
    return pd.DataFrame(records)


def recent_sessions(df: pd.DataFrame, limit: int = 6) -> pd.DataFrame:
    cols = [
        ColumnNames.TIMESTAMP_UTC.value,
        ColumnNames.EVALUATION_SCORE.value,
        ColumnNames.PRIMARY_WEAKNESS.value,
        ColumnNames.RESOURCE_ID.value,
    ]
    return df.sort_values(ColumnNames.TIMESTAMP_UTC.value, ascending=False).head(limit)[cols]


def aggregate_summary(df: pd.DataFrame) -> dict[str, float]:
    """Overall metrics across all learners."""
    return {
        "events": len(df),
        "learners": df[ColumnNames.LEARNER_ID.value].nunique(),
        "resources": df[ColumnNames.RESOURCE_ID.value].nunique(),
        "avg_score": df[ColumnNames.EVALUATION_SCORE.value].mean(),
    }


def main() -> None:
    st.set_page_config(page_title="AIRE Learner Scorecard", layout="wide")
    # tighten sidebar top padding
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            padding-top: 0 !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 4px !important;
            margin-top: 0 !important;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("AIRE Learner Scorecard")

    df = load_data()

    # Sidebar branding
    st.sidebar.markdown(
        """
        <div style="padding-top:8px; font-family: 'Inter', sans-serif;">
            <div style="font-size: 26px; font-weight: 700; line-height: 1.1; margin-bottom: 2px;">
                AIRE
            </div>
            <div style="font-size: 13px; font-weight: 500; line-height: 1.2; margin-bottom: 12px;">
                Applied AI Innovation and Research Enablement
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Determine learner scope
    learners = sorted(df[ColumnNames.LEARNER_ID.value].unique())
    if not learners:
        st.warning("No learners found in dataset.")
        return

    default_id = learners[0]
    query_params = st.query_params
    fixed_id = AIRE_FIXED_LEARNER_ID or query_params.get("learner_id", default_id)

    if fixed_id not in learners:
        st.error(f"Learner '{fixed_id}' not found in dataset.")
        st.stop()

    if AIRE_ALLOW_LEARNER_SWITCH:
        st.sidebar.header("Learner Profile (dev mode)")
        selected_learner = st.sidebar.selectbox("Select Learner ID", learners, index=learners.index(fixed_id))
    else:
        selected_learner = fixed_id
        st.sidebar.info(f"Learner locked to {selected_learner}")

    learner_df = df[df[ColumnNames.LEARNER_ID.value] == selected_learner]
    summary = learner_summary(learner_df)

    # Sidebar Metrics
    st.sidebar.markdown("---")
    st.sidebar.metric("Total Interactions", summary["events"])
    st.sidebar.metric("Resources Accessed", summary["resources"])
    st.sidebar.metric("Avg Evaluation Score", f"{summary['avg_score']:.2f}")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 8px;">
            <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/github.svg" width="18" height="18" />
            <a href="https://github.com/aire-program/aire-learner-scorecard" target="_blank">Contribute on GitHub</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "Quick View",
            "Performance & Stability",
            "Skill Weakness & Progress",
            "Action → Outcome",
            "Prompt Crafting Aids",
            "Recent Sessions",
        ]
    )

    # Quick View tab (landing)
    with tabs[0]:
        st.subheader("Quick View")
        st.caption("A fast snapshot of how you're doing today.")
        overview_col1, overview_col2 = st.columns([2, 1])
        with overview_col1:
            st.markdown("**Score trend** – how your scores have moved. Steady ups mean your new habits are sticking.")
            st.plotly_chart(score_trend_chart(learner_df), use_container_width=True, key="score_trend")
        with overview_col2:
            st.markdown("**Quick tips** – the most relevant next actions.")
            for rec in get_recommendations(learner_df):
                st.info(rec)

    # Performance & Stability tab
    with tabs[1]:
        st.subheader("Performance & Stability")
        st.caption("See how steady your scores are and how fast you recover after a low score.")

        c1, c2, c3 = st.columns(3)
        c1.metric("Steady progress", f"{consistency_score(learner_df):.2f} std dev")
        bounce = bounce_back_prompts(learner_df)
        c2.metric("Bounce-back speed", f"{bounce:.1f} prompts" if bounce else "No dips yet")

        target_score = st.slider("Target average score", 3.0, 5.0, 4.2, 0.1)
        target_interactions = st.slider("How many recent prompts to track", 5, 30, 10, 1)
        current_avg, remaining = goal_progress(learner_df, target_score, target_interactions)
        c3.metric("Goal tracker", f"{current_avg:.2f} / {target_score}", f"{remaining} prompts left")

    # Skill Weakness & Progress tab
    with tabs[2]:
        st.subheader("Skill Weakness & Progress")
        st.caption("Spot which skills are improving and which still need attention.")
        st.plotly_chart(weakness_decay_chart(learner_df), use_container_width=True, key="weakness_decay")
        st.plotly_chart(micro_skill_heatmap(learner_df), use_container_width=True, key="micro_skill")
        dips = surprise_dips(learner_df)
        with st.expander("Surprise dips (sessions to review)"):
            if dips.empty:
                st.write("No big drops found—keep it up!")
            else:
                st.dataframe(dips)

    # Action → Outcome tab
    with tabs[3]:
        st.subheader("Action → Outcome")
        st.caption("See what happened after you followed tips or used resources.")
        st.plotly_chart(resource_usage_chart(learner_df), use_container_width=True, key="resource_usage")
        effects = resource_effect(learner_df)
        st.markdown("**What helped most** (score change after first using each resource)")
        if effects.empty:
            st.write("Not enough data yet.")
        else:
            st.dataframe(effects)

        acted = acted_on_feedback(learner_df)
        st.markdown("**When you followed a recommendation right away**")
        if acted.empty:
            st.write("No immediate follow-through recorded yet.")
        else:
            st.dataframe(acted)

    # Prompt Crafting Aids tab
    with tabs[4]:
        st.subheader("Prompt Crafting Aids")
        st.caption("Find your sweet spot for prompt length and mix up your practice.")
        st.plotly_chart(prompt_length_scatter(learner_df), use_container_width=True, key="prompt_length")
        st.plotly_chart(practice_variety_chart(learner_df), use_container_width=True, key="practice_variety")
        st.plotly_chart(best_time_chart(learner_df), use_container_width=True, key="best_time")

    # Recent Sessions tab
    with tabs[5]:
        st.subheader("Recent Sessions")
        st.caption("A quick log of your latest prompts to reflect on what changed.")
        st.dataframe(recent_sessions(learner_df))


if __name__ == "__main__":
    main()

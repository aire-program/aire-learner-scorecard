from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.schema import REQUIRED_COLUMNS, ColumnNames

# Design tokens
PRIMARY_ACCENT = "#0F6678"
SECONDARY_ACCENT = "#1BA3BC"
SURFACE = "#F7FBFC"
SURFACE_MUTED = "#E8F2F4"
TEXT_STRONG = "#0B1C22"
TEXT_MUTED = "#5A6B70"
BORDER = "#D6E5E8"
SHADOW = "0 10px 30px -18px rgba(15,102,120,0.35)"


def apply_fig_theme(fig: go.Figure) -> go.Figure:
    """Consistent chart styling with accent palette."""
    fig.update_layout(
        colorway=[PRIMARY_ACCENT, SECONDARY_ACCENT, "#8FA3AD", "#C4D5DA"],
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=TEXT_STRONG, family="Manrope, system-ui, sans-serif"),
        hoverlabel=dict(bgcolor="white", font_color=TEXT_STRONG),
        xaxis=dict(showgrid=True, gridcolor="rgba(15,102,120,0.18)", linecolor=BORDER, ticks="outside"),
        yaxis=dict(showgrid=True, gridcolor="rgba(15,102,120,0.18)", linecolor=BORDER, ticks="outside"),
        legend=dict(bgcolor="rgba(255,255,255,0.8)", bordercolor=BORDER, borderwidth=1),
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
    )
    return fig


def render_card(title: str | None, icon: str | None, body_fn: callable) -> None:
    """Utility to render a styled card with optional title and icon."""
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if title:
        icon_html = f"<span class='tab-icon' data-lucide='{icon}'></span>" if icon else ""
        st.markdown(f"<div class='card-title'>{icon_html}{title}</div>", unsafe_allow_html=True)
    body_fn()
    st.markdown("</div>", unsafe_allow_html=True)


def render_empty_card(title: str, message: str, icon: str = "folder-x") -> None:
    """Consistent empty/edge state card."""
    st.markdown(
        f"""
        <div class='card empty-card'>
            <div class='card-title'><span class='tab-icon' data-lucide='{icon}'></span>{title}</div>
            <div class='empty-emoji'>📄</div>
            <div class='muted'>{message}</div>
            <div class='empty-actions'>
                <a class='primary-btn' href='#'>Add data</a>
                <a class='ghost-btn' href='https://github.com/aire-program/aire-learner-scorecard' target='_blank'>Learn how</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    fig.update_traces(line=dict(width=3), marker=dict(size=8, color=SECONDARY_ACCENT, line=dict(width=0)))
    return apply_fig_theme(fig)


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
    fig.update_traces(marker_color=PRIMARY_ACCENT, marker_line_width=0)
    return apply_fig_theme(fig)


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
    fig.update_traces(marker=dict(color=PRIMARY_ACCENT, size=9, line=dict(width=0)))
    return apply_fig_theme(fig)


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
    fig.update_traces(marker_color=SECONDARY_ACCENT, marker_line_width=0)
    return apply_fig_theme(fig)


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
    fig.update_traces(line=dict(width=3), marker=dict(size=7, color=SECONDARY_ACCENT))
    return apply_fig_theme(fig)


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
    fig.update_traces(marker_color=PRIMARY_ACCENT, marker_line_width=0)
    return apply_fig_theme(fig)


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
    fig.update_layout(legend_title_text="Weakness")
    fig.update_traces(line=dict(width=2), fill="tozeroy")
    return apply_fig_theme(fig)


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
    fig.update_layout(coloraxis_colorscale="Tealgrn")
    return apply_fig_theme(fig)


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

    # Global styling + icon CDN
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Manrope:wght@400;500;600&display=swap" rel="stylesheet">
        <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
        <style>
        :root {{
            --accent: {PRIMARY_ACCENT};
            --accent-2: {SECONDARY_ACCENT};
            --surface: {SURFACE};
            --surface-muted: {SURFACE_MUTED};
            --text-strong: {TEXT_STRONG};
            --text-muted: {TEXT_MUTED};
            --border: {BORDER};
            --shadow-elevated: {SHADOW};
            --success: #3CBF8A;
            --warn: #F5A524;
            --radius: 14px;
            --radius-soft: 10px;
        }}
        html, body, [class*="css"] {{
            font-family: 'Manrope', system-ui, -apple-system, sans-serif;
            color: var(--text-strong);
            background: linear-gradient(180deg, #fdfefe 0%, #f3f7f8 35%, #eef5f6 100%);
        }}
        .main-title {{
            font-family: 'Space Grotesk', 'Manrope', sans-serif;
            font-weight: 700;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        /* Utility bar (row housing title + date/actions) */
        div[data-testid="stHorizontalBlock"]:has(#utility-title) {{
            padding: 10px 14px;
            margin: 6px 0 14px 0;
            background: #ffffffbf;
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow-elevated);
            backdrop-filter: blur(6px);
        }}
        .utility-actions { display: flex; gap: 10px; align-items: center; }
        .pill {{
            padding: 6px 10px; border-radius: 999px; border: 1px solid var(--border);
            background: var(--surface);
            color: var(--text-muted);
            font-size: 12px; font-weight: 600;
        }}
        .icon-btn {{
            width: 36px; height: 36px; border-radius: 10px;
            display: grid; place-items: center;
            background: var(--surface); border: 1px solid var(--border);
            transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease, background 160ms ease;
        }}
        .icon-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 14px 30px -18px rgba(15,102,120,0.45);
            border-color: var(--accent);
            background: #fff;
        }}
        .icon-btn:active {{ transform: scale(0.995); }}
        .stButton>button {{
            border-radius: 12px;
            border: 1px solid var(--border);
            background: var(--surface);
            color: var(--text-strong);
            font-weight: 600;
            transition: all 180ms ease;
            box-shadow: 0 10px 30px -22px rgba(15,102,120,0.55);
        }}
        .stButton>button:hover {{
            transform: translateY(-2px);
            border-color: var(--accent);
            background: #fff;
        }}
        .stButton>button:active {{ transform: scale(0.995); }}
        .stButton>button.primary {{
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }}
        .stButton>button.primary:hover {{ background: #0d5666; }}
        .stButton>button.ghost {{ background: transparent; }}
        .primary-btn, .ghost-btn {{
            display: inline-flex; align-items: center; justify-content: center;
            padding: 10px 14px; border-radius: 12px; font-weight: 700;
            text-decoration: none; transition: all 180ms ease; border: 1px solid var(--border);
        }}
        .primary-btn {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
        .primary-btn:hover {{ background: #0d5666; }}
        .ghost-btn {{ background: transparent; color: var(--text-strong); }}
        .ghost-btn:hover {{ border-color: var(--accent); }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            box-shadow: var(--shadow-elevated);
            padding: 18px;
            transition: transform 160ms ease, box-shadow 160ms ease;
        }}
        .card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 18px 34px -18px rgba(15,102,120,0.45);
        }}
        .card-title {{ display: flex; align-items: center; gap: 10px; font-weight: 700; margin-bottom: 6px; }}
        .muted {{ color: var(--text-muted); font-size: 13px; }}
        .kpi-number {{ font-size: 32px; font-weight: 700; letter-spacing: -0.02em; }}
        .kpi-label {{ color: var(--text-muted); font-weight: 600; font-size: 13px; }}
        .chip-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }}
        .chip {{ padding: 6px 10px; background: var(--surface-muted); border-radius: 999px; font-weight: 600; color: var(--text-muted); font-size: 12px; border: 1px solid var(--border); }}
        .empty-card {{
            border: 1px dashed var(--border);
            background: #ffffff80;
            text-align: center;
            padding: 24px;
        }}
        .empty-emoji { font-size: 28px; margin-bottom: 8px; }
        .empty-actions {{ display:flex; gap:10px; justify-content:center; margin-top:12px; }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0C2430 0%, {PRIMARY_ACCENT} 65%, #0B1C22 100%);
            color: white;
        }}
        section[data-testid="stSidebar"] .block-container {{ padding-top: 12px; }}
        section[data-testid="stSidebar"] a {{ color: #d9f2f7; }}
        section[data-testid="stSidebar"] .sidebar-card {{
            border: 1px solid rgba(255,255,255,0.18);
            background: rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 8px 30px -20px rgba(0,0,0,0.5);
        }}
        .tab-icon {{ width: 16px; height: 16px; display: inline-block; vertical-align: middle; margin-right: 8px; }}
        /* Plotly tweaks */
        .js-plotly-plot .plotly .cartesianlayer .gridline {{ stroke: rgba(15,102,120,0.18); }}
        .js-plotly-plot .plotly .legend text {{ fill: {TEXT_MUTED}; font-weight: 600; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

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

    df = load_data()
    min_date = df[ColumnNames.TIMESTAMP_UTC.value].dt.date.min()
    max_date = df[ColumnNames.TIMESTAMP_UTC.value].dt.date.max()

    util_cols = st.columns([2.3, 1.4, 1.0, 1.2])
    with util_cols[0]:
        st.markdown(
            """
            <div id="utility-title" class="main-title">
                <span data-lucide="layout-dashboard" class="tab-icon"></span>
                AIRE Learner Scorecard
            </div>
            <div class="muted">Personalized view across your selected date range.</div>
            """,
            unsafe_allow_html=True,
        )
    with util_cols[1]:
        date_range = st.date_input(
            "Date range",
            (min_date, max_date),
            format="YYYY-MM-DD",
            key="date_range",
            help="Filter all charts and tables to this window.",
        )
    with util_cols[2]:
        view_mode = st.radio("View scope", ["Learner", "All"], horizontal=True, label_visibility="collapsed")
        st.markdown("<div class='muted' style='margin-top:4px;'>View toggle</div>", unsafe_allow_html=True)
    with util_cols[3]:
        action_cols = st.columns(3)
        with action_cols[0]:
            st.markdown(
                "<button class='icon-btn' title='Download'><span data-lucide='download-cloud'></span></button>",
                unsafe_allow_html=True,
            )
        with action_cols[1]:
            st.markdown(
                "<button class='icon-btn' title='Refresh'><span data-lucide='rotate-cw'></span></button>",
                unsafe_allow_html=True,
            )
        with action_cols[2]:
            st.markdown("<span class='pill'>Last updated: Feb 1, 2026</span>", unsafe_allow_html=True)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    df = df[df[ColumnNames.TIMESTAMP_UTC.value].dt.date.between(start_date, end_date)]

    # Sidebar branding
    st.sidebar.markdown(
        """
        <div style="padding-top:8px; font-family: 'Space Grotesk', sans-serif;">
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

    st.sidebar.markdown(
        """
        <div class="sidebar-card" style="margin-bottom: 10px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:34px; height:34px; border-radius:10px; background:rgba(255,255,255,0.12); display:grid; place-items:center; font-weight:700;">AL</div>
                <div>
                    <div style="font-weight:700;">Learner Mode</div>
                    <div style="font-size:12px; opacity:0.8;">Adaptive scorecard</div>
                </div>
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
    query_params = st.experimental_get_query_params()
    fixed_id = AIRE_FIXED_LEARNER_ID or query_params.get("learner_id", [default_id])[0]

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

    tab_labels = ["Overview", "Performance", "Assessments", "Actions", "Content", "Sessions"]
    tab_icons = ["layout-dashboard", "trending-up", "check-square", "book-open", "users", "bell-ring"]
    tabs = st.tabs(tab_labels)

    tab_icon_js = "[" + ",".join([f"'{icon}'" for icon in tab_icons]) + "]"
    st.markdown(
        f"""
        <script>
        const tabIcons = {tab_icon_js};
        setTimeout(() => {{
            const tabs = window.parent.document.querySelectorAll('div[data-testid="stTabs"] button p');
            tabs.forEach((el, idx) => {{
                if (!tabIcons[idx]) return;
                if (el.dataset.iconized === "1") return;
                const span = document.createElement('span');
                span.setAttribute('data-lucide', tabIcons[idx]);
                span.className = 'tab-icon';
                el.prepend(span);
                el.dataset.iconized = "1";
            }});
            if (window.lucide) lucide.createIcons();
        }}, 150);
        </script>
        """,
        unsafe_allow_html=True,
    )

    scope_df = learner_df if view_mode == "Learner" else df
    scope_summary = learner_summary(scope_df)

    # Overview tab
    with tabs[0]:
        kpi_cols = st.columns(3)
        kpi_data = [
            ("Total Interactions", scope_summary["events"], "activity", "Interactions in range"),
            ("Resources Accessed", scope_summary["resources"], "book-open", "Unique resources touched"),
            ("Avg Evaluation Score", f"{scope_summary['avg_score']:.2f}", "circle-check", "Mean score"),
        ]
        for col, (label, val, icon, caption) in zip(kpi_cols, kpi_data):
            with col:
                render_card(
                    label,
                    icon,
                    lambda v=val, c=caption: (
                        st.markdown(f"<div class='kpi-number'>{v}</div>", unsafe_allow_html=True),
                        st.markdown(f"<div class='kpi-label'>{c}</div>", unsafe_allow_html=True),
                        st.markdown(
                            "<div class='chip-row'><span class='chip'>Filtered</span><span class='chip'>Active learner</span></div>",
                            unsafe_allow_html=True,
                        ),
                    ),
                )

        col_a, col_b = st.columns([2, 1])
        with col_a:
            render_card(
                "Score trend",
                "trending-up",
                lambda: (
                    st.markdown("Steady ups mean new habits are sticking.", unsafe_allow_html=True),
                    st.plotly_chart(score_trend_chart(scope_df), use_container_width=True),
                    st.markdown(
                        "<div class='chip-row'><span class='chip'>Line</span><span class='chip'>Markers</span></div>",
                        unsafe_allow_html=True,
                    ),
                ),
            )
        with col_b:
            render_card(
                "Quick tips",
                "info",
                lambda: (
                    st.markdown("<div class='muted'>Most relevant next actions.</div>", unsafe_allow_html=True),
                    [st.info(rec) for rec in get_recommendations(learner_df)],
                ),
            )

        render_card(
            "Insight",
            "lightbulb",
            lambda: st.markdown(
                "<strong>Keep a balanced mix:</strong> alternate resource types to lift consistency and avoid weak spots compounding.",
                unsafe_allow_html=True,
            ),
        )

    # Performance tab
    with tabs[1]:
        perf_cols = st.columns(3)
        bounce = bounce_back_prompts(learner_df)
        perf_metrics = [
            ("Steady progress", f"{consistency_score(learner_df):.2f} std dev", "activity"),
            ("Bounce-back speed", f"{bounce:.1f} prompts" if bounce else "No dips yet", "rotate-cw"),
            ("Goal tracker", "", "flag"),
        ]
        target_score = st.slider("Target average score", 3.0, 5.0, 4.2, 0.1)
        target_interactions = st.slider("How many recent prompts to track", 5, 30, 10, 1)
        current_avg, remaining = goal_progress(learner_df, target_score, target_interactions)

        for idx, col in enumerate(perf_cols):
            label, value, icon = perf_metrics[idx]
            with col:
                if label == "Goal tracker":
                    value = f"{current_avg:.2f} / {target_score}"
                    delta = f"{remaining} prompts left"
                else:
                    delta = None
                def body(val=value, d=delta):
                    st.markdown(f"<div class='kpi-number'>{val}</div>", unsafe_allow_html=True)
                    if d:
                        st.markdown(f"<div class='kpi-label'>{d}</div>", unsafe_allow_html=True)
                render_card(label, icon, body)

        chart_cols = st.columns([2, 1])
        with chart_cols[0]:
            render_card(
                "Aggregate score trend",
                "area-chart",
                lambda: st.plotly_chart(aggregate_score_trend_chart(df), use_container_width=True),
            )
        with chart_cols[1]:
            render_card(
                "Best time of day",
                "clock",
                lambda: st.plotly_chart(best_time_chart(learner_df), use_container_width=True),
            )

    # Assessments tab
    with tabs[2]:
        render_card(
            "Weakness decay",
            "line-chart",
            lambda: st.plotly_chart(weakness_decay_chart(learner_df), use_container_width=True),
        )
        render_card(
            "Micro skill heatmap",
            "grid-2x2",
            lambda: st.plotly_chart(micro_skill_heatmap(learner_df), use_container_width=True),
        )
        dips = surprise_dips(learner_df)
        if dips.empty:
            render_empty_card("Surprise dips", "No big drops found—keep it up!")
        else:
            render_card("Surprise dips", "bell-ring", lambda: st.dataframe(dips))

    # Actions tab
    with tabs[3]:
        render_card(
            "Resource engagement",
            "bar-chart-3",
            lambda: st.plotly_chart(resource_usage_chart(learner_df), use_container_width=True),
        )
        effects = resource_effect(learner_df)
        if effects.empty:
            render_empty_card("What helped most", "Not enough data yet.", icon="folder-x")
        else:
            render_card(
                "What helped most",
                "sparkles",
                lambda: st.dataframe(effects),
            )

        acted = acted_on_feedback(learner_df)
        if acted.empty:
            render_empty_card("Follow-through", "No immediate follow-through recorded yet.", icon="info")
        else:
            render_card("Follow-through", "check-square", lambda: st.dataframe(acted))

    # Content tab (prompt crafting & variety)
    with tabs[4]:
        render_card(
            "Prompt length vs score",
            "ruler",
            lambda: st.plotly_chart(prompt_length_scatter(learner_df), use_container_width=True),
        )
        render_card(
            "Practice variety",
            "layout-grid",
            lambda: st.plotly_chart(practice_variety_chart(learner_df), use_container_width=True),
        )

    # Sessions tab
    with tabs[5]:
        recent = recent_sessions(learner_df)
        if recent.empty:
            render_empty_card("Recent sessions", "No sessions in this date range.", icon="calendar-range")
        else:
            render_card("Recent sessions", "calendar-range", lambda: st.dataframe(recent))


if __name__ == "__main__":
    main()

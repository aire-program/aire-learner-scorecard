"""
Unified chart styling for AIRE Learner Scorecard.
Mirrors the canonical design vocabulary from AIRE Impact Dashboard.
"""

import plotly.graph_objects as go

# Canonical AIRE color palette
PALETTE = {
    "primary": "#09728B",
    "primary_dark": "#066F91",
    "accent": "#0BA6C5",
    "muted": "#5A6A73",
    "soft": "#E6F3F7",
    "warning": "#B47515",
}

COLORWAY = [PALETTE["primary"], PALETTE["accent"], "#0A4D64", "#7C3F87", "#4A4A4A"]


def apply_layout_defaults(fig: go.Figure, title: str = "") -> go.Figure:
    """
    Apply consistent layout styling to a Plotly figure.
    Matches the AIRE Impact Dashboard design vocabulary.
    """
    fig.update_layout(
        title=title,
        template="plotly_white",
        colorway=COLORWAY,
        margin=dict(l=20, r=20, t=60, b=20),
        hoverlabel=dict(bgcolor="white"),
        plot_bgcolor="#f9fbfd",
        paper_bgcolor="#f9fbfd",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor="#d8e3ea",
            title_font=dict(size=12),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#dfe9ef",
            zeroline=False,
            title_font=dict(size=12),
        ),
        font=dict(color=PALETTE["primary_dark"]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            x=0,
            font=dict(size=11),
        ),
    )
    return fig

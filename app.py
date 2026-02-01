from __future__ import annotations

import os
from datetime import datetime
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

# Design tokens
TOKENS = {
    "accent": "#0F6678",
    "accent_secondary": "#1BA3BC",
    "surface": "#0B1C22",
    "muted": "#5A6B70",
    "border": "#D6E5E8",
    "card_bg": "#F7FBFC",
    "success": "#3CBF8A",
    "warn": "#F5A524",
    "shadow_elevated": "0 10px 30px -18px rgba(15,102,120,0.35)",
}

# Chart color scheme
CHART_COLORS = {
    "primary": "#0F6678",
    "secondary": "#1BA3BC",
    "neutral": "#B8C4C8",
    "area_fill": "rgba(15, 102, 120, 0.3)",
}


def get_custom_css() -> str:
    """Return the custom CSS for the entire application."""
    return f"""
    <style>
    /* ===== CSS TOKENS ===== */
    :root {{
        --accent: {TOKENS['accent']};
        --accent-secondary: {TOKENS['accent_secondary']};
        --surface: {TOKENS['surface']};
        --muted: {TOKENS['muted']};
        --border: {TOKENS['border']};
        --card-bg: {TOKENS['card_bg']};
        --success: {TOKENS['success']};
        --warn: {TOKENS['warn']};
        --shadow-elevated: {TOKENS['shadow_elevated']};
    }}

    /* ===== GLOBAL STYLES ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    /* Typography hierarchy */
    h1 {{
        font-size: 28px !important;
        font-weight: 700 !important;
        color: var(--surface) !important;
        line-height: 1.2 !important;
    }}
    
    h2, .stSubheader {{
        font-size: 20px !important;
        font-weight: 600 !important;
        color: var(--surface) !important;
    }}
    
    p, .stMarkdown {{
        font-size: 14px !important;
        font-weight: 400 !important;
        color: var(--surface) !important;
    }}
    
    .stCaption, caption {{
        font-size: 12px !important;
        font-weight: 500 !important;
        color: var(--muted) !important;
    }}

    /* ===== SIDEBAR POLISH ===== */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0C2430 0%, #0F6678 60%, #0B1C22 100%) !important;
        padding-top: 0 !important;
    }}
    
    section[data-testid="stSidebar"] > div:first-child {{
        padding-top: 4px !important;
        margin-top: 0 !important;
    }}
    
    section[data-testid="stSidebar"] .block-container {{
        padding-top: 0 !important;
        margin-top: 0 !important;
    }}
    
    section[data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255,255,255,0.15) !important;
        margin: 12px 0 !important;
    }}
    
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {{
        font-size: 14px !important;
        font-weight: 600 !important;
    }}
    
    /* Sidebar nav link styling */
    section[data-testid="stSidebar"] .nav-link {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        color: rgba(255,255,255,0.85) !important;
        text-decoration: none;
        transition: all 180ms ease;
        margin: 2px 0;
    }}
    
    section[data-testid="stSidebar"] .nav-link:hover {{
        background: rgba(255,255,255,0.1);
        color: #FFFFFF !important;
    }}
    
    section[data-testid="stSidebar"] .nav-link.active {{
        background: rgba(255,255,255,0.15);
        color: #FFFFFF !important;
    }}
    
    section[data-testid="stSidebar"] .nav-divider {{
        height: 1px;
        background: rgba(255,255,255,0.1);
        margin: 8px 0;
    }}

    /* ===== CARD STYLES ===== */
    .aire-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 14px;
        box-shadow: var(--shadow-elevated);
        padding: 18px 24px;
        transition: transform 180ms ease, box-shadow 180ms ease;
        margin-bottom: 16px;
        animation: fadeRise 400ms ease-out;
    }}
    
    .aire-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 14px 40px -15px rgba(15,102,120,0.45);
    }}
    
    .aire-card:active {{
        transform: scale(0.995);
    }}
    
    .aire-card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border);
    }}
    
    .aire-card-title {{
        font-size: 16px;
        font-weight: 600;
        color: var(--surface);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    
    .aire-card-actions {{
        display: flex;
        gap: 8px;
    }}
    
    .aire-card-footer {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid var(--border);
        font-size: 12px;
        color: var(--muted);
    }}
    
    .aire-card-body {{
        min-height: 60px;
    }}

    /* ===== KPI CARDS ===== */
    .kpi-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 14px;
        box-shadow: var(--shadow-elevated);
        padding: 20px 24px;
        text-align: center;
        transition: transform 180ms ease, box-shadow 180ms ease;
        animation: fadeRise 400ms ease-out;
    }}
    
    .kpi-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 14px 40px -15px rgba(15,102,120,0.45);
    }}
    
    .kpi-number {{
        font-size: 36px;
        font-weight: 700;
        color: var(--accent);
        line-height: 1.1;
        margin-bottom: 4px;
    }}
    
    .kpi-label {{
        font-size: 13px;
        font-weight: 500;
        color: var(--muted);
        margin-bottom: 8px;
    }}
    
    .kpi-secondary {{
        font-size: 12px;
        color: var(--muted);
        opacity: 0.8;
    }}

    /* ===== BUTTONS ===== */
    .aire-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 180ms ease;
        border: none;
        outline: none;
    }}
    
    .aire-btn-primary {{
        background: var(--accent);
        color: #FFFFFF;
    }}
    
    .aire-btn-primary:hover {{
        background: #0D5A6A;
    }}
    
    .aire-btn-primary:active {{
        background: #0A4D5B;
    }}
    
    .aire-btn-primary:focus {{
        box-shadow: 0 0 0 3px rgba(15, 102, 120, 0.3);
    }}
    
    .aire-btn-ghost {{
        background: transparent;
        color: var(--accent);
        border: 1px solid var(--border);
    }}
    
    .aire-btn-ghost:hover {{
        background: rgba(15, 102, 120, 0.08);
    }}
    
    .aire-btn-icon {{
        width: 32px;
        height: 32px;
        padding: 0;
        border-radius: 8px;
        background: transparent;
        color: var(--muted);
        border: 1px solid transparent;
    }}
    
    .aire-btn-icon:hover {{
        background: rgba(15, 102, 120, 0.08);
        color: var(--accent);
        border-color: var(--border);
    }}

    /* ===== CHIPS & PILLS ===== */
    .aire-chip {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 500;
        background: rgba(15, 102, 120, 0.1);
        color: var(--accent);
    }}
    
    .aire-pill {{
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
    }}
    
    .aire-pill-success {{
        background: rgba(60, 191, 138, 0.15);
        color: var(--success);
    }}
    
    .aire-pill-warn {{
        background: rgba(245, 165, 36, 0.15);
        color: var(--warn);
    }}
    
    .aire-pill-neutral {{
        background: rgba(90, 107, 112, 0.15);
        color: var(--muted);
    }}

    /* ===== HEADER UTILITY ROW ===== */
    .header-utility {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 0;
        margin-bottom: 20px;
        border-bottom: 1px solid var(--border);
    }}
    
    .header-left {{
        display: flex;
        flex-direction: column;
        gap: 4px;
    }}
    
    .header-title {{
        font-size: 28px;
        font-weight: 700;
        color: var(--surface);
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }}
    
    .header-context {{
        font-size: 14px;
        color: var(--muted);
    }}
    
    .header-right {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .header-updated {{
        font-size: 12px;
        color: var(--muted);
    }}

    /* ===== EMPTY STATES ===== */
    .empty-state {{
        background: var(--card-bg);
        border: 2px dashed var(--border);
        border-radius: 14px;
        padding: 40px 24px;
        text-align: center;
        animation: fadeRise 400ms ease-out;
    }}
    
    .empty-state-icon {{
        font-size: 48px;
        margin-bottom: 16px;
        opacity: 0.6;
    }}
    
    .empty-state-text {{
        font-size: 14px;
        color: var(--muted);
        margin-bottom: 20px;
    }}
    
    .empty-state-actions {{
        display: flex;
        justify-content: center;
        gap: 12px;
    }}

    /* ===== ERROR STATES ===== */
    .error-state {{
        background: rgba(245, 165, 36, 0.08);
        border: 1px solid rgba(245, 165, 36, 0.3);
        border-radius: 14px;
        padding: 20px 24px;
        display: flex;
        align-items: center;
        gap: 16px;
    }}
    
    .error-state-icon {{
        color: var(--warn);
        flex-shrink: 0;
    }}
    
    .error-state-content {{
        flex: 1;
    }}
    
    .error-state-title {{
        font-size: 14px;
        font-weight: 600;
        color: var(--surface);
        margin-bottom: 4px;
    }}
    
    .error-state-message {{
        font-size: 13px;
        color: var(--muted);
    }}

    /* ===== SKELETON LOADERS ===== */
    .skeleton {{
        background: linear-gradient(90deg, #e8eef0 25%, #f7fbfc 50%, #e8eef0 75%);
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
        border-radius: 8px;
    }}
    
    .skeleton-text {{
        height: 14px;
        margin-bottom: 8px;
    }}
    
    .skeleton-title {{
        height: 24px;
        width: 60%;
        margin-bottom: 12px;
    }}
    
    .skeleton-chart {{
        height: 200px;
    }}
    
    .skeleton-kpi {{
        height: 80px;
    }}

    /* ===== ANIMATIONS ===== */
    @keyframes fadeRise {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    @keyframes shimmer {{
        0% {{
            background-position: -200% 0;
        }}
        100% {{
            background-position: 200% 0;
        }}
    }}

    /* ===== INSIGHT CALLOUT ===== */
    .insight-callout {{
        background: linear-gradient(135deg, rgba(15, 102, 120, 0.08) 0%, rgba(27, 163, 188, 0.08) 100%);
        border: 1px solid var(--accent);
        border-left: 4px solid var(--accent);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: flex-start;
        gap: 16px;
        animation: fadeRise 400ms ease-out;
    }}
    
    .insight-callout-icon {{
        color: var(--accent);
        flex-shrink: 0;
        margin-top: 2px;
    }}
    
    .insight-callout-content {{
        flex: 1;
    }}
    
    .insight-callout-title {{
        font-size: 15px;
        font-weight: 600;
        color: var(--surface);
        margin-bottom: 6px;
    }}
    
    .insight-callout-text {{
        font-size: 13px;
        color: var(--muted);
        line-height: 1.5;
    }}

    /* ===== PROFILE MICRO-CARD ===== */
    .profile-card {{
        background: rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 14px 16px;
        margin-top: 20px;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .profile-avatar {{
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: var(--accent);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        font-weight: 600;
        color: #FFFFFF;
    }}
    
    .profile-info {{
        flex: 1;
    }}
    
    .profile-name {{
        font-size: 14px;
        font-weight: 600;
        color: #FFFFFF;
        margin-bottom: 2px;
    }}
    
    .profile-role {{
        font-size: 11px;
        color: rgba(255,255,255,0.7);
    }}

    /* ===== TAB STYLING ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 12px 20px;
        font-size: 14px;
        font-weight: 500;
        color: var(--muted);
        border-radius: 8px 8px 0 0;
        border: none;
        background: transparent;
        transition: all 180ms ease;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        color: var(--accent);
        background: rgba(15, 102, 120, 0.05);
    }}
    
    .stTabs [aria-selected="true"] {{
        color: var(--accent) !important;
        background: var(--card-bg) !important;
        border: 1px solid var(--border) !important;
        border-bottom: 1px solid var(--card-bg) !important;
        margin-bottom: -1px;
    }}

    /* ===== METRICS OVERRIDE ===== */
    [data-testid="stMetricValue"] {{
        font-size: 28px !important;
        font-weight: 700 !important;
        color: var(--accent) !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: var(--muted) !important;
    }}
    
    [data-testid="stMetricDelta"] {{
        font-size: 12px !important;
    }}

    /* ===== DATAFRAME STYLING ===== */
    .stDataFrame {{
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }}
    
    .stDataFrame thead th {{
        background: var(--card-bg) !important;
        font-weight: 600 !important;
        color: var(--surface) !important;
        font-size: 13px !important;
    }}
    
    .stDataFrame tbody td {{
        font-size: 13px !important;
        color: var(--surface) !important;
    }}

    /* ===== EXPANDER STYLING ===== */
    .streamlit-expanderHeader {{
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--surface) !important;
        background: var(--card-bg) !important;
        border-radius: 12px !important;
    }}

    /* ===== SLIDER STYLING ===== */
    .stSlider [data-baseweb="slider"] {{
        margin-top: 8px;
    }}
    
    .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {{
        color: var(--accent) !important;
        font-weight: 600 !important;
    }}

    /* ===== INFO/WARNING BOXES ===== */
    .stAlert {{
        border-radius: 12px !important;
        border: none !important;
    }}
    
    div[data-baseweb="notification"] {{
        border-radius: 12px !important;
    }}
    </style>
    """


def get_lucide_script() -> str:
    """Return the Lucide icons CDN script."""
    return """
    <script src="https://unpkg.com/lucide@latest/dist/umd/lucide.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        });
        // Re-run on Streamlit rerenders
        setTimeout(function() {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }, 100);
    </script>
    """


def render_card(title: str, content: str, icon: str = "", footer: str = "", show_actions: bool = True) -> str:
    """Render a styled card component."""
    actions_html = ""
    if show_actions:
        actions_html = """
        <div class="aire-card-actions">
            <button class="aire-btn aire-btn-icon" title="Refresh">
                <i data-lucide="rotate-cw" style="width:16px;height:16px;"></i>
            </button>
            <button class="aire-btn aire-btn-icon" title="Download">
                <i data-lucide="download-cloud" style="width:16px;height:16px;"></i>
            </button>
        </div>
        """
    
    icon_html = f'<i data-lucide="{icon}" style="width:18px;height:18px;color:var(--accent);"></i>' if icon else ""
    footer_html = f'<div class="aire-card-footer">{footer}</div>' if footer else ""
    
    return f"""
    <div class="aire-card">
        <div class="aire-card-header">
            <h3 class="aire-card-title">{icon_html} {title}</h3>
            {actions_html}
        </div>
        <div class="aire-card-body">
            {content}
        </div>
        {footer_html}
    </div>
    """


def render_kpi_card(value: str, label: str, secondary: str = "", icon: str = "") -> str:
    """Render a KPI card component."""
    icon_html = f'<i data-lucide="{icon}" style="width:24px;height:24px;color:var(--accent);margin-bottom:8px;"></i>' if icon else ""
    secondary_html = f'<div class="kpi-secondary">{secondary}</div>' if secondary else ""
    
    return f"""
    <div class="kpi-card">
        {icon_html}
        <div class="kpi-number">{value}</div>
        <div class="kpi-label">{label}</div>
        {secondary_html}
    </div>
    """


def render_empty_state(message: str, emoji: str = "📊", hint: str = "", primary_action: str = "Add data", secondary_action: str = "Learn how") -> str:
    """Render an empty state component."""
    return f"""
    <div class="empty-state">
        <div class="empty-state-icon">{emoji}</div>
        <div class="empty-state-text">{message}</div>
        {f'<p style="font-size:12px;color:var(--muted);margin-bottom:16px;">{hint}</p>' if hint else ''}
        <div class="empty-state-actions">
            <button class="aire-btn aire-btn-primary">{primary_action}</button>
            <button class="aire-btn aire-btn-ghost">{secondary_action}</button>
        </div>
    </div>
    """


def render_error_state(title: str, message: str, show_retry: bool = True) -> str:
    """Render an error state component."""
    retry_html = '<button class="aire-btn aire-btn-primary" style="margin-top:12px;">Retry</button>' if show_retry else ""
    return f"""
    <div class="error-state">
        <div class="error-state-icon">
            <i data-lucide="triangle-alert" style="width:24px;height:24px;"></i>
        </div>
        <div class="error-state-content">
            <div class="error-state-title">{title}</div>
            <div class="error-state-message">{message}</div>
            {retry_html}
        </div>
    </div>
    """


def render_insight_callout(title: str, text: str, icon: str = "info") -> str:
    """Render an insight callout component."""
    return f"""
    <div class="insight-callout">
        <div class="insight-callout-icon">
            <i data-lucide="{icon}" style="width:20px;height:20px;"></i>
        </div>
        <div class="insight-callout-content">
            <div class="insight-callout-title">{title}</div>
            <div class="insight-callout-text">{text}</div>
        </div>
    </div>
    """


def render_header_utility(title: str, context: str, tab_icon: str = "layout-dashboard") -> str:
    """Render the header utility row."""
    current_date = datetime.now().strftime("%b %d, %Y")
    return f"""
    <div class="header-utility">
        <div class="header-left">
            <h1 class="header-title">
                <i data-lucide="{tab_icon}" style="width:28px;height:28px;color:var(--accent);"></i>
                {title}
            </h1>
            <div class="header-context">{context}</div>
        </div>
        <div class="header-right">
            <button class="aire-btn aire-btn-ghost">
                <i data-lucide="calendar-range" style="width:14px;height:14px;"></i>
                Last 30 days
            </button>
            <button class="aire-btn aire-btn-icon" title="Filter">
                <i data-lucide="filter" style="width:16px;height:16px;"></i>
            </button>
            <button class="aire-btn aire-btn-icon" title="Download">
                <i data-lucide="download-cloud" style="width:16px;height:16px;"></i>
            </button>
            <button class="aire-btn aire-btn-icon" title="Refresh">
                <i data-lucide="rotate-cw" style="width:16px;height:16px;"></i>
            </button>
            <span class="header-updated">Last updated: {current_date}</span>
        </div>
    </div>
    """


def render_profile_card(learner_id: str) -> str:
    """Render the profile micro-card for sidebar."""
    initials = learner_id[:2].upper() if learner_id else "??"
    return f"""
    <div class="profile-card">
        <div class="profile-avatar">{initials}</div>
        <div class="profile-info">
            <div class="profile-name">{learner_id}</div>
            <div class="profile-role">Learner</div>
        </div>
        <span class="aire-pill aire-pill-success">Active</span>
    </div>
    """


def render_sidebar_nav() -> str:
    """Render the sidebar navigation with icons."""
    return """
    <div style="margin: 16px 0;">
        <div class="nav-divider"></div>
        <div style="padding: 8px 0; font-size: 11px; font-weight: 600; text-transform: uppercase; color: rgba(255,255,255,0.5); letter-spacing: 0.5px;">
            Navigation
        </div>
        <a href="#" class="nav-link active">
            <i data-lucide="layout-dashboard" style="width:16px;height:16px;"></i>
            Overview
        </a>
        <a href="#" class="nav-link">
            <i data-lucide="trending-up" style="width:16px;height:16px;"></i>
            Performance
        </a>
        <a href="#" class="nav-link">
            <i data-lucide="users" style="width:16px;height:16px;"></i>
            Learners
        </a>
        <a href="#" class="nav-link">
            <i data-lucide="book-open" style="width:16px;height:16px;"></i>
            Content
        </a>
        <div class="nav-divider"></div>
        <a href="#" class="nav-link">
            <i data-lucide="check-square" style="width:16px;height:16px;"></i>
            Assessments
        </a>
        <a href="#" class="nav-link">
            <i data-lucide="bell-ring" style="width:16px;height:16px;"></i>
            Alerts
        </a>
        <a href="#" class="nav-link">
            <i data-lucide="sliders-horizontal" style="width:16px;height:16px;"></i>
            Settings
        </a>
    </div>
    """


def apply_chart_styling(fig: go.Figure, chart_type: str = "line") -> go.Figure:
    """Apply consistent styling to Plotly charts."""
    fig.update_layout(
        font_family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        font_size=12,
        font_color=TOKENS["muted"],
        title_font_size=16,
        title_font_color=TOKENS["surface"],
        title_font_family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
        title_x=0,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=TOKENS["muted"]),
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter",
            bordercolor=TOKENS["border"],
        ),
    )
    
    # Reduce gridlines
    fig.update_xaxes(
        showgrid=False,
        linecolor=TOKENS["border"],
        tickfont=dict(size=11, color=TOKENS["muted"]),
        title_font=dict(size=12, color=TOKENS["muted"]),
    )
    
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(214, 229, 232, 0.5)",
        gridwidth=1,
        linecolor=TOKENS["border"],
        tickfont=dict(size=11, color=TOKENS["muted"]),
        title_font=dict(size=12, color=TOKENS["muted"]),
        rangemode="tozero" if chart_type == "bar" else "normal",
    )
    
    return fig


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
    """Plot evaluation score over time with enhanced styling."""
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
    
    # Update line styling
    fig.update_traces(
        line=dict(color=CHART_COLORS["primary"], width=2),
        marker=dict(size=6, color=CHART_COLORS["primary"]),
        fill="tozeroy",
        fillcolor=CHART_COLORS["area_fill"],
    )
    
    return apply_chart_styling(fig, "line")


def resource_usage_chart(df: pd.DataFrame) -> go.Figure:
    """Plot usage by resource ID with enhanced styling."""
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
    
    # Update bar styling - rounded bars effect
    fig.update_traces(
        marker_color=CHART_COLORS["primary"],
        marker_line_width=0,
    )
    
    return apply_chart_styling(fig, "bar")


def prompt_length_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter of prompt length vs score with enhanced styling."""
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
    
    fig.update_traces(
        marker=dict(
            color=CHART_COLORS["primary"],
            size=8,
            opacity=0.7,
            line=dict(width=1, color="white"),
        )
    )
    
    return apply_chart_styling(fig, "scatter")


def practice_variety_chart(df: pd.DataFrame) -> go.Figure:
    """Distribution of resource usage."""
    return resource_usage_chart(df)


def best_time_chart(df: pd.DataFrame) -> go.Figure:
    """Best time to work by hour-of-day scores with enhanced styling."""
    hours = df.copy()
    hours["hour"] = hours[ColumnNames.TIMESTAMP_UTC.value].dt.hour
    agg = hours.groupby("hour")[ColumnNames.EVALUATION_SCORE.value].mean().reset_index()
    fig = px.bar(
        agg,
        x="hour",
        y=ColumnNames.EVALUATION_SCORE.value,
        labels={"hour": "Hour of day", ColumnNames.EVALUATION_SCORE.value: "Avg score"},
        title="When You Usually Do Your Best",
    )
    
    fig.update_traces(
        marker_color=CHART_COLORS["secondary"],
        marker_line_width=0,
    )
    
    return apply_chart_styling(fig, "bar")


def aggregate_score_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Plot average evaluation score over time (daily) with enhanced styling."""
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
    
    fig.update_traces(
        line=dict(color=CHART_COLORS["primary"], width=2),
        marker=dict(size=6, color=CHART_COLORS["primary"]),
        fill="tozeroy",
        fillcolor=CHART_COLORS["area_fill"],
    )
    
    return apply_chart_styling(fig, "line")


def weakness_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Plot distribution of primary weaknesses with enhanced styling."""
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
    
    fig.update_traces(
        marker_color=CHART_COLORS["primary"],
        marker_line_width=0,
    )
    
    return apply_chart_styling(fig, "bar")


def weakness_decay_chart(df: pd.DataFrame) -> go.Figure:
    """Rolling share of weaknesses over last 30 days with enhanced styling."""
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
        color_discrete_sequence=[CHART_COLORS["primary"], CHART_COLORS["secondary"], CHART_COLORS["neutral"], "#E8B4BC", "#B4D4E8"],
    )
    fig.update_layout(legend_title_text="Weakness")
    
    return apply_chart_styling(fig, "area")


def micro_skill_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap of rubric dimensions by session order with enhanced styling."""
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
        color_continuous_scale=[
            [0, "#F7FBFC"],
            [0.5, CHART_COLORS["secondary"]],
            [1, CHART_COLORS["primary"]],
        ],
    )
    fig.update_yaxes(ticktext=["Clarity", "Context", "Constraints", "Overall"], tickvals=list(range(4)))
    
    return apply_chart_styling(fig, "heatmap")


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
    
    # Inject custom CSS and Lucide icons
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    st.markdown(get_lucide_script(), unsafe_allow_html=True)

    df = load_data()

    # ===== SIDEBAR =====
    st.sidebar.markdown(
        """
        <div style="padding: 16px 0 8px 0; font-family: 'Inter', sans-serif;">
            <div style="font-size: 28px; font-weight: 700; line-height: 1.1; margin-bottom: 4px; color: #FFFFFF;">
                AIRE
            </div>
            <div style="font-size: 12px; font-weight: 500; line-height: 1.3; color: rgba(255,255,255,0.7);">
                Applied AI Innovation and<br/>Research Enablement
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render sidebar navigation
    st.sidebar.markdown(render_sidebar_nav(), unsafe_allow_html=True)

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
        st.sidebar.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)
        st.sidebar.markdown(
            '<div style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: rgba(255,255,255,0.5); letter-spacing: 0.5px; padding: 8px 0;">Dev Mode</div>',
            unsafe_allow_html=True,
        )
        selected_learner = st.sidebar.selectbox("Select Learner ID", learners, index=learners.index(fixed_id))
    else:
        selected_learner = fixed_id

    learner_df = df[df[ColumnNames.LEARNER_ID.value] == selected_learner]
    summary = learner_summary(learner_df)

    # Profile micro-card at bottom of sidebar
    st.sidebar.markdown('<div style="flex-grow: 1;"></div>', unsafe_allow_html=True)
    st.sidebar.markdown(render_profile_card(selected_learner), unsafe_allow_html=True)
    
    # GitHub link
    st.sidebar.markdown(
        """
        <div style="margin-top: 16px; padding: 12px 0; border-top: 1px solid rgba(255,255,255,0.1);">
            <a href="https://github.com/aire-program/aire-learner-scorecard" target="_blank" 
               style="display: flex; align-items: center; gap: 8px; color: rgba(255,255,255,0.7); text-decoration: none; font-size: 12px;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
                </svg>
                Contribute on GitHub
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== MAIN CONTENT =====
    tabs = st.tabs([
        "📊 Overview",
        "📈 Performance",
        "🎯 Skills",
        "⚡ Actions",
        "✍️ Prompts",
        "📋 Sessions",
    ])

    # ===== OVERVIEW TAB =====
    with tabs[0]:
        # Header utility row
        st.markdown(
            render_header_utility(
                "Quick View",
                "A fast snapshot of how you're doing today",
                "layout-dashboard"
            ),
            unsafe_allow_html=True,
        )
        
        # Full-width insight callout
        if summary["avg_score"] >= 4.0:
            st.markdown(
                render_insight_callout(
                    "🎉 Great Progress!",
                    f"Your average score of {summary['avg_score']:.2f} is excellent. Keep up the consistent practice to maintain this momentum.",
                    "circle-check"
                ),
                unsafe_allow_html=True,
            )
        elif summary["avg_score"] < 3.0:
            st.markdown(
                render_insight_callout(
                    "💡 Room for Growth",
                    "Your scores show opportunity for improvement. Focus on the recommendations below to boost your performance.",
                    "info"
                ),
                unsafe_allow_html=True,
            )
        
        # KPI row - three equal cards
        kpi_cols = st.columns(3)
        with kpi_cols[0]:
            st.markdown(
                render_kpi_card(
                    str(summary["events"]),
                    "Total Interactions",
                    f"+{min(summary['events'], 12)} this week",
                    "trending-up"
                ),
                unsafe_allow_html=True,
            )
        with kpi_cols[1]:
            st.markdown(
                render_kpi_card(
                    f"{summary['avg_score']:.2f}",
                    "Average Score",
                    "Out of 5.0",
                    "trending-up"
                ),
                unsafe_allow_html=True,
            )
        with kpi_cols[2]:
            st.markdown(
                render_kpi_card(
                    str(summary["resources"]),
                    "Resources Used",
                    "Unique resources accessed",
                    "book-open"
                ),
                unsafe_allow_html=True,
            )
        
        # 2:1 layout - Score trend vs Recommendations
        main_col, side_col = st.columns([2, 1])
        
        with main_col:
            st.markdown(
                render_card(
                    "Score Trend",
                    "",
                    "trending-up",
                    '<span class="aire-chip">Last 30 days</span>',
                    True
                ).replace('<div class="aire-card-body">', '<div class="aire-card-body" id="score-trend-chart">'),
                unsafe_allow_html=True,
            )
            st.plotly_chart(score_trend_chart(learner_df), use_container_width=True, key="overview_score_trend")
        
        with side_col:
            st.markdown(
                '<div class="aire-card"><div class="aire-card-header"><h3 class="aire-card-title"><i data-lucide="info" style="width:18px;height:18px;color:var(--accent);"></i> Quick Tips</h3></div><div class="aire-card-body">',
                unsafe_allow_html=True,
            )
            for rec in get_recommendations(learner_df):
                st.info(rec)
            st.markdown('</div></div>', unsafe_allow_html=True)

    # ===== PERFORMANCE TAB =====
    with tabs[1]:
        st.markdown(
            render_header_utility(
                "Performance & Stability",
                "Track your consistency and recovery patterns",
                "trending-up"
            ),
            unsafe_allow_html=True,
        )
        
        # Three KPI cards
        perf_cols = st.columns(3)
        
        with perf_cols[0]:
            consistency = consistency_score(learner_df)
            consistency_status = "Excellent" if consistency < 0.5 else "Good" if consistency < 1.0 else "Variable"
            st.markdown(
                render_kpi_card(
                    f"{consistency:.2f}",
                    "Consistency (Std Dev)",
                    f"Status: {consistency_status}",
                    "trending-up"
                ),
                unsafe_allow_html=True,
            )
        
        with perf_cols[1]:
            bounce = bounce_back_prompts(learner_df)
            st.markdown(
                render_kpi_card(
                    f"{bounce:.1f}" if bounce else "—",
                    "Bounce-back Speed",
                    "Prompts to recover" if bounce else "No dips yet",
                    "rotate-cw"
                ),
                unsafe_allow_html=True,
            )
        
        with perf_cols[2]:
            target_score = 4.0
            target_interactions = 10
            current_avg, remaining = goal_progress(learner_df, target_score, target_interactions)
            st.markdown(
                render_kpi_card(
                    f"{current_avg:.2f}",
                    "Current Average",
                    f"Target: {target_score} | {remaining} prompts left",
                    "check-square"
                ),
                unsafe_allow_html=True,
            )
        
        # Goal tracking sliders
        st.markdown("---")
        slider_col1, slider_col2 = st.columns(2)
        with slider_col1:
            target_score = st.slider("Target average score", 3.0, 5.0, 4.2, 0.1)
        with slider_col2:
            target_interactions = st.slider("Recent prompts to track", 5, 30, 10, 1)
        
        current_avg, remaining = goal_progress(learner_df, target_score, target_interactions)
        
        if current_avg >= target_score:
            st.markdown(
                render_insight_callout(
                    "🎯 Goal Achieved!",
                    f"You've reached your target of {target_score}! Consider setting a more ambitious goal.",
                    "circle-check"
                ),
                unsafe_allow_html=True,
            )

    # ===== SKILLS TAB =====
    with tabs[2]:
        st.markdown(
            render_header_utility(
                "Skill Weakness & Progress",
                "Identify areas for improvement and track your growth",
                "check-square"
            ),
            unsafe_allow_html=True,
        )
        
        # 2:1 layout
        chart_col, detail_col = st.columns([2, 1])
        
        with chart_col:
            st.plotly_chart(weakness_decay_chart(learner_df), use_container_width=True)
            st.plotly_chart(micro_skill_heatmap(learner_df), use_container_width=True)
        
        with detail_col:
            st.markdown(
                '<div class="aire-card"><div class="aire-card-header"><h3 class="aire-card-title"><i data-lucide="triangle-alert" style="width:18px;height:18px;color:var(--warn);"></i> Surprise Dips</h3></div><div class="aire-card-body">',
                unsafe_allow_html=True,
            )
            dips = surprise_dips(learner_df)
            if dips.empty:
                st.markdown(
                    render_empty_state(
                        "No big drops found",
                        "✨",
                        "Keep it up! Your scores are consistent.",
                        "View all",
                        "Tips"
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.dataframe(dips, use_container_width=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

    # ===== ACTIONS TAB =====
    with tabs[3]:
        st.markdown(
            render_header_utility(
                "Action → Outcome",
                "See the impact of your practice and recommendations",
                "trending-up"
            ),
            unsafe_allow_html=True,
        )
        
        # Full-width chart
        st.plotly_chart(resource_usage_chart(learner_df), use_container_width=True)
        
        # 2:1 layout for tables
        effects_col, acted_col = st.columns([2, 1])
        
        with effects_col:
            st.markdown(
                '<div class="aire-card"><div class="aire-card-header"><h3 class="aire-card-title"><i data-lucide="trending-up" style="width:18px;height:18px;color:var(--accent);"></i> What Helped Most</h3></div><div class="aire-card-body">',
                unsafe_allow_html=True,
            )
            effects = resource_effect(learner_df)
            if effects.empty:
                st.markdown(
                    render_empty_state(
                        "Not enough data yet",
                        "📊",
                        "Keep practicing to see which resources help most.",
                        "Add data",
                        "Learn how"
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.dataframe(effects, use_container_width=True)
            st.markdown('</div></div>', unsafe_allow_html=True)
        
        with acted_col:
            st.markdown(
                '<div class="aire-card"><div class="aire-card-header"><h3 class="aire-card-title"><i data-lucide="check-square" style="width:18px;height:18px;color:var(--success);"></i> Follow-through</h3></div><div class="aire-card-body">',
                unsafe_allow_html=True,
            )
            acted = acted_on_feedback(learner_df)
            if acted.empty:
                st.markdown(
                    render_empty_state(
                        "No immediate follow-through yet",
                        "🎯",
                        "Try using recommended resources right after feedback.",
                        "View tips",
                        "Learn more"
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.dataframe(acted, use_container_width=True)
            st.markdown('</div></div>', unsafe_allow_html=True)

    # ===== PROMPTS TAB =====
    with tabs[4]:
        st.markdown(
            render_header_utility(
                "Prompt Crafting Aids",
                "Optimize your prompt length and practice timing",
                "book-open"
            ),
            unsafe_allow_html=True,
        )
        
        # 2:1 layout
        main_chart_col, side_chart_col = st.columns([2, 1])
        
        with main_chart_col:
            st.plotly_chart(prompt_length_scatter(learner_df), use_container_width=True)
        
        with side_chart_col:
            st.markdown(
                render_insight_callout(
                    "💡 Prompt Tips",
                    "Longer prompts don't always mean better scores. Find your sweet spot by experimenting with different lengths.",
                    "info"
                ),
                unsafe_allow_html=True,
            )
        
        # Full width charts
        chart_row = st.columns(2)
        with chart_row[0]:
            st.plotly_chart(practice_variety_chart(learner_df), use_container_width=True)
        with chart_row[1]:
            st.plotly_chart(best_time_chart(learner_df), use_container_width=True)

    # ===== SESSIONS TAB =====
    with tabs[5]:
        st.markdown(
            render_header_utility(
                "Recent Sessions",
                "Review your latest practice sessions",
                "book-open"
            ),
            unsafe_allow_html=True,
        )
        
        sessions = recent_sessions(learner_df)
        if sessions.empty:
            st.markdown(
                render_empty_state(
                    "No sessions recorded yet",
                    "📋",
                    "Start practicing to see your session history here.",
                    "Get started",
                    "Learn more"
                ),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="aire-card"><div class="aire-card-header"><h3 class="aire-card-title"><i data-lucide="book-open" style="width:18px;height:18px;color:var(--accent);"></i> Session Log</h3><div class="aire-card-actions"><button class="aire-btn aire-btn-icon" title="Download"><i data-lucide="download-cloud" style="width:16px;height:16px;"></i></button></div></div><div class="aire-card-body">',
                unsafe_allow_html=True,
            )
            st.dataframe(sessions, use_container_width=True)
            st.markdown(
                '<div class="aire-card-footer"><span>Showing last 6 sessions</span><span class="aire-chip">All time</span></div></div></div>',
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()

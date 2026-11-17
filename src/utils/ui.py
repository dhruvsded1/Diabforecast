"""
Shared Streamlit UI Components, Styling, and Cached Data Loaders for DiabForecast.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, Optional, Tuple, List
import streamlit as st
import pandas as pd
import numpy as np

from src.utils.config import (
    PROCESSED_DATA_PATH,
    FORECASTS_2030_PATH,
    MODEL_EVALUATION_CSV,
    GBD_DATA_DIR,
)
from src.data.load_data import load_gbd_workbook

# Custom Deep Navy / Healthcare Teal CSS
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Global background */
    .stApp {
        background-color: #0B132B;
        color: #F8FAFC;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }
    
    /* KPI Metric Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px 22px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        margin-bottom: 15px;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .kpi-card:hover {
        border-color: #0D9488;
        transform: translateY(-2px);
    }
    .kpi-title {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #38BDF8;
        line-height: 1.2;
    }
    .kpi-subtitle {
        font-size: 0.78rem;
        color: #64748B;
        margin-top: 6px;
    }
    
    /* Medical Disclaimer Banner */
    .disclaimer-banner {
        background-color: rgba(13, 148, 136, 0.12);
        border-left: 4px solid #0D9488;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.85rem;
        color: #99F6E4;
        margin-bottom: 24px;
        line-height: 1.5;
    }
    
    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0B132B 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 26px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #F8FAFC;
        letter-spacing: -0.02em;
        margin-bottom: 8px;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(13, 148, 136, 0.2);
        color: #2DD4BF;
        border: 1px solid #0D9488;
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 12px;
    }
    .hero-desc {
        font-size: 1.05rem;
        color: #94A3B8;
        max-width: 850px;
        line-height: 1.6;
    }

    /* Section Headers */
    .section-header {
        font-size: 1.35rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 24px;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid #334155;
    }

    /* Streamlit Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E293B;
        border-radius: 8px 8px 0 0;
        color: #94A3B8;
        padding: 8px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0D9488 !important;
        color: #FFFFFF !important;
    }
</style>
"""


def apply_custom_theme():
    """Inject premium CSS styling into Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_disclaimer():
    """Display standardized epidemiological disclaimer banner."""
    html = """
    <div class="disclaimer-banner">
        <strong>⚠️ Population Epidemiological Notice:</strong> DiabForecast analyses country-level 
        World Health Organization (WHO) age-standardized diabetes prevalence estimates (adults aged 18+, both sexes). 
        This is a population-level epidemiological forecasting system; it does not diagnose individual patients, 
        estimate individual risk, or establish medical causality.
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_kpi_card(title: str, value: str, subtitle: str = ""):
    """Render a styled KPI metric card."""
    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-subtitle">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_processed_data() -> pd.DataFrame:
    """Load and cache processed WHO diabetes dataset."""
    return pd.read_csv(PROCESSED_DATA_PATH)


@st.cache_data(show_spinner=False)
def get_forecast_data() -> pd.DataFrame:
    """Load and cache 2023-2030 forecasts dataset."""
    return pd.read_csv(FORECASTS_2030_PATH)


@st.cache_data(show_spinner=False)
def get_evaluation_data() -> pd.DataFrame:
    """Load and cache chronological backtesting results."""
    return pd.read_csv(MODEL_EVALUATION_CSV)


@st.cache_data(show_spinner=False)
def get_gbd_workbook_cached(filename: str, sheet_name: int = 0) -> pd.DataFrame:
    """Load and cache GBD supplementary excel workbooks."""
    target = GBD_DATA_DIR / filename
    if not target.exists():
        return pd.DataFrame()
    return pd.read_excel(target, sheet_name=sheet_name)


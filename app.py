"""
DiabForecast — Global Diabetes Prevalence Analysis and Forecasting System.
Main Application Entry Point.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.utils.ui import (
    apply_custom_theme,
    render_disclaimer,
    render_kpi_card,
    get_processed_data,
    get_forecast_data,
    get_evaluation_data,
)
from src.visualization.maps import plot_global_choropleth
from src.visualization.charts import plot_historical_trend

# Configure Streamlit Application
st.set_page_config(
    page_title="DiabForecast — Global Diabetes Forecasting",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_theme()

# Sidebar Navigation Header
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 20px 0;">
    <h2 style="color: #38BDF8; margin: 0; font-weight: 800;">🩺 DiabForecast</h2>
    <p style="color: #94A3B8; font-size: 0.8rem; margin: 4px 0 0 0;">Global Health Intelligence System</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**System Version:** `v1.0.0 (Production)`  
**Data Sources:** WHO GHO & GBD 2023  
**Target Group:** Adults 18+, Both Sexes  
**Coverage:** 152 Sovereign Countries  
**Forecast Target:** 2030 Horizon  
""")
st.sidebar.markdown("---")

# Main Page Header Hero Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-badge">Epidemiological AI Intelligence Platform</div>
    <div class="hero-title">DiabForecast</div>
    <div style="font-size: 1.3rem; font-weight: 600; color: #38BDF8; margin-bottom: 12px;">
        Global Diabetes Prevalence Analysis & Forecasting System
    </div>
    <div class="hero-desc">
        A clinical-grade population healthcare analytics application analyzing 33 years of 
        World Health Organization (WHO) age-standardized historical prevalence (1990–2022) across 152 countries, 
        and projecting future trajectories through 2030 using machine learning and statistical time-series models.
    </div>
</div>
""", unsafe_allow_html=True)

render_disclaimer()

# Load Core Data
try:
    df_clean = get_processed_data()
    df_forecasts = get_forecast_data()
    df_eval = get_evaluation_data()
    data_loaded = True
except Exception as e:
    st.error(f"Error loading system data: {e}")
    data_loaded = False

if data_loaded:
    # Key Operational KPIs
    df_2022 = df_clean[df_clean["year"] == 2022]
    unweighted_mean_2022 = df_2022["prevalence_pct"].mean()
    highest_2022 = df_2022.sort_values("prevalence_pct", ascending=False).iloc[0]
    lowest_2022 = df_2022.sort_values("prevalence_pct", ascending=True).iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        render_kpi_card("Sovereign Locations", f"{df_clean['location'].nunique()}", "WHO geographic entities")
    with col2:
        render_kpi_card("Historical Horizon", "1990 – 2022", "33 annual observations")
    with col3:
        render_kpi_card("Unweighted Mean (2022)", f"{unweighted_mean_2022:.2f}%", "Cross-national average")
    with col4:
        render_kpi_card("Highest (2022)", f"{highest_2022['prevalence_pct']:.1f}%", f"{highest_2022['location']}")
    with col5:
        render_kpi_card("Lowest (2022)", f"{lowest_2022['prevalence_pct']:.1f}%", f"{lowest_2022['location']}")

    st.markdown("<div class='section-header'>Global Prevalence Landscape (Latest Observed: 2022)</div>", unsafe_allow_html=True)
    
    # Interactive Global Map
    fig_map = plot_global_choropleth(df_clean, year=2022)
    st.plotly_chart(fig_map, use_container_width=True)

    # System Architecture and Modules Guide
    st.markdown("<div class='section-header'>System Capabilities & Navigation Guide</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytic Modules", "🤖 ML Forecasting Architecture", "📐 Quality Assurance & Governance", "📖 About & Data Attribution"])
    
    with tab1:
        st.markdown("""
        Explore the system using the dedicated pages in the sidebar navigation:
        
        1. **Overview Dashboard (`1_Overview.py`):** Cross-sectional rankings, WHO regional distributions, and statistical aggregates.
        2. **Historical Trends (`2_Historical_Trends.py`):** 33-year trajectories with WHO 95% uncertainty ribbons, country comparisons, and filtered CSV downloads.
        3. **Forecast 2030 (`3_Forecast_2030.py`):** Core projection engine producing annual forecasts through 2030 across 4 algorithms with defensible prediction intervals.
        4. **Model Comparison (`4_Model_Comparison.py`):** Empirical out-of-sample backtesting (MAE, RMSE, MAPE, WAPE) benchmarking against a persistence baseline.
        5. **Country Comparison (`5_Country_Comparison.py`):** Multi-country cohort analysis, growth rate benchmarking, and ranking projections.
        6. **Disease Burden Context (`6_Disease_Burden.py`):** Macro-level disease burden (DALYs, PAFs, risk factors) from GBD 2023 reference workbooks.
        """)

    with tab2:
        st.markdown("""
        ### Four Machine Learning & Time-Series Algorithms
        - **Linear Regression:** Individual country trend estimation via ordinary least squares with t-distribution prediction intervals.
        - **ARIMA:** Non-seasonal autoregressive integrated moving average with AIC-optimized order selection and convergence fallbacks.
        - **Holt Exponential Smoothing:** Additive damped trend exponential smoothing to prevent explosive runaway projections.
        - **Random Forest Regressor:** Pooled cross-national non-linear tree ensemble with recursive autoregressive lag updating.
        
        *All models are evaluated on genuine out-of-sample backtesting (2018–2022) without target leakage or synthetic interpolation.*
        """)

    with tab3:
        st.markdown("""
        ### Strict Epidemiological Standards
        - **No Synthetic Slovenia Imputation:** Slovenia's 17 historical observations (2006–2022) are modeled strictly on observed empirical records.
        - **Separation of Uncertainty Measures:** WHO empirical measurement uncertainty intervals are strictly differentiated from model forecast prediction intervals.
        - **Metric Separation:** WHO country percentages are never conflated with GBD rates per 100,000 or DALY counts.
        - **Unweighted Metric Clarification:** Cross-national averages are explicitly presented as unweighted means, not global population-weighted prevalence.
        """)

    with tab4:
        st.markdown("""
        ### Primary Citation & Attribution
        - **Primary Data Source:** World Health Organization (WHO) Global Health Observatory (GHO).
        - **Indicator:** Age-standardized diabetes prevalence among adults aged 18+ years (`NCD_DIABETES_PREVALENCE_AGESTD`).
        - **Reference Framework:** Global Burden of Disease (GBD 2023) Study, Institute for Health Metrics and Evaluation (IHME).
        - **Core Methodology Reference:** *Enhancing AI-driven forecasting of diabetes burden: a comparative analysis of deep learning and statistical models* (2024).
        """)


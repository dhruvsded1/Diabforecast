"""
Page 1: Overview Dashboard — DiabForecast.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from src.utils.ui import (
    apply_custom_theme,
    render_disclaimer,
    render_kpi_card,
    get_processed_data,
)
from src.visualization.charts import (
    plot_historical_trend,
    plot_prevalence_distribution,
    plot_regional_comparison,
    plot_country_rankings,
)

st.set_page_config(page_title="Overview Dashboard | DiabForecast", page_icon="📊", layout="wide")
apply_custom_theme()

st.title("📊 Global Diabetes Overview Dashboard")
st.markdown("Macro-level cross-sectional and temporal landscape of age-standardized adult diabetes prevalence.")
render_disclaimer()

df = get_processed_data()

# Year selector for cross-sectional views
col_sel1, col_sel2 = st.columns([2, 4])
with col_sel1:
    selected_year = st.slider("Select Analysis Benchmark Year", min_value=1990, max_value=2022, value=2022, step=1)

df_yr = df[df["year"] == selected_year]

# KPIs for Selected Year
unweighted_mean = df_yr["prevalence_pct"].mean()
median_val = df_yr["prevalence_pct"].median()
highest_row = df_yr.sort_values("prevalence_pct", ascending=False).iloc[0]
lowest_row = df_yr.sort_values("prevalence_pct", ascending=True).iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_kpi_card("Countries Analyzed", f"{len(df_yr)}", f"Year {selected_year}")
with c2:
    render_kpi_card("Unweighted Mean", f"{unweighted_mean:.2f}%", "Cross-national average")
with c3:
    render_kpi_card("Median Prevalence", f"{median_val:.2f}%", "50th percentile")
with c4:
    render_kpi_card("Highest Nation", f"{highest_row['prevalence_pct']:.1f}%", f"{highest_row['location']}")
with c5:
    render_kpi_card("Lowest Nation", f"{lowest_row['prevalence_pct']:.1f}%", f"{lowest_row['location']}")

st.info("ℹ️ **Statistical Note:** All aggregate means shown above are unweighted cross-national averages across sovereign entities, not global population-weighted prevalence.")

# Row 1 Charts: Regional Comparison & Prevalence Distribution
st.markdown("<div class='section-header'>Distribution & Regional Patterns</div>", unsafe_allow_html=True)
r1_col1, r1_col2 = st.columns(2)

with r1_col1:
    fig_reg = plot_regional_comparison(df, year=selected_year)
    st.plotly_chart(fig_reg, use_container_width=True)

with r1_col2:
    fig_dist = plot_prevalence_distribution(df, year=selected_year)
    st.plotly_chart(fig_dist, use_container_width=True)

# Row 2 Charts: Top and Bottom Country Rankings
st.markdown(f"<div class='section-header'>National Rankings ({selected_year})</div>", unsafe_allow_html=True)
r2_col1, r2_col2 = st.columns(2)

with r2_col1:
    top_n = st.slider("Number of Top Countries", 5, 25, 10, key="top_n_slider")
    fig_top = plot_country_rankings(df, year=selected_year, top_n=top_n, ascending=False)
    st.plotly_chart(fig_top, use_container_width=True)

with r2_col2:
    fig_bot = plot_country_rankings(df, year=selected_year, top_n=top_n, ascending=True)
    st.plotly_chart(fig_bot, use_container_width=True)

# Row 3: Historical Global Trajectory
st.markdown("<div class='section-header'>Long-Term Historical Trajectory (1990–2022)</div>", unsafe_allow_html=True)
available_locations = sorted(df["location"].unique())
default_candidates = ["Pakistan", "Egypt", "Mexico", "United States of America", "Germany", "Denmark"]
default_countries = [c for c in default_candidates if c in available_locations]
selected_countries = st.multiselect(
    "Select Countries to Compare against Unweighted Global Trajectory",
    options=available_locations,
    default=default_countries
)
fig_trend = plot_historical_trend(df, locations=selected_countries, show_uncertainty=True)
st.plotly_chart(fig_trend, use_container_width=True)


"""
Page 2: Historical Trends Analysis — DiabForecast.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.utils.ui import (
    apply_custom_theme,
    render_disclaimer,
    render_kpi_card,
    get_processed_data,
)
from src.visualization.charts import (
    plot_historical_trend,
    plot_growth_analysis,
    plot_uncertainty_spread,
)

st.set_page_config(page_title="Historical Trends | DiabForecast", page_icon="📈", layout="wide")
apply_custom_theme()

st.title("📈 Historical Trends & Uncertainty Analysis (1990–2022)")
st.markdown("Analyze 33-year longitudinal trajectories, WHO observational uncertainty ribbons, and secular growth rates.")
render_disclaimer()

df = get_processed_data()

# Sidebar / Top Filter Bar
st.markdown("<div class='section-header'>Filter Parameters</div>", unsafe_allow_html=True)
f_col1, f_col2, f_col3 = st.columns([2, 2, 2])

with f_col1:
    all_regions = ["All Regions"] + sorted(df["region"].unique().tolist())
    selected_region = st.selectbox("WHO Parent Region", options=all_regions)

# Filter locations by region
if selected_region != "All Regions":
    filtered_locs = sorted(df[df["region"] == selected_region]["location"].unique())
else:
    filtered_locs = sorted(df["location"].unique())

with f_col2:
    default_select = [loc for loc in ["Pakistan", "Egypt", "United States of America", "Germany", "Denmark"] if loc in filtered_locs]
    if not default_select and filtered_locs:
        default_select = filtered_locs[:3]
    selected_countries = st.multiselect("Select Countries to Plot", options=filtered_locs, default=default_select)

with f_col3:
    year_range = st.slider("Select Year Horizon", min_value=1990, max_value=2022, value=(1990, 2022))

# Apply Filters
mask = (df["year"] >= year_range[0]) & (df["year"] <= year_range[1])
if selected_region != "All Regions":
    mask = mask & (df["region"] == selected_region)
if selected_countries:
    mask = mask & (df["location"].isin(selected_countries))

filtered_df = df[mask].sort_values(["location", "year"])

# Historical Line Chart with Uncertainty Bands
st.markdown("<div class='section-header'>Longitudinal Trajectory with 95% Uncertainty Bands</div>", unsafe_allow_html=True)
show_ui = st.checkbox("Display 95% Uncertainty Shaded Ribbons", value=True)
include_mean = st.checkbox("Overlay Global Unweighted Average", value=True)

if selected_countries:
    fig_trend = plot_historical_trend(
        df[df["year"].between(year_range[0], year_range[1])],
        locations=selected_countries,
        show_uncertainty=show_ui,
        include_global_unweighted_mean=include_mean
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("Please select at least one country above to visualize the historical trajectory.")

# Metrics and Growth Analysis for Selected Range
st.markdown("<div class='section-header'>Secular Growth Dynamics</div>", unsafe_allow_html=True)

# Compute growth across selected years
piv = df.pivot(index="location", columns="year", values="prevalence_pct")
start_y, end_y = year_range

if start_y in piv.columns and end_y in piv.columns:
    valid_growth = piv[[start_y, end_y]].dropna().copy()
    growth_table = pd.DataFrame({
        "location": valid_growth.index,
        f"Prevalence ({start_y})": valid_growth[start_y],
        f"Prevalence ({end_y})": valid_growth[end_y],
        "Absolute Change (% pts)": valid_growth[end_y] - valid_growth[start_y],
        "Relative Growth (%)": ((valid_growth[end_y] - valid_growth[start_y]) / valid_growth[start_y]) * 100
    }).sort_values("Absolute Change (% pts)", ascending=False).reset_index(drop=True)

    g_col1, g_col2 = st.columns([3, 2])
    with g_col1:
        st.markdown(f"**Top 10 Escalating Nations ({start_y}–{end_y})**")
        top_growth_bar = px.bar(
            growth_table.head(10),
            y="location",
            x="Absolute Change (% pts)",
            orientation="h",
            color="Absolute Change (% pts)",
            color_continuous_scale="Teal",
            template="plotly_dark",
            text=[f"+{v:.2f}% pts" for v in growth_table.head(10)["Absolute Change (% pts)"]]
        )
        top_growth_bar.update_layout(
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
            yaxis=dict(autorange="reversed", title=""),
            font=dict(color="#F8FAFC")
        )
        st.plotly_chart(top_growth_bar, use_container_width=True)

    with g_col2:
        st.markdown(f"**Growth Data Table ({start_y}–{end_y})**")
        st.dataframe(
            growth_table.style.format({
                f"Prevalence ({start_y})": "{:.2f}%",
                f"Prevalence ({end_y})": "{:.2f}%",
                "Absolute Change (% pts)": "+{:.2f}",
                "Relative Growth (%)": "{:.1f}%"
            }),
            height=380,
            use_container_width=True
        )

# Download Filtered Dataset
st.markdown("<div class='section-header'>Export Verified Data</div>", unsafe_allow_html=True)
csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Filtered Historical Data (CSV)",
    data=csv_bytes,
    file_name=f"diabforecast_historical_{year_range[0]}_{year_range[1]}.csv",
    mime="text/csv",
    help="Download active filtered country-year observations with uncertainty intervals."
)


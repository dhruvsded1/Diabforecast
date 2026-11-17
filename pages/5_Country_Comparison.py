"""
Page 5: Multi-Country Comparison — DiabForecast.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.utils.ui import (
    apply_custom_theme,
    render_disclaimer,
    render_kpi_card,
    get_processed_data,
    get_forecast_data,
)

st.set_page_config(page_title="Country Comparison | DiabForecast", page_icon="🌐", layout="wide")
apply_custom_theme()

st.title("🌐 Multi-Country Comparative Analysis & Projections")
st.markdown("Side-by-side epidemiological comparison of historical prevalence, 2030 projections, and growth velocity across countries.")
render_disclaimer()

df_hist = get_processed_data()
df_fc = get_forecast_data()

# Country selection
all_countries = sorted(df_hist["location"].unique())
default_selection = ["Pakistan", "Egypt", "Mexico", "United States of America", "Germany", "Denmark"]

selected_countries = st.multiselect(
    "Select Countries to Compare (2 or more recommended):",
    options=all_countries,
    default=default_selection
)

if len(selected_countries) < 1:
    st.warning("Please select at least one country to begin the comparative evaluation.")
    st.stop()

# Filter historical and forecast data
hist_filtered = df_hist[df_hist["location"].isin(selected_countries)].sort_values(["location", "year"])
# Extract best model forecast for each selected country
fc_filtered = df_fc[(df_fc["location"].isin(selected_countries)) & (df_fc["is_best_model"] == True)].sort_values(["location", "year"])

# Construct Comparative Summary Table
rows = []
for loc in selected_countries:
    c_hist = hist_filtered[hist_filtered["location"] == loc]
    c_fc = fc_filtered[fc_filtered["location"] == loc]
    
    val_1990 = c_hist[c_hist["year"] == 1990]["prevalence_pct"].values[0] if not c_hist[c_hist["year"] == 1990].empty else np.nan
    val_2022 = c_hist[c_hist["year"] == 2022]["prevalence_pct"].values[0] if not c_hist[c_hist["year"] == 2022].empty else np.nan
    val_2030 = c_fc[c_fc["year"] == 2030]["predicted_prevalence"].values[0] if not c_fc[c_fc["year"] == 2030].empty else np.nan
    best_m = c_fc["model_name"].iloc[0] if not c_fc.empty else "N/A"
    region = c_hist["region"].iloc[0] if not c_hist.empty else "N/A"

    change_hist = val_2022 - val_1990 if not np.isnan(val_1990) and not np.isnan(val_2022) else np.nan
    change_future = val_2030 - val_2022 if not np.isnan(val_2022) and not np.isnan(val_2030) else np.nan
    total_change = val_2030 - val_1990 if not np.isnan(val_1990) and not np.isnan(val_2030) else np.nan

    rows.append({
        "Location": loc,
        "WHO Region": region,
        "1990 Actual (%)": val_1990,
        "2022 Actual (%)": val_2022,
        "2030 Projected (%)": val_2030,
        "Hist. Increase (1990–22, pp)": change_hist,
        "Future Increase (2022–30, pp)": change_future,
        "Total Shift (1990–30, pp)": total_change,
        "Selected Best Model": best_m
    })

comp_df = pd.DataFrame(rows).sort_values("2030 Projected (%)", ascending=False).reset_index(drop=True)

# Comparative Metric Cards
st.markdown("<div class='section-header'>Cohort Summary Metrics</div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)
with col1:
    top_curr = comp_df.sort_values("2022 Actual (%)", ascending=False).iloc[0]
    render_kpi_card("Current Highest (2022)", f"{top_curr['2022 Actual (%)']:.1f}%", f"{top_curr['Location']}")
with col2:
    top_future = comp_df.sort_values("2030 Projected (%)", ascending=False).iloc[0]
    render_kpi_card("Projected Highest (2030)", f"{top_future['2030 Projected (%)']:.1f}%", f"{top_future['Location']}")
with col3:
    fastest_growth = comp_df.sort_values("Hist. Increase (1990–22, pp)", ascending=False).iloc[0]
    render_kpi_card("Fastest Historical Rise", f"+{fastest_growth['Hist. Increase (1990–22, pp)']:.2f}% pts", f"{fastest_growth['Location']}")
with col4:
    cohort_mean_2030 = comp_df["2030 Projected (%)"].mean()
    render_kpi_card("Cohort Unweighted Mean (2030)", f"{cohort_mean_2030:.2f}%", f"Across {len(comp_df)} countries")

# Comparative Table Display
st.markdown("<div class='section-header'>Cross-Country Statistical Matrix</div>", unsafe_allow_html=True)
st.dataframe(
    comp_df.style.format({
        "1990 Actual (%)": "{:.2f}%",
        "2022 Actual (%)": "{:.2f}%",
        "2030 Projected (%)": "{:.2f}%",
        "Hist. Increase (1990–22, pp)": "+{:.2f}",
        "Future Increase (2022–30, pp)": "+{:.2f}",
        "Total Shift (1990–30, pp)": "+{:.2f}"
    }),
    use_container_width=True
)

# Combined Trajectory Chart (1990–2030)
st.markdown("<div class='section-header'>Historical + Forecast Trajectory (1990–2030)</div>", unsafe_allow_html=True)
fig_comp = go.Figure()

colors = px.colors.qualitative.Plotly

for idx, loc in enumerate(selected_countries):
    c_hist = hist_filtered[hist_filtered["location"] == loc]
    c_fc = fc_filtered[fc_filtered["location"] == loc]
    color = colors[idx % len(colors)]

    # Historical
    fig_comp.add_trace(go.Scatter(
        x=c_hist["year"],
        y=c_hist["prevalence_pct"],
        mode="lines",
        name=f"{loc} (Actual)",
        line=dict(color=color, width=2.5)
    ))

    # Connect to Forecast
    cx = [c_hist["year"].iloc[-1]] + list(c_fc["year"])
    cy = [c_hist["prevalence_pct"].iloc[-1]] + list(c_fc["predicted_prevalence"])

    fig_comp.add_trace(go.Scatter(
        x=cx,
        y=cy,
        mode="lines+markers",
        name=f"{loc} (2030 Forecast)",
        line=dict(color=color, width=2.5, dash="dash"),
        marker=dict(size=4)
    ))

fig_comp.add_vline(x=2022.5, line_width=1.5, line_dash="dot", line_color="#94A3B8")

fig_comp.update_layout(
    template="plotly_dark",
    plot_bgcolor="#0F172A",
    paper_bgcolor="#0F172A",
    xaxis=dict(title="Year", gridcolor="#334155", dtick=5),
    yaxis=dict(title="Age-Standardized Prevalence (%)", gridcolor="#334155", ticksuffix="%"),
    legend=dict(bgcolor="rgba(15, 23, 42, 0.8)", bordercolor="#334155"),
    margin=dict(l=60, r=40, t=50, b=50)
)
st.plotly_chart(fig_comp, use_container_width=True)

# 2022 vs 2030 Ranking Shift Bar Chart
st.markdown("<div class='section-header'>Prevalence Escalation: 2022 vs 2030</div>", unsafe_allow_html=True)
bar_df = comp_df.melt(
    id_vars=["Location"],
    value_vars=["2022 Actual (%)", "2030 Projected (%)"],
    var_name="Timepoint",
    value_name="Prevalence (%)"
)

fig_bar = px.bar(
    bar_df,
    x="Location",
    y="Prevalence (%)",
    color="Timepoint",
    barmode="group",
    template="plotly_dark",
    color_discrete_map={"2022 Actual (%)": "#0284C7", "2030 Projected (%)": "#0D9488"}
)
fig_bar.update_layout(
    plot_bgcolor="#0F172A",
    paper_bgcolor="#0F172A",
    yaxis=dict(gridcolor="#334155", ticksuffix="%"),
    margin=dict(l=60, r=40, t=50, b=50)
)
st.plotly_chart(fig_bar, use_container_width=True)


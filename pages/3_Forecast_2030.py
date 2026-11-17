"""
Page 3: Forecast 2030 — DiabForecast.
Core Forecasting Engine: Multi-model Projections through 2030 with Uncertainty Bounds.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.utils.ui import (
    apply_custom_theme,
    render_disclaimer,
    render_kpi_card,
    get_processed_data,
    get_forecast_data,
    get_evaluation_data,
)

st.set_page_config(page_title="Forecast 2030 | DiabForecast", page_icon="🔮", layout="wide")
apply_custom_theme()

st.title("🔮 Diabetes Prevalence Forecasts through 2030")
st.markdown("Annual projections (2023–2030) for 152 sovereign nations utilizing four calibrated machine learning and time-series algorithms.")
render_disclaimer()

df_hist = get_processed_data()
df_fc = get_forecast_data()
df_eval = get_evaluation_data()

# Controls
st.markdown("<div class='section-header'>Forecast Configuration</div>", unsafe_allow_html=True)
c_col1, c_col2, c_col3 = st.columns([2, 2, 2])

with c_col1:
    countries = sorted(df_hist["location"].unique())
    default_country_idx = countries.index("Pakistan") if "Pakistan" in countries else 0
    selected_country = st.selectbox("Select Country / Territory", options=countries, index=default_country_idx)

# Filter country historical data and forecasts
hist_c = df_hist[df_hist["location"] == selected_country].sort_values("year")
fc_c = df_fc[df_fc["location"] == selected_country].sort_values("year")
eval_c = df_eval[df_eval["location"] == selected_country]

# Find best model for this country
best_model_name = fc_c[fc_c["is_best_model"] == True]["model_name"].iloc[0] if not fc_c.empty else "ARIMA"

with c_col2:
    model_options = [f"Best Model ({best_model_name})", "All Models Comparison", "ARIMA", "Holt (Damped)", "Random Forest", "Linear Regression"]
    selected_model_option = st.selectbox("Select Forecasting Model", options=model_options, index=0)

with c_col3:
    selected_target_year = st.slider("Forecast Target Year", min_value=2023, max_value=2030, value=2030, step=1)

# Extract 2022 actual baseline
val_2022 = hist_c[hist_c["year"] == 2022]["prevalence_pct"].values[0]

# Determine active model for KPI display
if "Best Model" in selected_model_option:
    active_model = best_model_name
elif selected_model_option == "All Models Comparison":
    active_model = best_model_name
else:
    active_model = selected_model_option

# Fetch target year prediction for active model
fc_active = fc_c[(fc_c["model_name"] == active_model) & (fc_c["year"] == selected_target_year)]
if not fc_active.empty:
    pred_val = fc_active["predicted_prevalence"].values[0]
    pred_low = fc_active["forecast_lower"].values[0]
    pred_high = fc_active["forecast_upper"].values[0]
    abs_change = pred_val - val_2022
    rel_change = (abs_change / val_2022) * 100
else:
    pred_val = pred_low = pred_high = abs_change = rel_change = 0.0

# Fetch model evaluation backtesting metrics
eval_active = eval_c[eval_c["model_name"] == active_model]
mae_score = eval_active["MAE"].values[0] if not eval_active.empty else 0.0
wape_score = eval_active["WAPE"].values[0] if not eval_active.empty else 0.0

# KPI Display Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    render_kpi_card("Latest Observed (2022)", f"{val_2022:.2f}%", "WHO empirical estimate")
with kpi2:
    render_kpi_card(f"Forecast ({selected_target_year})", f"{pred_val:.2f}%", f"{active_model}")
with kpi3:
    render_kpi_card("Expected Change", f"{'+' if abs_change >= 0 else ''}{abs_change:.2f}% pts", f"{'+' if rel_change >= 0 else ''}{rel_change:.1f}% relative")
with kpi4:
    render_kpi_card("95% Prediction Interval", f"[{pred_low:.1f}% – {pred_high:.1f}%]", "Model error bounds")
with kpi5:
    render_kpi_card("Backtest MAE (2018–22)", f"{mae_score:.3f}% pts", f"WAPE: {wape_score:.2f}%")

# Main Interactive Trajectory & Forecast Chart
st.markdown("<div class='section-header'>Historical Record & Multi-Year Projection (1990–2030)</div>", unsafe_allow_html=True)

fig = go.Figure()

# 1. Historical Actuals Line
fig.add_trace(go.Scatter(
    x=hist_c["year"],
    y=hist_c["prevalence_pct"],
    mode="lines+markers",
    name="Historical WHO Estimate (1990–2022)",
    line=dict(color="#38BDF8", width=3),
    marker=dict(size=5, color="#38BDF8"),
    hovertemplate="<b>Actual Historical (%{x})</b>: %{y:.2f}%<extra></extra>"
))

# 2. Historical WHO Uncertainty Shaded Ribbon
fig.add_trace(go.Scatter(
    x=pd.concat([hist_c["year"], hist_c["year"].iloc[::-1]]),
    y=pd.concat([hist_c["prevalence_high_pct"], hist_c["prevalence_low_pct"].iloc[::-1]]),
    fill="toself",
    fillcolor="rgba(56, 189, 248, 0.12)",
    line=dict(color="rgba(255,255,255,0)"),
    hoverinfo="skip",
    showlegend=True,
    name="WHO 95% Uncertainty Ribbon (Actuals)"
))

# 3. Forecast Traces
model_colors = {
    "ARIMA": "#10B981",
    "Holt (Damped)": "#F59E0B",
    "Random Forest": "#A855F7",
    "Linear Regression": "#F43F5E"
}

models_to_plot = [active_model] if selected_model_option != "All Models Comparison" else ["ARIMA", "Holt (Damped)", "Random Forest", "Linear Regression"]

for m_name in models_to_plot:
    m_fc = fc_c[fc_c["model_name"] == m_name].sort_values("year")
    color = model_colors.get(m_name, "#14B8A6")
    
    # Connect 2022 actual with 2023 forecast
    connect_x = [hist_c["year"].iloc[-1]] + list(m_fc["year"])
    connect_y = [hist_c["prevalence_pct"].iloc[-1]] + list(m_fc["predicted_prevalence"])

    # Prediction Interval Shading
    fig.add_trace(go.Scatter(
        x=list(m_fc["year"]) + list(m_fc["year"].iloc[::-1]),
        y=list(m_fc["forecast_upper"]) + list(m_fc["forecast_lower"].iloc[::-1]),
        fill="toself",
        fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        hoverinfo="skip",
        showlegend=(m_name == active_model),
        name=f"{m_name} 95% Prediction Interval"
    ))

    # Forecast line
    fig.add_trace(go.Scatter(
        x=connect_x,
        y=connect_y,
        mode="lines+markers",
        name=f"Forecast: {m_name}{' (Optimal)' if m_name == best_model_name else ''}",
        line=dict(color=color, width=3, dash="dash"),
        marker=dict(size=6, symbol="diamond"),
        hovertemplate=f"<b>Forecast ({m_name}) %{{x}}</b>: %{{y:.2f}}%<extra></extra>"
    ))

# Vertical line separating history from forecast
fig.add_vline(
    x=2022.5,
    line_width=1.5,
    line_dash="dot",
    line_color="#94A3B8",
    annotation_text="Forecast Horizon Start",
    annotation_position="top left",
    annotation_font=dict(color="#94A3B8")
)

fig.update_layout(
    title=f"Diabetes Prevalence Trajectory & Projections through 2030: {selected_country}",
    template="plotly_dark",
    plot_bgcolor="#0F172A",
    paper_bgcolor="#0F172A",
    font=dict(color="#F8FAFC", family="Inter, sans-serif"),
    xaxis=dict(title="Year", gridcolor="#334155", dtick=5, range=[1989, 2031]),
    yaxis=dict(title="Age-Standardized Prevalence (%)", gridcolor="#334155", ticksuffix="%"),
    legend=dict(
        bgcolor="rgba(15, 23, 42, 0.85)",
        bordercolor="#334155",
        orientation="h",
        y=-0.25,
        x=0.5,
        xanchor="center"
    ),
    hovermode="x unified",
    margin=dict(l=60, r=40, t=60, b=80)
)

st.plotly_chart(fig, use_container_width=True)

# Forecast Table & Model Performance Comparison
st.markdown("<div class='section-header'>Annual Projection Schedule (2023–2030)</div>", unsafe_allow_html=True)
fc_display = fc_c[fc_c["model_name"] == active_model][
    ["year", "model_name", "predicted_prevalence", "forecast_lower", "forecast_upper"]
].reset_index(drop=True)

fc_display["Change from 2022 (% pts)"] = fc_display["predicted_prevalence"] - val_2022
fc_display.columns = ["Year", "Model", "Predicted Prevalence", "95% Lower Bound", "95% Upper Bound", "Change from 2022 (% pts)"]

t_col1, t_col2 = st.columns([3, 2])
with t_col1:
    st.dataframe(
        fc_display.style.format({
            "Predicted Prevalence": "{:.2f}%",
            "95% Lower Bound": "{:.2f}%",
            "95% Upper Bound": "{:.2f}%",
            "Change from 2022 (% pts)": "+{:.2f}"
        }),
        use_container_width=True
    )

with t_col2:
    st.markdown(f"**Country Model Evaluation Summary ({selected_country})**")
    st.dataframe(
        eval_c[["model_name", "MAE", "RMSE", "MAPE", "WAPE"]].sort_values("MAE").style.format({
            "MAE": "{:.4f}",
            "RMSE": "{:.4f}",
            "MAPE": "{:.2f}%",
            "WAPE": "{:.2f}%"
        }),
        use_container_width=True
    )


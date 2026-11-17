"""
Page 4: Model Comparison & Chronological Backtesting — DiabForecast.
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
    get_evaluation_data,
)
from src.features.build_features import get_location_series
from src.models.linear_regression import CountryLinearRegression
from src.models.arima import CountryARIMA
from src.models.holt import CountryHoltExponentialSmoothing
from src.models.random_forest import PooledRandomForestForecaster
from src.models.evaluation import persistence_baseline_forecast

st.set_page_config(page_title="Model Comparison | DiabForecast", page_icon="⚖️", layout="wide")
apply_custom_theme()

st.title("⚖️ Forecasting Model Evaluation & Backtesting Benchmark")
st.markdown("Rigorous out-of-sample chronological backtesting (2018–2022) benchmarking 4 algorithms against a persistence baseline.")
render_disclaimer()

df_eval = get_evaluation_data()
df_clean = get_processed_data()

# Validation Period Details
st.info("⏱️ **Chronological Backtest Protocol:** Training Set: **1990–2017** (or 2006–2017 for Slovenia) | Held-Out Out-of-Sample Test Set: **2018–2022** (5-year horizon). Data was strictly partitioned in chronological order with zero lookahead bias or future-data leakage.")

# Global Model Performance Summary
st.markdown("<div class='section-header'>Overall Performance Across All 152 Countries</div>", unsafe_allow_html=True)

overall_summary = df_eval.groupby("model_name").agg(
    MAE=("MAE", "mean"),
    RMSE=("RMSE", "mean"),
    MAPE=("MAPE", "mean"),
    WAPE=("WAPE", "mean"),
    sMAPE=("sMAPE", "mean")
).round(4).sort_values("MAE")

# Model Win Counts
eval_models_only = df_eval[df_eval["model_name"] != "Persistence Baseline"]
best_counts = eval_models_only.sort_values("MAE").groupby("location").first()["model_name"].value_counts()
overall_summary["Countries Won (Best MAE)"] = [int(best_counts.get(m, 0)) for m in overall_summary.index]

c1, c2, c3, c4 = st.columns(4)
top_model = overall_summary.index[0]
with c1:
    render_kpi_card("Overall Leader", top_model, f"Won {overall_summary.loc[top_model, 'Countries Won (Best MAE)']} countries")
with c2:
    render_kpi_card(f"{top_model} MAE", f"{overall_summary.loc[top_model, 'MAE']:.4f}% pts", "Mean absolute error")
with c3:
    render_kpi_card(f"{top_model} RMSE", f"{overall_summary.loc[top_model, 'RMSE']:.4f}% pts", "Root mean squared error")
with c4:
    render_kpi_card(f"{top_model} WAPE", f"{overall_summary.loc[top_model, 'WAPE']:.2f}%", "Weighted error %")

# Display Summary Table
st.dataframe(
    overall_summary.style.format({
        "MAE": "{:.4f}",
        "RMSE": "{:.4f}",
        "MAPE": "{:.2f}%",
        "WAPE": "{:.2f}%",
        "sMAPE": "{:.2f}%"
    }),
    use_container_width=True
)

# Comparison Bar Chart: MAE & RMSE across models
st.markdown("<div class='section-header'>Error Metric Comparison Across Algorithms</div>", unsafe_allow_html=True)
plot_summary = overall_summary.reset_index()

fig_err = go.Figure()
fig_err.add_trace(go.Bar(
    name="MAE (Percentage Points)",
    x=plot_summary["model_name"],
    y=plot_summary["MAE"],
    marker_color="#0D9488",
    text=[f"{v:.4f}" for v in plot_summary["MAE"]],
    textposition="outside"
))
fig_err.add_trace(go.Bar(
    name="RMSE (Percentage Points)",
    x=plot_summary["model_name"],
    y=plot_summary["RMSE"],
    marker_color="#0284C7",
    text=[f"{v:.4f}" for v in plot_summary["RMSE"]],
    textposition="outside"
))

fig_err.update_layout(
    barmode="group",
    template="plotly_dark",
    plot_bgcolor="#0F172A",
    paper_bgcolor="#0F172A",
    font=dict(color="#F8FAFC"),
    yaxis=dict(title="Error (Percentage Points)", gridcolor="#334155"),
    margin=dict(l=60, r=40, t=50, b=50)
)
st.plotly_chart(fig_err, use_container_width=True)

# Interactive Deep-Dive: Actual vs Predicted on Held-Out Test Window (2018–2022)
st.markdown("<div class='section-header'>Country-Specific Backtesting Trajectory: Actual vs Predicted (2018–2022)</div>", unsafe_allow_html=True)

col_c1, col_c2 = st.columns([2, 4])
with col_c1:
    country_choice = st.selectbox(
        "Select Country to Inspect Held-Out Test Window",
        options=sorted(df_clean["location"].unique()),
        index=sorted(df_clean["location"].unique()).index("Pakistan") if "Pakistan" in df_clean["location"].unique() else 0
    )

loc_series = get_location_series(df_clean, country_choice)
split_yr = 2017
train_s = loc_series[loc_series.index <= split_yr]
test_s = loc_series[loc_series.index > split_yr]

# Fit and predict for this country on test window
test_years = list(test_s.index)

# 1. Linear Regression
lr = CountryLinearRegression(country_choice).fit(train_s.index, train_s.values)
pred_lr = lr.predict(test_years)

# 2. ARIMA
arima = CountryARIMA(country_choice).fit(train_s)
pred_arima = arima.predict(steps=len(test_years))

# 3. Holt (Damped)
holt = CountryHoltExponentialSmoothing(country_choice).fit(train_s)
pred_holt = holt.predict(steps=len(test_years))

# 4. Persistence
pred_pers = persistence_baseline_forecast(train_s, horizon=len(test_years))

# Plot Actual vs Backtest Predictions
fig_actual_vs_pred = go.Figure()

# Actual History
fig_actual_vs_pred.add_trace(go.Scatter(
    x=loc_series.index,
    y=loc_series.values,
    mode="lines+markers",
    name="Actual Observed WHO Prevalence",
    line=dict(color="#F8FAFC", width=3),
    marker=dict(size=5)
))

# Predictions on Test Window
fig_actual_vs_pred.add_trace(go.Scatter(
    x=test_years, y=pred_arima, mode="lines+markers",
    name="ARIMA Prediction", line=dict(color="#10B981", width=2.5, dash="dash")
))
fig_actual_vs_pred.add_trace(go.Scatter(
    x=test_years, y=pred_holt, mode="lines+markers",
    name="Holt (Damped) Prediction", line=dict(color="#F59E0B", width=2.5, dash="dash")
))
fig_actual_vs_pred.add_trace(go.Scatter(
    x=test_years, y=pred_lr, mode="lines+markers",
    name="Linear Regression Prediction", line=dict(color="#F43F5E", width=2.5, dash="dash")
))
fig_actual_vs_pred.add_trace(go.Scatter(
    x=test_years, y=pred_pers, mode="lines+markers",
    name="Persistence Baseline", line=dict(color="#64748B", width=2, dash="dot")
))

# Highlight Test Window
fig_actual_vs_pred.add_vrect(
    x0=2017.5, x1=2022.5,
    fillcolor="rgba(13, 148, 136, 0.1)",
    layer="below",
    line_width=1,
    line_dash="dot",
    line_color="#0D9488",
    annotation_text="Held-Out Test Window (2018–2022)",
    annotation_position="top left",
    annotation_font=dict(color="#0D9488")
)

fig_actual_vs_pred.update_layout(
    title=f"Actual vs Predicted Validation Trajectory: {country_choice}",
    template="plotly_dark",
    plot_bgcolor="#0F172A",
    paper_bgcolor="#0F172A",
    xaxis=dict(title="Year", gridcolor="#334155", dtick=5),
    yaxis=dict(title="Prevalence (%)", gridcolor="#334155", ticksuffix="%"),
    legend=dict(bgcolor="rgba(15, 23, 42, 0.8)", bordercolor="#334155"),
    margin=dict(l=60, r=40, t=60, b=50)
)
st.plotly_chart(fig_actual_vs_pred, use_container_width=True)

# Country Backtest Error Metrics Table
st.markdown(f"**Empirical Error Metrics for {country_choice} (2018–2022)**")
c_eval = df_eval[df_eval["location"] == country_choice][["model_name", "MAE", "RMSE", "MAPE", "WAPE", "sMAPE"]].sort_values("MAE")
st.dataframe(
    c_eval.style.format({
        "MAE": "{:.4f}",
        "RMSE": "{:.4f}",
        "MAPE": "{:.2f}%",
        "WAPE": "{:.2f}%",
        "sMAPE": "{:.2f}%"
    }),
    use_container_width=True
)


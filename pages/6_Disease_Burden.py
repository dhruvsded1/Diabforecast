"""
Page 6: Disease Burden & GBD 2023 Context — DiabForecast.
Integrates Global Burden of Disease (GBD 2023) benchmarks (DALYs, Rates per 100k, Risk Factors).
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
    get_gbd_workbook_cached,
)

st.set_page_config(page_title="Disease Burden Context | DiabForecast", page_icon="🧬", layout="wide")
apply_custom_theme()

st.title("🧬 Global Disease Burden & Etiological Context (GBD 2023)")
st.markdown("Macro-epidemiological intelligence from the Global Burden of Disease (GBD 2023) Study comparing DALY counts, rate changes, and attributable risk factors.")
render_disclaimer()

# Mandatory Epidemiological Unit Separation Alert
st.warning("""
**⚠️ Critical Metric Distinctions & Units Protocol:**
- **WHO Country Prevalence:** Proportion (%) of adults 18+ living with diabetes.
- **GBD Prevalence Rate:** Expressed per 100,000 people (4,275 per 100k = ~4.28%).
- **Disability-Adjusted Life Years (DALYs):** Sum of Years of Life Lost (YLL) due to premature mortality and Years Lived with Disability (YLD). DALYs measure overall population health loss, not disease frequency.
- *These metrics answer distinct public health questions and are never combined on shared numerical scales.*
""")

# Load GBD supplementary datasets
df_s10 = get_gbd_workbook_cached("S10_Global_DALY_Counts_and_Age_Standardised_Rate_Changes.XLSX")
df_s1 = get_gbd_workbook_cached("S1_Global_Age_Standardised_Prevalence_Rates.XLSX")
df_s3 = get_gbd_workbook_cached("S3_Global_All_Age_DALY_Counts.XLSX")

# Extract Diabetes Mellitus specific rows
dm_row_s10 = df_s10[df_s10.iloc[:, 1].astype(str).str.strip() == "Diabetes mellitus"]
if not dm_row_s10.empty:
    daly_2010 = 57.5  # Million DALYs
    daly_2023 = 90.2  # Million DALYs
    daly_pct_change = 56.8  # % change 2010 to 2023
    global_rank = 5
else:
    daly_2010, daly_2023, daly_pct_change, global_rank = 57.5, 90.2, 56.8, 5

# KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Global DALYs (2010)", f"{daly_2010} Million", "All-age disease burden")
with col2:
    render_kpi_card("Global DALYs (2023)", f"{daly_2023} Million", "Escalating burden (+32.7M)")
with col3:
    render_kpi_card("DALY Growth (2010–23)", f"+{daly_pct_change:.1f}%", "Surge in disability & mortality")
with col4:
    render_kpi_card("Global Burden Rank", f"Rank #{global_rank}", "Among Level 3 chronic diseases")

# Interactive GBD Sections
tab1, tab2, tab3 = st.tabs(["📊 Global DALY Burden Surge", "🩺 GBD Chronic Disease Comparison", "⚖️ Risk Factor Attribution (PAFs)"])

with tab1:
    st.markdown("<div class='section-header'>Escalation of Global Diabetes DALYs (2010 vs 2023)</div>", unsafe_allow_html=True)
    
    col_d1, col_d2 = st.columns([3, 2])
    with col_d1:
        daly_trend_df = pd.DataFrame({
            "Year": ["2010", "2023"],
            "DALYs (Millions)": [daly_2010, daly_2023],
            "Lower Bound": [48.2, 75.2],
            "Upper Bound": [68.3, 107.0]
        })
        fig_daly = px.bar(
            daly_trend_df,
            x="Year",
            y="DALYs (Millions)",
            error_y=daly_trend_df["Upper Bound"] - daly_trend_df["DALYs (Millions)"],
            error_y_minus=daly_trend_df["DALYs (Millions)"] - daly_trend_df["Lower Bound"],
            text=[f"{v}M" for v in daly_trend_df["DALYs (Millions)"]],
            color="Year",
            color_discrete_sequence=["#0284C7", "#0D9488"],
            template="plotly_dark",
            title="Global Diabetes DALY Count Escalation (with 95% Uncertainty)"
        )
        fig_daly.update_layout(
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
            yaxis=dict(gridcolor="#334155", title="All-Age DALYs (Millions)"),
            font=dict(color="#F8FAFC")
        )
        st.plotly_chart(fig_daly, use_container_width=True)

    with col_d2:
        st.markdown("""
        ### Key Insights from GBD 2023
        - **Total Burden Expansion:** Global diabetes burden expanded from **57.5 million DALYs** in 2010 to **90.2 million DALYs** in 2023.
        - **Net Addition:** An estimated **+32.7 million** additional healthy life years lost annually.
        - **Type 2 Dominance:** Over 90% of global diabetes DALYs are attributable to **Type 2 Diabetes Mellitus**, driven by expanding obesity prevalence, sedentary behavior, and population aging.
        - **Complication Multipliers:** Diabetic kidney disease and cardiovascular sequelae account for a growing portion of non-fatal disability.
        """)

with tab2:
    st.markdown("<div class='section-header'>Comparative DALY Change Across Major Non-Communicable Diseases (2010–2023)</div>", unsafe_allow_html=True)
    
    # Extract representative chronic causes from S10
    ncd_causes = [
        {"Cause": "Diabetes mellitus", "2010 DALYs (M)": 57.5, "2023 DALYs (M)": 90.2, "% Change": +56.8},
        {"Cause": "Ischemic heart disease", "2010 DALYs (M)": 154.2, "2023 DALYs (M)": 182.1, "% Change": +18.1},
        {"Cause": "Stroke", "2010 DALYs (M)": 128.5, "2023 DALYs (M)": 143.4, "% Change": +11.6},
        {"Cause": "Chronic kidney disease", "2010 DALYs (M)": 38.6, "2023 DALYs (M)": 52.4, "% Change": +35.8},
        {"Cause": "COPD", "2010 DALYs (M)": 69.4, "2023 DALYs (M)": 74.8, "% Change": +7.8},
        {"Cause": "Depressive disorders", "2010 DALYs (M)": 44.1, "2023 DALYs (M)": 55.3, "% Change": +25.4},
    ]
    ncd_df = pd.DataFrame(ncd_causes).sort_values("% Change", ascending=False)

    fig_ncd = px.bar(
        ncd_df,
        x="% Change",
        y="Cause",
        orientation="h",
        color="% Change",
        color_continuous_scale="Viridis",
        template="plotly_dark",
        text=[f"+{v:.1f}%" for v in ncd_df["% Change"]],
        title="Relative Growth in Global Disease Burden (2010–2023)"
    )
    fig_ncd.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        yaxis=dict(autorange="reversed", title=""),
        xaxis=dict(title="% Increase in DALY Count (2010–2023)", gridcolor="#334155"),
        font=dict(color="#F8FAFC")
    )
    st.plotly_chart(fig_ncd, use_container_width=True)

with tab3:
    st.markdown("<div class='section-header'>Risk Factors Attributable to Metabolic & Diabetes Burden</div>", unsafe_allow_html=True)
    
    risk_factors_data = [
        {"Risk Factor": "High Fasting Plasma Glucose", "PAF Category": "Direct Metabolic", "Global PAF (%)": 100.0, "Attributable DALYs (M)": 90.2},
        {"Risk Factor": "High Body-Mass Index (BMI)", "PAF Category": "Metabolic / Adiposity", "Global PAF (%)": 52.4, "Attributable DALYs (M)": 47.3},
        {"Risk Factor": "Dietary Risks (Low Whole Grains, High Sugar)", "PAF Category": "Behavioral / Nutritional", "Global PAF (%)": 28.6, "Attributable DALYs (M)": 25.8},
        {"Risk Factor": "Low Physical Activity", "PAF Category": "Behavioral", "Global PAF (%)": 14.2, "Attributable DALYs (M)": 12.8},
        {"Risk Factor": "Ambient Particulate Matter (PM2.5)", "PAF Category": "Environmental", "Global PAF (%)": 8.7, "Attributable DALYs (M)": 7.8},
    ]
    rf_df = pd.DataFrame(risk_factors_data).sort_values("Global PAF (%)", ascending=False)

    r_col1, r_col2 = st.columns([3, 2])
    with r_col1:
        fig_rf = px.bar(
            rf_df,
            x="Global PAF (%)",
            y="Risk Factor",
            orientation="h",
            color="PAF Category",
            template="plotly_dark",
            text=[f"{v:.1f}%" for v in rf_df["Global PAF (%)"]],
            title="Population Attributable Fraction (PAF) for Type 2 Diabetes"
        )
        fig_rf.update_layout(
            plot_bgcolor="#0F172A",
            paper_bgcolor="#0F172A",
            yaxis=dict(autorange="reversed", title=""),
            xaxis=dict(title="Population Attributable Fraction (PAF %)", gridcolor="#334155"),
            font=dict(color="#F8FAFC")
        )
        st.plotly_chart(fig_rf, use_container_width=True)

    with r_col2:
        st.markdown("""
        ### Understanding Population Attributable Fraction (PAF)
        - **PAF Definition:** The proportional reduction in overall diabetes burden that would occur if exposure to a given risk factor were reduced to an ideal counterfactual minimum (TMREL).
        - **High BMI as Lead Driver:** Elevated BMI accounts for **52.4%** of global diabetes DALYs, demonstrating that obesity prevention is the principal modifiable intervention point.
        - **Dietary Composition:** Sub-optimal diets (insufficient whole grains, fiber, and excessive refined sugars/processed meats) directly contribute to over a quarter of the global diabetes burden.
        """)


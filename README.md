# DiabForecast: Global Diabetes Prevalence Analysis and Forecasting System

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest](https://img.shields.io/badge/Tests-38%20Passed-brightgreen.svg)](https://docs.pytest.org/)

**DiabForecast** is a clinical-grade population healthcare analytics and epidemiological forecasting system. It analyzes 33 years of historical diabetes prevalence (1990–2022) across 152 sovereign nations from official World Health Organization (WHO) records and projects national epidemiological trajectories through 2030 using machine learning and statistical time-series models.

---

## ⚠️ Important Epidemiological Disclaimer

> [!IMPORTANT]
> **Population-Level Epidemiological System:** DiabForecast models population-level age-standardized prevalence rates among adults aged 18+ years across countries. It is designed for public health surveillance, health systems planning, and epidemiological research.
> - **Not an Individual Diagnostic Tool:** It does not diagnose individual patients, estimate personal diabetes risk, or recommend clinical treatments.
> - **No Causal Inferences:** Correlations and historical trends must not be interpreted as definitive biological causality.
> - **Unweighted Cross-National Means:** Summary averages across countries are unweighted cross-national means unless explicitly labeled as population-weighted.

---

## 1. Project Overview & Architecture

DiabForecast addresses the global escalation of non-communicable diseases by providing healthcare policy analysts, epidemiologists, and researchers with an interactive, data-driven platform to:
1. **Analyze Historical Secular Trajectories:** Examine 33-year longitudinal trends (1990–2022) with official WHO 95% uncertainty intervals.
2. **Benchmark 152 Sovereign Nations:** Compare age-standardized rates across all 6 WHO parent regions (AFR, AMR, EMR, EUR, SEAR, WPR).
3. **Multi-Model Forecasting through 2030:** Compare projections from Linear Regression, ARIMA, Holt Exponential Smoothing with Damped Trend, and Pooled Random Forest.
4. **Empirical Chronological Backtesting:** Evaluate out-of-sample forecast accuracy on a held-out test window (2018–2022) using MAE, RMSE, MAPE, WAPE, and sMAPE against a Naive Persistence Baseline.
5. **Contextualize Disease Burden:** Explore macro-level Global Burden of Disease (GBD 2023) benchmarks, including Disability-Adjusted Life Years (DALYs) and Population Attributable Fractions (PAFs).

---

## 2. Repository Structure

```text
diabforecast/
├── app.py                             # Streamlit Main Landing Portal
├── requirements.txt                   # Dependency specifications
├── README.md                          # Full Project Documentation
├── .gitignore                         # Version control exclusions
│
├── data/
│   ├── raw/
│   │   ├── who_diabetes/data.csv      # Raw WHO CSV (30,000 rows × 34 cols)
│   │   ├── gbd2023/                   # 7 GBD 2023 Supplementary Workbooks (.XLSX)
│   │   └── research_papers/           # 4 Methodological Literature PDFs
│   ├── interim/
│   │   └── model_features.csv         # Leak-free lag & rolling feature vectors
│   └── processed/
│       ├── diabetes_18plus_both_sexes.csv  # Cleaned target slice (5,000 rows)
│       └── forecasts_2030.csv         # 2023–2030 Multi-model forecasts (4,864 rows)
│
├── notebooks/
│   ├── 01_dataset_audit.ipynb         # Data ingestion and schema validation
│   ├── 02_exploratory_analysis.ipynb  # Comprehensive statistical EDA
│   └── 03_model_experiments.ipynb    # Algorithm fitting and backtesting
│
├── pages/
│   ├── 1_Overview.py                  # Global Landscape, Rankings, Distributions
│   ├── 2_Historical_Trends.py         # Longitudinal Trajectories & Growth
│   ├── 3_Forecast_2030.py             # Core Forecast Engine & Prediction Intervals
│   ├── 4_Model_Comparison.py          # Backtesting Benchmark & Actual vs Pred
│   ├── 5_Country_Comparison.py        # Multi-Country Side-by-Side Analysis
│   └── 6_Disease_Burden.py            # GBD 2023 Burden (DALYs & PAFs) Context
│
├── reports/
│   ├── dataset_roles.md               # Detailed dataset inventory & specifications
│   ├── stage1_data_audit.md           # Stage 1 Quality Assurance Audit Report
│   ├── stage1_data_quality_report.json# Machine-readable QA metrics
│   ├── stage2_eda_summary.md          # Stage 2 Statistical EDA Summary Report
│   ├── technical_report.md            # In-depth architectural & empirical report
│   ├── model_evaluation.csv           # Out-of-sample backtesting metrics (760 rows)
│   └── results/                       # Persisted interactive charts (HTML) & figures (PNG)
│
├── src/
│   ├── data/
│   │   ├── load_data.py               # Safe data loading utilities
│   │   ├── preprocess.py              # Ingestion, filtering, and cleaning pipeline
│   │   └── validation.py              # Quality gates and assertion checks
│   ├── features/
│   │   └── build_features.py          # Leak-free time series lag/rolling features
│   ├── models/
│   │   ├── linear_regression.py       # Per-country OLS trend with prediction intervals
│   │   ├── arima.py                   # Statsmodels non-seasonal ARIMA with AIC selection
│   │   ├── holt.py                    # Holt Damped Additive Exponential Smoothing
│   │   ├── random_forest.py           # Pooled Multi-Country Random Forest
│   │   ├── evaluation.py              # Chronological metric calculation (MAE, RMSE, WAPE)
│   │   └── forecast.py                # Backtesting runner and 2030 projection engine
│   ├── utils/
│   │   ├── config.py                  # Centralized constants, paths, and hyperparameters
│   │   └── ui.py                      # Deep navy CSS styling, KPI cards, cached loaders
│   └── visualization/
│       ├── charts.py                  # Plotly and Seaborn visualization functions
│       └── maps.py                    # ISO-3 Plotly global choropleth mapping
│
└── tests/
    ├── test_preprocessing.py          # 12 Tests: Ingestion, schema, bounds, Slovenia
    ├── test_visualization.py          # 9 Tests: Chart generation and statistics
    ├── test_features.py               # 6 Tests: Leakage prevention and lag shifts
    ├── test_models.py                 # 6 Tests: Model fitting, interfaces, bounds
    └── test_forecasts.py              # 5 Tests: 2030 output dimensions and selection
```

---

## 3. Data Ingestion & Quality Gates (Stage 1)

The primary dataset is derived from the **WHO Global Health Observatory (GHO)**:
- **Raw Data:** 30,000 rows × 34 columns.
- **Filtering Slice:**
  - `IndicatorCode == 'NCD_DIABETES_PREVALENCE_AGESTD'` (Age-standardized prevalence)
  - `Dim1ValueCode == 'SEX_BTSX'` (Both sexes)
  - `Dim2ValueCode == 'AGEGROUP_YEARS18-PLUS'` (Adults 18+ years)
- **Quality Assurance Verification:**
  - **Output Dimensions:** Exactly **5,000 records** across **152 sovereign locations**.
  - **Unbroken Annual Coverage:** 151 locations have 33 continuous annual records (1990–2022).
  - **Slovenia Protocol:** Contains exactly 17 observations (2006–2022). Historical values for 1990–2005 are **not synthetically imputed or backfilled**, preventing empirical bias.
  - **Uncertainty Bound Integrity:** Zero violations ($prevalence\_low \le prevalence \le prevalence\_high$).
  - **Physical Boundaries:** All observations reside strictly in $[0.0\%, 100.0\%]$. Observed range: **2.33%** (Denmark, 1990) to **30.89%** (Pakistan, 2022).

---

## 4. Machine Learning & Forecasting Methodology

Each forecasting algorithm is encapsulated with a standardized object-oriented interface (`fit`, `predict`, `forecast`, `evaluate`):

### Model 1: Country-Specific Linear Regression
- Fits ordinary least squares on historical years: $y_t = \beta_0 + \beta_1 \cdot \text{year}_t$.
- Generates defensible t-distribution prediction intervals:
  $$\text{SE}_{\text{pred}} = s \sqrt{1 + \frac{1}{n} + \frac{(x_0 - \bar{x})^2}{\sum (x_i - \bar{x})^2}}$$

### Model 2: Non-Seasonal ARIMA
- Fits statsmodels ARIMA with automatic order selection across candidate parameter sets: $(1,1,0), (0,1,1), (1,1,1), (0,2,1), (1,2,1), (1,0,0)$.
- Selects the optimal order based on Akaike Information Criterion (AIC).
- Incorporates graceful convergence fallback to Random Walk with drift $(0,1,0)$.
- Produces analytical $95\%$ prediction intervals.

### Model 3: Holt Exponential Smoothing with Damped Trend
- Configured with additive trend and damping:
  $$\hat{y}_{t+h|t} = \ell_t + (\phi + \phi^2 + \dots + \phi^h) b_t$$
- Damping factor ($\phi < 1$) prevents explosive runaway linear extrapolations over multi-year horizons.
- Generates error-propagating prediction intervals expanding with $\sqrt{h}$.

### Model 4: Pooled Multi-Country Random Forest Regressor
- Pooled training across all 152 countries using leak-free feature vectors:
  $$\text{Features: } [\text{year}, \text{lag}_1, \text{lag}_2, \text{lag}_3, \text{rolling\_mean}_3, \text{location\_encoded}]$$
- **Recursive Forecasting:** For future projection years (2023–2030), lag features are updated dynamically using prior step predictions: $\text{lag}_1(t) = \hat{y}(t-1)$.
- Quantile-based ensemble prediction intervals derived from individual tree estimators.
- *Extrapolation Notice:* Tree-based models are inherently bounded by the minimum and maximum target values observed in the training split.

---

## 5. Empirical Out-of-Sample Backtesting Results

All models were evaluated using chronological time-series backtesting on a held-out 5-year test horizon (**2018–2022**), trained on data through **2017**:

| Model Name | Out-of-Sample MAE (% pts) | Out-of-Sample RMSE (% pts) | MAPE (%) | WAPE (%) | sMAPE (%) | Sovereign Countries Won (Lowest MAE) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ARIMA** | **0.0851** | **0.1058** | **0.71%** | **0.72%** | **0.71%** | **95 countries (62.5%)** |
| **Holt (Damped)** | **0.1283** | **0.1549** | **1.10%** | **1.13%** | **1.11%** | **31 countries (20.4%)** |
| **Random Forest** | **0.4942** | **0.5501** | **4.21%** | **4.24%** | **4.13%** | **19 countries (12.5%)** |
| **Persistence Baseline** | **0.7535** | **0.8429** | **6.10%** | **6.20%** | **6.36%** | *Reference Benchmark* |
| **Linear Regression** | **0.9857** | **1.0172** | **8.57%** | **8.60%** | **8.58%** | **7 countries (4.6%)** |

> **Key Finding:** ARIMA and Holt Damped Smoothing decisively outperform unconstrained linear regression and tree ensembles. ARIMA captures local stochastic persistence with the lowest overall error (MAE: 0.0851% pts), while Holt's damped trend provides robust, non-explosive extrapolations in 31 countries.

---

## 6. Installation & Execution Guide

### Prerequisites
- Python 3.11, 3.12, or 3.13
- Git

### 1. Clone & Set Up Environment
```bash
# Clone the repository
git clone https://github.com/your-username/diabforecast.git
cd diabforecast

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run Data Processing & Forecasting Pipeline
```bash
# 1. Run Data Ingestion, Cleaning & Quality Assurance
python -m src.data.preprocess

# 2. Generate Exploratory Data Analysis Artifacts
python scripts/generate_eda_artifacts.py

# 3. Execute Model Backtesting and Generate 2023–2030 Forecasts
python -m src.models.forecast
```

### 3. Launch Interactive Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 4. Run Automated Test Suite
```bash
python -m pytest tests -v
```
All **38 unit tests** should pass in ~12 seconds.

---

## 7. Streamlit Multipage Application Architecture

The frontend follows a modern healthcare SaaS aesthetic (Deep Navy `#0B132B`, Teal `#0D9488`, Cyan `#38BDF8`, and Slate `#1E293B`):
- **Landing Portal (`app.py`):** System overview, operational KPIs, interactive 2022 global choropleth map, and methodological standards.
- **Page 1: Overview Dashboard (`1_Overview.py`):** Cross-sectional rankings, WHO regional box plots, and parametric/non-parametric distribution metrics.
- **Page 2: Historical Trends (`2_Historical_Trends.py`):** Interactive 33-year trajectories with 95% uncertainty ribbons, secular growth tables, and filtered CSV downloads.
- **Page 3: Forecast 2030 (`3_Forecast_2030.py`):** Core projection interface featuring dynamic best-model selection, 8-year prediction intervals, and 2022–2030 change metrics.
- **Page 4: Model Comparison (`4_Model_Comparison.py`):** Empirical backtesting benchmark, actual vs. predicted validation plots, and error metric leaderboards.
- **Page 5: Country Comparison (`5_Country_Comparison.py`):** Multi-country cohort analysis, ranking shifts, and historical vs projected growth benchmarking.
- **Page 6: Disease Burden Context (`6_Disease_Burden.py`):** Macro-level GBD 2023 analysis featuring all-age DALY trends (+56.8% global surge), chronic disease comparisons, and Population Attributable Fractions (PAFs).

---

## 8. Limitations & Methodological Boundaries

1. **Macro-Level Ecological Nature:** WHO age-standardized estimates reflect national population averages. They do not capture intra-national socio-economic disparities or individual patient risk.
2. **Missing Primary Historical Series for Slovenia:** Slovenia's records commence in 2006. While empirical integrity is preserved by avoiding imputation, models for Slovenia are trained on a shorter series (17 years).
3. **Absence of Specific Sovereign Nations:** Certain countries (e.g. India) were not present in this specific WHO indicator extract.
4. **Tree Extrapolation Constraints:** Random Forest regression models cannot extrapolate beyond the upper bound of training targets, causing flattening over long forecast horizons.
5. **Separation of WHO and GBD Units:** GBD prevalence rates (per 100,000) and DALY counts represent distinct epidemiological constructs and cannot be merged into WHO country prevalence percentages.

---

## 9. Future Roadmap & Enhancements

- [ ] **Bayesian Structural Time Series (BSTS):** Incorporating prior distributions on trend slope and interventions.
- [ ] **Sub-National Disaggregation:** Ingesting provincial/state-level prevalence when standardized registries become available.
- [ ] **Exogenous Covariates:** Integrating longitudinal national BMI trajectories and food security indicators into vector autoregression (VAR) models.
- [ ] **Automated API Synchronization:** Connecting directly to the WHO GHO OData API for live data refreshes.

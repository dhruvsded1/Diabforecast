# DiabForecast — Complete Project Inventory & Workspace Audit

**Audit Date:** 2026-11-16  
**Auditor:** Senior ML Engineer & Academic Reviewer  
**Status:** Complete Technical Inventory  

---

## 1. Executive Summary

This inventory documents all technical assets, datasets, code modules, trained artifacts, evaluation summaries, and documentation files present in the `DiabForecast` repository. Each item has been verified directly via filesystem inspection.

---

## 2. Source Code Inventory

### 2.1 Core Python Architecture (`src/`)

| File Path | Purpose | Key Classes / Functions | Status |
| :--- | :--- | :--- | :--- |
| `src/__init__.py` | Package marker | Package initialization | Verified |
| `src/utils/config.py` | Central configuration | Global constants, path definitions, cohort filters, validation bounds | Verified |
| `src/utils/ui.py` | Streamlit styling & caching | `apply_custom_theme`, `render_disclaimer`, `render_kpi_card`, cached data loaders | Verified |
| `src/data/load_data.py` | Data loading utilities | `load_raw_who`, `load_processed_who`, `load_gbd_workbook`, file listers | Verified |
| `src/data/preprocess.py` | Preprocessing pipeline | `run_preprocessing_pipeline`, `generate_markdown_audit_report` | Verified |
| `src/data/validation.py` | Data validation & quality gates | `validate_raw_who_schema`, `validate_filter_consistency`, `validate_processed_data` | Verified |
| `src/features/build_features.py` | Feature engineering & splitting | `generate_time_series_features`, `create_chronological_splits`, `get_location_series` | Verified |
| `src/models/linear_regression.py` | Linear regression forecasting | `CountryLinearRegression` (OLS with t-distribution prediction intervals) | Verified |
| `src/models/arima.py` | Non-seasonal ARIMA forecasting | `CountryARIMA` (AIC order search across 6 candidate specs, convergence fallbacks) | Verified |
| `src/models/holt.py` | Holt exponential smoothing | `CountryHoltExponentialSmoothing` (damped additive trend, sqrt(h) prediction intervals) | Verified |
| `src/models/random_forest.py` | Multi-country tree ensemble | `PooledRandomForestForecaster` (pooled training, recursive autoregressive multi-step) | Verified |
| `src/models/evaluation.py` | Metric computation | `compute_metrics` (MAE, RMSE, MAPE, WAPE, sMAPE), `persistence_baseline_forecast` | Verified |
| `src/models/forecast.py` | Execution orchestrator | `run_chronological_backtesting`, `generate_all_forecasts_2030` | Verified |
| `src/visualization/charts.py` | Statistical & trend plotting | `plot_historical_trend`, `plot_prevalence_distribution`, `plot_regional_comparison`, `plot_country_rankings`, `plot_growth_analysis` | Verified |
| `src/visualization/maps.py` | Geographic choropleth mapping | `plot_global_choropleth`, `plot_regional_choropleth` (ISO-3 Plotly mapping) | Verified |

### 2.2 Streamlit Web Application

| File Path | Role | Key Components |
| :--- | :--- | :--- |
| `app.py` | Main entry point | Hero banner, global choropleth map (2022), operational KPIs, architecture guide |
| `pages/1_Overview.py` | Overview dashboard | Benchmark slider, regional boxplots, prevalence distributions, national rankings |
| `pages/2_Historical_Trends.py` | Longitudinal analysis | 33-year trajectories with WHO 95% uncertainty ribbons, secular growth leaderboard |
| `pages/3_Forecast_2030.py` | 2030 projections | Country-specific multi-model forecasts, prediction intervals, 2022–2030 change |
| `pages/4_Model_Comparison.py` | Out-of-sample backtesting | Model leaderboard, bar charts, actual vs predicted trajectory (2018–2022) |
| `pages/5_Country_Comparison.py` | Multi-country benchmarking | Cohort analysis, cross-country statistical matrix, ranking shifts |
| `pages/6_Disease_Burden.py` | Macro GBD 2023 context | All-age DALY surge (2010 vs 2023), chronic disease comparisons, PAF attributions |

### 2.3 Standalone Scripts (`scripts/`)

| Script Path | Purpose |
| :--- | :--- |
| `scripts/audit_inventory.py` | Automated inventory & schema inspection script |
| `scripts/create_model_experiments_notebook.py` | Generator for notebook 03 |
| `scripts/create_notebooks.py` | Generator for notebooks 01 and 02 |
| `scripts/generate_eda_artifacts.py` | Batch generation of EDA tables and HTML/PNG figures |

---

## 3. Dataset & Data Storage Inventory

### 3.1 Primary WHO Dataset

| File Path | Description | Format | Dimensions | Size |
| :--- | :--- | :--- | :--- | :--- |
| `data/raw/who_diabetes/data.csv` | Raw WHO Global Health Observatory extract | CSV | 30,000 rows × 34 cols | 6,561 KB |
| `data/processed/diabetes_18plus_both_sexes.csv` | Filtered target slice (18+, both sexes) | CSV | 5,000 rows × 16 cols | 609 KB |
| `data/interim/model_features.csv` | Engineered lag & rolling feature vectors | CSV | 5,000 rows × 12 cols | 733 KB |
| `data/processed/forecasts_2030.csv` | Multi-model projections (2023–2030) | CSV | 4,864 rows × 9 cols | 510 KB |

### 3.2 GBD 2023 Supplementary Workbooks (`data/raw/gbd2023/`)

| File Name | Sheet Name(s) | Max Rows × Cols | Primary Epidemiological Measure |
| :--- | :--- | :--- | :--- |
| `S1_Global_Age_Standardised_Prevalence_Rates.XLSX` | `sheet1` | 386 × 38 | Age-standardized prevalence rate per 100,000 |
| `S1_Geographic_Hierarchy.XLSX` | `sheet1` | 241 × 2 | GBD 2023 location hierarchy and level mapping |
| `S3_Global_All_Age_DALY_Counts.XLSX` | `sheet1` | 386 × 38 | Global all-age DALY counts by cause (2010, 2020, 2023) |
| `S9_Healthy_Life_Expectancy_By_Location_and_Sex.XLSX` | `sheet1` | 715 × 46 | Healthy life expectancy (HALE) by location & sex |
| `S10_Global_DALY_Counts_and_Age_Standardised_Rate_Changes.XLSX` | `sheet1` | 381 × 21 | % change in count & age-standardized rate of DALYs (2010–2023) |
| `S12_Locations_by_SDI_Group.XLSX` | `Sheet1` | 851 × 1 | Socio-Demographic Index (SDI) location classification |
| `S13A_Global_Risk_Factor_DALYs_and_PAFs.XLSX` | `sheet1` | 848 × 34 | Global all-age DALYs, PAFs, and rate changes by risk factor |
| `README.md` | N/A | N/A | Data source documentation and citation manifest |

### 3.3 Methodological Literature PDFs (`data/raw/research_papers/`)

| File Name | Topic / Domain | File Size |
| :--- | :--- | :--- |
| `Enhancing AI-driven forecasting of diabetes burden a comparative analysis of deep learning and statistical models.pdf` | Deep learning vs statistical time series for diabetes forecasting | 1,848 KB |
| `Burden of disease scenarios for 204 countries and territories, 2022–2050 a forecasting analysis for the Global Burden of Disease Study 2021.pdf` | GBD 2021 global forecasting methodology | 9,933 KB |
| `Beyond the 1.5°C planetary boundary AI-forecast of Global Disease Burden and Health inequities.pdf` | Planetary boundary and AI disease burden forecasting | 1,372 KB |
| `Depressive disorders burden attributable to childhood sexual abuse in China and India from 1990 to 2023 and prediction for 2040 Analysis of data from the Global Burden of Disease Study 2023.pdf` | GBD 2023 predictive modeling case study | 2,829 KB |

---

## 4. Trained Models, Notebooks & Reports

### 4.1 Machine Learning Models (`models/saved/`)

| Model Artifact | Algorithm | Size | Status |
| :--- | :--- | :--- | :--- |
| `final_random_forest.joblib` | `PooledRandomForestForecaster` (300 estimators, max_depth=6) | 2,823 KB | Verified & loadable |

### 4.2 Jupyter Notebooks (`notebooks/`)

| Notebook Name | Cells | Size | Objective |
| :--- | :--- | :--- | :--- |
| `01_dataset_audit.ipynb` | 8 cells | 3.1 KB | Schema verification, quality gate assertions |
| `02_exploratory_analysis.ipynb` | 14 cells | 4.4 KB | Parametric & non-parametric EDA, regional distributions |
| `03_model_experiments.ipynb` | 10 cells | 5.8 KB | Model fitting, backtesting, forecast generation |

### 4.3 Evaluation & Audit Reports (`reports/`)

| File Name | Format | Rows × Cols | Description |
| :--- | :--- | :--- | :--- |
| `reports/model_evaluation.csv` | CSV | 760 × 10 | 5-model out-of-sample backtesting metrics across 152 countries |
| `reports/research_report.md` | Markdown | 382 lines | Current research report text |
| `reports/stage1_data_audit.md` | Markdown | 252 lines | Stage 1 QA audit report |
| `reports/stage1_data_quality_report.json` | JSON | 42 lines | Machine-readable Stage 1 QA summary |
| `reports/stage2_eda_summary.md` | Markdown | 260 lines | Stage 2 EDA summary report |
| `reports/technical_report.md` | Markdown | 338 lines | Detailed system architecture and empirical report |
| `reports/dataset_roles.md` | Markdown | 425 lines | Dataset role separation and governance guidelines |
| `reports/project_planning.md` | Markdown | 290 lines | Project development roadmap |
| `reports/project_structure.md` | Markdown | 62 lines | File tree structure |
| `reports/results/country_rankings_2022.csv` | CSV | 152 × 7 | 2022 national prevalence rankings |
| `reports/results/country_growth_1990_2022.csv` | CSV | 151 × 5 | 1990–2022 secular growth rates |
| `reports/results/regional_summary_2022.csv` | CSV | 6 × 9 | WHO regional summary statistics |
| `reports/results/eda_summary_statistics.csv` | CSV | 2 × 12 | Parametric/non-parametric distribution stats |

---

## 5. Test Suite & Verification Assets

| Test File | Number of Tests | Coverage Area | Status |
| :--- | :--- | :--- | :--- |
| `tests/test_preprocessing.py` | 12 tests | Raw schema, cohort filters, row count, nulls, bounds, Slovenia, GBD accessibility | 12 / 12 Passed |
| `tests/test_features.py` | 6 tests | Lag accuracy, temporal leakage prevention, cross-country bleed, Slovenia lags | 6 / 6 Passed |
| `tests/test_models.py` | 6 tests | LR, ARIMA, Holt Damped, Random Forest fitting, bounds enforcement, Slovenia | 6 / 6 Passed |
| `tests/test_forecasts.py` | 5 tests | Output dimensions (4,864), year range (2023–2030), bounds, best-model coverage | 5 / 5 Passed |
| `tests/test_visualization.py` | 9 tests | Plotly figures, choropleth maps, growth tables, summary statistics | 9 / 9 Passed |
| **Total** | **38 tests** | **End-to-End System Test Suite** | **38 / 38 Passed (100%)** |

---

## 6. Discrepancy & Gap Analysis (Missing Files / Inconsistencies)

1. **Missing `research_report.pdf`:** The user prompt states: *"I have also provided my current research report (`research_report.pdf`)."* The PDF is not in the directory; only `reports/research_report.md` is present.
2. **Missing `data/processed/forecasts_2023_2030.csv`:** The existing file is named `forecasts_2030.csv`. Stage 7 requires `data/processed/forecasts_2023_2030.csv`.
3. **Missing Audit Reports Required by Specification:**
   - `reports/final_audit/project_inventory.md` (Created herein)
   - `reports/final_audit/model_evaluation.csv` (To be produced in Stage 5)
   - `reports/final_audit/country_level_evaluation.csv` (To be produced in Stage 5)
   - `reports/final_audit/evaluation_methodology.md` (To be produced in Stage 4/5)
   - `reports/final_audit/audit_summary.md` (To be produced in Stage 11/12)
   - `reports/DiabForecast_Final_Research_Report.docx` (To be produced in Stage 11)
   - `reports/DiabForecast_Final_Research_Report.pdf` (To be produced in Stage 11)

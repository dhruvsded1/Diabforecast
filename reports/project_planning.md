# DiabForecast — STRIPS Planning

**Project:** Global Diabetes Prevalence Analysis and Forecasting System

Each operator has: **Pre** (preconditions) | **Add** (new truths) | **Del** (removed truths)

---

## Initial → Goal State

| Initial State | Goal State |
|---|---|
| `raw_WHO_CSV_available` | `project_structure_ready` |
| `raw_GBD_workbooks_available` | `clean_data_saved` |
| `python_installed` | `EDA_complete` |
| `no_project_structure` | `features_built` |
| `no_clean_data` | `models_trained` |
| `no_EDA` | `evaluation_done` |
| `no_features` | `forecasts_generated` |
| `no_models` | `dashboard_running` |
| `no_evaluation` | `tests_passing` |
| `no_forecasts / no_dashboard / no_tests / no_documentation` | `documentation_complete` |

---

## Operators

### 1 · PROJECT_SETUP
**Pre:** `python_installed, raw_WHO_CSV_available, raw_GBD_workbooks_available`  
**Add:** `project_structure_ready, dependencies_installed, raw_data_placed`  
**Del:** `no_project_structure`

- Create `src/`, `data/`, `pages/`, `reports/`, `tests/`, `notebooks/`
- `pip install -r requirements.txt`
- Place raw data in `data/raw/who_diabetes/` and `data/raw/gbd2023/`
- **Output:** `requirements.txt`, `.gitignore`, folder structure

---

### 2 · DATA_CLEANING
**Pre:** `project_structure_ready, raw_data_placed, dependencies_installed`  
**Add:** `clean_data_saved, preprocessing_modules_ready`  
**Del:** `no_clean_data`

- Load raw CSV (30,000 rows) → filter to 5,000 rows (indicator / sex / age)
- Rename: `Period→year`, `FactValueNumeric→prevalence_pct`
- Validate nulls, duplicates, uncertainty bounds (low ≤ estimate ≤ high)
- Slovenia: 17 observations only — do not fabricate missing years
- **Output:** `data/processed/diabetes_18plus_both_sexes.csv`, `src/data/load_data.py`, `preprocess.py`, `validation.py`

---

### 3 · EXPLORATORY_DATA_ANALYSIS
**Pre:** `clean_data_saved, preprocessing_modules_ready`  
**Add:** `EDA_complete, summary_statistics_computed, visualizations_saved`  
**Del:** `no_EDA`

- Stats: mean, median, std, quartiles, skewness
- Charts: histograms, box plots, global trend (1990–2022), country rankings, regional comparison
- World choropleth map, uncertainty bands, fastest-growing countries
- **Output:** `reports/stage2_eda_summary.md`, CSVs + HTML charts in `reports/results/`, `src/visualization/charts.py`, `maps.py`

---

### 4 · FEATURE_ENGINEERING
**Pre:** `clean_data_saved, EDA_complete`  
**Add:** `features_built, feature_module_ready, interim_data_saved`  
**Del:** `no_features`

- Linear Reg: `year` only
- ARIMA / Holt: annual time series per country
- Random Forest: `lag_1`, `lag_2`, `lag_3`, `rolling_mean_3`, `location_encoded` (no leakage)
- **Output:** `data/interim/model_features.csv`, `src/features/build_features.py`

---

### 5 · MODEL_TRAINING
**Pre:** `features_built, interim_data_saved, feature_module_ready`  
**Add:** `models_trained, model_modules_ready, saved_model_available`  
**Del:** `no_models`

- Linear Regression, ARIMA, Holt (damped), Random Forest — all share `fit/predict/forecast/evaluate`
- Persistence baseline included
- **Output:** `src/models/{linear_regression,arima,holt,random_forest,evaluation}.py`, `models/saved/final_random_forest.joblib`

---

### 6 · MODEL_EVALUATION
**Pre:** `models_trained, model_modules_ready, clean_data_saved`  
**Add:** `evaluation_done, best_model_identified`  
**Del:** `no_evaluation`

- Train ≤2017, test 2018–2022 (chronological split)
- Metrics: MAE, RMSE, MAPE, sMAPE vs persistence baseline
- **Result:** ARIMA 95 countries · Holt 31 · RF 19 · Linear 7
- **Output:** `reports/model_evaluation.csv`, `src/models/forecast.py`

---

### 7 · FORECASTING_2030
**Pre:** `evaluation_done, best_model_identified, models_trained`  
**Add:** `forecasts_generated, forecast_data_saved`  
**Del:** `no_forecasts`

- Retrain on full data (1990–2022), forecast 2023–2030 for 152 countries × 4 models
- **Output:** `data/processed/forecasts_2030.csv` (4,864 rows)

---

### 8 · DASHBOARD_BUILD
**Pre:** `clean_data_saved, EDA_complete, forecasts_generated, evaluation_done`  
**Add:** `dashboard_running, all_pages_built`  
**Del:** `no_dashboard`

- `app.py` — landing page, global choropleth
- `pages/1_Overview.py` — rankings, distributions
- `pages/2_Historical_Trends.py` — time series + uncertainty ribbons
- `pages/3_Forecast_2030.py` — interactive forecasting
- `pages/4_Model_Comparison.py` — backtest, actual vs predicted
- `pages/5_Country_Comparison.py` — multi-country side-by-side
- `pages/6_Disease_Burden.py` — GBD context (DALYs, risk factors)
- **Output:** `app.py`, `pages/`, `src/utils/ui.py`

---

### 9 · TESTING_AND_DOCUMENTATION
**Pre:** `dashboard_running, forecasts_generated, evaluation_done, models_trained`  
**Add:** `tests_passing, documentation_complete`  
**Del:** `no_tests, no_documentation`

- Tests: preprocessing, visualization, features (lag / no-leakage), model interface, forecasts
- `pytest tests -v` → **38 tests passing**
- **Output:** `tests/test_*.py`, `README.md`, `reports/research_report.md`

---

## Dependency Chain

```
PROJECT_SETUP → DATA_CLEANING → EDA → FEATURE_ENGINEERING
  → MODEL_TRAINING → MODEL_EVALUATION → FORECASTING_2030
      ├── DASHBOARD_BUILD
      └── TESTING_AND_DOCUMENTATION
```

## State Trace

| Operator | Key Result |
|---|---|
| PROJECT_SETUP | Folders, deps, raw data in place |
| DATA_CLEANING | 5,000-row clean CSV saved |
| EDA | Stats, charts, choropleth done |
| FEATURE_ENGINEERING | Lag features, model-ready data saved |
| MODEL_TRAINING | 4 models + baseline implemented |
| MODEL_EVALUATION | ARIMA best (95/152 countries) |
| FORECASTING_2030 | 4,864 forecast records generated |
| DASHBOARD_BUILD | 7-page Streamlit app running |
| TESTING_AND_DOCS | 38 tests passing, docs complete |

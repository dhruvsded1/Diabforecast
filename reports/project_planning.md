# DiabForecast — Project Planning Document
## Using STRIPS (Stanford Research Institute Problem Solver)

**Project:** Global Diabetes Prevalence Analysis and Forecasting System  
**Approach:** STRIPS-based planning — each project phase is modelled as an operator with preconditions and effects

---

## What is STRIPS?

STRIPS is a planning method from artificial intelligence. Every task is written as an **operator** (action) with three parts:

- **Preconditions** — what must already be done before this task can start
- **Add List** — what new things become true after this task is finished
- **Delete List** — what is no longer true (old state removed) after this task

The project starts from an **Initial State** and ends at a **Goal State**. Each operator moves us one step closer to the goal.

---

## Initial State

```
{
  raw_WHO_CSV_available,
  raw_GBD_workbooks_available,
  python_installed,
  no_project_structure,
  no_clean_data,
  no_EDA,
  no_features,
  no_models,
  no_evaluation,
  no_forecasts,
  no_dashboard,
  no_tests,
  no_documentation
}
```

## Goal State

```
{
  project_structure_ready,
  clean_data_saved,
  EDA_complete,
  features_built,
  models_trained,
  evaluation_done,
  forecasts_generated,
  dashboard_running,
  tests_passing,
  documentation_complete
}
```

---

## STRIPS Operators

---

### Operator 1: PROJECT_SETUP

> Set up the folder structure, virtual environment, and dependencies.

**Preconditions:**
```
{ python_installed, raw_WHO_CSV_available, raw_GBD_workbooks_available }
```

**Add List:**
```
{ project_structure_ready, dependencies_installed, raw_data_placed, gitignore_created, requirements_file_created }
```

**Delete List:**
```
{ no_project_structure }
```

**Actions Taken:**
- Create folders: `src/`, `data/`, `pages/`, `reports/`, `tests/`, `notebooks/`
- Run `pip install -r requirements.txt`
- Place WHO CSV into `data/raw/who_diabetes/`
- Place GBD Excel files into `data/raw/gbd2023/`
- Create `.gitignore` and `requirements.txt`

**Output Files:**
- `requirements.txt`
- `.gitignore`
- Folder structure in place

---

### Operator 2: DATA_CLEANING

> Filter, validate, and save the clean working dataset.

**Preconditions:**
```
{ project_structure_ready, raw_data_placed, dependencies_installed }
```

**Add List:**
```
{ clean_data_saved, data_quality_report_generated, preprocessing_modules_ready }
```

**Delete List:**
```
{ no_clean_data }
```

**Actions Taken:**
- Load raw CSV (30,000 rows)
- Filter by indicator, sex, and age group → 5,000 rows
- Rename columns (`Period` → `year`, `FactValueNumeric` → `prevalence_pct`, etc.)
- Check for nulls, duplicates, and out-of-range values
- Validate uncertainty bounds (low ≤ estimate ≤ high)
- Note Slovenia has only 17 observations — do not fabricate missing years
- Save cleaned data

**Output Files:**
- `data/processed/diabetes_18plus_both_sexes.csv` (5,000 rows)
- `reports/stage1_data_audit.md`
- `reports/stage1_data_quality_report.json`
- `src/data/load_data.py`, `preprocess.py`, `validation.py`

---

### Operator 3: EXPLORATORY_DATA_ANALYSIS

> Understand the data through statistics, charts, and maps.

**Preconditions:**
```
{ clean_data_saved, preprocessing_modules_ready }
```

**Add List:**
```
{ EDA_complete, summary_statistics_computed, visualizations_saved, regional_analysis_done }
```

**Delete List:**
```
{ no_EDA }
```

**Actions Taken:**
- Compute mean, median, std, quartiles, skewness
- Plot prevalence distribution (histograms, box plots)
- Plot global trend over time (1990–2022)
- Create country rankings for 2022
- Build regional comparison charts
- Create a world choropleth map
- Analyse uncertainty bands
- Identify fastest-growing countries

**Output Files:**
- `reports/stage2_eda_summary.md`
- `reports/results/eda_summary_statistics.csv`
- `reports/results/regional_summary_2022.csv`
- Interactive HTML charts in `reports/results/`
- `src/visualization/charts.py`, `maps.py`
- `notebooks/01_dataset_audit.ipynb`, `02_exploratory_analysis.ipynb`

---

### Operator 4: FEATURE_ENGINEERING

> Build model-ready features from the clean dataset.

**Preconditions:**
```
{ clean_data_saved, EDA_complete }
```

**Add List:**
```
{ features_built, feature_module_ready, interim_data_saved }
```

**Delete List:**
```
{ no_features }
```

**Actions Taken:**
- For Linear Regression: use `year` as the only feature
- For ARIMA and Holt: prepare annual time series per country
- For Random Forest: create `lag_1`, `lag_2`, `lag_3`, `rolling_mean_3`, `location_encoded`
- Use only past observations for lag and rolling features (no data leakage)
- Do not interpolate Slovenia's missing years
- Save feature data

**Output Files:**
- `data/interim/model_features.csv`
- `src/features/build_features.py`

---

### Operator 5: MODEL_TRAINING

> Implement and train the four forecasting models.

**Preconditions:**
```
{ features_built, interim_data_saved, feature_module_ready }
```

**Add List:**
```
{ models_trained, model_modules_ready, saved_model_available }
```

**Delete List:**
```
{ no_models }
```

**Actions Taken:**
- Implement Linear Regression (one model per country, `year → prevalence`)
- Implement ARIMA (non-seasonal, per country)
- Implement Holt Exponential Smoothing with damped trend (per country)
- Implement Random Forest (uses lag features + encoded location)
- Each model follows the same interface: `fit()`, `predict()`, `forecast()`, `evaluate()`
- Implement a persistence baseline (predicts last known value)
- Save trained Random Forest model

**Output Files:**
- `src/models/linear_regression.py`
- `src/models/arima.py`
- `src/models/holt.py`
- `src/models/random_forest.py`
- `src/models/evaluation.py`
- `models/saved/final_random_forest.joblib`

---

### Operator 6: MODEL_EVALUATION

> Backtest all models fairly and compare their performance.

**Preconditions:**
```
{ models_trained, model_modules_ready, clean_data_saved }
```

**Add List:**
```
{ evaluation_done, best_model_identified, evaluation_report_saved }
```

**Delete List:**
```
{ no_evaluation }
```

**Actions Taken:**
- Split data chronologically: train on data up to 2017, test on 2018–2022
- Predict test period for each model for all 152 countries
- Compute MAE, RMSE, MAPE, sMAPE per model per country
- Compare against persistence baseline
- Find the best model for each country
- Result: ARIMA wins 95 countries, Holt wins 31, Random Forest wins 19, Linear wins 7

**Output Files:**
- `reports/model_evaluation.csv`
- `src/models/forecast.py`
- `notebooks/03_model_experiments.ipynb`

---

### Operator 7: FORECASTING_2030

> Generate future prevalence predictions through 2030.

**Preconditions:**
```
{ evaluation_done, best_model_identified, models_trained }
```

**Add List:**
```
{ forecasts_generated, forecast_data_saved }
```

**Delete List:**
```
{ no_forecasts }
```

**Actions Taken:**
- Retrain each model on all available data (1990–2022)
- Forecast years 2023–2030 for all 152 countries using all 4 models
- Total output: 4,864 forecast records (152 × 4 × 8)
- Save forecast results

**Output Files:**
- `data/processed/forecasts_2030.csv` (4,864 rows)

---

### Operator 8: DASHBOARD_BUILD

> Build the interactive Streamlit web application.

**Preconditions:**
```
{ clean_data_saved, EDA_complete, forecasts_generated, evaluation_done }
```

**Add List:**
```
{ dashboard_running, all_pages_built, UI_theme_applied }
```

**Delete List:**
```
{ no_dashboard }
```

**Actions Taken:**
- Build landing page (`app.py`) with global choropleth and project summary
- Build Overview page — country rankings, distributions, regional charts
- Build Historical Trends page — time series with uncertainty ribbons
- Build Forecast 2030 page — interactive country forecasting
- Build Model Comparison page — backtest results and actual vs predicted
- Build Country Comparison page — side-by-side multi-country analysis
- Build Disease Burden page — GBD context (DALYs, risk factors)
- Create shared UI theme and helper functions

**Output Files:**
- `app.py`
- `pages/1_Overview.py` through `pages/6_Disease_Burden.py`
- `src/utils/ui.py`

---

### Operator 9: TESTING_AND_DOCUMENTATION

> Write automated tests and finalise all project documentation.

**Preconditions:**
```
{ dashboard_running, forecasts_generated, evaluation_done, models_trained }
```

**Add List:**
```
{ tests_passing, documentation_complete }
```

**Delete List:**
```
{ no_tests, no_documentation }
```

**Actions Taken:**
- Write tests for data preprocessing (correct shape, types, ranges)
- Write tests for visualization functions (run without errors)
- Write tests for feature engineering (lag correctness, no leakage)
- Write tests for model interface (fit/predict/evaluate work)
- Write tests for forecasts (correct shape, valid ranges)
- Run: `python -m pytest tests -v` → 38 tests passing
- Write `README.md` with setup and run instructions
- Write research report
- Review code for comments and docstrings

**Output Files:**
- `tests/test_preprocessing.py`, `test_visualization.py`, `test_features.py`, `test_models.py`, `test_forecasts.py`
- `README.md`
- `reports/research_report.md`

---

## Operator Dependency Chain

This shows which operator must finish before the next one can start:

```
PROJECT_SETUP
      │
      ▼
DATA_CLEANING
      │
      ▼
EXPLORATORY_DATA_ANALYSIS
      │
      ▼
FEATURE_ENGINEERING
      │
      ▼
MODEL_TRAINING
      │
      ▼
MODEL_EVALUATION
      │
      ▼
FORECASTING_2030
      │
      ├──────────────────┐
      ▼                  ▼
DASHBOARD_BUILD    TESTING_AND_DOCUMENTATION
```

---

## State Trace

Below is how the world state changes as each operator executes:

| After Operator | Key State Changes |
|---|---|
| Initial | Raw data available, nothing built |
| PROJECT_SETUP | Folders, dependencies, and raw data in place |
| DATA_CLEANING | 5,000-row clean dataset saved |
| EDA | Statistics computed, charts and maps created |
| FEATURE_ENGINEERING | Lag features and model-ready data saved |
| MODEL_TRAINING | 4 models implemented and trained |
| MODEL_EVALUATION | Backtest done, ARIMA identified as best |
| FORECASTING_2030 | 4,864 forecast records generated |
| DASHBOARD_BUILD | 7-page Streamlit app running |
| TESTING_AND_DOCS | 38 tests passing, all reports complete |

---

*End of STRIPS Planning Document*

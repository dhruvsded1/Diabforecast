"""
Create notebooks/03_model_experiments.ipynb
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = ROOT / "notebooks"

nb = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# DiabForecast — Notebook 03: Machine Learning Model Experiments & Forecasting\n",
                "\n",
                "**Objective:** Experiment with 4 statistical and machine learning forecasting models:\n",
                "1. **Linear Regression (OLS):** Per-country parametric trend estimation with t-distribution prediction intervals.\n",
                "2. **ARIMA:** Non-seasonal autoregressive integrated moving average with AIC order selection and convergence fallbacks.\n",
                "3. **Holt Exponential Smoothing:** Additive damped trend exponential smoothing to prevent explosive extrapolations.\n",
                "4. **Random Forest Regressor:** Pooled cross-national non-linear tree ensemble with recursive autoregressive lag updating.\n",
                "\n",
                "**Validation Protocol:** Chronological out-of-sample backtesting on 2018–2022 (5 years), benchmarked against a Naive Persistence Baseline."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys\n",
                "from pathlib import Path\n",
                "sys.path.insert(0, str(Path.cwd().parent))\n",
                "\n",
                "import pandas as pd\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "\n",
                "from src.features.build_features import generate_time_series_features, create_chronological_splits, get_location_series\n",
                "from src.models.evaluation import compute_metrics, persistence_baseline_forecast\n",
                "from src.models.linear_regression import CountryLinearRegression\n",
                "from src.models.arima import CountryARIMA\n",
                "from src.models.holt import CountryHoltExponentialSmoothing\n",
                "from src.models.random_forest import PooledRandomForestForecaster\n",
                "\n",
                "feat_df = generate_time_series_features()\n",
                "print(f\"Loaded feature dataset: {feat_df.shape}\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 1. Chronological Split (Train: 1990–2017, Test: 2018–2022)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "train_df, test_df = create_chronological_splits(feat_df, val_years=5)\n",
                "print(f\"Train records: {len(train_df)} (Years: {train_df['year'].min()}–{train_df['year'].max()})\")\n",
                "print(f\"Test records: {len(test_df)} (Years: {test_df['year'].min()}–{test_df['year'].max()})\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 2. Model Fitting and Evaluation on Case Study (Pakistan)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "c_train = train_df[train_df['location'] == 'Pakistan'].sort_values('year')\n",
                "c_test = test_df[test_df['location'] == 'Pakistan'].sort_values('year')\n",
                "\n",
                "# Fit Models\n",
                "lr = CountryLinearRegression('Pakistan').fit(c_train['year'], c_train['prevalence_pct'])\n",
                "arima = CountryARIMA('Pakistan').fit(pd.Series(c_train['prevalence_pct'].values, index=c_train['year'].values))\n",
                "holt = CountryHoltExponentialSmoothing('Pakistan').fit(pd.Series(c_train['prevalence_pct'].values, index=c_train['year'].values))\n",
                "rf = PooledRandomForestForecaster(n_estimators=100, max_depth=6, random_state=42).fit(train_df)\n",
                "\n",
                "print(\"Pakistan Evaluations:\")\n",
                "print(\"Linear Regression:\", lr.evaluate(c_test['year'], c_test['prevalence_pct']))\n",
                "print(\"ARIMA:\", arima.evaluate(pd.Series(c_test['prevalence_pct'].values, index=c_test['year'].values)))\n",
                "print(\"Holt (Damped):\", holt.evaluate(pd.Series(c_test['prevalence_pct'].values, index=c_test['year'].values)))\n",
                "print(\"Random Forest:\", rf.evaluate_location(c_train, c_test, 'Pakistan'))"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 3. Overall Chronological Backtesting Results Summary (152 Countries)"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.utils.config import MODEL_EVALUATION_CSV\n",
                "eval_df = pd.read_csv(MODEL_EVALUATION_CSV)\n",
                "summary = eval_df.groupby('model_name')[['MAE', 'RMSE', 'MAPE', 'WAPE', 'sMAPE']].mean().round(4).sort_values('MAE')\n",
                "summary"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "## 4. 2023–2030 Forecast Projections Inspection"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "from src.utils.config import FORECASTS_2030_PATH\n",
                "fc_df = pd.read_csv(FORECASTS_2030_PATH)\n",
                "print(f\"Total forecast records: {len(fc_df)}\")\n",
                "top_2030 = fc_df[(fc_df['year'] == 2030) & (fc_df['is_best_model'] == True)].sort_values('predicted_prevalence', ascending=False)\n",
                "top_2030[['location', 'region', 'model_name', 'predicted_prevalence', 'forecast_lower', 'forecast_upper']].head(10)"
            ]
        }
    ],
    "metadata": {
        "language_info": {"name": "python", "version": "3.11"}
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open(NOTEBOOKS_DIR / "03_model_experiments.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)
print("Created notebooks/03_model_experiments.ipynb")


"""
Central Model Evaluation, Forecasting Engine, and Selection Module for DiabForecast.
Conducts chronological backtesting across all 152 countries, produces 2023-2030 forecasts,
and saves model objects and evaluation reports.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, List, Tuple, Optional
import os
import logging
import numpy as np
import pandas as pd
import joblib

from src.utils.config import (
    MODEL_FEATURES_PATH,
    PROCESSED_DATA_PATH,
    MODEL_EVALUATION_CSV,
    FORECASTS_2030_PATH,
    SAVED_MODELS_DIR,
    HISTORICAL_START_YEAR,
    HISTORICAL_END_YEAR,
    FORECAST_START_YEAR,
    FORECAST_END_YEAR,
)
from src.features.build_features import (
    generate_time_series_features,
    create_chronological_splits,
    get_location_series,
)
from src.models.evaluation import compute_metrics, persistence_baseline_forecast
from src.models.linear_regression import CountryLinearRegression
from src.models.arima import CountryARIMA
from src.models.holt import CountryHoltExponentialSmoothing
from src.models.random_forest import PooledRandomForestForecaster

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_chronological_backtesting(
    feat_df: Optional[pd.DataFrame] = None,
    val_years: int = 5
) -> pd.DataFrame:
    """
    Run chronological backtesting across all 152 countries on a held-out test window (2018-2022).
    Evaluates:
    - Persistence Baseline (Naive)
    - Linear Regression
    - ARIMA
    - Holt Exponential Smoothing (Damped)
    - Random Forest Regressor

    Returns
    -------
    pd.DataFrame
        Evaluation results table per location and model.
    """
    if feat_df is None:
        feat_df = generate_time_series_features()

    split_year = HISTORICAL_END_YEAR - val_years
    test_start = split_year + 1
    test_end = HISTORICAL_END_YEAR

    logger.info(
        "Starting chronological backtesting: Train <= %d, Test = %d-%d (%d years)",
        split_year, test_start, test_end, val_years
    )

    train_df, test_df = create_chronological_splits(feat_df, val_years=val_years)

    # Train pooled Random Forest on chronological train split
    logger.info("Training pooled Random Forest on training period <= %d...", split_year)
    rf_eval = PooledRandomForestForecaster(n_estimators=300, max_depth=6, random_state=42)
    rf_eval.fit(train_df)

    eval_rows = []
    locations = sorted(feat_df["location"].unique())

    for idx, loc in enumerate(locations):
        loc_train = train_df[train_df["location"] == loc].sort_values("year")
        loc_test = test_df[test_df["location"] == loc].sort_values("year")

        if loc_test.empty:
            continue

        train_years = loc_train["year"].values
        train_y = loc_train["prevalence_pct"].values
        test_years = loc_test["year"].values
        test_y = loc_test["prevalence_pct"].values
        train_series = pd.Series(train_y, index=train_years)
        test_series = pd.Series(test_y, index=test_years)

        # 1. Baseline: Persistence Naive
        base_preds = persistence_baseline_forecast(train_series, horizon=len(test_y))
        base_metrics = compute_metrics(test_y, base_preds)
        eval_rows.append({
            "location": loc,
            "model_name": "Persistence Baseline",
            "training_end_year": int(train_years[-1]),
            "test_start_year": int(test_start),
            "test_end_year": int(test_end),
            **base_metrics
        })

        # 2. Linear Regression
        try:
            lr = CountryLinearRegression(loc)
            lr.fit(train_years, train_y)
            lr_metrics = lr.evaluate(test_years, test_y)
            eval_rows.append({
                "location": loc,
                "model_name": "Linear Regression",
                "training_end_year": int(train_years[-1]),
                "test_start_year": int(test_start),
                "test_end_year": int(test_end),
                **lr_metrics
            })
        except Exception as e:
            logger.warning("Linear Regression failed for %s: %s", loc, e)

        # 3. ARIMA
        try:
            arima = CountryARIMA(loc)
            arima.fit(train_series)
            arima_metrics = arima.evaluate(test_series)
            eval_rows.append({
                "location": loc,
                "model_name": "ARIMA",
                "training_end_year": int(train_years[-1]),
                "test_start_year": int(test_start),
                "test_end_year": int(test_end),
                **arima_metrics
            })
        except Exception as e:
            logger.warning("ARIMA failed for %s: %s", loc, e)

        # 4. Holt (Damped)
        try:
            holt = CountryHoltExponentialSmoothing(loc)
            holt.fit(train_series)
            holt_metrics = holt.evaluate(test_series)
            eval_rows.append({
                "location": loc,
                "model_name": "Holt (Damped)",
                "training_end_year": int(train_years[-1]),
                "test_start_year": int(test_start),
                "test_end_year": int(test_end),
                **holt_metrics
            })
        except Exception as e:
            logger.warning("Holt failed for %s: %s", loc, e)

        # 5. Random Forest (Recursive)
        try:
            rf_metrics = rf_eval.evaluate_location(loc_train, loc_test, loc)
            eval_rows.append({
                "location": loc,
                "model_name": "Random Forest",
                "training_end_year": int(train_years[-1]),
                "test_start_year": int(test_start),
                "test_end_year": int(test_end),
                **rf_metrics
            })
        except Exception as e:
            logger.warning("Random Forest evaluation failed for %s: %s", loc, e)

    eval_df = pd.DataFrame(eval_rows)
    MODEL_EVALUATION_CSV.parent.mkdir(parents=True, exist_ok=True)
    eval_df.to_csv(MODEL_EVALUATION_CSV, index=False)
    logger.info("Saved backtesting evaluation results to: %s", MODEL_EVALUATION_CSV)

    return eval_df


def generate_all_forecasts_2030(
    feat_df: Optional[pd.DataFrame] = None,
    eval_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Train final models on complete 1990-2022 dataset and produce 2023-2030 forecasts
    for all 152 locations across all 4 models, plus tag the best-selected model per location.

    Returns
    -------
    pd.DataFrame
        Complete forecast table saved to data/processed/forecasts_2030.csv.
    """
    if feat_df is None:
        feat_df = generate_time_series_features()
    if eval_df is None:
        eval_df = run_chronological_backtesting(feat_df)

    logger.info("Training final models on full history (1990–2022) for 2023–2030 projections...")
    future_years = list(range(FORECAST_START_YEAR, FORECAST_END_YEAR + 1))  # 2023–2030

    # Train final pooled Random Forest on complete historical data
    final_rf = PooledRandomForestForecaster(n_estimators=300, max_depth=6, random_state=42)
    final_rf.fit(feat_df)

    # Save final RF model
    SAVED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_rf, SAVED_MODELS_DIR / "final_random_forest.joblib")

    # Determine best model per country from evaluation MAE (ignoring Persistence Baseline for selection)
    eval_models = eval_df[eval_df["model_name"] != "Persistence Baseline"]
    best_per_country = (
        eval_models.sort_values("MAE")
        .groupby("location")
        .first()["model_name"]
        .to_dict()
    )

    # Extract metadata lookup (location_code, region)
    meta_lookup = feat_df.groupby("location").first()[["location_code", "region"]].to_dict("index")

    forecast_dfs = []
    locations = sorted(feat_df["location"].unique())

    for loc in locations:
        loc_df = feat_df[feat_df["location"] == loc].sort_values("year")
        years = loc_df["year"].values
        y = loc_df["prevalence_pct"].values
        series = pd.Series(y, index=years)
        meta = meta_lookup[loc]

        best_model_name = best_per_country.get(loc, "Holt (Damped)")

        # 1. Linear Regression
        try:
            lr = CountryLinearRegression(loc)
            lr.fit(years, y)
            df_lr = lr.forecast(future_years)
            df_lr["location_code"] = meta["location_code"]
            df_lr["region"] = meta["region"]
            df_lr["is_best_model"] = (df_lr["model_name"] == best_model_name)
            forecast_dfs.append(df_lr)
        except Exception as e:
            logger.warning("LR forecast failed for %s: %s", loc, e)

        # 2. ARIMA
        try:
            arima = CountryARIMA(loc)
            arima.fit(series)
            df_arima = arima.forecast(future_years)
            df_arima["location_code"] = meta["location_code"]
            df_arima["region"] = meta["region"]
            df_arima["is_best_model"] = (df_arima["model_name"] == best_model_name)
            forecast_dfs.append(df_arima)
        except Exception as e:
            logger.warning("ARIMA forecast failed for %s: %s", loc, e)

        # 3. Holt (Damped)
        try:
            holt = CountryHoltExponentialSmoothing(loc)
            holt.fit(series)
            df_holt = holt.forecast(future_years)
            df_holt["location_code"] = meta["location_code"]
            df_holt["region"] = meta["region"]
            df_holt["is_best_model"] = (df_holt["model_name"] == best_model_name)
            forecast_dfs.append(df_holt)
        except Exception as e:
            logger.warning("Holt forecast failed for %s: %s", loc, e)

        # 4. Random Forest (Recursive)
        try:
            df_rf = final_rf.forecast_location(loc_df, future_years, loc)
            df_rf["location_code"] = meta["location_code"]
            df_rf["region"] = meta["region"]
            df_rf["is_best_model"] = (df_rf["model_name"] == best_model_name)
            forecast_dfs.append(df_rf)
        except Exception as e:
            logger.warning("RF forecast failed for %s: %s", loc, e)

    all_forecasts = pd.concat(forecast_dfs, ignore_index=True)

    # Enforce non-negativity and upper bound [0, 100]
    all_forecasts["predicted_prevalence"] = np.clip(all_forecasts["predicted_prevalence"], 0.0, 100.0)
    all_forecasts["forecast_lower"] = np.clip(all_forecasts["forecast_lower"], 0.0, 100.0)
    all_forecasts["forecast_upper"] = np.clip(all_forecasts["forecast_upper"], 0.0, 100.0)

    # Save to data/processed/forecasts_2030.csv
    FORECASTS_2030_PATH.parent.mkdir(parents=True, exist_ok=True)
    all_forecasts.to_csv(FORECASTS_2030_PATH, index=False)
    logger.info("Saved 2023–2030 forecasts to: %s (%d total rows)", FORECASTS_2030_PATH, len(all_forecasts))

    return all_forecasts


if __name__ == "__main__":
    feat_df = generate_time_series_features()
    eval_df = run_chronological_backtesting(feat_df)
    fc_df = generate_all_forecasts_2030(feat_df, eval_df)
    print("Forecasting and evaluation pipeline completed successfully!")

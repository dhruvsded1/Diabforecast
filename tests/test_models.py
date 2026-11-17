"""
Unit Tests for Stage 4: Machine Learning and Statistical Models.
"""
import pytest
import numpy as np
import pandas as pd

from src.data.load_data import load_processed_who
from src.features.build_features import generate_time_series_features, get_location_series
from src.models.evaluation import compute_metrics, persistence_baseline_forecast
from src.models.linear_regression import CountryLinearRegression
from src.models.arima import CountryARIMA
from src.models.holt import CountryHoltExponentialSmoothing
from src.models.random_forest import PooledRandomForestForecaster


@pytest.fixture(scope="module")
def feat_df():
    return generate_time_series_features()


def test_metrics_calculation():
    """Verify evaluation metric mathematical consistency."""
    y_true = np.array([10.0, 12.0, 14.0, 16.0, 18.0])
    y_pred = np.array([10.5, 11.5, 14.0, 15.0, 19.0])
    metrics = compute_metrics(y_true, y_pred)
    
    assert metrics["MAE"] >= 0.0
    assert metrics["RMSE"] >= metrics["MAE"]
    assert metrics["MAPE"] >= 0.0
    assert metrics["WAPE"] >= 0.0
    assert metrics["sMAPE"] >= 0.0


def test_linear_regression_model(feat_df):
    """Verify Linear Regression fits, predicts, and enforces [0, 100] bounds."""
    series = get_location_series(feat_df, "Egypt")
    years = series.index.values
    y = series.values

    lr = CountryLinearRegression("Egypt")
    lr.fit(years[:25], y[:25])
    
    preds = lr.predict(years[25:])
    assert len(preds) == len(years[25:])
    assert (preds >= 0.0).all() and (preds <= 100.0).all()

    fc_df = lr.forecast([2023, 2024, 2025, 2030])
    assert len(fc_df) == 4
    assert (fc_df["predicted_prevalence"] >= 0.0).all()
    assert (fc_df["forecast_lower"] <= fc_df["predicted_prevalence"]).all()
    assert (fc_df["predicted_prevalence"] <= fc_df["forecast_upper"]).all()


def test_arima_model(feat_df):
    """Verify ARIMA fits, predicts, and handles parameter orders with bounds."""
    series = get_location_series(feat_df, "Germany")
    train = series.iloc[:28]
    test = series.iloc[28:]

    arima = CountryARIMA("Germany")
    arima.fit(train)
    assert arima.is_fitted
    assert arima.fitted_order is not None

    preds = arima.predict(steps=len(test))
    assert len(preds) == len(test)
    assert (preds >= 0.0).all() and (preds <= 100.0).all()

    fc_df = arima.forecast(list(range(2023, 2031)))
    assert len(fc_df) == 8
    assert (fc_df["forecast_lower"] <= fc_df["forecast_upper"]).all()


def test_holt_damped_model(feat_df):
    """Verify Holt damped smoothing fits and forecasts with expanding uncertainty."""
    series = get_location_series(feat_df, "Mexico")
    train = series.iloc[:28]
    test = series.iloc[28:]

    holt = CountryHoltExponentialSmoothing("Mexico")
    holt.fit(train)
    assert holt.is_fitted

    preds = holt.predict(steps=len(test))
    assert len(preds) == len(test)

    fc_df = holt.forecast(list(range(2023, 2031)))
    assert len(fc_df) == 8
    # Uncertainty interval width must expand monotonically over horizon
    widths = (fc_df["forecast_upper"] - fc_df["forecast_lower"]).values
    assert (np.diff(widths) >= 0.0).all()


def test_random_forest_pooled_and_recursive(feat_df):
    """Verify Random Forest pooled training and recursive lag update."""
    rf = PooledRandomForestForecaster(n_estimators=50, max_depth=4, random_state=42)
    rf.fit(feat_df[feat_df["year"] <= 2017])
    assert rf.is_fitted

    loc_df = feat_df[feat_df["location"] == "Pakistan"].sort_values("year")
    fc_df = rf.forecast_location(loc_df, future_years=[2023, 2024, 2025], location="Pakistan")
    assert len(fc_df) == 3
    assert (fc_df["predicted_prevalence"] >= 0.0).all()
    assert (fc_df["predicted_prevalence"] <= 100.0).all()


def test_slovenia_edge_case_all_models(feat_df):
    """Verify all 4 models fit and forecast on Slovenia's shorter series (17 rows)."""
    slovenia_series = get_location_series(feat_df, "Slovenia")
    assert len(slovenia_series) == 17

    # Linear Regression
    lr = CountryLinearRegression("Slovenia").fit(slovenia_series.index, slovenia_series.values)
    assert len(lr.forecast([2023, 2024])) == 2

    # ARIMA
    arima = CountryARIMA("Slovenia").fit(slovenia_series)
    assert len(arima.forecast([2023, 2024])) == 2

    # Holt
    holt = CountryHoltExponentialSmoothing("Slovenia").fit(slovenia_series)
    assert len(holt.forecast([2023, 2024])) == 2


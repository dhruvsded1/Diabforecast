"""
Unit Tests for Stage 5 & 6: Forecast Output Validation and Model Selection.
"""
import pytest
import pandas as pd
import numpy as np

from src.utils.config import (
    FORECASTS_2030_PATH,
    MODEL_EVALUATION_CSV,
    EXPECTED_UNIQUE_LOCATIONS,
    FORECAST_START_YEAR,
    FORECAST_END_YEAR,
    FORECAST_HORIZON,
    MIN_PREVALENCE_PCT,
    MAX_PREVALENCE_PCT,
)


@pytest.fixture(scope="module")
def forecasts_df():
    assert FORECASTS_2030_PATH.exists(), "Forecasts file not generated"
    return pd.read_csv(FORECASTS_2030_PATH)


@pytest.fixture(scope="module")
def eval_df():
    assert MODEL_EVALUATION_CSV.exists(), "Evaluation file not generated"
    return pd.read_csv(MODEL_EVALUATION_CSV)


def test_forecast_dimensions(forecasts_df):
    """Verify exact output dimensions: 152 locations * 4 models * 8 years = 4,864 rows."""
    expected_rows = EXPECTED_UNIQUE_LOCATIONS * 4 * FORECAST_HORIZON
    assert len(forecasts_df) == expected_rows, f"Expected {expected_rows} rows, got {len(forecasts_df)}"


def test_forecast_years_and_horizon(forecasts_df):
    """Verify forecast covers strictly 2023 through 2030."""
    years = sorted(forecasts_df["year"].unique())
    assert years == list(range(FORECAST_START_YEAR, FORECAST_END_YEAR + 1))


def test_forecast_boundaries(forecasts_df):
    """Verify forecasts fall strictly within scientifically valid 0-100% bounds."""
    assert (forecasts_df["predicted_prevalence"] >= MIN_PREVALENCE_PCT).all()
    assert (forecasts_df["predicted_prevalence"] <= MAX_PREVALENCE_PCT).all()
    assert (forecasts_df["forecast_lower"] >= MIN_PREVALENCE_PCT).all()
    assert (forecasts_df["forecast_upper"] <= MAX_PREVALENCE_PCT).all()
    assert (forecasts_df["forecast_lower"] <= forecasts_df["forecast_upper"]).all()


def test_best_model_selection_coverage(forecasts_df):
    """Verify every single country has exactly one designated best model."""
    best_df = forecasts_df[forecasts_df["is_best_model"] == True]
    assert best_df["location"].nunique() == EXPECTED_UNIQUE_LOCATIONS
    # Each country must have exactly 8 years of best model forecasts
    loc_counts = best_df.groupby("location").size()
    assert (loc_counts == FORECAST_HORIZON).all()


def test_evaluation_table_structure(eval_df):
    """Verify evaluation table contains 760 records (152 locs * 5 models) with valid metrics."""
    assert len(eval_df) == EXPECTED_UNIQUE_LOCATIONS * 5
    for col in ["MAE", "RMSE", "MAPE", "WAPE", "sMAPE"]:
        assert col in eval_df.columns
        assert not eval_df[col].isna().any()
        assert (eval_df[col] >= 0.0).all()


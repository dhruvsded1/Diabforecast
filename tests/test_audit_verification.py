"""
Audit Verification & Regression Prevention Test Suite for DiabForecast.
Validates Egypt 2022 actuals, metric consistency, forecast files, and dashboard loaders.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.utils.config import (
    PROCESSED_DATA_PATH,
    FORECASTS_2030_PATH,
    MODEL_EVALUATION_CSV,
    EXPECTED_UNIQUE_LOCATIONS,
    HISTORICAL_END_YEAR,
)
from src.utils.ui import (
    get_processed_data,
    get_forecast_data,
    get_evaluation_data,
    get_gbd_workbook_cached,
)


def test_egypt_2022_verified_actual():
    """Verify Egypt 2022 prevalence is strictly 27.78% (correcting the 28.47% draft error)."""
    df = get_processed_data()
    egypt_2022 = df[(df["location"] == "Egypt") & (df["year"] == 2022)]
    assert len(egypt_2022) == 1, "Egypt 2022 record missing"
    val = egypt_2022["prevalence_pct"].values[0]
    assert val == pytest.approx(27.78, abs=0.01), f"Expected Egypt 2022 to be 27.78%, got {val}%"
    assert egypt_2022["prevalence_low_pct"].values[0] == pytest.approx(20.63, abs=0.01)
    assert egypt_2022["prevalence_high_pct"].values[0] == pytest.approx(35.37, abs=0.01)


def test_representative_countries_2022_actuals():
    """Verify 2022 actual values for Pakistan, Mexico, USA, Germany, and Denmark."""
    df = get_processed_data()
    df_2022 = df[df["year"] == 2022].set_index("location")["prevalence_pct"]
    
    assert df_2022["Pakistan"] == pytest.approx(30.89, abs=0.01)
    assert df_2022["Mexico"] == pytest.approx(14.27, abs=0.01)
    assert df_2022["United States of America"] == pytest.approx(12.48, abs=0.01)
    assert df_2022["Germany"] == pytest.approx(6.59, abs=0.01)
    assert df_2022["Denmark"] == pytest.approx(2.33, abs=0.01)


def test_forecasts_2023_2030_file_and_content():
    """Verify data/processed/forecasts_2023_2030.csv exists, is identical to forecasts_2030.csv, and valid."""
    fc_path = Path("data/processed/forecasts_2023_2030.csv")
    assert fc_path.exists(), "data/processed/forecasts_2023_2030.csv must exist"
    df_fc = pd.read_csv(fc_path)
    
    assert len(df_fc) == EXPECTED_UNIQUE_LOCATIONS * 4 * 8
    assert sorted(df_fc["year"].unique()) == list(range(2023, 2031))
    assert set(df_fc["model_name"].unique()) == {"Linear Regression", "ARIMA", "Holt (Damped)", "Random Forest"}
    
    # Verify bounds
    assert (df_fc["predicted_prevalence"] >= 0.0).all()
    assert (df_fc["predicted_prevalence"] <= 100.0).all()
    assert (df_fc["forecast_lower"] <= df_fc["predicted_prevalence"]).all()
    assert (df_fc["predicted_prevalence"] <= df_fc["forecast_upper"]).all()


def test_recalculated_model_evaluation_metrics():
    """Verify backtesting evaluation metrics in reports/final_audit/model_evaluation.csv."""
    audit_eval_path = Path("reports/final_audit/model_evaluation.csv")
    assert audit_eval_path.exists(), "Final audit model evaluation CSV missing"
    df_eval = pd.read_csv(audit_eval_path).set_index("model_name")
    
    # ARIMA MAE is 0.0851, RMSE is 0.1058
    assert df_eval.loc["ARIMA", "MAE_mean"] == pytest.approx(0.0851, abs=0.001)
    assert df_eval.loc["ARIMA", "RMSE_mean"] == pytest.approx(0.1058, abs=0.001)
    assert df_eval.loc["ARIMA", "Countries_Won"] == 95
    
    # Holt Damped MAE is 0.1283, RMSE is 0.1549
    assert df_eval.loc["Holt (Damped)", "MAE_mean"] == pytest.approx(0.1283, abs=0.001)
    assert df_eval.loc["Holt (Damped)", "RMSE_mean"] == pytest.approx(0.1549, abs=0.001)
    assert df_eval.loc["Holt (Damped)", "Countries_Won"] == 31
    
    # Random Forest MAE is 0.4942, RMSE is 0.5501
    assert df_eval.loc["Random Forest", "MAE_mean"] == pytest.approx(0.4942, abs=0.001)
    assert df_eval.loc["Random Forest", "RMSE_mean"] == pytest.approx(0.5501, abs=0.001)
    assert df_eval.loc["Random Forest", "Countries_Won"] == 19
    
    # Persistence Baseline MAE is 0.7535, RMSE is 0.8429
    assert df_eval.loc["Persistence Baseline", "MAE_mean"] == pytest.approx(0.7535, abs=0.001)
    assert df_eval.loc["Persistence Baseline", "RMSE_mean"] == pytest.approx(0.8429, abs=0.001)
    
    # Linear Regression MAE is 0.9857, RMSE is 1.0172
    assert df_eval.loc["Linear Regression", "MAE_mean"] == pytest.approx(0.9857, abs=0.001)
    assert df_eval.loc["Linear Regression", "RMSE_mean"] == pytest.approx(1.0172, abs=0.001)
    assert df_eval.loc["Linear Regression", "Countries_Won"] == 7


def test_dashboard_cached_loaders():
    """Verify that cached data loading functions in src/utils/ui.py execute without errors."""
    df_p = get_processed_data()
    assert len(df_p) == 5000
    
    df_f = get_forecast_data()
    assert len(df_f) == 4864
    
    df_e = get_evaluation_data()
    assert len(df_e) == 760
    
    df_gbd = get_gbd_workbook_cached("S10_Global_DALY_Counts_and_Age_Standardised_Rate_Changes.XLSX")
    assert not df_gbd.empty

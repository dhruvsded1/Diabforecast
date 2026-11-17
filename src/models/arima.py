"""
ARIMA Forecasting Model for DiabForecast.
Uses statsmodels ARIMA with automatic order selection and graceful convergence fallbacks.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, Optional, Tuple, List, Union
import logging
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from src.models.evaluation import compute_metrics

logger = logging.getLogger(__name__)


class CountryARIMA:
    """
    Location-specific ARIMA model for annual prevalence series.
    """

    CANDIDATE_ORDERS = [
        (1, 1, 0),
        (0, 1, 1),
        (1, 1, 1),
        (0, 2, 1),
        (1, 2, 1),
        (1, 0, 0)
    ]

    def __init__(self, location: str, order: Optional[Tuple[int, int, int]] = None):
        self.location = location
        self.preferred_order = order
        self.fitted_order: Optional[Tuple[int, int, int]] = None
        self.model_res = None
        self.is_fitted = False
        self.last_train_year: Optional[int] = None
        self.train_series: Optional[pd.Series] = None

    def fit(self, series: pd.Series) -> "CountryARIMA":
        """
        Fit ARIMA model on chronological series indexed by year.
        Selects lowest AIC among viable orders with convergence fallback.
        """
        # Ensure series is numeric and sorted by year
        s = series.sort_index().dropna().astype(float)
        if len(s) < 5:
            raise ValueError(f"Series too short ({len(s)}) to fit ARIMA for {self.location}")

        self.train_series = s
        self.last_train_year = int(s.index[-1])

        orders_to_try = [self.preferred_order] if self.preferred_order else self.CANDIDATE_ORDERS

        best_aic = float("inf")
        best_res = None
        best_order = None

        for ord_tuple in orders_to_try:
            if ord_tuple is None:
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model = ARIMA(s.values, order=ord_tuple)
                    res = model.fit()
                    if res.aic < best_aic:
                        best_aic = res.aic
                        best_res = res
                        best_order = ord_tuple
            except Exception as e:
                logger.debug("ARIMA%s failed for %s: %s", ord_tuple, self.location, e)
                continue

        # If all candidates failed, fallback to simple random walk with drift (0, 1, 0)
        if best_res is None:
            try:
                model = ARIMA(s.values, order=(0, 1, 0))
                best_res = model.fit()
                best_order = (0, 1, 0)
            except Exception:
                # Absolute fallback: AR(1)
                model = ARIMA(s.values, order=(1, 0, 0))
                best_res = model.fit()
                best_order = (1, 0, 0)

        self.model_res = best_res
        self.fitted_order = best_order
        self.is_fitted = True
        return self

    def predict(self, steps: int) -> np.ndarray:
        """Forecast point predictions for `steps` ahead."""
        if not self.is_fitted or self.model_res is None:
            raise RuntimeError("Model must be fitted before predict().")
        preds = self.model_res.forecast(steps=steps)
        return np.clip(preds, 0.0, 100.0)

    def forecast(
        self,
        future_years: Union[List[int], np.ndarray, pd.Series],
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Produce future forecasts with statsmodels prediction intervals.
        """
        if not self.is_fitted or self.model_res is None:
            raise RuntimeError("Model must be fitted before forecast().")

        f_years = np.asarray(future_years, dtype=int)
        steps = len(f_years)
        
        # Get forecast object
        fc_obj = self.model_res.get_forecast(steps=steps)
        preds = np.clip(fc_obj.predicted_mean, 0.0, 100.0)

        # Confidence intervals
        alpha = 1.0 - confidence_level
        conf_int = fc_obj.conf_int(alpha=alpha)
        lower = np.clip(conf_int[:, 0], 0.0, 100.0)
        upper = np.clip(conf_int[:, 1], 0.0, 100.0)

        df_out = pd.DataFrame({
            "year": f_years,
            "location": self.location,
            "model_name": "ARIMA",
            "predicted_prevalence": np.round(preds, 2),
            "forecast_lower": np.round(lower, 2),
            "forecast_upper": np.round(upper, 2)
        })
        return df_out

    def evaluate(
        self,
        test_series: pd.Series
    ) -> Dict[str, float]:
        """Evaluate out-of-sample forecast against actual test series."""
        steps = len(test_series)
        preds = self.predict(steps)
        return compute_metrics(test_series.values, preds)


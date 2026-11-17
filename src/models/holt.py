"""
Holt Exponential Smoothing with Damped Trend for DiabForecast.
Uses statsmodels ExponentialSmoothing configured with additive damped trend.
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
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from src.models.evaluation import compute_metrics

logger = logging.getLogger(__name__)


class CountryHoltExponentialSmoothing:
    """
    Location-specific Holt Exponential Smoothing with Damped Additive Trend.
    Prevents unrealistic linear runaway projections over multi-year horizons.
    """

    def __init__(self, location: str, damping_trend: Optional[float] = None, damping_slope: Optional[float] = None):
        self.location = location
        self.damping_trend = damping_trend if damping_trend is not None else damping_slope
        self.damping_slope = self.damping_trend  # alias
        self.model_res = None
        self.is_fitted = False
        self.residual_std: float = 0.0
        self.last_train_year: Optional[int] = None
        self.train_series: Optional[pd.Series] = None

    def fit(self, series: pd.Series) -> "CountryHoltExponentialSmoothing":
        """
        Fit Holt damped additive trend model.
        """
        s = series.sort_index().dropna().astype(float)
        if len(s) < 4:
            raise ValueError(f"Series too short ({len(s)}) for Holt smoothing in {self.location}")

        self.train_series = s
        self.last_train_year = int(s.index[-1])

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ExponentialSmoothing(
                    s.values,
                    trend="add",
                    damped_trend=True,
                    seasonal=None,
                    initialization_method="estimated"
                )
                if self.damping_trend is not None:
                    self.model_res = model.fit(damping_trend=self.damping_trend)
                else:
                    self.model_res = model.fit()
        except Exception as e:
            logger.warning("Holt damped fit failed for %s (%s); falling back to un-damped trend", self.location, e)
            model = ExponentialSmoothing(
                s.values,
                trend="add",
                damped_trend=False,
                seasonal=None,
                initialization_method="estimated"
            )
            self.model_res = model.fit()

        # Compute in-sample residual standard deviation
        in_sample_preds = self.model_res.fittedvalues
        residuals = s.values - in_sample_preds
        dof = max(len(s) - 3, 1)
        self.residual_std = float(np.sqrt(np.sum(residuals ** 2) / dof))
        self.is_fitted = True

        return self

    def predict(self, steps: int) -> np.ndarray:
        """Point forecast for next `steps` periods."""
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
        Produce future forecasts with error-propagation prediction intervals.
        Interval width expands with forecast horizon sqrt(h).
        """
        if not self.is_fitted or self.model_res is None:
            raise RuntimeError("Model must be fitted before forecast().")

        f_years = np.asarray(future_years, dtype=int)
        steps = len(f_years)
        preds = self.predict(steps)

        # Standard normal critical value for confidence_level
        z_crit = 1.96 if abs(confidence_level - 0.95) < 0.01 else 2.576
        # Horizon step expansion factor: sqrt(h)
        h_steps = np.arange(1, steps + 1)
        margin = z_crit * self.residual_std * np.sqrt(h_steps)

        lower = np.clip(preds - margin, 0.0, 100.0)
        upper = np.clip(preds + margin, 0.0, 100.0)

        df_out = pd.DataFrame({
            "year": f_years,
            "location": self.location,
            "model_name": "Holt (Damped)",
            "predicted_prevalence": np.round(preds, 2),
            "forecast_lower": np.round(lower, 2),
            "forecast_upper": np.round(upper, 2)
        })
        return df_out

    def evaluate(
        self,
        test_series: pd.Series
    ) -> Dict[str, float]:
        """Evaluate against chronological held-out test series."""
        steps = len(test_series)
        preds = self.predict(steps)
        return compute_metrics(test_series.values, preds)

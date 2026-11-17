"""
Linear Regression Forecasting Model for DiabForecast.
Fits per-location trend lines with parametric prediction intervals.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, Optional, Tuple, List, Union
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
import scipy.stats as stats

from src.models.evaluation import compute_metrics


class CountryLinearRegression:
    """
    Location-specific Linear Trend Model.
    y = beta_0 + beta_1 * (year - year_0)
    """

    def __init__(self, location: str):
        self.location = location
        self.model = LinearRegression()
        self.is_fitted = False
        self.train_years: Optional[np.ndarray] = None
        self.train_y: Optional[np.ndarray] = None
        self.residual_std: float = 0.0
        self.dof: int = 1

    def fit(self, years: Union[List[int], np.ndarray, pd.Series], y: Union[List[float], np.ndarray, pd.Series]) -> "CountryLinearRegression":
        """Fit linear regression on historical years and prevalence."""
        X = np.asarray(years, dtype=float).reshape(-1, 1)
        y_arr = np.asarray(y, dtype=float)

        self.model.fit(X, y_arr)
        self.train_years = X.flatten()
        self.train_y = y_arr
        self.is_fitted = True

        # Calculate residual standard error for prediction intervals
        y_pred = self.model.predict(X)
        residuals = y_arr - y_pred
        self.dof = max(len(y_arr) - 2, 1)
        self.residual_std = float(np.sqrt(np.sum(residuals ** 2) / self.dof))

        return self

    def predict(self, years: Union[List[int], np.ndarray, pd.Series]) -> np.ndarray:
        """Predict prevalence values for given years."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict().")
        X = np.asarray(years, dtype=float).reshape(-1, 1)
        preds = self.model.predict(X)
        return np.clip(preds, 0.0, 100.0)

    def forecast(
        self,
        future_years: Union[List[int], np.ndarray, pd.Series],
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Produce future forecasts with defensible OLS prediction intervals.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before forecast().")

        f_years = np.asarray(future_years, dtype=int)
        preds = self.predict(f_years)

        # Standard error of prediction: se_pred = s * sqrt(1 + 1/n + (x0 - x_bar)^2 / sum((xi - x_bar)^2))
        n = len(self.train_years)
        x_bar = np.mean(self.train_years)
        ss_x = np.sum((self.train_years - x_bar) ** 2)
        if ss_x <= 0:
            ss_x = 1.0

        t_crit = stats.t.ppf((1 + confidence_level) / 2.0, df=self.dof)
        se_pred = self.residual_std * np.sqrt(1.0 + (1.0 / n) + ((f_years - x_bar) ** 2) / ss_x)
        margin = t_crit * se_pred

        lower = np.clip(preds - margin, 0.0, 100.0)
        upper = np.clip(preds + margin, 0.0, 100.0)

        df_out = pd.DataFrame({
            "year": f_years,
            "location": self.location,
            "model_name": "Linear Regression",
            "predicted_prevalence": np.round(preds, 2),
            "forecast_lower": np.round(lower, 2),
            "forecast_upper": np.round(upper, 2)
        })
        return df_out

    def evaluate(
        self,
        test_years: Union[List[int], np.ndarray, pd.Series],
        test_y: Union[List[float], np.ndarray, pd.Series]
    ) -> Dict[str, float]:
        """Evaluate model against held-out actuals."""
        preds = self.predict(test_years)
        return compute_metrics(test_y, preds)


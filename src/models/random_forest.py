"""
Random Forest Regressor for DiabForecast.
Implements pooled cross-national training and autoregressive recursive forecasting.
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
from sklearn.ensemble import RandomForestRegressor

from src.models.evaluation import compute_metrics


FEATURE_COLS = ["year", "lag_1", "lag_2", "lag_3", "rolling_mean_3", "location_encoded"]


class PooledRandomForestForecaster:
    """
    Pooled Multi-Country Random Forest Model.
    Trains on historical country-year feature vectors and forecasts recursively.
    """

    def __init__(
        self,
        n_estimators: int = 300,
        max_depth: int = 6,
        min_samples_leaf: int = 2,
        random_state: int = 42
    ):
        self.rf = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
            n_jobs=-1
        )
        self.is_fitted = False
        self.train_features: List[str] = FEATURE_COLS
        self.feature_importances_: Optional[Dict[str, float]] = None

    def fit(self, train_df: pd.DataFrame) -> "PooledRandomForestForecaster":
        """
        Fit Random Forest model on feature-engineered training dataframe.
        Drops burn-in rows with missing lag values.
        """
        clean_train = train_df.dropna(subset=self.train_features + ["prevalence_pct"])
        X = clean_train[self.train_features]
        y = clean_train["prevalence_pct"]

        self.rf.fit(X, y)
        self.is_fitted = True
        self.feature_importances_ = {
            col: round(float(imp), 4)
            for col, imp in zip(self.train_features, self.rf.feature_importances_)
        }
        return self

    def predict_one_step(self, X_row: Union[pd.DataFrame, np.ndarray]) -> float:
        """Predict a single feature row."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before prediction.")
        val = self.rf.predict(X_row)[0]
        return float(np.clip(val, 0.0, 100.0))

    def forecast_location(
        self,
        location_hist_df: pd.DataFrame,
        future_years: List[int],
        location: str,
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Recursive autoregressive multi-step forecast for a single country.
        Updates lags dynamically using predictions from prior future years.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before forecast.")

        hist = location_hist_df.sort_values("year").copy()
        if hist.empty:
            raise ValueError(f"No historical data provided for {location}")

        loc_code = int(hist["location_encoded"].iloc[0])

        # Extract last 3 observed historical values
        last_y = hist["prevalence_pct"].values
        if len(last_y) < 3:
            raise ValueError(f"Need at least 3 historical points for lags in {location}")

        lag_1 = last_y[-1]
        lag_2 = last_y[-2]
        lag_3 = last_y[-3]

        predictions = []
        lowers = []
        uppers = []

        alpha = (1.0 - confidence_level) / 2.0
        pct_low = alpha * 100.0
        pct_high = (1.0 - alpha) * 100.0

        for yr in future_years:
            rolling_3 = (lag_1 + lag_2 + lag_3) / 3.0
            x_step = pd.DataFrame([{
                "year": yr,
                "lag_1": lag_1,
                "lag_2": lag_2,
                "lag_3": lag_3,
                "rolling_mean_3": rolling_3,
                "location_encoded": loc_code
            }])[self.train_features]

            # Ensemble prediction
            tree_preds = np.array([tree.predict(x_step.values)[0] for tree in self.rf.estimators_])
            y_hat = float(np.clip(np.mean(tree_preds), 0.0, 100.0))
            y_low = float(np.clip(np.percentile(tree_preds, pct_low), 0.0, 100.0))
            y_high = float(np.clip(np.percentile(tree_preds, pct_high), 0.0, 100.0))

            predictions.append(y_hat)
            lowers.append(y_low)
            uppers.append(y_high)

            # Shift lags forward recursively for next step
            lag_3 = lag_2
            lag_2 = lag_1
            lag_1 = y_hat

        return pd.DataFrame({
            "year": future_years,
            "location": location,
            "model_name": "Random Forest",
            "predicted_prevalence": np.round(predictions, 2),
            "forecast_lower": np.round(lowers, 2),
            "forecast_upper": np.round(uppers, 2)
        })

    def evaluate_location(
        self,
        location_train_df: pd.DataFrame,
        location_test_df: pd.DataFrame,
        location: str
    ) -> Dict[str, float]:
        """
        Evaluate recursive multi-step forecasting out-of-sample on held-out test years.
        """
        test_years = location_test_df.sort_values("year")["year"].tolist()
        y_true = location_test_df.sort_values("year")["prevalence_pct"].values

        pred_df = self.forecast_location(
            location_hist_df=location_train_df,
            future_years=test_years,
            location=location
        )
        return compute_metrics(y_true, pred_df["predicted_prevalence"].values)


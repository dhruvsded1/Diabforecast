"""
Evaluation Metrics and Backtesting Engine for DiabForecast.
Computes MAE, RMSE, MAPE, WAPE, and sMAPE.
"""
from typing import Dict, Any, Union, List
import numpy as np
import pandas as pd


def compute_metrics(
    y_true: Union[np.ndarray, pd.Series, List[float]],
    y_pred: Union[np.ndarray, pd.Series, List[float]]
) -> Dict[str, float]:
    """
    Compute standard chronological forecasting evaluation metrics.

    Parameters
    ----------
    y_true : array-like
        Ground truth actual values.
    y_pred : array-like
        Predicted values.

    Returns
    -------
    dict
        Dictionary containing MAE, RMSE, MAPE (%), WAPE (%), sMAPE (%).
    """
    yt = np.asarray(y_true, dtype=float)
    yp = np.asarray(y_pred, dtype=float)

    if len(yt) != len(yp):
        raise ValueError(f"Length mismatch: y_true has {len(yt)}, y_pred has {len(yp)}")
    if len(yt) == 0:
        return {"mae": np.nan, "rmse": np.nan, "mape": np.nan, "wape": np.nan, "smape": np.nan}

    errors = yt - yp
    abs_errors = np.abs(errors)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # WAPE: Sum(|Actual - Pred|) / Sum(|Actual|) * 100
    sum_yt = np.sum(np.abs(yt))
    wape = float((np.sum(abs_errors) / sum_yt * 100.0) if sum_yt > 0 else 0.0)

    # Safe MAPE: Avoid division by zero
    eps = 1e-6
    non_zero_mask = np.abs(yt) > eps
    if np.any(non_zero_mask):
        mape = float(np.mean(abs_errors[non_zero_mask] / np.abs(yt[non_zero_mask])) * 100.0)
    else:
        mape = 0.0

    # sMAPE: 200 * |yt - yp| / (|yt| + |yp|)
    denom = np.abs(yt) + np.abs(yp)
    valid_denom = denom > eps
    if np.any(valid_denom):
        smape = float(np.mean(2.0 * abs_errors[valid_denom] / denom[valid_denom]) * 100.0)
    else:
        smape = 0.0

    return {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "MAPE": round(mape, 2),
        "WAPE": round(wape, 2),
        "sMAPE": round(smape, 2),
    }


def persistence_baseline_forecast(
    train_series: pd.Series,
    horizon: int = 5
) -> np.ndarray:
    """
    Persistence / Naive Random Walk baseline:
    Predicts the last observed value for all future periods.
    """
    last_val = train_series.iloc[-1]
    return np.full(shape=horizon, fill_value=last_val, dtype=float)


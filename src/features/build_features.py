"""
Feature Engineering Module for DiabForecast.
Constructs leak-free chronological time-series features for forecasting models.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Tuple, Dict, Any, Optional
import pandas as pd
import numpy as np

from src.utils.config import (
    MODEL_FEATURES_PATH,
    HISTORICAL_START_YEAR,
    HISTORICAL_END_YEAR,
)
from src.data.load_data import load_processed_who


def generate_time_series_features(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Construct leak-free lag and rolling features for each geographic location.

    Parameters
    ----------
    df : pd.DataFrame, optional
        Preprocessed WHO dataframe. If None, loads from PROCESSED_DATA_PATH.

    Returns
    -------
    pd.DataFrame
        Dataframe sorted by location and year containing:
        - location, location_code, region, year
        - prevalence_pct, prevalence_low_pct, prevalence_high_pct
        - lag_1, lag_2, lag_3 (strictly past values)
        - rolling_mean_3 (mean of lag_1, lag_2, lag_3)
        - location_encoded (integer encoding for tree models)
    """
    if df is None:
        df = load_processed_who()

    # Ensure strictly sorted by location and chronological year
    df_sorted = df.sort_values(["location", "year"]).copy()

    records = []
    # Assign deterministic integer code for locations
    unique_locations = sorted(df_sorted["location"].unique())
    loc_to_idx = {loc: idx for idx, loc in enumerate(unique_locations)}

    for loc, grp in df_sorted.groupby("location", sort=True):
        grp = grp.sort_values("year").copy()
        
        # Verify chronological step is 1 year
        year_diff = grp["year"].diff()
        # First observation will have NaN diff; rest must be 1.0
        if not (year_diff.dropna() == 1.0).all():
            raise ValueError(f"Irregular non-annual year gap detected in {loc}")

        # Construct strictly past features to prevent future data leakage
        grp["lag_1"] = grp["prevalence_pct"].shift(1)
        grp["lag_2"] = grp["prevalence_pct"].shift(2)
        grp["lag_3"] = grp["prevalence_pct"].shift(3)
        
        # rolling_mean_3: average of previous 3 observations (t-1, t-2, t-3)
        grp["rolling_mean_3"] = (grp["lag_1"] + grp["lag_2"] + grp["lag_3"]) / 3.0
        
        grp["location_encoded"] = loc_to_idx[loc]
        records.append(grp)

    featured_df = pd.concat(records, ignore_index=True)

    # Save to data/interim/model_features.csv
    MODEL_FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
    featured_df.to_csv(MODEL_FEATURES_PATH, index=False)

    return featured_df


def create_chronological_splits(
    df: pd.DataFrame,
    val_years: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split time series chronologically into train and validation sets.
    Never shuffles data to prevent temporal lookahead bias.

    Parameters
    ----------
    df : pd.DataFrame
        Feature-engineered dataframe.
    val_years : int, default 5
        Number of test years at the end of the historical period (e.g. 2018–2022).

    Returns
    -------
    tuple of (train_df, val_df)
    """
    split_year = HISTORICAL_END_YEAR - val_years
    train_df = df[df["year"] <= split_year].copy()
    val_df = df[df["year"] > split_year].copy()

    return train_df, val_df


def get_location_series(
    df: pd.DataFrame,
    location: str,
    target_col: str = "prevalence_pct"
) -> pd.Series:
    """
    Extract a clean annual time series for a single country indexed by year.

    Parameters
    ----------
    df : pd.DataFrame
        Processed or feature-engineered dataframe.
    location : str
        Country name.
    target_col : str, default 'prevalence_pct'
        Column name to extract as series.

    Returns
    -------
    pd.Series
        Series indexed by integer year.
    """
    loc_df = df[df["location"] == location].sort_values("year")
    if loc_df.empty:
        raise KeyError(f"Location '{location}' not found in dataset.")
    
    series = pd.Series(
        data=loc_df[target_col].values,
        index=loc_df["year"].values,
        name=f"{location}_{target_col}"
    )
    return series


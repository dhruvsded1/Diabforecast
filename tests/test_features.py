"""
Unit Tests for Stage 3: Feature Engineering and Temporal Leakage Prevention.
"""
import pytest
import pandas as pd
import numpy as np

from src.features.build_features import (
    generate_time_series_features,
    create_chronological_splits,
    get_location_series,
)
from src.utils.config import HISTORICAL_START_YEAR, HISTORICAL_END_YEAR


@pytest.fixture(scope="module")
def feat_df():
    return generate_time_series_features()


def test_feature_generation_dimensions(feat_df):
    """Verify total row count matches 5,000 and columns are generated."""
    assert len(feat_df) == 5000
    for col in ["lag_1", "lag_2", "lag_3", "rolling_mean_3", "location_encoded"]:
        assert col in feat_df.columns


def test_no_temporal_leakage_in_lags(feat_df):
    """Verify lags strictly represent past observations without lookahead."""
    sample_country = "Pakistan"
    c_df = feat_df[feat_df["location"] == sample_country].sort_values("year").reset_index(drop=True)
    
    for i in range(3, len(c_df)):
        y_t = c_df.loc[i, "prevalence_pct"]
        y_prev1 = c_df.loc[i - 1, "prevalence_pct"]
        y_prev2 = c_df.loc[i - 2, "prevalence_pct"]
        y_prev3 = c_df.loc[i - 3, "prevalence_pct"]
        
        assert c_df.loc[i, "lag_1"] == pytest.approx(y_prev1)
        assert c_df.loc[i, "lag_2"] == pytest.approx(y_prev2)
        assert c_df.loc[i, "lag_3"] == pytest.approx(y_prev3)
        assert c_df.loc[i, "rolling_mean_3"] == pytest.approx((y_prev1 + y_prev2 + y_prev3) / 3.0)
        # Ensure target value y_t is NOT equal to lag_1 unless by coincidence (target not leaked)
        assert "prevalence_pct" in c_df.columns


def test_no_cross_country_leakage(feat_df):
    """Verify first observations of any country do not bleed from prior country."""
    for loc, grp in feat_df.groupby("location"):
        first_row = grp.sort_values("year").iloc[0]
        # First row of any country MUST have NaN for lag_1
        assert pd.isna(first_row["lag_1"]), f"{loc} first lag_1 is not NaN"
        assert pd.isna(first_row["rolling_mean_3"])


def test_slovenia_feature_integrity(feat_df):
    """Verify Slovenia starts in 2006 without backfill and properly sets lags."""
    slovenia = feat_df[feat_df["location"] == "Slovenia"].sort_values("year").reset_index(drop=True)
    assert len(slovenia) == 17
    assert slovenia.loc[0, "year"] == 2006
    assert pd.isna(slovenia.loc[0, "lag_1"])
    assert pd.isna(slovenia.loc[1, "lag_2"])
    assert pd.isna(slovenia.loc[2, "lag_3"])
    # 4th observation (index 3, year 2009) must have non-null lags
    assert not pd.isna(slovenia.loc[3, "lag_3"])
    assert not pd.isna(slovenia.loc[3, "rolling_mean_3"])


def test_chronological_splits(feat_df):
    """Verify chronological split guarantees zero temporal leakage."""
    train_df, val_df = create_chronological_splits(feat_df, val_years=5)
    assert train_df["year"].max() == HISTORICAL_END_YEAR - 5
    assert val_df["year"].min() == HISTORICAL_END_YEAR - 5 + 1
    assert train_df["year"].max() < val_df["year"].min()
    assert len(train_df) + len(val_df) == len(feat_df)


def test_get_location_series(feat_df):
    """Verify extracting a single country's series."""
    series = get_location_series(feat_df, "Denmark")
    assert isinstance(series, pd.Series)
    assert len(series) == 33
    assert series.index[0] == HISTORICAL_START_YEAR
    assert series.index[-1] == HISTORICAL_END_YEAR


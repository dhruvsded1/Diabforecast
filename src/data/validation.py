"""
Validation Rules and Quality Assurance for DiabForecast.
"""
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any, List
import pandas as pd
import numpy as np

from src.utils.config import (
    WHO_REQUIRED_COLUMNS,
    EXPECTED_ROW_COUNT,
    EXPECTED_UNIQUE_LOCATIONS,
    EXPECTED_STANDARD_SERIES_LENGTH,
    EXPECTED_SLOVENIA_SERIES_LENGTH,
    SLOVENIA_START_YEAR,
    HISTORICAL_START_YEAR,
    HISTORICAL_END_YEAR,
    MIN_PREVALENCE_PCT,
    MAX_PREVALENCE_PCT,
    FILTER_INDICATOR_CODE,
    FILTER_SEX_CODE,
    FILTER_AGE_CODE,
)


class DataValidationError(Exception):
    """Custom exception raised when data validation fails."""
    pass


def validate_raw_who_schema(df: pd.DataFrame) -> None:
    """Validate that raw WHO CSV contains required columns."""
    missing = [c for c in WHO_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataValidationError(f"Missing required columns in raw WHO dataset: {missing}")


def validate_filter_consistency(df: pd.DataFrame) -> None:
    """Validate that the filtered dataset contains only the target slice."""
    if not (df["IndicatorCode"] == FILTER_INDICATOR_CODE).all():
        raise DataValidationError("Found non-matching IndicatorCode in filtered slice.")
    if not (df["Dim1ValueCode"] == FILTER_SEX_CODE).all():
        raise DataValidationError("Found non-matching Dim1ValueCode in filtered slice.")
    if not (df["Dim2ValueCode"] == FILTER_AGE_CODE).all():
        raise DataValidationError("Found non-matching Dim2ValueCode in filtered slice.")


def validate_processed_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run comprehensive quality checks on the cleaned 18+ both sexes dataset.

    Raises
    ------
    DataValidationError
        If any validation rule or assertion is violated.

    Returns
    -------
    dict
        Detailed audit report dictionary.
    """
    # 1. Row count check
    if len(df) != EXPECTED_ROW_COUNT:
        raise DataValidationError(
            f"Expected {EXPECTED_ROW_COUNT} rows, found {len(df)}"
        )

    # 2. Key columns existence
    key_cols = ["location", "year", "prevalence_pct", "prevalence_low_pct", "prevalence_high_pct"]
    for c in key_cols:
        if c not in df.columns:
            raise DataValidationError(f"Missing mandatory column: {c}")

    # 3. Missing values check
    null_counts = df[key_cols].isna().sum()
    if null_counts.any():
        raise DataValidationError(f"Found missing values in critical columns:\n{null_counts}")

    # 4. Duplicate (location, year) check
    dups = df.duplicated(subset=["location", "year"]).sum()
    if dups > 0:
        raise DataValidationError(f"Found {dups} duplicate (location, year) records.")

    # 5. Uncertainty interval integrity: low <= estimate <= high
    invalid_bounds = df[
        (df["prevalence_low_pct"] > df["prevalence_pct"]) |
        (df["prevalence_pct"] > df["prevalence_high_pct"])
    ]
    if not invalid_bounds.empty:
        raise DataValidationError(
            f"Found {len(invalid_bounds)} rows violating low <= prevalence <= high bound conditions."
        )

    # 6. Prevalence % physical range [0, 100]
    out_of_range = df[
        (df["prevalence_pct"] < MIN_PREVALENCE_PCT) |
        (df["prevalence_pct"] > MAX_PREVALENCE_PCT) |
        (df["prevalence_low_pct"] < MIN_PREVALENCE_PCT) |
        (df["prevalence_high_pct"] > MAX_PREVALENCE_PCT)
    ]
    if not out_of_range.empty:
        raise DataValidationError(
            f"Found {len(out_of_range)} rows with prevalence percentage outside [{MIN_PREVALENCE_PCT}, {MAX_PREVALENCE_PCT}]."
        )

    # 7. Year range check
    if df["year"].min() != HISTORICAL_START_YEAR or df["year"].max() != HISTORICAL_END_YEAR:
        raise DataValidationError(
            f"Year range {df['year'].min()}-{df['year'].max()} does not match expected {HISTORICAL_START_YEAR}-{HISTORICAL_END_YEAR}."
        )

    # 8. Geographic coverage and series length
    unique_locations = df["location"].nunique()
    if unique_locations != EXPECTED_UNIQUE_LOCATIONS:
        raise DataValidationError(
            f"Expected {EXPECTED_UNIQUE_LOCATIONS} unique locations, found {unique_locations}."
        )

    loc_counts = df["location"].value_counts()
    standard_locs = loc_counts[loc_counts == EXPECTED_STANDARD_SERIES_LENGTH]
    if len(standard_locs) != (EXPECTED_UNIQUE_LOCATIONS - 1):
        raise DataValidationError(
            f"Expected {EXPECTED_UNIQUE_LOCATIONS - 1} locations with {EXPECTED_STANDARD_SERIES_LENGTH} years, found {len(standard_locs)}."
        )

    if "Slovenia" not in loc_counts:
        raise DataValidationError("Slovenia not found in dataset.")

    if loc_counts["Slovenia"] != EXPECTED_SLOVENIA_SERIES_LENGTH:
        raise DataValidationError(
            f"Expected Slovenia to have {EXPECTED_SLOVENIA_SERIES_LENGTH} observations, found {loc_counts['Slovenia']}."
        )

    slovenia_min_year = df[df["location"] == "Slovenia"]["year"].min()
    if slovenia_min_year != SLOVENIA_START_YEAR:
        raise DataValidationError(
            f"Expected Slovenia observations to start at {SLOVENIA_START_YEAR}, found {slovenia_min_year}."
        )

    # 9. Sort order check (must be sorted by location, then year)
    is_sorted = (
        df["location"].is_monotonic_increasing or
        df.sort_values(["location", "year"]).reset_index(drop=True).equals(df.reset_index(drop=True))
    )
    if not is_sorted:
        raise DataValidationError("Dataframe is not sorted by location and year.")

    # Compute audit summary
    full_years = set(range(HISTORICAL_START_YEAR, HISTORICAL_END_YEAR + 1))
    missing_years_by_loc = {}
    for loc, grp in df.groupby("location"):
        diff = sorted(full_years - set(grp["year"]))
        if diff:
            missing_years_by_loc[loc] = diff

    summary = {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "unique_locations": int(unique_locations),
        "year_range": [int(df["year"].min()), int(df["year"].max())],
        "locations_with_full_series": int(len(standard_locs)),
        "irregular_locations": missing_years_by_loc,
        "null_counts": {k: int(v) for k, v in null_counts.items()},
        "duplicate_count": int(dups),
        "bounds_valid": True,
        "range_valid": True,
        "prevalence_stats": {
            "min": float(df["prevalence_pct"].min()),
            "max": float(df["prevalence_pct"].max()),
            "mean_unweighted": float(df["prevalence_pct"].mean()),
            "median": float(df["prevalence_pct"].median()),
            "std": float(df["prevalence_pct"].std()),
            "q25": float(df["prevalence_pct"].quantile(0.25)),
            "q75": float(df["prevalence_pct"].quantile(0.75)),
        }
    }
    return summary


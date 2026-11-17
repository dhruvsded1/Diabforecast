"""
Unit Tests for Stage 1: Data Ingestion, Preprocessing, and Quality Gates.
"""
import pytest
import pandas as pd
from pathlib import Path

from src.utils.config import (
    WHO_DATA_PATH,
    PROCESSED_DATA_PATH,
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
from src.data.load_data import (
    load_raw_who,
    load_processed_who,
    load_gbd_workbook,
    list_available_gbd_files,
    list_available_papers,
)
from src.data.validation import (
    validate_raw_who_schema,
    validate_filter_consistency,
    validate_processed_data,
    DataValidationError,
)


def test_raw_who_file_exists_and_schema():
    """Verify raw WHO CSV exists and has all required schema columns."""
    assert WHO_DATA_PATH.exists(), f"Raw WHO CSV not found at {WHO_DATA_PATH}"
    df_raw = load_raw_who()
    assert len(df_raw) == 30000, f"Expected 30,000 raw rows, got {len(df_raw)}"
    assert df_raw.shape[1] == 34, f"Expected 34 raw columns, got {df_raw.shape[1]}"
    # Should not raise
    validate_raw_who_schema(df_raw)


def test_processed_dataset_row_count():
    """Verify cleaned dataset has exactly 5,000 records."""
    df = load_processed_who()
    assert len(df) == EXPECTED_ROW_COUNT, f"Expected {EXPECTED_ROW_COUNT} rows, found {len(df)}"


def test_processed_cohort_filters():
    """Verify that only the 18+ Both Sexes Age-standardized cohort is retained."""
    df = load_processed_who()
    assert (df["indicator_code"] == FILTER_INDICATOR_CODE).all()
    assert (df["sex_code"] == FILTER_SEX_CODE).all()
    assert (df["age_group_code"] == FILTER_AGE_CODE).all()


def test_unique_location_year_keys():
    """Verify there are no duplicate (location, year) pairs."""
    df = load_processed_who()
    duplicates = df.duplicated(subset=["location", "year"]).sum()
    assert duplicates == 0, f"Found {duplicates} duplicate location-year keys"


def test_missing_values():
    """Verify there are no nulls in location, year, prevalence, or uncertainty bounds."""
    df = load_processed_who()
    key_cols = ["location", "year", "prevalence_pct", "prevalence_low_pct", "prevalence_high_pct"]
    nulls = df[key_cols].isna().sum()
    assert nulls.sum() == 0, f"Found missing values in key columns:\n{nulls}"


def test_uncertainty_interval_integrity():
    """Verify prevalence_low_pct <= prevalence_pct <= prevalence_high_pct across all rows."""
    df = load_processed_who()
    violations = df[
        (df["prevalence_low_pct"] > df["prevalence_pct"]) |
        (df["prevalence_pct"] > df["prevalence_high_pct"])
    ]
    assert len(violations) == 0, f"Found {len(violations)} uncertainty interval bound violations"


def test_prevalence_physical_range():
    """Verify prevalence percentages and bounds fall strictly within [0, 100]."""
    df = load_processed_who()
    assert (df["prevalence_pct"] >= MIN_PREVALENCE_PCT).all()
    assert (df["prevalence_pct"] <= MAX_PREVALENCE_PCT).all()
    assert (df["prevalence_low_pct"] >= MIN_PREVALENCE_PCT).all()
    assert (df["prevalence_high_pct"] <= MAX_PREVALENCE_PCT).all()


def test_geographic_and_temporal_coverage():
    """Verify 152 locations, 1990-2022 coverage, and Slovenia special case."""
    df = load_processed_who()
    assert df["location"].nunique() == EXPECTED_UNIQUE_LOCATIONS
    assert df["year"].min() == HISTORICAL_START_YEAR
    assert df["year"].max() == HISTORICAL_END_YEAR

    loc_counts = df["location"].value_counts()
    assert (loc_counts == EXPECTED_STANDARD_SERIES_LENGTH).sum() == 151
    assert loc_counts["Slovenia"] == EXPECTED_SLOVENIA_SERIES_LENGTH

    slovenia_years = sorted(df[df["location"] == "Slovenia"]["year"].tolist())
    assert slovenia_years == list(range(SLOVENIA_START_YEAR, HISTORICAL_END_YEAR + 1))


def test_sorting_order():
    """Verify dataframe is strictly sorted by location, then year."""
    df = load_processed_who()
    expected_df = df.sort_values(["location", "year"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(df, expected_df)


def test_validation_error_on_invalid_data():
    """Verify validation raises DataValidationError when constraints are violated."""
    df = load_processed_who().copy()
    
    # Intentionally corrupt a bound
    corrupted_df = df.copy()
    corrupted_df.loc[0, "prevalence_low_pct"] = 99.0
    corrupted_df.loc[0, "prevalence_pct"] = 10.0
    
    with pytest.raises(DataValidationError):
        validate_processed_data(corrupted_df)


def test_gbd_supplementary_files_accessible():
    """Verify that all 7 GBD Excel files are present and readable."""
    files = list_available_gbd_files()
    assert len(files) == 7, f"Expected 7 GBD workbooks, found {len(files)}"
    # Verify reading one
    df_s1 = load_gbd_workbook("S1_Global_Age_Standardised_Prevalence_Rates.XLSX")
    assert not df_s1.empty


def test_research_papers_accessible():
    """Verify that all 4 research PDFs are present in raw storage."""
    papers = list_available_papers()
    assert len(papers) == 4, f"Expected 4 research PDFs, found {len(papers)}"
    assert any("Enhancing AI-driven" in p for p in papers)


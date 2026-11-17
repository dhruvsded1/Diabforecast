"""
Centralized Configuration for DiabForecast.
"""
from pathlib import Path

# Paths
SRC_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = SRC_DIR.parent

DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
WHO_DATA_PATH = RAW_DATA_DIR / "who_diabetes" / "data.csv"
GBD_DATA_DIR = RAW_DATA_DIR / "gbd2023"
PAPERS_DIR = RAW_DATA_DIR / "research_papers"

INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "diabetes_18plus_both_sexes.csv"
MODEL_FEATURES_PATH = INTERIM_DATA_DIR / "model_features.csv"
FORECASTS_2030_PATH = PROCESSED_DATA_DIR / "forecasts_2030.csv"

REPORTS_DIR = ROOT_DIR / "reports"
STAGE1_AUDIT_REPORT_JSON = REPORTS_DIR / "stage1_data_quality_report.json"
STAGE1_AUDIT_REPORT_MD = REPORTS_DIR / "stage1_data_audit.md"
DATASET_ROLES_REPORT_MD = REPORTS_DIR / "dataset_roles.md"
MODEL_EVALUATION_CSV = REPORTS_DIR / "model_evaluation.csv"

SAVED_MODELS_DIR = ROOT_DIR / "models" / "saved"

# WHO Filter Settings
FILTER_INDICATOR_CODE = "NCD_DIABETES_PREVALENCE_AGESTD"
FILTER_SEX_CODE = "SEX_BTSX"                    # Both sexes
FILTER_AGE_CODE = "AGEGROUP_YEARS18-PLUS"       # 18+ years

# Time Horizon
HISTORICAL_START_YEAR = 1990
HISTORICAL_END_YEAR = 2022
FORECAST_START_YEAR = 2023
FORECAST_END_YEAR = 2030
FORECAST_HORIZON = 8  # 2023 to 2030

# Expected Data Attributes
EXPECTED_ROW_COUNT = 5000
EXPECTED_UNIQUE_LOCATIONS = 152
EXPECTED_STANDARD_SERIES_LENGTH = 33
EXPECTED_SLOVENIA_SERIES_LENGTH = 17
SLOVENIA_START_YEAR = 2006

# Prevalence Boundaries
MIN_PREVALENCE_PCT = 0.0
MAX_PREVALENCE_PCT = 100.0

# Required raw WHO columns
WHO_REQUIRED_COLUMNS = [
    "IndicatorCode",
    "Indicator",
    "ParentLocationCode",
    "ParentLocation",
    "SpatialDimValueCode",
    "Location",
    "Period",
    "IsLatestYear",
    "Dim1ValueCode",
    "Dim1",
    "Dim2ValueCode",
    "Dim2",
    "FactValueNumeric",
    "FactValueNumericLow",
    "FactValueNumericHigh",
    "DateModified",
]

# Cleaned dataset column definitions
CLEANED_COLUMN_TYPES = {
    "indicator_code": "string",
    "indicator": "string",
    "location_code": "string",
    "location": "string",
    "region_code": "string",
    "region": "string",
    "year": "int64",
    "sex_code": "string",
    "sex": "string",
    "age_group_code": "string",
    "age_group": "string",
    "prevalence_pct": "float64",
    "prevalence_low_pct": "float64",
    "prevalence_high_pct": "float64",
    "is_latest_year": "bool",
    "date_modified": "string",
}

# GBD Supplementary File Names
GBD_FILES = {
    "S1_PREVALENCE": "S1_Global_Age_Standardised_Prevalence_Rates.XLSX",
    "S3_DALY_COUNTS": "S3_Global_All_Age_DALY_Counts.XLSX",
    "S10_DALY_CHANGES": "S10_Global_DALY_Counts_and_Age_Standardised_Rate_Changes.XLSX",
    "S13A_RISK_FACTORS": "S13A_Global_Risk_Factor_DALYs_and_PAFs.XLSX",
    "S9_HALE": "S9_Healthy_Life_Expectancy_By_Location_and_Sex.XLSX",
    "S12_SDI": "S12_Locations_by_SDI_Group.XLSX",
    "S1_HIERARCHY": "S1_Geographic_Hierarchy.XLSX",
}


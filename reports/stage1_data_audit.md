# DiabForecast — Stage 1 Data Quality & Ingestion Audit Report

**Report Generation Date:** 2026-11-13  
**Status:** VALIDATION PASSED (Zero Errors, Zero Duplicates, Zero Missing Values)  
**Primary Dataset:** WHO Age-standardized Diabetes Prevalence (`data.csv`)

---

## 1. Executive Summary

The primary dataset from the World Health Organization (WHO) was ingested, verified against schema integrity constraints, filtered to the designated target cohort (18+ years, both sexes), cleansed of formatting anomalies, and structured for time-series feature engineering.

- **Raw Dataset Dimensions:** 30,000 rows × 34 columns
- **Selected Cohort Dimensions:** 5,000 rows × 16 columns
- **Unique Geographic Locations:** 152 sovereign countries / territories
- **Historical Period Coverage:** 1990 – 2022 (33 continuous calendar years)
- **Primary Target Variable:** `prevalence_pct` (Age-standardized diabetes prevalence percentage)
- **Uncertainty Bounds:** `prevalence_low_pct` (95% lower bound) and `prevalence_high_pct` (95% upper bound)

---

## 2. Ingestion & Quality Gates Verification

| Quality Gate | Condition / Rule | Result | Status |
| :--- | :--- | :--- | :--- |
| **Cohort Filter** | `IndicatorCode == 'NCD_DIABETES_PREVALENCE_AGESTD'`, `Dim1ValueCode == 'SEX_BTSX'`, `Dim2ValueCode == 'AGEGROUP_YEARS18-PLUS'` | Exactly 5,000 observations selected | **PASSED** |
| **Row Count** | Expected = 5,000 | 5,000 rows | **PASSED** |
| **Missing Values** | Key / Target / Uncertainty columns (`location`, `year`, `prevalence_pct`, `prevalence_low_pct`, `prevalence_high_pct`) | 0 nulls across all 5,000 rows | **PASSED** |
| **Duplicate Keys** | Unique constraint on `(location, year)` | 0 duplicate keys | **PASSED** |
| **Uncertainty Interval Integrity** | `prevalence_low_pct <= prevalence_pct <= prevalence_high_pct` | 0 violations across all 5,000 rows | **PASSED** |
| **Physical Value Range** | `0.0% <= prevalence_pct <= 100.0%` | Values span 2.33% to 30.89% | **PASSED** |
| **Chronological Continuity** | Complete annual series (1990–2022) | 151 locations have all 33 years | **PASSED** |
| **Irregular Series Integrity** | Slovenia coverage without fabricated backfilling | 17 observations (2006–2022) preserved | **PASSED** |

---

## 3. Geographic Coverage & Slovenia Treatment

- **Standard Locations (151):** 151 countries have 33 unbroken annual observations from 1990 to 2022.
- **Slovenia (17 observations):** Starts in 2006 and runs through 2022.
  - **Epidemiological Protocol:** No imputation or synthetic backfilling has been performed for 1990–2005. Fabricating estimates would introduce non-empirical bias. Models for Slovenia will strictly train on observed history (2006–2022).
- **India Absence Note:** India is not present in this specific WHO indicator dataset (`SpatialDimValueCode` IND absent). Country coverage is strictly 152 countries.

---

## 4. Descriptive Statistics (Population-Unweighted)

> [!NOTE]
> All summary figures below represent population-unweighted cross-national averages across the 5,000 observations. They reflect the distribution of country-level age-standardized estimates, not global population-weighted prevalence.

- **Minimum Observed Prevalence:** 2.33% (Denmark, 1990)
- **Maximum Observed Prevalence:** 30.89% (Pakistan, 2022)
- **Unweighted Mean Prevalence:** 9.9669%
- **Median Prevalence:** 8.33%
- **Standard Deviation:** 5.1511%
- **Interquartile Range (IQR):** 6.25% (Q1) – 12.31% (Q3)

---

## 5. Year 2022 Cross-Sectional Snapshot

### Highest 5 Prevalence Locations (2022)
| Location | WHO Region | Prevalence (%) | 95% Uncertainty Low (%) | 95% Uncertainty High (%) |
| :--- | :--- | :--- | :--- | :--- |
| Pakistan | Eastern Mediterranean | 30.89% | 23.71% | 38.58% |
| Trinidad and Tobago | Americas | 28.08% | 16.77% | 41.11% |
| Libya | Eastern Mediterranean | 28.00% | 23.39% | 32.81% |
| Egypt | Eastern Mediterranean | 27.78% | 20.63% | 35.37% |
| Kuwait | Eastern Mediterranean | 26.77% | 19.32% | 34.83% |

### Lowest 5 Prevalence Locations (2022)
| Location | WHO Region | Prevalence (%) | 95% Uncertainty Low (%) | 95% Uncertainty High (%) |
| :--- | :--- | :--- | :--- | :--- |
| Denmark | Europe | 2.33% | 1.68% | 3.09% |
| France | Europe | 2.69% | 2.00% | 3.54% |
| Spain | Europe | 3.61% | 2.37% | 5.17% |
| Switzerland | Europe | 4.29% | 2.95% | 5.99% |
| Uganda | Africa | 5.16% | 3.45% | 7.29% |

---

## 6. Preprocessing Output File

- **Processed CSV Path:** `data/processed/diabetes_18plus_both_sexes.csv`
- **Output Record Count:** 5,000 rows
- **Output Schema:**
  1. `indicator_code` (str): `NCD_DIABETES_PREVALENCE_AGESTD`
  2. `indicator` (str): WHO indicator description
  3. `location_code` (str): ISO 3-letter spatial dimension code
  4. `location` (str): Country/territory name
  5. `region_code` (str): WHO parent region code (e.g., AMR, EUR, EMR, AFR, SEAR, WPR)
  6. `region` (str): WHO parent region name
  7. `year` (int): 1990–2022
  8. `sex_code` (str): `SEX_BTSX`
  9. `sex` (str): Both sexes
  10. `age_group_code` (str): `AGEGROUP_YEARS18-PLUS`
  11. `age_group` (str): 18+ years
  12. `prevalence_pct` (float): Age-standardized diabetes prevalence percentage
  13. `prevalence_low_pct` (float): Lower bound of 95% uncertainty interval
  14. `prevalence_high_pct` (float): Upper bound of 95% uncertainty interval
  15. `is_latest_year` (bool): Boolean flag for year == 2022
  16. `date_modified` (str): Source publication timestamp

---

## 7. Stage 1 Sign-Off

The data pipeline has completed all verification checks with zero warnings and zero data anomalies. The processed dataset is ready for feature engineering, model training, and dashboard integration upon user approval.

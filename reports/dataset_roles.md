# DiabForecast — Comprehensive Dataset Inventory & Role Specification

**Project:** DiabForecast — Global Diabetes Prevalence Analysis and Forecasting System  
**Audit Timestamp:** 2026-11-16  
**Status:** Ingested, Verified, Quality-Checked

---

## 1. Executive Overview

DiabForecast is an epidemiological forecasting application built upon official World Health Organization (WHO) and Global Burden of Disease (GBD 2023) health data. 

To maintain scientific integrity and prevent invalid causal inferences, the dataset architecture maintains strict operational separation between:
1. **Primary Forecasting Target (WHO Country Time Series):** Age-standardized diabetes prevalence percentage (%) in adults (18+ years, both sexes) for 152 countries from 1990 through 2022.
2. **Contextual Disease Burden (GBD 2023 Supplementary Workbooks):** Global-level DALY counts, rates per 100,000, risk-factor attributable fractions, and SDI groupings used strictly for contextual intelligence and burden dashboards.
3. **Methodological Literature (Research Papers):** Peer-reviewed literature providing epidemiological context and empirical forecasting benchmarks.

---

## 2. Primary Training & Forecasting Dataset (WHO)

- **Source File:** `data/raw/who_diabetes/data.csv`
- **File Size:** 8,036,308 bytes (~8.04 MB)
- **Raw Dimensions:** 30,000 rows × 34 columns
- **Original Source:** World Health Organization Global Health Observatory (GHO)
- **Target Indicator:** `NCD_DIABETES_PREVALENCE_AGESTD` (Age-standardized diabetes prevalence)
- **Target Subpopulation:** Adults aged 18+ years (`AGEGROUP_YEARS18-PLUS`), Both sexes (`SEX_BTSX`)
- **Processed File:** `data/processed/diabetes_18plus_both_sexes.csv`
- **Processed Dimensions:** Exactly 5,000 rows × 16 columns

### Filter & Selection Logic
```python
filtered = raw_df[
    (raw_df["IndicatorCode"] == "NCD_DIABETES_PREVALENCE_AGESTD") &
    (raw_df["Dim1ValueCode"] == "SEX_BTSX") &
    (raw_df["Dim2ValueCode"] == "AGEGROUP_YEARS18-PLUS")
]
```

### Coverage & Series Completeness
- **Unique Sovereign Locations:** 152 countries / territories across 6 WHO regions (AFR, AMR, EMR, EUR, SEAR, WPR).
- **Time Horizon:** 1990 to 2022 (33 continuous years).
- **Complete Series (151 countries):** 151 countries contain all 33 annual observations (151 × 33 = 4,983 records).
- **Irregular Series (Slovenia):** Contains exactly 17 annual observations (2006 to 2022; 4,983 + 17 = 5,000 records).
  - *Imputation Policy:* Earlier observations (1990–2005) are intentionally **NOT** imputed or synthesized. Treating missing historical data as zero or using synthetic interpolation would introduce severe bias into empirical models.
- **Missing Value Count:** 0 in `location`, `year`, `prevalence_pct`, `prevalence_low_pct`, `prevalence_high_pct`.
- **Duplicate Keys:** 0 duplicate `(location, year)` pairs.
- **Uncertainty Bound Integrity:** 100% compliant (`prevalence_low_pct <= prevalence_pct <= prevalence_high_pct`).
- **Physical Range:** 100% within [0.0%, 100.0%]. Observed values span 2.33% (Denmark, 1990) to 30.89% (Pakistan, 2022). Unweighted cross-national mean is 9.9669%.

### Processed Schema Specification
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `indicator_code` | string | WHO Indicator Code (`NCD_DIABETES_PREVALENCE_AGESTD`) |
| `indicator` | string | Full indicator title |
| `location_code` | string | ISO 3-letter spatial dimension code (e.g., PAK, DNK, USA) |
| `location` | string | Sovereign country / territory name |
| `region_code` | string | WHO parent region code (AFR, AMR, EMR, EUR, SEAR, WPR) |
| `region` | string | WHO parent region name |
| `year` | int64 | Calendar observation year (1990–2022) |
| `sex_code` | string | Sex dimension code (`SEX_BTSX`) |
| `sex` | string | Sex label ("Both sexes") |
| `age_group_code` | string | Age dimension code (`AGEGROUP_YEARS18-PLUS`) |
| `age_group` | string | Age group label ("18+ years") |
| `prevalence_pct` | float64 | Age-standardized diabetes prevalence estimate (%) |
| `prevalence_low_pct` | float64 | Lower bound of 95% uncertainty interval (%) |
| `prevalence_high_pct` | float64 | Upper bound of 95% uncertainty interval (%) |
| `is_latest_year` | bool | True if year == 2022 |
| `date_modified` | string | WHO registry update timestamp |

---

## 3. Supplementary GBD 2023 Workbooks (Contextual Intelligence)

All files reside in `data/raw/gbd2023/`.

### 1. `S1_Global_Age_Standardised_Prevalence_Rates.XLSX`
- **File Size:** 132,960 bytes (~133 KB)
- **Sheet Name:** `sheet1`
- **Dimensions:** 384 data rows × 38 columns (385 rows in Excel with header)
- **Measure & Unit:** Global age-standardized prevalence rate **per 100,000 people** (NOT percentage).
- **Year Coverage:** 1990, 2010, 2020, 2023 (sparse benchmark years).
- **Geographic Coverage:** Global aggregate by cause level (384 cause and sequelae categories).
- **Column Names / Multi-level Header Structure:**
  - `Cause Level` (int, 1–4)
  - `Cause` (string cause description)
  - `1990`: `Both Sexes` (Mean, Lower 95% UI, Upper 95% UI), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
  - `2010`: `Both Sexes` (Mean, Lower, Upper), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
  - `2020`: `Both Sexes` (Mean, Lower, Upper), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
  - `2023`: `Both Sexes` (Mean, Lower, Upper), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
- **Key Causes Present:** `Diabetes mellitus` (Row 243 / Excel row 245), `Diabetes mellitus type 1`, `Diabetes mellitus type 2`, `Diabetes and kidney diseases`.
- **Intended Use:** Global macro-level cross-validation and historical trajectory benchmarking.
- **Rule:** Do NOT concatenate with or substitute for WHO annual country prevalence percentages.

### 2. `S3_Global_All_Age_DALY_Counts.XLSX`
- **File Size:** 113,997 bytes (~114 KB)
- **Sheet Name:** `sheet1`
- **Dimensions:** 384 data rows × 38 columns (385 rows in Excel with header)
- **Measure & Unit:** Global all-age Disability-Adjusted Life Years (DALY) counts (in thousands/millions).
- **Year Coverage:** 1990, 2010, 2020, 2023.
- **Geographic Coverage:** Global aggregate.
- **Column Names / Multi-level Header Structure:**
  - `Cause Level` (int, 1–4)
  - `Cause` (string cause description)
  - `1990 DALYs`: `Both Sexes` (Mean, Lower, Upper), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
  - `2010 DALYs`: `Both Sexes` (Mean, Lower, Upper), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
  - `2020 DALYs`: `Both Sexes` (Mean, Lower, Upper), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
  - `2023 DALYs`: `Both Sexes` (Mean, Lower, Upper), `Females` (Mean, Lower, Upper), `Males` (Mean, Lower, Upper)
- **Intended Use:** Quantifying total population disease burden on Page 6 (Disease Burden).
- **Epidemiological Distinction:** DALYs measure years of healthy life lost due to premature mortality and disability; they are fundamentally distinct from prevalence rates.

### 3. `S10_Global_DALY_Counts_and_Age_Standardised_Rate_Changes.XLSX`
- **File Size:** 78,498 bytes (~78 KB)
- **Sheet Name:** `sheet1`
- **Dimensions:** 379 data rows × 21 columns (380 rows in Excel with header)
- **Measure & Unit:** Percentage change between 2010 and 2023 in DALY counts and age-standardized DALY rates.
- **Geographic Coverage:** Global aggregate, both sexes.
- **Column Names / Multi-level Header Structure:**
  - `Cause Level` (int, 1–4)
  - `Cause` (string cause description)
  - `Rank Within Cause Level by 2023 Count` (int)
  - `Counts (millions)`: `2010` (Mean, Lower, Upper), `2023` (Mean, Lower, Upper), `Percentage Change, 2010-2023` (Mean, Lower, Upper)
  - `Age-standardised Rate (per 100,000)`: `2010` (Mean, Lower, Upper), `2023` (Mean, Lower, Upper), `Percentage Change, 2010-2023` (Mean, Lower, Upper)
- **Intended Use:** Highlighting the escalation of diabetes relative to cardiovascular, oncology, and infectious diseases over the 2010–2023 decade.

### 4. `S13A_Global_Risk_Factor_DALYs_and_PAFs.XLSX`
- **File Size:** 217,145 bytes (~217 KB)
- **Sheet Name:** `sheet1`
- **Dimensions:** 846 data rows × 34 columns (847 rows in Excel with header)
- **Measure & Unit:** Global all-age DALYs, Population Attributable Fractions (PAFs, %), and age-standardized DALY rates per 100,000.
- **Year Coverage:** 1990, 2010, 2023.
- **Column Names / Multi-level Header Structure:**
  - `Risk Name` (string risk factor description)
  - `1990 DALYs` (Mean, Lower, Upper)
  - `2010 DALYs` (Mean, Lower, Upper)
  - `2023 DALYs` (Mean, Lower, Upper)
  - `1990 DALYs PAF (%)` (Mean, Lower, Upper)
  - `2010 DALYs PAF (%)` (Mean, Lower, Upper)
  - `2023 DALYs PAF (%)` (Mean, Lower, Upper)
  - `1990 age-standardised DALY rate (per 100,000)` (Mean, Lower, Upper)
  - `2010 age-standardised DALY rate (per 100,000)` (Mean, Lower, Upper)
  - `2023 age-standardised DALY rate (per 100,000)` (Mean, Lower, Upper)
  - `Percentage change in age-standardised DALY rate, 2010-2023` (Mean, Lower, Upper)
- **Risk Factors Evaluated:** High fasting plasma glucose, high body-mass index (BMI), dietary risks, physical inactivity, ambient particulate matter.
- **Intended Use:** Attribution analysis in the Disease Burden dashboard.

### 5. `S9_Healthy_Life_Expectancy_By_Location_and_Sex.XLSX`
- **File Size:** 194,212 bytes (~194 KB)
- **Sheet Name:** `sheet1`
- **Dimensions:** 714 data rows × 46 columns (715 rows in Excel with header)
- **Measure & Unit:** Healthy Life Expectancy (HALE) at birth in years.
- **Year Coverage:** 1990, 2010, 2020, 2023.
- **Geographic Coverage:** Country-level and regional (714 location-sex strata).
- **Column Names / Multi-level Header Structure:**
  - `Location` (string country or regional name)
  - `Both Sexes`: `1990` (Mean, Lower, Upper), `2010` (Mean, Lower, Upper), `2020` (Mean, Lower, Upper), `2023` (Mean, Lower, Upper), `Percentage Change, 2010-2023` (Mean, Lower, Upper)
  - `Females`: `1990` (Mean, Lower, Upper), `2010` (Mean, Lower, Upper), `2020` (Mean, Lower, Upper), `2023` (Mean, Lower, Upper), `Percentage Change, 2010-2023` (Mean, Lower, Upper)
  - `Males`: `1990` (Mean, Lower, Upper), `2010` (Mean, Lower, Upper), `2020` (Mean, Lower, Upper), `2023` (Mean, Lower, Upper), `Percentage Change, 2010-2023` (Mean, Lower, Upper)
- **Intended Use:** Multi-country comparative health system context.

### 6. `S12_Locations_by_SDI_Group.XLSX`
- **File Size:** 23,144 bytes (~23 KB)
- **Sheet Name:** `Sheet1`
- **Dimensions:** 850 data rows × 1 column (851 rows in Excel with header)
- **Measure & Unit:** Categorical Socio-Demographic Index (SDI) grouping (High SDI, High-middle SDI, Middle SDI, Low-middle SDI, Low SDI).
- **Column Name:** `Table S12. GBD 2023 Socio-Demographic Index groupings by location` (or `Location Name`)
- **Intended Use:** Stratifying country-level historical trends and forecast trajectories by economic development tier.

### 7. `S1_Geographic_Hierarchy.XLSX`
- **File Size:** 13,526 bytes (~14 KB)
- **Sheet Name:** `sheet1`
- **Dimensions:** 239 data rows × 2 columns (240 rows in Excel with header)
- **Column Names:** `Geography` (string name), `level` (int: 0=Global, 1=Super-Region, 2=Region, 3=Country)
- **Intended Use:** Geographic reference and mapping dictionary.

---

## 4. Research Literature Inventory

All PDF files reside in `data/raw/research_papers/`.

| File Name | File Size | Focus & Methodological Role |
| :--- | :--- | :--- |
| `Enhancing AI-driven forecasting of diabetes burden a comparative analysis of deep learning and statistical models.pdf` | 3,693,257 bytes (~3.69 MB) | **Core Forecasting Reference:** Comparative evaluation of ARIMA, Holt-Winters, Prophet, LSTM, and tree-based ensembles. Proves the necessity of damped trend constraints to prevent explosive extrapolations in chronic non-communicable disease modeling. |
| `Burden of disease scenarios for 204 countries and territories, 2022–2050 a forecasting analysis for the Global Burden of Disease Study 2021.pdf` | 6,738,185 bytes (~6.74 MB) | **IHME Long-Term Projection Reference:** Demographic transition modeling, mortality displacement, and risk-factor exposure trajectory forecasting through 2050. |
| `Beyond the 1.5°C planetary boundary AI-forecast of Global Disease Burden and Health inequities.pdf` | 1,115,704 bytes (~1.12 MB) | **Environmental & Health Equity Context:** AI modeling of disease burden divergence across socio-economic gradients. |
| `Depressive disorders burden attributable to childhood sexual abuse in China and India from 1990 to 2023 and prediction for 2040 Analysis of data from the Global Burden of Disease Study 2023.pdf` | 1,563,325 bytes (~1.56 MB) | **Attributable Risk & Backtesting Reference:** Validation framework for out-of-sample backtesting, sMAPE metrics, and uncertainty interval calibration. |

---

## 5. Metric Harmonization and Epidemiological Integrity Rules

1. **Unit Separation:**
   - WHO Prevalence: Measured as a **percentage (%)** of the population aged 18+.
   - GBD Prevalence: Measured as a **rate per 100,000** people.
   - Conversion formula: `Rate_per_100k = Prevalence_pct * 1,000`.
   - Never combine or overlay raw GBD rates with WHO percentages on a shared axis without explicit normalization.
2. **Prevalence vs Burden (DALYs):**
   - Prevalence counts who currently lives with diabetes.
   - DALY counts quantify years of healthy life lost due to premature death and disability. They answer distinct public health questions and must never be conflated.
3. **No Synthetic Backfilling:**
   - Slovenia’s missing 1990–2005 data will remain omitted.
   - Time series models for Slovenia will train strictly on 2006–2022.
4. **Population-Unweighted Notice:**
   - Mean prevalence across countries must always be labeled as **unweighted cross-national mean**, not global population-weighted prevalence.

# DiabForecast: Technical Architecture & Empirical Evaluation Report

**Document Version:** 1.0.0  
**Date:** 2026-11-13  
**Authors:** Senior Data Science & ML Engineering Team  
**System:** DiabForecast — Global Diabetes Prevalence Analysis and Forecasting System  

---

## 1. Abstract

This report documents the architectural design, data engineering pipeline, econometric and machine learning methodologies, out-of-sample backtesting results, and limitations of **DiabForecast**. The system evaluates 33 years of historical World Health Organization (WHO) age-standardized diabetes prevalence estimates (1990–2022) across 152 sovereign nations and produces multi-year annual forecasts through 2030 across four algorithmic families: Linear Regression, ARIMA, Holt Exponential Smoothing with Damped Trend, and Pooled Random Forest. In out-of-sample chronological backtesting over a 5-year test horizon (2018–2022), non-seasonal ARIMA and Holt Damped Smoothing demonstrated superior generalization, achieving unweighted mean absolute errors of 0.0851 and 0.1283 percentage points, respectively, substantially outperforming unconstrained linear trends (0.9857 pp) and a Naive Persistence Baseline (0.7535 pp).

---

## 2. Problem Formulation & Epidemiological Framework

Diabetes mellitus is an escalating chronic non-communicable disease (NCD) characterized by persistent hyperglycemia and progressive vascular complications. Traditional health surveillance systems provide retrospective registries with 2–3 year publication lags. Effective health systems planning, resource allocation, and prevention targeting necessitate robust, prospective forecasting systems.

### Target Specification
- **Indicator:** Age-standardized diabetes prevalence among adults aged 18+ years (`NCD_DIABETES_PREVALENCE_AGESTD`).
- **Target Variable:** $y_{i,t} \in [0, 100]$ representing the percentage prevalence in location $i \in \{1, \dots, 152\}$ at calendar year $t \in \{1990, \dots, 2022\}$.
- **Forecast Horizon:** $h \in \{1, \dots, 8\}$, corresponding to target projection years $t \in \{2023, \dots, 2030\}$.

---

## 3. Data Ingestion & Quality Engineering

### Primary WHO Ingestion Pipeline
The raw dataset (`data.csv`, 30,000 rows × 34 columns) was ingested and filtered by stable code fields:
- `IndicatorCode == 'NCD_DIABETES_PREVALENCE_AGESTD'`
- `Dim1ValueCode == 'SEX_BTSX'` (Both sexes)
- `Dim2ValueCode == 'AGEGROUP_YEARS18-PLUS'` (Adults 18+ years)

### Quality Gates Enforced
1. **Row Count Assertion:** Exactly 5,000 observations selected.
2. **Key Uniqueness:** Zero duplicate $(location, year)$ tuples.
3. **Missing Value Constraint:** Exactly zero missing values in primary and bound fields.
4. **Uncertainty Interval Integrity:** $prevalence\_low_{i,t} \le prevalence_{i,t} \le prevalence\_high_{i,t}$ across 100% of rows.
5. **Physical Range:** All values reside within $[0.0\%, 100.0\%]$.
6. **Chronological Structure:** 151 sovereign countries possess 33 complete annual records (1990–2022). Slovenia possesses 17 observations (2006–2022).
7. **No Synthetic Backfilling:** In accordance with epidemiological standards, earlier years for Slovenia (1990–2005) were **not** imputed or interpolated, preventing synthetic artifacts.

---

## 4. Feature Engineering & Leakage Prevention

For time-series and tree-based forecasting, leak-free lag and rolling features were constructed strictly from past observations:
- $\text{lag}_1(t) = y_{t-1}$
- $\text{lag}_2(t) = y_{t-2}$
- $\text{lag}_3(t) = y_{t-3}$
- $\text{rolling\_mean}_3(t) = \frac{1}{3} \sum_{k=1}^3 y_{t-k}$
- $\text{location\_encoded} \in \{0, \dots, 151\}$

Burn-in observations (the first 3 years per country) contain necessary missing lag values and are dropped during supervised training without cross-country data contamination.

---

## 5. Forecasting Algorithms & Theoretical Specifications

### 5.1 Model 1: Location-Specific Linear Regression
- Fits ordinary least squares: $y_t = \beta_0 + \beta_1 t + \epsilon_t$.
- Serves as an unconstrained linear trend baseline.
- Produces analytical prediction intervals via Student's t-distribution:
  $$\hat{y}_0 \pm t_{n-2, \alpha/2} \cdot s \sqrt{1 + \frac{1}{n} + \frac{(t_0 - \bar{t})^2}{\sum (t_i - \bar{t})^2}}$$

### 5.2 Model 2: Non-Seasonal ARIMA
- Formulated as $\text{ARIMA}(p, d, q)$:
  $$\Phi(B)(1 - B)^d y_t = \Theta(B) \epsilon_t$$
- Automatically searches parameter space: $(1,1,0), (0,1,1), (1,1,1), (0,2,1), (1,2,1), (1,0,0)$.
- Selection criterion: Minimization of Akaike Information Criterion (AIC).
- Features automated convergence fallback to Random Walk with drift $(0,1,0)$.

### 5.3 Model 3: Holt Exponential Smoothing with Damped Trend
- State space formulation:
  $$\ell_t = \alpha y_t + (1 - \alpha)(\ell_{t-1} + \phi b_{t-1})$$
  $$b_t = \beta (\ell_t - \ell_{t-1}) + (1 - \beta)\phi b_{t-1}$$
  $$\hat{y}_{t+h|t} = \ell_t + \sum_{j=1}^h \phi^j b_t$$
- The damping parameter $0 < \phi < 1$ prevents linear trend runaway, flattening the projection curve asymptotically as $h \to \infty$.

### 5.4 Model 4: Pooled Random Forest Regressor
- Pooled ensemble consisting of $B = 300$ regression trees ($max\_depth = 6, min\_samples\_leaf = 2$).
- Multi-step forecasting is conducted **recursively**: at each projection step $t \in [2023, 2030]$, the model predicts $\hat{y}_t$, which is dynamically fed into $\text{lag}_1(t+1)$, propagating through rolling features.
- Ensemble prediction intervals are derived from the empirical percentiles of the 300 tree estimators.

---

## 6. Empirical Validation & Backtesting Results

### 6.1 Backtest Protocol
- **Training Horizon:** 1990–2017 (28 annual steps; 2006–2017 for Slovenia).
- **Out-of-Sample Test Window:** 2018–2022 (5 continuous annual steps).
- **Sample Size:** 152 locations × 5 evaluation models = **760 evaluation rows**.

### 6.2 Overall Metric Summary Across All 152 Sovereign Countries
| Model | Mean MAE (% pts) | Mean RMSE (% pts) | Mean MAPE (%) | Mean WAPE (%) | Mean sMAPE (%) | Optimal Country Count |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ARIMA** | **0.0851** | **0.1058** | **0.71%** | **0.72%** | **0.71%** | **95 (62.5%)** |
| **Holt (Damped)** | **0.1283** | **0.1549** | **1.10%** | **1.13%** | **1.11%** | **31 (20.4%)** |
| **Random Forest** | **0.4942** | **0.5501** | **4.21%** | **4.24%** | **4.13%** | **19 (12.5%)** |
| **Persistence Baseline** | **0.7535** | **0.8429** | **6.10%** | **6.20%** | **6.36%** | *0 (0.0%)* |
| **Linear Regression** | **0.9857** | **1.0172** | **8.57%** | **8.60%** | **8.58%** | **7 (4.6%)** |

### 6.3 Methodological Analysis
1. **Dominance of Statistical Time Series:** ARIMA and Holt Damped Smoothing demonstrate superior local trend fitting and momentum preservation over multi-step horizons, yielding sub-0.15 pp average errors.
2. **Failure of Naive Persistence:** The persistence baseline incurred an average MAE of 0.7535 pp, confirming that static assumptions are invalid in an environment of rapid secular prevalence escalation.
3. **Limitations of Unconstrained Linear Regression:** Linear Regression incurred the highest error (0.9857 pp) due to rigid slope extrapolation that overshoots inflection points in deceleration phases.
4. **Tree Extrapolation Ceiling:** While Random Forest performs well on 1-step validation, its recursive multi-step forecasts tend to plateau because decision trees cannot predict values outside the range of their training leaves.

---

## 7. 2023–2030 Forecasting Projections Summary

Applying the calibrated models across all 152 locations yields 4,864 forecast records:
- **Projected Unweighted Mean (2030):** Rises to **14.88%** (from 13.06% in 2022 and 7.02% in 1990).
- **Highest Projected Countries (2030):**
  1. **Pakistan:** 36.42% [95% PI: 30.96% – 41.88%]
  2. **Egypt:** 31.84% [95% PI: 28.90% – 34.78%]
  3. **Trinidad and Tobago:** 29.85% [95% PI: 28.28% – 31.42%]
  4. **Kuwait:** 28.91% [95% PI: 26.85% – 30.97%]
  5. **Libya:** 28.45% [95% PI: 25.10% – 31.80%]
- **Lowest Projected Countries (2030):** Denmark (2.41%), France (2.85%), Spain (3.78%).

---

## 8. Verification and Quality Assurance

A comprehensive automated test suite consisting of **38 unit tests** in `tests/` covers:
- Preprocessing schema and filtering assertions (12 tests)
- Visualization data mapping and figure types (9 tests)
- Feature engineering temporal shift and leak-free checks (6 tests)
- Model fitting, prediction bounds, and Slovenia edge cases (6 tests)
- Forecast dimension and dynamic selection integrity (5 tests)

All 38 tests pass deterministically via `python -m pytest tests -v`.


# Planned project layout

```text
DiabForecast/
├── app.py
├── pages/
│   ├── 1_Overview.py
│   ├── 2_Historical_Trends.py
│   ├── 3_Forecast_2030.py
│   ├── 4_Model_Comparison.py
│   └── 5_Country_Comparison.py
├── data/
│   ├── raw/
│   │   ├── who_diabetes/data.csv
│   │   └── gbd2023/                 # Optional reference workbooks
│   ├── interim/                     # Temporary feature tables
│   └── processed/
│       └── diabetes_18plus_both_sexes.csv
├── notebooks/
│   ├── 01_dataset_audit.ipynb
│   ├── 02_exploratory_analysis.ipynb
│   └── 03_model_experiments.ipynb
├── src/
│   ├── data/
│   │   ├── load_data.py
│   │   ├── preprocess.py
│   │   └── validation.py
│   ├── features/
│   │   └── build_features.py
│   ├── models/
│   │   ├── linear_regression.py
│   │   ├── arima.py
│   │   ├── holt.py
│   │   ├── random_forest.py
│   │   ├── evaluation.py
│   │   └── forecast.py
│   ├── visualization/
│   │   ├── charts.py
│   │   └── maps.py
│   └── utils/
├── models/saved/                    # Serialized fitted model artifacts
├── reports/
│   ├── stage1_data_quality_report.json
│   ├── dataset_roles.md
│   └── results/
├── tests/
├── requirements.txt
├── README.md
└── .gitignore
```

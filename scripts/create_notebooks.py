"""
Generate 01_dataset_audit.ipynb and 02_exploratory_analysis.ipynb
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS_DIR = ROOT / "notebooks"
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)


def create_audit_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# DiabForecast — Notebook 01: Dataset Ingestion & Quality Audit\n",
                    "\n",
                    "**Objective:** Inspect raw WHO diabetes data, verify primary slice filters (Adults 18+, Both Sexes, Age-Standardized), check uncertainty bounds, and enforce quality assurance gates."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import sys\n",
                    "from pathlib import Path\n",
                    "sys.path.insert(0, str(Path.cwd().parent))\n",
                    "\n",
                    "import pandas as pd\n",
                    "from src.utils.config import WHO_DATA_PATH, PROCESSED_DATA_PATH\n",
                    "from src.data.load_data import load_raw_who, load_processed_who\n",
                    "from src.data.validation import validate_processed_data\n",
                    "\n",
                    "print(f\"Raw WHO path: {WHO_DATA_PATH}\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Raw Dataset Inspection"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "df_raw = load_raw_who()\n",
                    "print(f\"Raw dimensions: {df_raw.shape}\")\n",
                    "print(\"Indicators:\", df_raw['IndicatorCode'].unique())\n",
                    "print(\"Sex codes:\", df_raw['Dim1ValueCode'].unique())\n",
                    "print(\"Age groups:\", df_raw['Dim2ValueCode'].unique())"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Processed Dataset Verification"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "df_clean = load_processed_who()\n",
                    "print(f\"Cleaned shape: {df_clean.shape}\")\n",
                    "audit = validate_processed_data(df_clean)\n",
                    "print(\"Validation Status: ALL GATES PASSED\")\n",
                    "print(\"Descriptive Summary:\", audit['prevalence_stats'])\n",
                    "df_clean.head()"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. Slovenia Historical Series Audit\n",
                    "Confirm that Slovenia's 17 observations (2006–2022) are preserved without synthetic imputation."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "slovenia = df_clean[df_clean['location'] == 'Slovenia']\n",
                    "print(f\"Slovenia record count: {len(slovenia)}\")\n",
                    "print(f\"Year range: {slovenia['year'].min()} - {slovenia['year'].max()}\")\n",
                    "slovenia[['year', 'prevalence_pct', 'prevalence_low_pct', 'prevalence_high_pct']].head()"
                ]
            }
        ],
        "metadata": {
            "language_info": {"name": "python", "version": "3.11"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    with open(NOTEBOOKS_DIR / "01_dataset_audit.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print("Created notebooks/01_dataset_audit.ipynb")


def create_eda_notebook():
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# DiabForecast — Notebook 02: Exploratory Data Analysis (EDA)\n",
                    "\n",
                    "**Objective:** Conduct exploratory analysis of historical diabetes prevalence (1990–2022):\n",
                    "- Trajectory trends & unweighted global averages\n",
                    "- Geographic disparities & WHO regional distributions\n",
                    "- Parametric & non-parametric statistical summaries\n",
                    "- Heteroscedasticity in observational uncertainty"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import sys\n",
                    "from pathlib import Path\n",
                    "sys.path.insert(0, str(Path.cwd().parent))\n",
                    "\n",
                    "import pandas as pd\n",
                    "import plotly.io as pio\n",
                    "pio.renderers.default = 'notebook'\n",
                    "\n",
                    "from src.data.load_data import load_processed_who\n",
                    "from src.visualization.charts import (\n",
                    "    compute_eda_statistics,\n",
                    "    plot_historical_trend,\n",
                    "    plot_prevalence_distribution,\n",
                    "    plot_regional_comparison,\n",
                    "    plot_country_rankings,\n",
                    "    plot_growth_analysis,\n",
                    "    plot_uncertainty_spread\n",
                    ")\n",
                    "from src.visualization.maps import plot_global_choropleth\n",
                    "\n",
                    "df = load_processed_who()\n",
                    "print(f\"Loaded {len(df)} records across {df['location'].nunique()} countries.\")"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 1. Statistical Summary & Distributions"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "stats = compute_eda_statistics(df)\n",
                    "print(\"Overall Skewness:\", stats['overall']['skewness'])\n",
                    "print(\"Overall Kurtosis:\", stats['overall']['kurtosis'])\n",
                    "print(\"Unweighted Mean:\", stats['overall']['mean_unweighted'])\n",
                    "plot_prevalence_distribution(df, year=2022)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 2. Historical Trajectory & Country Trends"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "sample_countries = ['Pakistan', 'Egypt', 'Kuwait', 'Mexico', 'United States of America', 'Germany', 'Denmark']\n",
                    "plot_historical_trend(df, locations=sample_countries)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 3. WHO Regional Comparison"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "plot_regional_comparison(df, year=2022)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 4. Global Choropleth Map"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "plot_global_choropleth(df, year=2022)"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 5. Absolute Growth (1990 to 2022)"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "fig_growth, growth_df = plot_growth_analysis(df, start_year=1990, end_year=2022, top_n=12)\n",
                    "fig_growth"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 6. Uncertainty Heteroscedasticity Analysis"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "plot_uncertainty_spread(df, year=2022)"
                ]
            }
        ],
        "metadata": {
            "language_info": {"name": "python", "version": "3.11"}
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    with open(NOTEBOOKS_DIR / "02_exploratory_analysis.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print("Created notebooks/02_exploratory_analysis.ipynb")


if __name__ == "__main__":
    create_audit_notebook()
    create_eda_notebook()


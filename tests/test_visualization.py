"""
Unit Tests for Stage 2: Visualizations and Statistical Summary Functions.
"""
import pytest
import pandas as pd
import plotly.graph_objects as go

from src.data.load_data import load_processed_who
from src.visualization.charts import (
    compute_eda_statistics,
    plot_historical_trend,
    plot_prevalence_distribution,
    plot_regional_comparison,
    plot_country_rankings,
    plot_growth_analysis,
    plot_uncertainty_spread,
)
from src.visualization.maps import (
    plot_global_choropleth,
    plot_regional_choropleth,
)


@pytest.fixture(scope="module")
def df_clean():
    return load_processed_who()


def test_compute_eda_statistics(df_clean):
    """Verify statistical metrics calculation."""
    stats = compute_eda_statistics(df_clean)
    assert "overall" in stats
    assert "year_2022" in stats
    assert stats["overall"]["count"] == 5000
    assert stats["overall"]["min"] < stats["overall"]["mean_unweighted"] < stats["overall"]["max"]
    assert stats["year_2022"]["count"] == 152
    assert isinstance(stats["overall"]["skewness"], float)


def test_plot_historical_trend(df_clean):
    """Verify historical trend figure generation."""
    fig = plot_historical_trend(df_clean, locations=["Pakistan", "Denmark"], show_uncertainty=True)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_plot_prevalence_distribution(df_clean):
    """Verify prevalence distribution figure generation."""
    fig = plot_prevalence_distribution(df_clean, year=2022)
    assert isinstance(fig, go.Figure)


def test_plot_regional_comparison(df_clean):
    """Verify regional boxplot figure generation."""
    fig = plot_regional_comparison(df_clean, year=2022)
    assert isinstance(fig, go.Figure)


def test_plot_country_rankings(df_clean):
    """Verify country rankings figure generation."""
    fig_top = plot_country_rankings(df_clean, year=2022, top_n=10, ascending=False)
    assert isinstance(fig_top, go.Figure)
    fig_bot = plot_country_rankings(df_clean, year=2022, top_n=10, ascending=True)
    assert isinstance(fig_bot, go.Figure)


def test_plot_growth_analysis(df_clean):
    """Verify growth calculation and chart generation."""
    fig, growth_df = plot_growth_analysis(df_clean, start_year=1990, end_year=2022, top_n=10)
    assert isinstance(fig, go.Figure)
    assert not growth_df.empty
    assert len(growth_df) == 151  # Slovenia excluded from 1990 baseline
    assert "abs_change_pp" in growth_df.columns
    assert "relative_growth_pct" in growth_df.columns
    assert not growth_df["abs_change_pp"].isna().any()


def test_plot_uncertainty_spread(df_clean):
    """Verify uncertainty spread scatter plot generation."""
    fig = plot_uncertainty_spread(df_clean, year=2022)
    assert isinstance(fig, go.Figure)


def test_plot_global_choropleth(df_clean):
    """Verify global choropleth map generation."""
    fig = plot_global_choropleth(df_clean, year=2022)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "choropleth"
    assert len(fig.data[0].locations) == 152


def test_plot_regional_choropleth(df_clean):
    """Verify regional choropleth map generation."""
    fig = plot_regional_choropleth(df_clean, region_name="Europe", year=2022)
    assert isinstance(fig, go.Figure)


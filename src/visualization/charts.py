"""
Reusable Visualization Modules for DiabForecast.
Contains interactive Plotly and static Matplotlib chart generation functions.
"""
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns


# Color palette: Deep Navy / Healthcare Teal theme
COLOR_PALETTE = {
    "primary": "#0D9488",       # Teal
    "secondary": "#0284C7",     # Cyan / Sky
    "accent": "#F59E0B",        # Amber
    "danger": "#EF4444",        # Red
    "dark": "#0F172A",          # Slate Navy
    "card_bg": "#1E293B",       # Slate 800
    "text": "#F8FAFC",          # Off white
    "grid": "#334155",          # Slate 700
    "line_colors": [
        "#14B8A6", "#38BDF8", "#F43F5E", "#A855F7", "#F59E0B",
        "#10B981", "#6366F1", "#EC4899", "#EAB308", "#06B6D4"
    ]
}


def compute_eda_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate comprehensive descriptive statistics across observations.
    
    Parameters
    ----------
    df : pd.DataFrame
        Processed dataset containing prevalence_pct.
        
    Returns
    -------
    dict
        Dictionary containing parametric, non-parametric, skewness, and outlier metrics.
    """
    series = df["prevalence_pct"]
    q1 = float(series.quantile(0.25))
    q3 = float(series.quantile(0.75))
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    
    outliers = df[(df["prevalence_pct"] < lower_fence) | (df["prevalence_pct"] > upper_fence)]
    
    # 2022 slice statistics
    df_2022 = df[df["year"] == 2022]
    s_2022 = df_2022["prevalence_pct"]
    
    stats = {
        "overall": {
            "count": int(series.count()),
            "mean_unweighted": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "q25": q1,
            "median": float(series.median()),
            "q75": q3,
            "max": float(series.max()),
            "iqr": float(iqr),
            "skewness": float(series.skew()),
            "kurtosis": float(series.kurtosis()),
            "outliers_count": int(len(outliers)),
            "outlier_locations": sorted(outliers["location"].unique().tolist())
        },
        "year_2022": {
            "count": int(s_2022.count()),
            "mean_unweighted": float(s_2022.mean()),
            "std": float(s_2022.std()),
            "min": float(s_2022.min()),
            "q25": float(s_2022.quantile(0.25)),
            "median": float(s_2022.median()),
            "q75": float(s_2022.quantile(0.75)),
            "max": float(s_2022.max()),
            "skewness": float(s_2022.skew()),
        }
    }
    return stats


def plot_historical_trend(
    df: pd.DataFrame,
    locations: Optional[List[str]] = None,
    show_uncertainty: bool = True,
    include_global_unweighted_mean: bool = True,
    title: Optional[str] = None
) -> go.Figure:
    """
    Generate an interactive Plotly line chart displaying historical trends with uncertainty intervals.

    Parameters
    ----------
    df : pd.DataFrame
        Processed WHO dataframe.
    locations : list of str, optional
        List of country names to plot. If None, plots top representative countries.
    show_uncertainty : bool, default True
        Whether to show shaded uncertainty intervals (ribbons).
    include_global_unweighted_mean : bool, default True
        Whether to overlay unweighted cross-national average trend.
    title : str, optional
        Chart title.

    Returns
    -------
    go.Figure
        Plotly Figure object.
    """
    fig = go.Figure()

    if locations is None:
        locations = ["Pakistan", "Egypt", "United States of America", "Germany", "Denmark"]

    # Filter to existing locations
    available_locs = df["location"].unique()
    valid_locs = [loc for loc in locations if loc in available_locs]

    for idx, loc in enumerate(valid_locs):
        loc_df = df[df["location"] == loc].sort_values("year")
        color = COLOR_PALETTE["line_colors"][idx % len(COLOR_PALETTE["line_colors"])]

        # Uncertainty band (ribbon)
        if show_uncertainty:
            fig.add_trace(go.Scatter(
                x=pd.concat([loc_df["year"], loc_df["year"].iloc[::-1]]),
                y=pd.concat([loc_df["prevalence_high_pct"], loc_df["prevalence_low_pct"].iloc[::-1]]),
                fill="toself",
                fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.12)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                showlegend=False,
                name=f"{loc} 95% UI"
            ))

        # Main trend line
        fig.add_trace(go.Scatter(
            x=loc_df["year"],
            y=loc_df["prevalence_pct"],
            mode="lines+markers",
            name=loc,
            line=dict(color=color, width=2.5),
            marker=dict(size=5),
            hovertemplate=(
                f"<b>{loc} (%{{x}})</b><br>"
                "Prevalence: %{y:.2f}%<br>"
                "<extra></extra>"
            )
        ))

    # Add global unweighted mean trend
    if include_global_unweighted_mean:
        mean_trend = df.groupby("year")["prevalence_pct"].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=mean_trend["year"],
            y=mean_trend["prevalence_pct"],
            mode="lines",
            name="Unweighted Mean (152 countries)",
            line=dict(color="#CBD5E1", width=3, dash="dash"),
            hovertemplate="<b>Unweighted Mean (%{x})</b>: %{y:.2f}%<extra></extra>"
        ))

    fig.update_layout(
        title=title or "Historical Diabetes Prevalence (1990–2022) with 95% Uncertainty",
        template="plotly_dark",
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC", family="Inter, Arial, sans-serif"),
        xaxis=dict(
            title="Year",
            gridcolor="#334155",
            dtick=5,
            range=[1989, 2023]
        ),
        yaxis=dict(
            title="Age-Standardized Prevalence (%)",
            gridcolor="#334155",
            ticksuffix="%"
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="#334155",
            borderwidth=1,
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=60, r=40, t=60, b=80),
        hovermode="x unified"
    )

    return fig


def plot_prevalence_distribution(df: pd.DataFrame, year: Optional[int] = 2022) -> go.Figure:
    """
    Plot interactive distribution histogram and box plot of country prevalence.
    """
    plot_df = df[df["year"] == year] if year is not None else df
    yr_label = f"in {year}" if year else "Across All Years (1990–2022)"

    fig = px.histogram(
        plot_df,
        x="prevalence_pct",
        color="region",
        marginal="box",
        nbins=35,
        title=f"Distribution of Diabetes Prevalence {yr_label} (N={len(plot_df)})",
        labels={"prevalence_pct": "Age-Standardized Prevalence (%)", "region": "WHO Region"},
        template="plotly_dark",
        color_discrete_sequence=COLOR_PALETTE["line_colors"]
    )

    fig.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC", family="Inter, sans-serif"),
        xaxis=dict(gridcolor="#334155", ticksuffix="%"),
        yaxis=dict(gridcolor="#334155", title="Country Count"),
        legend=dict(bgcolor="rgba(15, 23, 42, 0.8)", bordercolor="#334155"),
        margin=dict(l=60, r=40, t=60, b=50)
    )
    return fig


def plot_regional_comparison(df: pd.DataFrame, year: int = 2022) -> go.Figure:
    """
    Generate box plots comparing prevalence distributions across WHO regions.
    """
    df_yr = df[df["year"] == year].copy()

    # Order regions by median prevalence
    region_order = (
        df_yr.groupby("region")["prevalence_pct"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig = px.box(
        df_yr,
        x="region",
        y="prevalence_pct",
        color="region",
        category_orders={"region": region_order},
        points="all",
        title=f"Cross-Regional Diabetes Prevalence Comparison ({year})",
        labels={"region": "WHO Parent Region", "prevalence_pct": "Prevalence (%)"},
        template="plotly_dark",
        color_discrete_sequence=COLOR_PALETTE["line_colors"]
    )

    fig.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        xaxis=dict(gridcolor="#334155", title=""),
        yaxis=dict(gridcolor="#334155", ticksuffix="%"),
        showlegend=False,
        margin=dict(l=60, r=40, t=60, b=60)
    )
    return fig


def plot_country_rankings(
    df: pd.DataFrame,
    year: int = 2022,
    top_n: int = 15,
    ascending: bool = False
) -> go.Figure:
    """
    Horizontal bar chart of top or bottom prevalence countries for a given year.
    """
    df_yr = df[df["year"] == year].sort_values("prevalence_pct", ascending=ascending).head(top_n)
    title_prefix = "Lowest" if ascending else "Highest"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_yr["location"],
        x=df_yr["prevalence_pct"],
        orientation="h",
        marker=dict(
            color=df_yr["prevalence_pct"],
            colorscale="Teal" if ascending else "Reds",
            showscale=False
        ),
        error_x=dict(
            type="data",
            symmetric=False,
            array=df_yr["prevalence_high_pct"] - df_yr["prevalence_pct"],
            arrayminus=df_yr["prevalence_pct"] - df_yr["prevalence_low_pct"],
            color="#94A3B8"
        ),
        hovertemplate="<b>%{y}</b><br>Prevalence: %{x:.2f}%<extra></extra>"
    ))

    fig.update_layout(
        title=f"{title_prefix} {top_n} Countries by Prevalence in {year} (with 95% Uncertainty)",
        template="plotly_dark",
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        xaxis=dict(title="Prevalence (%)", gridcolor="#334155", ticksuffix="%"),
        yaxis=dict(title="", autorange="reversed" if not ascending else "reversed"),
        margin=dict(l=150, r=40, t=60, b=50)
    )
    return fig


def plot_growth_analysis(
    df: pd.DataFrame,
    start_year: int = 1990,
    end_year: int = 2022,
    top_n: int = 10
) -> Tuple[go.Figure, pd.DataFrame]:
    """
    Analyze absolute percentage point change and relative % growth between two benchmark years.
    """
    # Filter to countries with observations at both years
    piv = df.pivot(index="location", columns="year", values="prevalence_pct")
    valid_countries = piv[[start_year, end_year]].dropna()

    growth_df = pd.DataFrame({
        "location": valid_countries.index,
        f"prev_{start_year}": valid_countries[start_year],
        f"prev_{end_year}": valid_countries[end_year],
        "abs_change_pp": valid_countries[end_year] - valid_countries[start_year],
        "relative_growth_pct": ((valid_countries[end_year] - valid_countries[start_year]) / valid_countries[start_year]) * 100
    }).reset_index(drop=True)

    top_growth = growth_df.sort_values("abs_change_pp", ascending=False).head(top_n)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top_growth["location"],
        x=top_growth["abs_change_pp"],
        orientation="h",
        marker=dict(color="#0D9488"),
        text=[f"+{v:.2f}% pts" for v in top_growth["abs_change_pp"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Change: +%{x:.2f} percentage points<extra></extra>"
    ))

    fig.update_layout(
        title=f"Top {top_n} Countries by Absolute Prevalence Increase ({start_year}–{end_year})",
        template="plotly_dark",
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        xaxis=dict(title="Absolute Change (Percentage Points)", gridcolor="#334155"),
        yaxis=dict(title="", autorange="reversed"),
        margin=dict(l=160, r=60, t=60, b=50)
    )

    return fig, growth_df


def plot_uncertainty_spread(df: pd.DataFrame, year: int = 2022) -> go.Figure:
    """
    Plot relationship between prevalence estimate and width of 95% uncertainty interval.
    """
    df_yr = df[df["year"] == year].copy()
    df_yr["ui_width"] = df_yr["prevalence_high_pct"] - df_yr["prevalence_low_pct"]

    fig = px.scatter(
        df_yr,
        x="prevalence_pct",
        y="ui_width",
        color="region",
        hover_name="location",
        title=f"Prevalence vs 95% Uncertainty Interval Width ({year})",
        labels={
            "prevalence_pct": "Prevalence Estimate (%)",
            "ui_width": "Uncertainty Width (Upper - Lower % points)",
            "region": "WHO Region"
        },
        template="plotly_dark",
        color_discrete_sequence=COLOR_PALETTE["line_colors"],
        trendline="ols"
    )

    fig.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        font=dict(color="#F8FAFC"),
        xaxis=dict(gridcolor="#334155", ticksuffix="%"),
        yaxis=dict(gridcolor="#334155", ticksuffix=" pp"),
        legend=dict(bgcolor="rgba(15, 23, 42, 0.8)", bordercolor="#334155"),
        margin=dict(l=60, r=40, t=60, b=50)
    )
    return fig


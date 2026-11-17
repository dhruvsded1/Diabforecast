"""
Choropleth and Geographic Visualization Modules for DiabForecast.
Provides interactive world and regional prevalence maps using ISO-3 spatial codes.
"""
from typing import Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_global_choropleth(
    df: pd.DataFrame,
    year: int = 2022,
    title: Optional[str] = None,
    projection: str = "natural earth"
) -> go.Figure:
    """
    Generate an interactive global choropleth map for a specified year.

    Parameters
    ----------
    df : pd.DataFrame
        Processed dataset containing location_code, location, prevalence_pct, etc.
    year : int, default 2022
        Year to visualize.
    title : str, optional
        Map title.
    projection : str, default 'natural earth'
        Map projection type ('natural earth', 'equirectangular', 'orthographic', etc.)

    Returns
    -------
    go.Figure
        Plotly Figure object.
    """
    df_yr = df[df["year"] == year].copy()

    # Format hover text with uncertainty intervals and region
    hover_text = [
        f"<b>{loc}</b> ({code})<br>"
        f"Region: {reg}<br>"
        f"Prevalence ({year}): <b>{prev:.2f}%</b><br>"
        f"95% Uncertainty: [{low:.2f}% – {high:.2f}%]"
        for loc, code, reg, prev, low, high in zip(
            df_yr["location"],
            df_yr["location_code"],
            df_yr["region"],
            df_yr["prevalence_pct"],
            df_yr["prevalence_low_pct"],
            df_yr["prevalence_high_pct"]
        )
    ]

    fig = go.Figure(data=go.Choropleth(
        locations=df_yr["location_code"],
        z=df_yr["prevalence_pct"],
        text=hover_text,
        hoverinfo="text",
        colorscale="Viridis",
        autocolorscale=False,
        reversescale=False,
        marker_line_color="#334155",
        marker_line_width=0.7,
        colorbar=dict(
            title=dict(
                text="Prevalence (%)",
                font=dict(color="#F8FAFC", size=12)
            ),
            tickfont=dict(color="#F8FAFC"),
            ticksuffix="%",
            len=0.7,
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="#334155",
            borderwidth=1
        )
    ))

    fig.update_layout(
        title=dict(
            text=title or f"Global Diabetes Prevalence ({year}) — Age-Standardized, Adults 18+ (WHO Estimates)",
            font=dict(color="#F8FAFC", size=16, family="Inter, Arial, sans-serif")
        ),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="#475569",
            showland=True,
            landcolor="#1E293B",
            showocean=True,
            oceancolor="#0B132B",
            showlakes=True,
            lakecolor="#0B132B",
            projection_type=projection,
            bgcolor="#0F172A"
        ),
        paper_bgcolor="#0F172A",
        margin=dict(l=0, r=0, t=50, b=0)
    )

    return fig


def plot_regional_choropleth(
    df: pd.DataFrame,
    region_name: str,
    year: int = 2022
) -> go.Figure:
    """
    Generate a focused choropleth map for a specific WHO parent region.
    """
    df_reg = df[(df["region"] == region_name) & (df["year"] == year)].copy()

    # Determine regional map scope
    scope_mapping = {
        "Africa": "africa",
        "Americas": "north america",  # or world bounded
        "Europe": "europe",
        "Asia": "asia",
    }
    scope = "world"
    for k, v in scope_mapping.items():
        if k.lower() in region_name.lower():
            scope = v
            break

    fig = px.choropleth(
        df_reg,
        locations="location_code",
        color="prevalence_pct",
        hover_name="location",
        hover_data={"prevalence_low_pct": ":.2f%", "prevalence_high_pct": ":.2f%", "location_code": False},
        color_continuous_scale="Teal",
        title=f"Diabetes Prevalence in WHO {region_name} ({year})",
        labels={"prevalence_pct": "Prevalence (%)"},
        scope=scope,
        template="plotly_dark"
    )

    fig.update_layout(
        plot_bgcolor="#0F172A",
        paper_bgcolor="#0F172A",
        geo=dict(
            bgcolor="#0F172A",
            landcolor="#1E293B",
            showocean=True,
            oceancolor="#0B132B"
        ),
        font=dict(color="#F8FAFC"),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    return fig


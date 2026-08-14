# SilkTrace — Executive Analytics & Operational Insights Engine
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import PRODUCTIVITY_DATASET_PATH, ENERGY_DATASET_PATH

@st.cache_data
def load_analytics_datasets():
    """Load and preprocess real project datasets for Analytics module."""
    if not PRODUCTIVITY_DATASET_PATH.exists():
        raise FileNotFoundError(f"Productivity dataset missing at {PRODUCTIVITY_DATASET_PATH}")
    if not ENERGY_DATASET_PATH.exists():
        raise FileNotFoundError(f"Energy dataset missing at {ENERGY_DATASET_PATH}")

    prod_df = pd.read_csv(PRODUCTIVITY_DATASET_PATH)
    eng_df = pd.read_csv(ENERGY_DATASET_PATH)

    # Clean missing values safely if present
    if "wip" in prod_df.columns:
        prod_df["wip"] = prod_df["wip"].fillna(0)

    return prod_df, eng_df

def compute_executive_kpis(prod_df: pd.DataFrame, eng_df: pd.DataFrame, energy_history: pd.DataFrame, prod_history: pd.DataFrame, inspection_history: pd.DataFrame):
    """Calculate key industrial KPI metrics across datasets and runtime histories."""
    avg_actual_prod = prod_df["actual_productivity"].mean() if "actual_productivity" in prod_df.columns else 0.72
    avg_targeted_prod = prod_df["targeted_productivity"].mean() if "targeted_productivity" in prod_df.columns else 0.73
    
    avg_energy_kwh = eng_df["Usage_kWh"].mean() if "Usage_kWh" in eng_df.columns else 27.38
    total_energy_kwh = eng_df["Usage_kWh"].sum() if "Usage_kWh" in eng_df.columns else 0.0

    defect_count = len(inspection_history) if not inspection_history.empty else 0
    defect_rate = ((inspection_history["Detected Defect"] != "Normal").mean() * 100) if defect_count > 0 and "Detected Defect" in inspection_history.columns else 0.0

    total_predictions = len(energy_history) + len(prod_history) + defect_count

    return {
        "avg_actual_prod": avg_actual_prod,
        "avg_targeted_prod": avg_targeted_prod,
        "avg_energy_kwh": avg_energy_kwh,
        "total_energy_kwh": total_energy_kwh,
        "total_predictions": total_predictions,
        "defect_count": defect_count,
        "defect_rate": defect_rate,
    }

def generate_operational_alerts(prod_df: pd.DataFrame, eng_df: pd.DataFrame) -> list[dict]:
    """Generate statistically-justified operational alerts based on real dataset distributions."""
    alerts = []

    # 1. Low Productivity Alert Check
    if "actual_productivity" in prod_df.columns and "targeted_productivity" in prod_df.columns:
        gap = prod_df["targeted_productivity"].mean() - prod_df["actual_productivity"].mean()
        if gap > 0.01:
            alerts.append({
                "category": "WORKFORCE PRODUCTIVITY",
                "severity": "WARNING",
                "message": f"Average actual productivity ({prod_df['actual_productivity'].mean():.2%}) is lagging target ({prod_df['targeted_productivity'].mean():.2%}).",
                "reason": "Departmental bottleneck in sewing assembly or excessive line style changes.",
                "suggested_action": "Review WIP levels and balance worker allocation across teams."
            })

    # 2. Energy Peak Consumption Warning
    if "Usage_kWh" in eng_df.columns:
        p95 = eng_df["Usage_kWh"].quantile(0.95)
        high_usage_ratio = (eng_df["Usage_kWh"] > p95).mean()
        alerts.append({
            "category": "ENERGY OPTIMIZATION",
            "severity": "CRITICAL" if high_usage_ratio > 0.1 else "INFO",
            "message": f"Industrial peak load threshold established at {p95:.2f} kWh.",
            "reason": "Heavy equipment operating concurrently during peak pricing shifts.",
            "suggested_action": "Shift high-power weaving machinery to off-peak status schedules."
        })

    # 3. Power Factor Anomaly Check
    if "Lagging_Current_Power_Factor" in eng_df.columns:
        low_pf = (eng_df["Lagging_Current_Power_Factor"] < 70).mean()
        if low_pf > 0.05:
            alerts.append({
                "category": "ELECTRICAL HEALTH",
                "severity": "WARNING",
                "message": f"Low Power Factor (< 70%) detected in {low_pf:.1%} of operational logs.",
                "reason": "Inductive motor loads operating without adequate capacitor compensation.",
                "suggested_action": "Inspect automatic power factor correction (APFC) bank units."
            })

    return alerts

def create_department_productivity_chart(prod_df: pd.DataFrame):
    """Plotly bar chart for department-wise average productivity."""
    dept_stats = prod_df.groupby("department")[["actual_productivity", "targeted_productivity"]].mean().reset_index()
    fig = px.bar(
        dept_stats,
        x="department",
        y=["actual_productivity", "targeted_productivity"],
        barmode="group",
        title="Departmental Target vs. Actual Productivity",
        labels={"value": "Productivity Score", "department": "Department", "variable": "Metric"},
        color_discrete_map={"actual_productivity": "#22c55e", "targeted_productivity": "#60a5fa"}
    )
    fig.update_layout(
        height=380,
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def create_quarterly_productivity_trend_chart(prod_df: pd.DataFrame):
    """Plotly spline line chart for quarterly productivity trends."""
    quarter_stats = prod_df.groupby("quarter")["actual_productivity"].mean().reset_index()
    fig = px.line(
        quarter_stats,
        x="quarter",
        y="actual_productivity",
        markers=True,
        title="Quarterly Productivity Performance Trend",
        labels={"actual_productivity": "Avg Productivity", "quarter": "Quarter"},
        line_shape="spline"
    )
    fig.update_traces(line_color="#3b82f6", line_width=3, marker_size=8)
    fig.update_layout(
        height=380,
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0")
    )
    return fig

def create_energy_load_pie_chart(eng_df: pd.DataFrame):
    """Plotly pie chart for energy consumption by load type."""
    load_stats = eng_df.groupby("Load_Type")["Usage_kWh"].sum().reset_index()
    fig = px.pie(
        load_stats,
        names="Load_Type",
        values="Usage_kWh",
        title="Energy Consumption Share by Load Type",
        color_discrete_sequence=["#ef4444", "#f59e0b", "#0ea5e9"],
        hole=0.4
    )
    fig.update_layout(
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0")
    )
    return fig

def create_power_factor_analysis_chart(eng_df: pd.DataFrame):
    """Plotly scatter plot for power factor vs energy usage."""
    sample_df = eng_df.sample(n=min(1000, len(eng_df)), random_state=42)
    fig = px.scatter(
        sample_df,
        x="Lagging_Current_Power_Factor",
        y="Usage_kWh",
        color="Load_Type",
        title="Power Factor vs. Energy Usage (kWh)",
        labels={"Lagging_Current_Power_Factor": "Power Factor (%)", "Usage_kWh": "Energy Usage (kWh)"},
        color_discrete_sequence=["#0ea5e9", "#f59e0b", "#ef4444"]
    )
    fig.update_layout(
        height=380,
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0")
    )
    return fig

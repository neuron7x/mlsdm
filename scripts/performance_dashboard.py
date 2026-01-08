"""Real-time performance dashboard."""
from __future__ import annotations

import time

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="MLSDM Performance Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 MLSDM Performance Dashboard")

API_URL = st.sidebar.text_input("API URL", "http://localhost:8000")

auto_refresh = st.sidebar.checkbox("Auto Refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 60, 5)

col1, col2, col3, col4 = st.columns(4)


def fetch_metrics() -> dict | None:
    """Fetch current metrics."""
    try:
        response = requests.get(f"{API_URL}/metrics/performance", timeout=5)
        return response.json()
    except Exception as exc:
        st.error(f"Error fetching metrics: {exc}")
        return None


def display_metrics(data: dict | None) -> None:
    """Display metrics in dashboard."""
    if not data:
        return

    metrics = data["metrics"]

    with col1:
        st.metric(
            "P50 Latency",
            f"{metrics['p50_latency_ms']:.2f}ms",
            delta=None,
            delta_color="inverse",
        )

    with col2:
        st.metric(
            "P95 Latency",
            f"{metrics['p95_latency_ms']:.2f}ms",
            delta=None,
            delta_color="inverse",
        )

    with col3:
        st.metric(
            "P99 Latency",
            f"{metrics['p99_latency_ms']:.2f}ms",
            delta=None,
            delta_color="inverse",
        )

    with col4:
        st.metric(
            "Throughput",
            f"{metrics['throughput_rps']:.2f} RPS",
            delta=None,
        )

    st.subheader("SLO Compliance")
    if data["slo_compliant"]:
        st.success("✅ All SLOs met")
    else:
        st.error("❌ SLO Violations:")
        for violation in data["violations"]:
            st.write(f"• {violation}")

    st.subheader("Latency Distribution")
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=["P50", "P95", "P99"],
            y=[
                metrics["p50_latency_ms"],
                metrics["p95_latency_ms"],
                metrics["p99_latency_ms"],
            ],
            marker_color=["green", "orange", "red"],
        )
    )

    fig.add_hline(
        y=30,
        line_dash="dash",
        line_color="green",
        annotation_text="P50 SLO (30ms)",
    )
    fig.add_hline(
        y=120,
        line_dash="dash",
        line_color="orange",
        annotation_text="P95 SLO (120ms)",
    )
    fig.add_hline(
        y=200,
        line_dash="dash",
        line_color="red",
        annotation_text="P99 SLO (200ms)",
    )

    fig.update_layout(
        title="Latency Percentiles",
        yaxis_title="Latency (ms)",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def display_history_table(data: dict | None) -> None:
    """Display a placeholder history table."""
    if not data:
        return

    metrics = data["metrics"]
    table = pd.DataFrame(
        {
            "metric": ["p50", "p95", "p99", "throughput"],
            "value": [
                metrics["p50_latency_ms"],
                metrics["p95_latency_ms"],
                metrics["p99_latency_ms"],
                metrics["throughput_rps"],
            ],
        }
    )
    st.subheader("Latest Metrics Snapshot")
    st.dataframe(table, use_container_width=True)


data = fetch_metrics()

display_metrics(data)

display_history_table(data)

if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

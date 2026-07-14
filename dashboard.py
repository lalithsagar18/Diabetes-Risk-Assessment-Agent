# dashboard.py
import streamlit as st
from database import get_dashboard_metrics
from utils import init_session_state
import plotly.express as px
import pandas as pd


def render_dashboard():
    """Render the main dashboard with key metrics and charts."""
    init_session_state()
    st.title(":bar_chart: DiabetesCare AI Dashboard")
    metrics = get_dashboard_metrics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total Patients", value=metrics["total_patients"])
    col2.metric(label="High‑Risk Patients", value=metrics["high_risk"])
    col3.metric(label="Low‑Risk Patients", value=metrics["low_risk"])
    col4.metric(label="Avg Risk %", value=f"{metrics["average_risk"]}%")

    st.subheader("Recent Predictions")
    recent_df = pd.DataFrame(metrics["recent_predictions"]).rename(columns={
        "patient_id": "Patient ID",
        "name": "Name",
        "risk_percentage": "Risk %",
        "created_at": "Timestamp",
    })
    st.dataframe(recent_df)

    # Risk distribution pie chart
    with st.expander("Risk Distribution"):
        conn = None
        try:
            from database import _get_connection
            conn = _get_connection()
            df = pd.read_sql_query("SELECT risk_percentage FROM patients", conn)
            # Categorise risk
            bins = [0, 30, 70, 100]
            labels = ["Low", "Moderate", "High"]
            df["category"] = pd.cut(df["risk_percentage"], bins=bins, labels=labels, include_lowest=True)
            fig = px.pie(df, names="category", title="Risk Distribution")
            st.plotly_chart(fig, use_container_width=True)
        finally:
            if conn:
                conn.close()

    # Age vs Risk scatter
    with st.expander("Age vs Risk"):
        conn = None
        try:
            from database import _get_connection
            conn = _get_connection()
            df = pd.read_sql_query("SELECT age, risk_percentage FROM patients WHERE age IS NOT NULL", conn)
            if not df.empty:
                fig = px.scatter(df, x="age", y="risk_percentage", trendline="ols", title="Age vs Risk %")
                st.plotly_chart(fig, use_container_width=True)
        finally:
            if conn:
                conn.close()

    # BMI vs Risk scatter
    with st.expander("BMI vs Risk"):
        conn = None
        try:
            from database import _get_connection
            conn = _get_connection()
            df = pd.read_sql_query("SELECT bmi, risk_percentage FROM patients WHERE bmi IS NOT NULL", conn)
            if not df.empty:
                fig = px.scatter(df, x="bmi", y="risk_percentage", trendline="ols", title="BMI vs Risk %")
                st.plotly_chart(fig, use_container_width=True)
        finally:
            if conn:
                conn.close()

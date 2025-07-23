# streamlit_app.py
"""
Modern Log Analysis Dashboard using Streamlit
To run: streamlit run streamlit_app.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- File Uploader ---
st.set_page_config(
    page_title="Log Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="📊"
)

st.sidebar.title("Log File Upload")
log_file = st.sidebar.file_uploader("Upload log CSV", type=["csv"])

if log_file is not None:
    df = pd.read_csv(log_file)
    log_file_name = log_file.name
    analysis_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    total_logs = len(df)
    anomaly_count = df['is_anomaly'].sum() if 'is_anomaly' in df else 0
    normal_count = total_logs - anomaly_count
    # Severity distribution
    if 'severity' in df:
        severity_counts = df['severity'].value_counts().reindex(['Critical', 'High', 'Medium', 'Low'], fill_value=0).to_dict()
    else:
        severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    # Anomaly type distribution
    if 'anomaly_type' in df:
        anomaly_types = df['anomaly_type'].value_counts().to_dict()
    else:
        anomaly_types = {}
else:
    st.warning("Please upload a log CSV file with columns: timestamp, logline, is_anomaly, severity, anomaly_type.")
    st.stop()

# --- Top Card ---
st.markdown(f"""
<div style='background: linear-gradient(90deg, #3b82f6 0%, #9333ea 100%); border-radius: 1rem; padding: 2rem 2rem 1rem 2rem; margin-bottom: 2rem; color: white; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;'>
    <div>
        <h2 style='margin-bottom: 0.5rem;'>Log File: <span style='font-family: monospace;'>{log_file_name}</span></h2>
        <div>Total Logs: <b>{total_logs:,}</b></div>
    </div>
    <div style='margin-top: 1rem; font-size: 1rem;'>
        <span style='background: #fff3; color: #fff; padding: 0.5rem 1rem; border-radius: 999px;'>Analyzed: {analysis_timestamp}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Anomaly Count Donut ---
donut_fig = go.Figure(data=[
    go.Pie(
        labels=['Anomalies', 'Normal Logs'],
        values=[anomaly_count, normal_count],
        hole=0.6,
        marker=dict(colors=['#ef4444', '#22d3ee']),
        textinfo='label+percent',
        insidetextorientation='radial',
    )
])
donut_fig.update_layout(
    showlegend=True,
    legend=dict(orientation='h', y=-0.1),
    margin=dict(t=20, b=20, l=0, r=0),
    height=350,
    paper_bgcolor='rgba(0,0,0,0)',
    font_color=st.get_option('theme.textColor')
)
st.plotly_chart(donut_fig, use_container_width=True)

# --- Two charts side by side ---
col_left, col_right = st.columns(2)

# Vulnerability Severity (Horizontal Bar)
with col_left:
    bar_fig = go.Figure(go.Bar(
        x=list(severity_counts.values()),
        y=list(severity_counts.keys()),
        orientation='h',
        marker=dict(color=['#dc2626', '#f59e42', '#fbbf24', '#38bdf8']),
        text=list(severity_counts.values()),
        textposition='auto',
    ))
    bar_fig.update_layout(
        title='Vulnerability Severity',
        xaxis_title='Count',
        yaxis_title='',
        height=350,
        margin=dict(t=40, b=20, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=st.get_option('theme.textColor')
    )
    st.plotly_chart(bar_fig, use_container_width=True)

# Anomaly Type Distribution (Donut)
with col_right:
    type_fig = go.Figure(data=[
        go.Pie(
            labels=list(anomaly_types.keys()),
            values=list(anomaly_types.values()),
            hole=0.5,
            marker=dict(colors=['#a21caf', '#2563eb', '#059669', '#eab308', '#64748b']),
            textinfo='label+percent',
            insidetextorientation='radial',
        )
    ])
    type_fig.update_layout(
        title='Anomaly Type Distribution',
        showlegend=True,
        legend=dict(orientation='h', y=-0.1),
        height=350,
        margin=dict(t=40, b=20, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        font_color=st.get_option('theme.textColor')
    )
    st.plotly_chart(type_fig, use_container_width=True) 
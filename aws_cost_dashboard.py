#!/usr/bin/env python3
"""
AWS Cost Explorer Dashboard
Streamlit-based interactive dashboard for AWS cost analysis and comparison.
"""

import streamlit as st
import boto3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import smtplib
import os
import io
import csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, date
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import calendar

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AWS Cost Explorer",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Dark background */
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}

[data-testid="stSidebar"] * {
    color: #e6edf3 !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
}

[data-testid="metric-container"] label {
    color: #8b949e !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #58a6ff !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.6rem !important;
    font-weight: 600;
}

[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace !important;
}

/* Headings */
h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #f0f6fc !important;
    letter-spacing: -0.02em;
}

h1 { font-size: 1.8rem !important; }
h2 { font-size: 1.2rem !important; color: #58a6ff !important; }

/* Dividers */
hr { border-color: #30363d !important; }

/* Buttons */
.stButton > button {
    background: #238636 !important;
    color: #ffffff !important;
    border: 1px solid #2ea043 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: #2ea043 !important;
    border-color: #3fb950 !important;
    transform: translateY(-1px);
}

/* Select boxes and inputs */
.stSelectbox > div, .stDateInput > div, .stTextInput > div {
    background: #161b22 !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid #30363d;
    border-radius: 8px;
    overflow: hidden;
}

/* Alerts */
.stAlert {
    border-radius: 8px !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #8b949e !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stTabs [aria-selected="true"] {
    color: #58a6ff !important;
    border-bottom-color: #58a6ff !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace !important;
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    color: #8b949e !important;
}

/* Badge/tag styles */
.badge-increase { color: #f85149; font-weight: 600; }
.badge-decrease { color: #3fb950; font-weight: 600; }
.badge-new { color: #e3b341; font-weight: 600; }

/* Section labels */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}

/* Top bar */
.top-bar {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 20px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AWS Regions
# ─────────────────────────────────────────────
AWS_REGIONS = [
    "ap-south-1", "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
    "ap-northeast-2", "ap-northeast-3", "ap-east-1", "ap-south-2",
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
    "eu-north-1", "eu-south-1",
    "ca-central-1", "sa-east-1",
    "me-south-1", "af-south-1",
]

GLOBAL_SERVICES = [
    'AWS CloudTrail', 'AWS Systems Manager', 'AWS Secrets Manager',
    'AWS Config', 'AWS Key Management Service', 'AWS Cost Explorer',
    'AWS CloudFront', 'Amazon Route 53', 'Amazon QuickSight',
    'Amazon Simple Email Service', 'Amazon Simple Notification Service',
    'Amazon Simple Queue Service',
]

# ─────────────────────────────────────────────
# Data Fetching
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_costs(start_date: str, end_date: str, aws_access_key: str, aws_secret_key: str, aws_region_session: str = "us-east-1"):
    """Fetch costs from AWS Cost Explorer."""
    session = boto3.Session(
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region_session,
    )
    ce = session.client('ce', region_name='us-east-1')

    # With region grouping
    response_region = ce.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {'Type': 'DIMENSION', 'Key': 'SERVICE'},
            {'Type': 'DIMENSION', 'Key': 'REGION'},
        ]
    )

    # Without region grouping
    response_global = ce.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    # Daily granularity for trend chart
    response_daily = ce.get_cost_and_usage(
        TimePeriod={'Start': start_date, 'End': end_date},
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
    )

    # Anomaly data
    try:
        anomaly_response = ce.get_anomalies(
            DateInterval={'StartDate': start_date, 'EndDate': end_date},
            TotalImpact={'NumericOperator': 'GREATER_THAN', 'StartValue': 1.0},
        )
        anomalies = anomaly_response.get('Anomalies', [])
    except Exception:
        anomalies = []

    return response_region, response_global, response_daily, anomalies


def parse_costs(response_region, response_global, target_region):
    """Parse cost responses into structured dicts."""
    costs_by_month = defaultdict(dict)
    all_services_by_month = defaultdict(dict)

    for result in response_global['ResultsByTime']:
        month = result['TimePeriod']['Start'][:7]
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            all_services_by_month[month][service] = cost

    for result in response_region['ResultsByTime']:
        month = result['TimePeriod']['Start'][:7]
        for group in result['Groups']:
            service = group['Keys'][0]
            region = group['Keys'][1]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            if region == target_region or service in GLOBAL_SERVICES:
                costs_by_month[month][service] = costs_by_month[month].get(service, 0) + cost

    for month in all_services_by_month:
        for service, cost in all_services_by_month[month].items():
            if service not in costs_by_month[month]:
                if (service.startswith('Tax') or 'Marketplace' in service or
                        service.startswith('[') or 'aws3.link' in service):
                    costs_by_month[month][service] = cost

    return costs_by_month


def build_comparison(month1_costs, month2_costs, label1, label2):
    """Build a comparison DataFrame."""
    all_services = set(month1_costs.keys()) | set(month2_costs.keys())
    rows = []
    for service in sorted(all_services):
        c1 = month1_costs.get(service, 0.0)
        c2 = month2_costs.get(service, 0.0)
        diff = c2 - c1
        if c1 > 0:
            pct = (diff / c1) * 100
        elif c2 > 0:
            pct = float('inf')
        else:
            pct = 0.0
        rows.append({
            'Service': service,
            label1: c1,
            label2: c2,
            'Difference ($)': diff,
            'Change (%)': pct,
            'Is Marketplace': (service.startswith('[') or 'MongoDB' in service or
                               'aws3.link' in service or
                               ('Marketplace' in service and 'AWS' not in service)),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# CSV Export
# ─────────────────────────────────────────────
def build_csv(df, label1, label2, total1, total2):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Service', f'{label1} ($)', f'{label2} ($)', 'Difference ($)', 'Change (%)'])

    aws_df = df[~df['Is Marketplace']]
    mkt_df = df[df['Is Marketplace']]

    writer.writerow(['=== AWS SERVICES ===', '', '', '', ''])
    for _, row in aws_df.iterrows():
        pct = 'NEW' if row['Change (%)'] == float('inf') else f"{row['Change (%)']:.1f}"
        writer.writerow([row['Service'], f"{row[label1]:.2f}", f"{row[label2]:.2f}",
                         f"{row['Difference ($)']:+.2f}", pct])
    writer.writerow(['AWS SUBTOTAL', f"{aws_df[label1].sum():.2f}", f"{aws_df[label2].sum():.2f}",
                     f"{(aws_df[label2].sum()-aws_df[label1].sum()):+.2f}",
                     f"{((aws_df[label2].sum()-aws_df[label1].sum())/aws_df[label1].sum()*100 if aws_df[label1].sum() else 0):+.1f}"])
    writer.writerow([])

    writer.writerow(['=== MARKETPLACE & THIRD-PARTY ===', '', '', '', ''])
    for _, row in mkt_df.iterrows():
        pct = 'NEW' if row['Change (%)'] == float('inf') else f"{row['Change (%)']:.1f}"
        writer.writerow([row['Service'], f"{row[label1]:.2f}", f"{row[label2]:.2f}",
                         f"{row['Difference ($)']:+.2f}", pct])
    if len(mkt_df):
        writer.writerow(['MARKETPLACE SUBTOTAL', f"{mkt_df[label1].sum():.2f}", f"{mkt_df[label2].sum():.2f}",
                         f"{(mkt_df[label2].sum()-mkt_df[label1].sum()):+.2f}", ''])
    writer.writerow([])

    total_diff = total2 - total1
    total_pct = (total_diff / total1 * 100) if total1 else 0
    writer.writerow(['GRAND TOTAL', f"{total1:.2f}", f"{total2:.2f}", f"{total_diff:+.2f}", f"{total_pct:+.1f}"])
    return buf.getvalue()


# ─────────────────────────────────────────────
# Email
# ─────────────────────────────────────────────
def send_email_report(sender, app_password, recipient, csv_data, df, label1, label2, total1, total2, region):
    increases = df[df['Difference ($)'] > 0].sort_values('Difference ($)', ascending=False).head(10)
    body = f"AWS Cost Comparison Report — {region}\n{label1} vs {label2}\n\n"
    body += f"{'Grand Total':<20} {label1}: ${total1:.2f}   {label2}: ${total2:.2f}   Δ ${total2-total1:+.2f}\n\n"
    body += "Top 10 Services with Biggest Cost Increases:\n" + "=" * 60 + "\n"
    for i, (_, row) in enumerate(increases.iterrows(), 1):
        pct = "NEW" if row['Change (%)'] == float('inf') else f"{row['Change (%)']:+.1f}%"
        body += f"{i}. {row['Service']}\n"
        body += f"   {label1}: ${row[label1]:.2f}  →  {label2}: ${row[label2]:.2f}  (Δ ${row['Difference ($)']:+.2f} {pct})\n\n"
    body += "\nSee attached CSV for full breakdown.\n"

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = f'AWS Cost Report — {region} ({label1} vs {label2})'
    msg.attach(MIMEText(body, 'plain'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(csv_data.encode())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename=aws_cost_comparison.csv')
    msg.attach(part)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.send_message(msg)


# ─────────────────────────────────────────────
# Plotly theme helper
# ─────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor='#161b22',
    plot_bgcolor='#0d1117',
    font=dict(family='IBM Plex Mono, monospace', color='#8b949e'),
    xaxis=dict(gridcolor='#21262d', linecolor='#30363d'),
    yaxis=dict(gridcolor='#21262d', linecolor='#30363d'),
    margin=dict(l=20, r=20, t=40, b=20),
)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ☁️ AWS Cost Explorer")
    st.markdown("---")

    st.markdown('<div class="section-label">AWS Credentials</div>', unsafe_allow_html=True)
    aws_key = st.text_input("Access Key ID", type="password", placeholder="AKIA...")
    aws_secret = st.text_input("Secret Access Key", type="password", placeholder="wJalrX...")

    st.markdown("---")
    st.markdown('<div class="section-label">Region</div>', unsafe_allow_html=True)
    target_region = st.selectbox("Target Region", AWS_REGIONS, index=0)

    st.markdown("---")
    st.markdown('<div class="section-label">Compare Months</div>', unsafe_allow_html=True)

    # Default: previous two months
    today = date.today()
    default_m1 = (today - relativedelta(months=2)).replace(day=1)
    default_m2 = (today - relativedelta(months=1)).replace(day=1)

    month1 = st.date_input("Month 1 (start)", value=default_m1)
    month2 = st.date_input("Month 2 (start)", value=default_m2)

    # Extend to 3-month trend
    include_trend = st.checkbox("Include 3rd month for trend", value=True)
    if include_trend:
        month0 = st.date_input("Month 0 (trend baseline)", value=(today - relativedelta(months=3)).replace(day=1))

    st.markdown("---")
    st.markdown('<div class="section-label">Budget Alert Threshold</div>', unsafe_allow_html=True)
    budget_threshold = st.number_input("Alert if service > $", min_value=0.0, value=100.0, step=10.0)

    st.markdown("---")
    fetch_btn = st.button("🔄  Fetch & Analyze", width="stretch")

    st.markdown("---")
    st.markdown('<div class="section-label">Email Report</div>', unsafe_allow_html=True)
    gmail_sender = st.text_input("Gmail Sender", placeholder="you@gmail.com")
    gmail_password = st.text_input("App Password", type="password", placeholder="16-char app password")
    recipient_email = st.text_input("Recipient Email", placeholder="team@company.com")
    send_btn = st.button("📧  Send Email Report", width="stretch")


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
st.markdown("# AWS Cost Explorer Dashboard")
st.markdown(f"Region: `{target_region}` &nbsp;|&nbsp; Built with Streamlit + AWS Cost Explorer API")
st.markdown("---")

# Session state for storing results
if 'data' not in st.session_state:
    st.session_state.data = None

# ─── FETCH ───
if fetch_btn:
    if not aws_key or not aws_secret:
        st.error("Please enter your AWS credentials in the sidebar.")
    else:
        # Build date range: from month0 (or month1) to end of month2
        m1_start = month1.strftime('%Y-%m-%d')
        m2_end_day = calendar.monthrange(month2.year, month2.month)[1]
        m2_end = month2.replace(day=m2_end_day)
        # Need first day of month AFTER month2 as end date for CE
        m2_end_exclusive = (month2 + relativedelta(months=1)).replace(day=1).strftime('%Y-%m-%d')

        if include_trend:
            fetch_start = month0.strftime('%Y-%m-%d')
        else:
            fetch_start = m1_start

        with st.spinner("Fetching data from AWS Cost Explorer..."):
            try:
                resp_region, resp_global, resp_daily, anomalies = fetch_costs(
                    fetch_start, m2_end_exclusive, aws_key, aws_secret
                )
                costs_by_month = parse_costs(resp_region, resp_global, target_region)

                label1 = month1.strftime('%b %Y')
                label2 = month2.strftime('%b %Y')
                m1_key = month1.strftime('%Y-%m')
                m2_key = month2.strftime('%Y-%m')

                m1_costs = costs_by_month.get(m1_key, {})
                m2_costs = costs_by_month.get(m2_key, {})
                df = build_comparison(m1_costs, m2_costs, label1, label2)

                # 3rd month
                m0_costs = {}
                label0 = ''
                if include_trend:
                    m0_key = month0.strftime('%Y-%m')
                    m0_costs = costs_by_month.get(m0_key, {})
                    label0 = month0.strftime('%b %Y')

                # Daily data
                daily_rows = []
                for result in resp_daily['ResultsByTime']:
                    daily_rows.append({
                        'Date': result['TimePeriod']['Start'],
                        'Cost': float(result['Total']['UnblendedCost']['Amount']),
                    })
                daily_df = pd.DataFrame(daily_rows)
                daily_df['Date'] = pd.to_datetime(daily_df['Date'])

                st.session_state.data = {
                    'df': df, 'label1': label1, 'label2': label2,
                    'label0': label0,
                    'm1_costs': m1_costs, 'm2_costs': m2_costs, 'm0_costs': m0_costs,
                    'daily_df': daily_df, 'anomalies': anomalies,
                    'costs_by_month': costs_by_month,
                    'target_region': target_region,
                    'budget_threshold': budget_threshold,
                }
                st.success("✅ Data fetched successfully!")
            except Exception as e:
                st.error(f"Error fetching data: {e}")

# ─── DISPLAY ───
if st.session_state.data:
    d = st.session_state.data
    df = d['df']
    label1, label2 = d['label1'], d['label2']
    m1_costs, m2_costs = d['m1_costs'], d['m2_costs']
    daily_df = d['daily_df']
    anomalies = d['anomalies']

    total1 = sum(m1_costs.values())
    total2 = sum(m2_costs.values())
    total_diff = total2 - total1
    total_pct = (total_diff / total1 * 100) if total1 else 0

    # ── Anomaly Banner ──
    if anomalies:
        st.warning(f"⚠️ AWS detected **{len(anomalies)} cost anomaly/anomalies** in this period. Check the Anomalies tab.")

    # ── Budget Breach Banner ──
    breach = df[df[label2] > d['budget_threshold']]
    if not breach.empty:
        names = ', '.join(breach['Service'].tolist()[:5])
        st.warning(f"💸 **Budget threshold exceeded** (>${d['budget_threshold']:.0f}) by: {names}")

    # ── KPI Row ──
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(f"Total — {label1}", f"${total1:,.2f}")
    col2.metric(f"Total — {label2}", f"${total2:,.2f}", delta=f"${total_diff:+,.2f}")
    col3.metric("Change %", f"{total_pct:+.1f}%")
    col4.metric("Services Tracked", str(len(df)))
    increases_count = len(df[df['Difference ($)'] > 0])
    col5.metric("Services Increased", str(increases_count))

    st.markdown("---")

    # ── TABS ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "🔍 Service Breakdown", "📈 Daily Trend", "🏪 Marketplace", "🚨 Anomalies"
    ])

    # ════════════════ TAB 1: OVERVIEW ════════════════
    with tab1:
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown(f"### Top 10 — Biggest Increases ({label1} → {label2})")

            top_increases = (
                df[
                    (df['Difference ($)'].round(2) > 0.01) &
                    (~df['Service'].str.startswith('Tax')) &
                    (~df['Is Marketplace'])
                ]
                .sort_values('Difference ($)', ascending=False)
                .head(10)
                .copy()
            )

            if top_increases.empty:
                st.warning(f"⚠️ No cost increases found. Make sure Month 2 is set to the **1st of the month** (e.g. 2026/04/01) for a full month comparison.")
            else:
                top_increases['Label'] = (
                    top_increases['Service']
                    .str.replace('Amazon ', '', regex=False)
                    .str.replace('AWS ', '', regex=False)
                    .str[:32]
                )
                top_increases['Diff_display'] = top_increases['Difference ($)'].apply(
                    lambda v: f"+${v:,.2f}"
                )
                top_increases['Pct_display'] = top_increases['Change (%)'].apply(
                    lambda v: "NEW" if v == float('inf') else f"+{v:.1f}%"
                )
                top_increases['hover_label'] = (
                    top_increases['Service'] + "<br>" +
                    label1 + ": $" + top_increases[label1].map("{:,.2f}".format) +
                    "  →  " + label2 + ": $" + top_increases[label2].map("{:,.2f}".format) +
                    "<br>Increase: " + top_increases['Diff_display'] +
                    "  (" + top_increases['Pct_display'] + ")"
                )

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=top_increases['Difference ($)'],
                    y=top_increases['Label'],
                    orientation='h',
                    text=top_increases['Diff_display'],
                    textposition='outside',
                    hovertext=top_increases['hover_label'],
                    hoverinfo='text',
                    marker=dict(
                        color=top_increases['Difference ($)'],
                        colorscale=[[0, '#1f6feb'], [0.5, '#e3b341'], [1, '#f85149']],
                        showscale=False,
                    ),
                ))
                layout_overrides = {
                    **PLOT_LAYOUT,
                    'showlegend': False,
                    'height': 420,
                    'xaxis': {**PLOT_LAYOUT.get('xaxis', {}), 'title': 'Increase ($)', 'tickprefix': '$'},
                    'yaxis': {**PLOT_LAYOUT.get('yaxis', {}), 'autorange': 'reversed', 'title': ''},
                    'margin': dict(l=20, r=100, t=40, b=20),
                }
                fig.update_layout(**layout_overrides)
                st.plotly_chart(fig, width="stretch")

        with col_right:
            st.markdown("### Cost Distribution — " + label2)
            # Exclude Tax from pie — it skews the real service breakdown
            pie_df = df[df[label2] > 0 & ~df['Service'].str.startswith('Tax')].nlargest(12, label2)
            # Shorten long service names for cleaner labels
            pie_df = pie_df.copy()
            pie_df['Label'] = pie_df['Service'].str.replace('Amazon ', '').str.replace('AWS ', '').str[:28]
            DISTINCT_COLORS = [
                '#58a6ff','#3fb950','#e3b341','#f85149','#bc8cff',
                '#79c0ff','#56d364','#ffa657','#ff7b72','#d2a8ff',
                '#39d353','#ffd700',
            ]
            fig2 = px.pie(
                pie_df, values=label2, names='Label',
                hole=0.55,
                color_discrete_sequence=DISTINCT_COLORS,
            )
            fig2.update_traces(
                textposition='outside',
                textinfo='percent',
                hovertemplate='<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>',
                pull=[0.03] * len(pie_df),
            )
            fig2.update_layout(
                **PLOT_LAYOUT, height=420,
                showlegend=True,
                legend=dict(
                    font=dict(color='#8b949e', size=11, family='IBM Plex Mono, monospace'),
                    bgcolor='rgba(0,0,0,0)',
                    bordercolor='#30363d',
                    borderwidth=1,
                    orientation='v',
                    x=1.02, y=0.5,
                ),
                annotations=[dict(
                    text=f"<b style='font-size:13px'>{label2}</b><br>excl. Tax",
                    x=0.5, y=0.5, font=dict(color='#8b949e', size=11), showarrow=False
                )]
            )
            st.plotly_chart(fig2, width="stretch")

        # Month-over-month grouped bar for top 15
        st.markdown("### Month-over-Month — Top 15 Services")
        top15 = df.nlargest(15, label2)
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name=label1, x=top15['Service'], y=top15[label1],
                              marker_color='#1f6feb'))
        fig3.add_trace(go.Bar(name=label2, x=top15['Service'], y=top15[label2],
                              marker_color='#58a6ff'))
        fig3.update_layout(**PLOT_LAYOUT, barmode='group', height=380,
                           legend=dict(font=dict(color='#8b949e')))
        st.plotly_chart(fig3, width="stretch")

        # 3-month trend bars (if available)
        if d['m0_costs'] and d['label0']:
            st.markdown("### 3-Month Total Cost Trend")
            trend_df = pd.DataFrame([
                {'Month': d['label0'], 'Total': sum(d['m0_costs'].values())},
                {'Month': label1, 'Total': total1},
                {'Month': label2, 'Total': total2},
            ])
            fig4 = px.bar(trend_df, x='Month', y='Total', text='Total',
                          color='Total', color_continuous_scale=[[0, '#1f6feb'], [1, '#58a6ff']])
            fig4.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
            fig4.update_layout(**PLOT_LAYOUT, showlegend=False, coloraxis_showscale=False, height=300)
            st.plotly_chart(fig4, width="stretch")

    # ════════════════ TAB 2: SERVICE BREAKDOWN ════════════════
    with tab2:
        st.markdown("### All Services — Detailed Comparison")

        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            filter_type = st.selectbox("Filter", ["All", "Increases Only", "Decreases Only", "New Services"])
        with filter_col2:
            min_cost = st.number_input("Min cost ($) to show", min_value=0.0, value=0.0, step=1.0)
        with filter_col3:
            sort_col = st.selectbox("Sort by", [label2, label1, 'Difference ($)', 'Change (%)'])

        display_df = df[~df['Is Marketplace']].copy()

        if filter_type == "Increases Only":
            display_df = display_df[display_df['Difference ($)'] > 0]
        elif filter_type == "Decreases Only":
            display_df = display_df[display_df['Difference ($)'] < 0]
        elif filter_type == "New Services":
            display_df = display_df[display_df[label1] == 0]

        display_df = display_df[display_df[label2] >= min_cost]
        display_df = display_df.sort_values(sort_col, ascending=False, key=lambda x: x.replace(float('inf'), 9999))

        def highlight_diff(val):
            if isinstance(val, float):
                if val > 0:
                    return 'color: #f85149'
                elif val < 0:
                    return 'color: #3fb950'
            return ''

        table_df = (
            display_df[['Service', label1, label2, 'Difference ($)', 'Change (%)']]
            .reset_index(drop=True)
        )
        styled = (
            table_df.style
            .format({label1: '${:.2f}', label2: '${:.2f}', 'Difference ($)': '${:+.2f}',
                     'Change (%)': lambda v: 'NEW' if v == float('inf') else f'{v:+.1f}%'})
            .map(highlight_diff, subset=['Difference ($)'])
            .set_properties(**{'background-color': '#0d1117', 'color': '#e6edf3',
                               'border': '1px solid #21262d'})
            .set_table_styles([
                {'selector': 'th', 'props': [('background-color', '#161b22'),
                                             ('color', '#58a6ff'),
                                             ('font-family', 'IBM Plex Mono, monospace'),
                                             ('font-size', '0.75rem')]},
            ])
        )
        st.dataframe(styled, width="stretch", height=500)

        # CSV Download
        csv_data = build_csv(df, label1, label2, total1, total2)
        st.download_button(
            label="⬇️ Download CSV Report",
            data=csv_data,
            file_name=f"aws_cost_{d['target_region']}_{label1.replace(' ', '_')}_vs_{label2.replace(' ', '_')}.csv",
            mime='text/csv',
        )

    # ════════════════ TAB 3: DAILY TREND ════════════════
    with tab3:
        st.markdown("### Daily Spend Trend")
        if not daily_df.empty:
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(
                x=daily_df['Date'], y=daily_df['Cost'],
                mode='lines+markers',
                line=dict(color='#58a6ff', width=2),
                marker=dict(size=4, color='#1f6feb'),
                fill='tozeroy',
                fillcolor='rgba(31, 111, 235, 0.1)',
                name='Daily Cost',
            ))
            # Rolling 7-day average
            daily_df['Rolling7'] = daily_df['Cost'].rolling(7, min_periods=1).mean()
            fig5.add_trace(go.Scatter(
                x=daily_df['Date'], y=daily_df['Rolling7'],
                mode='lines',
                line=dict(color='#e3b341', width=2, dash='dash'),
                name='7-day Avg',
            ))
            fig5.update_layout(**PLOT_LAYOUT, height=400,
                               legend=dict(font=dict(color='#8b949e')))
            st.plotly_chart(fig5, width="stretch")

            # Stats
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Peak Day", f"${daily_df['Cost'].max():.2f}", daily_df.loc[daily_df['Cost'].idxmax(), 'Date'].strftime('%b %d'))
            c2.metric("Lowest Day", f"${daily_df['Cost'].min():.2f}")
            c3.metric("Avg/Day", f"${daily_df['Cost'].mean():.2f}")
            c4.metric("7-day Avg (latest)", f"${daily_df['Rolling7'].iloc[-1]:.2f}")
        else:
            st.info("No daily data available for selected range.")

    # ════════════════ TAB 4: MARKETPLACE ════════════════
    with tab4:
        st.markdown("### AWS Marketplace & Third-Party")
        mkt_df = df[df['Is Marketplace']].copy()
        if mkt_df.empty:
            st.info("No Marketplace or third-party charges found in this period.")
        else:
            mkt1 = mkt_df[label1].sum()
            mkt2 = mkt_df[label2].sum()
            mkt_diff = mkt2 - mkt1
            m1, m2, m3 = st.columns(3)
            m1.metric(label1, f"${mkt1:.2f}")
            m2.metric(label2, f"${mkt2:.2f}", delta=f"${mkt_diff:+.2f}")
            m3.metric("% of Total", f"{(mkt2/total2*100) if total2 else 0:.1f}%")

            fig_mkt = px.bar(
                mkt_df.sort_values(label2, ascending=False),
                x='Service', y=[label1, label2],
                barmode='group',
                color_discrete_map={label1: '#1f6feb', label2: '#58a6ff'},
            )
            fig_mkt.update_layout(**PLOT_LAYOUT, height=350)
            st.plotly_chart(fig_mkt, width="stretch")

            st.dataframe(
                mkt_df[['Service', label1, label2, 'Difference ($)']].style
                .format({label1: '${:.2f}', label2: '${:.2f}', 'Difference ($)': '${:+.2f}'}),
                width="stretch",
            )

    # ════════════════ TAB 5: ANOMALIES ════════════════
    with tab5:
        st.markdown("### AWS Cost Anomalies")
        if not anomalies:
            st.success("✅ No anomalies detected by AWS for this period.")
        else:
            for a in anomalies:
                impact = a.get('TotalImpact', {})
                svc = a.get('RootCauses', [{}])[0].get('Service', 'Unknown')
                start = a.get('AnomalyStartDate', '')
                end = a.get('AnomalyEndDate', 'Ongoing')
                actual = impact.get('TotalActualSpend', 0)
                expected = impact.get('TotalExpectedSpend', 0)
                total_impact = impact.get('TotalImpact', 0)
                with st.expander(f"🔴 {svc} — ${total_impact:.2f} over-spend ({start} → {end})"):
                    st.write(f"**Actual:** ${actual:.2f}   |   **Expected:** ${expected:.2f}   |   **Delta:** ${total_impact:.2f}")
                    st.write(f"**Root Causes:** {a.get('RootCauses', [])}")

    # ─── EMAIL SEND ───
    if send_btn:
        if not gmail_sender or not gmail_password or not recipient_email:
            st.error("Fill in all email fields in the sidebar.")
        else:
            csv_data = build_csv(df, label1, label2, total1, total2)
            with st.spinner("Sending email..."):
                try:
                    send_email_report(
                        gmail_sender, gmail_password, recipient_email,
                        csv_data, df, label1, label2, total1, total2,
                        d['target_region']
                    )
                    st.success(f"✅ Email sent to {recipient_email}")
                except Exception as e:
                    st.error(f"Failed to send email: {e}")

else:
    # ── Empty state ──
    st.markdown("""
    <div style="
        background:#161b22; border:1px solid #30363d; border-radius:12px;
        padding:60px 40px; text-align:center; margin-top:40px;
    ">
        <div style="font-size:3rem;">☁️</div>
        <h2 style="color:#58a6ff; font-family:'IBM Plex Mono',monospace; margin-top:16px;">
            No data loaded yet
        </h2>
        <p style="color:#8b949e; font-family:'IBM Plex Sans',sans-serif; margin-top:8px;">
            Enter your AWS credentials and click <strong style="color:#e6edf3;">Fetch & Analyze</strong> to get started.
        </p>
        <div style="margin-top:32px; color:#30363d; font-size:0.8rem; font-family:'IBM Plex Mono',monospace;">
            Credentials are used only for this session and never stored.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("ℹ️ Setup Instructions"):
        st.markdown("""
**1. AWS Credentials**
- You need an IAM user/role with `ce:GetCostAndUsage`, `ce:GetCostForecast`, `ce:GetAnomalies` permissions.
- Go to IAM → Users → Security Credentials → Create Access Key.

**2. Gmail App Password**
- Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- Create a 16-character app password (not your regular password).

**3. Running Locally**
```bash
pip install streamlit boto3 plotly pandas python-dateutil
streamlit run aws_cost_dashboard.py
```

**4. Hosting on EC2**
```bash
# On a t3.micro Ubuntu instance:
pip install streamlit boto3 plotly pandas python-dateutil
nohup streamlit run aws_cost_dashboard.py --server.port 8501 &
# Open port 8501 in your security group
```
        """)
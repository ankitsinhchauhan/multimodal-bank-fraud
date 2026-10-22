import json
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --------------------------------------------------
# 1. PROJECT PATHS AND PAGE CONFIGURATION
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
TX = ROOT / "data" / "structured" / "transactions_100k.csv"
REPORTS = ROOT / "reports"

st.set_page_config(
    page_title="Bank Fraud Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# 2. CUSTOM CSS - LIGHT & DARK THEME ADAPTIVE
# --------------------------------------------------

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
    }

    /* Page Container Top Clearance */
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 2.5rem;
        max-width: 1600px;
    }

    /* Top Hero Header Section */
    .hero {
        padding: 26px 30px;
        border-radius: 18px;
        margin-top: 10px;
        background: linear-gradient(120deg, #0f172a, #1e293b 60%, #334155);
        border: 1px solid #334155;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        color: #ffffff !important;
    }

    .hero h1 {
        font-size: clamp(1.6rem, 2.8vw, 2.2rem);
        font-weight: 800;
        color: #ffffff !important;
        margin: 0 0 6px 0;
    }

    .hero p {
        color: #cbd5e1 !important;
        margin: 0;
        font-size: 0.95rem;
    }

    .eyebrow {
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.72rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 750;
        margin: 16px 0 12px 0;
    }

    /* KPI Cards Styling */
    .kpi {
        padding: 18px;
        border-radius: 16px;
        min-height: 125px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.22s ease, border-color 0.22s ease;
    }

    .kpi:hover {
        transform: translateY(-3px);
        border-color: #0284c7;
    }

    .kpi-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .kpi-value {
        color: #0f172a;
        font-size: clamp(1.1rem, 1.4vw, 1.65rem);
        font-weight: 800;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .kpi-note {
        color: #0284c7;
        font-size: 0.75rem;
        margin-top: 6px;
        font-weight: 600;
    }

    /* Panel Card Container */
    .panel {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.02);
    }

    .status-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 5px 11px;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.3);
        font-size: 0.74rem;
        font-weight: 700;
    }

    /* SIDEBAR MULTISELECT TAGS COLOR FIX (Replaced Red with Theme Blue) */
    span[data-baseweb="tag"] {
        background-color: #e0f2fe !important;
        border: 1px solid #bae6fd !important;
        border-radius: 6px !important;
    }

    span[data-baseweb="tag"] * {
        color: #0369a1 !important;
    }

    .footer {
        text-align: center;
        opacity: 0.75;
        font-size: 0.8rem;
        padding: 25px 0 5px 0;
    }

    /* DARK MODE OVERRIDES WHEN SWITCHED IN STREAMLIT MENU */
    @media (prefers-color-scheme: dark) {
        .kpi {
            background: rgba(18, 38, 66, 0.6) !important;
            border-color: rgba(148, 163, 184, 0.2) !important;
        }
        .kpi-label { color: #a9bbd1 !important; }
        .kpi-value { color: #f8fafc !important; }
        .kpi-note { color: #67e8f9 !important; }
        .panel {
            background: rgba(18, 38, 66, 0.5) !important;
            border-color: rgba(148, 163, 184, 0.2) !important;
        }
        span[data-baseweb="tag"] {
            background-color: rgba(103, 232, 249, 0.18) !important;
            border: 1px solid rgba(103, 232, 249, 0.4) !important;
        }
        span[data-baseweb="tag"] * {
            color: #67e8f9 !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# 3. HELPER FUNCTIONS
# --------------------------------------------------

def find_column(data, candidates):
    """Find the first matching column, ignoring letter case."""
    lookup = {str(c).lower(): c for c in data.columns}

    for name in candidates:
        if name.lower() in lookup:
            return lookup[name.lower()]

    return None


def money(value):
    if pd.isna(value):
        return "N/A"
    if value >= 10000000:
        return f"₹{value/10000000:,.2f} Cr"
    elif value >= 100000:
        return f"₹{value/100000:,.2f} Lk"
    return f"₹{value:,.2f}"


def style_chart(fig, height=360):
    """Apply consistent styling to Plotly charts."""
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="left",
            x=0
        )
    )

    fig.update_xaxes(
        gridcolor="rgba(148,163,184,0.15)",
        zerolinecolor="rgba(148,163,184,0.15)"
    )

    fig.update_yaxes(
        gridcolor="rgba(148,163,184,0.15)",
        zerolinecolor="rgba(148,163,184,0.15)"
    )

    return fig


def kpi_card(label, value, note, delay=0):
    st.markdown(
        f"""
        <div class="kpi" style="animation-delay:{delay}s">
            <div>
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" title="{value}">{value}</div>
            </div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# --------------------------------------------------
# 4. LOAD DATA
# --------------------------------------------------

@st.cache_data(show_spinner="Loading transaction dataset...")
def load_data(path, modified_time):
    data = pd.read_csv(path)

    fraud_col = find_column(data, ["fraud_label", "is_fraud", "fraud"])
    if fraud_col:
        data[fraud_col] = pd.to_numeric(data[fraud_col], errors="coerce")

    amount_col = find_column(data, ["amount", "transaction_amount", "txn_amount"])
    if amount_col:
        data[amount_col] = pd.to_numeric(data[amount_col], errors="coerce")

    date_col = find_column(
        data,
        ["timestamp", "transaction_timestamp", "transaction_time", "transaction_date", "event_time", "date", "datetime"]
    )
    if date_col:
        data["_dashboard_datetime"] = pd.to_datetime(data[date_col], errors="coerce", utc=True)

    return data


# --------------------------------------------------
# 5. PAGE HEADER
# --------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="eyebrow">BIG DATA • FRAUD INTELLIGENCE</div>
    <h1>Bank Transaction Analytics</h1>
    <p>
        Monitor transaction patterns, explore simulated fraud labels,
        and analyze financial activity using interactive visualizations.
    </p>
    <br>
    <span class="status-pill">SYNTHETIC DATA DEMONSTRATION</span>
</div>
""", unsafe_allow_html=True)


if not TX.exists():
    st.error(f"Dataset not found: {TX}\n\nRun `python scripts/generate_data.py` first.")
    st.stop()


try:
    df = load_data(str(TX), TX.stat().st_mtime)
except Exception as exc:
    st.error(f"Could not load transaction dataset: {exc}")
    st.stop()


if df.empty:
    st.warning("The transaction dataset is empty.")
    st.stop()


# --------------------------------------------------
# 6. IDENTIFY IMPORTANT COLUMNS
# --------------------------------------------------

amount_col = find_column(df, ["amount", "transaction_amount", "txn_amount"])
fraud_col = find_column(df, ["fraud_label", "is_fraud", "fraud"])
type_col = find_column(df, ["transaction_type", "type", "transaction_category", "category"])
location_col = find_column(df, ["location", "city", "transaction_location", "region"])
merchant_col = find_column(df, ["merchant", "merchant_name", "merchant_category"])
id_col = find_column(df, ["transaction_id", "txn_id", "id"])
date_col = "_dashboard_datetime" if "_dashboard_datetime" in df.columns else None


# --------------------------------------------------
# 7. SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.markdown("## Analytics Controls")
st.sidebar.caption("Filters update the charts and table.")

view = df.copy()

if type_col:
    all_types = sorted(view[type_col].dropna().astype(str).unique().tolist())
    selected_types = st.sidebar.multiselect("Transaction type", all_types, default=all_types)
    view = view[view[type_col].astype(str).isin(selected_types)]

if fraud_col:
    view["_dashboard_label"] = view[fraud_col].map({0: "Normal", 1: "Simulated Fraud"})
    view.loc[view[fraud_col] == 0, "_dashboard_label"] = "Normal"
    view.loc[view[fraud_col] == 1, "_dashboard_label"] = "Simulated Fraud"

    available_labels = [label for label in ["Normal", "Simulated Fraud"] if label in view["_dashboard_label"].dropna().unique()]
    selected_labels = st.sidebar.multiselect("Transaction label", available_labels, default=available_labels)
    view = view[view["_dashboard_label"].isin(selected_labels)]

if date_col and view[date_col].notna().any():
    valid_dates = view[date_col].dropna()
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    selected_dates = st.sidebar.date_input(
        "Transaction date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        view = view[view[date_col].dt.date.between(start_date, end_date)]

st.sidebar.divider()
st.sidebar.caption(f"Dataset rows: {len(df):,}")
st.sidebar.caption(f"Filtered rows: {len(view):,}")


# --------------------------------------------------
# 8. KPI CARDS
# --------------------------------------------------

st.markdown('<div class="section-title">Executive Overview</div>', unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card("TRANSACTIONS", f"{len(view):,}", "Records after filters", 0.0)

with k2:
    if amount_col and not view[amount_col].dropna().empty:
        total_amount = view[amount_col].sum()
        value = money(total_amount)
    else:
        value = "N/A"
    kpi_card("TOTAL AMOUNT", value, "Sum of selected transactions", 0.08)

with k3:
    if amount_col and not view[amount_col].dropna().empty:
        average_amount = money(view[amount_col].mean())
    else:
        average_amount = "N/A"
    kpi_card("AVERAGE AMOUNT", average_amount, "Mean transaction value", 0.16)

with k4:
    if fraud_col and len(view):
        fraud_count = int((view[fraud_col] == 1).sum())
        fraud_rate = fraud_count / len(view) * 100
        fraud_value = f"{fraud_rate:.2f}%"
        fraud_note = f"{fraud_count:,} simulated fraud labels"
    else:
        fraud_value = "N/A"
        fraud_note = "Fraud label unavailable"
    kpi_card("SIMULATED FRAUD RATE", fraud_value, fraud_note, 0.24)

st.caption("All fraud metrics are based on synthetic, rule-derived labels; they are not verified real-world fraud outcomes.")


# --------------------------------------------------
# 9. CHARTS - DONUT AND AMOUNT DISTRIBUTION
# --------------------------------------------------

st.markdown('<div class="section-title">Transaction Insights</div>', unsafe_allow_html=True)

left, right = st.columns(2)

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Fraud vs Normal Transactions")

    if fraud_col and len(view):
        donut_data = view[fraud_col].map({0: "Normal", 1: "Simulated Fraud"}).fillna("Unknown").value_counts().reset_index()
        donut_data.columns = ["Label", "Count"]

        fig = px.pie(
            donut_data,
            names="Label",
            values="Count",
            hole=0.65,
            color="Label",
            color_discrete_map={
                "Normal": "#0284c7",
                "Simulated Fraud": "#fb7185",
                "Unknown": "#94a3b8"
            }
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            insidetextfont=dict(size=14, color="#ffffff", family="Inter"),
            outsidetextfont=dict(size=14, family="Inter"),
            pull=[0.03] * len(donut_data)
        )

        style_chart(fig, 380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Fraud label column is not available.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Transaction Amount Distribution")

    if amount_col and not view[amount_col].dropna().empty:
        color_col = "_dashboard_label" if "_dashboard_label" in view.columns else None

        fig = px.histogram(
            view,
            x=amount_col,
            color=color_col,
            nbins=40,
            opacity=0.85,
            barmode="overlay",
            color_discrete_map={
                "Normal": "#0284c7",
                "Simulated Fraud": "#fb7185"
            },
            labels={amount_col: "Transaction amount"}
        )

        style_chart(fig, 380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Transaction amount column is not available.")
    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# 10. CATEGORY CHART AND DAILY TREND
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Transaction Type Analysis")

    if type_col and len(view):
        group_cols = [type_col]
        if "_dashboard_label" in view.columns:
            group_cols.append("_dashboard_label")

        agg = view.groupby(group_cols, dropna=False).size().reset_index(name="Transaction Count")
        color_col = "_dashboard_label" if "_dashboard_label" in agg.columns else None

        fig = px.bar(
            agg,
            x=type_col,
            y="Transaction Count",
            color=color_col,
            barmode="group",
            color_discrete_map={
                "Normal": "#0284c7",
                "Simulated Fraud": "#fb7185"
            },
            labels={type_col: "Transaction Type"}
        )

        fig.update_layout(xaxis_tickangle=-20)
        style_chart(fig, 380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Transaction type column is not available.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Daily Transaction Trend")

    if date_col and view[date_col].notna().any():
        trend_data = view.dropna(subset=[date_col]).copy()
        trend_data["_day"] = trend_data[date_col].dt.date
        daily = trend_data.groupby("_day").size().reset_index(name="Transactions")

        fig = px.line(
            daily,
            x="_day",
            y="Transactions",
            markers=True,
            labels={"_day": "Date", "Transactions": "Transaction count"}
        )

        fig.update_traces(line=dict(width=3, color="#0284c7"), marker=dict(size=6))
        style_chart(fig, 380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recognized timestamp/date column was found.")
    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# 11. HOURLY ACTIVITY AND LOCATION ANALYTICS
# --------------------------------------------------

left, right = st.columns(2)

with left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Transaction Activity by Hour")

    if date_col and view[date_col].notna().any():
        hourly_data = view.dropna(subset=[date_col]).copy()
        hourly_data["_hour"] = hourly_data[date_col].dt.hour
        hourly = hourly_data.groupby("_hour").size().reindex(range(24), fill_value=0).reset_index()
        hourly.columns = ["Hour", "Transactions"]

        fig = px.bar(hourly, x="Hour", y="Transactions", labels={"Hour": "Hour of day"})
        fig.update_traces(marker_color="#6366f1")
        style_chart(fig, 350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Timestamp data is unavailable.")
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Location Analytics")

    if location_col and len(view):
        location_summary = (
            view.groupby(location_col, dropna=False)
            .agg(Transactions=(location_col, "size"))
            .reset_index()
            .sort_values("Transactions", ascending=False)
            .head(12)
        )

        fig = px.bar(
            location_summary.sort_values("Transactions"),
            x="Transactions",
            y=location_col,
            orientation="h",
            labels={location_col: "Location"}
        )

        fig.update_traces(marker_color="#10b981")
        style_chart(fig, 350)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Location column is unavailable.")
    st.markdown("</div>", unsafe_allow_html=True)


# --------------------------------------------------
# 12. CORRELATION HEATMAP
# --------------------------------------------------

st.markdown('<div class="section-title">Numerical Relationship Analysis</div>', unsafe_allow_html=True)

numeric_cols = view.select_dtypes(include="number").columns.tolist()
numeric_cols = [c for c in numeric_cols if c.lower() not in {"transaction_id", "customer_id", "account_id", "id", "txn_id"}]

if len(numeric_cols) >= 2 and len(view) >= 2:
    corr = view[numeric_cols].corr(numeric_only=True)

    fig = px.imshow(
        corr,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="Blues",
        zmin=-1,
        zmax=1,
        labels=dict(color="Correlation")
    )

    style_chart(fig, max(400, 45 * len(numeric_cols)))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("At least two numeric columns are required for a correlation heatmap.")


# --------------------------------------------------
# 13. TRANSACTION EXPLORER AND CSV DOWNLOAD
# --------------------------------------------------

st.markdown('<div class="section-title">Transaction Explorer</div>', unsafe_allow_html=True)

search_text = st.text_input("Search visible records", placeholder="Search transaction ID, customer ID, merchant, location...")

table_view = view.copy()

if search_text.strip():
    text_columns = table_view.select_dtypes(include=["object", "string"]).columns.tolist()
    mask = table_view[text_columns].astype(str).apply(
        lambda col: col.str.contains(search_text, case=False, na=False, regex=False)
    ).any(axis=1) if text_columns else pd.Series(False, index=table_view.index)

    if id_col and id_col not in text_columns:
        mask = mask | table_view[id_col].astype(str).str.contains(search_text, case=False, na=False, regex=False)

    table_view = table_view[mask]

st.caption(f"Showing {min(len(table_view), 500):,} of {len(table_view):,} matching records.")

st.dataframe(
    table_view.drop(columns=["_dashboard_datetime", "_dashboard_label"], errors="ignore").head(500),
    use_container_width=True,
    hide_index=True
)

csv_data = table_view.drop(columns=["_dashboard_datetime", "_dashboard_label"], errors="ignore").to_csv(index=False).encode("utf-8")

st.download_button("Download filtered transactions as CSV", data=csv_data, file_name="filtered_bank_transactions.csv", mime="text/csv")


# --------------------------------------------------
# 14. REPORTS SECTION
# --------------------------------------------------

st.markdown('<div class="section-title">Project Reports</div>', unsafe_allow_html=True)

report_files = [
    ("validation_report.json", "Data Quality Validation"),
    ("model_metrics.json", "Fraud Model Metrics"),
    ("statistical_report.json", "Statistical Analytics"),
    ("monitoring_snapshot.json", "Monitoring Snapshot"),
    ("batch_summary.json", "Batch Processing Summary")
]

report_cols = st.columns(2)

for index, (filename, title) in enumerate(report_files):
    report_path = REPORTS / filename

    with report_cols[index % 2]:
        with st.expander(f"{title}"):
            if report_path.exists():
                try:
                    report_content = json.loads(report_path.read_text(encoding="utf-8"))
                    st.json(report_content)
                except Exception:
                    st.text(report_path.read_text(encoding="utf-8", errors="replace"))
            else:
                st.caption(f"{filename} has not been generated yet.")


# --------------------------------------------------
# 15. FOOTER
# --------------------------------------------------

st.markdown("""
<div class="footer">
    Multimodal Bank Transaction & Fraud Detection Analytics<br>
    Academic demonstration • Synthetic data • Not for real banking decisions
</div>
""", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import plotly.express as px
from fredapi import Fred
from io import BytesIO

# ==================================
# FRED KEY
# ==================================

FRED_API_KEY = "2132d80f475773a92941db7ac291147a"

fred = Fred(api_key=FRED_API_KEY)

# ==================================
# Page
# ==================================

st.set_page_config(
    page_title="FRED 經濟儀表板",
    page_icon="📈",
    layout="wide"
)

st.title("📈 FRED 全球總經儀表板")

# ==================================
# 指標
# ==================================

INDICATORS = {

    "GDP": "GDP",

    "CPI":
    "CPIAUCSL",

    "Core CPI":
    "CPILFESL",

    "PCE":
    "PCE",

    "Core PCE":
    "PCEPILFE",

    "Unemployment":
    "UNRATE",

    "Fed Funds":
    "FEDFUNDS",

    "M2":
    "M2SL",

    "US 10Y":
    "GS10",

    "US 2Y":
    "GS2",

    "Retail Sales":
    "RSAFS"
}

# ==================================
# Sidebar
# ==================================

indicator_name = st.sidebar.selectbox(
    "指標",
    list(INDICATORS.keys())
)

transform = st.sidebar.selectbox(
    "顯示方式",
    [
        "Level",
        "YoY %",
        "MoM %",
        "QoQ %",
        "QoQ SAAR %"
    ]
)

start_date = st.sidebar.date_input(
    "起始日期",
    pd.Timestamp("2000-01-01")
)

# ==================================
# Download
# ==================================

series = fred.get_series(
    INDICATORS[indicator_name]
)

df = pd.DataFrame(series)

df.columns = ["Value"]

df.index.name = "Date"

df.reset_index(inplace=True)

df = df[df["Date"] >= pd.Timestamp(start_date)]

# ==================================
# Transform
# ==================================

if transform == "YoY %":

    df["Value"] = (
        df["Value"]
        .pct_change(12)
        * 100
    )

elif transform == "MoM %":

    df["Value"] = (
        df["Value"]
        .pct_change(1)
        * 100
    )

elif transform == "QoQ %":

    df["Value"] = (
        df["Value"]
        .pct_change(3)
        * 100
    )

elif transform == "QoQ SAAR %":

    qoq = df["Value"].pct_change(3)

    df["Value"] = (
        ((1 + qoq) ** 4 - 1)
        * 100
    )

# ==================================
# Metrics
# ==================================

latest = df["Value"].dropna().iloc[-1]

max_value = df["Value"].max()

min_value = df["Value"].min()

c1, c2, c3 = st.columns(3)

c1.metric(
    "最新值",
    f"{latest:.2f}"
)

c2.metric(
    "最高值",
    f"{max_value:.2f}"
)

c3.metric(
    "最低值",
    f"{min_value:.2f}"
)

# ==================================
# Chart
# ==================================

fig = px.line(
    df,
    x="Date",
    y="Value",
    title=f"{indicator_name} ({transform})"
)

fig.update_layout(
    height=700
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================
# Raw Data
# ==================================

st.subheader("資料")

st.dataframe(
    df,
    use_container_width=True
)

# ==================================
# Excel Download
# ==================================

buffer = BytesIO()

with pd.ExcelWriter(
    buffer,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        index=False
    )

buffer.seek(0)

st.download_button(
    "📥 下載 Excel",
    buffer,
    file_name=f"{indicator_name}.xlsx"
)

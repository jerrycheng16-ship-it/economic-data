import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(
    page_title="全球經濟數據儀表板",
    page_icon="🌍",
    layout="wide"
)

# =========================
# World Bank 指標
# =========================

INDICATORS = {
    "GDP (Current US$)": {
        "code": "NY.GDP.MKTP.CD",
        "freq": "A"
    },
    "GDP Growth (%)": {
        "code": "NY.GDP.MKTP.KD.ZG",
        "freq": "A"
    },
    "GDP Per Capita": {
        "code": "NY.GDP.PCAP.CD",
        "freq": "A"
    },
    "Inflation CPI (%)": {
        "code": "FP.CPI.TOTL.ZG",
        "freq": "A"
    },
    "Unemployment (%)": {
        "code": "SL.UEM.TOTL.ZS",
        "freq": "A"
    },
    "Population": {
        "code": "SP.POP.TOTL",
        "freq": "A"
    }
}

COUNTRIES = {
    "United States":"USA",
    "China":"CHN",
    "Taiwan":"TWN",
    "Japan":"JPN",
    "South Korea":"KOR",
    "Germany":"DEU",
    "France":"FRA",
    "United Kingdom":"GBR",
    "India":"IND",
    "Brazil":"BRA",
    "Canada":"CAN",
    "Australia":"AUS"
}

# =========================
# World Bank API
# =========================

@st.cache_data
def get_world_bank_data(country, indicator):

    url = (
        f"https://api.worldbank.org/v2/country/"
        f"{country}/indicator/{indicator}"
        f"?format=json&per_page=5000"
    )

    response = requests.get(url)

    if response.status_code != 200:
        return pd.DataFrame()

    data = response.json()

    if len(data) < 2:
        return pd.DataFrame()

    rows = []

    for item in data[1]:
        if item["value"] is not None:

            rows.append({
                "Date": pd.to_datetime(item["date"]),
                "Value": float(item["value"])
            })

    df = pd.DataFrame(rows)

    if len(df) == 0:
        return df

    df = df.sort_values("Date")

    return df

# =========================
# 轉換
# =========================

def transform_series(df, mode):

    df = df.copy()

    if mode == "Level":
        return df

    if mode == "YoY %":
        df["Value"] = df["Value"].pct_change(1) * 100

    elif mode == "QoQ %":

        df["Value"] = df["Value"].pct_change(1) * 100

    elif mode == "QoQ SAAR %":

        qoq = df["Value"].pct_change(1)

        df["Value"] = (
            ((1 + qoq) ** 4 - 1)
            * 100
        )

    return df

# =========================
# Title
# =========================

st.title("🌍 全球經濟數據儀表板")

# =========================
# SideBar
# =========================

st.sidebar.header("參數設定")

selected_countries = st.sidebar.multiselect(
    "選擇國家",
    list(COUNTRIES.keys()),
    default=["United States"]
)

indicator_name = st.sidebar.selectbox(
    "選擇經濟指標",
    list(INDICATORS.keys())
)

transform_mode = st.sidebar.selectbox(
    "資料格式",
    [
        "Level",
        "YoY %",
        "QoQ %",
        "QoQ SAAR %"
    ]
)

start_year = st.sidebar.slider(
    "開始年份",
    1960,
    2025,
    2000
)

# =========================
# Data
# =========================

combined = pd.DataFrame()

for country_name in selected_countries:

    country_code = COUNTRIES[country_name]

    indicator_code = INDICATORS[indicator_name]["code"]

    df = get_world_bank_data(
        country_code,
        indicator_code
    )

    if len(df) == 0:
        continue

    df = transform_series(
        df,
        transform_mode
    )

    df = df[
        df["Date"].dt.year >= start_year
    ]

    df["Country"] = country_name

    combined = pd.concat(
        [combined, df],
        ignore_index=True
    )

if len(combined) == 0:


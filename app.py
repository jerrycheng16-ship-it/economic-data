import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from fredapi import Fred
from io import BytesIO

# ==========================================
# FRED API KEY
# ==========================================

FRED_API_KEY = "YOUR_FRED_API_KEY"

fred = Fred(api_key=FRED_API_KEY)

# ==========================================
# Page
# ==========================================

st.set_page_config(
    page_title="FRED Economic Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 FRED Economic Dashboard")

# ==========================================
# Search FRED
# ==========================================

@st.cache_data
def search_fred(keyword):

    if keyword == "":
        return pd.DataFrame()

    url = "https://api.stlouisfed.org/fred/series/search"

    params = {
        "search_text": keyword,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "limit": 100
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        data = response.json()

        if "seriess" not in data:
            return pd.DataFrame()

        rows = []

        for item in data["seriess"]:

            rows.append({
                "ID": item["id"],
                "Title": item["title"],
                "Frequency": item["frequency"],
                "Units": item["units"]
            })

        return pd.DataFrame(rows)

    except Exception:
        return pd.DataFrame()

# ==========================================
# Sidebar
# ==========================================

st.sidebar.header("FRED Search")

search_keyword = st.sidebar.text_input(
    "搜尋關鍵字",
    "CPI"
)

search_result = search_fred(search_keyword)

if search_result.empty:

    st.warning("查無資料")

    st.stop()

# ==========================================
# Select Series
# ==========================================

series_options = {}

for _, row in search_result.iterrows():

    label = (
        f"{row['ID']} | "
        f"{row['Title']}"
    )

    series_options[label] = row["ID"]

selected_label = st.sidebar.selectbox(
    "選擇 Series",
    list(series_options.keys())
)

series_id = series_options[selected_label]

# ==========================================
# Frequency
# ==========================================

frequency = st.sidebar.selectbox(
    "資料頻率",
    [
        "原始",
        "月",
        "季",
        "年"
    ]
)

# ==========================================
# Display
# ==========================================

display_mode = st.sidebar.selectbox(
    "顯示方式",
    [
        "Level",
        "YoY %",
        "MoM %",
        "QoQ %",
        "QoQ SAAR %"
    ]
)

# ==========================================
# Start Date
# ==========================================

start_date = st.sidebar.date_input(
    "開始日期",
    pd.Timestamp("2000-01-01")
)

# ==========================================
# Download Series
# ==========================================

try:

    series = fred.get_series(series_id)

except Exception as e:

    st.error(str(e))

    st.stop()

df = pd.DataFrame(series)

df.columns = ["Value"]

df.index.name = "Date"

df = df.reset_index()

df["Date"] = pd.to_datetime(df["Date"])

df = df[
    df["Date"] >= pd.Timestamp(start_date)
]

if df.empty:

    st.warning("無資料")

    st.stop()

# ==========================================
# Resample
# ==========================================

df = df.set_index("Date")

if frequency == "月":

    df = df.resample("ME").last()

elif frequency == "季":

    df = df.resample("QE").last()

elif frequency == "年":

    df = df.resample("YE").last()

df = df.reset_index()

# ==========================================
# Transform
# ==========================================

freq_lag = {
    "原始": 12,
    "月": 12,
    "季": 4,
    "年": 1
}

if display_mode == "YoY %":

    lag = freq_lag[frequency]

    df["Value"] = (
        df["Value"]
        .pct_change(lag)
        * 100
    )

elif display_mode == "MoM %":

    df["Value"] = (
        df["Value"]
        .pct_change(1)
        * 100
    )

elif display_mode == "QoQ %":

    df["Value"] = (
        df["Value"]
        .pct_change(1)
        * 100
    )

elif display_mode == "QoQ SAAR %":

    qoq = (
        df["Value"]
        .pct_change(1)
    )

    df["Value"] = (
        ((1 + qoq) ** 4 - 1)
        * 100
    )

# ==========================================
# Series Info
# ==========================================

selected_info = search_result[
    search_result["ID"] == series_id
].iloc[0]

col1, col2, col3 = st.columns(3)

col1.metric(
    "Series ID",
    series_id
)

col2.metric(
    "Frequency",
    selected_info["Frequency"]
)

col3.metric(
    "Units",
    selected_info["Units"]
)

st.write(
    f"### {selected_info['Title']}"
)

# ==========================================
# Statistics
# ==========================================

clean_data = df["Value"].dropna()

if len(clean_data) > 0:

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "最新值",
        f"{clean_data.iloc[-1]:,.2f}"
    )

    c2.metric(
        "最高值",
        f"{clean_data.max():,.2f}"
    )

    c3.metric(
        "最低值",
        f"{clean_data.min():,.2f}"
    )

# ==========================================
# Chart
# ==========================================

st.subheader("歷史走勢")

fig = px.line(
    df,
    x="Date",
    y="Value",
    title=f"{series_id} ({display_mode})"
)

fig.update_layout(
    height=700,
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==========================================
# Data
# ==========================================

st.subheader("資料")

st.dataframe(
    df,
    use_container_width=True
)

# ==========================================
# Excel Download
# ==========================================

buffer = BytesIO()

with pd.ExcelWriter(
    buffer,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        index=False,
        sheet_name=series_id
    )

buffer.seek(0)

st.download_button(
    "📥 下載 Excel",
    data=buffer,
    file_name=f"{series_id}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

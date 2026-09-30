import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from io import BytesIO

# ==================================================
# 頁面設定
# ==================================================

st.set_page_config(
    page_title="全球經濟數據儀表板",
    page_icon="🌍",
    layout="wide"
)

# ==================================================
# 世界銀行指標
# ==================================================

INDICATORS = {
    "GDP (Current US$)": "NY.GDP.MKTP.CD",
    "GDP Growth (%)": "NY.GDP.MKTP.KD.ZG",
    "GDP Per Capita": "NY.GDP.PCAP.CD",
    "Inflation CPI (%)": "FP.CPI.TOTL.ZG",
    "Unemployment (%)": "SL.UEM.TOTL.ZS",
    "Population": "SP.POP.TOTL"
}

# ==================================================
# 國家
# ==================================================

COUNTRIES = {
    "United States": "USA",
    "China": "CHN",
    "Japan": "JPN",
    "South Korea": "KOR",
    "India": "IND",
    "Germany": "DEU",
    "France": "FRA",
    "United Kingdom": "GBR",
    "Canada": "CAN",
    "Australia": "AUS",
    "Brazil": "BRA"
}

# ==================================================
# World Bank API
# ==================================================

@st.cache_data
def get_world_bank_data(country_code, indicator_code):

    url = (
        f"https://api.worldbank.org/v2/country/"
        f"{country_code}/indicator/"
        f"{indicator_code}"
        f"?format=json&per_page=5000"
    )

    try:

        response = requests.get(
            url,
            timeout=30
        )

        if response.status_code != 200:
            return pd.DataFrame()

        data = response.json()

        if not isinstance(data, list):
            return pd.DataFrame()

        if len(data) < 2:
            return pd.DataFrame()

        rows = []

        for item in data[1\]:

            value = item.get("value")

            if value is not None:

                rows.append({
                    "Date": pd.to_datetime(item["date"]),
                    "Value": float(value)
                })

        df = pd.DataFrame(rows)

        if df.empty:
            return pd.DataFrame()

        df = df.sort_values("Date")

        return df

    except Exception as e:

        st.error(f"API Error: {str(e)}")
        return pd.DataFrame()

# ==================================================
# 資料轉換
# ==================================================

def transform_data(df, mode):

    df = df.copy()

    if mode == "Level":
        return df

    if mode == "YoY %":

        df["Value"] = (
            df["Value"]
            .pct_change(1)
            * 100
        )

    return df

# ==================================================
# 標題
# ==================================================

st.title("🌍 全球經濟數據儀表板")

# ==================================================
# Sidebar
# ==================================================

st.sidebar.header("參數設定")

selected_countries = st.sidebar.multiselect(
    "選擇國家",
    list(COUNTRIES.keys()),
    default=["United States"]
)

if len(selected_countries) == 0:
    st.warning("請至少選擇一個國家")
    st.stop()

selected_indicator = st.sidebar.selectbox(
    "選擇經濟指標",
    list(INDICATORS.keys())
)

display_mode = st.sidebar.selectbox(
    "顯示方式",
    [
        "Level",
        "YoY %"
    ]
)

start_year = st.sidebar.slider(
    "開始年份",
    1960,
    2025,
    2000
)

# ==================================================
# 下載資料
# ==================================================

all_data = pd.DataFrame()

for country in selected_countries:

    df = get_world_bank_data(
        COUNTRIES[country],
        INDICATORS[selected_indicator]
    )

    if df.empty:
        continue

    df = transform_data(
        df,
        display_mode
    )

    df = df[
        df["Date"].dt.year >= start_year
    ]

    df["Country"] = country

    all_data = pd.concat(
        [all_data, df],
        ignore_index=True
    )

# ==================================================
# 無資料
# ==================================================

if all_data.empty:
    st.error("查無資料")
    st.stop()

# ==================================================
# 最新數據
# ==================================================

st.subheader("最新數據")

metric_cols = st.columns(
    len(selected_countries)
)

for i, country in enumerate(selected_countries):

    temp = all_data[
        all_data["Country"] == country
    ]

    if temp.empty:
        continue

    latest = temp["Value"].iloc[-1]

    metric_cols[i].metric(
        country,
        f"{latest:,.2f}"
    )

# ==================================================
# 圖表
# ==================================================

st.subheader(
    f"{selected_indicator} ({display_mode})"
)

fig = px.line(
    all_data,
    x="Date",
    y="Value",
    color="Country",
    markers=True
)

fig.update_layout(
    height=700,
    hovermode="x unified"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ==================================================
# 統計資訊
# ==================================================

st.subheader("統計資訊")

stats = []

for country in selected_countries:

    temp = all_data[
        all_data["Country"] == country
    ]

    if temp.empty:
        continue

    stats.append({
        "Country": country,
        "Latest": round(temp["Value"].iloc[-1], 2),
        "Max": round(temp["Value"].max(), 2),
        "Min": round(temp["Value"].min(), 2),
        "Average": round(temp["Value"].mean(), 2)
    })

stats_df = pd.DataFrame(stats)

st.dataframe(
    stats_df,
    use_container_width=True
)

# ==================================================
# 原始資料
# ==================================================

st.subheader("原始資料")

display_df = all_data.copy()

display_df["Date"] = (
    display_df["Date"]
    .dt.year
)

st.dataframe(
    display_df,
    use_container_width=True
)

# ==================================================
# Excel下載
# ==================================================

excel_buffer = BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    display_df.to_excel(
        writer,
        index=False,
        sheet_name="Economic Data"
    )

excel_buffer.seek(0)

st.download_button(
    label="📥 下載 Excel",
    data=excel_buffer,
    file_name="Global_Economic_Data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

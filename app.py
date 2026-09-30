import streamlit as st
import pandas as pd
import requests
from fredapi import Fred
import plotly.express as px
from datetime import datetime

# =====================
# FRED
# =====================

FRED_API_KEY = "YOUR_FRED_API_KEY"

fred = Fred(api_key=FRED_API_KEY)

st.set_page_config(
    page_title="全球總經儀表板",
    layout="wide"
)

st.title("🌍 全球經濟數據儀表板")

# =====================
# 經濟指標
# =====================

fred_series = {
    "美國GDP": "GDP",
    "美國CPI": "CPIAUCSL",
    "美國核心CPI": "CPILFESL",
    "美國失業率": "UNRATE",
    "美國10年公債殖利率": "GS10",
    "美國聯邦基金利率": "FEDFUNDS",
    "美國M2": "M2SL",
    "美國PMI": "NAPM",
    "美元指數": "DTWEXBGS"
}

col1, col2 = st.columns(2)

with col1:
    indicator = st.selectbox(
        "選擇經濟指標",
        list(fred_series.keys())
    )

with col2:
    start_date = st.date_input(
        "開始日期",
        datetime(2010,1,1)
    )

# =====================
# 下載資料
# =====================

series_id = fred_series[indicator]

data = fred.get_series(
    series_id,
    observation_start=start_date
)

df = pd.DataFrame(data)

df.columns = [indicator]
df.index.name = "Date"
df = df.reset_index()

# =====================
# 圖表
# =====================

fig = px.line(
    df,
    x="Date",
    y=indicator,
    title=indicator
)

fig.update_layout(
    height=600
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================
# 統計
# =====================

latest = df[indicator].iloc[-1]
max_value = df[indicator].max()
min_value = df[indicator].min()

c1,c2,c3 = st.columns(3)

c1.metric(
    "最新值",
    f"{latest:,.2f}"
)

c2.metric(
    "歷史最高",
    f"{max_value:,.2f}"
)

c3.metric(
    "歷史最低",
    f"{min_value:,.2f}"
)

# =====================
# 資料表
# =====================

st.subheader("資料")

st.dataframe(df)

# =====================
# 匯出 Excel
# =====================

excel_file = "economic_data.xlsx"

df.to_excel(
    excel_file,
    index=False
)

with open(excel_file, "rb") as f:
    st.download_button(
        "下載Excel",
        f,
        file_name=excel_file
    )

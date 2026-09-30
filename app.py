import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from fredapi import Fred
from io import BytesIO

# =====================================================
# FRED API KEY
# =====================================================

FRED_API_KEY = st.secrets["2132d80f475773a92941db7ac291147a"]

fred = Fred(api_key=FRED_API_KEY)

# =====================================================
# PAGE
# =====================================================

st.set_page_config(
    page_title="FRED Economic Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("📈 FRED Economic Dashboard")

# =====================================================
# SEARCH FUNCTION
# =====================================================

@st.cache_data(show_spinner=False)
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

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    data = response.json()

    if "seriess" not in data:
        return pd.DataFrame()

    rows = []

    for item in data["seriess"\]:

        rows.append(
            {
                "ID": item["id"],
                "Title": item["title"],
                "Frequency": item["frequency"],
                "Units": item["units"],
                "Start": item["observation_start"],
                "End": item["observation_end"]
            }
        )

    return pd.DataFrame(rows)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("FRED Search")

search_keyword = st.sidebar.text_input(
    "搜尋關鍵字",
    value="CPI"
)

search_df = search_fred(search_keyword)

if search_df.empty:
    st.warning("查無符合的 Series")
    st.stop()

# =====================================================
# SERIES SELECT
# =====================================================

series_options = {}

for _, row in search_df.iterrows():

    label = (
        f"{row['ID']} | "
        f"{row['Title']}"
    )

    series_options[label] = row["ID"]

selected_labels = st.sidebar.multiselect(
    "選擇 Series (可複選)",
    options=list(series_options.keys()),
    default=list(series_options.keys())[:3]
)

if len(selected_labels) == 0:
    st.warning("請至少選擇一個 Series")
    st.stop()

selected_series = [
    series_options[x]
    for x in selected_labels
]

# =====================================================
# SETTINGS
# =====================================================

frequency = st.sidebar.selectbox(
    "資料頻率",
    [
        "原始",
        "月",
        "季",
        "年"
    ]
)

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

normalize = st.sidebar.checkbox(
    "Normalize (基期=100)",
    value=False
)

start_date = st.sidebar.date_input(
    "開始日期",
    pd.Timestamp("2000-01-01")
)

# =====================================================
# DOWNLOAD DATA
# =====================================================

combined_df = pd.DataFrame()

for sid in selected_series:

    try:

        data = fred.get_series(sid)

        temp = pd.DataFrame(data)

        temp.columns = [sid]

        temp.index.name = "Date"

        if combined_df.empty:

            combined_df = temp

        else:

            combined_df = combined_df.join(
                temp,
                how="outer"
            )

    except Exception as e:

        st.warning(f"{sid} 下載失敗")

# =====================================================
# CHECK DATA
# =====================================================

if combined_df.empty:
    st.error("無法下載任何資料")
    st.stop()

# =====================================================
# DATE PROCESS
# =====================================================

combined_df = combined_df.reset_index()

combined_df["Date"] = pd.to_datetime(
    combined_df["Date"]
)

combined_df = combined_df[
    combined_df["Date"] >= pd.Timestamp(start_date)
]

combined_df = combined_df.sort_values(
    "Date"
)

# =====================================================
# RESAMPLE
# =====================================================

combined_df = combined_df.set_index(
    "Date"
)

if frequency == "月":

    combined_df = (
        combined_df
        .resample("ME")
        .last()
    )

elif frequency == "季":

    combined_df = (
        combined_df
        .resample("QE")
        .last()
    )

elif frequency == "年":

    combined_df = (
        combined_df
        .resample("YE")
        .last()
    )

combined_df = combined_df.reset_index()

# =====================================================
# TRANSFORM
# =====================================================

value_cols = [
    c for c in combined_df.columns
    if c != "Date"
]

lag_map = {
    "原始": 12,
    "月": 12,
    "季": 4,
    "年": 1
}

for col in value_cols:

    if display_mode == "YoY %":

        combined_df[col] = (
            combined_df[col]
            .pct_change(
                lag_map[frequency]
            )
            * 100
        )

    elif display_mode == "MoM %":

        combined_df[col] = (
            combined_df[col]
            .pct_change(1)
            * 100
        )

    elif display_mode == "QoQ %":

        combined_df[col] = (
            combined_df[col]
            .pct_change(1)
            * 100
        )

    elif display_mode == "QoQ SAAR %":

        qoq = (
            combined_df[col]
            .pct_change(1)
        )

        combined_df[col] = (
            ((1 + qoq) ** 4 - 1)
            * 100
        )

# =====================================================
# NORMALIZE
# =====================================================

if normalize:

    for col in value_cols:

        clean = combined_df[col].dropna()

        if len(clean) > 0:

            base = clean.iloc[0]

            if base != 0:

                combined_df[col] = (
                    combined_df[col]
                    / base
                    * 100
                )

# =====================================================
# SERIES INFO
# =====================================================

st.subheader("Series 資訊")

info_df = search_df[
    search_df["ID"].isin(selected_series)
]

st.dataframe(
    info_df,
    use_container_width=True
)

# =====================================================
# MELT FOR PLOTLY
# =====================================================

plot_df = combined_df.melt(
    id_vars="Date",
    var_name="Series",
    value_name="Value"
)

# =====================================================
# CHART
# =====================================================

st.subheader("歷史走勢")

fig = px.line(
    plot_df,
    x="Date",
    y="Value",
    color="Series"
)

fig.update_layout(
    height=800,
    hovermode="x unified",
    legend_title="Series"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# LATEST VALUES
# =====================================================

st.subheader("最新數值")

latest_rows = []

for col in value_cols:

    s = combined_df[col].dropna()

    if len(s) > 0:

        latest_rows.append(
            {
                "Series": col,
                "Latest": round(
                    s.iloc[-1],
                    4
                ),
                "Max": round(
                    s.max(),
                    4
                ),
                "Min": round(
                    s.min(),
                    4
                )
            }
        )

latest_df = pd.DataFrame(
    latest_rows
)

st.dataframe(
    latest_df,
    use_container_width=True
)

# =====================================================
# RAW DATA
# =====================================================

st.subheader("原始資料")

st.dataframe(
    combined_df,
    use_container_width=True
)

# =====================================================
# DOWNLOAD EXCEL
# =====================================================

buffer = BytesIO()

with pd.ExcelWriter(
    buffer,
    engine="openpyxl"
) as writer:

    combined_df.to_excel(
        writer,
        sheet_name="Data",
        index=False
    )

    latest_df.to_excel(
        writer,
        sheet_name="Statistics",
        index=False
    )

buffer.seek(0)

st.download_button(
    label="📥 Download Excel",
    data=buffer,
    file_name="fred_multi_series.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

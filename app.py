import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

st.set_page_config(
    page_title="Global Asset Dashboard",
    layout="wide"
)

st.title("🌎 Global Asset Dashboard")

# =====================================================
# ETF Universe
# =====================================================

EQUITY_ETFS = {

    "美國-SPY":"SPY",
    "美國-IVV":"IVV",
    "美國-VTI":"VTI",
    "美國科技-QQQ":"QQQ",
    "美國成長-VUG":"VUG",
    "美國價值-VTV":"VTV",
    "美國小型股-IWM":"IWM",

    "加拿大-EWC":"EWC",
    "墨西哥-EWW":"EWW",

    "台灣-EWT":"EWT",
    "日本-EWJ":"EWJ",
    "中國-MCHI":"MCHI",
    "中國A股-CNYA":"CNYA",
    "香港-EWH":"EWH",
    "韓國-EWY":"EWY",
    "印度-INDA":"INDA",
    "印尼-EIDO":"EIDO",
    "馬來西亞-EWM":"EWM",
    "新加坡-EWS":"EWS",
    "泰國-THD":"THD",
    "越南-VNM":"VNM",
    "菲律賓-EPHE":"EPHE",

    "英國-EWU":"EWU",
    "德國-EWG":"EWG",
    "法國-EWQ":"EWQ",
    "義大利-EWI":"EWI",
    "西班牙-EWP":"EWP",
    "荷蘭-EWN":"EWN",
    "瑞士-EWL":"EWL",
    "瑞典-EWD":"EWD",
    "挪威-ENOR":"ENOR",
    "波蘭-EPOL":"EPOL",
    "希臘-GREK":"GREK",
    "土耳其-TUR":"TUR",

    "巴西-EWZ":"EWZ",
    "智利-ECH":"ECH",
    "秘魯-EPU":"EPU",

    "沙烏地-KSA":"KSA",
    "阿聯-UAE":"UAE",
    "卡達-QAT":"QAT",

    "南非-EZA":"EZA",
    "埃及-EGPT":"EGPT",

    "新興市場-EEM":"EEM",
    "新興市場-VWO":"VWO",
    "歐洲-VGK":"VGK",
    "歐元區-EZU":"EZU",
    "亞太除日本-AAXJ":"AAXJ",
    "MSCI世界-URTH":"URTH",
    "全球股票-ACWI":"ACWI"
}

TREASURY_ETFS = {
    "超短公債-BIL":"BIL",
    "短期公債-SHY":"SHY",
    "中期公債-IEF":"IEF",
    "長期公債-TLT":"TLT",
    "超長公債-VGLT":"VGLT"
}

IG_ETFS = {
    "投資級債-LQD":"LQD",
    "短投資級債-VCSH":"VCSH",
    "中投資級債-VCIT":"VCIT"
}

HY_ETFS = {
    "高收益債-HYG":"HYG",
    "非投資級債-JNK":"JNK"
}

EMD_ETFS = {
    "新興美元債-EMB":"EMB",
    "新興美元債-VWOB":"VWOB"
}

LOCAL_ETFS = {
    "新興本幣債-LEMB":"LEMB"
}

COMMODITY_ETFS = {
    "黃金-GLD":"GLD",
    "黃金-IAU":"IAU",
    "白銀-SLV":"SLV",
    "原油-USO":"USO",
    "天然氣-UNG":"UNG",
    "工業金屬-DBB":"DBB",
    "農產品-DBA":"DBA",
    "商品綜合-DBC":"DBC"
}

REIT_ETFS = {
    "美國REIT-VNQ":"VNQ",
    "全球REIT-REET":"REET",
    "國際REIT-VNQI":"VNQI"
}

SAFE_ETFS = {
    "美元-UUP":"UUP",
    "日圓-FXY":"FXY",
    "瑞郎-FXF":"FXF"
}

ALL_ETFS = {
    **EQUITY_ETFS,
    **TREASURY_ETFS,
    **IG_ETFS,
    **HY_ETFS,
    **EMD_ETFS,
    **LOCAL_ETFS,
    **COMMODITY_ETFS,
    **REIT_ETFS,
    **SAFE_ETFS
}

# =====================================================
# Sidebar
# =====================================================

st.sidebar.header("設定")

search_text = st.sidebar.text_input(
    "搜尋 ETF / 國家",
    ""
)

available_assets = list(ALL_ETFS.keys())

if search_text:
    available_assets = [
        x for x in available_assets
        if search_text.lower() in x.lower()
    ]

selected_assets = st.sidebar.multiselect(
    "選擇ETF",
    available_assets,
    default=[
        "美國-SPY",
        "台灣-EWT",
        "長期公債-TLT",
        "黃金-GLD"
    ]
)

period = st.sidebar.selectbox(
    "期間",
    [
        "MTD",
        "YTD",
        "1M",
        "3M",
        "6M",
        "1Y",
        "2Y",
        "3Y",
        "5Y"
    ],
    index=4
)

# =====================================================
# Date
# =====================================================

today = pd.Timestamp.today()

if period == "MTD":
    start = today.replace(day=1)

elif period == "YTD":
    start = pd.Timestamp(today.year, 1, 1)

elif period == "1M":
    start = today - pd.DateOffset(months=1)

elif period == "3M":
    start = today - pd.DateOffset(months=3)

elif period == "6M":
    start = today - pd.DateOffset(months=6)

elif period == "1Y":
    start = today - pd.DateOffset(years=1)

elif period == "2Y":
    start = today - pd.DateOffset(years=2)

elif period == "3Y":
    start = today - pd.DateOffset(years=3)

else:
    start = today - pd.DateOffset(years=5)

# =====================================================
# Download
# =====================================================

if st.button("開始分析"):

    if len(selected_assets) == 0:
        st.warning("請選擇ETF")
        st.stop()

    prices = pd.DataFrame()

    with st.spinner("下載資料中..."):

        for asset in selected_assets:

            ticker = ALL_ETFS[asset]

            try:

                data = yf.download(
                    ticker,
                    start=start,
                    end=today,
                    auto_adjust=True,
                    progress=False
                )

                if not data.empty:
                    prices[asset] = data["Close"]

            except:
                pass

    if prices.empty:
        st.error("無法取得資料")
        st.stop()

    prices = prices.ffill()

    # ==========================
    # Return Ranking
    # ==========================

    returns = (
        prices.iloc[-1]
        / prices.iloc[0]
        - 1
    ) * 100

    ranking = pd.DataFrame({
        "Return (%)": returns
    })

    ranking = ranking.sort_values(
        "Return (%)",
        ascending=False
    )

    st.subheader("📈 報酬率排名")
    st.dataframe(ranking)

    fig_rank = px.bar(
        ranking,
        x="Return (%)",
        y=ranking.index,
        orientation="h"
    )

    st.plotly_chart(
        fig_rank,
        use_container_width=True
    )

    # ==========================
    # Heatmap
    # ==========================

    st.subheader("🔥 Heatmap")

    fig_heat = px.imshow(
        ranking.T,
        text_auto=".1f",
        color_continuous_scale="RdYlGn"
    )

    st.plotly_chart(
        fig_heat,
        use_container_width=True
    )

    # ==========================
    # Performance
    # ==========================

    st.subheader("📊 累積績效")

    cumulative = (
        prices / prices.iloc[0]
    ) * 100

    fig_line = px.line(
        cumulative,
        x=cumulative.index,
        y=cumulative.columns
    )

    st.plotly_chart(
        fig_line,
        use_container_width=True
    )

    # ==========================
    # Excel
    # ==========================

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="xlsxwriter"
    ) as writer:

        ranking.to_excel(
            writer,
            sheet_name="Ranking"
        )

        prices.to_excel(
            writer,
            sheet_name="Price"
        )

        cumulative.to_excel(
            writer,
            sheet_name="Performance"
        )

    st.download_button(
        "📥下載Excel",
        output.getvalue(),
        file_name=f"asset_dashboard_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

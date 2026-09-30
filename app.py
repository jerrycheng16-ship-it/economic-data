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
    "United States":"USA",
    "China":"CHN",
    "Taiwan":"TWN",
    "Japan":"JPN",
    "South Korea":"KOR",
    "India":"IND",
    "Germany":"DEU",
    "France":"FRA",
    "United Kingdom":"GBR",
    "Canada":"CAN",
    "Australia":"AUS",
    "Brazil":"BRA"
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

 

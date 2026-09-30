import streamlit as st

st.write("Step 1")

import pandas as pd
st.write("Step 2")

import requests
st.write("Step 3")

st.title("全球經濟數據儀表板")

st.write("Step 4")

response = requests.get(
    "https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json"
)

st.write("Step 5")

st.write(response.status_code)

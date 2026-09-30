import streamlit as st
import pandas as pd
import requests

st.title("全球經濟數據儀表板")

url = (
    "https://api.worldbank.org/v2/"
    "country/USA/indicator/"
    "NY.GDP.MKTP.CD?format=json"
)

response = requests.get(url)

st.write("API Status")
st.write(response.status_code)

data = response.json()

st.write("Data Type")
st.write(type(data))

st.write("Data Length")
st.write(len(data))

st.write("First Element")
st.write(data[0])

st.write("Second Element Sample")
st.write(data[1][0])

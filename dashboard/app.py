import streamlit as st

st.set_page_config(page_title="Wage-Climate Vulnerability", layout="wide")

pg = st.navigation([
    st.Page("pages/overview.py",  title="Overview"),
    st.Page("pages/trends.py",    title="Trends"),
    st.Page("pages/explorer.py",  title="Country Explorer"),
])
pg.run()

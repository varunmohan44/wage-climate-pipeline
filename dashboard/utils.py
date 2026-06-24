import psycopg2
import pandas as pd
import streamlit as st

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "pipeline",
    "user": "pipeline",
    "password": "pipeline",
}

@st.cache_data(ttl=300)
def run_query(sql, params=None):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()

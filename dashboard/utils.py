import os

import psycopg2
import pandas as pd
import streamlit as st

DB_CONFIG = {
    "host":     os.getenv("PIPELINE_DB_HOST", "localhost"),
    "port":     int(os.getenv("PIPELINE_DB_PORT", "5433")),
    "database": os.getenv("PIPELINE_DB_NAME", "pipeline"),
    "user":     os.getenv("PIPELINE_DB_USER", "pipeline"),
    "password": os.getenv("PIPELINE_DB_PASSWORD", "pipeline"),
}

@st.cache_data(ttl=300)
def run_query(sql, params=None):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()

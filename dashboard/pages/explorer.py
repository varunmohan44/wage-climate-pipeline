import streamlit as st
import plotly.express as px
import pandas as pd
from utils import run_query

st.title("Component Explorer")
st.caption("What drives vulnerability? Break down the six index components for any country.")

countries = run_query("""
    select distinct country_name
    from dev_facts.fct_wage_climate_vulnerability
    where components_used >= 4
    order by country_name
""")

default_idx = list(countries["country_name"]).index("Nigeria") if "Nigeria" in countries["country_name"].values else 0
country = st.selectbox("Select a country", countries["country_name"], index=default_idx)

timeseries = run_query(
    """
    select
        year,
        round(vulnerability_index::numeric, 3)      as vulnerability_index,
        round(wage_depression_score::numeric, 3)    as wage_depression,
        round(informality_score::numeric, 3)        as informality,
        round(gender_gap_score::numeric, 3)         as gender_gap,
        round(poverty_score::numeric, 3)            as poverty,
        round(climate_exposure_score::numeric, 3)   as climate_exposure,
        round(low_readiness_score::numeric, 3)      as low_readiness,
        components_used
    from dev_facts.fct_wage_climate_vulnerability
    where country_name = %s
      and components_used >= 2
    order by year
    """,
    params=(country,),
)

fig1 = px.line(
    timeseries, x="year", y="vulnerability_index",
    title=f"Composite Vulnerability Index — {country}",
    labels={"vulnerability_index": "Vulnerability Index (0–1)", "year": "Year"},
    range_y=[0, 1],
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()
st.subheader(f"Component Breakdown (Latest Year) — {country}")

if not timeseries.empty:
    latest = timeseries.loc[timeseries["year"].idxmax()]
    comp_df = pd.DataFrame({
        "component": ["Wage Depression", "Informality", "Gender Gap", "Poverty", "Climate Exposure", "Low Readiness"],
        "score": [
            latest["wage_depression"], latest["informality"], latest["gender_gap"],
            latest["poverty"], latest["climate_exposure"], latest["low_readiness"],
        ],
    })
    fig2 = px.bar(
        comp_df, x="component", y="score",
        title=f"Component Scores (Most Recent Year) — {country}",
        labels={"score": "Normalized Score (0–1)", "component": "Component"},
        range_y=[0, 1],
        color_discrete_sequence=["#3b82f6"],
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Informality vs. Vulnerability (Latest Year, All Countries)")

scatter = run_query("""
    select
        country_name,
        region,
        round(informality_rate_total::numeric, 1)   as informality_rate_pct,
        round(vulnerability_index::numeric, 3)       as vulnerability_index,
        vulnerability_tier
    from dev_facts.fct_wage_climate_vulnerability
    where year = (select max(year) from dev_facts.fct_wage_climate_vulnerability)
      and components_used >= 4
      and informality_rate_total is not null
    order by vulnerability_index desc
""")

fig3 = px.scatter(
    scatter, x="informality_rate_pct", y="vulnerability_index", color="vulnerability_tier",
    hover_name="country_name",
    title="Informality Rate vs. Vulnerability Index",
    labels={"informality_rate_pct": "Informal Employment Rate (%)", "vulnerability_index": "Vulnerability Index", "vulnerability_tier": "Tier"},
    color_discrete_map={"High": "#ef4444", "Medium": "#eab308", "Low": "#22c55e"},
)
st.plotly_chart(fig3, use_container_width=True)

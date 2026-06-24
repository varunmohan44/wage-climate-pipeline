import streamlit as st
import plotly.express as px
from utils import run_query, VULN_TABLE

st.title("Vulnerability Trends Over Time")
st.caption("How has wage-climate vulnerability shifted across countries and regions since 2000?")

st.subheader("Global Average Trend")

global_trend = run_query(f"""
    select
        year,
        round(avg(vulnerability_index)::numeric, 3)                                                    as avg_vulnerability,
        round(percentile_cont(0.9) within group (order by vulnerability_index)::numeric, 3)            as p90_vulnerability,
        round(percentile_cont(0.1) within group (order by vulnerability_index)::numeric, 3)            as p10_vulnerability,
        count(distinct country_code)                                                                    as countries
    from {VULN_TABLE}
    where components_used >= 4
      and year >= 2000
    group by year
    order by year
""")

fig1 = px.line(
    global_trend, x="year",
    y=["p90_vulnerability", "avg_vulnerability", "p10_vulnerability"],
    title="Global Vulnerability Distribution Over Time (P10 / Average / P90)",
    labels={"value": "Vulnerability Index", "year": "Year", "variable": "Metric"},
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()
st.subheader("Top 10 Most Vulnerable Countries Over Time")

top_countries = run_query(f"""
    with top_10 as (
        select country_name
        from {VULN_TABLE}
        where components_used >= 4
        group by country_name
        having count(*) >= 10
        order by avg(vulnerability_index) desc
        limit 10
    )
    select f.year, f.country_name,
        round(f.vulnerability_index::numeric, 3) as vulnerability_index
    from {VULN_TABLE} f
    join top_10 t on f.country_name = t.country_name
    where f.components_used >= 4
      and f.year >= 2000
    order by f.year, f.country_name
""")

fig2 = px.line(
    top_countries, x="year", y="vulnerability_index", color="country_name",
    title="Vulnerability Index — Top 10 Most Vulnerable Countries",
    labels={"vulnerability_index": "Vulnerability Index (0–1)", "year": "Year", "country_name": "Country"},
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader("Most Consistently Vulnerable Countries")

persistent = run_query(f"""
    select
        country_name,
        round(avg(vulnerability_index)::numeric, 3)  as avg_vulnerability,
        round(min(vulnerability_index)::numeric, 3)  as best_year,
        round(max(vulnerability_index)::numeric, 3)  as worst_year,
        count(*)                                      as years_with_data
    from {VULN_TABLE}
    where components_used >= 4
    group by country_name
    having count(*) >= 10
    order by avg_vulnerability desc
    limit 15
""")

st.dataframe(persistent, use_container_width=True, hide_index=True)

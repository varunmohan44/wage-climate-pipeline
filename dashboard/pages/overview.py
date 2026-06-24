import streamlit as st
import plotly.express as px
from utils import run_query

st.title("Wage-Climate Vulnerability Index")
st.caption("Which developing countries are caught in cycles where climate stress worsens wages and deteriorates labor markets?")

latest_year_df = run_query("""
    select max(year) as year
    from dev_facts.fct_wage_climate_vulnerability
    where components_used >= 4
""")
latest_year = int(latest_year_df["year"][0])

stats = run_query("""
    select
        count(distinct country_code)                                    as countries_tracked,
        max(year)                                                       as last_year,
        count(*) filter (where vulnerability_tier = 'High')            as high_count,
        count(*) filter (where vulnerability_tier = 'Low')             as low_count
    from dev_facts.fct_wage_climate_vulnerability
    where components_used >= 4
      and year = %(year)s
""", params={"year": latest_year})

col1, col2, col3, col4 = st.columns(4)
col1.metric("Countries Tracked", int(stats["countries_tracked"][0]))
col2.metric("Latest Year", latest_year)
col3.metric("High Vulnerability", int(stats["high_count"][0]))
col4.metric("Low Vulnerability", int(stats["low_count"][0]))

st.divider()
st.subheader("Most Vulnerable Countries")

rankings = run_query("""
    select
        row_number() over (order by vulnerability_index desc)   as rank,
        country_name,
        round(vulnerability_index::numeric, 3)                  as vulnerability_index,
        vulnerability_tier,
        components_used,
        round(gdp_per_capita_usd::numeric, 0)                   as gdp_per_capita,
        round(poverty_headcount_ratio::numeric, 1)              as poverty_pct,
        round(gain_vulnerability_score::numeric, 3)             as climate_vulnerability
    from dev_facts.fct_wage_climate_vulnerability
    where year = %(year)s
      and components_used >= 4
    order by vulnerability_index desc
    limit 20
""", params={"year": latest_year})

st.dataframe(rankings, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Distribution by Vulnerability Tier")

tier_data = run_query("""
    select vulnerability_tier, count(*) as country_count
    from dev_facts.fct_wage_climate_vulnerability
    where year = %(year)s
      and components_used >= 4
    group by vulnerability_tier
    order by vulnerability_tier
""", params={"year": latest_year})

fig = px.bar(
    tier_data,
    x="vulnerability_tier", y="country_count", color="vulnerability_tier",
    title="Countries by Vulnerability Tier (Latest Year)",
    labels={"country_count": "Number of Countries", "vulnerability_tier": "Tier"},
    color_discrete_map={"High": "#ef4444", "Medium": "#eab308", "Low": "#22c55e"},
)
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

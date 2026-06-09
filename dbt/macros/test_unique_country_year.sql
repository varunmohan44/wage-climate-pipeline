{% macro test_unique_country_year(model) -%}
/*
  Generic test: fails when a country/year combination appears more than once.
  Expects `model` to be a relation or a subquery.
*/
select
  country_code,
  year,
  count(*) as duplicate_count
from {{ model }}
group by country_code, year
having count(*) > 1

{%- endmacro %}

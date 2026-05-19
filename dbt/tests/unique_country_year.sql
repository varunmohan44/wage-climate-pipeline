-- Fails when a country/year combination appears more than once.
-- Model-level generic test for stg_economic.

select
  country_code,
  year,
  count(*) as duplicate_count
from {{ ref('stg_economic') }}
group by country_code, year
having count(*) > 1

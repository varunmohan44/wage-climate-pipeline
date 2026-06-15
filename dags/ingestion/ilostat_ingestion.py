import os
import requests
import psycopg2

# config
INDICATORS = [
    ("EAR_EHRA_SEX_ECO_CUR_NB", "Average nominal earnings by sex and economic activity"),
    ("EAR_GGAP_OCU_RT", "Gender wage gap by occupation"),
    ("EMP_2IFL_SEX_RT", "Informal employment rate by sex"),
    ("EMP_2EMP_SEX_STE_NB", "Employment by sex and status in employment"),
]

BASE_URL = "https://sdmx.ilo.org/rest/data"
KEEP_SEX = {"SEX_T", "SEX_M", "SEX_F"}
KEEP_ACTIVITY = {"ECO_ISIC4_TOTAL", "_T", "TOTAL"}

DB_CONFIG = {
    "host": os.getenv("PIPELINE_DB_HOST", "pipeline-db"),
    "port": int(os.getenv("PIPELINE_DB_PORT", "5432")),
    "dbname": os.getenv("PIPELINE_DB_NAME", "pipeline"),
    "user": os.getenv("PIPELINE_DB_USER", "pipeline"),
    "password": os.getenv("PIPELINE_DB_PASSWORD", "pipeline"),
}


def fetch_indicator(indicator_code: str) -> list[dict]:
    url = f"{BASE_URL}/ILO,DF_{indicator_code},1.0/all"
    params = {
        "format": "jsondata",
        "startPeriod": "2000",
        "endPeriod": "2024",
        "dimensionAtObservation": "AllDimensions",
    }

    response = requests.get(url, params=params, timeout=60)
    if response.status_code == 404:
        print(f"  Dataflow not found for {indicator_code}, skipping.")
        return []
    response.raise_for_status()

    payload = response.json()
    data = payload.get("data", payload)
    structure = data.get("structures") or data.get("structure") or []
    if isinstance(structure, list):
        structure = structure[0] if structure else {}
    series_dims = structure.get("dimensions", {}).get("series", [])
    obs_dims = structure.get("dimensions", {}).get("observation", [])
    datasets = data.get("dataSets", [])

    if not datasets:
        print(f"  No datasets returned for {indicator_code}.")
        return []

    dataset = datasets[0]
    if not dataset.get("series") and not dataset.get("observations"):
        print(f"  No data returned for {indicator_code}.")
        return []

    # map dimensions
    records = []
    if dataset.get("series"):
        dim_lookup = [{i: v["id"] for i, v in enumerate(d["values"])} for d in series_dims]
        time_lookup = {i: v["id"] for i, v in enumerate(obs_dims[0]["values"])} if obs_dims else {}

        dim_ids = [d["id"] for d in series_dims]
        ref_idx = next((i for i, d in enumerate(dim_ids) if d in ("REF_AREA", "COUNTRY")), None)
        sex_idx = next((i for i, d in enumerate(dim_ids) if d == "SEX"), None)
        eco_idx = next((i for i, d in enumerate(dim_ids) if d in ("ECONOMIC_ACTIVITY", "ECO")), None)
        ste_idx = next((i for i, d in enumerate(dim_ids) if d == "STE"), None)

        country_lookup = {v["id"]: v["name"] for v in series_dims[ref_idx]["values"]} if ref_idx is not None else {}
        meas_dim = next((d for d in series_dims if d["id"] == "MEASURE"), None)
        indicator_name = meas_dim["values"][0]["name"] if meas_dim and meas_dim.get("values") else indicator_code

        for series_key, series_body in dataset["series"].items():
            indices = [int(i) for i in series_key.split(":")]
            country_code = dim_lookup[ref_idx].get(indices[ref_idx], "") if ref_idx is not None else ""
            sex = dim_lookup[sex_idx].get(indices[sex_idx], "SEX_T") if sex_idx is not None else "SEX_T"
            activity = dim_lookup[eco_idx].get(indices[eco_idx], "_T") if eco_idx is not None else "_T"
            ste = dim_lookup[ste_idx].get(indices[ste_idx], "_T") if ste_idx is not None else "_T"

            if sex not in KEEP_SEX or activity not in KEEP_ACTIVITY:
                continue

            for obs_key, obs_value in series_body.get("observations", {}).items():
                period = time_lookup.get(int(obs_key.split(":")[0]), "")
                if len(period) == 4 and period.isdigit():
                    records.append({
                        "country_code": country_code,
                        "country_name": country_lookup.get(country_code, country_code),
                        "indicator_code": indicator_code,
                        "indicator_name": indicator_name,
                        "sex": sex,
                        "economic_activity": activity,
                        "status_in_employment": ste,
                        "year": int(period),
                        "value": obs_value[0] if obs_value else None,
                    })
    else:
        obs_dim_lookup = [{i: v["id"] for i, v in enumerate(d["values"])} for d in obs_dims]
        obs_ids = [d["id"] for d in obs_dims]
        ref_idx = next((i for i, d in enumerate(obs_ids) if d in ("REF_AREA", "COUNTRY")), None)
        sex_idx = next((i for i, d in enumerate(obs_ids) if d == "SEX"), None)
        eco_idx = next((i for i, d in enumerate(obs_ids) if d in ("ECONOMIC_ACTIVITY", "ECO")), None)
        ste_idx = next((i for i, d in enumerate(obs_ids) if d == "STE"), None)
        time_idx = next((i for i, d in enumerate(obs_ids) if d == "TIME_PERIOD"), None)
        country_lookup = {v["id"]: v["name"] for v in obs_dims[ref_idx]["values"]} if ref_idx is not None else {}
        meas_dim = next((d for d in obs_dims if d["id"] == "MEASURE"), None)
        indicator_name = meas_dim["values"][0]["name"] if meas_dim and meas_dim.get("values") else indicator_code

        for obs_key, obs_value in dataset["observations"].items():
            indices = [int(i) for i in obs_key.split(":")]
            if len(indices) != len(obs_dim_lookup):
                continue

            country_code = obs_dim_lookup[ref_idx].get(indices[ref_idx], "") if ref_idx is not None else ""
            sex = obs_dim_lookup[sex_idx].get(indices[sex_idx], "SEX_T") if sex_idx is not None else "SEX_T"
            activity = obs_dim_lookup[eco_idx].get(indices[eco_idx], "_T") if eco_idx is not None else "_T"
            ste = obs_dim_lookup[ste_idx].get(indices[ste_idx], "_T") if ste_idx is not None else "_T"
            period = obs_dim_lookup[time_idx].get(indices[time_idx], "") if time_idx is not None else ""

            if sex not in KEEP_SEX or activity not in KEEP_ACTIVITY:
                continue
            if not (isinstance(period, str) and len(period) == 4 and period.isdigit()):
                continue

            records.append({
                "country_code": country_code,
                "country_name": country_lookup.get(country_code, country_code),
                "indicator_code": indicator_code,
                "indicator_name": indicator_name,
                "sex": sex,
                "economic_activity": activity,
                "status_in_employment": ste,
                "year": int(period),
                "value": obs_value[0] if obs_value else None,
            })

    return records


def save_records(conn, indicator_code: str, records: list[dict]) -> None:
    if not records:
        print(f"  No records to save for {indicator_code}.")
        return

    query = """
        INSERT INTO raw.raw_labor (
            country_code, country_name, indicator_code, indicator_name,
            sex, economic_activity, status_in_employment, year, value
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (country_code, indicator_code, sex, economic_activity, status_in_employment, year)
        DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
    """

    data_tuples = (
        (r["country_code"], r["country_name"], r["indicator_code"], r["indicator_name"],
         r["sex"], r["economic_activity"], r["status_in_employment"], r["year"], r["value"])
        for r in records
    )

    with conn.cursor() as cursor:
        cursor.executemany(query, data_tuples)

    print(f"  Saved {len(records)} rows for {indicator_code}.")


def run_ingestion() -> None:
    with psycopg2.connect(**DB_CONFIG) as conn:
        for indicator_code, _ in INDICATORS:
            print(f"Fetching {indicator_code}...")
            records = fetch_indicator(indicator_code)
            save_records(conn, indicator_code, records)
    print("Done.")


if __name__ == "__main__":
    run_ingestion()
"""Fetches World Bank indicators and saves them to Postgres."""

import os
import requests
import psycopg2


INDICATORS = [
    "NY.GDP.PCAP.CD",
    "SI.POV.DDAY",
    "SP.RUR.TOTL.ZS",
    "DT.ODA.ALLD.CD",
    # Climate exposure and adaptation proxies
    "EG.ELC.ACCS.ZS",  # Access to electricity (% of population)
    "ER.H2O.FWTL.ZS",  # Freshwater withdrawal (% of internal resources)
    "AG.LND.PRCP.MM",  # Annual precipitation (mm)
    "AG.LND.ARBL.ZS",  # Arable land (% of land area)
    "AG.LND.FRST.ZS",  # Forest area (% of land area)
]

DB_CONFIG = {
    "host": os.getenv("PIPELINE_DB_HOST", "pipeline-db"),
    "port": int(os.getenv("PIPELINE_DB_PORT", "5432")),
    "dbname": os.getenv("PIPELINE_DB_NAME", "pipeline"),
    "user": os.getenv("PIPELINE_DB_USER", "pipeline"),
    "password": os.getenv("PIPELINE_DB_PASSWORD", "pipeline"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def fetch_indicator(indicator_code):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
    params = {
        "format": "json",
        "per_page": 1000,
        "date": "2000:2024",
        "lendingType": "IBD,IDB",
    }

    records = []
    page = 1

    with requests.Session() as session:
        while True:
            response = session.get(url, params={**params, "page": page}, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list) or len(data) < 2:
                raise RuntimeError(
                    f"Unexpected World Bank API response for {indicator_code}: {data}"
                )

            metadata, page_records = data
            if not page_records:
                break

            for record in page_records:
                records.append({
                    "country_code": record["country"]["id"],
                    "country_name": record["country"]["value"],
                    "indicator_name": record["indicator"]["value"],
                    "year": int(record["date"]),
                    "value": record["value"],
                })

            if page >= metadata["pages"]:
                break

            page += 1

    return records


def save_records(conn, indicator_code, records):
    if not records:
        print(f"No records found for {indicator_code}")
        return

    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO raw.raw_economic
                (country_code, country_name, indicator_code, indicator_name, year, value)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (country_code, indicator_code, year)
            DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = NOW()
            """,
            [
                (
                    record["country_code"],
                    record["country_name"],
                    indicator_code,
                    record["indicator_name"],
                    record["year"],
                    record["value"],
                )
                for record in records
            ],
        )

    print(f"Saved {len(records)} rows for {indicator_code}")


def run_ingestion():
    with get_connection() as conn:
        for indicator_code in INDICATORS:
            print(f"Fetching {indicator_code}...")
            records = fetch_indicator(indicator_code)
            save_records(conn, indicator_code, records)

    print("Done")


if __name__ == "__main__":
    run_ingestion()

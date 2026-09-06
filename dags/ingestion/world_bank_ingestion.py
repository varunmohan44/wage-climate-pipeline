# Fetches World Bank indicators and saves them to Postgres.

import os
import time

import psycopg2
import requests


INDICATORS = [
    "NY.GDP.PCAP.CD",
    "SI.POV.DDAY",
    "SP.RUR.TOTL.ZS",
    "DT.ODA.ALLD.CD",
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


def fetch_valid_country_iso3() -> set:
    response = requests.get(
        "https://api.worldbank.org/v2/country",
        params={"format": "json", "per_page": 500, "type": "country"},
        timeout=30,
    )
    response.raise_for_status()
    _, countries = response.json()
    return {c["id"] for c in countries if c.get("id")}


def fetch_indicator(indicator_code, valid_iso3: set):
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
    params = {
        "format": "json",
        "per_page": 1000,
        "date": "2000:2024",
    }

    records = []
    page = 1

    with requests.Session() as session:
        while True:
            for attempt in range(3):
                response = session.get(url, params={**params, "page": page}, timeout=30)
                if response.status_code == 200:
                    break
                time.sleep(2 ** attempt)
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
                iso3 = record.get("countryiso3code", "")
                if iso3 not in valid_iso3:
                    continue
                records.append({
                    "country_code": iso3,
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
    valid_iso3 = fetch_valid_country_iso3()
    with get_connection() as conn:
        for indicator_code in INDICATORS:
            print(f"Fetching {indicator_code}...")
            records = fetch_indicator(indicator_code, valid_iso3)
            save_records(conn, indicator_code, records)

    print("Done")


if __name__ == "__main__":
    run_ingestion()

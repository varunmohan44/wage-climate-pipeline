"""Fetches ND-GAIN country vulnerability and readiness data and writes it to Postgres."""

import csv
import io
import os
import requests
import psycopg2

DB_CONFIG = {
    "host": os.getenv("PIPELINE_DB_HOST", "pipeline-db"),
    "port": int(os.getenv("PIPELINE_DB_PORT", "5432")),
    "dbname": os.getenv("PIPELINE_DB_NAME", "pipeline"),
    "user": os.getenv("PIPELINE_DB_USER", "pipeline"),
    "password": os.getenv("PIPELINE_DB_PASSWORD", "pipeline"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(float(value.replace(",", "")))
    except ValueError:
        return None


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def normalize_text(value: str | None) -> str:
    return value.strip() if value and value.strip() else ""


def get_csv_source_url() -> str | None:
    return os.getenv("ND_GAIN_CSV_URL")


def get_csv_source_path() -> str | None:
    return os.getenv("ND_GAIN_CSV_PATH")


def read_csv_rows() -> list[dict]:
    local_path = get_csv_source_path()
    if local_path:
        with open(local_path, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    csv_url = get_csv_source_url()
    if not csv_url:
        raise RuntimeError(
            "ND-GAIN ingestion requires ND_GAIN_CSV_URL or ND_GAIN_CSV_PATH to be set."
        )

    response = requests.get(csv_url, timeout=60)
    response.raise_for_status()
    return list(csv.DictReader(io.StringIO(response.text)))


def parse_gain_row(row: dict) -> dict:
    country_code = (
        row.get("ISO3")
        or row.get("Country Code")
        or row.get("ISO 3")
        or row.get("iso3")
        or row.get("CountryCode")
        or ""
    )

    country_name = (
        row.get("Country")
        or row.get("country")
        or row.get("Country Name")
        or ""
    )

    return {
        "country_code": normalize_text(country_code),
        "country_name": normalize_text(country_name),
        "year": parse_int(row.get("Year") or row.get("year")),
        "vulnerability_score": parse_float(
            row.get("Vulnerability") or row.get("Vulnerability Score")
        ),
        "vulnerability_rank": parse_int(
            row.get("Vulnerability Rank") or row.get("Vulnerability_Rank")
        ),
        "readiness_score": parse_float(
            row.get("Readiness") or row.get("Readiness Score")
        ),
        "readiness_rank": parse_int(
            row.get("Readiness Rank") or row.get("Readiness_Rank")
        ),
        "overall_score": parse_float(
            row.get("Overall Score") or row.get("GAIN Score")
        ),
        "overall_rank": parse_int(
            row.get("Overall Rank") or row.get("GAIN Rank")
        ),
        "region": normalize_text(row.get("Region") or row.get("region")),
        "income_group": normalize_text(row.get("Income Group") or row.get("Income Level")),
    }


def fetch_gain_rows() -> list[dict]:
    csv_rows = read_csv_rows()
    records = [parse_gain_row(row) for row in csv_rows]
    return [record for record in records if record["country_code"] and record["year"]]


def save_records(conn, records: list[dict]) -> None:
    if not records:
        print("No ND-GAIN records to save.")
        return

    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO raw.raw_gain (
                country_code,
                country_name,
                year,
                vulnerability_score,
                vulnerability_rank,
                readiness_score,
                readiness_rank,
                overall_score,
                overall_rank,
                region,
                income_group
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (country_code, year)
            DO UPDATE SET
                country_name = EXCLUDED.country_name,
                vulnerability_score = EXCLUDED.vulnerability_score,
                vulnerability_rank = EXCLUDED.vulnerability_rank,
                readiness_score = EXCLUDED.readiness_score,
                readiness_rank = EXCLUDED.readiness_rank,
                overall_score = EXCLUDED.overall_score,
                overall_rank = EXCLUDED.overall_rank,
                region = EXCLUDED.region,
                income_group = EXCLUDED.income_group,
                updated_at = NOW();
            """,
            [
                (
                    record["country_code"],
                    record["country_name"],
                    record["year"],
                    record["vulnerability_score"],
                    record["vulnerability_rank"],
                    record["readiness_score"],
                    record["readiness_rank"],
                    record["overall_score"],
                    record["overall_rank"],
                    record["region"],
                    record["income_group"],
                )
                for record in records
            ],
        )

    print(f"Saved {len(records)} ND-GAIN records.")


def run_ingestion() -> None:
    records = fetch_gain_rows()
    if not records:
        print("No ND-GAIN records found.")
        return

    with get_connection() as conn:
        save_records(conn, records)

    print("ND-GAIN ingestion complete.")

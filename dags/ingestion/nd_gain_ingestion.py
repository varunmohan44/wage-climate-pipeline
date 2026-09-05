# Fetches ND-GAIN vulnerability and readiness scores and writes them to Postgres.

import csv
import io
import os
import zipfile

import psycopg2
import requests

GAIN_ZIP_URL = "https://gain.nd.edu/assets/647440/ndgain_countryindex_2026.zip"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; wage-climate-pipeline/1.0)",
    "Referer": "https://gain.nd.edu/our-work/country-index/download-data/",
}

DB_CONFIG = {
    "host": os.getenv("PIPELINE_DB_HOST", "pipeline-db"),
    "port": int(os.getenv("PIPELINE_DB_PORT", "5432")),
    "dbname": os.getenv("PIPELINE_DB_NAME", "pipeline"),
    "user": os.getenv("PIPELINE_DB_USER", "pipeline"),
    "password": os.getenv("PIPELINE_DB_PASSWORD", "pipeline"),
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def _download_zip() -> bytes:
    url = os.getenv("ND_GAIN_ZIP_URL", GAIN_ZIP_URL)
    response = requests.get(url, headers=_HEADERS, timeout=60)
    response.raise_for_status()
    return response.content


def _resolve_member(zf: zipfile.ZipFile, suffix: str) -> str:
    # ND-GAIN's zip has nested the resources/ dir under a varying top-level
    # folder name across releases (e.g. "resources 2/"), so match by suffix
    # instead of assuming a fixed prefix. __MACOSX/ entries mirror real paths
    # and must be excluded.
    matches = [n for n in zf.namelist() if n.endswith(suffix) and "__MACOSX" not in n]
    if not matches:
        raise KeyError(f"No archive member ending with {suffix!r} found in ND-GAIN zip")
    return matches[0]


def _parse_wide(zf: zipfile.ZipFile, member: str) -> dict[str, dict[str, float | None]]:
    with zf.open(member) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
        result: dict[str, dict[str, float | None]] = {}
        for row in reader:
            iso3 = row.get("ISO3", "").strip()
            if not iso3:
                continue
            years: dict[str, float | None] = {}
            for col, val in row.items():
                if col in ("ISO3", "Name") or not col.isdigit():
                    continue
                stripped = val.strip() if val else ""
                years[col] = float(stripped) if stripped else None
            result[iso3] = years
    return result


def _country_names(zf: zipfile.ZipFile, member: str) -> dict[str, str]:
    with zf.open(member) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))
        return {
            row["ISO3"].strip(): row.get("Name", "").strip()
            for row in reader
            if row.get("ISO3", "").strip()
        }


def fetch_gain_records() -> list[dict]:
    zip_bytes = _download_zip()

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        gain_member = _resolve_member(zf, "gain/gain.csv")
        vuln_member = _resolve_member(zf, "vulnerability/vulnerability.csv")
        read_member = _resolve_member(zf, "readiness/readiness.csv")

        gain_scores = _parse_wide(zf, gain_member)
        vuln_scores = _parse_wide(zf, vuln_member)
        read_scores = _parse_wide(zf, read_member)
        names = _country_names(zf, gain_member)

    all_iso3 = set(gain_scores) | set(vuln_scores) | set(read_scores)
    records = []

    for iso3 in sorted(all_iso3):
        country_name = names.get(iso3, iso3)
        all_years = (
            set(gain_scores.get(iso3, {}))
            | set(vuln_scores.get(iso3, {}))
            | set(read_scores.get(iso3, {}))
        )

        for year_str in sorted(all_years):
            if not (year_str.isdigit() and len(year_str) == 4):
                continue

            overall = gain_scores.get(iso3, {}).get(year_str)
            vuln = vuln_scores.get(iso3, {}).get(year_str)
            ready = read_scores.get(iso3, {}).get(year_str)

            if overall is None and vuln is None and ready is None:
                continue

            records.append({
                "country_code": iso3,
                "country_name": country_name,
                "year": int(year_str),
                "vulnerability_score": vuln,
                "readiness_score": ready,
                "overall_score": overall,
            })

    return records


def save_records(conn, records: list[dict]) -> None:
    if not records:
        print("No ND-GAIN records to save.")
        return

    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO raw.raw_gain (
                country_code, country_name, year,
                vulnerability_score, readiness_score, overall_score
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (country_code, year)
            DO UPDATE SET
                country_name = EXCLUDED.country_name,
                vulnerability_score = EXCLUDED.vulnerability_score,
                readiness_score = EXCLUDED.readiness_score,
                overall_score = EXCLUDED.overall_score,
                updated_at = NOW();
            """,
            [
                (
                    r["country_code"], r["country_name"], r["year"],
                    r["vulnerability_score"], r["readiness_score"], r["overall_score"],
                )
                for r in records
            ],
        )

    print(f"Saved {len(records)} ND-GAIN records.")


def run_ingestion() -> None:
    records = fetch_gain_records()
    if not records:
        print("No ND-GAIN records found.")
        return

    with get_connection() as conn:
        save_records(conn, records)

    print("ND-GAIN ingestion complete.")


if __name__ == "__main__":
    run_ingestion()

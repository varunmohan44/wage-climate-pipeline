from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dags.ingestion.nd_gain_ingestion import fetch_gain_rows, parse_gain_row

SAMPLE_CSV = """Country,ISO3,Year,Vulnerability,Vulnerability Rank,Readiness,Readiness Rank,Overall Score,Overall Rank,Region,Income Group
Testland,TST,2024,23.4,45,66.1,12,44.5,34,Europe & Central Asia,High income
"""


def test_parse_gain_row():
    row = {
        "Country": "Testland",
        "ISO3": "TST",
        "Year": "2024",
        "Vulnerability": "23.4",
        "Vulnerability Rank": "45",
        "Readiness": "66.1",
        "Readiness Rank": "12",
        "Overall Score": "44.5",
        "Overall Rank": "34",
        "Region": "Europe & Central Asia",
        "Income Group": "High income",
    }

    parsed = parse_gain_row(row)

    assert parsed["country_code"] == "TST"
    assert parsed["country_name"] == "Testland"
    assert parsed["year"] == 2024
    assert parsed["vulnerability_score"] == 23.4
    assert parsed["vulnerability_rank"] == 45
    assert parsed["readiness_score"] == 66.1
    assert parsed["readiness_rank"] == 12
    assert parsed["overall_score"] == 44.5
    assert parsed["overall_rank"] == 34
    assert parsed["region"] == "Europe & Central Asia"
    assert parsed["income_group"] == "High income"


def test_fetch_gain_rows_from_local_path(tmp_path, monkeypatch):
    csv_path = tmp_path / "nd_gain.csv"
    csv_path.write_text(SAMPLE_CSV, encoding="utf-8")

    monkeypatch.setenv("ND_GAIN_CSV_PATH", str(csv_path))
    rows = fetch_gain_rows()

    assert len(rows) == 1
    assert rows[0]["country_code"] == "TST"
    assert rows[0]["year"] == 2024


def test_fetch_gain_rows_requires_source(monkeypatch):
    monkeypatch.delenv("ND_GAIN_CSV_PATH", raising=False)
    monkeypatch.delenv("ND_GAIN_CSV_URL", raising=False)

    with pytest.raises(RuntimeError, match="ND-GAIN ingestion requires"):
        fetch_gain_rows()


def test_fetch_gain_rows_from_url(monkeypatch):
    class DummyResponse(SimpleNamespace):
        def raise_for_status(self):
            return None

    def dummy_get(url, timeout):
        return DummyResponse(text=SAMPLE_CSV)

    monkeypatch.setenv("ND_GAIN_CSV_URL", "https://example.com/nd_gain.csv")
    monkeypatch.setattr("dags.ingestion.nd_gain_ingestion.requests.get", dummy_get)

    rows = fetch_gain_rows()

    assert rows[0]["country_code"] == "TST"
    assert rows[0]["year"] == 2024

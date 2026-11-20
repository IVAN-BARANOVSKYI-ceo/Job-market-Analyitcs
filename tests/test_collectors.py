import json

from src.collectors import arbeitnow, remotive
from src.collectors.raw_store import load_latest_raw, save_raw
from src.processing.standardize import standardize_arbeitnow, standardize_remotive
from tests.sample_data import ARBEITNOW_RAW, REMOTIVE_RAW


def test_arbeitnow_pagination_stops_on_empty_page(monkeypatch):
    pages = {1: {"data": ARBEITNOW_RAW[:2]}, 2: {"data": ARBEITNOW_RAW[2:]}, 3: {"data": []}}
    monkeypatch.setattr(arbeitnow, "get_json", lambda url, params=None: pages[params["page"]])
    monkeypatch.setattr(arbeitnow.time, "sleep", lambda s: None)
    assert len(arbeitnow.fetch_jobs(max_pages=5)) == 4


def test_arbeitnow_keeps_earlier_pages_when_later_page_fails(monkeypatch):
    def fake_get(url, params=None):
        if params["page"] == 2:
            raise RuntimeError("boom")
        return {"data": ARBEITNOW_RAW[:2]}

    monkeypatch.setattr(arbeitnow, "get_json", fake_get)
    monkeypatch.setattr(arbeitnow.time, "sleep", lambda s: None)
    assert len(arbeitnow.fetch_jobs(max_pages=3)) == 2


def test_remotive_fetch(monkeypatch):
    monkeypatch.setattr(remotive, "get_json", lambda url, params=None: {"jobs": REMOTIVE_RAW})
    assert len(remotive.fetch_jobs()) == 2


def test_raw_store_roundtrip(tmp_path):
    path = save_raw("arbeitnow", ARBEITNOW_RAW, raw_dir=tmp_path)
    assert path.exists()
    assert load_latest_raw("arbeitnow", raw_dir=tmp_path) == json.loads(path.read_text(encoding="utf-8"))


def test_standardize_arbeitnow():
    job = standardize_arbeitnow(ARBEITNOW_RAW[0])
    assert job["source"] == "arbeitnow"
    assert job["source_job_id"] == job["slug"]
    assert job["employment_raw"] == "Full Time"


def test_standardize_remotive():
    job = standardize_remotive(REMOTIVE_RAW[0])
    assert job["slug"] == "remotive-101"
    assert job["remote"] is True
    assert job["salary_raw"] == "€45k - €55k"
    assert "Data" in job["tags"]

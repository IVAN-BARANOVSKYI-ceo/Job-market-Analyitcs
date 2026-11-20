from src.processing.normalization import (
    detect_workplace,
    is_europe_relevant,
    normalize_date,
    normalize_employment,
    parse_location,
)


def test_parse_location_known_city():
    assert parse_location("Frankfurt am Main") == ("Frankfurt", "Germany", "DE")
    assert parse_location("München") == ("Munich", "Germany", "DE")


def test_parse_location_city_and_country():
    assert parse_location("Lisbon, Portugal") == ("Lisbon", "Portugal", "PT")


def test_parse_location_country_only_and_generic():
    assert parse_location("Netherlands") == (None, "Netherlands", "NL")
    assert parse_location("Worldwide") == (None, None, None)


def test_parse_location_unknown_city_keeps_city_without_country():
    assert parse_location("Smalltown") == ("Smalltown", None, None)


def test_parse_location_empty():
    assert parse_location(None) == (None, None, None)


def test_normalize_date():
    assert normalize_date(1763539200) == "2025-11-19"
    assert normalize_date("2026-11-10T09:30:00") == "2026-11-10"
    assert normalize_date("2026-11-10T09:30:00Z") == "2026-11-10"
    assert normalize_date("not a date") is None
    assert normalize_date(None) is None


def test_normalize_employment():
    assert normalize_employment("Full Time, Professional") == "Full-time"
    assert normalize_employment("part_time") == "Part-time"
    assert normalize_employment("contract") == "Contract"
    assert normalize_employment("Praktikum") == "Internship"
    assert normalize_employment(None) == "Unknown"


def test_detect_workplace():
    assert detect_workplace("Dev Berlin", "hybrid model", False) == "Hybrid"
    assert detect_workplace("Dev Remote", "", None) == "Remote"
    assert detect_workplace("Dev", "", True) == "Remote"
    assert detect_workplace("Dev Berlin", "work on-site", False) == "On-site"
    assert detect_workplace("Dev Berlin", "nothing here", False) == "Unknown"


def test_is_europe_relevant():
    assert is_europe_relevant({"source": "remotive", "country_code": "NL", "location": "Netherlands"})
    assert is_europe_relevant({"source": "remotive", "country_code": None, "location": "Europe"})
    assert not is_europe_relevant({"source": "remotive", "country_code": None, "location": "USA Only"})
    assert is_europe_relevant({"source": "arbeitnow", "country_code": None, "location": "Smalltown"})

from src.processing.cleaning import (
    clean_html_content,
    clean_jobs,
    make_dedup_key,
    remove_cross_source_duplicates,
    remove_duplicates,
    remove_empty_jobs,
)
from tests.sample_data import ARBEITNOW_RAW
from src.processing.standardize import standardize_source


def test_clean_html_plain():
    assert clean_html_content("<p>Hello <strong>world</strong></p>") == "Hello world"


def test_clean_html_escaped_and_double_escaped():
    assert clean_html_content("&lt;p&gt;Hello &lt;strong&gt;world&lt;/strong&gt;&lt;/p&gt;") == "Hello world"
    assert clean_html_content("&amp;lt;p&amp;gt;Hi&amp;lt;/p&amp;gt;") == "Hi"


def test_clean_html_removes_scripts_and_whitespace():
    assert clean_html_content("<script>alert(1)</script><p>A&nbsp; B</p>") == "A B"


def test_clean_html_empty_values():
    assert clean_html_content(None) == ""
    assert clean_html_content("") == ""


def test_remove_duplicates_by_slug():
    jobs = [{"slug": "a"}, {"slug": "a"}, {"slug": "b"}, {"slug": None}]
    assert [j["slug"] for j in remove_duplicates(jobs)] == ["a", "b"]


def test_remove_empty_jobs():
    good = {"slug": "a", "title": "T", "company_name": "C", "location": "L"}
    bad = {"slug": "b", "title": "T", "company_name": "", "location": "L"}
    assert remove_empty_jobs([good, bad]) == [good]


def test_clean_jobs_full_pipeline():
    records = standardize_source("arbeitnow", ARBEITNOW_RAW)
    cleaned = clean_jobs(records)
    assert len(cleaned) == 2
    assert "<" not in cleaned[0]["description"]


def test_cross_source_duplicates():
    key = make_dedup_key("Data Analyst (m/w/d)", "Acme", "Berlin")
    assert key == make_dedup_key("Data Analyst", "ACME ", "berlin")
    jobs = [{"dedup_key": key, "source": "a"}, {"dedup_key": key, "source": "b"}]
    assert len(remove_cross_source_duplicates(jobs)) == 1

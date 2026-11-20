from src.database import db
from src.processing.pipeline import process_jobs
from src.processing.standardize import standardize_source
from tests.sample_data import ARBEITNOW_RAW, REMOTIVE_RAW


# Build processed jobs from the mock API data
def build_jobs():
    records = standardize_source("arbeitnow", ARBEITNOW_RAW) + standardize_source("remotive", REMOTIVE_RAW)
    return process_jobs(records)


def test_pipeline_counts():
    jobs, stats = build_jobs()
    assert stats["standardized"] == 6
    # duplicate slug and empty company removed, non-European Remotive job filtered out
    assert stats["after_cleaning"] == 4
    assert stats["after_europe_filter"] == 3
    assert len(jobs) == 3


def test_pipeline_enrichment():
    jobs, _ = build_jobs()
    python_job = next(j for j in jobs if j["source_job_id"] == "senior-python-developer-berlin-1")
    assert python_job["country"] == "Germany"
    assert python_job["seniority"] == "Senior"
    assert python_job["industry"] == "Technology"
    assert python_job["salary_min"] == 60000
    assert python_job["created_at"] == "2025-11-19"
    assert {"Python", "Django", "PostgreSQL", "Docker"} <= {name for name, _ in python_job["skills"]}

    marketing = next(j for j in jobs if j["source_job_id"] == "marketing-manager-munich-2")
    assert marketing["workplace_type"] == "Hybrid"
    assert marketing["industry"] == "Non-Technology"

    remotive_job = next(j for j in jobs if j["source"] == "remotive")
    assert remotive_job["salary_raw"] == "€45k - €55k"
    assert remotive_job["salary_max"] == 55000
    assert remotive_job["workplace_type"] == "Remote"


def test_load_is_idempotent():
    conn = db.connect(":memory:")
    jobs, _ = build_jobs()
    assert db.load_jobs(conn, jobs) == (3, 0)
    assert db.load_jobs(conn, jobs) == (0, 3)
    assert conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 3
    skills_count = conn.execute("SELECT COUNT(*) FROM job_skills").fetchone()[0]
    db.load_jobs(conn, jobs)
    assert conn.execute("SELECT COUNT(*) FROM job_skills").fetchone()[0] == skills_count


def test_update_existing_record():
    conn = db.connect(":memory:")
    jobs, _ = build_jobs()
    db.load_jobs(conn, jobs)
    jobs[0]["title"] = "Changed title"
    db.load_jobs(conn, jobs)
    titles = [r[0] for r in conn.execute("SELECT title FROM jobs")]
    assert "Changed title" in titles
    assert len(titles) == 3

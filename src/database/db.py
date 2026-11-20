import json
import sqlite3
from pathlib import Path

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    source_job_id TEXT NOT NULL,
    slug TEXT,
    url TEXT,
    title TEXT NOT NULL,
    company_name TEXT NOT NULL,
    description TEXT,
    country TEXT,
    city TEXT,
    location TEXT,
    country_code TEXT,
    industry TEXT,
    job_category TEXT,
    job_role TEXT,
    classification_method TEXT,
    seniority TEXT,
    employment_type TEXT,
    workplace_type TEXT,
    remote INTEGER,
    salary_min REAL,
    salary_max REAL,
    salary_currency TEXT,
    salary_period TEXT,
    salary_period_source TEXT,
    salary_raw TEXT,
    tags TEXT,
    created_at TEXT,
    collected_at TEXT,
    updated_at TEXT,
    dedup_key TEXT,
    UNIQUE (source, source_job_id)
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id),
    PRIMARY KEY (job_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_country ON jobs(country);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(job_category);
CREATE INDEX IF NOT EXISTS idx_jobs_industry ON jobs(industry);
CREATE INDEX IF NOT EXISTS idx_jobs_seniority ON jobs(seniority);
CREATE INDEX IF NOT EXISTS idx_jobs_dedup ON jobs(dedup_key);
"""

JOB_COLUMNS = [
    "source", "source_job_id", "slug", "url", "title", "company_name", "description",
    "country", "city", "location", "country_code", "industry", "job_category", "job_role",
    "classification_method", "seniority", "employment_type", "workplace_type", "remote",
    "salary_min", "salary_max", "salary_currency", "salary_period", "salary_period_source",
    "salary_raw", "tags", "created_at", "collected_at", "updated_at", "dedup_key",
]


# Open a SQLite connection and make sure the schema exists
def connect(path=None):
    path = path or config.DB_PATH
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


# Convert a job dict to a row of database values
def _job_values(job):
    row = {column: job.get(column) for column in JOB_COLUMNS}
    row["tags"] = json.dumps(job.get("tags") or [], ensure_ascii=False)
    if row["remote"] is not None:
        row["remote"] = int(bool(row["remote"]))
    return [row[column] for column in JOB_COLUMNS]


# Insert a job or update it if (source, source_job_id) already exists
def upsert_job(conn, job):
    exists = conn.execute(
        "SELECT id FROM jobs WHERE source = ? AND source_job_id = ?",
        (job["source"], job["source_job_id"]),
    ).fetchone()

    placeholders = ", ".join("?" for _ in JOB_COLUMNS)
    updates = ", ".join(
        f"{c} = excluded.{c}" for c in JOB_COLUMNS if c not in ("source", "source_job_id")
    )
    conn.execute(
        f"INSERT INTO jobs ({', '.join(JOB_COLUMNS)}) VALUES ({placeholders}) "
        f"ON CONFLICT(source, source_job_id) DO UPDATE SET {updates}",
        _job_values(job),
    )
    job_id = conn.execute(
        "SELECT id FROM jobs WHERE source = ? AND source_job_id = ?",
        (job["source"], job["source_job_id"]),
    ).fetchone()[0]
    return job_id, exists is None


# Replace the skills linked to a job
def set_job_skills(conn, job_id, skills):
    conn.execute("DELETE FROM job_skills WHERE job_id = ?", (job_id,))
    for name, category in skills:
        conn.execute("INSERT OR IGNORE INTO skills (name, category) VALUES (?, ?)", (name, category))
        skill_id = conn.execute("SELECT id FROM skills WHERE name = ?", (name,)).fetchone()[0]
        conn.execute(
            "INSERT OR IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)", (job_id, skill_id)
        )


# Write all jobs in one transaction; returns (inserted, updated)
def load_jobs(conn, jobs):
    inserted = updated = 0
    with conn:
        for job in jobs:
            job_id, is_new = upsert_job(conn, job)
            set_job_skills(conn, job_id, job.get("skills") or [])
            if is_new:
                inserted += 1
            else:
                updated += 1
    return inserted, updated

from src.analysis import queries
from src.analysis.report import build_summary
from src.database import db
from src.visualization.charts import build_all
from tests.test_database import build_jobs


# Create an in-memory database filled with mock jobs
def make_conn():
    conn = db.connect(":memory:")
    jobs, _ = build_jobs()
    db.load_jobs(conn, jobs)
    return conn


def test_quality_metrics():
    quality = queries.quality_metrics(make_conn())
    assert quality["total_jobs"] == 3
    assert quality["country_known_pct"] == 100.0
    assert quality["sources"] == {"arbeitnow": 2, "remotive": 1}


def test_basic_queries():
    conn = make_conn()
    countries = queries.jobs_by_country(conn)
    assert countries.iloc[0]["country"] == "Germany"
    assert queries.top_skills(conn).iloc[0]["jobs"] >= 1
    assert set(queries.tech_vs_nontech(conn)["industry"]) == {"Technology", "Non-Technology"}


def test_small_groups_are_hidden_in_salary_medians():
    # mock data has fewer than MIN_GROUP_SIZE jobs per group
    assert queries.median_salary_by(make_conn(), "seniority").empty


def test_summary_and_charts(tmp_path):
    conn = make_conn()
    paths = build_all(conn, figures_dir=tmp_path)
    assert all(p.exists() for p in paths)
    assert len(paths) >= 5
    summary = build_summary(conn)
    assert "Jobs in database: **3**" in summary

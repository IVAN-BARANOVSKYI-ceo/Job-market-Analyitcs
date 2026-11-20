import pandas as pd

import config


# Run a SQL query and return a DataFrame
def _query(conn, sql, params=()):
    return pd.read_sql_query(sql, conn, params=params)


# Top countries by number of jobs
def jobs_by_country(conn, limit=10):
    return _query(
        conn,
        "SELECT country, COUNT(*) AS jobs FROM jobs WHERE country IS NOT NULL "
        "GROUP BY country ORDER BY jobs DESC LIMIT ?",
        (limit,),
    )


# Top cities by number of jobs
def jobs_by_city(conn, limit=15):
    return _query(
        conn,
        "SELECT city, COUNT(*) AS jobs FROM jobs WHERE city IS NOT NULL "
        "GROUP BY city ORDER BY jobs DESC LIMIT ?",
        (limit,),
    )


# Number of jobs per job category
def jobs_by_category(conn):
    return _query(
        conn,
        "SELECT job_category, industry, COUNT(*) AS jobs FROM jobs "
        "GROUP BY job_category, industry ORDER BY jobs DESC",
    )


# Share of technology jobs per country (classified jobs only)
def tech_share_by_country(conn, limit=10):
    return _query(
        conn,
        "SELECT country, COUNT(*) AS jobs, ROUND(100.0 * AVG(industry = 'Technology'), 1) AS tech_pct "
        "FROM jobs WHERE country IS NOT NULL AND industry != 'Unknown' "
        "GROUP BY country HAVING COUNT(*) >= ? ORDER BY jobs DESC LIMIT ?",
        (config.MIN_GROUP_SIZE, limit),
    )


# Most frequent technologies
def top_skills(conn, limit=20):
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    df = _query(
        conn,
        "SELECT s.name, s.category, COUNT(*) AS jobs FROM job_skills js "
        "JOIN skills s ON s.id = js.skill_id GROUP BY s.id ORDER BY jobs DESC LIMIT ?",
        (limit,),
    )
    df["pct_of_jobs"] = (100.0 * df["jobs"] / total).round(1) if total else 0.0
    return df


# Skill share (% of jobs) for the most common tech roles and skills
def skills_by_role(conn, max_roles=8, max_skills=15):
    roles = _query(
        conn,
        "SELECT job_role, COUNT(*) AS role_jobs FROM jobs WHERE industry = 'Technology' "
        "GROUP BY job_role HAVING COUNT(*) >= ? ORDER BY role_jobs DESC LIMIT ?",
        (config.MIN_GROUP_SIZE, max_roles),
    )
    if roles.empty:
        return pd.DataFrame()

    pairs = _query(
        conn,
        "SELECT j.job_role, s.name AS skill, COUNT(*) AS n FROM jobs j "
        "JOIN job_skills js ON js.job_id = j.id JOIN skills s ON s.id = js.skill_id "
        "WHERE j.industry = 'Technology' GROUP BY j.job_role, s.name",
    )
    pairs = pairs.merge(roles, on="job_role")
    pairs["pct"] = 100.0 * pairs["n"] / pairs["role_jobs"]
    top = pairs.groupby("skill")["n"].sum().nlargest(max_skills).index
    table = pairs[pairs["skill"].isin(top)].pivot_table(
        index="job_role", columns="skill", values="pct", fill_value=0.0
    )
    return table.reindex(roles["job_role"])


# Number of jobs per seniority level
def seniority_distribution(conn):
    return _query(
        conn, "SELECT seniority, COUNT(*) AS jobs FROM jobs GROUP BY seniority ORDER BY jobs DESC"
    )


# Workplace type counts per industry group
def workplace_by_industry(conn):
    return _query(
        conn,
        "SELECT industry, workplace_type, COUNT(*) AS jobs FROM jobs "
        "WHERE industry != 'Unknown' GROUP BY industry, workplace_type",
    )


# Tech vs Non-Tech comparison table (classified jobs only)
def tech_vs_nontech(conn):
    return _query(
        conn,
        "SELECT industry, COUNT(*) AS jobs, "
        "ROUND(100.0 * AVG(workplace_type = 'Remote'), 1) AS remote_pct, "
        "ROUND(100.0 * AVG(seniority != 'Unknown'), 1) AS seniority_known_pct, "
        "ROUND(100.0 * AVG(salary_min IS NOT NULL), 1) AS salary_pct "
        "FROM jobs WHERE industry != 'Unknown' GROUP BY industry ORDER BY industry DESC",
    )


# Share of jobs with a parsed salary per country
def salary_transparency_by_country(conn, limit=10):
    return _query(
        conn,
        "SELECT country, COUNT(*) AS jobs, "
        "ROUND(100.0 * AVG(salary_min IS NOT NULL), 1) AS salary_pct "
        "FROM jobs WHERE country IS NOT NULL GROUP BY country "
        "HAVING COUNT(*) >= ? ORDER BY jobs DESC LIMIT ?",
        (config.MIN_GROUP_SIZE, limit),
    )


# Yearly EUR salaries (midpoint) with seniority and role, for salary comparison
def yearly_eur_salaries(conn):
    return _query(
        conn,
        "SELECT job_role, industry, seniority, country, "
        "(salary_min + salary_max) / 2.0 AS salary_mid FROM jobs "
        "WHERE salary_period = 'yearly' AND salary_currency = 'EUR'",
    )


# Median yearly EUR salary per group, only for groups with enough jobs
def median_salary_by(conn, column):
    df = yearly_eur_salaries(conn)
    if df.empty:
        return pd.DataFrame(columns=[column, "jobs", "median_salary"])
    grouped = df.groupby(column)["salary_mid"].agg(jobs="count", median_salary="median")
    grouped = grouped[grouped["jobs"] >= config.MIN_GROUP_SIZE]
    return grouped.sort_values("median_salary", ascending=False).reset_index()


# Data quality metrics and sample description
def quality_metrics(conn):
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    if total == 0:
        return {"total_jobs": 0}

    def pct(condition):
        count = conn.execute(f"SELECT COUNT(*) FROM jobs WHERE {condition}").fetchone()[0]
        return round(100.0 * count / total, 1)

    with_skills = conn.execute("SELECT COUNT(DISTINCT job_id) FROM job_skills").fetchone()[0]
    dates = conn.execute("SELECT MIN(created_at), MAX(created_at), MIN(collected_at) FROM jobs").fetchone()
    sources = dict(conn.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source").fetchall())
    return {
        "total_jobs": total,
        "sources": sources,
        "country_known_pct": pct("country IS NOT NULL"),
        "city_known_pct": pct("city IS NOT NULL"),
        "classified_pct": pct("job_category != 'Unclassified'"),
        "seniority_known_pct": pct("seniority != 'Unknown'"),
        "workplace_known_pct": pct("workplace_type != 'Unknown'"),
        "salary_pct": pct("salary_min IS NOT NULL"),
        "with_skills_pct": round(100.0 * with_skills / total, 1),
        "posted_from": dates[0],
        "posted_to": dates[1],
        "collected_at": dates[2],
    }

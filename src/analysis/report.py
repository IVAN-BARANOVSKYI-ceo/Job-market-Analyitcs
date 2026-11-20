from datetime import date

import config
from src.analysis import queries


# Render a DataFrame as a Markdown table
def _table(df):
    if df.empty:
        return "_Not enough data._\n"
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    divider = "|" + "---|" * len(df.columns)
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, divider, *rows]) + "\n"


# Build the factual summary (reports/summary.md) from database results
def build_summary(conn, stats=None, figure_paths=None):
    quality = queries.quality_metrics(conn)
    if quality["total_jobs"] == 0:
        return "# Summary\n\nNo data available.\n"

    lines = [f"# Job Market Summary\n\nGenerated on {date.today().isoformat()}.\n"]

    lines.append("## Sample\n")
    lines.append(f"- Jobs in database: **{quality['total_jobs']}**")
    sources = ", ".join(f"{name} ({n})" for name, n in quality["sources"].items())
    lines.append(f"- Sources: {sources}")
    lines.append(f"- Postings published between {quality['posted_from']} and {quality['posted_to']}")
    lines.append(f"- Collected: {quality['collected_at']}")
    if stats:
        lines.append(
            "- Pipeline steps: " + " → ".join(f"{k.replace('_', ' ')}: {v}" for k, v in stats.items())
        )
    lines.append("")

    lines.append("## Data quality\n")
    lines.append(f"- Country identified: {quality['country_known_pct']}%")
    lines.append(f"- City identified: {quality['city_known_pct']}%")
    lines.append(f"- Job category identified: {quality['classified_pct']}%")
    lines.append(f"- Seniority identified: {quality['seniority_known_pct']}%")
    lines.append(f"- Workplace type identified: {quality['workplace_known_pct']}%")
    lines.append(f"- Salary parsed: {quality['salary_pct']}%")
    lines.append(f"- At least one technology found: {quality['with_skills_pct']}%\n")

    countries = queries.jobs_by_country(conn)
    if not countries.empty:
        known = int(conn.execute("SELECT COUNT(*) FROM jobs WHERE country IS NOT NULL").fetchone()[0])
        top = countries.iloc[0]
        lines.append("## Geography\n")
        lines.append(
            f"{top['country']} has the most jobs in the sample: {int(top['jobs'])} "
            f"({round(100 * top['jobs'] / known, 1)}% of jobs with an identified country).\n"
        )
        lines.append(_table(countries))

    compare = queries.tech_vs_nontech(conn)
    lines.append("## Technology vs Non-Technology\n")
    lines.append("Based on jobs with an identified job category. Columns are shares of jobs in %.\n")
    lines.append(_table(compare))

    skills = queries.top_skills(conn, limit=10)
    lines.append("## Most requested technologies\n")
    lines.append(_table(skills))

    lines.append("## Salaries\n")
    salary = queries.median_salary_by(conn, "seniority")
    lines.append(
        f"Only {quality['salary_pct']}% of jobs have a parsed salary. Medians below use yearly EUR "
        f"salaries only, in groups with at least {config.MIN_GROUP_SIZE} jobs.\n"
    )
    lines.append(_table(salary))

    if figure_paths:
        lines.append("## Figures\n")
        lines.extend(f"- `reports/figures/{path.name}`" for path in figure_paths)
        lines.append("")

    lines.append(
        "## Notes\n\nThis is a one-time snapshot of the selected sources, not the full European "
        "job market. See the README for methodology and limitations.\n"
    )
    return "\n".join(lines)

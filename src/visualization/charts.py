import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config
from src.analysis import queries

logger = logging.getLogger(__name__)

COLORS = {"main": "#2F6690", "tech": "#2F6690", "non": "#E07A5F", "grey": "#9AA5B1"}
plt.rcParams.update({
    "figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "font.size": 10,
})


# Save a figure with a title and a footer showing sample size and collection date
def _finish(fig, ax, title, xlabel, ylabel, meta, filename, figures_dir):
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    footer = f"n = {meta['total_jobs']} jobs | Sources: {', '.join(meta['sources'])} | Collected: {meta['collected_at']}"
    fig.text(0.01, 0.01, footer, fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    path = Path(figures_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


# Horizontal bar chart helper
def _barh(df, label_col, value_col, title, xlabel, ylabel, meta, filename, figures_dir, color=None):
    if df.empty:
        logger.info("Skipping %s: no data", filename)
        return None
    df = df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, max(3, 0.38 * len(df) + 1.5)))
    bars = ax.barh(df[label_col].astype(str), df[value_col], color=color or COLORS["main"])
    ax.bar_label(bars, padding=3, fontsize=8)
    return _finish(fig, ax, title, xlabel, ylabel, meta, filename, figures_dir)


# Build all figures; returns the list of saved paths
def build_all(conn, figures_dir=None):
    figures_dir = figures_dir or config.FIGURES_DIR
    quality = queries.quality_metrics(conn)
    if quality["total_jobs"] == 0:
        logger.warning("Database is empty, no figures created")
        return []
    meta = {
        "total_jobs": quality["total_jobs"],
        "sources": sorted(quality["sources"]),
        "collected_at": (quality["collected_at"] or "")[:10],
    }
    saved = []

    # 1. Geography
    saved.append(_barh(queries.jobs_by_country(conn), "country", "jobs",
                       "Top countries by number of jobs", "Number of jobs", "",
                       meta, "01_jobs_by_country.png", figures_dir))
    saved.append(_barh(queries.jobs_by_city(conn), "city", "jobs",
                       "Top cities by number of jobs", "Number of jobs", "",
                       meta, "02_jobs_by_city.png", figures_dir))

    # 2. Technology demand
    saved.append(_barh(queries.top_skills(conn), "name", "pct_of_jobs",
                       "Most requested technologies", "% of all jobs mentioning the technology", "",
                       meta, "03_top_technologies.png", figures_dir))
    saved.append(_skills_heatmap(conn, meta, figures_dir))

    # 3. Seniority
    seniority = queries.seniority_distribution(conn)
    saved.append(_barh(seniority, "seniority", "jobs",
                       "Jobs by seniority level (Unknown = no signal in title)", "Number of jobs", "",
                       meta, "05_seniority.png", figures_dir))

    # 4. Workplace and Tech vs Non-Tech
    saved.append(_workplace_chart(conn, meta, figures_dir))
    saved.append(_tech_vs_nontech_chart(conn, meta, figures_dir))
    saved.append(_barh(queries.jobs_by_category(conn), "job_category", "jobs",
                       "Jobs by professional category", "Number of jobs", "",
                       meta, "08_job_categories.png", figures_dir))

    # 5. Salary
    saved.append(_barh(queries.salary_transparency_by_country(conn), "country", "salary_pct",
                       "Salary transparency: % of jobs with a parsed salary", "% of jobs", "",
                       meta, "09_salary_transparency.png", figures_dir))
    salary = queries.median_salary_by(conn, "seniority")
    saved.append(_barh(salary, "seniority", "median_salary",
                       "Median yearly salary in EUR by seniority", "EUR per year (midpoint of range)", "",
                       meta, "10_salary_by_seniority.png", figures_dir))

    return [path for path in saved if path]


# Heatmap: share of jobs mentioning each technology per tech role
def _skills_heatmap(conn, meta, figures_dir):
    table = queries.skills_by_role(conn)
    if table.empty:
        return None
    fig, ax = plt.subplots(figsize=(max(8, 0.6 * table.shape[1] + 3), 0.55 * table.shape[0] + 2.5))
    image = ax.imshow(table.values, cmap="Blues", aspect="auto")
    ax.set_xticks(range(table.shape[1]), table.columns, rotation=45, ha="right")
    ax.set_yticks(range(table.shape[0]), table.index)
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            value = table.values[i, j]
            if value >= 1:
                ax.text(j, i, f"{value:.0f}", ha="center", va="center", fontsize=7)
    fig.colorbar(image, ax=ax, label="% of role's jobs")
    return _finish(fig, ax, "Technologies by tech role (% of the role's jobs)", "Technology", "",
                   meta, "04_skills_by_role_heatmap.png", figures_dir)


# Stacked bar: Remote / Hybrid / On-site / Unknown per industry group
def _workplace_chart(conn, meta, figures_dir):
    df = queries.workplace_by_industry(conn)
    if df.empty:
        return None
    table = df.pivot_table(index="industry", columns="workplace_type", values="jobs", fill_value=0)
    table = 100.0 * table.div(table.sum(axis=1), axis=0)
    fig, ax = plt.subplots(figsize=(8, 3 + 0.5 * len(table)))
    table.plot(kind="barh", stacked=True, ax=ax, colormap="Blues_r", width=0.6)
    ax.legend(title="Workplace type", bbox_to_anchor=(1.01, 1), loc="upper left", frameon=False)
    return _finish(fig, ax, "Workplace type: Technology vs Non-Technology", "% of jobs", "",
                   meta, "06_workplace_by_industry.png", figures_dir)


# Grouped bars comparing Tech and Non-Tech on a few shares
def _tech_vs_nontech_chart(conn, meta, figures_dir):
    df = queries.tech_vs_nontech(conn)
    if len(df) < 2:
        return None
    metrics = {"remote_pct": "Remote", "seniority_known_pct": "Seniority stated", "salary_pct": "Salary stated"}
    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.38
    for offset, (_, row) in zip((-width / 2, width / 2), df.iterrows()):
        color = COLORS["tech"] if row["industry"] == "Technology" else COLORS["non"]
        bars = ax.bar([i + offset for i in range(len(metrics))], [row[m] for m in metrics],
                      width, label=f"{row['industry']} (n={int(row['jobs'])})", color=color)
        ax.bar_label(bars, fmt="%.1f", fontsize=8, padding=2)
    ax.set_xticks(range(len(metrics)), list(metrics.values()))
    ax.legend(frameon=False)
    return _finish(fig, ax, "Technology vs Non-Technology jobs", "", "% of jobs",
                   meta, "07_tech_vs_nontech.png", figures_dir)

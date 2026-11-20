from datetime import datetime, timezone

from src.processing.classification import classify_job, detect_seniority, extract_skills
from src.processing.cleaning import (
    clean_jobs,
    make_dedup_key,
    remove_cross_source_duplicates,
)
from src.processing.normalization import (
    detect_workplace,
    is_europe_relevant,
    normalize_date,
    normalize_employment,
    parse_location,
)
from src.processing.salary import parse_salary


# Add normalized and derived fields to one cleaned job
def enrich_job(job, collected_at):
    title = job["title"]
    tags = job.get("tags") or []
    description = job.get("description") or ""

    city, country, country_code = parse_location(job.get("location"))
    category, role, industry, method = classify_job(title, tags)

    salary_text = job.get("salary_raw") or description
    salary = parse_salary(salary_text)

    enriched = dict(job)
    enriched.update(salary)
    enriched["salary_raw"] = job.get("salary_raw") or salary["salary_raw"]
    enriched.update({
        "city": city,
        "country": country,
        "country_code": country_code,
        "industry": industry,
        "job_category": category,
        "job_role": role,
        "classification_method": method,
        "seniority": detect_seniority(title),
        "employment_type": normalize_employment(job.get("employment_raw")),
        "workplace_type": detect_workplace(
            " ".join([title, job.get("location") or "", " ".join(tags)]),
            description,
            job.get("remote"),
        ),
        "created_at": normalize_date(job.get("created_at")),
        "updated_at": normalize_date(job.get("updated_at")),
        "collected_at": collected_at,
        "skills": extract_skills(title, tags, description),
        "dedup_key": make_dedup_key(title, job.get("company_name"), city),
    })
    return enriched


# Run cleaning, enrichment, Europe filter and deduplication; returns jobs and step counts
def process_jobs(records):
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stats = {"standardized": len(records)}

    cleaned = clean_jobs(records)
    stats["after_cleaning"] = len(cleaned)

    enriched = [enrich_job(job, collected_at) for job in cleaned]
    enriched = [job for job in enriched if is_europe_relevant(job)]
    stats["after_europe_filter"] = len(enriched)

    unique = remove_cross_source_duplicates(enriched)
    stats["after_deduplication"] = len(unique)
    return unique, stats

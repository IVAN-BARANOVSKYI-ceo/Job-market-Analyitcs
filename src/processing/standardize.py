# Convert a raw Arbeitnow record to the common job structure
def standardize_arbeitnow(raw):
    return {
        "source": "arbeitnow",
        "source_job_id": raw.get("slug"),
        "slug": raw.get("slug"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "company_name": raw.get("company_name"),
        "description": raw.get("description"),
        "location": raw.get("location"),
        "remote": raw.get("remote"),
        "tags": list(raw.get("tags") or []),
        "employment_raw": ", ".join(raw.get("job_types") or []),
        "created_at": raw.get("created_at"),
        "updated_at": None,
        "salary_raw": None,
    }


# Convert a raw Remotive record to the common job structure
def standardize_remotive(raw):
    job_id = raw.get("id")
    tags = list(raw.get("tags") or [])
    if raw.get("category"):
        tags.append(raw["category"])
    return {
        "source": "remotive",
        "source_job_id": str(job_id) if job_id is not None else None,
        "slug": f"remotive-{job_id}" if job_id is not None else None,
        "url": raw.get("url"),
        "title": raw.get("title"),
        "company_name": raw.get("company_name"),
        "description": raw.get("description"),
        "location": raw.get("candidate_required_location"),
        "remote": True,
        "tags": tags,
        "employment_raw": raw.get("job_type"),
        "created_at": raw.get("publication_date"),
        "updated_at": None,
        "salary_raw": raw.get("salary") or None,
    }


STANDARDIZERS = {
    "arbeitnow": standardize_arbeitnow,
    "remotive": standardize_remotive,
}


# Standardize all raw records of one source
def standardize_source(source, raw_jobs):
    return [STANDARDIZERS[source](raw) for raw in raw_jobs]

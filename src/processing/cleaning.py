import html
import re

from bs4 import BeautifulSoup


# Remove duplicate jobs by slug
def remove_duplicates(jobs):
    seen_slug = set()
    unique_jobs = []
    for job in jobs:
        slug = job.get("slug")
        if slug and slug not in seen_slug:
            seen_slug.add(slug)
            unique_jobs.append(job)
    return unique_jobs


# Remove jobs with empty required fields
def remove_empty_jobs(jobs):
    valid_jobs = []
    for job in jobs:
        if all(job.get(field) for field in ["slug", "title", "company_name", "location"]):
            valid_jobs.append(job)
    return valid_jobs


# Collapse repeated whitespace in a text value
def normalize_whitespace(text):
    if not text:
        return ""
    return " ".join(str(text).split())


# Convert HTML description to plain text (also handles escaped HTML)
def clean_html_content(html_content):
    if not html_content:
        return ""

    text = str(html_content)

    for _ in range(3):
        text = html.unescape(text)
        if "<" not in text and "&lt;" not in text:
            break
        if "<" not in text:
            continue
        soup = BeautifulSoup(text, "html.parser")
        for element in soup(["script", "style"]):
            element.decompose()
        text = soup.get_text(separator=" ", strip=True)

    return normalize_whitespace(text)


# Clean HTML in the descriptions of all jobs
def clean_html_jobs(jobs):
    for job in jobs:
        job["description"] = clean_html_content(job.get("description"))
    return jobs


# Normalize whitespace in short text fields
def clean_text_fields(jobs):
    for job in jobs:
        for field in ["title", "company_name", "location"]:
            job[field] = normalize_whitespace(job.get(field))
    return jobs


# Final cleaning function that combines all cleaning steps
def clean_jobs(jobs):
    cleaned_jobs = remove_duplicates(jobs)
    cleaned_jobs = clean_text_fields(cleaned_jobs)
    cleaned_jobs = remove_empty_jobs(cleaned_jobs)
    cleaned_jobs = clean_html_jobs(cleaned_jobs)
    return cleaned_jobs


# Build a key that identifies the same job posted in several sources
def make_dedup_key(title, company_name, city):
    title = re.sub(r"\(.*?\)", "", (title or "").lower())
    parts = [title, (company_name or "").lower(), (city or "").lower()]
    return "|".join(re.sub(r"[^a-z0-9]+", "", part) for part in parts)


# Remove jobs that appear in more than one source (keeps the first one)
def remove_cross_source_duplicates(jobs):
    seen_keys = set()
    unique_jobs = []
    for job in jobs:
        key = job.get("dedup_key")
        if key and key in seen_keys:
            continue
        seen_keys.add(key)
        unique_jobs.append(job)
    return unique_jobs

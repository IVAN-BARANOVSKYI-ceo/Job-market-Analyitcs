from bs4 import BeautifulSoup

def remove_duplicates(jobs):
    seen_slug = set()
    unique_jobs = []
    for job in jobs:
        slug = job.get("slug")
        if slug and slug not in seen_slug:
            seen_slug.add(slug)
            unique_jobs.append(job)
    return unique_jobs


def remove_empty_jobs(jobs):
    valid_jobs = []
    for job in jobs:
        if all(job.get(field) for field in ["slug", "title", "company_name", "location"]):
            valid_jobs.append(job)
    return valid_jobs


def clean_html_content(html_content):
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def clean_html_jobs(jobs):
    no_html_jobs = []
    for job in jobs:
        job_description = job.get("description")
        job["description"] = clean_html_content(job_description)
        no_html_jobs.append(job)
    return no_html_jobs

def clean_jobs(jobs):
    cleaned_jobs = remove_duplicates(jobs)
    cleaned_jobs = remove_empty_jobs(cleaned_jobs)
    cleaned_jobs = clean_html_jobs(cleaned_jobs)
    return cleaned_jobs

if __name__ == "__main__":
    test_jobs = [
        {
            "slug": "python-developer",
            "title": "Python Developer",
            "company_name": "Google",
            "location": "Germany",
            "description": "<p>Looking for <b>Python</b> developer</p>"
        },
        {
            "slug": "python-developer",
            "title": "Python Developer",
            "company_name": "Google",
            "location": "Germany",
            "description": "Duplicate job"
        },
        {
            "slug": "data-analyst",
            "title": "",
            "company_name": "Company",
            "location": "France",
            "description": "Some description"
        },
        {
            "slug": "sql-analyst",
            "title": "SQL Analyst",
            "company_name": "Microsoft",
            "location": "Poland",
            "description": "<p>Experience with <b>SQL</b></p>"
        }
    ]

    result = clean_jobs(test_jobs)
    print(result)
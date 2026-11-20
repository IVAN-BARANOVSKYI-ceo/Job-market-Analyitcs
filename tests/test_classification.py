from src.processing.classification import classify_job, detect_seniority, extract_skills


def test_seniority():
    assert detect_seniority("Senior Python Developer (m/w/d)") == "Senior"
    assert detect_seniority("Junior Data Analyst") == "Junior"
    assert detect_seniority("Praktikum Marketing") == "Internship"
    assert detect_seniority("Head of Engineering") == "Lead"
    assert detect_seniority("Software Engineer") == "Unknown"
    assert detect_seniority("Mid-Market Sales Manager") == "Unknown"


def test_classify_by_title():
    assert classify_job("Senior Data Analyst") == ("Data & Analytics", "Data Analyst", "Technology", "title")
    assert classify_job("Marketing Manager")[2] == "Non-Technology"
    assert classify_job("Backend Developer")[1] == "Backend Developer"


def test_classify_falls_back_to_tags():
    assert classify_job("Rockstar wanted", ["python", "backend"])[3] == "tags"


def test_classify_unknown():
    assert classify_job("Rockstar wanted", []) == ("Unclassified", "Unclassified", "Unknown", "none")


def test_extract_skills():
    skills = dict(extract_skills("Python dev", ["sql"], "We use C++, JavaScript, Node.js and PostgreSQL. Excellent team."))
    assert {"Python", "SQL", "C++", "JavaScript", "Node.js", "PostgreSQL"} <= set(skills)
    assert "Java" not in skills
    assert "Excel" not in skills
    assert skills["PostgreSQL"] == "database"

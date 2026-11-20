import re

# Seniority rules, checked in order against the job title only
SENIORITY_RULES = [
    ("Internship", r"\b(intern|internship|praktikum|praktikant(in)?|werkstudent(in)?|working student)\b"),
    ("Junior", r"\b(junior|jr|entry[- ]level|graduate|trainee|apprentice|ausbildung|azubi)\b"),
    ("Lead", r"\b(lead(?! generation)|principal|head of|director|chief|vp)\b"),
    ("Senior", r"\b(senior|sr|experienced)\b"),
    ("Mid", r"\b(mid[- ]level|intermediate|mid(?![- ]market))\b"),
]

# (job_category, job_role, regex), checked in order; first match wins
ROLE_RULES = [
    ("Data & Analytics", "Data Scientist", r"data scien|machine learning|\bml\b|\bai engineer|\bnlp\b|computer vision"),
    ("Data & Analytics", "Data Engineer", r"data engineer|\betl\b|analytics engineer|big data"),
    ("Data & Analytics", "Data Analyst", r"data analy|business analy|bi analy|\bbi\b|analytics|business intelligence"),
    ("IT Operations & Security", "Security Engineer", r"security|cyber|penetration|soc analyst"),
    ("Software Development", "DevOps / Cloud Engineer", r"devops|\bsre\b|site reliability|cloud engineer|platform engineer|infrastructure engineer|kubernetes"),
    ("Software Development", "QA / Test Engineer", r"\bqa\b|test engineer|quality assurance|\btester\b|sdet"),
    ("Software Development", "Mobile Developer", r"\bios\b|android|mobile developer|flutter|react native"),
    ("Software Development", "Full-Stack Developer", r"full[- ]?stack"),
    ("Software Development", "Frontend Developer", r"front[- ]?end|\breact\b|angular|\bvue\b"),
    ("Software Development", "Backend Developer", r"back[- ]?end|\bphp\b|laravel|\bjava\b|python|\.net\b|golang|\bruby\b|\bnode"),
    ("Software Development", "Software Engineer", r"software|developer|entwickler|programm"),
    ("IT Operations & Security", "IT Support / Administrator", r"it support|system administrator|sysadmin|helpdesk|it administrator|network (engineer|admin)"),
    ("Product & Design", "Product Manager", r"product (manager|owner)|product management"),
    ("Product & Design", "Designer", r"designer|\bux\b|\bui\b|graphic"),
    ("Project Management", "Project Manager", r"project manager|scrum master|program manager"),
    ("Marketing", "Marketing", r"marketing|\bseo\b|\bsem\b|content|social media|brand|growth|communications"),
    ("Sales", "Sales", r"sales|account executive|business development|account manager|vertrieb"),
    ("Customer Support", "Customer Support", r"customer (support|service|success)|support specialist|kundenservice|call center"),
    ("Finance & Accounting", "Finance / Accounting", r"financ|accountant|accounting|controller|buchhalt|bookkeep|auditor|\btax\b"),
    ("HR & Recruiting", "HR / Recruiter", r"\bhr\b|human resources|recruit|talent|people (partner|operations)|personalreferent"),
    ("Healthcare", "Healthcare", r"nurse|pflege|doctor|arzt|physician|medical|clinic|therap|pharma"),
    ("Logistics & Operations", "Logistics / Operations", r"logistic|warehouse|driver|fahrer|supply chain|lager|courier|operations"),
    ("Engineering", "Engineer (non-software)", r"mechanical|electrical|civil|mechatronic|industrial engineer|maschinenbau|elektro|production|manufactur"),
    ("Legal", "Legal", r"legal|lawyer|jurist|paralegal|compliance|attorney"),
    ("Education", "Education", r"teacher|lehrer|tutor|trainer|educator|lecturer"),
    ("Hospitality & Retail", "Hospitality / Retail", r"\bchef\b|\bcook\b|\bkoch\b|waiter|retail|cashier|hotel|restaurant|barista|verkäufer"),
    ("Administration", "Administration", r"administrat|assistant|secretary|office manager|sachbearbeiter|receptionist"),
]

# Job categories treated as the technology sector
TECH_CATEGORIES = {"Data & Analytics", "Software Development", "IT Operations & Security"}

_SENIORITY = [(name, re.compile(rx, re.I)) for name, rx in SENIORITY_RULES]
_ROLES = [(cat, role, re.compile(rx, re.I)) for cat, role, rx in ROLE_RULES]


# Detect seniority from the job title (Unknown if no signal)
def detect_seniority(title):
    for name, pattern in _SENIORITY:
        if pattern.search(title or ""):
            return name
    return "Unknown"


# Classify a job by title, then by tags; returns category, role, industry, method
def classify_job(title, tags=None):
    for text, method in ((title or "", "title"), (" ".join(tags or []), "tags")):
        for category, role, pattern in _ROLES:
            if text and pattern.search(text):
                industry = "Technology" if category in TECH_CATEGORIES else "Non-Technology"
                return category, role, industry, method
    return "Unclassified", "Unclassified", "Unknown", "none"


# Skill name -> (category, search terms); matched case-insensitively
SKILLS = {
    "Python": ("language", ["python"]),
    "Java": ("language", ["java"]),
    "JavaScript": ("language", ["javascript"]),
    "TypeScript": ("language", ["typescript"]),
    "C#": ("language", ["c#"]),
    "C++": ("language", ["c++"]),
    "PHP": ("language", ["php"]),
    "Go": ("language", ["golang"]),
    "Rust": ("language", ["rust"]),
    "Kotlin": ("language", ["kotlin"]),
    "Swift": ("language", ["swift"]),
    "Ruby": ("language", ["ruby"]),
    "Scala": ("language", ["scala"]),
    "SQL": ("language", ["sql"]),
    "React": ("framework", ["react", "reactjs", "react.js"]),
    "Angular": ("framework", ["angular"]),
    "Vue": ("framework", ["vue", "vue.js", "vuejs"]),
    "Node.js": ("framework", ["node.js", "nodejs"]),
    "Django": ("framework", ["django"]),
    "Flask": ("framework", ["flask"]),
    "FastAPI": ("framework", ["fastapi"]),
    "Spring": ("framework", ["spring boot"]),
    "Laravel": ("framework", ["laravel"]),
    ".NET": ("framework", [".net"]),
    "PostgreSQL": ("database", ["postgresql", "postgres"]),
    "MySQL": ("database", ["mysql"]),
    "MongoDB": ("database", ["mongodb"]),
    "Redis": ("database", ["redis"]),
    "Elasticsearch": ("database", ["elasticsearch"]),
    "Snowflake": ("database", ["snowflake"]),
    "BigQuery": ("database", ["bigquery"]),
    "AWS": ("cloud & devops", ["aws", "amazon web services"]),
    "Azure": ("cloud & devops", ["azure"]),
    "GCP": ("cloud & devops", ["gcp", "google cloud"]),
    "Docker": ("cloud & devops", ["docker"]),
    "Kubernetes": ("cloud & devops", ["kubernetes", "k8s"]),
    "Terraform": ("cloud & devops", ["terraform"]),
    "Jenkins": ("cloud & devops", ["jenkins"]),
    "CI/CD": ("cloud & devops", ["ci/cd"]),
    "Git": ("cloud & devops", ["git"]),
    "Linux": ("cloud & devops", ["linux"]),
    "Spark": ("data & ml", ["apache spark", "pyspark"]),
    "Airflow": ("data & ml", ["airflow"]),
    "dbt": ("data & ml", ["dbt"]),
    "Kafka": ("data & ml", ["kafka"]),
    "pandas": ("data & ml", ["pandas"]),
    "TensorFlow": ("data & ml", ["tensorflow"]),
    "PyTorch": ("data & ml", ["pytorch"]),
    "scikit-learn": ("data & ml", ["scikit-learn", "sklearn"]),
    "Tableau": ("bi & analytics", ["tableau"]),
    "Power BI": ("bi & analytics", ["power bi", "powerbi"]),
    "Looker": ("bi & analytics", ["looker"]),
    "Excel": ("bi & analytics", ["excel"]),
}

_SKILL_PATTERNS = {
    name: re.compile(
        "|".join(rf"(?<![\w+#]){re.escape(term)}(?![\w+#])" for term in terms), re.I
    )
    for name, (_, terms) in SKILLS.items()
}


# Find known technologies in title, tags and description; returns (name, category) pairs
def extract_skills(title, tags, description):
    text = " ".join([title or "", " ".join(tags or []), description or ""])
    return [
        (name, SKILLS[name][0])
        for name, pattern in _SKILL_PATTERNS.items()
        if pattern.search(text)
    ]

import re
from datetime import datetime, timezone

# Canonical country name -> ISO code (European countries)
COUNTRY_CODES = {
    "Albania": "AL", "Austria": "AT", "Belgium": "BE", "Bosnia and Herzegovina": "BA",
    "Bulgaria": "BG", "Croatia": "HR", "Cyprus": "CY", "Czech Republic": "CZ",
    "Denmark": "DK", "Estonia": "EE", "Finland": "FI", "France": "FR", "Germany": "DE",
    "Greece": "GR", "Hungary": "HU", "Iceland": "IS", "Ireland": "IE", "Italy": "IT",
    "Latvia": "LV", "Lithuania": "LT", "Luxembourg": "LU", "Malta": "MT",
    "Netherlands": "NL", "North Macedonia": "MK", "Norway": "NO", "Poland": "PL",
    "Portugal": "PT", "Romania": "RO", "Serbia": "RS", "Slovakia": "SK",
    "Slovenia": "SI", "Spain": "ES", "Sweden": "SE", "Switzerland": "CH",
    "Ukraine": "UA", "United Kingdom": "GB",
}

# Lowercase spelling -> canonical country name
COUNTRY_ALIASES = {name.lower(): name for name in COUNTRY_CODES}
COUNTRY_ALIASES.update({
    "deutschland": "Germany", "österreich": "Austria", "schweiz": "Switzerland",
    "uk": "United Kingdom", "great britain": "United Kingdom", "england": "United Kingdom",
    "czechia": "Czech Republic", "holland": "Netherlands", "the netherlands": "Netherlands",
    "españa": "Spain", "italia": "Italy", "polska": "Poland", "lietuva": "Lithuania",
})

# Lowercase city spelling -> (canonical city, country)
CITIES = {
    "berlin": ("Berlin", "Germany"), "munich": ("Munich", "Germany"),
    "münchen": ("Munich", "Germany"), "hamburg": ("Hamburg", "Germany"),
    "frankfurt": ("Frankfurt", "Germany"), "frankfurt am main": ("Frankfurt", "Germany"),
    "cologne": ("Cologne", "Germany"), "köln": ("Cologne", "Germany"),
    "stuttgart": ("Stuttgart", "Germany"), "düsseldorf": ("Düsseldorf", "Germany"),
    "dusseldorf": ("Düsseldorf", "Germany"), "leipzig": ("Leipzig", "Germany"),
    "dresden": ("Dresden", "Germany"), "hannover": ("Hannover", "Germany"),
    "nuremberg": ("Nuremberg", "Germany"), "nürnberg": ("Nuremberg", "Germany"),
    "bremen": ("Bremen", "Germany"), "dortmund": ("Dortmund", "Germany"),
    "essen": ("Essen", "Germany"), "karlsruhe": ("Karlsruhe", "Germany"),
    "mannheim": ("Mannheim", "Germany"), "bonn": ("Bonn", "Germany"),
    "potsdam": ("Potsdam", "Germany"), "heidelberg": ("Heidelberg", "Germany"),
    "vienna": ("Vienna", "Austria"), "wien": ("Vienna", "Austria"),
    "graz": ("Graz", "Austria"), "salzburg": ("Salzburg", "Austria"),
    "linz": ("Linz", "Austria"), "zurich": ("Zurich", "Switzerland"),
    "zürich": ("Zurich", "Switzerland"), "geneva": ("Geneva", "Switzerland"),
    "basel": ("Basel", "Switzerland"), "bern": ("Bern", "Switzerland"),
    "amsterdam": ("Amsterdam", "Netherlands"), "rotterdam": ("Rotterdam", "Netherlands"),
    "utrecht": ("Utrecht", "Netherlands"), "eindhoven": ("Eindhoven", "Netherlands"),
    "brussels": ("Brussels", "Belgium"), "paris": ("Paris", "France"),
    "lyon": ("Lyon", "France"), "madrid": ("Madrid", "Spain"),
    "barcelona": ("Barcelona", "Spain"), "lisbon": ("Lisbon", "Portugal"),
    "porto": ("Porto", "Portugal"), "rome": ("Rome", "Italy"), "milan": ("Milan", "Italy"),
    "dublin": ("Dublin", "Ireland"), "london": ("London", "United Kingdom"),
    "manchester": ("Manchester", "United Kingdom"), "warsaw": ("Warsaw", "Poland"),
    "krakow": ("Krakow", "Poland"), "prague": ("Prague", "Czech Republic"),
    "budapest": ("Budapest", "Hungary"), "stockholm": ("Stockholm", "Sweden"),
    "copenhagen": ("Copenhagen", "Denmark"), "oslo": ("Oslo", "Norway"),
    "helsinki": ("Helsinki", "Finland"), "tallinn": ("Tallinn", "Estonia"),
    "riga": ("Riga", "Latvia"), "vilnius": ("Vilnius", "Lithuania"),
    "kaunas": ("Kaunas", "Lithuania"), "bucharest": ("Bucharest", "Romania"),
    "athens": ("Athens", "Greece"), "luxembourg": ("Luxembourg", "Luxembourg"),
}

# Location values that name no real place
GENERIC_LOCATIONS = {
    "worldwide", "anywhere", "remote", "europe", "emea", "eu", "european union",
    "global", "home office", "homeoffice",
}


# Split a raw location into (city, country, country_code); unknown parts stay None
def parse_location(location):
    if not location:
        return None, None, None

    parts = [p.strip() for p in re.split(r"[,/|;()]", str(location)) if p.strip()]
    country = None
    city = None

    for part in parts:
        if part.lower() in COUNTRY_ALIASES:
            country = COUNTRY_ALIASES[part.lower()]

    for part in parts:
        if part.lower() in CITIES:
            city, city_country = CITIES[part.lower()]
            country = country or city_country
            break

    if city is None:
        for part in parts:
            key = part.lower()
            if key not in COUNTRY_ALIASES and key not in GENERIC_LOCATIONS:
                city = part
                break

    return city, country, COUNTRY_CODES.get(country)


# Check if a job is relevant for the European scope of the project
def is_europe_relevant(job):
    if job.get("country_code"):
        return True
    if job.get("source") == "arbeitnow":
        return True
    location = (job.get("location") or "").lower()
    return bool(re.search(r"\beurope\b|\bemea\b|\beu\b|european union", location))


# Convert a unix timestamp or ISO string to YYYY-MM-DD (None if invalid)
def normalize_date(value):
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)) or str(value).isdigit():
            moment = datetime.fromtimestamp(int(value), tz=timezone.utc)
        else:
            moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return moment.date().isoformat()
    except (ValueError, OverflowError, OSError):
        return None


# Map a raw employment type string to a standard value
def normalize_employment(raw):
    text = (raw or "").lower()
    if re.search(r"intern|praktik|working student|werkstudent", text):
        return "Internship"
    if re.search(r"part[ _-]?time|teilzeit", text):
        return "Part-time"
    if re.search(r"contract|freelance|temporary|befristet", text):
        return "Contract"
    if re.search(r"full[ _-]?time|vollzeit", text):
        return "Full-time"
    return "Unknown"


# Detect Remote / Hybrid / On-site from explicit signals only, otherwise Unknown
def detect_workplace(short_text, full_text, remote_flag=None):
    short_text = (short_text or "").lower()
    full_text = (full_text or "").lower()

    if "hybrid" in short_text or "hybrid" in full_text:
        return "Hybrid"
    if remote_flag is True or re.search(r"\bremote\b|work from home|home ?office", short_text):
        return "Remote"
    if re.search(r"on-?site|vor ort|office-based", short_text + " " + full_text):
        return "On-site"
    return "Unknown"

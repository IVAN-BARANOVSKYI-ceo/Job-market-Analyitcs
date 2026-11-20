import re

_CUR = r"(€|\$|£|\b(?:eur(?:os?)?|usd|gbp|chf)\b)"
_NUM = r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(k)?"
_RANGE = re.compile(rf"{_CUR}?\s*{_NUM}\s*(?:-|–|—|to|bis)\s*{_CUR}?\s*{_NUM}\s*{_CUR}?", re.I)
_SINGLE = re.compile(rf"{_CUR}\s*{_NUM}|{_NUM}\s*{_CUR}", re.I)
_MILLION = re.compile(r"^\s*(million|mio|mln|bn|billion)", re.I)

_SYMBOLS = {"€": "EUR", "$": "USD", "£": "GBP"}
_PERIODS = [
    ("hourly", re.compile(r"hour|\bhr\b|stunde|/h\b", re.I)),
    ("monthly", re.compile(r"month|monat|/mo\b|mtl", re.I)),
    ("yearly", re.compile(r"year|annum|\byr\b|jahr|p\.a|annual|/y\b", re.I)),
]

EMPTY = {
    "salary_min": None, "salary_max": None, "salary_currency": None,
    "salary_period": None, "salary_period_source": None, "salary_raw": None,
}


# Convert a number string such as "50.000" or "60k" to a float
def _to_number(text, k_flag):
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", text):
        value = float(re.sub(r"[.,]", "", text))
    else:
        value = float(text.replace(",", "."))
    return value * 1000 if k_flag else value


# Convert a currency symbol or code to a 3-letter code
def _currency(symbol):
    symbol = symbol.lower()
    if symbol in _SYMBOLS:
        return _SYMBOLS[symbol]
    return symbol[:3].upper()


# Extract salary range, currency and period from free text (needs a currency)
def parse_salary(text):
    if not text:
        return dict(EMPTY)
    text = str(text)

    match = _RANGE.search(text)
    if match:
        currency = match.group(1) or match.group(4) or match.group(7)
        low = _to_number(match.group(2), match.group(3))
        high = _to_number(match.group(5), match.group(6))
        if match.group(6) and not match.group(3) and low < 1000:
            low *= 1000
    else:
        match = _SINGLE.search(text)
        if not match:
            return dict(EMPTY)
        if match.group(1):
            currency, low = match.group(1), _to_number(match.group(2), match.group(3))
        else:
            currency, low = match.group(6), _to_number(match.group(4), match.group(5))
        high = low

    if not currency or _MILLION.match(text[match.end():match.end() + 12]):
        return dict(EMPTY)

    low, high = sorted((low, high))
    window = text[max(0, match.start() - 15):match.end() + 25]

    period, period_source = None, None
    for name, pattern in _PERIODS:
        if pattern.search(window):
            period, period_source = name, "explicit"
            break
    if period is None and low >= 10000:
        period, period_source = "yearly", "inferred"
    if period is None:
        return dict(EMPTY)
    if period == "yearly" and high > 1_000_000:
        return dict(EMPTY)

    return {
        "salary_min": low, "salary_max": high, "salary_currency": _currency(currency),
        "salary_period": period, "salary_period_source": period_source,
        "salary_raw": match.group(0).strip(),
    }

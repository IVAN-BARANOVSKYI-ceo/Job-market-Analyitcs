from src.processing.salary import parse_salary


def test_range_with_symbols_and_thousands_separator():
    result = parse_salary("Salary: €60.000 - €80.000 per year")
    assert (result["salary_min"], result["salary_max"]) == (60000, 80000)
    assert result["salary_currency"] == "EUR"
    assert result["salary_period"] == "yearly"
    assert result["salary_period_source"] == "explicit"


def test_k_notation_infers_yearly():
    result = parse_salary("$80k - $100k")
    assert (result["salary_min"], result["salary_max"]) == (80000, 100000)
    assert result["salary_currency"] == "USD"
    assert result["salary_period_source"] == "inferred"


def test_hourly_and_monthly_periods():
    assert parse_salary("€25 - €35 per hour")["salary_period"] == "hourly"
    assert parse_salary("€3.000 - €4.000 pro Monat")["salary_period"] == "monthly"


def test_no_currency_means_no_salary():
    assert parse_salary("70-90k")["salary_min"] is None


def test_unclear_period_is_not_stored():
    assert parse_salary("€3000 - €4000")["salary_min"] is None


def test_million_is_ignored():
    assert parse_salary("revenue of $2 - 3 million")["salary_min"] is None


def test_empty_text():
    assert parse_salary(None)["salary_min"] is None

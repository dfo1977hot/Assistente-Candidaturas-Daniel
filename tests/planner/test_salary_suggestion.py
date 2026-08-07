from acd.domain.planner.salary_suggestion import SalarySuggestion


def test_salary_creation():

    salary = SalarySuggestion(
        minimum=10000,
        recommended=12000,
        maximum=15000,
    )

    assert salary.minimum == 10000

    assert salary.recommended == 12000

    assert salary.maximum == 15000

    assert salary.currency == "BRL"

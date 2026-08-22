from acd.presentation.pages.application_page import ApplicationPage


def test_format_brl_currency() -> None:
    assert ApplicationPage._format_brl_currency(8500) == "R$ 8.500,00"
    assert ApplicationPage._format_brl_currency(15750.5) == "R$ 15.750,50"


def test_parse_brl_currency() -> None:
    assert ApplicationPage._parse_optional_number("R$ 8.500,00") == 8500.0
    assert ApplicationPage._parse_optional_number("12.000,50") == 12000.5
    assert ApplicationPage._parse_optional_number("13500.00") == 13500.0


def test_parse_empty_currency_is_none() -> None:
    assert ApplicationPage._parse_optional_number("") is None
    assert ApplicationPage._parse_optional_number("A combinar") is None

from __future__ import annotations

from acd.services.company_name_matcher import (
    find_company_name_candidate,
    normalize_company_name,
)


def test_normalizes_legal_particles_and_accents() -> None:
    assert normalize_company_name("LACTALIS DO BRASIL LTDA.") == "lactalis brasil"


def test_matches_lactalis_name_variation() -> None:
    candidate = find_company_name_candidate(
        "LACTALIS BRASIL",
        [(1, "Outra Empresa"), (2, "LACTALIS DO BRASIL")],
    )
    assert candidate is not None
    assert candidate.index == 2
    assert candidate.name == "LACTALIS DO BRASIL"
    assert candidate.exact is False


def test_prefers_literal_exact_match() -> None:
    candidate = find_company_name_candidate(
        "Lactalis Brasil",
        [(1, "LACTALIS DO BRASIL"), (2, "Lactalis Brasil")],
    )
    assert candidate is not None
    assert candidate.index == 2
    assert candidate.exact is True


def test_rejects_unrelated_company() -> None:
    candidate = find_company_name_candidate(
        "Lactalis Brasil",
        [(1, "Volkswagen do Brasil")],
    )
    assert candidate is None

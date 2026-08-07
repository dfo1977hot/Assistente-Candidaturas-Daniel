"""Tests for FieldResolverService."""

from __future__ import annotations

from acd.services.field_resolver_service import FieldResolverService


def test_exact_match() -> None:
    """Should return exact match."""

    service = FieldResolverService()

    result = service.resolve(
        "email",
        [
            "name",
            "email",
            "phone",
        ],
    )

    assert result == "email"


def test_partial_match_candidate_contains_source() -> None:
    """Should match when candidate contains source."""

    service = FieldResolverService()

    result = service.resolve(
        "email",
        [
            "candidate_email",
            "telefone",
        ],
    )

    assert result == "candidate_email"


def test_partial_match_source_contains_candidate() -> None:
    """Should match when source contains candidate."""

    service = FieldResolverService()

    result = service.resolve(
        "candidate_email",
        [
            "email",
            "phone",
        ],
    )

    assert result == "email"


def test_prefix_match() -> None:
    """Should match using prefix heuristic."""

    service = FieldResolverService()

    result = service.resolve(
        "telefone",
        [
            "tel_number",
            "email",
        ],
    )

    assert result == "tel_number"


def test_best_candidate_selected() -> None:
    """Should return the first candidate when scores are tied."""

    service = FieldResolverService()

    result = service.resolve(
        "linkedin",
        [
            "link",
            "linkedin_profile",
            "phone",
        ],
    )

    assert result == "link"


def test_no_good_match_returns_first_candidate() -> None:
    """Should return first candidate when all scores are equal."""

    service = FieldResolverService()

    result = service.resolve(
        "xyz",
        [
            "abc",
            "def",
            "ghi",
        ],
    )

    assert result == "abc"


def test_empty_candidates() -> None:
    """Should return None for empty candidates."""

    service = FieldResolverService()

    assert service.resolve("email", []) is None


def test_normalize() -> None:
    """Should normalize values."""

    service = FieldResolverService()

    assert (
        service._normalize("E-mail Principal!")
        == "emailprincipal"
    )


def test_score_exact() -> None:
    """Exact match scores 100."""

    service = FieldResolverService()

    assert service._score("email", "email") == 100


def test_score_partial() -> None:
    """Partial match scores 60."""

    service = FieldResolverService()

    assert (
        service._score(
            "email",
            "candidateemail",
        )
        == 60
    )


def test_score_prefix() -> None:
    """Prefix match scores 30."""

    service = FieldResolverService()

    assert (
        service._score(
            "telefone",
            "telnumber",
        )
        == 30
    )


def test_score_none() -> None:
    """No similarity scores zero."""

    service = FieldResolverService()

    assert (
        service._score(
            "email",
            "phone",
        )
        == 0
    )
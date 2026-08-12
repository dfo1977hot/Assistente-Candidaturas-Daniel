from acd.services.recruiter_email_research_service import RecruiterEmailResearchService


def test_recruiter_email_parser_accepts_public_email() -> None:
    raw = '{"email":"talentos@empresa.com.br"}'
    assert (
        RecruiterEmailResearchService._extract_email_from_response(raw)
        == "talentos@empresa.com.br"
    )


def test_recruiter_email_parser_rejects_noreply() -> None:
    raw = '{"email":"noreply@empresa.com.br"}'
    assert RecruiterEmailResearchService._extract_email_from_response(raw) == ""

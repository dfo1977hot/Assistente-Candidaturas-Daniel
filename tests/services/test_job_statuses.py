from __future__ import annotations

import pytest

from acd.services.job_service import JobService


@pytest.mark.parametrize("status", JobService.JOB_STATUSES)
def test_all_visible_job_statuses_are_valid(status: str) -> None:
    JobService()._validate_status(status)


def test_unknown_job_status_is_rejected() -> None:
    with pytest.raises(ValueError, match="Status inválido"):
        JobService()._validate_status("Status inexistente")

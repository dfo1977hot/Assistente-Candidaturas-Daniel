from acd.infrastructure.linkedin.linkedin_saved_jobs_browser import (
    LOGIN_URL,
    LinkedInSavedJobsBrowser,
    SavedLinkedInJob,
)


def _job(job_id: str) -> SavedLinkedInJob:
    return SavedLinkedInJob(
        f"https://www.linkedin.com/jobs/view/{job_id}/",
        job_id,
        f"Cargo {job_id}",
        "Acme",
        "São Paulo, SP",
    )


class PaginatedBrowser(LinkedInSavedJobsBrowser):
    def __init__(self, pages):
        super().__init__(maximum_pages=50)
        self.pages = pages
        self.index = 0

    def _collect_current_page(self, _page, *, cancellation_requested):
        self._raise_if_cancelled(cancellation_requested)
        return self.pages[self.index]

    def _advance_to_next_page(
        self,
        _page,
        *,
        current_signature,
        cancellation_requested,
    ):
        self._raise_if_cancelled(cancellation_requested)
        assert current_signature == self._jobs_signature(self.pages[self.index])
        if self.index + 1 >= len(self.pages):
            return False
        self.index += 1
        return True


def test_job_id_is_extracted_from_linkedin_url() -> None:
    assert LinkedInSavedJobsBrowser._job_id(
        "https://www.linkedin.com/jobs/view/sample-1234567890/"
    ) == "1234567890"


def test_login_url_redirects_back_to_tracker() -> None:
    assert "session_redirect=" in LOGIN_URL
    assert "%2Fjobs-tracker%2F" in LOGIN_URL


def test_collect_all_follows_every_page_and_deduplicates_jobs() -> None:
    browser = PaginatedBrowser(
        [
            [_job("1234567"), _job("2345678")],
            [_job("2345678"), _job("3456789")],
            [_job("4567890")],
        ]
    )
    messages: list[str] = []

    jobs = browser._collect_all(
        object(),
        cancellation_requested=None,
        status_callback=messages.append,
    )

    assert [job.linkedin_job_id for job in jobs] == [
        "1234567",
        "2345678",
        "3456789",
        "4567890",
    ]
    assert messages[-1] == "Página 3: 4 vaga(s) salva(s) encontrada(s)..."


def test_collect_all_stops_when_linkedin_repeats_the_same_page() -> None:
    browser = PaginatedBrowser(
        [
            [_job("1234567")],
            [_job("1234567")],
            [_job("2345678")],
        ]
    )

    jobs = browser._collect_all(
        object(),
        cancellation_requested=None,
        status_callback=None,
    )

    assert [job.linkedin_job_id for job in jobs] == ["1234567"]
    assert browser.index == 1

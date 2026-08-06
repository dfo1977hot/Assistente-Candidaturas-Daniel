from acd.presentation.pages.company_lookup_worker import CompanyLookupWorker
from acd.services.company_lookup_service import CompanyLookupResult


def test_worker_emits_results(monkeypatch, qtbot) -> None:
    expected = [CompanyLookupResult(name="Acme")]

    def fake_search(self, name, *, force_refresh=False):
        assert name == "Acme"
        assert force_refresh is True
        return expected

    monkeypatch.setattr(
        "acd.presentation.pages.company_lookup_worker.CompanyLookupService.search",
        fake_search,
    )
    worker = CompanyLookupWorker(
        name="Acme",
        provider_name="openai",
        force_refresh=True,
    )

    with qtbot.waitSignal(worker.succeeded) as blocker:
        worker.run()

    assert blocker.args == [expected]

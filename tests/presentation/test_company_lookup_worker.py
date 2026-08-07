from __future__ import annotations

from acd.presentation.pages.company_lookup_worker import CompanyLookupWorker
from acd.services.company_lookup_service import CompanyLookupResult


class FakeCompanyLookupGateway:
    def __init__(self, results: list[CompanyLookupResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, bool]] = []

    def search(
        self,
        name: str,
        *,
        force_refresh: bool = False,
    ) -> list[CompanyLookupResult]:
        self.calls.append((name, force_refresh))
        return self.results


def test_worker_emits_results(qtbot) -> None:
    expected = [CompanyLookupResult(name="Acme")]
    gateway = FakeCompanyLookupGateway(expected)
    factory_calls: list[str] = []

    def service_factory(provider_name: str) -> FakeCompanyLookupGateway:
        factory_calls.append(provider_name)
        return gateway

    worker = CompanyLookupWorker(
        service_factory=service_factory,
        name="Acme",
        provider_name="openai",
        force_refresh=True,
    )

    results: list[list[CompanyLookupResult]] = []
    worker.succeeded.connect(results.append)

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    assert factory_calls == ["openai"]
    assert gateway.calls == [("Acme", True)]
    assert results == [expected]


def test_worker_emits_failure(qtbot) -> None:
    class FailingGateway:
        def search(
            self,
            name: str,
            *,
            force_refresh: bool = False,
        ) -> list[CompanyLookupResult]:
            raise RuntimeError("provider failure")

    worker = CompanyLookupWorker(
        service_factory=lambda _provider_name: FailingGateway(),
        name="Acme",
        provider_name="openai",
        force_refresh=False,
    )

    failures: list[str] = []
    worker.failed.connect(failures.append)

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    assert failures == ["Não foi possível concluir a busca de empresas."]

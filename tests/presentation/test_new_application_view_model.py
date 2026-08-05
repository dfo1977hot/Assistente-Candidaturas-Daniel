from acd.presentation.pages.new_application_view_model import (
    NewApplicationViewModel,
)


def test_start_application_updates_snapshot() -> None:
    vm = NewApplicationViewModel()

    snapshot = vm.start_application(
        company_name="OpenAI",
        job_title="Software Engineer",
        job_description="Develop AI systems.",
    )

    assert snapshot.company_name == "OpenAI"
    assert snapshot.job_title == "Software Engineer"
    assert snapshot.job_description == "Develop AI systems."


def test_clear_snapshot() -> None:
    vm = NewApplicationViewModel()

    vm.start_application(
        company_name="OpenAI",
        job_title="Engineer",
        job_description="Description",
    )

    snapshot = vm.clear()

    assert snapshot.company_name == ""
    assert snapshot.job_title == ""
    assert snapshot.job_description == ""


def test_set_company_name() -> None:
    vm = NewApplicationViewModel()

    vm.set_company_name(" OpenAI ")

    assert vm.company_name == "OpenAI"
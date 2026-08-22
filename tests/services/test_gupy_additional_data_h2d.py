from __future__ import annotations

from acd.infrastructure.application_automation.playwright_application_browser import (
    GupyApplicationStage,
    PlaywrightApplicationBrowser,
)


class _Locator:
    def __init__(
        self,
        *,
        text: str = "",
        visible: bool = True,
        value: str = "",
        selectable: bool = False,
    ) -> None:
        self.text = text
        self.visible = visible
        self.value = value
        self.selectable = selectable
        self.clicked = False
        self.selected_label = ""

    @property
    def first(self) -> _Locator:
        return self

    def count(self) -> int:
        return 1 if self.visible else 0

    def is_visible(self) -> bool:
        return self.visible

    def inner_text(self) -> str:
        return self.text

    def input_value(self) -> str:
        return self.value

    def click(self, **_kwargs: object) -> None:
        self.clicked = True

    def select_option(self, *, label: str) -> None:
        if not self.selectable:
            raise RuntimeError("not a native select")
        self.selected_label = label
        self.value = label


class _Page:
    def __init__(self, body_text: str) -> None:
        self.url = "https://tenant.gupy.io/candidates/applications/1/steps/2/curriculum"
        self.body = _Locator(text=body_text)
        self.combobox = _Locator(visible=False)
        self.options: dict[str, _Locator] = {}

    def locator(self, selector: str) -> _Locator:
        if selector == "body":
            return self.body
        return _Locator(visible=False)

    def get_by_role(
        self,
        role: str,
        *,
        name: object,
        exact: bool | None = None,
    ) -> _Locator:
        del exact
        if role == "combobox":
            return self.combobox
        if role == "option":
            return self.options.get(str(name), _Locator(visible=False))
        return _Locator(visible=False)

    def get_by_label(self, _name: object) -> _Locator:
        return self.combobox


def test_source_label_maps_linkedin() -> None:
    assert (
        PlaywrightApplicationBrowser._gupy_source_label(
            "https://www.linkedin.com/jobs/view/123"
        )
        == "LinkedIn"
    )


def test_source_label_does_not_guess_unknown_source() -> None:
    assert (
        PlaywrightApplicationBrowser._gupy_source_label(
            "https://example.com/jobs/123"
        )
        == ""
    )


def test_additional_data_fills_only_known_source_channel_native_select() -> None:
    page = _Page("Dados adicionais")
    page.combobox = _Locator(selectable=True)

    changed = PlaywrightApplicationBrowser._fill_gupy_source_channel(
        page,
        "https://www.linkedin.com/jobs/view/123",
    )

    assert changed
    assert page.combobox.selected_label == "LinkedIn"


def test_additional_data_does_not_touch_unknown_source() -> None:
    page = _Page("Dados adicionais")
    page.combobox = _Locator(selectable=True)

    changed = PlaywrightApplicationBrowser._fill_gupy_source_channel(
        page,
        "https://unknown.example/jobs/123",
    )

    assert not changed
    assert page.combobox.selected_label == ""


def test_referral_and_current_employment_require_manual_confirmation() -> None:
    page = _Page(
        "Dados adicionais\n"
        "Alguém que trabalha nesta empresa indicou você para esta vaga?\n"
        "Você trabalha na empresa Lojas Renner S.A.?"
    )

    pending = PlaywrightApplicationBrowser._gupy_additional_data_manual_items(page)

    assert pending == (
        "indicação por colaborador",
        "vínculo atual com a empresa",
    )


def test_post_auth_additional_data_reports_manual_items_and_source_fill() -> None:
    page = _Page(
        "Dados adicionais\n"
        "Alguém que trabalha nesta empresa indicou você para esta vaga?\n"
        "Você trabalha na empresa Lojas Renner S.A.?"
    )
    page.combobox = _Locator(selectable=True)
    progress: list[object] = []

    returned = PlaywrightApplicationBrowser._prepare_gupy_post_auth(
        page,
        progress.append,
        source_url="https://www.linkedin.com/jobs/view/123",
    )

    assert returned is page
    assert (
        PlaywrightApplicationBrowser._gupy_application_stage(page)
        is GupyApplicationStage.ADDITIONAL_DATA
    )
    assert page.combobox.selected_label == "LinkedIn"
    assert any("Origem da vaga preenchida" in str(item) for item in progress)
    assert any("Confirmação manual necessária" in str(item) for item in progress)

from __future__ import annotations


class WizardNavigator:
    """
    Controla a navegação entre as páginas do ApplicationWizard.
    """

    def __init__(self) -> None:
        self._current_index = 0
        self._page_count = 0

    @property
    def current_index(self) -> int:
        return self._current_index

    @property
    def page_count(self) -> int:
        return self._page_count

    def configure(self, page_count: int) -> None:
        if page_count < 0:
            raise ValueError("page_count must be non-negative")

        self._page_count = page_count

        if self._current_index >= page_count:
            self._current_index = max(0, page_count - 1)

    def can_go_next(self) -> bool:
        return self._current_index < self._page_count - 1

    def can_go_previous(self) -> bool:
        return self._current_index > 0

    def next(self) -> int:
        if self.can_go_next():
            self._current_index += 1

        return self._current_index

    def previous(self) -> int:
        if self.can_go_previous():
            self._current_index -= 1

        return self._current_index

    def go_to(self, index: int) -> int:
        if not 0 <= index < self._page_count:
            raise IndexError(index)

        self._current_index = index

        return self._current_index

    def reset(self) -> None:
        self._current_index = 0
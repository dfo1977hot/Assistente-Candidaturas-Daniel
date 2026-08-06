from acd.desktop_composition_root import DesktopCompositionRoot


def test_runtime_pages_are_composed_by_the_desktop_root(qapp):
    window = DesktopCompositionRoot().build_main_window()

    for page in window.router.pages.values():
        assert page is not None
        assert hasattr(page, "layout")

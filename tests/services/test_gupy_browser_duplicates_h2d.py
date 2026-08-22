from __future__ import annotations

import ast
from pathlib import Path

SOURCE_PATH = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
)


def _source() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def _browser() -> ast.ClassDef:
    tree = ast.parse(_source())
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "PlaywrightApplicationBrowser"
    )


def test_browser_has_no_duplicate_methods() -> None:
    names = [
        node.name
        for node in _browser().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    duplicates = sorted(
        name
        for name in set(names)
        if names.count(name) > 1
    )
    assert duplicates == []


def test_gupy_uses_exact_passwordless_button() -> None:
    source = _source()

    assert 'page.locator("#passwordlessSignin")' in source
    assert "_try_gupy_password_login" not in source
    assert "_fill_gupy_password_login" not in source
    assert "_configured_login_for_gupy_page" not in source


def test_gupy_keeps_imap_magic_link_flow() -> None:
    source = _source()

    assert "self.magic_link_service.wait_for_link(" in source
    assert "TerraImapGupyMagicLinkService" in source
    assert "OutlookGupyMagicLinkService" not in source

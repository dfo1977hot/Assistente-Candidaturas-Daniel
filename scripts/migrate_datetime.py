from __future__ import annotations

from pathlib import Path
import re

PROJECT = Path(__file__).resolve().parents[1]

FILES = list(PROJECT.rglob("*.py"))

IMPORT = "from acd.core.datetime_utils import utc_now"


def process(file: Path) -> bool:
    """
    Migra automaticamente datetime.utcnow para utc_now
    nos modelos SQLAlchemy.
    """

    # Nunca alterar o próprio utilitário
    if file.name == "datetime_utils.py":
        return False

    text = file.read_text(encoding="utf-8")
    original = text

    # Não há nada para migrar
    if "datetime.utcnow" not in text:
        return False

    # ------------------------------------------------------------------
    # Substituições
    # ------------------------------------------------------------------

    text = text.replace(
        "default=utc_now",
        "default=utc_now",
    )

    text = text.replace(
        "onupdate=utc_now",
        "onupdate=utc_now",
    )

    # ------------------------------------------------------------------
    # Adiciona o import somente se necessário
    # ------------------------------------------------------------------

    if "utc_now" in text and IMPORT not in text:
        imports = re.search(
            r"((?:from .* import .*\n|import .*\n)+)",
            text,
        )

        if imports:
            pos = imports.end()
            text = text[:pos] + IMPORT + "\n" + text[pos:]
        else:
            text = IMPORT + "\n\n" + text

    # ------------------------------------------------------------------

    if text != original:
        file.write_text(text, encoding="utf-8")
        return True

    return False


count = 0

for py in FILES:
    if process(py):
        count += 1
        print("OK", py.relative_to(PROJECT))

print()
print("--------------------------------")
print(f"Arquivos modificados: {count}")
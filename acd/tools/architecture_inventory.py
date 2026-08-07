from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------
# Arquivos
# --------------------------------------------------------


def python_files() -> list[Path]:
    return list(PROJECT_ROOT.rglob("*.py"))


def count_python_files() -> int:
    return len(python_files())


def count_lines() -> int:
    total = 0

    for file in python_files():
        try:
            with file.open(encoding="utf-8") as f:
                total += sum(1 for _ in f)
        except UnicodeDecodeError:
            pass

    return total


def count_folder(folder: str) -> int:
    """
    Conta quantos arquivos .py existem dentro de uma pasta.
    """

    path = PROJECT_ROOT / folder

    if not path.exists():
        return 0

    return len(list(path.rglob("*.py")))


# --------------------------------------------------------
# AST
# --------------------------------------------------------


def analyze_python_file(path: Path) -> dict:

    result = {
        "classes": 0,
        "functions": 0,
        "methods": 0,
        "imports": [],
    }

    try:

        tree = ast.parse(path.read_text(encoding="utf-8"))

    except Exception:

        return result

    for node in ast.walk(tree):

        if isinstance(node, ast.ClassDef):
            result["classes"] += 1

            for child in node.body:

                if isinstance(child, ast.FunctionDef):
                    result["methods"] += 1

        elif isinstance(node, ast.FunctionDef):

            if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                result["functions"] += 1

        elif isinstance(node, ast.Import):

            for alias in node.names:
                result["imports"].append(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                result["imports"].append(node.module)

    return result


# --------------------------------------------------------
# Projeto
# --------------------------------------------------------


def project_metrics():

    metrics = {
        "classes": 0,
        "functions": 0,
        "methods": 0,
        "imports": set(),
    }

    for file in python_files():

        data = analyze_python_file(file)

        metrics["classes"] += data["classes"]
        metrics["functions"] += data["functions"]
        metrics["methods"] += data["methods"]

        metrics["imports"].update(data["imports"])

    return metrics


# --------------------------------------------------------
# Relatório
# --------------------------------------------------------


def print_report():

    metrics = project_metrics()

    print("=" * 65)
    print("ACD ARCHITECTURE INVENTORY")
    print("=" * 65)

    print()

    print(f"Python files ......... {count_python_files():>6}")
    print(f"Lines of code ........ {count_lines():>6}")

    print()

    print(f"Classes .............. {metrics['classes']:>6}")
    print(f"Functions ............ {metrics['functions']:>6}")
    print(f"Methods .............. {metrics['methods']:>6}")
    print(f"Imported modules ..... {len(metrics['imports']):>6}")

    print()

    print("=" * 65)


def generate_markdown_report() -> None:

    metrics = project_metrics()

    report_path = PROJECT_ROOT / "docs" / "architecture" / "ARCHITECTURE_REPORT.md"

    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = f"""# Architecture Report

Gerado automaticamente pelo ACD.

---

Data

{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

---

## Estatísticas Gerais

| Indicador | Valor |
|-----------|------:|
| Arquivos Python | {count_python_files()} |
| Linhas de Código | {count_lines()} |
| Classes | {metrics['classes']} |
| Funções | {metrics['functions']} |
| Métodos | {metrics['methods']} |
| Imports únicos | {len(metrics['imports'])} |

---

## Estrutura do Projeto

| Camada | Arquivos |
|---------|---------:|
| Presentation | {count_folder('acd/presentation')} |
| Services | {count_folder('acd/services')} |
| Repositories | {count_folder('acd/infrastructure/repositories')} |
| Domain | {count_folder('acd/domain')} |
| Tests | {count_folder('tests')} |

---

## Architecture Health

Status

🟢 Em auditoria

---

## Dívida Técnica Conhecida

- coexistência de `agent` e `agents`
- ampliar cobertura de testes
- revisar entidades sem Repository dedicado

---

## Próxima Sprint

Sprint 0.4
"""

    report_path.write_text(report, encoding="utf-8")

    print()
    print("Relatório gerado em:")
    print(report_path)


if __name__ == "__main__":
    print_report()
    generate_markdown_report()

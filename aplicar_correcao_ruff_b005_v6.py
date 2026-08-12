from __future__ import annotations

from pathlib import Path

path = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
)
text = path.read_text(encoding="utf-8")
lines = text.splitlines()

target_prefix = "                    wrapped = variant[index:end].rstrip("
replacement = '                    wrapped = variant[index:end].rstrip("\\\\")'

matches = [
    index
    for index, line in enumerate(lines)
    if line.startswith(target_prefix)
]

if len(matches) != 1:
    raise SystemExit(
        f"Esperado exatamente 1 trecho wrapped/rstrip; encontrados: {len(matches)}"
    )

index = matches[0]
old_line = lines[index]

if old_line == replacement:
    print("O arquivo já está corrigido.")
else:
    backup = path.with_suffix(".py.bak_b005_v6")
    if not backup.exists():
        backup.write_text(text, encoding="utf-8", newline="\n")

    lines[index] = replacement
    new_text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    path.write_text(new_text, encoding="utf-8", newline="\n")

    print(f"Corrigido: {path}")
    print(f"Linha antiga: {old_line}")
    print(f"Linha nova:   {replacement}")
    print(f"Backup: {backup}")

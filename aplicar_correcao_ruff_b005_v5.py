from pathlib import Path

path = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
)
text = path.read_text(encoding="utf-8")

old = '                    wrapped = variant[index:end].rstrip("\\\\")'
new = '                    wrapped = variant[index:end].rstrip("\\\\")'

# The source text representation above may be ambiguous after escaping.
# Replace the exact Python source line by matching the visible code form.
if old not in text:
    old = '                    wrapped = variant[index:end].rstrip("\\\\")'

# B005-safe version: remove trailing backslashes one character at a time.
replacement = (
    '                    wrapped = variant[index:end]\n'
    '                    while wrapped.endswith("\\\\"):\n'
    '                        wrapped = wrapped[:-1]'
)

if 'wrapped = variant[index:end].rstrip("\\\\")' not in text:
    raise SystemExit("Trecho B005 não encontrado; nenhuma alteração aplicada.")

backup = path.with_suffix(".py.bak_b005_v5")
if not backup.exists():
    backup.write_text(text, encoding="utf-8")

text = text.replace(
    '                    wrapped = variant[index:end].rstrip("\\\\")',
    replacement,
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
print(f"Corrigido: {path}")

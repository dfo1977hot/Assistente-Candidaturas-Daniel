from __future__ import annotations

from pathlib import Path
import re

path = Path("acd/services/linkedin_job_import_service.py")
if not path.exists():
    raise SystemExit(f"Arquivo não encontrado: {path}")

text = path.read_text(encoding="utf-8")
original = text

if "from acd.services.settings_service import SettingsService" not in text:
    lines = text.splitlines()
    insert_at = None
    for index, line in enumerate(lines):
        if line.startswith("from acd.security.secret_provider import "):
            insert_at = index + 1
            break
    if insert_at is None:
        for index, line in enumerate(lines):
            if line.startswith("from acd.") or line.startswith("import "):
                insert_at = index + 1
    if insert_at is None:
        raise SystemExit("Não foi possível localizar a seção de imports.")
    lines.insert(insert_at, "from acd.services.settings_service import SettingsService")
    text = "\n".join(lines) + ("\n" if original.endswith("\n") else "")

patterns = [
    r'self\._api_key\s*=\s*\(api_key\s+or\s+EnvironmentSecretProvider\(\)\.get_secret\("OPENAI_API_KEY"\)\s+or\s+""\)\.strip\(\)',
    r'self\._api_key\s*=\s*\(api_key\s+or\s+os\.getenv\("OPENAI_API_KEY",\s*""\)\)\.strip\(\)',
]
replaced = False
for pattern in patterns:
    text, count = re.subn(pattern, 'self._api_key = (api_key or "").strip()', text, count=1)
    if count:
        replaced = True
        break

if not replaced and 'self._api_key = (api_key or "").strip()' not in text:
    raise SystemExit(
        "Não foi localizado o trecho que inicializa _api_key. "
        "Nenhuma alteração foi aplicada."
    )

needle = "        normalized_url = self.normalize_linkedin_job_url(url)\n"
replacement = (
    "        normalized_url = self.normalize_linkedin_job_url(url)\n"
    "        api_key = self._api_key or SettingsService().get_api_key(\"openai\").strip()\n"
)
if replacement not in text:
    if needle not in text:
        raise SystemExit("Não foi localizado o início de import_from_url.")
    text = text.replace(needle, replacement, 1)

old_validation = (
    "        if not self._api_key:\n"
    "            raise LinkedInJobImportError(\n"
    "                \"A variável OPENAI_API_KEY não está configurada para importar a vaga.\"\n"
    "            )"
)
new_validation = (
    "        if not api_key:\n"
    "            raise LinkedInJobImportError(\n"
    "                \"A chave da OpenAI não está configurada. Cadastre e teste a chave \"\n"
    "                \"na página Configurações.\"\n"
    "            )"
)
text = text.replace(old_validation, new_validation, 1)

text = text.replace(
    '\"Authorization\": f\"Bearer {self._api_key}\",',
    '\"Authorization\": f\"Bearer {api_key}\",',
    1,
)

text = text.replace(
    'return "A chave da OpenAI foi recusada. Verifique OPENAI_API_KEY."',
    'return "A chave da OpenAI foi recusada. Verifique e teste a chave na página Configurações."',
)

if text.count("EnvironmentSecretProvider") == 1:
    text = text.replace(
        "from acd.security.secret_provider import EnvironmentSecretProvider, read_setting",
        "from acd.security.secret_provider import read_setting",
    )

if text == original:
    print("Nenhuma alteração necessária; o arquivo já parece corrigido.")
else:
    backup = path.with_suffix(".py.bak_openai_settings")
    backup.write_text(original, encoding="utf-8")
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"Corrigido: {path}")
    print(f"Backup: {backup}")

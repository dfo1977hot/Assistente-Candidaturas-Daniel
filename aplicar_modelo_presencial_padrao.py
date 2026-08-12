from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"Já corrigido: {path}")
        return
    if old not in text:
        raise SystemExit(f"Trecho esperado não encontrado em {path}:\n{old}")
    backup = path.with_suffix(path.suffix + ".bak_modelo_presencial")
    if not backup.exists():
        backup.write_text(text, encoding="utf-8")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    print(f"Corrigido: {path}")


# Importação individual do LinkedIn
path = Path("acd/services/linkedin_job_import_service.py")
replace_once(
    path,
    'work_model=cls._choice(data.get("work_model"), {"Presencial", "Híbrido", "Remoto"}),',
    'work_model=cls._choice(data.get("work_model"), {"Presencial", "Híbrido", "Remoto"}) or "Presencial",',
)

text = path.read_text(encoding="utf-8")
rule = "- Se o modelo de trabalho não puder ser determinado, use Presencial."
if rule not in text:
    marker = "- Não invente informações ausentes."
    if marker not in text:
        raise SystemExit(f"Marcador do prompt não encontrado em {path}")
    path.write_text(
        text.replace(marker, marker + "\n" + rule, 1),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Prompt atualizado: {path}")


# Importação em lote das vagas salvas
path = Path("acd/services/linkedin_saved_jobs_import_service.py")
replacements = [
    (
        "work_model=imported_job.work_model or reference.work_model,",
        'work_model=imported_job.work_model or reference.work_model or "Presencial",',
    ),
    (
        'work_model=job.work_model.strip() or "Não informado",',
        'work_model=job.work_model.strip() or "Presencial",',
    ),
    (
        "work_model=job.work_model or reference.work_model,",
        'work_model=job.work_model or reference.work_model or "Presencial",',
    ),
]
for old, new in replacements:
    replace_once(path, old, new)


# Página Vagas
path = Path("acd/presentation/pages/job_page.py")
replace_once(
    path,
    "        if result.work_model:\n"
    "            self.work_model_combo.setCurrentText(result.work_model)",
    '        self.work_model_combo.setCurrentText(result.work_model or "Presencial")',
)
replace_once(
    path,
    '        self.work_model_combo.setCurrentText(job.work_model or "")',
    '        self.work_model_combo.setCurrentText(job.work_model or "Presencial")',
)
replace_once(
    path,
    "        self.work_model_combo.setCurrentIndex(0)",
    '        self.work_model_combo.setCurrentText("Presencial")',
)

print("Correção concluída.")

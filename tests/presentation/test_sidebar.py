from pathlib import Path

from acd.desktop_composition_root import DesktopCompositionRoot


def _expected_widget(window, label: str):
    if "Dashboard" in label:
        return window.dashboard
    if "Vagas" in label:
        return window.job_page
    if "Empresas" in label:
        return window.company_page
    if "Candidaturas" in label:
        return window.application_page
    if "Entrevistas" in label:
        return window.interview_page
    if "Currículos" in label:
        return window.curriculum_page
    if "Cartas" in label:
        return window.cover_letters_page
    if "Workflow" in label:
        return window.workflow_page
    if "CRM" in label:
        return window.crm_page
    if "Análise" in label:
        return window.analytics_page
    if "Planejamento" in label or "Carreira" in label:
        return window.career_page
    if "Assistente" in label or "IA" in label:
        return window.assistant_page
    if "Agentes" in label:
        return window.agent_console_page
    if "Perfil do Candidato" in label:
        return window.candidate_profile_page
    if "Config" in label:
        return window.settings_page
    return None


def test_sidebar_navigates_all_items_without_exception(qapp, qtbot):
    window = DesktopCompositionRoot().build_main_window()
    log_path = Path("logs/functional_validation.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []

    for i in range(window.sidebar.count()):
        item = window.sidebar.item(i)
        label = item.text()
        expected = _expected_widget(window, label)

        try:
            window._on_sidebar_item_clicked(item)
            current = window.stack.currentWidget()
            assert expected is not None, f"Missing expected mapping for sidebar item: {label}"
            assert current is expected, f"Navigation mismatch for {label}"
        except Exception as exc:  # defensive logging for sprint evidence
            errors.append(f"[{label}] {type(exc).__name__}: {exc}")

    if window.dashboard._executor.is_running:
        qtbot.waitUntil(lambda: not window.dashboard._executor.is_running)

    if errors:
        with log_path.open("a", encoding="utf-8") as handle:
            for line in errors:
                handle.write(line + "\n")

    assert not errors, "Sidebar validation found navigation errors"

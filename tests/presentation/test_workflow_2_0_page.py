from pathlib import Path


def test_workflow_page_exposes_conditions_schedule_and_resume() -> None:
    source = Path("acd/presentation/pages/workflow_page.py").read_text(encoding="utf-8")
    for text in (
        "SE campo",
        "Operador",
        "SENÃO",
        "Encerrar workflow",
        "Agendado",
        "Data e hora",
        "Recorrência",
        "Status alvo",
        "Retomar workflow",
        "Retomar a partir da falha",
    ):
        assert text in source


def test_scheduler_runs_with_existing_background_executor() -> None:
    source = Path("acd/presentation/pages/workflow_page.py").read_text(encoding="utf-8")
    assert "LongRunningTaskExecutor(self)" in source
    assert "self.scheduler_service.due_schedules()" in source
    assert "self._scheduler_executor.execute(self.scheduler_service.run_due)" in source
    assert "QTimer.singleShot" not in source
    main_window = Path("acd/ui/main_window.py").read_text(encoding="utf-8")
    assert "def showEvent" in main_window
    assert 'getattr(self.workflow_page, "start_scheduler", None)' in main_window


def test_presentation_keeps_architecture_boundary() -> None:
    source = Path("acd/presentation/pages/workflow_page.py").read_text(encoding="utf-8")
    assert "acd.infrastructure" not in source
    assert "WorkflowSchedulerService()" not in source
    assert "WorkflowService()" not in source

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any
from uuid import uuid4

LogSink = Callable[[str, dict[str, Any]], None]
TelemetrySink = Callable[[dict[str, Any]], None]


@dataclass(slots=True)
class PipelineObservability:
    """Collects pipeline logs, metrics and trace records through injected sinks."""

    execution_id: str = field(default_factory=lambda: str(uuid4()))
    log_sink: LogSink | None = None
    telemetry_sink: TelemetrySink | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    _started_at: float = field(default_factory=perf_counter, init=False, repr=False)

    def record_stage(self, stage: str, duration_seconds: float, status: str) -> None:
        """Record one stage observation with the pipeline execution identifier."""

        record = {
            "execution_id": self.execution_id,
            "stage": stage,
            "duration_seconds": duration_seconds,
            "status": status,
        }
        self.trace.append(record)
        self.metrics[f"pipeline.stage.{stage}.duration_seconds"] = duration_seconds
        self._emit("pipeline.stage", record)

    def complete(self, status: str) -> None:
        """Record final duration and completion status."""

        duration_seconds = perf_counter() - self._started_at
        record = {
            "execution_id": self.execution_id,
            "status": status,
            "duration_seconds": duration_seconds,
        }
        self.trace.append(record)
        self.metrics["pipeline.total.duration_seconds"] = duration_seconds
        self._emit("pipeline.completed", record)

    def _emit(self, message: str, record: dict[str, Any]) -> None:
        if self.log_sink is not None:
            self.log_sink(message, record)
        if self.telemetry_sink is not None:
            self.telemetry_sink(record)

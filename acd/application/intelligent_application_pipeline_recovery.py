from __future__ import annotations

from typing import Any

from acd.application.intelligent_application_pipeline import (
    IntelligentApplicationPipeline,
    PipelineStageResult,
)
from acd.application.intelligent_application_pipeline_state import PipelineState


class PipelineRecovery:
    """Resumes a pipeline from a valid in-memory checkpoint."""

    def resume(
        self,
        pipeline: IntelligentApplicationPipeline,
        context: dict[str, Any],
        state: PipelineState,
    ) -> list[PipelineStageResult]:
        """Continue execution from the checkpoint boundary."""

        checkpoint = state.checkpoint
        next_stage_index = checkpoint.get("next_stage_index")
        if not isinstance(next_stage_index, int) or next_stage_index < 0:
            raise ValueError("Pipeline checkpoint is invalid.")

        context.update(checkpoint.get("partial_result", {}))
        return pipeline.run(context, start_index=next_stage_index)

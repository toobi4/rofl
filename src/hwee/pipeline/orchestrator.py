"""The Pipeline Orchestrator: topologically sorts stages by their declared data dependencies."""

from __future__ import annotations

from hwee.kernel.bus import MessageBus
from hwee.kernel.container import Container
from hwee.kernel.errors import HweeError
from hwee.kernel.plugins import REGISTRY, PluginRegistry
from hwee.kernel.telemetry import TELEMETRY
from hwee.pipeline.stage import PipelineContext, Stage


class PipelineOrchestrator:
    def __init__(self, container: Container, bus: MessageBus) -> None:
        self.container = container
        self.bus = bus

    def plan(self) -> list[Stage]:
        PluginRegistry.discover("hwee.pipeline")
        stages: list[Stage] = [self.container.construct(d.cls) for d in REGISTRY.of("stage")]
        available: set[str] = set()
        ordered: list[Stage] = []
        pending = list(stages)
        while pending:  # Kahn's algorithm, priority-stable
            ready = [s for s in pending if set(s.requires) <= available]
            if not ready:
                raise HweeError(f"Unsatisfiable stage graph: {[s.name for s in pending]}")
            stage = ready[0]
            pending.remove(stage)
            ordered.append(stage)
            available |= set(stage.produces)
        return ordered

    def run(self) -> PipelineContext:
        context = PipelineContext()
        stages = self.plan()
        for index, stage in enumerate(stages, 1):
            self.bus.publish("pipeline.stage.started", {"index": index, "name": stage.name})
            self.bus.drain()
            with TELEMETRY.span(f"stage {index:02d}/{len(stages)}: {stage.name}"):
                produced = stage.execute(context)
            if set(produced) != set(stage.produces):
                raise HweeError(f"Stage {stage.name!r} violated its contract")
            for key, value in produced.items():
                context.put(key, value, stage.name)
            self.bus.publish("pipeline.stage.completed", {"index": index, "name": stage.name})
            self.bus.drain()
        return context

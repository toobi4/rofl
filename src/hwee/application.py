"""Application bootstrap: the composition root."""

from __future__ import annotations

from pathlib import Path

from hwee.config.model import Configuration
from hwee.kernel.bus import MessageBus
from hwee.kernel.container import Container
from hwee.kernel.entropy import DeterministicEntropySource
from hwee.kernel.resources import ResourceLocator
from hwee.kernel.telemetry import TELEMETRY
from hwee.output.sink import FileDescriptorSink, OutputSink
from hwee.pipeline.orchestrator import PipelineOrchestrator
from hwee.pipeline.stage import PipelineContext

DEFAULT_CONFIG = Path(__file__).resolve().parent / "hwee.conf"


class HelloWorldEnterpriseApplication:
    def __init__(self, config: Configuration, sink: OutputSink | None = None) -> None:
        self.container = Container()
        self.container.register(Container, instance=self.container)
        self.container.register(Configuration, instance=config)
        self.container.register(MessageBus)
        self.container.register(ResourceLocator)
        self.container.register(DeterministicEntropySource, factory=lambda c: DeterministicEntropySource(
            c.resolve(Configuration).get("application.entropy_seed", int, 0x48574545)))
        self.container.register(OutputSink, instance=sink if sink is not None else FileDescriptorSink(1))
        self.container.register(PipelineOrchestrator)

    def run(self) -> PipelineContext:
        bus: MessageBus = self.container.resolve(MessageBus)
        bus.subscribe("pipeline.stage.started", lambda _t, m: TELEMETRY.incr("pipeline.stages.started"))
        bus.subscribe("pipeline.stage.completed", lambda _t, m: TELEMETRY.incr("pipeline.stages.completed"))
        with TELEMETRY.span("greeting-delivery"):
            return self.container.resolve(PipelineOrchestrator).run()

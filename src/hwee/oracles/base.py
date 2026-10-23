"""The Oracle contract and its abstract factory provider."""

from __future__ import annotations

import abc

from hwee.config.model import Configuration
from hwee.kernel.container import Container
from hwee.kernel.entropy import DeterministicEntropySource
from hwee.kernel.plugins import REGISTRY, PluginRegistry
from hwee.kernel.resources import ResourceLocator


class GlyphOracle(abc.ABC):
    plugin_name = "abstract"
    byzantine = False

    def __init__(self, resources: ResourceLocator, config: Configuration,
                 entropy: DeterministicEntropySource) -> None:
        self.resources = resources
        self.config = config
        self.entropy = entropy.fork(type(self).__name__)

    def setting(self, key: str, expected: type, default=None):
        return self.config.get(f"oracles.{self.plugin_name}.{key}", expected, default)

    def enabled(self) -> bool:
        return self.setting("enabled", bool, True)

    @abc.abstractmethod
    def divine(self) -> list[int]:
        """Return the code points of the greeting, in order."""


class AbstractGlyphOracleFactory(abc.ABC):
    @abc.abstractmethod
    def create_all(self) -> list[GlyphOracle]:
        ...


class ReflectiveGlyphOracleFactory(AbstractGlyphOracleFactory):
    PACKAGE = "hwee.oracles"

    def __init__(self, container: Container) -> None:
        self.container = container

    def create_all(self) -> list[GlyphOracle]:
        PluginRegistry.discover(self.PACKAGE)
        oracles = [self.container.construct(d.cls) for d in REGISTRY.of("oracle")]
        return [oracle for oracle in oracles if oracle.enabled()]


class GlyphOracleFactoryProvider:
    """Provides the factory that creates the oracles. Obviously."""

    def __init__(self, container: Container) -> None:
        self.container = container

    def provide(self) -> AbstractGlyphOracleFactory:
        return ReflectiveGlyphOracleFactory(self.container)

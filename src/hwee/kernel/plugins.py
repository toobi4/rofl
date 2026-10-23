"""Plugin discovery via reflective package scanning."""

from __future__ import annotations

import importlib
import pkgutil
from collections import defaultdict
from dataclasses import dataclass

from hwee.kernel.errors import PluginDiscoveryError


@dataclass(frozen=True)
class PluginDescriptor:
    category: str
    name: str
    cls: type
    priority: int


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, dict[str, PluginDescriptor]] = defaultdict(dict)

    def add(self, descriptor: PluginDescriptor) -> None:
        bucket = self._plugins[descriptor.category]
        existing = bucket.get(descriptor.name)
        if existing is not None and existing.cls is not descriptor.cls:
            raise PluginDiscoveryError(f"Duplicate plugin {descriptor.category}/{descriptor.name}")
        bucket[descriptor.name] = descriptor

    def of(self, category: str) -> list[PluginDescriptor]:
        return sorted(self._plugins[category].values(), key=lambda d: (d.priority, d.name))

    @staticmethod
    def discover(package_name: str) -> None:
        package = importlib.import_module(package_name)
        for info in pkgutil.walk_packages(package.__path__, prefix=package_name + "."):
            importlib.import_module(info.name)


REGISTRY = PluginRegistry()


def plugin(category: str, name: str, priority: int = 100):
    def decorate(cls: type) -> type:
        REGISTRY.add(PluginDescriptor(category, name, cls, priority))
        cls.plugin_name = name
        return cls
    return decorate

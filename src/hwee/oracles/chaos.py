"""Chaos Monkey Oracle: a deliberately Byzantine replica.

Kept in production to continuously prove the cluster's fault tolerance.
It is intentionally registered with the highest priority so that it becomes
the primary of view 0 and forces a view change on every boot.
"""

from __future__ import annotations

from hwee.kernel.plugins import plugin
from hwee.oracles.base import GlyphOracle


@plugin("oracle", "chaos_monkey", priority=0)
class ChaosMonkeyOracle(GlyphOracle):
    byzantine = True

    def divine(self) -> list[int]:
        length = 5 + self.entropy.below(20)
        return [33 + self.entropy.below(94) for _ in range(length)]

    def lie(self) -> int:
        return 33 + self.entropy.below(94)

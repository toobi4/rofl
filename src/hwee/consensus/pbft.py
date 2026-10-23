"""The PBFT cluster coordinator and client."""

from __future__ import annotations

from collections import Counter, defaultdict

from hwee.consensus.messages import NEW_VIEW, PRE_PREPARE, REPLY, SCHEMAS, VIEW_CHANGE, digest_of
from hwee.consensus.replica import Replica
from hwee.kernel.bus import MessageBus
from hwee.kernel.errors import ConsensusError
from hwee.kernel.telemetry import TELEMETRY


class PBFTCluster:
    def __init__(self, replicas: list[Replica], bus: MessageBus, faults: int) -> None:
        if len(replicas) < 3 * faults + 1:
            raise ConsensusError(f"{len(replicas)} replicas cannot tolerate {faults} Byzantine faults")
        self.replicas = replicas
        self.bus = bus
        self.f = faults
        self.view = 0
        self.replies: dict[tuple[int, int], dict[int, int]] = defaultdict(dict)
        self.view_votes: dict[int, set[int]] = defaultdict(set)
        for topic, schema in SCHEMAS.items():
            bus.register_schema(topic, schema)
        bus.subscribe(REPLY, self._on_reply)
        bus.subscribe(VIEW_CHANGE, self._on_view_change)
        for replica in replicas:
            replica.bind()

    def _on_reply(self, _topic: str, msg: dict) -> None:
        self.replies[(msg["view"], msg["seq"])][msg["replica"]] = msg["value"]

    def _on_view_change(self, _topic: str, msg: dict) -> None:
        self.view_votes[msg["new_view"]].add(msg["replica"])

    def primary(self) -> Replica:
        return self.replicas[self.view % len(self.replicas)]

    def agree(self, seq: int) -> tuple[int, list[str]]:
        for _ in range(len(self.replicas)):
            primary = self.primary()
            value = primary.propose(seq)
            self.bus.publish(PRE_PREPARE, {"view": self.view, "seq": seq, "value": value,
                                           "digest": digest_of(self.view, seq, value), "replica": primary.id})
            self.bus.drain()
            replies = self.replies[(self.view, seq)]
            tally = Counter(replies.values())
            if tally:
                decided, votes = tally.most_common(1)[0]
                if votes >= self.f + 1:
                    TELEMETRY.incr("consensus.decisions")
                    witnesses = [self.replicas[r].name for r, v in sorted(replies.items()) if v == decided]
                    return decided, witnesses
            self._change_view()
        raise ConsensusError(f"No agreement reached for sequence {seq}")

    def _change_view(self) -> None:
        target = self.view + 1
        TELEMETRY.log(f"    view change {self.view} -> {target} (primary {self.primary().name} suspected)")
        for replica in self.replicas:
            self.bus.publish(VIEW_CHANGE, {"new_view": target, "replica": replica.id})
        self.bus.drain()
        if len(self.view_votes[target]) < 2 * self.f + 1:
            raise ConsensusError("Insufficient view-change quorum")
        self.view = target
        for replica in self.replicas:
            replica.view = target
        self.bus.publish(NEW_VIEW, {"view": target, "replica": self.primary().id})
        self.bus.drain()
        TELEMETRY.incr("consensus.view_changes")

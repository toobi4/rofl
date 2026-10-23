"""PBFT replicas: honest and Byzantine."""

from __future__ import annotations

from collections import defaultdict

from hwee.consensus.messages import COMMIT, PRE_PREPARE, PREPARE, REPLY, digest_of
from hwee.kernel.bus import MessageBus
from hwee.kernel.entropy import DeterministicEntropySource


class Replica:
    def __init__(self, replica_id: int, name: str, values: list[int], bus: MessageBus,
                 cluster_size: int, faults: int) -> None:
        self.id = replica_id
        self.name = name
        self.values = values
        self.bus = bus
        self.n = cluster_size
        self.f = faults
        self.view = 0
        self.accepted: dict[tuple[int, int], str] = {}
        self.prepares: dict[tuple[int, int, str], set[int]] = defaultdict(set)
        self.commits: dict[tuple[int, int, str], set[int]] = defaultdict(set)
        self.sent_commit: set[tuple[int, int]] = set()
        self.committed: dict[int, int] = {}
        self.proposals: dict[tuple[int, int], int] = {}

    def bind(self) -> None:
        self.bus.subscribe(PRE_PREPARE, self.on_pre_prepare)
        self.bus.subscribe(PREPARE, self.on_prepare)
        self.bus.subscribe(COMMIT, self.on_commit)

    def local_value(self, seq: int) -> int | None:
        if seq == 0:
            return len(self.values)
        return self.values[seq - 1] if seq - 1 < len(self.values) else None

    def propose(self, seq: int) -> int:
        value = self.local_value(seq)
        return -1 if value is None else value

    # --- protocol handlers -----------------------------------------------------
    def on_pre_prepare(self, _topic: str, msg: dict) -> None:
        if msg["view"] != self.view or msg["replica"] != self.view % self.n:
            return
        key = (msg["view"], msg["seq"])
        if key in self.accepted or digest_of(msg["view"], msg["seq"], msg["value"]) != msg["digest"]:
            return
        if msg["value"] != self.local_value(msg["seq"]):
            return  # the primary is lying, or we are; either way, no PREPARE
        self.accepted[key] = msg["digest"]
        self.proposals[key] = msg["value"]
        if msg["replica"] != self.id:
            self.bus.publish(PREPARE, {"view": msg["view"], "seq": msg["seq"],
                                       "digest": msg["digest"], "replica": self.id})
        self._maybe_commit(*key)

    def on_prepare(self, _topic: str, msg: dict) -> None:
        self.prepares[(msg["view"], msg["seq"], msg["digest"])].add(msg["replica"])
        self._maybe_commit(msg["view"], msg["seq"])

    def _prepared(self, view: int, seq: int) -> bool:
        digest = self.accepted.get((view, seq))
        return digest is not None and len(self.prepares[(view, seq, digest)]) >= 2 * self.f

    def _maybe_commit(self, view: int, seq: int) -> None:
        if (view, seq) in self.sent_commit or not self._prepared(view, seq):
            return
        self.sent_commit.add((view, seq))
        self.bus.publish(COMMIT, {"view": view, "seq": seq,
                                  "digest": self.accepted[(view, seq)], "replica": self.id})

    def on_commit(self, _topic: str, msg: dict) -> None:
        key = (msg["view"], msg["seq"], msg["digest"])
        self.commits[key].add(msg["replica"])
        if (msg["seq"] not in self.committed and self._prepared(msg["view"], msg["seq"])
                and self.accepted[(msg["view"], msg["seq"])] == msg["digest"]
                and len(self.commits[key]) >= 2 * self.f + 1):
            value = self.proposals[(msg["view"], msg["seq"])]
            self.committed[msg["seq"]] = value
            self.bus.publish(REPLY, {"view": msg["view"], "seq": msg["seq"], "value": value, "replica": self.id})


class ByzantineReplica(Replica):
    """Sends conflicting garbage, never commits, and lies when it is primary."""

    def __init__(self, *args, entropy: DeterministicEntropySource, liar=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.entropy = entropy
        self.liar = liar

    def propose(self, seq: int) -> int:
        return self.liar() if self.liar else self.entropy.below(0x110000)

    def on_pre_prepare(self, _topic: str, msg: dict) -> None:
        if msg["replica"] == self.id:
            return
        forged = digest_of(msg["view"], msg["seq"], self.entropy.below(0x110000))
        self.bus.publish(PREPARE, {"view": msg["view"], "seq": msg["seq"], "digest": forged, "replica": self.id})

    def on_prepare(self, _topic: str, msg: dict) -> None:
        return

    def on_commit(self, _topic: str, msg: dict) -> None:
        return

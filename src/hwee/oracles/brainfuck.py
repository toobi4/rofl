"""Esoteric Virtualization Oracle.

Runs a Brainfuck program on a Brainfuck interpreter written in HWASM,
assembled to an HWVM object file and executed on the HWVM.
"""

from __future__ import annotations

from hwee.kernel.plugins import plugin
from hwee.kernel.telemetry import TELEMETRY
from hwee.oracles.base import GlyphOracle
from hwee.vm.assembler import assemble, from_object_file, to_object_file
from hwee.vm.machine import VirtualMachine


@plugin("oracle", "brainfuck", priority=40)
class BrainfuckVirtualizationOracle(GlyphOracle):
    INTERPRETER = "bf_interpreter.hwasm"
    PROGRAM = "greeting.bf"

    def divine(self) -> list[int]:
        object_file = to_object_file(assemble(self.resources.read_text(self.INTERPRETER)))
        TELEMETRY.gauge("vm.object_file_bytes", len(object_file))
        machine = VirtualMachine(from_object_file(object_file))
        source = [ord(ch) for ch in self.resources.read_text(self.PROGRAM)]
        machine.load_data(0, source + [0])
        return machine.run()

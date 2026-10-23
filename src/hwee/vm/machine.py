"""The HWVM execution engine."""

from __future__ import annotations

from hwee.kernel.errors import VirtualMachineFault
from hwee.kernel.telemetry import TELEMETRY
from hwee.vm.isa import Opcode


class VirtualMachine:
    MEMORY_WORDS = 1 << 16

    def __init__(self, program: list[int], step_limit: int = 50_000_000) -> None:
        self.program = program
        self.memory = [0] * self.MEMORY_WORDS
        self.stack: list[int] = []
        self.pc = 0
        self.output: list[int] = []
        self.steps = 0
        self.step_limit = step_limit
        self.halted = False

    def load_data(self, base: int, values: list[int]) -> None:
        self.memory[base:base + len(values)] = values

    def _pop(self) -> int:
        if not self.stack:
            raise VirtualMachineFault(f"Stack underflow at pc={self.pc}")
        return self.stack.pop()

    def run(self) -> list[int]:
        program, memory, stack = self.program, self.memory, self.stack
        pop = self._pop
        while not self.halted:
            if self.steps >= self.step_limit:
                raise VirtualMachineFault("Step limit exceeded; the greeting may be non-terminating")
            self.steps += 1
            op = program[self.pc]
            self.pc += 1
            if op == Opcode.PUSH:
                stack.append(program[self.pc])
                self.pc += 1
            elif op == Opcode.POP:
                pop()
            elif op == Opcode.DUP:
                value = pop()
                stack.extend((value, value))
            elif op == Opcode.SWAP:
                b, a = pop(), pop()
                stack.extend((b, a))
            elif op == Opcode.OVER:
                b, a = pop(), pop()
                stack.extend((a, b, a))
            elif op == Opcode.LOAD:
                stack.append(memory[pop()])
            elif op == Opcode.STORE:
                address = pop()
                memory[address] = pop()
            elif op == Opcode.ADD:
                b, a = pop(), pop()
                stack.append(a + b)
            elif op == Opcode.SUB:
                b, a = pop(), pop()
                stack.append(a - b)
            elif op == Opcode.MUL:
                b, a = pop(), pop()
                stack.append(a * b)
            elif op == Opcode.MOD:
                b, a = pop(), pop()
                stack.append(a % b)
            elif op == Opcode.EQ:
                b, a = pop(), pop()
                stack.append(1 if a == b else 0)
            elif op == Opcode.JMP:
                self.pc = program[self.pc]
            elif op == Opcode.JZ:
                target = program[self.pc]
                self.pc = target if pop() == 0 else self.pc + 1
            elif op == Opcode.JNZ:
                target = program[self.pc]
                self.pc = target if pop() != 0 else self.pc + 1
            elif op == Opcode.OUT:
                self.output.append(pop())
            elif op == Opcode.HALT:
                self.halted = True
            elif op == Opcode.NOP:
                pass
            else:
                raise VirtualMachineFault(f"Illegal opcode {op:#x} at pc={self.pc - 1}")
        TELEMETRY.incr("vm.instructions_retired", self.steps)
        return self.output

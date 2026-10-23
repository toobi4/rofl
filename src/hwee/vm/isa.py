"""HWVM Instruction Set Architecture, revision 7."""

from __future__ import annotations

import enum


class Opcode(enum.IntEnum):
    NOP = 0x00
    PUSH = 0x01
    POP = 0x02
    DUP = 0x03
    SWAP = 0x04
    OVER = 0x05
    LOAD = 0x10
    STORE = 0x11
    ADD = 0x20
    SUB = 0x21
    MUL = 0x22
    MOD = 0x23
    EQ = 0x24
    JMP = 0x30
    JZ = 0x31
    JNZ = 0x32
    OUT = 0x40
    HALT = 0xFF


TAKES_OPERAND = frozenset({Opcode.PUSH, Opcode.JMP, Opcode.JZ, Opcode.JNZ})
BRANCHES = frozenset({Opcode.JMP, Opcode.JZ, Opcode.JNZ})

"""Two-pass assembler for HWASM, plus the HWVM object file format.

Object file layout::

    b"HWVM" | u16 version | u32 word count | u32 crc32 | words (i32 big-endian)
"""

from __future__ import annotations

import struct

from hwee.crypto.crc32 import crc32
from hwee.kernel.errors import IntegrityError, VirtualMachineFault
from hwee.vm.isa import TAKES_OPERAND, Opcode

MAGIC = b"HWVM"
VERSION = 7


def _parse_number(token: str, constants: dict[str, int], labels: dict[str, int] | None) -> int:
    if token in constants:
        return constants[token]
    if labels is not None and token in labels:
        return labels[token]
    if token.startswith("'") and token.endswith("'") and len(token) == 3:
        return ord(token[1])
    return int(token, 0)


def assemble(source: str) -> list[int]:
    constants: dict[str, int] = {}
    labels: dict[str, int] = {}
    instructions: list[tuple[int, Opcode, str | None]] = []
    address = 0
    for line_number, raw in enumerate(source.splitlines(), 1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith(".equ"):
            _, name, value = line.split()
            constants[name] = _parse_number(value, constants, None)
            continue
        while ":" in line:
            label, line = line.split(":", 1)
            labels[label.strip()] = address
            line = line.strip()
        if not line:
            continue
        parts = line.split()
        try:
            opcode = Opcode[parts[0].upper()]
        except KeyError as exc:
            raise VirtualMachineFault(f"line {line_number}: unknown mnemonic {parts[0]!r}") from exc
        operand = parts[1] if len(parts) > 1 else None
        if (opcode in TAKES_OPERAND) != (operand is not None):
            raise VirtualMachineFault(f"line {line_number}: operand mismatch for {opcode.name}")
        instructions.append((line_number, opcode, operand))
        address += 2 if opcode in TAKES_OPERAND else 1
    words: list[int] = []
    for line_number, opcode, operand in instructions:
        words.append(int(opcode))
        if operand is not None:
            try:
                words.append(_parse_number(operand, constants, labels))
            except ValueError as exc:
                raise VirtualMachineFault(f"line {line_number}: bad operand {operand!r}") from exc
    return words


def to_object_file(words: list[int]) -> bytes:
    body = b"".join(struct.pack(">i", w) for w in words)
    return MAGIC + struct.pack(">HII", VERSION, len(words), crc32(body)) + body


def from_object_file(blob: bytes) -> list[int]:
    if blob[:4] != MAGIC:
        raise IntegrityError("Not an HWVM object file")
    version, count, checksum = struct.unpack(">HII", blob[4:14])
    if version != VERSION:
        raise IntegrityError(f"Unsupported HWVM object version {version}")
    body = blob[14:]
    if len(body) != count * 4 or crc32(body) != checksum:
        raise IntegrityError("HWVM object file checksum mismatch")
    return [struct.unpack(">i", body[i:i + 4])[0] for i in range(0, len(body), 4)]

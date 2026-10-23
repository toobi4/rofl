"""Loader for the HWFONT bitmap font format."""

from __future__ import annotations

from dataclasses import dataclass

from hwee.kernel.errors import RecognitionError

Bitmap = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class BitmapFont:
    name: str
    width: int
    height: int
    glyphs: dict[int, Bitmap]

    def glyph(self, code_point: int) -> Bitmap:
        try:
            return self.glyphs[code_point]
        except KeyError as exc:
            raise RecognitionError(f"Font {self.name!r} lacks glyph U+{code_point:04X}") from exc


def parse_font(source: str) -> BitmapFont:
    lines = iter(source.splitlines())
    if next(lines).strip() != "HWFONT 1":
        raise RecognitionError("Unsupported font format")
    name, width, height = "unnamed", 0, 0
    glyphs: dict[int, Bitmap] = {}
    for line in lines:
        line = line.strip()
        if line.startswith("NAME "):
            name = line[5:]
        elif line.startswith("SIZE "):
            width, height = map(int, line[5:].split())
        elif line.startswith("GLYPH U+"):
            code_point = int(line[8:], 16)
            rows = []
            for row in lines:
                row = row.strip()
                if row == "END":
                    break
                if len(row) != width:
                    raise RecognitionError(f"Glyph U+{code_point:04X} row has wrong width")
                rows.append(tuple(1 if c == "#" else 0 for c in row))
            if len(rows) != height:
                raise RecognitionError(f"Glyph U+{code_point:04X} has wrong height")
            glyphs[code_point] = tuple(rows)
    return BitmapFont(name, width, height, glyphs)

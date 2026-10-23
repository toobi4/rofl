"""A monochrome virtual framebuffer and text rasterizer."""

from __future__ import annotations

from hwee.kernel.entropy import DeterministicEntropySource
from hwee.render.font import BitmapFont


class Framebuffer:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.pixels = [[0] * width for _ in range(height)]

    def blit(self, bitmap, x: int, y: int) -> None:
        for dy, row in enumerate(bitmap):
            for dx, pixel in enumerate(row):
                self.pixels[y + dy][x + dx] = pixel

    def flip(self, x: int, y: int) -> None:
        self.pixels[y][x] ^= 1

    def to_ascii_art(self) -> str:
        return "\n".join("".join("█" if p else " " for p in row) for row in self.pixels)


class TextRasterizer:
    def __init__(self, font: BitmapFont, spacing: int = 1, margin: int = 1) -> None:
        self.font = font
        self.spacing = spacing
        self.margin = margin

    @property
    def pitch(self) -> int:
        return self.font.width + self.spacing

    def rasterize(self, code_points: list[int]) -> Framebuffer:
        fb = Framebuffer(2 * self.margin + len(code_points) * self.pitch,
                         2 * self.margin + self.font.height)
        for index, cp in enumerate(code_points):
            fb.blit(self.font.glyph(cp), self.margin + index * self.pitch, self.margin)
        return fb

    def degrade(self, fb: Framebuffer, cells: int, entropy: DeterministicEntropySource,
                probability: float) -> int:
        """Simulate a dusty scanner: at most one flipped pixel per glyph cell."""
        flips = 0
        for index in range(cells):
            if entropy.chance(probability):
                fb.flip(self.margin + index * self.pitch + entropy.below(self.font.width),
                        self.margin + entropy.below(self.font.height))
                flips += 1
        return flips

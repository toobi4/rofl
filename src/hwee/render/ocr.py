"""Template-matching OCR engine with Hamming-distance classification."""

from __future__ import annotations

from hwee.kernel.errors import RecognitionError
from hwee.kernel.telemetry import TELEMETRY
from hwee.render.font import BitmapFont
from hwee.render.framebuffer import Framebuffer


class OpticalCharacterRecognizer:
    def __init__(self, font: BitmapFont, pitch: int, margin: int, max_distance: int = 2) -> None:
        self.font = font
        self.pitch = pitch
        self.margin = margin
        self.max_distance = max_distance

    def _cell(self, fb: Framebuffer, index: int):
        x0 = self.margin + index * self.pitch
        return tuple(tuple(fb.pixels[self.margin + y][x0 + x] for x in range(self.font.width))
                     for y in range(self.font.height))

    @staticmethod
    def _distance(a, b) -> int:
        return sum(pa != pb for ra, rb in zip(a, b) for pa, pb in zip(ra, rb))

    def recognize(self, fb: Framebuffer) -> list[int]:
        count = (fb.width - 2 * self.margin) // self.pitch
        result = []
        for index in range(count):
            cell = self._cell(fb, index)
            ranked = sorted((self._distance(cell, glyph), cp) for cp, glyph in self.font.glyphs.items())
            (best_distance, best), (runner_up, _) = ranked[0], ranked[1]
            if best_distance > self.max_distance or runner_up == best_distance:
                raise RecognitionError(f"Ambiguous glyph at cell {index} (distance {best_distance})")
            TELEMETRY.incr("ocr.pixel_corrections", best_distance)
            result.append(best)
        return result

import unittest

from hwee.config.model import Configuration
from hwee.config.parser import ConfigParser
from hwee.kernel.container import Container
from hwee.kernel.errors import DependencyResolutionError, SchemaViolation
from hwee.kernel.schema import validate
from hwee.render.font import parse_font
from hwee.kernel.resources import ResourceLocator
from hwee.transport import base64_, hamming, huffman, utf8


class A:
    def __init__(self, b: "B") -> None:
        self.b = b


class B:
    def __init__(self, a: A) -> None:
        self.a = a


class InfrastructureTests(unittest.TestCase):
    def test_config_interpolation(self):
        tree = ConfigParser('[a.b]\nx = ${env:X:-0x10}\ny = "s"\nz = on\n', environ={}).parse()
        self.assertEqual(tree, {"a": {"b": {"x": 16, "y": "s", "z": True}}})
        self.assertEqual(Configuration(tree).get("a.b.x", int), 16)

    def test_container_detects_cycles(self):
        c = Container()
        c.register(A)
        c.register(B)
        with self.assertRaises(DependencyResolutionError):
            c.resolve(A)

    def test_schema(self):
        with self.assertRaises(SchemaViolation):
            validate({"x": "1"}, {"type": "object", "properties": {"x": {"type": "integer"}}})

    def test_transport_codecs(self):
        data = utf8.encode([72, 0xE9, 0x20AC, 0x1F600])
        self.assertEqual(data, "Hé€😀".encode())
        self.assertEqual(huffman.decompress(huffman.compress(data)), data)
        self.assertEqual(base64_.decode(base64_.encode(data)), data)
        words = hamming.encode(data)
        for word in words:
            word[3] ^= 1
        self.assertEqual(hamming.decode(words)[0], data)

    def test_font_is_single_error_correcting(self):
        font = parse_font(ResourceLocator().read_text("fonts/hwee-5x7.hwfont"))
        glyphs = list(font.glyphs.values())
        for i, a in enumerate(glyphs):
            for b in glyphs[i + 1:]:
                distance = sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb))
                self.assertGreaterEqual(distance, 3)

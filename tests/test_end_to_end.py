import os
import pathlib
import unittest

from hwee.application import DEFAULT_CONFIG, HelloWorldEnterpriseApplication
from hwee.config.model import Configuration
from hwee.output.sink import MemorySink

EXPECTED = bytes([72, 101, 108, 108, 111, 44, 32, 87, 111, 114, 108, 100, 33, 10])


class EndToEndTests(unittest.TestCase):
    def test_greeting_is_delivered(self):
        config = Configuration.from_file(DEFAULT_CONFIG)
        config.override("ledger.difficulty_bits", 4)
        sink = MemorySink()
        HelloWorldEnterpriseApplication(config, sink).run()
        self.assertEqual(bytes(sink.buffer), EXPECTED)

    def test_runtime_contains_no_greeting_literal(self):
        root = pathlib.Path(__file__).resolve().parent.parent / "src" / "hwee"
        needles = [EXPECTED[:6].decode(), EXPECTED[7:13].decode()]  # the product name is allowed
        for path in root.rglob("*"):
            if path.is_file() and path.suffix != ".pyc":
                text = path.read_text(encoding="utf-8", errors="ignore")
                for needle in needles:
                    self.assertNotIn(needle, text, str(path))


if __name__ == "__main__":
    unittest.main()

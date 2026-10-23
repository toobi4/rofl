import sys
import unittest

from hwee.kernel.resources import ResourceLocator
from hwee.lambda_calculus.church import decode_numeral
from hwee.lambda_calculus.parser import parse_program
from hwee.lambda_calculus.reducer import normalize
from hwee.vm.assembler import assemble, from_object_file, to_object_file
from hwee.vm.machine import VirtualMachine


class VirtualMachineTests(unittest.TestCase):
    def run_bf(self, program: str) -> list[int]:
        source = ResourceLocator().read_text("bf_interpreter.hwasm")
        machine = VirtualMachine(from_object_file(to_object_file(assemble(source))))
        machine.load_data(0, [ord(c) for c in program] + [0])
        return machine.run()

    def test_nested_loops(self):
        self.assertEqual(self.run_bf("++[>+++[>++<-]<-]>>."), [12])

    def test_wraparound(self):
        self.assertEqual(self.run_bf("-."), [255])


class LambdaTests(unittest.TestCase):
    def test_church_arithmetic(self):
        sys.setrecursionlimit(50_000)
        env = parse_program(ResourceLocator().read_text("prelude.lc"))
        env = parse_program("X := ADD (MUL SEVEN SIX) (POW TWO THREE)", env)
        self.assertEqual(decode_numeral(normalize(env["X"])[0]), 50)

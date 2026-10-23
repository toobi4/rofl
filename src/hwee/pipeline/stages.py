"""Concrete pipeline stages, in order of ceremony."""

from __future__ import annotations

from typing import Any

from hwee.config.model import Configuration
from hwee.consensus.pbft import PBFTCluster
from hwee.consensus.replica import ByzantineReplica, Replica
from hwee.crypto.crc32 import crc32
from hwee.crypto.selftest import run_known_answer_tests
from hwee.kernel.bus import MessageBus
from hwee.kernel.container import Container
from hwee.kernel.entropy import DeterministicEntropySource
from hwee.kernel.errors import AttestationError, ConsensusError, IntegrityError, RecognitionError, TransportError
from hwee.kernel.plugins import plugin
from hwee.kernel.resources import ResourceLocator
from hwee.kernel.telemetry import TELEMETRY
from hwee.ledger.chain import Blockchain
from hwee.ledger.miner import Miner
from hwee.ml.trainer import GreetingStudent
from hwee.oracles.base import GlyphOracle, GlyphOracleFactoryProvider
from hwee.output.resilience import CircuitBreaker, RetryPolicy
from hwee.output.sink import LINE_TERMINATORS, OutputSink, ResilientSink
from hwee.pipeline.stage import PipelineContext, Stage
from hwee.render.font import parse_font
from hwee.render.framebuffer import TextRasterizer
from hwee.render.ocr import OpticalCharacterRecognizer
from hwee.transport import base64_, hamming, huffman, utf8
from hwee.transport.channel import NoisyChannel


@plugin("stage", "self-test", priority=10)
class CryptographicSelfTestStage(Stage):
    name = "FIPS 140-style power-on self test"
    produces = ("self_test.passed",)

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        return {"self_test.passed": run_known_answer_tests()}


@plugin("stage", "provisioning", priority=20)
class OracleProvisioningStage(Stage):
    name = "Oracle provisioning via reflective abstract factory provider"
    requires = ("self_test.passed",)
    produces = ("oracles",)

    def __init__(self, container: Container) -> None:
        self.container = container

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        oracles = GlyphOracleFactoryProvider(self.container).provide().create_all()
        TELEMETRY.gauge("oracles.provisioned", len(oracles))
        return {"oracles": oracles}


@plugin("stage", "divination", priority=30)
class OracleDivinationStage(Stage):
    name = "N-version glyph divination"
    requires = ("oracles",)
    produces = ("divinations",)

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        divinations = {}
        for oracle in context.require("oracles"):
            with TELEMETRY.span(f"oracle:{oracle.plugin_name}"):
                divinations[oracle.plugin_name] = oracle.divine()
        return {"divinations": divinations}


@plugin("stage", "consensus", priority=40)
class ByzantineConsensusStage(Stage):
    name = "PBFT consensus over code points"
    requires = ("oracles", "divinations")
    produces = ("consensus.code_points", "consensus.witnesses")

    def __init__(self, entropy: DeterministicEntropySource) -> None:
        self.entropy = entropy.fork("pbft")

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        oracles: list[GlyphOracle] = context.require("oracles")
        divinations = context.require("divinations")
        bus = MessageBus()
        faults = (len(oracles) - 1) // 3
        if faults < 1:
            raise ConsensusError("Refusing to run consensus without Byzantine fault tolerance")
        replicas = []
        for index, oracle in enumerate(oracles):
            args = (index, oracle.plugin_name, divinations[oracle.plugin_name], bus, len(oracles), faults)
            if oracle.byzantine:
                replicas.append(ByzantineReplica(*args, entropy=self.entropy.fork(oracle.plugin_name),
                                                 liar=getattr(oracle, "lie", None)))
            else:
                replicas.append(Replica(*args))
        cluster = PBFTCluster(replicas, bus, faults)
        length, _ = cluster.agree(0)
        code_points, witnesses = [], []
        for seq in range(1, length + 1):
            value, attesters = cluster.agree(seq)
            code_points.append(value)
            witnesses.append(attesters)
        return {"consensus.code_points": code_points, "consensus.witnesses": witnesses}


@plugin("stage", "attestation", priority=50)
class NeuralAttestationStage(Stage):
    name = "Neural attestation by a student network"
    requires = ("consensus.code_points",)
    produces = ("attestation.predictions",)

    def __init__(self, config: Configuration, entropy: DeterministicEntropySource) -> None:
        self.config = config
        self.entropy = entropy.fork("neural")

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        targets = context.require("consensus.code_points")
        hidden = self.config.get("attestation.hidden_units", int, 8)
        for attempt in range(1, self.config.get("attestation.max_restarts", int, 3) + 1):
            student = GreetingStudent(len(targets), hidden, self.entropy.fork(f"init-{attempt}"))
            report = student.fit(targets, self.config.get("attestation.learning_rate", float, 0.02),
                                 self.config.get("attestation.max_epochs", int, 5000),
                                 self.config.get("attestation.tolerance", float, 0.05))
            TELEMETRY.gauge("ml.final_loss", report.final_loss)
            if report.predictions == targets:
                return {"attestation.predictions": report.predictions}
            hidden *= 2
        raise AttestationError("The student network refuses to believe the consensus")


@plugin("stage", "ledger", priority=60)
class LedgerCommitStage(Stage):
    name = "Proof-of-work ledger commit"
    requires = ("consensus.code_points", "consensus.witnesses", "attestation.predictions")
    produces = ("ledger",)

    def __init__(self, config: Configuration) -> None:
        self.config = config

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        chain = Blockchain(self.config.get("ledger.difficulty_bits", int, 10), Miner())
        for position, (cp, witnesses, predicted) in enumerate(zip(
                context.require("consensus.code_points"), context.require("consensus.witnesses"),
                context.require("attestation.predictions"))):
            chain.append([{"type": "glyph", "position": position, "code_point": cp,
                           "witnesses": witnesses, "neural_attestation": predicted}])
        TELEMETRY.gauge("ledger.height", len(chain.blocks))
        return {"ledger": chain}


@plugin("stage", "reconstruction", priority=70)
class LedgerReconstructionStage(Stage):
    name = "Ledger validation and greeting reconstruction"
    requires = ("ledger",)
    produces = ("ledger.code_points",)

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        chain: Blockchain = context.require("ledger")
        chain.validate()
        glyphs = sorted(chain.transactions("glyph"), key=lambda tx: tx["position"])
        if [tx["position"] for tx in glyphs] != list(range(len(glyphs))):
            raise IntegrityError("Ledger has gaps in glyph positions")
        return {"ledger.code_points": [tx["code_point"] for tx in glyphs]}


@plugin("stage", "optical", priority=80)
class OpticalRoundTripStage(Stage):
    name = "Rasterization and OCR round trip"
    requires = ("ledger.code_points",)
    produces = ("ocr.code_points",)

    FONT = "fonts/hwee-5x7.hwfont"

    def __init__(self, resources: ResourceLocator, config: Configuration,
                 entropy: DeterministicEntropySource) -> None:
        self.resources = resources
        self.config = config
        self.entropy = entropy.fork("scanner")

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        code_points = context.require("ledger.code_points")
        font = parse_font(self.resources.read_text(self.FONT))
        rasterizer = TextRasterizer(font)
        fb = rasterizer.rasterize(code_points)
        flips = rasterizer.degrade(fb, len(code_points), self.entropy,
                                   self.config.get("render.dust_probability", float, 0.5))
        TELEMETRY.gauge("render.dust_flips", flips)
        TELEMETRY.log("    framebuffer:\n" + fb.to_ascii_art())
        recognized = OpticalCharacterRecognizer(font, rasterizer.pitch, rasterizer.margin).recognize(fb)
        if recognized != code_points:
            raise RecognitionError("OCR disagrees with the ledger")
        return {"ocr.code_points": recognized}


@plugin("stage", "transport", priority=90)
class TransportStage(Stage):
    name = "UTF-8 / Huffman / Base64 / Hamming(7,4) over a noisy channel"
    requires = ("ocr.code_points",)
    produces = ("transport.payload",)

    def __init__(self, config: Configuration, entropy: DeterministicEntropySource) -> None:
        self.config = config
        self.entropy = entropy.fork("channel")

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        code_points = context.require("ocr.code_points")
        encoded = utf8.encode(code_points)
        checksum = crc32(encoded)
        armored = base64_.encode(huffman.compress(encoded)).encode("ascii")
        channel = NoisyChannel(self.entropy, self.config.get("transport.bit_error_rate", float, 0.25))
        received, corrected = hamming.decode(channel.transmit(hamming.encode(armored)))
        TELEMETRY.gauge("transport.bits_flipped", channel.flips)
        TELEMETRY.gauge("transport.bits_corrected", corrected)
        payload = huffman.decompress(base64_.decode(received.decode("ascii")))
        if crc32(payload) != checksum or utf8.decode(payload) != code_points:
            raise TransportError("End-to-end integrity check failed")
        return {"transport.payload": payload}


@plugin("stage", "emission", priority=100)
class EmissionStage(Stage):
    name = "Resilient emission"
    requires = ("transport.payload",)
    produces = ("emitted.bytes",)

    def __init__(self, sink: OutputSink, config: Configuration) -> None:
        self.sink = sink
        self.config = config

    def execute(self, context: PipelineContext) -> dict[str, Any]:
        payload = context.require("transport.payload")
        terminator = LINE_TERMINATORS[self.config.get("output.line_terminator", str, "LF")]()
        payload += utf8.encode(terminator.terminator())
        resilient = ResilientSink(self.sink, RetryPolicy(self.config.get("output.retry_attempts", int, 5)),
                                  CircuitBreaker(self.config.get("output.breaker_threshold", int, 3)))
        resilient.emit(payload)
        return {"emitted.bytes": len(payload)}

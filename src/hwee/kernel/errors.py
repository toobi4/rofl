"""Exception hierarchy. Every failure deserves its own taxonomy."""


class HweeError(Exception):
    """Root of all enterprise sorrow."""


class ConfigurationError(HweeError):
    pass


class DependencyResolutionError(HweeError):
    pass


class PluginDiscoveryError(HweeError):
    pass


class IntegrityError(HweeError):
    pass


class SelfTestFailure(IntegrityError):
    pass


class SchemaViolation(HweeError):
    pass


class OracleError(HweeError):
    pass


class ConsensusError(HweeError):
    pass


class AttestationError(HweeError):
    pass


class LedgerIntegrityError(IntegrityError):
    pass


class RecognitionError(HweeError):
    pass


class TransportError(HweeError):
    pass


class EmissionError(HweeError):
    pass


class CircuitOpenError(EmissionError):
    pass


class VirtualMachineFault(HweeError):
    pass


class ReductionLimitExceeded(HweeError):
    pass

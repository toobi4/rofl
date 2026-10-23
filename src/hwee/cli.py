"""Command-line interface."""

from __future__ import annotations

import argparse
import sys

from hwee import __version__
from hwee.application import DEFAULT_CONFIG, HelloWorldEnterpriseApplication
from hwee.config.model import Configuration
from hwee.kernel.errors import HweeError
from hwee.kernel.telemetry import TELEMETRY


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hwee", description="Hello World Enterprise Edition")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to an HWCONF file")
    parser.add_argument("--verbose", "-v", action="store_true", help="narrate the journey on stderr")
    parser.add_argument("--telemetry", action="store_true", help="print a telemetry report to stderr")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="override a configuration key (integer values only, for safety)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    TELEMETRY.verbose = args.verbose
    try:
        config = Configuration.from_file(args.config)
        for item in args.set:
            key, _, value = item.partition("=")
            config.override(key, int(value, 0) if value.lstrip("-").isdigit() or value.startswith("0x")
                            else float(value) if value.replace(".", "", 1).isdigit() else value)
        HelloWorldEnterpriseApplication(config).run()
    except HweeError as exc:
        print(f"hwee: greeting delivery failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 70
    finally:
        if args.telemetry or args.verbose:
            print(TELEMETRY.report(), file=sys.stderr)
    return 0

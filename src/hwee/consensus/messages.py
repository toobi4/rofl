"""PBFT wire schemas."""

from __future__ import annotations

import json

from hwee.crypto.sha256 import sha256_hex

PRE_PREPARE = "pbft.pre_prepare"
PREPARE = "pbft.prepare"
COMMIT = "pbft.commit"
REPLY = "pbft.reply"
VIEW_CHANGE = "pbft.view_change"
NEW_VIEW = "pbft.new_view"

_INT = {"type": "integer", "minimum": 0}
_DIGEST = {"type": "string"}

SCHEMAS = {
    PRE_PREPARE: {"type": "object", "required": ["view", "seq", "value", "digest", "replica"],
                  "properties": {"view": _INT, "seq": _INT, "value": {"type": "integer"},
                                 "digest": _DIGEST, "replica": _INT}},
    PREPARE: {"type": "object", "required": ["view", "seq", "digest", "replica"],
              "properties": {"view": _INT, "seq": _INT, "digest": _DIGEST, "replica": _INT}},
    COMMIT: {"type": "object", "required": ["view", "seq", "digest", "replica"],
             "properties": {"view": _INT, "seq": _INT, "digest": _DIGEST, "replica": _INT}},
    REPLY: {"type": "object", "required": ["view", "seq", "value", "replica"],
            "properties": {"view": _INT, "seq": _INT, "value": {"type": "integer"}, "replica": _INT}},
    VIEW_CHANGE: {"type": "object", "required": ["new_view", "replica"],
                  "properties": {"new_view": _INT, "replica": _INT}},
    NEW_VIEW: {"type": "object", "required": ["view", "replica"],
               "properties": {"view": _INT, "replica": _INT}},
}


def digest_of(view: int, seq: int, value: int) -> str:
    return sha256_hex(json.dumps({"view": view, "seq": seq, "value": value}, sort_keys=True).encode())

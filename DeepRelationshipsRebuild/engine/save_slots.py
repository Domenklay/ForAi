# -*- coding: utf-8 -*-
"""Save slot identification, with conservative fallback.

A zero slot is not a reliable identifier for multiple different game saves.
Do not commit a v0.8 sidecar under that value without confirmation.
"""


def valid_slot(value):
    try:
        value = int(value)
        return str(value) if value > 0 else None
    except (ValueError, TypeError, OverflowError):
        return None


def find_save_slot(client=None, persistence=None):
    candidates = []
    if client is not None:
        candidates.append(("account", getattr(getattr(client, "account", None),
                                               "save_slot_id", None)))
        candidates.append(("client", getattr(client, "save_slot_id", None)))
    if persistence is not None:
        for prop in ("save_slot_id", "_save_slot_id", "current_save_slot_id"):
            try:
                candidates.append(("persistence." + prop, getattr(persistence, prop, None)))
            except Exception:
                pass
        method = getattr(persistence, "get_save_slot_proto_buff", None)
        if callable(method):
            try:
                obj = method()
                for prop in ("slot_id", "save_slot_id"):
                    candidates.append(("save_slot_proto." + prop, getattr(obj, prop, None)))
            except Exception:
                pass
    for source, value in candidates:
        parsed = valid_slot(value)
        if parsed is not None:
            return parsed, source
    return "0", "unresolved"

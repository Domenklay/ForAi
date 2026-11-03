# -*- coding: utf-8 -*-
"""Read-only compatibility reader for legacy v0.2-v0.7 sidecar schema.

No writes or mutation. Must not be used to overwrite the game's save data.
"""
import json


class LegacyStateError(ValueError):
    pass


def legacy_relationships(snapshot, slot_id):
    """Return normalized *copies* of one slot's directional relationship records.

    Legacy shape: {version: ..., slots: {<slot>: {relationships: {key: record}}}}
    Unknown fields are preserved in the returned dict. Invalid entries are
    ignored; malformed top-level data raises rather than silently wiping data.
    """
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("slots"), dict):
        raise LegacyStateError("Missing legacy slots mapping")
    slot = snapshot["slots"].get(str(slot_id), {})
    if not isinstance(slot, dict):
        raise LegacyStateError("Invalid legacy save slot")
    pairs = slot.get("relationships", {})
    if not isinstance(pairs, dict):
        raise LegacyStateError("Invalid legacy relationships")
    result = []
    for record in pairs.values():
        if not isinstance(record, dict):
            continue
        try:
            source = int(record["source_id"])
            target = int(record["target_id"])
        except (KeyError, ValueError, TypeError, OverflowError):
            continue
        if source <= 0 or target <= 0 or source == target:
            continue
        copy = dict(record)
        copy["source_id"] = source
        copy["target_id"] = target
        result.append(copy)
    return result


def parse_legacy_json(contents, slot_id):
    return legacy_relationships(json.loads(contents), slot_id)

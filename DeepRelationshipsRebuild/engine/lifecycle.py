# -*- coding: utf-8 -*-
"""Timed relationship transitions (one call per six in-game hours)."""
from grievances import memory, resentment, age

TIMERS=(
    "breakup_talk_steps", "relationship_pause_steps",
    "breakup_decision_steps", "post_breakup_steps",
    "autonomy_distance_steps", "second_chance_steps",
    "closeness_steps", "ready_to_forgive_steps",
    "forgiveness_block_steps",
    "cooldown_discuss", "cooldown_apologize", "cooldown_admit_fault",
    "cooldown_forgive", "cooldown_not_ready", "cooldown_second_chance",
)


def tick_record(record):
    """Advance exactly one directional record without external side effects."""
    age(record)
    for key in TIMERS:
        old = int(record.get(key, 0) or 0)
        if old > 0:
            record[key] = old-1
    phase = str(record.get("breakup_state", "none") or "none")
    if phase == "talk" and int(record.get("breakup_talk_steps", 0) or 0) <= 0:
        record["breakup_state"] = "none"
    elif phase == "pause" and int(record.get("relationship_pause_steps", 0) or 0) <= 0:
        record["breakup_state"] = "talk"
        record["breakup_talk_steps"] = max(1, int(record.get("breakup_talk_steps", 0) or 0))
    elif phase == "repairing":
        if (resentment(record) < 8 and
                float(record.get("trust", 0) or 0) >= 45 and
                float(record.get("satisfaction", 0) or 0) >= 45):
            record["breakup_state"] = "none"
            memory(record, "reunion", 6)
    if (record.get("reconciliation_stage") == "second_chance"
            and int(record.get("second_chance_steps", 0) or 0) <= 0):
        record["reconciliation_stage"] = ""
    return record

# -*- coding: utf-8 -*-
"""Grievance and memory rules ported from v0.4 / v0.6, without Sims 4 APIs.

Mutates an in-memory directed relationship record. Persistence/notifications
are the responsibility of the gameplay adapter.
"""
from copy import deepcopy

CONFIG = {
    "arguments": ("Ссоры и грубость", 0.45),
    "romantic_hurt": ("Романтическая обида", 0.65),
    "neglect": ("Недостаток внимания", 0.55),
    "infidelity": ("Измена", 0.92),
}
MEMORY_KINDS = {
    "arguments": "argument",
    "romantic_hurt": "romantic_hurt",
    "neglect": "neglect",
    "infidelity": "betrayal",
}
MAX_MEMORIES = 30


def clamp(v, low=0.0, high=100.0):
    return min(high, max(low, float(v)))


def ensure(record):
    if not isinstance(record.get("grievances"), dict):
        record["grievances"] = {}
    if not isinstance(record.get("relationship_memories"), list):
        record["relationship_memories"] = []
    record.setdefault("resentment", 0.0)
    record.setdefault("last_conflict_state", "Спокойно")
    return record


def resentment(record):
    ensure(record)
    total = sum(max(0.0, float(entry.get("severity", 0.0) or 0.0))
                for entry in record["grievances"].values() if isinstance(entry, dict))
    record["resentment"] = clamp(total)
    return record["resentment"]


def conflict_state(record):
    r = resentment(record)
    if r >= 70:
        return "Глубокая обида"
    if r >= 45:
        return "Серьёзный конфликт"
    if r >= 25:
        return "Накопленная обида"
    if r >= 8:
        return "Лёгкое раздражение"
    return "Спокойно"


def memory(record, kind, severity=1.0, merge=True):
    ensure(record)
    severity = clamp(max(0.1, float(severity)))
    partner_id = int(record.get("target_id", 0) or 0)
    memories = record["relationship_memories"]
    if merge:
        for item in reversed(memories):
            if not isinstance(item, dict):
                continue
            if item.get("kind") == kind and int(item.get("partner_id", 0) or 0) == partner_id:
                if int(item.get("age_steps", 99) or 0) <= 8:
                    item["severity"] = clamp(float(item.get("severity", 0) or 0) + severity)
                    item["age_steps"] = 0
                    item["resolved"] = False
                    return item
    item = {
        "kind": str(kind), "severity": severity, "age_steps": 0,
        "partner_id": partner_id, "resolved": False,
    }
    memories.append(item)
    if len(memories) > MAX_MEMORIES:
        memories.sort(key=lambda m: (
            m.get("kind") in ("betrayal", "second_chance"),
            float(m.get("severity", 0) or 0),
            -int(m.get("age_steps", 0) or 0)), reverse=True)
        del memories[MAX_MEMORIES:]
    return item


def add_grievance(record, reason, amount, count_event=True):
    if reason not in CONFIG:
        raise ValueError("Unknown grievance " + str(reason))
    ensure(record)
    label, persistence = CONFIG[reason]
    item = record["grievances"].setdefault(reason, {
        "label": label, "severity": 0.0, "count": 0, "age_steps": 0,
    })
    item["label"] = label
    item["severity"] = clamp(float(item.get("severity", 0) or 0) + max(0, float(amount)))
    item["age_steps"] = 0
    if count_event:
        item["count"] = int(item.get("count", 0) or 0) + 1
    value = resentment(record)
    record["last_conflict_state"] = conflict_state(record)
    memory_kind = MEMORY_KINDS[reason]
    memory(record, memory_kind, amount, merge=True)
    apply_caps(record)
    return value


def apply_caps(record):
    r = resentment(record)
    if r <= 0:
        return
    record["trust"] = min(float(record.get("trust", 0) or 0), max(35.0, 100.0-r*0.60))
    record["satisfaction"] = min(float(record.get("satisfaction", 0) or 0), max(25.0, 100.0-r*0.70))


def reduce_strongest(record, amount):
    ensure(record)
    items = [(float(value.get("severity", 0) or 0), key, value)
             for key, value in record["grievances"].items() if isinstance(value, dict)]
    if not items:
        return 0.0
    before, key, item = max(items, key=lambda x: x[0])
    factor = 0.45 if key == "infidelity" else 0.80 if key == "romantic_hurt" else 1.0
    after = max(0.0, before-max(0.0, float(amount))*factor)
    if after < 0.6:
        record["grievances"].pop(key, None)
    else:
        item["severity"] = after
        item["age_steps"] = 0
    resentment(record)
    record["last_conflict_state"] = conflict_state(record)
    return before-after


def update_metrics(record, trust=0, satisfaction=0, love=0, attachment=0):
    for key, change in (("trust", trust), ("satisfaction", satisfaction),
                        ("love", love), ("attachment", attachment)):
        record[key] = clamp(float(record.get(key, 0) or 0)+change)
    apply_caps(record)


def age(record):
    """One game decay tick. Infidelity severity decays much more slowly."""
    ensure(record)
    for reason, item in list(record["grievances"].items()):
        if not isinstance(item, dict):
            continue
        persistence = CONFIG.get(reason, ("", 0.50))[1]
        item["age_steps"] = int(item.get("age_steps", 0) or 0)+1
        item["severity"] = max(0.0, float(item.get("severity", 0) or 0) - (1-persistence))
        if item["severity"] < 0.6:
            record["grievances"].pop(reason, None)
    decay = {"argument": 0.30, "romantic_hurt": 0.18, "neglect": 0.15,
             "betrayal": 0.05, "second_chance": 0.10, "reconnection": 0.20}
    kept = []
    for item in record["relationship_memories"]:
        if not isinstance(item, dict):
            continue
        item["age_steps"] = int(item.get("age_steps", 0) or 0)+1
        kind = str(item.get("kind", ""))
        item["severity"] = max(0.0, float(item.get("severity", 0) or 0)-decay.get(kind, 0.2))
        if item["severity"] >= 0.6 or kind in ("betrayal", "second_chance"):
            kept.append(item)
    record["relationship_memories"] = kept[-MAX_MEMORIES:]
    record["last_conflict_state"] = conflict_state(record)


def copy_for_preview(record):
    return deepcopy(record)

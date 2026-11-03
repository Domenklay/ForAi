# -*- coding: utf-8 -*-
"""Pure relationship stage selection. No Sims 4 imports and no global hooks.

A stage is resolved per directed relationship. A Sim may have many records;
an active partner wins over historic ex-partner records.
Python 3.7 compatible.
"""
STAGES = (
    "argument", "deep_conflict", "infidelity", "reconciliation",
    "pause", "breakup", "exes", "second_chance", "recovery",
    "refused_forgive",
)
PRIORITIES = {
    "breakup": 100, "pause": 95, "refused_forgive": 90,
    "second_chance": 88, "recovery": 85, "infidelity": 80,
    "deep_conflict": 75, "argument": 70, "reconciliation": 60, "exes": 20,
}


def _number(value, fallback=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return fallback


def _steps(record, key):
    try:
        return max(0, int(record.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def resentment(record):
    return _number(record.get("resentment", 0.0))


def grievance(record, kind):
    data = record.get("grievances", {})
    item = data.get(kind, {}) if isinstance(data, dict) else {}
    return _number(item.get("severity", 0)) if isinstance(item, dict) else 0.0


def active(record):
    return (record.get("relationship_phase", "active") != "former"
            and record.get("breakup_state", "none") != "ended")


def select_stage(record, reverse=None):
    """Stage for record.source_id, including both sides' pair-level context."""
    if not isinstance(record, dict):
        return None
    reverse = reverse if isinstance(reverse, dict) else {}
    states = {record.get("breakup_state", "none"), reverse.get("breakup_state", "none")}
    pair_resentment = max(resentment(record), resentment(reverse))
    recent_conflict = max(_steps(record, "recent_conflict_steps"), _steps(reverse, "recent_conflict_steps"))

    if "ended" in states:
        return "breakup" if max(_steps(record, "post_breakup_steps"), _steps(reverse, "post_breakup_steps")) else "exes"
    if "pause" in states:
        return "pause"
    if record.get("reconciliation_stage") == "second_chance" and _steps(record, "second_chance_steps"):
        return "second_chance"
    if "repairing" in states:
        return "recovery"
    if _steps(record, "forgiveness_block_steps"):
        return "refused_forgive"
    if (_steps(record, "closeness_steps") or _steps(reverse, "closeness_steps")) and pair_resentment < 8:
        return "reconciliation"
    if grievance(record, "infidelity") >= 1:
        return "infidelity"
    if pair_resentment >= 70:
        return "deep_conflict"
    if recent_conflict or pair_resentment >= 0.75:
        return "argument"
    return None


def selected_stage_for_sim(sim_id, records):
    """Return (stage, record) deterministic across reloads."""
    valid = [r for r in records if isinstance(r, dict) and str(r.get("source_id")) == str(sim_id)]
    active_records = [r for r in valid if active(r)]
    candidates = active_records if active_records else valid
    by_direction = {(str(r.get("source_id")), str(r.get("target_id"))): r for r in valid}
    ranked = []
    for record in candidates:
        reverse = by_direction.get((str(record.get("target_id")), str(sim_id)))
        stage = select_stage(record, reverse)
        if stage:
            try:
                partner = int(record.get("target_id", 0))
            except (TypeError, ValueError):
                partner = 0
            ranked.append((PRIORITIES[stage], -partner, stage, record))
    if not ranked:
        return (None, None)
    chosen = max(ranked, key=lambda item: (item[0], item[1]))
    return chosen[2], chosen[3]

# -*- coding: utf-8 -*-
"""Pure, deterministic relationship stage rules (Python 3.7).

Port of v0.7.8's pair logic and v0.7.11's active-relationship selection.
No Sims imports, global hooks, disk I/O or mutations.
"""
STAGES = (
    "argument", "deep_conflict", "infidelity", "reconciliation",
    "pause", "breakup", "exes", "second_chance", "recovery",
    "refused_forgive",
)
PRIORITIES = {
    "breakup": 100, "pause": 95, "refused_forgive": 90,
    "second_chance": 88, "recovery": 85, "infidelity": 80,
    "deep_conflict": 75, "argument": 70, "reconciliation": 60,
    "exes": 20,
}
REPAIR_MEMORY_KINDS = frozenset((
    "reconnection", "reunion", "save_relationship", "forgiveness"
))


def _number(value, fallback=0.0):
    try:
        return float(value or 0)
    except (TypeError, ValueError, OverflowError):
        return fallback


def _steps(record, key):
    try:
        return max(0, int(record.get(key, 0) or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def resentment(record):
    """Derive current resentment from severity entries when available.

    The adapter may supply an already recalculated value. The original game
    engine recalculates severity and decay before this stage decision.
    """
    return _number(record.get("resentment", 0.0)) if isinstance(record, dict) else 0.0


def grievance(record, kind):
    data = record.get("grievances", {}) if isinstance(record, dict) else {}
    item = data.get(kind, {}) if isinstance(data, dict) else {}
    return _number(item.get("severity", 0)) if isinstance(item, dict) else 0.0


def active(record):
    return (
        isinstance(record, dict) and
        str(record.get("relationship_phase", "active") or "active") != "former" and
        str(record.get("breakup_state", "none") or "none") != "ended"
    )


def _recent_memory(record, kinds, max_age):
    if not isinstance(record, dict):
        return False
    memories = record.get("relationship_memories")
    if not isinstance(memories, list):
        return False
    for item in reversed(memories):
        if not isinstance(item, dict) or str(item.get("kind", "")) not in kinds:
            continue
        try:
            if int(item.get("age_steps", 99)) <= max_age:
                return True
        except (TypeError, ValueError, OverflowError):
            pass
    return False


def _healthy_for_reconciliation(record, reverse):
    records = [r for r in (record, reverse) if isinstance(r, dict) and r]
    if not records or max(resentment(r) for r in records) >= 8.0:
        return False
    return all(
        _number(r.get("trust")) >= 40.0 and
        _number(r.get("satisfaction")) >= 40.0
        for r in records
    )


def _real_second_chance(record, reverse):
    records = [r for r in (record, reverse) if isinstance(r, dict) and r]
    if not records or max(_steps(r, "second_chance_steps") for r in records) <= 0:
        return False
    return any(
        str(r.get("reconciliation_stage", "") or "") == "second_chance" or
        _recent_memory(r, frozenset(("second_chance",)), 12)
        for r in records
    )


def select_stage(record, reverse=None):
    """Return the visible stage of record's source Sim in a directional pair."""
    if not isinstance(record, dict):
        return None
    reverse = reverse if isinstance(reverse, dict) else None
    records = [r for r in (record, reverse) if r is not None]
    states = {str(r.get("breakup_state", "none") or "none") for r in records}
    pair_resentment = max(resentment(r) for r in records)
    recent_conflict = max(_steps(r, "recent_conflict_steps") for r in records)
    post_breakup = max(_steps(r, "post_breakup_steps") for r in records)
    closeness = max(_steps(r, "closeness_steps") for r in records)

    if "ended" in states:
        return "breakup" if post_breakup > 0 else "exes"
    if "pause" in states:
        return "pause"
    if _real_second_chance(record, reverse):
        return "second_chance"
    if "repairing" in states:
        return "recovery"
    if _steps(record, "forgiveness_block_steps"):
        return "refused_forgive"

    recent_repair = any(
        _recent_memory(r, REPAIR_MEMORY_KINDS, 8) for r in records
    )
    if _healthy_for_reconciliation(record, reverse) and (closeness > 0 or recent_repair):
        return "reconciliation"
    if grievance(record, "infidelity") >= 1.0:
        return "infidelity"
    if pair_resentment >= 70.0:
        return "deep_conflict"
    if recent_conflict > 0 or pair_resentment >= 0.75:
        return "argument"
    return None


def selected_stage_for_sim(sim_id, records):
    """Use *all* directional records for reverse lookup, then rank Sim's records.

    An active pair takes precedence over former partners. A former-partner
    stage is used only when the Sim has no active tracked relationship.
    Ties are deterministic by partner ID, regardless of iteration order.
    """
    all_records = [r for r in records if isinstance(r, dict)]
    by_direction = {
        (str(r.get("source_id")), str(r.get("target_id"))): r
        for r in all_records
    }
    owned = [r for r in all_records if str(r.get("source_id")) == str(sim_id)]
    active_owned = [r for r in owned if active(r)]
    candidates = active_owned if active_owned else owned
    ranked = []
    for record in candidates:
        reverse = by_direction.get((str(record.get("target_id")), str(sim_id)))
        stage = select_stage(record, reverse)
        if not stage:
            continue
        try:
            partner = int(record.get("target_id", 0))
        except (TypeError, ValueError, OverflowError):
            partner = 0
        ranked.append((PRIORITIES[stage], -partner, stage, record))
    if ranked:
        best = max(ranked, key=lambda row: (row[0], row[1]))
        return best[2], best[3]
    return (None, active_owned[0] if active_owned else None)

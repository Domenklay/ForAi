# -*- coding: utf-8 -*-
"""One authoritative calculation for stage + supporting emotion Buffs.

26 original resources (10 stage + 16 supporting/legacy), Python 3.7.
The engine never adds old story-stage copies beside a new story stage.
"""
from stages import STAGES

STAGE_TO_BUFF = {
    "argument": 12004666048318715120,
    "deep_conflict": 12004666048318715121,
    "reconciliation": 12004666048318715122,
    "infidelity": 12004666048318715123,
    "refused_forgive": 12004666048318715124,
    "pause": 12004666048318715125,
    "breakup": 12004666048318715126,
    "exes": 12004666048318715127,
    "second_chance": 12004666048318715128,
    "recovery": 12004666048318715129,
}
STAGE_BUFFS = frozenset(STAGE_TO_BUFF.values())
EXTRA_BUFFS = {
    "light_irritation": 9809346411725758677,
    "accumulated_resentment": 14935880521011841611,
    "serious_conflict": 14816115564650603146,
    "deep_hurt": 16750057278039550849,
    "betrayed_trust": 14632315915397281344,
    "jealousy": 12004666048318715101,
    "loss_of_confidence": 12004666048318715102,
    "lack_of_attention": 12004666048318715103,
    "lonely_in_relationship": 12004666048318715104,
    "unmet_expectations": 12004666048318715105,
    "ready_to_forgive": 12004666048318715106,
    "legacy_second_chance": 12004666048318715107,
    "closeness": 12004666048318715108,
    "happy_relationship": 12004666048318715109,
    "unstable_relationship": 12004666048318715110,
    "on_verge_breakup": 12004666048318715111,
}
EXTRA_BUFF_IDS = frozenset(EXTRA_BUFFS.values())
ALL_BUFFS = STAGE_BUFFS | EXTRA_BUFF_IDS
NEGATIVE_STAGES = frozenset((
    "argument", "deep_conflict", "infidelity", "refused_forgive",
    "pause", "breakup", "exes"
))
# These resources existed in the old tuning and are retained for cleanup
# and compatibility; new primary stages take priority over their duplicates.
LEGACY_STAGE_EXTRAS = frozenset((
    "light_irritation", "accumulated_resentment", "serious_conflict",
    "deep_hurt", "ready_to_forgive", "legacy_second_chance", "closeness"
))
assert set(STAGES) == set(STAGE_TO_BUFF)
assert len(STAGE_BUFFS) == 10
assert len(EXTRA_BUFF_IDS) == 16
assert len(ALL_BUFFS) == 26


def _num(record, key, default=0.0):
    try:
        value = record.get(key, default)
        return float(default if value is None else value)
    except (ValueError, TypeError, OverflowError):
        return default


def _grievance(record, key):
    items = record.get("grievances", {})
    if not isinstance(items, dict):
        return 0.0
    item = items.get(key)
    return _num(item, "severity") if isinstance(item, dict) else 0.0


def _extra_names(record, stage):
    """Return supporting statuses without contradicting the story stage.

    Some legacy effects still exist in .package but are deliberately never
    applied beside a new stage representing the same story beat.
    """
    if not isinstance(record, dict) or not {"love", "trust", "satisfaction"}.issubset(record):
        return set()
    r = _num(record, "resentment")
    love = _num(record, "love")
    trust = _num(record, "trust")
    attachment = _num(record, "attachment")
    compatibility = _num(record, "compatibility", 50.0)
    satisfaction = _num(record, "satisfaction")
    quiet = _num(record, "quiet_steps")
    infidelity = _grievance(record, "infidelity")
    neglect = _grievance(record, "neglect")
    hurt = _grievance(record, "romantic_hurt")
    desired = set()

    # Independent emotions: betrayal is directional; jealous reactions must
    # have actual betrayal/romantic hurt rather than generic arguing.
    if infidelity >= 1:
        desired.add("betrayed_trust")
        if trust < 55 or hurt >= 10:
            desired.add("jealousy")
    elif hurt >= 10 and trust < 55:
        desired.add("jealousy")
    if love >= 25 and (trust < 40 or satisfaction < 30):
        desired.add("loss_of_confidence")
    if (neglect >= 12 or quiet >= 20) and attachment >= 40:
        desired.add("lonely_in_relationship")
    elif neglect >= 4 or quiet >= 12:
        desired.add("lack_of_attention")
    if compatibility < 42 and satisfaction < 48 and love >= 25:
        desired.add("unmet_expectations")

    # One overall health effect at most. Never say 'happy' during conflict.
    if love < 25 and trust < 25 and satisfaction < 20:
        desired.add("on_verge_breakup")
    elif r >= 25 or (satisfaction < 40 and love >= 35):
        desired.add("unstable_relationship")
    elif stage is None and r < 8 and love >= 75 and trust >= 70 and satisfaction >= 70:
        desired.add("happy_relationship")

    # Old emotional conflict-ladder is only useful when there is no dedicated
    # stage for a conflict (for example, while a current stage is suppressed).
    # At least one of these status effects is available from the resource map,
    # but never put it on top of another main stage.
    if stage is None:
        if r >= 70:
            desired.add("deep_hurt")
        elif r >= 45:
            desired.add("serious_conflict")
        elif r >= 25:
            desired.add("accumulated_resentment")
        elif r >= 8:
            desired.add("light_irritation")
        if 8 <= r < 35 and love >= 60 and trust >= 35:
            desired.add("ready_to_forgive")
        elif r < 8 and love >= 65 and trust >= 60 and attachment >= 55 and satisfaction >= 55:
            desired.add("closeness")
        elif 1 <= r < 25 and love >= 65 and satisfaction >= 40 and trust >= 40:
            desired.add("legacy_second_chance")
    if stage in NEGATIVE_STAGES:
        desired.discard("happy_relationship")
        desired.discard("closeness")
        desired.discard("legacy_second_chance")
        desired.discard("ready_to_forgive")
    if stage == "exes":
        desired.discard("unstable_relationship")
    return desired


def desired_ids(stage, record=None):
    if stage not in STAGE_TO_BUFF and stage is not None:
        raise ValueError("Unknown stage {!r}".format(stage))
    values = {STAGE_TO_BUFF[stage]} if stage is not None else set()
    values.update(EXTRA_BUFFS[x] for x in _extra_names(record, stage))
    return values


def changeset(current_ids, stage, record=None):
    """Compute removals/additions across *all* 26 managed Buff resources."""
    current = set(current_ids or ())
    desired = desired_ids(stage, record)
    owned = current.intersection(ALL_BUFFS)
    return (owned - desired, desired - owned)

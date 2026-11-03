# -*- coding: utf-8 -*-
"""Contextual menu action availability, independent of Sims 4 imports."""
from stages import select_stage, resentment, grievance


def action_allowed(action, actor, partner):
    """No reconciliation/breakup decisions on an untouched healthy couple.

    Both directional records are required. A stage or actual relationship
    state is necessary before offering corresponding conflict decisions.
    """
    if action == "report":
        return isinstance(actor, dict) and isinstance(partner, dict)
    if not isinstance(actor, dict) or not isinstance(partner, dict):
        return False
    stage = select_stage(actor, partner)
    r = max(resentment(actor), resentment(partner))
    trouble = (r >= 0.75 or
               min(float(actor.get("satisfaction", 50) or 0),
                   float(partner.get("satisfaction", 50) or 0)) < 40 or
               max(grievance(actor, "infidelity"), grievance(partner, "infidelity")) > 0 or
               stage in ("argument", "deep_conflict", "infidelity", "refused_forgive",
                         "pause", "breakup", "exes", "reconciliation", "recovery",
                         "second_chance"))
    forgiveness = stage in ("argument", "deep_conflict", "infidelity",
                           "refused_forgive", "reconciliation", "recovery",
                           "second_chance")
    broken = stage in ("pause", "breakup", "exes", "second_chance",
                       "recovery", "refused_forgive")
    if action in ("discuss", "apologize", "admit_fault"):
        return bool(trouble and stage not in ("breakup", "exes"))
    if action in ("forgive", "not_ready"):
        return bool(forgiveness)
    if action == "second_chance":
        return bool(broken)
    if action == "breakup_talk":
        return bool(trouble and stage not in ("breakup", "exes", "pause"))
    if action == "take_pause":
        return bool(trouble and stage not in ("pause", "breakup", "exes"))
    if action == "save_relationship":
        return bool(trouble and stage not in ("exes",))
    if action == "decide_breakup":
        return bool(trouble and stage not in ("breakup", "exes"))
    return False

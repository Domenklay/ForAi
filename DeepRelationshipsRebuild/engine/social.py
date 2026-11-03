# -*- coding: utf-8 -*-
"""Pure consequences of observed EA relationship score changes.

Input must be the actual, post-EA-change delta and the directed owner record.
All operations are in-memory. No save/sidecar writes or Sims 4 imports.
"""
from grievances import add_grievance, resentment, apply_caps, memory


def apply_score_delta(record, actual_delta, kind):
    """Call *once* per committed score change for the affected direction."""
    delta = float(actual_delta or 0.0)
    if kind not in ("romance", "friendship"):
        return False
    if delta < -0.0001:
        magnitude = abs(delta)
        if kind == "romance":
            add_grievance(record, "romantic_hurt",
                          min(12.0, max(2.0, magnitude*0.32)))
        else:
            add_grievance(record, "arguments",
                          min(10.0, max(1.5, magnitude*0.28)))
        apply_caps(record)
        return True

    if delta > 0.5:
        grievance_map = record.get("grievances", {})
        neglect = grievance_map.get("neglect") if isinstance(grievance_map, dict) else None
        if isinstance(neglect, dict):
            before = float(neglect.get("severity", 0.0) or 0.0)
            reduction = min(1.8, delta*(0.10 if kind == "romance" else 0.07))
            neglect["severity"] = max(0.0, before-reduction)
            if neglect["severity"] < 0.6:
                grievance_map.pop("neglect", None)
            # Recalculate from the updated grievance map and maintain caps.
            from grievances import resentment as recalculate
            recalculate(record)
            apply_caps(record)
        if resentment(record) >= 8.0 and delta >= 3:
            memory(record, "positive_contact", min(6, delta*0.25))
        if resentment(record) < 8.0 and float(record.get("trust",0) or 0)>=55:
            memory(record, "reconnection", 2)
        return True
    return False

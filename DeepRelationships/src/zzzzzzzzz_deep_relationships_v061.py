# -*- coding: utf-8 -*-
"""Deep Relationships v0.6.1 — pair-level moodlet consistency.

Fixes the situation where one partner starts a conflict but keeps the
"Happy relationship" moodlet because only the victim carries directional
resentment. Pair-level conflict now suppresses positive relationship moodlets
for both Sims. The hurt side keeps its specific conflict moodlets; the other
side receives a general unstable-relationship tension moodlet while the pair
is actively in conflict.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation

VERSION = '0.6.1'
base.VERSION = VERSION
moodlets.VERSION = VERSION

_POSITIVE_RELATIONSHIP_BUFFS = {
    moodlets.BUFF_READY_TO_FORGIVE,
    moodlets.BUFF_SECOND_CHANCE,
    moodlets.BUFF_CLOSENESS,
    moodlets.BUFF_HAPPY_RELATIONSHIP,
}


def _record_resentment(record):
    if record is None:
        return 0.0
    try:
        return float(grievances._recalculate_resentment(record) or 0.0)
    except Exception:
        try:
            return float(record.get('resentment', 0.0) or 0.0)
        except Exception:
            return 0.0


def _reverse_record(record):
    if record is None:
        return None
    try:
        source_id = int(record.get('source_id', 0) or 0)
        target_id = int(record.get('target_id', 0) or 0)
        if not source_id or not target_id:
            return None
        return core._existing_record(target_id, source_id)
    except Exception:
        return None


def _pair_conflict_level(record):
    """Return the strongest active resentment in either direction."""
    own = _record_resentment(record)
    reverse = _record_resentment(_reverse_record(record))
    return max(own, reverse)


def _pair_has_conflict(record):
    return _pair_conflict_level(record) >= 8.0


_PREVIOUS_DESIRED_FOR_RECORD = moodlets._desired_for_record


def _desired_for_record_v061(record):
    desired = set(_PREVIOUS_DESIRED_FOR_RECORD(record))
    if record is None:
        return desired

    pair_conflict = _pair_conflict_level(record)
    own_conflict = _record_resentment(record)

    if pair_conflict >= 8.0:
        # A relationship cannot simultaneously be presented as happy/close while
        # either partner is carrying an active conflict with the other.
        desired.difference_update(_POSITIVE_RELATIONSHIP_BUFFS)

        # The victim already receives a specific conflict ladder from the base
        # moodlet logic. The partner who is not carrying the directional hurt
        # still feels that the relationship is unstable instead of remaining
        # "Happy +3" after starting the argument.
        if own_conflict < 8.0:
            desired.add(moodlets.BUFF_UNSTABLE_RELATIONSHIP)

        # If the pair is in a serious conflict, the general unstable moodlet is
        # useful on both sides in addition to the victim-specific hurt moodlet.
        if pair_conflict >= 25.0:
            desired.add(moodlets.BUFF_UNSTABLE_RELATIONSHIP)
    else:
        # No active conflict: normal positive relationship moodlets can return
        # through the existing v0.5/v0.6 rules.
        pass

    return desired


moodlets._desired_for_record = _desired_for_record_v061


# v0.4.6 chooses one dominant relationship to drive visible moodlets. Extend the
# impact score so a pair conflict matters even if the selected Sim is the
# offender and their own directional resentment is zero.
try:
    import zzzzz_deep_relationships_core_v046 as _core_module
    _PREVIOUS_IMPACT = _core_module._record_impact

    def _record_impact_v061(record):
        negative, positive = _PREVIOUS_IMPACT(record)
        pair_conflict = _pair_conflict_level(record)
        own_conflict = _record_resentment(record)
        if pair_conflict > own_conflict:
            negative += (pair_conflict - own_conflict) * 2.25
        if pair_conflict >= 8.0:
            # Do not let high historic love/trust make a currently fighting pair
            # win the "positive relationship" selection.
            positive *= 0.65
        return negative, positive

    _core_module._record_impact = _record_impact_v061
except Exception:
    base.flog('V061 IMPACT PATCH FAILED')
    base.flog(traceback.format_exc())


# Force immediate moodlet refresh for BOTH partners whenever a grievance changes.
# Earlier layers often synchronised only the record owner; this left the other
# Sim's old happy relationship buff alive until a later periodic tick.
_PREVIOUS_ADD_GRIEVANCE = grievances.add_grievance


def _sync_both_sides(record):
    if record is None:
        return
    try:
        manager = base.services.sim_info_manager()
        if manager is None:
            return
        ids = set()
        for rec in (record, _reverse_record(record)):
            if rec is None:
                continue
            try:
                ids.add(int(rec.get('source_id', 0) or 0))
            except Exception:
                pass
        try:
            ids.add(int(record.get('target_id', 0) or 0))
        except Exception:
            pass
        for sim_id in ids:
            if not sim_id:
                continue
            sim_info = manager.get(sim_id)
            if sim_info is not None:
                moodlets.sync_sim_moodlets(sim_info)
    except Exception:
        base.flog('V061 BOTH-SIDE MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())


def _add_grievance_v061(record, reason, amount, count_event=True):
    result = _PREVIOUS_ADD_GRIEVANCE(record, reason, amount, count_event=count_event)
    try:
        _sync_both_sides(record)
    except Exception:
        base.flog('V061 GRIEVANCE MOODLET REFRESH FAILED')
        base.flog(traceback.format_exc())
    return result


grievances.add_grievance = _add_grievance_v061


# Also refresh both sides after any relationship delta, including conflicts that
# create the grievance through the v0.5.1 role system.
_PREVIOUS_DELTA = base.on_relationship_delta


def _on_relationship_delta_v061(source_id, target_id, supplied_delta, kind):
    result = _PREVIOUS_DELTA(source_id, target_id, supplied_delta, kind)
    try:
        rec = core._existing_record(int(source_id), int(target_id))
        if rec is None:
            rec = core._existing_record(int(target_id), int(source_id))
        _sync_both_sides(rec)
    except Exception:
        base.flog('V061 DELTA MOODLET REFRESH FAILED')
        base.flog(traceback.format_exc())
    return result


base.on_relationship_delta = _on_relationship_delta_v061


# On zone initialisation, clean any stale happy buff that survived from v0.6.0.
_PREVIOUS_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v061():
    result = _PREVIOUS_INITIALIZE_ZONE()
    try:
        moodlets.sync_household_moodlets()
        base.flog('V061 PAIR MOODLET CONSISTENCY READY')
    except Exception:
        base.flog('V061 INITIAL MOODLET CLEANUP FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v061
base.flog('V061 PAIR-LEVEL MOODLET FIX INSTALLED')

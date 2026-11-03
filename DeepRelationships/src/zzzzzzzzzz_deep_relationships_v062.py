# -*- coding: utf-8 -*-
"""Deep Relationships v0.6.2 — hard moodlet cleanup.

Fixes stale custom relationship buffs that could remain visible after their
condition stopped being true. The old synchronizer gated removal behind
SimInfo.has_buff(); v0.6.2 removes every undesired Deep Relationships buff
unconditionally and verifies the result.

Also treats any fresh/unresolved relationship hurt as incompatible with the
"Happy relationship" presentation. A couple no longer needs to reach 8 points
of resentment before the old happy status is suppressed.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core

VERSION = '0.6.2'
base.VERSION = VERSION
moodlets.VERSION = VERSION

_POSITIVE = {
    moodlets.BUFF_READY_TO_FORGIVE,
    moodlets.BUFF_SECOND_CHANCE,
    moodlets.BUFF_CLOSENESS,
    moodlets.BUFF_HAPPY_RELATIONSHIP,
}

_NEGATIVE_MEMORY_KINDS = {
    'argument', 'romantic_hurt', 'neglect', 'betrayal',
    'apology_rejected', 'distance',
}


def _resentment(record):
    if record is None:
        return 0.0
    try:
        return float(grievances._recalculate_resentment(record) or 0.0)
    except Exception:
        try:
            return float(record.get('resentment', 0.0) or 0.0)
        except Exception:
            return 0.0


def _reverse(record):
    if record is None:
        return None
    try:
        return core._existing_record(
            int(record.get('target_id', 0) or 0),
            int(record.get('source_id', 0) or 0)
        )
    except Exception:
        return None


def _recent_steps(record):
    if record is None:
        return 0
    try:
        return max(0, int(record.get('recent_conflict_steps', 0) or 0))
    except Exception:
        return 0


def _has_unresolved_negative_memory(record):
    if record is None:
        return False
    memories = record.get('relationship_memories')
    if not isinstance(memories, list):
        return False
    for item in memories:
        if not isinstance(item, dict):
            continue
        if bool(item.get('resolved', False)):
            continue
        if str(item.get('kind', '')) not in _NEGATIVE_MEMORY_KINDS:
            continue
        try:
            if float(item.get('severity', 0.0) or 0.0) >= 1.0:
                return True
        except Exception:
            continue
    return False


def _pair_problem(record):
    """Any active hurt or very recent fight suppresses happy-pair presentation."""
    reverse = _reverse(record)
    if max(_resentment(record), _resentment(reverse)) >= 0.75:
        return True
    if max(_recent_steps(record), _recent_steps(reverse)) > 0:
        return True
    if _has_unresolved_negative_memory(record) or _has_unresolved_negative_memory(reverse):
        return True
    return False


_PREVIOUS_DESIRED_FOR_RECORD = moodlets._desired_for_record


def _desired_for_record_v062(record):
    desired = set(_PREVIOUS_DESIRED_FOR_RECORD(record))
    if record is None:
        return desired

    if _pair_problem(record):
        # A current fight/hurt and a happy relationship status are mutually
        # exclusive. Recovery buffs are also withheld until the pair actually
        # enters a reconciliation stage without an active recent-conflict flag.
        desired.difference_update(_POSITIVE)

        # Even the offender/non-hurt side must feel relationship instability.
        # The victim may additionally receive the more specific conflict ladder.
        desired.add(moodlets.BUFF_UNSTABLE_RELATIONSHIP)

    return desired


moodlets._desired_for_record = _desired_for_record_v062


# ---------------------------------------------------------------------------
# Hard synchronizer: remove undesired buffs unconditionally.
# ---------------------------------------------------------------------------
def _still_has(sim_info, buff_type):
    try:
        return bool(sim_info.has_buff(buff_type))
    except Exception:
        return False


def _force_remove(sim_info, buff_type, buff_id):
    """Remove by type without trusting the pre-removal has_buff check."""
    try:
        sim_info.remove_buff_by_type(buff_type)
    except Exception:
        base.flog('V062 REMOVE CALL FAILED: sim {} buff {}'.format(
            getattr(sim_info, 'sim_id', '?'), buff_id
        ))
        base.flog(traceback.format_exc())
        return False

    # A second call is harmless (vanilla remove_buff_by_type is a no-op when
    # absent) and covers a stale UI/component edge where the first call consumes
    # an old entry/handle but the type remains active.
    try:
        if _still_has(sim_info, buff_type):
            sim_info.remove_buff_by_type(buff_type)
    except Exception:
        pass

    if _still_has(sim_info, buff_type):
        base.flog('V062 BUFF STILL PRESENT AFTER REMOVE: sim {} buff {}'.format(
            getattr(sim_info, 'sim_id', '?'), buff_id
        ))
        return False
    return True


def _sync_sim_moodlets_v062(sim_info):
    if sim_info is None:
        return False
    manager = moodlets._buff_manager()
    if manager is None:
        base.flog('V062 MOODLET BUFF MANAGER MISSING')
        return False

    try:
        desired = set(moodlets._desired_moodlets(sim_info))
    except Exception:
        base.flog('V062 DESIRED MOODLETS FAILED: sim {}'.format(
            getattr(sim_info, 'sim_id', '?')
        ))
        base.flog(traceback.format_exc())
        return False

    changed = False

    # First purge everything that should not be active. Do NOT gate this behind
    # has_buff(). remove_buff_by_type() safely ignores absent buffs.
    for buff_id in moodlets.ALL_BUFFS:
        if buff_id in desired:
            continue
        try:
            buff_type = manager.get(buff_id)
            if buff_type is None:
                continue
            was_present = _still_has(sim_info, buff_type)
            removed = _force_remove(sim_info, buff_type, buff_id)
            if was_present and removed:
                changed = True
                base.flog('V062 MOODLET REMOVED: sim {} buff {}'.format(
                    getattr(sim_info, 'sim_id', '?'), buff_id
                ))
        except Exception:
            base.flog('V062 MOODLET PURGE FAILED: sim {} buff {}'.format(
                getattr(sim_info, 'sim_id', '?'), buff_id
            ))
            base.flog(traceback.format_exc())

    # Then add desired buffs that are actually absent.
    for buff_id in desired:
        try:
            if buff_id not in moodlets.ALL_BUFFS:
                continue
            buff_type = manager.get(buff_id)
            if buff_type is None:
                continue
            if not _still_has(sim_info, buff_type):
                handle = sim_info.add_buff(buff_type)
                if handle is not None:
                    changed = True
                    base.flog('V062 MOODLET ADDED: sim {} buff {}'.format(
                        getattr(sim_info, 'sim_id', '?'), buff_id
                    ))
        except Exception:
            base.flog('V062 MOODLET ADD FAILED: sim {} buff {}'.format(
                getattr(sim_info, 'sim_id', '?'), buff_id
            ))
            base.flog(traceback.format_exc())

    return changed


moodlets.sync_sim_moodlets = _sync_sim_moodlets_v062


# Household sync must call the new function dynamically rather than the old
# function object captured in v0.4.2.
def _sync_household_moodlets_v062():
    changed = 0
    try:
        hh = base.household()
        for sim_info in base.sims_in_household(hh):
            if moodlets.sync_sim_moodlets(sim_info):
                changed += 1
    except Exception:
        base.flog('V062 HOUSEHOLD MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())
    return changed


moodlets.sync_household_moodlets = _sync_household_moodlets_v062


# ---------------------------------------------------------------------------
# Recent-conflict marker. One negative relationship event suppresses Happy for
# about 24 sim-hours even before resentment grows to the old 8-point threshold.
# ---------------------------------------------------------------------------
_PREVIOUS_DELTA = base.on_relationship_delta


def _set_recent_pair(source_id, target_id):
    changed = False
    for a, b in ((source_id, target_id), (target_id, source_id)):
        try:
            record = core._existing_record(int(a), int(b))
            if record is not None:
                record['recent_conflict_steps'] = max(
                    4, int(record.get('recent_conflict_steps', 0) or 0)
                )
                changed = True
        except Exception:
            pass
    if changed:
        base.DIRTY = True


def _on_relationship_delta_v062(source_id, target_id, supplied_delta, kind):
    actual = 0.0
    try:
        actual, _ = core._actual_delta(source_id, target_id, supplied_delta, kind)
    except Exception:
        try:
            actual = float(supplied_delta or 0.0)
        except Exception:
            actual = 0.0

    result = _PREVIOUS_DELTA(source_id, target_id, supplied_delta, kind)

    try:
        if actual < -0.0001:
            _set_recent_pair(source_id, target_id)
        manager = base.services.sim_info_manager()
        if manager is not None:
            for sim_id in (int(source_id), int(target_id)):
                sim_info = manager.get(sim_id)
                if sim_info is not None:
                    moodlets.sync_sim_moodlets(sim_info)
    except Exception:
        base.flog('V062 DELTA HARD REFRESH FAILED')
        base.flog(traceback.format_exc())
    return result


base.on_relationship_delta = _on_relationship_delta_v062


# Decrease recent-conflict marker on the existing six-hour tick.
_PREVIOUS_DECAY_TICK = base.decay_tick


def _decay_tick_v062():
    result = _PREVIOUS_DECAY_TICK()
    try:
        changed = False
        for record in tuple(base.slot_state().values()):
            steps = _recent_steps(record)
            if steps > 0:
                record['recent_conflict_steps'] = steps - 1
                changed = True
        if changed:
            base.DIRTY = True
        moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V062 RECENT-CONFLICT TICK FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v062


_PREVIOUS_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v062():
    result = _PREVIOUS_INITIALIZE_ZONE()
    try:
        # This immediately purges stale positive relationship buffs carried over
        # from v0.6.1 on the first loaded lot.
        moodlets.sync_household_moodlets()
        base.flog('V062 HARD MOODLET CLEANUP READY')
    except Exception:
        base.flog('V062 INITIAL CLEANUP FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v062
base.flog('V062 HARD MOODLET CLEANUP INSTALLED')

# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.1 — visible relationship moodlets."""

import traceback

import sims4.resources

import deep_relationships as base
import zz_deep_relationships_grievances as grievances

VERSION = '0.4.1'

BUFF_LIGHT_IRRITATION = 9809346411725758677
BUFF_ACCUMULATED_RESENTMENT = 14935880521011841611
BUFF_SERIOUS_CONFLICT = 14816115564650603146
BUFF_DEEP_HURT = 16750057278039550849
BUFF_BETRAYED_TRUST = 14632315915397281344

CONFLICT_BUFFS = (
    BUFF_LIGHT_IRRITATION,
    BUFF_ACCUMULATED_RESENTMENT,
    BUFF_SERIOUS_CONFLICT,
    BUFF_DEEP_HURT,
)
ALL_BUFFS = CONFLICT_BUFFS + (BUFF_BETRAYED_TRUST,)

base.VERSION = VERSION


def _buff_manager():
    try:
        return base.services.get_instance_manager(sims4.resources.Types.BUFF)
    except Exception:
        return None


def _buff_type(buff_id):
    manager = _buff_manager()
    if manager is None:
        return None
    try:
        return manager.get(int(buff_id))
    except Exception:
        return None


def _has_buff(sim_info, buff_type):
    if sim_info is None or buff_type is None:
        return False
    try:
        return bool(sim_info.has_buff(buff_type))
    except Exception:
        return False


def _records_for_sim(sim_info):
    if sim_info is None:
        return ()
    try:
        sim_id = int(sim_info.sim_id)
    except Exception:
        return ()
    result = []
    try:
        for record in tuple(base.slot_state().values()):
            try:
                if int(record.get('source_id', 0)) == sim_id:
                    result.append(record)
            except Exception:
                pass
    except Exception:
        base.flog('MOODLET RECORD LOOKUP FAILED')
        base.flog(traceback.format_exc())
    return tuple(result)


def _desired_moodlets(sim_info):
    max_resentment = 0.0
    max_infidelity = 0.0
    for record in _records_for_sim(sim_info):
        try:
            grievances._grievance_fields(record)
            max_resentment = max(
                max_resentment,
                float(grievances._recalculate_resentment(record))
            )
            infidelity = record.get('grievances', {}).get('infidelity')
            if isinstance(infidelity, dict):
                max_infidelity = max(
                    max_infidelity,
                    float(infidelity.get('severity', 0.0) or 0.0)
                )
        except Exception:
            base.flog('MOODLET RECORD EVALUATION FAILED')
            base.flog(traceback.format_exc())

    desired = set()
    if max_resentment >= 70.0:
        desired.add(BUFF_DEEP_HURT)
    elif max_resentment >= 45.0:
        desired.add(BUFF_SERIOUS_CONFLICT)
    elif max_resentment >= 25.0:
        desired.add(BUFF_ACCUMULATED_RESENTMENT)
    elif max_resentment >= 8.0:
        desired.add(BUFF_LIGHT_IRRITATION)

    if max_infidelity >= 1.0:
        desired.add(BUFF_BETRAYED_TRUST)
    return desired


def sync_sim_moodlets(sim_info):
    if sim_info is None:
        return False
    desired = _desired_moodlets(sim_info)
    changed = False
    manager = _buff_manager()
    if manager is None:
        base.flog('MOODLET BUFF MANAGER MISSING')
        return False

    for buff_id in ALL_BUFFS:
        try:
            buff_type = manager.get(buff_id)
            if buff_type is None:
                base.flog('MOODLET BUFF MISSING: {}'.format(buff_id))
                continue
            has_buff = _has_buff(sim_info, buff_type)
            if buff_id in desired:
                if not has_buff:
                    handle = sim_info.add_buff(buff_type)
                    if handle is not None:
                        changed = True
                        base.flog('MOODLET ADDED: sim {} buff {}'.format(
                            getattr(sim_info, 'sim_id', '?'), buff_id
                        ))
            elif has_buff:
                sim_info.remove_buff_by_type(buff_type)
                changed = True
                base.flog('MOODLET REMOVED: sim {} buff {}'.format(
                    getattr(sim_info, 'sim_id', '?'), buff_id
                ))
        except Exception:
            base.flog('MOODLET SYNC FAILED: sim {} buff {}'.format(
                getattr(sim_info, 'sim_id', '?'), buff_id
            ))
            base.flog(traceback.format_exc())
    return changed


def sync_household_moodlets():
    count = 0
    try:
        hh = base.household()
        for sim_info in base.sims_in_household(hh):
            if sync_sim_moodlets(sim_info):
                count += 1
        base.flog('MOODLET SYNC COMPLETE: {} sims changed'.format(count))
    except Exception:
        base.flog('HOUSEHOLD MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())
    return count


def _sync_record_owner(record):
    if record is None:
        return
    try:
        manager = base.services.sim_info_manager()
        sim_info = manager.get(int(record.get('source_id', 0))) if manager is not None else None
        if sim_info is not None:
            sync_sim_moodlets(sim_info)
    except Exception:
        base.flog('OWNER MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())


_ORIGINAL_ADD_GRIEVANCE = grievances.add_grievance


def _add_grievance_with_moodlet(record, reason, amount, count_event=True):
    result = _ORIGINAL_ADD_GRIEVANCE(record, reason, amount, count_event=count_event)
    try:
        _sync_record_owner(record)
    except Exception:
        base.flog('MOODLET UPDATE AFTER GRIEVANCE FAILED')
        base.flog(traceback.format_exc())
    return result


grievances.add_grievance = _add_grievance_with_moodlet


_ORIGINAL_DECAY_TICK = base.decay_tick


def _decay_tick_with_moodlets():
    result = _ORIGINAL_DECAY_TICK()
    try:
        sync_household_moodlets()
    except Exception:
        base.flog('MOODLET UPDATE AFTER DECAY FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_with_moodlets


_ORIGINAL_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_with_moodlets():
    result = _ORIGINAL_INITIALIZE_ZONE()
    try:
        sync_household_moodlets()
        missing = []
        manager = _buff_manager()
        for buff_id in ALL_BUFFS:
            if manager is None or manager.get(buff_id) is None:
                missing.append(buff_id)
        if missing:
            base.flog('MOODLET SYSTEM ACTIVE WITH MISSING BUFFS: {}'.format(missing))
        else:
            base.flog('MOODLET SYSTEM ACTIVE: all 5 buffs loaded')
    except Exception:
        base.flog('MOODLET ZONE INIT FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_with_moodlets

base.flog('MOODLET SYSTEM INSTALLED v{}'.format(VERSION))

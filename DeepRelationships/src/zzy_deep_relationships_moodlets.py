# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.2 — expanded visible relationship moodlets."""

import traceback

import sims4.resources

import deep_relationships as base
import zz_deep_relationships_grievances as grievances

VERSION = '0.4.2'
base.VERSION = VERSION

BUFF_LIGHT_IRRITATION = 9809346411725758677
BUFF_ACCUMULATED_RESENTMENT = 14935880521011841611
BUFF_SERIOUS_CONFLICT = 14816115564650603146
BUFF_DEEP_HURT = 16750057278039550849
BUFF_BETRAYED_TRUST = 14632315915397281344
BUFF_JEALOUSY = 12004666048318715101
BUFF_LOSS_OF_CONFIDENCE = 12004666048318715102
BUFF_LACK_OF_ATTENTION = 12004666048318715103
BUFF_LONELY_IN_RELATIONSHIP = 12004666048318715104
BUFF_UNMET_EXPECTATIONS = 12004666048318715105
BUFF_READY_TO_FORGIVE = 12004666048318715106
BUFF_SECOND_CHANCE = 12004666048318715107
BUFF_CLOSENESS = 12004666048318715108
BUFF_HAPPY_RELATIONSHIP = 12004666048318715109
BUFF_UNSTABLE_RELATIONSHIP = 12004666048318715110
BUFF_ON_VERGE_BREAKUP = 12004666048318715111

ALL_BUFFS = (
    BUFF_LIGHT_IRRITATION,
    BUFF_ACCUMULATED_RESENTMENT,
    BUFF_SERIOUS_CONFLICT,
    BUFF_DEEP_HURT,
    BUFF_BETRAYED_TRUST,
    BUFF_JEALOUSY,
    BUFF_LOSS_OF_CONFIDENCE,
    BUFF_LACK_OF_ATTENTION,
    BUFF_LONELY_IN_RELATIONSHIP,
    BUFF_UNMET_EXPECTATIONS,
    BUFF_READY_TO_FORGIVE,
    BUFF_SECOND_CHANCE,
    BUFF_CLOSENESS,
    BUFF_HAPPY_RELATIONSHIP,
    BUFF_UNSTABLE_RELATIONSHIP,
    BUFF_ON_VERGE_BREAKUP,
)


def _buff_manager():
    try:
        return base.services.get_instance_manager(sims4.resources.Types.BUFF)
    except Exception:
        return None


def _records_for_sim(sim_info):
    if sim_info is None:
        return ()
    try:
        sim_id = int(sim_info.sim_id)
    except Exception:
        return ()
    records = []
    try:
        for record in tuple(base.slot_state().values()):
            try:
                if int(record.get('source_id', 0)) == sim_id:
                    records.append(record)
            except Exception:
                pass
    except Exception:
        base.flog('V042 MOODLET RECORD LOOKUP FAILED')
        base.flog(traceback.format_exc())
    return tuple(records)


def _record_metrics(record):
    grievances._grievance_fields(record)
    grievance_map = record.get('grievances', {})
    if not isinstance(grievance_map, dict):
        grievance_map = {}

    def grievance_value(key):
        item = grievance_map.get(key)
        if not isinstance(item, dict):
            return 0.0
        try:
            return float(item.get('severity', 0.0) or 0.0)
        except Exception:
            return 0.0

    return {
        'resentment': float(grievances._recalculate_resentment(record) or 0.0),
        'love': float(record.get('love', 0.0) or 0.0),
        'trust': float(record.get('trust', 0.0) or 0.0),
        'attachment': float(record.get('attachment', 0.0) or 0.0),
        'compatibility': float(record.get('compatibility', 0.0) or 0.0),
        'satisfaction': float(record.get('satisfaction', 0.0) or 0.0),
        'quiet_steps': int(record.get('quiet_steps', 0) or 0),
        'infidelity': grievance_value('infidelity'),
        'neglect': grievance_value('neglect'),
        'romantic_hurt': grievance_value('romantic_hurt'),
    }


def _desired_for_record(record):
    m = _record_metrics(record)
    desired = set()
    r = m['resentment']

    # Conflict ladder: one moodlet at a time.
    if r >= 70:
        desired.add(BUFF_DEEP_HURT)
    elif r >= 45:
        desired.add(BUFF_SERIOUS_CONFLICT)
    elif r >= 25:
        desired.add(BUFF_ACCUMULATED_RESENTMENT)
    elif r >= 8:
        desired.add(BUFF_LIGHT_IRRITATION)

    # Trust and betrayal.
    if m['infidelity'] >= 1:
        desired.add(BUFF_BETRAYED_TRUST)
        if m['trust'] < 55 or m['romantic_hurt'] >= 10:
            desired.add(BUFF_JEALOUSY)
    elif m['romantic_hurt'] >= 10 and m['trust'] < 55:
        desired.add(BUFF_JEALOUSY)

    if m['love'] >= 25 and (m['trust'] < 40 or m['satisfaction'] < 30):
        desired.add(BUFF_LOSS_OF_CONFIDENCE)

    # Attention and expectations.
    if m['neglect'] >= 4 or m['quiet_steps'] >= 12:
        desired.add(BUFF_LACK_OF_ATTENTION)
    if (m['neglect'] >= 12 or m['quiet_steps'] >= 20) and m['attachment'] >= 40:
        desired.add(BUFF_LONELY_IN_RELATIONSHIP)
    if m['compatibility'] < 42 and m['satisfaction'] < 48 and m['love'] >= 25:
        desired.add(BUFF_UNMET_EXPECTATIONS)

    # Reconciliation and positive recovery.
    if 8 <= r < 35 and m['love'] >= 60 and m['trust'] >= 35:
        desired.add(BUFF_READY_TO_FORGIVE)
    if 1 <= r < 25 and m['love'] >= 65 and m['satisfaction'] >= 40 and m['trust'] >= 40:
        desired.add(BUFF_SECOND_CHANCE)
    if r < 8 and m['love'] >= 65 and m['trust'] >= 60 and m['attachment'] >= 55 and m['satisfaction'] >= 55:
        desired.add(BUFF_CLOSENESS)

    # Overall relationship condition.
    if m['love'] < 25 and m['trust'] < 25 and m['satisfaction'] < 20:
        desired.add(BUFF_ON_VERGE_BREAKUP)
    elif r >= 25 or (m['satisfaction'] < 40 and m['love'] >= 35):
        desired.add(BUFF_UNSTABLE_RELATIONSHIP)
    elif r < 8 and m['love'] >= 75 and m['trust'] >= 70 and m['satisfaction'] >= 70:
        desired.add(BUFF_HAPPY_RELATIONSHIP)

    return desired


def _desired_moodlets(sim_info):
    desired = set()
    for record in _records_for_sim(sim_info):
        try:
            desired.update(_desired_for_record(record))
        except Exception:
            base.flog('V042 MOODLET RECORD EVALUATION FAILED')
            base.flog(traceback.format_exc())
    return desired


def _has_buff(sim_info, buff_type):
    if sim_info is None or buff_type is None:
        return False
    try:
        return bool(sim_info.has_buff(buff_type))
    except Exception:
        return False


def sync_sim_moodlets(sim_info):
    if sim_info is None:
        return False
    manager = _buff_manager()
    if manager is None:
        base.flog('V042 MOODLET BUFF MANAGER MISSING')
        return False
    desired = _desired_moodlets(sim_info)
    changed = False
    for buff_id in ALL_BUFFS:
        try:
            buff_type = manager.get(buff_id)
            if buff_type is None:
                base.flog('V042 MOODLET BUFF MISSING: {}'.format(buff_id))
                continue
            has_buff = _has_buff(sim_info, buff_type)
            if buff_id in desired and not has_buff:
                handle = sim_info.add_buff(buff_type)
                if handle is not None:
                    changed = True
                    base.flog('V042 MOODLET ADDED: sim {} buff {}'.format(getattr(sim_info, 'sim_id', '?'), buff_id))
            elif buff_id not in desired and has_buff:
                sim_info.remove_buff_by_type(buff_type)
                changed = True
                base.flog('V042 MOODLET REMOVED: sim {} buff {}'.format(getattr(sim_info, 'sim_id', '?'), buff_id))
        except Exception:
            base.flog('V042 MOODLET SYNC FAILED: sim {} buff {}'.format(getattr(sim_info, 'sim_id', '?'), buff_id))
            base.flog(traceback.format_exc())
    return changed


def sync_household_moodlets():
    changed = 0
    try:
        hh = base.household()
        for sim_info in base.sims_in_household(hh):
            if sync_sim_moodlets(sim_info):
                changed += 1
        base.flog('V042 MOODLET SYNC COMPLETE: {} sims changed'.format(changed))
    except Exception:
        base.flog('V042 HOUSEHOLD MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())
    return changed


def _sync_record_owner(record):
    if record is None:
        return
    try:
        manager = base.services.sim_info_manager()
        sim_info = manager.get(int(record.get('source_id', 0))) if manager is not None else None
        if sim_info is not None:
            sync_sim_moodlets(sim_info)
    except Exception:
        base.flog('V042 OWNER MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())


_ORIGINAL_ADD_GRIEVANCE = grievances.add_grievance


def _add_grievance_v042(record, reason, amount, count_event=True):
    result = _ORIGINAL_ADD_GRIEVANCE(record, reason, amount, count_event=count_event)
    try:
        _sync_record_owner(record)
    except Exception:
        base.flog('V042 MOODLET UPDATE AFTER GRIEVANCE FAILED')
        base.flog(traceback.format_exc())
    return result


grievances.add_grievance = _add_grievance_v042


_ORIGINAL_ON_DELTA = base.on_relationship_delta


def _on_relationship_delta_v042(source_id, target_id, delta, kind):
    result = _ORIGINAL_ON_DELTA(source_id, target_id, delta, kind)
    try:
        manager = base.services.sim_info_manager()
        sim_info = manager.get(int(source_id)) if manager is not None else None
        if sim_info is not None:
            sync_sim_moodlets(sim_info)
    except Exception:
        base.flog('V042 MOODLET UPDATE AFTER DELTA FAILED')
        base.flog(traceback.format_exc())
    return result


base.on_relationship_delta = _on_relationship_delta_v042


_ORIGINAL_DECAY_TICK = base.decay_tick


def _decay_tick_v042():
    result = _ORIGINAL_DECAY_TICK()
    try:
        sync_household_moodlets()
    except Exception:
        base.flog('V042 MOODLET UPDATE AFTER DECAY FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v042


_ORIGINAL_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v042():
    result = _ORIGINAL_INITIALIZE_ZONE()
    try:
        sync_household_moodlets()
        manager = _buff_manager()
        missing = []
        for buff_id in ALL_BUFFS:
            if manager is None or manager.get(buff_id) is None:
                missing.append(buff_id)
        if missing:
            base.flog('V042 MOODLET SYSTEM ACTIVE WITH MISSING BUFFS: {}'.format(missing))
        else:
            base.flog('V042 MOODLET SYSTEM ACTIVE: all 16 buffs loaded')
    except Exception:
        base.flog('V042 MOODLET ZONE INIT FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v042

base.flog('MOODLET SYSTEM INSTALLED v{} (16 moodlets)'.format(VERSION))

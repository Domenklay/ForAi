# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.5 — stage moodlets + jealousy context fix."""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzzz_deep_relationships_memory_v060 as memory
import zzzzzzzzzzzz_deep_relationships_breakup_v070 as breakup
import zzzzzzzzzzzzzzz_deep_relationships_stability_v072 as stability
import zzzzzzzzzzzzzzzz_deep_relationships_v073 as v073

VERSION = '0.7.5'
base.VERSION = VERSION
moodlets.VERSION = VERSION

# New stage-specific visible buffs. Existing buffers cover:
# argument/light conflict, deep conflict, betrayal, reconciliation and second chance.
BUFF_REFUSED_FORGIVE = 12004666048318715112
BUFF_RELATIONSHIP_PAUSE = 12004666048318715113
BUFF_BREAKUP = 12004666048318715114
BUFF_EX_PARTNERS = 12004666048318715115
BUFF_RECOVERY = 12004666048318715116

moodlets.BUFF_REFUSED_FORGIVE = BUFF_REFUSED_FORGIVE
moodlets.BUFF_RELATIONSHIP_PAUSE = BUFF_RELATIONSHIP_PAUSE
moodlets.BUFF_BREAKUP = BUFF_BREAKUP
moodlets.BUFF_EX_PARTNERS = BUFF_EX_PARTNERS
moodlets.BUFF_RECOVERY = BUFF_RECOVERY

_extra = (
    BUFF_REFUSED_FORGIVE,
    BUFF_RELATIONSHIP_PAUSE,
    BUFF_BREAKUP,
    BUFF_EX_PARTNERS,
    BUFF_RECOVERY,
)
if not all(buff_id in moodlets.ALL_BUFFS for buff_id in _extra):
    moodlets.ALL_BUFFS = tuple(moodlets.ALL_BUFFS) + tuple(
        buff_id for buff_id in _extra if buff_id not in moodlets.ALL_BUFFS
    )


def _grievance(record, key):
    if record is None:
        return 0.0
    try:
        grievances._grievance_fields(record)
        item = record.get('grievances', {}).get(key)
        if isinstance(item, dict):
            return max(0.0, float(item.get('severity', 0.0) or 0.0))
    except Exception:
        pass
    return 0.0


def _resentment(record):
    if record is None:
        return 0.0
    try:
        return float(grievances._recalculate_resentment(record) or 0.0)
    except Exception:
        return float(record.get('resentment', 0.0) or 0.0)


def _reverse(record):
    if record is None:
        return None
    try:
        return core._existing_record(
            int(record.get('target_id', 0) or 0),
            int(record.get('source_id', 0) or 0),
        )
    except Exception:
        return None


def _recent_conflict(record):
    try:
        return max(0, int(record.get('recent_conflict_steps', 0) or 0))
    except Exception:
        return 0


def _breakup_state(record):
    try:
        return str(record.get('breakup_state', 'none') or 'none')
    except Exception:
        return 'none'


def _repair_memory_recent(record):
    memories = record.get('relationship_memories') if isinstance(record, dict) else None
    if not isinstance(memories, list):
        return False
    repair_kinds = {
        'apology_accepted', 'admit_fault', 'forgiveness', 'second_chance',
        'save_relationship', 'reconnection', 'reunion', 'constructive_talk',
    }
    for item in reversed(memories):
        if not isinstance(item, dict):
            continue
        if str(item.get('kind', '')) not in repair_kinds:
            continue
        try:
            if int(item.get('age_steps', 99) or 99) <= 8:
                return True
        except Exception:
            pass
    return False


_PREVIOUS_DESIRED = moodlets._desired_for_record


def _desired_for_record_v075(record):
    desired = set(_PREVIOUS_DESIRED(record))
    if record is None:
        return desired

    reverse = _reverse(record)
    resentment = _resentment(record)
    pair_resentment = max(resentment, _resentment(reverse))
    state = _breakup_state(record)
    reverse_state = _breakup_state(reverse)
    states = {state, reverse_state}

    try:
        love = float(record.get('love', 0.0) or 0.0)
        attachment = float(record.get('attachment', 0.0) or 0.0)
    except Exception:
        love = attachment = 0.0

    # JEALOUSY FIX: ordinary arguments / romantic hurt are NOT jealousy.
    # Jealousy only appears when there is an actual infidelity grievance.
    desired.discard(moodlets.BUFF_JEALOUSY)
    if _grievance(record, 'infidelity') >= 1.0 and love >= 20.0 and attachment >= 20.0:
        desired.add(moodlets.BUFF_JEALOUSY)

    # Stage 1: argument. One fresh negative social is enough to show it.
    if _recent_conflict(record) > 0 and resentment < 25.0 and not states.intersection(('pause', 'ended')):
        desired.add(moodlets.BUFF_LIGHT_IRRITATION)

    # Existing Deep Hurt is now presented as Deep Conflict by STBL text.
    # Existing Betrayed Trust is now presented as Infidelity by STBL text.

    # Refusal to forgive is directional: only the hurt Sim carries it.
    if int(record.get('forgiveness_block_steps', 0) or 0) > 0:
        desired.add(BUFF_REFUSED_FORGIVE)
        desired.discard(moodlets.BUFF_READY_TO_FORGIVE)
    else:
        desired.discard(BUFF_REFUSED_FORGIVE)

    # Pause belongs to both directions of the pair.
    if 'pause' in states:
        desired.add(BUFF_RELATIONSHIP_PAUSE)
        desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)
        desired.discard(moodlets.BUFF_CLOSENESS)
        desired.discard(moodlets.BUFF_SECOND_CHANCE)
        desired.discard(BUFF_RECOVERY)
    else:
        desired.discard(BUFF_RELATIONSHIP_PAUSE)

    # Breakup -> Exes sequence.
    post_breakup = int(record.get('post_breakup_steps', 0) or 0)
    ex_steps = int(record.get('ex_partner_steps', 0) or 0)
    if 'ended' in states:
        desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)
        desired.discard(moodlets.BUFF_CLOSENESS)
        desired.discard(moodlets.BUFF_READY_TO_FORGIVE)
        desired.discard(moodlets.BUFF_SECOND_CHANCE)
        desired.discard(BUFF_RECOVERY)
        if post_breakup > 0:
            desired.add(BUFF_BREAKUP)
            desired.discard(BUFF_EX_PARTNERS)
        elif ex_steps > 0:
            desired.add(BUFF_EX_PARTNERS)
            desired.discard(BUFF_BREAKUP)
    else:
        desired.discard(BUFF_BREAKUP)
        desired.discard(BUFF_EX_PARTNERS)

    # Second Chance must mean an actual accepted second chance, not merely a
    # mathematical combination of mild hurt + remaining love.
    second_steps = int(record.get('second_chance_steps', 0) or 0)
    if second_steps <= 0:
        desired.discard(moodlets.BUFF_SECOND_CHANCE)

    # Reconciliation (existing Closeness buff, renamed in STBL) only follows a
    # real repair marker, not every healthy relationship.
    closeness_steps = int(record.get('closeness_steps', 0) or 0)
    if closeness_steps <= 0:
        desired.discard(moodlets.BUFF_CLOSENESS)
    elif resentment < 8.0 and not states.intersection(('pause', 'ended', 'decided')):
        desired.add(moodlets.BUFF_CLOSENESS)

    # Recovery follows Second Chance / save-relationship work.
    repairing = 'repairing' in states
    if second_steps <= 0 and repairing and pair_resentment < 45.0:
        desired.add(BUFF_RECOVERY)
    elif second_steps <= 0 and _repair_memory_recent(record) and pair_resentment < 25.0 and closeness_steps <= 0:
        desired.add(BUFF_RECOVERY)
    else:
        desired.discard(BUFF_RECOVERY)

    # Do not allow positive recovery presentation during a new active fight.
    if max(_recent_conflict(record), _recent_conflict(reverse)) > 0 and pair_resentment >= 8.0:
        desired.discard(moodlets.BUFF_CLOSENESS)
        desired.discard(BUFF_RECOVERY)

    return desired


moodlets._desired_for_record = _desired_for_record_v075


# ---------------------------------------------------------------------------
# Breakup stage markers.
# ---------------------------------------------------------------------------
_PREVIOUS_MARK_BREAKUP = breakup._mark_actual_breakup


def _mark_actual_breakup_v075(record):
    result = _PREVIOUS_MARK_BREAKUP(record)
    reverse = _reverse(record)
    for current in (record, reverse):
        if current is None:
            continue
        current['post_breakup_steps'] = max(12, int(current.get('post_breakup_steps', 0) or 0))
        current['ex_partner_steps'] = max(28, int(current.get('ex_partner_steps', 0) or 0))
        base.DIRTY = True
    return result


breakup._mark_actual_breakup = _mark_actual_breakup_v075


def _has_recent_breakup_memory(record):
    memories = record.get('relationship_memories') if isinstance(record, dict) else None
    if not isinstance(memories, list):
        return False
    for item in reversed(memories):
        if not isinstance(item, dict) or str(item.get('kind', '')) != 'breakup':
            continue
        try:
            return int(item.get('age_steps', 99) or 99) <= 4
        except Exception:
            return False
    return False


def _migrate_v075():
    changed = 0
    try:
        for record in tuple(base.slot_state().values()):
            if 'ex_partner_steps' not in record:
                record['ex_partner_steps'] = 0
                changed += 1
            if _breakup_state(record) == 'ended':
                if _has_recent_breakup_memory(record):
                    if int(record.get('post_breakup_steps', 0) or 0) <= 0:
                        record['post_breakup_steps'] = 12
                        changed += 1
                    if int(record.get('ex_partner_steps', 0) or 0) <= 0:
                        record['ex_partner_steps'] = 28
                        changed += 1
                elif int(record.get('ex_partner_steps', 0) or 0) <= 0:
                    record['ex_partner_steps'] = 8
                    changed += 1
        if changed:
            base.DIRTY = True
        base.flog('V075 STAGE MOODLET MIGRATION: {} fields'.format(changed))
    except Exception:
        base.flog('V075 MIGRATION FAILED')
        base.flog(traceback.format_exc())


_PREVIOUS_DECAY = base.decay_tick


def _decay_tick_v075():
    result = _PREVIOUS_DECAY()
    try:
        changed = False
        for record in tuple(base.slot_state().values()):
            old = int(record.get('ex_partner_steps', 0) or 0)
            if old > 0:
                record['ex_partner_steps'] = old - 1
                changed = True
        if changed:
            base.DIRTY = True
        moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V075 STAGE TICK FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v075


_PREVIOUS_INIT = base.initialize_zone


def _initialize_zone_v075():
    result = _PREVIOUS_INIT()
    try:
        _migrate_v075()
        moodlets.sync_household_moodlets()
        manager = moodlets._buff_manager()
        missing = [buff_id for buff_id in _extra if manager is None or manager.get(buff_id) is None]
        if missing:
            base.flog('V075 STAGE MOODLETS MISSING: {}'.format(missing))
        else:
            base.flog('V075 STAGE MOODLETS READY: 21 buffs total')
    except Exception:
        base.flog('V075 INIT FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v075
base.flog('V075 STAGE MOODLETS + JEALOUSY FIX INSTALLED')

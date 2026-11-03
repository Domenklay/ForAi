# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.6 — dedicated relationship stage moodlets.

Each major relationship-story stage now has its own Buff ID instead of reusing
or renaming older generic moodlets.  Reconciliation is intentionally one Buff
that can be reached both after an ordinary conflict and after a successful
post-breakup recovery.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzzzz_deep_relationships_memory_v060 as memory
import zzzzzzzzzzzz_deep_relationships_breakup_v070 as breakup
import zzzzzzzzzzzzzzzzz_deep_relationships_v075 as v075

VERSION = '0.7.6'
base.VERSION = VERSION
moodlets.VERSION = VERSION

# Dedicated v0.7.6 story-stage Buff IDs.
BUFF_STAGE_ARGUMENT = 12004666048318715120
BUFF_STAGE_DEEP_CONFLICT = 12004666048318715121
BUFF_STAGE_RECONCILIATION = 12004666048318715122
BUFF_STAGE_INFIDELITY = 12004666048318715123
BUFF_STAGE_REFUSED_FORGIVE = 12004666048318715124
BUFF_STAGE_PAUSE = 12004666048318715125
BUFF_STAGE_BREAKUP = 12004666048318715126
BUFF_STAGE_EXES = 12004666048318715127
BUFF_STAGE_SECOND_CHANCE = 12004666048318715128
BUFF_STAGE_RECOVERY = 12004666048318715129

STAGE_BUFFS = (
    BUFF_STAGE_ARGUMENT,
    BUFF_STAGE_DEEP_CONFLICT,
    BUFF_STAGE_RECONCILIATION,
    BUFF_STAGE_INFIDELITY,
    BUFF_STAGE_REFUSED_FORGIVE,
    BUFF_STAGE_PAUSE,
    BUFF_STAGE_BREAKUP,
    BUFF_STAGE_EXES,
    BUFF_STAGE_SECOND_CHANCE,
    BUFF_STAGE_RECOVERY,
)

moodlets.BUFF_STAGE_ARGUMENT = BUFF_STAGE_ARGUMENT
moodlets.BUFF_STAGE_DEEP_CONFLICT = BUFF_STAGE_DEEP_CONFLICT
moodlets.BUFF_STAGE_RECONCILIATION = BUFF_STAGE_RECONCILIATION
moodlets.BUFF_STAGE_INFIDELITY = BUFF_STAGE_INFIDELITY
moodlets.BUFF_STAGE_REFUSED_FORGIVE = BUFF_STAGE_REFUSED_FORGIVE
moodlets.BUFF_STAGE_PAUSE = BUFF_STAGE_PAUSE
moodlets.BUFF_STAGE_BREAKUP = BUFF_STAGE_BREAKUP
moodlets.BUFF_STAGE_EXES = BUFF_STAGE_EXES
moodlets.BUFF_STAGE_SECOND_CHANCE = BUFF_STAGE_SECOND_CHANCE
moodlets.BUFF_STAGE_RECOVERY = BUFF_STAGE_RECOVERY

if not all(buff_id in moodlets.ALL_BUFFS for buff_id in STAGE_BUFFS):
    moodlets.ALL_BUFFS = tuple(moodlets.ALL_BUFFS) + tuple(
        buff_id for buff_id in STAGE_BUFFS if buff_id not in moodlets.ALL_BUFFS
    )

# Old generic/reused Buffs are still part of the package because they are used by
# other relationship diagnostics, but the story-stage layer does not display
# them as the primary stage.  This prevents duplicate "stage" icons.
LEGACY_STAGE_PRESENTATION = {
    moodlets.BUFF_LIGHT_IRRITATION,
    moodlets.BUFF_ACCUMULATED_RESENTMENT,
    moodlets.BUFF_SERIOUS_CONFLICT,
    moodlets.BUFF_DEEP_HURT,
    moodlets.BUFF_BETRAYED_TRUST,
    moodlets.BUFF_CLOSENESS,
    moodlets.BUFF_SECOND_CHANCE,
    getattr(moodlets, 'BUFF_REFUSED_FORGIVE', 0),
    getattr(moodlets, 'BUFF_RELATIONSHIP_PAUSE', 0),
    getattr(moodlets, 'BUFF_BREAKUP', 0),
    getattr(moodlets, 'BUFF_EX_PARTNERS', 0),
    getattr(moodlets, 'BUFF_RECOVERY', 0),
}
LEGACY_STAGE_PRESENTATION.discard(0)

STAGE_LABELS = {
    'argument': 'Ссора',
    'deep_conflict': 'Глубокий конфликт',
    'reconciliation': 'Примирение',
    'infidelity': 'Измена',
    'refused_forgive': 'Не готов простить',
    'pause': 'Пауза в отношениях',
    'breakup': 'Расставание',
    'exes': 'Теперь бывшие',
    'second_chance': 'Второй шанс',
    'recovery': 'Восстановление отношений',
}

STAGE_TO_BUFF = {
    'argument': BUFF_STAGE_ARGUMENT,
    'deep_conflict': BUFF_STAGE_DEEP_CONFLICT,
    'reconciliation': BUFF_STAGE_RECONCILIATION,
    'infidelity': BUFF_STAGE_INFIDELITY,
    'refused_forgive': BUFF_STAGE_REFUSED_FORGIVE,
    'pause': BUFF_STAGE_PAUSE,
    'breakup': BUFF_STAGE_BREAKUP,
    'exes': BUFF_STAGE_EXES,
    'second_chance': BUFF_STAGE_SECOND_CHANCE,
    'recovery': BUFF_STAGE_RECOVERY,
}

NEGATIVE_STAGES = {
    'argument', 'deep_conflict', 'infidelity', 'refused_forgive',
    'pause', 'breakup', 'exes',
}


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


def _state(record):
    if record is None:
        return 'none'
    try:
        return str(record.get('breakup_state', 'none') or 'none')
    except Exception:
        return 'none'


def _steps(record, key):
    if record is None:
        return 0
    try:
        return max(0, int(record.get(key, 0) or 0))
    except Exception:
        return 0


def _recent_memory(record, kinds, max_age=8):
    if record is None:
        return False
    memories = record.get('relationship_memories')
    if not isinstance(memories, list):
        return False
    wanted = set(kinds)
    for item in reversed(memories):
        if not isinstance(item, dict):
            continue
        if str(item.get('kind', '')) not in wanted:
            continue
        try:
            if int(item.get('age_steps', 99) or 99) <= int(max_age):
                return True
        except Exception:
            pass
    return False


def _healthy_enough_for_reconciliation(record, reverse):
    records = [r for r in (record, reverse) if r is not None]
    if not records:
        return False
    if max(_resentment(r) for r in records) >= 8.0:
        return False
    for current in records:
        try:
            if float(current.get('trust', 0.0) or 0.0) < 40.0:
                return False
            if float(current.get('satisfaction', 0.0) or 0.0) < 40.0:
                return False
        except Exception:
            return False
    return True


def relationship_stage(record):
    """Return one primary story stage for this directional relationship."""
    if record is None:
        return None

    reverse = _reverse(record)
    states = {_state(record), _state(reverse)}
    pair_resentment = max(_resentment(record), _resentment(reverse))
    pair_recent_conflict = max(
        _steps(record, 'recent_conflict_steps'),
        _steps(reverse, 'recent_conflict_steps'),
    )

    # 1. Actual breakup has top priority and deliberately progresses to Exes.
    if 'ended' in states:
        post = max(_steps(record, 'post_breakup_steps'), _steps(reverse, 'post_breakup_steps'))
        ex_steps = max(_steps(record, 'ex_partner_steps'), _steps(reverse, 'ex_partner_steps'))
        if post > 0:
            return 'breakup'
        if ex_steps > 0:
            return 'exes'
        return 'exes'

    # 2. Pair decision stages.
    if 'pause' in states:
        return 'pause'

    # 3. Directional refusal belongs only to the hurt Sim.
    if _steps(record, 'forgiveness_block_steps') > 0:
        return 'refused_forgive'

    # 4. Actual infidelity only. Ordinary romantic hurt never becomes jealousy
    # or the Infidelity stage.
    if _grievance(record, 'infidelity') >= 1.0:
        return 'infidelity'

    # 5. A real accepted second chance dominates ordinary recovery.
    if max(_steps(record, 'second_chance_steps'), _steps(reverse, 'second_chance_steps')) > 0:
        return 'second_chance'

    # 6. Repairing after second chance/save relationship.
    if 'repairing' in states:
        return 'recovery'

    # 7. Reconciliation can happen after an ordinary conflict OR at the end of
    # post-breakup recovery.  It is the same Buff in both places in the chain.
    closeness = max(_steps(record, 'closeness_steps'), _steps(reverse, 'closeness_steps'))
    recent_repair = (
        _recent_memory(record, ('reconnection', 'reunion', 'save_relationship', 'forgiveness'), 8) or
        _recent_memory(reverse, ('reconnection', 'reunion', 'save_relationship', 'forgiveness'), 8)
    )
    if _healthy_enough_for_reconciliation(record, reverse) and (closeness > 0 or recent_repair):
        return 'reconciliation'

    # 8. Conflict ladder for the primary story stage is intentionally simple:
    # ordinary fight -> deep conflict.  The internal resentment value still
    # keeps all intermediate detail for reports and notifications.
    if pair_resentment >= 70.0:
        return 'deep_conflict'
    if pair_recent_conflict > 0 or pair_resentment >= 0.75:
        return 'argument'

    return None


_PREVIOUS_DESIRED = moodlets._desired_for_record


def _desired_for_record_v076(record):
    desired = set(_PREVIOUS_DESIRED(record))

    # Remove all legacy presentation Buffs that previously stood in for one of
    # the new dedicated stages.  Supporting statuses (loneliness, low trust,
    # instability, jealousy after real infidelity, etc.) may still coexist.
    desired.difference_update(LEGACY_STAGE_PRESENTATION)
    desired.difference_update(STAGE_BUFFS)

    stage = relationship_stage(record)
    if stage is None:
        return desired

    buff_id = STAGE_TO_BUFF.get(stage)
    if buff_id is not None:
        desired.add(buff_id)

    # A visible story stage should not sit beside the generic Happy Pair status.
    desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)

    # Jealousy is supplementary only to real infidelity.
    if stage != 'infidelity' and _grievance(record, 'infidelity') < 1.0:
        desired.discard(moodlets.BUFF_JEALOUSY)

    return desired


moodlets._desired_for_record = _desired_for_record_v076


# Add the current primary stage to the relationship report.
_PREVIOUS_RECORD_TEXT = base.record_text


def _record_text_v076(source, target, record):
    text = _PREVIOUS_RECORD_TEXT(source, target, record)
    stage = relationship_stage(record)
    label = STAGE_LABELS.get(stage)
    if label:
        return '{}\nЭтап отношений: {}'.format(text, label)
    return text


base.record_text = _record_text_v076


# Ensure the new stage set is immediately evaluated after load.
_PREVIOUS_INIT = base.initialize_zone


def _initialize_zone_v076():
    result = _PREVIOUS_INIT()
    try:
        moodlets.sync_household_moodlets()
        manager = moodlets._buff_manager()
        missing = [buff_id for buff_id in STAGE_BUFFS if manager is None or manager.get(buff_id) is None]
        if missing:
            base.flog('V076 DEDICATED STAGE BUFFS MISSING: {}'.format(missing))
        else:
            base.flog('V076 DEDICATED STAGE MOODLETS READY: 10 stage buffs')
    except Exception:
        base.flog('V076 STAGE INIT FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v076
base.flog('V076 FULL DEDICATED STAGE MOODLETS INSTALLED')

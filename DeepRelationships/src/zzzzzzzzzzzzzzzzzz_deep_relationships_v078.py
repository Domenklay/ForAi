# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.8 — stable visible relationship stages.

The ten dedicated v0.7.6 Buffs become the authoritative visible story-stage
presentation.  Exactly one primary stage is selected for the dominant tracked
relationship.  Stage Buffs are state indicators rather than clocks: package
v0.7.8 hides their timeout and gives them a very long technical lifetime; the
script removes/replaces them immediately when the relationship stage changes.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzzz_deep_relationships_memory_v060 as memory
import zzzzzzzzzzz_deep_relationships_breakup_v070 as breakup
import zzzzzzzzzzzzzzzzz_deep_relationships_v076 as v076

VERSION = '0.7.8'
base.VERSION = VERSION
moodlets.VERSION = VERSION

STAGE_BUFFS = tuple(v076.STAGE_BUFFS)
STAGE_TO_BUFF = dict(v076.STAGE_TO_BUFF)
STAGE_LABELS = dict(v076.STAGE_LABELS)

# Every older Buff that was previously used as a story-stage presentation is
# removed before the single v0.7.8 stage is applied. Supporting statuses such as
# loneliness, loss of confidence or instability may still coexist.
OLD_STAGE_BUFFS = set(v076.LEGACY_STAGE_PRESENTATION)
OLD_STAGE_BUFFS.update(STAGE_BUFFS)


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


def _steps(record, key):
    if record is None:
        return 0
    try:
        return max(0, int(record.get(key, 0) or 0))
    except Exception:
        return 0


def _state(record):
    if record is None:
        return 'none'
    try:
        return str(record.get('breakup_state', 'none') or 'none')
    except Exception:
        return 'none'


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
            if int(item.get('age_steps', 99)) <= int(max_age):
                return True
        except Exception:
            pass
    return False


def _healthy_for_reconciliation(record, reverse):
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


def _real_second_chance(record, reverse):
    """Distinguish an actual accepted second chance from ordinary forgiveness.

    v0.5 may use second_chance_steps as a generic post-forgiveness recovery
    marker.  The visible story stage must only say 'Second Chance' after the
    dedicated action was really accepted.
    """
    records = [r for r in (record, reverse) if r is not None]
    if not records:
        return False
    if max(_steps(r, 'second_chance_steps') for r in records) <= 0:
        return False
    for current in records:
        if str(current.get('reconciliation_stage', '') or '') == 'second_chance':
            return True
        if _recent_memory(current, ('second_chance',), 12):
            return True
    return False


def relationship_stage(record):
    """Return the single primary visible stage for the pair/direction."""
    if record is None:
        return None

    reverse = _reverse(record)
    records = [r for r in (record, reverse) if r is not None]
    states = {_state(r) for r in records}

    pair_resentment = max((_resentment(r) for r in records), default=0.0)
    recent_conflict = max((_steps(r, 'recent_conflict_steps') for r in records), default=0)
    post_breakup = max((_steps(r, 'post_breakup_steps') for r in records), default=0)
    closeness = max((_steps(r, 'closeness_steps') for r in records), default=0)

    # 1. A completed breakup is the strongest pair state.  The acute breakup
    # stage lasts while post_breakup_steps is active; afterwards the pair is
    # visibly 'Now Exes' until a real second chance/reunion changes the state.
    if 'ended' in states:
        return 'breakup' if post_breakup > 0 else 'exes'

    # 2. Pair decision stages override the underlying reason for the crisis.
    if 'pause' in states:
        return 'pause'

    # 3. A real accepted second chance must override historic infidelity.
    if _real_second_chance(record, reverse):
        return 'second_chance'

    # 4. After the second-chance window, repairing is its own visible stage.
    if 'repairing' in states:
        return 'recovery'

    # 5. 'Not ready to forgive' is directional and only belongs to the hurt Sim.
    if _steps(record, 'forgiveness_block_steps') > 0:
        return 'refused_forgive'

    # 6. Reconciliation is allowed to override old historic hurt only once the
    # pair is genuinely healthy enough and has an explicit recent repair marker.
    recent_repair = (
        _recent_memory(record, ('reconnection', 'reunion', 'save_relationship', 'forgiveness'), 8) or
        _recent_memory(reverse, ('reconnection', 'reunion', 'save_relationship', 'forgiveness'), 8)
    )
    if _healthy_for_reconciliation(record, reverse) and (closeness > 0 or recent_repair):
        return 'reconciliation'

    # 7. Infidelity is a distinct stage only for the actually hurt direction.
    if _grievance(record, 'infidelity') >= 1.0:
        return 'infidelity'

    # 8. Ordinary conflict ladder. Intermediate resentment remains visible in
    # the detailed relationship report; the stage moodlet intentionally keeps
    # only the two story beats requested by the player.
    if pair_resentment >= 70.0:
        return 'deep_conflict'
    if recent_conflict > 0 or pair_resentment >= 0.75:
        return 'argument'

    return None


_PREVIOUS_DESIRED = moodlets._desired_for_record


def _desired_for_record_v078(record):
    desired = set(_PREVIOUS_DESIRED(record))

    # Remove every old/reused story-stage Buff first. Exactly one dedicated v0.7.6
    # stage can then be added below.
    desired.difference_update(OLD_STAGE_BUFFS)

    stage = relationship_stage(record)
    if stage is None:
        return desired

    buff_id = STAGE_TO_BUFF.get(stage)
    if buff_id is not None:
        desired.add(buff_id)

    # A dramatic story stage and generic Happy Relationship are mutually exclusive.
    desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)

    # Jealousy is supplementary only to actual infidelity, never ordinary fighting.
    if _grievance(record, 'infidelity') < 1.0:
        desired.discard(moodlets.BUFF_JEALOUSY)

    return desired


moodlets._desired_for_record = _desired_for_record_v078


# Relationship report uses the same authoritative stage calculation as Buff UI.
_PREVIOUS_RECORD_TEXT = base.record_text


def _record_text_v078(source, target, record):
    text = _PREVIOUS_RECORD_TEXT(source, target, record)
    stage = relationship_stage(record)
    label = STAGE_LABELS.get(stage)
    # v0.7.6 already appended an older stage line. Avoid showing two lines by
    # replacing the final occurrence when present.
    marker = '\nЭтап отношений: '
    if marker in text:
        text = text.rsplit(marker, 1)[0]
    if label:
        return '{}\nЭтап отношений: {}'.format(text, label)
    return text


base.record_text = _record_text_v078


# On load, immediately purge old stage Buffs and apply the authoritative stage.
_PREVIOUS_INIT = base.initialize_zone


def _initialize_zone_v078():
    result = _PREVIOUS_INIT()
    try:
        moodlets.sync_household_moodlets()
        base.flog('V078 STAGE MOODLETS READY: authoritative persistent stage presentation')
    except Exception:
        base.flog('V078 STAGE INITIALIZATION FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v078
base.flog('V078 STABLE RELATIONSHIP STAGE MOODLETS INSTALLED')

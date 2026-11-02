# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.6 — core correctness cleanup.

Keeps v0.4.5 save semantics and tuning, but fixes relationship accounting:
- actual before/after vanilla deltas instead of requested increments;
- no double counting when a pair is first discovered;
- no new NPC<->NPC tracking outside the active household;
- compatibility becomes stable after initialization;
- previously tracked former partners remain queryable;
- overall state respects severe resentment;
- one dominant relationship drives visible relationship moodlets;
- periodic decay only advances relationships relevant to the active household;
- repetitive diagnostic logging is filtered in normal mode.
"""

import traceback
from functools import wraps

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets

VERSION = '0.4.6'
base.VERSION = VERSION
moodlets.VERSION = VERSION

DEBUG = False
_RAW_FLOG = base.flog


def _quiet_flog(message):
    text = str(message)
    important = (
        'FAILED', 'ERROR', 'INSTALLED', 'STATE CHANGE', 'PAIR CREATED',
        'GRIEVANCE', 'INFIDELITY', 'COMMITTED', 'RELOADED', 'RESET',
        'STARTED', 'MISSING', 'V046'
    )
    if DEBUG or any(token in text for token in important):
        _RAW_FLOG(text)


base.flog = _quiet_flog


def _active_household_ids():
    result = set()
    try:
        for sim_info in base.sims_in_household(base.household()):
            result.add(int(sim_info.sim_id))
    except Exception:
        pass
    return result


def _existing_record(source_id, target_id):
    try:
        return base.slot_state().get(base.pair_key(source_id, target_id))
    except Exception:
        return None


def _pair_relevant(source_id, target_id):
    active = _active_household_ids()
    try:
        return int(source_id) in active or int(target_id) in active
    except Exception:
        return False


def _normalize_owner(source_id, target_id):
    """Prefer the active-household sim as the directional owner when only one is active."""
    active = _active_household_ids()
    source_id = int(source_id)
    target_id = int(target_id)
    if source_id in active:
        return source_id, target_id, False
    if target_id in active:
        return target_id, source_id, True
    return source_id, target_id, False


def _scores_for_ids(source_id, target_id):
    try:
        manager = base.services.sim_info_manager()
        source = manager.get(int(source_id)) if manager is not None else None
        if source is None:
            return 0.0, 0.0
        return base.scores(source, int(target_id))
    except Exception:
        return 0.0, 0.0


# ---------------------------------------------------------------------------
# Stable compatibility + former relationship history
# ---------------------------------------------------------------------------
_LEGACY_MAKE_RECORD = base.make_record
_LEGACY_ROMANTIC_CONTEXT = base.romantic_context
_LEGACY_STATE_NAME = base.state_name
_LEGACY_ENSURE_PAIR = base.ensure_pair


def _make_record_v046(source, target, friendship, romance):
    record = _LEGACY_MAKE_RECORD(source, target, friendship, romance)
    record['compatibility_base'] = base.clamp(record.get('compatibility', 50.0))
    record['compatibility'] = record['compatibility_base']
    record['ever_romantic'] = True
    record['relationship_phase'] = 'active'
    return record


base.make_record = _make_record_v046


def _romantic_context_v046(source, target_id, romance_score, force=False):
    if _LEGACY_ROMANTIC_CONTEXT(source, target_id, romance_score, force=force):
        return True
    try:
        if _existing_record(source.sim_id, target_id) is not None:
            return True
    except Exception:
        pass
    return False


base.romantic_context = _romantic_context_v046


def _refresh_phase(record):
    if record is None:
        return
    try:
        manager = base.services.sim_info_manager()
        source = manager.get(int(record.get('source_id', 0))) if manager is not None else None
        target_id = int(record.get('target_id', 0))
        if source is None:
            return
        _, romance = base.scores(source, target_id)
        active_now = _LEGACY_ROMANTIC_CONTEXT(source, target_id, romance, force=False)
        phase = 'active' if active_now else 'former'
        if record.get('relationship_phase') != phase:
            record['relationship_phase'] = phase
            base.DIRTY = True
    except Exception:
        pass


def _state_name_v046(record):
    if record is None:
        return 'Развивающиеся отношения'
    if record.get('relationship_phase') == 'former':
        return 'Бывшие отношения'
    try:
        resentment = float(record.get('resentment', 0.0) or 0.0)
    except Exception:
        resentment = 0.0
    if resentment >= 70.0:
        return 'На грани разрыва'
    if resentment >= 45.0:
        return 'Кризис'
    if resentment >= 25.0:
        return 'Напряжённые отношения'
    return _LEGACY_STATE_NAME(record)


base.state_name = _state_name_v046


def _ensure_pair_v046(source_id, target_id, force=False):
    # Existing records are relationship history. Never lose them just because
    # vanilla romance later reached zero or the couple broke up.
    existing = _existing_record(source_id, target_id)
    if existing is not None:
        existing.setdefault('compatibility_base', base.clamp(existing.get('compatibility', 50.0)))
        existing['compatibility'] = base.clamp(existing.get('compatibility_base', 50.0))
        existing.setdefault('ever_romantic', True)
        _refresh_phase(existing)
        return existing

    # Do not create an ever-growing world database for NPC<->NPC activity.
    if not _pair_relevant(source_id, target_id):
        return None

    record = _LEGACY_ENSURE_PAIR(source_id, target_id, force=force)
    if record is not None:
        record.setdefault('compatibility_base', base.clamp(record.get('compatibility', 50.0)))
        record['compatibility'] = base.clamp(record.get('compatibility_base', 50.0))
        record.setdefault('ever_romantic', True)
        _refresh_phase(record)
    return record


base.ensure_pair = _ensure_pair_v046


# ---------------------------------------------------------------------------
# Actual vanilla delta accounting.
# The original v0.3 observer is still physically installed. These outer wrappers
# capture the pre-change values; when that observer calls base.on_relationship_delta
# we replace it with the v0.4.6 implementation below.
# ---------------------------------------------------------------------------
_DELTA_CONTEXT_STACK = []


def _service_score(service, sim_id_a, sim_id_b, track):
    try:
        return float(service.get_relationship_score(sim_id_a, sim_id_b, track=track))
    except Exception:
        return None


def _capture_context(service, sim_id_a, sim_id_b, track, kind):
    a_scores = _scores_for_ids(sim_id_a, sim_id_b)
    b_scores = _scores_for_ids(sim_id_b, sim_id_a)
    return {
        'service': service,
        'a': int(sim_id_a),
        'b': int(sim_id_b),
        'track': track,
        'kind': kind,
        'track_before': _service_score(service, sim_id_a, sim_id_b, track),
        'a_scores_before': a_scores,
        'b_scores_before': b_scores,
        'had_ab': _existing_record(sim_id_a, sim_id_b) is not None,
        'had_ba': _existing_record(sim_id_b, sim_id_a) is not None,
    }


def _context_for(source_id, target_id, kind):
    if not _DELTA_CONTEXT_STACK:
        return None
    ctx = _DELTA_CONTEXT_STACK[-1]
    try:
        if ctx['a'] == int(source_id) and ctx['b'] == int(target_id) and ctx['kind'] == kind:
            return ctx
    except Exception:
        pass
    return None


def _create_from_prechange(owner_id, other_id, kind, ctx, swapped):
    manager = base.services.sim_info_manager()
    if manager is None:
        return None
    owner = manager.get(int(owner_id))
    other = manager.get(int(other_id))
    if owner is None or other is None:
        return None

    before_scores = ctx['b_scores_before'] if swapped else ctx['a_scores_before']
    friendship_before, romance_before = before_scores
    friendship_now, romance_now = base.scores(owner, int(other_id))

    # Only create a brand-new relationship model when there is/was a genuine
    # romantic context. A rejected flirt from zero romance should not create an
    # eternal "former partner" record by itself.
    romantic_before = _LEGACY_ROMANTIC_CONTEXT(owner, int(other_id), romance_before, force=False)
    romantic_after = _LEGACY_ROMANTIC_CONTEXT(owner, int(other_id), romance_now, force=False)
    if not (romantic_before or romantic_after):
        return None

    record = base.make_record(owner, other, friendship_before, romance_before)
    record['relationship_phase'] = 'active'
    base.slot_state()[base.pair_key(owner_id, other_id)] = record
    base.DIRTY = True
    base.flog('PAIR CREATED V046: {} -> {}'.format(base.full_name(owner), base.full_name(other)))
    return record


def _actual_delta(source_id, target_id, supplied_delta, kind):
    ctx = _context_for(source_id, target_id, kind)
    if ctx is None or ctx.get('track_before') is None:
        try:
            return float(supplied_delta), ctx
        except Exception:
            return 0.0, ctx
    after = _service_score(ctx['service'], ctx['a'], ctx['b'], ctx['track'])
    if after is None:
        try:
            return float(supplied_delta), ctx
        except Exception:
            return 0.0, ctx
    return float(after) - float(ctx['track_before']), ctx


def _apply_metric_delta(record, delta, kind):
    if kind == 'romance':
        if delta > 0:
            record['love'] = base.clamp(record.get('love', 0.0) + delta * 0.30)
            record['satisfaction'] = base.clamp(record.get('satisfaction', 0.0) + delta * 0.18)
            record['attachment'] = base.clamp(record.get('attachment', 0.0) + delta * 0.08)
        else:
            record['love'] = base.clamp(record.get('love', 0.0) + delta * 0.25)
            record['satisfaction'] = base.clamp(record.get('satisfaction', 0.0) + delta * 0.30)
            record['trust'] = base.clamp(record.get('trust', 0.0) + delta * 0.10)
    elif kind == 'friendship':
        if delta > 0:
            record['trust'] = base.clamp(record.get('trust', 0.0) + delta * 0.20)
            record['attachment'] = base.clamp(record.get('attachment', 0.0) + delta * 0.05)
            record['satisfaction'] = base.clamp(record.get('satisfaction', 0.0) + delta * 0.08)
        else:
            record['trust'] = base.clamp(record.get('trust', 0.0) + delta * 0.35)
            record['satisfaction'] = base.clamp(record.get('satisfaction', 0.0) + delta * 0.25)
            record['love'] = base.clamp(record.get('love', 0.0) + delta * 0.05)

    # Compatibility describes fit, not how many friendly interactions were spammed.
    record.setdefault('compatibility_base', base.clamp(record.get('compatibility', 50.0)))
    record['compatibility'] = base.clamp(record.get('compatibility_base', 50.0))


def _on_relationship_delta_v046(source_id, target_id, supplied_delta, kind):
    try:
        actual, ctx = _actual_delta(source_id, target_id, supplied_delta, kind)
        if abs(actual) < 0.0001:
            return

        owner_id, other_id, swapped = _normalize_owner(source_id, target_id)
        record = _existing_record(owner_id, other_id)
        if record is None:
            if not _pair_relevant(owner_id, other_id):
                return
            if ctx is not None:
                record = _create_from_prechange(owner_id, other_id, kind, ctx, swapped)
            if record is None:
                record = base.ensure_pair(owner_id, other_id, force=False)
        if record is None:
            return

        record['quiet_steps'] = 0
        _apply_metric_delta(record, actual, kind)
        record.setdefault('ever_romantic', True)
        _refresh_phase(record)
        base.DIRTY = True

        if actual < -0.0001:
            magnitude = abs(actual)
            if kind == 'romance':
                grievances.add_grievance(
                    record, 'romantic_hurt', min(12.0, max(2.0, magnitude * 0.32))
                )
            elif kind == 'friendship':
                grievances.add_grievance(
                    record, 'arguments', min(10.0, max(1.5, magnitude * 0.28))
                )

        grievances.apply_resentment_caps(record)
        base.update_state(record)

        manager = base.services.sim_info_manager()
        sim_info = manager.get(int(owner_id)) if manager is not None else None
        if sim_info is not None:
            moodlets.sync_sim_moodlets(sim_info)

        base.flog('V046 DELTA: {} -> {} {} actual {:+.2f}'.format(
            owner_id, other_id, kind, actual
        ))
    except Exception:
        base.flog('V046 RELATIONSHIP DELTA FAILED')
        base.flog(traceback.format_exc())


base.on_relationship_delta = _on_relationship_delta_v046


# Outer wrappers capture pre-change values while leaving the proven v0.3 hooks
# intact underneath. The underneath hooks call the v0.4.6 handler above.
_CURRENT_ADD = base.RelationshipService.add_relationship_score


@wraps(_CURRENT_ADD)
def _add_relationship_score_v046(self, sim_id_a, sim_id_b, increment,
                                 track=base.DEFAULT, threshold=None, **kwargs):
    kind = base.relationship_kind(track)
    ctx = None
    if kind is not None:
        ctx = _capture_context(self, sim_id_a, sim_id_b, track, kind)
        _DELTA_CONTEXT_STACK.append(ctx)
    try:
        return _CURRENT_ADD(
            self, sim_id_a, sim_id_b, increment,
            track=track, threshold=threshold, **kwargs
        )
    finally:
        if ctx is not None and _DELTA_CONTEXT_STACK:
            _DELTA_CONTEXT_STACK.pop()


_add_relationship_score_v046._deeprel_v046_actual_delta = True
base.RelationshipService.add_relationship_score = _add_relationship_score_v046


_CURRENT_SET = base.RelationshipService.set_relationship_score


@wraps(_CURRENT_SET)
def _set_relationship_score_v046(self, sim_id_a, sim_id_b, value,
                                 track=base.DEFAULT, threshold=None, **kwargs):
    kind = base.relationship_kind(track)
    ctx = None
    if kind is not None:
        ctx = _capture_context(self, sim_id_a, sim_id_b, track, kind)
        _DELTA_CONTEXT_STACK.append(ctx)
    try:
        return _CURRENT_SET(
            self, sim_id_a, sim_id_b, value,
            track=track, threshold=threshold, **kwargs
        )
    finally:
        if ctx is not None and _DELTA_CONTEXT_STACK:
            _DELTA_CONTEXT_STACK.pop()


_set_relationship_score_v046._deeprel_v046_actual_delta = True
base.RelationshipService.set_relationship_score = _set_relationship_score_v046


# ---------------------------------------------------------------------------
# Periodic processing: only active-household-relevant records advance.
# ---------------------------------------------------------------------------
def _decay_tick_v046():
    try:
        for record in tuple(base.slot_state().values()):
            source_id = int(record.get('source_id', 0) or 0)
            target_id = int(record.get('target_id', 0) or 0)
            if not _pair_relevant(source_id, target_id):
                continue

            _refresh_phase(record)
            record['quiet_steps'] = int(record.get('quiet_steps', 0) or 0) + 1
            quiet = record['quiet_steps']

            if record.get('relationship_phase') != 'former' and quiet >= 8:
                attachment = base.clamp(record.get('attachment', 0.0))
                protection = min(0.65, attachment / 150.0)
                record['satisfaction'] = base.clamp(
                    record.get('satisfaction', 0.0) - 0.60 * (1.0 - protection)
                )
                if quiet >= 16:
                    record['attachment'] = base.clamp(record.get('attachment', 0.0) - 0.12)
                if quiet >= 24:
                    record['love'] = base.clamp(record.get('love', 0.0) - 0.08)

            grievances._age_grievances(record)
            if record.get('relationship_phase') != 'former':
                grievances._update_neglect_grievance(record)
            grievances.apply_resentment_caps(record)
            record['compatibility'] = base.clamp(record.get('compatibility_base', record.get('compatibility', 50.0)))
            base.update_state(record)
            base.DIRTY = True

        moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V046 DECAY TICK FAILED')
        base.flog(traceback.format_exc())


base.decay_tick = _decay_tick_v046


# ---------------------------------------------------------------------------
# Multiple partners: show moodlets for the relationship with the strongest
# current emotional impact instead of contradictory happy/crisis moodlets from
# several partners at once.
# ---------------------------------------------------------------------------
def _record_impact(record):
    m = moodlets._record_metrics(record)
    negative = (
        m['resentment'] * 2.0 +
        m['infidelity'] * 1.5 +
        max(0.0, 50.0 - m['trust']) +
        max(0.0, 50.0 - m['satisfaction']) +
        max(0.0, 35.0 - m['love'])
    )
    positive = m['love'] + m['trust'] + m['attachment'] + m['satisfaction']
    return negative, positive


def _desired_moodlets_v046(sim_info):
    records = list(moodlets._records_for_sim(sim_info))
    if not records:
        return set()
    scored = [(record, _record_impact(record)) for record in records]
    worst = max(scored, key=lambda item: item[1][0])
    if worst[1][0] >= 20.0:
        chosen = worst[0]
    else:
        chosen = max(scored, key=lambda item: item[1][1])[0]
    return moodlets._desired_for_record(chosen)


moodlets._desired_moodlets = _desired_moodlets_v046


# ---------------------------------------------------------------------------
# Migration of existing v0.4.5 records without resetting player progress.
# ---------------------------------------------------------------------------
def _migrate_records_v046():
    changed = 0
    try:
        manager = base.services.sim_info_manager()
        for record in tuple(base.slot_state().values()):
            if 'compatibility_base' not in record:
                record['compatibility_base'] = base.clamp(record.get('compatibility', 50.0))
                changed += 1
            record['compatibility'] = base.clamp(record.get('compatibility_base', 50.0))
            if 'ever_romantic' not in record:
                record['ever_romantic'] = True
                changed += 1
            _refresh_phase(record)
            # Refresh state silently during migration; no burst of notifications.
            record['last_state'] = base.state_name(record)
        if changed:
            base.DIRTY = True
        base.flog('V046 MIGRATION COMPLETE: {} records changed'.format(changed))
    except Exception:
        base.flog('V046 MIGRATION FAILED')
        base.flog(traceback.format_exc())


_CURRENT_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v046():
    result = _CURRENT_INITIALIZE_ZONE()
    try:
        _migrate_records_v046()
        moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V046 ZONE MIGRATION FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v046
base.flog('V046 CORE CLEANUP INSTALLED')

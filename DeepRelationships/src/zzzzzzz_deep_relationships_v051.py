# -*- coding: utf-8 -*-
"""Deep Relationships v0.5.1 — conflict roles and forgiveness direction.

Fixes two issues found in playtesting:
- negative relationship changes are attributed to a victim/offender pair instead
  of automatically making the active sim the resentful side;
- Forgive / Not ready to forgive are only offered to the victim, while Apologize
  / Admit fault are only offered when the target is the victim of the actor.

The mood-strength rebalance lives in the v0.5.1 package tuning.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation

VERSION = '0.5.1'
base.VERSION = VERSION
moodlets.VERSION = VERSION


def _active_sim_id():
    try:
        sim = base.active_sim()
        sim_info = getattr(sim, 'sim_info', sim)
        return int(sim_info.sim_id) if sim_info is not None else 0
    except Exception:
        return 0


def _mark_role(record, role, partner_id):
    if record is None:
        return
    record['last_conflict_role'] = str(role)
    record['last_conflict_partner_id'] = int(partner_id)
    base.DIRTY = True


def _role_matches(record, role, partner_id):
    if record is None:
        return False
    try:
        if str(record.get('last_conflict_role', '')) != str(role):
            return False
        return int(record.get('last_conflict_partner_id', 0) or 0) == int(partner_id)
    except Exception:
        return False


def _record_for_direction(source_id, target_id, kind, ctx=None):
    record = core._existing_record(source_id, target_id)
    if record is not None:
        return record
    if ctx is not None:
        try:
            swapped = int(source_id) == int(ctx.get('b', 0))
            record = core._create_from_prechange(
                int(source_id), int(target_id), kind, ctx, swapped
            )
        except Exception:
            record = None
    if record is None:
        try:
            record = base.ensure_pair(int(source_id), int(target_id), force=False)
        except Exception:
            record = None
    return record


def _sync_direction(record):
    if record is None:
        return
    try:
        manager = base.services.sim_info_manager()
        sim_info = manager.get(int(record.get('source_id', 0))) if manager is not None else None
        if sim_info is not None:
            moodlets.sync_sim_moodlets(sim_info)
    except Exception:
        base.flog('V051 MOODLET ROLE SYNC FAILED')
        base.flog(traceback.format_exc())


# A single social can cause the same negative track to be reported in both
# directions during one simulation tick. Keep one grievance event per pair/kind/tick.
_LAST_NEGATIVE = {}


def _sim_tick():
    try:
        service = base.services.time_service()
        now = getattr(service, 'sim_now', None)
        absolute = getattr(now, 'absolute_ticks', None)
        if callable(absolute):
            absolute = absolute()
        return int(absolute or 0)
    except Exception:
        return 0


def _duplicate_negative(a, b, kind):
    tick = _sim_tick()
    key = (min(int(a), int(b)), max(int(a), int(b)), str(kind))
    previous = _LAST_NEGATIVE.get(key)
    _LAST_NEGATIVE[key] = tick
    return tick != 0 and previous == tick


_PREVIOUS_DELTA = base.on_relationship_delta


def _on_relationship_delta_v051(source_id, target_id, supplied_delta, kind):
    try:
        actual, ctx = core._actual_delta(source_id, target_id, supplied_delta, kind)
    except Exception:
        actual, ctx = float(supplied_delta or 0.0), None

    # Positive changes keep the proven v0.4.6 accounting.
    if actual >= -0.0001:
        return _PREVIOUS_DELTA(source_id, target_id, supplied_delta, kind)

    try:
        source_id = int(source_id)
        target_id = int(target_id)
        if not core._pair_relevant(source_id, target_id):
            return
        if _duplicate_negative(source_id, target_id, kind):
            return

        # For player-triggered socials the selected/active Sim is the most
        # reliable initiator signal available at RelationshipService level.
        # If neither side is active, preserve the service call direction.
        active_id = _active_sim_id()
        if active_id == source_id:
            offender_id, victim_id = source_id, target_id
        elif active_id == target_id:
            offender_id, victim_id = target_id, source_id
        else:
            offender_id, victim_id = source_id, target_id

        victim_record = _record_for_direction(victim_id, offender_id, kind, ctx)
        offender_record = _record_for_direction(offender_id, victim_id, kind, ctx)
        if victim_record is None:
            return

        # The victim carries the emotional damage. The offender still has their
        # quiet timer reset because the pair interacted, but does not gain a
        # grievance merely for starting the argument.
        victim_record['quiet_steps'] = 0
        if offender_record is not None:
            offender_record['quiet_steps'] = 0

        core._apply_metric_delta(victim_record, actual, kind)
        magnitude = abs(float(actual))
        if kind == 'romance':
            grievances.add_grievance(
                victim_record, 'romantic_hurt',
                min(12.0, max(2.0, magnitude * 0.32))
            )
        elif kind == 'friendship':
            grievances.add_grievance(
                victim_record, 'arguments',
                min(10.0, max(1.5, magnitude * 0.28))
            )

        _mark_role(victim_record, 'victim', offender_id)
        _mark_role(offender_record, 'offender', victim_id)

        grievances.apply_resentment_caps(victim_record)
        base.update_state(victim_record)
        if offender_record is not None:
            base.update_state(offender_record)
        base.DIRTY = True

        _sync_direction(victim_record)
        _sync_direction(offender_record)
        base.flog('V051 CONFLICT ROLE: offender {} -> victim {} | {} {:+.2f}'.format(
            offender_id, victim_id, kind, actual
        ))
    except Exception:
        base.flog('V051 NEGATIVE DELTA FAILED')
        base.flog(traceback.format_exc())


base.on_relationship_delta = _on_relationship_delta_v051


# Infidelity and neglect are already directional in the grievance layer:
# source_id is the hurt/neglected Sim and target_id is their partner.
_PREVIOUS_ADD_GRIEVANCE = grievances.add_grievance


def _add_grievance_v051(record, reason, amount, count_event=True):
    result = _PREVIOUS_ADD_GRIEVANCE(record, reason, amount, count_event=count_event)
    try:
        if record is not None and reason in ('infidelity', 'neglect'):
            victim_id = int(record.get('source_id', 0) or 0)
            offender_id = int(record.get('target_id', 0) or 0)
            if victim_id and offender_id:
                _mark_role(record, 'victim', offender_id)
                reverse = core._existing_record(offender_id, victim_id)
                _mark_role(reverse, 'offender', victim_id)
    except Exception:
        base.flog('V051 SPECIAL GRIEVANCE ROLE FAILED')
        base.flog(traceback.format_exc())
    return result


grievances.add_grievance = _add_grievance_v051


# Tighten the reconciliation menu by role. Existing v0.5 records without role
# metadata simply do not show victim/offender-specific actions until the next
# conflict establishes who hurt whom; neutral "Discuss problems" still works.
_PREVIOUS_CAN_ACTION = reconciliation._can_action


def _can_action_v051(action, actor, target):
    if not _PREVIOUS_CAN_ACTION(action, actor, target):
        return False
    actor_info = reconciliation._sim_info(actor)
    target_info = reconciliation._sim_info(target)
    try:
        actor_id = int(actor_info.sim_id)
        target_id = int(target_info.sim_id)
    except Exception:
        return False
    actor_record, target_record = reconciliation._records(actor, target, create=False)

    if action in ('forgive', 'not_ready'):
        return _role_matches(actor_record, 'victim', target_id)

    if action in ('apologize', 'admit_fault'):
        # The target must be the side currently carrying the hurt caused by actor.
        return _role_matches(target_record, 'victim', actor_id)

    return True


reconciliation._can_action = _can_action_v051


# Show the role in the relationship report while conflict is still meaningful.
_PREVIOUS_RECORD_TEXT = base.record_text


def _record_text_v051(source, target, record):
    text = _PREVIOUS_RECORD_TEXT(source, target, record)
    if record is None:
        return text
    try:
        if reconciliation._resentment(record) < 8.0:
            return text
        role = record.get('last_conflict_role')
        if role == 'victim':
            return text + '\nРоль в последнем конфликте: пострадавшая сторона'
        if role == 'offender':
            return text + '\nРоль в последнем конфликте: инициатор конфликта'
    except Exception:
        pass
    return text


base.record_text = _record_text_v051
base.flog('V051 CONFLICT ROLE SYSTEM INSTALLED')

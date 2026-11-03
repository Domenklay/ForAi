# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.2 — core stabilization.

Critical fixes after the v0.7.1 audit:
- remove temporary custom buffs by their active handle ids instead of relying on
  remove_buff_by_type(), which can refuse removal for commodity-backed buffs;
- make any meaningful pair contact reset neglect silence for both directions;
- use RelationshipService call direction for conflict roles so autonomous NPC
  socials are not attributed to whichever Sim happens to be selected;
- recognize real vanilla breakups from ex/broken-up/divorced relationship bits;
- stop old duplicate conflict notifications and de-duplicate pair breakup-risk
  notifications;
- classify stock notification urgency by event title, not by incidental words in
  a successful message body.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzz_deep_relationships_v051 as roles
import zzzzzzzz_deep_relationships_memory_v060 as memory
import zzzzzzzzzz_deep_relationships_v062 as moodlet_fix
import zzzzzzzzzzz_deep_relationships_breakup_v070 as breakup
import zzzzzzzzzzzzz_deep_relationships_notifications_v071 as notifications

VERSION = '0.7.2'
base.VERSION = VERSION
moodlets.VERSION = VERSION

# Vanilla relationship bits that explicitly mean a romantic relationship ended.
# These are much safer breakup signals than simply watching the romance score hit 0.
EX_RELATIONSHIP_BITS = {
    15811,  # romantic-Broken_Up
    15812,  # romantic-Broken_Up_Engaged
    15814,  # romantic-Despised_Ex
    15815,  # romantic-Divorced
    15817,  # romantic-Frustrated_Ex
}


# ---------------------------------------------------------------------------
# 1. Reliable custom Buff removal.
# ---------------------------------------------------------------------------
def _buff_component(sim_info):
    if sim_info is None:
        return None
    try:
        return getattr(sim_info, 'buff_component', None)
    except Exception:
        return None


def _active_buff_entry(sim_info, buff_type):
    component = _buff_component(sim_info)
    if component is None:
        return None
    try:
        active = getattr(component, '_active_buffs', None)
        if isinstance(active, dict):
            return active.get(buff_type)
    except Exception:
        pass
    return None


def _is_buff_present(sim_info, buff_type):
    try:
        if bool(sim_info.has_buff(buff_type)):
            return True
    except Exception:
        pass
    return _active_buff_entry(sim_info, buff_type) is not None


def _remove_buff_by_handles(sim_info, buff_type, buff_id):
    """Remove every handle of a Buff, then fall back to remove-by-type.

    Temporary commodity backed buffs can be ignored by remove_buff_by_type().
    Removing their active handles goes through BuffComponent.remove_buff(), which
    tears down the visible buff entry and sends the UI removal update.
    """
    if sim_info is None or buff_type is None:
        return False
    was_present = _is_buff_present(sim_info, buff_type)
    component = _buff_component(sim_info)

    try:
        entry = _active_buff_entry(sim_info, buff_type)
        handles = tuple(getattr(entry, 'handle_ids', ()) or ()) if entry is not None else ()
        for handle in handles:
            try:
                if component is not None:
                    component.remove_buff(handle, update_mood=True, immediate=True)
                else:
                    sim_info.remove_buff(handle, update_mood=True, immediate=True)
            except TypeError:
                # Older signatures do not expose the immediate kwarg.
                try:
                    if component is not None:
                        component.remove_buff(handle, update_mood=True)
                    else:
                        sim_info.remove_buff(handle, update_mood=True)
                except Exception:
                    pass
            except Exception:
                pass
    except Exception:
        base.flog('V072 BUFF HANDLE REMOVE FAILED: sim {} buff {}'.format(
            getattr(sim_info, 'sim_id', '?'), buff_id
        ))
        base.flog(traceback.format_exc())

    # Fallback for ordinary non-temporary buffs / versions where the handle list
    # is not exposed. This is deliberately second, not first.
    if _is_buff_present(sim_info, buff_type):
        try:
            sim_info.remove_buff_by_type(buff_type)
        except Exception:
            pass

    # One more handle pass covers multiple handles on the same tuned Buff.
    if _is_buff_present(sim_info, buff_type):
        try:
            entry = _active_buff_entry(sim_info, buff_type)
            handles = tuple(getattr(entry, 'handle_ids', ()) or ()) if entry is not None else ()
            for handle in handles:
                try:
                    if component is not None:
                        component.remove_buff(handle, update_mood=True, immediate=True)
                except Exception:
                    pass
        except Exception:
            pass

    still_present = _is_buff_present(sim_info, buff_type)
    if was_present and not still_present:
        base.flog('V072 MOODLET REMOVED BY HANDLE: sim {} buff {}'.format(
            getattr(sim_info, 'sim_id', '?'), buff_id
        ))
        return True
    if still_present:
        base.flog('V072 MOODLET STILL PRESENT: sim {} buff {}'.format(
            getattr(sim_info, 'sim_id', '?'), buff_id
        ))
    return False


def _sim_has_any_pair_problem(sim_info):
    try:
        for record in tuple(moodlets._records_for_sim(sim_info)):
            if moodlet_fix._pair_problem(record):
                return True
    except Exception:
        pass
    return False


_PREVIOUS_DESIRED_MOODLETS = moodlets._desired_moodlets


def _desired_moodlets_v072(sim_info):
    desired = set(_PREVIOUS_DESIRED_MOODLETS(sim_info))
    # Safety invariant: a Sim cannot display "Happy relationship" while ANY
    # tracked relationship currently contains fresh/unresolved hurt. This also
    # covers a very small fight that has not reached the old resentment=8 tier.
    if _sim_has_any_pair_problem(sim_info):
        desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)
    return desired


moodlets._desired_moodlets = _desired_moodlets_v072


def _sync_sim_moodlets_v072(sim_info):
    if sim_info is None:
        return False
    manager = moodlets._buff_manager()
    if manager is None:
        base.flog('V072 MOODLET BUFF MANAGER MISSING')
        return False
    try:
        desired = set(moodlets._desired_moodlets(sim_info))
    except Exception:
        base.flog('V072 DESIRED MOODLETS FAILED')
        base.flog(traceback.format_exc())
        return False

    changed = False
    # Remove first so contradictory old statuses disappear before additions.
    for buff_id in moodlets.ALL_BUFFS:
        if buff_id in desired:
            continue
        try:
            buff_type = manager.get(buff_id)
            if buff_type is not None and _is_buff_present(sim_info, buff_type):
                if _remove_buff_by_handles(sim_info, buff_type, buff_id):
                    changed = True
        except Exception:
            base.flog('V072 MOODLET PURGE FAILED: {}'.format(buff_id))
            base.flog(traceback.format_exc())

    for buff_id in desired:
        if buff_id not in moodlets.ALL_BUFFS:
            continue
        try:
            buff_type = manager.get(buff_id)
            if buff_type is not None and not _is_buff_present(sim_info, buff_type):
                handle = sim_info.add_buff(buff_type)
                if handle is not None:
                    changed = True
                    base.flog('V072 MOODLET ADDED: sim {} buff {}'.format(
                        getattr(sim_info, 'sim_id', '?'), buff_id
                    ))
        except Exception:
            base.flog('V072 MOODLET ADD FAILED: {}'.format(buff_id))
            base.flog(traceback.format_exc())
    return changed


moodlets.sync_sim_moodlets = _sync_sim_moodlets_v072


def _sync_household_v072():
    changed = 0
    try:
        for sim_info in base.sims_in_household(base.household()):
            if moodlets.sync_sim_moodlets(sim_info):
                changed += 1
    except Exception:
        base.flog('V072 HOUSEHOLD MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())
    return changed


moodlets.sync_household_moodlets = _sync_household_v072


# ---------------------------------------------------------------------------
# 2. Pair contact / neglect symmetry and safer conflict roles.
# ---------------------------------------------------------------------------
# RelationshipService score calls are actor -> target for social relationship
# effects. Do not override that direction merely because the other Sim is the
# currently selected Sim; this fixes autonomous NPC arguments being reversed.
def _service_direction_role_source():
    return 0


roles._active_sim_id = _service_direction_role_source


def _reset_pair_contact(source_id, target_id):
    changed = False
    for a, b in ((source_id, target_id), (target_id, source_id)):
        try:
            record = core._existing_record(int(a), int(b))
            if record is None:
                continue
            if int(record.get('quiet_steps', 0) or 0) != 0:
                record['quiet_steps'] = 0
                changed = True
            # A real contact starts a new neglect cycle. Existing neglect
            # grievance remains and can still require repair, but future silence
            # should be measured from this contact rather than an old marker.
            if int(record.get('neglect_marker', 0) or 0) != 0:
                record['neglect_marker'] = 0
                changed = True
        except Exception:
            pass
    if changed:
        base.DIRTY = True


def _sync_pair_sims(source_id, target_id):
    try:
        manager = base.services.sim_info_manager()
        if manager is None:
            return
        for sim_id in {int(source_id), int(target_id)}:
            sim_info = manager.get(sim_id)
            if sim_info is not None:
                moodlets.sync_sim_moodlets(sim_info)
    except Exception:
        base.flog('V072 PAIR MOODLET REFRESH FAILED')
        base.flog(traceback.format_exc())


_PREVIOUS_DELTA = base.on_relationship_delta


def _on_relationship_delta_v072(source_id, target_id, supplied_delta, kind):
    try:
        actual, _ = core._actual_delta(source_id, target_id, supplied_delta, kind)
    except Exception:
        try:
            actual = float(supplied_delta or 0.0)
        except Exception:
            actual = 0.0

    result = _PREVIOUS_DELTA(source_id, target_id, supplied_delta, kind)
    try:
        if abs(actual) >= 0.05:
            _reset_pair_contact(source_id, target_id)
        _sync_pair_sims(source_id, target_id)
    except Exception:
        base.flog('V072 DELTA STABILIZATION FAILED')
        base.flog(traceback.format_exc())
    return result


base.on_relationship_delta = _on_relationship_delta_v072


# ---------------------------------------------------------------------------
# 3. Explicit vanilla breakup detection.
# ---------------------------------------------------------------------------
def _relationship_bits(source_id, target_id):
    try:
        manager = base.services.sim_info_manager()
        source = manager.get(int(source_id)) if manager is not None else None
        if source is None:
            return ()
        return tuple(source.relationship_tracker.get_all_bits(int(target_id)) or ())
    except Exception:
        return ()


def _has_explicit_ex_bit(source_id, target_id):
    for bit in _relationship_bits(source_id, target_id):
        try:
            if grievances._bit_guid(bit) in EX_RELATIONSHIP_BITS:
                return True
        except Exception:
            pass
    return False


def _mark_breakup_pair(source_id, target_id, notify=True):
    records = []
    for a, b in ((source_id, target_id), (target_id, source_id)):
        record = core._existing_record(int(a), int(b))
        if record is not None:
            records.append(record)
    if not records:
        return False

    already_ended = all(breakup._breakup_state(r) == 'ended' for r in records)
    if not already_ended:
        breakup._mark_actual_breakup(records[0])
    for record in records:
        record['relationship_phase'] = 'former'
        record['breakup_state'] = 'ended'
        base.DIRTY = True

    if notify and not already_ended:
        try:
            manager = base.services.sim_info_manager()
            a = manager.get(int(source_id)) if manager is not None else None
            b = manager.get(int(target_id)) if manager is not None else None
            notifications.relationship_notify(
                'Отношения завершены',
                '{} и {} теперь считаются бывшими партнёрами. История отношений сохранена.'.format(
                    base.full_name(a), base.full_name(b)
                ),
                icon_sim=b,
                urgent=True,
            )
        except Exception:
            pass
    _sync_pair_sims(source_id, target_id)
    return True


# Replace score-only phase refresh. A low/zero romance score by itself is not a
# breakup. Explicit ex bits or our already-recorded ended state are authoritative.
def _refresh_phase_v072(record):
    if record is None:
        return
    try:
        source_id = int(record.get('source_id', 0) or 0)
        target_id = int(record.get('target_id', 0) or 0)
        if not source_id or not target_id:
            return

        explicit_ex = _has_explicit_ex_bit(source_id, target_id) or _has_explicit_ex_bit(target_id, source_id)
        state = breakup._breakup_state(record)
        if explicit_ex or state == 'ended':
            if record.get('relationship_phase') != 'former':
                record['relationship_phase'] = 'former'
                base.DIRTY = True
            if explicit_ex and state != 'ended':
                _mark_breakup_pair(source_id, target_id, notify=False)
            return

        # Official partners and accepted second-chance recovery are active.
        official = breakup._is_official_partner(source_id, target_id)
        second = int(record.get('second_chance_steps', 0) or 0) > 0
        repairing = state == 'repairing'
        if official or second or repairing:
            if record.get('relationship_phase') != 'active':
                record['relationship_phase'] = 'active'
                base.DIRTY = True
            return

        # Otherwise preserve the current historical phase instead of deriving a
        # breakup from the romance score alone.
        record.setdefault('relationship_phase', 'active')
    except Exception:
        base.flog('V072 PHASE REFRESH FAILED')
        base.flog(traceback.format_exc())


core._refresh_phase = _refresh_phase_v072


@base.inject_to(base.RelationshipService, 'add_relationship_bit', '_deeprel_v072_breakup_bit_wrapped')
def _observe_breakup_bit(original, self, actor_sim_id, target_sim_id, bit_to_add,
                         force_add=False, from_load=False, send_rel_change_event=True,
                         allow_readdition=True):
    result = original(
        self, actor_sim_id, target_sim_id, bit_to_add,
        force_add=force_add, from_load=from_load,
        send_rel_change_event=send_rel_change_event,
        allow_readdition=allow_readdition
    )
    try:
        bit_id = grievances._bit_guid(bit_to_add)
        if bit_id in EX_RELATIONSHIP_BITS:
            _mark_breakup_pair(actor_sim_id, target_sim_id, notify=not from_load)
    except Exception:
        base.flog('V072 BREAKUP BIT OBSERVER FAILED')
        base.flog(traceback.format_exc())
    return result


# ---------------------------------------------------------------------------
# 4. Centralized notification cleanup.
# ---------------------------------------------------------------------------
# Old v0.4 grievance transitions generated a second notification for the same
# threshold that v0.7.1 now reports. Keep only the new colored notification.
def _no_legacy_conflict_notification(record, old_state, new_state):
    return None


grievances._maybe_notify_conflict = _no_legacy_conflict_notification

# Exact/title-driven urgency. Successful messages stay blue even if their body
# contains words such as "обида" or "конфликт".
_URGENT_TITLES = {
    'Извинение не принято',
    'Отношения пока не удалось спасти',
    'Пауза в отношениях',
    'Решение о расставании',
    'Отношения завершены',
    'Напряжение в отношениях',
    'Накопленная обида',
    'Серьёзный конфликт',
    'Глубокая обида',
    'Доверие стало низким',
    'Доверие серьёзно разрушено',
    'Риск расставания вырос',
}

_POSITIVE_TITLES = {
    'Извинение принято',
    'Признание вины',
    'Прощение',
    'Второй шанс',
    'Разговор об отношениях',
    'Попытка сохранить отношения',
    'Обида начинает ослабевать',
    'Напряжение снизилось',
    'Осталось раздражение',
    'Конфликт почти исчерпан',
    'Доверие восстанавливается',
    'Доверие стало устойчивым',
    'Риск расставания снизился',
    'Отношения выходят из опасной зоны',
}


def _is_urgent_v072(title, text):
    title_text = str(title or '').strip()
    if title_text in _POSITIVE_TITLES:
        return False
    if title_text in _URGENT_TITLES:
        return True
    lowered = title_text.lower()
    return any(token in lowered for token in (
        'измена', 'предатель', 'глубокая обида', 'серьёзный конфликт',
        'расстав', 'разрыв', 'развод', 'критичес', 'на грани',
    ))


notifications._is_urgent = _is_urgent_v072

# Suppress the legacy generic "state changed" toast. v0.7.1 already provides
# specific threshold messages, and keeping both is noisy/confusing.
_PREVIOUS_BASE_NOTIFY = base.notify


def _notify_v072(title, text, icon_sim=None):
    try:
        if str(title or '') == str(base.MOD_NAME):
            body = str(text or '')
            if 'отношения с' in body and 'теперь' in body:
                return False
    except Exception:
        pass
    return notifications.relationship_notify(
        title,
        text,
        icon_sim=icon_sim,
        urgent=_is_urgent_v072(title, text),
    )


base.notify = _notify_v072

# Risk belongs to the pair, while conflict/trust are directional. Emit a risk
# threshold notification only from one canonical direction when both records exist.
_PREVIOUS_RISK_NOTIFICATION = notifications._risk_notification


def _risk_notification_v072(record, old_band, new_band):
    try:
        reverse = core._existing_record(
            int(record.get('target_id', 0) or 0),
            int(record.get('source_id', 0) or 0),
        )
        if reverse is not None:
            source_id = int(record.get('source_id', 0) or 0)
            target_id = int(record.get('target_id', 0) or 0)
            if source_id > target_id:
                return
    except Exception:
        pass
    return _PREVIOUS_RISK_NOTIFICATION(record, old_band, new_band)


notifications._risk_notification = _risk_notification_v072


# ---------------------------------------------------------------------------
# 5. Load/tick cleanup and small migration.
# ---------------------------------------------------------------------------
def _migrate_v072():
    changed = 0
    try:
        for record in tuple(base.slot_state().values()):
            record.setdefault('stability_epoch', 72)
            # If vanilla currently has an explicit ex bit, make historical phase
            # authoritative even if an older layer left it active.
            source_id = int(record.get('source_id', 0) or 0)
            target_id = int(record.get('target_id', 0) or 0)
            if source_id and target_id and (
                _has_explicit_ex_bit(source_id, target_id) or
                _has_explicit_ex_bit(target_id, source_id)
            ):
                if record.get('relationship_phase') != 'former' or breakup._breakup_state(record) != 'ended':
                    record['relationship_phase'] = 'former'
                    record['breakup_state'] = 'ended'
                    changed += 1
        if changed:
            base.DIRTY = True
        base.flog('V072 MIGRATION COMPLETE: {} corrected records'.format(changed))
    except Exception:
        base.flog('V072 MIGRATION FAILED')
        base.flog(traceback.format_exc())


_PREVIOUS_INIT = base.initialize_zone


def _initialize_zone_v072():
    result = _PREVIOUS_INIT()
    try:
        _migrate_v072()
        # Purge stale Happy +3 immediately on first loaded lot when the save is
        # already in a conflict state.
        moodlets.sync_household_moodlets()
        base.flog('V072 CORE STABILIZATION READY')
    except Exception:
        base.flog('V072 INITIALIZATION FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v072


_PREVIOUS_DECAY = base.decay_tick


def _decay_tick_v072():
    result = _PREVIOUS_DECAY()
    try:
        # Keep explicit breakup phase authoritative and clean stale Buff UI on
        # the existing six-hour maintenance cycle as a fallback.
        for record in tuple(base.slot_state().values()):
            core._refresh_phase(record)
        moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V072 MAINTENANCE FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v072
base.flog('V072 CORE STABILIZATION INSTALLED')

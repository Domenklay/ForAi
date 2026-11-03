# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.1 — stock Sims 4 relationship notifications.

Uses only the game's native notification styles:
- DEFAULT: ordinary/positive information (blue in the standard UI)
- URGENT: serious relationship problems (orange in the standard UI)

The layer also tracks threshold transitions for conflict, trust and breakup risk.
Existing reconciliation/breakup notifications are automatically classified by
severity because base.notify is replaced globally after all previous layers load.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzzzz_deep_relationships_core_v046 as core
import zzzzzzzz_deep_relationships_memory_v060 as memory
import zzzzzzzzzzz_deep_relationships_v062 as moodlet_fix
import zzzzzzzzzzzz_deep_relationships_breakup_v070 as breakup

VERSION = '0.7.1'
base.VERSION = VERSION


# ---------------------------------------------------------------------------
# Native notification colour / urgency
# ---------------------------------------------------------------------------
_ORIGINAL_NOTIFY = base.notify

_URGENT_TITLE_WORDS = (
    'ссора', 'конфликт', 'обида', 'кризис', 'недовер', 'измен', 'предатель',
    'не принято', 'не принят', 'не удалось', 'не готов', 'одиноч', 'ревност',
    'пауза', 'дистанц', 'расстав', 'разрыв', 'развест', 'критичес', 'на грани',
    'риск расставания', 'решение о расставании',
)


def _is_urgent(title, text):
    value = '{} {}'.format(title or '', text or '').lower()
    return any(word in value for word in _URGENT_TITLE_WORDS)


def relationship_notify(title, text, icon_sim=None, urgent=False):
    """Show a native Sims 4 notification with stock urgency colour."""
    sim = base.active_sim()
    if sim is None:
        return False
    try:
        urgency = (
            base.UiDialogNotification.UiDialogNotificationUrgency.URGENT
            if urgent else
            base.UiDialogNotification.UiDialogNotificationUrgency.DEFAULT
        )
        dialog = base.UiDialogNotification.TunableFactory().default(
            sim,
            title=lambda **_: base.LocalizationHelperTuning.get_raw_text(str(title)),
            text=lambda **_: base.LocalizationHelperTuning.get_raw_text(str(text)),
            urgency=urgency,
        )
        icon_object = icon_sim if icon_sim is not None else sim
        if base.IconInfoData is not None:
            try:
                dialog.show_dialog(icon_override=base.IconInfoData(obj_instance=icon_object))
            except Exception:
                dialog.show_dialog()
        else:
            dialog.show_dialog()
        base.flog('V071 NOTIFICATION SHOWN [{}]: {}'.format(
            'URGENT' if urgent else 'DEFAULT', title
        ))
        return True
    except Exception:
        base.flog('V071 NATIVE NOTIFICATION FAILED')
        base.flog(traceback.format_exc())
        try:
            return _ORIGINAL_NOTIFY(title, text, icon_sim=icon_sim)
        except Exception:
            return False


def _notify_v071(title, text, icon_sim=None):
    return relationship_notify(
        title, text, icon_sim=icon_sim,
        urgent=_is_urgent(title, text),
    )


# All existing mod notifications now use native blue/orange severity automatically.
base.notify = _notify_v071


# ---------------------------------------------------------------------------
# Per-record transition tracking
# ---------------------------------------------------------------------------
def _notification_state(record):
    if record is None:
        return None
    value = record.get('notification_state')
    if not isinstance(value, dict):
        value = {}
        record['notification_state'] = value
        base.DIRTY = True
    return value


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


def _conflict_band(record):
    value = _resentment(record)
    if value >= 70.0:
        return 4
    if value >= 45.0:
        return 3
    if value >= 25.0:
        return 2
    if value >= 8.0:
        return 1
    return 0


def _trust_band(record):
    try:
        value = float(record.get('trust', 0.0) or 0.0)
    except Exception:
        value = 0.0
    if value < 25.0:
        return 0
    if value < 40.0:
        return 1
    if value < 60.0:
        return 2
    return 3


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


def _risk_value(record):
    if record is None:
        return 0.0
    try:
        return float(breakup._risk_for_records(record, _reverse(record)) or 0.0)
    except Exception:
        return 0.0


def _risk_band(record):
    value = _risk_value(record)
    if value >= 85.0:
        return 4
    if value >= 65.0:
        return 3
    if value >= 40.0:
        return 2
    if value >= 20.0:
        return 1
    return 0


def _names(record):
    source = None
    target = None
    try:
        manager = base.services.sim_info_manager()
        if manager is not None:
            source = manager.get(int(record.get('source_id', 0) or 0))
            target = manager.get(int(record.get('target_id', 0) or 0))
    except Exception:
        pass
    return source, target, base.full_name(source), base.full_name(target)


def _relevant_to_active_household(record):
    if record is None:
        return False
    try:
        active = core._active_household_ids()
        return (
            int(record.get('source_id', 0) or 0) in active or
            int(record.get('target_id', 0) or 0) in active
        )
    except Exception:
        return False


def _baseline_record(record):
    state = _notification_state(record)
    if state is None:
        return
    state['initialized'] = True
    state['conflict_band'] = _conflict_band(record)
    state['trust_band'] = _trust_band(record)
    state['risk_band'] = _risk_band(record)
    state['relationship_state'] = str(base.state_name(record))
    try:
        state['recovery_stage'] = str(memory._recovery_stage(record))
    except Exception:
        state['recovery_stage'] = ''
    base.DIRTY = True


def _conflict_notification(record, old_band, new_band):
    source, target, source_name, target_name = _names(record)
    if new_band > old_band:
        data = {
            1: ('Напряжение в отношениях', '{} начинает раздражаться из-за отношений с {}.'.format(source_name, target_name)),
            2: ('Накопленная обида', 'Обида {} на {} стала заметной. Обычных приятных действий уже может быть недостаточно.'.format(source_name, target_name)),
            3: ('Серьёзный конфликт', 'Между {} и {} возник серьёзный конфликт. Доверие и удовлетворённость будут восстанавливаться медленно.'.format(source_name, target_name)),
            4: ('Глубокая обида', '{} глубоко обижен(а) на {}. Отношения находятся в опасном состоянии.'.format(source_name, target_name)),
        }
        title, text = data.get(new_band, data[1])
        relationship_notify(title, text, icon_sim=target, urgent=True)
    elif new_band < old_band:
        data = {
            3: ('Обида начинает ослабевать', 'Глубокая обида {} на {} стала слабее, но конфликт ещё далёк от завершения.'.format(source_name, target_name)),
            2: ('Напряжение снизилось', 'Конфликт между {} и {} стал менее острым.'.format(source_name, target_name)),
            1: ('Осталось раздражение', '{} всё ещё раздражён(а) отношениями с {}, но сильная обида постепенно проходит.'.format(source_name, target_name)),
            0: ('Конфликт почти исчерпан', 'Активная обида {} на {} опустилась ниже конфликтного порога.'.format(source_name, target_name)),
        }
        title, text = data.get(new_band, data[0])
        relationship_notify(title, text, icon_sim=target, urgent=False)


def _trust_notification(record, old_band, new_band):
    source, target, source_name, target_name = _names(record)
    try:
        trust = float(record.get('trust', 0.0) or 0.0)
    except Exception:
        trust = 0.0
    if new_band < old_band:
        if new_band == 1:
            relationship_notify(
                'Доверие стало низким',
                '{} всё меньше доверяет {}. Текущее доверие: {:.0f}.'.format(source_name, target_name, trust),
                icon_sim=target, urgent=True,
            )
        elif new_band == 0:
            relationship_notify(
                'Доверие серьёзно разрушено',
                'Доверие {} к {} упало до {:.0f}. Без примирения восстановить отношения будет трудно.'.format(source_name, target_name, trust),
                icon_sim=target, urgent=True,
            )
    elif new_band > old_band:
        if new_band == 2:
            relationship_notify(
                'Доверие восстанавливается',
                '{} снова начинает доверять {}. Текущее доверие: {:.0f}.'.format(source_name, target_name, trust),
                icon_sim=target, urgent=False,
            )
        elif new_band == 3:
            relationship_notify(
                'Доверие стало устойчивым',
                'Доверие {} к {} восстановилось до {:.0f}.'.format(source_name, target_name, trust),
                icon_sim=target, urgent=False,
            )


def _risk_notification(record, old_band, new_band):
    source, target, source_name, target_name = _names(record)
    risk = _risk_value(record)
    if new_band > old_band and new_band >= 2:
        label = {2: 'средним', 3: 'высоким', 4: 'критическим'}.get(new_band, 'повышенным')
        relationship_notify(
            'Риск расставания вырос',
            'Риск расставания {} и {} стал {} — около {:.0f}%.'.format(source_name, target_name, label, risk),
            icon_sim=target, urgent=True,
        )
    elif new_band < old_band:
        # Notify recovery only when the pair crosses back below a meaningful danger tier.
        if old_band >= 3 and new_band <= 2:
            relationship_notify(
                'Риск расставания снизился',
                'У {} и {} риск расставания снизился примерно до {:.0f}%.'.format(source_name, target_name, risk),
                icon_sim=target, urgent=False,
            )
        elif old_band >= 2 and new_band <= 1:
            relationship_notify(
                'Отношения выходят из опасной зоны',
                'Риск расставания {} и {} теперь около {:.0f}%.'.format(source_name, target_name, risk),
                icon_sim=target, urgent=False,
            )


def _check_record_notifications(record, allow_notifications=True):
    if record is None or not _relevant_to_active_household(record):
        return False
    state = _notification_state(record)
    if state is None:
        return False
    if not state.get('initialized'):
        _baseline_record(record)
        return False

    changed = False
    current_conflict = _conflict_band(record)
    current_trust = _trust_band(record)
    current_risk = _risk_band(record)
    current_state = str(base.state_name(record))
    try:
        current_recovery = str(memory._recovery_stage(record))
    except Exception:
        current_recovery = ''

    old_conflict = int(state.get('conflict_band', current_conflict) or 0)
    old_trust = int(state.get('trust_band', current_trust) or 0)
    old_risk = int(state.get('risk_band', current_risk) or 0)

    if current_conflict != old_conflict:
        if allow_notifications:
            _conflict_notification(record, old_conflict, current_conflict)
        state['conflict_band'] = current_conflict
        changed = True

    if current_trust != old_trust:
        if allow_notifications:
            _trust_notification(record, old_trust, current_trust)
        state['trust_band'] = current_trust
        changed = True

    if current_risk != old_risk:
        if allow_notifications:
            _risk_notification(record, old_risk, current_risk)
        state['risk_band'] = current_risk
        changed = True

    if state.get('relationship_state') != current_state:
        state['relationship_state'] = current_state
        changed = True
    if state.get('recovery_stage') != current_recovery:
        state['recovery_stage'] = current_recovery
        changed = True

    if changed:
        base.DIRTY = True
    return changed


# ---------------------------------------------------------------------------
# Hook state changes, periodic progression and load baseline
# ---------------------------------------------------------------------------
_PREVIOUS_UPDATE_STATE = base.update_state


def _update_state_v071(record):
    result = _PREVIOUS_UPDATE_STATE(record)
    try:
        _check_record_notifications(record, allow_notifications=True)
    except Exception:
        base.flog('V071 UPDATE NOTIFICATION CHECK FAILED')
        base.flog(traceback.format_exc())
    return result


base.update_state = _update_state_v071


_PREVIOUS_ADD_GRIEVANCE = grievances.add_grievance


def _add_grievance_v071(record, reason, amount, count_event=True):
    result = _PREVIOUS_ADD_GRIEVANCE(record, reason, amount, count_event=count_event)
    try:
        _check_record_notifications(record, allow_notifications=True)
    except Exception:
        base.flog('V071 GRIEVANCE NOTIFICATION CHECK FAILED')
        base.flog(traceback.format_exc())
    return result


grievances.add_grievance = _add_grievance_v071


_PREVIOUS_DECAY_TICK = base.decay_tick


def _decay_tick_v071():
    result = _PREVIOUS_DECAY_TICK()
    try:
        for record in tuple(base.slot_state().values()):
            _check_record_notifications(record, allow_notifications=True)
    except Exception:
        base.flog('V071 PERIODIC NOTIFICATION CHECK FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v071


_PREVIOUS_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v071():
    result = _PREVIOUS_INITIALIZE_ZONE()
    try:
        # Existing relationships establish their current state silently. Loading a
        # save must not generate a flood of old threshold notifications.
        for record in tuple(base.slot_state().values()):
            state = _notification_state(record)
            if not state or not state.get('initialized'):
                _baseline_record(record)
        base.flog('V071 RELATIONSHIP NOTIFICATIONS READY')
    except Exception:
        base.flog('V071 NOTIFICATION BASELINE FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v071
base.flog('V071 STOCK RELATIONSHIP NOTIFICATIONS INSTALLED')

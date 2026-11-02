# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.0 — accumulated grievances extension."""

import traceback

import deep_relationships as base

VERSION = '0.4.0'
CHEATED_WITH_BIT_ID = 37265

base.VERSION = VERSION
base.STATE['version'] = 4

GRIEVANCE_CONFIG = {
    'arguments': {
        'label': 'Ссоры и грубость',
        'persistence': 0.45,
    },
    'romantic_hurt': {
        'label': 'Романтическая обида',
        'persistence': 0.65,
    },
    'neglect': {
        'label': 'Недостаток внимания',
        'persistence': 0.55,
    },
    'infidelity': {
        'label': 'Измена',
        'persistence': 0.92,
    },
}


def _grievance_fields(record):
    changed = False
    if not isinstance(record.get('grievances'), dict):
        record['grievances'] = {}
        changed = True
    if 'resentment' not in record:
        record['resentment'] = 0.0
        changed = True
    if 'neglect_marker' not in record:
        record['neglect_marker'] = 0
        changed = True
    if 'last_conflict_state' not in record:
        record['last_conflict_state'] = 'Спокойно'
        changed = True
    if changed:
        base.DIRTY = True
    return record


def _recalculate_resentment(record):
    _grievance_fields(record)
    total = 0.0
    for item in record.get('grievances', {}).values():
        try:
            total += max(0.0, float(item.get('severity', 0.0)))
        except Exception:
            pass
    value = base.clamp(total)
    if abs(float(record.get('resentment', 0.0)) - value) > 0.001:
        record['resentment'] = value
        base.DIRTY = True
    return value


def conflict_state(record):
    value = _recalculate_resentment(record)
    if value >= 70:
        return 'Глубокая обида'
    if value >= 45:
        return 'Серьёзный конфликт'
    if value >= 25:
        return 'Накопленная обида'
    if value >= 8:
        return 'Лёгкое раздражение'
    return 'Спокойно'


def grievance_level(value):
    value = max(0.0, float(value or 0.0))
    if value >= 45:
        return 'очень сильная'
    if value >= 28:
        return 'сильная'
    if value >= 15:
        return 'заметная'
    if value >= 6:
        return 'лёгкая'
    return 'слабая'


def _maybe_notify_conflict(record, old_state, new_state):
    if old_state == new_state or new_state in ('Спокойно', 'Лёгкое раздражение'):
        return
    try:
        manager = base.services.sim_info_manager()
        source = manager.get(int(record.get('source_id', 0))) if manager is not None else None
        target = manager.get(int(record.get('target_id', 0))) if manager is not None else None
        hh = base.household()
        if source is not None and hh is not None and source in base.sims_in_household(hh):
            base.notify(
                base.MOD_NAME,
                '{}: отношения с {} теперь имеют состояние конфликта «{}».'.format(
                    base.full_name(source), base.full_name(target), new_state
                )
            )
    except Exception:
        base.flog('CONFLICT NOTIFICATION FAILED')
        base.flog(traceback.format_exc())


def add_grievance(record, reason, amount, count_event=True):
    if record is None:
        return 0.0
    _grievance_fields(record)
    config = GRIEVANCE_CONFIG.get(reason)
    if config is None:
        return _recalculate_resentment(record)
    old_state = conflict_state(record)
    grievances = record['grievances']
    item = grievances.get(reason)
    if not isinstance(item, dict):
        item = {
            'label': config['label'],
            'severity': 0.0,
            'count': 0,
            'age_steps': 0,
        }
        grievances[reason] = item
    item['label'] = config['label']
    item['severity'] = min(100.0, max(0.0, float(item.get('severity', 0.0))) + max(0.0, float(amount)))
    if count_event:
        item['count'] = int(item.get('count', 0)) + 1
    item['age_steps'] = 0
    base.DIRTY = True
    value = _recalculate_resentment(record)
    new_state = conflict_state(record)
    record['last_conflict_state'] = new_state
    _maybe_notify_conflict(record, old_state, new_state)
    base.flog('GRIEVANCE: {} -> {} | {} +{:.2f} | resentment {:.2f}'.format(
        record.get('source_id', 0), record.get('target_id', 0), reason, float(amount), value
    ))
    return value


def apply_resentment_caps(record):
    if record is None:
        return
    value = _recalculate_resentment(record)
    if value <= 0:
        return
    trust_cap = max(35.0, 100.0 - value * 0.60)
    satisfaction_cap = max(25.0, 100.0 - value * 0.70)
    old_trust = float(record.get('trust', 0.0))
    old_satisfaction = float(record.get('satisfaction', 0.0))
    record['trust'] = min(old_trust, trust_cap)
    record['satisfaction'] = min(old_satisfaction, satisfaction_cap)
    if record['trust'] != old_trust or record['satisfaction'] != old_satisfaction:
        base.DIRTY = True
        base.update_state(record)


def _migrate_all_records():
    changed = False
    try:
        slots = base.STATE.setdefault('slots', {})
        for slot in slots.values():
            relationships = slot.setdefault('relationships', {})
            for record in relationships.values():
                before = (
                    'grievances' in record,
                    'resentment' in record,
                    'neglect_marker' in record,
                    'last_conflict_state' in record,
                )
                _grievance_fields(record)
                _recalculate_resentment(record)
                record['last_conflict_state'] = conflict_state(record)
                after = (
                    'grievances' in record,
                    'resentment' in record,
                    'neglect_marker' in record,
                    'last_conflict_state' in record,
                )
                if before != after:
                    changed = True
        base.STATE['version'] = 4
        if changed:
            base.DIRTY = True
    except Exception:
        base.flog('V4 MIGRATION FAILED')
        base.flog(traceback.format_exc())


_ORIGINAL_LOAD_STATE = base.load_state


def _load_state_v4():
    _ORIGINAL_LOAD_STATE()
    base.STATE['version'] = 4
    _migrate_all_records()


base.load_state = _load_state_v4


_ORIGINAL_ENSURE_PAIR = base.ensure_pair


def _ensure_pair_v4(source_id, target_id, force=False):
    record = _ORIGINAL_ENSURE_PAIR(source_id, target_id, force=force)
    if record is not None:
        _grievance_fields(record)
        _recalculate_resentment(record)
    return record


base.ensure_pair = _ensure_pair_v4


_ORIGINAL_ON_DELTA = base.on_relationship_delta


def _on_relationship_delta_v4(source_id, target_id, delta, kind):
    try:
        numeric_delta = float(delta)
    except Exception:
        numeric_delta = 0.0
    result = _ORIGINAL_ON_DELTA(source_id, target_id, delta, kind)
    try:
        record = base.ensure_pair(source_id, target_id, force=(kind == 'romance'))
        if record is None:
            return result
        if numeric_delta < -0.0001:
            magnitude = abs(numeric_delta)
            if kind == 'romance':
                add_grievance(record, 'romantic_hurt', min(12.0, max(2.0, magnitude * 0.32)))
            elif kind == 'friendship':
                add_grievance(record, 'arguments', min(10.0, max(1.5, magnitude * 0.28)))
        apply_resentment_caps(record)
        base.save_state(False)
    except Exception:
        base.flog('V4 DELTA EXTENSION FAILED')
        base.flog(traceback.format_exc())
    return result


base.on_relationship_delta = _on_relationship_delta_v4


def _age_grievances(record):
    _grievance_fields(record)
    grievances = record.get('grievances', {})
    remove = []
    for reason, item in tuple(grievances.items()):
        config = GRIEVANCE_CONFIG.get(reason, {'persistence': 0.5})
        persistence = float(config.get('persistence', 0.5))
        severity = max(0.0, float(item.get('severity', 0.0)))
        item['age_steps'] = int(item.get('age_steps', 0)) + 1
        loss = 0.08 + (1.0 - persistence) * 0.45
        severity = max(0.0, severity - loss)
        item['severity'] = severity
        if severity < 0.60:
            remove.append(reason)
    for reason in remove:
        grievances.pop(reason, None)
    if grievances or remove:
        base.DIRTY = True
    _recalculate_resentment(record)
    record['last_conflict_state'] = conflict_state(record)


def _update_neglect_grievance(record):
    quiet = int(record.get('quiet_steps', 0))
    if quiet < 12:
        return
    stage = 1 + max(0, (quiet - 12) // 8)
    marker = int(record.get('neglect_marker', 0))
    if stage <= marker:
        return
    record['neglect_marker'] = stage
    add_grievance(record, 'neglect', min(8.0, 3.0 + stage), count_event=True)


_ORIGINAL_DECAY_TICK = base.decay_tick


def _decay_tick_v4():
    result = _ORIGINAL_DECAY_TICK()
    try:
        for record in tuple(base.slot_state().values()):
            _age_grievances(record)
            _update_neglect_grievance(record)
            apply_resentment_caps(record)
        base.save_state(False)
    except Exception:
        base.flog('V4 GRIEVANCE DECAY FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v4


_ORIGINAL_RECORD_TEXT = base.record_text


def _record_text_v4(source, target, record):
    text = _ORIGINAL_RECORD_TEXT(source, target, record)
    if record is None:
        return text
    _grievance_fields(record)
    value = _recalculate_resentment(record)
    state = conflict_state(record)
    lines = [text, '', 'Конфликт: {} ({:.0f}/100)'.format(state, value)]
    grievances = record.get('grievances', {})
    if not grievances:
        lines.append('Что мешает отношениям: заметных обид нет.')
        return '\n'.join(lines)
    lines.append('Что мешает отношениям:')
    ordered = sorted(
        grievances.values(),
        key=lambda item: float(item.get('severity', 0.0)),
        reverse=True
    )[:4]
    for item in ordered:
        severity = float(item.get('severity', 0.0))
        count = int(item.get('count', 0))
        suffix = ' • эпизодов: {}'.format(count) if count > 1 else ''
        lines.append('• {} — {} ({:.0f}){}'.format(
            item.get('label', 'Обида'), grievance_level(severity), severity, suffix
        ))
    return '\n'.join(lines)


base.record_text = _record_text_v4


def _bit_guid(bit):
    for attr in ('guid64', 'guid', 'id'):
        try:
            value = getattr(bit, attr, None)
            if value is not None:
                return int(value)
        except Exception:
            pass
    try:
        return int(bit)
    except Exception:
        return 0


def _mark_infidelity_for_partners(cheater_id, affair_partner_id):
    try:
        cheater_id = int(cheater_id)
        affair_partner_id = int(affair_partner_id)
        manager = base.services.sim_info_manager()
        cheater = manager.get(cheater_id) if manager is not None else None
        if cheater is None:
            return
        changed = 0
        for record in tuple(base.slot_state().values()):
            try:
                source_id = int(record.get('source_id', 0))
                target_id = int(record.get('target_id', 0))
            except Exception:
                continue
            if target_id != cheater_id or source_id == affair_partner_id:
                continue
            partner = manager.get(source_id) if manager is not None else None
            if partner is None:
                continue
            _, romance = base.scores(partner, cheater_id)
            if not base.romantic_context(partner, cheater_id, romance):
                continue
            old_infidelity = record.get('grievances', {}).get('infidelity', {})
            old_count = int(old_infidelity.get('count', 0)) if isinstance(old_infidelity, dict) else 0
            add_grievance(record, 'infidelity', 30.0, count_event=True)
            if int(record.get('grievances', {}).get('infidelity', {}).get('count', 0)) > old_count:
                record['trust'] = base.clamp(float(record.get('trust', 0.0)) - 14.0)
                record['satisfaction'] = base.clamp(float(record.get('satisfaction', 0.0)) - 18.0)
                base.update_state(record)
                apply_resentment_caps(record)
                changed += 1
        if changed:
            base.DIRTY = True
            base.save_state(False)
            base.flog('INFIDELITY DETECTED: cheater {} with {} | affected partners {}'.format(
                cheater_id, affair_partner_id, changed
            ))
    except Exception:
        base.flog('INFIDELITY HANDLER FAILED')
        base.flog(traceback.format_exc())


@base.inject_to(base.RelationshipService, 'add_relationship_bit', '_deeprel_v4_bit_wrapped')
def _observe_relationship_bit(original, self, actor_sim_id, target_sim_id, bit_to_add,
                              force_add=False, from_load=False, send_rel_change_event=True,
                              allow_readdition=True):
    result = original(
        self, actor_sim_id, target_sim_id, bit_to_add,
        force_add=force_add,
        from_load=from_load,
        send_rel_change_event=send_rel_change_event,
        allow_readdition=allow_readdition
    )
    try:
        if not from_load and _bit_guid(bit_to_add) == CHEATED_WITH_BIT_ID:
            _mark_infidelity_for_partners(actor_sim_id, target_sim_id)
            _mark_infidelity_for_partners(target_sim_id, actor_sim_id)
    except Exception:
        base.flog('RELATIONSHIP BIT OBSERVER FAILED')
        base.flog(traceback.format_exc())
    return result


_ORIGINAL_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v4():
    result = _ORIGINAL_INITIALIZE_ZONE()
    try:
        _migrate_all_records()
        for record in tuple(base.slot_state().values()):
            apply_resentment_caps(record)
        base.save_state(False)
        base.flog('GRIEVANCE SYSTEM ACTIVE')
    except Exception:
        base.flog('V4 ZONE EXTENSION FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v4

base.flog('GRIEVANCE SYSTEM INSTALLED v{}'.format(VERSION))
base.logger.info('Deep Relationships grievances v{} imported.'.format(VERSION))

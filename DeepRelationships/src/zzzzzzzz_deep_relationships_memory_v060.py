# -*- coding: utf-8 -*-
"""Deep Relationships v0.6.0 — relationship memory and consequences.

Adds persistent relationship memories, a primary conflict issue, recovery stages,
and resistance to ordinary positive socials while serious hurt is unresolved.
The system works on the directional records created by the proven v0.4-v0.5
layers and uses the same save/rollback lifecycle.
"""

import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzz_deep_relationships_v051 as roles

VERSION = '0.6.0'
base.VERSION = VERSION
moodlets.VERSION = VERSION

MAX_MEMORIES = 16

MEMORY_LABELS = {
    'argument': 'Ссора',
    'romantic_hurt': 'Романтическая обида',
    'neglect': 'Недостаток внимания',
    'betrayal': 'Измена и предательство',
    'constructive_talk': 'Спокойный разговор',
    'apology_accepted': 'Принятое извинение',
    'apology_rejected': 'Отвергнутое извинение',
    'admit_fault': 'Признание вины',
    'forgiveness': 'Попытка простить',
    'distance': 'Потребность в дистанции',
    'second_chance': 'Второй шанс',
    'positive_contact': 'Тёплое общение',
    'reconnection': 'Сближение после конфликта',
}

NEGATIVE_MEMORY_KINDS = ('argument', 'romantic_hurt', 'neglect', 'betrayal', 'apology_rejected', 'distance')
POSITIVE_MEMORY_KINDS = ('constructive_talk', 'apology_accepted', 'admit_fault', 'forgiveness', 'second_chance', 'positive_contact', 'reconnection')


def _memories(record):
    if record is None:
        return []
    value = record.get('relationship_memories')
    if not isinstance(value, list):
        value = []
        record['relationship_memories'] = value
        base.DIRTY = True
    return value


def _memory_kind_for_grievance(reason):
    return {
        'arguments': 'argument',
        'romantic_hurt': 'romantic_hurt',
        'neglect': 'neglect',
        'infidelity': 'betrayal',
    }.get(str(reason))


def _add_memory(record, kind, severity=1.0, partner_id=None, merge=True):
    if record is None or not kind:
        return None
    try:
        severity = max(0.1, float(severity))
    except Exception:
        severity = 1.0
    memories = _memories(record)
    if partner_id is None:
        try:
            partner_id = int(record.get('target_id', 0) or 0)
        except Exception:
            partner_id = 0

    # Repeated neglect/arguments should strengthen one memory instead of filling
    # the history with dozens of identical rows.
    if merge:
        for item in reversed(memories):
            if not isinstance(item, dict):
                continue
            if str(item.get('kind', '')) != str(kind):
                continue
            try:
                if int(item.get('partner_id', 0) or 0) != int(partner_id or 0):
                    continue
            except Exception:
                continue
            age = int(item.get('age_steps', 0) or 0)
            if age <= 8:
                item['severity'] = min(100.0, float(item.get('severity', 0.0) or 0.0) + severity)
                item['age_steps'] = 0
                item['resolved'] = False
                base.DIRTY = True
                return item

    item = {
        'kind': str(kind),
        'severity': min(100.0, severity),
        'age_steps': 0,
        'partner_id': int(partner_id or 0),
        'resolved': False,
    }
    memories.append(item)
    if len(memories) > MAX_MEMORIES:
        # Keep the most meaningful recent history. Betrayal and second chances
        # are intentionally harder to evict than small old interactions.
        memories.sort(key=lambda m: (
            1 if str(m.get('kind', '')) in ('betrayal', 'second_chance') else 0,
            float(m.get('severity', 0.0) or 0.0),
            -int(m.get('age_steps', 0) or 0)
        ), reverse=True)
        del memories[MAX_MEMORIES:]
    base.DIRTY = True
    return item


def _age_memories(record):
    memories = _memories(record)
    changed = False
    keep = []
    grievance_map = record.get('grievances', {}) if isinstance(record.get('grievances'), dict) else {}
    active_reason = {
        'argument': 'arguments',
        'romantic_hurt': 'romantic_hurt',
        'neglect': 'neglect',
        'betrayal': 'infidelity',
    }
    decay = {
        'argument': 0.30,
        'romantic_hurt': 0.18,
        'neglect': 0.15,
        'betrayal': 0.05,
        'apology_rejected': 0.20,
        'distance': 0.22,
        'constructive_talk': 0.35,
        'apology_accepted': 0.25,
        'admit_fault': 0.25,
        'forgiveness': 0.18,
        'second_chance': 0.10,
        'positive_contact': 0.45,
        'reconnection': 0.20,
    }
    for item in memories:
        if not isinstance(item, dict):
            continue
        old_age = int(item.get('age_steps', 0) or 0)
        item['age_steps'] = old_age + 1
        kind = str(item.get('kind', ''))
        old_severity = float(item.get('severity', 0.0) or 0.0)
        new_severity = max(0.0, old_severity - float(decay.get(kind, 0.20)))
        item['severity'] = new_severity
        reason = active_reason.get(kind)
        if reason is not None and reason not in grievance_map and old_age >= 3:
            item['resolved'] = True
        if new_severity >= 0.6 or kind in ('betrayal', 'second_chance'):
            keep.append(item)
        changed = True
    if keep != memories:
        record['relationship_memories'] = keep[-MAX_MEMORIES:]
        changed = True
    if changed:
        base.DIRTY = True
    return changed


def _grievance_severity(record, reason):
    if record is None:
        return 0.0
    try:
        grievances._grievance_fields(record)
        item = record.get('grievances', {}).get(reason)
        if isinstance(item, dict):
            return max(0.0, float(item.get('severity', 0.0) or 0.0))
    except Exception:
        pass
    return 0.0


def _primary_issue(record):
    if record is None:
        return 'Нет выраженной проблемы'
    candidates = [
        (_grievance_severity(record, 'infidelity') * 2.0, 'Разбитое доверие после измены'),
        (_grievance_severity(record, 'neglect') * 1.35, 'Недостаток внимания'),
        (_grievance_severity(record, 'romantic_hurt') * 1.20, 'Ревность и романтическая обида'),
        (_grievance_severity(record, 'arguments'), 'Постоянные ссоры'),
    ]
    try:
        compatibility = float(record.get('compatibility', 50.0) or 50.0)
        satisfaction = float(record.get('satisfaction', 50.0) or 50.0)
        love = float(record.get('love', 0.0) or 0.0)
        if compatibility < 42.0 and satisfaction < 48.0 and love >= 25.0:
            candidates.append((max(6.0, 42.0 - compatibility), 'Несовпадение ожиданий'))
    except Exception:
        pass
    score, label = max(candidates, key=lambda row: row[0])
    if score < 3.0:
        return 'Нет выраженной проблемы'
    return label


def _recovery_stage(record):
    if record is None:
        return 'Нет данных'
    try:
        resentment = float(reconciliation._resentment(record) or 0.0)
    except Exception:
        resentment = 0.0
    block = int(record.get('forgiveness_block_steps', 0) or 0)
    ready = int(record.get('ready_to_forgive_steps', 0) or 0)
    second = int(record.get('second_chance_steps', 0) or 0)
    closeness = int(record.get('closeness_steps', 0) or 0)
    trust = float(record.get('trust', 0.0) or 0.0)
    satisfaction = float(record.get('satisfaction', 0.0) or 0.0)

    if resentment >= 45.0:
        return 'Конфликт'
    if block > 0:
        return 'Дистанция'
    if ready > 0:
        return 'Готовность простить'
    if second > 0:
        return 'Второй шанс'
    if closeness > 0:
        return 'Сближение'
    if resentment >= 8.0:
        return 'Осторожный разговор'
    if trust < 60.0 or satisfaction < 55.0:
        return 'Восстановление доверия'
    return 'Примирение'


def _gain_multiplier(record, kind='romance'):
    if record is None:
        return 1.0
    resentment = float(reconciliation._resentment(record) or 0.0)
    betrayal = _grievance_severity(record, 'infidelity')
    block = int(record.get('forgiveness_block_steps', 0) or 0)
    second = int(record.get('second_chance_steps', 0) or 0)

    if betrayal >= 1.0:
        value = 0.35 if kind == 'romance' else 0.50
    elif resentment >= 70.0:
        value = 0.35
    elif resentment >= 45.0:
        value = 0.45
    elif resentment >= 25.0:
        value = 0.65
    elif resentment >= 8.0:
        value = 0.82
    else:
        value = 1.0
    if block > 0:
        value = min(value, 0.50)
    if second > 0:
        value = min(1.0, value + 0.15)
    return max(0.25, min(1.0, value))


def _resistance_label(record):
    mult = _gain_multiplier(record, 'romance')
    if mult <= 0.40:
        return 'очень сильное'
    if mult <= 0.55:
        return 'сильное'
    if mult <= 0.75:
        return 'заметное'
    if mult < 0.95:
        return 'лёгкое'
    return 'нет'


# ---------------------------------------------------------------------------
# Memories from grievance events.
# ---------------------------------------------------------------------------
_PREVIOUS_ADD_GRIEVANCE = grievances.add_grievance


def _add_grievance_v060(record, reason, amount, count_event=True):
    result = _PREVIOUS_ADD_GRIEVANCE(record, reason, amount, count_event=count_event)
    try:
        kind = _memory_kind_for_grievance(reason)
        if kind is not None and record is not None:
            multiplier = 2.0 if kind == 'betrayal' else 1.0
            _add_memory(record, kind, float(amount or 0.0) * multiplier)
    except Exception:
        base.flog('V060 MEMORY AFTER GRIEVANCE FAILED')
        base.flog(traceback.format_exc())
    return result


grievances.add_grievance = _add_grievance_v060


# ---------------------------------------------------------------------------
# Ordinary positive socials are less effective internally while serious hurt is
# unresolved. Negative damage is not softened. This applies equally to player
# chosen and autonomous socials because both reach RelationshipService.
# ---------------------------------------------------------------------------
_PREVIOUS_APPLY_METRIC_DELTA = core._apply_metric_delta


def _apply_metric_delta_v060(record, delta, kind):
    try:
        value = float(delta)
    except Exception:
        value = 0.0
    if value > 0.0:
        multiplier = _gain_multiplier(record, kind)
        value *= multiplier
    return _PREVIOUS_APPLY_METRIC_DELTA(record, value, kind)


core._apply_metric_delta = _apply_metric_delta_v060


_PREVIOUS_DELTA = base.on_relationship_delta


def _on_relationship_delta_v060(source_id, target_id, supplied_delta, kind):
    try:
        actual, _ = core._actual_delta(source_id, target_id, supplied_delta, kind)
    except Exception:
        try:
            actual = float(supplied_delta or 0.0)
        except Exception:
            actual = 0.0

    result = _PREVIOUS_DELTA(source_id, target_id, supplied_delta, kind)

    # Positive contact can specifically repair neglect, but not magically erase
    # betrayal or a serious argument. Keep this intentionally small.
    if actual > 0.5:
        try:
            owner_id, other_id, _ = core._normalize_owner(source_id, target_id)
            record = core._existing_record(owner_id, other_id)
            if record is not None:
                neglect = record.get('grievances', {}).get('neglect') if isinstance(record.get('grievances'), dict) else None
                if isinstance(neglect, dict):
                    before = float(neglect.get('severity', 0.0) or 0.0)
                    repair = min(1.8, actual * (0.10 if kind == 'romance' else 0.07))
                    neglect['severity'] = max(0.0, before - repair)
                    if neglect['severity'] < 0.60:
                        record.get('grievances', {}).pop('neglect', None)
                    grievances._recalculate_resentment(record)
                    grievances.apply_resentment_caps(record)
                    base.update_state(record)
                    base.DIRTY = True
                if reconciliation._resentment(record) >= 8.0 and actual >= 3.0:
                    _add_memory(record, 'positive_contact', min(6.0, actual * 0.25))
                if reconciliation._resentment(record) < 8.0 and float(record.get('trust', 0.0) or 0.0) >= 55.0:
                    _add_memory(record, 'reconnection', 2.0)
                roles._sync_direction(record)
        except Exception:
            base.flog('V060 POSITIVE CONTACT CONSEQUENCE FAILED')
            base.flog(traceback.format_exc())
    return result


base.on_relationship_delta = _on_relationship_delta_v060


# ---------------------------------------------------------------------------
# Different problems respond best to different reconciliation actions.
# ---------------------------------------------------------------------------
_ACTION_CONTEXT = [None]
_PREVIOUS_REDUCE_GRIEVANCE = reconciliation._reduce_grievance

ACTION_EFFECTIVENESS = {
    'discuss': {
        'arguments': 1.45, 'neglect': 1.30, 'romantic_hurt': 1.00, 'infidelity': 0.45,
    },
    'apologize': {
        'arguments': 0.95, 'neglect': 0.80, 'romantic_hurt': 1.35, 'infidelity': 0.75,
    },
    'admit_fault': {
        'arguments': 1.00, 'neglect': 0.90, 'romantic_hurt': 1.20, 'infidelity': 1.30,
    },
    'forgive': {
        'arguments': 1.20, 'neglect': 1.20, 'romantic_hurt': 1.00, 'infidelity': 0.75,
    },
    'second_chance': {
        'arguments': 1.00, 'neglect': 1.00, 'romantic_hurt': 1.00, 'infidelity': 0.85,
    },
}


def _reduce_grievance_v060(record, amount):
    action = _ACTION_CONTEXT[0]
    key, _ = reconciliation._top_grievance(record)
    multiplier = ACTION_EFFECTIVENESS.get(action, {}).get(key, 1.0)
    return _PREVIOUS_REDUCE_GRIEVANCE(record, float(amount) * multiplier)


reconciliation._reduce_grievance = _reduce_grievance_v060


def _wrap_action(action, runner):
    def wrapped(actor, target):
        actor_record, target_record = reconciliation._records(actor, target, create=False)
        before_actor = reconciliation._resentment(actor_record)
        before_target = reconciliation._resentment(target_record)
        _ACTION_CONTEXT[0] = action
        try:
            result = runner(actor, target)
        finally:
            _ACTION_CONTEXT[0] = None

        try:
            actor_record, target_record = reconciliation._records(actor, target, create=False)
            after_actor = reconciliation._resentment(actor_record)
            after_target = reconciliation._resentment(target_record)
            improved = (after_actor + after_target) < (before_actor + before_target - 0.25)

            if action == 'discuss' and improved:
                _add_memory(actor_record, 'constructive_talk', 3.0)
                _add_memory(target_record, 'constructive_talk', 3.0)
            elif action == 'apologize':
                kind = 'apology_accepted' if improved else 'apology_rejected'
                _add_memory(target_record, kind, 4.0 if improved else 3.0)
            elif action == 'admit_fault' and improved:
                _add_memory(target_record, 'admit_fault', 4.0)
            elif action == 'forgive' and improved:
                _add_memory(actor_record, 'forgiveness', 5.0)
            elif action == 'not_ready':
                _add_memory(actor_record, 'distance', 4.0)
            elif action == 'second_chance':
                accepted = False
                for record in (actor_record, target_record):
                    if record is not None and int(record.get('second_chance_steps', 0) or 0) > 0:
                        accepted = True
                if accepted:
                    _add_memory(actor_record, 'second_chance', 7.0)
                    _add_memory(target_record, 'second_chance', 7.0)
        except Exception:
            base.flog('V060 MEMORY AFTER RECONCILIATION FAILED')
            base.flog(traceback.format_exc())
        return result
    return wrapped


for _action_name, _runner in tuple(reconciliation.ACTION_RUNNERS.items()):
    reconciliation.ACTION_RUNNERS[_action_name] = _wrap_action(_action_name, _runner)


# ---------------------------------------------------------------------------
# Age memories on the existing six-hour relationship tick.
# ---------------------------------------------------------------------------
_PREVIOUS_DECAY_TICK = base.decay_tick


def _decay_tick_v060():
    result = _PREVIOUS_DECAY_TICK()
    try:
        changed = False
        for record in tuple(base.slot_state().values()):
            source_id = int(record.get('source_id', 0) or 0)
            target_id = int(record.get('target_id', 0) or 0)
            if not core._pair_relevant(source_id, target_id):
                continue
            if _age_memories(record):
                changed = True
        if changed:
            moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V060 MEMORY TICK FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v060


# ---------------------------------------------------------------------------
# Relationship report: explain the problem, recovery stage and actual history.
# ---------------------------------------------------------------------------
_PREVIOUS_RECORD_TEXT = base.record_text


def _memory_age_text(steps):
    hours = max(0, int(steps or 0)) * 6
    if hours < 24:
        return '{} ч. назад'.format(hours)
    days = int(round(hours / 24.0))
    return '{} дн. назад'.format(days)


def _important_memories(record):
    memories = [item for item in _memories(record) if isinstance(item, dict)]
    memories.sort(key=lambda item: (
        0 if bool(item.get('resolved', False)) else 1,
        float(item.get('severity', 0.0) or 0.0),
        -int(item.get('age_steps', 0) or 0)
    ), reverse=True)
    return memories[:3]


def _record_text_v060(source, target, record):
    text = _PREVIOUS_RECORD_TEXT(source, target, record)
    if record is None:
        return text
    lines = [text, '', 'Главная проблема: {}'.format(_primary_issue(record))]
    lines.append('Этап восстановления: {}'.format(_recovery_stage(record)))
    resistance = _resistance_label(record)
    lines.append('Сопротивление сближению: {}'.format(resistance))
    if resistance != 'нет':
        percent = int(round(_gain_multiplier(record, 'romance') * 100.0))
        lines.append('Обычное позитивное общение сейчас восстанавливает внутренние показатели примерно на {}%.'.format(percent))

    memories = _important_memories(record)
    if memories:
        lines.extend(['', 'Память отношений:'])
        for item in memories:
            label = MEMORY_LABELS.get(str(item.get('kind', '')), str(item.get('kind', '')))
            age = _memory_age_text(item.get('age_steps', 0))
            status = ' — пережито' if bool(item.get('resolved', False)) else ''
            lines.append('• {} ({}){}'.format(label, age, status))
    return '\n'.join(lines)


base.record_text = _record_text_v060


# Migrate existing records without resetting current progress.
def _migrate_v060():
    changed = 0
    try:
        for record in tuple(base.slot_state().values()):
            if 'relationship_memories' not in record:
                record['relationship_memories'] = []
                changed += 1
            # Seed the history from currently active grievances so v0.5 saves
            # immediately show meaningful memory without fabricating dates.
            mapping = record.get('grievances', {}) if isinstance(record.get('grievances'), dict) else {}
            if not record['relationship_memories']:
                for reason, item in mapping.items():
                    if not isinstance(item, dict):
                        continue
                    kind = _memory_kind_for_grievance(reason)
                    if kind is None:
                        continue
                    severity = float(item.get('severity', 0.0) or 0.0)
                    if severity > 0.5:
                        _add_memory(record, kind, severity * (2.0 if kind == 'betrayal' else 1.0), merge=False)
                        changed += 1
        if changed:
            base.DIRTY = True
        base.flog('V060 MEMORY MIGRATION COMPLETE: {} changes'.format(changed))
    except Exception:
        base.flog('V060 MEMORY MIGRATION FAILED')
        base.flog(traceback.format_exc())


_PREVIOUS_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v060():
    result = _PREVIOUS_INITIALIZE_ZONE()
    try:
        _migrate_v060()
        moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V060 INITIALIZE FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v060
base.flog('V060 MEMORY AND CONSEQUENCES SYSTEM INSTALLED')

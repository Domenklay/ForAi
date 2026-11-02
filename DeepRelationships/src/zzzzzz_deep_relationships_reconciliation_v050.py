# -*- coding: utf-8 -*-
"""Deep Relationships v0.5.0 — reconciliation and forgiveness.

Adds player-facing reconciliation interactions that work on directional
relationship records. All changes remain in memory and are persisted by the
proven v0.4.5 save lifecycle only when the player actually saves the game.
"""

import random
import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core

VERSION = '0.5.0'
base.VERSION = VERSION
moodlets.VERSION = VERSION

# Tuning interaction IDs. These must match the resources in the .package.
INTERACTION_DISCUSS = 16907167177260101701
INTERACTION_APOLOGIZE = 16907167177260101702
INTERACTION_ADMIT_FAULT = 16907167177260101703
INTERACTION_FORGIVE = 16907167177260101704
INTERACTION_NOT_READY = 16907167177260101705
INTERACTION_SECOND_CHANCE = 16907167177260101706

ACTION_IDS = (
    INTERACTION_DISCUSS,
    INTERACTION_APOLOGIZE,
    INTERACTION_ADMIT_FAULT,
    INTERACTION_FORGIVE,
    INTERACTION_NOT_READY,
    INTERACTION_SECOND_CHANCE,
)


def _sim_info(value):
    return getattr(value, 'sim_info', value)


def _records(actor, target, create=True):
    actor_info = _sim_info(actor)
    target_info = _sim_info(target)
    if actor_info is None or target_info is None:
        return None, None
    try:
        actor_id = int(actor_info.sim_id)
        target_id = int(target_info.sim_id)
    except Exception:
        return None, None

    actor_record = core._existing_record(actor_id, target_id)
    target_record = core._existing_record(target_id, actor_id)
    if create:
        if actor_record is None:
            actor_record = base.ensure_pair(actor_id, target_id, force=False)
        if target_record is None:
            target_record = base.ensure_pair(target_id, actor_id, force=False)
    return actor_record, target_record


def _resentment(record):
    if record is None:
        return 0.0
    try:
        return float(grievances._recalculate_resentment(record) or 0.0)
    except Exception:
        return float(record.get('resentment', 0.0) or 0.0)


def _cooldowns(record):
    if record is None:
        return {}
    value = record.get('reconciliation_cooldowns')
    if not isinstance(value, dict):
        value = {}
        record['reconciliation_cooldowns'] = value
        base.DIRTY = True
    return value


def _cooldown(record, action):
    try:
        return max(0, int(_cooldowns(record).get(action, 0) or 0))
    except Exception:
        return 0


def _set_cooldown(record, action, steps):
    if record is None:
        return
    _cooldowns(record)[action] = max(0, int(steps))
    base.DIRTY = True


def _block_steps(record):
    if record is None:
        return 0
    try:
        return max(0, int(record.get('forgiveness_block_steps', 0) or 0))
    except Exception:
        return 0


def _set_marker(record, name, steps):
    if record is None:
        return
    record[name] = max(0, int(steps))
    base.DIRTY = True


def _clamp_chance(value, low=0.08, high=0.90):
    return max(low, min(high, float(value)))


def _roll(chance):
    return random.random() < _clamp_chance(chance)


def _top_grievance(record):
    if record is None:
        return None, None
    grievances._grievance_fields(record)
    mapping = record.get('grievances', {})
    if not isinstance(mapping, dict) or not mapping:
        return None, None
    items = []
    for key, value in mapping.items():
        if not isinstance(value, dict):
            continue
        try:
            severity = float(value.get('severity', 0.0) or 0.0)
        except Exception:
            severity = 0.0
        items.append((severity, key, value))
    if not items:
        return None, None
    _, key, item = max(items, key=lambda row: row[0])
    return key, item


def _reduce_grievance(record, amount):
    """Reduce the strongest current grievance and return actual reduction."""
    if record is None:
        return 0.0
    key, item = _top_grievance(record)
    if item is None:
        return 0.0
    try:
        before = max(0.0, float(item.get('severity', 0.0) or 0.0))
    except Exception:
        before = 0.0
    effective = max(0.0, float(amount))
    # Betrayal is deliberately harder to erase than ordinary arguments.
    if key == 'infidelity':
        effective *= 0.45
    elif key == 'romantic_hurt':
        effective *= 0.80
    after = max(0.0, before - effective)
    item['severity'] = after
    item['age_steps'] = 0
    if after < 0.60:
        try:
            record.get('grievances', {}).pop(key, None)
        except Exception:
            pass
    grievances._recalculate_resentment(record)
    record['last_conflict_state'] = grievances.conflict_state(record)
    base.DIRTY = True
    return before - after


def _improve(record, trust=0.0, satisfaction=0.0, love=0.0, attachment=0.0):
    if record is None:
        return
    record['trust'] = base.clamp(record.get('trust', 0.0) + trust)
    record['satisfaction'] = base.clamp(record.get('satisfaction', 0.0) + satisfaction)
    record['love'] = base.clamp(record.get('love', 0.0) + love)
    record['attachment'] = base.clamp(record.get('attachment', 0.0) + attachment)
    grievances.apply_resentment_caps(record)
    base.update_state(record)
    base.DIRTY = True


def _sync_records(*records):
    active_ids = core._active_household_ids()
    manager = base.services.sim_info_manager()
    if manager is None:
        return
    synced = set()
    for record in records:
        if record is None:
            continue
        try:
            sim_id = int(record.get('source_id', 0))
        except Exception:
            continue
        if sim_id in synced or sim_id not in active_ids:
            continue
        sim_info = manager.get(sim_id)
        if sim_info is not None:
            moodlets.sync_sim_moodlets(sim_info)
            synced.add(sim_id)


def _notify_outcome(actor, target, title, text):
    try:
        base.notify(title, text, icon_sim=target)
    except Exception:
        base.flog('V050 OUTCOME NOTIFICATION FAILED')
        base.flog(traceback.format_exc())


def _names(actor, target):
    return base.full_name(_sim_info(actor)), base.full_name(_sim_info(target))


def _can_action(action, actor, target):
    actor_info = _sim_info(actor)
    target_info = _sim_info(target)
    if actor_info is None or target_info is None:
        return False
    try:
        if int(actor_info.sim_id) == int(target_info.sim_id):
            return False
    except Exception:
        return False

    actor_record, target_record = _records(actor, target, create=False)
    if actor_record is None and target_record is None:
        return False

    actor_r = _resentment(actor_record)
    target_r = _resentment(target_record)

    if action == 'discuss':
        if actor_record is not None and _cooldown(actor_record, action) > 0:
            return False
        low_quality = False
        for record in (actor_record, target_record):
            if record is not None:
                low_quality = low_quality or float(record.get('trust', 0.0) or 0.0) < 45.0
                low_quality = low_quality or float(record.get('satisfaction', 0.0) or 0.0) < 45.0
        return actor_r >= 8.0 or target_r >= 8.0 or low_quality

    if action == 'apologize':
        if actor_record is not None and _cooldown(actor_record, action) > 0:
            return False
        return target_record is not None and target_r >= 8.0 and _block_steps(target_record) <= 0

    if action == 'admit_fault':
        if actor_record is not None and _cooldown(actor_record, action) > 0:
            return False
        return target_record is not None and target_r >= 6.0

    if action == 'forgive':
        if actor_record is None or _cooldown(actor_record, action) > 0:
            return False
        return actor_r >= 8.0

    if action == 'not_ready':
        if actor_record is None or _cooldown(actor_record, action) > 0:
            return False
        return actor_r >= 8.0 and _block_steps(actor_record) <= 0

    if action == 'second_chance':
        if actor_record is not None and _cooldown(actor_record, action) > 0:
            return False
        if target_record is None or _block_steps(target_record) > 0:
            return False
        severe = target_r >= 45.0 or actor_r >= 45.0
        former = (
            (actor_record is not None and actor_record.get('relationship_phase') == 'former') or
            target_record.get('relationship_phase') == 'former'
        )
        if not (former or severe):
            return False
        love = float(target_record.get('love', 0.0) or 0.0)
        attachment = float(target_record.get('attachment', 0.0) or 0.0)
        return love >= 25.0 or attachment >= 45.0

    return False


def _do_discuss(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if actor_record is None and target_record is None:
        return False
    if actor_record is not None:
        _set_cooldown(actor_record, 'discuss', 1)  # ~6 sim hours

    records = [record for record in (actor_record, target_record) if record is not None]
    compatibility = sum(float(r.get('compatibility', 50.0) or 50.0) for r in records) / len(records)
    trust = sum(float(r.get('trust', 40.0) or 40.0) for r in records) / len(records)
    resentment = sum(_resentment(r) for r in records) / len(records)
    chance = 0.48 + compatibility * 0.0025 + trust * 0.0015 - resentment * 0.0025
    a_name, t_name = _names(actor, target)

    if _roll(chance):
        total = 0.0
        for record in records:
            total += _reduce_grievance(record, 6.0 + compatibility * 0.035)
            _improve(record, trust=1.5, satisfaction=2.5, attachment=0.5)
            if _resentment(record) < 8.0:
                _set_marker(record, 'closeness_steps', 4)
            else:
                _set_marker(record, 'ready_to_forgive_steps', 4)
        _notify_outcome(
            actor, target, 'Разговор об отношениях',
            '{} и {} смогли спокойно обсудить проблемы. Напряжение между ними снизилось.'.format(a_name, t_name)
        )
        base.flog('V050 DISCUSS SUCCESS: {} <-> {} reduced {:.2f}'.format(a_name, t_name, total))
    else:
        # A failed talk is not automatically a disaster. Only very poor relationships
        # gain a tiny extra argument grievance.
        if chance < 0.35:
            for record in records:
                grievances.add_grievance(record, 'arguments', 1.5, count_event=True)
        _notify_outcome(
            actor, target, 'Трудный разговор',
            '{} и {} пока не смогли найти общий язык. Для серьёзного разговора им нужно больше доверия.'.format(a_name, t_name)
        )
        base.flog('V050 DISCUSS FAILED: {} <-> {} chance {:.2f}'.format(a_name, t_name, chance))

    _sync_records(actor_record, target_record)
    return True


def _do_apologize(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if target_record is None:
        return False
    if actor_record is not None:
        _set_cooldown(actor_record, 'apologize', 2)  # ~12 sim hours

    r = _resentment(target_record)
    trust = float(target_record.get('trust', 0.0) or 0.0)
    attachment = float(target_record.get('attachment', 0.0) or 0.0)
    compatibility = float(target_record.get('compatibility', 50.0) or 50.0)
    chance = 0.18 + trust * 0.0030 + attachment * 0.0020 + compatibility * 0.0015 - r * 0.0035
    a_name, t_name = _names(actor, target)

    if _roll(chance):
        reduction = _reduce_grievance(target_record, 12.0 + attachment * 0.05)
        _improve(target_record, trust=2.0, satisfaction=3.0, attachment=0.5)
        if actor_record is not None:
            _improve(actor_record, satisfaction=1.0)
        if _resentment(target_record) < 8.0:
            _set_marker(target_record, 'closeness_steps', 4)
        else:
            _set_marker(target_record, 'ready_to_forgive_steps', 4)
        _notify_outcome(
            actor, target, 'Извинение принято',
            '{} принял(а) извинения {}. Обида уменьшилась, но серьёзные причины конфликта могут потребовать времени.'.format(t_name, a_name)
        )
        base.flog('V050 APOLOGY ACCEPTED: {} -> {} reduced {:.2f}'.format(a_name, t_name, reduction))
    else:
        _notify_outcome(
            actor, target, 'Извинение не принято',
            '{} пока не готов(а) принять извинения {}. Давление сейчас только помешает.'.format(t_name, a_name)
        )
        base.flog('V050 APOLOGY REJECTED: {} -> {} chance {:.2f}'.format(a_name, t_name, chance))

    _sync_records(actor_record, target_record)
    return True


def _do_admit_fault(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if target_record is None:
        return False
    if actor_record is not None:
        _set_cooldown(actor_record, 'admit_fault', 2)
    a_name, t_name = _names(actor, target)

    blocked = _block_steps(target_record) > 0
    amount = 4.0 if blocked else 10.0
    reduction = _reduce_grievance(target_record, amount)
    _improve(target_record, trust=0.5 if blocked else 1.5, satisfaction=1.0 if blocked else 2.0)
    if not blocked:
        _set_marker(target_record, 'ready_to_forgive_steps', 4)
    _notify_outcome(
        actor, target, 'Признание вины',
        ('{} услышал(а), что {} признаёт свою вину, но пока не готов(а) идти дальше.' if blocked else
         '{} оценил(а), что {} признал(а) свою ответственность. Это не стирает прошлое, но помогает восстановлению доверия.').format(t_name, a_name)
    )
    base.flog('V050 ADMIT FAULT: {} -> {} reduced {:.2f}'.format(a_name, t_name, reduction))
    _sync_records(actor_record, target_record)
    return True


def _do_forgive(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if actor_record is None:
        return False
    _set_cooldown(actor_record, 'forgive', 3)  # ~18 sim hours
    a_name, t_name = _names(actor, target)

    reduction = _reduce_grievance(actor_record, 15.0)
    _improve(actor_record, trust=3.0, satisfaction=4.0, attachment=1.0)
    actor_record['forgiveness_block_steps'] = 0
    actor_record['ready_to_forgive_steps'] = 0
    if _resentment(actor_record) < 8.0:
        _set_marker(actor_record, 'closeness_steps', 4)
    else:
        _set_marker(actor_record, 'second_chance_steps', 4)
    _notify_outcome(
        actor, target, 'Прощение',
        '{} решил(а) попытаться простить {}. Прощение уменьшает обиду, но доверие всё равно придётся восстанавливать поступками.'.format(a_name, t_name)
    )
    base.flog('V050 FORGIVE: {} -> {} reduced {:.2f}'.format(a_name, t_name, reduction))
    _sync_records(actor_record, target_record)
    return True


def _do_not_ready(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if actor_record is None:
        return False
    _set_cooldown(actor_record, 'not_ready', 4)
    _set_marker(actor_record, 'forgiveness_block_steps', 4)  # ~24 sim hours
    actor_record['ready_to_forgive_steps'] = 0
    actor_record['second_chance_steps'] = 0
    a_name, t_name = _names(actor, target)
    _notify_outcome(
        actor, target, 'Не готов(а) простить',
        '{} дал(а) понять {}, что сейчас не готов(а) к примирению. Следующую попытку лучше сделать позже.'.format(a_name, t_name)
    )
    base.flog('V050 NOT READY: {} -> {}'.format(a_name, t_name))
    _sync_records(actor_record, target_record)
    return True


def _do_second_chance(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if target_record is None:
        return False
    if actor_record is not None:
        _set_cooldown(actor_record, 'second_chance', 4)

    r = _resentment(target_record)
    love = float(target_record.get('love', 0.0) or 0.0)
    trust = float(target_record.get('trust', 0.0) or 0.0)
    attachment = float(target_record.get('attachment', 0.0) or 0.0)
    compatibility = float(target_record.get('compatibility', 50.0) or 50.0)
    chance = 0.10 + love * 0.0030 + attachment * 0.0030 + compatibility * 0.0010 + trust * 0.0010 - r * 0.0040
    a_name, t_name = _names(actor, target)

    if _roll(chance):
        reduction = _reduce_grievance(target_record, 11.0)
        _improve(target_record, trust=2.0, satisfaction=4.0, love=3.0, attachment=1.0)
        _set_marker(target_record, 'second_chance_steps', 8)  # ~2 sim days
        target_record['forgiveness_block_steps'] = 0
        target_record['reconciliation_stage'] = 'second_chance'
        if actor_record is not None:
            _reduce_grievance(actor_record, 7.0)
            _improve(actor_record, satisfaction=2.0, love=2.0)
            _set_marker(actor_record, 'second_chance_steps', 8)
            actor_record['reconciliation_stage'] = 'second_chance'
        _notify_outcome(
            actor, target, 'Второй шанс',
            '{} согласил(ся/ась) дать {} второй шанс. Это не возвращает прежние отношения автоматически — теперь результат зависит от их следующих поступков.'.format(t_name, a_name)
        )
        base.flog('V050 SECOND CHANCE ACCEPTED: {} -> {} reduced {:.2f}'.format(a_name, t_name, reduction))
    else:
        _set_marker(target_record, 'forgiveness_block_steps', 2)
        _notify_outcome(
            actor, target, 'Второй шанс отклонён',
            '{} пока не готов(а) снова довериться {}. Возможно, сначала стоит восстановить доверие менее серьёзными шагами.'.format(t_name, a_name)
        )
        base.flog('V050 SECOND CHANCE REJECTED: {} -> {} chance {:.2f}'.format(a_name, t_name, chance))

    _sync_records(actor_record, target_record)
    return True


ACTION_RUNNERS = {
    'discuss': _do_discuss,
    'apologize': _do_apologize,
    'admit_fault': _do_admit_fault,
    'forgive': _do_forgive,
    'not_ready': _do_not_ready,
    'second_chance': _do_second_chance,
}


class _DeepRelReconciliationInteraction(base.SuperInteraction):
    ACTION = None
    DISPLAY_NAME = 'Глубокие отношения'

    @base.flexmethod
    def get_name(cls, inst, *args, **kwargs):
        return base.LocalizationHelperTuning.get_raw_text(cls.DISPLAY_NAME)

    @classmethod
    def _test(cls, target, context, **kwargs):
        result = super()._test(target, context, **kwargs)
        if not result:
            return result
        try:
            actor = getattr(context, 'sim', None)
            if actor is None or target is None or actor is target:
                return base.TestResult(False)
            if not _can_action(cls.ACTION, actor, target):
                return base.TestResult(False)
        except Exception:
            return base.TestResult(False)
        return base.TestResult.TRUE

    @base.flexmethod
    def _constraint_gen(cls, inst, sim, target, participant_type, **kwargs):
        yield base.Anywhere()

    def _run_interaction_gen(self, timeline):
        yield from ()
        actor = getattr(self, 'sim', None)
        target = getattr(self, 'target', None)
        runner = ACTION_RUNNERS.get(self.ACTION)
        if runner is None:
            return False
        try:
            return bool(runner(actor, target))
        except Exception:
            base.flog('V050 ACTION FAILED: {}'.format(self.ACTION))
            base.flog(traceback.format_exc())
            return False


class DeepRelDiscussProblemsInteraction(_DeepRelReconciliationInteraction):
    ACTION = 'discuss'
    DISPLAY_NAME = 'Обсудить проблемы'


class DeepRelApologizeInteraction(_DeepRelReconciliationInteraction):
    ACTION = 'apologize'
    DISPLAY_NAME = 'Попросить прощения'


class DeepRelAdmitFaultInteraction(_DeepRelReconciliationInteraction):
    ACTION = 'admit_fault'
    DISPLAY_NAME = 'Признать свою вину'


class DeepRelForgiveInteraction(_DeepRelReconciliationInteraction):
    ACTION = 'forgive'
    DISPLAY_NAME = 'Простить'


class DeepRelNotReadyInteraction(_DeepRelReconciliationInteraction):
    ACTION = 'not_ready'
    DISPLAY_NAME = 'Не готов простить'


class DeepRelSecondChanceInteraction(_DeepRelReconciliationInteraction):
    ACTION = 'second_chance'
    DISPLAY_NAME = 'Попросить второй шанс'


def _install_reconciliation_interactions(sim):
    try:
        manager = base.services.affordance_manager()
        current = tuple(getattr(sim, '_super_affordances', ()))
        changed = False
        for interaction_id in ACTION_IDS:
            affordance = manager.get(interaction_id)
            if affordance is None:
                base.flog('V050 INTERACTION TUNING MISSING: {}'.format(interaction_id))
                continue
            if affordance not in current:
                current = current + (affordance,)
                changed = True
        if changed:
            sim._super_affordances = current
        return True
    except Exception:
        base.flog('V050 INTERACTION INSTALL FAILED')
        base.flog(traceback.format_exc())
        return False


def _install_on_instanced_sims():
    try:
        manager = base.services.sim_info_manager()
        if manager is None:
            return 0
        count = 0
        for sim in manager.instanced_sims_gen():
            if _install_reconciliation_interactions(sim):
                count += 1
        return count
    except Exception:
        base.flog('V050 EXISTING SIM INSTALL FAILED')
        base.flog(traceback.format_exc())
        return 0


# Add the interactions to Sims that instantiate after the current zone loads.
_PREVIOUS_SIM_ON_ADD = base.Sim.on_add


def _sim_on_add_v050(self, *args, **kwargs):
    result = _PREVIOUS_SIM_ON_ADD(self, *args, **kwargs)
    _install_reconciliation_interactions(self)
    return result


if not getattr(base.Sim.on_add, '_deeprel_v050_reconciliation', False):
    _sim_on_add_v050._deeprel_v050_reconciliation = True
    base.Sim.on_add = _sim_on_add_v050


# Recovery moodlets now also react directly to reconciliation events.
_PREVIOUS_DESIRED_FOR_RECORD = moodlets._desired_for_record


def _desired_for_record_v050(record):
    desired = set(_PREVIOUS_DESIRED_FOR_RECORD(record))
    if record is None:
        return desired
    block = _block_steps(record)
    ready = int(record.get('ready_to_forgive_steps', 0) or 0)
    second = int(record.get('second_chance_steps', 0) or 0)
    closeness = int(record.get('closeness_steps', 0) or 0)

    if block > 0:
        desired.discard(moodlets.BUFF_READY_TO_FORGIVE)
        desired.discard(moodlets.BUFF_SECOND_CHANCE)
        desired.discard(moodlets.BUFF_CLOSENESS)
    elif second > 0:
        desired.discard(moodlets.BUFF_READY_TO_FORGIVE)
        desired.add(moodlets.BUFF_SECOND_CHANCE)
    elif ready > 0:
        desired.add(moodlets.BUFF_READY_TO_FORGIVE)
    if block <= 0 and closeness > 0:
        desired.add(moodlets.BUFF_CLOSENESS)
    return desired


moodlets._desired_for_record = _desired_for_record_v050


# Cooldowns/temporary reconciliation states advance on the existing six-hour tick.
_PREVIOUS_DECAY_TICK = base.decay_tick


def _decrement_record_timers(record):
    changed = False
    mapping = record.get('reconciliation_cooldowns')
    if isinstance(mapping, dict):
        for key in tuple(mapping.keys()):
            try:
                old = int(mapping.get(key, 0) or 0)
            except Exception:
                old = 0
            new = max(0, old - 1)
            if new != old:
                mapping[key] = new
                changed = True
            if new <= 0:
                mapping.pop(key, None)
    for field in (
        'forgiveness_block_steps', 'ready_to_forgive_steps',
        'second_chance_steps', 'closeness_steps'
    ):
        try:
            old = int(record.get(field, 0) or 0)
        except Exception:
            old = 0
        if old > 0:
            record[field] = old - 1
            changed = True
    if changed:
        base.DIRTY = True
    return changed


def _decay_tick_v050():
    result = _PREVIOUS_DECAY_TICK()
    try:
        any_changed = False
        for record in tuple(base.slot_state().values()):
            if _decrement_record_timers(record):
                any_changed = True
        if any_changed:
            moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V050 RECONCILIATION TIMER TICK FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v050


# Show reconciliation state inside the existing relationship report.
_PREVIOUS_RECORD_TEXT = base.record_text


def _record_text_v050(source, target, record):
    text = _PREVIOUS_RECORD_TEXT(source, target, record)
    if record is None:
        return text
    lines = [text]
    block = _block_steps(record)
    second = int(record.get('second_chance_steps', 0) or 0)
    ready = int(record.get('ready_to_forgive_steps', 0) or 0)
    closeness = int(record.get('closeness_steps', 0) or 0)
    if block > 0:
        lines.extend(['', 'Примирение: пока не готов(а) к разговору (примерно ещё {} ч.)'.format(block * 6)])
    elif second > 0:
        lines.extend(['', 'Примирение: открыт второй шанс (примерно ещё {} ч.)'.format(second * 6)])
    elif closeness > 0:
        lines.extend(['', 'Примирение: пара снова сближается (примерно ещё {} ч.)'.format(closeness * 6)])
    elif ready > 0:
        lines.extend(['', 'Примирение: готовность простить (примерно ещё {} ч.)'.format(ready * 6)])
    return '\n'.join(lines)


base.record_text = _record_text_v050


# Existing zone bootstrap resolves base.initialize_zone dynamically, so wrapping it
# here installs all six interactions without adding another Zone hook.
_PREVIOUS_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v050():
    result = _PREVIOUS_INITIALIZE_ZONE()
    try:
        count = _install_on_instanced_sims()
        moodlets.sync_household_moodlets()
        base.flog('V050 RECONCILIATION READY: {} sims checked'.format(count))
    except Exception:
        base.flog('V050 RECONCILIATION INIT FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v050
base.flog('V050 RECONCILIATION SYSTEM INSTALLED')

# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.0 — breakup process and distance consequences.

This layer deliberately does not fake vanilla divorce/break-up relationship bits.
It handles the emotional process before/after a breakup, and detects the actual
vanilla relationship transition to former partners when the player uses the
normal Sims 4 Break Up / Divorce interaction.
"""

import random
import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzz_deep_relationships_v051 as roles
import zzzzzzzz_deep_relationships_memory_v060 as memory

VERSION = '0.7.0'
base.VERSION = VERSION
moodlets.VERSION = VERSION

INTERACTION_BREAKUP_TALK = 16907167177260101721
INTERACTION_TAKE_PAUSE = 16907167177260101722
INTERACTION_SAVE_RELATIONSHIP = 16907167177260101723
INTERACTION_DECIDE_BREAKUP = 16907167177260101724

ACTION_IDS = (
    INTERACTION_BREAKUP_TALK,
    INTERACTION_TAKE_PAUSE,
    INTERACTION_SAVE_RELATIONSHIP,
    INTERACTION_DECIDE_BREAKUP,
)

memory.MEMORY_LABELS.update({
    'breakup_talk': 'Разговор о возможном расставании',
    'relationship_pause': 'Пауза в отношениях',
    'save_relationship': 'Попытка сохранить отношения',
    'save_relationship_failed': 'Неудачная попытка сохранить отношения',
    'breakup_decision': 'Решение расстаться',
    'breakup': 'Расставание',
    'reunion': 'Возобновление отношений',
})


def _records(actor, target, create=True):
    return reconciliation._records(actor, target, create=create)


def _reverse(record):
    if record is None:
        return None
    try:
        return core._existing_record(
            int(record.get('target_id', 0) or 0),
            int(record.get('source_id', 0) or 0)
        )
    except Exception:
        return None


def _resentment(record):
    return reconciliation._resentment(record)


def _grievance(record, key):
    if record is None:
        return 0.0
    try:
        item = record.get('grievances', {}).get(key)
        if isinstance(item, dict):
            return max(0.0, float(item.get('severity', 0.0) or 0.0))
    except Exception:
        pass
    return 0.0


def _avg(records, key, default=50.0):
    values = []
    for record in records:
        if record is None:
            continue
        try:
            values.append(float(record.get(key, default) or 0.0))
        except Exception:
            pass
    return sum(values) / len(values) if values else float(default)


def _breakup_state(record):
    if record is None:
        return 'none'
    return str(record.get('breakup_state', 'none') or 'none')


def _set_pair_field(actor_record, target_record, key, value):
    for record in (actor_record, target_record):
        if record is not None:
            record[key] = value
            base.DIRTY = True


def _set_pair_marker(actor_record, target_record, key, steps):
    for record in (actor_record, target_record):
        if record is not None:
            record[key] = max(0, int(steps))
            base.DIRTY = True


def _clear_positive_markers(record):
    if record is None:
        return
    for key in ('ready_to_forgive_steps', 'second_chance_steps', 'closeness_steps'):
        record[key] = 0
    base.DIRTY = True


def _risk_for_records(actor_record, target_record):
    records = [r for r in (actor_record, target_record) if r is not None]
    if not records:
        return 0.0
    resentment = max(_resentment(r) for r in records)
    satisfaction = _avg(records, 'satisfaction', 50.0)
    trust = _avg(records, 'trust', 50.0)
    love = _avg(records, 'love', 40.0)
    attachment = _avg(records, 'attachment', 40.0)
    betrayal = max(_grievance(r, 'infidelity') for r in records)

    risk = resentment * 0.55
    risk += max(0.0, 50.0 - satisfaction) * 0.65
    risk += max(0.0, 45.0 - trust) * 0.45
    risk += max(0.0, 35.0 - love) * 0.40
    risk += betrayal * 0.65
    risk -= max(0.0, attachment - 65.0) * 0.12

    states = {_breakup_state(r) for r in records}
    if 'talk' in states:
        risk += 5.0
    if 'pause' in states:
        risk += 10.0
    if 'decided' in states:
        risk += 25.0
    if 'ended' in states:
        return 100.0
    return max(0.0, min(100.0, risk))


def _risk_label(value):
    value = float(value)
    if value >= 85:
        return 'критический'
    if value >= 65:
        return 'высокий'
    if value >= 40:
        return 'средний'
    if value >= 20:
        return 'повышенный'
    return 'низкий'


def _pair_conflict(actor_record, target_record):
    return max(_resentment(actor_record), _resentment(target_record))


def _is_official_partner(source_id, target_id):
    """Detect vanilla spouse/fiance/steady relation without changing it."""
    try:
        manager = base.services.sim_info_manager()
        source = manager.get(int(source_id)) if manager is not None else None
        if source is None:
            return False
        tracker = source.relationship_tracker
        if getattr(tracker, 'spouse_sim_id', None) == int(target_id):
            return True
        if getattr(tracker, 'fiance_sim_id', None) == int(target_id):
            return True
        if int(target_id) in tuple(getattr(tracker, 'steady_sim_ids', ())):
            return True
    except Exception:
        pass
    return False


def _sync(actor_record, target_record):
    try:
        reconciliation._sync_records(actor_record, target_record)
    except Exception:
        base.flog('V070 SYNC FAILED')
        base.flog(traceback.format_exc())


def _notify(actor, target, title, text):
    try:
        reconciliation._notify_outcome(actor, target, title, text)
    except Exception:
        base.notify(title, text, icon_sim=target)


def _can_action(action, actor, target):
    actor_record, target_record = _records(actor, target, create=False)
    if actor_record is None and target_record is None:
        return False
    records = [r for r in (actor_record, target_record) if r is not None]
    if any(r.get('relationship_phase') == 'former' for r in records):
        return False
    if any(_breakup_state(r) == 'ended' for r in records):
        return False

    risk = _risk_for_records(actor_record, target_record)
    conflict = _pair_conflict(actor_record, target_record)
    states = {_breakup_state(r) for r in records}

    if action == 'breakup_talk':
        return risk >= 30.0 or conflict >= 25.0 or _avg(records, 'satisfaction', 50.0) < 35.0
    if action == 'take_pause':
        return 'talk' in states or risk >= 55.0
    if action == 'save_relationship':
        return bool(states.intersection(('talk', 'pause', 'decided'))) or risk >= 55.0
    if action == 'decide_breakup':
        return bool(states.intersection(('talk', 'pause'))) or risk >= 70.0
    return False


def _do_breakup_talk(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if actor_record is None and target_record is None:
        return False
    _set_pair_field(actor_record, target_record, 'breakup_state', 'talk')
    _set_pair_marker(actor_record, target_record, 'breakup_talk_steps', 4)  # 24h
    for record in (actor_record, target_record):
        _clear_positive_markers(record)
        if record is not None:
            memory._add_memory(record, 'breakup_talk', 5.0, merge=True)
    a_name, t_name = reconciliation._names(actor, target)
    _notify(
        actor, target, 'Разговор о расставании',
        '{} и {} всерьёз заговорили о будущем отношений. Теперь у пары есть примерно сутки, чтобы решить: взять паузу, попытаться сохранить отношения или прийти к расставанию.'.format(a_name, t_name)
    )
    _sync(actor_record, target_record)
    return True


def _do_take_pause(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if actor_record is None and target_record is None:
        return False
    _set_pair_field(actor_record, target_record, 'breakup_state', 'pause')
    _set_pair_marker(actor_record, target_record, 'relationship_pause_steps', 8)  # 2 days
    _set_pair_marker(actor_record, target_record, 'breakup_talk_steps', 0)
    for record in (actor_record, target_record):
        _clear_positive_markers(record)
        if record is not None:
            record['forgiveness_block_steps'] = max(2, int(record.get('forgiveness_block_steps', 0) or 0))
            memory._add_memory(record, 'relationship_pause', 6.0, merge=True)
    a_name, t_name = reconciliation._names(actor, target)
    _notify(
        actor, target, 'Пауза в отношениях',
        '{} и {} решили взять паузу примерно на два игровых дня. Обычное романтическое сближение в это время почти не восстанавливает внутренние показатели.'.format(a_name, t_name)
    )
    _sync(actor_record, target_record)
    return True


def _save_chance(actor_record, target_record):
    records = [r for r in (actor_record, target_record) if r is not None]
    love = _avg(records, 'love', 35.0)
    trust = _avg(records, 'trust', 35.0)
    attachment = _avg(records, 'attachment', 40.0)
    compatibility = _avg(records, 'compatibility', 50.0)
    resentment = max((_resentment(r) for r in records), default=0.0)
    betrayal = max((_grievance(r, 'infidelity') for r in records), default=0.0)
    chance = 0.12
    chance += love * 0.0025
    chance += trust * 0.0018
    chance += attachment * 0.0028
    chance += compatibility * 0.0012
    chance -= resentment * 0.0032
    chance -= betrayal * 0.0045
    return max(0.08, min(0.88, chance))


def _do_save_relationship(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if actor_record is None and target_record is None:
        return False
    chance = _save_chance(actor_record, target_record)
    success = random.random() < chance
    records = [r for r in (actor_record, target_record) if r is not None]
    a_name, t_name = reconciliation._names(actor, target)

    if success:
        total = 0.0
        for record in records:
            total += reconciliation._reduce_grievance(record, 7.0)
            reconciliation._improve(record, trust=2.0, satisfaction=4.0, love=1.0, attachment=1.0)
            record['breakup_state'] = 'repairing'
            record['breakup_talk_steps'] = 0
            record['relationship_pause_steps'] = 0
            record['breakup_decision_steps'] = 0
            record['forgiveness_block_steps'] = 0
            record['closeness_steps'] = max(4, int(record.get('closeness_steps', 0) or 0))
            memory._add_memory(record, 'save_relationship', 7.0, merge=True)
        _notify(
            actor, target, 'Попытка сохранить отношения',
            '{} и {} решили не заканчивать отношения сейчас. Конфликт уменьшился, но доверие и удовлетворённость всё ещё придётся восстанавливать поступками.'.format(a_name, t_name)
        )
        base.flog('V070 SAVE RELATIONSHIP SUCCESS: {} <-> {} reduced {:.2f}'.format(a_name, t_name, total))
    else:
        for record in records:
            memory._add_memory(record, 'save_relationship_failed', 5.0, merge=True)
            if _breakup_state(record) == 'none':
                record['breakup_state'] = 'talk'
                record['breakup_talk_steps'] = max(2, int(record.get('breakup_talk_steps', 0) or 0))
        _notify(
            actor, target, 'Отношения пока не удалось спасти',
            '{} и {} попытались договориться, но напряжение осталось. Можно взять паузу или позже снова вернуться к разговору.'.format(a_name, t_name)
        )
        base.flog('V070 SAVE RELATIONSHIP FAILED: {} <-> {} chance {:.2f}'.format(a_name, t_name, chance))
    base.DIRTY = True
    _sync(actor_record, target_record)
    return True


def _do_decide_breakup(actor, target):
    actor_record, target_record = _records(actor, target, create=True)
    if actor_record is None and target_record is None:
        return False
    _set_pair_field(actor_record, target_record, 'breakup_state', 'decided')
    _set_pair_marker(actor_record, target_record, 'breakup_decision_steps', 8)
    _set_pair_marker(actor_record, target_record, 'breakup_talk_steps', 0)
    _set_pair_marker(actor_record, target_record, 'relationship_pause_steps', 0)
    for record in (actor_record, target_record):
        _clear_positive_markers(record)
        if record is not None:
            memory._add_memory(record, 'breakup_decision', 8.0, merge=True)
    a_name, t_name = reconciliation._names(actor, target)
    _notify(
        actor, target, 'Решение о расставании',
        '{} и {} пришли к решению расстаться. Для окончательного разрыва используй стандартное действие Sims 4 «Расстаться» или «Развестись». Мод автоматически распознает фактический разрыв и сохранит его в истории пары.'.format(a_name, t_name)
    )
    _sync(actor_record, target_record)
    return True


ACTION_RUNNERS = {
    'breakup_talk': _do_breakup_talk,
    'take_pause': _do_take_pause,
    'save_relationship': _do_save_relationship,
    'decide_breakup': _do_decide_breakup,
}


class _DeepRelBreakupInteraction(base.SuperInteraction):
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
        runner = ACTION_RUNNERS.get(self.ACTION)
        if runner is None:
            return False
        try:
            return bool(runner(getattr(self, 'sim', None), getattr(self, 'target', None)))
        except Exception:
            base.flog('V070 ACTION FAILED: {}'.format(self.ACTION))
            base.flog(traceback.format_exc())
            return False


class DeepRelBreakupTalkInteraction(_DeepRelBreakupInteraction):
    ACTION = 'breakup_talk'
    DISPLAY_NAME = 'Поговорить о расставании'


class DeepRelTakePauseInteraction(_DeepRelBreakupInteraction):
    ACTION = 'take_pause'
    DISPLAY_NAME = 'Предложить паузу в отношениях'


class DeepRelSaveRelationshipInteraction(_DeepRelBreakupInteraction):
    ACTION = 'save_relationship'
    DISPLAY_NAME = 'Попытаться сохранить отношения'


class DeepRelDecideBreakupInteraction(_DeepRelBreakupInteraction):
    ACTION = 'decide_breakup'
    DISPLAY_NAME = 'Принять решение расстаться'


def _install_breakup_interactions(sim):
    try:
        manager = base.services.affordance_manager()
        current = tuple(getattr(sim, '_super_affordances', ()))
        changed = False
        for interaction_id in ACTION_IDS:
            affordance = manager.get(interaction_id)
            if affordance is None:
                base.flog('V070 INTERACTION TUNING MISSING: {}'.format(interaction_id))
                continue
            if affordance not in current:
                current = current + (affordance,)
                changed = True
        if changed:
            sim._super_affordances = current
        return True
    except Exception:
        base.flog('V070 INTERACTION INSTALL FAILED')
        base.flog(traceback.format_exc())
        return False


def _install_existing():
    try:
        manager = base.services.sim_info_manager()
        if manager is None:
            return 0
        count = 0
        for sim in manager.instanced_sims_gen():
            if _install_breakup_interactions(sim):
                count += 1
        return count
    except Exception:
        base.flog('V070 EXISTING SIM INSTALL FAILED')
        base.flog(traceback.format_exc())
        return 0


_PREVIOUS_SIM_ON_ADD = base.Sim.on_add


def _sim_on_add_v070(self, *args, **kwargs):
    result = _PREVIOUS_SIM_ON_ADD(self, *args, **kwargs)
    _install_breakup_interactions(self)
    return result


if not getattr(base.Sim.on_add, '_deeprel_v070_breakup', False):
    _sim_on_add_v070._deeprel_v070_breakup = True
    base.Sim.on_add = _sim_on_add_v070


# ---------------------------------------------------------------------------
# Breakup state changes moodlets and recovery effectiveness.
# ---------------------------------------------------------------------------
_PREVIOUS_DESIRED = moodlets._desired_for_record


def _desired_for_record_v070(record):
    desired = set(_PREVIOUS_DESIRED(record))
    if record is None:
        return desired
    reverse = _reverse(record)
    states = {_breakup_state(record), _breakup_state(reverse)}
    risk = _risk_for_records(record, reverse)

    if states.intersection(('talk', 'pause', 'decided', 'ended')):
        desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)
        desired.discard(moodlets.BUFF_CLOSENESS)
    if states.intersection(('talk', 'pause', 'decided')):
        desired.add(moodlets.BUFF_UNSTABLE_RELATIONSHIP)
    if 'decided' in states or risk >= 85.0:
        desired.add(moodlets.BUFF_ON_VERGE_BREAKUP)
    if 'ended' in states:
        desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)
        desired.discard(moodlets.BUFF_SECOND_CHANCE)
        desired.discard(moodlets.BUFF_READY_TO_FORGIVE)
    return desired


moodlets._desired_for_record = _desired_for_record_v070


_PREVIOUS_GAIN_MULTIPLIER = memory._gain_multiplier


def _gain_multiplier_v070(record, kind='romance'):
    value = float(_PREVIOUS_GAIN_MULTIPLIER(record, kind))
    state = _breakup_state(record)
    if state == 'pause':
        value = min(value, 0.35)
    elif state == 'decided':
        value = min(value, 0.25)
    elif state == 'talk':
        value = min(value, 0.65)
    try:
        if int(record.get('autonomy_distance_steps', 0) or 0) > 0:
            value = min(value, 0.60)
    except Exception:
        pass
    return max(0.20, min(1.0, value))


memory._gain_multiplier = _gain_multiplier_v070


# ---------------------------------------------------------------------------
# Detect the actual vanilla breakup/divorce transition.
# ---------------------------------------------------------------------------
_PREVIOUS_REFRESH_PHASE = core._refresh_phase


def _mark_actual_breakup(record):
    if record is None:
        return
    reverse = _reverse(record)
    for current in (record, reverse):
        if current is None:
            continue
        current['breakup_state'] = 'ended'
        current['post_breakup_steps'] = max(12, int(current.get('post_breakup_steps', 0) or 0))
        current['breakup_talk_steps'] = 0
        current['relationship_pause_steps'] = 0
        current['breakup_decision_steps'] = 0
        _clear_positive_markers(current)
        memory._add_memory(current, 'breakup', 10.0, merge=True)
        base.DIRTY = True


def _refresh_phase_v070(record):
    if record is None:
        return _PREVIOUS_REFRESH_PHASE(record)
    old_phase = str(record.get('relationship_phase', 'active') or 'active')
    old_breakup = _breakup_state(record)
    result = _PREVIOUS_REFRESH_PHASE(record)
    new_phase = str(record.get('relationship_phase', 'active') or 'active')

    if old_phase != 'former' and new_phase == 'former':
        _mark_actual_breakup(record)
        return result

    # A tiny amount of romance after a breakup should not instantly erase the
    # former-partner history. Officially becoming partners again or completing
    # a second-chance recovery can restore the active state.
    if old_breakup == 'ended' and new_phase == 'active':
        try:
            source_id = int(record.get('source_id', 0) or 0)
            target_id = int(record.get('target_id', 0) or 0)
            official = _is_official_partner(source_id, target_id)
            second = int(record.get('second_chance_steps', 0) or 0) > 0
            if not official and not second:
                record['relationship_phase'] = 'former'
            else:
                record['breakup_state'] = 'repairing'
                memory._add_memory(record, 'reunion', 7.0, merge=True)
                base.DIRTY = True
        except Exception:
            pass
    return result


core._refresh_phase = _refresh_phase_v070


# Successful second chance after a former relationship opens a real recovery path.
_PREVIOUS_SECOND_CHANCE_RUNNER = reconciliation.ACTION_RUNNERS.get('second_chance')


def _second_chance_v070(actor, target):
    result = _PREVIOUS_SECOND_CHANCE_RUNNER(actor, target) if _PREVIOUS_SECOND_CHANCE_RUNNER is not None else False
    if result:
        actor_record, target_record = _records(actor, target, create=False)
        accepted = any(
            r is not None and int(r.get('second_chance_steps', 0) or 0) > 0
            for r in (actor_record, target_record)
        )
        if accepted:
            for record in (actor_record, target_record):
                if record is not None and _breakup_state(record) == 'ended':
                    record['breakup_state'] = 'repairing'
                    base.DIRTY = True
    return result


if _PREVIOUS_SECOND_CHANCE_RUNNER is not None:
    reconciliation.ACTION_RUNNERS['second_chance'] = _second_chance_v070


# ---------------------------------------------------------------------------
# Six-hour progression and basic autonomous-distance consequences.
# This does NOT make Sims autonomously press "break up". It changes how much
# spontaneous positive contact can repair a relationship while the crisis is high.
# ---------------------------------------------------------------------------
_PREVIOUS_DECAY = base.decay_tick


def _decrement(record, key):
    try:
        old = int(record.get(key, 0) or 0)
    except Exception:
        old = 0
    if old > 0:
        record[key] = old - 1
        base.DIRTY = True
    return max(0, old - 1)


def _decay_tick_v070():
    result = _PREVIOUS_DECAY()
    try:
        processed_pairs = set()
        for record in tuple(base.slot_state().values()):
            source_id = int(record.get('source_id', 0) or 0)
            target_id = int(record.get('target_id', 0) or 0)
            pair = (min(source_id, target_id), max(source_id, target_id))
            if pair in processed_pairs:
                continue
            processed_pairs.add(pair)
            reverse = _reverse(record)
            records = [r for r in (record, reverse) if r is not None]
            if not records:
                continue

            for current in records:
                _decrement(current, 'breakup_talk_steps')
                pause_left = _decrement(current, 'relationship_pause_steps')
                _decrement(current, 'breakup_decision_steps')
                _decrement(current, 'post_breakup_steps')
                _decrement(current, 'autonomy_distance_steps')
                if _breakup_state(current) == 'talk' and int(current.get('breakup_talk_steps', 0) or 0) <= 0:
                    current['breakup_state'] = 'none'
                if _breakup_state(current) == 'pause' and pause_left <= 0:
                    current['breakup_state'] = 'talk'
                if _breakup_state(current) == 'repairing':
                    if _resentment(current) < 8.0 and float(current.get('trust', 0.0) or 0.0) >= 45.0 and float(current.get('satisfaction', 0.0) or 0.0) >= 45.0:
                        current['breakup_state'] = 'none'
                        memory._add_memory(current, 'reunion', 6.0, merge=True)
                base.DIRTY = True

            risk = _risk_for_records(record, reverse)
            if risk >= 65.0 and not any(_breakup_state(r) in ('ended', 'repairing') for r in records):
                for current in records:
                    current['autonomy_distance_steps'] = max(2, int(current.get('autonomy_distance_steps', 0) or 0))
                    base.DIRTY = True
            _sync(record, reverse)
    except Exception:
        base.flog('V070 BREAKUP TICK FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v070


# ---------------------------------------------------------------------------
# Relationship report.
# ---------------------------------------------------------------------------
_PREVIOUS_RECORD_TEXT = base.record_text


def _state_text(record):
    state = _breakup_state(record)
    return {
        'none': 'нет активного решения о расставании',
        'talk': 'обсуждение будущего отношений',
        'pause': 'пауза в отношениях',
        'decided': 'решение расстаться принято',
        'ended': 'отношения завершены',
        'repairing': 'попытка восстановить отношения',
    }.get(state, state)


def _record_text_v070(source, target, record):
    text = _PREVIOUS_RECORD_TEXT(source, target, record)
    if record is None:
        return text
    reverse = _reverse(record)
    risk = _risk_for_records(record, reverse)
    lines = [text, '', 'Риск расставания: {} ({:.0f}%)'.format(_risk_label(risk), risk)]
    lines.append('Статус решения: {}'.format(_state_text(record)))
    pause = int(record.get('relationship_pause_steps', 0) or 0)
    talk = int(record.get('breakup_talk_steps', 0) or 0)
    distance = int(record.get('autonomy_distance_steps', 0) or 0)
    if pause > 0:
        lines.append('Пауза: ещё примерно {} ч.'.format(pause * 6))
    elif talk > 0:
        lines.append('Время на решение: ещё примерно {} ч.'.format(talk * 6))
    if distance > 0:
        lines.append('Склонность к дистанции: высокая — спонтанное позитивное общение хуже восстанавливает отношения.')
    if _breakup_state(record) == 'decided':
        lines.append('Для окончательного разрыва используй стандартное действие Sims 4 «Расстаться/Развестись».')
    return '\n'.join(lines)


base.record_text = _record_text_v070


# Migrate current records without resetting anything.
def _migrate_v070():
    changed = 0
    try:
        for record in tuple(base.slot_state().values()):
            defaults = {
                'breakup_state': 'none',
                'breakup_talk_steps': 0,
                'relationship_pause_steps': 0,
                'breakup_decision_steps': 0,
                'post_breakup_steps': 0,
                'autonomy_distance_steps': 0,
            }
            for key, value in defaults.items():
                if key not in record:
                    record[key] = value
                    changed += 1
        if changed:
            base.DIRTY = True
        base.flog('V070 MIGRATION COMPLETE: {} fields'.format(changed))
    except Exception:
        base.flog('V070 MIGRATION FAILED')
        base.flog(traceback.format_exc())


_PREVIOUS_INIT = base.initialize_zone


def _initialize_zone_v070():
    result = _PREVIOUS_INIT()
    try:
        _migrate_v070()
        count = _install_existing()
        moodlets.sync_household_moodlets()
        base.flog('V070 BREAKUP SYSTEM READY: {} sims checked'.format(count))
    except Exception:
        base.flog('V070 INIT FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v070
base.flog('V070 BREAKUP AND DISTANCE SYSTEM INSTALLED')

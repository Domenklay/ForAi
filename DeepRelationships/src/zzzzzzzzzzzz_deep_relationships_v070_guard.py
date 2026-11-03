# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.0 guard — breakup action cooldowns."""

import traceback

import deep_relationships as base
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzzzzzz_deep_relationships_breakup_v070 as breakup

VERSION = '0.7.0'

_PREVIOUS_CAN_ACTION = breakup._can_action


def _actor_record(actor, target):
    actor_record, _ = breakup._records(actor, target, create=False)
    return actor_record


def _can_action_guard(action, actor, target):
    if not _PREVIOUS_CAN_ACTION(action, actor, target):
        return False
    actor_record, target_record = breakup._records(actor, target, create=False)
    if actor_record is None and target_record is None:
        return False

    states = set()
    for record in (actor_record, target_record):
        if record is not None:
            states.add(breakup._breakup_state(record))

    if action == 'decide_breakup' and 'decided' in states:
        return False

    cooldown_key = {
        'breakup_talk': 'breakup_talk',
        'take_pause': 'take_pause',
        'save_relationship': 'save_relationship',
        'decide_breakup': 'decide_breakup',
    }.get(action)
    if cooldown_key and actor_record is not None:
        try:
            if reconciliation._cooldown(actor_record, cooldown_key) > 0:
                return False
        except Exception:
            return False
    return True


breakup._can_action = _can_action_guard


def _wrap_runner(action, runner, steps):
    def wrapped(actor, target):
        actor_record, _ = breakup._records(actor, target, create=False)
        if actor_record is not None:
            reconciliation._set_cooldown(actor_record, action, steps)
        return runner(actor, target)
    return wrapped


_COOLDOWNS = {
    'breakup_talk': 2,       # ~12h
    'take_pause': 4,         # ~24h
    'save_relationship': 4,  # ~24h
    'decide_breakup': 8,     # ~48h; normally hidden after decision anyway
}

try:
    for _action, _steps in _COOLDOWNS.items():
        _runner = breakup.ACTION_RUNNERS.get(_action)
        if _runner is not None:
            breakup.ACTION_RUNNERS[_action] = _wrap_runner(_action, _runner, _steps)
except Exception:
    base.flog('V070 COOLDOWN GUARD FAILED')
    base.flog(traceback.format_exc())

base.flog('V070 BREAKUP COOLDOWN GUARD INSTALLED')

# -*- coding: utf-8 -*-
"""Single canonical catalogue and dispatcher for original player actions.

Runners are intentionally injected later by the gameplay layer. Registering a
label is NOT equivalent to making an action available inside Sims 4.
"""
ACTIONS = {
    "discuss": "Обсудить проблемы",
    "apologize": "Извиниться",
    "admit_fault": "Признать вину",
    "forgive": "Простить",
    "not_ready": "Не готов простить",
    "second_chance": "Дать второй шанс",
    "breakup_talk": "Поговорить о расставании",
    "take_pause": "Взять паузу",
    "save_relationship": "Попробовать спасти отношения",
    "decide_breakup": "Решить расстаться",
}


class ActionRegistry(object):
    def __init__(self, stage_dispatch, log=None):
        self.runners = {}
        self.conditions = {}
        self.dispatch = stage_dispatch
        self.log = log if log is not None else (lambda message: None)
        self._busy = set()

    def register(self, action_id, runner, condition=None):
        if action_id not in ACTIONS:
            raise ValueError("Unknown action {}".format(action_id))
        if action_id in self.runners:
            raise ValueError("Duplicate runner for {}".format(action_id))
        if not callable(runner):
            raise TypeError("Runner must be callable")
        self.runners[action_id] = runner
        self.conditions[action_id] = condition or (lambda a, b: True)

    def available(self, action_id, actor, partner):
        if actor == partner or actor is None or partner is None:
            return False
        return (action_id in self.runners and
                bool(self.conditions[action_id](actor, partner)))

    def execute(self, action_id, actor, partner):
        """Refresh both Sims only after a successful gameplay action."""
        if not self.available(action_id, actor, partner):
            return False
        key = (action_id, actor, partner)
        if key in self._busy:
            return False
        self._busy.add(key)
        try:
            succeeded = bool(self.runners[action_id](actor, partner))
            if succeeded:
                self.dispatch.pair_changed(actor, partner, "action:" + action_id)
            return succeeded
        except Exception as exc:
            self.log("ACTION ERROR {} {} {}".format(action_id, type(exc).__name__, exc))
            return False
        finally:
            self._busy.discard(key)

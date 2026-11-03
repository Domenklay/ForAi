# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from actions import ACTIONS, ActionRegistry


class Dispatch(object):
    def __init__(self):
        self.calls = []
    def pair_changed(self, a, b, name):
        self.calls.append((a, b, name))
        return True


class ActionRegistryTests(unittest.TestCase):
    def setUp(self):
        self.dispatch = Dispatch()
        self.reg = ActionRegistry(self.dispatch)

    def test_ten_actions_and_labels(self):
        self.assertEqual(len(ACTIONS), 10)
        self.assertTrue(all(ACTIONS.values()))

    def test_success_refreshes_both_via_dispatch(self):
        self.reg.register("apologize", lambda a,b: True)
        self.assertTrue(self.reg.execute("apologize", 1, 2))
        self.assertEqual(self.dispatch.calls, [(1, 2, "action:apologize")])

    def test_failure_does_not_refresh(self):
        self.reg.register("apologize", lambda a,b: False)
        self.assertFalse(self.reg.execute("apologize", 1, 2))
        self.assertEqual(self.dispatch.calls, [])

    def test_disabled_condition(self):
        self.reg.register("forgive", lambda a,b: True,
                          condition=lambda a,b: False)
        self.assertFalse(self.reg.execute("forgive", 1, 2))

    def test_duplicate_registration_fails(self):
        self.reg.register("discuss", lambda a,b: True)
        with self.assertRaises(ValueError):
            self.reg.register("discuss", lambda a,b: True)

    def test_missing_runner_not_shown(self):
        self.assertFalse(self.reg.available("take_pause", 1, 2))


if __name__ == "__main__":
    unittest.main()

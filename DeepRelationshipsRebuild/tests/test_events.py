# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from events import EventDispatcher


class FakeCoordinator(object):
    def __init__(self):
        self.calls = []
    def refresh_sim(self, sim_id, event):
        self.calls.append(("sim", sim_id, event))
        return True
    def refresh_pair(self, actor_id, target_id, event):
        self.calls.append(("pair", actor_id, target_id, event))
        return True


class EventTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeCoordinator()
        self.logs = []
        self.dispatcher = EventDispatcher(self.fake, self.logs.append)

    def test_load_deduplicates(self):
        self.assertTrue(self.dispatcher.household_loaded([1, 1, 2]))
        self.assertEqual(self.fake.calls, [("sim", 1, "zone_loaded"),
                                           ("sim", 2, "zone_loaded")])

    def test_pair_event(self):
        self.assertTrue(self.dispatcher.pair_changed(1, 2, "argument"))
        self.assertEqual(self.fake.calls, [("pair", 1, 2, "argument")])

    def test_reentrancy(self):
        class Reenter(FakeCoordinator):
            def refresh_pair(inner, a, b, event):
                return self.dispatcher.pair_changed(a, b, event)
        self.dispatcher.coordinator = Reenter()
        self.assertFalse(self.dispatcher.pair_changed(1, 2, "argument"))
        self.assertTrue(any("EVENT SKIP" in line for line in self.logs))


if __name__ == "__main__":
    unittest.main()

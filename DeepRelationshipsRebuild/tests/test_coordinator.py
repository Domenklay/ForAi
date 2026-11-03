# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from coordinator import StageCoordinator
from moodlets import STAGE_TO_BUFF


class StageCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.records = [
            {"source_id": 1, "target_id": 2, "resentment": 2},
            {"source_id": 2, "target_id": 1, "resentment": 2},
        ]
        self.buffs = {1: {777}, 2: {888}}
        self.messages = []
        self.operations = []

        def add(sim, buff):
            self.operations.append(("add", sim, buff))
            self.buffs[sim].add(buff)

        def remove(sim, buff):
            self.operations.append(("remove", sim, buff))
            self.buffs[sim].discard(buff)

        self.coordinator = StageCoordinator(
            lambda: self.records,
            lambda sim: self.buffs[sim],
            remove, add,
            self.messages.append
        )

    def test_both_partners_and_supplementary_moods(self):
        self.assertTrue(self.coordinator.refresh_pair(1, 2, "argument"))
        self.assertEqual(self.buffs[1], {777, STAGE_TO_BUFF["argument"]})
        self.assertEqual(self.buffs[2], {888, STAGE_TO_BUFF["argument"]})

    def test_no_duplicate_on_repeat(self):
        self.assertTrue(self.coordinator.refresh_pair(1, 2))
        self.operations[:] = []
        self.assertTrue(self.coordinator.refresh_pair(1, 2))
        self.assertEqual(self.operations, [])

    def test_stage_change(self):
        self.coordinator.refresh_pair(1, 2)
        self.records[0]["resentment"] = 80
        self.assertTrue(self.coordinator.refresh_pair(1, 2, "deep_conflict"))
        self.assertEqual(self.buffs[1], {777, STAGE_TO_BUFF["deep_conflict"]})
        self.assertEqual(self.buffs[2], {888, STAGE_TO_BUFF["deep_conflict"]})

    def test_add_failure_detected(self):
        def ignored_add(sim, buff):
            pass
        self.coordinator.buff_adder = ignored_add
        self.assertFalse(self.coordinator.refresh_sim(1, "broken_add"))
        self.assertTrue(any("missing" in m for m in self.messages))

    def test_action_error_is_logged_and_not_propagated(self):
        self.coordinator.record_reader = lambda: 1 / 0
        self.assertFalse(self.coordinator.refresh_sim(1))
        self.assertIn("MOODLETS ERROR", self.messages[-1])


if __name__ == "__main__":
    unittest.main()

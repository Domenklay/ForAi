# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import RelationshipRuntime, RelationshipStore


class Bridge(object):
    def __init__(self):
        self.events = []
    def install(self, reader, log):
        self.reader = reader
        return self
    def pair_changed(self, a, b, name):
        self.events.append((a, b, name))
        return True
    def on_zone_ready(self):
        self.events.append(("zone",))
        return True


def fixture():
    return {"slots": {"1": {"relationships": {
        "1:2": {"source_id": 1, "target_id": 2, "trust": 70, "satisfaction": 70,
                "love": 70, "attachment": 70, "compatibility": 70},
        "2:1": {"source_id": 2, "target_id": 1, "trust": 70, "satisfaction": 70,
                "love": 70, "attachment": 70, "compatibility": 70}
    }}}}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()
        self.store = RelationshipStore()
        self.assertEqual(self.store.load_legacy(self.data, 1), 2)
        self.bridge = Bridge()
        self.runtime = RelationshipRuntime(self.store, self.bridge, random_number=lambda: 0.0)

    def test_load_does_not_mutate_legacy_save(self):
        self.runtime.execute_action("not_ready", 1, 2)
        self.assertNotIn("forgiveness_block_steps",
                         self.data["slots"]["1"]["relationships"]["1:2"])
        self.assertTrue(self.store.dirty)
        self.assertEqual(self.bridge.events[0], (1, 2, "action:not_ready"))

    def test_delta_uses_live_in_memory_data(self):
        self.assertTrue(self.runtime.on_score_changed(1, 2, "romance", -10))
        self.assertEqual(self.store.existing(1, 2)["grievances"]
                         ["romantic_hurt"]["severity"], 3.2)
        self.assertTrue(self.store.dirty)

    def test_healthy_pair_action_works_both_directions(self):
        self.assertTrue(self.runtime.execute_action("take_pause", 1, 2))
        one, two = self.store.get_pair(1, 2)
        self.assertEqual(one["breakup_state"], "pause")
        self.assertEqual(two["breakup_state"], "pause")

    def test_no_fake_new_couple(self):
        with self.assertRaises(ValueError):
            self.store.get_pair(1, 3)

    def test_read_snapshot_is_defensive(self):
        copy = list(self.store.records())
        copy[0]["trust"] = 0
        self.assertEqual(self.store.existing(1, 2)["trust"], 70)

    def test_second_slot_isolation(self):
        self.store.load_legacy({"slots":{"2":{"relationships":{}}}}, 2)
        self.assertEqual(self.store.records(), ())
        self.assertFalse(self.store.dirty)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from grievances import add_grievance, resentment, reduce_strongest, memory, age, update_metrics


class GrievanceTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "source_id": 1, "target_id": 2, "trust": 80.0,
            "satisfaction": 80.0, "love": 70.0, "attachment": 70.0,
        }

    def test_grievance_accumulates_and_merges_memory(self):
        add_grievance(self.record, "arguments", 5)
        add_grievance(self.record, "arguments", 6)
        self.assertEqual(resentment(self.record), 11)
        self.assertEqual(self.record["grievances"]["arguments"]["count"], 2)
        self.assertEqual(len(self.record["relationship_memories"]), 1)
        self.assertEqual(self.record["last_conflict_state"], "Лёгкое раздражение")

    def test_betrayal_reduces_slowly(self):
        add_grievance(self.record, "infidelity", 20)
        self.assertAlmostEqual(reduce_strongest(self.record, 10), 4.5)
        self.assertAlmostEqual(resentment(self.record), 15.5)
        self.assertEqual(self.record["relationship_memories"][0]["kind"], "betrayal")

    def test_caps_limit_trust_during_severe_grievances(self):
        add_grievance(self.record, "arguments", 80)
        self.assertLessEqual(self.record["trust"], 52.0)
        update_metrics(self.record, trust=30, satisfaction=50)
        self.assertLessEqual(self.record["trust"], 52.0)

    def test_memories_are_bounded(self):
        for i in range(60):
            memory(self.record, "unique_" + str(i), severity=2, merge=False)
        self.assertLessEqual(len(self.record["relationship_memories"]), 30)

    def test_age_reduces_not_immediately_destroys_betrayal(self):
        add_grievance(self.record, "infidelity", 10)
        age(self.record)
        self.assertIn("infidelity", self.record["grievances"])
        self.assertIn("betrayal", [m["kind"] for m in self.record["relationship_memories"]])

    def test_invalid_reason_fails(self):
        with self.assertRaises(ValueError):
            add_grievance(self.record, "unknown", 4)


if __name__ == "__main__":
    unittest.main()

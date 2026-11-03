# -*- coding: utf-8 -*-
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from legacy import LegacyStateError, legacy_relationships, parse_legacy_json


class LegacyTests(unittest.TestCase):
    def test_slot_read_preserves_fields_and_original(self):
        record = {"source_id": "1", "target_id": "2", "resentment": 13,
                  "relationship_memories": [{"kind": "argument", "age_steps": 1}],
                  "custom": {"keep": "this"}}
        data = {"version": 3, "slots": {"7": {"relationships": {"1:2": record}},
                                       "8": {"relationships": {}}}}
        before = json.dumps(data, sort_keys=True)
        loaded = legacy_relationships(data, "7")
        self.assertEqual(loaded[0]["custom"], {"keep": "this"})
        self.assertEqual(loaded[0]["source_id"], 1)
        self.assertEqual(json.dumps(data, sort_keys=True), before)
        self.assertEqual(legacy_relationships(data, "8"), [])

    def test_invalid_top_level_never_silently_resets(self):
        with self.assertRaises(LegacyStateError):
            legacy_relationships({"slots": []}, 1)

    def test_skips_bad_pairs(self):
        data = {"slots": {"0": {"relationships": {
            "a": {"source_id": 3, "target_id": 3},
            "b": {"source_id": 2, "target_id": 4},
            "c": {"source_id": "wrong", "target_id": 5},
        }}}}
        self.assertEqual(len(parse_legacy_json(json.dumps(data), 0)), 1)


if __name__ == "__main__":
    unittest.main()

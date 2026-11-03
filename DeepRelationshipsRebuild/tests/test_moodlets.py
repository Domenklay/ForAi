# -*- coding: utf-8 -*-
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from moodlets import changeset, STAGE_TO_BUFF, STAGE_BUFFS


class MoodletTests(unittest.TestCase):
    def test_ten_unique_ids(self):
        self.assertEqual(len(STAGE_TO_BUFF), 10)
        self.assertEqual(len(STAGE_BUFFS), 10)

    def test_add_missing_stage(self):
        removed, added = changeset(set(), "argument")
        self.assertFalse(removed)
        self.assertEqual(added, {STAGE_TO_BUFF["argument"]})

    def test_replace_only_stage(self):
        unrelated = 12004666048318715110
        current = {unrelated, STAGE_TO_BUFF["argument"]}
        removed, added = changeset(current, "reconciliation")
        self.assertEqual(removed, {STAGE_TO_BUFF["argument"], unrelated})
        self.assertEqual(added, {STAGE_TO_BUFF["reconciliation"]})
        self.assertIn(unrelated, removed)

    def test_no_duplicate(self):
        self.assertEqual(changeset({STAGE_TO_BUFF["pause"]}, "pause"), (set(), set()))

    def test_clear_when_no_stage(self):
        self.assertEqual(changeset({STAGE_TO_BUFF["pause"]}, None),
                         ({STAGE_TO_BUFF["pause"]}, set()))

    def test_reject_unknown(self):
        with self.assertRaises(ValueError):
            changeset([], "unknown")


if __name__ == "__main__":
    unittest.main()

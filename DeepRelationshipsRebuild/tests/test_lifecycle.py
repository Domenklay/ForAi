# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"engine"))
from lifecycle import tick_record


class LifecycleTests(unittest.TestCase):
    def test_pause_expires(self):
        rec={"source_id":1,"target_id":2,"breakup_state":"pause","relationship_pause_steps":1}
        tick_record(rec)
        self.assertEqual(rec["breakup_state"],"talk")
        tick_record(rec)
        self.assertEqual(rec["breakup_state"],"none")

    def test_second_chance_expires(self):
        rec={"source_id":1,"target_id":2,"second_chance_steps":1,
             "reconciliation_stage":"second_chance"}
        tick_record(rec)
        self.assertEqual(rec["second_chance_steps"],0)
        self.assertEqual(rec["reconciliation_stage"],"")

    def test_recovery_finalizes_after_trust_returns(self):
        rec={"source_id":1,"target_id":2,"breakup_state":"repairing",
             "trust":65,"satisfaction":65}
        tick_record(rec)
        self.assertEqual(rec["breakup_state"],"none")
        self.assertTrue(any(m.get("kind")=="reunion"
                            for m in rec["relationship_memories"]))

    def test_recovery_not_finalized_low_trust(self):
        rec={"source_id":1,"target_id":2,"breakup_state":"repairing",
             "trust":10,"satisfaction":65}
        tick_record(rec)
        self.assertEqual(rec["breakup_state"],"repairing")


if __name__=="__main__":
    unittest.main()

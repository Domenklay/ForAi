# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from social import apply_score_delta
from grievances import add_grievance, resentment


class SocialDeltaTests(unittest.TestCase):
    def setUp(self):
        self.r={"source_id":1,"target_id":2,"trust":60,"satisfaction":70,
                "relationship_memories":[]}

    def test_negative_romance_hurts(self):
        self.assertTrue(apply_score_delta(self.r,-10,"romance"))
        self.assertAlmostEqual(self.r["grievances"]["romantic_hurt"]["severity"],3.2)

    def test_negative_friendship_causes_arguments(self):
        self.assertTrue(apply_score_delta(self.r,-10,"friendship"))
        self.assertAlmostEqual(self.r["grievances"]["arguments"]["severity"],2.8)

    def test_positive_contact_repairs_neglect_not_betrayal(self):
        add_grievance(self.r,"neglect",9)
        add_grievance(self.r,"infidelity",20)
        before=self.r["grievances"]["neglect"]["severity"]
        betrayal=self.r["grievances"]["infidelity"]["severity"]
        self.assertTrue(apply_score_delta(self.r,10,"romance"))
        self.assertLess(self.r["grievances"]["neglect"]["severity"],before)
        self.assertEqual(self.r["grievances"]["infidelity"]["severity"],betrayal)

    def test_positive_contact_remembers_reconnection(self):
        self.assertTrue(apply_score_delta(self.r,3,"friendship"))
        self.assertEqual(self.r["relationship_memories"][0]["kind"],"reconnection")

    def test_unrelated_track_does_not_change_record(self):
        self.assertFalse(apply_score_delta(self.r,12,"other"))
        self.assertNotIn("grievances",self.r)


if __name__=="__main__":
    unittest.main()

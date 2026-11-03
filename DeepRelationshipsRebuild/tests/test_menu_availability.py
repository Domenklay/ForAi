# -*- coding: utf-8 -*-
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engine"))
from availability import action_allowed

def pair(**overrides):
    a={"love":100,"trust":68,"satisfaction":80,"attachment":57,
       "compatibility":57,"resentment":0,"source_id":1,"target_id":2}
    a.update(overrides)
    b=dict(a,source_id=2,target_id=1)
    return a,b

class MenuAvailabilityTests(unittest.TestCase):
    def test_untouched_couple_offers_only_report(self):
        a,b=pair()
        self.assertTrue(action_allowed("report",a,b))
        for choice in ("discuss","apologize","admit_fault","forgive",
                       "not_ready","second_chance","breakup_talk","take_pause",
                       "save_relationship","decide_breakup"):
            self.assertFalse(action_allowed(choice,a,b),choice)
    def test_conflict_opens_talk_and_pause(self):
        a,b=pair(resentment=12)
        for choice in ("discuss","apologize","take_pause","breakup_talk"):
            self.assertTrue(action_allowed(choice,a,b),choice)
        self.assertFalse(action_allowed("second_chance",a,b))
    def test_pause_does_not_offer_pause_again(self):
        a,b=pair(breakup_state="pause")
        self.assertFalse(action_allowed("take_pause",a,b))
        self.assertTrue(action_allowed("second_chance",a,b))
        self.assertTrue(action_allowed("save_relationship",a,b))
    def test_no_record(self):
        self.assertFalse(action_allowed("report",None,None))
if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engine"))
from moodlets import (ALL_BUFFS, STAGE_BUFFS, EXTRA_BUFFS, EXTRA_BUFF_IDS,
                      desired_ids, changeset)

def record(**changes):
    value={"source_id":1,"target_id":2,"love":75,"trust":70,"attachment":70,
           "compatibility":60,"satisfaction":70,"resentment":0,"quiet_steps":0}
    value.update(changes)
    return value


class SupplementaryMoodletTests(unittest.TestCase):
    def test_26_unique_resources(self):
        self.assertEqual(len(ALL_BUFFS),26)
        self.assertEqual(len(EXTRA_BUFF_IDS),16)
        self.assertEqual(len(ALL_BUFFS.intersection(STAGE_BUFFS)),10)

    def test_healthy_happy_without_stage(self):
        self.assertIn(EXTRA_BUFFS["happy_relationship"],desired_ids(None,record()))
        self.assertNotIn(EXTRA_BUFFS["happy_relationship"],
                         desired_ids("reconciliation",record()))

    def test_jealousy_and_betrayal_can_coexist_with_infidelity(self):
        r=record(trust=25,grievances={"infidelity":{"severity":12}})
        expected=desired_ids("infidelity",r)
        self.assertIn(EXTRA_BUFFS["betrayed_trust"],expected)
        self.assertIn(EXTRA_BUFFS["jealousy"],expected)
        self.assertNotIn(EXTRA_BUFFS["happy_relationship"],expected)

    def test_lonely_replaces_lack_of_attention(self):
        r=record(quiet_steps=25,attachment=70)
        ids=desired_ids(None,r)
        self.assertIn(EXTRA_BUFFS["lonely_in_relationship"],ids)
        self.assertNotIn(EXTRA_BUFFS["lack_of_attention"],ids)

    def test_no_legacy_closeness_during_pause(self):
        r=record(resentment=2)
        ids=desired_ids("pause",r)
        for name in ("happy_relationship","closeness","legacy_second_chance",
                     "ready_to_forgive","light_irritation"):
            self.assertNotIn(EXTRA_BUFFS[name],ids)

    def test_removes_unwanted_extra_moodlet(self):
        r=record(trust=20,grievances={"infidelity":{"severity":9}})
        old=EXTRA_BUFFS["happy_relationship"]
        removed,added=changeset({old},"infidelity",r)
        self.assertIn(old,removed)
        self.assertIn(EXTRA_BUFFS["betrayed_trust"],added)

    def test_partial_records_do_not_fake_breakup(self):
        self.assertEqual(desired_ids(None,{"source_id":1,"target_id":2}),set())

if __name__=="__main__":
    unittest.main()

# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from gameplay import RelationshipActions, bind_action_runners
from actions import ActionRegistry, ACTIONS
from stages import select_stage
from grievances import add_grievance, resentment


class Dispatch(object):
    def __init__(self):
        self.called=[]
    def pair_changed(self, a,b,event):
        self.called.append((a,b,event))


class GameplayTests(unittest.TestCase):
    def setUp(self):
        self.a={"source_id":1,"target_id":2,"trust":70,"satisfaction":70,
                "compatibility":70,"love":75,"attachment":65}
        self.b={"source_id":2,"target_id":1,"trust":70,"satisfaction":70,
                "compatibility":70,"love":75,"attachment":65}
        self.outcomes=[]
        self.logic=RelationshipActions(lambda a,b: (self.a,self.b),lambda: 0.0,
                                       lambda *x:self.outcomes.append(x))

    def test_all_ten_actions_registered(self):
        dispatcher=Dispatch()
        registry=ActionRegistry(dispatcher)
        bind_action_runners(registry,self.logic)
        self.assertEqual(set(registry.runners),set(ACTIONS))
        self.assertTrue(registry.execute("discuss",1,2))
        self.assertEqual(dispatcher.called,[(1,2,"action:discuss")])

    def test_apology_reduces_target_grievance(self):
        add_grievance(self.b,"arguments",15)
        before=resentment(self.b)
        self.logic.apologize(1,2)
        self.assertLess(resentment(self.b),before)
        self.assertEqual(self.logic.last_outcome,("apologize",True))

    def test_refusal_directional(self):
        self.logic.not_ready(1,2)
        self.assertEqual(select_stage(self.a,self.b),"refused_forgive")
        self.assertNotEqual(select_stage(self.b,self.a),"refused_forgive")

    def test_second_chance_acceptance_requires_roll(self):
        self.logic.second_chance(1,2)
        self.assertEqual(select_stage(self.a,self.b),"second_chance")
        self.assertEqual(self.a["reconciliation_stage"],"second_chance")

    def test_rejected_second_chance_does_not_fake_acceptance(self):
        self.logic.roll=lambda: 0.9999
        self.logic.second_chance(1,2)
        self.assertNotEqual(select_stage(self.a,self.b),"second_chance")
        self.assertEqual(self.logic.last_outcome,("second_chance",False))

    def test_pause_both_directions(self):
        self.logic.take_pause(1,2)
        self.assertEqual(select_stage(self.a,self.b),"pause")
        self.assertEqual(select_stage(self.b,self.a),"pause")

    def test_save_relationship_creates_recovery(self):
        self.logic.take_pause(1,2)
        self.logic.save_relationship(1,2)
        self.assertEqual(select_stage(self.a,self.b),"recovery")
        self.assertEqual(self.logic.last_outcome,("save_relationship",True))

    def test_breakup_decision_does_not_end_vanilla_relationship(self):
        self.logic.decide_breakup(1,2)
        self.assertEqual(self.a["breakup_state"],"decided")
        self.assertNotEqual(self.a["breakup_state"],"ended")

    def test_failed_apology_still_counts_as_action(self):
        self.logic.roll=lambda:0.999
        self.assertTrue(self.logic.apologize(1,2))
        self.assertEqual(self.logic.last_outcome,("apologize",False))


if __name__=="__main__":
    unittest.main()

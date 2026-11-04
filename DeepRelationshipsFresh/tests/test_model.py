import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from drfresh_model import pair_key,default_pair,eligible,apply,stage_of
class ModelTests(unittest.TestCase):
    def test_direction_is_same_pair(self):
        self.assertEqual(pair_key(3,2),pair_key(2,3))
    def test_self_relation_rejected(self):
        with self.assertRaises(ValueError):pair_key(1,1)
    def test_healthy_no_conflict_choices(self):
        p=default_pair(1,2)
        for action in ("apologize","pause","reconcile","breakup"):
            self.assertFalse(eligible(action,p),action)
    def test_conflict_resolution(self):
        p=default_pair(1,2)
        for i in range(3):self.assertTrue(apply(p,"complain"))
        self.assertEqual(stage_of(p),"conflict")
        self.assertTrue(apply(p,"pause"))
        self.assertFalse(eligible("pause",p))
        self.assertTrue(apply(p,"reconcile"))
        self.assertNotEqual(stage_of(p),"pause")
    def test_children_no_adult_choices(self):
        p=default_pair(1,2)
        for i in range(3):apply(p,"complain")
        self.assertFalse(eligible("pause",p,False))
        self.assertFalse(eligible("breakup",p,False))
    def test_history_bounded(self):
        p=default_pair(1,2)
        for i in range(100):apply(p,"talk")
        self.assertEqual(len(p["history"]),20)
if __name__=="__main__":unittest.main()

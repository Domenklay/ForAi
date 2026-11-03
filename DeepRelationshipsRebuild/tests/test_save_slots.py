# -*- coding: utf-8 -*-
import sys
import types
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"engine"))
from save_slots import find_save_slot, valid_slot


class SaveSlotTests(unittest.TestCase):
    def test_account_slot(self):
        client=types.SimpleNamespace(account=types.SimpleNamespace(save_slot_id=12))
        self.assertEqual(find_save_slot(client)[0],"12")

    def test_persistence_fallback_when_account_zero(self):
        client=types.SimpleNamespace(account=types.SimpleNamespace(save_slot_id=0))
        persistence=types.SimpleNamespace(save_slot_id=45)
        self.assertEqual(find_save_slot(client,persistence),("45","persistence.save_slot_id"))

    def test_proto_fallback(self):
        persistence=types.SimpleNamespace(
            get_save_slot_proto_buff=lambda:types.SimpleNamespace(slot_id=8))
        self.assertEqual(find_save_slot(None,persistence)[0],"8")

    def test_unresolved_zero_never_trusted(self):
        client=types.SimpleNamespace(account=types.SimpleNamespace(save_slot_id=0))
        self.assertEqual(find_save_slot(client),( "0", "unresolved"))
        self.assertIsNone(valid_slot(0))

if __name__=="__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""Offline regression checks. Run: python -m unittest discover -s DeepRelationshipsRebuild/tests"""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from stages import select_stage, selected_stage_for_sim, STAGES


def pair(**kw):
    result = {"source_id": 1, "target_id": 2, "relationship_phase": "active", "breakup_state": "none"}
    result.update(kw)
    return result


class StageTests(unittest.TestCase):
    def test_ten_unique_stages(self):
        self.assertEqual(len(STAGES), 10)
        self.assertEqual(len(set(STAGES)), 10)

    def test_no_stage_for_healthy_pair(self):
        self.assertIsNone(select_stage(pair()))

    def test_argument(self):
        self.assertEqual(select_stage(pair(resentment=8)), "argument")

    def test_deep_conflict(self):
        self.assertEqual(select_stage(pair(resentment=70)), "deep_conflict")

    def test_infidelity_directional(self):
        record = pair(grievances={"infidelity": {"severity": 3}})
        self.assertEqual(select_stage(record), "infidelity")
        self.assertIsNone(select_stage(pair(), record))

    def test_pause_over_argument(self):
        self.assertEqual(select_stage(pair(breakup_state="pause", resentment=99)), "pause")

    def test_breakup_to_exes(self):
        self.assertEqual(select_stage(pair(breakup_state="ended", post_breakup_steps=5)), "breakup")
        self.assertEqual(select_stage(pair(breakup_state="ended", post_breakup_steps=0)), "exes")

    def test_second_chance_over_infidelity(self):
        self.assertEqual(select_stage(pair(reconciliation_stage="second_chance", second_chance_steps=4,
            grievances={"infidelity": {"severity": 5}})), "second_chance")

    def test_recovery(self):
        self.assertEqual(select_stage(pair(breakup_state="repairing")), "recovery")

    def test_refused_forgive_directional(self):
        self.assertEqual(select_stage(pair(forgiveness_block_steps=2)), "refused_forgive")

    def test_reconciliation(self):
        self.assertEqual(select_stage(pair(closeness_steps=3, resentment=2, trust=55, satisfaction=60)), "reconciliation")

    def test_reverse_direction_severe_conflict(self):
        actor = pair(resentment=0)
        partner = pair(source_id=2, target_id=1, resentment=75)
        self.assertEqual(select_stage(actor, partner), "deep_conflict")
        self.assertEqual(selected_stage_for_sim(1, [actor, partner])[0], "deep_conflict")

    def test_reverse_direction_pause(self):
        actor = pair()
        partner = pair(source_id=2, target_id=1, breakup_state="pause")
        self.assertEqual(selected_stage_for_sim(1, [actor, partner])[0], "pause")

    def test_repair_needs_mutual_trust(self):
        actor = pair(resentment=1, closeness_steps=3, trust=70, satisfaction=70)
        partner = pair(source_id=2, target_id=1, trust=10, satisfaction=80)
        self.assertNotEqual(select_stage(actor, partner), "reconciliation")

    def test_repair_from_recent_memory(self):
        actor = pair(resentment=1, trust=60, satisfaction=60,
                     relationship_memories=[{"kind": "forgiveness", "age_steps": 2}])
        self.assertEqual(select_stage(actor), "reconciliation")

    def test_old_generic_second_chance_is_not_accepted(self):
        actor = pair(second_chance_steps=3)
        self.assertIsNone(select_stage(actor))

    def test_accepted_second_chance_from_other_partner(self):
        actor = pair()
        partner = pair(source_id=2, target_id=1, reconciliation_stage="second_chance",
                       second_chance_steps=3)
        self.assertEqual(select_stage(actor, partner), "second_chance")

    def test_active_partner_beats_historic_ex(self):
        old = pair(target_id=3, relationship_phase="former", breakup_state="ended")
        current = pair(target_id=2, resentment=7)
        self.assertEqual(selected_stage_for_sim(1, [old, current])[0], "argument")

    def test_healthy_active_relationship_hides_old_ex(self):
        old = pair(target_id=3, relationship_phase="former", breakup_state="ended")
        current = pair(target_id=2, trust=70, satisfaction=75)
        self.assertIsNone(selected_stage_for_sim(1, [old, current])[0])

    def test_determinism(self):
        a = pair(target_id=5, resentment=3)
        b = pair(target_id=2, resentment=4)
        first = selected_stage_for_sim(1, [a, b])
        second = selected_stage_for_sim(1, [b, a])
        self.assertEqual(first[1]["target_id"], second[1]["target_id"])


if __name__ == "__main__":
    unittest.main()

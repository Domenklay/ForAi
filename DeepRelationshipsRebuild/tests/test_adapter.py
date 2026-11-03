# -*- coding: utf-8 -*-
"""Tests of adapter integration using minimal fake Sims 4 objects."""
import importlib
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class SimInfo(object):
    def __init__(self, sim_id):
        self.sim_id = sim_id
        self.buffs = set()
    def has_buff(self, buff):
        return buff in self.buffs
    def remove_buff_by_type(self, buff):
        self.buffs.discard(buff)
    def add_buff(self, buff):
        self.buffs.add(buff)
        return True

class GameAdapterTests(unittest.TestCase):
    def setUp(self):
        self.sims = {1: SimInfo(1), 2: SimInfo(2)}
        self.buff_registry = {}
        self.household = types.SimpleNamespace(
            sim_info_gen=lambda: iter(self.sims.values()))
        sims = self.sims
        registry = self.buff_registry
        fake_services = types.ModuleType("services")
        fake_services.sim_info_manager = lambda: types.SimpleNamespace(get=lambda i: sims.get(i))
        fake_services.get_instance_manager = lambda type_id: types.SimpleNamespace(get=lambda i: registry.get(i))
        fake_services.active_household = lambda: self.household
        fake_sims4 = types.ModuleType("sims4")
        fake_resources = types.ModuleType("sims4.resources")
        fake_resources.Types = types.SimpleNamespace(BUFF=1)
        fake_sims4.resources = fake_resources
        self.previous = {k: sys.modules.get(k) for k in ("services", "sims4", "sims4.resources", "adapter.game")}
        sys.modules.update({"services": fake_services, "sims4": fake_sims4, "sims4.resources": fake_resources})
        sys.modules.pop("adapter.game", None)
        self.game = importlib.import_module("adapter.game")
        # Existing integration tests explicitly exercise the opt-in engine;
        # production safe mode stays disabled by default.
        self.game.CUSTOM_BUFFS_ENABLED = True
        self.logs = []
        self.records = [
            {"source_id": 1, "target_id": 2, "resentment": 4},
            {"source_id": 2, "target_id": 1, "resentment": 0},
        ]

    def tearDown(self):
        for key, value in self.previous.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value

    def test_safe_mode_never_modifies_any_sim_buffs(self):
        self.game.CUSTOM_BUFFS_ENABLED = False
        sentinel = object()
        self.sims[1].buffs.add(sentinel)
        self.sims[2].buffs.add(sentinel)
        self.game.install(lambda: self.records, self.logs.append)
        self.assertTrue(self.game.on_zone_ready())
        self.assertFalse(self.game.on_relationship_changed(1, 2, "conflict"))
        self.assertEqual(self.sims[1].buffs, {sentinel})
        self.assertEqual(self.sims[2].buffs, {sentinel})
        self.assertTrue(any("DISABLED" in line for line in self.logs))

    def test_handle_backed_buff_is_removed_when_stage_changes(self):
        from engine.moodlets import STAGE_TO_BUFF
        old_id = STAGE_TO_BUFF["reconciliation"]
        new_id = STAGE_TO_BUFF["pause"]
        old_type = object()
        new_type = object()
        self.buff_registry[old_id] = old_type
        self.buff_registry[new_id] = new_type

        class HandleEntry(object):
            def __init__(self, handles):
                self.handle_ids = handles

        class BuffComponent(object):
            def __init__(self, owner):
                self.owner = owner
                self._active_buffs = {old_type: HandleEntry((101, 102))}
                self.handle_map = {101: old_type, 102: old_type}

            def remove_buff(self, handle, update_mood=True, immediate=True):
                buff = self.handle_map.pop(handle, None)
                if buff is not None:
                    rest = tuple(h for h, t in self.handle_map.items() if t is buff)
                    if rest:
                        self._active_buffs[buff].handle_ids = rest
                    else:
                        self._active_buffs.pop(buff, None)
                        self.owner.buffs.discard(buff)

        for sim in self.sims.values():
            sim.buffs.add(old_type)
            sim.buffs_component = BuffComponent(sim)
            # This simulates the exact failure observed in the game: ordinary
            # remove-by-type does not clear commodity-backed handles.
            sim.remove_buff_by_type = lambda buff: None

        self.game.install(lambda: self.records, self.logs.append)
        self.records[0]["breakup_state"] = "pause"
        self.records[1]["breakup_state"] = "pause"
        self.assertTrue(self.game.on_relationship_changed(1, 2, "take_pause"))
        for sim in self.sims.values():
            self.assertNotIn(old_type, sim.buffs)
            self.assertIn(new_type, sim.buffs)
        self.assertTrue(any("REMOVED BY HANDLES" in line for line in self.logs))

    def test_registered_buff_reaches_both_sims(self):
        from engine.moodlets import STAGE_TO_BUFF
        stage_id = STAGE_TO_BUFF["argument"]
        self.buff_registry[stage_id] = object()
        self.game.install(lambda: self.records, self.logs.append)
        self.assertTrue(self.game.on_zone_ready())
        self.assertIn(self.buff_registry[stage_id], self.sims[1].buffs)
        self.assertIn(self.buff_registry[stage_id], self.sims[2].buffs)

    def test_missing_buff_is_reported_as_failure(self):
        self.game.install(lambda: self.records, self.logs.append)
        self.assertFalse(self.game.on_zone_ready())
        self.assertTrue(any("stages 0/10 extras 0/16" in x for x in self.logs))
        self.assertTrue(any("missing" in x for x in self.logs))

    def test_updates_after_relationship_change(self):
        from engine.moodlets import STAGE_TO_BUFF
        for stage_id in STAGE_TO_BUFF.values():
            self.buff_registry[stage_id] = object()
        self.game.install(lambda: self.records, self.logs.append)
        self.game.on_zone_ready()
        self.records[1]["resentment"] = 80
        self.assertTrue(self.game.on_relationship_changed(1, 2, "conflict"))
        self.assertIn(self.buff_registry[STAGE_TO_BUFF["deep_conflict"]], self.sims[1].buffs)
        self.assertNotIn(self.buff_registry[STAGE_TO_BUFF["argument"]], self.sims[1].buffs)


if __name__ == "__main__":
    unittest.main()

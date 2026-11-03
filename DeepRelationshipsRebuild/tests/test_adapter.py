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
        self.assertTrue(any("REGISTRATION 0/10" in x for x in self.logs))
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

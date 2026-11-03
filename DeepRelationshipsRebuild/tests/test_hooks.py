# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from adapter.hooks import GameHooks


class Zone(object):
    def on_loading_screen_animation_finished(self):
        return "loaded"


class Relationship(object):
    def __init__(self):
        self.value = 0

    def get_relationship_score(self, a, b, track=None):
        return self.value

    def add_relationship_score(self, a, b, increment, track=None):
        self.value += increment
        return "added"

    def set_relationship_score(self, a, b, value, track=None):
        self.value = value
        return "set"


class Bridge(object):
    def __init__(self):
        self.calls = []
    def on_zone_ready(self):
        self.calls.append(("zone",))
    def on_relationship_changed(self, a, b, kind):
        self.calls.append(("pair", a, b, kind))


class HookTests(unittest.TestCase):
    def setUp(self):
        self.bridge = Bridge()
        self.messages = []
        self.deltas = []
        # Classes created per test: avoid residual mutations from another case.
        self.Zone = type("NewZone", (Zone,), {})
        self.Rel = type("NewRel", (Relationship,), {})
        self.hooks = GameHooks(self.bridge, self.messages.append)
        self.kind = lambda track: "friendship" if track is None else "romance"

    def test_installs_once(self):
        self.assertEqual(self.hooks.install(self.Zone, self.Rel, self.kind), 3)
        self.assertEqual(self.hooks.install(self.Zone, self.Rel, self.kind), 0)
        self.assertEqual(self.Zone().on_loading_screen_animation_finished(), "loaded")
        self.assertEqual(self.bridge.calls, [("zone",)])

    def test_add_and_set_exactly_once(self):
        self.hooks.install(self.Zone, self.Rel, self.kind,
                           lambda a,b,k,d: self.deltas.append(d))
        rel = self.Rel()
        self.assertEqual(rel.add_relationship_score(1, 2, 3), "added")
        self.assertEqual(rel.set_relationship_score(1, 2, 10), "set")
        self.assertEqual(rel.set_relationship_score(1, 2, 10), "set")
        self.assertEqual(self.deltas, [3, 7])
        self.assertEqual(len(self.bridge.calls), 2)

    def test_forward_named_track(self):
        self.hooks.install(self.Zone, self.Rel, self.kind)
        rel = self.Rel()
        rel.add_relationship_score(1, 2, 2, track="romance")
        self.assertEqual(self.bridge.calls, [("pair", 1, 2, "romance")])


if __name__ == "__main__":
    unittest.main()

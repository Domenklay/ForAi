# -*- coding: utf-8 -*-
"""In-memory relationship state for the new v0.8 runtime.

The game save adapter owns commit timing. No writes happen in this module.
Every directional relationship is independent, but the UI refreshes the pair.
"""
from copy import deepcopy
from engine.legacy import legacy_relationships
from engine.social import apply_score_delta
from engine.gameplay import RelationshipActions, bind_action_runners
from engine.actions import ActionRegistry


def _id(value):
    try:
        return int(getattr(value, "sim_id", value))
    except (ValueError, TypeError, OverflowError):
        return 0


class RelationshipStore(object):
    def __init__(self):
        self._pairs = {}
        self.dirty = False
        self.slot_id = None

    def load_legacy(self, snapshot, slot_id):
        """Prepare a copy of the requested slot. Repeated loads are safe."""
        selected = {}
        for record in legacy_relationships(snapshot, slot_id):
            selected[(_id(record["source_id"]), _id(record["target_id"]))] = record
        self._pairs = selected
        self.slot_id = str(slot_id)
        self.dirty = False
        return len(selected)

    def records(self):
        # A read-only snapshot avoids externally mutating a tracked record.
        return tuple(deepcopy(r) for r in self._pairs.values())

    def existing(self, actor_id, partner_id):
        return self._pairs.get((_id(actor_id), _id(partner_id)))

    def get_pair(self, actor_id, partner_id):
        """Never fabricate a romantic relationship if it isn't tracked."""
        a = self.existing(actor_id, partner_id)
        b = self.existing(partner_id, actor_id)
        if a is None or b is None:
            raise ValueError("Unknown directed relationship pair")
        return a, b

    def apply_score(self, actor_id, partner_id, kind, actual_delta):
        record = self.existing(actor_id, partner_id)
        if record is None:
            return False
        changed = apply_score_delta(record, actual_delta, kind)
        if changed:
            self.dirty = True
        return changed

    def mark_dirty(self):
        self.dirty = True

    def snapshot(self):
        """Return a non-mutating snapshot; save hook must commit separately."""
        return tuple(deepcopy(r) for r in self._pairs.values())


class RelationshipRuntime(object):
    """Assembles a single event dispatcher, game Buff bridge and action registry."""

    def __init__(self, store, bridge, log=None, random_number=None, outcome=None):
        self.store = store
        self.bridge = bridge
        self.log = log or (lambda line: None)
        self.dispatcher = bridge.install(store.records, self.log)
        self.gameplay = RelationshipActions(store.get_pair, random_number, outcome)
        self.actions = bind_action_runners(ActionRegistry(self.dispatcher, self.log), self.gameplay)

    def on_score_changed(self, actor_id, partner_id, kind, delta):
        return self.store.apply_score(actor_id, partner_id, kind, delta)

    def execute_action(self, name, actor_id, partner_id):
        result = self.actions.execute(name, _id(actor_id), _id(partner_id))
        if result:
            self.store.mark_dirty()
        return result

    def on_zone_ready(self):
        return self.bridge.on_zone_ready()

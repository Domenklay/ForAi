# -*- coding: utf-8 -*-
"""Idempotent Sims 4 hook registration.

Hooks only observe committed EA actions. The caller is responsible for updating
the new relationship records before dispatching a stage refresh; the hook itself
must not mutate user saves. No dependency on legacy v0.7.x modules.
"""
from functools import wraps
import traceback


def wrap_once(obj, method_name, flag, hook, log):
    original = getattr(obj, method_name)
    if getattr(original, flag, False):
        log("HOOK SKIP duplicate {}".format(method_name))
        return False

    @wraps(original)
    def wrapped(*args, **kwargs):
        return hook(original, *args, **kwargs)

    setattr(wrapped, flag, True)
    setattr(obj, method_name, wrapped)
    log("HOOK INSTALLED {}".format(method_name))
    return True


class GameHooks(object):
    def __init__(self, dispatcher, logger):
        self.dispatcher = dispatcher
        self.log = logger

    def install(self, zone_class, relationship_class, kind_from_track,
                after_score_update=None):
        """One zone hook and one observer for each vanilla score mutator."""
        dispatcher = self.dispatcher
        log = self.log
        after_score_update = after_score_update or (lambda a, b, kind, delta: None)

        def zone_hook(original, zone, *args, **kwargs):
            result = original(zone, *args, **kwargs)
            try:
                dispatcher.household_loaded()
            except Exception:
                log("HOOK ZONE ERROR {}".format(traceback.format_exc()))
            return result

        def score_add(original, relationship, sim_a, sim_b, increment,
                      track=None, **kwargs):
            result = original(relationship, sim_a, sim_b, increment,
                              track=track, **kwargs)
            try:
                kind = kind_from_track(track)
                if kind is not None:
                    after_score_update(sim_a, sim_b, kind, increment)
                    dispatcher.on_relationship_changed(sim_a, sim_b, kind)
            except Exception:
                log("HOOK ADD ERROR {}".format(traceback.format_exc()))
            return result

        def score_set(original, relationship, sim_a, sim_b, value,
                      track=None, **kwargs):
            kind = kind_from_track(track)
            before = None
            if kind is not None:
                try:
                    before = float(relationship.get_relationship_score(
                        sim_a, sim_b, track=track))
                except Exception:
                    log("HOOK SET BEFORE ERROR {}".format(traceback.format_exc()))
            result = original(relationship, sim_a, sim_b, value,
                              track=track, **kwargs)
            if kind is not None and before is not None:
                try:
                    after = float(relationship.get_relationship_score(
                        sim_a, sim_b, track=track))
                    delta = after - before
                    if abs(delta) > 0.0001:
                        after_score_update(sim_a, sim_b, kind, delta)
                        dispatcher.on_relationship_changed(sim_a, sim_b, kind)
                except Exception:
                    log("HOOK SET ERROR {}".format(traceback.format_exc()))
            return result

        installed = []
        for cls, name, suffix, handler in (
            (zone_class, "on_loading_screen_animation_finished", "_deeprel_v08_zone", zone_hook),
            (relationship_class, "add_relationship_score", "_deeprel_v08_add", score_add),
            (relationship_class, "set_relationship_score", "_deeprel_v08_set", score_set),
        ):
            installed.append(wrap_once(cls, name, suffix, handler, log))
        return sum(installed)

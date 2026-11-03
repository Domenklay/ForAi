# -*- coding: utf-8 -*-
"""Pure dispatch from game events to relationship stages.

EA-specific callbacks supply sim IDs and current state. This dispatcher does
not touch the game's relationship engine or mutate saved records.
"""


class EventDispatcher(object):
    def __init__(self, coordinator, log=None):
        self.coordinator = coordinator
        self.log = log if log is not None else (lambda message: None)
        self._busy = set()

    def pair_changed(self, source_id, target_id, event):
        key = (str(source_id), str(target_id))
        if key in self._busy:
            self.log("EVENT SKIP recursive {} {}".format(event, key))
            return False
        self._busy.add(key)
        try:
            return self.coordinator.refresh_pair(source_id, target_id, event)
        except Exception as exc:
            self.log("EVENT ERROR {} {} {}".format(event, key, exc))
            return False
        finally:
            self._busy.discard(key)

    def household_loaded(self, sim_ids):
        # First run after zone initialization: exactly once per unique Sim.
        done = set()
        passed = True
        for sim_id in sim_ids:
            if sim_id in done:
                continue
            done.add(sim_id)
            if not self.coordinator.refresh_sim(sim_id, "zone_loaded"):
                passed = False
        self.log("EVENT HOUSEHOLD LOADED checked {} passed {}".format(len(done), passed))
        return passed

# -*- coding: utf-8 -*-
"""Single event-driven stage coordinator; independent of Sims 4 runtime.

Game adapter must report *committed* changed records after processing each
social/event action. This module does not write saves or call EA APIs.
"""
from stages import selected_stage_for_sim
from moodlets import changeset, STAGE_BUFFS


class StageCoordinator(object):
    """Deduplicate stage updates and preserve non-stage moodlets."""

    def __init__(self, record_reader, buff_reader, buff_remover, buff_adder, log=None):
        self.record_reader = record_reader
        self.buff_reader = buff_reader
        self.buff_remover = buff_remover
        self.buff_adder = buff_adder
        self.log = log if log is not None else (lambda message: None)
        self._active = set()

    def refresh_sim(self, sim_id, event="manual"):
        if sim_id in self._active:
            self.log("STAGE REFRESH SKIP reentrant sim {} event {}".format(sim_id, event))
            return False
        self._active.add(sim_id)
        try:
            records = tuple(self.record_reader())
            stage, record = selected_stage_for_sim(sim_id, records)
            present = set(self.buff_reader(sim_id) or ())
            remove, add = changeset(present, stage)
            for buff_id in sorted(remove):
                self.buff_remover(sim_id, buff_id)
            for buff_id in sorted(add):
                self.buff_adder(sim_id, buff_id)
            final = set(self.buff_reader(sim_id) or ())
            leftover_remove, missing_add = changeset(final, stage)
            self.log(
                "STAGE CHECK event {} sim {} stage {} remove {} add {} "
                "registered_or_visible {} leftover {} missing {}".format(
                    event, sim_id, stage, sorted(remove), sorted(add),
                    sorted(final.intersection(STAGE_BUFFS)),
                    sorted(leftover_remove), sorted(missing_add)
                )
            )
            return not leftover_remove and not missing_add
        except Exception as exc:
            self.log("STAGE ERROR event {} sim {} type {} message {}".format(
                event, sim_id, type(exc).__name__, exc
            ))
            return False
        finally:
            self._active.discard(sim_id)

    def refresh_pair(self, actor_id, partner_id, event="relationship_changed"):
        """Two directional refreshes; never refresh only the acting Sim."""
        left = self.refresh_sim(actor_id, event)
        right = self.refresh_sim(partner_id, event) if str(actor_id) != str(partner_id) else True
        return left and right

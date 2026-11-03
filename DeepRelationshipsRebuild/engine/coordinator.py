# -*- coding: utf-8 -*-
"""Single authoritative 26-Buff coordinator, no Sims 4 imports."""
from stages import selected_stage_for_sim
from moodlets import changeset, desired_ids, ALL_BUFFS


class StageCoordinator(object):
    """Tracks changes in desired effects and verifies actual Buff delivery."""

    def __init__(self, record_reader, buff_reader, buff_remover, buff_adder, log=None):
        self.record_reader = record_reader
        self.buff_reader = buff_reader
        self.buff_remover = buff_remover
        self.buff_adder = buff_adder
        self.log = log if log is not None else (lambda message: None)
        self._active = set()
        self._applied = {}

    def refresh_sim(self, sim_id, event="manual"):
        if sim_id in self._active:
            self.log("STAGE REFRESH SKIP reentrant sim {} event {}".format(sim_id, event))
            return False
        self._active.add(sim_id)
        try:
            records = tuple(self.record_reader())
            stage, record = selected_stage_for_sim(sim_id, records)
            desired = frozenset(desired_ids(stage, record))
            forced = event in ("zone_loaded", "scheduled", "manual")
            # A successful prior update can be skipped if the desired set
            # has not changed. Zone loading and the six-hour tick still verify.
            if not forced and self._applied.get(sim_id) == desired:
                return True
            present = set(self.buff_reader(sim_id) or ())
            remove, add = changeset(present, stage, record)
            for buff_id in sorted(remove):
                self.buff_remover(sim_id, buff_id)
            for buff_id in sorted(add):
                self.buff_adder(sim_id, buff_id)
            final = set(self.buff_reader(sim_id) or ())
            leftover_remove, missing_add = changeset(final, stage, record)
            success = not leftover_remove and not missing_add
            if success:
                self._applied[sim_id] = desired
            else:
                self._applied.pop(sim_id, None)
            # Avoid filling the log with unchanged vanilla social contacts.
            if remove or add or not success or event in ("zone_loaded", "scheduled"):
                self.log(
                    "MOODLETS CHECK event {} sim {} stage {} desired {} "
                    "remove {} add {} leftover {} missing {} success {}".format(
                        event, sim_id, stage, len(desired), sorted(remove), sorted(add),
                        sorted(leftover_remove), sorted(missing_add), success
                    )
                )
            return success
        except Exception as exc:
            self._applied.pop(sim_id, None)
            self.log("MOODLETS ERROR event {} sim {} type {} message {}".format(
                event, sim_id, type(exc).__name__, exc))
            return False
        finally:
            self._active.discard(sim_id)

    def refresh_pair(self, actor_id, partner_id, event="relationship_changed"):
        left = self.refresh_sim(actor_id, event)
        right = self.refresh_sim(partner_id, event) if str(actor_id) != str(partner_id) else True
        return left and right

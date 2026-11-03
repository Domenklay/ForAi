# -*- coding: utf-8 -*-
"""Relationship actions using one in-memory pair model (no EA imports).

A returned True means the action ran, NOT that the partner accepted it.
Outcome status is in last_outcome; the ActionRegistry then refreshes both Sims.
A single externally injected random roll keeps tests deterministic.
"""
import random

from grievances import (
    add_grievance, resentment, reduce_strongest, update_metrics, memory, clamp
)


def _steps(record, key, count):
    record[key] = max(0, int(count))


def _average(records, key, fallback):
    return sum(float(r.get(key, fallback) if r.get(key) is not None else fallback)
               for r in records) / len(records)


def _chance(value, ceiling=0.90):
    return min(ceiling, max(0.08, value))


class RelationshipActions(object):
    """Pure gameplay implementation of the ten original action IDs."""

    def __init__(self, read_pair, random_number=None, outcome=None):
        # read_pair(actor, partner) -> (actor->partner, partner->actor)
        self.read_pair = read_pair
        self.roll = random_number or random.random
        self.outcome = outcome or (lambda name, success, actor, target: None)
        self.last_outcome = None

    def _pair(self, a, b):
        left, right = self.read_pair(a, b)
        if not isinstance(left, dict) or not isinstance(right, dict):
            raise ValueError("Both directed relationship records are required")
        return left, right

    def _finish(self, action, accepted, a, b):
        self.last_outcome = (action, accepted)
        self.outcome(action, accepted, a, b)
        return True

    def _roll(self, chance):
        return float(self.roll()) < _chance(chance)

    def discuss(self, actor, partner):
        a, b = self._pair(actor, partner)
        _steps(a, "cooldown_discuss", 1)
        average = _average((a, b), "compatibility", 50)
        trust = _average((a, b), "trust", 40)
        r = (resentment(a)+resentment(b))/2.0
        probability = 0.48 + average*0.0025 + trust*0.0015 - r*0.0025
        success = self._roll(probability)
        if success:
            for record in (a,b):
                reduce_strongest(record, 6 + average*0.035)
                update_metrics(record, trust=1.5, satisfaction=2.5, attachment=0.5)
                _steps(record, "closeness_steps" if resentment(record)<8 else "ready_to_forgive_steps", 4)
                memory(record, "constructive_talk", 3)
        elif probability < 0.35:
            for record in (a,b):
                add_grievance(record, "arguments", 1.5)
        return self._finish("discuss", success, actor, partner)

    def apologize(self, actor, partner):
        a, b = self._pair(actor, partner)
        _steps(a, "cooldown_apologize", 2)
        r = resentment(b)
        trust = float(b.get("trust", 0) or 0)
        attach = float(b.get("attachment", 0) or 0)
        compatible = float(b.get("compatibility", 50) or 50)
        success = self._roll(0.18+trust*0.0030+attach*0.0020+compatible*0.0015-r*0.0035)
        if success:
            reduce_strongest(b, 12+attach*0.05)
            update_metrics(b, trust=2, satisfaction=3, attachment=0.5)
            update_metrics(a, satisfaction=1)
            _steps(b, "closeness_steps" if resentment(b)<8 else "ready_to_forgive_steps", 4)
            memory(b, "apology_accepted", 3)
        else:
            memory(b, "apology_rejected", 3)
        return self._finish("apologize", success, actor, partner)

    def admit_fault(self, actor, partner):
        a,b = self._pair(actor, partner)
        _steps(a, "cooldown_admit_fault", 2)
        blocked = int(b.get("forgiveness_block_steps", 0) or 0)>0
        reduce_strongest(b, 4 if blocked else 10)
        update_metrics(b, trust=0.5 if blocked else 1.5, satisfaction=1 if blocked else 2)
        if not blocked:
            _steps(b, "ready_to_forgive_steps", 4)
        memory(b, "admit_fault", 3)
        return self._finish("admit_fault", not blocked, actor, partner)

    def forgive(self, actor, partner):
        a,b = self._pair(actor, partner)
        _steps(a, "cooldown_forgive", 3)
        reduce_strongest(a, 15)
        update_metrics(a, trust=3, satisfaction=4, attachment=1)
        _steps(a, "forgiveness_block_steps", 0)
        _steps(a, "ready_to_forgive_steps", 0)
        _steps(a, "closeness_steps" if resentment(a)<8 else "second_chance_steps", 4)
        memory(a, "forgiveness", 4)
        return self._finish("forgive", True, actor, partner)

    def not_ready(self, actor, partner):
        a,b = self._pair(actor, partner)
        _steps(a, "cooldown_not_ready", 4)
        _steps(a, "forgiveness_block_steps", 4)
        _steps(a, "ready_to_forgive_steps", 0)
        _steps(a, "second_chance_steps", 0)
        memory(a, "apology_rejected", 4)
        return self._finish("not_ready", True, actor, partner)

    def second_chance(self, actor, partner):
        a,b = self._pair(actor, partner)
        _steps(a, "cooldown_second_chance", 4)
        r=resentment(b)
        success=self._roll(0.10 + float(b.get("love", 0) or 0)*0.003
                           + float(b.get("attachment", 0) or 0)*0.003
                           + float(b.get("compatibility", 50) or 50)*0.001
                           + float(b.get("trust", 0) or 0)*0.001 - r*0.004)
        if success:
            reduce_strongest(b, 11)
            update_metrics(b, trust=2, satisfaction=4, love=3, attachment=1)
            reduce_strongest(a, 7)
            update_metrics(a, satisfaction=2, love=2)
            for record in (a,b):
                _steps(record, "second_chance_steps", 8)
                _steps(record, "forgiveness_block_steps", 0)
                record["reconciliation_stage"] = "second_chance"
                memory(record, "second_chance", 6)
        else:
            _steps(b, "forgiveness_block_steps", 2)
            memory(b, "apology_rejected", 4)
        return self._finish("second_chance", success, actor, partner)

    def breakup_talk(self, actor, partner):
        a,b = self._pair(actor, partner)
        for record in (a,b):
            record["breakup_state"] = "talk"
            _steps(record, "breakup_talk_steps", 4)
            memory(record, "breakup_talk", 5)
        return self._finish("breakup_talk", True, actor, partner)

    def take_pause(self, actor, partner):
        a,b = self._pair(actor, partner)
        for record in (a,b):
            record["breakup_state"] = "pause"
            _steps(record, "relationship_pause_steps", 8)
            _steps(record, "breakup_talk_steps", 0)
            _steps(record, "forgiveness_block_steps",
                   max(2, int(record.get("forgiveness_block_steps",0) or 0)))
            memory(record, "relationship_pause", 6)
        return self._finish("take_pause", True, actor, partner)

    def save_relationship(self, actor, partner):
        a,b = self._pair(actor, partner)
        records=(a,b)
        love=_average(records, "love",35)
        trust=_average(records, "trust",35)
        attachment=_average(records,"attachment",40)
        compatibility=_average(records,"compatibility",50)
        r=max(resentment(a),resentment(b))
        betrayal=max(float(x.get("grievances",{}).get("infidelity",{}).get("severity",0) or 0)
                     for x in records)
        chance=0.12+love*0.0025+trust*0.0018+attachment*0.0028+compatibility*0.0012-r*0.0032-betrayal*0.0045
        success=float(self.roll()) < _chance(chance, ceiling=0.88)
        if success:
            for record in records:
                reduce_strongest(record, 7)
                update_metrics(record, trust=2,satisfaction=4,love=1,attachment=1)
                record["breakup_state"] = "repairing"
                for key in ("breakup_talk_steps", "relationship_pause_steps", "breakup_decision_steps", "forgiveness_block_steps"):
                    _steps(record,key,0)
                _steps(record,"closeness_steps",max(4,int(record.get("closeness_steps",0) or 0)))
                memory(record, "save_relationship",7)
        else:
            for record in records:
                memory(record, "save_relationship_failed",5)
                if record.get("breakup_state","none")=="none":
                    record["breakup_state"]="talk"
                    _steps(record,"breakup_talk_steps",2)
        return self._finish("save_relationship", success, actor, partner)

    def decide_breakup(self, actor, partner):
        a,b = self._pair(actor, partner)
        for record in (a,b):
            record["breakup_state"]="decided"
            _steps(record,"breakup_decision_steps",8)
            _steps(record,"breakup_talk_steps",0)
            _steps(record,"relationship_pause_steps",0)
            memory(record,"breakup_decision",8)
        # Vanilla Sims 4 breakup is a separate action, not executed here.
        return self._finish("decide_breakup",True,actor,partner)


def bind_action_runners(registry, actions):
    """Register all ten pure gameplay runners into the canonical registry."""
    for name in (
        "discuss","apologize","admit_fault","forgive","not_ready",
        "second_chance","breakup_talk","take_pause",
        "save_relationship","decide_breakup"
    ):
        registry.register(name, getattr(actions,name))
    return registry

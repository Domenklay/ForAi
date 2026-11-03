# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.9 — stage delivery hotfix.

The v0.7.8 stage calculation itself is correct, but the older moodlet engine can
choose a different "dominant" relationship before calling _desired_for_record.
That can hide an explicit player-driven stage such as Relationship Pause.

v0.7.9 makes visible story stages authoritative at Sim level: after the legacy
moodlet calculation, inspect every tracked directional relationship owned by the
Sim, choose the most relevant current stage, remove all other stage Buffs, and
add exactly that dedicated stage Buff.  Explicit active-pair stages outrank old
former/ex relationships.
"""

import traceback

import deep_relationships as base
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzzzzzz_deep_relationships_breakup_v070 as breakup
import zzzzzzzzzzzzzzzzzz_deep_relationships_v078 as stages

VERSION = '0.7.9'
base.VERSION = VERSION
moodlets.VERSION = VERSION

# Higher value wins if a Sim has several tracked relationships.  Acute stages
# in a current relationship beat historical ex status.
_STAGE_PRIORITY = {
    'breakup': 100,
    'pause': 95,
    'refused_forgive': 90,
    'second_chance': 88,
    'recovery': 85,
    'infidelity': 80,
    'deep_conflict': 75,
    'argument': 70,
    'reconciliation': 60,
    'exes': 20,
}


def _source_records(sim_id):
    result = []
    try:
        for record in tuple(base.slot_state().values()):
            if not isinstance(record, dict):
                continue
            try:
                if int(record.get('source_id', 0) or 0) != int(sim_id):
                    continue
            except Exception:
                continue
            result.append(record)
    except Exception:
        pass
    return result


def _best_stage_for_sim(sim_info):
    if sim_info is None:
        return None, None
    try:
        sim_id = int(sim_info.sim_id)
    except Exception:
        return None, None

    candidates = []
    for record in _source_records(sim_id):
        try:
            stage = stages.relationship_stage(record)
        except Exception:
            continue
        if not stage:
            continue

        priority = int(_STAGE_PRIORITY.get(stage, 0))
        # A currently active/pause/repairing relationship should always beat an
        # old former/ex record when priorities otherwise happen to be close.
        try:
            breakup_state = str(record.get('breakup_state', 'none') or 'none')
            phase = str(record.get('relationship_phase', 'active') or 'active')
            if breakup_state in ('pause', 'repairing', 'talk', 'decided'):
                priority += 30
            elif phase == 'active' and stage != 'exes':
                priority += 20
        except Exception:
            pass

        candidates.append((priority, stage, record))

    if not candidates:
        return None, None
    candidates.sort(key=lambda row: row[0], reverse=True)
    _, stage, record = candidates[0]
    return stage, record


_PREVIOUS_DESIRED_MOODLETS = moodlets._desired_moodlets


def _desired_moodlets_v079(sim_info):
    desired = set(_PREVIOUS_DESIRED_MOODLETS(sim_info))

    # Remove all story-stage presentations chosen by older dominant-record
    # logic, then add the authoritative Sim-level stage below.
    desired.difference_update(stages.OLD_STAGE_BUFFS)

    stage, record = _best_stage_for_sim(sim_info)
    if stage is None:
        return desired

    buff_id = stages.STAGE_TO_BUFF.get(stage)
    if buff_id is not None:
        desired.add(buff_id)

    # Any explicit story stage is incompatible with generic Happy Relationship.
    desired.discard(moodlets.BUFF_HAPPY_RELATIONSHIP)

    # Jealousy is still supplementary only to real infidelity in the selected
    # directional relationship.
    if stage != 'infidelity':
        try:
            if stages._grievance(record, 'infidelity') < 1.0:
                desired.discard(moodlets.BUFF_JEALOUSY)
        except Exception:
            desired.discard(moodlets.BUFF_JEALOUSY)

    return desired


moodlets._desired_moodlets = _desired_moodlets_v079


# ---------------------------------------------------------------------------
# Immediate force-refresh after player-driven stage actions.
# ---------------------------------------------------------------------------
def _sync_pair_now(actor, target, action_name='stage_action'):
    try:
        actor_record, target_record = reconciliation._records(actor, target, create=False)
        reconciliation._sync_records(actor_record, target_record)

        # Log the exact stage after the action so a future test immediately
        # distinguishes state-detection from Buff-registration problems.
        manager = base.services.sim_info_manager()
        for obj in (actor, target):
            sim_info = getattr(obj, 'sim_info', obj)
            if sim_info is None:
                continue
            stage, record = _best_stage_for_sim(sim_info)
            buff_id = stages.STAGE_TO_BUFF.get(stage)
            buff_type = moodlets._buff_manager().get(buff_id) if buff_id is not None and moodlets._buff_manager() is not None else None
            base.flog('V079 STAGE REFRESH {}: sim {} stage {} buff {} registered {}'.format(
                action_name,
                getattr(sim_info, 'sim_id', '?'),
                stage,
                buff_id,
                bool(buff_type is not None),
            ))
    except Exception:
        base.flog('V079 IMMEDIATE STAGE REFRESH FAILED: {}'.format(action_name))
        base.flog(traceback.format_exc())


def _wrap_runner(action_name, runner):
    def wrapped(actor, target):
        result = runner(actor, target)
        try:
            _sync_pair_now(actor, target, action_name)
        except Exception:
            pass
        return result
    return wrapped


try:
    # Wrap the final ACTION_RUNNERS table, which is what the custom interactions
    # resolve dynamically at execution time.
    for _action in ('breakup_talk', 'take_pause', 'save_relationship', 'decide_breakup'):
        _runner = breakup.ACTION_RUNNERS.get(_action)
        if _runner is not None and not getattr(_runner, '_deeprel_v079_stage_refresh', False):
            _wrapped = _wrap_runner(_action, _runner)
            _wrapped._deeprel_v079_stage_refresh = True
            breakup.ACTION_RUNNERS[_action] = _wrapped
except Exception:
    base.flog('V079 BREAKUP RUNNER PATCH FAILED')
    base.flog(traceback.format_exc())


# On zone load, refresh with the new Sim-level selection immediately.
_PREVIOUS_INIT = base.initialize_zone


def _initialize_zone_v079():
    result = _PREVIOUS_INIT()
    try:
        moodlets.sync_household_moodlets()
        manager = moodlets._buff_manager()
        missing = []
        if manager is not None:
            for stage, buff_id in stages.STAGE_TO_BUFF.items():
                if manager.get(buff_id) is None:
                    missing.append((stage, buff_id))
        if missing:
            base.flog('V079 STAGE BUFF REGISTRATION MISSING: {}'.format(missing))
        else:
            base.flog('V079 STAGE BUFF REGISTRATION OK: 10/10')
    except Exception:
        base.flog('V079 INITIAL STAGE REFRESH FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v079
base.flog('V079 AUTHORITATIVE SIM-LEVEL STAGE DELIVERY INSTALLED')

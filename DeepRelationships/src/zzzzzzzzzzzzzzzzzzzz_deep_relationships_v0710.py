# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.10 — unified delivery for every story-stage moodlet.

v0.7.9 repaired pause when the legacy dominant-relationship algorithm selected
another partner. This layer applies the same immediate delivery to all ten story
stages and all relevant event sources, without changing persistence or Buff IDs.

The stage is still derived by v0.7.8.  This layer does not invent transitions.
"""
import traceback

import deep_relationships as base
import zz_deep_relationships_grievances as grievances
import zzy_deep_relationships_moodlets as moodlets
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzzzzzz_deep_relationships_breakup_v070 as breakup
import zzzzzzzzzzzzzz_deep_relationships_stability_v072 as stability
import zzzzzzzzzzzzzzz_deep_relationships_v073 as buff_cleanup
import zzzzzzzzzzzzzzzzzz_deep_relationships_v078 as stages
import zzzzzzzzzzzzzzzzzzz_deep_relationships_v079 as delivery

VERSION = '0.7.10'
base.VERSION = VERSION
moodlets.VERSION = VERSION

# The last interaction partner is a contextual presentation choice, NOT saved
# relationship data.  Sims with several romances see the most recently changed
# pair, instead of an unrelated partner's more severe old stage.
_FOCUS = {}
_IN_SYNC = set()
_LAST_STAGE_DIAGNOSTIC = {}

_OLD_BEST = delivery._best_stage_for_sim


def _id(obj):
    try:
        return int(getattr(getattr(obj, 'sim_info', obj), 'sim_id', obj))
    except Exception:
        return 0


def _focus_pair(source_id, target_id):
    a, b = _id(source_id), _id(target_id)
    if a and b and a != b:
        _FOCUS[a] = b
        _FOCUS[b] = a
    return a, b


def _best_stage_v0710(sim_info):
    if sim_info is None:
        return None, None
    sim_id = _id(sim_info)
    partner_id = _FOCUS.get(sim_id)
    if partner_id:
        record = None
        for candidate in delivery._source_records(sim_id):
            if _id(candidate.get('target_id', 0)) == partner_id:
                record = candidate
                break
        if record is not None:
            try:
                selected = stages.relationship_stage(record)
                if selected is not None:
                    return selected, record
                # A new healthy active relationship must not be overridden by
                # unrelated long-term "now exes" from a previous partner.
                original_stage, original_record = _OLD_BEST(sim_info)
                if original_stage == 'exes' and (
                    str(record.get('relationship_phase', 'active')) == 'active' and
                    str(record.get('breakup_state', 'none')) != 'ended'
                ):
                    return None, record
            except Exception:
                base.flog('V0710 STAGE EVALUATION FAILED: {}'.format(sim_id))
                base.flog(traceback.format_exc())
    return _OLD_BEST(sim_info)


# v0.7.9 _desired_moodlets resolves this symbol dynamically.
delivery._best_stage_for_sim = _best_stage_v0710


def _present(sim_info, buff_type):
    try:
        return bool(buff_cleanup._present(sim_info, buff_type))
    except Exception:
        try:
            return bool(sim_info.has_buff(buff_type))
        except Exception:
            return False


def _refresh_ids(ids, reason, verbose=False):
    """Exactly one final-stage sync per Sim, with actionable diagnostics."""
    try:
        manager = base.services.sim_info_manager()
        buff_manager = moodlets._buff_manager()
    except Exception:
        return
    if manager is None:
        return
    for sim_id in set(_id(value) for value in ids):
        if not sim_id or sim_id in _IN_SYNC:
            continue
        try:
            sim_info = manager.get(sim_id)
        except Exception:
            sim_info = None
        if sim_info is None:
            continue
        _IN_SYNC.add(sim_id)
        try:
            # Uses v0.7.3 handle-removing synchronizer and v0.7.9's final
            # Sim-level desired-moodlet computation.
            moodlets.sync_sim_moodlets(sim_info)
            stage, record = _best_stage_v0710(sim_info)
            buff_id = stages.STAGE_TO_BUFF.get(stage)
            buff_type = buff_manager.get(buff_id) if buff_id is not None and buff_manager is not None else None
            present = bool(buff_type is not None and _present(sim_info, buff_type))
            registered = bool(buff_type is not None)
            diagnostic = (stage, registered, present, _id(record.get('target_id', 0)) if record else 0)
            # Every player action logs, every automatic step logs only
            # changes/missing Buffs. Avoid flooding deeprel.log each tick.
            if verbose or diagnostic != _LAST_STAGE_DIAGNOSTIC.get(sim_id) or (buff_id and not present):
                base.flog('V0710 STAGE {}: sim {} partner {} stage {} buff {} registered {} present {}'.format(
                    reason, sim_id, diagnostic[3], stage, buff_id, registered, present,
                ))
                _LAST_STAGE_DIAGNOSTIC[sim_id] = diagnostic
        except Exception:
            base.flog('V0710 STAGE REFRESH FAILED: {} sim {}'.format(reason, sim_id))
            base.flog(traceback.format_exc())
        finally:
            _IN_SYNC.discard(sim_id)


def _refresh_pair(actor, target, reason, verbose=True):
    a, b = _focus_pair(actor, target)
    _refresh_ids((a, b), reason, verbose=verbose)


def _wrap_action_table(table, action_names, prefix):
    for action in action_names:
        previous = table.get(action)
        if previous is None or getattr(previous, '_deeprel_v0710', False):
            continue

        def wrapper(actor, target, _previous=previous, _action=action):
            result = _previous(actor, target)
            # False means interaction rejected before running.  A failed roll
            # can still mutate refusal/cooldown state and returns True.
            if result is not False:
                _refresh_pair(actor, target, prefix + '.' + _action)
            return result

        wrapper._deeprel_v0710 = True
        table[action] = wrapper


# Covers ALL player-driven events, not only the four breakup actions in v0.7.9.
_wrap_action_table(reconciliation.ACTION_RUNNERS, (
    'discuss', 'apologize', 'admit_fault',
    'forgive', 'not_ready', 'second_chance',
), 'reconciliation')
_wrap_action_table(breakup.ACTION_RUNNERS, (
    'breakup_talk', 'take_pause', 'save_relationship', 'decide_breakup',
), 'breakup')


# Ordinary social events: fight, positive reconciliation, deep conflict.
_OLD_DELTA = base.on_relationship_delta


def _on_relationship_delta_v0710(source_id, target_id, supplied_delta, kind):
    result = _OLD_DELTA(source_id, target_id, supplied_delta, kind)
    try:
        _refresh_pair(source_id, target_id, 'relationship_delta', verbose=False)
    except Exception:
        base.flog('V0710 RELATIONSHIP DELTA STAGE FAILED')
        base.flog(traceback.format_exc())
    return result


base.on_relationship_delta = _on_relationship_delta_v0710


# Betrayal, grievances and resentment changes can be produced without a
# RelationshipService score delta.  Both participants need immediate refresh.
_OLD_ADD_GRIEVANCE = grievances.add_grievance


def _add_grievance_v0710(record, reason, amount, count_event=True):
    result = _OLD_ADD_GRIEVANCE(record, reason, amount, count_event=count_event)
    try:
        if record is not None:
            source = record.get('source_id', 0)
            target = record.get('target_id', 0)
            _refresh_pair(source, target, 'grievance.' + str(reason), verbose=False)
    except Exception:
        base.flog('V0710 GRIEVANCE STAGE FAILED')
        base.flog(traceback.format_exc())
    return result


grievances.add_grievance = _add_grievance_v0710


# A real vanilla Break Up / Divorce relationship bit is observed by v0.7.2,
# whose observer resolves _mark_breakup_pair from its module at call time.
_OLD_MARK_BREAKUP_PAIR = stability._mark_breakup_pair


def _mark_breakup_pair_v0710(source_id, target_id, notify=True):
    result = _OLD_MARK_BREAKUP_PAIR(source_id, target_id, notify=notify)
    if result:
        _refresh_pair(source_id, target_id, 'official_breakup')
    return result


stability._mark_breakup_pair = _mark_breakup_pair_v0710


# The six-hour maintenance cycle decreases post_breakup_steps,
# relationship_pause_steps, second_chance_steps and forgiveness_block_steps.
# Refresh once afterwards so the automatic stages are visible immediately.
_OLD_DECAY = base.decay_tick


def _decay_tick_v0710():
    result = _OLD_DECAY()
    try:
        for sim_info in base.sims_in_household(base.household()):
            _refresh_ids((_id(sim_info),), 'stage_progress', verbose=False)
    except Exception:
        base.flog('V0710 STAGE TICK FAILED')
        base.flog(traceback.format_exc())
    return result


base.decay_tick = _decay_tick_v0710


_OLD_INIT = base.initialize_zone


def _initialize_zone_v0710():
    # Focus is transient: never leak a previous zone's selected partner into
    # freshly loaded save state.
    _FOCUS.clear()
    _LAST_STAGE_DIAGNOSTIC.clear()
    result = _OLD_INIT()
    try:
        manager = moodlets._buff_manager()
        missing = []
        for label, buff_id in stages.STAGE_TO_BUFF.items():
            if manager is None or manager.get(buff_id) is None:
                missing.append((label, buff_id))
        if missing:
            base.flog('V0710 STAGE BUFF REGISTRATION MISSING: {}'.format(missing))
        else:
            base.flog('V0710 STAGE BUFF REGISTRATION OK: 10/10')
        for sim_info in base.sims_in_household(base.household()):
            _refresh_ids((_id(sim_info),), 'zone_load', verbose=True)
    except Exception:
        base.flog('V0710 STAGE INITIALIZATION FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v0710
base.flog('V0710 ALL TEN STAGE MOODLET DELIVERY INSTALLED')

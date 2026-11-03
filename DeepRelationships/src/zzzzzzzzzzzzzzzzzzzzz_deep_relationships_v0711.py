# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.11 — final stage selection and reunion stability.

Single visible stage per Sim, deterministic across zone loads, and an isolated
history of ex partners. Does not change the saved-file schema or existing Buff
resource IDs. All 10 stage Buff icons and texts remain in the package.
"""

import traceback

import deep_relationships as base
import zzy_deep_relationships_moodlets as moodlets
import zzzzz_deep_relationships_core_v046 as core
import zzzzzz_deep_relationships_reconciliation_v050 as reconciliation
import zzzzzzzzzzzzzz_deep_relationships_stability_v072 as stability
import zzzzzzzzzzzzzzzzzz_deep_relationships_v078 as stages
import zzzzzzzzzzzzzzzzzzz_deep_relationships_v079 as delivery
import zzzzzzzzzzzzzzzzzzzzz_deep_relationships_v0710 as delivery_all

VERSION = '0.7.11'
base.VERSION = VERSION
moodlets.VERSION = VERSION

# Exact one-primary-stage semantics: specific decisions precede generic hurts.
# Ties are deterministic by partner Sim ID, not by order of random events.
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


def _id(value):
    try:
        return int(getattr(getattr(value, 'sim_info', value), 'sim_id', value))
    except Exception:
        return 0


def _active_record(record):
    if not isinstance(record, dict):
        return False
    return (
        str(record.get('relationship_phase', 'active') or 'active') != 'former' and
        str(record.get('breakup_state', 'none') or 'none') != 'ended'
    )


def _best_stage_stable(sim_info):
    """Pick a stage by real relationship state, not last conversation target.

    A happy new active romantic pair takes precedence over stale "Now Exes"
    statuses from former partners; former history remains queryable per pair.
    """
    sim_id = _id(sim_info)
    if not sim_id:
        return None, None

    records = delivery._source_records(sim_id)
    active = [r for r in records if _active_record(r)]
    candidates = active if active else records
    ranked = []
    for record in candidates:
        try:
            stage = stages.relationship_stage(record)
        except Exception:
            base.flog('V0711 STAGE EVALUATION FAILED: {}'.format(sim_id))
            base.flog(traceback.format_exc())
            continue
        if not stage:
            continue
        # Active pair wins on equal stages; partner ID provides a stable
        # tie-breaker across restarts and transitions.
        priority = _STAGE_PRIORITY.get(stage, 0)
        if not priority:
            continue
        partner_id = _id(record.get('target_id', 0))
        ranked.append((priority, 1 if _active_record(record) else 0,
                       -partner_id, stage, record))

    if ranked:
        chosen = max(ranked, key=lambda item: item[:3])
        return chosen[3], chosen[4]

    # If the Sim has a healthy current relationship, do not display an
    # unrelated ex-stage even if the old history is still tracked.
    if active:
        return None, active[0]
    return None, None


# v0.7.9's final desired-moodlets function looks up this function dynamically.
# v0.7.10's diagnostic does the same through its own module-global symbol.
delivery._best_stage_for_sim = _best_stage_stable
delivery_all._best_stage_v0710 = _best_stage_stable


# v0.7.10 used to change selected pair on every social score delta. Keep its
# refresh pipeline, but never mutate focus: mundane social interactions should
# not replace a paused pair with an unrelated argument.
def _no_focus_pair(source_id, target_id):
    return _id(source_id), _id(target_id)


delivery_all._FOCUS.clear()
delivery_all._focus_pair = _no_focus_pair


# Older dominant-record and "ANY tracked relationship" safety checks included
# former partners. Filter only the moodlet presentation, not historical storage
# or the per-pair relationship report.
_OLD_RECORDS_FOR_SIM = moodlets._records_for_sim


def _records_for_current_moodlets(sim_info):
    records = tuple(_OLD_RECORDS_FOR_SIM(sim_info))
    active = tuple(r for r in records if _active_record(r))
    return active if active else records


moodlets._records_for_sim = _records_for_current_moodlets


# Restore the active relationship after an actually ACCEPTED second chance,
# even when vanilla has an old Ex relationship bit.  On a NEW breakup the
# authoritative vanilla bit observer resets this explicit reunion flag.
_OLD_REFRESH_PHASE = core._refresh_phase


def _refresh_phase_v0711(record):
    if record is None:
        return _OLD_REFRESH_PHASE(record)
    try:
        second_chance_confirmed = (
            str(record.get('reconciliation_stage', '') or '') == 'second_chance' and
            int(record.get('second_chance_steps', 0) or 0) > 0
        )
        if second_chance_confirmed and str(record.get('breakup_state', 'none')) == 'ended':
            record['reunion_accepted'] = True
            record['breakup_state'] = 'repairing'
            base.DIRTY = True
        if record.get('reunion_accepted') and str(record.get('breakup_state', 'none')) != 'ended':
            if record.get('relationship_phase') != 'active':
                record['relationship_phase'] = 'active'
                base.DIRTY = True
            return None
    except Exception:
        base.flog('V0711 REUNION PHASE CHECK FAILED')
        base.flog(traceback.format_exc())
    return _OLD_REFRESH_PHASE(record)


core._refresh_phase = _refresh_phase_v0711


_OLD_SECOND_CHANCE_RUNNER = reconciliation.ACTION_RUNNERS.get('second_chance')


def _second_chance_v0711(actor, target):
    result = _OLD_SECOND_CHANCE_RUNNER(actor, target) if _OLD_SECOND_CHANCE_RUNNER else False
    if result:
        try:
            actor_record, target_record = reconciliation._records(actor, target, create=False)
            accepted = any(
                record is not None and
                str(record.get('reconciliation_stage', '') or '') == 'second_chance' and
                int(record.get('second_chance_steps', 0) or 0) > 0
                for record in (actor_record, target_record)
            )
            if accepted:
                for record in (actor_record, target_record):
                    if record is None:
                        continue
                    record['reunion_accepted'] = True
                    if str(record.get('breakup_state', 'none') or 'none') == 'ended':
                        record['breakup_state'] = 'repairing'
                    record['relationship_phase'] = 'active'
                    base.DIRTY = True
                delivery_all._refresh_pair(actor, target, 'second_chance_accepted')
        except Exception:
            base.flog('V0711 SECOND CHANCE REUNION FAILED')
            base.flog(traceback.format_exc())
    return result


if _OLD_SECOND_CHANCE_RUNNER is not None:
    reconciliation.ACTION_RUNNERS['second_chance'] = _second_chance_v0711


# A new actual vanilla breakup overrides any historical reunion.
_OLD_MARK_BREAKUP_PAIR = stability._mark_breakup_pair


def _mark_breakup_pair_v0711(source_id, target_id, notify=True):
    # Loading historical vanilla Ex bits must not cancel a genuine reunion.
    # New, player-driven Break Up / Divorce events pass notify=True.
    if not notify:
        try:
            saved = [core._existing_record(_id(a), _id(b))
                     for a, b in ((source_id, target_id), (target_id, source_id))]
            if any(record is not None and record.get('reunion_accepted')
                   and str(record.get('breakup_state', 'none')) != 'ended'
                   for record in saved):
                return False
        except Exception:
            pass
    for a, b in ((source_id, target_id), (target_id, source_id)):
        try:
            record = core._existing_record(_id(a), _id(b))
            if record is not None:
                record['reunion_accepted'] = False
                record['reconciliation_stage'] = ''
                base.DIRTY = True
        except Exception:
            pass
    return _OLD_MARK_BREAKUP_PAIR(source_id, target_id, notify=notify)


stability._mark_breakup_pair = _mark_breakup_pair_v0711


# v0.7.10 already handles all player interactions, relationship deltas,
# grievances, official breakups and six-hour ticks.  This final layer changes
# only the state selector and restores historical relationship isolation.
_OLD_INIT = base.initialize_zone


def _initialize_zone_v0711():
    result = _OLD_INIT()
    try:
        manager = moodlets._buff_manager()
        missing = []
        for stage, buff_id in stages.STAGE_TO_BUFF.items():
            if manager is None or manager.get(buff_id) is None:
                missing.append((stage, buff_id))
        if missing:
            base.flog('V0711 STAGE BUFF REGISTRATION MISSING: {}'.format(missing))
        else:
            base.flog('V0711 STAGE BUFF REGISTRATION OK: 10/10')
        moodlets.sync_household_moodlets()
    except Exception:
        base.flog('V0711 STAGE INITIALIZATION FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v0711
base.flog('V0711 STABLE TEN STAGE MOODLETS INSTALLED')

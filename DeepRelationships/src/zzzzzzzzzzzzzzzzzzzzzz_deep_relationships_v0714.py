# -*- coding: utf-8 -*-
"""v0.7.14: independently scheduled stage-moodlet delivery and diagnostics.

Never changes relationship records, save files, or Buff identifiers.
"""
import traceback
import alarms
import date_and_time
from zone import Zone

import deep_relationships as base
import zzy_deep_relationships_moodlets as moodlets
import zzzzzzzzzzzzzzz_deep_relationships_v073 as cleanup
import zzzzzzzzzzzzzzzzzzz_deep_relationships_v079 as delivery
import zzzzzzzzzzzzzzzzzzzzz_deep_relationships_v0711 as stable
import zzzzzzzzzzzzzzzzzz_deep_relationships_v078 as stages

VERSION = '0.7.14'
base.VERSION = VERSION
moodlets.VERSION = VERSION
_ALARM = None
_OWNER = type('_DeepRelStageAlarmOwner', (), {})()
_LAST = {}
_BUSY = False


def _present(sim_info, buff_type):
    try:
        return bool(cleanup._present(sim_info, buff_type))
    except Exception:
        try:
            return bool(sim_info.has_buff(buff_type))
        except Exception:
            return False


def _apply(sim_info, manager, reason):
    sim_id = getattr(sim_info, 'sim_id', 0)
    try:
        stage, record = stable._best_stage_stable(sim_info)
        buff_id = stages.STAGE_TO_BUFF.get(stage)
        # First run the existing engine for supporting moods (grief, jealousy,
        # instability etc.). It must not decide the final exclusive story stage.
        try:
            moodlets.sync_sim_moodlets(sim_info)
        except Exception:
            base.flog('V0714 LEGACY SYNC FAILED sim {}: {}'.format(sim_id, traceback.format_exc()))
        for candidate in stages.STAGE_BUFFS:
            if candidate == buff_id:
                continue
            buff_type = manager.get(candidate)
            if buff_type is not None and _present(sim_info, buff_type):
                cleanup._remove_all_handles(sim_info, buff_type, candidate)
        registered = bool(buff_id is not None and manager.get(buff_id) is not None)
        if registered:
            buff_type = manager.get(buff_id)
            if not _present(sim_info, buff_type):
                try:
                    handle = sim_info.add_buff(buff_type)
                    base.flog('V0714 ADD sim {} stage {} buff {} handle {}'.format(
                        sim_id, stage, buff_id, bool(handle is not None)))
                except Exception:
                    base.flog('V0714 ADD ERROR sim {} stage {}: {}'.format(
                        sim_id, stage, traceback.format_exc()))
        present = bool(registered and _present(sim_info, manager.get(buff_id)))
        diagnosis = (stage, buff_id, registered, present)
        if _LAST.get(sim_id) != diagnosis or reason == 'zone_load':
            base.flog('V0714 CHECK {} sim {} stage {} buff {} registered {} present {}'.format(
                reason, sim_id, stage, buff_id, registered, present))
            _LAST[sim_id] = diagnosis
    except Exception:
        base.flog('V0714 SIM ERROR {}: {}'.format(sim_id, traceback.format_exc()))


def refresh(reason='tick'):
    global _BUSY
    if _BUSY:
        return
    _BUSY = True
    try:
        manager = moodlets._buff_manager()
        if manager is None:
            base.flog('V0714 BUFF MANAGER MISSING')
            return
        if reason == 'zone_load':
            missing = [(name, buff_id) for name, buff_id in stages.STAGE_TO_BUFF.items()
                       if manager.get(buff_id) is None]
            base.flog('V0714 STAGE REGISTRY {} / {} missing {}'.format(
                len(stages.STAGE_TO_BUFF) - len(missing), len(stages.STAGE_TO_BUFF), missing))
        for sim_info in base.sims_in_household(base.household()):
            _apply(sim_info, manager, reason)
    except Exception:
        base.flog('V0714 REFRESH ERROR: {}'.format(traceback.format_exc()))
    finally:
        _BUSY = False


def _alarm_tick(_):
    refresh('scheduled')


@base.inject_to(Zone, 'on_loading_screen_animation_finished', '_deeprel_v0714_zone_hook')
def _zone_loaded_v0714(original, self, *args, **kwargs):
    global _ALARM
    result = original(self, *args, **kwargs)
    try:
        if _ALARM is not None:
            try:
                alarms.cancel_alarm(_ALARM)
            except Exception:
                pass
            _ALARM = None
        _LAST.clear()
        refresh('zone_load')
        _ALARM = alarms.add_alarm(
            _OWNER,
            date_and_time.create_time_span(minutes=10),
            _alarm_tick,
            repeating=True,
            repeating_time_span=date_and_time.create_time_span(hours=1))
        base.flog('V0714 STAGE MAINTENANCE ALARM STARTED')
    except Exception:
        base.flog('V0714 ZONE HOOK FAILED: {}'.format(traceback.format_exc()))
    return result


base.flog('V0714 INDEPENDENT STAGE DELIVERY HOOK INSTALLED')

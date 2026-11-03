# -*- coding: utf-8 -*-
"""Sims 4 API bridge for clean v0.8 engine. NOT AN INSTALLABLE RELEASE.

Only the main bootstrap may import this module. It does not import legacy
v0.7.x modules, patch save hooks or write sidecar data.
"""
import traceback
import services
import sims4.resources

from engine.coordinator import StageCoordinator
from engine.events import EventDispatcher
from engine.moodlets import STAGE_BUFFS

LOG_PREFIX = "DEEPREL_V08"
_HOOKED = False
_DISPATCHER = None
_DIAGNOSTIC_LOG = None


def _log(message):
    try:
        if _DIAGNOSTIC_LOG is not None:
            _DIAGNOSTIC_LOG("{} {}".format(LOG_PREFIX, message))
    except Exception:
        pass


def _sim_info(sim_id):
    try:
        manager = services.sim_info_manager()
        return manager.get(int(sim_id)) if manager is not None else None
    except Exception:
        _log("SIM LOOKUP ERROR {}".format(traceback.format_exc()))
        return None


def _buff_manager():
    return services.get_instance_manager(sims4.resources.Types.BUFF)


def _present_buff_ids(sim_id):
    sim_info = _sim_info(sim_id)
    manager = _buff_manager()
    if sim_info is None or manager is None:
        return ()
    result = set()
    for buff_id in STAGE_BUFFS:
        buff_type = manager.get(buff_id)
        if buff_type is None:
            continue
        try:
            if sim_info.has_buff(buff_type):
                result.add(buff_id)
        except Exception:
            _log("BUFF LOOKUP ERROR {} {}".format(sim_id, buff_id))
    return result


def _buffs_component(sim_info):
    # TS4 SimInfo exposes the plural 'buffs_component'. The previous code
    # used remove_buff_by_type, which does not always clear commodity-backed
    # Buff handle instances.
    for name in ("buffs_component", "buff_component"):
        try:
            found = getattr(sim_info, name, None)
            if found is not None:
                return found
        except Exception:
            pass
    try:
        from objects.components.types import BUFF_COMPONENT
        getter = getattr(sim_info, "get_component", None)
        if getter is not None:
            return getter(BUFF_COMPONENT)
    except Exception:
        pass
    return None


def _active_buff_entry(component, buff_type):
    active = getattr(component, "_active_buffs", None)
    if isinstance(active, dict):
        return active.get(buff_type)
    return None


def _remove_buff(sim_id, buff_id):
    sim_info = _sim_info(sim_id)
    manager = _buff_manager()
    buff_type = manager.get(buff_id) if manager is not None else None
    if sim_info is None or buff_type is None:
        _log("BUFF REMOVE NOT AVAILABLE sim {} buff {}".format(sim_id, buff_id))
        return

    component = _buffs_component(sim_info)
    removed_handles = 0
    if component is not None:
        # Multiple independent reasons can hold the same buff. Remove every
        # handle, but never touch Buffs unrelated to this mod.
        for attempt in range(4):
            entry = _active_buff_entry(component, buff_type)
            if entry is None:
                break
            handles = tuple(getattr(entry, "handle_ids", ()) or ())
            if not handles:
                break
            for handle in handles:
                try:
                    component.remove_buff(handle, update_mood=True, immediate=True)
                    removed_handles += 1
                except TypeError:
                    try:
                        component.remove_buff(handle, update_mood=True)
                        removed_handles += 1
                    except Exception:
                        _log("BUFF HANDLE REMOVE ERROR sim {} buff {} {}".format(
                            sim_id, buff_id, traceback.format_exc()))
                except Exception:
                    _log("BUFF HANDLE REMOVE ERROR sim {} buff {} {}".format(
                        sim_id, buff_id, traceback.format_exc()))

    # Some ordinary Buffs have no active handles; type removal is a fallback.
    try:
        if sim_info.has_buff(buff_type):
            sim_info.remove_buff_by_type(buff_type)
    except Exception:
        _log("BUFF TYPE REMOVE ERROR sim {} buff {} {}".format(
            sim_id, buff_id, traceback.format_exc()))

    try:
        still_present = bool(sim_info.has_buff(buff_type))
    except Exception:
        still_present = _active_buff_entry(component, buff_type) is not None if component is not None else False
    if still_present:
        entry = _active_buff_entry(component, buff_type) if component is not None else None
        handles = tuple(getattr(entry, "handle_ids", ()) or ()) if entry is not None else ()
        _log("BUFF REMOVE FAILED sim {} buff {} handles {} component {}".format(
            sim_id, buff_id, handles, bool(component is not None)))
    elif removed_handles:
        _log("BUFF REMOVED BY HANDLES sim {} buff {} handles {}".format(
            sim_id, buff_id, removed_handles))


def _add_buff(sim_id, buff_id):
    sim_info = _sim_info(sim_id)
    manager = _buff_manager()
    buff_type = manager.get(buff_id) if manager is not None else None
    if sim_info is None or buff_type is None:
        _log("BUFF ADD NOT AVAILABLE sim {} buff {}".format(sim_id, buff_id))
        return
    sim_info.add_buff(buff_type)


def _household_ids():
    hh = services.active_household()
    if hh is None:
        return ()
    return tuple(s.sim_id for s in hh.sim_info_gen() if s is not None)


def install(record_reader, diagnostic_logger):
    """Explicit dependency injection; no automatic monkeypatch at import."""
    global _DISPATCHER, _DIAGNOSTIC_LOG
    _DIAGNOSTIC_LOG = diagnostic_logger
    coordinator = StageCoordinator(
        record_reader, _present_buff_ids, _remove_buff, _add_buff, _log
    )
    _DISPATCHER = EventDispatcher(coordinator, _log)
    _log("BRIDGE INITIALIZED")
    return _DISPATCHER


def on_zone_ready():
    if _DISPATCHER is None:
        _log("ZONE IGNORED: BRIDGE NOT INITIALIZED")
        return False
    try:
        manager = _buff_manager()
        missing = [v for v in sorted(STAGE_BUFFS)
                   if manager is None or manager.get(v) is None]
        _log("STAGE BUFF REGISTRATION {}/10 missing {}".format(10-len(missing), missing))
        return _DISPATCHER.household_loaded(_household_ids())
    except Exception:
        _log("ZONE ERROR {}".format(traceback.format_exc()))
        return False


def on_relationship_changed(source_id, target_id, kind="delta"):
    if _DISPATCHER is None:
        return False
    return _DISPATCHER.pair_changed(source_id, target_id, kind)

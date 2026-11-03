# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.3 — temporary Buff removal hotfix.

v0.7.2 correctly identified that our temporary commodity-backed moodlets need
handle-based removal, but looked for SimInfo.buff_component. The actual Sims 4
component name is SimInfo.buffs_component (component type name "Buffs").
Because of that typo, the handle list was never reached and the code fell back
to remove_buff_by_type(), reproducing the stale Happy Relationship buff.

This layer replaces the moodlet synchronizer with one that resolves the real
BuffComponent and removes every active handle directly.
"""

import traceback

import deep_relationships as base
import zzy_deep_relationships_moodlets as moodlets
import zzzzzzzzzzzzzzz_deep_relationships_stability_v072 as stability

VERSION = '0.7.3'
base.VERSION = VERSION
moodlets.VERSION = VERSION


def _real_buff_component(sim_info):
    if sim_info is None:
        return None
    # Sims 4 component type BUFF_COMPONENT is exposed on SimInfo as
    # ``buffs_component`` (plural), not ``buff_component``.
    for attr in ('buffs_component', 'buff_component'):
        try:
            component = getattr(sim_info, attr, None)
            if component is not None:
                return component
        except Exception:
            pass
    try:
        # Fallback for builds where component attributes are not directly
        # exposed. Avoid importing component types unless necessary.
        import objects.components.types as component_types
        getter = getattr(sim_info, 'get_component', None)
        if getter is not None:
            return getter(component_types.BUFF_COMPONENT)
    except Exception:
        pass
    return None


def _active_entry(sim_info, buff_type):
    component = _real_buff_component(sim_info)
    if component is None:
        return None
    try:
        active = getattr(component, '_active_buffs', None)
        if isinstance(active, dict):
            return active.get(buff_type)
    except Exception:
        pass
    return None


def _present(sim_info, buff_type):
    try:
        entry = _active_entry(sim_info, buff_type)
        if entry is not None:
            return True
    except Exception:
        pass
    try:
        return bool(sim_info.has_buff(buff_type))
    except Exception:
        return False


def _remove_all_handles(sim_info, buff_type, buff_id):
    component = _real_buff_component(sim_info)
    if component is None:
        base.flog('V073 BUFF COMPONENT MISSING: sim {} buff {}'.format(
            getattr(sim_info, 'sim_id', '?'), buff_id
        ))
        return False

    removed_any = False
    # Re-read the entry after every pass because removing the last handle deletes
    # the entry from _active_buffs.
    for _ in range(3):
        entry = _active_entry(sim_info, buff_type)
        if entry is None:
            break
        try:
            handles = tuple(getattr(entry, 'handle_ids', ()) or ())
        except Exception:
            handles = ()
        if not handles:
            break
        for handle in handles:
            try:
                component.remove_buff(handle, update_mood=True, immediate=True)
                removed_any = True
            except TypeError:
                try:
                    component.remove_buff(handle, update_mood=True)
                    removed_any = True
                except Exception:
                    pass
            except Exception:
                pass

    # Only use remove-by-type as a final fallback for any ordinary Buff type.
    if _present(sim_info, buff_type):
        try:
            sim_info.remove_buff_by_type(buff_type)
        except Exception:
            pass

    still_present = _present(sim_info, buff_type)
    if still_present:
        try:
            entry = _active_entry(sim_info, buff_type)
            handles = tuple(getattr(entry, 'handle_ids', ()) or ()) if entry is not None else ()
            base.flog('V073 BUFF STILL PRESENT: sim {} buff {} handles {}'.format(
                getattr(sim_info, 'sim_id', '?'), buff_id, handles
            ))
        except Exception:
            pass
        return False

    if removed_any:
        base.flog('V073 MOODLET REMOVED BY REAL COMPONENT: sim {} buff {}'.format(
            getattr(sim_info, 'sim_id', '?'), buff_id
        ))
    return removed_any


def _sync_sim_moodlets_v073(sim_info):
    if sim_info is None:
        return False
    manager = moodlets._buff_manager()
    if manager is None:
        base.flog('V073 MOODLET BUFF MANAGER MISSING')
        return False

    try:
        desired = set(moodlets._desired_moodlets(sim_info))
    except Exception:
        base.flog('V073 DESIRED MOODLETS FAILED')
        base.flog(traceback.format_exc())
        return False

    changed = False

    # Purge undesired statuses before adding any new ones. This is important for
    # mutually exclusive presentation such as Happy Relationship vs conflict.
    for buff_id in moodlets.ALL_BUFFS:
        if buff_id in desired:
            continue
        try:
            buff_type = manager.get(buff_id)
            if buff_type is None:
                continue
            if _present(sim_info, buff_type):
                if _remove_all_handles(sim_info, buff_type, buff_id):
                    changed = True
        except Exception:
            base.flog('V073 MOODLET PURGE FAILED: {}'.format(buff_id))
            base.flog(traceback.format_exc())

    for buff_id in desired:
        if buff_id not in moodlets.ALL_BUFFS:
            continue
        try:
            buff_type = manager.get(buff_id)
            if buff_type is None:
                continue
            if not _present(sim_info, buff_type):
                handle = sim_info.add_buff(buff_type)
                if handle is not None:
                    changed = True
                    base.flog('V073 MOODLET ADDED: sim {} buff {}'.format(
                        getattr(sim_info, 'sim_id', '?'), buff_id
                    ))
        except Exception:
            base.flog('V073 MOODLET ADD FAILED: {}'.format(buff_id))
            base.flog(traceback.format_exc())

    return changed


moodlets.sync_sim_moodlets = _sync_sim_moodlets_v073


def _sync_household_v073():
    changed = 0
    try:
        for sim_info in base.sims_in_household(base.household()):
            if moodlets.sync_sim_moodlets(sim_info):
                changed += 1
    except Exception:
        base.flog('V073 HOUSEHOLD MOODLET SYNC FAILED')
        base.flog(traceback.format_exc())
    return changed


moodlets.sync_household_moodlets = _sync_household_v073


# Ensure every pair refresh path installed by v0.7.2 resolves to the new
# synchronizer dynamically.
stability._buff_component = _real_buff_component
stability._active_buff_entry = _active_entry
stability._is_buff_present = _present
stability._remove_buff_by_handles = _remove_all_handles


_PREVIOUS_INIT = base.initialize_zone


def _initialize_zone_v073():
    result = _PREVIOUS_INIT()
    try:
        # Immediately clean stale v0.7.2 moodlets on the first loaded lot.
        moodlets.sync_household_moodlets()
        base.flog('V073 REAL BUFF COMPONENT CLEANUP READY')
    except Exception:
        base.flog('V073 INITIAL CLEANUP FAILED')
        base.flog(traceback.format_exc())
    return result


base.initialize_zone = _initialize_zone_v073
base.flog('V073 TEMPORARY BUFF REMOVAL HOTFIX INSTALLED')

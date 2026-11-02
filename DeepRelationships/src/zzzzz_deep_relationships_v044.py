# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.4 — strict save semantics hotfix.

Fixes two issues left in v0.4.3:
1) The sidecar state was committed before the vanilla save generator finished.
2) Reloading the same save in the same application process was not detected in
   every case, so unsaved in-memory state could leak into the next load.

This layer disables the v0.4.3 pre-save writer and commits only AFTER the
vanilla save generator returns successfully.
"""

import json
import os
import traceback

from services.persistence_service import PersistenceService

import deep_relationships as base
import zzzz_deep_relationships_persistence as persistence_v043

VERSION = '0.4.4'
base.VERSION = VERSION

try:
    import zzy_deep_relationships_moodlets as moodlets
    moodlets.VERSION = VERSION
except Exception:
    moodlets = None


# ---------------------------------------------------------------------------
# Disable every v0.4.3 route that can write before the vanilla save completes.
# ---------------------------------------------------------------------------

def _never_write_before_save(force=False):
    try:
        base.flog('V044: premature state write blocked')
    except Exception:
        pass
    return False


base.save_state = _never_write_before_save
try:
    persistence_v043._REAL_SAVE_STATE = _never_write_before_save
except Exception:
    pass


def _write_committed_state():
    """Write the current in-memory snapshot atomically to the sidecar file."""
    try:
        base._ensure_data_dir()
        temp = base.STATE_PATH + '.tmp'
        with open(temp, 'w', encoding='utf-8') as handle:
            json.dump(base.STATE, handle, ensure_ascii=False, indent=2, sort_keys=True)
        try:
            os.replace(temp, base.STATE_PATH)
        except AttributeError:
            if os.path.isfile(base.STATE_PATH):
                os.remove(base.STATE_PATH)
            os.rename(temp, base.STATE_PATH)
        base.DIRTY = False
        base.flog('V044: COMMITTED STATE WRITTEN AFTER VANILLA SAVE')
        return True
    except Exception:
        base.flog('V044: COMMITTED STATE WRITE FAILED')
        base.flog(traceback.format_exc())
        return False


def _reload_committed_state(reason):
    try:
        base.STATE = {'version': 3, 'slots': {}}
        base.STATE_LOADED = False
        base.DIRTY = False
        base.load_state()
        base.flog('V044: COMMITTED STATE RELOADED: {}'.format(reason))
        return True
    except Exception:
        base.flog('V044: COMMITTED STATE RELOAD FAILED: {}'.format(reason))
        base.flog(traceback.format_exc())
        return False


# ---------------------------------------------------------------------------
# Detect a genuinely new loaded play session more robustly than client alone.
# Traveling between lots normally preserves these managers/objects, while
# Main Menu -> Load reconstructs at least one of them.
# ---------------------------------------------------------------------------
_LAST_CONTEXT_TOKEN = None


def _context_token():
    try:
        c = base.client()
    except Exception:
        c = None
    try:
        hh = base.household()
    except Exception:
        hh = None
    try:
        sim_manager = base.services.sim_info_manager()
    except Exception:
        sim_manager = None
    try:
        slot = base.slot_id()
    except Exception:
        slot = '0'
    return (
        slot,
        id(c) if c is not None else None,
        id(hh) if hh is not None else None,
        id(sim_manager) if sim_manager is not None else None,
    )


_ORIGINAL_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_v044():
    global _LAST_CONTEXT_TOKEN
    token = _context_token()
    try:
        if _LAST_CONTEXT_TOKEN is not None and token != _LAST_CONTEXT_TOKEN:
            old_slot = _LAST_CONTEXT_TOKEN[0]
            new_slot = token[0]
            # Slot change is definitely another save. For same-slot reloads,
            # a reconstructed client/household/sim manager marks a new session.
            if new_slot != old_slot:
                _reload_committed_state('slot changed {} -> {}'.format(old_slot, new_slot))
            else:
                old_objects = _LAST_CONTEXT_TOKEN[1:]
                new_objects = token[1:]
                if old_objects != new_objects:
                    _reload_committed_state('same slot reloaded; context rebuilt')
        _LAST_CONTEXT_TOKEN = token
    except Exception:
        base.flog('V044: SESSION DETECTION FAILED')
        base.flog(traceback.format_exc())
    return _ORIGINAL_INITIALIZE_ZONE()


base.initialize_zone = _initialize_zone_v044


# ---------------------------------------------------------------------------
# Commit only after the vanilla save generator actually completes.
# If the generator raises/cancels/never runs, this code never writes the file.
# ---------------------------------------------------------------------------
@base.inject_to(PersistenceService, 'save_game_gen', '_deeprel_v044_save_wrapped')
def _commit_only_after_successful_save(original, self, timeline, save_game_data,
                                       send_save_message=True, check_cooldown=False):
    try:
        # Prepare the memory snapshot, but DO NOT touch disk yet.
        base.scan_active_household()
    except Exception:
        base.flog('V044: PRE-SAVE SCAN FAILED')
        base.flog(traceback.format_exc())

    result = yield from original(
        self,
        timeline,
        save_game_data,
        send_save_message=send_save_message,
        check_cooldown=check_cooldown
    )

    # Some game paths may explicitly return False when no save was performed.
    # Treat only an explicit False as failure; normal generator completion is
    # commonly None.
    if result is False:
        base.flog('V044: VANILLA SAVE RETURNED FALSE; SIDECAR NOT COMMITTED')
        return result

    _write_committed_state()
    return result


base.flog('SAVE SEMANTICS INSTALLED v{}: commit strictly after vanilla save'.format(VERSION))

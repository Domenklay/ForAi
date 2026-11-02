# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.5 — save/load semantics tied to real TS4 save lifecycle.

Gameplay changes remain in memory. The sidecar JSON is reloaded whenever TS4
actually loads a save (GameServiceManager.on_all_households_and_sim_infos_loaded)
and is written only after a successful manual game save completes.
"""

import json
import os
import traceback

from game_services import GameServiceManager
from services.persistence_service import PersistenceService

import deep_relationships as base

VERSION = '0.4.5'
base.VERSION = VERSION

try:
    import zzy_deep_relationships_moodlets as moodlets
    moodlets.VERSION = VERSION
except Exception:
    moodlets = None


# The base module has legacy calls to save_state() after interactions, ticks and
# report opening. They must never touch disk during normal gameplay.
def _session_only_save_state(force=False):
    try:
        base.flog('V045: gameplay state kept in memory')
    except Exception:
        pass
    return False


base.save_state = _session_only_save_state


def _write_committed_state():
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
        base.flog('V045: STATE COMMITTED WITH VANILLA SAVE')
        return True
    except Exception:
        base.flog('V045: STATE COMMIT FAILED')
        base.flog(traceback.format_exc())
        return False


def _reload_committed_state(reason='save loaded'):
    try:
        base.STATE = {'version': 3, 'slots': {}}
        base.STATE_LOADED = False
        base.DIRTY = False
        base.load_state()
        base.flog('V045: COMMITTED STATE RELOADED ({})'.format(reason))
        return True
    except Exception:
        base.flog('V045: COMMITTED STATE RELOAD FAILED ({})'.format(reason))
        base.flog(traceback.format_exc())
        return False


# This hook is used by established TS4 libraries to detect an actual save load.
# It fires once after all households/SimInfos are loaded for a save and is not
# the normal lot-travel hook. Therefore unsaved in-memory state is discarded
# reliably when the player returns to the main menu and loads the save again.
@base.inject_to(GameServiceManager, 'on_all_households_and_sim_infos_loaded',
                '_deeprel_v045_load_wrapped')
def _on_real_save_loaded(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    _reload_committed_state('GameServiceManager save load')
    return result


# Commit only after the vanilla save generator completes. send_save_message is
# also checked so internal/background save-like calls do not create a checkpoint.
@base.inject_to(PersistenceService, 'save_game_gen', '_deeprel_v045_save_wrapped')
def _commit_after_real_save(original, self, timeline, save_game_data,
                            send_save_message=True, check_cooldown=False):
    try:
        base.scan_active_household()
    except Exception:
        base.flog('V045: PRE-SAVE SCAN FAILED')
        base.flog(traceback.format_exc())

    result = yield from original(
        self,
        timeline,
        save_game_data,
        send_save_message=send_save_message,
        check_cooldown=check_cooldown
    )

    if send_save_message and result is not False:
        _write_committed_state()
    else:
        base.flog('V045: SIDECAR COMMIT SKIPPED (not a completed player save)')
    return result


base.flog('V045 SAVE/LOAD LIFECYCLE HOOKS INSTALLED')

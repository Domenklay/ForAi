# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.5 — real TS4 save/load semantics.

Normal gameplay mutates only in-memory state. The sidecar JSON is reloaded when
TS4 actually loads a save and is committed only after a completed player save.
Old v0.4.2-v0.4.4 sidecars are reset once because those versions could persist
unsaved session changes.
"""

import json
import os
import traceback

from game_services import GameServiceManager
from services.persistence_service import PersistenceService

import deep_relationships as base

VERSION = '0.4.5'
PERSISTENCE_EPOCH = 5
base.VERSION = VERSION

try:
    import zzy_deep_relationships_moodlets as moodlets
    moodlets.VERSION = VERSION
except Exception:
    moodlets = None


# Legacy base functions call save_state after interactions, ticks and reports.
# Replace that public writer with a no-op so gameplay never touches the sidecar.
def _session_only_save_state(force=False):
    try:
        base.flog('V045: gameplay state kept in memory')
    except Exception:
        pass
    return False


base.save_state = _session_only_save_state


def _write_committed_state():
    try:
        base.STATE['persistence_epoch'] = PERSISTENCE_EPOCH
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
        # Always discard memory from the previous play session first.
        base.STATE = {'version': 3, 'slots': {}}
        base.STATE_LOADED = False
        base.DIRTY = False
        base.load_state()

        # Previous releases could write unsaved changes. Treat their sidecar as
        # untrusted once, then rebuild from the vanilla relationships contained
        # in the currently loaded save. Nothing is written until the player
        # performs the next normal Save.
        if int(base.STATE.get('persistence_epoch', 0) or 0) != PERSISTENCE_EPOCH:
            base.STATE = {
                'version': 3,
                'persistence_epoch': PERSISTENCE_EPOCH,
                'slots': {}
            }
            base.STATE_LOADED = True
            base.DIRTY = True
            base.flog('V045: LEGACY SIDECAR RESET; REBUILDING FROM LOADED SAVE')
        else:
            base.flog('V045: COMMITTED STATE RELOADED ({})'.format(reason))
        return True
    except Exception:
        base.flog('V045: COMMITTED STATE RELOAD FAILED ({})'.format(reason))
        base.flog(traceback.format_exc())
        return False


# Established TS4 libraries use this exact lifecycle point for Save Loaded.
# Unlike Zone loading, this fires once for an actual save load and not for
# ordinary travel between lots.
@base.inject_to(GameServiceManager, 'on_all_households_and_sim_infos_loaded',
                '_deeprel_v045_load_wrapped')
def _on_real_save_loaded(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    _reload_committed_state('GameServiceManager save load')
    return result


# Commit only after the vanilla save generator has completed. Internal calls
# without send_save_message do not establish a Deep Relationships checkpoint.
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

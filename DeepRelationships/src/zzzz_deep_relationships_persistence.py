# -*- coding: utf-8 -*-
"""Deep Relationships v0.4.3 — save semantics.

Session changes stay in memory. The external state file is committed only when
The Sims 4 invokes its normal save routine. This makes Quit Without Saving roll
back Deep Relationships together with the vanilla save.
"""

import traceback

from services.persistence_service import PersistenceService

import deep_relationships as base

VERSION = '0.4.3'
base.VERSION = VERSION

try:
    import zzy_deep_relationships_moodlets as moodlets
    moodlets.VERSION = VERSION
except Exception:
    moodlets = None

# Keep the real disk writer, then replace the public writer used by gameplay
# updates with a no-op. All gameplay mutations remain in base.STATE in memory.
_REAL_SAVE_STATE = base.save_state


def _deferred_save_state(force=False):
    try:
        if force:
            base.flog('STATE WRITE DEFERRED UNTIL GAME SAVE')
    except Exception:
        pass
    return False


base.save_state = _deferred_save_state


# Used to notice a new play session inside the same application process (for
# example: Main Menu -> load the same save again without restarting the game).
_LAST_CLIENT_TOKEN = None
_LAST_SLOT_ID = None


def _reload_committed_state(reason):
    try:
        base.STATE = {'version': 3, 'slots': {}}
        base.STATE_LOADED = False
        base.DIRTY = False
        base.load_state()
        base.flog('COMMITTED STATE RELOADED: {}'.format(reason))
        return True
    except Exception:
        base.flog('COMMITTED STATE RELOAD FAILED: {}'.format(reason))
        base.flog(traceback.format_exc())
        return False


_ORIGINAL_INITIALIZE_ZONE = base.initialize_zone


def _initialize_zone_with_save_semantics():
    global _LAST_CLIENT_TOKEN, _LAST_SLOT_ID
    try:
        current_client = base.client()
        current_token = id(current_client) if current_client is not None else None
        current_slot = base.slot_id()

        # A different slot always means a different committed state. A new
        # client object with the same slot usually means the user returned to
        # the main menu and loaded again; reload from disk so unsaved changes
        # from the previous play session do not leak into the newly loaded save.
        if _LAST_SLOT_ID is not None:
            if current_slot != _LAST_SLOT_ID:
                _reload_committed_state('slot changed {} -> {}'.format(
                    _LAST_SLOT_ID, current_slot))
            elif (_LAST_CLIENT_TOKEN is not None and current_token is not None
                  and current_token != _LAST_CLIENT_TOKEN):
                _reload_committed_state('new client loaded same slot {}'.format(current_slot))

        _LAST_CLIENT_TOKEN = current_token
        _LAST_SLOT_ID = current_slot
    except Exception:
        base.flog('SAVE SEMANTICS SESSION CHECK FAILED')
        base.flog(traceback.format_exc())

    return _ORIGINAL_INITIALIZE_ZONE()


base.initialize_zone = _initialize_zone_with_save_semantics


@base.inject_to(PersistenceService, 'save_game_gen', '_deeprel_v043_save_wrapped')
def _commit_on_game_save(original, self, timeline, save_game_data,
                         send_save_message=True, check_cooldown=False):
    """Commit Deep Relationships only when TS4 itself is saving."""
    try:
        # Make sure newly discovered romantic directions are included in the
        # same snapshot the player is explicitly saving.
        base.scan_active_household()
        _REAL_SAVE_STATE(True)
        base.flog('DEEP RELATIONSHIPS COMMITTED WITH GAME SAVE')
    except Exception:
        # Never block the vanilla save because our sidecar state failed.
        base.flog('DEEP RELATIONSHIPS SAVE COMMIT FAILED')
        base.flog(traceback.format_exc())

    return original(
        self,
        timeline,
        save_game_data,
        send_save_message=send_save_message,
        check_cooldown=check_cooldown
    )


base.flog('SAVE SEMANTICS INSTALLED v{}: disk writes only on game save'.format(VERSION))

# -*- coding: utf-8 -*-
"""Deep Relationships / Глубокие отношения v0.2.0
Target: The Sims 4 1.127.x / Python 3.7.
Single-file diagnostic build with direct zone bootstrap.
"""

import json
import os
import traceback
from functools import wraps

VERSION = '0.2.0'
MOD_NAME = 'Глубокие отношения'


def _ts4_root_from_script():
    try:
        p = os.path.abspath(__file__)
        low = p.lower()
        marker = '.ts4script'
        idx = low.find(marker)
        if idx >= 0:
            p = p[:idx + len(marker)]
        p = os.path.dirname(p)
        for _ in range(10):
            if os.path.basename(p).lower() == 'mods':
                return os.path.dirname(p)
            q = os.path.dirname(p)
            if q == p:
                break
            p = q
    except Exception:
        pass
    return os.path.join(os.path.expanduser('~'), 'Documents', 'Electronic Arts', 'The Sims 4')


TS4_ROOT = _ts4_root_from_script()
DATA_DIR = os.path.join(TS4_ROOT, 'mod_data', 'DeepRelationships')
LOG_PATH = os.path.join(DATA_DIR, 'deeprel.log')
STATE_PATH = os.path.join(DATA_DIR, 'deep_relationships_v2.json')


def _ensure_data_dir():
    try:
        if not os.path.isdir(DATA_DIR):
            os.makedirs(DATA_DIR)
    except Exception:
        pass


def flog(message):
    _ensure_data_dir()
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as handle:
            handle.write(str(message) + '\n')
    except Exception:
        pass


flog('=== Deep Relationships {} ==='.format(VERSION))
flog('SCRIPT IMPORTED')
flog('SCRIPT FILE: {}'.format(globals().get('__file__', '?')))
flog('TS4 ROOT: {}'.format(TS4_ROOT))

try:
    import alarms
    import date_and_time
    import services
    import sims4.commands
    import sims4.log
    import zone
    from relationships.relationship_service import RelationshipService
    from relationships.relationship_track import RelationshipTrack
    from services.persistence_service import PersistenceService
    from sims4.localization import LocalizationHelperTuning
    from singletons import DEFAULT
    from ui.ui_dialog_notification import UiDialogNotification
    try:
        from distributor.shared_messages import IconInfoData
    except Exception:
        IconInfoData = None
    flog('GAME IMPORTS OK')
except Exception:
    flog('GAME IMPORT FAILED')
    flog(traceback.format_exc())
    raise

logger = sims4.log.Logger('DeepRelationships', default_owner='DeepRelationships')
STATE = {'version': 2, 'slots': {}}
STATE_LOADED = False
DIRTY = False
ALARM = None
NOTICE_SHOWN = False


class _AlarmOwner:
    pass


ALARM_OWNER = _AlarmOwner()


def clamp(value, low=0.0, high=100.0):
    try:
        value = float(value)
    except Exception:
        value = 0.0
    return max(low, min(high, value))


def client():
    try:
        return services.client_manager().get_first_client()
    except Exception:
        return None


def household():
    c = client()
    if c is not None:
        hh = getattr(c, 'household', None)
        if hh is not None:
            return hh
    try:
        return services.active_household()
    except Exception:
        return None


def active_sim():
    c = client()
    return getattr(c, 'active_sim', None) if c is not None else None


def slot_id():
    c = client()
    try:
        return str(int(c.account.save_slot_id or 0)) if c is not None else '0'
    except Exception:
        return '0'


def load_state():
    global STATE, STATE_LOADED
    if STATE_LOADED:
        return
    STATE_LOADED = True
    _ensure_data_dir()
    if not os.path.isfile(STATE_PATH):
        flog('STATE: new file')
        return
    try:
        with open(STATE_PATH, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        if isinstance(data, dict) and isinstance(data.get('slots'), dict):
            STATE = data
        flog('STATE LOADED')
    except Exception:
        flog('STATE LOAD FAILED')
        flog(traceback.format_exc())


def save_state(force=False):
    global DIRTY
    load_state()
    if not force and not DIRTY:
        return
    _ensure_data_dir()
    try:
        temp = STATE_PATH + '.tmp'
        with open(temp, 'w', encoding='utf-8') as handle:
            json.dump(STATE, handle, ensure_ascii=False, indent=2, sort_keys=True)
        try:
            os.replace(temp, STATE_PATH)
        except AttributeError:
            if os.path.isfile(STATE_PATH):
                os.remove(STATE_PATH)
            os.rename(temp, STATE_PATH)
        DIRTY = False
        flog('STATE SAVED')
    except Exception:
        flog('STATE SAVE FAILED')
        flog(traceback.format_exc())


def slot_state():
    load_state()
    return STATE.setdefault('slots', {}).setdefault(slot_id(), {}).setdefault('relationships', {})


def sims_in_household(hh):
    if hh is None:
        return []
    try:
        result = list(hh.sim_info_gen())
    except Exception:
        try:
            result = list(hh)
        except Exception:
            result = list(getattr(hh, '_sim_infos', ()))
    return [sim_info for sim_info in result if sim_info is not None]


def full_name(sim_info):
    if sim_info is None:
        return 'неизвестный сим'
    try:
        value = sim_info.full_name
        if value:
            return str(value)
    except Exception:
        pass
    return '{} {}'.format(getattr(sim_info, 'first_name', '') or '', getattr(sim_info, 'last_name', '') or '').strip() or 'Сим'


def notify(title, text):
    sim = active_sim()
    if sim is None:
        flog('NOTIFICATION SKIPPED: active sim not found')
        return False
    try:
        dialog = UiDialogNotification.TunableFactory().default(
            sim,
            title=lambda **_: LocalizationHelperTuning.get_raw_text(str(title)),
            text=lambda **_: LocalizationHelperTuning.get_raw_text(str(text))
        )
        if IconInfoData is not None:
            try:
                dialog.show_dialog(icon_override=IconInfoData(obj_instance=sim))
            except Exception:
                dialog.show_dialog()
        else:
            dialog.show_dialog()
        flog('NOTIFICATION SHOWN: {}'.format(title))
        return True
    except Exception:
        flog('NOTIFICATION FAILED')
        flog(traceback.format_exc())
        return False


def pair_key(source_id, target_id):
    return '{}:{}'.format(int(source_id), int(target_id))


def trait_similarity(a, b):
    try:
        a_traits = set()
        b_traits = set()
        for trait in a.trait_tracker.equipped_traits:
            guid = getattr(trait, 'guid64', None)
            if guid is not None:
                a_traits.add(guid)
        for trait in b.trait_tracker.equipped_traits:
            guid = getattr(trait, 'guid64', None)
            if guid is not None:
                b_traits.add(guid)
        return min(18.0, float(len(a_traits.intersection(b_traits))) * 6.0)
    except Exception:
        return 0.0


def scores(source, target_id):
    friendship = 0.0
    romance = 0.0
    try:
        friendship = float(source.relationship_tracker.get_relationship_score(target_id, RelationshipTrack.FRIENDSHIP_TRACK))
    except Exception:
        try:
            friendship = float(source.relationship_tracker.get_relationship_score(target_id))
        except Exception:
            pass
    try:
        romance = float(source.relationship_tracker.get_relationship_score(target_id, RelationshipTrack.ROMANCE_TRACK))
    except Exception:
        pass
    return friendship, romance


def romantic_context(source, target_id, romance_score, force=False):
    if force or romance_score > 0.0:
        return True
    tracker = source.relationship_tracker
    try:
        if getattr(tracker, 'spouse_sim_id', None) == target_id:
            return True
        if getattr(tracker, 'fiance_sim_id', None) == target_id:
            return True
        if target_id in getattr(tracker, 'steady_sim_ids', ()):
            return True
    except Exception:
        pass
    return False


def state_name(record):
    love = float(record.get('love', 0))
    trust = float(record.get('trust', 0))
    attachment = float(record.get('attachment', 0))
    satisfaction = float(record.get('satisfaction', 0))
    if love < 25 and trust < 25 and satisfaction < 20:
        return 'На грани разрыва'
    if attachment >= 75 and love < 40:
        return 'Отношения по привычке'
    if love >= 50 and trust < 30:
        return 'Недоверие'
    if love >= 50 and satisfaction < 30:
        return 'Кризис'
    if love < 40 and satisfaction < 40:
        return 'Отдаление'
    if love >= 85 and satisfaction >= 80 and attachment < 65:
        return 'Медовый месяц'
    if love >= 70 and trust >= 65 and satisfaction >= 60:
        return 'Крепкая пара'
    if attachment >= 80 and love >= 50:
        return 'Сильная привязанность'
    if love >= 55 and satisfaction >= 45:
        return 'Стабильные отношения'
    return 'Развивающиеся отношения'


def make_record(source, target, friendship, romance):
    positive_friendship = max(0.0, friendship)
    positive_romance = max(0.0, romance)
    shared = trait_similarity(source, target)
    compatibility_context = max(-12.0, min(18.0, friendship * 0.08 + romance * 0.06))
    record = {
        'source_id': int(source.sim_id),
        'target_id': int(target.sim_id),
        'love': clamp(positive_romance),
        'trust': clamp(30.0 + positive_friendship * 0.65 + min(10.0, positive_romance * 0.10)),
        'attachment': clamp(15.0 + positive_romance * 0.35 + positive_friendship * 0.15),
        'compatibility': clamp(48.0 + shared + compatibility_context),
        'satisfaction': clamp(38.0 + positive_romance * 0.35 + positive_friendship * 0.15),
        'quiet_steps': 0,
        'last_state': ''
    }
    record['last_state'] = state_name(record)
    return record


def ensure_pair(source_id, target_id, force=False):
    global DIRTY
    manager = services.sim_info_manager()
    if manager is None:
        return None
    source = manager.get(source_id)
    target = manager.get(target_id)
    if source is None or target is None:
        return None
    friendship, romance = scores(source, target_id)
    if not romantic_context(source, target_id, romance, force=force):
        return None
    relationships = slot_state()
    key = pair_key(source_id, target_id)
    record = relationships.get(key)
    if record is None:
        record = make_record(source, target, friendship, romance)
        relationships[key] = record
        DIRTY = True
        flog('PAIR CREATED: {} -> {} | {}'.format(full_name(source), full_name(target), record['last_state']))
    return record


def scan_active_household():
    hh = household()
    if hh is None:
        flog('HOUSEHOLD NOT FOUND')
        return 0
    members = sims_in_household(hh)
    flog('HOUSEHOLD FOUND: {} sims'.format(len(members)))
    created = 0
    for source in members:
        try:
            targets = tuple(source.relationship_tracker.target_sim_gen())
        except Exception:
            targets = ()
        for target_id in targets:
            before = len(slot_state())
            record = ensure_pair(source.sim_id, target_id)
            if record is not None and len(slot_state()) > before:
                created += 1
    flog('SCAN COMPLETE: {} tracked directions, {} new'.format(len(slot_state()), created))
    return created


def update_state(record):
    global DIRTY
    old = record.get('last_state') or state_name(record)
    new = state_name(record)
    record['last_state'] = new
    if old != new:
        DIRTY = True
        source_id = record.get('source_id', 0)
        target_id = record.get('target_id', 0)
        manager = services.sim_info_manager()
        source = manager.get(source_id) if manager is not None else None
        target = manager.get(target_id) if manager is not None else None
        try:
            hh = household()
            if hh is not None and source in sims_in_household(hh):
                notify(MOD_NAME, '{}: отношения с {} теперь — «{}».'.format(full_name(source), full_name(target), new))
        except Exception:
            pass
        flog('STATE CHANGE: {} -> {} : {} -> {}'.format(source_id, target_id, old, new))


def on_relationship_delta(source_id, target_id, delta, kind):
    global DIRTY
    try:
        delta = float(delta)
    except Exception:
        return
    if abs(delta) < 0.0001:
        return
    record = ensure_pair(source_id, target_id, force=(kind == 'romance'))
    if record is None:
        return

    record['quiet_steps'] = 0
    if kind == 'romance':
        if delta > 0:
            record['love'] = clamp(record['love'] + delta * 0.30)
            record['satisfaction'] = clamp(record['satisfaction'] + delta * 0.18)
            record['attachment'] = clamp(record['attachment'] + delta * 0.08)
            record['compatibility'] = clamp(record['compatibility'] + min(0.30, delta * 0.02))
        else:
            record['love'] = clamp(record['love'] + delta * 0.25)
            record['satisfaction'] = clamp(record['satisfaction'] + delta * 0.30)
            record['trust'] = clamp(record['trust'] + delta * 0.10)
            record['compatibility'] = clamp(record['compatibility'] + max(-0.40, delta * 0.025))
    else:
        if delta > 0:
            record['trust'] = clamp(record['trust'] + delta * 0.20)
            record['attachment'] = clamp(record['attachment'] + delta * 0.05)
            record['satisfaction'] = clamp(record['satisfaction'] + delta * 0.08)
            record['compatibility'] = clamp(record['compatibility'] + min(0.15, delta * 0.01))
        else:
            record['trust'] = clamp(record['trust'] + delta * 0.35)
            record['satisfaction'] = clamp(record['satisfaction'] + delta * 0.25)
            record['love'] = clamp(record['love'] + delta * 0.05)
            record['compatibility'] = clamp(record['compatibility'] + max(-0.20, delta * 0.012))
    DIRTY = True
    update_state(record)


def decay_tick():
    global DIRTY
    relationships = slot_state()
    for record in tuple(relationships.values()):
        record['quiet_steps'] = int(record.get('quiet_steps', 0)) + 1
        quiet = record['quiet_steps']
        if quiet >= 8:
            attachment = clamp(record.get('attachment', 0))
            protection = min(0.65, attachment / 150.0)
            record['satisfaction'] = clamp(record.get('satisfaction', 0) - 0.60 * (1.0 - protection))
            if quiet >= 16:
                record['attachment'] = clamp(record.get('attachment', 0) - 0.12)
            if quiet >= 24:
                record['love'] = clamp(record.get('love', 0) - 0.08)
            DIRTY = True
            update_state(record)


def _track_kind(track):
    if track is DEFAULT:
        return 'friendship'
    try:
        if track is RelationshipTrack.ROMANCE_TRACK or track == RelationshipTrack.ROMANCE_TRACK:
            return 'romance'
        if track is RelationshipTrack.FRIENDSHIP_TRACK or track == RelationshipTrack.FRIENDSHIP_TRACK:
            return 'friendship'
    except Exception:
        pass
    return None


def inject_to(obj, name, marker):
    def decorator(new):
        old = getattr(obj, name)
        if getattr(old, marker, False):
            return new
        @wraps(old)
        def wrapped(*args, **kwargs):
            return new(old, *args, **kwargs)
        setattr(wrapped, marker, True)
        setattr(obj, name, wrapped)
        return new
    return decorator


@inject_to(RelationshipService, 'add_relationship_score', '_deeprel_v2_add')
def observe_add(original, self, sim_id_a, sim_id_b, increment, track=DEFAULT, threshold=None, **kwargs):
    result = original(self, sim_id_a, sim_id_b, increment, track=track, threshold=threshold, **kwargs)
    try:
        kind = _track_kind(track)
        if kind is not None:
            on_relationship_delta(sim_id_a, sim_id_b, increment, kind)
    except Exception:
        flog('RELATIONSHIP ADD OBSERVER FAILED')
        flog(traceback.format_exc())
    return result


@inject_to(RelationshipService, 'set_relationship_score', '_deeprel_v2_set')
def observe_set(original, self, sim_id_a, sim_id_b, value, track=DEFAULT, threshold=None, **kwargs):
    kind = _track_kind(track)
    before = None
    if kind is not None:
        try:
            before = float(self.get_relationship_score(sim_id_a, sim_id_b, track=track))
        except Exception:
            before = None
    result = original(self, sim_id_a, sim_id_b, value, track=track, threshold=threshold, **kwargs)
    if kind is not None and before is not None:
        try:
            after = float(self.get_relationship_score(sim_id_a, sim_id_b, track=track))
            delta = after - before
            if abs(delta) > 0.0001:
                on_relationship_delta(sim_id_a, sim_id_b, delta, kind)
        except Exception:
            flog('RELATIONSHIP SET OBSERVER FAILED')
            flog(traceback.format_exc())
    return result


flog('RELATIONSHIP OBSERVERS INSTALLED')


def alarm_callback(_):
    try:
        flog('PERIODIC TICK')
        scan_active_household()
        decay_tick()
        save_state(force=True)
    except Exception:
        flog('PERIODIC TICK FAILED')
        flog(traceback.format_exc())


def start_alarm():
    global ALARM
    if ALARM is not None:
        try:
            alarms.cancel_alarm(ALARM)
        except Exception:
            pass
    try:
        ALARM = alarms.add_alarm(
            ALARM_OWNER,
            date_and_time.create_time_span(minutes=30),
            alarm_callback,
            repeating=True,
            repeating_time_span=date_and_time.create_time_span(hours=6)
        )
        flog('ALARM STARTED')
    except Exception:
        flog('ALARM START FAILED')
        flog(traceback.format_exc())


def initialize_zone():
    global NOTICE_SHOWN
    flog('ZONE LOADED')
    sim = active_sim()
    if sim is None:
        flog('ACTIVE SIM NOT FOUND')
    else:
        flog('ACTIVE SIM FOUND: {}'.format(full_name(getattr(sim, 'sim_info', None) or sim)))

    # Show the startup notice before the relationship engine does any heavy work.
    if not NOTICE_SHOWN:
        if notify('Глубокие отношения v{}'.format(VERSION), 'Мод успешно загружен. Анализ отношений запущен автоматически.'):
            NOTICE_SHOWN = True

    try:
        load_state()
        hh = household()
        if hh is None:
            flog('HOUSEHOLD NOT FOUND DURING INIT')
        else:
            flog('HOUSEHOLD FOUND DURING INIT')
        scan_active_household()
        save_state(force=True)
        start_alarm()
        flog('RELATIONSHIP ENGINE STARTED: {} tracked directions'.format(len(slot_state())))
    except Exception:
        flog('RELATIONSHIP ENGINE INIT FAILED')
        flog(traceback.format_exc())


@inject_to(zone.Zone, 'on_loading_screen_animation_finished', '_deeprel_v2_zone')
def on_loading_finished(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    try:
        initialize_zone()
    except Exception:
        flog('ZONE HOOK FAILED')
        flog(traceback.format_exc())
    return result


@inject_to(PersistenceService, 'save_game_gen', '_deeprel_v2_save')
def on_save(original, self, timeline, save_game_data, send_save_message=True, check_cooldown=False):
    try:
        scan_active_household()
        save_state(force=True)
        flog('GAME SAVE HOOK OK')
    except Exception:
        flog('GAME SAVE HOOK FAILED')
        flog(traceback.format_exc())
    return original(self, timeline, save_game_data, send_save_message=send_save_message, check_cooldown=check_cooldown)


@sims4.commands.Command('deeprel.status', command_type=sims4.commands.CommandType.Live)
def deeprel_status(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        rels = slot_state()
        output('Deep Relationships v{} | slot {} | tracked {}'.format(VERSION, slot_id(), len(rels)))
        output('Log: {}'.format(LOG_PATH))
        return True
    except Exception as exc:
        output('Deep Relationships status error: {}'.format(exc))
        return False


flog('BOOTSTRAP HOOK INSTALLED')
logger.info('Deep Relationships v{} imported.'.format(VERSION))

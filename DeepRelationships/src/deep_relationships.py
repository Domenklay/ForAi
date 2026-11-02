# -*- coding: utf-8 -*-
"""Deep Relationships / Глубокие отношения for The Sims 4.

Standalone script mod. Normal gameplay requires no console commands.
Target game line: 1.127.x (Python 3.7 runtime).
"""

import json
import os
from functools import wraps

import alarms
import services
import sims4.commands
import sims4.log
from date_and_time import create_time_span
from game_services import GameServiceManager
from relationships.relationship_track import RelationshipTrack
from relationships.relationship_tracker import RelationshipTracker
from sims4.localization import LocalizationHelperTuning
from sims4.service_manager import Service
from singletons import DEFAULT
from ui.ui_dialog_notification import UiDialogNotification

MOD_NAME = 'Глубокие отношения'
MOD_VERSION = '0.1.0'
DATA_VERSION = 1
logger = sims4.log.Logger('DeepRelationships', default_owner='DeepRelationships')


def clamp(value, low=0.0, high=100.0):
    try:
        value = float(value)
    except Exception:
        value = 0.0
    if value < low:
        return low
    if value > high:
        return high
    return value


def _documents_path():
    """Resolve the Windows Documents folder, including OneDrive redirection."""
    try:
        import winreg
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            value, _ = winreg.QueryValueEx(key, 'Personal')
            return os.path.expandvars(value)
    except Exception:
        return os.path.expanduser(os.path.join('~', 'Documents'))


def _data_root():
    root = os.path.join(_documents_path(), 'Electronic Arts', 'The Sims 4', 'mod_data', 'DeepRelationships')
    try:
        os.makedirs(root, exist_ok=True)
    except Exception:
        pass
    return root


def _save_slot_key():
    try:
        persistence = services.get_persistence_service()
        if persistence is not None:
            guid = persistence.get_save_slot_proto_guid()
            if guid:
                return str(guid)
            slot = persistence.get_save_slot_proto_buff()
            if slot is not None and getattr(slot, 'slot_id', None) is not None:
                return str(slot.slot_id)
    except Exception:
        pass
    return 'default'


def _full_name(sim_info):
    if sim_info is None:
        return 'неизвестный сим'
    try:
        return sim_info.full_name
    except Exception:
        try:
            return '{} {}'.format(sim_info.first_name, sim_info.last_name).strip()
        except Exception:
            return 'сим'


def _show_notification(title, text):
    try:
        client = services.client_manager().get_first_client()
        if client is None or client.active_sim is None:
            return
        notification = UiDialogNotification.TunableFactory().default(
            client.active_sim,
            title=lambda **_: LocalizationHelperTuning.get_raw_text(title),
            text=lambda **_: LocalizationHelperTuning.get_raw_text(text)
        )
        notification.show_dialog()
    except Exception as exc:
        logger.exception('Unable to show notification: {}', exc)


def _is_active_household_sim(sim_id):
    try:
        household = services.active_household()
        if household is None:
            return False
        sim_info = services.sim_info_manager().get(sim_id)
        return sim_info is not None and sim_info in household
    except Exception:
        return False


def _track_kind(track):
    try:
        if track is RelationshipTrack.ROMANCE_TRACK or track == RelationshipTrack.ROMANCE_TRACK:
            return 'romance'
        if track is RelationshipTrack.FRIENDSHIP_TRACK or track == RelationshipTrack.FRIENDSHIP_TRACK:
            return 'friendship'
    except Exception:
        pass
    return None


def _trait_similarity(source_info, target_info):
    """Small, stable compatibility bonus for shared visible/equipped traits."""
    try:
        source_traits = set()
        target_traits = set()
        for trait in source_info.trait_tracker.equipped_traits:
            guid = getattr(trait, 'guid64', None)
            if guid is not None:
                source_traits.add(guid)
        for trait in target_info.trait_tracker.equipped_traits:
            guid = getattr(trait, 'guid64', None)
            if guid is not None:
                target_traits.add(guid)
        return min(18.0, float(len(source_traits.intersection(target_traits))) * 6.0)
    except Exception:
        return 0.0


def _state_for(record):
    love = record.get('love', 0.0)
    trust = record.get('trust', 0.0)
    attachment = record.get('attachment', 0.0)
    satisfaction = record.get('satisfaction', 0.0)

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


class DeepRelationshipEngine(object):
    def __init__(self):
        self.slot_key = None
        self.path = None
        self.data = {'version': DATA_VERSION, 'relationships': {}}
        self.dirty = False
        self.pending_changes = 0

    def _pair_key(self, source_id, target_id):
        return '{}:{}'.format(int(source_id), int(target_id))

    def load_for_current_save(self):
        slot_key = _save_slot_key()
        if self.slot_key == slot_key and self.path is not None:
            return
        self.slot_key = slot_key
        self.path = os.path.join(_data_root(), 'relationships_{}.json'.format(slot_key))
        self.data = {'version': DATA_VERSION, 'relationships': {}}
        try:
            if os.path.isfile(self.path):
                with open(self.path, 'r', encoding='utf-8') as handle:
                    loaded = json.load(handle)
                if isinstance(loaded, dict) and isinstance(loaded.get('relationships'), dict):
                    self.data = loaded
                    self.data['version'] = DATA_VERSION
        except Exception as exc:
            logger.exception('Unable to load relationship data: {}', exc)
        self.dirty = False
        self.pending_changes = 0

    def save(self, force=False):
        if not force and not self.dirty:
            return
        if self.path is None:
            self.load_for_current_save()
        try:
            folder = os.path.dirname(self.path)
            os.makedirs(folder, exist_ok=True)
            temp_path = self.path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as handle:
                json.dump(self.data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            os.replace(temp_path, self.path)
            self.dirty = False
            self.pending_changes = 0
        except Exception as exc:
            logger.exception('Unable to save relationship data: {}', exc)

    def _relationship_scores(self, source_info, target_id):
        romance = 0.0
        friendship = 0.0
        try:
            romance = float(source_info.relationship_tracker.get_relationship_score(target_id, RelationshipTrack.ROMANCE_TRACK))
        except Exception:
            pass
        try:
            friendship = float(source_info.relationship_tracker.get_relationship_score(target_id, RelationshipTrack.FRIENDSHIP_TRACK))
        except Exception:
            pass
        return friendship, romance

    def _is_romantic_context(self, source_info, target_id, romance_score, force=False):
        if force or romance_score > 0.0:
            return True
        tracker = source_info.relationship_tracker
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

    def _new_record(self, source_info, target_info, friendship, romance):
        positive_friendship = max(0.0, friendship)
        positive_romance = max(0.0, romance)
        shared_trait_bonus = _trait_similarity(source_info, target_info)
        compatibility_context = max(-12.0, min(18.0, friendship * 0.08 + romance * 0.06))
        record = {
            'source_id': int(source_info.sim_id),
            'target_id': int(target_info.sim_id) if target_info is not None else 0,
            'love': clamp(positive_romance),
            'trust': clamp(30.0 + positive_friendship * 0.65 + min(10.0, positive_romance * 0.10)),
            'attachment': clamp(15.0 + positive_romance * 0.35 + positive_friendship * 0.15),
            'compatibility': clamp(48.0 + shared_trait_bonus + compatibility_context),
            'satisfaction': clamp(38.0 + positive_romance * 0.35 + positive_friendship * 0.15),
            'quiet_steps': 0,
            'last_state': ''
        }
        record['last_state'] = _state_for(record)
        return record

    def ensure_pair(self, source_id, target_id, force=False):
        self.load_for_current_save()
        manager = services.sim_info_manager()
        if manager is None:
            return None
        source_info = manager.get(source_id)
        target_info = manager.get(target_id)
        if source_info is None or target_info is None:
            return None
        friendship, romance = self._relationship_scores(source_info, target_id)
        if not self._is_romantic_context(source_info, target_id, romance, force=force):
            return None
        key = self._pair_key(source_id, target_id)
        relationships = self.data.setdefault('relationships', {})
        record = relationships.get(key)
        if record is None:
            record = self._new_record(source_info, target_info, friendship, romance)
            relationships[key] = record
            self.dirty = True
        return record

    def scan_active_household(self):
        self.load_for_current_save()
        household = services.active_household()
        relationship_service = services.relationship_service()
        if household is None or relationship_service is None:
            return 0
        initialized = 0
        for source_info in tuple(household):
            try:
                targets = tuple(relationship_service.target_sim_gen(source_info.sim_id))
            except Exception:
                targets = ()
            for target_id in targets:
                before = len(self.data.get('relationships', {}))
                record = self.ensure_pair(source_info.sim_id, target_id, force=False)
                if record is not None and len(self.data.get('relationships', {})) > before:
                    initialized += 1
        if initialized:
            self.save(force=True)
        return initialized

    def _notify_state_change(self, source_id, target_id, old_state, new_state):
        if not _is_active_household_sim(source_id):
            return
        manager = services.sim_info_manager()
        source_info = manager.get(source_id) if manager is not None else None
        target_info = manager.get(target_id) if manager is not None else None
        text = '{}: отношения с {} теперь — «{}».'.format(_full_name(source_info), _full_name(target_info), new_state)
        _show_notification(MOD_NAME, text)

    def _update_state(self, record, notify=True):
        old_state = record.get('last_state') or _state_for(record)
        new_state = _state_for(record)
        record['last_state'] = new_state
        if notify and new_state != old_state:
            self._notify_state_change(record.get('source_id', 0), record.get('target_id', 0), old_state, new_state)
        return new_state

    def on_delta(self, source_id, target_id, delta, kind):
        if delta == 0:
            return
        manager = services.sim_info_manager()
        source_info = manager.get(source_id) if manager is not None else None
        if source_info is None:
            return
        friendship, romance = self._relationship_scores(source_info, target_id)
        force = kind == 'romance'
        record = self.ensure_pair(source_id, target_id, force=force)
        if record is None:
            return

        delta = float(delta)
        if delta > 0:
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
        elif kind == 'friendship':
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

        self._update_state(record, notify=True)
        self.dirty = True
        self.pending_changes += 1
        if self.pending_changes >= 8:
            self.save(force=True)

    def tick(self):
        self.load_for_current_save()
        relationships = self.data.get('relationships', {})
        if not relationships:
            return
        changed = False
        for record in tuple(relationships.values()):
            quiet_steps = int(record.get('quiet_steps', 0)) + 1
            record['quiet_steps'] = quiet_steps
            if quiet_steps >= 8:
                attachment = clamp(record.get('attachment', 0.0))
                protection = min(0.65, attachment / 150.0)
                satisfaction_loss = 0.60 * (1.0 - protection)
                record['satisfaction'] = clamp(record.get('satisfaction', 0.0) - satisfaction_loss)
                if quiet_steps >= 16:
                    record['attachment'] = clamp(record.get('attachment', 0.0) - 0.12)
                if quiet_steps >= 24:
                    record['love'] = clamp(record.get('love', 0.0) - 0.08)
                self._update_state(record, notify=True)
                changed = True
        if changed:
            self.dirty = True
        self.save(force=True)

    def report_for_active_sim(self):
        self.load_for_current_save()
        client = services.client_manager().get_first_client()
        if client is None or client.active_sim is None:
            return 'Нет активного сима.'
        source_id = client.active_sim.sim_id
        manager = services.sim_info_manager()
        lines = []
        prefix = '{}:'.format(source_id)
        for key, record in self.data.get('relationships', {}).items():
            if not key.startswith(prefix):
                continue
            target_info = manager.get(record.get('target_id')) if manager is not None else None
            lines.append('{} — {} | Любовь {:.0f}, Доверие {:.0f}, Привязанность {:.0f}, Совместимость {:.0f}, Удовлетворённость {:.0f}'.format(
                _full_name(target_info), _state_for(record), record.get('love', 0), record.get('trust', 0),
                record.get('attachment', 0), record.get('compatibility', 0), record.get('satisfaction', 0)))
        if not lines:
            return 'У активного сима пока нет отслеживаемых романтических отношений.'
        return '\n'.join(lines)


ENGINE = DeepRelationshipEngine()
_service_instance = None
_session_notified = False


class DeepRelationshipsService(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._alarm_handle = None

    def start(self, *args, **kwargs):
        try:
            if self._alarm_handle is None:
                self._alarm_handle = alarms.add_alarm(
                    self,
                    create_time_span(minutes=360),
                    self._on_tick,
                    repeating=True
                )
        except Exception as exc:
            logger.exception('Unable to start repeating alarm: {}', exc)

    def on_zone_load(self, *args, **kwargs):
        global _session_notified
        try:
            initialized = ENGINE.scan_active_household()
            ENGINE.save(force=True)
            if not _session_notified:
                count = len(ENGINE.data.get('relationships', {}))
                _show_notification(
                    '{} v{}'.format(MOD_NAME, MOD_VERSION),
                    'Мод активен. Команды не нужны. Отслеживаемых направлений отношений: {}. Система автоматически учитывает любовь, доверие, привязанность, совместимость и удовлетворённость.'.format(count)
                )
                _session_notified = True
        except Exception as exc:
            logger.exception('Zone-load initialization failed: {}', exc)

    def _on_tick(self, _alarm_handle):
        try:
            ENGINE.tick()
        except Exception as exc:
            logger.exception('Relationship tick failed: {}', exc)

    def stop(self, *args, **kwargs):
        try:
            ENGINE.save(force=True)
        except Exception:
            pass
        try:
            if self._alarm_handle is not None:
                alarms.cancel_alarm(self._alarm_handle)
        except Exception:
            pass
        self._alarm_handle = None


def _inject(target_object, function_name):
    def decorator(new_function):
        original = getattr(target_object, function_name)
        if getattr(original, '_deep_relationships_wrapped', False):
            return new_function

        @wraps(original)
        def wrapper(*args, **kwargs):
            return new_function(original, *args, **kwargs)

        wrapper._deep_relationships_wrapped = True
        setattr(target_object, function_name, wrapper)
        return new_function
    return decorator


@_inject(GameServiceManager, 'start_services')
def _deep_relationships_start_services(original, self, *args, **kwargs):
    global _service_instance
    try:
        if _service_instance is None:
            _service_instance = DeepRelationshipsService()
            self.register_service(_service_instance, is_init_critical=False)
    except Exception as exc:
        logger.exception('Unable to register service: {}', exc)
    return original(self, *args, **kwargs)


@_inject(RelationshipTracker, 'add_relationship_score')
def _deep_relationships_add_score(original, self, target_sim_id, increment, track=DEFAULT, threshold=None, **kwargs):
    result = original(self, target_sim_id, increment, track=track, threshold=threshold, **kwargs)
    try:
        kind = _track_kind(track)
        if kind is not None:
            ENGINE.on_delta(self._sim_info.sim_id, target_sim_id, float(increment), kind)
    except Exception as exc:
        logger.exception('add_relationship_score observer failed: {}', exc)
    return result


@_inject(RelationshipTracker, 'set_relationship_score')
def _deep_relationships_set_score(original, self, target_sim_id, value, track=DEFAULT, threshold=None, **kwargs):
    kind = _track_kind(track)
    before = None
    if kind is not None:
        try:
            before = float(self.get_relationship_score(target_sim_id, track))
        except Exception:
            before = None
    result = original(self, target_sim_id, value, track=track, threshold=threshold, **kwargs)
    if kind is not None and before is not None:
        try:
            after = float(self.get_relationship_score(target_sim_id, track))
            delta = after - before
            if abs(delta) > 0.0001:
                ENGINE.on_delta(self._sim_info.sim_id, target_sim_id, delta, kind)
        except Exception as exc:
            logger.exception('set_relationship_score observer failed: {}', exc)
    return result


@sims4.commands.Command('deeprel.report', command_type=sims4.commands.CommandType.Live)
def deeprel_report(_connection=None):
    """Optional diagnostic command; the mod itself does not require commands."""
    output = sims4.commands.CheatOutput(_connection)
    try:
        report = ENGINE.report_for_active_sim()
        output(report)
        _show_notification('{} — диагностика'.format(MOD_NAME), report)
    except Exception as exc:
        output('Deep Relationships error: {}'.format(exc))


logger.info('Deep Relationships v{} loaded.', MOD_VERSION)

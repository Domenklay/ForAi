# -*- coding: utf-8 -*-
"""Reliable zone bootstrap for Deep Relationships v0.1.1."""

from functools import wraps
import alarms
import date_and_time
import zone
from services.persistence_service import PersistenceService
import deep_relationships as base

VERSION = '0.1.1'
ALARM = None
START_NOTICE = False

class _Owner:
    pass

OWNER = _Owner()
base.MOD_VERSION = VERSION


def inject_to(obj, name):
    def deco(new):
        old = getattr(obj, name)
        if getattr(old, '_deeprel_bootstrap_wrapped', False):
            return new
        @wraps(old)
        def wrapped(*args, **kwargs):
            return new(old, *args, **kwargs)
        wrapped._deeprel_bootstrap_wrapped = True
        setattr(obj, name, wrapped)
        return new
    return deco


def alarm_cb(_):
    try:
        base.ENGINE.scan_active_household()
        base.ENGINE.tick()
    except Exception as exc:
        base.logger.exception('Deep Relationships periodic update failed: {}', exc)


def start_alarm():
    global ALARM
    try:
        service = getattr(base, '_service_instance', None)
        if service is not None and getattr(service, '_alarm_handle', None) is not None:
            return
    except Exception:
        pass
    if ALARM is not None:
        try:
            alarms.cancel_alarm(ALARM)
        except Exception:
            pass
    try:
        ALARM = alarms.add_alarm(
            OWNER,
            date_and_time.create_time_span(minutes=15),
            alarm_cb,
            repeating=True,
            repeating_time_span=date_and_time.create_time_span(hours=6)
        )
    except Exception as exc:
        base.logger.exception('Deep Relationships fallback alarm failed: {}', exc)


def initialize_zone():
    global START_NOTICE
    try:
        base.ENGINE.load_for_current_save()
        initialized = base.ENGINE.scan_active_household()
        base.ENGINE.save(force=True)
        start_alarm()
        if not START_NOTICE:
            START_NOTICE = True
            count = len(base.ENGINE.data.get('relationships', {}))
            base._show_notification(
                'Глубокие отношения v{}'.format(VERSION),
                'Мод активен. Команды не нужны. Отслеживаемых направлений отношений: {}. Любовь, доверие, привязанность, совместимость и удовлетворённость работают автоматически.'.format(count)
            )
    except Exception as exc:
        base.logger.exception('Deep Relationships zone bootstrap failed: {}', exc)


@inject_to(zone.Zone, 'on_loading_screen_animation_finished')
def on_loading_finished(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    initialize_zone()
    return result


@inject_to(PersistenceService, 'save_game_gen')
def on_save(original, self, timeline, save_game_data, send_save_message=True, check_cooldown=False):
    try:
        base.ENGINE.scan_active_household()
        base.ENGINE.save(force=True)
    except Exception as exc:
        base.logger.exception('Deep Relationships save hook failed: {}', exc)
    return original(self, timeline, save_game_data, send_save_message=send_save_message, check_cooldown=check_cooldown)


base.logger.info('Deep Relationships reliable bootstrap v{} loaded.'.format(VERSION))

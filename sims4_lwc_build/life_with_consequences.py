# -*- coding: utf-8 -*-
import json
import os
import random
from functools import wraps

import alarms
import clock
import services
import sims4.commands
import zone

from sims4.localization import LocalizationHelperTuning
from ui.ui_dialog_notification import UiDialogNotification

MOD_VERSION = "0.2.2"
TARGET_GAME = "1.127.41.1030"
CHECK_HOURS = 1

DEFAULT_SETTINGS = {
    "automatic_events": True,
    "event_interval_hours": 72,
    "event_jitter_hours": 12,
    "recovery_hours": 6,
    "stress_recovery": 2,
    "notifications": True,
}

DATA = None
SLOT = None
ALARM = None
NOTICE_SHOWN = False


class AlarmOwner:
    pass


ALARM_OWNER = AlarmOwner()


def output(connection, text):
    try:
        sims4.commands.CheatOutput(connection)(text)
    except Exception:
        pass


def ts4_folder():
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "Documents", "Electronic Arts", "The Sims 4"),
        os.path.join(home, "OneDrive", "Documents", "Electronic Arts", "The Sims 4"),
        os.path.join(home, "OneDrive", "Документы", "Electronic Arts", "The Sims 4"),
    ]
    for path in candidates:
        if os.path.isdir(path):
            return path
    return candidates[0]


def slot_key():
    try:
        client = services.client_manager().get_first_client()
        account = getattr(client, "account", None)
        value = getattr(account, "save_slot_id", None)
        if value is not None:
            return "Slot_{:08X}".format(int(value))
    except Exception:
        pass
    return "Slot_UNSLOTTED"


def state_path():
    return os.path.join(
        ts4_folder(), "mod_data", "LifeWithConsequences", "slots", slot_key(), "state.json"
    )


def blank_data():
    return {
        "version": MOD_VERSION,
        "settings": dict(DEFAULT_SETTINGS),
        "sims": {},
    }


def load_data(force=False):
    global DATA, SLOT
    current = slot_key()
    if DATA is not None and SLOT == current and not force:
        return DATA

    SLOT = current
    path = state_path()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        if not isinstance(raw, dict):
            raw = {}
    except Exception:
        raw = {}

    result = blank_data()
    if isinstance(raw.get("settings"), dict):
        result["settings"].update(raw["settings"])
    if isinstance(raw.get("sims"), dict):
        result["sims"] = raw["sims"]
    DATA = result
    save_data()
    return DATA


def save_data():
    if DATA is None or slot_key() == "Slot_UNSLOTTED":
        return
    path = state_path()
    folder = os.path.dirname(path)
    try:
        os.makedirs(folder, exist_ok=True)
        temp = path + ".tmp"
        with open(temp, "w", encoding="utf-8") as handle:
            json.dump(DATA, handle, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(temp, path)
    except Exception:
        pass


def active_sim_info():
    try:
        client = services.client_manager().get_first_client()
        if client is not None and client.active_sim is not None:
            return client.active_sim.sim_info
    except Exception:
        pass
    return None


def household_sims():
    try:
        household = services.active_household()
        if household is not None:
            generator = getattr(household, "sim_info_gen", None)
            if generator is not None:
                return list(generator())
    except Exception:
        pass
    sim_info = active_sim_info()
    return [sim_info] if sim_info is not None else []


def sim_id(sim_info):
    return getattr(sim_info, "sim_id", getattr(sim_info, "id", None))


def sim_name(sim_info):
    name = "{} {}".format(
        getattr(sim_info, "first_name", ""),
        getattr(sim_info, "last_name", ""),
    ).strip()
    return name or "Сим"


def eligible(sim_info):
    try:
        attr = getattr(sim_info, "is_teen_or_older")
        return bool(attr() if callable(attr) else attr)
    except Exception:
        return True


def now_ticks():
    try:
        return int(services.time_service().sim_now.absolute_ticks())
    except Exception:
        return 0


def hours_ticks(hours):
    try:
        return int(clock.interval_in_sim_hours(float(hours)).in_ticks())
    except Exception:
        return 0


def event_delay():
    settings = load_data()["settings"]
    base = max(12, int(settings.get("event_interval_hours", 72)))
    jitter = max(0, int(settings.get("event_jitter_hours", 12)))
    return max(12, base + random.randint(-jitter, jitter))


def new_state(sim_info):
    now = now_ticks()
    return {
        "name": sim_name(sim_info),
        "stress": 0,
        "reputation": 0,
        "xp": 0,
        "events": 0,
        "last_event": "",
        "perk_points": 0,
        "next_event_tick": now + hours_ticks(event_delay()) if now else 0,
        "next_recovery_tick": now + hours_ticks(6) if now else 0,
    }


def sim_state(sim_info):
    data = load_data()
    key = str(sim_id(sim_info))
    state = data["sims"].get(key)
    if not isinstance(state, dict):
        state = new_state(sim_info)
        data["sims"][key] = state
    defaults = new_state(sim_info)
    for name, value in defaults.items():
        state.setdefault(name, value)
    state["name"] = sim_name(sim_info)
    save_data()
    return state


def level_from_xp(xp):
    xp = max(0, int(xp))
    level = 1
    while level < 20:
        n = level
        if xp < 50 * n * (n + 1):
            break
        level += 1
    return level


def stress_stage(value):
    value = int(value)
    if value >= 100:
        return "Кризис"
    if value >= 75:
        return "На грани"
    if value >= 50:
        return "Сильное напряжение"
    if value >= 25:
        return "Напряжение"
    return "Спокойствие"


def reputation_stage(value):
    value = int(value)
    if value >= 75:
        return "Безупречная"
    if value >= 30:
        return "Хорошая"
    if value > -30:
        return "Нейтральная"
    if value > -75:
        return "Плохая"
    return "Скандальная"


def notify(title, text):
    if not load_data()["settings"].get("notifications", True):
        return
    try:
        client = services.client_manager().get_first_client()
        sim = client.active_sim
        dialog = UiDialogNotification.TunableFactory().default(
            sim,
            title=lambda **_: LocalizationHelperTuning.get_raw_text(title),
            text=lambda **_: LocalizationHelperTuning.get_raw_text(text),
        )
        dialog.show_dialog()
    except Exception:
        pass


def apply(sim_info, state, stress=0, reputation=0, xp=0):
    old_level = level_from_xp(state["xp"])
    state["stress"] = max(0, min(100, int(state["stress"]) + int(stress)))
    state["reputation"] = max(-100, min(100, int(state["reputation"]) + int(reputation)))
    state["xp"] = max(0, int(state["xp"]) + int(xp))
    new_level = level_from_xp(state["xp"])
    if new_level > old_level:
        state["perk_points"] = int(state.get("perk_points", 0)) + new_level - old_level
        notify(
            "Новый жизненный уровень",
            "{} достиг(ла) уровня {}.".format(sim_name(sim_info), new_level),
        )
    save_data()


EVENTS = (
    ("Неудачный день", "Одна проблема потянула за собой другую.", 14, 0, 18),
    ("Маленькая победа", "Сегодня многое получилось лучше ожидаемого.", -10, 3, 16),
    ("Публичная ссора", "Конфликт заметили окружающие.", 10, -12, 28),
    ("Неожиданная поддержка", "Помощь пришла именно вовремя.", -12, 4, 18),
    ("Непредвиденные расходы", "Внезапные траты ударили по планам.", 13, 0, 18),
    ("Хорошее впечатление", "Сим достойно справился со сложной ситуацией.", 2, 10, 30),
    ("Слухи", "О симе начали ходить неприятные разговоры.", 9, -9, 22),
    ("Полезное знакомство", "Новое знакомство открыло перспективы.", -4, 7, 26),
    ("Переутомление", "Темп жизни оказался слишком высоким.", 17, 0, 20),
    ("Время на себя", "Спокойный период помог привести мысли в порядок.", -16, 0, 14),
    ("Сложное решение", "Пришлось выбирать без идеального варианта.", 8, 1, 38),
    ("Уважение окружающих", "Последние поступки сима заметили.", -3, 12, 28),
)


def trigger_event(sim_info):
    if sim_info is None or not eligible(sim_info):
        return None
    state = sim_state(sim_info)
    event = random.choice(EVENTS)
    state["events"] = int(state["events"]) + 1
    state["last_event"] = event[0]
    apply(sim_info, state, event[2], event[3], event[4])
    state["next_event_tick"] = now_ticks() + hours_ticks(event_delay())
    save_data()
    notify(
        "Событие: {}".format(event[0]),
        "{}\n\n{}\n\nСтресс {:+d}\nРепутация {:+d}\nОпыт {:+d}".format(
            sim_name(sim_info), event[1], event[2], event[3], event[4]
        ),
    )
    return event


def scheduler(*_):
    try:
        data = load_data()
        now = now_ticks()
        if not now:
            return
        changed = False
        for sim_info in household_sims():
            if sim_info is None or not eligible(sim_info):
                continue
            state = sim_state(sim_info)
            settings = data["settings"]

            recovery_hours = max(1, int(settings.get("recovery_hours", 6)))
            recovery_tick = hours_ticks(recovery_hours)
            if state["next_recovery_tick"] and now >= int(state["next_recovery_tick"]):
                amount = max(0, int(settings.get("stress_recovery", 2)))
                if amount and int(state["stress"]) > 0:
                    apply(sim_info, state, -amount, 0, 0)
                state["next_recovery_tick"] = now + recovery_tick
                changed = True

            if (
                settings.get("automatic_events", True)
                and state["next_event_tick"]
                and now >= int(state["next_event_tick"])
            ):
                trigger_event(sim_info)
                changed = True

        if changed:
            save_data()
    except Exception:
        pass


def start_scheduler():
    global ALARM
    try:
        if ALARM is not None:
            alarms.cancel_alarm(ALARM)
    except Exception:
        pass
    try:
        span = clock.interval_in_sim_hours(CHECK_HOURS)
        ALARM = alarms.add_alarm(
            ALARM_OWNER,
            span,
            scheduler,
            repeating=True,
            repeating_time_span=span,
        )
    except Exception:
        ALARM = None


def inject(target, name):
    def decorator(new_function):
        original = getattr(target, name)

        @wraps(original)
        def wrapper(*args, **kwargs):
            return new_function(original, *args, **kwargs)

        setattr(target, name, wrapper)
        return new_function
    return decorator


@inject(zone.Zone, "on_loading_screen_animation_finished")
def on_zone_loaded(original, self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    global NOTICE_SHOWN
    load_data(force=True)
    for info in household_sims():
        if info is not None and eligible(info):
            sim_state(info)
    start_scheduler()
    if not NOTICE_SHOWN:
        NOTICE_SHOWN = True
        notify("Life With Consequences", "Мод {} загружен.".format(MOD_VERSION))
    return result


def selected(connection):
    info = active_sim_info()
    if info is None:
        output(connection, "[LWC] Сначала выбери сима.")
        return None, None
    return info, sim_state(info)


@sims4.commands.Command("lwc.help", command_type=sims4.commands.CommandType.Live)
def cmd_help(_connection=None):
    output(_connection, "[LWC] Life With Consequences {} | TS4 {}".format(MOD_VERSION, TARGET_GAME))
    output(_connection, "lwc.status | lwc.event | lwc.stress N | lwc.rep N | lwc.xp N")
    output(_connection, "lwc.auto on/off | lwc.eventhours N | lwc.notifications on/off | lwc.slot")


@sims4.commands.Command("lwc.status", command_type=sims4.commands.CommandType.Live)
def cmd_status(_connection=None):
    info, state = selected(_connection)
    if info is None:
        return
    now = now_ticks()
    hour = max(1, hours_ticks(1))
    remaining = max(0, int(state["next_event_tick"]) - now) // hour
    output(
        _connection,
        "[LWC] {} | Стресс {}/100 ({}) | Репутация {} ({}) | Уровень {}/20 | XP {} | Перки {} | Следующее ~{}ч".format(
            sim_name(info),
            state["stress"],
            stress_stage(state["stress"]),
            state["reputation"],
            reputation_stage(state["reputation"]),
            level_from_xp(state["xp"]),
            state["xp"],
            state["perk_points"],
            remaining,
        ),
    )


@sims4.commands.Command("lwc.event", command_type=sims4.commands.CommandType.Live)
def cmd_event(_connection=None):
    info, state = selected(_connection)
    if info is None:
        return
    event = trigger_event(info)
    output(_connection, "[LWC] {}".format(event[0] if event else "Событие недоступно"))


@sims4.commands.Command("lwc.stress", command_type=sims4.commands.CommandType.Live)
def cmd_stress(amount: int = 0, _connection=None):
    info, state = selected(_connection)
    if info is not None:
        apply(info, state, stress=amount)
        cmd_status(_connection=_connection)


@sims4.commands.Command("lwc.rep", command_type=sims4.commands.CommandType.Live)
def cmd_rep(amount: int = 0, _connection=None):
    info, state = selected(_connection)
    if info is not None:
        apply(info, state, reputation=amount)
        cmd_status(_connection=_connection)


@sims4.commands.Command("lwc.xp", command_type=sims4.commands.CommandType.Live)
def cmd_xp(amount: int = 0, _connection=None):
    info, state = selected(_connection)
    if info is not None:
        apply(info, state, xp=amount)
        cmd_status(_connection=_connection)


@sims4.commands.Command("lwc.auto", command_type=sims4.commands.CommandType.Live)
def cmd_auto(value: str = "", _connection=None):
    value = str(value).lower()
    if value not in ("on", "off"):
        output(_connection, "[LWC] lwc.auto on/off")
        return
    load_data()["settings"]["automatic_events"] = value == "on"
    save_data()
    output(_connection, "[LWC] Автособытия: {}".format(value))


@sims4.commands.Command("lwc.eventhours", command_type=sims4.commands.CommandType.Live)
def cmd_hours(value: int = 72, _connection=None):
    value = max(12, min(336, int(value)))
    data = load_data()
    data["settings"]["event_interval_hours"] = value
    now = now_ticks()
    for state in data["sims"].values():
        if isinstance(state, dict):
            state["next_event_tick"] = now + hours_ticks(event_delay())
    save_data()
    output(_connection, "[LWC] Интервал: ~{} игровых часов.".format(value))


@sims4.commands.Command("lwc.notifications", command_type=sims4.commands.CommandType.Live)
def cmd_notifications(value: str = "", _connection=None):
    value = str(value).lower()
    if value not in ("on", "off"):
        output(_connection, "[LWC] lwc.notifications on/off")
        return
    load_data()["settings"]["notifications"] = value == "on"
    save_data()
    output(_connection, "[LWC] Уведомления: {}".format(value))


@sims4.commands.Command("lwc.slot", command_type=sims4.commands.CommandType.Live)
def cmd_slot(_connection=None):
    output(_connection, "[LWC] {} | {}".format(slot_key(), state_path()))

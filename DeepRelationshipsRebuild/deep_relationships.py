# -*- coding: utf-8 -*-
"""Deep Relationships v0.8 beta: single game runtime, no legacy patches."""
import json
import os
import sys
import traceback
from functools import wraps

VERSION = "0.8.7-safe"
MOD_NAME = "Глубокие отношения"

# The installed script is a zip: both the zip root and its engine subdirectory
# are import locations. Existing pure-Python tests can still import these files.
SCRIPT_PATH = os.path.abspath(__file__)
ZIP_PATH = SCRIPT_PATH.split(".ts4script", 1)[0] + ".ts4script"
if ZIP_PATH + "/engine" not in sys.path:
    sys.path.insert(0, ZIP_PATH + "/engine")

import services
import sims4.resources
import alarms
import date_and_time
from zone import Zone
from game_services import GameServiceManager
from services.persistence_service import PersistenceService
from sims.sim import Sim
from sims4.localization import LocalizationHelperTuning
from interactions.base.super_interaction import SuperInteraction
from interactions.constraints import Anywhere
from event_testing.results import TestResult
from sims4.utils import flexmethod
from ui.ui_dialog import UiDialogOk
from ui.ui_dialog_notification import UiDialogNotification
from relationships.relationship_track import RelationshipTrack
from relationships.relationship_service import RelationshipService
from singletons import DEFAULT

from runtime import RelationshipStore, RelationshipRuntime
import adapter.game as bridge
from adapter.hooks import GameHooks

TUNINGS = {
    "report": 16907167177260101633,
    "discuss": 16907167177260101701,
    "apologize": 16907167177260101702,
    "admit_fault": 16907167177260101703,
    "forgive": 16907167177260101704,
    "not_ready": 16907167177260101705,
    "second_chance": 16907167177260101706,
    "breakup_talk": 16907167177260101721,
    "take_pause": 16907167177260101722,
    "save_relationship": 16907167177260101723,
    "decide_breakup": 16907167177260101724,
}
_ROOT = None
_STORE = RelationshipStore()
_RUNTIME = None
_ALARM = None
_ALARM_OWNER = type("_DeepRelAlarmOwner", (), {})()
_SAVING = False
_STARTUP_NOTIFIED = False


def _root():
    global _ROOT
    if _ROOT is not None:
        return _ROOT
    here = ZIP_PATH
    for _ in range(12):
        here = os.path.dirname(here)
        if os.path.basename(here).lower() == "mods":
            _ROOT = os.path.dirname(here)
            return _ROOT
    _ROOT = os.path.join(os.path.expanduser("~"), "Documents", "Electronic Arts", "The Sims 4")
    return _ROOT


def _data_path(name):
    folder = os.path.join(_root(), "mod_data", "DeepRelationships")
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, name)


def log(message):
    try:
        with open(_data_path("deeprel_v08.log"), "a", encoding="utf-8") as f:
            f.write(str(message) + "\n")
    except Exception:
        pass


def _slot_id():
    # Prefer a positive save slot from either account or PersistenceService.
    # The old v0.8 beta always saw slot 0 on some installations.
    from engine.save_slots import find_save_slot
    try:
        client = services.client_manager().get_first_client()
    except Exception:
        client = None
    try:
        persistence = services.get_persistence_service()
    except Exception:
        persistence = None
    slot, source = find_save_slot(client, persistence)
    return slot


def _sim_info(value):
    return getattr(value, "sim_info", value)


def _sim_id(value):
    try:
        return int(_sim_info(value).sim_id)
    except Exception:
        return 0


def _scores(a, b_id):
    friendship = romance = 0.0
    try:
        friendship = float(a.relationship_tracker.get_relationship_score(b_id, RelationshipTrack.FRIENDSHIP_TRACK))
    except Exception:
        pass
    try:
        romance = float(a.relationship_tracker.get_relationship_score(b_id, RelationshipTrack.ROMANCE_TRACK))
    except Exception:
        pass
    return friendship, romance


def _romantic(a, b_id, romance):
    if romance > 0:
        return True
    try:
        tracker = a.relationship_tracker
        return (int(getattr(tracker, "spouse_sim_id", 0) or 0) == b_id or
                int(getattr(tracker, "fiance_sim_id", 0) or 0) == b_id or
                b_id in getattr(tracker, "steady_sim_ids", ()))
    except Exception:
        return False


def _ensure_pair(a_id, b_id, forced=False):
    if not a_id or not b_id or a_id == b_id:
        return False
    sim_manager = services.sim_info_manager()
    a, b = sim_manager.get(int(a_id)), sim_manager.get(int(b_id))
    if a is None or b is None:
        return False
    for owner, other in ((a, b), (b, a)):
        if _STORE.existing(owner.sim_id, other.sim_id) is not None:
            continue
        friendship, romance = _scores(owner, other.sim_id)
        if not (forced or _romantic(owner, other.sim_id, romance)):
            continue
        r = {
            "source_id": int(owner.sim_id), "target_id": int(other.sim_id),
            "love": max(0.0, min(100.0, romance)),
            "trust": max(0.0, min(100.0, 30 + max(0, friendship)*0.65 + max(0, romance)*0.1)),
            "attachment": max(0.0, min(100.0, 15 + max(0, romance)*0.35 + max(0, friendship)*0.15)),
            "compatibility": max(0.0, min(100.0, 48 + friendship*0.08 + romance*0.06)),
            "satisfaction": max(0.0, min(100.0, 38 + max(0, romance)*0.35 + max(0, friendship)*0.15)),
            "relationship_phase": "active", "breakup_state": "none",
        }
        _STORE._pairs[(r["source_id"], r["target_id"])] = r
        _STORE.dirty = True
        log("PAIR CREATED {} to {}".format(owner.sim_id, other.sim_id))
    return _STORE.existing(a_id, b_id) is not None and _STORE.existing(b_id, a_id) is not None


def _scan():
    hh = services.active_household()
    if hh is None:
        log("HOUSEHOLD UNAVAILABLE")
        return ()
    members = tuple(hh.sim_info_gen())
    for info in members:
        try:
            targets = tuple(info.relationship_tracker.target_sim_gen())
        except Exception:
            targets = ()
        for target in targets:
            b = int(getattr(target, "sim_id", target))
            _ensure_pair(int(info.sim_id), b)
    log("HOUSEHOLD SCANNED {} sims {} directions".format(len(members), len(_STORE._pairs)))
    return tuple(int(s.sim_id) for s in members)


def _load_slot():
    slot = _slot_id()
    if slot == "0":
        log("SAVE SLOT WARNING: unresolved ID 0; read-only legacy fallback")
    if _STORE.slot_id == slot:
        return
    data = {"slots": {}}
    modern = _data_path("deep_relationships_v08_state.json")
    legacy = _data_path("deep_relationships_state.json")
    path = modern if os.path.isfile(modern) else legacy
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        count = _STORE.load_legacy(data, slot)
        log("STATE LOADED slot {} count {} source {}".format(slot, count, os.path.basename(path)))
    except Exception:
        log("STATE LOAD ERROR "+traceback.format_exc())
        # Do not overwrite failed/corrupt state on save.
        _STORE.slot_id = slot
        _STORE._pairs = {}
        _STORE.load_blocked = True


def _write():
    if getattr(_STORE, "load_blocked", False):
        log("SAVE BLOCKED: invalid state must be recovered manually")
        return False
    if _slot_id() == "0":
        log("STATE COMMIT BLOCKED: save slot unresolved (0); preserving existing sidecar")
        return False
    try:
        path = _data_path("deep_relationships_v08_state.json")
        data = {"version": 8, "slots": {}}
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or not isinstance(data.get("slots"), dict):
                raise ValueError("Existing v08 save malformed")
        slot = _slot_id()
        data["slots"][slot] = {"relationships": {
            "{}:{}".format(r["source_id"], r["target_id"]): r
            for r in _STORE.snapshot()
        }}
        temp = path + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp, path)
        _STORE.dirty = False
        log("STATE COMMITTED slot {} records {}".format(slot,len(_STORE._pairs)))
        return True
    except Exception:
        log("SAVE ERROR "+traceback.format_exc())
        return False


def _notify_startup():
    """Once per session, as soon as the active Sim is available."""
    global _STARTUP_NOTIFIED
    if _STARTUP_NOTIFIED:
        return True
    try:
        sim = services.get_active_sim()
        if sim is None:
            log("STARTUP NOTIFICATION DEFERRED: no active Sim")
            return False
        buff_manager = services.get_instance_manager(sims4.resources.Types.BUFF)
        from engine.moodlets import STAGE_BUFFS, EXTRA_BUFF_IDS
        from adapter.game import CUSTOM_BUFFS_ENABLED
        stages = sum(1 for i in STAGE_BUFFS if buff_manager and buff_manager.get(i))
        extras = sum(1 for i in EXTRA_BUFF_IDS if buff_manager and buff_manager.get(i))
        message = ("Мод v{} запущен в безопасном режиме. "
                   "Мудлеты временно отключены; только отчёт отношений. "
                   "Слот: {}.").format(VERSION, _slot_id())
        dialog = UiDialogNotification.TunableFactory().default(
            sim,
            title=lambda *args, **kwargs: LocalizationHelperTuning.get_raw_text(
                "Глубокие отношения — мод активен"),
            text=lambda *args, **kwargs: LocalizationHelperTuning.get_raw_text(message))
        dialog.show_dialog()
        _STARTUP_NOTIFIED = True
        log("STARTUP NOTIFICATION SHOWN version {} buffs {}/{} slot {}".format(
            VERSION, stages, extras, _slot_id()))
        return True
    except Exception:
        log("STARTUP NOTIFICATION FAILED " + traceback.format_exc())
        return False


def _buff_diagnostics(sim_id, stage):
    """Log tuning metadata and instance state, not inferred UI visibility."""
    try:
        from engine.moodlets import desired_ids
        from adapter.game import CUSTOM_BUFFS_ENABLED
        if not CUSTOM_BUFFS_ENABLED:
            return "Мудлеты временно отключены для защиты настроений симов"
        record = _STORE.existing(sim_id, next((
            r["target_id"] for r in _STORE.records()
            if int(r.get("source_id", 0)) == sim_id), 0))
        expected = sorted(desired_ids(stage, record))
        manager = services.get_instance_manager(sims4.resources.Types.BUFF)
        info = services.sim_info_manager().get(sim_id)
        out = []
        for buff_id in expected:
            buff_type = manager.get(buff_id) if manager else None
            if buff_type is None:
                out.append("{}:TUNING_MISSING".format(buff_id))
                continue
            has = bool(info.has_buff(buff_type)) if info is not None else False
            mood = getattr(buff_type, "mood_type", None)
            weight = getattr(buff_type, "mood_weight", None)
            visible = getattr(buff_type, "visible", None)
            icon = getattr(buff_type, "icon", None)
            out.append("{}:active={} visible={} mood={} weight={} icon={}".format(
                buff_id, has, visible, mood, weight, icon is not None))
        result = " ; ".join(out) if out else "нет активных условий"
        log("UI BUFF DIAGNOSTICS sim {} stage {} {}".format(sim_id, stage, result))
        return result
    except Exception:
        log("UI BUFF DIAGNOSTICS ERROR " + traceback.format_exc())
        return "ошибка диагностики — см. журнал"


def _outcome(action, accepted, a, b):
    log("ACTION {} {} -> {} outcome {}".format(action,a,b,accepted))
    try:
        sim = services.get_active_sim()
        dialog = UiDialogNotification.TunableFactory().default(
            sim,
            title=lambda **_: LocalizationHelperTuning.get_raw_text("Глубокие отношения"),
            text=lambda **_: LocalizationHelperTuning.get_raw_text(
                "{}: {}".format(action, "успешно" if accepted else "не удалось")))
        dialog.show_dialog()
    except Exception:
        log("ACTION NOTIFICATION ERROR "+traceback.format_exc())


def _runtime():
    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = RelationshipRuntime(_STORE, bridge, log, outcome=_outcome)
        log("RUNTIME CREATED")
    return _RUNTIME


def _kind(track):
    if track is None or track is DEFAULT:
        return "friendship"
    try:
        if track is RelationshipTrack.ROMANCE_TRACK or track == RelationshipTrack.ROMANCE_TRACK:
            return "romance"
        if track is RelationshipTrack.FRIENDSHIP_TRACK or track == RelationshipTrack.FRIENDSHIP_TRACK:
            return "friendship"
    except Exception:
        pass
    return None


def _score_changed(a,b,kind,delta):
    try:
        _ensure_pair(int(a),int(b),forced=(kind=="romance"))
        _runtime().on_score_changed(int(a),int(b),kind,delta)
    except Exception:
        log("SCORE ERROR "+traceback.format_exc())


def _sync_zone():
    global _ALARM
    try:
        _load_slot()
        _scan()
        _install_ui()
        _runtime().on_zone_ready()
        _notify_startup()
        if _ALARM is not None:
            alarms.cancel_alarm(_ALARM)
        _ALARM = alarms.add_alarm(
            _ALARM_OWNER, date_and_time.create_time_span(minutes=15),
            _tick, repeating=True,
            repeating_time_span=date_and_time.create_time_span(hours=6))
        log("ZONE READY alarm started")
    except Exception:
        log("ZONE ERROR "+traceback.format_exc())


def _tick(_):
    try:
        from engine.lifecycle import tick_record
        for record in _STORE._pairs.values():
            tick_record(record)
        _STORE.dirty=True
        _scan()
        _runtime().on_zone_ready()
        _notify_startup()
    except Exception:
        log("TICK ERROR "+traceback.format_exc())


def execute(action, actor, target):
    try:
        a,b = _sim_id(actor),_sim_id(target)
        if not _ensure_pair(a,b):
            log("ACTION BLOCKED no tracked pair {}".format(action))
            return False
        from engine.availability import action_allowed
        if not action_allowed(action, _STORE.existing(a,b), _STORE.existing(b,a)):
            log("ACTION BLOCKED by stage eligibility {} {} -> {}".format(action,a,b))
            return False
        return _runtime().execute_action(action,a,b)
    except Exception:
        log("ACTION ERROR "+traceback.format_exc())
        return False


def report(actor,target):
    a,b=_sim_id(actor),_sim_id(target)
    if not _ensure_pair(a,b):
        return False
    from engine.stages import selected_stage_for_sim
    first=_STORE.existing(a,b)
    second=_STORE.existing(b,a)
    stage,_=selected_stage_for_sim(a,_STORE.records())
    def details(r):
        return ("Любовь: {love:.0f}\nДоверие: {trust:.0f}\n"
                "Привязанность: {attachment:.0f}\nСовместимость: {compatibility:.0f}\n"
                "Удовлетворённость: {satisfaction:.0f}\nОбиды: {resentment:.1f}").format(
                    **dict({key:float(r.get(key,0) or 0) for key in
                           ("love","trust","attachment","compatibility","satisfaction","resentment")}))
    try:
        sim=getattr(actor,"sim",actor)
        diag = _buff_diagnostics(a, stage)
        log("REPORT DETAIL buff diagnostic {}".format(diag))
        # Keep the regular report readable; long diagnostic strings are
        # written into the log instead of clipping the dialog.
        body="{} → {}\\n{}\\n\\n{} → {}\\n{}\\n\\nСтадия: {}\\nBuff: см. deeprel_v08.log".format(
            a,b,details(first),b,a,details(second),stage or "нет")
        dialog=UiDialogOk.TunableFactory().default(
            sim,
            title=lambda **_:LocalizationHelperTuning.get_raw_text("Наши отношения"),
            text=lambda **_:LocalizationHelperTuning.get_raw_text(body))
        dialog.show_dialog()
        return True
    except Exception:
        log("REPORT ERROR "+traceback.format_exc())
        return False


class _Interaction(SuperInteraction):
    ACTION = None
    NAME = "Глубокие отношения"

    @flexmethod
    def get_name(cls, inst, *args, **kwargs):
        return LocalizationHelperTuning.get_raw_text(cls.NAME)

    @classmethod
    def _test(cls, target, context, **kwargs):
        result=super()._test(target,context,**kwargs)
        if not result:
            return result
        actor=getattr(context,"sim",None)
        try:
            if _sim_id(actor)==_sim_id(target) or not _sim_id(actor) or not _sim_id(target):
                return TestResult(False)
            a, b = _sim_id(actor), _sim_id(target)
            left, right = _STORE.existing(a,b), _STORE.existing(b,a)
            if left is None or right is None:
                return TestResult(False)
            from engine.availability import action_allowed
            if not action_allowed(cls.ACTION, left, right):
                return TestResult(False)
        except Exception:
            return TestResult(False)
        return TestResult.TRUE

    @flexmethod
    def _constraint_gen(cls, inst, sim, target, participant_type, **kwargs):
        yield Anywhere()

    def _run_interaction_gen(self,timeline):
        yield from ()
        if self.ACTION=="report":
            return bool(report(self.sim,self.target))
        return bool(execute(self.ACTION,self.sim,self.target))


class DeepRelationshipViewInteraction(_Interaction):
    ACTION="report"
    NAME="Наши отношения"

class DeepRelDiscussProblemsInteraction(_Interaction):
    ACTION="discuss"
    NAME="Обсудить проблемы"


class DeepRelApologizeInteraction(_Interaction):
    ACTION="apologize"
    NAME="Извиниться"


class DeepRelAdmitFaultInteraction(_Interaction):
    ACTION="admit_fault"
    NAME="Признать вину"


class DeepRelForgiveInteraction(_Interaction):
    ACTION="forgive"
    NAME="Простить"


class DeepRelNotReadyInteraction(_Interaction):
    ACTION="not_ready"
    NAME="Не готов простить"


class DeepRelSecondChanceInteraction(_Interaction):
    ACTION="second_chance"
    NAME="Дать второй шанс"


class DeepRelBreakupTalkInteraction(_Interaction):
    ACTION="breakup_talk"
    NAME="Поговорить о расставании"


class DeepRelTakePauseInteraction(_Interaction):
    ACTION="take_pause"
    NAME="Взять паузу"


class DeepRelSaveRelationshipInteraction(_Interaction):
    ACTION="save_relationship"
    NAME="Попробовать спасти отношения"


class DeepRelDecideBreakupInteraction(_Interaction):
    ACTION="decide_breakup"
    NAME="Решить расстаться"



def _install_ui(sim=None):
    manager=services.affordance_manager()
    if manager is None:
        log("UI ERROR: no affordance manager")
        return
    def attach(s):
        current=tuple(getattr(s,"_super_affordances",()))
        added=0
        # The old action tunings are not loaded by EA in v0.8.6; keep only
        # the known-working report interaction until rebuilt from vanilla.
        for name, guid in TUNINGS.items():
            if name != "report":
                continue
            affordance=manager.get(guid)
            if affordance is None:
                log("UI TUNING MISSING {} {}".format(name,guid))
                continue
            if affordance not in current:
                current += (affordance,)
                added+=1
        if added:
            s._super_affordances=current
        return added
    if sim is not None:
        attach(sim)
        return
    sim_manager=services.sim_info_manager()
    if sim_manager:
        for s in sim_manager.instanced_sims_gen():
            attach(s)
    log("UI SCAN COMPLETE")


def _sim_on_add_original():
    orig=Sim.on_add
    if getattr(orig,"_deeprel08_ui",False):
        return
    @wraps(orig)
    def wrapped(self,*args,**kwargs):
        result=orig(self,*args,**kwargs)
        try:
            _install_ui(self)
        except Exception:
            log("UI ON_ADD ERROR "+traceback.format_exc())
        return result
    wrapped._deeprel08_ui=True
    Sim.on_add=wrapped


def _on_load_hook():
    orig=GameServiceManager.on_all_households_and_sim_infos_loaded
    if getattr(orig,"_deeprel08_load",False):
        return
    @wraps(orig)
    def wrapped(self,*args,**kwargs):
        result=orig(self,*args,**kwargs)
        _STORE.slot_id=None
        _STORE.load_blocked=False
        _load_slot()
        return result
    wrapped._deeprel08_load=True
    GameServiceManager.on_all_households_and_sim_infos_loaded=wrapped


def _on_save_hook():
    orig=PersistenceService.save_game_gen
    if getattr(orig,"_deeprel08_save",False):
        return
    @wraps(orig)
    def wrapped(self,timeline,save_game_data,send_save_message=True,check_cooldown=False):
        _scan()
        result=yield from orig(
            self,timeline,save_game_data,
            send_save_message=send_save_message,check_cooldown=check_cooldown)
        if send_save_message and result is not False and _STORE.slot_id==_slot_id():
            _write()
        return result
    wrapped._deeprel08_save=True
    PersistenceService.save_game_gen=wrapped


def initialize():
    try:
        _runtime()
        GameHooks(
            type("_Proxy",(),{"on_zone_ready":staticmethod(_sync_zone),
                               "on_relationship_changed":staticmethod(bridge.on_relationship_changed)}),
            log
        ).install(Zone,RelationshipService,_kind,_score_changed)
        _sim_on_add_original()
        _on_load_hook()
        _on_save_hook()
        log("V08 INITIALIZED: hooks installed")
    except Exception:
        log("V08 INIT ERROR "+traceback.format_exc())


log("=== Deep Relationships v{} import ===".format(VERSION))
initialize()

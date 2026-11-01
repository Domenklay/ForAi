# -*- coding: utf-8 -*-
"""
Life With Consequences v0.3.1
Target: The Sims 4 1.127.41.1030 DX11
Automatic gameplay build: no console commands required.
"""
import json
import os
import random
import traceback
from functools import wraps

import alarms
import clock
import services
import sims4.commands
import zone

from sims4.localization import LocalizationHelperTuning
from ui.ui_dialog import UiDialogOkCancel
from ui.ui_dialog_notification import UiDialogNotification

MOD_VERSION = "0.3.1"
TARGET_GAME = "1.127.41.1030"
CHECK_INTERVAL_HOURS = 1
FIRST_EVENT_HOURS = 6
NORMAL_EVENT_MIN_HOURS = 60
NORMAL_EVENT_MAX_HOURS = 84

_DATA = None
_SLOT = None
_ALARM = None
_DIALOG_OPEN = False
_START_NOTICE_SHOWN = False

class _AlarmOwner:
    pass

_ALARM_OWNER = _AlarmOwner()

EVENTS = (
    {"title":"Сложный день","text":"На {} свалилось сразу несколько проблем. Как поступить?","ok":"Собраться","cancel":"Пустить всё на самотёк","ok_result":(-4,3,28,"resilient"),"cancel_result":(12,-2,15,"reckless")},
    {"title":"Чужая просьба","text":"Знакомый просит {} о помощи в неудобный момент.","ok":"Помочь","cancel":"Отказать","ok_result":(5,9,30,"reliable"),"cancel_result":(-2,-6,18,"selfish")},
    {"title":"Рискованная возможность","text":"{} замечает шанс получить выгоду, но всё может закончиться неприятностями.","ok":"Рискнуть","cancel":"Не ввязываться","ok_result":(11,1,42,"reckless"),"cancel_result":(-4,2,20,"resilient")},
    {"title":"Неприятные слухи","text":"{} узнаёт, что за спиной распространяют неприятные слухи.","ok":"Спокойно разобраться","cancel":"Устроить скандал","ok_result":(3,7,32,"resilient"),"cancel_result":(14,-10,35,"reckless")},
    {"title":"Найденный кошелёк","text":"{} находит чужой кошелёк. Владелец пока не заметил пропажу.","ok":"Вернуть владельцу","cancel":"Оставить себе","ok_result":(-2,10,34,"reliable"),"cancel_result":(2,-9,28,"selfish")},
    {"title":"Переутомление","text":"{} слишком долго жил(а) в напряжённом темпе.","ok":"Устроить передышку","cancel":"Продолжать через силу","ok_result":(-18,0,18,"resilient"),"cancel_result":(16,1,36,"reckless")},
)
TRAIT_NAMES={"resilient":"Закалённый","reliable":"Надёжный","reckless":"Безрассудный","selfish":"Эгоист"}

def _user_folder():
    home=os.path.expanduser("~")
    candidates=(os.path.join(home,"Documents","Electronic Arts","The Sims 4"),os.path.join(home,"OneDrive","Documents","Electronic Arts","The Sims 4"),os.path.join(home,"OneDrive","Документы","Electronic Arts","The Sims 4"))
    for path in candidates:
        try:
            if os.path.isdir(path): return path
        except Exception: pass
    return candidates[0]

def _root(): return os.path.join(_user_folder(),"mod_data","LifeWithConsequences")
def _ensure_root():
    try: os.makedirs(_root(),exist_ok=True); return True
    except Exception: return False

def _log(message):
    try:
        if not _ensure_root(): return
        with open(os.path.join(_root(),"lwc.log"),"a",encoding="utf-8") as fp: fp.write("[v{}] {}\n".format(MOD_VERSION,message))
    except Exception: pass

def _log_exception(where): _log("{}\n{}".format(where,traceback.format_exc()))

def _slot_key():
    try:
        client=services.client_manager().get_first_client(); account=getattr(client,"account",None) if client is not None else None; value=getattr(account,"save_slot_id",None) if account is not None else None
        if value is not None: return "Slot_{:08X}".format(int(value))
    except Exception: pass
    return "CurrentSave"

def _state_path(slot=None): return os.path.join(_root(),"slots",slot or _slot_key(),"state.json")
def _default_data(): return {"version":MOD_VERSION,"sims":{}}

def _load(force=False):
    global _DATA,_SLOT
    slot=_slot_key()
    if not force and _DATA is not None and _SLOT==slot: return _DATA
    _SLOT=slot; path=_state_path(slot)
    try:
        with open(path,"r",encoding="utf-8") as fp: raw=json.load(fp)
        if not isinstance(raw,dict): raw={}
    except Exception: raw={}
    data=_default_data()
    if isinstance(raw.get("sims"),dict): data["sims"]=raw["sims"]
    _DATA=data; _save(); return _DATA

def _save():
    if _DATA is None: return
    try:
        path=_state_path(_SLOT or _slot_key()); os.makedirs(os.path.dirname(path),exist_ok=True); tmp=path+".tmp"
        with open(tmp,"w",encoding="utf-8") as fp: json.dump(_DATA,fp,ensure_ascii=False,indent=2,sort_keys=True)
        os.replace(tmp,path)
    except Exception: _log_exception("save failed")

def _active_sim():
    try:
        client=services.client_manager().get_first_client(); return getattr(client,"active_sim",None) if client is not None else None
    except Exception: return None

def _active_sim_info():
    sim=_active_sim(); return getattr(sim,"sim_info",None) if sim is not None else None

def _household_infos():
    try:
        household=services.active_household()
        if household is not None:
            generator=getattr(household,"sim_info_gen",None)
            if generator is not None: return list(generator())
    except Exception: pass
    info=_active_sim_info(); return [info] if info is not None else []

def _sim_id(info):
    if info is None: return None
    value=getattr(info,"sim_id",None); return value if value is not None else getattr(info,"id",None)

def _sim_name(info): return "{} {}".format(getattr(info,"first_name",""),getattr(info,"last_name","")).strip() or "Сим"

def _eligible(info):
    if info is None: return False
    try:
        value=getattr(info,"is_teen_or_older"); return bool(value() if callable(value) else value)
    except Exception: return True

def _now_ticks():
    try:
        service=services.time_service(); return int(service.sim_now.absolute_ticks()) if service is not None else 0
    except Exception: return 0

def _hours_ticks(hours):
    try: return int(clock.interval_in_sim_hours(float(hours)).in_ticks())
    except Exception: return 0

def _level(xp):
    xp=max(0,int(xp)); level=1
    while level<20:
        n=level; required=50*n*(n+1)
        if xp<required: break
        level+=1
    return level

def _stage(stress):
    stress=int(stress)
    if stress>=100:return "Кризис"
    if stress>=75:return "На грани"
    if stress>=50:return "Сильное напряжение"
    if stress>=25:return "Напряжение"
    return "Спокойствие"

def _new_state(info):
    now=_now_ticks()
    return {"name":_sim_name(info),"stress":0,"reputation":0,"xp":0,"perk_points":0,"events":0,"last_event":"","traits":{},"next_event_tick":now+_hours_ticks(FIRST_EVENT_HOURS) if now else 0,"next_recovery_tick":now+_hours_ticks(6) if now else 0,"first_event_pending":True}

def _state(info):
    data=_load(); key=str(_sim_id(info)); state=data["sims"].get(key)
    if not isinstance(state,dict): state=_new_state(info); data["sims"][key]=state
    defaults=_new_state(info)
    for k,v in defaults.items(): state.setdefault(k,v)
    state["name"]=_sim_name(info); now=_now_ticks()
    if now:
        if int(state.get("next_event_tick",0) or 0)<=0: state["next_event_tick"]=now+_hours_ticks(FIRST_EVENT_HOURS)
        if int(state.get("next_recovery_tick",0) or 0)<=0: state["next_recovery_tick"]=now+_hours_ticks(6)
    _save(); return state

def _raw(text): return LocalizationHelperTuning.get_raw_text(str(text))

def _notify(title,text):
    try:
        info=_active_sim_info()
        if info is None: _log("notification skipped: no active Sim"); return False
        dialog=UiDialogNotification.TunableFactory().default(info,title=lambda *_,**__: _raw(title),text=lambda *_,**__: _raw(text)); dialog.show_dialog(); return True
    except Exception: _log_exception("notification failed"); return False

def _trait_points(state,key): return int(state.setdefault("traits",{}).get(key,0))
def _grant_trait_progress(info,state,key,amount=1):
    traits=state.setdefault("traits",{}); old=int(traits.get(key,0)); new=old+int(amount); traits[key]=new
    if old<3<=new: _notify("Новая жизненная черта","{} сформировал(а) черту «{}».".format(_sim_name(info),TRAIT_NAMES.get(key,key)))

def _apply_result(info,state,result):
    stress_delta,rep_delta,xp_delta,tendency=result
    if stress_delta>0 and _trait_points(state,"resilient")>=3: stress_delta=max(1,int(round(stress_delta*0.75)))
    if tendency=="reckless" and _trait_points(state,"reckless")>=3:
        xp_delta=int(round(xp_delta*1.2))
        if stress_delta>0: stress_delta+=2
    old_level=_level(state["xp"]); old_stage=_stage(state["stress"])
    state["stress"]=max(0,min(100,int(state["stress"])+int(stress_delta))); state["reputation"]=max(-100,min(100,int(state["reputation"])+int(rep_delta))); state["xp"]=max(0,int(state["xp"])+int(xp_delta)); _grant_trait_progress(info,state,tendency,1)
    new_level=_level(state["xp"]); new_stage=_stage(state["stress"])
    if new_level>old_level:
        gained=new_level-old_level; state["perk_points"]=int(state.get("perk_points",0))+gained; _notify("Новый жизненный уровень","{} достиг(ла) уровня {}. Получено очков перков: {}.".format(_sim_name(info),new_level,gained))
    if new_stage!=old_stage: _notify("Стресс: {}".format(new_stage),"{} — стресс {}/100.".format(_sim_name(info),state["stress"]))
    _save(); return stress_delta,rep_delta,xp_delta

def _schedule_next(state):
    now=_now_ticks(); delay=random.randint(NORMAL_EVENT_MIN_HOURS,NORMAL_EVENT_MAX_HOURS); state["next_event_tick"]=now+_hours_ticks(delay); state["first_event_pending"]=False; _save(); return delay

def _finish_event(info,state,event,result,choice_text):
    applied=_apply_result(info,state,result); state["events"]=int(state.get("events",0))+1; state["last_event"]=event["title"]; delay=_schedule_next(state)
    _notify("Последствия решения","{}\n\nСтресс {:+d}\nРепутация {:+d}\nОпыт {:+d}\n\nСледующее жизненное событие примерно через {} игровых ч.".format(choice_text,applied[0],applied[1],applied[2],delay))

def _show_event(info):
    global _DIALOG_OPEN
    if _DIALOG_OPEN:return False
    state=_state(info); event=random.choice(EVENTS); name=_sim_name(info); title=event["title"]; text=event["text"].format(name)
    try:
        dialog=UiDialogOkCancel.TunableFactory().default(info,title=lambda *_,**__: _raw("Жизненное событие: {}".format(title)),text=lambda *_,**__: _raw(text),text_ok=lambda *_,**__: _raw(event["ok"]),text_cancel=lambda *_,**__: _raw(event["cancel"])); _DIALOG_OPEN=True
        def _selected(result_dialog):
            global _DIALOG_OPEN
            try:
                if result_dialog.accepted: _finish_event(info,state,event,event["ok_result"],event["ok"])
                else: _finish_event(info,state,event,event["cancel_result"],event["cancel"])
            except Exception: _log_exception("event result callback failed"); _schedule_next(state)
            finally: _DIALOG_OPEN=False
        dialog.add_listener(_selected); dialog.show_dialog(); _log("event dialog shown for {}: {}".format(name,title)); return True
    except Exception:
        _DIALOG_OPEN=False; _log_exception("event dialog failed"); _notify("Life With Consequences — ошибка события","Не удалось открыть окно жизненного события. Подробности записаны в lwc.log."); state["next_event_tick"]=_now_ticks()+_hours_ticks(3); _save(); return False

def _scheduler(*_):
    try:
        now=_now_ticks()
        if now<=0: _log("scheduler tick skipped: sim time unavailable"); return
        active=_active_sim_info(); active_id=_sim_id(active)
        for info in _household_infos():
            if not _eligible(info): continue
            state=_state(info); next_recovery=int(state.get("next_recovery_tick",0) or 0)
            if next_recovery and now>=next_recovery:
                if int(state["stress"])>0: state["stress"]=max(0,int(state["stress"])-2)
                state["next_recovery_tick"]=now+_hours_ticks(6); _save()
            next_event=int(state.get("next_event_tick",0) or 0)
            if next_event and now>=next_event and _sim_id(info)==active_id: _show_event(info); break
    except Exception: _log_exception("scheduler callback failed")

def _start_scheduler():
    global _ALARM
    try:
        if _ALARM is not None: alarms.cancel_alarm(_ALARM)
    except Exception: pass
    _ALARM=None
    try:
        span=clock.interval_in_sim_hours(CHECK_INTERVAL_HOURS); _ALARM=alarms.add_alarm(_ALARM_OWNER,span,_scheduler,repeating=True,repeating_time_span=span); _log("scheduler started; interval={} sim hour".format(CHECK_INTERVAL_HOURS)); return True
    except Exception: _log_exception("scheduler start failed"); return False

def _inject(target,name):
    def decorator(replacement):
        original=getattr(target,name)
        @wraps(original)
        def wrapper(*args,**kwargs): return replacement(original,*args,**kwargs)
        setattr(target,name,wrapper); return replacement
    return decorator

@_inject(zone.Zone,"on_loading_screen_animation_finished")
def _zone_loaded(original,self,*args,**kwargs):
    result=original(self,*args,**kwargs); global _START_NOTICE_SHOWN
    try:
        _load(force=True); active_info=_active_sim_info()
        if active_info is not None and _eligible(active_info):
            state=_state(active_info); now=_now_ticks()
            if int(state.get("events",0))==0: state["first_event_pending"]=True; state["next_event_tick"]=now+_hours_ticks(FIRST_EVENT_HOURS); _save()
        started=_start_scheduler()
        if not _START_NOTICE_SHOWN:
            _START_NOTICE_SHOWN=True
            if started: _notify("Life With Consequences v{}".format(MOD_VERSION),"Мод запущен. Планировщик активен.\nПервое жизненное событие должно появиться примерно через {} игровых часов.".format(FIRST_EVENT_HOURS))
            else: _notify("Life With Consequences v{}".format(MOD_VERSION),"Мод загрузился, но планировщик не запустился. Подробности записаны в mod_data/LifeWithConsequences/lwc.log.")
    except Exception: _log_exception("zone initialization failed"); _notify("Life With Consequences v{}".format(MOD_VERSION),"Ошибка инициализации. Проверьте mod_data/LifeWithConsequences/lwc.log.")
    return result

@sims4.commands.Command("lwc.testevent",command_type=sims4.commands.CommandType.Live)
def _cmd_testevent(_connection=None):
    info=_active_sim_info()
    if info is not None:_show_event(info)

@sims4.commands.Command("lwc.status",command_type=sims4.commands.CommandType.Live)
def _cmd_status(_connection=None):
    info=_active_sim_info()
    if info is None:return
    state=_state(info)
    try:
        out=sims4.commands.CheatOutput(_connection); now=_now_ticks(); one_hour=max(1,_hours_ticks(1)); left=max(0,int(state["next_event_tick"])-now)//one_hour; out("[LWC {}] {} | stress={} | rep={} | xp={} | events={} | next~{}h".format(MOD_VERSION,_sim_name(info),state["stress"],state["reputation"],state["xp"],state["events"],left))
    except Exception: pass

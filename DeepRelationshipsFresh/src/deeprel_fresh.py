# -*- coding: utf-8 -*-
"""Fresh Sims 4 relationship controller. Never accesses buffs or mood UI."""
import json, os, traceback
from functools import wraps
import services
from zone import Zone
from sims.sim import Sim
from sims4.utils import flexmethod
from sims4.localization import LocalizationHelperTuning
from interactions.base.super_interaction import SuperInteraction
from interactions.constraints import Anywhere
from event_testing.results import TestResult
from ui.ui_dialog import UiDialogOk
from drfresh_model import pair_key, default_pair, stage_of, eligible, apply

VERSION="1.0.0-alpha"
ROOT=os.path.join(os.path.expanduser("~"),"Documents","Electronic Arts","The Sims 4","mod_data","DeepRelationshipsFresh")
_STATE={"slot":None,"pairs":{}}
_NOTICE=False
_IDS={key:17702810370001000000+i for i,key in enumerate(
    ("report","talk","complain","apologize","pause","reconcile","breakup"),1)}
def log(msg):
    try:
        if not os.path.isdir(ROOT):os.makedirs(ROOT)
        with open(os.path.join(ROOT,"fresh.log"),"a",encoding="utf-8") as f:f.write(str(msg)+"\n")
    except Exception:pass
def slot_id():
    try:
        client=services.client_manager().get_first_client()
        persistence=services.get_persistence_service()
        vals=[getattr(getattr(client,"account",None),"save_slot_id",None),
              getattr(client,"save_slot_id",None)]
        vals.extend(getattr(persistence,n,None) for n in
                    ("save_slot_id","_save_slot_id","current_save_slot_id"))
        for val in vals:
            try:
                if int(val)>0:return str(int(val))
            except (ValueError,TypeError,OverflowError):pass
    except Exception:log("SLOT ERROR "+traceback.format_exc())
    return None
def path():
    slot=slot_id()
    return os.path.join(ROOT,"slot_"+slot+".json") if slot else None
def load():
    filename=path()
    if not filename:
        _STATE.update(slot=None,pairs={})
        log("READ ONLY unresolved save slot")
        return
    slot=slot_id()
    if _STATE["slot"]==slot:return
    pairs={}
    try:
        if os.path.isfile(filename):
            with open(filename,"r",encoding="utf-8") as f:data=json.load(f)
            if data.get("schema")==1 and isinstance(data.get("pairs"),dict):
                pairs=data["pairs"]
    except Exception:log("LOAD ERROR "+traceback.format_exc())
    _STATE.update(slot=slot,pairs=pairs)
    log("STATE LOADED slot %s pairs %d"%(slot,len(pairs)))
def save():
    filename=path()
    if not filename or _STATE["slot"]!=slot_id():
        log("SAVE BLOCKED unknown slot");return False
    try:
        if not os.path.isdir(ROOT):os.makedirs(ROOT)
        tmp=filename+".tmp"
        with open(tmp,"w",encoding="utf-8") as f:
            json.dump({"schema":1,"pairs":_STATE["pairs"]},f,ensure_ascii=False)
        os.replace(tmp,filename)
        log("SAVED slot "+_STATE["slot"])
        return True
    except Exception:
        log("SAVE ERROR "+traceback.format_exc());return False
def sim_id(sim):
    try:return int(getattr(sim,"sim_info",sim).sim_id)
    except Exception:return 0
def adult_pair(a,b):
    def adult(sim):
        info=getattr(sim,"sim_info",sim)
        return bool(any(getattr(info,name,False) for name in
                        ("is_young_adult","is_adult","is_elder")))
    return adult(a) and adult(b)
def pair(a,b,create=False):
    a,b=sim_id(a),sim_id(b)
    try:key=pair_key(a,b)
    except Exception:return None
    if _STATE["slot"] is None:return None if create else default_pair(a,b)
    result=_STATE["pairs"].get(key)
    if result is None and create:
        result=default_pair(a,b)
        _STATE["pairs"][key]=result
    return result if result is not None else default_pair(a,b)
def show_dialog(sim,title,text):
    try:
        dialog=UiDialogOk.TunableFactory().default(
            sim,title=lambda **_:LocalizationHelperTuning.get_raw_text(title),
            text=lambda **_:LocalizationHelperTuning.get_raw_text(text))
        dialog.show_dialog()
        return True
    except Exception:
        log("DIALOG ERROR "+traceback.format_exc());return False
def report(a,b):
    p=pair(a,b)
    if not p:return False
    labels={"steady":"Спокойные","tension":"Напряжение","conflict":"Конфликт",
            "pause":"Пауза","breakup":"Расставание"}
    text=("Стадия: %s\nДоверие: %s\nБлизость: %s\nОбиды: %s\n\n"
          "Мудлеты отключены в этой тестовой версии.")%(
        labels.get(stage_of(p),"?"),p["trust"],p["closeness"],p["resentment"])
    return show_dialog(a,"Глубокие отношения",text)
def execute(a,b,action):
    p=pair(a,b)
    if p is None or not eligible(action,p,adult_pair(a,b)):return False
    p=pair(a,b,create=True)
    if p is None or not apply(p,action,adult_pair(a,b)):return False
    save()
    log("ACTION %s pair %s stage %s"%(action,pair_key(sim_id(a),sim_id(b)),stage_of(p)))
    return show_dialog(a,"Глубокие отношения","Действие выполнено.\nСтадия: "+stage_of(p))

class _Base(SuperInteraction):
    ACTION="report"
    TITLE="Наши отношения"
    @flexmethod
    def get_name(cls,inst,*args,**kwargs):
        return LocalizationHelperTuning.get_raw_text(cls.TITLE)
    @classmethod
    def _test(cls,target,context,**kwargs):
        base=super()._test(target,context,**kwargs)
        if not base:return base
        a=getattr(context,"sim",None)
        if a is None or target is None or sim_id(a)==sim_id(target):
            return TestResult(False)
        p=pair(a,target)
        return TestResult.TRUE if p is not None and eligible(
            cls.ACTION,p,adult_pair(a,target)) else TestResult(False)
    @flexmethod
    def _constraint_gen(cls,inst,sim,target,participant_type,**kwargs):
        yield Anywhere()
    def _run_interaction_gen(self,timeline):
        yield from ()
        if self.ACTION=="report":return report(self.sim,self.target)
        return execute(self.sim,self.target,self.ACTION)

class DeepFreshReport(_Base):
    ACTION="report"
    TITLE="Наши отношения"
class DeepFreshTalk(_Base):
    ACTION="talk"
    TITLE="Поговорить по душам"
class DeepFreshComplain(_Base):
    ACTION="complain"
    TITLE="Высказать недовольство"
class DeepFreshApologize(_Base):
    ACTION="apologize"
    TITLE="Извиниться"
class DeepFreshPause(_Base):
    ACTION="pause"
    TITLE="Взять паузу"
class DeepFreshReconcile(_Base):
    ACTION="reconcile"
    TITLE="Примириться"
class DeepFreshBreakup(_Base):
    ACTION="breakup"
    TITLE="Решить расстаться"

def zone_ready():
    global _NOTICE
    try:
        load()
        manager=services.affordance_manager()
        if manager:
            entries=[manager.get(guid) for guid in _IDS.values()]
            missing=[name for name,guid in _IDS.items() if manager.get(guid) is None]
            log("TUNINGS 7 loaded, missing "+str(missing))
            if not missing:
                for sim in services.sim_info_manager().instanced_sims_gen():
                    current=tuple(getattr(sim,"_super_affordances",()))
                    updated=current+tuple(x for x in entries if x not in current)
                    if current!=updated:sim._super_affordances=updated
        if not _NOTICE:
            active=services.get_active_sim()
            if active:
                show_dialog(active,"Deep Relationships Fresh",
                            "Новая система отношений загружена. Мудлеты отключены.")
                _NOTICE=True
        log("ZONE READY")
    except Exception:log("ZONE ERROR "+traceback.format_exc())
def initialize():
    original=Zone.on_loading_screen_animation_finished
    if getattr(original,"_deepfresh",False):return
    @wraps(original)
    def hook(self,*args,**kwargs):
        value=original(self,*args,**kwargs)
        zone_ready()
        return value
    hook._deepfresh=True
    Zone.on_loading_screen_animation_finished=hook
    log("INIT version "+VERSION)
initialize()

# -*- coding: utf-8 -*-
"""Life With Consequences — Family & Relationships v0.7.0.
Target: The Sims 4 1.127.41.1030 DX11 / Python 3.7.
Runs next to LifeWithConsequences 0.6.5 and uses its own state file.
"""
import json, os, random, traceback
from functools import wraps
import alarms, date_and_time, services, sims4.commands, sims4.log, zone
from services.persistence_service import PersistenceService
from sims4.localization import LocalizationHelperTuning
from ui.ui_dialog_notification import UiDialogNotification
try:
    from distributor.shared_messages import IconInfoData
except Exception:
    IconInfoData = None

VERSION='0.7.0'; TARGET='1.127.41.1030 DX11'; STATE_FILE='family_state.json'
COOLDOWN_MIN=3; COOLDOWN_MAX=5; MAX_MEMORIES=12
log=sims4.log.Logger('LWC_Family', default_owner='LifeWithConsequences')
STATE={'version':1,'slots':{}}; LOADED=False; ALARM=None; START_NOTICE=False
class _Owner: pass
OWNER=_Owner()

def inject_to(obj,name):
    def deco(new):
        old=getattr(obj,name)
        @wraps(old)
        def wrapped(*a,**k): return new(old,*a,**k)
        setattr(obj,name,wrapped); return new
    return deco

def clamp(v,lo=0.0,hi=100.0):
    try: return max(lo,min(hi,float(v)))
    except Exception: return lo

def client():
    try: return services.client_manager().get_first_client()
    except Exception: return None

def household():
    c=client(); return getattr(c,'household',None) if c else None

def slot_id():
    c=client()
    try: return str(int(c.account.save_slot_id or 0)) if c else '0'
    except Exception: return '0'

def ts4_root():
    try:
        p=os.path.abspath(__file__); low=p.lower(); m='.ts4script'; i=low.find(m)
        if i>=0: p=p[:i+len(m)]
        p=os.path.dirname(p)
        for _ in range(8):
            if os.path.basename(p).lower()=='mods': return os.path.dirname(p)
            q=os.path.dirname(p)
            if q==p: break
            p=q
    except Exception: pass
    try: return os.path.join(os.path.expanduser('~'),'Documents','Electronic Arts','The Sims 4')
    except Exception: return None

def state_path():
    root=ts4_root()
    if not root: return None
    d=os.path.join(root,'mod_data','LifeWithConsequences')
    try:
        if not os.path.isdir(d): os.makedirs(d)
        return os.path.join(d,STATE_FILE)
    except Exception:
        log.exception('state folder'); return None

def load_state():
    global STATE,LOADED
    if LOADED: return
    LOADED=True; p=state_path()
    if not p or not os.path.isfile(p): return
    try:
        with open(p,'r',encoding='utf-8') as f: data=json.load(f)
        if isinstance(data,dict) and isinstance(data.get('slots'),dict): STATE=data
    except Exception: log.exception('load family state')

def save_state():
    load_state(); p=state_path()
    if not p: return
    try:
        t=p+'.tmp'
        with open(t,'w',encoding='utf-8') as f: json.dump(STATE,f,ensure_ascii=False,indent=2,sort_keys=True)
        try: os.replace(t,p)
        except AttributeError:
            if os.path.isfile(p): os.remove(p)
            os.rename(t,p)
    except Exception: log.exception('save family state')

def hstate(hh):
    load_state(); s=STATE.setdefault('slots',{}).setdefault(slot_id(),{}).setdefault('households',{})
    h=s.setdefault(str(getattr(hh,'id',0) or 0),{})
    h.setdefault('pairs',{}); h.setdefault('roles',{}); h.setdefault('history',[]); return h

def day():
    try: return int(services.time_service().sim_now.absolute_days())
    except Exception: return 0

def name(s):
    try:
        if s.full_name: return str(s.full_name)
    except Exception: pass
    return ('{} {}'.format(getattr(s,'first_name','') or '',getattr(s,'last_name','') or '')).strip() or 'Сим'

def sims(hh):
    try: out=list(hh.sim_info_gen())
    except Exception:
        try: out=list(getattr(hh,'_sim_infos',()))
        except Exception: out=[]
    out=[x for x in out if x is not None]
    try: out.sort(key=lambda x:int(x.sim_id))
    except Exception: pass
    return out

def parents(s):
    try: return set(int(x) for x in s.genealogy.get_parent_sim_ids_gen())
    except Exception: return set()

def ptype(a,b):
    try:
        if a.spouse_sim_id==b.sim_id or b.spouse_sim_id==a.sim_id: return 'spouse'
    except Exception: pass
    ap,bp=parents(a),parents(b)
    if a.sim_id in bp or b.sim_id in ap: return 'parent_child'
    if ap and bp and ap.intersection(bp): return 'siblings'
    return 'household'

def rel(a,b):
    try: return max(-100.0,min(100.0,float(a.relationship_tracker.get_relationship_score(b.sim_id))))
    except Exception: return 0.0

def add_rel(a,b,n):
    try: a.relationship_tracker.add_relationship_score(b.sim_id,float(n))
    except Exception: log.exception('rel a-b')
    try: b.relationship_tracker.add_relationship_score(a.sim_id,float(n))
    except Exception: log.exception('rel b-a')

def key(a,b):
    x,y=int(a.sim_id),int(b.sim_id); return '{}:{}'.format(min(x,y),max(x,y))

def pair_state(h,a,b,score,typ):
    k=key(a,b); p=h['pairs'].get(k)
    if p is None:
        close=clamp((score+100.0)/2.0)
        p={'a':int(a.sim_id),'b':int(b.sim_id),'type':typ,'closeness':round(close,2),
           'trust':round(clamp(close+(8 if typ in ('spouse','parent_child') else 0)),2),
           'tension':round(clamp(100-close),2),
           'attachment':round(clamp(close+(15 if typ in ('spouse','parent_child') else (8 if typ=='siblings' else 0))),2),
           'last_friendship':round(score,2),'memories':[]}
        h['pairs'][k]=p
    p['type']=typ; p.setdefault('memories',[]); return p

def memory(p,kind,text,weight,d):
    p['memories'].insert(0,{'kind':kind,'text':text,'weight':float(weight),'day':int(d)})
    del p['memories'][MAX_MEMORIES:]

def update_pair(p,score,d):
    kept=[]; pos=neg=0.0
    for m in p.get('memories',[]):
        try:
            age=max(0,d-int(m.get('day',d))); eff=float(m.get('weight',0))*(0.975**age)
            if abs(eff)>=0.7 or age<=7:
                m=dict(m); m['effective_weight']=round(eff,2); kept.append(m)
                if eff>=0: pos+=eff
                else: neg+=abs(eff)
        except Exception: pass
    p['memories']=kept[:MAX_MEMORIES]
    old=float(p.get('last_friendship',score)); delta=score-old; target=clamp((score+100)/2)
    close=clamp(float(p.get('closeness',target))*.70+target*.30)
    trust=clamp(float(p.get('trust',close))+delta*.14+min(1.5,pos*.015)-min(1.8,neg*.020))
    tension=float(p.get('tension',100-close))+max(0,-delta)*.20-max(0,delta)*.12+min(1.5,neg*.018)-min(1,pos*.012)
    if score>=30: tension-=.8
    attach=float(p.get('attachment',close))+(close-float(p.get('attachment',close)))*.08
    if p.get('type') in ('spouse','parent_child'): attach+=.25
    p.update(closeness=round(close,2),trust=round(clamp(trust),2),tension=round(clamp(tension),2),
             attachment=round(clamp(attach),2),last_friendship=round(score,2))

def notify(title,text):
    try:
        c=client(); sim=c.active_sim if c else None
        if sim is None: return
        n=UiDialogNotification.TunableFactory().default(sim,
            title=lambda **_:LocalizationHelperTuning.get_raw_text(str(title)),
            text=lambda **_:LocalizationHelperTuning.get_raw_text(str(text)))
        if IconInfoData is not None: n.show_dialog(icon_override=IconInfoData(obj_instance=sim))
        else: n.show_dialog()
    except Exception: log.exception('notification')

def by_id(ss,i):
    try: i=int(i)
    except Exception: return None
    for s in ss:
        try:
            if int(s.sim_id)==i: return s
        except Exception: pass
    return None

def roles(h,ss):
    if not ss: h['roles']={}; return
    rows=[]
    for s in ss:
        scores=[]; links=0
        for o in ss:
            if o is s: continue
            scores.append(rel(s,o))
            if ptype(s,o) in ('spouse','parent_child','siblings'): links+=1
        avg=sum(scores)/len(scores) if scores else 0
        rows.append((s,avg,links))
    h['roles']={'head':int(max(rows,key=lambda x:(x[2],x[1]))[0].sim_id),
                'peacemaker':int(max(rows,key=lambda x:x[1])[0].sim_id),
                'black_sheep':int(min(rows,key=lambda x:x[1])[0].sim_id)}

def apply_story(rec,d,kind,title,text,delta=0,tension=0,trust=0,weight=0):
    a,b,p=rec['a'],rec['b'],rec['p']
    if delta: add_rel(a,b,delta)
    p['tension']=round(clamp(float(p.get('tension',0))+tension),2)
    p['trust']=round(clamp(float(p.get('trust',50))+trust),2)
    memory(p,kind,text,weight,d)
    return title,text

def story(h,ss,recs,d):
    childmap={}
    for ch in ss:
        for pid in parents(ch):
            par=by_id(ss,pid)
            if par: childmap.setdefault(int(par.sim_id),[]).append(ch)
    fav=[]
    for pid,ch in childmap.items():
        if len(ch)<2: continue
        par=by_id(ss,pid); ranked=sorted([(x,rel(par,x)) for x in ch],key=lambda z:z[1])
        if ranked[-1][1]-ranked[0][1]>=25: fav.append((par,ranked[-1][0],ranked[0][0]))
    if fav and random.random()<.55:
        par,favorite,over=random.choice(fav); rec=next((r for r in recs if r['k']==key(par,over)),None)
        if rec:
            return apply_story(rec,d,'favorite_child','Любимый ребёнок?',
                '{} замечает, что {} и {} заметно ближе. Ощущение несправедливости начинает копиться.'.format(name(over),name(par),name(favorite)),0,10,-6,-10)
    bad_sp=[r for r in recs if r['p']['type']=='spouse' and (r['p']['tension']>=48 or r['p']['closeness']<=42)]
    bad_pc=[r for r in recs if r['p']['type']=='parent_child' and (r['p']['tension']>=55 or r['p']['closeness']<42)]
    bad_si=[r for r in recs if r['p']['type']=='siblings' and (r['p']['tension']>=50 or r['p']['closeness']<45)]
    recon=[r for r in recs if r['p']['type']=='spouse' and 28<=r['p']['tension']<=68 and r['p']['trust']>=48]
    mid_sp=[r for r in recs if r['p']['type']=='spouse' and 42<=r['p']['closeness']<=72 and 25<=r['p']['tension']<=55]
    good_si=[r for r in recs if r['p']['type']=='siblings' and r['p']['closeness']>=65 and r['p']['trust']>=55]
    good=[r for r in recs if r['p']['type'] in ('spouse','parent_child','siblings') and r['p']['closeness']>=55]
    groups=[]
    if bad_sp: groups.append(('cold',bad_sp))
    if bad_pc: groups.append(('gen',bad_pc))
    if bad_si: groups.append(('sibbad',bad_si))
    if recon: groups.append(('recon',recon))
    if mid_sp: groups.append(('attention',mid_sp))
    if good_si: groups.append(('sibgood',good_si))
    if good: groups.append(('support',good))
    if not groups:
        direct=[r for r in recs if r['p']['type'] in ('spouse','parent_child','siblings')]
        if not direct: return None
        r=random.choice(direct); r['p']['tension']=round(clamp(r['p']['tension']-3),2); r['p']['closeness']=round(clamp(r['p']['closeness']+1),2)
        memory(r['p'],'quiet','Спокойное совместное время немного сблизило их.',3,d)
        return 'Тихий семейный день','{} и {} обошлись сегодня без драмы. Такие спокойные дни тоже укрепляют отношения.'.format(name(r['a']),name(r['b']))
    kind,group=random.choice(groups); r=random.choice(group); a,b=r['a'],r['b']
    if kind=='cold': return apply_story(r,d,'cold_marriage','Остывший брак','{} и {} всё чаще чувствуют дистанцию между собой.'.format(name(a),name(b)),-3,8,-4,-8)
    if kind=='gen': return apply_story(r,d,'generation_conflict','Конфликт поколений','{} и {} всё сложнее слышать друг друга. Обычный разговор быстро превращается в спор.'.format(name(a),name(b)),-2,8,-3,-7)
    if kind=='sibbad': return apply_story(r,d,'sibling_rivalry','Соперничество','{} и {} снова начали сравнивать себя друг с другом. Конкуренция становится личной.'.format(name(a),name(b)),-3,8,0,-7)
    if kind=='recon': return apply_story(r,d,'reconciliation','Шаг к примирению','{} и {} нашли время для честного разговора. Старое напряжение стало слабее.'.format(name(a),name(b)),4,-10,6,10)
    if kind=='attention': return apply_story(r,d,'lack_attention','Не хватает внимания','У {} и {} всё вроде нормально, но один всё чаще чувствует себя оставленным без внимания.'.format(name(a),name(b)),0,6,-2,-5)
    if kind=='sibgood': return apply_story(r,d,'sibling_bond','Крепкая связь','{} и {} всё чаще оказываются на одной стороне. Между ними формируется настоящая поддержка.'.format(name(a),name(b)),2,-5,4,7)
    return apply_story(r,d,'family_support','Семья рядом','{} и {} напомнили друг другу, что в трудный момент могут рассчитывать на семью.'.format(name(a),name(b)),2,-6,5,8)

def scan(show_notice=False,allow_story=True):
    global START_NOTICE
    hh=household()
    if hh is None: return
    ss=sims(hh)
    if len(ss)<2: return
    h=hstate(hh); d=day(); recs=[]
    for i in range(len(ss)):
        for j in range(i+1,len(ss)):
            a,b=ss[i],ss[j]; score=rel(a,b); p=pair_state(h,a,b,score,ptype(a,b)); update_pair(p,score,d)
            recs.append({'k':key(a,b),'a':a,'b':b,'p':p})
    roles(h,ss); h['last_scan_day']=d
    nxt=h.get('next_story_day')
    if nxt is None: h['next_story_day']=d+random.randint(COOLDOWN_MIN,COOLDOWN_MAX)
    elif allow_story and d>=int(nxt):
        ev=story(h,ss,recs,d)
        if ev:
            title,text=ev; h['history'].insert(0,{'day':d,'title':title,'text':text}); del h['history'][20:]; notify(title,text)
        h['next_story_day']=d+random.randint(COOLDOWN_MIN,COOLDOWN_MAX)
    if show_notice and not START_NOTICE:
        START_NOTICE=True; left=max(0,int(h.get('next_story_day',d))-d)
        notify('Семья и отношения v'+VERSION,'Модуль активен. Семейные отношения анализируются автоматически. Следующий крупный сюжет — примерно через {} дн.'.format(left))

def alarm_cb(_):
    try: scan(False,True)
    except Exception: log.error('scan failed:\n{}',traceback.format_exc())

def start_alarm():
    global ALARM
    if ALARM is not None:
        try: alarms.cancel_alarm(ALARM)
        except Exception: pass
    try:
        ALARM=alarms.add_alarm(OWNER,date_and_time.create_time_span(minutes=15),alarm_cb,repeating=True,
            repeating_time_span=date_and_time.create_time_span(hours=24))
    except Exception: log.exception('alarm start')

@inject_to(zone.Zone,'on_loading_screen_animation_finished')
def on_zone(old,self,*a,**k):
    result=old(self,*a,**k)
    try: load_state(); start_alarm(); scan(True,False)
    except Exception: log.error('zone init failed:\n{}',traceback.format_exc())
    return result

@inject_to(PersistenceService,'save_game_gen')
def on_save(old,self,timeline,save_game_data,send_save_message=True,check_cooldown=False):
    try: scan(False,False); save_state()
    except Exception: log.error('save hook failed:\n{}',traceback.format_exc())
    return old(self,timeline,save_game_data,send_save_message=send_save_message,check_cooldown=check_cooldown)

@sims4.commands.Command('lwc.familystatus',command_type=sims4.commands.CommandType.Live)
def status(_connection=None):
    out=sims4.commands.CheatOutput(_connection)
    try:
        hh=household()
        if hh is None: out('LWC Family: active household not found'); return False
        h=hstate(hh); mem=sum(len(p.get('memories',[])) for p in h['pairs'].values())
        out('LWC Family v{} | TS4 {} | slot {} | day {}'.format(VERSION,TARGET,slot_id(),day()))
        out('Pairs: {} | memories: {} | next story day: {}'.format(len(h['pairs']),mem,h.get('next_story_day','?')))
        out('Roles: {}'.format(h.get('roles',{}))); return True
    except Exception as e: out('LWC Family status error: {}'.format(e)); return False

log.info('LifeWithConsequences Family v{} loaded for {}'.format(VERSION,TARGET))

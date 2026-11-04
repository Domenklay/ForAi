# -*- coding: utf-8 -*-
"""Independent pair-level relationship model. No Sims4 or Buff imports."""
ACTIONS=("talk","complain","apologize","pause","reconcile","breakup")
def pair_key(a,b):
    a,b=int(a),int(b)
    if not a or not b or a==b:raise ValueError("Two Sims required")
    return "%d:%d"%((a,b) if a<b else (b,a))
def default_pair(a,b):
    return {"ids":[min(int(a),int(b)),max(int(a),int(b))],"trust":60,
            "closeness":50,"resentment":0,"stage":"steady","history":[]}
def stage_of(r):
    if r["stage"] in ("pause","breakup"):return r["stage"]
    return "conflict" if r["resentment"]>=15 else ("tension" if r["resentment"] else "steady")
def eligible(action,r,adult=True):
    s=stage_of(r)
    if action=="report":return True
    if action not in ACTIONS or s=="breakup":return False
    if action in ("pause","reconcile","breakup") and not adult:return False
    if action in ("talk","complain"):return s!="pause"
    if action=="apologize":return r["resentment"]>0 and s!="pause"
    if action=="pause":return s=="conflict"
    if action=="reconcile":return s=="pause"
    if action=="breakup":return s in ("conflict","pause")
    return False
def apply(r,action,adult=True):
    if not eligible(action,r,adult):return False
    if action=="talk":
        r["trust"]=min(100,r["trust"]+1)
        r["closeness"]=min(100,r["closeness"]+3)
        r["resentment"]=max(0,r["resentment"]-2)
    elif action=="complain":
        r["trust"]=max(0,r["trust"]-2)
        r["resentment"]=min(100,r["resentment"]+7)
    elif action=="apologize":
        r["trust"]=min(100,r["trust"]+1)
        r["resentment"]=max(0,r["resentment"]-8)
    elif action=="pause":r["stage"]="pause"
    elif action=="reconcile":
        r["stage"]="steady"
        r["resentment"]=max(0,r["resentment"]-15)
        r["trust"]=min(100,r["trust"]+5)
    elif action=="breakup":r["stage"]="breakup"
    r.setdefault("history",[]).append(action)
    del r["history"][:-20]
    return True

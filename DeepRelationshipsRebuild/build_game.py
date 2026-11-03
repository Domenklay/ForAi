# -*- coding: utf-8 -*-
"""Compile Sims 4 Python 3.7 .ts4script with static integrity checks."""
import ast
import os
import py_compile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DIST=ROOT/"dist"
DST=DIST/"DeepRelationships_v0.8.6_MENU_FIX.ts4script"
MAGIC=bytes.fromhex("420d0d0a")
EXCLUDE={"tests", "dist", "__pycache__"}
SOURCES=sorted(p for p in ROOT.rglob("*.py") if not EXCLUDE.intersection(p.relative_to(ROOT).parts) and p.name!="build_game.py")

def main():
    DIST.mkdir(exist_ok=True)
    if DST.exists():
        DST.unlink()
    # Validate all sources before writing any distributable archive.
    for path in SOURCES:
        ast.parse(path.read_text(encoding="utf-8"),filename=str(path))
    with zipfile.ZipFile(str(DST),"w",zipfile.ZIP_DEFLATED) as archive:
        for path in SOURCES:
            rel=path.relative_to(ROOT).with_suffix(".pyc")
            target=DIST/"tmp"/rel
            target.parent.mkdir(exist_ok=True,parents=True)
            py_compile.compile(str(path),cfile=str(target),doraise=True)
            if target.read_bytes()[:4]!=MAGIC:
                raise RuntimeError("Python 3.7 magic mismatch: "+str(path))
            archive.write(str(target),str(rel).replace(os.sep,"/"))
    with zipfile.ZipFile(str(DST)) as archive:
        files=set(archive.namelist())
        required={
            "deep_relationships.pyc", "runtime.pyc",
            "engine/__init__.pyc", "adapter/__init__.pyc",
            "zzzzzz_deep_relationships_reconciliation_v050.pyc",
            "zzzzzzzzzzz_deep_relationships_breakup_v070.pyc",
        }
        if not required.issubset(files):
            raise RuntimeError("Missing game modules "+repr(required-files))
        if archive.testzip() is not None:
            raise RuntimeError("Corrupt script archive")
    print("BUILT",str(DST),DST.stat().st_size,"bytes",len(SOURCES),"modules")

if __name__=="__main__":
    main()

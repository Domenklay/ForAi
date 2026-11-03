# -*- coding: utf-8 -*-
import os
import py_compile
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
BUILD = ROOT / 'build'
DIST = ROOT / 'dist'
VERSION = '0.7.0'
SCRIPT_NAME = 'DeepRelationships_v{}.ts4script'.format(VERSION)
EXPECTED_MAGIC = bytes.fromhex('420d0d0a')
EXPECTED_MODULES = [
    'deep_relationships.pyc',
    'zz_deep_relationships_grievances.pyc',
    'zzy_deep_relationships_moodlets.pyc',
    'zzzz_deep_relationships_persistence_v045.pyc',
    'zzzzz_deep_relationships_core_v046.pyc',
    'zzzzzz_deep_relationships_reconciliation_v050.pyc',
    'zzzzzzz_deep_relationships_v051.pyc',
    'zzzzzzzz_deep_relationships_memory_v060.pyc',
    'zzzzzzzzz_deep_relationships_v061.pyc',
    'zzzzzzzzzz_deep_relationships_v062.pyc',
    'zzzzzzzzzzz_deep_relationships_breakup_v070.pyc',
]
SOURCE_NAMES = [
    'deep_relationships.py',
    'zz_deep_relationships_grievances.py',
    'zzy_deep_relationships_moodlets.py',
    'zzzz_deep_relationships_persistence_v045.py',
    'zzzzz_deep_relationships_core_v046.py',
    'zzzzzz_deep_relationships_reconciliation_v050.py',
    'zzzzzzz_deep_relationships_v051.py',
    'zzzzzzzz_deep_relationships_memory_v060.py',
    'zzzzzzzzz_deep_relationships_v061.py',
    'zzzzzzzzzz_deep_relationships_v062.py',
    'zzzzzzzzzzz_deep_relationships_breakup_v070.py',
]


def main():
    for path in (BUILD, DIST):
        if path.exists():
            shutil.rmtree(str(path))
        path.mkdir(parents=True, exist_ok=True)

    compiled = BUILD / 'compiled'
    compiled.mkdir(parents=True, exist_ok=True)
    pycs = []
    for source_name in SOURCE_NAMES:
        source = SRC / source_name
        target = compiled / (source.stem + '.pyc')
        py_compile.compile(str(source), cfile=str(target), doraise=True)
        if target.read_bytes()[:4] != EXPECTED_MAGIC:
            raise RuntimeError('Wrong Python magic for {}'.format(target.name))
        pycs.append(target)

    names = sorted(p.name for p in pycs)
    if names != sorted(EXPECTED_MODULES):
        raise RuntimeError('Unexpected modules: {}'.format(names))

    output = DIST / SCRIPT_NAME
    with zipfile.ZipFile(str(output), 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for pyc in sorted(pycs, key=lambda p: p.name):
            archive.write(str(pyc), arcname=pyc.name)

    with zipfile.ZipFile(str(output), 'r') as archive:
        if sorted(archive.namelist()) != sorted(EXPECTED_MODULES):
            raise RuntimeError('Bad ts4script members')
        if archive.testzip() is not None:
            raise RuntimeError('Corrupt ts4script')

    print('Python:', os.sys.version)
    print('Built:', output)
    print('Members:', ', '.join(names))
    print('Size:', output.stat().st_size)


if __name__ == '__main__':
    main()

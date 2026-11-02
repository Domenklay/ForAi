from pathlib import Path
import base64
import gzip
import importlib.util
import py_compile
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build_v065'
DIST = ROOT / 'dist_v065'
BUILD.mkdir(exist_ok=True)
DIST.mkdir(exist_ok=True)

base = gzip.decompress(base64.b64decode((ROOT / 'sims4_lwc_build/lwc_v041.py.gz.b64').read_text().strip())).decode('utf-8')
old_workflow = subprocess.check_output([
    'git', 'show',
    '44aa727d21d049bb98480821885bac8e4eae500c:.github/workflows/build-sims4-lwc-v042.yml'
]).decode('utf-8')
start = old_workflow.index("          addon=r'''\n") + len("          addon=r'''\n")
end = old_workflow.index("\n'''\n          source += addon", start)

base = base.replace('Life With Consequences v0.4.1 SAFE', 'Life With Consequences v0.4.2')
base = base.replace('MOD_VERSION = "0.4.1"', 'MOD_VERSION = "0.4.2"')
source = base + old_workflow[start:end]
for name in (
    'lwc_v050_addon.py.txt',
    'lwc_v051_addon.py.txt',
    'lwc_v060_addon.py.txt',
    'lwc_v061_addon.py.txt',
    'lwc_v063_addon.py.txt',
    'lwc_v064_addon.py.txt',
    'lwc_v065_addon.py.txt',
):
    source += '\n\n' + (ROOT / 'sims4_lwc_build' / name).read_text(encoding='utf-8') + '\n'
source += '\n\nMOD_VERSION = "0.6.5"\n'

assert 'MOD_VERSION = "0.6.5"' in source
assert 'class _LWC063ImmediateRelationshipListener' in source
assert 'class _LWC064ImmediateLifeListener' in source
assert 'def _lwc065_buffstatus' in source
assert 'LWC_BUFF_GRIEF = 533850013479795656' in source
assert 'def _lwc051_commit_state' in source

src = BUILD / 'life_with_consequences.py'
pyc = BUILD / 'life_with_consequences.pyc'
out = DIST / 'LifeWithConsequences_0.6.5_TS4_1.127.41.ts4script'
src.write_text(source, encoding='utf-8')
py_compile.compile(str(src), cfile=str(pyc), doraise=True, optimize=2)
with zipfile.ZipFile(str(out), 'w', zipfile.ZIP_DEFLATED) as z:
    z.write(str(pyc), 'life_with_consequences.pyc')
with zipfile.ZipFile(str(out)) as z:
    names = z.namelist()
    data = z.read('life_with_consequences.pyc')
assert names == ['life_with_consequences.pyc']
assert data[:4] == importlib.util.MAGIC_NUMBER
print('source bytes', len(source.encode('utf-8')))
print('python magic', data[:4].hex())
print(out)

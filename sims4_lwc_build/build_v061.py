from pathlib import Path
import base64
import gzip
import importlib.util
import py_compile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build_v061'
DIST = ROOT / 'dist_v061'
BUILD.mkdir(exist_ok=True)
DIST.mkdir(exist_ok=True)

base = gzip.decompress(base64.b64decode((ROOT / 'sims4_lwc_build/lwc_v041.py.gz.b64').read_text().strip())).decode('utf-8')
wf = (ROOT / '.github/workflows/build-sims4-lwc-v042.yml').read_text(encoding='utf-8')
start = wf.index("          addon=r'''\n") + len("          addon=r'''\n")
end = wf.index("\n'''\n          source += addon", start)
base = base.replace('Life With Consequences v0.4.1 SAFE', 'Life With Consequences v0.4.2')
base = base.replace('MOD_VERSION = "0.4.1"', 'MOD_VERSION = "0.4.2"')
source = base + wf[start:end]
for name in ('lwc_v050_addon.py.txt', 'lwc_v051_addon.py.txt', 'lwc_v060_addon.py.txt', 'lwc_v061_addon.py.txt'):
    source += '\n\n' + (ROOT / 'sims4_lwc_build' / name).read_text(encoding='utf-8') + '\n'

assert 'MOD_VERSION = "0.6.1"' in source
assert 'LWC_BUFF_BETRAYAL' in source
assert 'def _lwc051_commit_state' in source
assert 'def _lwc060_watch_tick' in source

src = BUILD / 'life_with_consequences.py'
pyc = BUILD / 'life_with_consequences.pyc'
out = DIST / 'LifeWithConsequences_0.6.1_TS4_1.127.41.ts4script'
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

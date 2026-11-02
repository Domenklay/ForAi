from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
dist = root / 'dist_v063'
files = [
    dist / 'LifeWithConsequences_0.6.3_TS4_1.127.41.ts4script',
    dist / 'LifeWithConsequences_0.6.3.package',
]
for p in files:
    if not p.exists():
        raise FileNotFoundError(p)
out = dist / 'LifeWithConsequences_0.6.3_FULL.zip'
with zipfile.ZipFile(str(out), 'w', zipfile.ZIP_DEFLATED) as z:
    for p in files:
        z.write(str(p), p.name)
print(out)

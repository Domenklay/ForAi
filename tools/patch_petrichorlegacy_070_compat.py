from pathlib import Path

p = Path(__file__).resolve().parents[1] / "PetrichorLegacy" / "Persistence" / "SaveService.cs"
t = p.read_text(encoding="utf-8")
old = '''            if (p.schemaVersion < 6)\n            {\n                p.schemaVersion = 6;\n            }'''
new = '''            if (p.schemaVersion < 6)\n            {\n                // New Legacy nodes extend the already chosen direction. Existing purchases stay intact.\n                p.schemaVersion = 6;\n            }'''
if old not in t and new not in t:
    raise RuntimeError("Schema 6 migration block not found")
if old in t:
    t = t.replace(old, new, 1)
p.write_text(t, encoding="utf-8")
print("Prepared schema 6 migration for 0.7.0")

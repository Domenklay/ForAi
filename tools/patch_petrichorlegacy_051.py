from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"


def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")


def save(p, text):
    p.write_text(text, encoding="utf-8")


# ---------- Early Legacy tree: meaningful levels 1-9 ----------
p, t = rw("Progression/TalentCatalog.cs")
start = t.index("            // НАСЛЕДИЕ")
end = t.index("            // СТРАЖ", start)
legacy = r'''            // НАСЛЕДИЕ — путь до первого класса. Каждый ранний уровень даёт отдельный выбор.
            new TalentDef("legacy_pack", "Первый трофей", "+1 вместимость стартового Арсенала. Базовая вместимость до этого равна 0.", TalentBranch.Legacy, 1, 1, 1, null, 0, 1, 0),

            // Три стартовых направления: бой / выживание / мобильность.
            new TalentDef("legacy_damage", "Заточенное оружие", "+1.5% урона.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 0, 1),
            new TalentDef("legacy_hp", "Закалка", "+2% максимального здоровья.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 1, 1),
            new TalentDef("legacy_move", "Лёгкая поступь", "+2% скорости движения.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 2, 1),

            new TalentDef("legacy_attack", "Быстрая рука", "+1.5% скорости атаки.", TalentBranch.Legacy, 1, 1, 4, "legacy_damage", 1, 0, 2),
            new TalentDef("legacy_regen", "Полевой рацион", "+4% естественной регенерации.", TalentBranch.Legacy, 1, 1, 4, "legacy_hp", 1, 1, 2),
            new TalentDef("legacy_sprint", "Марш-бросок", "+3% скорости спринта.", TalentBranch.Legacy, 1, 1, 4, "legacy_move", 1, 2, 2),

            new TalentDef("legacy_hunter", "Охотничий инстинкт", "+3% урона боссам и особым монстрам.", TalentBranch.Legacy, 1, 1, 6, "legacy_attack", 1, 0, 3),
            new TalentDef("legacy_armor", "Крепкая кожа", "+2 брони.", TalentBranch.Legacy, 1, 1, 6, "legacy_regen", 1, 1, 3),
            new TalentDef("legacy_jump", "Лёгкое снаряжение", "+8% силы прыжка.", TalentBranch.Legacy, 1, 1, 6, "legacy_sprint", 1, 2, 3),

            // Универсальная экспедиционная дорожка: ещё один слот и небольшой стартовый запас.
            new TalentDef("legacy_pack2", "Экспедиционный ранец", "+1 вместимость стартового Арсенала.", TalentBranch.Legacy, 1, 1, 8, "legacy_pack", 1, 1, 4),
            new TalentDef("legacy_startgold", "Заначка", "+15 золота в начале каждого забега.", TalentBranch.Legacy, 1, 1, 9, "legacy_pack2", 1, 1, 5),

'''
t = t[:start] + legacy + t[end:]
save(p, t)


# ---------- First talent point exists at level 1; Arsenal base capacity is 0 ----------
p, t = rw("Progression/ProgressionService.cs")
t = t.replace(
'''            if (level <= 40) return level - 1;\n            return 39 + (level - 40) / 2;''',
'''            if (level <= 40) return level;\n            return 40 + (level - 40) / 2;''')

old_capacity = '''        public static int StartingCapacity(ProfileProgress profile)\n        {\n            if (profile == null) return 1;\n            var level = profile.level;\n            var capacity = 1;\n            if (level >= 5) capacity = 2;\n            if (level >= 10) capacity = 3;\n            if (level >= 20) capacity = 5;\n            if (level >= 40) capacity = 7;\n            if (level >= 50) capacity = 10;\n            if (level >= 70) capacity = 11;\n            if (level >= 100) capacity = 12;\n            if (level >= 150) capacity = 13;\n            if (level >= 250) capacity = 14;\n            if (level >= 400) capacity = 15;\n\n            capacity += TalentCatalog.GetRank(profile, "legacy_pack");\n            capacity += PerfectionCatalog.GetRank(profile, "perfection_pack");\n            capacity += PerfectionCatalog.GetRank(profile, "perfection_prestige_treasurer");\n            return capacity;\n        }'''
new_capacity = '''        public static int StartingCapacity(ProfileProgress profile)\n        {\n            if (profile == null) return 0;\n            var level = profile.level;\n\n            // Levels 1-19 rely on the Legacy tree: 0 base slots, then +1/+1 from the two backpack nodes.\n            // From level 20 onward the old long-term capacity curve is preserved after those two slots are added.\n            var capacity = 0;\n            if (level >= 20) capacity = 3;\n            if (level >= 40) capacity = 5;\n            if (level >= 50) capacity = 8;\n            if (level >= 70) capacity = 9;\n            if (level >= 100) capacity = 10;\n            if (level >= 150) capacity = 11;\n            if (level >= 250) capacity = 12;\n            if (level >= 400) capacity = 13;\n\n            capacity += TalentCatalog.GetRank(profile, "legacy_pack");\n            capacity += TalentCatalog.GetRank(profile, "legacy_pack2");\n            capacity += PerfectionCatalog.GetRank(profile, "perfection_pack");\n            capacity += PerfectionCatalog.GetRank(profile, "perfection_prestige_treasurer");\n            return capacity;\n        }'''
if old_capacity not in t:
    raise RuntimeError("StartingCapacity block not found")
t = t.replace(old_capacity, new_capacity)
save(p, t)


# ---------- New profiles start with one talent point; schema 4 migrates old Legacy safely ----------
p, t = rw("Models/ProfileProgress.cs")
t = t.replace("public int schemaVersion = 3;", "public int schemaVersion = 4;")
t = t.replace("public int unspentTalentPoints = 0;", "public int unspentTalentPoints = 1;")
save(p, t)

p, t = rw("Persistence/SaveService.cs")
marker = '''            if (p.schemaVersion < 3)\n            {'''
if marker not in t:
    raise RuntimeError("Save migration marker not found")
t = t.replace(marker, '''            var migratedFromPreV3 = p.schemaVersion < 3;\n\n            if (p.schemaVersion < 3)\n            {''', 1)

insert_after = '''                p.schemaVersion = 3;\n            }'''
if insert_after not in t:
    raise RuntimeError("v3 migration end not found")
v4 = '''                p.schemaVersion = 3;\n            }\n\n            if (p.schemaVersion < 4)\n            {\n                // The Legacy tree was redesigned. Refund only its old ranks; class/spec progress stays intact.\n                var legacyRefund = 0;\n                for (var i = p.talents.Count - 1; i >= 0; i--)\n                {\n                    var record = p.talents[i];\n                    if (record == null) continue;\n                    var def = TalentCatalog.Find(record.id);\n                    if (def == null || def.Branch != TalentBranch.Legacy) continue;\n                    legacyRefund += Math.Max(0, record.rank);\n                    p.talents.RemoveAt(i);\n                }\n\n                p.unspentTalentPoints += legacyRefund;\n                // v0.5.1 gives a real level-1 talent point. Pre-v3 migration already used the new earned-point formula.\n                if (!migratedFromPreV3) p.unspentTalentPoints += 1;\n                p.schemaVersion = 4;\n            }'''
t = t.replace(insert_after, v4, 1)
save(p, t)


# ---------- Runtime effects for the new early tree ----------
p, t = rw("Progression/TalentEffects.cs")
old_legacy = '''            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "legacy_hp") * 0.01f;\n            self.damage *= 1f + ServerProgressionState.Rank(self.master, "legacy_damage") * 0.01f;\n            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_attack") * 0.01f;\n            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_move") * 0.015f;\n            self.armor += ServerProgressionState.Rank(self.master, "legacy_armor");\n            self.regen *= 1f + ServerProgressionState.Rank(self.master, "legacy_regen") * 0.02f;'''
new_legacy = '''            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "legacy_hp") * 0.02f;\n            self.damage *= 1f + ServerProgressionState.Rank(self.master, "legacy_damage") * 0.015f;\n            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_attack") * 0.015f;\n            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_move") * 0.02f;\n            self.sprintingSpeedMultiplier *= 1f + ServerProgressionState.Rank(self.master, "legacy_sprint") * 0.03f;\n            self.jumpPower *= 1f + ServerProgressionState.Rank(self.master, "legacy_jump") * 0.08f;\n            self.armor += ServerProgressionState.Rank(self.master, "legacy_armor") * 2f;\n            self.regen *= 1f + ServerProgressionState.Rank(self.master, "legacy_regen") * 0.04f;'''
if old_legacy not in t:
    raise RuntimeError("Legacy stat block not found")
t = t.replace(old_legacy, new_legacy, 1)

hunt_anchor = '''            if (attackerBody != null && attackerBody.master != null && victimBody != null)\n            {'''
if hunt_anchor not in t:
    raise RuntimeError("damage hook anchor not found")
t = t.replace(hunt_anchor, hunt_anchor + '''\n                var legacyHunter = ServerProgressionState.Rank(attackerBody.master, "legacy_hunter");\n                if (legacyHunter > 0 && (victimBody.isBoss || victimBody.GetComponent<MonsterRarityMarker>() != null))\n                    damageInfo.damage *= 1f + legacyHunter * 0.03f;''', 1)
save(p, t)


# ---------- Early starting gold ----------
p, t = rw("Networking/ProgressionNetwork.cs")
start_gold_anchor = '''            var startGold = 0f;'''
if start_gold_anchor not in t:
    raise RuntimeError("start gold anchor not found")
t = t.replace(start_gold_anchor, start_gold_anchor + '''\n            startGold += ServerProgressionState.Rank(master, "legacy_startgold") * 15f;''', 1)
save(p, t)


# ---------- UI label ----------
p, t = rw("UI/MetaProgressionUIV5.cs")
t = t.replace('case TalentBranch.Legacy: return "НАСЛЕДИЕ";', 'case TalentBranch.Legacy: return "НАСЛЕДИЕ • ПУТЬ ДО КЛАССА";')
save(p, t)


# ---------- Version/package ----------
p, t = rw("Plugin.cs")
t = t.replace('public const string PluginVersion = "0.5.0";', 'public const string PluginVersion = "0.5.1";')
save(p, t)

p, t = rw("manifest.json")
t = t.replace('"version_number": "0.5.0"', '"version_number": "0.5.1"')
t = t.replace('Seven-class infinite meta progression', 'Seven-class infinite meta progression with a redesigned level 1-9 Legacy journey')
save(p, t)

p, t = rw("PetrichorLegacy.csproj")
t = t.replace('<Version>0.5.0</Version>', '<Version>0.5.1</Version>')
save(p, t)

print("Applied PetrichorLegacy 0.5.1 early progression patch")

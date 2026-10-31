from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
ui_path = root / "PetrichorLegacy" / "UI" / "MetaProgressionUIV5.cs"
progress_path = root / "PetrichorLegacy" / "Progression" / "ProgressionService.cs"

ui = ui_path.read_text(encoding="utf-8")
progress = progress_path.read_text(encoding="utf-8")

# Arsenal is profile progression and must survive ordinary talent respecs.
progress = progress.replace("            profile.startingLoadout.Clear();\n", "")
progress_path.write_text(progress, encoding="utf-8")

# Make the tree intentionally tall/readable and rely on vertical scrolling.
replacements = {
    "const float baseHeight = 575f;": "const float baseHeight = 820f;",
    "const float specHeight = 610f;": "const float specHeight = 900f;",
    "$\"ОСНОВА — {ClassDisplay(classId)}\", false, string.Empty, 102f)": "$\"ОСНОВА — {ClassDisplay(classId)}\", false, string.Empty, 165f)",
    "BranchTitle(spec1), true, TalentCatalog.SpecForBranch(spec1), 104f)": "BranchTitle(spec1), true, TalentCatalog.SpecForBranch(spec1), 165f)",
    "BranchTitle(spec2), true, TalentCatalog.SpecForBranch(spec2), 104f)": "BranchTitle(spec2), true, TalentCatalog.SpecForBranch(spec2), 165f)",
    "BranchTitle(spec3), true, TalentCatalog.SpecForBranch(spec3), 104f)": "BranchTitle(spec3), true, TalentCatalog.SpecForBranch(spec3), 165f)",
    "const float nodeHeight = 82f;": "const float nodeHeight = 140f;",
    "var iconRect = new Rect(rect.x + 7f, rect.y + 8f, 55f, 55f);": "var iconRect = new Rect(rect.x + 7f, rect.y + 10f, 60f, 60f);",
    "var textX = rect.x + 68f;": "var textX = rect.x + 74f;",
    "var textW = rect.width - 75f;": "var textW = rect.width - 81f;",
    "GUI.Label(new Rect(textX, rect.y + 5f, textW, 21f), $\"{def.Name} [{rank}/{def.MaxRank}]\", _nodeTitle);": "GUI.Label(new Rect(textX, rect.y + 5f, textW, 36f), $\"{def.Name} [{rank}/{def.MaxRank}]\", _nodeTitle);",
    "GUI.Label(new Rect(textX, rect.y + 27f, textW, 24f), ShortEffect(def.Description), _nodeEffect);": "GUI.Label(new Rect(textX, rect.y + 43f, textW, 56f), ShortEffect(def.Description), _nodeEffect);",
    "if (GUI.Button(new Rect(textX, rect.yMax - 26f, textW, 22f), label))": "if (GUI.Button(new Rect(textX, rect.yMax - 35f, textW, 30f), label))",
    "return clean.Length <= 62 ? clean : clean.Substring(0, 59) + \"…\";": "return clean.Length <= 112 ? clean : clean.Substring(0, 109) + \"…\";",
    "_nodeTitle = new GUIStyle(GUI.skin.label) { fontSize = 12, fontStyle = FontStyle.Bold, clipping = TextClipping.Clip, normal = { textColor = Color.white } };": "_nodeTitle = new GUIStyle(GUI.skin.label) { fontSize = 13, fontStyle = FontStyle.Bold, wordWrap = true, clipping = TextClipping.Clip, normal = { textColor = Color.white } };",
    "_nodeEffect = new GUIStyle(GUI.skin.label) { fontSize = 10, wordWrap = true, clipping = TextClipping.Clip, normal = { textColor = new Color(0.84f, 0.89f, 0.92f, 1f) } };": "_nodeEffect = new GUIStyle(GUI.skin.label) { fontSize = 11, wordWrap = true, clipping = TextClipping.Clip, normal = { textColor = new Color(0.84f, 0.89f, 0.92f, 1f) } };",
}
for old, new in replacements.items():
    if old not in ui:
        raise RuntimeError(f"Expected UI fragment not found: {old}")
    ui = ui.replace(old, new)

start = ui.index("        private static string[] PreferredIconCandidates(string id)")
end = ui.index("        private static string EffectGlyph", start)
new_icons = r'''        private static string[] PreferredIconCandidates(string id)
        {
            id = (id ?? string.Empty).ToLowerInvariant();

            // Capstones deliberately use their actual reward icons.
            if (id.Contains("guardian_void_capstone")) return new[] { "BearVoid" };
            if (id.Contains("slayer_void_capstone")) return new[] { "BleedOnHitVoid" };
            if (id.Contains("path_void_capstone")) return new[] { "ChainLightningVoid" };
            if (id.Contains("seeker_void_capstone")) return new[] { "TreasureCacheVoid" };
            if (id.Contains("bastion_legendary")) return new[] { "CaptainDefenseMatrix" };
            if (id.Contains("unbroken_legendary")) return new[] { "IncreaseHealing" };
            if (id.Contains("vanguard_legendary")) return new[] { "ArmorReductionOnHit" };
            if (id.Contains("executioner_legendary")) return new[] { "Dagger" };
            if (id.Contains("hunter_legendary")) return new[] { "HeadHunter" };
            if (id.Contains("berserker_legendary")) return new[] { "ShockNearby" };
            if (id.Contains("scout_legendary")) return new[] { "AlienHead" };
            if (id.Contains("acro_legendary")) return new[] { "UtilitySkillMagazine" };
            if (id.Contains("saboteur_legendary")) return new[] { "BounceNearby" };
            if (id.Contains("merchant_legendary")) return new[] { "DroneWeapons" };
            if (id.Contains("prospector_legendary")) return new[] { "Clover" };
            if (id.Contains("relic_legendary")) return new[] { "Talisman" };

            string[] pool;
            if (HasAny(id, "crit", "precision", "accur"))
                pool = new[] { "CritGlasses", "AttackSpeedOnCrit", "HealOnCrit", "Crowbar" };
            else if (HasAny(id, "cooldown", "technique", "relic", "skill", "saboteur"))
                pool = new[] { "Bandolier", "AlienHead", "UtilitySkillMagazine", "EquipmentMagazine" };
            else if (HasAny(id, "attack", "haste", "tempo", "berserker", "rage", "fury"))
                pool = new[] { "Syringe", "AttackSpeedOnCrit", "WarCryOnMultiKill", "Crowbar" };
            else if (HasAny(id, "jump", "acro", "air", "spring"))
                pool = new[] { "Feather", "JumpBoost", "Hoof", "SprintBonus" };
            else if (HasAny(id, "move", "route", "flow", "adrenaline", "sprint", "scout", "line"))
                pool = new[] { "Hoof", "SprintBonus", "SprintOutOfCombat", "JumpBoost" };
            else if (HasAny(id, "shield", "barrier", "stability", "bastion", "layer"))
                pool = new[] { "PersonalShield", "BarrierOnKill", "ArmorPlate", "Infusion" };
            else if (HasAny(id, "armor", "harden", "iron", "guard", "fort", "vanguard"))
                pool = new[] { "ArmorPlate", "SprintArmor", "Knurl", "PersonalShield" };
            else if (HasAny(id, "regen", "heal", "breath", "rest", "calm", "unbroken"))
                pool = new[] { "Medkit", "HealWhileSafe", "Seed", "HealOnCrit" };
            else if (HasAny(id, "health", "vital", "body", "endurance", "surviv", "contour"))
                pool = new[] { "Infusion", "FlatHealth", "Knurl", "PersonalShield" };
            else if (HasAny(id, "gold", "merchant", "capital", "treasure", "prospector", "supply", "cache"))
                pool = new[] { "GoldOnHurt", "BonusGoldPackOnKill", "TreasureCache", "EquipmentMagazine" };
            else if (HasAny(id, "pack", "reserve"))
                pool = new[] { "EquipmentMagazine", "TreasureCache", "Bandolier", "Infusion" };
            else if (HasAny(id, "hunter", "boss", "giant", "prey", "hunt"))
                pool = new[] { "BossDamageBonus", "HeadHunter", "Crowbar", "CritGlasses" };
            else if (HasAny(id, "damage", "power", "focus", "verdict", "execution", "slayer", "strike"))
                pool = new[] { "Crowbar", "NearbyDamageBonus", "BossDamageBonus", "FragileDamageBonus" };
            else
                pool = new[] { "Infusion", "Medkit", "Hoof", "Crowbar", "ArmorPlate", "Syringe" };

            return RotateIconPool(pool, id);
        }

        private static bool HasAny(string value, params string[] parts)
        {
            foreach (var part in parts)
                if (value.Contains(part)) return true;
            return false;
        }

        private static string[] RotateIconPool(string[] pool, string id)
        {
            if (pool == null || pool.Length <= 1) return pool ?? new string[0];
            unchecked
            {
                var hash = 17;
                for (var i = 0; i < id.Length; i++) hash = hash * 31 + id[i];
                var offset = (hash & 0x7fffffff) % pool.Length;
                var rotated = new string[pool.Length];
                for (var i = 0; i < pool.Length; i++) rotated[i] = pool[(i + offset) % pool.Length];
                return rotated;
            }
        }

'''
ui = ui[:start] + new_icons + ui[end:]
ui_path.write_text(ui, encoding="utf-8")
print("Applied PetrichorLegacy 0.4.1 source patch")

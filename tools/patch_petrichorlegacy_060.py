from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"


def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")


def save(p, text):
    p.write_text(text, encoding="utf-8")


# ---------- Monster rarity: lower raw stat inflation, add trait assignment + compact visible item data ----------
p, t = rw("Progression/MonsterRaritySystem.cs")

t = t.replace(
'''    public sealed class MonsterRarityMarker : MonoBehaviour\n    {\n        public MonsterRarity Rarity;\n        public bool Rewarded;\n        public int GrantedCombatItems;\n    }''',
'''    public sealed class MonsterRarityMarker : MonoBehaviour\n    {\n        public MonsterRarity Rarity;\n        public bool Rewarded;\n        public int GrantedCombatItems;\n        public List<string> Traits = new List<string>();\n    }''')

marker = '    public static class MonsterRaritySystem\n    {'
if marker not in t:
    raise RuntimeError("MonsterRaritySystem marker not found")
visible_type = '''    public sealed class VisibleCombatItem\n    {\n        public ItemDef Item;\n        public int Count;\n    }\n\n'''
t = t.replace(marker, visible_type + marker, 1)

start = t.index("        private static readonly MonsterRarityInfo[] Tiers =")
end = t.index("        };", start) + len("        };")
new_tiers = r'''        private static readonly MonsterRarityInfo[] Tiers =
        {
            // Raw numbers are deliberately moderate: high tiers gain difficulty from affixes, not only HP sponges.
            new MonsterRarityInfo(MonsterRarity.Uncommon, "НЕОБЫЧНЫЙ", "#72D572", 2, 20, 1.20f, 1.04f, 1.02f, 1.01f, 2f, 1.02f, 100f, 1),
            new MonsterRarityInfo(MonsterRarity.Rare, "РЕДКИЙ", "#55C8FF", 5, 50, 1.45f, 1.08f, 1.03f, 1.02f, 5f, 1.04f, 38f, 1),
            new MonsterRarityInfo(MonsterRarity.Epic, "ЭПИЧЕСКИЙ", "#B982FF", 10, 120, 1.80f, 1.12f, 1.05f, 1.03f, 8f, 1.06f, 16f, 2),
            new MonsterRarityInfo(MonsterRarity.Legendary, "ЛЕГЕНДАРНЫЙ", "#FF8A4C", 20, 300, 2.30f, 1.18f, 1.07f, 1.04f, 12f, 1.08f, 6f, 2),
            new MonsterRarityInfo(MonsterRarity.Mythic, "МИФИЧЕСКИЙ", "#FF4F8B", 35, 700, 3.00f, 1.25f, 1.09f, 1.05f, 16f, 1.10f, 2.2f, 3),
            new MonsterRarityInfo(MonsterRarity.Ancient, "ДРЕВНИЙ", "#D9D7FF", 50, 1500, 3.80f, 1.32f, 1.11f, 1.06f, 22f, 1.12f, 0.8f, 3),
            new MonsterRarityInfo(MonsterRarity.Ascended, "ВОЗВЫШЕННЫЙ", "#FFFFFF", 75, 3000, 4.80f, 1.40f, 1.13f, 1.07f, 28f, 1.14f, 0.25f, 4),
            new MonsterRarityInfo(MonsterRarity.Flawless, "БЕЗУПРЕЧНЫЙ", "#F6E8A6", 100, 6000, 6.00f, 1.48f, 1.15f, 1.08f, 35f, 1.16f, 0.11f, 4),
            new MonsterRarityInfo(MonsterRarity.Primordial, "ПЕРВОЗДАННЫЙ", "#FFB35C", 150, 10000, 7.20f, 1.58f, 1.17f, 1.09f, 42f, 1.18f, 0.05f, 5),
            new MonsterRarityInfo(MonsterRarity.Divine, "БОЖЕСТВЕННЫЙ", "#FFF2B5", 200, 18000, 8.50f, 1.68f, 1.19f, 1.10f, 50f, 1.20f, 0.022f, 5),
            new MonsterRarityInfo(MonsterRarity.Anomalous, "АНОМАЛЬНЫЙ", "#80FFF1", 300, 30000, 10.0f, 1.80f, 1.21f, 1.11f, 60f, 1.22f, 0.009f, 6),
            new MonsterRarityInfo(MonsterRarity.Transcendent, "ТРАНСЦЕНДЕНТНЫЙ", "#FF80EE", 500, 50000, 12.0f, 1.95f, 1.24f, 1.12f, 72f, 1.24f, 0.003f, 7)
        };'''
t = t[:start] + new_tiers + t[end:]

assign_anchor = '''            marker.Rarity = rarity;\n            marker.GrantedCombatItems = GrantSafeCombatItems(body.master?.inventory, rarity, info.ItemBudget);'''
if assign_anchor not in t:
    raise RuntimeError("rarity assignment anchor not found")
t = t.replace(assign_anchor, assign_anchor + '''\n            MonsterTraitSystem.AssignTraits(body, marker);''', 1)

t = t.replace(
'''            var stageBonus = Run.instance != null ? Mathf.Min(0.06f, Run.instance.stageClearCount * 0.005f) : 0f;\n            var specialChance = Mathf.Clamp(0.025f + (metaLevel - 2) * 0.0016f + stageBonus, 0.025f, 0.35f);''',
'''            var stageBonus = Run.instance != null ? Mathf.Min(0.04f, Run.instance.stageClearCount * 0.004f) : 0f;\n            var specialChance = Mathf.Clamp(0.02f + (metaLevel - 2) * 0.0011f + stageBonus, 0.02f, 0.25f);''')

log_old = '''                PetrichorLegacyPlugin.Log?.LogInfo($"Spawned {info.DisplayName} monster: {body.GetDisplayName()} with {marker.GrantedCombatItems} safe combat item stacks.");'''
log_new = '''                PetrichorLegacyPlugin.Log?.LogInfo($"Spawned {info.DisplayName} monster: {body.GetDisplayName()} with {marker.GrantedCombatItems} item stacks and {marker.Traits.Count} affixes.");'''
t = t.replace(log_old, log_new)

helper_anchor = '''        private static MonsterRarityInfo GetInfo(MonsterRarity rarity)\n        {'''
if helper_anchor not in t:
    raise RuntimeError("GetInfo anchor not found")
helpers = r'''        public static List<VisibleCombatItem> GetVisibleCombatItems(CharacterBody body)
        {
            var result = new List<VisibleCombatItem>();
            var inventory = body?.master?.inventory;
            if (inventory == null) return result;
            for (var i = 0; i < SafeItems.Length; i++)
            {
                var index = ItemCatalog.FindItemIndex(SafeItems[i].InternalName);
                if (index == ItemIndex.None) continue;
                var count = inventory.GetItemCountPermanent(index);
                if (count <= 0) continue;
                var def = ItemCatalog.GetItemDef(index);
                if (def != null) result.Add(new VisibleCombatItem { Item = def, Count = count });
            }
            return result;
        }

        public static string ItemTooltip(VisibleCombatItem entry)
        {
            if (entry?.Item == null) return "Предмет врага";
            var name = Language.GetString(entry.Item.nameToken);
            if (string.IsNullOrWhiteSpace(name)) name = entry.Item.name;
            var description = Language.GetString(entry.Item.pickupToken);
            if (string.IsNullOrWhiteSpace(description)) description = "Боевой предмет особого монстра.";
            return $"{name} x{entry.Count}\n{description}";
        }

'''
t = t.replace(helper_anchor, helpers + helper_anchor, 1)
save(p, t)


# ---------- Trait registry must include low-rarity special enemies for item overlays ----------
p, t = rw("Progression/MonsterTraitSystem.cs")
old = '''        public static void AssignTraits(CharacterBody body, MonsterRarityMarker marker)\n        {\n            if (!NetworkServer.active || body == null || marker == null || marker.Rarity < MonsterRarity.Epic) return;\n            if (marker.Traits == null) marker.Traits = new List<string>();\n            if (marker.Traits.Count > 0) return;'''
new = '''        public static void AssignTraits(CharacterBody body, MonsterRarityMarker marker)\n        {\n            if (!NetworkServer.active || body == null || marker == null) return;\n            ActiveMarkers.Add(marker);\n            if (marker.Traits == null) marker.Traits = new List<string>();\n            if (marker.Rarity < MonsterRarity.Epic)\n            {\n                var lowRuntime = body.GetComponent<MonsterTraitRuntime>() ?? body.gameObject.AddComponent<MonsterTraitRuntime>();\n                lowRuntime.Initialize(body, marker);\n                return;\n            }\n            if (marker.Traits.Count > 0) return;'''
if old not in t:
    raise RuntimeError("AssignTraits header not found")
t = t.replace(old, new, 1)
save(p, t)


# ---------- Plugin/UI install ----------
p, t = rw("Plugin.cs")
t = t.replace('public const string PluginVersion = "0.5.1";', 'public const string PluginVersion = "0.6.0";')
t = t.replace('        private MetaProgressionUIV5 _ui;\n', '        private MetaProgressionUIV5 _ui;\n        private MonsterRarityOverlay _enemyOverlay;\n', 1)
t = t.replace('            MonsterRaritySystem.Install();', '            MonsterRaritySystem.Install();\n            MonsterTraitSystem.Install();', 1)
t = t.replace('            _ui.Configure(_toggleKey);', '            _ui.Configure(_toggleKey);\n            _enemyOverlay = gameObject.AddComponent<MonsterRarityOverlay>();', 1)
t = t.replace('            MonsterRaritySystem.Uninstall();', '            MonsterTraitSystem.Uninstall();\n            MonsterRaritySystem.Uninstall();', 1)
save(p, t)


# ---------- Version/package ----------
p, t = rw("manifest.json")
t = t.replace('"version_number": "0.5.1"', '"version_number": "0.6.0"')
t = t.replace('Seven-class infinite meta progression with a redesigned level 1-9 Legacy journey', 'Seven-class infinite meta progression with 39 compact enemy affixes, safer rarity scaling and enemy item/affix HUD')
save(p, t)

p, t = rw("PetrichorLegacy.csproj")
t = t.replace('<Version>0.5.1</Version>', '<Version>0.6.0</Version>')
save(p, t)

print("Applied PetrichorLegacy 0.6.0 enemy affix patch")

from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"


def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")


def save(p, text):
    p.write_text(text, encoding="utf-8")


# ---------- Special-enemy rarity distribution ----------
p, t = rw("Progression/MonsterRaritySystem.cs")
old_weight = '''        private static float EffectiveWeight(MonsterRarityInfo info, int metaLevel)\n        {\n            var levelsPastUnlock = Mathf.Max(0, metaLevel - info.UnlockLevel);\n            var growth = 1f + Mathf.Min(2.0f, levelsPastUnlock * 0.018f);\n            return info.Weight * growth;\n        }'''
new_weight = '''        private static float EffectiveWeight(MonsterRarityInfo info, int metaLevel)\n        {\n            // Progressively shift the distribution upward instead of letting Uncommon/Rare dominate forever.\n            // At 500+ the target share among special monsters is approximately:\n            // 35 / 25 / 17 / 10 / 6 / 3 / 1.5 / 1 / 0.7 / 0.4 / 0.25 / 0.15 %.\n            var shift = Mathf.Clamp01((metaLevel - 20f) / 480f);\n            var target = LateGameTargetWeight(info.Rarity);\n            var weight = Mathf.Lerp(info.Weight, target, shift);\n\n            // A newly unlocked rarity gets a short discovery window so an unlock is actually noticeable.\n            // The boost fades completely over the next 30 meta-levels.\n            var levelsPastUnlock = Mathf.Max(0, metaLevel - info.UnlockLevel);\n            if (info.Rarity >= MonsterRarity.Epic && levelsPastUnlock < 30)\n                weight *= 1f + 0.75f * (1f - levelsPastUnlock / 30f);\n\n            return Mathf.Max(0.001f, weight);\n        }\n\n        private static float LateGameTargetWeight(MonsterRarity rarity)\n        {\n            switch (rarity)\n            {\n                case MonsterRarity.Uncommon: return 35f;\n                case MonsterRarity.Rare: return 25f;\n                case MonsterRarity.Epic: return 17f;\n                case MonsterRarity.Legendary: return 10f;\n                case MonsterRarity.Mythic: return 6f;\n                case MonsterRarity.Ancient: return 3f;\n                case MonsterRarity.Ascended: return 1.5f;\n                case MonsterRarity.Flawless: return 1f;\n                case MonsterRarity.Primordial: return 0.7f;\n                case MonsterRarity.Divine: return 0.4f;\n                case MonsterRarity.Anomalous: return 0.25f;\n                case MonsterRarity.Transcendent: return 0.15f;\n                default: return 0f;\n            }\n        }'''
if old_weight not in t:
    raise RuntimeError("EffectiveWeight block not found")
t = t.replace(old_weight, new_weight, 1)
save(p, t)


# ---------- Legacy: exactly one of three early paths ----------
p, t = rw("Progression/ProgressionService.cs")
try_anchor = '''            if (!TalentCatalog.PrerequisiteMet(profile, def)) { error = "Сначала изучи предыдущий узел ветки."; return false; }\n            if (profile.unspentTalentPoints < def.PointCost) { error = "Недостаточно очков талантов."; return false; }'''
try_replacement = '''            if (!TalentCatalog.PrerequisiteMet(profile, def)) { error = "Сначала изучи предыдущий узел ветки."; return false; }\n\n            var path = LegacyPathForTalent(talentId);\n            var chosenPath = LegacyPathChoice(profile);\n            if (!string.IsNullOrEmpty(path) && !string.IsNullOrEmpty(chosenPath) && !string.Equals(path, chosenPath, StringComparison.OrdinalIgnoreCase))\n            {\n                error = "В Наследии можно выбрать только один путь. Сбрось таланты, чтобы сменить его.";\n                return false;\n            }\n            if (talentId == "legacy_pack2" && string.IsNullOrEmpty(chosenPath))\n            {\n                error = "Сначала выбери один из трёх путей Наследия.";\n                return false;\n            }\n\n            if (profile.unspentTalentPoints < def.PointCost) { error = "Недостаточно очков талантов."; return false; }'''
if try_anchor not in t:
    raise RuntimeError("TryBuyTalent legacy insertion anchor not found")
t = t.replace(try_anchor, try_replacement, 1)

helper_anchor = '''        public static bool TryBuyMastery(ProfileProgress profile, string masteryId, out string error)'''
legacy_helpers = '''        public static string LegacyPathForTalent(string talentId)\n        {\n            switch (talentId)\n            {\n                case "legacy_damage":\n                case "legacy_attack":\n                case "legacy_hunter": return "combat";\n                case "legacy_hp":\n                case "legacy_regen":\n                case "legacy_armor": return "survival";\n                case "legacy_move":\n                case "legacy_sprint":\n                case "legacy_jump": return "mobility";\n                default: return string.Empty;\n            }\n        }\n\n        public static string LegacyPathChoice(ProfileProgress profile)\n        {\n            if (profile == null) return string.Empty;\n            if (TalentCatalog.GetRank(profile, "legacy_damage") > 0 || TalentCatalog.GetRank(profile, "legacy_attack") > 0 || TalentCatalog.GetRank(profile, "legacy_hunter") > 0) return "combat";\n            if (TalentCatalog.GetRank(profile, "legacy_hp") > 0 || TalentCatalog.GetRank(profile, "legacy_regen") > 0 || TalentCatalog.GetRank(profile, "legacy_armor") > 0) return "survival";\n            if (TalentCatalog.GetRank(profile, "legacy_move") > 0 || TalentCatalog.GetRank(profile, "legacy_sprint") > 0 || TalentCatalog.GetRank(profile, "legacy_jump") > 0) return "mobility";\n            return string.Empty;\n        }\n\n        public static bool CanBuyLegacyPathTalent(ProfileProgress profile, string talentId)\n        {\n            if (profile == null) return false;\n            var chosen = LegacyPathChoice(profile);\n            if (talentId == "legacy_pack2") return !string.IsNullOrEmpty(chosen);\n            var path = LegacyPathForTalent(talentId);\n            return string.IsNullOrEmpty(path) || string.IsNullOrEmpty(chosen) || string.Equals(path, chosen, StringComparison.OrdinalIgnoreCase);\n        }\n\n'''
if helper_anchor not in t:
    raise RuntimeError("ProgressionService helper anchor not found")
t = t.replace(helper_anchor, legacy_helpers + helper_anchor, 1)
save(p, t)


# ---------- Save migration: clean up 0.6.1 profiles that bought more than one Legacy path ----------
p, t = rw("Models/ProfileProgress.cs")
if "public int schemaVersion = 4;" not in t:
    raise RuntimeError("Profile schema 4 not found")
t = t.replace("public int schemaVersion = 4;", "public int schemaVersion = 5;", 1)
save(p, t)

p, t = rw("Persistence/SaveService.cs")
v4_end = '''                p.schemaVersion = 4;\n            }'''
if v4_end not in t:
    raise RuntimeError("SaveService v4 migration end not found")
v5_block = '''                p.schemaVersion = 4;\n            }\n\n            if (p.schemaVersion < 5)\n            {\n                var combat = false;\n                var survival = false;\n                var mobility = false;\n                for (var i = 0; i < p.talents.Count; i++)\n                {\n                    var r = p.talents[i];\n                    if (r == null || r.rank <= 0) continue;\n                    switch (r.id)\n                    {\n                        case "legacy_damage": case "legacy_attack": case "legacy_hunter": combat = true; break;\n                        case "legacy_hp": case "legacy_regen": case "legacy_armor": survival = true; break;\n                        case "legacy_move": case "legacy_sprint": case "legacy_jump": mobility = true; break;\n                    }\n                }\n\n                var pathCount = (combat ? 1 : 0) + (survival ? 1 : 0) + (mobility ? 1 : 0);\n                if (pathCount > 1)\n                {\n                    // Refund only path-specific Legacy nodes. Shared backpack/gold nodes remain untouched.\n                    var refund = 0;\n                    for (var i = p.talents.Count - 1; i >= 0; i--)\n                    {\n                        var r = p.talents[i];\n                        if (r == null) continue;\n                        var id = r.id ?? string.Empty;\n                        var pathNode = id == "legacy_damage" || id == "legacy_attack" || id == "legacy_hunter" ||\n                                       id == "legacy_hp" || id == "legacy_regen" || id == "legacy_armor" ||\n                                       id == "legacy_move" || id == "legacy_sprint" || id == "legacy_jump";\n                        if (!pathNode) continue;\n                        refund += Math.Max(0, r.rank);\n                        p.talents.RemoveAt(i);\n                    }\n                    p.unspentTalentPoints += refund;\n                }\n                p.schemaVersion = 5;\n            }'''
t = t.replace(v4_end, v5_block, 1)
save(p, t)


# ---------- UI: dedicated Legacy layout + proper capstone cards ----------
p, ui = rw("UI/MetaProgressionUIV5.cs")
legacy_pattern = re.compile(r'''        private void DrawLegacySheet\(ProfileProgress p, Rect area\)\n        \{.*?\n        \}\n\n        private void DrawClassSheet''', re.S)
legacy_method = r'''        private void DrawLegacySheet(ProfileProgress p, Rect area)
        {
            GUI.Label(new Rect(area.x + 5f, area.y + 2f, area.width - 210f, 29f), "НАСЛЕДИЕ — ПУТЬ ДО ПЕРВОГО КЛАССА", _header);
            if (GUI.Button(new Rect(area.xMax - 190f, area.y, 184f, 30f), "Сбросить таланты"))
            {
                ProgressionService.Respec(p);
                _pendingSpecId = string.Empty;
                SetStatus("Обычные таланты сброшены.");
            }

            var viewport = new Rect(area.x, area.y + 38f, area.width, area.height - 38f);
            const float contentHeight = 1110f;
            _treeScroll = GUI.BeginScrollView(viewport, _treeScroll, new Rect(0f, 0f, viewport.width - 18f, Mathf.Max(contentHeight, viewport.height - 2f)));
            var w = viewport.width - 28f;

            var notice = new Rect(6f, 5f, w - 12f, 38f);
            FillRect(notice, new Color(0.045f, 0.060f, 0.068f, 1f));
            DrawBorder(notice, new Color(0.22f, 0.50f, 0.58f, 1f), 1f);
            GUI.Label(notice, "ВЫБЕРИ 1 ИЗ 3 ПУТЕЙ — после первого таланта две остальные ветки блокируются", _center);

            var first = TalentCatalog.Find("legacy_pack");
            var firstRect = new Rect(w * 0.5f - 190f, 58f, 380f, 140f);
            if (first != null) DrawTalentNode(p, first, firstRect);

            var chosen = ProgressionService.LegacyPathChoice(p);
            var gap = 12f;
            var colW = (w - 24f - gap * 2f) / 3f;
            var pathsY = 230f;
            var pathH = 505f;

            var combatPanel = new Rect(6f, pathsY, colW, pathH);
            var survivalPanel = new Rect(6f + colW + gap, pathsY, colW, pathH);
            var mobilityPanel = new Rect(6f + (colW + gap) * 2f, pathsY, colW, pathH);

            DrawLegacyPathPanel(p, combatPanel, "БОЕВОЙ ПУТЬ", "combat", chosen, new[] { "legacy_damage", "legacy_attack", "legacy_hunter" });
            DrawLegacyPathPanel(p, survivalPanel, "ПУТЬ ВЫЖИВАНИЯ", "survival", chosen, new[] { "legacy_hp", "legacy_regen", "legacy_armor" });
            DrawLegacyPathPanel(p, mobilityPanel, "ПУТЬ ПОДВИЖНОСТИ", "mobility", chosen, new[] { "legacy_move", "legacy_sprint", "legacy_jump" });

            if (first != null)
            {
                var active = TalentCatalog.GetRank(p, "legacy_pack") > 0;
                var lineColor = active ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f);
                var stemY = 214f;
                FillRect(new Rect(firstRect.center.x - 1f, firstRect.yMax, 2f, stemY - firstRect.yMax), lineColor);
                FillRect(new Rect(combatPanel.center.x, stemY - 1f, mobilityPanel.center.x - combatPanel.center.x, 2f), lineColor);
                FillRect(new Rect(combatPanel.center.x - 1f, stemY, 2f, pathsY - stemY), lineColor);
                FillRect(new Rect(survivalPanel.center.x - 1f, stemY, 2f, pathsY - stemY), lineColor);
                FillRect(new Rect(mobilityPanel.center.x - 1f, stemY, 2f, pathsY - stemY), lineColor);
            }

            var sharedHeader = new Rect(w * 0.5f - 210f, 760f, 420f, 30f);
            FillRect(sharedHeader, new Color(0.032f, 0.043f, 0.050f, 1f));
            DrawBorder(sharedHeader, new Color(0.16f, 0.30f, 0.36f, 1f), 1f);
            GUI.Label(sharedHeader, string.IsNullOrEmpty(chosen) ? "ОБЩИЙ ПУТЬ — сначала выбери одну ветку" : "ОБЩИЙ ПУТЬ", _center);

            var pack2 = TalentCatalog.Find("legacy_pack2");
            var gold = TalentCatalog.Find("legacy_startgold");
            var sharedW = Mathf.Min(440f, w * 0.42f);
            var packRect = new Rect(w * 0.5f - sharedW * 0.5f, 805f, sharedW, 140f);
            var goldRect = new Rect(w * 0.5f - sharedW * 0.5f, 962f, sharedW, 140f);
            if (pack2 != null) DrawTalentNode(p, pack2, packRect);
            if (gold != null) DrawTalentNode(p, gold, goldRect);
            if (pack2 != null && gold != null)
                DrawConnection(packRect, goldRect, TalentCatalog.GetRank(p, "legacy_pack2") > 0 ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));

            GUI.EndScrollView();
        }

        private void DrawLegacyPathPanel(ProfileProgress p, Rect panel, string title, string pathId, string chosen, string[] talentIds)
        {
            var selected = string.Equals(chosen, pathId, StringComparison.OrdinalIgnoreCase);
            var locked = !string.IsNullOrEmpty(chosen) && !selected;
            var fill = selected ? new Color(0.025f, 0.070f, 0.075f, 1f) : locked ? new Color(0.024f, 0.027f, 0.030f, 1f) : new Color(0.013f, 0.020f, 0.024f, 1f);
            var border = selected ? new Color(0.20f, 0.68f, 0.66f, 1f) : locked ? new Color(0.16f, 0.18f, 0.20f, 1f) : new Color(0.18f, 0.31f, 0.36f, 1f);
            FillRect(panel, fill);
            DrawBorder(panel, border, selected ? 2f : 1f);

            var state = selected ? " ✓ ВЫБРАН" : locked ? " — ЗАБЛОКИРОВАН" : " — ВЫБЕРИ";
            GUI.Label(new Rect(panel.x + 5f, panel.y + 5f, panel.width - 10f, 29f), title + state, _center);

            Rect previous = default(Rect);
            for (var i = 0; i < talentIds.Length; i++)
            {
                var def = TalentCatalog.Find(talentIds[i]);
                if (def == null) continue;
                var rect = new Rect(panel.x + 8f, panel.y + 40f + i * 151f, panel.width - 16f, 140f);
                if (i > 0)
                {
                    var parent = TalentCatalog.Find(talentIds[i - 1]);
                    var active = parent != null && TalentCatalog.GetRank(p, parent.Id) > 0;
                    DrawConnection(previous, rect, active ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));
                }
                DrawTalentNode(p, def, rect);
                previous = rect;
            }
        }

        private void DrawClassSheet'''
ui, count = legacy_pattern.subn(legacy_method, ui, count=1)
if count != 1:
    raise RuntimeError("DrawLegacySheet replacement failed")

# The class base capstone needs more vertical room and a wider card than normal nodes.
ui = ui.replace("const float baseHeight = 820f;", "const float baseHeight = 980f;", 1)
ui = ui.replace("const float specHeight = 900f;", "const float specHeight = 950f;", 1)
ui = ui.replace(
'''            const float nodeHeight = 140f;''',
'''            var nodeHeight = def.Id.EndsWith("_void_capstone", StringComparison.OrdinalIgnoreCase) ? 190f :\n                def.Id.EndsWith("_legendary", StringComparison.OrdinalIgnoreCase) ? 160f : 140f;''', 1)

width_anchor = '''            var y = canvas.y + 5f + def.TreeRow * rowStep;\n            return new Rect(x, y, nodeWidth, nodeHeight);'''
width_replacement = '''            if (def.Id.EndsWith("_void_capstone", StringComparison.OrdinalIgnoreCase) && canvas.width >= 650f)\n            {\n                nodeWidth = Mathf.Clamp(canvas.width * 0.31f, 360f, 470f);\n                x = canvas.center.x - nodeWidth * 0.5f;\n            }\n            var y = canvas.y + 5f + def.TreeRow * rowStep;\n            return new Rect(x, y, nodeWidth, nodeHeight);'''
if width_anchor not in ui:
    raise RuntimeError("GetNodeRect width anchor not found")
ui = ui.replace(width_anchor, width_replacement, 1)

# Respect the mutually-exclusive Legacy choice in the actual button state and explain why a node is locked.
state_anchor = '''            var maxed = rank >= def.MaxRank;\n            var activeBranch = TalentCatalog.IsBranchActive(p, def.Branch);'''
state_replacement = '''            var maxed = rank >= def.MaxRank;\n            var legacyChoiceOk = ProgressionService.CanBuyLegacyPathTalent(p, def.Id);\n            var activeBranch = TalentCatalog.IsBranchActive(p, def.Branch);'''
if state_anchor not in ui:
    raise RuntimeError("DrawTalentNode state anchor not found")
ui = ui.replace(state_anchor, state_replacement, 1)

label_anchor = '''            var label = maxed ? "Изучено" : !levelOk ? $"Откроется: ур. {def.UnlockLevel}" : !prereq ? "Нужен предыдущий узел" : $"Изучить — {def.PointCost}";\n            GUI.enabled = levelOk && prereq && !maxed && p.unspentTalentPoints >= def.PointCost;'''
label_replacement = '''            var label = maxed ? "Изучено" : !legacyChoiceOk ? (def.Id == "legacy_pack2" ? "Сначала выбери путь" : "Выбран другой путь") : !levelOk ? $"Откроется: ур. {def.UnlockLevel}" : !prereq ? "Нужен предыдущий узел" : $"Изучить — {def.PointCost}";\n            GUI.enabled = legacyChoiceOk && levelOk && prereq && !maxed && p.unspentTalentPoints >= def.PointCost;'''
if label_anchor not in ui:
    raise RuntimeError("DrawTalentNode label anchor not found")
ui = ui.replace(label_anchor, label_replacement, 1)

# 0.4.1 already expanded normal descriptions; capstones get still more room.
desc_anchor = '''            GUI.Label(new Rect(textX, rect.y + 43f, textW, 56f), ShortEffect(def.Description), _nodeEffect);'''
desc_replacement = '''            GUI.Label(new Rect(textX, rect.y + 43f, textW, voidCapstone ? 96f : legendary ? 72f : 56f), ShortEffect(def.Description), _nodeEffect);'''
if desc_anchor not in ui:
    raise RuntimeError("Capstone description anchor not found")
ui = ui.replace(desc_anchor, desc_replacement, 1)

save(p, ui)


# ---------- Version ----------
p, t = rw("Plugin.cs")
t = t.replace('public const string PluginVersion = "0.6.1";', 'public const string PluginVersion = "0.6.2";', 1)
save(p, t)

p, t = rw("manifest.json")
t = t.replace('"version_number": "0.6.1"', '"version_number": "0.6.2"', 1)
t = t.replace('gameplay-first enemy affixes', 'gameplay-first enemy affixes, upward rarity scaling and a clearer exclusive Legacy path UI')
save(p, t)

p, t = rw("PetrichorLegacy.csproj")
t = t.replace('<Version>0.6.1</Version>', '<Version>0.6.2</Version>', 1)
save(p, t)

print("Applied PetrichorLegacy 0.6.2 progression/UI patch")

from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"


def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")


def save(p, text):
    p.write_text(text, encoding="utf-8")


def replace_talent_desc(text, talent_id, description):
    pattern = re.compile(r'(new TalentDef\("' + re.escape(talent_id) + r'",\s*"[^"]*",\s*")[^"]*(")')
    text2, count = pattern.subn(lambda m: m.group(1) + description + m.group(2), text, count=1)
    if count != 1:
        raise RuntimeError(f"Talent description not found: {talent_id}")
    return text2


# ---------- Full level 1-10 Legacy journey ----------
p, t = rw("Progression/TalentCatalog.cs")
start = t.index("            // НАСЛЕДИЕ")
end = t.index("            // СТРАЖ", start)
legacy = r'''            // НАСЛЕДИЕ — десять покупок к моменту открытия первого класса.
            new TalentDef("legacy_pack", "Первый трофей", "+1 вместимость стартового Арсенала. Базовая вместимость до этого равна 0.", TalentBranch.Legacy, 1, 1, 1, null, 0, 1, 0),

            // НАТИСК
            new TalentDef("legacy_damage", "Заточенное оружие", "+1.5% урона.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 0, 1),
            new TalentDef("legacy_attack", "Быстрая рука", "+1.5% скорости атаки.", TalentBranch.Legacy, 1, 1, 3, "legacy_damage", 1, 0, 2),
            new TalentDef("legacy_hunter", "Охотничий инстинкт", "+3% урона боссам и особым монстрам.", TalentBranch.Legacy, 1, 1, 4, "legacy_attack", 1, 0, 3),
            new TalentDef("legacy_precision", "Точный расчёт", "+1% шанса критического удара.", TalentBranch.Legacy, 1, 1, 5, "legacy_hunter", 1, 0, 4),
            new TalentDef("legacy_finisher", "Добивание", "+6% урона целям ниже 25% здоровья.", TalentBranch.Legacy, 1, 1, 6, "legacy_precision", 1, 0, 5),
            new TalentDef("legacy_momentum", "Боевой темп", "+1% урона и +1% скорости движения.", TalentBranch.Legacy, 1, 1, 7, "legacy_finisher", 1, 0, 6),

            // СТОЙКОСТЬ
            new TalentDef("legacy_hp", "Закалка", "+2% максимального здоровья.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 1, 1),
            new TalentDef("legacy_regen", "Полевой рацион", "+4% естественной регенерации.", TalentBranch.Legacy, 1, 1, 3, "legacy_hp", 1, 1, 2),
            new TalentDef("legacy_armor", "Крепкая кожа", "+2 брони.", TalentBranch.Legacy, 1, 1, 4, "legacy_regen", 1, 1, 3),
            new TalentDef("legacy_recovery", "Запас сил", "+2% максимального здоровья.", TalentBranch.Legacy, 1, 1, 5, "legacy_armor", 1, 1, 4),
            new TalentDef("legacy_resolve", "Упрямство", "Ниже 35% здоровья получаешь +3 брони.", TalentBranch.Legacy, 1, 1, 6, "legacy_recovery", 1, 1, 5),
            new TalentDef("legacy_secondwind", "Резервный щит", "+3% максимального здоровья в виде щита.", TalentBranch.Legacy, 1, 1, 7, "legacy_resolve", 1, 1, 6),

            // МАНЁВР
            new TalentDef("legacy_move", "Лёгкая поступь", "+2% скорости движения.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 2, 1),
            new TalentDef("legacy_sprint", "Марш-бросок", "+3% скорости спринта.", TalentBranch.Legacy, 1, 1, 3, "legacy_move", 1, 2, 2),
            new TalentDef("legacy_jump", "Лёгкое снаряжение", "+8% силы прыжка.", TalentBranch.Legacy, 1, 1, 4, "legacy_sprint", 1, 2, 3),
            new TalentDef("legacy_evasion", "Смена позиции", "+1.5% скорости движения.", TalentBranch.Legacy, 1, 1, 5, "legacy_jump", 1, 2, 4),
            new TalentDef("legacy_stride", "Длинный шаг", "Ещё +2% скорости спринта.", TalentBranch.Legacy, 1, 1, 6, "legacy_evasion", 1, 2, 5),
            new TalentDef("legacy_aircontrol", "Чувство дистанции", "+5% силы прыжка.", TalentBranch.Legacy, 1, 1, 7, "legacy_stride", 1, 2, 6),

            // Общая концовка: уровни 8-10.
            new TalentDef("legacy_pack2", "Экспедиционный ранец", "+1 вместимость стартового Арсенала.", TalentBranch.Legacy, 1, 1, 8, "legacy_pack", 1, 1, 7),
            new TalentDef("legacy_startgold", "Заначка", "+15 золота в начале каждого забега.", TalentBranch.Legacy, 1, 1, 9, "legacy_pack2", 1, 1, 8),
            new TalentDef("legacy_fieldcraft", "Полевой опыт", "+5% мета-опыта за убийство особых монстров.", TalentBranch.Legacy, 1, 1, 10, "legacy_startgold", 1, 1, 9),

'''
t = t[:start] + legacy + t[end:]

# Capstones should explain the reward, not merely name it.
descriptions = {
    "guardian_void_capstone": "Даёт Safer Spaces: полностью блокирует следующий полученный удар, затем эффект перезаряжается.",
    "slayer_void_capstone": "Даёт Needletick: попадания могут наложить Collapse и вызвать отложенный взрывной урон.",
    "path_void_capstone": "Даёт Polylute: попадания могут вызвать серию повторных электрических ударов по цели.",
    "seeker_void_capstone": "Даёт Encrusted Key: на каждой стадии появляется скрытый Void-тайник с наградой.",
    "arcanist_void_capstone": "Даёт Lysate Cell: добавляет дополнительный заряд специального навыка.",
    "tech_void_capstone": "Даёт Plasma Shrimp: пока есть щит, попадания запускают самонаводящиеся ракеты.",
    "commander_void_capstone": "Даёт Singularity Band: сильные попадания создают чёрную дыру, стягивающую врагов и затем взрывающуюся.",

    "bastion_legendary": "Даёт Aegis: лечение сверх полного здоровья превращает часть перелечения во временный барьер.",
    "unbroken_legendary": "Даёт Rejuvenation Rack: всё получаемое лечение становится значительно сильнее.",
    "vanguard_legendary": "Даёт Shattering Justice: серия попаданий снижает броню цели и усиливает последующий урон по ней.",
    "executioner_legendary": "Даёт Ceremonial Dagger: убийства выпускают самонаводящиеся кинжалы по ближайшим врагам.",
    "hunter_legendary": "Даёт Wake of Vultures: убийство элитного врага временно даёт его элитную силу.",
    "berserker_legendary": "Даёт Unstable Tesla Coil: периодически поражает молниями ближайших врагов вокруг тебя.",
    "scout_legendary": "Даёт Alien Head: сокращает время восстановления всех навыков.",
    "acro_legendary": "Даёт Hardlight Afterburner: добавляет заряды Utility-навыка и ускоряет его восстановление.",
    "saboteur_legendary": "Даёт Sentient Meat Hook: попадания могут зацепить, притянуть и повредить соседних врагов.",
    "merchant_legendary": "Даёт War Bonds: в боях с боссами вызывает ракетный обстрел; чем больше золота заработано заранее, тем больше ракет.",
    "prospector_legendary": "Даёт 57 Leaf Clover: неблагоприятные случайные результаты перебрасываются в твою пользу.",
    "relic_legendary": "Даёт Soulbound Catalyst: убийства сокращают перезарядку экипировки.",
    "chrono_legendary": "Даёт Brainstalks: убийство элиты на короткое время почти убирает перезарядки навыков.",
    "hex_legendary": "Даёт Symbiotic Scorpion: каждое попадание всё сильнее снижает броню цели, пока она жива.",
    "storm_legendary": "Даёт Resonance Disc: быстрые убийства заряжают диск, который сам пронзает врагов и мощно взрывается.",
    "drone_legendary": "Даёт Spare Drone Parts: усиливает дронов, добавляет им ракеты и цепную пушку, а также даёт боевого дрона-компаньона.",
    "interceptor_legendary": "Даёт Defensive Microbots: автоматически сбивает ближайшие вражеские снаряды; перезарядка ускоряется от скорости атаки.",
    "constructor_legendary": "Даёт Orphaned Core: призывает дружелюбного Solus, который таранит врагов, наследует предметы скорости и сильнее бьёт на ходу.",
    "tactician_legendary": "Даёт Growth Nectar: каждый активный уникальный бафф повышает все основные характеристики, вплоть до четырёх баффов.",
    "standard_legendary": "Даёт Interstellar Desk Plant: убийства выращивают лечебные растения, создающие область восстановления здоровья для союзников.",
    "warlord_legendary": "Даёт Happiest Mask: убийства иногда создают временного усиленного призрака убитого врага на твоей стороне.",
}
for talent_id, description in descriptions.items():
    t = replace_talent_desc(t, talent_id, description)
save(p, t)


# ---------- One chosen Legacy direction, with softer wording ----------
p, t = rw("Progression/ProgressionService.cs")
old_helpers = r'''        public static string LegacyPathForTalent(string talentId)
        {
            switch (talentId)
            {
                case "legacy_damage":
                case "legacy_attack":
                case "legacy_hunter": return "combat";
                case "legacy_hp":
                case "legacy_regen":
                case "legacy_armor": return "survival";
                case "legacy_move":
                case "legacy_sprint":
                case "legacy_jump": return "mobility";
                default: return string.Empty;
            }
        }

        public static string LegacyPathChoice(ProfileProgress profile)
        {
            if (profile == null) return string.Empty;
            if (TalentCatalog.GetRank(profile, "legacy_damage") > 0 || TalentCatalog.GetRank(profile, "legacy_attack") > 0 || TalentCatalog.GetRank(profile, "legacy_hunter") > 0) return "combat";
            if (TalentCatalog.GetRank(profile, "legacy_hp") > 0 || TalentCatalog.GetRank(profile, "legacy_regen") > 0 || TalentCatalog.GetRank(profile, "legacy_armor") > 0) return "survival";
            if (TalentCatalog.GetRank(profile, "legacy_move") > 0 || TalentCatalog.GetRank(profile, "legacy_sprint") > 0 || TalentCatalog.GetRank(profile, "legacy_jump") > 0) return "mobility";
            return string.Empty;
        }'''
new_helpers = r'''        public static string LegacyPathForTalent(string talentId)
        {
            switch (talentId)
            {
                case "legacy_damage": case "legacy_attack": case "legacy_hunter": case "legacy_precision": case "legacy_finisher": case "legacy_momentum": return "combat";
                case "legacy_hp": case "legacy_regen": case "legacy_armor": case "legacy_recovery": case "legacy_resolve": case "legacy_secondwind": return "survival";
                case "legacy_move": case "legacy_sprint": case "legacy_jump": case "legacy_evasion": case "legacy_stride": case "legacy_aircontrol": return "mobility";
                default: return string.Empty;
            }
        }

        public static string LegacyPathChoice(ProfileProgress profile)
        {
            if (profile == null) return string.Empty;
            var ids = new[]
            {
                "legacy_damage", "legacy_attack", "legacy_hunter", "legacy_precision", "legacy_finisher", "legacy_momentum",
                "legacy_hp", "legacy_regen", "legacy_armor", "legacy_recovery", "legacy_resolve", "legacy_secondwind",
                "legacy_move", "legacy_sprint", "legacy_jump", "legacy_evasion", "legacy_stride", "legacy_aircontrol"
            };
            foreach (var id in ids)
                if (TalentCatalog.GetRank(profile, id) > 0) return LegacyPathForTalent(id);
            return string.Empty;
        }'''
if old_helpers not in t:
    raise RuntimeError("Legacy path helpers not found")
t = t.replace(old_helpers, new_helpers, 1)
t = t.replace('error = "В Наследии можно выбрать только один путь. Сбрось таланты, чтобы сменить его.";', 'error = "Это направление уже недоступно для текущего Наследия.";')
t = t.replace('error = "Сначала выбери один из трёх путей Наследия.";', 'error = "Сначала продвинься дальше по Наследию.";')
save(p, t)


# ---------- Effects for the extra early nodes, using existing hooks only ----------
p, t = rw("Progression/TalentEffects.cs")
anchor = '''            self.regen *= 1f + ServerProgressionState.Rank(self.master, "legacy_regen") * 0.04f;'''
if anchor not in t:
    raise RuntimeError("Legacy passive anchor not found")
t = t.replace(anchor, anchor + r'''
            self.crit += ServerProgressionState.Rank(self.master, "legacy_precision");
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "legacy_momentum") * 0.01f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_momentum") * 0.01f;
            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "legacy_recovery") * 0.02f;
            if (ServerProgressionState.Rank(self.master, "legacy_resolve") > 0 && self.healthComponent != null && self.healthComponent.combinedHealthFraction < 0.35f)
                self.armor += 3f;
            self.maxShield += self.baseMaxHealth * ServerProgressionState.Rank(self.master, "legacy_secondwind") * 0.03f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_evasion") * 0.015f;
            self.sprintingSpeedMultiplier *= 1f + ServerProgressionState.Rank(self.master, "legacy_stride") * 0.02f;
            self.jumpPower *= 1f + ServerProgressionState.Rank(self.master, "legacy_aircontrol") * 0.05f;''', 1)

damage_anchor = '''                var legacyHunter = ServerProgressionState.Rank(attackerBody.master, "legacy_hunter");
                if (legacyHunter > 0 && (victimBody.isBoss || victimBody.GetComponent<MonsterRarityMarker>() != null))
                    damageInfo.damage *= 1f + legacyHunter * 0.03f;'''
if damage_anchor not in t:
    raise RuntimeError("Legacy hunter damage anchor not found")
t = t.replace(damage_anchor, damage_anchor + r'''
                if (ServerProgressionState.Rank(attackerBody.master, "legacy_finisher") > 0 && victimBody.healthComponent != null && victimBody.healthComponent.combinedHealthFraction < 0.25f)
                    damageInfo.damage *= 1.06f;''', 1)
save(p, t)


# ---------- Level 10 fieldcraft: more meta XP from special monsters ----------
p, t = rw("Progression/MonsterRaritySystem.cs")
xp_anchor = '''            xpMultiplier += ServerProgressionState.Rank(report.attackerMaster, "hunter_specialxp") * 0.05f;'''
if xp_anchor not in t:
    raise RuntimeError("Monster rarity XP multiplier anchor not found")
t = t.replace(xp_anchor, xp_anchor + r'''
            xpMultiplier += ServerProgressionState.Rank(report.attackerMaster, "legacy_fieldcraft") * 0.05f;''', 1)
save(p, t)


# ---------- Save schema 6: additive extension only ----------
p, t = rw("Models/ProfileProgress.cs")
if "public int schemaVersion = 5;" not in t:
    raise RuntimeError("Profile schema 5 not found")
t = t.replace("public int schemaVersion = 5;", "public int schemaVersion = 6;", 1)
save(p, t)

p, t = rw("Persistence/SaveService.cs")
v5_end = '''                p.schemaVersion = 5;
            }'''
if v5_end not in t:
    raise RuntimeError("SaveService v5 migration end not found")
t = t.replace(v5_end, v5_end + r'''

            if (p.schemaVersion < 6)
            {
                p.schemaVersion = 6;
            }''', 1)
save(p, t)


# ---------- UI: six nodes per direction, subtle selection, correct item icons ----------
p, ui = rw("UI/MetaProgressionUIV5.cs")
ui = ui.replace('GUI.Label(notice, "ВЫБЕРИ 1 ИЗ 3 ПУТЕЙ — после первого таланта две остальные ветки блокируются", _center);',
                'GUI.Label(notice, "ПЕРВЫЕ ШАГИ — три разных подхода к подготовке перед классом", _center);')
ui = ui.replace('DrawLegacyPathPanel(p, combatPanel, "БОЕВОЙ ПУТЬ", "combat", chosen, new[] { "legacy_damage", "legacy_attack", "legacy_hunter" });',
                'DrawLegacyPathPanel(p, combatPanel, "НАТИСК", "combat", chosen, new[] { "legacy_damage", "legacy_attack", "legacy_hunter", "legacy_precision", "legacy_finisher", "legacy_momentum" });')
ui = ui.replace('DrawLegacyPathPanel(p, survivalPanel, "ПУТЬ ВЫЖИВАНИЯ", "survival", chosen, new[] { "legacy_hp", "legacy_regen", "legacy_armor" });',
                'DrawLegacyPathPanel(p, survivalPanel, "СТОЙКОСТЬ", "survival", chosen, new[] { "legacy_hp", "legacy_regen", "legacy_armor", "legacy_recovery", "legacy_resolve", "legacy_secondwind" });')
ui = ui.replace('DrawLegacyPathPanel(p, mobilityPanel, "ПУТЬ ПОДВИЖНОСТИ", "mobility", chosen, new[] { "legacy_move", "legacy_sprint", "legacy_jump" });',
                'DrawLegacyPathPanel(p, mobilityPanel, "МАНЁВР", "mobility", chosen, new[] { "legacy_move", "legacy_sprint", "legacy_jump", "legacy_evasion", "legacy_stride", "legacy_aircontrol" });')
ui = ui.replace('const float contentHeight = 1110f;', 'const float contentHeight = 1745f;')
ui = ui.replace('var pathH = 505f;', 'var pathH = 960f;')
ui = ui.replace('var sharedHeader = new Rect(w * 0.5f - 210f, 760f, 420f, 30f);', 'var sharedHeader = new Rect(w * 0.5f - 210f, 1215f, 420f, 30f);')
ui = ui.replace('GUI.Label(sharedHeader, string.IsNullOrEmpty(chosen) ? "ОБЩИЙ ПУТЬ — сначала выбери одну ветку" : "ОБЩИЙ ПУТЬ", _center);',
                'GUI.Label(sharedHeader, "СНАРЯЖЕНИЕ И ОПЫТ", _center);')
ui = ui.replace('var packRect = new Rect(w * 0.5f - sharedW * 0.5f, 805f, sharedW, 140f);', 'var packRect = new Rect(w * 0.5f - sharedW * 0.5f, 1260f, sharedW, 140f);')
ui = ui.replace('var goldRect = new Rect(w * 0.5f - sharedW * 0.5f, 962f, sharedW, 140f);', 'var goldRect = new Rect(w * 0.5f - sharedW * 0.5f, 1417f, sharedW, 140f);')

shared_block = '''            if (pack2 != null) DrawTalentNode(p, pack2, packRect);
            if (gold != null) DrawTalentNode(p, gold, goldRect);
            if (pack2 != null && gold != null)
                DrawConnection(packRect, goldRect, TalentCatalog.GetRank(p, "legacy_pack2") > 0 ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));'''
shared_new = '''            var fieldcraft = TalentCatalog.Find("legacy_fieldcraft");
            var fieldRect = new Rect(w * 0.5f - sharedW * 0.5f, 1574f, sharedW, 140f);
            if (pack2 != null) DrawTalentNode(p, pack2, packRect);
            if (gold != null) DrawTalentNode(p, gold, goldRect);
            if (fieldcraft != null) DrawTalentNode(p, fieldcraft, fieldRect);
            if (pack2 != null && gold != null)
                DrawConnection(packRect, goldRect, TalentCatalog.GetRank(p, "legacy_pack2") > 0 ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));
            if (gold != null && fieldcraft != null)
                DrawConnection(goldRect, fieldRect, TalentCatalog.GetRank(p, "legacy_startgold") > 0 ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));'''
if shared_block not in ui:
    raise RuntimeError("Legacy shared UI block not found")
ui = ui.replace(shared_block, shared_new, 1)

state_line = '''            var state = selected ? " ✓ ВЫБРАН" : locked ? " — ЗАБЛОКИРОВАН" : " — ВЫБЕРИ";
            GUI.Label(new Rect(panel.x + 5f, panel.y + 5f, panel.width - 10f, 29f), title + state, _center);'''
if state_line not in ui:
    raise RuntimeError("Legacy path header state not found")
ui = ui.replace(state_line, '''            GUI.Label(new Rect(panel.x + 5f, panel.y + 5f, panel.width - 10f, 29f), title, _center);''', 1)
ui = ui.replace('var rect = new Rect(panel.x + 8f, panel.y + 40f + i * 151f, panel.width - 16f, 140f);',
                'var rect = new Rect(panel.x + 8f, panel.y + 40f + i * 151f, panel.width - 16f, 140f);')
ui = ui.replace('var label = maxed ? "Изучено" : !legacyChoiceOk ? (def.Id == "legacy_pack2" ? "Сначала выбери путь" : "Выбран другой путь") : !levelOk ?',
                'var label = maxed ? "Изучено" : !legacyChoiceOk ? (def.Id == "legacy_pack2" ? "Продвинься дальше" : "Недоступно") : !levelOk ?')

# Explicit icons override the older semantic/fallback mapping.
icon_anchor = '''            id = (id ?? string.Empty).ToLowerInvariant();'''
icon_block = r'''            id = (id ?? string.Empty).ToLowerInvariant();

            // Legacy: distinct readable icons, no repeating placeholders across the starting tree.
            if (id == "legacy_pack") return new[] { "TreasureCache" };
            if (id == "legacy_damage") return new[] { "Crowbar" };
            if (id == "legacy_attack") return new[] { "Syringe" };
            if (id == "legacy_hunter") return new[] { "BossDamageBonus" };
            if (id == "legacy_precision") return new[] { "CritGlasses" };
            if (id == "legacy_finisher") return new[] { "ExecuteLowHealthElite" };
            if (id == "legacy_momentum") return new[] { "WarCryOnMultiKill" };
            if (id == "legacy_hp") return new[] { "Infusion" };
            if (id == "legacy_regen") return new[] { "HealWhileSafe" };
            if (id == "legacy_armor") return new[] { "ArmorPlate" };
            if (id == "legacy_recovery") return new[] { "Medkit" };
            if (id == "legacy_resolve") return new[] { "Knurl" };
            if (id == "legacy_secondwind") return new[] { "BarrierOnKill" };
            if (id == "legacy_move") return new[] { "Hoof" };
            if (id == "legacy_sprint") return new[] { "SprintBonus" };
            if (id == "legacy_jump") return new[] { "Feather" };
            if (id == "legacy_evasion") return new[] { "SprintOutOfCombat" };
            if (id == "legacy_stride") return new[] { "JumpBoost" };
            if (id == "legacy_aircontrol") return new[] { "SecondarySkillMagazine" };
            if (id == "legacy_pack2") return new[] { "EquipmentMagazine" };
            if (id == "legacy_startgold") return new[] { "GoldOnHurt" };
            if (id == "legacy_fieldcraft") return new[] { "HeadHunter" };

            // Class/spec capstones always show the icon of the item actually granted.
            if (id == "guardian_void_capstone") return new[] { "BearVoid" };
            if (id == "slayer_void_capstone") return new[] { "BleedOnHitVoid" };
            if (id == "path_void_capstone") return new[] { "ChainLightningVoid" };
            if (id == "seeker_void_capstone") return new[] { "TreasureCacheVoid" };
            if (id == "arcanist_void_capstone") return new[] { "EquipmentMagazineVoid" };
            if (id == "tech_void_capstone") return new[] { "MissileVoid" };
            if (id == "commander_void_capstone") return new[] { "ElementalRingVoid" };
            if (id == "bastion_legendary") return new[] { "BarrierOnOverHeal" };
            if (id == "unbroken_legendary") return new[] { "IncreaseHealing" };
            if (id == "vanguard_legendary") return new[] { "ArmorReductionOnHit" };
            if (id == "executioner_legendary") return new[] { "Dagger" };
            if (id == "hunter_legendary") return new[] { "HeadHunter" };
            if (id == "berserker_legendary") return new[] { "ShockNearby" };
            if (id == "scout_legendary") return new[] { "AlienHead" };
            if (id == "acro_legendary") return new[] { "UtilitySkillMagazine" };
            if (id == "saboteur_legendary") return new[] { "BounceNearby" };
            if (id == "merchant_legendary") return new[] { "BarrageOnBoss" };
            if (id == "prospector_legendary") return new[] { "Clover" };
            if (id == "relic_legendary") return new[] { "Talisman" };
            if (id == "chrono_legendary") return new[] { "KillEliteFrenzy" };
            if (id == "hex_legendary") return new[] { "PermanentDebuffOnHit" };
            if (id == "storm_legendary") return new[] { "LaserTurbine" };
            if (id == "drone_legendary") return new[] { "DroneWeapons" };
            if (id == "interceptor_legendary") return new[] { "CaptainDefenseMatrix" };
            if (id == "constructor_legendary") return new[] { "PhysicsProjectile" };
            if (id == "tactician_legendary") return new[] { "BoostAllStats" };
            if (id == "standard_legendary") return new[] { "Plant" };
            if (id == "warlord_legendary") return new[] { "GhostOnKill" };'''
if icon_anchor not in ui:
    raise RuntimeError("PreferredIconCandidates anchor not found")
ui = ui.replace(icon_anchor, icon_block, 1)
save(p, ui)


# ---------- Version ----------
p, t = rw("Plugin.cs")
t = t.replace('public const string PluginVersion = "0.6.2";', 'public const string PluginVersion = "0.6.3";')
save(p, t)

p, t = rw("manifest.json")
t = t.replace('"version_number": "0.6.2"', '"version_number": "0.6.3"')
save(p, t)

p, t = rw("PetrichorLegacy.csproj")
t = t.replace('<Version>0.6.2</Version>', '<Version>0.6.3</Version>')
save(p, t)

print("Applied PetrichorLegacy 0.6.3 Legacy/icons/descriptions patch")

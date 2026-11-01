from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"


def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")


def save(p, text):
    p.write_text(text, encoding="utf-8")


# ---------- Expand Legacy to a full ten-step level 1-10 journey ----------
p, t = rw("Progression/TalentCatalog.cs")
start = t.index("            // НАСЛЕДИЕ")
end = t.index("            // СТРАЖ", start)
legacy = r'''            // НАСЛЕДИЕ — десять ранних шагов до и на пороге первого класса.
            new TalentDef("legacy_pack", "Первый трофей", "+1 вместимость стартового Арсенала. Базовая вместимость до этого равна 0.", TalentBranch.Legacy, 1, 1, 1, null, 0, 1, 0),

            // Три направления. После первого купленного узла остальные направления закрываются.
            // НАТИСК
            new TalentDef("legacy_damage", "Заточенное оружие", "+1.5% урона.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 0, 1),
            new TalentDef("legacy_attack", "Быстрая рука", "+1.5% скорости атаки.", TalentBranch.Legacy, 1, 1, 3, "legacy_damage", 1, 0, 2),
            new TalentDef("legacy_hunter", "Охотничий инстинкт", "+3% урона боссам и особым монстрам.", TalentBranch.Legacy, 1, 1, 4, "legacy_attack", 1, 0, 3),
            new TalentDef("legacy_pressure", "Давление", "После убийства особого монстра на 6 сек. +5% скорости атаки.", TalentBranch.Legacy, 1, 1, 5, "legacy_hunter", 1, 0, 4),
            new TalentDef("legacy_finisher", "Добивание", "+6% урона целям ниже 25% здоровья.", TalentBranch.Legacy, 1, 1, 6, "legacy_pressure", 1, 0, 5),
            new TalentDef("legacy_momentum", "Боевой темп", "После убийства врага на 4 сек. +4% скорости движения; эффект обновляется.", TalentBranch.Legacy, 1, 1, 7, "legacy_finisher", 1, 0, 6),

            // СТОЙКОСТЬ
            new TalentDef("legacy_hp", "Закалка", "+2% максимального здоровья.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 1, 1),
            new TalentDef("legacy_regen", "Полевой рацион", "+4% естественной регенерации.", TalentBranch.Legacy, 1, 1, 3, "legacy_hp", 1, 1, 2),
            new TalentDef("legacy_armor", "Крепкая кожа", "+2 брони.", TalentBranch.Legacy, 1, 1, 4, "legacy_regen", 1, 1, 3),
            new TalentDef("legacy_recovery", "Передышка", "После 5 сек. без полученного урона регенерация усиливается ещё на 15%.", TalentBranch.Legacy, 1, 1, 5, "legacy_armor", 1, 1, 4),
            new TalentDef("legacy_resolve", "Упрямство", "Ниже 35% здоровья получаешь +5 брони.", TalentBranch.Legacy, 1, 1, 6, "legacy_recovery", 1, 1, 5),
            new TalentDef("legacy_secondwind", "Второе дыхание", "Раз за стадию при падении ниже 25% здоровья получаешь небольшой барьер.", TalentBranch.Legacy, 1, 1, 7, "legacy_resolve", 1, 1, 6),

            // МАНЁВР
            new TalentDef("legacy_move", "Лёгкая поступь", "+2% скорости движения.", TalentBranch.Legacy, 1, 1, 2, "legacy_pack", 1, 2, 1),
            new TalentDef("legacy_sprint", "Марш-бросок", "+3% скорости спринта.", TalentBranch.Legacy, 1, 1, 3, "legacy_move", 1, 2, 2),
            new TalentDef("legacy_jump", "Лёгкое снаряжение", "+8% силы прыжка.", TalentBranch.Legacy, 1, 1, 4, "legacy_sprint", 1, 2, 3),
            new TalentDef("legacy_evasion", "Смена позиции", "После получения урона на 2 сек. +8% скорости движения.", TalentBranch.Legacy, 1, 1, 5, "legacy_jump", 1, 2, 4),
            new TalentDef("legacy_stride", "Длинный шаг", "Во время спринта ещё +3% скорости движения.", TalentBranch.Legacy, 1, 1, 6, "legacy_evasion", 1, 2, 5),
            new TalentDef("legacy_aircontrol", "Чувство дистанции", "В воздухе +6% скорости движения.", TalentBranch.Legacy, 1, 1, 7, "legacy_stride", 1, 2, 6),

            // Общая концовка раннего пути: уровни 8-10.
            new TalentDef("legacy_pack2", "Экспедиционный ранец", "+1 вместимость стартового Арсенала.", TalentBranch.Legacy, 1, 1, 8, "legacy_pack", 1, 1, 7),
            new TalentDef("legacy_startgold", "Заначка", "+15 золота в начале каждого забега.", TalentBranch.Legacy, 1, 1, 9, "legacy_pack2", 1, 1, 8),
            new TalentDef("legacy_fieldcraft", "Полевой опыт", "+5% мета-опыта за особых монстров.", TalentBranch.Legacy, 1, 1, 10, "legacy_startgold", 1, 1, 9),

'''
t = t[:start] + legacy + t[end:]
save(p, t)


# ---------- Path rules: include all six branch nodes and soften wording ----------
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
                case "legacy_damage": case "legacy_attack": case "legacy_hunter":
                case "legacy_pressure": case "legacy_finisher": case "legacy_momentum": return "combat";
                case "legacy_hp": case "legacy_regen": case "legacy_armor":
                case "legacy_recovery": case "legacy_resolve": case "legacy_secondwind": return "survival";
                case "legacy_move": case "legacy_sprint": case "legacy_jump":
                case "legacy_evasion": case "legacy_stride": case "legacy_aircontrol": return "mobility";
                default: return string.Empty;
            }
        }

        public static string LegacyPathChoice(ProfileProgress profile)
        {
            if (profile == null) return string.Empty;
            var ids = new[]
            {
                "legacy_damage", "legacy_attack", "legacy_hunter", "legacy_pressure", "legacy_finisher", "legacy_momentum",
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
t = t.replace('error = "Сначала выбери один из трёх путей Наследия.";', 'error = "Сначала продвинься по одному из направлений Наследия.";')
save(p, t)


# ---------- Runtime effects for the extra Legacy nodes ----------
p, t = rw("Progression/TalentEffects.cs")
# Add passive stat effects after existing legacy movement block.
anchor = '''            self.regen *= 1f + ServerProgressionState.Rank(self.master, "legacy_regen") * 0.04f;'''
if anchor not in t:
    raise RuntimeError("Legacy passive anchor not found")
t = t.replace(anchor, anchor + r'''
            if (ServerProgressionState.Rank(self.master, "legacy_resolve") > 0 && self.healthComponent != null && self.healthComponent.combinedHealthFraction < 0.35f)
                self.armor += 5f;
            if (ServerProgressionState.Rank(self.master, "legacy_stride") > 0 && self.isSprinting)
                self.moveSpeed *= 1.03f;
            if (ServerProgressionState.Rank(self.master, "legacy_aircontrol") > 0 && self.characterMotor != null && !self.characterMotor.isGrounded)
                self.moveSpeed *= 1.06f;''', 1)

# Finisher is cleanly handled in the existing damage hook.
damage_anchor = '''                var legacyHunter = ServerProgressionState.Rank(attackerBody.master, "legacy_hunter");
                if (legacyHunter > 0 && (victimBody.isBoss || victimBody.GetComponent<MonsterRarityMarker>() != null))
                    damageInfo.damage *= 1f + legacyHunter * 0.03f;'''
if damage_anchor not in t:
    raise RuntimeError("Legacy hunter damage anchor not found")
t = t.replace(damage_anchor, damage_anchor + r'''
                if (ServerProgressionState.Rank(attackerBody.master, "legacy_finisher") > 0 && victimBody.healthComponent != null && victimBody.healthComponent.combinedHealthFraction < 0.25f)
                    damageInfo.damage *= 1.06f;''', 1)
save(p, t)


# ---------- Lightweight runtime controller for conditional early effects ----------
p, t = rw("Progression/MetaRuntimeController.cs")
# Preserve existing controller and append an independent server-side component.
if "LegacyEarlyRuntime" not in t:
    t += r'''

namespace PetrichorLegacy.Progression
{
    public sealed class LegacyEarlyRuntime : UnityEngine.MonoBehaviour
    {
        private RoR2.CharacterBody _body;
        private float _lastDamageTime = -100f;
        private float _evadeUntil;
        private float _pressureUntil;
        private float _momentumUntil;
        private bool _secondWindUsed;

        public static void Attach(RoR2.CharacterBody body)
        {
            if (body == null || body.master == null) return;
            if (body.GetComponent<LegacyEarlyRuntime>() == null)
                body.gameObject.AddComponent<LegacyEarlyRuntime>();
        }

        private void Awake() { _body = GetComponent<RoR2.CharacterBody>(); }

        public void NotifyDamaged()
        {
            _lastDamageTime = UnityEngine.Time.fixedTime;
            if (_body != null && _body.master != null && ServerProgressionState.Rank(_body.master, "legacy_evasion") > 0)
                _evadeUntil = UnityEngine.Time.fixedTime + 2f;
        }

        public void NotifyKill(bool special)
        {
            if (_body == null || _body.master == null) return;
            if (special && ServerProgressionState.Rank(_body.master, "legacy_pressure") > 0)
                _pressureUntil = UnityEngine.Time.fixedTime + 6f;
            if (ServerProgressionState.Rank(_body.master, "legacy_momentum") > 0)
                _momentumUntil = UnityEngine.Time.fixedTime + 4f;
        }

        private void FixedUpdate()
        {
            if (_body == null || _body.master == null || _body.healthComponent == null) return;
            var recalc = false;
            if (_evadeUntil > UnityEngine.Time.fixedTime || _pressureUntil > UnityEngine.Time.fixedTime || _momentumUntil > UnityEngine.Time.fixedTime ||
                (ServerProgressionState.Rank(_body.master, "legacy_recovery") > 0 && UnityEngine.Time.fixedTime - _lastDamageTime > 5f)) recalc = true;

            if (!_secondWindUsed && ServerProgressionState.Rank(_body.master, "legacy_secondwind") > 0 && _body.healthComponent.combinedHealthFraction < 0.25f)
            {
                _body.healthComponent.AddBarrier(_body.maxHealth * 0.12f);
                _secondWindUsed = true;
            }
            if (recalc && UnityEngine.Time.frameCount % 45 == 0) _body.RecalculateStats();
        }

        public bool EvasionActive => UnityEngine.Time.fixedTime < _evadeUntil;
        public bool PressureActive => UnityEngine.Time.fixedTime < _pressureUntil;
        public bool MomentumActive => UnityEngine.Time.fixedTime < _momentumUntil;
        public bool RecoveryActive => UnityEngine.Time.fixedTime - _lastDamageTime > 5f;
    }
}
'''
save(p, t)

# Wire the conditional runtime into TalentEffects hooks without adding new external dependencies.
p, t = rw("Progression/TalentEffects.cs")
install_anchor = '''            On.RoR2.CharacterBody.RecalculateStats += CharacterBody_RecalculateStats;'''
if install_anchor in t and "LegacyEarlyRuntime.Attach" not in t:
    # Attach opportunistically whenever stats recalc for a player body.
    recalc_anchor = '''            if (self == null || self.master == null) return;'''
    if recalc_anchor not in t:
        raise RuntimeError("TalentEffects recalc anchor not found")
    t = t.replace(recalc_anchor, recalc_anchor + r'''
            if (self.teamComponent != null && self.teamComponent.teamIndex == TeamIndex.Player)
                LegacyEarlyRuntime.Attach(self);''', 1)

    # Conditional buffs are applied during recalc.
    passive_anchor = '''            if (ServerProgressionState.Rank(self.master, "legacy_aircontrol") > 0 && self.characterMotor != null && !self.characterMotor.isGrounded)
                self.moveSpeed *= 1.06f;'''
    if passive_anchor not in t:
        raise RuntimeError("Extra legacy passive anchor not found")
    t = t.replace(passive_anchor, passive_anchor + r'''
            var legacyEarly = self.GetComponent<LegacyEarlyRuntime>();
            if (legacyEarly != null)
            {
                if (legacyEarly.EvasionActive) self.moveSpeed *= 1.08f;
                if (legacyEarly.PressureActive) self.attackSpeed *= 1.05f;
                if (legacyEarly.MomentumActive) self.moveSpeed *= 1.04f;
                if (legacyEarly.RecoveryActive && ServerProgressionState.Rank(self.master, "legacy_recovery") > 0) self.regen *= 1.15f;
            }''', 1)

    # Damage notification uses victim player body in the existing TakeDamage hook.
    victim_anchor = '''            var victimBody = self != null ? self.body : null;'''
    if victim_anchor not in t:
        raise RuntimeError("TalentEffects victim anchor not found")
    t = t.replace(victim_anchor, victim_anchor + r'''
            if (victimBody != null && victimBody.teamComponent != null && victimBody.teamComponent.teamIndex == TeamIndex.Player)
            {
                var early = victimBody.GetComponent<LegacyEarlyRuntime>();
                if (early != null) early.NotifyDamaged();
            }''', 1)
save(p, t)

# Kill notifications + special XP bonus in MonsterRaritySystem death path.
p, t = rw("Progression/MonsterRaritySystem.cs")
# We use the existing global death event for both normal and special kills.
kill_anchor = '''        private static void OnCharacterDeath(DamageReport report)
        {'''
if kill_anchor not in t:
    raise RuntimeError("Monster rarity death hook not found")
# Insert near beginning only once.
t = t.replace(kill_anchor, kill_anchor + r'''
            var killerBodyForLegacy = report?.attackerBody;
            if (killerBodyForLegacy != null)
            {
                var early = killerBodyForLegacy.GetComponent<LegacyEarlyRuntime>();
                var victimMarkerForLegacy = report.victimBody != null ? report.victimBody.GetComponent<MonsterRarityMarker>() : null;
                if (early != null) early.NotifyKill(victimMarkerForLegacy != null);
            }''', 1)
# Apply 5% bonus to meta XP for special monsters at reward calculation.
xp_pattern = re.compile(r'(var xp\s*=\s*[^;]+;)')
m = xp_pattern.search(t, t.index(kill_anchor))
if m:
    replacement = m.group(1) + r'''
            if (report?.attackerMaster != null && ServerProgressionState.Rank(report.attackerMaster, "legacy_fieldcraft") > 0)
                xp = Mathf.Max(1, Mathf.RoundToInt(xp * 1.05f));'''
    t = t[:m.start()] + replacement + t[m.end():]
else:
    raise RuntimeError("Special monster XP calculation not found")
save(p, t)


# ---------- Save migration to schema 6: new nodes are additive, no destructive reset ----------
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
                // New Legacy nodes extend the already chosen direction. Existing purchases stay intact.
                p.schemaVersion = 6;
            }''', 1)
save(p, t)


# ---------- UI: subtle branch presentation, six nodes per direction ----------
p, ui = rw("UI/MetaProgressionUIV5.cs")
ui = ui.replace('GUI.Label(notice, "ВЫБЕРИ 1 ИЗ 3 ПУТЕЙ — после первого таланта две остальные ветки блокируются", _center);',
                 'GUI.Label(notice, "ПЕРВЫЕ ШАГИ — каждое направление ведёт к своей подготовке перед классом", _center);')
ui = ui.replace('"БОЕВОЙ ПУТЬ", "combat", chosen, new[] { "legacy_damage", "legacy_attack", "legacy_hunter" }',
                 '"НАТИСК", "combat", chosen, new[] { "legacy_damage", "legacy_attack", "legacy_hunter", "legacy_pressure", "legacy_finisher", "legacy_momentum" }')
ui = ui.replace('"ПУТЬ ВЫЖИВАНИЯ", "survival", chosen, new[] { "legacy_hp", "legacy_regen", "legacy_armor" }',
                 '"СТОЙКОСТЬ", "survival", chosen, new[] { "legacy_hp", "legacy_regen", "legacy_armor", "legacy_recovery", "legacy_resolve", "legacy_secondwind" }')
ui = ui.replace('"ПУТЬ ПОДВИЖНОСТИ", "mobility", chosen, new[] { "legacy_move", "legacy_sprint", "legacy_jump" }',
                 '"МАНЁВР", "mobility", chosen, new[] { "legacy_move", "legacy_sprint", "legacy_jump", "legacy_evasion", "legacy_stride", "legacy_aircontrol" }')
ui = ui.replace('var pathH = 505f;', 'var pathH = 965f;')
ui = ui.replace('var sharedHeader = new Rect(w * 0.5f - 210f, 760f, 420f, 30f);', 'var sharedHeader = new Rect(w * 0.5f - 210f, 1215f, 420f, 30f);')
ui = ui.replace('GUI.Label(sharedHeader, string.IsNullOrEmpty(chosen) ? "ОБЩИЙ ПУТЬ — сначала выбери одну ветку" : "ОБЩИЙ ПУТЬ", _center);',
                 'GUI.Label(sharedHeader, "СНАРЯЖЕНИЕ И ОПЫТ", _center);')
ui = ui.replace('var packRect = new Rect(w * 0.5f - sharedW * 0.5f, 805f, sharedW, 140f);', 'var packRect = new Rect(w * 0.5f - sharedW * 0.5f, 1260f, sharedW, 140f);')
ui = ui.replace('var goldRect = new Rect(w * 0.5f - sharedW * 0.5f, 962f, sharedW, 140f);', 'var goldRect = new Rect(w * 0.5f - sharedW * 0.5f, 1417f, sharedW, 140f);')
ui = ui.replace('const float contentHeight = 1110f;', 'const float contentHeight = 1740f;')
# Insert fieldcraft after gold in the shared ending.
gold_draw = '''            if (pack2 != null) DrawTalentNode(p, pack2, packRect);
            if (gold != null) DrawTalentNode(p, gold, goldRect);
            if (pack2 != null && gold != null)
                DrawConnection(packRect, goldRect, TalentCatalog.GetRank(p, "legacy_pack2") > 0 ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));'''
field_draw = '''            var fieldcraft = TalentCatalog.Find("legacy_fieldcraft");
            var fieldRect = new Rect(w * 0.5f - sharedW * 0.5f, 1574f, sharedW, 140f);
            if (pack2 != null) DrawTalentNode(p, pack2, packRect);
            if (gold != null) DrawTalentNode(p, gold, goldRect);
            if (fieldcraft != null) DrawTalentNode(p, fieldcraft, fieldRect);
            if (pack2 != null && gold != null)
                DrawConnection(packRect, goldRect, TalentCatalog.GetRank(p, "legacy_pack2") > 0 ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));
            if (gold != null && fieldcraft != null)
                DrawConnection(goldRect, fieldRect, TalentCatalog.GetRank(p, "legacy_startgold") > 0 ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));'''
if gold_draw not in ui:
    raise RuntimeError("Legacy shared UI block not found")
ui = ui.replace(gold_draw, field_draw, 1)
# Remove explicit chosen/locked words from headers; selection is shown by tint/border only.
ui = ui.replace('var stateText = selected ? "  •  ✓ ВЫБРАН" : locked ? "  •  ЗАБЛОКИРОВАН" : string.Empty;',
                 'var stateText = string.Empty;')
# Six cards require tighter but still readable spacing inside each column.
ui = ui.replace('var nodeH = 118f;', 'var nodeH = 128f;')
ui = ui.replace('var step = 143f;', 'var step = 145f;')
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

print("Applied PetrichorLegacy 0.6.3 ten-step Legacy patch")

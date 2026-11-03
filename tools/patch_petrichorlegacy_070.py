from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"


def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")


def save(p, text):
    p.write_text(text, encoding="utf-8")


# ---------- Mastery: four endless disciplines + class milestones ----------
mastery = r'''using System;
using System.Collections.Generic;
using System.Linq;
using PetrichorLegacy.Models;

namespace PetrichorLegacy.Progression
{
    public sealed class MasteryDef
    {
        public readonly string Id;
        public readonly string Name;
        public readonly string Description;
        public readonly string ClassId;
        public readonly float PerRank;
        public readonly string IconItem;

        public MasteryDef(string id, string name, string description, string classId, float perRank, string iconItem)
        {
            Id = id;
            Name = name;
            Description = description;
            ClassId = classId;
            PerRank = perRank;
            IconItem = iconItem;
        }
    }

    public sealed class MasteryMilestoneDef
    {
        public readonly string ClassId;
        public readonly int RequiredRanks;
        public readonly string Name;
        public readonly string Description;

        public MasteryMilestoneDef(string classId, int requiredRanks, string name, string description)
        {
            ClassId = classId;
            RequiredRanks = requiredRanks;
            Name = name;
            Description = description;
        }
    }

    public static class MasteryCatalog
    {
        public static readonly IReadOnlyList<MasteryDef> All = new List<MasteryDef>
        {
            new MasteryDef("mastery_guardian_hp", "Основание крепости", "+0.14% максимального здоровья за эффективный ранг.", "Guardian", 0.0014f, "Infusion"),
            new MasteryDef("mastery_guardian_armor", "Стальная доктрина", "+0.18 брони за эффективный ранг.", "Guardian", 0.18f, "ArmorPlate"),
            new MasteryDef("mastery_guardian_regen", "Живучесть", "+0.22% регенерации за эффективный ранг.", "Guardian", 0.0022f, "Medkit"),
            new MasteryDef("mastery_guardian_shield", "Барьерный контур", "+0.10% базового здоровья в виде щита за эффективный ранг.", "Guardian", 0.0010f, "PersonalShield"),

            new MasteryDef("mastery_slayer_damage", "Острие", "+0.11% урона за эффективный ранг.", "Slayer", 0.0011f, "Crowbar"),
            new MasteryDef("mastery_slayer_attack", "Боевой ритм", "+0.11% скорости атаки за эффективный ранг.", "Slayer", 0.0011f, "Syringe"),
            new MasteryDef("mastery_slayer_cooldown", "Техника убийцы", "-0.045% времени восстановления за эффективный ранг.", "Slayer", 0.00045f, "Bandolier"),
            new MasteryDef("mastery_slayer_crit", "Безошибочность", "+0.045% критического шанса за эффективный ранг.", "Slayer", 0.045f, "CritGlasses"),

            new MasteryDef("mastery_path_move", "Дальний шаг", "+0.12% скорости движения за эффективный ранг.", "Pathfinder", 0.0012f, "Hoof"),
            new MasteryDef("mastery_path_sprint", "Темп экспедиции", "+0.18% скорости спринта за эффективный ранг.", "Pathfinder", 0.0018f, "SprintBonus"),
            new MasteryDef("mastery_path_jump", "Контроль высоты", "+0.22% силы прыжка за эффективный ранг.", "Pathfinder", 0.0022f, "Feather"),
            new MasteryDef("mastery_path_control", "Манёвренность", "+0.08% скорости движения за эффективный ранг.", "Pathfinder", 0.0008f, "JumpBoost"),

            new MasteryDef("mastery_seeker_gold", "Доля добычи", "+0.18% золота с особых монстров за эффективный ранг.", "Seeker", 0.0018f, "GoldOnHurt"),
            new MasteryDef("mastery_seeker_specialxp", "Редкие трофеи", "+0.14% мета-XP за особых монстров за эффективный ранг.", "Seeker", 0.0014f, "TreasureCache"),
            new MasteryDef("mastery_seeker_stagegold", "Снабжение", "+0.20 золота при переходе на следующую стадию за эффективный ранг.", "Seeker", 0.20f, "BonusGoldPackOnKill"),
            new MasteryDef("mastery_seeker_startgold", "Стартовый капитал", "+0.15 стартового золота за эффективный ранг.", "Seeker", 0.15f, "EquipmentMagazine"),

            new MasteryDef("mastery_arcanist_damage", "Арканный резонанс", "+0.10% урона за эффективный ранг.", "Arcanist", 0.0010f, "NearbyDamageBonus"),
            new MasteryDef("mastery_arcanist_attack", "Быстрый каст", "+0.11% скорости атаки за эффективный ранг.", "Arcanist", 0.0011f, "AttackSpeedOnCrit"),
            new MasteryDef("mastery_arcanist_cooldown", "Поток времени", "-0.05% времени восстановления за эффективный ранг.", "Arcanist", 0.0005f, "AlienHead"),
            new MasteryDef("mastery_arcanist_move", "Фазовый шаг", "+0.09% скорости движения за эффективный ранг.", "Arcanist", 0.0009f, "UtilitySkillMagazine"),

            new MasteryDef("mastery_tech_attack", "Сервоприводы", "+0.11% скорости атаки владельца за эффективный ранг.", "Technomancer", 0.0011f, "WarCryOnMultiKill"),
            new MasteryDef("mastery_tech_move", "Лёгкое шасси", "+0.11% скорости движения владельца за эффективный ранг.", "Technomancer", 0.0011f, "SprintOutOfCombat"),
            new MasteryDef("mastery_tech_minion_damage", "Боевые алгоритмы", "+0.28% урона миньонов за эффективный ранг.", "Technomancer", 0.0028f, "DroneWeapons"),
            new MasteryDef("mastery_tech_minion_health", "Усиленные корпуса", "+0.28% здоровья миньонов за эффективный ранг.", "Technomancer", 0.0028f, "CaptainDefenseMatrix"),

            new MasteryDef("mastery_commander_damage", "Приказ на огонь", "+0.09% урона за эффективный ранг.", "Commander", 0.0009f, "BossDamageBonus"),
            new MasteryDef("mastery_commander_move", "Перестроение", "+0.09% скорости движения за эффективный ранг.", "Commander", 0.0009f, "SprintArmor"),
            new MasteryDef("mastery_commander_armor", "Дисциплина", "+0.11 брони за эффективный ранг.", "Commander", 0.11f, "FlatHealth"),
            new MasteryDef("mastery_commander_minion", "Командование", "+0.18% урона миньонов за эффективный ранг.", "Commander", 0.0018f, "GhostOnKill")
        };

        public static readonly IReadOnlyList<MasteryMilestoneDef> Milestones = new List<MasteryMilestoneDef>
        {
            new MasteryMilestoneDef("Guardian", 25, "Оплот", "+2 брони."),
            new MasteryMilestoneDef("Guardian", 75, "Непоколебимость", "+2% максимального здоровья."),
            new MasteryMilestoneDef("Guardian", 150, "Вторая линия", "+5% регенерации и щит размером 3% базового здоровья."),
            new MasteryMilestoneDef("Guardian", 300, "Живая крепость", "+4 брони и ещё +2% максимального здоровья."),

            new MasteryMilestoneDef("Slayer", 25, "Острие", "+1% урона."),
            new MasteryMilestoneDef("Slayer", 75, "Разгон", "+1.5% скорости атаки."),
            new MasteryMilestoneDef("Slayer", 150, "Казнь", "+3% урона боссам и особым монстрам."),
            new MasteryMilestoneDef("Slayer", 300, "Совершенный хищник", "+2% урона и +1% скорости атаки."),

            new MasteryMilestoneDef("Pathfinder", 25, "Лёгкий шаг", "+1.5% скорости движения."),
            new MasteryMilestoneDef("Pathfinder", 75, "Без остановки", "+2% скорости спринта."),
            new MasteryMilestoneDef("Pathfinder", 150, "Воздушный контроль", "+5% силы прыжка и +1 броня."),
            new MasteryMilestoneDef("Pathfinder", 300, "Свобода движения", "+2% скорости движения и +1 дополнительный прыжок."),

            new MasteryMilestoneDef("Seeker", 25, "Знаток трофеев", "+5% мета-XP за особых монстров."),
            new MasteryMilestoneDef("Seeker", 75, "Выгодная добыча", "+5% золота с особых монстров."),
            new MasteryMilestoneDef("Seeker", 150, "Линия снабжения", "+15 золота при переходе на новую стадию."),
            new MasteryMilestoneDef("Seeker", 300, "Большой капитал", "+40 стартового золота."),

            new MasteryMilestoneDef("Arcanist", 25, "Стабильный поток", "Ещё -1% времени восстановления навыков."),
            new MasteryMilestoneDef("Arcanist", 75, "Резонанс", "+1% урона."),
            new MasteryMilestoneDef("Arcanist", 150, "Перегрузка", "+1.5% скорости атаки."),
            new MasteryMilestoneDef("Arcanist", 300, "Вне времени", "Ещё -2% времени восстановления навыков."),

            new MasteryMilestoneDef("Technomancer", 25, "Синхронизация", "+4% урона миньонов."),
            new MasteryMilestoneDef("Technomancer", 75, "Резервные корпуса", "+4% здоровья миньонов."),
            new MasteryMilestoneDef("Technomancer", 150, "Боевой рой", "+5% скорости атаки и движения миньонов."),
            new MasteryMilestoneDef("Technomancer", 300, "Единая сеть", "+2% скорости атаки и движения владельца."),

            new MasteryMilestoneDef("Commander", 25, "Дисциплина", "+1 броня."),
            new MasteryMilestoneDef("Commander", 75, "Строй", "+3% урона и здоровья миньонов."),
            new MasteryMilestoneDef("Commander", 150, "Боевой приказ", "+1.5% урона и скорости движения владельца."),
            new MasteryMilestoneDef("Commander", 300, "Главнокомандующий", "+5% скорости атаки и движения миньонов; +2 брони владельцу.")
        };

        private static readonly Dictionary<string, MasteryDef> ById = All.ToDictionary(x => x.Id, x => x);

        public static MasteryDef Find(string id) => id != null && ById.TryGetValue(id, out var def) ? def : null;

        public static int GetRank(ProfileProgress profile, string id)
        {
            if (profile?.masteries == null || string.IsNullOrEmpty(id)) return 0;
            return profile.masteries.FirstOrDefault(x => x.id == id)?.rank ?? 0;
        }

        public static int TotalRanks(ProfileProgress profile, string classId)
        {
            if (profile?.masteries == null || string.IsNullOrEmpty(classId)) return 0;
            var total = 0;
            foreach (var r in profile.masteries)
            {
                if (r == null || r.rank <= 0) continue;
                var def = Find(r.id);
                if (def != null && def.ClassId == classId) total += r.rank;
            }
            return total;
        }

        public static IEnumerable<MasteryMilestoneDef> MilestonesFor(string classId) =>
            Milestones.Where(x => string.Equals(x.ClassId, classId, StringComparison.OrdinalIgnoreCase)).OrderBy(x => x.RequiredRanks);

        public static float EffectiveRanks(int rank)
        {
            rank = Math.Max(0, rank);
            var total = 0f;
            var left = rank;
            var take = Math.Min(left, 25); total += take; left -= take;
            if (left <= 0) return total;
            take = Math.Min(left, 25); total += take * 0.75f; left -= take;
            if (left <= 0) return total;
            take = Math.Min(left, 50); total += take * 0.50f; left -= take;
            if (left <= 0) return total;
            take = Math.Min(left, 100); total += take * 0.30f; left -= take;
            if (left > 0) total += left * 0.20f;
            return total;
        }

        public static float Value(ProfileProgress profile, string id)
        {
            var def = Find(id);
            if (def == null) return 0f;
            return EffectiveRanks(GetRank(profile, id)) * def.PerRank;
        }

        public static string CurrentValueText(ProfileProgress profile, MasteryDef def)
        {
            if (def == null) return string.Empty;
            var value = Value(profile, def.Id);
            if (def.Id.Contains("armor")) return $"Сейчас: +{value:0.##} брони";
            if (def.Id.Contains("stagegold") || def.Id.Contains("startgold")) return $"Сейчас: +{value:0.##} золота";
            return $"Сейчас: {(def.Id.Contains("cooldown") ? "-" : "+")}{value * 100f:0.##}%";
        }

        public static int Milestone(int rank) => Math.Max(0, rank) / 10;
    }
}
'''
save(base / "Progression" / "MasteryCatalog.cs", mastery)


# ---------- Perfection: three non-exclusive constellation paths ----------
perfection = r'''using System.Collections.Generic;
using System.Linq;
using PetrichorLegacy.Models;

namespace PetrichorLegacy.Progression
{
    public sealed class PerfectionDef
    {
        public readonly string Id;
        public readonly string Name;
        public readonly string Description;
        public readonly int UnlockLevel;
        public readonly int MaxRank;
        public readonly string PrerequisiteId;
        public readonly int Column;
        public readonly int Row;
        public readonly bool Major;
        public readonly string IconItem;

        public PerfectionDef(string id, string name, string description, int unlockLevel, string prerequisiteId,
            int column, int row, string iconItem, bool major = false, int maxRank = 1)
        {
            Id = id;
            Name = name;
            Description = description;
            UnlockLevel = unlockLevel;
            MaxRank = maxRank;
            PrerequisiteId = prerequisiteId;
            Column = column;
            Row = row;
            Major = major;
            IconItem = iconItem;
        }
    }

    public static class PerfectionCatalog
    {
        public static readonly IReadOnlyList<PerfectionDef> All = new List<PerfectionDef>
        {
            // ТРИУМФ
            new PerfectionDef("perfection_giant_slayer", "Убийца великанов", "+3% урона боссам.", 25, null, 0, 0, "BossDamageBonus"),
            new PerfectionDef("perfection_prestige_predator", "Знак хищника", "+2% урона особым монстрам.", 50, "perfection_giant_slayer", 0, 1, "Crowbar"),
            new PerfectionDef("perfection_pursuit", "Неотступность", "После убийства особого монстра на 8 сек. +3% скорости движения и +2% скорости атаки.", 75, "perfection_prestige_predator", 0, 2, "WarCryOnMultiKill"),
            new PerfectionDef("perfection_prestige_veteran", "Ветеран охоты", "+1% скорости атаки и движения.", 100, "perfection_pursuit", 0, 3, "HeadHunter", true),
            new PerfectionDef("perfection_execution", "Право на казнь", "+5% урона целям ниже 25% здоровья.", 150, "perfection_prestige_veteran", 0, 4, "Dagger"),
            new PerfectionDef("perfection_relentless", "Без права на отступление", "Ещё +2% урона боссам и особым монстрам.", 200, "perfection_execution", 0, 5, "ArmorReductionOnHit", true),
            new PerfectionDef("perfection_apex", "Вершина охоты", "+2% всего урона и +1% критического шанса.", 300, "perfection_relentless", 0, 6, "CritGlasses", true),

            // СТОЙКОСТЬ
            new PerfectionDef("perfection_reserve", "Запас сил", "При переходе на новую стадию восстановить 5% здоровья.", 25, null, 1, 0, "Medkit"),
            new PerfectionDef("perfection_instinct", "Инстинкт выжившего", "+3 брони, когда здоровье ниже 30%.", 50, "perfection_reserve", 1, 1, "ArmorPlate"),
            new PerfectionDef("perfection_bulwark", "Полевая защита", "В начале каждой стадии получить барьер в 6% максимального здоровья.", 75, "perfection_instinct", 1, 2, "BarrierOnKill"),
            new PerfectionDef("perfection_prestige_hardened", "Закалённый", "+1% максимального здоровья.", 100, "perfection_bulwark", 1, 3, "Infusion", true),
            new PerfectionDef("perfection_recovery", "Живой резерв", "+5% естественной регенерации.", 150, "perfection_prestige_hardened", 1, 4, "HealWhileSafe"),
            new PerfectionDef("perfection_ironwill", "Железная воля", "Ниже 35% здоровья ещё +6 брони.", 200, "perfection_recovery", 1, 5, "SprintArmor", true),
            new PerfectionDef("perfection_laststand", "Последний рубеж", "В начале стадии дополнительно восстановить 8% здоровья и получить 8% барьера.", 300, "perfection_ironwill", 1, 6, "IncreaseHealing", true),

            // ЭКСПЕДИЦИЯ
            new PerfectionDef("perfection_pack", "Трофейный мешок", "+1 вместимость стартового Арсенала.", 25, null, 2, 0, "EquipmentMagazine"),
            new PerfectionDef("perfection_hunter", "Легендарный охотник", "+10% мета-XP за легендарных и более редких монстров.", 50, "perfection_pack", 2, 1, "TreasureCache"),
            new PerfectionDef("perfection_capital", "Походный капитал", "+25 золота в начале первого этапа забега.", 75, "perfection_hunter", 2, 2, "GoldOnHurt"),
            new PerfectionDef("perfection_supply", "Линия снабжения", "+15 золота при переходе на каждую следующую стадию.", 100, "perfection_capital", 2, 3, "BonusGoldPackOnKill", true),
            new PerfectionDef("perfection_bounty", "Редкая добыча", "+5% мета-XP и золота за всех особых монстров.", 150, "perfection_supply", 2, 4, "TreasureCacheVoid"),
            new PerfectionDef("perfection_spoils", "Право на трофеи", "Ещё +10% золота с особых монстров.", 200, "perfection_bounty", 2, 5, "BarrageOnBoss", true),
            new PerfectionDef("perfection_prestige_treasurer", "Хранитель наследия", "+1 вместимость Арсенала.", 300, "perfection_spoils", 2, 6, "Clover", true)
        };

        private static readonly Dictionary<string, PerfectionDef> ById = All.ToDictionary(x => x.Id, x => x);

        public static PerfectionDef Find(string id) => id != null && ById.TryGetValue(id, out var def) ? def : null;

        public static int GetRank(ProfileProgress profile, string id)
        {
            if (profile?.perfections == null || string.IsNullOrEmpty(id)) return 0;
            return profile.perfections.FirstOrDefault(x => x.id == id)?.rank ?? 0;
        }

        public static bool PrerequisiteMet(ProfileProgress profile, PerfectionDef def)
        {
            if (def == null || string.IsNullOrEmpty(def.PrerequisiteId)) return true;
            return GetRank(profile, def.PrerequisiteId) > 0;
        }
    }
}
'''
save(base / "Progression" / "PerfectionCatalog.cs", perfection)


# ---------- Progression purchasing / respec ----------
p, t = rw("Progression/ProgressionService.cs")
old_mastery = r'''        public static bool TryBuyMastery(ProfileProgress profile, string masteryId, out string error)
        {
            error = null;
            var def = MasteryCatalog.Find(masteryId);
            if (profile == null || def == null) { error = "Неизвестное мастерство."; return false; }
            if (profile.level < 41) { error = "Мастерство открывается с 41 уровня."; return false; }
            if (profile.activeClass != def.ClassId) { error = "Сначала сделай этот класс активным."; return false; }
            if (profile.unspentMasteryPoints <= 0) { error = "Недостаточно очков мастерства."; return false; }

            var record = profile.masteries.FirstOrDefault(x => x.id == masteryId);
            if (record == null)
            {
                record = new MasteryRankRecord { id = masteryId, rank = 0 };
                profile.masteries.Add(record);
            }
            record.rank++;
            profile.unspentMasteryPoints--;
            SaveService.SaveCurrent();
            return true;
        }'''
new_mastery = r'''        public static bool TryBuyMastery(ProfileProgress profile, string masteryId, out string error) =>
            TryBuyMasteryRanks(profile, masteryId, 1, out error);

        public static bool TryBuyMasteryRanks(ProfileProgress profile, string masteryId, int requestedRanks, out string error)
        {
            error = null;
            var def = MasteryCatalog.Find(masteryId);
            if (profile == null || def == null) { error = "Неизвестное мастерство."; return false; }
            if (profile.level < 41) { error = "Мастерство открывается с 41 уровня."; return false; }
            if (profile.activeClass != def.ClassId) { error = "Сначала сделай этот класс активным."; return false; }
            if (profile.unspentMasteryPoints <= 0) { error = "Недостаточно очков мастерства."; return false; }
            var count = Math.Max(1, Math.Min(requestedRanks, profile.unspentMasteryPoints));

            var record = profile.masteries.FirstOrDefault(x => x.id == masteryId);
            if (record == null)
            {
                record = new MasteryRankRecord { id = masteryId, rank = 0 };
                profile.masteries.Add(record);
            }
            record.rank += count;
            profile.unspentMasteryPoints -= count;
            SaveService.SaveCurrent();
            return true;
        }'''
if old_mastery not in t:
    raise RuntimeError("TryBuyMastery block not found")
t = t.replace(old_mastery, new_mastery, 1)

perf_anchor = '''            if (profile.level < def.UnlockLevel) { error = $"Требуется уровень {def.UnlockLevel}."; return false; }
            var rank = PerfectionCatalog.GetRank(profile, perfectionId);'''
perf_replace = '''            if (profile.level < def.UnlockLevel) { error = $"Требуется уровень {def.UnlockLevel}."; return false; }
            if (!PerfectionCatalog.PrerequisiteMet(profile, def)) { error = "Сначала открой предыдущий узел этого направления."; return false; }
            var rank = PerfectionCatalog.GetRank(profile, perfectionId);'''
if perf_anchor not in t:
    raise RuntimeError("Perfection prerequisite anchor not found")
t = t.replace(perf_anchor, perf_replace, 1)

respec_anchor = '''        public static int StartingCapacity(ProfileProgress profile)'''
respec_method = r'''        public static void RespecPerfection(ProfileProgress profile)
        {
            if (profile == null || profile.perfections == null) return;
            var refund = 0;
            foreach (var r in profile.perfections) if (r != null) refund += Math.Max(0, r.rank);
            profile.perfections.Clear();
            profile.unspentPerfectionPoints += refund;
            SaveService.SaveCurrent();
        }

'''
if respec_anchor not in t:
    raise RuntimeError("StartingCapacity anchor not found")
t = t.replace(respec_anchor, respec_method + respec_anchor, 1)
save(p, t)


# ---------- Server-side total mastery ranks ----------
p, t = rw("Progression/ServerProgressionState.cs")
anchor = '''        public static float MasteryValue(CharacterMaster master, string id)
        {
            var def = MasteryCatalog.Find(id);
            if (def == null) return 0f;
            return MasteryCatalog.EffectiveRanks(MasteryRank(master, id)) * def.PerRank;
        }'''
insert = anchor + r'''
        public static int MasteryTotalRanks(CharacterMaster master)
        {
            var p = Get(master);
            if (p == null || string.IsNullOrEmpty(p.ActiveClass)) return 0;
            var total = 0;
            foreach (var kv in p.Masteries)
            {
                var def = MasteryCatalog.Find(kv.Key);
                if (def != null && def.ClassId == p.ActiveClass) total += Math.Max(0, kv.Value);
            }
            return total;
        }'''
if anchor not in t:
    raise RuntimeError("MasteryValue anchor not found")
t = t.replace(anchor, insert, 1)
if "using System;" not in t:
    t = t.replace("using System.Collections.Generic;", "using System;\nusing System.Collections.Generic;", 1)
save(p, t)


# ---------- Milestone + new Perfection runtime ----------
runtime = r'''using RoR2;
using UnityEngine;
using UnityEngine.Networking;

namespace PetrichorLegacy.Progression
{
    public static class PerfectionRuntimeEffects
    {
        public static void Install()
        {
            On.RoR2.CharacterBody.RecalculateStats += CharacterBody_RecalculateStats;
            On.RoR2.HealthComponent.TakeDamageProcess += HealthComponent_TakeDamageProcess;
            Stage.onStageStartGlobal += OnStageStart;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterBody.RecalculateStats -= CharacterBody_RecalculateStats;
            On.RoR2.HealthComponent.TakeDamageProcess -= HealthComponent_TakeDamageProcess;
            Stage.onStageStartGlobal -= OnStageStart;
        }

        private static void CharacterBody_RecalculateStats(On.RoR2.CharacterBody.orig_RecalculateStats orig, CharacterBody self)
        {
            orig(self);
            if (self == null || self.master == null || self.master.playerCharacterMasterController == null) return;
            var progress = ServerProgressionState.Get(self.master);
            if (progress == null) return;

            if (progress.PursuitUntil > Time.fixedTime && ServerProgressionState.Perfection(self.master, "perfection_pursuit") > 0)
            {
                self.moveSpeed *= 1.03f;
                self.attackSpeed *= 1.02f;
            }
            if (ServerProgressionState.Perfection(self.master, "perfection_recovery") > 0) self.regen *= 1.05f;
            if (ServerProgressionState.Perfection(self.master, "perfection_ironwill") > 0 && self.healthComponent != null && self.healthComponent.combinedHealthFraction < 0.35f)
                self.armor += 6f;
            if (ServerProgressionState.Perfection(self.master, "perfection_apex") > 0)
            {
                self.damage *= 1.02f;
                self.crit += 1f;
            }

            var total = ServerProgressionState.MasteryTotalRanks(self.master);
            switch (progress.ActiveClass)
            {
                case "Guardian":
                    if (total >= 25) self.armor += 2f;
                    if (total >= 75) self.maxHealth *= 1.02f;
                    if (total >= 150) { self.regen *= 1.05f; self.maxShield += self.baseMaxHealth * 0.03f; }
                    if (total >= 300) { self.armor += 4f; self.maxHealth *= 1.02f; }
                    break;
                case "Slayer":
                    if (total >= 25) self.damage *= 1.01f;
                    if (total >= 75) self.attackSpeed *= 1.015f;
                    if (total >= 300) { self.damage *= 1.02f; self.attackSpeed *= 1.01f; }
                    break;
                case "Pathfinder":
                    if (total >= 25) self.moveSpeed *= 1.015f;
                    if (total >= 75) self.sprintingSpeedMultiplier *= 1.02f;
                    if (total >= 150) { self.jumpPower *= 1.05f; self.armor += 1f; }
                    if (total >= 300) { self.moveSpeed *= 1.02f; self.maxJumpCount += 1; }
                    break;
                case "Arcanist":
                    if (total >= 75) self.damage *= 1.01f;
                    if (total >= 150) self.attackSpeed *= 1.015f;
                    ApplyCooldownScale(self.skillLocator, total >= 300 ? 0.03f : total >= 25 ? 0.01f : 0f);
                    break;
                case "Technomancer":
                    if (total >= 300) { self.attackSpeed *= 1.02f; self.moveSpeed *= 1.02f; }
                    break;
                case "Commander":
                    if (total >= 25) self.armor += 1f;
                    if (total >= 150) { self.damage *= 1.015f; self.moveSpeed *= 1.015f; }
                    if (total >= 300) self.armor += 2f;
                    break;
            }
        }

        private static void HealthComponent_TakeDamageProcess(On.RoR2.HealthComponent.orig_TakeDamageProcess orig, HealthComponent self, DamageInfo damageInfo)
        {
            var attacker = damageInfo.attacker ? damageInfo.attacker.GetComponent<CharacterBody>() : null;
            var victim = self != null ? self.body : null;
            if (attacker != null && attacker.master != null && victim != null)
            {
                if (ServerProgressionState.Perfection(attacker.master, "perfection_execution") > 0 && victim.healthComponent != null && victim.healthComponent.combinedHealthFraction < 0.25f)
                    damageInfo.damage *= 1.05f;
                if (ServerProgressionState.Perfection(attacker.master, "perfection_relentless") > 0 && (victim.isBoss || victim.GetComponent<MonsterRarityMarker>() != null))
                    damageInfo.damage *= 1.02f;
                var progress = ServerProgressionState.Get(attacker.master);
                if (progress != null && progress.ActiveClass == "Slayer" && ServerProgressionState.MasteryTotalRanks(attacker.master) >= 150 &&
                    (victim.isBoss || victim.GetComponent<MonsterRarityMarker>() != null))
                    damageInfo.damage *= 1.03f;
            }
            orig(self, damageInfo);
        }

        private static void OnStageStart(Stage stage)
        {
            if (!NetworkServer.active || Run.instance == null) return;
            var stageIndex = Run.instance.stageClearCount;
            foreach (var pcmc in PlayerCharacterMasterController.instances)
            {
                var master = pcmc?.master;
                var body = master?.GetBody();
                if (master == null || body == null || body.healthComponent == null) continue;

                if (ServerProgressionState.Perfection(master, "perfection_bulwark") > 0)
                    body.healthComponent.AddBarrier(body.maxHealth * 0.06f);
                if (ServerProgressionState.Perfection(master, "perfection_laststand") > 0)
                {
                    body.healthComponent.HealFraction(0.08f, default(ProcChainMask));
                    body.healthComponent.AddBarrier(body.maxHealth * 0.08f);
                }

                var gold = 0f;
                if (stageIndex == 0 && ServerProgressionState.Perfection(master, "perfection_capital") > 0) gold += 25f;
                if (stageIndex > 0 && ServerProgressionState.Perfection(master, "perfection_supply") > 0) gold += 15f;

                var progress = ServerProgressionState.Get(master);
                if (progress != null && progress.ActiveClass == "Seeker")
                {
                    var total = ServerProgressionState.MasteryTotalRanks(master);
                    if (stageIndex > 0 && total >= 150) gold += 15f;
                    if (stageIndex == 0 && total >= 300) gold += 40f;
                }
                if (gold > 0f) master.GiveMoney((uint)Mathf.RoundToInt(gold));
            }
        }

        private static void ApplyCooldownScale(SkillLocator locator, float reduction)
        {
            if (locator == null || reduction <= 0f) return;
            var mult = Mathf.Clamp(1f - reduction, 0.70f, 1f);
            ApplySkill(locator.primary, mult); ApplySkill(locator.secondary, mult); ApplySkill(locator.utility, mult); ApplySkill(locator.special, mult);
        }

        private static void ApplySkill(GenericSkill skill, float mult)
        {
            if (skill == null) return;
            var type = typeof(GenericSkill);
            var field = type.GetField("cooldownScale", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
            if (field != null && field.FieldType == typeof(float)) field.SetValue(skill, Mathf.Clamp((float)field.GetValue(skill) * mult, 0.70f, 2f));
        }
    }
}
'''
save(base / "Progression" / "PerfectionRuntimeEffects.cs", runtime)


# ---------- Minion milestone bonuses ----------
p, t = rw("Progression/AdditionalSpecEffects.cs")
anchor = '''                dmg += ServerProgressionState.MasteryValue(owner, "mastery_commander_minion");
                self.damage *= 1f + dmg;'''
replacement = '''                dmg += ServerProgressionState.MasteryValue(owner, "mastery_commander_minion");
                var ownerProgress = ServerProgressionState.Get(owner);
                var masteryTotal = ServerProgressionState.MasteryTotalRanks(owner);
                if (ownerProgress != null && ownerProgress.ActiveClass == "Technomancer")
                {
                    if (masteryTotal >= 25) dmg += 0.04f;
                    if (masteryTotal >= 75) hp += 0.04f;
                    if (masteryTotal >= 150) { atk += 0.05f; mov += 0.05f; }
                }
                if (ownerProgress != null && ownerProgress.ActiveClass == "Commander")
                {
                    if (masteryTotal >= 75) { dmg += 0.03f; hp += 0.03f; }
                    if (masteryTotal >= 300) { atk += 0.05f; mov += 0.05f; }
                }
                self.damage *= 1f + dmg;'''
if anchor not in t:
    raise RuntimeError("Minion mastery anchor not found")
t = t.replace(anchor, replacement, 1)
save(p, t)


# ---------- Reward multipliers for mastery/perfection ----------
p, t = rw("Progression/MonsterRaritySystem.cs")
xp_anchor = '''            xpMultiplier += ServerProgressionState.MasteryValue(report.attackerMaster, "mastery_seeker_specialxp");'''
xp_extra = xp_anchor + r'''
            var activeProgress = ServerProgressionState.Get(report.attackerMaster);
            var masteryTotal = ServerProgressionState.MasteryTotalRanks(report.attackerMaster);
            if (activeProgress != null && activeProgress.ActiveClass == "Seeker" && masteryTotal >= 25) xpMultiplier += 0.05f;
            if (ServerProgressionState.Perfection(report.attackerMaster, "perfection_bounty") > 0) xpMultiplier += 0.05f;'''
if xp_anchor not in t:
    raise RuntimeError("XP mastery anchor not found")
t = t.replace(xp_anchor, xp_extra, 1)

gold_anchor = '''            goldMultiplier += ServerProgressionState.MasteryValue(report.attackerMaster, "mastery_seeker_gold");'''
gold_extra = gold_anchor + r'''
            if (activeProgress != null && activeProgress.ActiveClass == "Seeker" && masteryTotal >= 75) goldMultiplier += 0.05f;
            if (ServerProgressionState.Perfection(report.attackerMaster, "perfection_bounty") > 0) goldMultiplier += 0.05f;
            if (ServerProgressionState.Perfection(report.attackerMaster, "perfection_spoils") > 0) goldMultiplier += 0.10f;'''
if gold_anchor not in t:
    raise RuntimeError("Gold mastery anchor not found")
t = t.replace(gold_anchor, gold_extra, 1)
save(p, t)


# ---------- Profile migration: refund old Perfection, preserve Mastery ----------
p, t = rw("Models/ProfileProgress.cs")
if "public int schemaVersion = 6;" not in t:
    raise RuntimeError("Schema 6 not found")
t = t.replace("public int schemaVersion = 6;", "public int schemaVersion = 7;", 1)
save(p, t)

p, t = rw("Persistence/SaveService.cs")
v6 = '''            if (p.schemaVersion < 6)
            {
                // New Legacy nodes extend the already chosen direction. Existing purchases stay intact.
                p.schemaVersion = 6;
            }'''
if v6 not in t:
    raise RuntimeError("Schema 6 migration not found")
v7 = v6 + r'''

            if (p.schemaVersion < 7)
            {
                // Perfection became a prerequisite-based constellation. Refund old choices only.
                var refund = 0;
                if (p.perfections != null)
                {
                    foreach (var r in p.perfections) if (r != null) refund += Math.Max(0, r.rank);
                    p.perfections.Clear();
                }
                p.unspentPerfectionPoints += refund;
                p.schemaVersion = 7;
            }'''
t = t.replace(v6, v7, 1)
save(p, t)


# ---------- UI: mastery dashboard + perfection constellation ----------
p, ui = rw("UI/MetaProgressionUIV5.cs")
mastery_pattern = re.compile(r'''        private void DrawMasteryPage\(ProfileProgress p, Rect area\)\n        \{.*?\n        \}\n\n        private void DrawPerfectionPage''', re.S)
mastery_method = r'''        private void DrawMasteryPage(ProfileProgress p, Rect area)
        {
            GUI.Label(new Rect(area.x + 12f, area.y + 8f, area.width - 24f, 27f), $"МАСТЕРСТВО • доступно очков: {p.unspentMasteryPoints}", _header);
            GUI.Label(new Rect(area.x + 12f, area.y + 34f, area.width - 24f, 22f), "Бесконечные дисциплины активного класса. После 25 / 50 / 100 / 200 рангов новые ранги дают меньше силы.", _small);
            if (p.level < 41) { GUI.Label(new Rect(area.x + 20f, area.center.y - 15f, area.width - 40f, 30f), "Мастерство откроется на 41 уровне.", _center); return; }
            if (string.IsNullOrEmpty(p.activeClass)) { GUI.Label(new Rect(area.x + 20f, area.center.y - 15f, area.width - 40f, 30f), "Сначала выбери активный класс.", _center); return; }

            var total = MasteryCatalog.TotalRanks(p, p.activeClass);
            var milestoneRect = new Rect(area.x + 10f, area.y + 64f, area.width - 20f, 126f);
            FillRect(milestoneRect, new Color(0.015f, 0.022f, 0.027f, 1f));
            DrawBorder(milestoneRect, new Color(0.16f, 0.28f, 0.34f, 1f), 1f);
            GUI.Label(new Rect(milestoneRect.x + 10f, milestoneRect.y + 6f, 280f, 24f), $"{ClassDisplay(p.activeClass).ToUpperInvariant()} • суммарный ранг {total}", _header);

            var milestones = MasteryCatalog.MilestonesFor(p.activeClass).ToList();
            var mw = (milestoneRect.width - 20f) / Mathf.Max(1, milestones.Count);
            for (var i = 0; i < milestones.Count; i++)
            {
                var m = milestones[i];
                var reached = total >= m.RequiredRanks;
                var r = new Rect(milestoneRect.x + 8f + i * mw, milestoneRect.y + 36f, mw - 8f, 80f);
                FillRect(r, reached ? new Color(0.045f, 0.15f, 0.12f, 1f) : new Color(0.035f, 0.043f, 0.048f, 1f));
                DrawBorder(r, reached ? new Color(0.26f, 0.72f, 0.52f, 1f) : new Color(0.17f, 0.22f, 0.25f, 1f), reached ? 2f : 1f);
                GUI.Label(new Rect(r.x + 5f, r.y + 4f, r.width - 10f, 20f), $"{m.RequiredRanks} • {m.Name}", _center);
                GUI.Label(new Rect(r.x + 7f, r.y + 27f, r.width - 14f, 47f), m.Description, _tiny);
            }

            var cardsArea = new Rect(area.x + 8f, area.y + 198f, area.width - 16f, area.height - 206f);
            var defs = MasteryCatalog.All.Where(x => x.ClassId == p.activeClass).ToList();
            var gap = 10f;
            var cardW = (cardsArea.width - gap) * 0.5f;
            var cardH = 220f;
            var contentH = Mathf.Max(cardsArea.height - 4f, 2 * cardH + gap + 8f);
            _masteryScroll = GUI.BeginScrollView(cardsArea, _masteryScroll, new Rect(0f, 0f, cardsArea.width - 18f, contentH));
            for (var i = 0; i < defs.Count; i++)
            {
                var col = i % 2; var row = i / 2;
                DrawMasteryCard(p, defs[i], new Rect(col * (cardW + gap), row * (cardH + gap), cardW, cardH));
            }
            GUI.EndScrollView();
        }

        private void DrawMasteryCard(ProfileProgress p, MasteryDef def, Rect rect)
        {
            var rank = MasteryCatalog.GetRank(p, def.Id);
            FillRect(rect, new Color(0.025f, 0.034f, 0.040f, 1f));
            DrawBorder(rect, new Color(0.18f, 0.38f, 0.45f, 1f), 1f);
            var iconRect = new Rect(rect.x + 10f, rect.y + 10f, 64f, 64f);
            FillRect(iconRect, new Color(0.01f, 0.016f, 0.020f, 1f));
            var icon = ResolveProgressionIcon(def.IconItem);
            if (icon != null) DrawSprite(iconRect, icon, Color.white); else GUI.Label(iconRect, "∞", _center);
            DrawBorder(iconRect, new Color(0.20f, 0.52f, 0.60f, 1f), 1f);
            GUI.Label(new Rect(rect.x + 84f, rect.y + 10f, rect.width - 94f, 28f), $"{def.Name} • ранг {rank}", _header);
            GUI.Label(new Rect(rect.x + 84f, rect.y + 40f, rect.width - 94f, 34f), MasteryCatalog.CurrentValueText(p, def), _small);
            GUI.Label(new Rect(rect.x + 10f, rect.y + 83f, rect.width - 20f, 54f), def.Description, _small);
            GUI.Label(new Rect(rect.x + 10f, rect.y + 139f, rect.width - 20f, 20f), $"Эффективных рангов: {MasteryCatalog.EffectiveRanks(rank):0.##}", _tiny);

            var buttonY = rect.yMax - 45f;
            GUI.enabled = p.unspentMasteryPoints > 0;
            if (GUI.Button(new Rect(rect.x + 10f, buttonY, 92f, 32f), "+1")) BuyMasteryRanks(p, def, 1);
            if (GUI.Button(new Rect(rect.x + 108f, buttonY, 92f, 32f), "+5")) BuyMasteryRanks(p, def, 5);
            if (GUI.Button(new Rect(rect.x + 206f, buttonY, 92f, 32f), "+10")) BuyMasteryRanks(p, def, 10);
            GUI.enabled = true;
        }

        private void BuyMasteryRanks(ProfileProgress p, MasteryDef def, int count)
        {
            if (!ProgressionService.TryBuyMasteryRanks(p, def.Id, count, out var error)) SetStatus(error);
            else SetStatus($"{def.Name}: добавлено до {count} рангов.");
        }

        private void DrawPerfectionPage'''
ui, n = mastery_pattern.subn(mastery_method, ui, count=1)
if n != 1:
    raise RuntimeError("DrawMasteryPage replacement failed")

perf_pattern = re.compile(r'''        private void DrawPerfectionPage\(ProfileProgress p, Rect area\)\n        \{.*?\n        \}\n\n        private void DrawLoadoutPage''', re.S)
perf_method = r'''        private void DrawPerfectionPage(ProfileProgress p, Rect area)
        {
            GUI.Label(new Rect(area.x + 12f, area.y + 8f, area.width - 230f, 27f), $"СОВЕРШЕНСТВО • доступно: {p.unspentPerfectionPoints} • 1 очко каждые 25 уровней", _header);
            if (GUI.Button(new Rect(area.xMax - 200f, area.y + 5f, 188f, 30f), "Сбросить Совершенство"))
            {
                ProgressionService.RespecPerfection(p);
                SetStatus("Очки Совершенства возвращены.");
            }
            GUI.Label(new Rect(area.x + 12f, area.y + 35f, area.width - 24f, 21f), "Направления можно сочетать. Высокие узлы требуют предыдущего узла в своей цепочке.", _small);

            var viewport = new Rect(area.x + 6f, area.y + 62f, area.width - 12f, area.height - 68f);
            const float rowStep = 164f;
            const float headerH = 42f;
            var contentH = headerH + 7 * rowStep + 22f;
            _perfectionScroll = GUI.BeginScrollView(viewport, _perfectionScroll, new Rect(0f, 0f, viewport.width - 18f, contentH));
            var w = viewport.width - 24f;
            var gap = 12f;
            var colW = (w - gap * 2f) / 3f;
            var titles = new[] { "ТРИУМФ", "СТОЙКОСТЬ", "ЭКСПЕДИЦИЯ" };
            for (var c = 0; c < 3; c++)
            {
                var h = new Rect(c * (colW + gap), 0f, colW, 34f);
                FillRect(h, new Color(0.030f, 0.042f, 0.050f, 1f));
                DrawBorder(h, new Color(0.18f, 0.34f, 0.40f, 1f), 1f);
                GUI.Label(h, titles[c], _center);
            }

            foreach (var def in PerfectionCatalog.All)
            {
                if (string.IsNullOrEmpty(def.PrerequisiteId)) continue;
                var parent = PerfectionCatalog.Find(def.PrerequisiteId);
                if (parent == null) continue;
                var from = PerfectionNodeRect(parent, colW, gap, headerH, rowStep);
                var to = PerfectionNodeRect(def, colW, gap, headerH, rowStep);
                var active = PerfectionCatalog.GetRank(p, parent.Id) > 0;
                DrawConnection(from, to, active ? new Color(0.28f, 0.64f, 0.68f, 1f) : new Color(0.13f, 0.17f, 0.19f, 1f));
            }
            foreach (var def in PerfectionCatalog.All)
                DrawPerfectionNode(p, def, PerfectionNodeRect(def, colW, gap, headerH, rowStep));
            GUI.EndScrollView();
        }

        private Rect PerfectionNodeRect(PerfectionDef def, float colW, float gap, float headerH, float rowStep)
        {
            var x = def.Column * (colW + gap) + 7f;
            var y = headerH + def.Row * rowStep + 7f;
            return new Rect(x, y, colW - 14f, def.Major ? 146f : 132f);
        }

        private void DrawPerfectionNode(ProfileProgress p, PerfectionDef def, Rect rect)
        {
            var rank = PerfectionCatalog.GetRank(p, def.Id);
            var maxed = rank >= def.MaxRank;
            var levelOk = p.level >= def.UnlockLevel;
            var prereq = PerfectionCatalog.PrerequisiteMet(p, def);
            var fill = def.Major ? new Color(0.12f, 0.085f, 0.025f, 1f) : maxed ? new Color(0.040f, 0.14f, 0.11f, 1f) : new Color(0.030f, 0.040f, 0.047f, 1f);
            var border = def.Major ? new Color(0.85f, 0.62f, 0.18f, 1f) : maxed ? new Color(0.25f, 0.68f, 0.48f, 1f) : new Color(0.18f, 0.34f, 0.40f, 1f);
            FillRect(rect, fill); DrawBorder(rect, border, def.Major ? 2f : 1f);
            var iconRect = new Rect(rect.x + 8f, rect.y + 8f, 58f, 58f);
            FillRect(iconRect, new Color(0.01f, 0.015f, 0.019f, 1f));
            var icon = ResolveProgressionIcon(def.IconItem);
            if (icon != null) DrawSprite(iconRect, icon, levelOk ? Color.white : new Color(0.42f, 0.42f, 0.42f, 0.85f));
            else GUI.Label(iconRect, "✦", _center);
            DrawBorder(iconRect, border, 1f);
            var tx = rect.x + 74f; var tw = rect.width - 82f;
            GUI.Label(new Rect(tx, rect.y + 7f, tw, 36f), $"{def.Name} [{rank}/{def.MaxRank}]", _nodeTitle);
            GUI.Label(new Rect(tx, rect.y + 43f, tw, 48f), def.Description, _nodeEffect);
            var label = maxed ? "Изучено" : !levelOk ? $"Откроется: ур. {def.UnlockLevel}" : !prereq ? "Нужен предыдущий узел" : "Изучить";
            GUI.enabled = !maxed && levelOk && prereq && p.unspentPerfectionPoints > 0;
            if (GUI.Button(new Rect(tx, rect.yMax - 33f, tw, 27f), label))
            {
                if (!ProgressionService.TryBuyPerfection(p, def.Id, out var error)) SetStatus(error);
                else SetStatus($"Совершенство изучено: {def.Name}.");
            }
            GUI.enabled = true;
        }

        private Sprite ResolveProgressionIcon(string itemName)
        {
            if (string.IsNullOrEmpty(itemName)) return null;
            var item = ItemCatalog.allItemDefs.FirstOrDefault(x => x != null && string.Equals(x.name, itemName, StringComparison.OrdinalIgnoreCase));
            return item != null ? _iconResolver.Resolve(item) : null;
        }

        private void DrawLoadoutPage'''
ui, n = perf_pattern.subn(perf_method, ui, count=1)
if n != 1:
    raise RuntimeError("DrawPerfectionPage replacement failed")
save(p, ui)


# ---------- Version ----------
p, t = rw("Plugin.cs")
t = t.replace('public const string PluginVersion = "0.6.3";', 'public const string PluginVersion = "0.7.0";')
save(p, t)
p, t = rw("manifest.json")
t = t.replace('"version_number": "0.6.3"', '"version_number": "0.7.0"')
save(p, t)
p, t = rw("PetrichorLegacy.csproj")
t = t.replace('<Version>0.6.3</Version>', '<Version>0.7.0</Version>')
save(p, t)

print("Applied PetrichorLegacy 0.7.0 Mastery/Perfection overhaul")

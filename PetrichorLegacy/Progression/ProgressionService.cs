using System;
using System.Linq;
using PetrichorLegacy.Models;
using PetrichorLegacy.Persistence;
using RoR2;
using UnityEngine;

namespace PetrichorLegacy.Progression
{
    public static class ProgressionService
    {
        public static int LastAwardAmount { get; private set; }
        public static string LastAwardReason { get; private set; } = string.Empty;
        public static float LastAwardTime { get; private set; } = -100f;

        public static int XpRequiredForNextLevel(int level)
        {
            level = Math.Max(1, level);
            return Math.Max(1000, (int)Math.Round(900d + level * 110d + Math.Pow(level, 1.35d) * 20d));
        }

        public static int PrestigeLevel(int level) => Math.Max(0, level / 100);

        public static void AwardXp(ProfileProgress profile, int amount, string reason = null)
        {
            if (profile == null || amount <= 0) return;
            profile.currentXp += amount;
            profile.lifetimeXp += amount;
            LastAwardAmount = amount;
            LastAwardReason = string.IsNullOrWhiteSpace(reason) ? "Опыт" : reason;
            LastAwardTime = Time.unscaledTime;

            while (profile.currentXp >= XpRequiredForNextLevel(profile.level))
            {
                profile.currentXp -= XpRequiredForNextLevel(profile.level);
                profile.level++;
                GrantLevelRewards(profile, profile.level);
            }
            SaveService.SaveCurrent();
        }

        public static void GrantLevelRewards(ProfileProgress profile, int newLevel)
        {
            if (profile == null || newLevel < 2) return;
            if (newLevel <= 40) profile.unspentTalentPoints++;
            else
            {
                profile.unspentMasteryPoints++;
                if ((newLevel & 1) == 0) profile.unspentTalentPoints++;
            }
            if (newLevel % 25 == 0) profile.unspentPerfectionPoints++;
        }

        public static int EarnedTalentPointsForLevel(int level)
        {
            level = Math.Max(1, level);
            if (level <= 40) return level - 1;
            return 39 + (level - 40) / 2;
        }

        public static int EarnedMasteryPointsForLevel(int level) => Math.Max(0, level - 40);
        public static int EarnedPerfectionPointsForLevel(int level) => Math.Max(0, level / 25);

        public static bool TryBuyTalent(ProfileProgress profile, string talentId, out string error)
        {
            error = null;
            var def = TalentCatalog.Find(talentId);
            if (profile == null || def == null) { error = "Неизвестный талант."; return false; }
            if (profile.level < def.UnlockLevel) { error = $"Требуется мета-уровень {def.UnlockLevel}."; return false; }
            var current = TalentCatalog.GetRank(profile, talentId);
            if (current >= def.MaxRank) { error = "Талант уже изучен полностью."; return false; }
            if (!TalentCatalog.PrerequisiteMet(profile, def)) { error = "Сначала изучи предыдущий узел ветки."; return false; }
            if (profile.unspentTalentPoints < def.PointCost) { error = "Недостаточно очков талантов."; return false; }

            var record = profile.talents.FirstOrDefault(t => t.id == talentId);
            if (record == null)
            {
                record = new TalentRankRecord { id = talentId, rank = 0 };
                profile.talents.Add(record);
            }
            record.rank++;
            profile.unspentTalentPoints -= def.PointCost;
            SaveService.SaveCurrent();
            return true;
        }

        public static bool TryBuyMastery(ProfileProgress profile, string masteryId, out string error)
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
        }

        public static bool TryBuyPerfection(ProfileProgress profile, string perfectionId, out string error)
        {
            error = null;
            var def = PerfectionCatalog.Find(perfectionId);
            if (profile == null || def == null) { error = "Неизвестный узел Совершенства."; return false; }
            if (profile.level < def.UnlockLevel) { error = $"Требуется уровень {def.UnlockLevel}."; return false; }
            var rank = PerfectionCatalog.GetRank(profile, perfectionId);
            if (rank >= def.MaxRank) { error = "Узел уже изучен."; return false; }
            if (profile.unspentPerfectionPoints <= 0) { error = "Недостаточно очков Совершенства."; return false; }

            var record = profile.perfections.FirstOrDefault(x => x.id == perfectionId);
            if (record == null)
            {
                record = new PerfectionRankRecord { id = perfectionId, rank = 0 };
                profile.perfections.Add(record);
            }
            record.rank++;
            profile.unspentPerfectionPoints--;
            SaveService.SaveCurrent();
            return true;
        }

        public static bool TrySetActiveClass(ProfileProgress profile, string classId, out string error)
        {
            error = null;
            if (profile == null) return false;
            if (Run.instance != null) { error = "Класс можно менять только вне забега."; return false; }
            if (profile.level < 10) { error = "Классы открываются на 10 уровне."; return false; }
            if (classId != "Guardian" && classId != "Slayer" && classId != "Pathfinder" && classId != "Seeker")
            { error = "Неизвестный класс."; return false; }

            profile.activeClass = classId;
            if (!SpecBelongsToClass(profile.activeSpecialization, classId)) profile.activeSpecialization = string.Empty;
            SaveService.SaveCurrent();
            return true;
        }

        public static bool TrySetActiveSpecialization(ProfileProgress profile, string specId, out string error)
        {
            error = null;
            if (profile == null) return false;
            if (Run.instance != null) { error = "Специализацию можно менять только вне забега."; return false; }
            if (profile.level < 20) { error = "Специализации открываются на 20 уровне."; return false; }
            if (!SpecBelongsToClass(specId, profile.activeClass)) { error = "Эта специализация не принадлежит активному классу."; return false; }

            profile.activeSpecialization = specId;
            SaveService.SaveCurrent();
            return true;
        }

        public static bool SpecBelongsToClass(string specId, string classId)
        {
            if (string.IsNullOrEmpty(specId)) return true;
            switch (classId)
            {
                case "Guardian": return specId == "Bastion" || specId == "Unbroken" || specId == "Vanguard";
                case "Slayer": return specId == "Executioner" || specId == "Hunter" || specId == "Berserker";
                case "Pathfinder": return specId == "Scout" || specId == "Acrobat" || specId == "Saboteur";
                case "Seeker": return specId == "Merchant" || specId == "Prospector" || specId == "RelicKeeper";
                default: return false;
            }
        }

        public static void Respec(ProfileProgress profile)
        {
            if (profile == null) return;
            var refund = TalentCatalog.GetSpentPoints(profile);
            profile.talents.Clear();
            profile.unspentTalentPoints += refund;
            profile.activeClass = string.Empty;
            profile.activeSpecialization = string.Empty;
            profile.startingLoadout.Clear();
            SaveService.SaveCurrent();
        }

        public static int StartingCapacity(ProfileProgress profile)
        {
            if (profile == null) return 1;
            var level = profile.level;
            var capacity = 1;
            if (level >= 5) capacity = 2;
            if (level >= 10) capacity = 3;
            if (level >= 20) capacity = 5;
            if (level >= 40) capacity = 7;
            if (level >= 50) capacity = 10;
            if (level >= 70) capacity = 11;
            if (level >= 100) capacity = 12;
            if (level >= 150) capacity = 13;
            if (level >= 250) capacity = 14;
            if (level >= 400) capacity = 15;

            capacity += TalentCatalog.GetRank(profile, "legacy_pack");
            capacity += PerfectionCatalog.GetRank(profile, "perfection_pack");
            capacity += PerfectionCatalog.GetRank(profile, "perfection_prestige_treasurer");
            return capacity;
        }
    }
}

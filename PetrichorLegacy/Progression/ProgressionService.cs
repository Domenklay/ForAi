using System;
using System.Linq;
using PetrichorLegacy.Models;
using PetrichorLegacy.Persistence;

namespace PetrichorLegacy.Progression
{
    public static class ProgressionService
    {
        public static int XpRequiredForNextLevel(int level)
        {
            level = Math.Max(1, level);
            return 1200 + (level - 1) * 350 + ((level - 1) * (level - 1) * 18);
        }

        public static void AwardXp(ProfileProgress profile, int amount)
        {
            if (profile == null || amount <= 0) return;

            profile.currentXp += amount;
            profile.lifetimeXp += amount;

            while (profile.currentXp >= XpRequiredForNextLevel(profile.level))
            {
                profile.currentXp -= XpRequiredForNextLevel(profile.level);
                profile.level++;
                profile.unspentTalentPoints++;
            }

            SaveService.SaveCurrent();
        }

        public static bool TryBuyTalent(ProfileProgress profile, string talentId, out string error)
        {
            error = null;
            var def = TalentCatalog.Find(talentId);
            if (profile == null || def == null)
            {
                error = "Неизвестный талант.";
                return false;
            }

            var current = TalentCatalog.GetRank(profile, talentId);
            if (current >= def.MaxRank)
            {
                error = "Талант уже изучен полностью.";
                return false;
            }

            if (!TalentCatalog.PrerequisiteMet(profile, def))
            {
                error = "Сначала изучи предыдущий узел ветки.";
                return false;
            }

            if (profile.unspentTalentPoints < def.PointCost)
            {
                error = "Недостаточно очков талантов.";
                return false;
            }

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

        public static void Respec(ProfileProgress profile)
        {
            if (profile == null) return;
            var refund = TalentCatalog.GetSpentPoints(profile);
            profile.talents.Clear();
            profile.unspentTalentPoints += refund;
            profile.startingLoadout.Clear();
            SaveService.SaveCurrent();
        }

        public static int StartingCapacity(ProfileProgress profile)
        {
            return 1 + TalentCatalog.GetRank(profile, "expedition_capacity") * 2;
        }
    }
}

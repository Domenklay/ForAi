using System;
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

        public MasteryDef(string id, string name, string description, string classId, float perRank)
        {
            Id = id;
            Name = name;
            Description = description;
            ClassId = classId;
            PerRank = perRank;
        }
    }

    public static class MasteryCatalog
    {
        public static readonly IReadOnlyList<MasteryDef> All = new List<MasteryDef>
        {
            new MasteryDef("mastery_guardian_hp", "Крепость", "+0.15% максимального здоровья за эффективный ранг.", "Guardian", 0.0015f),
            new MasteryDef("mastery_guardian_armor", "Закалка", "+0.20 брони за эффективный ранг.", "Guardian", 0.20f),
            new MasteryDef("mastery_guardian_regen", "Восстановление", "+0.25% регенерации за эффективный ранг.", "Guardian", 0.0025f),
            new MasteryDef("mastery_guardian_shield", "Защитный контур", "+0.12% базового здоровья в виде щита за эффективный ранг.", "Guardian", 0.0012f),

            new MasteryDef("mastery_slayer_damage", "Мощь", "+0.12% урона за эффективный ранг.", "Slayer", 0.0012f),
            new MasteryDef("mastery_slayer_attack", "Темп", "+0.12% скорости атаки за эффективный ранг.", "Slayer", 0.0012f),
            new MasteryDef("mastery_slayer_cooldown", "Техника", "-0.05% времени восстановления за эффективный ранг.", "Slayer", 0.0005f),
            new MasteryDef("mastery_slayer_crit", "Точность", "+0.05% критического шанса за эффективный ранг.", "Slayer", 0.05f),

            new MasteryDef("mastery_path_move", "Шаг", "+0.15% скорости движения за эффективный ранг.", "Pathfinder", 0.0015f),
            new MasteryDef("mastery_path_sprint", "Спринтер", "+0.20% скорости спринта за эффективный ранг.", "Pathfinder", 0.0020f),
            new MasteryDef("mastery_path_jump", "Акробатика", "+0.25% силы прыжка за эффективный ранг.", "Pathfinder", 0.0025f),
            new MasteryDef("mastery_path_control", "Манёвренность", "+0.10% скорости движения после пересчёта за эффективный ранг.", "Pathfinder", 0.0010f),

            new MasteryDef("mastery_seeker_gold", "Торговля", "+0.20% золота с особых наград за эффективный ранг.", "Seeker", 0.0020f),
            new MasteryDef("mastery_seeker_specialxp", "Трофеи", "+0.15% XP за особых монстров за эффективный ранг.", "Seeker", 0.0015f),
            new MasteryDef("mastery_seeker_stagegold", "Запасы", "+0.20 золота в начале новой стадии за эффективный ранг.", "Seeker", 0.20f),
            new MasteryDef("mastery_seeker_startgold", "Капитал", "+0.15 стартового золота за эффективный ранг.", "Seeker", 0.15f)
        };

        private static readonly Dictionary<string, MasteryDef> ById = All.ToDictionary(x => x.Id, x => x);

        public static MasteryDef Find(string id) => id != null && ById.TryGetValue(id, out var def) ? def : null;

        public static int GetRank(ProfileProgress profile, string id)
        {
            if (profile?.masteries == null || string.IsNullOrEmpty(id)) return 0;
            return profile.masteries.FirstOrDefault(x => x.id == id)?.rank ?? 0;
        }

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

        public static int Milestone(int rank) => Math.Max(0, rank) / 10;
    }
}

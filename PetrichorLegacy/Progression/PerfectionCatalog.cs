using System.Collections.Generic;
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

        public PerfectionDef(string id, string name, string description, int unlockLevel, int maxRank = 1)
        {
            Id = id;
            Name = name;
            Description = description;
            UnlockLevel = unlockLevel;
            MaxRank = maxRank;
        }
    }

    public static class PerfectionCatalog
    {
        public static readonly IReadOnlyList<PerfectionDef> All = new List<PerfectionDef>
        {
            new PerfectionDef("perfection_giant_slayer", "Убийца великанов", "+3% урона боссам.", 25),
            new PerfectionDef("perfection_reserve", "Запас сил", "При переходе на новую стадию восстановить 5% здоровья.", 25),
            new PerfectionDef("perfection_hunter", "Легендарный охотник", "+10% XP за легендарных и более редких монстров.", 50),
            new PerfectionDef("perfection_pack", "Трофейный мешок", "+1 вместимость стартового Арсенала.", 50),
            new PerfectionDef("perfection_instinct", "Инстинкт выжившего", "+3 брони, когда здоровье ниже 30%.", 75),
            new PerfectionDef("perfection_pursuit", "Неотступность", "+3% скорости движения после убийства особого монстра на 8 сек.", 75),

            new PerfectionDef("perfection_prestige_hardened", "Престиж: закалённый", "+1% максимального здоровья.", 100),
            new PerfectionDef("perfection_prestige_predator", "Престиж: хищник", "+2% урона особым монстрам.", 100),
            new PerfectionDef("perfection_prestige_veteran", "Престиж: ветеран", "+1% скорости атаки и движения.", 200),
            new PerfectionDef("perfection_prestige_treasurer", "Престиж: хранитель", "+1 вместимость Арсенала.", 300)
        };

        private static readonly Dictionary<string, PerfectionDef> ById = All.ToDictionary(x => x.Id, x => x);

        public static PerfectionDef Find(string id) => id != null && ById.TryGetValue(id, out var def) ? def : null;

        public static int GetRank(ProfileProgress profile, string id)
        {
            if (profile?.perfections == null || string.IsNullOrEmpty(id)) return 0;
            return profile.perfections.FirstOrDefault(x => x.id == id)?.rank ?? 0;
        }
    }
}

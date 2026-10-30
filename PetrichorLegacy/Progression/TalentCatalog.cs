using System.Collections.Generic;
using System.Linq;
using PetrichorLegacy.Models;

namespace PetrichorLegacy.Progression
{
    public enum TalentBranch
    {
        Survival,
        Offense,
        Mobility,
        Fortune,
        Expedition
    }

    public sealed class TalentDef
    {
        public readonly string Id;
        public readonly string Name;
        public readonly string Description;
        public readonly TalentBranch Branch;
        public readonly int MaxRank;
        public readonly int PointCost;
        public readonly string PrerequisiteId;
        public readonly int PrerequisiteRank;

        public TalentDef(string id, string name, string description, TalentBranch branch, int maxRank,
            int pointCost = 1, string prerequisiteId = null, int prerequisiteRank = 0)
        {
            Id = id;
            Name = name;
            Description = description;
            Branch = branch;
            MaxRank = maxRank;
            PointCost = pointCost;
            PrerequisiteId = prerequisiteId;
            PrerequisiteRank = prerequisiteRank;
        }
    }

    public static class TalentCatalog
    {
        public static readonly IReadOnlyList<TalentDef> All = new List<TalentDef>
        {
            // Survival
            new TalentDef("survival_vitality", "Живучесть", "+2% максимального здоровья за ранг.", TalentBranch.Survival, 5),
            new TalentDef("survival_recovery", "Восстановление", "+4% регенерации здоровья за ранг.", TalentBranch.Survival, 5, prerequisiteId: "survival_vitality", prerequisiteRank: 3),
            new TalentDef("survival_armor", "Закалка", "+2 брони за ранг.", TalentBranch.Survival, 5, prerequisiteId: "survival_recovery", prerequisiteRank: 3),
            new TalentDef("survival_shield", "Энергетическая кожа", "+2% щита от базового здоровья за ранг.", TalentBranch.Survival, 3, prerequisiteId: "survival_armor", prerequisiteRank: 3),
            new TalentDef("survival_second_chance", "Второй шанс", "Раз за забег начинаешь с Dio's Best Friend.", TalentBranch.Survival, 1, 2, "survival_shield", 3),

            // Offense
            new TalentDef("offense_power", "Сила", "+2% урона за ранг.", TalentBranch.Offense, 5),
            new TalentDef("offense_frenzy", "Темп", "+2% скорости атаки за ранг.", TalentBranch.Offense, 5, prerequisiteId: "offense_power", prerequisiteRank: 3),
            new TalentDef("offense_precision", "Точность", "+1% критического шанса за ранг.", TalentBranch.Offense, 5, prerequisiteId: "offense_frenzy", prerequisiteRank: 3),
            new TalentDef("offense_cooldown", "Отточенная техника", "-1.5% времени восстановления навыков за ранг.", TalentBranch.Offense, 5, prerequisiteId: "offense_precision", prerequisiteRank: 3),
            new TalentDef("offense_executioner", "Палач", "+20% критического урона.", TalentBranch.Offense, 1, 2, "offense_cooldown", 5),

            // Mobility
            new TalentDef("mobility_stride", "Лёгкий шаг", "+2% скорости движения за ранг.", TalentBranch.Mobility, 5),
            new TalentDef("mobility_sprint", "Рывок", "+2% скорости спринта за ранг.", TalentBranch.Mobility, 5, prerequisiteId: "mobility_stride", prerequisiteRank: 3),
            new TalentDef("mobility_jump", "Пружина", "+4% силы прыжка за ранг.", TalentBranch.Mobility, 3, prerequisiteId: "mobility_sprint", prerequisiteRank: 3),
            new TalentDef("mobility_air", "Воздушный контроль", "+1 дополнительный прыжок.", TalentBranch.Mobility, 1, 2, "mobility_jump", 3),
            new TalentDef("mobility_mastery", "Неуловимость", "Ещё +5% скорости движения и +1 дополнительный прыжок.", TalentBranch.Mobility, 1, 2, "mobility_air", 1),

            // Fortune
            new TalentDef("fortune_luck", "Удача новичка", "+0.1 удачи за ранг.", TalentBranch.Fortune, 5),
            new TalentDef("fortune_gold", "Заначка", "+15 стартового золота за ранг.", TalentBranch.Fortune, 5, prerequisiteId: "fortune_luck", prerequisiteRank: 3),
            new TalentDef("fortune_stipend", "Полевое снабжение", "+10 золота за ранг в начале каждой новой стадии.", TalentBranch.Fortune, 5, prerequisiteId: "fortune_gold", prerequisiteRank: 3),
            new TalentDef("fortune_scavenger", "Сборщик", "+2% скорости движения и +2 брони за ранг.", TalentBranch.Fortune, 3, prerequisiteId: "fortune_stipend", prerequisiteRank: 3),
            new TalentDef("fortune_prospector", "Старатель", "После первой завершённой стадии получаешь случайный белый предмет раз за забег.", TalentBranch.Fortune, 1, 2, "fortune_scavenger", 3),

            // Expedition / starting kit
            new TalentDef("expedition_capacity", "Рюкзак", "+2 вместимости стартового набора за ранг. Базовая вместимость: 1.", TalentBranch.Expedition, 5),
            new TalentDef("expedition_green", "Необычные трофеи", "Разрешает зелёные предметы в стартовом наборе.", TalentBranch.Expedition, 1, 2, "expedition_capacity", 2),
            new TalentDef("expedition_red", "Легендарный груз", "Разрешает красные предметы.", TalentBranch.Expedition, 1, 2, "expedition_green", 1),
            new TalentDef("expedition_exotic", "Опасный багаж", "Разрешает боссовые, лунные и Void-предметы.", TalentBranch.Expedition, 1, 2, "expedition_red", 1),
            new TalentDef("expedition_hallowed", "Освящённый арсенал", "Разрешает Hallowed-предметы. Hexes и ключевые предметы по-прежнему запрещены.", TalentBranch.Expedition, 1, 3, "expedition_exotic", 1)
        };

        private static readonly Dictionary<string, TalentDef> ById = All.ToDictionary(t => t.Id, t => t);

        public static TalentDef Find(string id) => id != null && ById.TryGetValue(id, out var def) ? def : null;

        public static int GetRank(ProfileProgress profile, string id)
        {
            if (profile == null || string.IsNullOrEmpty(id)) return 0;
            var record = profile.talents.FirstOrDefault(t => t.id == id);
            return record?.rank ?? 0;
        }

        public static int GetSpentPoints(ProfileProgress profile)
        {
            if (profile == null) return 0;
            var total = 0;
            foreach (var record in profile.talents)
            {
                var def = Find(record.id);
                if (def == null) continue;
                total += System.Math.Min(record.rank, def.MaxRank) * def.PointCost;
            }
            return total;
        }

        public static bool PrerequisiteMet(ProfileProgress profile, TalentDef def)
        {
            if (def == null || string.IsNullOrEmpty(def.PrerequisiteId)) return true;
            return GetRank(profile, def.PrerequisiteId) >= def.PrerequisiteRank;
        }
    }
}

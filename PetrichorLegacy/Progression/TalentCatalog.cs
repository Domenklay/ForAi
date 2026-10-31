using System.Collections.Generic;
using System.Linq;
using PetrichorLegacy.Models;

namespace PetrichorLegacy.Progression
{
    public enum TalentBranch
    {
        Legacy,
        Guardian,
        GuardianBastion,
        GuardianUnbroken,
        GuardianVanguard,
        Slayer,
        SlayerExecutioner,
        SlayerHunter,
        SlayerBerserker,
        Pathfinder,
        PathfinderScout,
        PathfinderAcrobat,
        PathfinderSaboteur,
        Seeker,
        SeekerMerchant,
        SeekerProspector,
        SeekerRelicKeeper
    }

    public sealed class TalentDef
    {
        public readonly string Id;
        public readonly string Name;
        public readonly string Description;
        public readonly TalentBranch Branch;
        public readonly int MaxRank;
        public readonly int PointCost;
        public readonly int UnlockLevel;
        public readonly string PrerequisiteId;
        public readonly int PrerequisiteRank;
        public readonly int TreeColumn;
        public readonly int TreeRow;

        public TalentDef(string id, string name, string description, TalentBranch branch, int maxRank,
            int pointCost = 1, int unlockLevel = 1, string prerequisiteId = null, int prerequisiteRank = 0,
            int treeColumn = 1, int treeRow = 0)
        {
            Id = id;
            Name = name;
            Description = description;
            Branch = branch;
            MaxRank = maxRank;
            PointCost = pointCost;
            UnlockLevel = unlockLevel;
            PrerequisiteId = prerequisiteId;
            PrerequisiteRank = prerequisiteRank;
            TreeColumn = treeColumn;
            TreeRow = treeRow;
        }
    }

    public static class TalentCatalog
    {
        public static readonly IReadOnlyList<TalentDef> All = new List<TalentDef>
        {
            // НАСЛЕДИЕ — маленькие универсальные бонусы.
            new TalentDef("legacy_hp", "Закалённый", "+1% максимального здоровья за ранг.", TalentBranch.Legacy, 3, treeColumn: 1, treeRow: 0),
            new TalentDef("legacy_damage", "Точная рука", "+1% урона за ранг.", TalentBranch.Legacy, 3, prerequisiteId: "legacy_hp", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("legacy_move", "Лёгкая поступь", "+1.5% скорости движения за ранг.", TalentBranch.Legacy, 2, prerequisiteId: "legacy_hp", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("legacy_attack", "Быстрая реакция", "+1% скорости атаки за ранг.", TalentBranch.Legacy, 2, prerequisiteId: "legacy_damage", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("legacy_armor", "Подготовка", "+1 брони за ранг.", TalentBranch.Legacy, 2, prerequisiteId: "legacy_move", prerequisiteRank: 1, treeColumn: 2, treeRow: 2),
            new TalentDef("legacy_pack", "Рюкзак", "+1 вместимость стартового Арсенала за ранг.", TalentBranch.Legacy, 2, prerequisiteId: "legacy_attack", prerequisiteRank: 1, treeColumn: 0, treeRow: 3),
            new TalentDef("legacy_regen", "Полевой рацион", "+2% естественной регенерации за ранг.", TalentBranch.Legacy, 2, prerequisiteId: "legacy_armor", prerequisiteRank: 1, treeColumn: 2, treeRow: 3),

            // СТРАЖ — лучшая защита, но почти без прироста урона.
            new TalentDef("guardian_vitality", "Крепкое тело", "+1.5% максимального здоровья за ранг.", TalentBranch.Guardian, 3, unlockLevel: 10, treeColumn: 1, treeRow: 0),
            new TalentDef("guardian_armor", "Закалённая кожа", "+2 брони за ранг.", TalentBranch.Guardian, 3, unlockLevel: 10, prerequisiteId: "guardian_vitality", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("guardian_regen", "Восстановление", "+4% регенерации здоровья за ранг.", TalentBranch.Guardian, 2, unlockLevel: 10, prerequisiteId: "guardian_vitality", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("guardian_stability", "Стабилизация", "+1.5% базового здоровья в виде щита за ранг.", TalentBranch.Guardian, 2, unlockLevel: 12, prerequisiteId: "guardian_armor", prerequisiteRank: 1, treeColumn: 0, treeRow: 2),
            new TalentDef("guardian_stageheal", "Передышка", "На новой стадии восстановить 4% здоровья за ранг.", TalentBranch.Guardian, 2, unlockLevel: 12, prerequisiteId: "guardian_regen", prerequisiteRank: 1, treeColumn: 2, treeRow: 2),
            new TalentDef("guardian_endurance", "Стойкость", "+1% здоровья и +2 брони.", TalentBranch.Guardian, 1, 2, 15, "guardian_stageheal", 2, 1, 3),
            new TalentDef("guardian_void_capstone", "Пустотный бастион", "Классовый фиолетовый финал: каждый забег начинается с 1 Safer Spaces.", TalentBranch.Guardian, 1, 3, 18, "guardian_endurance", 1, 1, 4),

            // СТРАЖ / БАСТИОН — щиты и анти-снаряды.
            new TalentDef("bastion_shield", "Энергетический слой", "+2% базового здоровья в виде щита за ранг.", TalentBranch.GuardianBastion, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("bastion_armor", "Укрепление", "+2 брони за ранг.", TalentBranch.GuardianBastion, 2, unlockLevel: 20, prerequisiteId: "bastion_shield", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("bastion_health", "Плотный контур", "+1.5% здоровья за ранг.", TalentBranch.GuardianBastion, 2, unlockLevel: 22, prerequisiteId: "bastion_shield", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("bastion_stagebarrier", "Аварийный щит", "На новой стадии получить барьер 4% HP за ранг.", TalentBranch.GuardianBastion, 2, unlockLevel: 25, prerequisiteId: "bastion_armor", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("bastion_lastwall", "Последний рубеж", "+5% щита и +3 брони.", TalentBranch.GuardianBastion, 1, 2, 35, "bastion_stagebarrier", 2, 1, 3),
            new TalentDef("bastion_legendary", "Легенда: Защитные микроботы", "Финал подкласса: каждый забег начинается с 1 Defensive Microbots, сбивающего опасные снаряды.", TalentBranch.GuardianBastion, 1, 3, 45, "bastion_lastwall", 1, 1, 4),

            // СТРАЖ / НЕСОКРУШИМЫЙ — лечение и восстановление.
            new TalentDef("unbroken_regen", "Второе дыхание", "+5% регенерации за ранг.", TalentBranch.GuardianUnbroken, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("unbroken_health", "Живучий", "+1.5% здоровья за ранг.", TalentBranch.GuardianUnbroken, 2, unlockLevel: 20, prerequisiteId: "unbroken_regen", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("unbroken_stageheal", "Спокойствие", "На новой стадии восстановить ещё 3% здоровья за ранг.", TalentBranch.GuardianUnbroken, 2, unlockLevel: 22, prerequisiteId: "unbroken_regen", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("unbroken_bossheal", "Передышка после боя", "Убийство босса восстанавливает 5% здоровья за ранг.", TalentBranch.GuardianUnbroken, 2, unlockLevel: 25, prerequisiteId: "unbroken_health", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("unbroken_ironwill", "Железная воля", "+5 брони и +5% регенерации.", TalentBranch.GuardianUnbroken, 1, 2, 35, "unbroken_bossheal", 2, 1, 3),
            new TalentDef("unbroken_legendary", "Легенда: Омолаживающая стойка", "Финал подкласса: каждый забег начинается с 1 Rejuvenation Rack.", TalentBranch.GuardianUnbroken, 1, 3, 45, "unbroken_ironwill", 1, 1, 4),

            // СТРАЖ / АВАНГАРД — защитник, который давит вперёд.
            new TalentDef("vanguard_damage", "Ответный натиск", "+1% урона за ранг.", TalentBranch.GuardianVanguard, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("vanguard_move", "Линия фронта", "+1.5% скорости движения за ранг.", TalentBranch.GuardianVanguard, 2, unlockLevel: 20, prerequisiteId: "vanguard_damage", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("vanguard_armor", "Плечом вперёд", "+2 брони за ранг.", TalentBranch.GuardianVanguard, 2, unlockLevel: 20, prerequisiteId: "vanguard_damage", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("vanguard_attack", "Боевой темп", "+1.5% скорости атаки за ранг.", TalentBranch.GuardianVanguard, 2, unlockLevel: 25, prerequisiteId: "vanguard_move", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("vanguard_breaker", "Продавить строй", "+2% урона и +2 брони.", TalentBranch.GuardianVanguard, 1, 2, 35, "vanguard_attack", 2, 1, 3),
            new TalentDef("vanguard_legendary", "Легенда: Разрушительное правосудие", "Финал подкласса: каждый забег начинается с 1 Shattering Justice.", TalentBranch.GuardianVanguard, 1, 3, 45, "vanguard_breaker", 1, 1, 4),

            // ИСТРЕБИТЕЛЬ — лучший прямой урон, почти без защиты.
            new TalentDef("slayer_damage", "Натиск", "+1.5% урона за ранг.", TalentBranch.Slayer, 3, unlockLevel: 10, treeColumn: 1, treeRow: 0),
            new TalentDef("slayer_attack", "Темп", "+1% скорости атаки за ранг.", TalentBranch.Slayer, 3, unlockLevel: 10, prerequisiteId: "slayer_damage", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("slayer_crit", "Точность", "+1% критического шанса за ранг.", TalentBranch.Slayer, 2, unlockLevel: 10, prerequisiteId: "slayer_damage", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("slayer_cooldown", "Техника", "-1% времени восстановления навыков за ранг.", TalentBranch.Slayer, 2, unlockLevel: 12, prerequisiteId: "slayer_attack", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("slayer_move", "Адреналин", "+1.5% скорости движения за ранг.", TalentBranch.Slayer, 2, unlockLevel: 12, prerequisiteId: "slayer_crit", prerequisiteRank: 1, treeColumn: 2, treeRow: 2),
            new TalentDef("slayer_focus", "Боевая концентрация", "+2% урона и +1% скорости атаки.", TalentBranch.Slayer, 1, 2, 15, "slayer_cooldown", 2, 1, 3),
            new TalentDef("slayer_void_capstone", "Игла Бездны", "Классовый фиолетовый финал: каждый забег начинается с 1 Needletick.", TalentBranch.Slayer, 1, 3, 18, "slayer_focus", 1, 1, 4),

            // ИСТРЕБИТЕЛЬ / ПАЛАЧ — криты и добивание.
            new TalentDef("executioner_power", "Приоритетная цель", "+1% урона за ранг.", TalentBranch.SlayerExecutioner, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("executioner_critdamage", "Точный удар", "+5% критического урона за ранг.", TalentBranch.SlayerExecutioner, 2, unlockLevel: 20, prerequisiteId: "executioner_power", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("executioner_cooldown", "Хладнокровие", "-1% времени восстановления за ранг.", TalentBranch.SlayerExecutioner, 2, unlockLevel: 22, prerequisiteId: "executioner_power", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("executioner_attack", "Не отпускать", "+1.5% скорости атаки за ранг.", TalentBranch.SlayerExecutioner, 2, unlockLevel: 25, prerequisiteId: "executioner_critdamage", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("executioner_verdict", "Приговор", "+2% урона и +10% критического урона.", TalentBranch.SlayerExecutioner, 1, 2, 35, "executioner_attack", 2, 1, 3),
            new TalentDef("executioner_legendary", "Легенда: Церемониальный кинжал", "Финал подкласса: каждый забег начинается с 1 Ceremonial Dagger.", TalentBranch.SlayerExecutioner, 1, 3, 45, "executioner_verdict", 1, 1, 4),

            // ИСТРЕБИТЕЛЬ / ОХОТНИК — особые монстры и элитная добыча.
            new TalentDef("hunter_specialxp", "Знаток добычи", "+5% XP за особых монстров за ранг.", TalentBranch.SlayerHunter, 2, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("hunter_specialgold", "Трофейщик", "+10% золота за особых монстров за ранг.", TalentBranch.SlayerHunter, 2, unlockLevel: 20, prerequisiteId: "hunter_specialxp", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("hunter_haste", "Охотничий азарт", "Убийство эпического+ врага даёт +4% скорости атаки на 8 сек. за ранг.", TalentBranch.SlayerHunter, 2, unlockLevel: 22, prerequisiteId: "hunter_specialxp", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("hunter_legend", "Большая добыча", "Легендарные+ враги дают ещё +20% золота.", TalentBranch.SlayerHunter, 1, unlockLevel: 25, prerequisiteId: "hunter_specialgold", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("hunter_greathunt", "Великая охота", "Первый мифический+ враг каждой стадии даёт +50% своей XP-награды.", TalentBranch.SlayerHunter, 1, 2, 35, "hunter_haste", 2, 1, 3),
            new TalentDef("hunter_legendary", "Легенда: Пробуждение стервятников", "Финал подкласса: каждый забег начинается с 1 Wake of Vultures.", TalentBranch.SlayerHunter, 1, 3, 45, "hunter_greathunt", 1, 1, 4),

            // ИСТРЕБИТЕЛЬ / БЕРСЕРК — непрерывный темп и ближняя агрессия.
            new TalentDef("berserker_attack", "Ярость", "+2% скорости атаки за ранг.", TalentBranch.SlayerBerserker, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("berserker_damage", "Размашистый удар", "+1.5% урона за ранг.", TalentBranch.SlayerBerserker, 2, unlockLevel: 20, prerequisiteId: "berserker_attack", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("berserker_move", "В погоню", "+1.5% скорости движения за ранг.", TalentBranch.SlayerBerserker, 2, unlockLevel: 20, prerequisiteId: "berserker_attack", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("berserker_cooldown", "Без остановки", "-1% времени восстановления навыков за ранг.", TalentBranch.SlayerBerserker, 2, unlockLevel: 25, prerequisiteId: "berserker_damage", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("berserker_frenzy", "Кровавая ярость", "+2% урона и +2% скорости атаки.", TalentBranch.SlayerBerserker, 1, 2, 35, "berserker_cooldown", 2, 1, 3),
            new TalentDef("berserker_legendary", "Легенда: Катушка Теслы", "Финал подкласса: каждый забег начинается с 1 Unstable Tesla Coil.", TalentBranch.SlayerBerserker, 1, 3, 45, "berserker_frenzy", 1, 1, 4),

            // СЛЕДОПЫТ — лучший темп, мобильность и позиционирование.
            new TalentDef("path_move", "Походный шаг", "+1.5% скорости движения за ранг.", TalentBranch.Pathfinder, 3, unlockLevel: 10, treeColumn: 1, treeRow: 0),
            new TalentDef("path_sprint", "Бегун", "+2% скорости спринта за ранг.", TalentBranch.Pathfinder, 2, unlockLevel: 10, prerequisiteId: "path_move", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("path_jump", "Пружина", "+5% силы прыжка за ранг.", TalentBranch.Pathfinder, 2, unlockLevel: 10, prerequisiteId: "path_move", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("path_armor", "Уверенное движение", "+1 брони за ранг.", TalentBranch.Pathfinder, 2, unlockLevel: 12, prerequisiteId: "path_sprint", prerequisiteRank: 1, treeColumn: 0, treeRow: 2),
            new TalentDef("path_control", "Манёвренность", "+1% скорости движения за ранг.", TalentBranch.Pathfinder, 2, unlockLevel: 12, prerequisiteId: "path_jump", prerequisiteRank: 1, treeColumn: 2, treeRow: 2),
            new TalentDef("path_flow", "Поток странника", "+2% скорости движения.", TalentBranch.Pathfinder, 1, 2, 15, "path_control", 2, 1, 3),
            new TalentDef("path_void_capstone", "Полиимпульс", "Классовый фиолетовый финал: каждый забег начинается с 1 Polylute.", TalentBranch.Pathfinder, 1, 3, 18, "path_flow", 1, 1, 4),

            // СЛЕДОПЫТ / РАЗВЕДЧИК — скорость прохождения и частые навыки.
            new TalentDef("scout_move", "Маршрут", "+1.5% скорости движения за ранг.", TalentBranch.PathfinderScout, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("scout_sprint", "Быстрый старт", "+2% скорости спринта за ранг.", TalentBranch.PathfinderScout, 2, unlockLevel: 20, prerequisiteId: "scout_move", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("scout_stagegold", "Полевое снабжение", "+10 золота на новой стадии за ранг.", TalentBranch.PathfinderScout, 2, unlockLevel: 22, prerequisiteId: "scout_move", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("scout_jump", "Срез пути", "+5% силы прыжка за ранг.", TalentBranch.PathfinderScout, 2, unlockLevel: 25, prerequisiteId: "scout_sprint", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("scout_expedition", "Экспедиция", "+4% скорости движения и +20 золота на новой стадии.", TalentBranch.PathfinderScout, 1, 2, 35, "scout_stagegold", 2, 1, 3),
            new TalentDef("scout_legendary", "Легенда: Чужеродная голова", "Финал подкласса: каждый забег начинается с 1 Alien Head.", TalentBranch.PathfinderScout, 1, 3, 45, "scout_expedition", 1, 1, 4),

            // СЛЕДОПЫТ / АКРОБАТ — воздух, рывки и вертикальное перемещение.
            new TalentDef("acro_jump", "Лёгкость", "+6% силы прыжка за ранг.", TalentBranch.PathfinderAcrobat, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("acro_move", "Инерция", "+1.5% скорости движения за ранг.", TalentBranch.PathfinderAcrobat, 2, unlockLevel: 20, prerequisiteId: "acro_jump", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("acro_armor", "Мягкое приземление", "+1 брони за ранг.", TalentBranch.PathfinderAcrobat, 2, unlockLevel: 22, prerequisiteId: "acro_jump", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("acro_extra_jump", "Дополнительный импульс", "+1 дополнительный прыжок.", TalentBranch.PathfinderAcrobat, 1, 2, 25, "acro_move", 2, 0, 2),
            new TalentDef("acro_elusive", "Неуловимый", "+3% скорости движения и +5% силы прыжка.", TalentBranch.PathfinderAcrobat, 1, 2, 35, "acro_extra_jump", 1, 1, 3),
            new TalentDef("acro_legendary", "Легенда: Жёсткий форсаж", "Финал подкласса: каждый забег начинается с 1 Hardlight Afterburner.", TalentBranch.PathfinderAcrobat, 1, 3, 45, "acro_elusive", 1, 1, 4),

            // СЛЕДОПЫТ / ДИВЕРСАНТ — контроль толпы и частые навыки.
            new TalentDef("saboteur_cooldown", "Подготовленный заряд", "-1% времени восстановления навыков за ранг.", TalentBranch.PathfinderSaboteur, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("saboteur_damage", "Точный подрыв", "+1% урона за ранг.", TalentBranch.PathfinderSaboteur, 2, unlockLevel: 20, prerequisiteId: "saboteur_cooldown", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("saboteur_move", "Отход после подрыва", "+1.5% скорости движения за ранг.", TalentBranch.PathfinderSaboteur, 2, unlockLevel: 20, prerequisiteId: "saboteur_cooldown", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("saboteur_attack", "Быстрый запал", "+1.5% скорости атаки за ранг.", TalentBranch.PathfinderSaboteur, 2, unlockLevel: 25, prerequisiteId: "saboteur_damage", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("saboteur_chain", "Цепная реакция", "+2% урона и -2% времени восстановления навыков.", TalentBranch.PathfinderSaboteur, 1, 2, 35, "saboteur_attack", 2, 1, 3),
            new TalentDef("saboteur_legendary", "Легенда: Разумный крюк", "Финал подкласса: каждый забег начинается с 1 Sentient Meat Hook.", TalentBranch.PathfinderSaboteur, 1, 3, 45, "saboteur_chain", 1, 1, 4),

            // ИСКАТЕЛЬ — лучший долгосрочный ресурс и utility.
            new TalentDef("seeker_startgold", "Припас", "+10 стартового золота за ранг.", TalentBranch.Seeker, 3, unlockLevel: 10, treeColumn: 1, treeRow: 0),
            new TalentDef("seeker_stagegold", "Запасы", "+10 золота на новой стадии за ранг.", TalentBranch.Seeker, 3, unlockLevel: 10, prerequisiteId: "seeker_startgold", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("seeker_specialgold", "Сборщик", "+10% золота за особых монстров за ранг.", TalentBranch.Seeker, 2, unlockLevel: 10, prerequisiteId: "seeker_startgold", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("seeker_move", "Деловая хватка", "+1% скорости движения за ранг.", TalentBranch.Seeker, 2, unlockLevel: 12, prerequisiteId: "seeker_stagegold", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("seeker_armor", "Осторожный сборщик", "+1 брони за ранг.", TalentBranch.Seeker, 2, unlockLevel: 12, prerequisiteId: "seeker_specialgold", prerequisiteRank: 1, treeColumn: 2, treeRow: 2),
            new TalentDef("seeker_cache", "Тайник экспедиции", "+25 стартового золота.", TalentBranch.Seeker, 1, 2, 15, "seeker_move", 2, 1, 3),
            new TalentDef("seeker_void_capstone", "Пустотный ключ", "Классовый фиолетовый финал: каждый забег начинается с 1 Encrusted Key.", TalentBranch.Seeker, 1, 3, 18, "seeker_cache", 1, 1, 4),

            // ИСКАТЕЛЬ / ТОРГОВЕЦ — экономика, дроны и покупки.
            new TalentDef("merchant_startgold", "Финансовая подушка", "+15 стартового золота за ранг.", TalentBranch.SeekerMerchant, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("merchant_stagegold", "Инвестиция", "+15 золота на новой стадии за ранг.", TalentBranch.SeekerMerchant, 3, unlockLevel: 20, prerequisiteId: "merchant_startgold", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("merchant_specialgold", "Выгодный трофей", "+10% золота за особых монстров за ранг.", TalentBranch.SeekerMerchant, 2, unlockLevel: 22, prerequisiteId: "merchant_startgold", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("merchant_reserve", "Резерв", "+25 золота после завершения каждой стадии.", TalentBranch.SeekerMerchant, 1, unlockLevel: 25, prerequisiteId: "merchant_stagegold", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("merchant_capital", "Капитал", "На новой стадии получить ещё 10 × номер стадии золота.", TalentBranch.SeekerMerchant, 1, 2, 35, "merchant_reserve", 1, 1, 3),
            new TalentDef("merchant_legendary", "Легенда: Запчасти дронов", "Финал подкласса: каждый забег начинается с 1 Spare Drone Parts.", TalentBranch.SeekerMerchant, 1, 3, 45, "merchant_capital", 1, 1, 4),

            // ИСКАТЕЛЬ / СТАРАТЕЛЬ — трофеи и редкие находки.
            new TalentDef("prospector_specialgold", "Искатель сокровищ", "+10% золота за особых монстров за ранг.", TalentBranch.SeekerProspector, 2, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("prospector_white3", "Удачная партия", "После каждых 3 завершённых стадий получить случайный белый предмет.", TalentBranch.SeekerProspector, 1, unlockLevel: 20, prerequisiteId: "prospector_specialgold", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("prospector_legendwhite", "Ценный трофей", "Первый легендарный+ враг за забег даёт случайный белый предмет.", TalentBranch.SeekerProspector, 1, unlockLevel: 22, prerequisiteId: "prospector_specialgold", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("prospector_mythgreen", "Большая находка", "Первый мифический+ враг за забег имеет 25% шанс дать случайный зелёный предмет.", TalentBranch.SeekerProspector, 1, 2, 25, "prospector_legendwhite", 1, 2, 2),
            new TalentDef("prospector_goldmine", "Золотая жила", "Каждая пятая завершённая стадия даёт случайный зелёный предмет.", TalentBranch.SeekerProspector, 1, 2, 35, "prospector_white3", 1, 1, 3),
            new TalentDef("prospector_legendary", "Легенда: 57-листный клевер", "Финал подкласса: каждый забег начинается с 1 57 Leaf Clover.", TalentBranch.SeekerProspector, 1, 3, 45, "prospector_goldmine", 1, 1, 4),

            // ИСКАТЕЛЬ / РЕЛИКВАРИЙ — снаряжение и универсальная полезность.
            new TalentDef("relic_cooldown", "Знание реликвий", "-1% времени восстановления навыков за ранг.", TalentBranch.SeekerRelicKeeper, 3, unlockLevel: 20, treeColumn: 1, treeRow: 0),
            new TalentDef("relic_move", "Быстрый доступ", "+1.5% скорости движения за ранг.", TalentBranch.SeekerRelicKeeper, 2, unlockLevel: 20, prerequisiteId: "relic_cooldown", prerequisiteRank: 1, treeColumn: 0, treeRow: 1),
            new TalentDef("relic_armor", "Защитный футляр", "+2 брони за ранг.", TalentBranch.SeekerRelicKeeper, 2, unlockLevel: 20, prerequisiteId: "relic_cooldown", prerequisiteRank: 1, treeColumn: 2, treeRow: 1),
            new TalentDef("relic_attack", "Настроенный механизм", "+1.5% скорости атаки за ранг.", TalentBranch.SeekerRelicKeeper, 2, unlockLevel: 25, prerequisiteId: "relic_move", prerequisiteRank: 2, treeColumn: 0, treeRow: 2),
            new TalentDef("relic_attunement", "Настройка реликвии", "+2% скорости движения и -2% времени восстановления навыков.", TalentBranch.SeekerRelicKeeper, 1, 2, 35, "relic_attack", 2, 1, 3),
            new TalentDef("relic_legendary", "Легенда: Связанный душой катализатор", "Финал подкласса: каждый забег начинается с 1 Soulbound Catalyst.", TalentBranch.SeekerRelicKeeper, 1, 3, 45, "relic_attunement", 1, 1, 4)
        };

        private static readonly Dictionary<string, TalentDef> ById = All.ToDictionary(t => t.Id, t => t);

        public static TalentDef Find(string id) => id != null && ById.TryGetValue(id, out var def) ? def : null;

        public static int GetRank(ProfileProgress profile, string id)
        {
            if (profile?.talents == null || string.IsNullOrEmpty(id)) return 0;
            return profile.talents.FirstOrDefault(t => t.id == id)?.rank ?? 0;
        }

        public static int GetSpentPoints(ProfileProgress profile)
        {
            if (profile?.talents == null) return 0;
            var total = 0;
            foreach (var record in profile.talents)
            {
                var def = Find(record.id);
                if (def != null) total += System.Math.Min(record.rank, def.MaxRank) * def.PointCost;
            }
            return total;
        }

        public static bool PrerequisiteMet(ProfileProgress profile, TalentDef def)
        {
            if (def == null || string.IsNullOrEmpty(def.PrerequisiteId)) return true;
            return GetRank(profile, def.PrerequisiteId) >= def.PrerequisiteRank;
        }

        public static string ClassForBranch(TalentBranch branch)
        {
            switch (branch)
            {
                case TalentBranch.Guardian:
                case TalentBranch.GuardianBastion:
                case TalentBranch.GuardianUnbroken:
                case TalentBranch.GuardianVanguard: return "Guardian";
                case TalentBranch.Slayer:
                case TalentBranch.SlayerExecutioner:
                case TalentBranch.SlayerHunter:
                case TalentBranch.SlayerBerserker: return "Slayer";
                case TalentBranch.Pathfinder:
                case TalentBranch.PathfinderScout:
                case TalentBranch.PathfinderAcrobat:
                case TalentBranch.PathfinderSaboteur: return "Pathfinder";
                case TalentBranch.Seeker:
                case TalentBranch.SeekerMerchant:
                case TalentBranch.SeekerProspector:
                case TalentBranch.SeekerRelicKeeper: return "Seeker";
                default: return string.Empty;
            }
        }

        public static string SpecForBranch(TalentBranch branch)
        {
            switch (branch)
            {
                case TalentBranch.GuardianBastion: return "Bastion";
                case TalentBranch.GuardianUnbroken: return "Unbroken";
                case TalentBranch.GuardianVanguard: return "Vanguard";
                case TalentBranch.SlayerExecutioner: return "Executioner";
                case TalentBranch.SlayerHunter: return "Hunter";
                case TalentBranch.SlayerBerserker: return "Berserker";
                case TalentBranch.PathfinderScout: return "Scout";
                case TalentBranch.PathfinderAcrobat: return "Acrobat";
                case TalentBranch.PathfinderSaboteur: return "Saboteur";
                case TalentBranch.SeekerMerchant: return "Merchant";
                case TalentBranch.SeekerProspector: return "Prospector";
                case TalentBranch.SeekerRelicKeeper: return "RelicKeeper";
                default: return string.Empty;
            }
        }

        public static bool IsBranchActive(ProfileProgress profile, TalentBranch branch)
        {
            if (branch == TalentBranch.Legacy) return true;
            if (profile == null) return false;
            var classId = ClassForBranch(branch);
            if (profile.activeClass != classId) return false;
            var specId = SpecForBranch(branch);
            return string.IsNullOrEmpty(specId) || profile.activeSpecialization == specId;
        }

        public static int GetActiveRank(ProfileProgress profile, string id)
        {
            var def = Find(id);
            return def != null && IsBranchActive(profile, def.Branch) ? GetRank(profile, id) : 0;
        }
    }
}

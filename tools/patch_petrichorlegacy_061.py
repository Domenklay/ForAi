from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"

monster_traits = r'''using System;
using System.Collections.Generic;
using System.Linq;
using RoR2;
using UnityEngine;
using UnityEngine.Networking;

namespace PetrichorLegacy.Progression
{
    public enum MonsterTraitCategory
    {
        Offense,
        Defense,
        Mobility,
        Sustain,
        Aura,
        Major
    }

    public sealed class MonsterTraitDef
    {
        public readonly string Id;
        public readonly string Name;
        public readonly string Code;
        public readonly string Description;
        public readonly MonsterTraitCategory Category;
        public readonly MonsterRarity MinRarity;
        public readonly bool Major;
        public readonly float Weight;
        public readonly string Group;

        public MonsterTraitDef(string id, string name, string code, string description,
            MonsterTraitCategory category, MonsterRarity minRarity, string group,
            bool major = false, float weight = 1f)
        {
            Id = id;
            Name = name;
            Code = code;
            Description = description;
            Category = category;
            MinRarity = minRarity;
            Group = group ?? string.Empty;
            Major = major;
            Weight = Mathf.Max(0.01f, weight);
        }
    }

    public static class MonsterTraitSystem
    {
        // 32 regular mechanical affixes + 10 Ancient+ identity affixes.
        // Pure stat-only affixes were removed: every entry changes timing, positioning, priority or group behavior.
        public static readonly IReadOnlyList<MonsterTraitDef> All = new List<MonsterTraitDef>
        {
            new MonsterTraitDef("ambusher", "Засадник", "ZA", "Первый удар после 6 секунд без атаки наносит +35% урона.", MonsterTraitCategory.Offense, MonsterRarity.Epic, "tempo", weight: 1.0f),
            new MonsterTraitDef("duelist", "Дуэлянт", "DU", "После своей атаки на 2 секунды получает на 25% больше урона.", MonsterTraitCategory.Offense, MonsterRarity.Epic, "tempo", weight: 1.0f),
            new MonsterTraitDef("avenger", "Мститель", "MS", "Смерть другого монстра рядом вводит его в ярость на 8 секунд.", MonsterTraitCategory.Offense, MonsterRarity.Epic, "tempo", weight: 0.9f),
            new MonsterTraitDef("regenerator", "Регенератор", "RG", "После 4 секунд без полученного урона начинает быстро восстанавливать здоровье.", MonsterTraitCategory.Sustain, MonsterRarity.Epic, "sustain", weight: 0.9f),
            new MonsterTraitDef("barrierforge", "Барьерник", "BR", "Раз в 10 секунд создаёт барьер; окно хорошо видно по заполнению барьера.", MonsterTraitCategory.Sustain, MonsterRarity.Epic, "sustain", weight: 0.9f),
            new MonsterTraitDef("frontal", "Фронтальная броня", "FB", "Спереди получает на 35% меньше урона, сзади — на 25% больше.", MonsterTraitCategory.Defense, MonsterRarity.Epic, "defense", weight: 0.9f),
            new MonsterTraitDef("dasher", "Рывок", "RV", "Если цель далеко, раз в несколько секунд резко сокращает дистанцию.", MonsterTraitCategory.Mobility, MonsterRarity.Epic, "chaser", weight: 0.9f),
            new MonsterTraitDef("firetrail", "Огненный след", "OS", "При активном перемещении оставляет короткоживущие опасные зоны.", MonsterTraitCategory.Mobility, MonsterRarity.Epic, "hazard", weight: 0.8f),
            new MonsterTraitDef("unstable", "Нестабильный", "NS", "Через 2 секунды после смерти взрывается в небольшом радиусе.", MonsterTraitCategory.Offense, MonsterRarity.Epic, "death", weight: 0.8f),

            new MonsterTraitDef("executioner", "Палач", "PA", "Наносит +30% урона игрокам ниже 30% здоровья.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, "tempo", weight: 0.8f),
            new MonsterTraitDef("counterstrike", "Контрудар", "KO", "После 5 полученных ударов следующая атака наносит +45% урона.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, "tempo", weight: 0.8f),
            new MonsterTraitDef("vampiric", "Вампир", "VM", "Лечится от реально нанесённого игроку урона.", MonsterTraitCategory.Sustain, MonsterRarity.Legendary, "sustain", weight: 0.75f),
            new MonsterTraitDef("devourer", "Пожиратель", "PV", "Лечится на 8% при смерти другого монстра рядом.", MonsterTraitCategory.Sustain, MonsterRarity.Legendary, "sustain", weight: 0.7f),
            new MonsterTraitDef("adaptive", "Адаптивный", "AD", "После удара тяжелее 12% его HP на 3 секунды получает 25% снижения урона.", MonsterTraitCategory.Defense, MonsterRarity.Legendary, "defense", weight: 0.75f),
            new MonsterTraitDef("laststand", "Последний рубеж", "LR", "Один раз ниже 30% HP получает барьер в 22% максимального здоровья.", MonsterTraitCategory.Defense, MonsterRarity.Legendary, "defense", weight: 0.75f),
            new MonsterTraitDef("phase", "Фазовый", "FZ", "Периодически входит в короткую защищённую фазу; между фазами слегка уязвимее.", MonsterTraitCategory.Defense, MonsterRarity.Legendary, "defense", weight: 0.65f),
            new MonsterTraitDef("teleporter", "Телепортер", "TP", "Если держать большую дистанцию, периодически скачет ближе к цели.", MonsterTraitCategory.Mobility, MonsterRarity.Legendary, "chaser", weight: 0.65f),
            new MonsterTraitDef("hunter", "Охотник", "OH", "Пока его цель далеко, ускоряется; вблизи бонус пропадает.", MonsterTraitCategory.Mobility, MonsterRarity.Legendary, "chaser", weight: 0.8f),
            new MonsterTraitDef("repulsor", "Отталкивающий", "OT", "Периодически выпускает короткий силовой импульс вокруг себя.", MonsterTraitCategory.Aura, MonsterRarity.Legendary, "hazard", weight: 0.7f),
            new MonsterTraitDef("toxicblood", "Ядовитая кровь", "YK", "При получении урона иногда оставляет под собой короткую опасную лужу.", MonsterTraitCategory.Sustain, MonsterRarity.Legendary, "hazard", weight: 0.7f),
            new MonsterTraitDef("linked", "Связанные", "SV", "Если рядом есть другой особый враг со Связью, оба получают 20% снижения урона.", MonsterTraitCategory.Defense, MonsterRarity.Legendary, "support", weight: 0.6f),
            new MonsterTraitDef("cursed", "Проклятый", "PR", "Попадание проклинает игрока на 5 секунд: он получает на 10% больше урона.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, "debuff", weight: 0.7f),
            new MonsterTraitDef("shredder", "Разрушитель", "RS", "Попадания на 5 секунд снижают броню игрока; до 3 стаков.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, "debuff", weight: 0.7f),

            new MonsterTraitDef("gravity", "Гравитационный", "GV", "Создаёт локальное поле, заметно замедляющее игроков рядом.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, "hazard", weight: 0.6f),
            new MonsterTraitDef("storm", "Грозовой", "GR", "Периодически отмечает позицию игрока и через 1 секунду поражает её разрядом.", MonsterTraitCategory.Offense, MonsterRarity.Mythic, "hazard", weight: 0.6f),
            new MonsterTraitDef("mortar", "Мортирный", "MT", "По далёкой цели запускает медленный большой удар по её текущей позиции.", MonsterTraitCategory.Offense, MonsterRarity.Mythic, "hazard", weight: 0.55f),
            new MonsterTraitDef("painring", "Кольцо боли", "KR", "Периодически поражает кольцо вокруг себя: безопасно вплотную или далеко.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, "hazard", weight: 0.55f),
            new MonsterTraitDef("pulse", "Импульсный", "IM", "Раз в несколько секунд выпускает круговой импульс урона вокруг себя.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, "hazard", weight: 0.6f),
            new MonsterTraitDef("commander", "Командир", "CM", "Пока жив, ближайшие монстры наносят больше урона.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, "support", weight: 0.6f),
            new MonsterTraitDef("protector", "Защитник", "ZS", "Пока жив, ближайшие монстры получают на 18% меньше урона.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, "support", weight: 0.55f),
            new MonsterTraitDef("medic", "Лекарь", "MD", "Раз в 8 секунд лечит наиболее раненого особого монстра рядом.", MonsterTraitCategory.Sustain, MonsterRarity.Mythic, "support", weight: 0.55f),
            new MonsterTraitDef("standard", "Знаменосец", "ZN", "Создаёт зону боевого темпа: союзники рядом быстрее атакуют и двигаются.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, "support", weight: 0.55f),

            // Major traits: one per Ancient+ enemy.
            new MonsterTraitDef("double_phase", "Двойная фаза", "2F", "На 50% HP один раз получает большой барьер и переходит в более быструю вторую фазу.", MonsterTraitCategory.Major, MonsterRarity.Ancient, "major", true, 1.0f),
            new MonsterTraitDef("blood_moon", "Кровавая луна", "KM", "Ниже 60% HP усиливает атаки и резко повышает лечение от нанесённого урона.", MonsterTraitCategory.Major, MonsterRarity.Ancient, "major", true, 0.9f),
            new MonsterTraitDef("echo_core", "Эхо", "EH", "Его атака повторяет 45% нанесённого урона через 0.8 секунды.", MonsterTraitCategory.Major, MonsterRarity.Ancient, "major", true, 0.9f),
            new MonsterTraitDef("paradox", "Парадокс", "PX", "Чередует 3 секунды сильной защиты и 3 секунды повышенной уязвимости.", MonsterTraitCategory.Major, MonsterRarity.Ancient, "major", true, 0.8f),
            new MonsterTraitDef("soul_collector", "Собиратель душ", "SD", "Смерть врагов рядом лечит его, даёт барьер и накапливает до 5 зарядов силы.", MonsterTraitCategory.Major, MonsterRarity.Ascended, "major", true, 0.8f),
            new MonsterTraitDef("void_hunter", "Охотник Бездны", "OB", "При дальней дистанции телепортируется ближе, но после скачка на 2 секунды становится уязвимее.", MonsterTraitCategory.Major, MonsterRarity.Ascended, "major", true, 0.8f),
            new MonsterTraitDef("singularity_core", "Сингулярность", "SG", "Создаёт сильное поле замедления и периодические импульсы вокруг себя.", MonsterTraitCategory.Major, MonsterRarity.Flawless, "major", true, 0.7f),
            new MonsterTraitDef("rift_core", "Разлом", "RZ", "Периодически открывает несколько кратких опасных зон в позиции игрока.", MonsterTraitCategory.Major, MonsterRarity.Primordial, "major", true, 0.7f),
            new MonsterTraitDef("warlord_core", "Полководец", "PL", "Сильно усиливает ближайших монстров и заставляет его убивать в приоритете.", MonsterTraitCategory.Major, MonsterRarity.Primordial, "major", true, 0.7f),
            new MonsterTraitDef("cataclysm", "Катаклизм", "KT", "По циклу применяет разряд, кольцо или силовой импульс с большими паузами между ними.", MonsterTraitCategory.Major, MonsterRarity.Divine, "major", true, 0.6f)
        };

        private static readonly Dictionary<string, MonsterTraitDef> ById = All.ToDictionary(x => x.Id, x => x, StringComparer.OrdinalIgnoreCase);
        private static readonly HashSet<MonsterRarityMarker> ActiveMarkers = new HashSet<MonsterRarityMarker>();
        private static readonly Dictionary<string, int> GroupCaps = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase)
        {
            { "chaser", 1 }, { "defense", 2 }, { "hazard", 2 }, { "support", 2 },
            { "sustain", 2 }, { "tempo", 2 }, { "debuff", 1 }, { "death", 1 }
        };

        public static void Install()
        {
            On.RoR2.CharacterBody.RecalculateStats += CharacterBody_RecalculateStats;
            On.RoR2.HealthComponent.TakeDamageProcess += HealthComponent_TakeDamageProcess;
            GlobalEventManager.onCharacterDeathGlobal += OnCharacterDeath;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterBody.RecalculateStats -= CharacterBody_RecalculateStats;
            On.RoR2.HealthComponent.TakeDamageProcess -= HealthComponent_TakeDamageProcess;
            GlobalEventManager.onCharacterDeathGlobal -= OnCharacterDeath;
            ActiveMarkers.Clear();
        }

        public static MonsterTraitDef Find(string id) => !string.IsNullOrEmpty(id) && ById.TryGetValue(id, out var def) ? def : null;

        public static IReadOnlyList<MonsterRarityMarker> GetActiveMarkers()
        {
            ActiveMarkers.RemoveWhere(x => x == null || x.gameObject == null);
            return ActiveMarkers.ToList();
        }

        public static bool Has(MonsterRarityMarker marker, string id)
        {
            return marker != null && marker.Traits != null && marker.Traits.Contains(id);
        }

        public static void AssignTraits(CharacterBody body, MonsterRarityMarker marker)
        {
            if (!NetworkServer.active || body == null || marker == null || marker.Rarity < MonsterRarity.Epic) return;
            if (marker.Traits == null) marker.Traits = new List<string>();
            if (marker.Traits.Count > 0) return;

            var regularCount = RegularTraitCount(marker.Rarity);
            for (var i = 0; i < regularCount; i++)
            {
                var picked = PickTrait(marker.Rarity, false, marker.Traits);
                if (picked == null) break;
                marker.Traits.Add(picked.Id);
            }

            if (marker.Rarity >= MonsterRarity.Ancient)
            {
                var major = PickTrait(marker.Rarity, true, marker.Traits);
                if (major != null) marker.Traits.Add(major.Id);
            }

            ActiveMarkers.Add(marker);
            var runtime = body.GetComponent<MonsterTraitRuntime>() ?? body.gameObject.AddComponent<MonsterTraitRuntime>();
            runtime.Initialize(body, marker);
        }

        private static int RegularTraitCount(MonsterRarity rarity)
        {
            if (rarity == MonsterRarity.Epic) return 1;
            if (rarity == MonsterRarity.Legendary) return 2;
            if (rarity == MonsterRarity.Mythic) return 3;
            if (rarity >= MonsterRarity.Flawless) return 4;
            if (rarity >= MonsterRarity.Ancient) return 3;
            return 0;
        }

        private static MonsterTraitDef PickTrait(MonsterRarity rarity, bool major, List<string> already)
        {
            var available = All.Where(x => x.Major == major && rarity >= x.MinRarity &&
                (already == null || !already.Contains(x.Id)) && CanAdd(x, already)).ToList();
            if (available.Count == 0) return null;
            var total = available.Sum(x => x.Weight);
            var roll = UnityEngine.Random.value * total;
            foreach (var def in available)
            {
                roll -= def.Weight;
                if (roll <= 0f) return def;
            }
            return available[available.Count - 1];
        }

        private static bool CanAdd(MonsterTraitDef candidate, List<string> already)
        {
            if (candidate == null || candidate.Major || string.IsNullOrEmpty(candidate.Group) || already == null) return true;
            if (!GroupCaps.TryGetValue(candidate.Group, out var cap)) return true;
            var count = 0;
            foreach (var id in already)
            {
                var def = Find(id);
                if (def != null && string.Equals(def.Group, candidate.Group, StringComparison.OrdinalIgnoreCase)) count++;
            }
            return count < cap;
        }

        private static void CharacterBody_RecalculateStats(On.RoR2.CharacterBody.orig_RecalculateStats orig, CharacterBody self)
        {
            orig(self);
            if (self == null) return;

            var marker = self.GetComponent<MonsterRarityMarker>();
            var runtime = self.GetComponent<MonsterTraitRuntime>();
            if (marker != null && runtime != null)
            {
                if (runtime.HunterActive) self.moveSpeed *= 1.22f;
                if (runtime.AvengerActive) { self.damage *= 1.20f; self.attackSpeed *= 1.18f; }
                if (runtime.PhaseTwo) { self.attackSpeed *= 1.18f; self.moveSpeed *= 1.10f; }
                if (runtime.SoulStacks > 0) self.damage *= 1f + runtime.SoulStacks * 0.05f;
                if (Has(marker, "blood_moon") && self.healthComponent != null && self.healthComponent.combinedHealthFraction < 0.60f)
                    self.damage *= 1.18f;
            }

            var debuff = self.GetComponent<MonsterTraitPlayerDebuff>();
            if (debuff != null && debuff.ArmorShredUntil > Time.fixedTime && debuff.ArmorShredStacks > 0)
                self.armor -= debuff.ArmorShredStacks * 8f;

            if (self.teamComponent != null && self.teamComponent.teamIndex == TeamIndex.Player)
                ApplyPlayerAuras(self);
            else if (self.teamComponent != null && self.teamComponent.teamIndex == TeamIndex.Monster)
                ApplyMonsterSupport(self, marker);
        }

        private static void ApplyPlayerAuras(CharacterBody player)
        {
            var gravity = false;
            var singularity = false;
            foreach (var marker in GetActiveMarkers())
            {
                var enemy = marker != null ? marker.GetComponent<CharacterBody>() : null;
                if (enemy == null || enemy.healthComponent == null || !enemy.healthComponent.alive) continue;
                var sqr = (enemy.corePosition - player.corePosition).sqrMagnitude;
                if (sqr <= 18f * 18f && Has(marker, "gravity")) gravity = true;
                if (sqr <= 24f * 24f && Has(marker, "singularity_core")) singularity = true;
            }
            if (gravity) player.moveSpeed *= 0.86f;
            if (singularity) player.moveSpeed *= 0.70f;
        }

        private static void ApplyMonsterSupport(CharacterBody monster, MonsterRarityMarker selfMarker)
        {
            var commander = false;
            var standard = false;
            var warlord = false;
            foreach (var marker in GetActiveMarkers())
            {
                if (marker == null || marker == selfMarker) continue;
                var source = marker.GetComponent<CharacterBody>();
                if (source == null || source.healthComponent == null || !source.healthComponent.alive) continue;
                if ((source.corePosition - monster.corePosition).sqrMagnitude > 25f * 25f) continue;
                commander |= Has(marker, "commander");
                standard |= Has(marker, "standard");
                warlord |= Has(marker, "warlord_core");
            }
            if (commander) monster.damage *= 1.10f;
            if (standard) { monster.attackSpeed *= 1.10f; monster.moveSpeed *= 1.08f; }
            if (warlord) { monster.damage *= 1.15f; monster.attackSpeed *= 1.12f; monster.moveSpeed *= 1.08f; }
        }

        private static void HealthComponent_TakeDamageProcess(On.RoR2.HealthComponent.orig_TakeDamageProcess orig, HealthComponent self, DamageInfo damageInfo)
        {
            var victimBody = self != null ? self.body : null;
            var victimMarker = victimBody != null ? victimBody.GetComponent<MonsterRarityMarker>() : null;
            var victimRuntime = victimBody != null ? victimBody.GetComponent<MonsterTraitRuntime>() : null;
            var attackerBody = damageInfo.attacker ? damageInfo.attacker.GetComponent<CharacterBody>() : null;
            var attackerMarker = attackerBody != null ? attackerBody.GetComponent<MonsterRarityMarker>() : null;
            var attackerRuntime = attackerBody != null ? attackerBody.GetComponent<MonsterTraitRuntime>() : null;

            if (victimBody != null && victimBody.teamComponent != null && victimBody.teamComponent.teamIndex == TeamIndex.Player)
            {
                var debuff = victimBody.GetComponent<MonsterTraitPlayerDebuff>();
                if (debuff != null && debuff.CurseUntil > Time.fixedTime) damageInfo.damage *= 1.10f;
            }

            if (victimMarker != null)
            {
                if (Has(victimMarker, "frontal") && attackerBody != null)
                {
                    var dir = (attackerBody.corePosition - victimBody.corePosition).normalized;
                    var dot = Vector3.Dot(victimBody.transform.forward, dir);
                    if (dot > 0.20f) damageInfo.damage *= 0.65f;
                    else if (dot < -0.20f) damageInfo.damage *= 1.25f;
                }
                if (victimRuntime != null)
                {
                    if (victimRuntime.AdaptiveActive) damageInfo.damage *= 0.75f;
                    if (victimRuntime.PhaseActive) damageInfo.damage *= 0.48f;
                    else if (victimRuntime.PhaseExposed) damageInfo.damage *= 1.12f;
                    if (victimRuntime.ParadoxProtected) damageInfo.damage *= 0.52f;
                    else if (victimRuntime.ParadoxExposed) damageInfo.damage *= 1.25f;
                    if (victimRuntime.VoidHunterVulnerable) damageInfo.damage *= 1.30f;
                    if (victimRuntime.DuelistExposed) damageInfo.damage *= 1.25f;
                }
                if (HasNearbyTrait(victimBody, "linked", 20f, victimMarker)) damageInfo.damage *= 0.80f;
            }

            if (victimBody != null && victimBody.teamComponent != null && victimBody.teamComponent.teamIndex == TeamIndex.Monster &&
                HasNearbyTrait(victimBody, "protector", 22f, victimMarker))
                damageInfo.damage *= 0.82f;

            if (attackerMarker != null && victimBody != null && victimBody.teamComponent != null && victimBody.teamComponent.teamIndex == TeamIndex.Player)
            {
                var victimFraction = victimBody.healthComponent != null ? victimBody.healthComponent.combinedHealthFraction : 1f;
                if (Has(attackerMarker, "executioner") && victimFraction < 0.30f) damageInfo.damage *= 1.30f;
                if (attackerRuntime != null)
                {
                    if (Has(attackerMarker, "ambusher") && attackerRuntime.AmbushReady) damageInfo.damage *= 1.35f;
                    if (Has(attackerMarker, "counterstrike") && attackerRuntime.CounterReady) damageInfo.damage *= 1.45f;
                    if (Has(attackerMarker, "blood_moon") && attackerBody.healthComponent != null && attackerBody.healthComponent.combinedHealthFraction < 0.60f)
                        damageInfo.damage *= 1.12f;
                    if (Has(attackerMarker, "echo_core") && !attackerRuntime.EchoFiring)
                        attackerRuntime.ScheduleEcho(victimBody, damageInfo.damage * 0.45f);
                }
            }

            var rawDamage = Mathf.Max(0f, damageInfo.damage);
            if (victimRuntime != null) victimRuntime.NotifyIncomingHit(rawDamage);
            if (attackerRuntime != null) attackerRuntime.NotifyOutgoingHit(victimBody);

            if (attackerMarker != null && victimBody != null && victimBody.teamComponent != null && victimBody.teamComponent.teamIndex == TeamIndex.Player)
            {
                var debuff = victimBody.GetComponent<MonsterTraitPlayerDebuff>() ?? victimBody.gameObject.AddComponent<MonsterTraitPlayerDebuff>();
                if (Has(attackerMarker, "cursed")) debuff.CurseUntil = Mathf.Max(debuff.CurseUntil, Time.fixedTime + 5f);
                if (Has(attackerMarker, "shredder")) debuff.AddArmorShred();
            }

            orig(self, damageInfo);

            if (attackerMarker != null && attackerBody != null && attackerBody.healthComponent != null && attackerBody.healthComponent.alive)
            {
                var healScale = 0f;
                if (Has(attackerMarker, "vampiric")) healScale += 0.06f;
                if (Has(attackerMarker, "blood_moon") && attackerBody.healthComponent.combinedHealthFraction < 0.60f) healScale += 0.10f;
                if (healScale > 0f && attackerBody.maxHealth > 0f)
                {
                    var fraction = Mathf.Clamp((rawDamage / attackerBody.maxHealth) * healScale, 0f, 0.035f);
                    if (fraction > 0f) attackerBody.healthComponent.HealFraction(fraction, default(ProcChainMask));
                }
            }
        }

        private static bool HasNearbyTrait(CharacterBody target, string trait, float radius, MonsterRarityMarker ignore)
        {
            if (target == null) return false;
            var r2 = radius * radius;
            foreach (var marker in GetActiveMarkers())
            {
                if (marker == null || marker == ignore || !Has(marker, trait)) continue;
                var source = marker.GetComponent<CharacterBody>();
                if (source == null || source.healthComponent == null || !source.healthComponent.alive) continue;
                if ((source.corePosition - target.corePosition).sqrMagnitude <= r2) return true;
            }
            return false;
        }

        private static void OnCharacterDeath(DamageReport report)
        {
            if (!NetworkServer.active || report?.victimBody == null) return;
            var dead = report.victimBody;
            var deadMarker = dead.GetComponent<MonsterRarityMarker>();

            if (deadMarker != null && Has(deadMarker, "unstable"))
            {
                var go = new GameObject("PetrichorLegacy_UnstableBlast");
                var delayed = go.AddComponent<MonsterTraitDelayedBlast>();
                delayed.Initialize(null, dead.corePosition, 2f, 7f, Mathf.Max(12f, dead.damage * 1.15f));
            }

            if (dead.teamComponent == null || dead.teamComponent.teamIndex != TeamIndex.Monster) return;
            foreach (var marker in GetActiveMarkers())
            {
                if (marker == null || marker == deadMarker) continue;
                var body = marker.GetComponent<CharacterBody>();
                var runtime = body != null ? body.GetComponent<MonsterTraitRuntime>() : null;
                if (body == null || runtime == null || body.healthComponent == null || !body.healthComponent.alive) continue;
                if ((body.corePosition - dead.corePosition).sqrMagnitude > 24f * 24f) continue;

                if (Has(marker, "avenger")) runtime.TriggerAvenger();
                if (Has(marker, "devourer")) body.healthComponent.HealFraction(0.08f, default(ProcChainMask));
                if (Has(marker, "soul_collector")) runtime.CollectSoul();
            }
        }

        internal static CharacterBody NearestPlayer(Vector3 from, float maxDistance = 999f)
        {
            CharacterBody best = null;
            var bestSqr = maxDistance * maxDistance;
            foreach (var pcmc in PlayerCharacterMasterController.instances)
            {
                var body = pcmc?.master?.GetBody();
                if (body == null || body.healthComponent == null || !body.healthComponent.alive) continue;
                var sqr = (body.corePosition - from).sqrMagnitude;
                if (sqr < bestSqr) { bestSqr = sqr; best = body; }
            }
            return best;
        }

        internal static void DamagePlayersInRadius(CharacterBody owner, Vector3 position, float radius, float damage, float innerSafeRadius = 0f)
        {
            if (!NetworkServer.active || damage <= 0f) return;
            var r2 = radius * radius;
            var inner2 = innerSafeRadius * innerSafeRadius;
            foreach (var pcmc in PlayerCharacterMasterController.instances)
            {
                var body = pcmc?.master?.GetBody();
                if (body == null || body.healthComponent == null || !body.healthComponent.alive) continue;
                var sqr = (body.corePosition - position).sqrMagnitude;
                if (sqr > r2 || sqr < inner2) continue;
                var info = new DamageInfo
                {
                    attacker = owner != null ? owner.gameObject : null,
                    inflictor = owner != null ? owner.gameObject : null,
                    damage = damage,
                    position = body.corePosition,
                    procCoefficient = 0f,
                    crit = false
                };
                body.healthComponent.TakeDamage(info);
            }
        }

        internal static void Register(MonsterRarityMarker marker)
        {
            if (marker != null) ActiveMarkers.Add(marker);
        }

        internal static void Unregister(MonsterRarityMarker marker)
        {
            if (marker != null) ActiveMarkers.Remove(marker);
        }

        internal static IEnumerable<MonsterRarityMarker> Active => GetActiveMarkers();
    }

    public sealed class MonsterTraitPlayerDebuff : MonoBehaviour
    {
        public float CurseUntil;
        public float ArmorShredUntil;
        public int ArmorShredStacks;

        public void AddArmorShred()
        {
            ArmorShredStacks = Mathf.Min(3, ArmorShredStacks + 1);
            ArmorShredUntil = Time.fixedTime + 5f;
            GetComponent<CharacterBody>()?.RecalculateStats();
        }

        private void Update()
        {
            if (ArmorShredStacks > 0 && Time.fixedTime > ArmorShredUntil)
            {
                ArmorShredStacks = 0;
                GetComponent<CharacterBody>()?.RecalculateStats();
            }
        }
    }

    public sealed class MonsterTraitRuntime : MonoBehaviour
    {
        private sealed class PendingBlast
        {
            public Vector3 Position;
            public float At;
            public float Radius;
            public float Damage;
            public float InnerSafe;
        }

        private sealed class Hazard
        {
            public Vector3 Position;
            public float Until;
            public float NextTick;
            public float Radius;
            public float Damage;
        }

        private sealed class EchoHit
        {
            public CharacterBody Target;
            public float At;
            public float Damage;
        }

        private CharacterBody _body;
        private MonsterRarityMarker _marker;
        private readonly List<PendingBlast> _blasts = new List<PendingBlast>();
        private readonly List<Hazard> _hazards = new List<Hazard>();
        private readonly List<EchoHit> _echoes = new List<EchoHit>();

        private float _lastIncomingHit = -100f;
        private float _lastOutgoingHit = -100f;
        private float _adaptiveUntil;
        private float _duelistExposedUntil;
        private float _avengerUntil;
        private float _voidHunterVulnerableUntil;
        private float _nextBarrier;
        private float _nextMovement;
        private float _nextHazard;
        private float _nextSupport;
        private float _nextRecalc;
        private float _nextToxic;
        private Vector3 _lastTrailPosition;
        private int _counterHits;
        private bool _counterReady;
        private bool _lastStandUsed;
        private bool _phaseTwo;
        private int _soulStacks;

        public bool EchoFiring { get; private set; }
        public bool AmbushReady => Time.fixedTime - _lastOutgoingHit >= 6f;
        public bool CounterReady => _counterReady;
        public bool DuelistExposed => Time.fixedTime < _duelistExposedUntil;
        public bool AdaptiveActive => Time.fixedTime < _adaptiveUntil;
        public bool AvengerActive => Time.fixedTime < _avengerUntil;
        public bool VoidHunterVulnerable => Time.fixedTime < _voidHunterVulnerableUntil;
        public bool HunterActive { get; private set; }
        public bool PhaseTwo => _phaseTwo;
        public int SoulStacks => _soulStacks;
        public bool PhaseActive => MonsterTraitSystem.Has(_marker, "phase") && Mathf.Repeat(Time.fixedTime, 8f) < 1.8f;
        public bool PhaseExposed => MonsterTraitSystem.Has(_marker, "phase") && !PhaseActive;
        public bool ParadoxProtected => MonsterTraitSystem.Has(_marker, "paradox") && Mathf.Repeat(Time.fixedTime, 6f) < 3f;
        public bool ParadoxExposed => MonsterTraitSystem.Has(_marker, "paradox") && !ParadoxProtected;

        public void Initialize(CharacterBody body, MonsterRarityMarker marker)
        {
            _body = body;
            _marker = marker;
            _nextBarrier = Time.fixedTime + UnityEngine.Random.Range(6f, 9f);
            _nextMovement = Time.fixedTime + UnityEngine.Random.Range(5f, 8f);
            _nextHazard = Time.fixedTime + UnityEngine.Random.Range(5f, 8f);
            _nextSupport = Time.fixedTime + UnityEngine.Random.Range(4f, 7f);
            _nextRecalc = Time.fixedTime + 0.5f;
            _lastTrailPosition = body != null ? body.corePosition : Vector3.zero;
            MonsterTraitSystem.Register(marker);
        }

        public void NotifyIncomingHit(float damage)
        {
            _lastIncomingHit = Time.fixedTime;
            if (_body == null || _marker == null) return;
            _counterHits++;
            if (MonsterTraitSystem.Has(_marker, "counterstrike") && _counterHits >= 5)
            {
                _counterHits = 0;
                _counterReady = true;
            }
            if (MonsterTraitSystem.Has(_marker, "adaptive") && damage >= _body.maxHealth * 0.12f)
                _adaptiveUntil = Time.fixedTime + 3f;
            if (MonsterTraitSystem.Has(_marker, "toxicblood") && Time.fixedTime >= _nextToxic)
            {
                AddHazard(_body.corePosition, 3.2f, 3.2f, Mathf.Max(4f, _body.damage * 0.18f));
                _nextToxic = Time.fixedTime + 5f;
            }
        }

        public void NotifyOutgoingHit(CharacterBody victim)
        {
            _lastOutgoingHit = Time.fixedTime;
            if (_marker == null) return;
            if (MonsterTraitSystem.Has(_marker, "duelist")) _duelistExposedUntil = Time.fixedTime + 2f;
            if (_counterReady) _counterReady = false;
        }

        public void TriggerAvenger()
        {
            _avengerUntil = Mathf.Max(_avengerUntil, Time.fixedTime + 8f);
            _body?.RecalculateStats();
        }

        public void CollectSoul()
        {
            if (_body == null || _body.healthComponent == null) return;
            _soulStacks = Mathf.Min(5, _soulStacks + 1);
            _body.healthComponent.HealFraction(0.06f, default(ProcChainMask));
            _body.healthComponent.AddBarrier(_body.maxHealth * 0.05f);
            _body.RecalculateStats();
        }

        public void ScheduleEcho(CharacterBody victim, float damage)
        {
            if (victim == null || damage <= 0f) return;
            _echoes.Add(new EchoHit { Target = victim, At = Time.fixedTime + 0.8f, Damage = damage });
        }

        private void Update()
        {
            if (!NetworkServer.active || _body == null || _marker == null || _body.healthComponent == null || !_body.healthComponent.alive) return;

            var now = Time.fixedTime;
            var nearest = MonsterTraitSystem.NearestPlayer(_body.corePosition);
            var distance = nearest != null ? Vector3.Distance(nearest.corePosition, _body.corePosition) : 0f;
            HunterActive = nearest != null && MonsterTraitSystem.Has(_marker, "hunter") && distance > 16f;

            if (MonsterTraitSystem.Has(_marker, "regenerator") && now - _lastIncomingHit > 4f)
                _body.healthComponent.HealFraction(0.006f * Time.deltaTime, default(ProcChainMask));

            if (!_lastStandUsed && MonsterTraitSystem.Has(_marker, "laststand") && _body.healthComponent.combinedHealthFraction < 0.30f)
            {
                _lastStandUsed = true;
                _body.healthComponent.AddBarrier(_body.maxHealth * 0.22f);
            }

            if (!_phaseTwo && MonsterTraitSystem.Has(_marker, "double_phase") && _body.healthComponent.combinedHealthFraction < 0.50f)
            {
                _phaseTwo = true;
                _body.healthComponent.AddBarrier(_body.maxHealth * 0.28f);
                _body.RecalculateStats();
            }

            if (now >= _nextBarrier && MonsterTraitSystem.Has(_marker, "barrierforge"))
            {
                _body.healthComponent.AddBarrier(_body.maxHealth * 0.08f);
                _nextBarrier = now + 10f;
            }

            if (now >= _nextMovement && nearest != null)
            {
                if ((MonsterTraitSystem.Has(_marker, "teleporter") || MonsterTraitSystem.Has(_marker, "void_hunter")) && distance > 22f)
                {
                    var dir = (_body.corePosition - nearest.corePosition);
                    if (dir.sqrMagnitude < 0.01f) dir = Vector3.forward;
                    dir.y = 0f;
                    dir.Normalize();
                    _body.transform.position = nearest.corePosition + dir * 7f + Vector3.up * 0.2f;
                    if (MonsterTraitSystem.Has(_marker, "void_hunter")) _voidHunterVulnerableUntil = now + 2f;
                    _nextMovement = now + (MonsterTraitSystem.Has(_marker, "void_hunter") ? 7f : 10f);
                }
                else if (MonsterTraitSystem.Has(_marker, "dasher") && distance > 12f)
                {
                    var dir = (nearest.corePosition - _body.corePosition);
                    dir.y = 0f;
                    if (dir.sqrMagnitude > 0.01f)
                    {
                        dir.Normalize();
                        _body.transform.position += dir * Mathf.Min(6f, Mathf.Max(2f, distance - 7f));
                    }
                    _nextMovement = now + 6f;
                }
                else _nextMovement = now + 3f;
            }

            if (MonsterTraitSystem.Has(_marker, "firetrail") && now >= _nextHazard)
            {
                if ((_body.corePosition - _lastTrailPosition).sqrMagnitude > 3.5f * 3.5f)
                {
                    AddHazard(_lastTrailPosition, 3f, 3f, Mathf.Max(3f, _body.damage * 0.14f));
                    _lastTrailPosition = _body.corePosition;
                }
                _nextHazard = now + 1.2f;
            }

            if (now >= _nextHazard)
            {
                if (MonsterTraitSystem.Has(_marker, "storm") && nearest != null)
                {
                    ScheduleBlast(nearest.corePosition, 1.0f, 5f, _body.damage * 0.65f);
                    _nextHazard = now + 8f;
                }
                else if (MonsterTraitSystem.Has(_marker, "mortar") && nearest != null && distance > 15f)
                {
                    ScheduleBlast(nearest.corePosition, 1.6f, 7f, _body.damage * 0.85f);
                    _nextHazard = now + 11f;
                }
                else if (MonsterTraitSystem.Has(_marker, "painring"))
                {
                    ScheduleBlast(_body.corePosition, 0.8f, 12f, _body.damage * 0.45f, 5f);
                    _nextHazard = now + 10f;
                }
                else if (MonsterTraitSystem.Has(_marker, "pulse"))
                {
                    ScheduleBlast(_body.corePosition, 0.6f, 8f, _body.damage * 0.40f);
                    _nextHazard = now + 9f;
                }
                else if (MonsterTraitSystem.Has(_marker, "repulsor"))
                {
                    ScheduleBlast(_body.corePosition, 0.45f, 7f, _body.damage * 0.28f);
                    _nextHazard = now + 8f;
                }
                else if (MonsterTraitSystem.Has(_marker, "rift_core") && nearest != null)
                {
                    ScheduleBlast(nearest.corePosition, 1.1f, 4.5f, _body.damage * 0.50f);
                    ScheduleBlast(nearest.corePosition + Vector3.right * 5f, 1.4f, 4.5f, _body.damage * 0.50f);
                    ScheduleBlast(nearest.corePosition + Vector3.forward * 5f, 1.7f, 4.5f, _body.damage * 0.50f);
                    _nextHazard = now + 10f;
                }
                else if (MonsterTraitSystem.Has(_marker, "cataclysm") && nearest != null)
                {
                    var mode = UnityEngine.Random.Range(0, 3);
                    if (mode == 0) ScheduleBlast(nearest.corePosition, 1.0f, 6f, _body.damage * 0.75f);
                    else if (mode == 1) ScheduleBlast(_body.corePosition, 1.0f, 13f, _body.damage * 0.55f, 5f);
                    else ScheduleBlast(_body.corePosition, 0.8f, 9f, _body.damage * 0.50f);
                    _nextHazard = now + 12f;
                }
                else if (MonsterTraitSystem.Has(_marker, "singularity_core"))
                {
                    ScheduleBlast(_body.corePosition, 0.8f, 10f, _body.damage * 0.42f);
                    _nextHazard = now + 9f;
                }
                else _nextHazard = now + 1.5f;
            }

            if (now >= _nextSupport)
            {
                if (MonsterTraitSystem.Has(_marker, "medic")) HealNearbySpecial();
                _nextSupport = now + 8f;
            }

            TickBlasts(now);
            TickHazards(now);
            TickEchoes(now);

            if (now >= _nextRecalc)
            {
                _body.RecalculateStats();
                _nextRecalc = now + 0.75f;
            }
        }

        private void HealNearbySpecial()
        {
            CharacterBody best = null;
            var bestFraction = 1f;
            foreach (var marker in MonsterTraitSystem.Active)
            {
                if (marker == null || marker == _marker) continue;
                var body = marker.GetComponent<CharacterBody>();
                if (body == null || body.healthComponent == null || !body.healthComponent.alive) continue;
                if ((body.corePosition - _body.corePosition).sqrMagnitude > 24f * 24f) continue;
                var f = body.healthComponent.combinedHealthFraction;
                if (f < bestFraction) { bestFraction = f; best = body; }
            }
            if (best != null) best.healthComponent.HealFraction(0.10f, default(ProcChainMask));
        }

        private void ScheduleBlast(Vector3 position, float delay, float radius, float damage, float innerSafe = 0f)
        {
            _blasts.Add(new PendingBlast { Position = position, At = Time.fixedTime + delay, Radius = radius, Damage = damage, InnerSafe = innerSafe });
        }

        private void AddHazard(Vector3 position, float duration, float radius, float damage)
        {
            _hazards.Add(new Hazard { Position = position, Until = Time.fixedTime + duration, NextTick = Time.fixedTime + 0.2f, Radius = radius, Damage = damage });
        }

        private void TickBlasts(float now)
        {
            for (var i = _blasts.Count - 1; i >= 0; i--)
            {
                var blast = _blasts[i];
                if (now < blast.At) continue;
                MonsterTraitSystem.DamagePlayersInRadius(_body, blast.Position, blast.Radius, blast.Damage, blast.InnerSafe);
                _blasts.RemoveAt(i);
            }
        }

        private void TickHazards(float now)
        {
            for (var i = _hazards.Count - 1; i >= 0; i--)
            {
                var h = _hazards[i];
                if (now >= h.Until) { _hazards.RemoveAt(i); continue; }
                if (now >= h.NextTick)
                {
                    MonsterTraitSystem.DamagePlayersInRadius(_body, h.Position, h.Radius, h.Damage);
                    h.NextTick = now + 1f;
                }
            }
        }

        private void TickEchoes(float now)
        {
            for (var i = _echoes.Count - 1; i >= 0; i--)
            {
                var echo = _echoes[i];
                if (now < echo.At) continue;
                if (echo.Target != null && echo.Target.healthComponent != null && echo.Target.healthComponent.alive)
                {
                    EchoFiring = true;
                    var info = new DamageInfo
                    {
                        attacker = _body.gameObject,
                        inflictor = _body.gameObject,
                        damage = echo.Damage,
                        position = echo.Target.corePosition,
                        procCoefficient = 0f,
                        crit = false
                    };
                    echo.Target.healthComponent.TakeDamage(info);
                    EchoFiring = false;
                }
                _echoes.RemoveAt(i);
            }
        }

        private void OnDestroy()
        {
            MonsterTraitSystem.Unregister(_marker);
        }
    }

    public sealed class MonsterTraitDelayedBlast : MonoBehaviour
    {
        private CharacterBody _owner;
        private Vector3 _position;
        private float _at;
        private float _radius;
        private float _damage;

        public void Initialize(CharacterBody owner, Vector3 position, float delay, float radius, float damage)
        {
            _owner = owner;
            _position = position;
            _at = Time.fixedTime + delay;
            _radius = radius;
            _damage = damage;
        }

        private void Update()
        {
            if (!NetworkServer.active) { Destroy(gameObject); return; }
            if (Time.fixedTime < _at) return;
            MonsterTraitSystem.DamagePlayersInRadius(_owner, _position, _radius, _damage);
            Destroy(gameObject);
        }
    }
}
'''

(base / "Progression/MonsterTraitSystem.cs").write_text(monster_traits, encoding="utf-8")

# Version bump only; 0.6.0 patch already installs the system and overlay.
for rel in ["Plugin.cs", "manifest.json", "PetrichorLegacy.csproj"]:
    p = base / rel
    t = p.read_text(encoding="utf-8")
    t = t.replace("0.6.0", "0.6.1")
    if rel == "manifest.json":
        t = t.replace("39 gameplay affixes", "42 gameplay-first affixes with anti-frustration combination rules")
    p.write_text(t, encoding="utf-8")

print("Applied PetrichorLegacy 0.6.1 gameplay affix rework")

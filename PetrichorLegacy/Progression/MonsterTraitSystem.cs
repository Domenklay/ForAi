using System;
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

        public MonsterTraitDef(string id, string name, string code, string description,
            MonsterTraitCategory category, MonsterRarity minRarity, bool major = false, float weight = 1f)
        {
            Id = id;
            Name = name;
            Code = code;
            Description = description;
            Category = category;
            MinRarity = minRarity;
            Major = major;
            Weight = Mathf.Max(0.01f, weight);
        }
    }

    public static class MonsterTraitSystem
    {
        // 31 regular traits + 8 major traits. Regular traits start at Epic.
        public static readonly IReadOnlyList<MonsterTraitDef> All = new List<MonsterTraitDef>
        {
            new MonsterTraitDef("armored", "Бронированный", "AR", "+30 брони.", MonsterTraitCategory.Defense, MonsterRarity.Epic, weight: 1.1f),
            new MonsterTraitDef("colossus", "Колосс", "CL", "+45% здоровья, но -10% скорости движения.", MonsterTraitCategory.Defense, MonsterRarity.Epic, weight: 0.8f),
            new MonsterTraitDef("juggernaut", "Джаггернаут", "JG", "+25% здоровья и +20 брони, но -8% скорости.", MonsterTraitCategory.Defense, MonsterRarity.Legendary, weight: 0.8f),
            new MonsterTraitDef("berserker", "Берсерк", "BZ", "+25% урона и +15% скорости атаки, но -10 брони.", MonsterTraitCategory.Offense, MonsterRarity.Epic, weight: 1.0f),
            new MonsterTraitDef("frenzied", "Неистовый", "FR", "+28% скорости атаки.", MonsterTraitCategory.Offense, MonsterRarity.Epic, weight: 1.0f),
            new MonsterTraitDef("brutal", "Жестокий", "BT", "+30% урона.", MonsterTraitCategory.Offense, MonsterRarity.Epic, weight: 0.9f),
            new MonsterTraitDef("swift", "Стремительный", "SW", "+22% скорости движения.", MonsterTraitCategory.Mobility, MonsterRarity.Epic, weight: 1.0f),
            new MonsterTraitDef("skirmisher", "Застрельщик", "SK", "+12% скорости движения и атаки.", MonsterTraitCategory.Mobility, MonsterRarity.Epic, weight: 1.0f),
            new MonsterTraitDef("regenerator", "Регенератор", "RG", "Быстро восстанавливает здоровье вне мгновенного урона.", MonsterTraitCategory.Sustain, MonsterRarity.Epic, weight: 0.9f),
            new MonsterTraitDef("shielded", "Щитоносный", "SH", "+25% базового здоровья в виде щита.", MonsterTraitCategory.Defense, MonsterRarity.Epic, weight: 0.9f),
            new MonsterTraitDef("overcharged", "Перегруженный", "OC", "+15% щита и +12% скорости атаки.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, weight: 0.8f),
            new MonsterTraitDef("sniper", "Снайпер", "SN", "+40% урона, но -15% скорости атаки.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, weight: 0.7f),
            new MonsterTraitDef("ravager", "Разоритель", "RV", "+18% урона и +10% скорости движения.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, weight: 0.9f),
            new MonsterTraitDef("executioner", "Палач", "EX", "+25% урона по игрокам ниже 35% здоровья.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, weight: 0.8f),
            new MonsterTraitDef("opener", "Первый удар", "OP", "+25% урона по почти полностью здоровым игрокам.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, weight: 0.8f),
            new MonsterTraitDef("vampiric", "Вампирический", "VM", "Восстанавливает часть здоровья от нанесённого урона.", MonsterTraitCategory.Sustain, MonsterRarity.Legendary, weight: 0.7f),
            new MonsterTraitDef("hardened", "Закалённый", "HD", "Получает на 15% меньше прямого урона.", MonsterTraitCategory.Defense, MonsterRarity.Legendary, weight: 0.7f),
            new MonsterTraitDef("laststand", "Последний рубеж", "LS", "+40 брони ниже 30% здоровья.", MonsterTraitCategory.Defense, MonsterRarity.Legendary, weight: 0.8f),
            new MonsterTraitDef("enraged", "Разъярённый", "EN", "Ниже 50% здоровья получает +30% урона и +25% скорости атаки.", MonsterTraitCategory.Offense, MonsterRarity.Legendary, weight: 0.7f),
            new MonsterTraitDef("adrenaline", "Адреналиновый", "AD", "Ниже 50% здоровья получает +30% скорости движения.", MonsterTraitCategory.Mobility, MonsterRarity.Legendary, weight: 0.8f),
            new MonsterTraitDef("adaptive", "Адаптивный", "AP", "Получает до +45 брони по мере потери здоровья.", MonsterTraitCategory.Defense, MonsterRarity.Mythic, weight: 0.7f),
            new MonsterTraitDef("barrierforge", "Кузня барьера", "BF", "Периодически получает небольшой барьер.", MonsterTraitCategory.Sustain, MonsterRarity.Mythic, weight: 0.7f),
            new MonsterTraitDef("gravity", "Гравитационный", "GV", "Замедляет игроков рядом с собой.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.65f),
            new MonsterTraitDef("dread", "Аура ужаса", "DR", "Снижает скорость атаки игроков рядом.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.65f),
            new MonsterTraitDef("wither", "Иссушающий", "WT", "Снижает урон игроков рядом.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.6f),
            new MonsterTraitDef("corrosive", "Коррозийный", "CR", "Снижает броню игроков рядом.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.6f),
            new MonsterTraitDef("commander", "Командир", "CM", "Усиливает урон ближайших монстров.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.6f),
            new MonsterTraitDef("protector", "Защитник стаи", "PR", "Даёт броню ближайшим монстрам.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.6f),
            new MonsterTraitDef("wardrum", "Боевой ритм", "WD", "Ускоряет атаки ближайших монстров.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.6f),
            new MonsterTraitDef("packleader", "Вожак", "PL", "Ускоряет передвижение ближайших монстров.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.6f),
            new MonsterTraitDef("medic", "Полевой лекарь", "MD", "Усиливает регенерацию ближайших монстров.", MonsterTraitCategory.Aura, MonsterRarity.Mythic, weight: 0.55f),

            // Major traits are reserved for Ancient+ and are intentionally more identity-defining.
            new MonsterTraitDef("phase_shell", "Фазовая оболочка", "PH", "Раз в цикл на короткое время резко снижает входящий урон.", MonsterTraitCategory.Major, MonsterRarity.Ancient, true, 1f),
            new MonsterTraitDef("blood_moon", "Кровавая луна", "BM", "+15% урона и усиленное вампирическое восстановление.", MonsterTraitCategory.Major, MonsterRarity.Ancient, true, 0.9f),
            new MonsterTraitDef("unyielding", "Неумолимый", "UN", "Постоянно получает на 20% меньше прямого урона.", MonsterTraitCategory.Major, MonsterRarity.Ancient, true, 0.8f),
            new MonsterTraitDef("bastion_core", "Ядро бастиона", "BC", "Регулярно создаёт крупный барьер и получает дополнительную броню.", MonsterTraitCategory.Major, MonsterRarity.Ancient, true, 0.8f),
            new MonsterTraitDef("hunter_prime", "Высший охотник", "HP", "Быстрее двигается и сильнее добивает раненых игроков.", MonsterTraitCategory.Major, MonsterRarity.Ascended, true, 0.8f),
            new MonsterTraitDef("singularity_core", "Ядро сингулярности", "SG", "Создаёт сильное поле замедления вокруг себя.", MonsterTraitCategory.Major, MonsterRarity.Ascended, true, 0.7f),
            new MonsterTraitDef("warlord_core", "Полководец", "WL", "Сильно усиливает ближайших монстров и немного усиливает себя.", MonsterTraitCategory.Major, MonsterRarity.Primordial, true, 0.7f),
            new MonsterTraitDef("frenzy_core", "Ядро ярости", "FC", "Ниже половины здоровья входит в опасную финальную фазу.", MonsterTraitCategory.Major, MonsterRarity.Primordial, true, 0.7f)
        };

        private static readonly Dictionary<string, MonsterTraitDef> ById = All.ToDictionary(x => x.Id, x => x, StringComparer.OrdinalIgnoreCase);
        private static readonly HashSet<MonsterRarityMarker> ActiveMarkers = new HashSet<MonsterRarityMarker>();

        public static void Install()
        {
            On.RoR2.CharacterBody.RecalculateStats += CharacterBody_RecalculateStats;
            On.RoR2.HealthComponent.TakeDamageProcess += HealthComponent_TakeDamageProcess;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterBody.RecalculateStats -= CharacterBody_RecalculateStats;
            On.RoR2.HealthComponent.TakeDamageProcess -= HealthComponent_TakeDamageProcess;
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
            var available = All.Where(x => x.Major == major && rarity >= x.MinRarity && (already == null || !already.Contains(x.Id))).ToList();
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

        private static void CharacterBody_RecalculateStats(On.RoR2.CharacterBody.orig_RecalculateStats orig, CharacterBody self)
        {
            orig(self);
            if (self == null) return;

            var marker = self.GetComponent<MonsterRarityMarker>();
            if (marker != null && marker.Rarity != MonsterRarity.Common)
                ApplyOwnTraits(self, marker);

            if (self.teamComponent != null && self.teamComponent.teamIndex == TeamIndex.Player)
                ApplyPlayerAuras(self);
            else if (self.teamComponent != null && self.teamComponent.teamIndex == TeamIndex.Monster)
                ApplyMonsterAuras(self, marker);
        }

        private static void ApplyOwnTraits(CharacterBody body, MonsterRarityMarker marker)
        {
            if (Has(marker, "armored")) body.armor += 30f;
            if (Has(marker, "colossus")) { body.maxHealth *= 1.45f; body.moveSpeed *= 0.90f; }
            if (Has(marker, "juggernaut")) { body.maxHealth *= 1.25f; body.armor += 20f; body.moveSpeed *= 0.92f; }
            if (Has(marker, "berserker")) { body.damage *= 1.25f; body.attackSpeed *= 1.15f; body.armor -= 10f; }
            if (Has(marker, "frenzied")) body.attackSpeed *= 1.28f;
            if (Has(marker, "brutal")) body.damage *= 1.30f;
            if (Has(marker, "swift")) body.moveSpeed *= 1.22f;
            if (Has(marker, "skirmisher")) { body.moveSpeed *= 1.12f; body.attackSpeed *= 1.12f; }
            if (Has(marker, "regenerator")) body.regen += Mathf.Max(0.5f, body.maxHealth * 0.008f);
            if (Has(marker, "shielded")) body.maxShield += body.baseMaxHealth * 0.25f;
            if (Has(marker, "overcharged")) { body.maxShield += body.baseMaxHealth * 0.15f; body.attackSpeed *= 1.12f; }
            if (Has(marker, "sniper")) { body.damage *= 1.40f; body.attackSpeed *= 0.85f; }
            if (Has(marker, "ravager")) { body.damage *= 1.18f; body.moveSpeed *= 1.10f; }

            var hp = body.healthComponent != null ? body.healthComponent.combinedHealthFraction : 1f;
            if (Has(marker, "laststand") && hp < 0.30f) body.armor += 40f;
            if (Has(marker, "enraged") && hp < 0.50f) { body.damage *= 1.30f; body.attackSpeed *= 1.25f; }
            if (Has(marker, "adrenaline") && hp < 0.50f) body.moveSpeed *= 1.30f;
            if (Has(marker, "adaptive")) body.armor += Mathf.Clamp01(1f - hp) * 45f;

            if (Has(marker, "blood_moon")) body.damage *= 1.15f;
            if (Has(marker, "bastion_core")) body.armor += 25f;
            if (Has(marker, "hunter_prime")) body.moveSpeed *= 1.15f;
            if (Has(marker, "warlord_core")) { body.damage *= 1.08f; body.armor += 10f; }
            if (Has(marker, "frenzy_core") && hp < 0.50f)
            {
                body.damage *= 1.35f;
                body.attackSpeed *= 1.30f;
                body.moveSpeed *= 1.20f;
            }
        }

        private static void ApplyPlayerAuras(CharacterBody player)
        {
            var gravity = false;
            var dread = false;
            var wither = false;
            var corrosive = false;
            var singularity = false;

            foreach (var marker in GetActiveMarkers())
            {
                var enemy = marker != null ? marker.GetComponent<CharacterBody>() : null;
                if (enemy == null || enemy.healthComponent == null || !enemy.healthComponent.alive) continue;
                var sqr = (enemy.corePosition - player.corePosition).sqrMagnitude;
                if (sqr > 22f * 22f) continue;
                gravity |= Has(marker, "gravity");
                dread |= Has(marker, "dread");
                wither |= Has(marker, "wither");
                corrosive |= Has(marker, "corrosive");
                singularity |= Has(marker, "singularity_core");
            }

            // Each aura type applies at most once, so packs cannot create an unavoidable multiplicative collapse.
            if (gravity) player.moveSpeed *= 0.88f;
            if (dread) player.attackSpeed *= 0.88f;
            if (wither) player.damage *= 0.90f;
            if (corrosive) player.armor -= 15f;
            if (singularity) { player.moveSpeed *= 0.78f; player.attackSpeed *= 0.94f; }
        }

        private static void ApplyMonsterAuras(CharacterBody monster, MonsterRarityMarker selfMarker)
        {
            var commander = false;
            var protector = false;
            var wardrum = false;
            var packleader = false;
            var medic = false;
            var warlord = false;

            foreach (var marker in GetActiveMarkers())
            {
                if (marker == null || marker == selfMarker) continue;
                var source = marker.GetComponent<CharacterBody>();
                if (source == null || source.healthComponent == null || !source.healthComponent.alive) continue;
                if ((source.corePosition - monster.corePosition).sqrMagnitude > 25f * 25f) continue;
                commander |= Has(marker, "commander");
                protector |= Has(marker, "protector");
                wardrum |= Has(marker, "wardrum");
                packleader |= Has(marker, "packleader");
                medic |= Has(marker, "medic");
                warlord |= Has(marker, "warlord_core");
            }

            if (commander) monster.damage *= 1.10f;
            if (protector) monster.armor += 18f;
            if (wardrum) monster.attackSpeed *= 1.12f;
            if (packleader) monster.moveSpeed *= 1.12f;
            if (medic) monster.regen += Mathf.Max(0.25f, monster.maxHealth * 0.004f);
            if (warlord) { monster.damage *= 1.15f; monster.attackSpeed *= 1.10f; monster.armor += 15f; }
        }

        private static void HealthComponent_TakeDamageProcess(On.RoR2.HealthComponent.orig_TakeDamageProcess orig, HealthComponent self, DamageInfo damageInfo)
        {
            var victimBody = self != null ? self.body : null;
            var victimMarker = victimBody != null ? victimBody.GetComponent<MonsterRarityMarker>() : null;
            var attackerBody = damageInfo.attacker ? damageInfo.attacker.GetComponent<CharacterBody>() : null;
            var attackerMarker = attackerBody != null ? attackerBody.GetComponent<MonsterRarityMarker>() : null;

            if (victimMarker != null)
            {
                if (Has(victimMarker, "hardened")) damageInfo.damage *= 0.85f;
                if (Has(victimMarker, "unyielding")) damageInfo.damage *= 0.80f;
                var runtime = victimBody.GetComponent<MonsterTraitRuntime>();
                if (runtime != null && runtime.PhaseActive) damageInfo.damage *= 0.55f;
            }

            if (attackerMarker != null && victimBody != null && victimBody.teamComponent != null && victimBody.teamComponent.teamIndex == TeamIndex.Player)
            {
                var victimFraction = victimBody.healthComponent != null ? victimBody.healthComponent.combinedHealthFraction : 1f;
                if (Has(attackerMarker, "executioner") && victimFraction < 0.35f) damageInfo.damage *= 1.25f;
                if (Has(attackerMarker, "opener") && victimFraction > 0.85f) damageInfo.damage *= 1.25f;
                if (Has(attackerMarker, "blood_moon")) damageInfo.damage *= 1.12f;
                if (Has(attackerMarker, "hunter_prime") && victimFraction < 0.50f) damageInfo.damage *= 1.20f;
            }

            var dealt = Mathf.Max(0f, damageInfo.damage);
            orig(self, damageInfo);

            if (attackerMarker != null && attackerBody != null && attackerBody.healthComponent != null && attackerBody.healthComponent.alive)
            {
                var healScale = 0f;
                if (Has(attackerMarker, "vampiric")) healScale += 0.045f;
                if (Has(attackerMarker, "blood_moon")) healScale += 0.060f;
                if (healScale > 0f && attackerBody.maxHealth > 0f)
                {
                    var fraction = Mathf.Clamp((dealt / attackerBody.maxHealth) * healScale, 0.001f, 0.025f);
                    attackerBody.healthComponent.HealFraction(fraction, default(ProcChainMask));
                }
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
    }

    public sealed class MonsterTraitRuntime : MonoBehaviour
    {
        private CharacterBody _body;
        private MonsterRarityMarker _marker;
        private float _nextBarrier;
        private float _nextRecalc;

        public bool PhaseActive { get; private set; }

        public void Initialize(CharacterBody body, MonsterRarityMarker marker)
        {
            _body = body;
            _marker = marker;
            _nextBarrier = Time.fixedTime + UnityEngine.Random.Range(4f, 7f);
            _nextRecalc = Time.fixedTime + 0.5f;
            MonsterTraitSystem.Register(marker);
        }

        private void Update()
        {
            if (_body == null || _marker == null || _body.healthComponent == null || !_body.healthComponent.alive) return;

            PhaseActive = MonsterTraitSystem.Has(_marker, "phase_shell") && Mathf.Repeat(Time.fixedTime, 10f) < 2.0f;

            if (Time.fixedTime >= _nextBarrier)
            {
                var barrier = 0f;
                if (MonsterTraitSystem.Has(_marker, "barrierforge")) barrier += _body.maxHealth * 0.06f;
                if (MonsterTraitSystem.Has(_marker, "bastion_core")) barrier += _body.maxHealth * 0.12f;
                if (barrier > 0f) _body.healthComponent.AddBarrier(barrier);
                _nextBarrier = Time.fixedTime + (MonsterTraitSystem.Has(_marker, "bastion_core") ? 9f : 11f);
            }

            if (Time.fixedTime >= _nextRecalc)
            {
                _body.RecalculateStats();
                _nextRecalc = Time.fixedTime + 1.25f;
            }
        }

        private void OnDestroy()
        {
            MonsterTraitSystem.Unregister(_marker);
        }
    }
}

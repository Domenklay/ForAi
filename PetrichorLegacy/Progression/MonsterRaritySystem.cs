using System;
using System.Collections.Generic;
using PetrichorLegacy.Persistence;
using RoR2;
using UnityEngine;
using UnityEngine.Networking;

namespace PetrichorLegacy.Progression
{
    public enum MonsterRarity
    {
        Common = 0,
        Uncommon = 1,
        Rare = 2,
        Epic = 3,
        Legendary = 4,
        Mythic = 5,
        Ancient = 6,
        Ascended = 7,
        Flawless = 8,
        Primordial = 9,
        Divine = 10,
        Anomalous = 11,
        Transcendent = 12
    }

    public sealed class MonsterRarityMarker : MonoBehaviour
    {
        public MonsterRarity Rarity;
        public bool Rewarded;
        public int GrantedCombatItems;
    }

    internal sealed class MonsterRarityInfo
    {
        public readonly MonsterRarity Rarity;
        public readonly string DisplayName;
        public readonly string HexColor;
        public readonly int UnlockLevel;
        public readonly int BaseXp;
        public readonly float HealthMultiplier;
        public readonly float DamageMultiplier;
        public readonly float AttackSpeedMultiplier;
        public readonly float MoveSpeedMultiplier;
        public readonly float ArmorBonus;
        public readonly float ScaleMultiplier;
        public readonly float Weight;
        public readonly int ItemBudget;

        public MonsterRarityInfo(MonsterRarity rarity, string displayName, string hexColor, int unlockLevel,
            int baseXp, float healthMultiplier, float damageMultiplier, float attackSpeedMultiplier,
            float moveSpeedMultiplier, float armorBonus, float scaleMultiplier, float weight, int itemBudget)
        {
            Rarity = rarity;
            DisplayName = displayName;
            HexColor = hexColor;
            UnlockLevel = unlockLevel;
            BaseXp = baseXp;
            HealthMultiplier = healthMultiplier;
            DamageMultiplier = damageMultiplier;
            AttackSpeedMultiplier = attackSpeedMultiplier;
            MoveSpeedMultiplier = moveSpeedMultiplier;
            ArmorBonus = armorBonus;
            ScaleMultiplier = scaleMultiplier;
            Weight = weight;
            ItemBudget = itemBudget;
        }
    }

    internal sealed class SafeCombatItem
    {
        public readonly string InternalName;
        public readonly int MaxStacks;
        public readonly MonsterRarity MinRarity;

        public SafeCombatItem(string internalName, int maxStacks, MonsterRarity minRarity)
        {
            InternalName = internalName;
            MaxStacks = maxStacks;
            MinRarity = minRarity;
        }
    }

    public static class MonsterRaritySystem
    {
        private static readonly MonsterRarityInfo[] Tiers =
        {
            new MonsterRarityInfo(MonsterRarity.Uncommon, "НЕОБЫЧНЫЙ", "#72D572", 2, 25, 1.40f, 1.08f, 1.03f, 1.02f, 4f, 1.03f, 100f, 1),
            new MonsterRarityInfo(MonsterRarity.Rare, "РЕДКИЙ", "#55C8FF", 5, 70, 1.90f, 1.15f, 1.05f, 1.03f, 8f, 1.06f, 38f, 2),
            new MonsterRarityInfo(MonsterRarity.Epic, "ЭПИЧЕСКИЙ", "#B982FF", 10, 170, 2.80f, 1.25f, 1.08f, 1.05f, 14f, 1.09f, 16f, 3),
            new MonsterRarityInfo(MonsterRarity.Legendary, "ЛЕГЕНДАРНЫЙ", "#FF8A4C", 20, 450, 4.50f, 1.40f, 1.12f, 1.07f, 24f, 1.13f, 6f, 4),
            new MonsterRarityInfo(MonsterRarity.Mythic, "МИФИЧЕСКИЙ", "#FF4F8B", 35, 1100, 7.00f, 1.60f, 1.16f, 1.09f, 38f, 1.17f, 2.2f, 5),
            new MonsterRarityInfo(MonsterRarity.Ancient, "ДРЕВНИЙ", "#D9D7FF", 50, 2500, 11.0f, 1.85f, 1.20f, 1.11f, 55f, 1.21f, 0.8f, 6),
            new MonsterRarityInfo(MonsterRarity.Ascended, "ВОЗВЫШЕННЫЙ", "#FFFFFF", 75, 6000, 16.0f, 2.10f, 1.24f, 1.13f, 75f, 1.25f, 0.25f, 7),
            new MonsterRarityInfo(MonsterRarity.Flawless, "БЕЗУПРЕЧНЫЙ", "#F6E8A6", 100, 12000, 22.0f, 2.30f, 1.27f, 1.15f, 95f, 1.28f, 0.11f, 8),
            new MonsterRarityInfo(MonsterRarity.Primordial, "ПЕРВОЗДАННЫЙ", "#FFB35C", 150, 25000, 30.0f, 2.50f, 1.30f, 1.17f, 120f, 1.31f, 0.05f, 9),
            new MonsterRarityInfo(MonsterRarity.Divine, "БОЖЕСТВЕННЫЙ", "#FFF2B5", 200, 50000, 40.0f, 2.70f, 1.32f, 1.19f, 150f, 1.34f, 0.022f, 10),
            new MonsterRarityInfo(MonsterRarity.Anomalous, "АНОМАЛЬНЫЙ", "#80FFF1", 300, 100000, 55.0f, 2.90f, 1.34f, 1.21f, 190f, 1.37f, 0.009f, 12),
            new MonsterRarityInfo(MonsterRarity.Transcendent, "ТРАНСЦЕНДЕНТНЫЙ", "#FF80EE", 500, 200000, 75.0f, 3.10f, 1.36f, 1.23f, 240f, 1.40f, 0.003f, 14)
        };

        // Whitelist only. No rockets, bands, explosions, chain lightning, Tesla, Behemoth, Clover,
        // Dio, Void/Lunar/Hallowed, on-death nukes or other proc chains that can ruin a random run.
        private static readonly SafeCombatItem[] SafeItems =
        {
            new SafeCombatItem("Syringe", 3, MonsterRarity.Uncommon),
            new SafeCombatItem("Hoof", 3, MonsterRarity.Uncommon),
            new SafeCombatItem("PersonalShield", 2, MonsterRarity.Uncommon),
            new SafeCombatItem("ArmorPlate", 3, MonsterRarity.Uncommon),
            new SafeCombatItem("Medkit", 2, MonsterRarity.Rare),
            new SafeCombatItem("Mushroom", 2, MonsterRarity.Rare),
            new SafeCombatItem("Bear", 2, MonsterRarity.Rare),
            new SafeCombatItem("SprintBonus", 2, MonsterRarity.Rare),
            new SafeCombatItem("HealWhileSafe", 2, MonsterRarity.Epic),
            new SafeCombatItem("BarrierOnKill", 2, MonsterRarity.Epic),
            new SafeCombatItem("SprintArmor", 2, MonsterRarity.Epic),
            new SafeCombatItem("Seed", 2, MonsterRarity.Legendary),
            new SafeCombatItem("Infusion", 1, MonsterRarity.Legendary),
            new SafeCombatItem("Feather", 1, MonsterRarity.Legendary),
            new SafeCombatItem("SecondarySkillMagazine", 1, MonsterRarity.Mythic)
        };

        public static void Install()
        {
            On.RoR2.CharacterMaster.OnBodyStart += CharacterMaster_OnBodyStart;
            On.RoR2.CharacterBody.RecalculateStats += CharacterBody_RecalculateStats;
            On.RoR2.CharacterBody.GetDisplayName += CharacterBody_GetDisplayName;
            GlobalEventManager.onCharacterDeathGlobal += OnCharacterDeath;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterMaster.OnBodyStart -= CharacterMaster_OnBodyStart;
            On.RoR2.CharacterBody.RecalculateStats -= CharacterBody_RecalculateStats;
            On.RoR2.CharacterBody.GetDisplayName -= CharacterBody_GetDisplayName;
            GlobalEventManager.onCharacterDeathGlobal -= OnCharacterDeath;
        }

        private static void CharacterMaster_OnBodyStart(On.RoR2.CharacterMaster.orig_OnBodyStart orig, CharacterMaster self, CharacterBody body)
        {
            orig(self, body);
            TryAssignRarity(body);
        }

        private static void TryAssignRarity(CharacterBody body)
        {
            if (!NetworkServer.active || body == null || Run.instance == null) return;
            if (body.GetComponent<MonsterRarityMarker>() != null) return;
            if (body.teamComponent == null || body.teamComponent.teamIndex != TeamIndex.Monster) return;
            if (body.isPlayerControlled || body.isBoss || body.isElite) return;

            SaveService.RefreshProfile();
            var profile = SaveService.Current;
            if (profile == null || profile.level < 2) return;

            var rarity = RollRarity(profile.level);
            if (rarity == MonsterRarity.Common) return;
            var info = GetInfo(rarity);
            if (info == null) return;

            var marker = body.gameObject.AddComponent<MonsterRarityMarker>();
            marker.Rarity = rarity;
            marker.GrantedCombatItems = GrantSafeCombatItems(body.master?.inventory, rarity, info.ItemBudget);

            body.transform.localScale *= info.ScaleMultiplier;
            body.RecalculateStats();
            if (body.healthComponent != null)
                body.healthComponent.Networkhealth = body.healthComponent.fullHealth;

            if (rarity >= MonsterRarity.Epic)
                PetrichorLegacyPlugin.Log?.LogInfo($"Spawned {info.DisplayName} monster: {body.GetDisplayName()} with {marker.GrantedCombatItems} safe combat item stacks.");
        }

        private static int GrantSafeCombatItems(Inventory inventory, MonsterRarity rarity, int budget)
        {
            if (inventory == null || budget <= 0) return 0;
            var granted = 0;
            var stacks = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase);
            var attempts = 0;
            while (granted < budget && attempts++ < budget * 20)
            {
                var candidate = SafeItems[UnityEngine.Random.Range(0, SafeItems.Length)];
                if (rarity < candidate.MinRarity) continue;
                stacks.TryGetValue(candidate.InternalName, out var current);
                if (current >= candidate.MaxStacks) continue;
                var index = ItemCatalog.FindItemIndex(candidate.InternalName);
                if (index == ItemIndex.None) continue;

                inventory.GiveItemPermanent(index, 1);
                stacks[candidate.InternalName] = current + 1;
                granted++;
            }
            return granted;
        }

        private static MonsterRarity RollRarity(int metaLevel)
        {
            var stageBonus = Run.instance != null ? Mathf.Min(0.06f, Run.instance.stageClearCount * 0.005f) : 0f;
            var specialChance = Mathf.Clamp(0.025f + (metaLevel - 2) * 0.0016f + stageBonus, 0.025f, 0.35f);
            if (UnityEngine.Random.value > specialChance) return MonsterRarity.Common;

            var totalWeight = 0f;
            for (var i = 0; i < Tiers.Length; i++)
            {
                var info = Tiers[i];
                if (metaLevel >= info.UnlockLevel) totalWeight += EffectiveWeight(info, metaLevel);
            }
            if (totalWeight <= 0f) return MonsterRarity.Common;

            var roll = UnityEngine.Random.value * totalWeight;
            for (var i = Tiers.Length - 1; i >= 0; i--)
            {
                var info = Tiers[i];
                if (metaLevel < info.UnlockLevel) continue;
                var weight = EffectiveWeight(info, metaLevel);
                if (roll <= weight) return info.Rarity;
                roll -= weight;
            }
            return MonsterRarity.Uncommon;
        }

        private static float EffectiveWeight(MonsterRarityInfo info, int metaLevel)
        {
            var levelsPastUnlock = Mathf.Max(0, metaLevel - info.UnlockLevel);
            var growth = 1f + Mathf.Min(2.0f, levelsPastUnlock * 0.018f);
            return info.Weight * growth;
        }

        private static void CharacterBody_RecalculateStats(On.RoR2.CharacterBody.orig_RecalculateStats orig, CharacterBody self)
        {
            orig(self);
            if (self == null) return;
            var marker = self.GetComponent<MonsterRarityMarker>();
            if (marker == null || marker.Rarity == MonsterRarity.Common) return;
            var info = GetInfo(marker.Rarity);
            if (info == null) return;

            self.maxHealth *= info.HealthMultiplier;
            self.damage *= info.DamageMultiplier;
            self.attackSpeed *= info.AttackSpeedMultiplier;
            self.moveSpeed *= info.MoveSpeedMultiplier;
            self.armor += info.ArmorBonus;
        }

        private static string CharacterBody_GetDisplayName(On.RoR2.CharacterBody.orig_GetDisplayName orig, CharacterBody self)
        {
            var baseName = orig(self);
            if (self == null) return baseName;
            var marker = self.GetComponent<MonsterRarityMarker>();
            if (marker == null || marker.Rarity == MonsterRarity.Common) return baseName;
            var info = GetInfo(marker.Rarity);
            return info == null ? baseName : $"<color={info.HexColor}>{info.DisplayName}</color> {baseName}";
        }

        private static void OnCharacterDeath(DamageReport report)
        {
            if (!NetworkServer.active || report?.victimBody == null || report.attackerMaster == null) return;
            if (report.attackerMaster.playerCharacterMasterController == null) return;

            var marker = report.victimBody.GetComponent<MonsterRarityMarker>();
            if (marker == null || marker.Rarity == MonsterRarity.Common || marker.Rewarded) return;
            marker.Rewarded = true;
            var info = GetInfo(marker.Rarity);
            if (info == null || !SaveService.RefreshProfile() || SaveService.Current == null) return;

            var progress = ServerProgressionState.Get(report.attackerMaster);
            var stage = Run.instance?.stageClearCount ?? 0;
            var stageMultiplier = 1f + Mathf.Min(2f, stage * 0.12f);
            var difficultyMultiplier = 1f;
            if (Run.instance != null)
            {
                var diffDef = DifficultyCatalog.GetDifficultyDef(Run.instance.selectedDifficulty);
                if (diffDef != null) difficultyMultiplier = Mathf.Clamp(0.85f + diffDef.scalingValue * 0.15f, 0.9f, 2.0f);
            }

            var xpMultiplier = 1f;
            xpMultiplier += ServerProgressionState.Rank(report.attackerMaster, "hunter_specialxp") * 0.05f;
            xpMultiplier += ServerProgressionState.MasteryValue(report.attackerMaster, "mastery_seeker_specialxp");
            if (marker.Rarity >= MonsterRarity.Legendary && ServerProgressionState.Perfection(report.attackerMaster, "perfection_hunter") > 0)
                xpMultiplier += 0.10f;
            if (marker.Rarity >= MonsterRarity.Mythic && ServerProgressionState.Rank(report.attackerMaster, "hunter_greathunt") > 0 && progress != null && progress.LastGreatHuntStage != stage)
            {
                progress.LastGreatHuntStage = stage;
                xpMultiplier += 0.50f;
            }

            var xp = Mathf.Max(1, Mathf.RoundToInt(info.BaseXp * stageMultiplier * difficultyMultiplier * xpMultiplier));
            ProgressionService.AwardXp(SaveService.Current, xp, $"{info.DisplayName} монстр");

            var goldMultiplier = 1f;
            goldMultiplier += ServerProgressionState.Rank(report.attackerMaster, "hunter_specialgold") * 0.10f;
            goldMultiplier += ServerProgressionState.Rank(report.attackerMaster, "seeker_specialgold") * 0.10f;
            goldMultiplier += ServerProgressionState.Rank(report.attackerMaster, "merchant_specialgold") * 0.10f;
            goldMultiplier += ServerProgressionState.Rank(report.attackerMaster, "prospector_specialgold") * 0.10f;
            goldMultiplier += ServerProgressionState.MasteryValue(report.attackerMaster, "mastery_seeker_gold");
            if (marker.Rarity >= MonsterRarity.Legendary && ServerProgressionState.Rank(report.attackerMaster, "hunter_legend") > 0)
                goldMultiplier += 0.20f;
            var gold = Mathf.RoundToInt((10f + (int)marker.Rarity * 12f + stage * 5f) * goldMultiplier);
            if (gold > 0) report.attackerMaster.GiveMoney((uint)gold);

            if (progress != null)
            {
                if (marker.Rarity >= MonsterRarity.Epic && ServerProgressionState.Rank(report.attackerMaster, "hunter_haste") > 0)
                    progress.HunterHasteUntil = Time.fixedTime + 8f;
                if (ServerProgressionState.Perfection(report.attackerMaster, "perfection_pursuit") > 0)
                    progress.PursuitUntil = Time.fixedTime + 8f;

                if (marker.Rarity >= MonsterRarity.Legendary && ServerProgressionState.Rank(report.attackerMaster, "prospector_legendwhite") > 0 && !progress.ProspectorLegendWhiteGranted)
                {
                    progress.ProspectorLegendWhiteGranted = true;
                    TalentEffects.GrantRandomItem(report.attackerMaster, false);
                }
                if (marker.Rarity >= MonsterRarity.Mythic && ServerProgressionState.Rank(report.attackerMaster, "prospector_mythgreen") > 0 && !progress.ProspectorMythGreenGranted && UnityEngine.Random.value < 0.25f)
                {
                    progress.ProspectorMythGreenGranted = true;
                    TalentEffects.GrantRandomItem(report.attackerMaster, true);
                }
            }

            report.attackerMaster.GetBody()?.RecalculateStats();
            PetrichorLegacyPlugin.Log?.LogInfo($"Rarity reward: +{xp} XP, +{gold} gold for {info.DisplayName}; enemy combat items were not dropped.");
        }

        private static MonsterRarityInfo GetInfo(MonsterRarity rarity)
        {
            for (var i = 0; i < Tiers.Length; i++) if (Tiers[i].Rarity == rarity) return Tiers[i];
            return null;
        }
    }
}

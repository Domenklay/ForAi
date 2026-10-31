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
        Ascended = 7
    }

    public sealed class MonsterRarityMarker : MonoBehaviour
    {
        public MonsterRarity Rarity;
        public bool Rewarded;
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

        public MonsterRarityInfo(MonsterRarity rarity, string displayName, string hexColor, int unlockLevel,
            int baseXp, float healthMultiplier, float damageMultiplier, float attackSpeedMultiplier,
            float moveSpeedMultiplier, float armorBonus, float scaleMultiplier, float weight)
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
        }
    }

    public static class MonsterRaritySystem
    {
        private static readonly MonsterRarityInfo[] Tiers =
        {
            new MonsterRarityInfo(MonsterRarity.Uncommon, "НЕОБЫЧНЫЙ", "#72D572", 2,
                25, 1.50f, 1.15f, 1.05f, 1.02f, 5f, 1.04f, 100f),
            new MonsterRarityInfo(MonsterRarity.Rare, "РЕДКИЙ", "#55C8FF", 5,
                70, 2.20f, 1.35f, 1.08f, 1.04f, 10f, 1.08f, 38f),
            new MonsterRarityInfo(MonsterRarity.Epic, "ЭПИЧЕСКИЙ", "#B982FF", 10,
                170, 3.50f, 1.60f, 1.12f, 1.06f, 20f, 1.12f, 16f),
            new MonsterRarityInfo(MonsterRarity.Legendary, "ЛЕГЕНДАРНЫЙ", "#FF8A4C", 20,
                450, 6.00f, 2.00f, 1.18f, 1.08f, 35f, 1.18f, 6f),
            new MonsterRarityInfo(MonsterRarity.Mythic, "МИФИЧЕСКИЙ", "#FF4F8B", 35,
                1100, 10.0f, 2.60f, 1.25f, 1.12f, 60f, 1.24f, 2.2f),
            new MonsterRarityInfo(MonsterRarity.Ancient, "ДРЕВНИЙ", "#D9D7FF", 50,
                2500, 16.0f, 3.30f, 1.35f, 1.15f, 100f, 1.32f, 0.8f),
            new MonsterRarityInfo(MonsterRarity.Ascended, "ВОЗВЫШЕННЫЙ", "#FFFFFF", 75,
                6000, 25.0f, 4.50f, 1.45f, 1.20f, 150f, 1.40f, 0.25f)
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

            body.transform.localScale *= info.ScaleMultiplier;
            body.RecalculateStats();
            if (body.healthComponent != null)
                body.healthComponent.Networkhealth = body.healthComponent.fullHealth;

            if (rarity >= MonsterRarity.Epic)
                PetrichorLegacyPlugin.Log?.LogInfo($"Spawned {info.DisplayName} monster: {body.GetDisplayName()} (meta level {profile.level}).");
        }

        private static MonsterRarity RollRarity(int metaLevel)
        {
            var stageBonus = Run.instance != null ? Mathf.Min(0.05f, Run.instance.stageClearCount * 0.005f) : 0f;
            var specialChance = Mathf.Clamp(0.025f + (metaLevel - 2) * 0.0020f + stageBonus, 0.025f, 0.28f);
            if (UnityEngine.Random.value > specialChance)
                return MonsterRarity.Common;

            var totalWeight = 0f;
            for (var i = 0; i < Tiers.Length; i++)
            {
                var info = Tiers[i];
                if (metaLevel < info.UnlockLevel) continue;
                totalWeight += EffectiveWeight(info, metaLevel);
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
            var growth = 1f + Mathf.Min(2.5f, levelsPastUnlock * 0.025f);
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
            if (info == null) return baseName;
            return $"<color={info.HexColor}>{info.DisplayName}</color> {baseName}";
        }

        private static void OnCharacterDeath(DamageReport report)
        {
            if (!NetworkServer.active || report == null || report.victimBody == null) return;
            if (report.attackerMaster == null || report.attackerMaster.playerCharacterMasterController == null) return;

            var marker = report.victimBody.GetComponent<MonsterRarityMarker>();
            if (marker == null || marker.Rarity == MonsterRarity.Common || marker.Rewarded) return;
            marker.Rewarded = true;

            var info = GetInfo(marker.Rarity);
            if (info == null) return;
            if (!SaveService.RefreshProfile() || SaveService.Current == null) return;

            var stageMultiplier = 1f + Mathf.Min(2f, (Run.instance?.stageClearCount ?? 0) * 0.12f);
            var difficultyMultiplier = 1f;
            if (Run.instance != null)
            {
                var diffDef = DifficultyCatalog.GetDifficultyDef(Run.instance.selectedDifficulty);
                if (diffDef != null)
                    difficultyMultiplier = Mathf.Clamp(0.85f + diffDef.scalingValue * 0.15f, 0.9f, 2.0f);
            }

            var xp = Mathf.Max(1, Mathf.RoundToInt(info.BaseXp * stageMultiplier * difficultyMultiplier));
            ProgressionService.AwardXp(SaveService.Current, xp, $"{info.DisplayName} монстр");
            PetrichorLegacyPlugin.Log?.LogInfo($"Rarity XP: +{xp} for {info.DisplayName} monster.");
        }

        private static MonsterRarityInfo GetInfo(MonsterRarity rarity)
        {
            for (var i = 0; i < Tiers.Length; i++)
                if (Tiers[i].Rarity == rarity)
                    return Tiers[i];
            return null;
        }
    }
}

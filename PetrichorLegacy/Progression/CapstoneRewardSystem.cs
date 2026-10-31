using System;
using System.Collections.Generic;
using System.Linq;
using RoR2;
using UnityEngine.Networking;

namespace PetrichorLegacy.Progression
{
    public static class CapstoneRewardSystem
    {
        private sealed class RewardDef
        {
            public string TalentId;
            public string DisplayName;
            public string[] ItemCandidates;
        }

        private static readonly RewardDef[] ClassRewards =
        {
            new RewardDef { TalentId = "guardian_void_capstone", DisplayName = "Safer Spaces", ItemCandidates = new[] { "BearVoid" } },
            new RewardDef { TalentId = "slayer_void_capstone", DisplayName = "Needletick", ItemCandidates = new[] { "BleedOnHitVoid" } },
            new RewardDef { TalentId = "path_void_capstone", DisplayName = "Polylute", ItemCandidates = new[] { "ChainLightningVoid" } },
            new RewardDef { TalentId = "seeker_void_capstone", DisplayName = "Encrusted Key", ItemCandidates = new[] { "TreasureCacheVoid" } }
        };

        private static readonly RewardDef[] SpecRewards =
        {
            new RewardDef { TalentId = "bastion_legendary", DisplayName = "Defensive Microbots", ItemCandidates = new[] { "CaptainDefenseMatrix" } },
            new RewardDef { TalentId = "unbroken_legendary", DisplayName = "Rejuvenation Rack", ItemCandidates = new[] { "IncreaseHealing" } },
            new RewardDef { TalentId = "vanguard_legendary", DisplayName = "Shattering Justice", ItemCandidates = new[] { "ArmorReductionOnHit" } },

            new RewardDef { TalentId = "executioner_legendary", DisplayName = "Ceremonial Dagger", ItemCandidates = new[] { "Dagger" } },
            new RewardDef { TalentId = "hunter_legendary", DisplayName = "Wake of Vultures", ItemCandidates = new[] { "HeadHunter" } },
            new RewardDef { TalentId = "berserker_legendary", DisplayName = "Unstable Tesla Coil", ItemCandidates = new[] { "ShockNearby" } },

            new RewardDef { TalentId = "scout_legendary", DisplayName = "Alien Head", ItemCandidates = new[] { "AlienHead" } },
            new RewardDef { TalentId = "acro_legendary", DisplayName = "Hardlight Afterburner", ItemCandidates = new[] { "UtilitySkillMagazine" } },
            new RewardDef { TalentId = "saboteur_legendary", DisplayName = "Sentient Meat Hook", ItemCandidates = new[] { "BounceNearby" } },

            new RewardDef { TalentId = "merchant_legendary", DisplayName = "Spare Drone Parts", ItemCandidates = new[] { "DroneWeapons" } },
            new RewardDef { TalentId = "prospector_legendary", DisplayName = "57 Leaf Clover", ItemCandidates = new[] { "Clover" } },
            new RewardDef { TalentId = "relic_legendary", DisplayName = "Soulbound Catalyst", ItemCandidates = new[] { "Talisman" } }
        };

        private static readonly HashSet<string> MissingLogged = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        public static void Install()
        {
            On.RoR2.CharacterMaster.OnBodyStart += CharacterMaster_OnBodyStart;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterMaster.OnBodyStart -= CharacterMaster_OnBodyStart;
        }

        private static void CharacterMaster_OnBodyStart(On.RoR2.CharacterMaster.orig_OnBodyStart orig, CharacterMaster self, CharacterBody body)
        {
            orig(self, body);
            if (!NetworkServer.active || self == null || self.playerCharacterMasterController == null || self.inventory == null) return;
            if (ServerProgressionState.Get(self) == null) return;

            foreach (var reward in ClassRewards) GrantIfUnlocked(self, reward);
            foreach (var reward in SpecRewards) GrantIfUnlocked(self, reward);
        }

        private static void GrantIfUnlocked(CharacterMaster master, RewardDef reward)
        {
            if (master == null || reward == null || ServerProgressionState.Rank(master, reward.TalentId) <= 0) return;
            var item = ResolveItem(reward.ItemCandidates);
            if (item == null)
            {
                if (MissingLogged.Add(reward.TalentId))
                    PetrichorLegacyPlugin.Log?.LogWarning($"Capstone reward item not found for {reward.TalentId}: {reward.DisplayName}.");
                return;
            }
            if (master.inventory.GetItemCount(item) <= 0)
                master.inventory.GiveItem(item, 1);
        }

        private static ItemDef ResolveItem(IEnumerable<string> candidates)
        {
            if (candidates == null) return null;
            var defs = ItemCatalog.allItemDefs;
            if (defs == null) return null;

            foreach (var candidate in candidates.Where(x => !string.IsNullOrWhiteSpace(x)))
            {
                var exact = defs.FirstOrDefault(x => x != null && string.Equals(x.name, candidate, StringComparison.OrdinalIgnoreCase));
                if (exact != null) return exact;
            }
            foreach (var candidate in candidates.Where(x => !string.IsNullOrWhiteSpace(x)))
            {
                var partial = defs.FirstOrDefault(x => x != null && !string.IsNullOrEmpty(x.name) && x.name.IndexOf(candidate, StringComparison.OrdinalIgnoreCase) >= 0);
                if (partial != null) return partial;
            }
            return null;
        }
    }
}

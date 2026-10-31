using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using PetrichorLegacy.Loadout;
using PetrichorLegacy.Models;
using PetrichorLegacy.Persistence;
using PetrichorLegacy.Progression;
using RoR2;
using UnityEngine.Networking;

namespace PetrichorLegacy.Networking
{
    public static class ProgressionNetwork
    {
        public static void Register()
        {
            PetrichorLegacyPlugin.Log?.LogInfo("Standalone progression sync enabled (no R2API Networking dependency).");
        }

        public static IEnumerator SendLocalProgressWhenReady()
        {
            for (var i = 0; i < 600; i++)
            {
                SaveService.RefreshProfile();
                var local = LocalUserManager.GetFirstLocalUser();
                var master = local?.cachedMaster;
                if (master != null && master.inventory != null)
                {
                    if (!NetworkServer.active)
                    {
                        PetrichorLegacyPlugin.Log.LogWarning("Standalone build detected a multiplayer client. Meta bonuses are host/single-player only in v0.1.1.");
                        yield break;
                    }

                    ApplyLocalProfile(master, SaveService.Current);
                    yield break;
                }
                yield return null;
            }

            PetrichorLegacyPlugin.Log.LogWarning("Could not apply local meta progression: player master was not ready.");
        }

        private static void ApplyLocalProfile(CharacterMaster master, ProfileProgress profile)
        {
            if (master == null || master.inventory == null || profile == null) return;

            var validated = ValidateTalents(profile.level, profile.talents);
            ServerProgressionState.Set(master, validated);
            ApplyRunStartBonuses(master, validated);
            ApplyValidatedLoadout(master, validated, profile.startingLoadout);
            master.GetBody()?.RecalculateStats();
            PetrichorLegacyPlugin.Log.LogInfo($"Standalone meta progression applied: level={validated.Level}, loadout={profile.startingLoadout?.Count ?? 0} records.");
        }

        private static ValidatedProgress ValidateTalents(int claimedLevel, List<TalentRankRecord> claimed)
        {
            claimedLevel = Math.Max(1, Math.Min(claimedLevel, 10000));
            claimed = claimed ?? new List<TalentRankRecord>();
            var availablePoints = claimedLevel - 1;
            var progress = new ValidatedProgress { Level = claimedLevel };
            var spent = 0;

            foreach (var def in TalentCatalog.All)
            {
                var requested = claimed.FirstOrDefault(x => x.id == def.Id)?.rank ?? 0;
                requested = Math.Max(0, Math.Min(requested, def.MaxRank));

                var prereqMet = string.IsNullOrEmpty(def.PrerequisiteId) ||
                                (progress.Talents.TryGetValue(def.PrerequisiteId, out var preRank) && preRank >= def.PrerequisiteRank);
                if (!prereqMet) requested = 0;

                var affordableRanks = Math.Min(requested, Math.Max(0, (availablePoints - spent) / def.PointCost));
                progress.Talents[def.Id] = affordableRanks;
                spent += affordableRanks * def.PointCost;
            }

            return progress;
        }

        private static void ApplyRunStartBonuses(CharacterMaster master, ValidatedProgress progress)
        {
            if (progress.LoadoutApplied) return;

            var startGoldRank = Rank(progress, "fortune_gold");
            if (startGoldRank > 0) master.GiveMoney((uint)(startGoldRank * 15));

            var luckRank = Rank(progress, "fortune_luck");
            if (luckRank > 0) master.luck += luckRank * 0.1f;

            if (Rank(progress, "survival_second_chance") > 0)
                master.inventory.GiveItemPermanent(RoR2Content.Items.ExtraLife, 1);
        }

        private static void ApplyValidatedLoadout(CharacterMaster master, ValidatedProgress progress, List<LoadoutItemRecord> requested)
        {
            if (progress.LoadoutApplied) return;
            requested = requested ?? new List<LoadoutItemRecord>();

            var pseudoProfile = new ProfileProgress { level = progress.Level };
            foreach (var kv in progress.Talents)
                pseudoProfile.talents.Add(new TalentRankRecord { id = kv.Key, rank = kv.Value });

            var capacity = ProgressionService.StartingCapacity(pseudoProfile);
            var used = 0;

            foreach (var record in requested)
            {
                var item = StartingLoadoutService.FindItem(record.itemName);
                if (item == null || !StartingLoadoutService.IsEligible(item, pseudoProfile)) continue;
                var requestedCount = Math.Max(0, Math.Min(record.count, 64));

                for (var i = 0; i < requestedCount; i++)
                {
                    var cost = StartingLoadoutService.CostOfCopy(item, i);
                    if (used + cost > capacity) break;
                    master.inventory.GiveItemPermanent(item.itemIndex, 1);
                    used += cost;
                }
            }

            progress.LoadoutApplied = true;
        }

        private static int Rank(ValidatedProgress p, string id) => p.Talents.TryGetValue(id, out var r) ? r : 0;
    }
}

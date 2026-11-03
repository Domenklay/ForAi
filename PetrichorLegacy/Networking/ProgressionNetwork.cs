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
            PetrichorLegacyPlugin.Log?.LogInfo("Standalone progression sync enabled (host/single-player authoritative).");
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
                        PetrichorLegacyPlugin.Log.LogWarning("Multiplayer client detected. Meta bonuses are host/single-player authoritative in v0.3.0.");
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

            var validated = Validate(profile);
            ServerProgressionState.Set(master, validated);
            ApplyRunStartBonuses(master, validated);
            ApplyValidatedLoadout(master, validated, profile.startingLoadout);
            master.GetBody()?.RecalculateStats();
            PetrichorLegacyPlugin.Log.LogInfo($"Meta progression applied: level={validated.Level}, class={validated.ActiveClass}, spec={validated.ActiveSpecialization}.");
        }

        private static ValidatedProgress Validate(ProfileProgress profile)
        {
            var level = Math.Max(1, Math.Min(profile.level, 100000));
            var progress = new ValidatedProgress
            {
                Level = level,
                ActiveClass = ValidClass(profile.activeClass) ? profile.activeClass : string.Empty,
                ActiveSpecialization = string.Empty
            };
            if (ProgressionService.SpecBelongsToClass(profile.activeSpecialization, progress.ActiveClass))
                progress.ActiveSpecialization = profile.activeSpecialization ?? string.Empty;

            var availableTalentPoints = ProgressionService.EarnedTalentPointsForLevel(level);
            var spent = 0;
            foreach (var def in TalentCatalog.All)
            {
                var requested = profile.talents?.FirstOrDefault(x => x.id == def.Id)?.rank ?? 0;
                requested = Math.Max(0, Math.Min(requested, def.MaxRank));
                if (level < def.UnlockLevel) requested = 0;
                var prereqMet = string.IsNullOrEmpty(def.PrerequisiteId) ||
                                (progress.Talents.TryGetValue(def.PrerequisiteId, out var preRank) && preRank >= def.PrerequisiteRank);
                if (!prereqMet) requested = 0;
                var affordable = Math.Min(requested, Math.Max(0, (availableTalentPoints - spent) / Math.Max(1, def.PointCost)));
                progress.Talents[def.Id] = affordable;
                spent += affordable * def.PointCost;
            }

            var masteryLeft = ProgressionService.EarnedMasteryPointsForLevel(level);
            foreach (var def in MasteryCatalog.All)
            {
                var requested = Math.Max(0, profile.masteries?.FirstOrDefault(x => x.id == def.Id)?.rank ?? 0);
                var accepted = Math.Min(requested, masteryLeft);
                progress.Masteries[def.Id] = accepted;
                masteryLeft -= accepted;
            }

            var perfectionLeft = ProgressionService.EarnedPerfectionPointsForLevel(level);
            foreach (var def in PerfectionCatalog.All)
            {
                var requested = Math.Max(0, profile.perfections?.FirstOrDefault(x => x.id == def.Id)?.rank ?? 0);
                if (level < def.UnlockLevel) requested = 0;
                var accepted = Math.Min(Math.Min(requested, def.MaxRank), perfectionLeft);
                progress.Perfections[def.Id] = accepted;
                perfectionLeft -= accepted;
            }

            return progress;
        }

        private static bool ValidClass(string classId) =>
            classId == "Guardian" || classId == "Slayer" || classId == "Pathfinder" || classId == "Seeker";

        private static void ApplyRunStartBonuses(CharacterMaster master, ValidatedProgress progress)
        {
            if (progress.LoadoutApplied) return;

            var startGold = 0f;
            startGold += ServerProgressionState.Rank(master, "seeker_startgold") * 10f;
            startGold += ServerProgressionState.Rank(master, "seeker_cache") * 25f;
            startGold += ServerProgressionState.Rank(master, "merchant_startgold") * 15f;
            startGold += ServerProgressionState.MasteryValue(master, "mastery_seeker_startgold");
            if (startGold > 0f) master.GiveMoney((uint)Math.Max(0, Math.Round(startGold)));
        }

        private static void ApplyValidatedLoadout(CharacterMaster master, ValidatedProgress progress, List<LoadoutItemRecord> requested)
        {
            if (progress.LoadoutApplied) return;
            requested = requested ?? new List<LoadoutItemRecord>();

            var pseudoProfile = new ProfileProgress
            {
                level = progress.Level,
                activeClass = progress.ActiveClass,
                activeSpecialization = progress.ActiveSpecialization
            };
            foreach (var kv in progress.Talents)
                pseudoProfile.talents.Add(new TalentRankRecord { id = kv.Key, rank = kv.Value });
            foreach (var kv in progress.Perfections)
                pseudoProfile.perfections.Add(new PerfectionRankRecord { id = kv.Key, rank = kv.Value });

            var capacity = ProgressionService.StartingCapacity(pseudoProfile);
            var used = 0;
            var highImpactUsed = false;

            foreach (var record in requested)
            {
                var item = StartingLoadoutService.FindItem(record.itemName);
                if (item == null || !StartingLoadoutService.IsEligible(item, pseudoProfile)) continue;
                var requestedCount = Math.Max(0, Math.Min(record.count, 64));

                for (var i = 0; i < requestedCount; i++)
                {
                    if (StartingLoadoutService.IsHighImpact(item) && highImpactUsed) break;
                    var cost = StartingLoadoutService.CostOfCopy(item, i);
                    if (used + cost > capacity) break;
                    master.inventory.GiveItemPermanent(item.itemIndex, 1);
                    used += cost;
                    if (StartingLoadoutService.IsHighImpact(item)) highImpactUsed = true;
                }
            }

            progress.LoadoutApplied = true;
        }
    }
}

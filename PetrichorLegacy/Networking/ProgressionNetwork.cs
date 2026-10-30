using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using PetrichorLegacy.Loadout;
using PetrichorLegacy.Models;
using PetrichorLegacy.Persistence;
using PetrichorLegacy.Progression;
using R2API.Networking;
using R2API.Networking.Interfaces;
using RoR2;
using UnityEngine.Networking;

namespace PetrichorLegacy.Networking
{
    public static class ProgressionNetwork
    {
        public static void Register()
        {
            NetworkingAPI.RegisterMessageType<PlayerProgressMessage>();
        }

        public static IEnumerator SendLocalProgressWhenReady()
        {
            for (var i = 0; i < 300; i++)
            {
                SaveService.RefreshProfile();
                var local = LocalUserManager.GetFirstLocalUser();
                var localMaster = local?.cachedMaster;
                var networkUser = NetworkUser.readOnlyInstancesList.FirstOrDefault(n => n != null && n.master == localMaster);
                if (networkUser != null && networkUser.master != null && networkUser.master.inventory != null)
                {
                    var msg = PlayerProgressMessage.FromProfile(networkUser.netId.Value, SaveService.Current);
                    msg.Send(NetworkDestination.Server);
                    yield break;
                }
                yield return null;
            }

            PetrichorLegacyPlugin.Log.LogWarning("Could not send local meta progression: NetworkUser was not ready.");
        }
    }

    public sealed class PlayerProgressMessage : INetMessage
    {
        private uint networkUserNetId;
        private int level;
        private List<TalentRankRecord> talents = new List<TalentRankRecord>();
        private List<LoadoutItemRecord> loadout = new List<LoadoutItemRecord>();

        public static PlayerProgressMessage FromProfile(uint netId, ProfileProgress profile)
        {
            return new PlayerProgressMessage
            {
                networkUserNetId = netId,
                level = Math.Max(1, profile?.level ?? 1),
                talents = profile?.talents?.Select(x => new TalentRankRecord { id = x.id, rank = x.rank }).ToList() ?? new List<TalentRankRecord>(),
                loadout = profile?.startingLoadout?.Select(x => new LoadoutItemRecord { itemName = x.itemName, count = x.count }).ToList() ?? new List<LoadoutItemRecord>()
            };
        }

        public void Serialize(NetworkWriter writer)
        {
            writer.Write(networkUserNetId);
            writer.Write(level);
            writer.Write(talents.Count);
            foreach (var t in talents)
            {
                writer.Write(t.id ?? string.Empty);
                writer.Write(t.rank);
            }

            writer.Write(loadout.Count);
            foreach (var item in loadout)
            {
                writer.Write(item.itemName ?? string.Empty);
                writer.Write(item.count);
            }
        }

        public void Deserialize(NetworkReader reader)
        {
            networkUserNetId = reader.ReadUInt32();
            level = reader.ReadInt32();
            talents = new List<TalentRankRecord>();
            var talentCount = Math.Max(0, Math.Min(reader.ReadInt32(), 128));
            for (var i = 0; i < talentCount; i++)
                talents.Add(new TalentRankRecord { id = reader.ReadString(), rank = reader.ReadInt32() });

            loadout = new List<LoadoutItemRecord>();
            var loadoutCount = Math.Max(0, Math.Min(reader.ReadInt32(), 256));
            for (var i = 0; i < loadoutCount; i++)
                loadout.Add(new LoadoutItemRecord { itemName = reader.ReadString(), count = reader.ReadInt32() });
        }

        public void OnReceived()
        {
            if (!NetworkServer.active) return;

            var networkUser = NetworkUser.readOnlyInstancesList.FirstOrDefault(n => n != null && n.netId.Value == networkUserNetId);
            var master = networkUser?.master;
            if (master == null || master.inventory == null) return;

            var validated = ValidateTalents(level, talents);
            ServerProgressionState.Set(master, validated);
            ApplyRunStartBonuses(master, validated);
            ApplyValidatedLoadout(master, validated, loadout);
        }

        private static ValidatedProgress ValidateTalents(int claimedLevel, List<TalentRankRecord> claimed)
        {
            claimedLevel = Math.Max(1, Math.Min(claimedLevel, 10000));
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

            if (Rank(progress, "survival_second_chance") > 0)
                master.inventory.GiveItem(RoR2Content.Items.ExtraLife, 1);
        }

        private static void ApplyValidatedLoadout(CharacterMaster master, ValidatedProgress progress, List<LoadoutItemRecord> requested)
        {
            if (progress.LoadoutApplied) return;

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
                    master.inventory.GiveItem(item.itemIndex, 1);
                    used += cost;
                }
            }

            progress.LoadoutApplied = true;
        }

        private static int Rank(ValidatedProgress p, string id) => p.Talents.TryGetValue(id, out var r) ? r : 0;
    }
}

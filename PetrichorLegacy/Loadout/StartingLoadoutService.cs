using System;
using System.Collections.Generic;
using System.Linq;
using PetrichorLegacy.Models;
using PetrichorLegacy.Progression;
using RoR2;

namespace PetrichorLegacy.Loadout
{
    public static class StartingLoadoutService
    {
        public static IEnumerable<ItemDef> EnumerateEligibleItems(ProfileProgress profile, UserProfile userProfile)
        {
            foreach (var item in ItemCatalog.allItemDefs)
            {
                if (item == null || !IsEligible(item, profile)) continue;
                var pickup = PickupCatalog.FindPickupIndex(item.itemIndex);
                if (userProfile != null && pickup != PickupIndex.none && !userProfile.HasDiscoveredPickup(pickup))
                    continue;
                yield return item;
            }
        }

        public static bool IsEligible(ItemDef item, ProfileProgress profile)
        {
            if (item == null || item.hidden) return false;
            var name = item.name ?? string.Empty;
            if (name.IndexOf("Scrap", StringComparison.OrdinalIgnoreCase) >= 0 ||
                name.IndexOf("ArtifactKey", StringComparison.OrdinalIgnoreCase) >= 0 ||
                name.IndexOf("Consumed", StringComparison.OrdinalIgnoreCase) >= 0 ||
                name.IndexOf("Cerebellum", StringComparison.OrdinalIgnoreCase) >= 0)
                return false;

            var tierName = TierName(item);
            if (Contains(tierName, "Hex") || Contains(tierName, "Page")) return false;
            if (Contains(tierName, "Hallowed") || Contains(tierName, "Cursed"))
                return TalentCatalog.GetRank(profile, "expedition_hallowed") > 0;
            if (Contains(tierName, "FoodTier"))
                return TalentCatalog.GetRank(profile, "expedition_green") > 0;

            switch (item.tier)
            {
                case ItemTier.Tier1:
                    return true;
                case ItemTier.Tier2:
                    return TalentCatalog.GetRank(profile, "expedition_green") > 0;
                case ItemTier.Tier3:
                    return TalentCatalog.GetRank(profile, "expedition_red") > 0;
                case ItemTier.Boss:
                case ItemTier.Lunar:
                case ItemTier.VoidTier1:
                case ItemTier.VoidTier2:
                case ItemTier.VoidTier3:
                case ItemTier.VoidBoss:
                    return TalentCatalog.GetRank(profile, "expedition_exotic") > 0;
                default:
                    return TalentCatalog.GetRank(profile, "expedition_hallowed") > 0;
            }
        }

        public static int ItemBaseCost(ItemDef item)
        {
            if (item == null) return 99;
            var tierName = TierName(item);
            if (Contains(tierName, "Hallowed") || Contains(tierName, "Cursed")) return 6;
            if (Contains(tierName, "FoodTier")) return 2;

            switch (item.tier)
            {
                case ItemTier.Tier1: return 1;
                case ItemTier.Tier2: return 2;
                case ItemTier.Tier3: return 4;
                case ItemTier.Boss: return 4;
                case ItemTier.Lunar: return 4;
                case ItemTier.VoidTier1: return 2;
                case ItemTier.VoidTier2: return 3;
                case ItemTier.VoidTier3: return 5;
                case ItemTier.VoidBoss: return 5;
                default: return 5;
            }
        }

        public static int CostOfCopy(ItemDef item, int alreadySelected)
        {
            return ItemBaseCost(item) + Math.Max(0, alreadySelected);
        }

        public static int UsedCapacity(ProfileProgress profile)
        {
            if (profile?.startingLoadout == null) return 0;
            var total = 0;
            foreach (var record in profile.startingLoadout)
            {
                var item = FindItem(record.itemName);
                if (item == null) continue;
                for (var i = 0; i < record.count; i++) total += CostOfCopy(item, i);
            }
            return total;
        }

        public static bool TryAdd(ProfileProgress profile, ItemDef item, out string error)
        {
            error = null;
            if (!IsEligible(item, profile))
            {
                error = "Этот тип предмета пока не открыт или запрещён для старта.";
                return false;
            }

            var record = profile.startingLoadout.FirstOrDefault(x => x.itemName == item.name);
            var count = record?.count ?? 0;
            var nextCost = CostOfCopy(item, count);
            if (UsedCapacity(profile) + nextCost > ProgressionService.StartingCapacity(profile))
            {
                error = "Не хватает вместимости стартового набора.";
                return false;
            }

            if (record == null)
            {
                record = new LoadoutItemRecord { itemName = item.name, count = 0 };
                profile.startingLoadout.Add(record);
            }
            record.count++;
            Persistence.SaveService.SaveCurrent();
            return true;
        }

        public static void RemoveOne(ProfileProgress profile, ItemDef item)
        {
            var record = profile?.startingLoadout?.FirstOrDefault(x => x.itemName == item?.name);
            if (record == null) return;
            record.count--;
            if (record.count <= 0) profile.startingLoadout.Remove(record);
            Persistence.SaveService.SaveCurrent();
        }

        public static ItemDef FindItem(string internalName)
        {
            if (string.IsNullOrEmpty(internalName)) return null;
            return ItemCatalog.allItemDefs.FirstOrDefault(x => x != null && x.name == internalName);
        }

        public static string TierName(ItemDef item)
        {
            if (item == null) return string.Empty;
            try
            {
                var def = ItemTierCatalog.GetItemTierDef(item.tier);
                return def != null ? def.name : item.tier.ToString();
            }
            catch
            {
                return item.tier.ToString();
            }
        }

        private static bool Contains(string text, string part) =>
            !string.IsNullOrEmpty(text) && text.IndexOf(part, StringComparison.OrdinalIgnoreCase) >= 0;
    }
}

using System.Reflection;
using RoR2;
using UnityEngine;
using UnityEngine.Networking;

namespace PetrichorLegacy.Progression
{
    public static class TalentEffects
    {
        public static void Install()
        {
            On.RoR2.CharacterBody.RecalculateStats += CharacterBody_RecalculateStats;
            Stage.onStageStartGlobal += OnStageStart;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterBody.RecalculateStats -= CharacterBody_RecalculateStats;
            Stage.onStageStartGlobal -= OnStageStart;
        }

        private static void CharacterBody_RecalculateStats(On.RoR2.CharacterBody.orig_RecalculateStats orig, CharacterBody self)
        {
            orig(self);
            if (self == null || self.master == null) return;

            var master = self.master;

            self.maxHealth *= 1f + ServerProgressionState.Rank(master, "survival_vitality") * 0.02f;
            self.regen *= 1f + ServerProgressionState.Rank(master, "survival_recovery") * 0.04f;
            self.armor += ServerProgressionState.Rank(master, "survival_armor") * 2f;
            self.maxShield += self.baseMaxHealth * ServerProgressionState.Rank(master, "survival_shield") * 0.02f;

            self.damage *= 1f + ServerProgressionState.Rank(master, "offense_power") * 0.02f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(master, "offense_frenzy") * 0.02f;
            self.crit += ServerProgressionState.Rank(master, "offense_precision");

            var cooldownRank = ServerProgressionState.Rank(master, "offense_cooldown");
            if (cooldownRank > 0 && self.skillLocator != null)
            {
                var mult = Mathf.Max(0.1f, 1f - cooldownRank * 0.015f);
                ApplyCooldownScale(self.skillLocator.primary, mult);
                ApplyCooldownScale(self.skillLocator.secondary, mult);
                ApplyCooldownScale(self.skillLocator.utility, mult);
                ApplyCooldownScale(self.skillLocator.special, mult);
            }

            if (ServerProgressionState.Rank(master, "offense_executioner") > 0)
                MultiplyFloatMember(self, "critMultiplier", 1.20f);

            self.moveSpeed *= 1f + ServerProgressionState.Rank(master, "mobility_stride") * 0.02f;
            self.sprintingSpeedMultiplier *= 1f + ServerProgressionState.Rank(master, "mobility_sprint") * 0.02f;
            self.jumpPower *= 1f + ServerProgressionState.Rank(master, "mobility_jump") * 0.04f;
            self.maxJumpCount += ServerProgressionState.Rank(master, "mobility_air");
            if (ServerProgressionState.Rank(master, "mobility_mastery") > 0)
            {
                self.moveSpeed *= 1.05f;
                self.maxJumpCount += 1;
            }

            var scavenger = ServerProgressionState.Rank(master, "fortune_scavenger");
            self.moveSpeed *= 1f + scavenger * 0.02f;
            self.armor += scavenger * 2f;
        }

        private static void ApplyCooldownScale(GenericSkill skill, float multiplier)
        {
            if (skill == null) return;
            var type = typeof(GenericSkill);
            var field = type.GetField("cooldownScale", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (field != null && field.FieldType == typeof(float))
            {
                var value = (float)field.GetValue(skill);
                field.SetValue(skill, value * multiplier);
                return;
            }

            var prop = type.GetProperty("cooldownScale", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (prop != null && prop.CanRead && prop.CanWrite && prop.PropertyType == typeof(float))
            {
                var value = (float)prop.GetValue(skill, null);
                prop.SetValue(skill, value * multiplier, null);
            }
        }

        private static void MultiplyFloatMember(object obj, string name, float multiplier)
        {
            if (obj == null) return;
            var type = obj.GetType();
            var field = type.GetField(name, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (field != null && field.FieldType == typeof(float))
            {
                field.SetValue(obj, (float)field.GetValue(obj) * multiplier);
                return;
            }

            var prop = type.GetProperty(name, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (prop != null && prop.CanRead && prop.CanWrite && prop.PropertyType == typeof(float))
                prop.SetValue(obj, (float)prop.GetValue(obj, null) * multiplier, null);
        }

        private static void OnStageStart(Stage stage)
        {
            if (!NetworkServer.active || Run.instance == null) return;

            foreach (var pcmc in PlayerCharacterMasterController.instances)
            {
                var master = pcmc?.master;
                if (master == null) continue;
                var progress = ServerProgressionState.Get(master);
                if (progress == null) continue;

                var stipendRank = ServerProgressionState.Rank(master, "fortune_stipend");
                if (stipendRank > 0 && Run.instance.stageClearCount > 0)
                    master.GiveMoney((uint)(stipendRank * 10));

                if (ServerProgressionState.Rank(master, "fortune_prospector") > 0 &&
                    !progress.ProspectorGranted && Run.instance.stageClearCount > 0)
                {
                    progress.ProspectorGranted = true;
                    GrantRandomWhite(master);
                }
            }
        }

        private static void GrantRandomWhite(CharacterMaster master)
        {
            var drops = Run.instance?.availableTier1DropList;
            if (drops == null || drops.Count == 0 || master.inventory == null) return;
            var pickup = drops[Random.Range(0, drops.Count)];
            var def = PickupCatalog.GetPickupDef(pickup);
            if (def != null && def.itemIndex != ItemIndex.None)
                master.inventory.GiveItemPermanent(def.itemIndex, 1);
        }
    }
}

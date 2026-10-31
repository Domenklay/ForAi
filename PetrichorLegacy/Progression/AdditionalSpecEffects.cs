using System.Reflection;
using RoR2;
using UnityEngine;

namespace PetrichorLegacy.Progression
{
    public static class AdditionalSpecEffects
    {
        public static void Install()
        {
            On.RoR2.CharacterBody.RecalculateStats += CharacterBody_RecalculateStats;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterBody.RecalculateStats -= CharacterBody_RecalculateStats;
        }

        private static void CharacterBody_RecalculateStats(On.RoR2.CharacterBody.orig_RecalculateStats orig, CharacterBody self)
        {
            orig(self);
            if (self == null || self.master == null || self.master.playerCharacterMasterController == null) return;
            if (ServerProgressionState.Get(self.master) == null) return;

            // Guardian / Vanguard — modest offense without reaching Slayer output.
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "vanguard_damage") * 0.01f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "vanguard_move") * 0.015f;
            self.armor += ServerProgressionState.Rank(self.master, "vanguard_armor") * 2f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "vanguard_attack") * 0.015f;
            if (ServerProgressionState.Rank(self.master, "vanguard_breaker") > 0)
            {
                self.damage *= 1.02f;
                self.armor += 2f;
            }

            // Slayer / Berserker — highest tempo, no extra defensive scaling.
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "berserker_attack") * 0.02f;
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "berserker_damage") * 0.015f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "berserker_move") * 0.015f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "berserker_cooldown") * 0.01f);
            if (ServerProgressionState.Rank(self.master, "berserker_frenzy") > 0)
            {
                self.damage *= 1.02f;
                self.attackSpeed *= 1.02f;
            }

            // Pathfinder / Saboteur — skill frequency and crowd-control oriented damage.
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "saboteur_cooldown") * 0.01f);
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "saboteur_damage") * 0.01f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "saboteur_move") * 0.015f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "saboteur_attack") * 0.015f;
            if (ServerProgressionState.Rank(self.master, "saboteur_chain") > 0)
            {
                self.damage *= 1.02f;
                ApplyCooldownScale(self.skillLocator, 0.02f);
            }

            // Seeker / Relic Keeper — utility stats; the legendary reward handles equipment identity.
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "relic_cooldown") * 0.01f);
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "relic_move") * 0.015f;
            self.armor += ServerProgressionState.Rank(self.master, "relic_armor") * 2f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "relic_attack") * 0.015f;
            if (ServerProgressionState.Rank(self.master, "relic_attunement") > 0)
            {
                self.moveSpeed *= 1.02f;
                ApplyCooldownScale(self.skillLocator, 0.02f);
            }
        }

        private static void ApplyCooldownScale(SkillLocator locator, float reduction)
        {
            if (locator == null || reduction <= 0f) return;
            var mult = Mathf.Clamp(1f - reduction, 0.70f, 1f);
            ApplyCooldownScale(locator.primary, mult);
            ApplyCooldownScale(locator.secondary, mult);
            ApplyCooldownScale(locator.utility, mult);
            ApplyCooldownScale(locator.special, mult);
        }

        private static void ApplyCooldownScale(GenericSkill skill, float multiplier)
        {
            if (skill == null) return;
            var type = typeof(GenericSkill);
            var field = type.GetField("cooldownScale", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (field != null && field.FieldType == typeof(float))
            {
                var value = (float)field.GetValue(skill);
                field.SetValue(skill, Mathf.Clamp(value * multiplier, 0.70f, 2f));
                return;
            }
            var prop = type.GetProperty("cooldownScale", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (prop != null && prop.CanRead && prop.CanWrite && prop.PropertyType == typeof(float))
            {
                var value = (float)prop.GetValue(skill, null);
                prop.SetValue(skill, Mathf.Clamp(value * multiplier, 0.70f, 2f), null);
            }
        }
    }
}

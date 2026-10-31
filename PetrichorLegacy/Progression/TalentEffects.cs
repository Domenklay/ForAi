using System;
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
            On.RoR2.CharacterMaster.OnBodyStart += CharacterMaster_OnBodyStart;
            On.RoR2.HealthComponent.TakeDamageProcess += HealthComponent_TakeDamageProcess;
            Stage.onStageStartGlobal += OnStageStart;
            GlobalEventManager.onCharacterDeathGlobal += OnCharacterDeath;
        }

        public static void Uninstall()
        {
            On.RoR2.CharacterBody.RecalculateStats -= CharacterBody_RecalculateStats;
            On.RoR2.CharacterMaster.OnBodyStart -= CharacterMaster_OnBodyStart;
            On.RoR2.HealthComponent.TakeDamageProcess -= HealthComponent_TakeDamageProcess;
            Stage.onStageStartGlobal -= OnStageStart;
            GlobalEventManager.onCharacterDeathGlobal -= OnCharacterDeath;
        }

        private static void CharacterMaster_OnBodyStart(On.RoR2.CharacterMaster.orig_OnBodyStart orig, CharacterMaster self, CharacterBody body)
        {
            orig(self, body);
            if (body == null || self == null || self.playerCharacterMasterController == null) return;
            var controller = body.GetComponent<MetaRuntimeController>() ?? body.gameObject.AddComponent<MetaRuntimeController>();
            controller.Initialize(body);
        }

        private static void CharacterBody_RecalculateStats(On.RoR2.CharacterBody.orig_RecalculateStats orig, CharacterBody self)
        {
            orig(self);
            if (self == null || self.master == null || self.master.playerCharacterMasterController == null) return;
            if (ServerProgressionState.Get(self.master) == null) return;

            // Legacy: always active.
            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "legacy_hp") * 0.01f;
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "legacy_damage") * 0.01f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_attack") * 0.01f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "legacy_move") * 0.015f;
            self.armor += ServerProgressionState.Rank(self.master, "legacy_armor");
            self.regen *= 1f + ServerProgressionState.Rank(self.master, "legacy_regen") * 0.02f;

            // Guardian base + specs.
            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "guardian_vitality") * 0.015f;
            self.armor += ServerProgressionState.Rank(self.master, "guardian_armor") * 2f;
            self.regen *= 1f + ServerProgressionState.Rank(self.master, "guardian_regen") * 0.04f;
            self.maxShield += self.baseMaxHealth * ServerProgressionState.Rank(self.master, "guardian_stability") * 0.015f;
            if (ServerProgressionState.Rank(self.master, "guardian_endurance") > 0)
            {
                self.maxHealth *= 1.01f;
                self.armor += 2f;
            }

            self.maxShield += self.baseMaxHealth * ServerProgressionState.Rank(self.master, "bastion_shield") * 0.02f;
            self.armor += ServerProgressionState.Rank(self.master, "bastion_armor") * 2f;
            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "bastion_health") * 0.015f;
            if (ServerProgressionState.Rank(self.master, "bastion_lastwall") > 0)
            {
                self.maxShield += self.baseMaxHealth * 0.05f;
                self.armor += 3f;
            }

            self.regen *= 1f + ServerProgressionState.Rank(self.master, "unbroken_regen") * 0.05f;
            self.maxHealth *= 1f + ServerProgressionState.Rank(self.master, "unbroken_health") * 0.015f;
            if (ServerProgressionState.Rank(self.master, "unbroken_ironwill") > 0)
            {
                self.armor += 5f;
                self.regen *= 1.05f;
            }

            // Slayer base + Executioner.
            self.damage *= 1f + ServerProgressionState.Rank(self.master, "slayer_damage") * 0.015f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "slayer_attack") * 0.01f;
            self.crit += ServerProgressionState.Rank(self.master, "slayer_crit");
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "slayer_move") * 0.015f;
            if (ServerProgressionState.Rank(self.master, "slayer_focus") > 0)
            {
                self.damage *= 1.02f;
                self.attackSpeed *= 1.01f;
            }
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "slayer_cooldown") * 0.01f);

            self.damage *= 1f + ServerProgressionState.Rank(self.master, "executioner_power") * 0.01f;
            self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "executioner_attack") * 0.015f;
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.Rank(self.master, "executioner_cooldown") * 0.01f);
            var critDamageBonus = ServerProgressionState.Rank(self.master, "executioner_critdamage") * 0.05f;
            if (ServerProgressionState.Rank(self.master, "executioner_verdict") > 0)
            {
                self.damage *= 1.02f;
                critDamageBonus += 0.10f;
            }
            if (critDamageBonus > 0f) MultiplyFloatMember(self, "critMultiplier", 1f + critDamageBonus);

            var progress = ServerProgressionState.Get(self.master);
            if (progress != null && progress.HunterHasteUntil > Time.fixedTime)
                self.attackSpeed *= 1f + ServerProgressionState.Rank(self.master, "hunter_haste") * 0.04f;

            // Pathfinder base + specs.
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "path_move") * 0.015f;
            self.sprintingSpeedMultiplier *= 1f + ServerProgressionState.Rank(self.master, "path_sprint") * 0.02f;
            self.jumpPower *= 1f + ServerProgressionState.Rank(self.master, "path_jump") * 0.05f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "path_control") * 0.01f;
            self.armor += ServerProgressionState.Rank(self.master, "path_armor");
            if (ServerProgressionState.Rank(self.master, "path_flow") > 0) self.moveSpeed *= 1.02f;

            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "scout_move") * 0.015f;
            self.sprintingSpeedMultiplier *= 1f + ServerProgressionState.Rank(self.master, "scout_sprint") * 0.02f;
            self.jumpPower *= 1f + ServerProgressionState.Rank(self.master, "scout_jump") * 0.05f;
            if (ServerProgressionState.Rank(self.master, "scout_expedition") > 0) self.moveSpeed *= 1.04f;

            self.jumpPower *= 1f + ServerProgressionState.Rank(self.master, "acro_jump") * 0.06f;
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "acro_move") * 0.015f;
            self.armor += ServerProgressionState.Rank(self.master, "acro_armor");
            self.maxJumpCount += ServerProgressionState.Rank(self.master, "acro_extra_jump");
            if (ServerProgressionState.Rank(self.master, "acro_elusive") > 0)
            {
                self.moveSpeed *= 1.03f;
                self.jumpPower *= 1.05f;
            }

            // Seeker base.
            self.moveSpeed *= 1f + ServerProgressionState.Rank(self.master, "seeker_move") * 0.01f;
            self.armor += ServerProgressionState.Rank(self.master, "seeker_armor");

            // Infinite mastery. Only the active class contributes.
            self.maxHealth *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_guardian_hp");
            self.armor += ServerProgressionState.MasteryValue(self.master, "mastery_guardian_armor");
            self.regen *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_guardian_regen");
            self.maxShield += self.baseMaxHealth * ServerProgressionState.MasteryValue(self.master, "mastery_guardian_shield");

            self.damage *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_slayer_damage");
            self.attackSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_slayer_attack");
            self.crit += ServerProgressionState.MasteryValue(self.master, "mastery_slayer_crit");
            ApplyCooldownScale(self.skillLocator, ServerProgressionState.MasteryValue(self.master, "mastery_slayer_cooldown"));

            self.moveSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_path_move");
            self.sprintingSpeedMultiplier *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_path_sprint");
            self.jumpPower *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_path_jump");
            self.moveSpeed *= 1f + ServerProgressionState.MasteryValue(self.master, "mastery_path_control");

            // Perfection and prestige.
            if (ServerProgressionState.Perfection(self.master, "perfection_prestige_hardened") > 0) self.maxHealth *= 1.01f;
            if (ServerProgressionState.Perfection(self.master, "perfection_prestige_veteran") > 0)
            {
                self.attackSpeed *= 1.01f;
                self.moveSpeed *= 1.01f;
            }
            if (ServerProgressionState.Perfection(self.master, "perfection_instinct") > 0 &&
                self.healthComponent != null && self.healthComponent.combinedHealthFraction < 0.30f)
                self.armor += 3f;
        }

        private static void HealthComponent_TakeDamageProcess(On.RoR2.HealthComponent.orig_TakeDamageProcess orig, HealthComponent self, DamageInfo damageInfo)
        {
            var attackerBody = damageInfo.attacker ? damageInfo.attacker.GetComponent<CharacterBody>() : null;
            var victimBody = self != null ? self.body : null;
            if (attackerBody != null && attackerBody.master != null && victimBody != null)
            {
                if (victimBody.isBoss && ServerProgressionState.Perfection(attackerBody.master, "perfection_giant_slayer") > 0)
                    damageInfo.damage *= 1.03f;
                if (victimBody.GetComponent<MonsterRarityMarker>() != null &&
                    ServerProgressionState.Perfection(attackerBody.master, "perfection_prestige_predator") > 0)
                    damageInfo.damage *= 1.02f;
            }
            orig(self, damageInfo);
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
                var body = master?.GetBody();
                var progress = master != null ? ServerProgressionState.Get(master) : null;
                if (master == null || body == null || progress == null) continue;

                var healFraction = 0f;
                healFraction += ServerProgressionState.Rank(master, "guardian_stageheal") * 0.04f;
                healFraction += ServerProgressionState.Rank(master, "unbroken_stageheal") * 0.03f;
                if (ServerProgressionState.Perfection(master, "perfection_reserve") > 0) healFraction += 0.05f;
                if (healFraction > 0f && body.healthComponent != null)
                    body.healthComponent.HealFraction(healFraction, default(ProcChainMask));

                var barrierFraction = ServerProgressionState.Rank(master, "bastion_stagebarrier") * 0.04f;
                if (barrierFraction > 0f && body.healthComponent != null)
                    body.healthComponent.AddBarrier(body.maxHealth * barrierFraction);

                var stageIndex = Math.Max(0, Run.instance.stageClearCount);
                var gold = 0f;
                if (stageIndex > 0)
                {
                    gold += ServerProgressionState.Rank(master, "seeker_stagegold") * 10f;
                    gold += ServerProgressionState.Rank(master, "merchant_stagegold") * 15f;
                    gold += ServerProgressionState.Rank(master, "merchant_reserve") * 25f;
                    gold += ServerProgressionState.Rank(master, "scout_stagegold") * 10f;
                    if (ServerProgressionState.Rank(master, "scout_expedition") > 0) gold += 20f;
                    if (ServerProgressionState.Rank(master, "merchant_capital") > 0) gold += stageIndex * 10f;
                    gold += ServerProgressionState.MasteryValue(master, "mastery_seeker_stagegold");
                }
                if (gold > 0f) master.GiveMoney((uint)Math.Round(gold));

                if (ServerProgressionState.Rank(master, "prospector_white3") > 0 && stageIndex > 0 && stageIndex % 3 == 0)
                    GrantRandomItem(master, false);
                if (ServerProgressionState.Rank(master, "prospector_goldmine") > 0 && stageIndex > 0 && stageIndex % 5 == 0)
                    GrantRandomItem(master, true);
            }
        }

        private static void OnCharacterDeath(DamageReport report)
        {
            if (!NetworkServer.active || report?.victimBody == null || report.attackerMaster == null) return;
            if (report.attackerMaster.playerCharacterMasterController == null) return;

            if (report.victimBody.isBoss)
            {
                var rank = ServerProgressionState.Rank(report.attackerMaster, "unbroken_bossheal");
                var body = report.attackerMaster.GetBody();
                if (rank > 0 && body?.healthComponent != null)
                    body.healthComponent.HealFraction(rank * 0.05f, default(ProcChainMask));
            }
        }

        public static void GrantRandomItem(CharacterMaster master, bool green)
        {
            if (master?.inventory == null || Run.instance == null) return;
            var drops = green ? Run.instance.availableTier2DropList : Run.instance.availableTier1DropList;
            if (drops == null || drops.Count == 0) return;
            var pickup = drops[UnityEngine.Random.Range(0, drops.Count)];
            var def = PickupCatalog.GetPickupDef(pickup);
            if (def != null && def.itemIndex != ItemIndex.None)
                master.inventory.GiveItemPermanent(def.itemIndex, 1);
        }
    }
}

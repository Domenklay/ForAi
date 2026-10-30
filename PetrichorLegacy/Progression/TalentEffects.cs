using R2API;
using RoR2;
using UnityEngine;
using UnityEngine.Networking;

namespace PetrichorLegacy.Progression
{
    public static class TalentEffects
    {
        public static void Install()
        {
            RecalculateStatsAPI.GetStatCoefficients += ApplyStats;
            Stage.onStageStartGlobal += OnStageStart;
        }

        public static void Uninstall()
        {
            RecalculateStatsAPI.GetStatCoefficients -= ApplyStats;
            Stage.onStageStartGlobal -= OnStageStart;
        }

        private static void ApplyStats(CharacterBody body, RecalculateStatsAPI.StatHookEventArgs args)
        {
            var master = body?.master;
            if (master == null) return;

            args.healthTotalMult += ServerProgressionState.Rank(master, "survival_vitality") * 0.02f;
            args.regenTotalMult += ServerProgressionState.Rank(master, "survival_recovery") * 0.04f;
            args.armorAdd += ServerProgressionState.Rank(master, "survival_armor") * 2f;
            args.baseShieldAdd += body.baseMaxHealth * ServerProgressionState.Rank(master, "survival_shield") * 0.02f;

            args.damageTotalMult += ServerProgressionState.Rank(master, "offense_power") * 0.02f;
            args.attackSpeedTotalMult += ServerProgressionState.Rank(master, "offense_frenzy") * 0.02f;
            args.critAdd += ServerProgressionState.Rank(master, "offense_precision") * 1f;
            args.allSkills.cooldownReductionMultAdd += ServerProgressionState.Rank(master, "offense_cooldown") * 0.015f;
            if (ServerProgressionState.Rank(master, "offense_executioner") > 0)
                args.critDamageMultAdd += 0.20f;

            args.moveSpeedTotalMult += ServerProgressionState.Rank(master, "mobility_stride") * 0.02f;
            args.sprintSpeedAdd += ServerProgressionState.Rank(master, "mobility_sprint") * 0.02f;
            args.jumpPowerTotalMult += ServerProgressionState.Rank(master, "mobility_jump") * 0.04f;
            args.jumpCountAdd += ServerProgressionState.Rank(master, "mobility_air");
            if (ServerProgressionState.Rank(master, "mobility_mastery") > 0)
            {
                args.moveSpeedTotalMult += 0.05f;
                args.jumpCountAdd += 1;
            }

            args.luckAdd += ServerProgressionState.Rank(master, "fortune_luck") * 0.1f;
            var scavenger = ServerProgressionState.Rank(master, "fortune_scavenger");
            args.moveSpeedTotalMult += scavenger * 0.02f;
            args.armorAdd += scavenger * 2f;
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
            var pickup = drops[UnityEngine.Random.Range(0, drops.Count)];
            var def = PickupCatalog.GetPickupDef(pickup);
            if (def != null && def.itemIndex != ItemIndex.None)
                master.inventory.GiveItem(def.itemIndex, 1);
        }
    }
}

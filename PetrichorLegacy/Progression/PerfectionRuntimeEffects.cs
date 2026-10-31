using RoR2;
using UnityEngine;

namespace PetrichorLegacy.Progression
{
    public static class PerfectionRuntimeEffects
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
            var progress = ServerProgressionState.Get(self.master);
            if (progress != null && progress.PursuitUntil > Time.fixedTime &&
                ServerProgressionState.Perfection(self.master, "perfection_pursuit") > 0)
            {
                self.moveSpeed *= 1.03f;
            }
        }
    }
}

using System;
using RoR2;
using UnityEngine;
using PetrichorLegacy.Persistence;

namespace PetrichorLegacy.Progression
{
    public static class RunTracker
    {
        private static int _bossKills;
        private static bool _awarded;
        private static bool _won;
        private static string _endingName;

        public static void Install()
        {
            Run.onRunStartGlobal += OnRunStart;
            Run.onRunDestroyGlobal += OnRunDestroy;
            GlobalEventManager.onCharacterDeathGlobal += OnCharacterDeath;
            On.RoR2.Run.BeginGameOver += Run_BeginGameOver;
        }

        public static void Uninstall()
        {
            Run.onRunStartGlobal -= OnRunStart;
            Run.onRunDestroyGlobal -= OnRunDestroy;
            GlobalEventManager.onCharacterDeathGlobal -= OnCharacterDeath;
            On.RoR2.Run.BeginGameOver -= Run_BeginGameOver;
        }

        private static void OnRunStart(Run run)
        {
            _bossKills = 0;
            _awarded = false;
            _won = false;
            _endingName = "Unknown";
            ServerProgressionState.ResetForRun();
            PetrichorLegacyPlugin.Instance.StartCoroutine(Networking.ProgressionNetwork.SendLocalProgressWhenReady());
        }

        private static void OnCharacterDeath(DamageReport report)
        {
            if (report?.victimBody != null && report.victimBody.isBoss)
                _bossKills++;
        }

        private static void Run_BeginGameOver(On.RoR2.Run.orig_BeginGameOver orig, Run self, GameEndingDef ending)
        {
            _won = ending != null && ending.isWin;
            _endingName = ending != null ? ending.cachedName : "Unknown";
            AwardIfNeeded(self);
            orig(self, ending);
        }

        private static void OnRunDestroy(Run run)
        {
            AwardIfNeeded(run);
        }

        private static void AwardIfNeeded(Run run)
        {
            if (_awarded || run == null) return;
            if (!SaveService.RefreshProfile()) return;

            _awarded = true;
            var profile = SaveService.Current;

            var stages = Mathf.Max(0, run.stageClearCount);
            var minutes = Mathf.Clamp(run.GetRunStopwatch() / 60f, 0f, 60f);
            var diffDef = DifficultyCatalog.GetDifficultyDef(run.selectedDifficulty);
            var scaling = diffDef != null ? Mathf.Max(0.5f, diffDef.scalingValue) : 1f;

            var raw = 200f + stages * 260f + _bossKills * 90f + minutes * 5f;
            var difficultyMultiplier = Mathf.Clamp(0.75f + scaling * 0.25f, 0.75f, 2.5f);
            var resultMultiplier = _won ? 1.5f : IsObliteration(_endingName) ? 1.25f : 1f;
            var xp = Mathf.Max(50, Mathf.RoundToInt(raw * difficultyMultiplier * resultMultiplier));

            profile.runsCompleted++;
            if (_won) profile.wins++;
            ProgressionService.AwardXp(profile, xp, "Итог забега");
            PetrichorLegacyPlugin.Log.LogInfo($"Run XP: +{xp} (stages={stages}, bosses={_bossKills}, win={_won}, ending={_endingName})");
        }

        private static bool IsObliteration(string endingName)
        {
            return !string.IsNullOrEmpty(endingName) && endingName.IndexOf("Obliter", StringComparison.OrdinalIgnoreCase) >= 0;
        }
    }
}

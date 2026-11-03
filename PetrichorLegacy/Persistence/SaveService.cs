using System;
using System.IO;
using BepInEx;
using PetrichorLegacy.Models;
using PetrichorLegacy.Progression;
using RoR2;
using UnityEngine;

namespace PetrichorLegacy.Persistence
{
    public static class SaveService
    {
        private static string _currentProfileKey;
        public static ProfileProgress Current { get; private set; } = new ProfileProgress();

        private static string SaveDirectory => System.IO.Path.Combine(Paths.ConfigPath, "PetrichorLegacy");

        public static bool RefreshProfile()
        {
            var local = LocalUserManager.GetFirstLocalUser();
            var profile = local?.userProfile;
            if (profile == null) return false;

            var key = string.IsNullOrWhiteSpace(profile.fileName) ? "default" : Sanitize(profile.fileName);
            if (key == _currentProfileKey) return true;

            _currentProfileKey = key;
            LoadCurrent();
            return true;
        }

        private static string CurrentPath => System.IO.Path.Combine(SaveDirectory, (_currentProfileKey ?? "default") + ".json");

        public static void LoadCurrent()
        {
            Directory.CreateDirectory(SaveDirectory);
            try
            {
                if (!File.Exists(CurrentPath))
                {
                    Current = new ProfileProgress();
                    SaveCurrent();
                    return;
                }

                var json = File.ReadAllText(CurrentPath);
                Current = JsonUtility.FromJson<ProfileProgress>(json) ?? new ProfileProgress();
                Normalize(Current);
                SaveCurrent();
            }
            catch (Exception e)
            {
                PetrichorLegacyPlugin.Log.LogError($"Failed to load progression: {e}");
                Current = new ProfileProgress();
            }
        }

        public static void SaveCurrent()
        {
            if (Current == null || string.IsNullOrEmpty(_currentProfileKey)) return;
            Directory.CreateDirectory(SaveDirectory);
            try
            {
                Normalize(Current);
                File.WriteAllText(CurrentPath, JsonUtility.ToJson(Current, true));
            }
            catch (Exception e)
            {
                PetrichorLegacyPlugin.Log.LogError($"Failed to save progression: {e}");
            }
        }

        private static void Normalize(ProfileProgress p)
        {
            p.level = Math.Max(1, p.level);
            p.currentXp = Math.Max(0, p.currentXp);
            p.unspentTalentPoints = Math.Max(0, p.unspentTalentPoints);
            p.unspentMasteryPoints = Math.Max(0, p.unspentMasteryPoints);
            p.unspentPerfectionPoints = Math.Max(0, p.unspentPerfectionPoints);
            if (p.talents == null) p.talents = new System.Collections.Generic.List<TalentRankRecord>();
            if (p.masteries == null) p.masteries = new System.Collections.Generic.List<MasteryRankRecord>();
            if (p.perfections == null) p.perfections = new System.Collections.Generic.List<PerfectionRankRecord>();
            if (p.startingLoadout == null) p.startingLoadout = new System.Collections.Generic.List<LoadoutItemRecord>();
            if (p.activeClass == null) p.activeClass = string.Empty;
            if (p.activeSpecialization == null) p.activeSpecialization = string.Empty;

            if (p.schemaVersion < 3)
            {
                var oldSpent = 0;
                foreach (var record in p.talents)
                {
                    if (record != null) oldSpent += Math.Max(0, record.rank);
                }
                p.talents.Clear();
                p.masteries.Clear();
                p.perfections.Clear();
                p.activeClass = string.Empty;
                p.activeSpecialization = string.Empty;

                p.unspentTalentPoints = Math.Max(p.unspentTalentPoints + oldSpent,
                    ProgressionService.EarnedTalentPointsForLevel(p.level));
                p.unspentMasteryPoints = Math.Max(p.unspentMasteryPoints,
                    ProgressionService.EarnedMasteryPointsForLevel(p.level));
                p.unspentPerfectionPoints = Math.Max(p.unspentPerfectionPoints,
                    ProgressionService.EarnedPerfectionPointsForLevel(p.level));
                p.startingLoadout.Clear();
                p.schemaVersion = 3;
            }
        }

        private static string Sanitize(string value)
        {
            foreach (var c in System.IO.Path.GetInvalidFileNameChars()) value = value.Replace(c, '_');
            return value;
        }
    }
}

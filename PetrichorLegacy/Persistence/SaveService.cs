using System;
using System.IO;
using BepInEx;
using PetrichorLegacy.Models;
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
            if (p.talents == null) p.talents = new System.Collections.Generic.List<TalentRankRecord>();
            if (p.startingLoadout == null) p.startingLoadout = new System.Collections.Generic.List<LoadoutItemRecord>();
        }

        private static string Sanitize(string value)
        {
            foreach (var c in System.IO.Path.GetInvalidFileNameChars()) value = value.Replace(c, '_');
            return value;
        }
    }
}

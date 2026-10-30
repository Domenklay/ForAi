using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using PetrichorLegacy.Networking;
using PetrichorLegacy.Persistence;
using PetrichorLegacy.Progression;
using PetrichorLegacy.UI;
using UnityEngine;

namespace PetrichorLegacy
{
    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    [BepInDependency(R2API.RecalculateStatsAPI.PluginGUID)]
    [BepInDependency(R2API.Networking.NetworkingAPI.PluginGUID)]
    public sealed class PetrichorLegacyPlugin : BaseUnityPlugin
    {
        public const string PluginGuid = "com.petrichorlegacy.metaprogression";
        public const string PluginName = "Petrichor Legacy";
        public const string PluginVersion = "0.1.0";

        public static PetrichorLegacyPlugin Instance { get; private set; }
        public static ManualLogSource Log { get; private set; }

        private MetaProgressionUI _ui;
        private ConfigEntry<KeyboardShortcut> _toggleKey;

        private void Awake()
        {
            Instance = this;
            Log = Logger;
            _toggleKey = Config.Bind("UI", "ToggleKey", new KeyboardShortcut(KeyCode.M), "Open meta progression in the character-select lobby.");

            ProgressionNetwork.Register();
            RunTracker.Install();
            TalentEffects.Install();

            _ui = gameObject.AddComponent<MetaProgressionUI>();
            _ui.Configure(_toggleKey);

            SaveService.RefreshProfile();
            Logger.LogInfo($"{PluginName} {PluginVersion} loaded.");
        }

        private void OnDestroy()
        {
            SaveService.SaveCurrent();
            RunTracker.Uninstall();
            TalentEffects.Uninstall();
        }
    }
}

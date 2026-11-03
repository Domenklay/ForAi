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
    public sealed class PetrichorLegacyPlugin : BaseUnityPlugin
    {
        public const string PluginGuid = "com.petrichorlegacy.metaprogression";
        public const string PluginName = "Petrichor Legacy";
        public const string PluginVersion = "0.4.0";

        public static PetrichorLegacyPlugin Instance { get; private set; }
        public static ManualLogSource Log { get; private set; }

        private MetaProgressionUIV5 _ui;
        private ConfigEntry<KeyboardShortcut> _toggleKey;

        private void Awake()
        {
            Instance = this;
            Log = Logger;
            _toggleKey = Config.Bind("UI", "ToggleKey", new KeyboardShortcut(KeyCode.M), "Open meta progression UI.");

            ProgressionNetwork.Register();
            RunTracker.Install();
            TalentEffects.Install();
            AdditionalSpecEffects.Install();
            CapstoneRewardSystem.Install();
            PerfectionRuntimeEffects.Install();
            MonsterRaritySystem.Install();

            _ui = gameObject.AddComponent<MetaProgressionUIV5>();
            _ui.Configure(_toggleKey);

            SaveService.RefreshProfile();
            Logger.LogInfo($"{PluginName} Infinite Progression {PluginVersion} loaded. Press M to open the progression window.");
        }

        private void OnDestroy()
        {
            SaveService.SaveCurrent();
            MonsterRaritySystem.Uninstall();
            PerfectionRuntimeEffects.Uninstall();
            CapstoneRewardSystem.Uninstall();
            AdditionalSpecEffects.Uninstall();
            RunTracker.Uninstall();
            TalentEffects.Uninstall();
        }
    }
}

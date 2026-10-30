using System.Collections.Generic;
using RoR2;

namespace PetrichorLegacy.Progression
{
    public sealed class ValidatedProgress
    {
        public int Level;
        public readonly Dictionary<string, int> Talents = new Dictionary<string, int>();
        public bool LoadoutApplied;
        public bool ProspectorGranted;
    }

    public static class ServerProgressionState
    {
        private static readonly Dictionary<uint, ValidatedProgress> ByMaster = new Dictionary<uint, ValidatedProgress>();

        public static void ResetForRun() => ByMaster.Clear();

        public static void Set(CharacterMaster master, ValidatedProgress progress)
        {
            if (master == null || progress == null) return;
            ByMaster[master.netId.Value] = progress;
        }

        public static ValidatedProgress Get(CharacterMaster master)
        {
            if (master == null) return null;
            return ByMaster.TryGetValue(master.netId.Value, out var p) ? p : null;
        }

        public static int Rank(CharacterMaster master, string id)
        {
            var p = Get(master);
            return p != null && p.Talents.TryGetValue(id, out var rank) ? rank : 0;
        }

        public static IEnumerable<KeyValuePair<uint, ValidatedProgress>> All => ByMaster;
    }
}

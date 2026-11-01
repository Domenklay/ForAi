using System.Collections.Generic;
using RoR2;

namespace PetrichorLegacy.Progression
{
    public sealed class ValidatedProgress
    {
        public int Level;
        public string ActiveClass = string.Empty;
        public string ActiveSpecialization = string.Empty;
        public readonly Dictionary<string, int> Talents = new Dictionary<string, int>();
        public readonly Dictionary<string, int> Masteries = new Dictionary<string, int>();
        public readonly Dictionary<string, int> Perfections = new Dictionary<string, int>();
        public bool LoadoutApplied;
        public bool ProspectorGranted;
        public bool ProspectorLegendWhiteGranted;
        public bool ProspectorMythGreenGranted;
        public int LastGreatHuntStage = -1;
        public float HunterHasteUntil;
        public float PursuitUntil;
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
            if (p == null || !p.Talents.TryGetValue(id, out var rank)) return 0;
            var def = TalentCatalog.Find(id);
            return def != null && IsBranchActive(p, def.Branch) ? rank : 0;
        }
        public static int MasteryRank(CharacterMaster master, string id)
        {
            var p = Get(master);
            if (p == null || !p.Masteries.TryGetValue(id, out var rank)) return 0;
            var def = MasteryCatalog.Find(id);
            return def != null && def.ClassId == p.ActiveClass ? rank : 0;
        }
        public static float MasteryValue(CharacterMaster master, string id)
        {
            var def = MasteryCatalog.Find(id);
            if (def == null) return 0f;
            return MasteryCatalog.EffectiveRanks(MasteryRank(master, id)) * def.PerRank;
        }
        public static int Perfection(CharacterMaster master, string id)
        {
            var p = Get(master);
            return p != null && p.Perfections.TryGetValue(id, out var rank) ? rank : 0;
        }
        public static bool IsBranchActive(ValidatedProgress p, TalentBranch branch)
        {
            if (branch == TalentBranch.Legacy) return true;
            if (p == null) return false;
            var classId = TalentCatalog.ClassForBranch(branch);
            if (p.ActiveClass != classId) return false;
            var specId = TalentCatalog.SpecForBranch(branch);
            return string.IsNullOrEmpty(specId) || p.ActiveSpecialization == specId;
        }
        public static IEnumerable<KeyValuePair<uint, ValidatedProgress>> All => ByMaster;
    }
}

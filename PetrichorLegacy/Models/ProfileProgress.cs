using System;
using System.Collections.Generic;

namespace PetrichorLegacy.Models
{
    [Serializable]
    public sealed class ProfileProgress
    {
        public int schemaVersion = 3;
        public int level = 1;
        public int currentXp = 0;
        public long lifetimeXp = 0;
        public int unspentTalentPoints = 0;
        public int unspentMasteryPoints = 0;
        public int unspentPerfectionPoints = 0;
        public int runsCompleted = 0;
        public int wins = 0;

        public string activeClass = string.Empty;
        public string activeSpecialization = string.Empty;

        public List<TalentRankRecord> talents = new List<TalentRankRecord>();
        public List<MasteryRankRecord> masteries = new List<MasteryRankRecord>();
        public List<PerfectionRankRecord> perfections = new List<PerfectionRankRecord>();
        public List<LoadoutItemRecord> startingLoadout = new List<LoadoutItemRecord>();
    }

    [Serializable]
    public sealed class TalentRankRecord
    {
        public string id;
        public int rank;
    }

    [Serializable]
    public sealed class MasteryRankRecord
    {
        public string id;
        public int rank;
    }

    [Serializable]
    public sealed class PerfectionRankRecord
    {
        public string id;
        public int rank;
    }

    [Serializable]
    public sealed class LoadoutItemRecord
    {
        public string itemName;
        public int count;
    }
}

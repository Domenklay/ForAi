using System;
using System.Collections.Generic;

namespace PetrichorLegacy.Models
{
    [Serializable]
    public sealed class ProfileProgress
    {
        public int schemaVersion = 1;
        public int level = 1;
        public int currentXp = 0;
        public long lifetimeXp = 0;
        public int unspentTalentPoints = 0;
        public int runsCompleted = 0;
        public int wins = 0;
        public List<TalentRankRecord> talents = new List<TalentRankRecord>();
        public List<LoadoutItemRecord> startingLoadout = new List<LoadoutItemRecord>();
    }

    [Serializable]
    public sealed class TalentRankRecord
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

from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
base = root / "PetrichorLegacy"


def rw(rel):
    p = base / rel
    return p, p.read_text(encoding="utf-8")


def save(p, text):
    p.write_text(text, encoding="utf-8")


# ---------- Mastery: class milestones use effective ranks; disciplines have 10/25/50/100 thresholds ----------
p, t = rw("Progression/MasteryCatalog.cs")
t = re.sub(r'new MasteryMilestoneDef\("([^"]+)", 75,', r'new MasteryMilestoneDef("\1", 60,', t)
t = re.sub(r'new MasteryMilestoneDef\("([^"]+)", 150,', r'new MasteryMilestoneDef("\1", 120,', t)
t = re.sub(r'new MasteryMilestoneDef\("([^"]+)", 300,', r'new MasteryMilestoneDef("\1", 220,', t)

anchor = '''        public static IEnumerable<MasteryMilestoneDef> MilestonesFor(string classId) =>
            Milestones.Where(x => string.Equals(x.ClassId, classId, StringComparison.OrdinalIgnoreCase)).OrderBy(x => x.RequiredRanks);

        public static float EffectiveRanks(int rank)'''
if anchor not in t:
    raise RuntimeError("Mastery milestone anchor not found")
insert = r'''        public static IEnumerable<MasteryMilestoneDef> MilestonesFor(string classId) =>
            Milestones.Where(x => string.Equals(x.ClassId, classId, StringComparison.OrdinalIgnoreCase)).OrderBy(x => x.RequiredRanks);

        public static readonly int[] DisciplineThresholds = { 10, 25, 50, 100 };

        public static float TotalEffectiveRanks(ProfileProgress profile, string classId)
        {
            if (profile?.masteries == null || string.IsNullOrEmpty(classId)) return 0f;
            var total = 0f;
            foreach (var r in profile.masteries)
            {
                if (r == null || r.rank <= 0) continue;
                var def = Find(r.id);
                if (def != null && def.ClassId == classId) total += EffectiveRanks(r.rank);
            }
            return total;
        }

        public static float DisciplineMultiplier(int rank)
        {
            var mult = 1f;
            if (rank >= 10) mult += 0.05f;
            if (rank >= 25) mult += 0.075f;
            if (rank >= 50) mult += 0.10f;
            if (rank >= 100) mult += 0.125f;
            return mult;
        }

        public static string DisciplineMilestoneText(MasteryDef def, int threshold)
        {
            if (def == null) return string.Empty;
            if (threshold == 10) return "Практика: сила дисциплины +5%.";
            if (threshold == 25) return "Специализация: ещё +7.5%.";
            if (threshold == 50) return "Эксперт: ещё +10%.";
            if (threshold == 100) return "Совершенное владение: ещё +12.5%; " + SignatureText(def.Id);
            return string.Empty;
        }

        public static string SignatureText(string id)
        {
            switch (id)
            {
                case "mastery_guardian_hp": return "+2% максимального здоровья.";
                case "mastery_guardian_armor": return "+2 брони.";
                case "mastery_guardian_regen": return "в начале стадии восстановить ещё 3% здоровья.";
                case "mastery_guardian_shield": return "в начале стадии получить барьер 5% здоровья.";

                case "mastery_slayer_damage": return "+3% урона боссам и особым монстрам.";
                case "mastery_slayer_attack": return "+2% скорости атаки.";
                case "mastery_slayer_cooldown": return "ещё -1% восстановления навыков.";
                case "mastery_slayer_crit": return "+1% критического шанса.";

                case "mastery_path_move": return "+2% скорости движения.";
                case "mastery_path_sprint": return "+1 броня во время спринта.";
                case "mastery_path_jump": return "+1 дополнительный прыжок.";
                case "mastery_path_control": return "ещё -1% восстановления навыков.";

                case "mastery_seeker_gold": return "ещё +10% золота с особых монстров.";
                case "mastery_seeker_specialxp": return "ещё +10% мета-XP с особых монстров.";
                case "mastery_seeker_stagegold": return "+20 золота на каждой следующей стадии.";
                case "mastery_seeker_startgold": return "+30 золота в начале забега.";

                case "mastery_arcanist_damage": return "+3% урона боссам и особым монстрам.";
                case "mastery_arcanist_attack": return "+2% скорости атаки.";
                case "mastery_arcanist_cooldown": return "ещё -1.5% восстановления навыков.";
                case "mastery_arcanist_move": return "+2% скорости движения.";

                case "mastery_tech_attack": return "+2% скорости атаки владельца.";
                case "mastery_tech_move": return "+2% скорости движения владельца.";
                case "mastery_tech_minion_damage": return "+8% урона миньонов.";
                case "mastery_tech_minion_health": return "+8% здоровья миньонов.";

                case "mastery_commander_damage": return "+2% урона боссам и особым монстрам.";
                case "mastery_commander_move": return "+1.5% скорости движения и +1 броня.";
                case "mastery_commander_armor": return "+2 брони.";
                case "mastery_commander_minion": return "+5% урона и здоровья миньонов.";
                default: return "открывается финальный бонус дисциплины.";
            }
        }

        public static float EffectiveRanks(int rank)'''
t = t.replace(anchor, insert, 1)

old_value = '''            return EffectiveRanks(GetRank(profile, id)) * def.PerRank;'''
new_value = '''            var rank = GetRank(profile, id);
            return EffectiveRanks(rank) * def.PerRank * DisciplineMultiplier(rank);'''
if old_value not in t:
    raise RuntimeError("Mastery Value line not found")
t = t.replace(old_value, new_value, 1)
save(p, t)


# ---------- Server-side mastery helpers ----------
p, t = rw("Progression/ServerProgressionState.cs")
old_value = '''            return MasteryCatalog.EffectiveRanks(MasteryRank(master, id)) * def.PerRank;'''
new_value = '''            var rank = MasteryRank(master, id);
            return MasteryCatalog.EffectiveRanks(rank) * def.PerRank * MasteryCatalog.DisciplineMultiplier(rank);'''
if old_value not in t:
    raise RuntimeError("Server MasteryValue line not found")
t = t.replace(old_value, new_value, 1)

raw_total = '''        public static int MasteryTotalRanks(CharacterMaster master)
        {
            var p = Get(master);
            if (p == null || string.IsNullOrEmpty(p.ActiveClass)) return 0;
            var total = 0;
            foreach (var kv in p.Masteries)
            {
                var def = MasteryCatalog.Find(kv.Key);
                if (def != null && def.ClassId == p.ActiveClass) total += Math.Max(0, kv.Value);
            }
            return total;
        }'''
if raw_total not in t:
    raise RuntimeError("MasteryTotalRanks block not found")
t = t.replace(raw_total, raw_total + r'''
        public static float MasteryTotalEffectiveRanks(CharacterMaster master)
        {
            var p = Get(master);
            if (p == null || string.IsNullOrEmpty(p.ActiveClass)) return 0f;
            var total = 0f;
            foreach (var kv in p.Masteries)
            {
                var def = MasteryCatalog.Find(kv.Key);
                if (def != null && def.ClassId == p.ActiveClass)
                    total += MasteryCatalog.EffectiveRanks(Math.Max(0, kv.Value));
            }
            return total;
        }''', 1)
save(p, t)


# ---------- Infinite Prestige: automatic five-step cycle every 100 levels ----------
prestige = r'''using System;

namespace PetrichorLegacy.Progression
{
    public static class PrestigeCatalog
    {
        public static int RankForLevel(int level) => Math.Max(0, level / 100);
        public static int NextLevel(int level) => (RankForLevel(level) + 1) * 100;
        public static int Step(int rank) => rank <= 0 ? 0 : ((rank - 1) % 5) + 1;
        public static int Cycle(int rank) => rank <= 0 ? 0 : ((rank - 1) / 5) + 1;

        private static int StepStacks(int rank, int step)
        {
            if (rank < step || step < 1 || step > 5) return 0;
            return 1 + (rank - step) / 5;
        }

        public static int StacksForStep(int level, int step) => StepStacks(RankForLevel(level), step);
        public static float SpecialXpBonus(int level) => StepStacks(RankForLevel(level), 1) * 0.02f;
        public static int StartingGoldBonus(int level) => StepStacks(RankForLevel(level), 2) * 10;
        public static float SpecialGoldBonus(int level) => StepStacks(RankForLevel(level), 3) * 0.05f;
        public static float HunterDamageBonus(int level) => StepStacks(RankForLevel(level), 4) * 0.02f;
        public static int ArsenalCapacityBonus(int level) => StepStacks(RankForLevel(level), 5);

        public static string RewardName(int step)
        {
            switch (step)
            {
                case 1: return "Летопись охоты";
                case 2: return "Ветеранский запас";
                case 3: return "Право трофея";
                case 4: return "Печать охотника";
                case 5: return "Хартия Арсенала";
                default: return "Престиж";
            }
        }

        public static string RewardDescription(int step)
        {
            switch (step)
            {
                case 1: return "+2% мета-XP с особых монстров.";
                case 2: return "+10 стартового золота.";
                case 3: return "+5% золота с особых монстров.";
                case 4: return "+2% урона боссам и особым монстрам.";
                case 5: return "+1 вместимость Арсенала.";
                default: return string.Empty;
            }
        }
    }
}
'''
save(base / "Progression" / "PrestigeCatalog.cs", prestige)


# ---------- Runtime: effective class milestones + rank-100 discipline signatures + Prestige combat ----------
p, t = rw("Progression/PerfectionRuntimeEffects.cs")
t = t.replace('ServerProgressionState.MasteryTotalRanks(self.master)', 'ServerProgressionState.MasteryTotalEffectiveRanks(self.master)')
t = t.replace('ServerProgressionState.MasteryTotalRanks(attacker.master)', 'ServerProgressionState.MasteryTotalEffectiveRanks(attacker.master)')
t = t.replace('ServerProgressionState.MasteryTotalRanks(master)', 'ServerProgressionState.MasteryTotalEffectiveRanks(master)')
t = t.replace('total >= 75', 'total >= 60')
t = t.replace('total >= 150', 'total >= 120')
t = t.replace('total >= 300', 'total >= 220')

switch_anchor = '''            switch (progress.ActiveClass)
            {'''
if switch_anchor not in t:
    raise RuntimeError("Mastery class switch not found")
signatures = r'''            if (ServerProgressionState.MasteryRank(self.master, "mastery_guardian_hp") >= 100) self.maxHealth *= 1.02f;
            if (ServerProgressionState.MasteryRank(self.master, "mastery_guardian_armor") >= 100) self.armor += 2f;

            if (ServerProgressionState.MasteryRank(self.master, "mastery_slayer_attack") >= 100) self.attackSpeed *= 1.02f;
            if (ServerProgressionState.MasteryRank(self.master, "mastery_slayer_cooldown") >= 100) ApplyCooldownScale(self.skillLocator, 0.01f);
            if (ServerProgressionState.MasteryRank(self.master, "mastery_slayer_crit") >= 100) self.crit += 1f;

            if (ServerProgressionState.MasteryRank(self.master, "mastery_path_move") >= 100) self.moveSpeed *= 1.02f;
            if (ServerProgressionState.MasteryRank(self.master, "mastery_path_sprint") >= 100 && self.isSprinting) self.armor += 1f;
            if (ServerProgressionState.MasteryRank(self.master, "mastery_path_jump") >= 100) self.maxJumpCount += 1;
            if (ServerProgressionState.MasteryRank(self.master, "mastery_path_control") >= 100) ApplyCooldownScale(self.skillLocator, 0.01f);

            if (ServerProgressionState.MasteryRank(self.master, "mastery_arcanist_attack") >= 100) self.attackSpeed *= 1.02f;
            if (ServerProgressionState.MasteryRank(self.master, "mastery_arcanist_cooldown") >= 100) ApplyCooldownScale(self.skillLocator, 0.015f);
            if (ServerProgressionState.MasteryRank(self.master, "mastery_arcanist_move") >= 100) self.moveSpeed *= 1.02f;

            if (ServerProgressionState.MasteryRank(self.master, "mastery_tech_attack") >= 100) self.attackSpeed *= 1.02f;
            if (ServerProgressionState.MasteryRank(self.master, "mastery_tech_move") >= 100) self.moveSpeed *= 1.02f;

            if (ServerProgressionState.MasteryRank(self.master, "mastery_commander_move") >= 100) { self.moveSpeed *= 1.015f; self.armor += 1f; }
            if (ServerProgressionState.MasteryRank(self.master, "mastery_commander_armor") >= 100) self.armor += 2f;

            switch (progress.ActiveClass)
            {'''
t = t.replace(switch_anchor, signatures, 1)

damage_anchor = '''                var progress = ServerProgressionState.Get(attacker.master);
                if (progress != null && progress.ActiveClass == "Slayer"'''
if damage_anchor not in t:
    raise RuntimeError("Damage mastery anchor not found")
damage_new = r'''                var progress = ServerProgressionState.Get(attacker.master);
                var specialTarget = victim.isBoss || victim.GetComponent<MonsterRarityMarker>() != null;
                if (specialTarget)
                {
                    var prestigeDamage = progress != null ? PrestigeCatalog.HunterDamageBonus(progress.Level) : 0f;
                    if (prestigeDamage > 0f) damageInfo.damage *= 1f + prestigeDamage;
                    if (ServerProgressionState.MasteryRank(attacker.master, "mastery_slayer_damage") >= 100) damageInfo.damage *= 1.03f;
                    if (ServerProgressionState.MasteryRank(attacker.master, "mastery_arcanist_damage") >= 100) damageInfo.damage *= 1.03f;
                    if (ServerProgressionState.MasteryRank(attacker.master, "mastery_commander_damage") >= 100) damageInfo.damage *= 1.02f;
                }
                if (progress != null && progress.ActiveClass == "Slayer"'''
t = t.replace(damage_anchor, damage_new, 1)

stage_anchor = '''                var gold = 0f;'''
if stage_anchor not in t:
    raise RuntimeError("Stage gold anchor not found")
t = t.replace(stage_anchor, r'''                if (ServerProgressionState.MasteryRank(master, "mastery_guardian_regen") >= 100)
                    body.healthComponent.HealFraction(0.03f, default(ProcChainMask));
                if (ServerProgressionState.MasteryRank(master, "mastery_guardian_shield") >= 100)
                    body.healthComponent.AddBarrier(body.maxHealth * 0.05f);

                var gold = 0f;''', 1)

gold_award = '''                if (gold > 0f) master.GiveMoney((uint)Mathf.RoundToInt(gold));'''
if gold_award not in t:
    raise RuntimeError("Stage gold award not found")
t = t.replace(gold_award, r'''                if (stageIndex > 0 && ServerProgressionState.MasteryRank(master, "mastery_seeker_stagegold") >= 100) gold += 20f;
                if (stageIndex == 0 && ServerProgressionState.MasteryRank(master, "mastery_seeker_startgold") >= 100) gold += 30f;
                if (gold > 0f) master.GiveMoney((uint)Mathf.RoundToInt(gold));''', 1)
save(p, t)


# ---------- Minions: effective class milestones + rank-100 signatures ----------
p, t = rw("Progression/AdditionalSpecEffects.cs")
t = t.replace('ServerProgressionState.MasteryTotalRanks(owner)', 'ServerProgressionState.MasteryTotalEffectiveRanks(owner)')
t = t.replace('masteryTotal >= 75', 'masteryTotal >= 60')
t = t.replace('masteryTotal >= 150', 'masteryTotal >= 120')
t = t.replace('masteryTotal >= 300', 'masteryTotal >= 220')
anchor = '''                var ownerProgress = ServerProgressionState.Get(owner);'''
if anchor not in t:
    raise RuntimeError("Minion ownerProgress anchor not found")
t = t.replace(anchor, r'''                if (ServerProgressionState.MasteryRank(owner, "mastery_tech_minion_damage") >= 100) dmg += 0.08f;
                if (ServerProgressionState.MasteryRank(owner, "mastery_tech_minion_health") >= 100) hp += 0.08f;
                if (ServerProgressionState.MasteryRank(owner, "mastery_commander_minion") >= 100) { dmg += 0.05f; hp += 0.05f; }
                var ownerProgress = ServerProgressionState.Get(owner);''', 1)
save(p, t)


# ---------- Special-enemy rewards: effective Seeker milestones + rank-100 signatures + Prestige ----------
p, t = rw("Progression/MonsterRaritySystem.cs")
t = t.replace('var masteryTotal = ServerProgressionState.MasteryTotalRanks(report.attackerMaster);',
              'var masteryTotal = ServerProgressionState.MasteryTotalEffectiveRanks(report.attackerMaster);')
t = t.replace('masteryTotal >= 75', 'masteryTotal >= 60')
t = t.replace('masteryTotal >= 150', 'masteryTotal >= 120')
t = t.replace('masteryTotal >= 300', 'masteryTotal >= 220')

active_anchor = '''            var activeProgress = ServerProgressionState.Get(report.attackerMaster);'''
if active_anchor not in t:
    raise RuntimeError("Active progression rarity anchor not found")
t = t.replace(active_anchor, active_anchor + r'''
            if (activeProgress != null) xpMultiplier += PrestigeCatalog.SpecialXpBonus(activeProgress.Level);
            if (ServerProgressionState.MasteryRank(report.attackerMaster, "mastery_seeker_specialxp") >= 100) xpMultiplier += 0.10f;''', 1)

gold_anchor = '''            var goldMultiplier = 1f;'''
if gold_anchor not in t:
    raise RuntimeError("Gold multiplier anchor not found")
t = t.replace(gold_anchor, gold_anchor + r'''
            if (activeProgress != null) goldMultiplier += PrestigeCatalog.SpecialGoldBonus(activeProgress.Level);
            if (ServerProgressionState.MasteryRank(report.attackerMaster, "mastery_seeker_gold") >= 100) goldMultiplier += 0.10f;''', 1)
save(p, t)


# ---------- Prestige start gold ----------
p, t = rw("Networking/ProgressionNetwork.cs")
start_anchor = '''            var startGold = 0f;'''
if start_anchor not in t:
    raise RuntimeError("Start gold anchor not found")
t = t.replace(start_anchor, start_anchor + r'''
            startGold += PrestigeCatalog.StartingGoldBonus(progress.Level);''', 1)
save(p, t)


# ---------- Prestige Arsenal capacity ----------
p, t = rw("Progression/ProgressionService.cs")
cap_anchor = '''            capacity += PerfectionCatalog.GetRank(profile, "perfection_prestige_treasurer");
            return capacity;'''
if cap_anchor not in t:
    raise RuntimeError("Starting capacity anchor not found")
t = t.replace(cap_anchor, '''            capacity += PerfectionCatalog.GetRank(profile, "perfection_prestige_treasurer");
            capacity += PrestigeCatalog.ArsenalCapacityBonus(profile.level);
            return capacity;''', 1)
save(p, t)


# ---------- UI: effective mastery + readable discipline thresholds + Prestige strip ----------
p, ui = rw("UI/MetaProgressionUIV5.cs")
ui = ui.replace('var total = MasteryCatalog.TotalRanks(p, p.activeClass);',
                'var total = MasteryCatalog.TotalEffectiveRanks(p, p.activeClass);', 1)
ui = ui.replace('$"{ClassDisplay(p.activeClass).ToUpperInvariant()} • суммарный ранг {total}"',
                '$"{ClassDisplay(p.activeClass).ToUpperInvariant()} • эффективное мастерство {total:0.#}"', 1)
ui = ui.replace('"Бесконечные дисциплины активного класса. После 25 / 50 / 100 / 200 рангов новые ранги дают меньше силы."',
                '"Дисциплины бесконечны; классовые рубежи считаются по эффективным рангам. Личные рубежи дисциплины: 10 / 25 / 50 / 100."', 1)
ui = ui.replace('var cardH = 220f;', 'var cardH = 320f;', 1)

footer = '''            GUI.Label(new Rect(rect.x + 10f, rect.y + 139f, rect.width - 20f, 20f), $"Эффективных рангов: {MasteryCatalog.EffectiveRanks(rank):0.##}", _tiny);

            var buttonY = rect.yMax - 45f;'''
if footer not in ui:
    raise RuntimeError("Mastery card footer not found")
footer_new = r'''            GUI.Label(new Rect(rect.x + 10f, rect.y + 139f, rect.width - 20f, 20f), $"Эффективных рангов: {MasteryCatalog.EffectiveRanks(rank):0.##} • сила дисциплины ×{MasteryCatalog.DisciplineMultiplier(rank):0.###}", _tiny);

            var milestoneY = rect.y + 164f;
            for (var i = 0; i < MasteryCatalog.DisciplineThresholds.Length; i++)
            {
                var req = MasteryCatalog.DisciplineThresholds[i];
                var reached = rank >= req;
                var mr = new Rect(rect.x + 10f, milestoneY + i * 24f, rect.width - 20f, 21f);
                FillRect(mr, reached ? new Color(0.045f, 0.12f, 0.095f, 1f) : new Color(0.027f, 0.032f, 0.036f, 1f));
                DrawBorder(mr, reached ? new Color(0.22f, 0.62f, 0.45f, 1f) : new Color(0.14f, 0.18f, 0.20f, 1f), 1f);
                GUI.Label(new Rect(mr.x + 5f, mr.y + 1f, 42f, 18f), req.ToString(), _center);
                GUI.Label(new Rect(mr.x + 50f, mr.y + 1f, mr.width - 55f, 18f), MasteryCatalog.DisciplineMilestoneText(def, req), _tiny);
            }

            var buttonY = rect.yMax - 45f;'''
ui = ui.replace(footer, footer_new, 1)

perf_anchor = '''            GUI.Label(new Rect(area.x + 12f, area.y + 35f, area.width - 24f, 21f), "Направления можно сочетать. Высокие узлы требуют предыдущего узла в своей цепочке.", _small);

            var viewport = new Rect(area.x + 6f, area.y + 62f, area.width - 12f, area.height - 68f);'''
if perf_anchor not in ui:
    raise RuntimeError("Perfection viewport anchor not found")
prestige_panel = r'''            GUI.Label(new Rect(area.x + 12f, area.y + 35f, area.width - 24f, 21f), "Направления можно сочетать. Высокие узлы требуют предыдущего узла в своей цепочке.", _small);

            var prestigeRank = PrestigeCatalog.RankForLevel(p.level);
            var prestigePanel = new Rect(area.x + 8f, area.y + 60f, area.width - 16f, 112f);
            FillRect(prestigePanel, new Color(0.027f, 0.022f, 0.040f, 1f));
            DrawBorder(prestigePanel, new Color(0.48f, 0.34f, 0.67f, 1f), 1f);
            GUI.Label(new Rect(prestigePanel.x + 10f, prestigePanel.y + 5f, 320f, 24f), $"ПРЕСТИЖ {prestigeRank} • следующий: ур. {PrestigeCatalog.NextLevel(p.level)}", _header);
            GUI.Label(new Rect(prestigePanel.x + 330f, prestigePanel.y + 6f, prestigePanel.width - 340f, 22f), "Каждые 5 ступеней цикл начинается заново и награды складываются.", _small);

            var cycle = Mathf.Max(1, PrestigeCatalog.Cycle(Mathf.Max(1, prestigeRank)));
            var pw = (prestigePanel.width - 20f) / 5f;
            for (var step = 1; step <= 5; step++)
            {
                var stacks = PrestigeCatalog.StacksForStep(p.level, step);
                var active = stacks > 0;
                var rr = new Rect(prestigePanel.x + 8f + (step - 1) * pw, prestigePanel.y + 34f, pw - 5f, 70f);
                FillRect(rr, active ? new Color(0.095f, 0.060f, 0.13f, 1f) : new Color(0.030f, 0.030f, 0.038f, 1f));
                DrawBorder(rr, active ? new Color(0.62f, 0.42f, 0.82f, 1f) : new Color(0.16f, 0.16f, 0.20f, 1f), active ? 2f : 1f);
                GUI.Label(new Rect(rr.x + 4f, rr.y + 3f, rr.width - 8f, 18f), $"ур. {(cycle - 1) * 500 + step * 100} • {PrestigeCatalog.RewardName(step)}", _tiny);
                GUI.Label(new Rect(rr.x + 4f, rr.y + 22f, rr.width - 8f, 43f), PrestigeCatalog.RewardDescription(step) + (active ? $"  ×{stacks}" : string.Empty), _tiny);
            }

            var viewport = new Rect(area.x + 6f, area.y + 180f, area.width - 12f, area.height - 186f);'''
ui = ui.replace(perf_anchor, prestige_panel, 1)
save(p, ui)


# ---------- Version ----------
p, t = rw("Plugin.cs")
t = t.replace('public const string PluginVersion = "0.7.0";', 'public const string PluginVersion = "0.7.1";')
save(p, t)

p, t = rw("manifest.json")
t = t.replace('"version_number": "0.7.0"', '"version_number": "0.7.1"')
save(p, t)

p, t = rw("PetrichorLegacy.csproj")
t = t.replace('<Version>0.7.0</Version>', '<Version>0.7.1</Version>')
save(p, t)

print("Applied PetrichorLegacy 0.7.1 effective mastery and infinite prestige")

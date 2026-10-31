using System;
using System.Collections.Generic;
using System.Linq;
using BepInEx.Configuration;
using PetrichorLegacy.Loadout;
using PetrichorLegacy.Models;
using PetrichorLegacy.Persistence;
using PetrichorLegacy.Progression;
using RoR2;
using UnityEngine;

namespace PetrichorLegacy.UI
{
    public sealed class MetaProgressionUIV5 : MonoBehaviour
    {
        private Rect _window = new Rect(28f, 24f, 1540f, 920f);
        private bool _open;
        private int _tab;
        private TalentBranch _selectedBranch = TalentBranch.Legacy;
        private string _pendingSpecId = string.Empty;
        private Vector2 _treeScroll;
        private Vector2 _masteryScroll;
        private Vector2 _perfectionScroll;
        private Vector2 _itemScroll;
        private Vector2 _selectedItemScroll;
        private string _search = string.Empty;
        private int _itemFilter;
        private string _status = string.Empty;
        private float _statusUntil;
        private ConfigEntry<KeyboardShortcut> _toggleKey;

        private bool _cursorCaptured;
        private bool _previousCursorVisible;
        private CursorLockMode _previousCursorLock;

        private GUIStyle _windowStyle;
        private GUIStyle _header;
        private GUIStyle _small;
        private GUIStyle _tiny;
        private GUIStyle _nodeTitle;
        private GUIStyle _nodeEffect;
        private GUIStyle _center;
        private GUIStyle _hud;
        private GUIStyle _tileLabel;
        private Texture2D _windowTexture;
        private readonly PickupIconResolver _iconResolver = new PickupIconResolver();

        public void Configure(ConfigEntry<KeyboardShortcut> toggleKey) => _toggleKey = toggleKey;

        private void Update()
        {
            SaveService.RefreshProfile();
            if (_toggleKey != null && _toggleKey.Value.IsDown()) SetOpen(!_open);
            if (_open)
            {
                Cursor.visible = true;
                Cursor.lockState = CursorLockMode.None;
            }
        }

        private void OnDestroy()
        {
            RestoreCursor();
            _iconResolver.Dispose();
            if (_windowTexture != null) Destroy(_windowTexture);
        }

        private void SetOpen(bool open)
        {
            if (_open == open) return;
            _open = open;
            if (open)
            {
                if (!_cursorCaptured)
                {
                    _previousCursorVisible = Cursor.visible;
                    _previousCursorLock = Cursor.lockState;
                    _cursorCaptured = true;
                }
                Cursor.visible = true;
                Cursor.lockState = CursorLockMode.None;
            }
            else RestoreCursor();
        }

        private void RestoreCursor()
        {
            if (!_cursorCaptured) return;
            Cursor.visible = _previousCursorVisible;
            Cursor.lockState = _previousCursorLock;
            _cursorCaptured = false;
        }

        private void OnGUI()
        {
            EnsureStyles();
            if (Run.instance != null && SaveService.Current != null) DrawXpHud();
            if (!_open || SaveService.Current == null) return;

            _window.width = Mathf.Min(1560f, Mathf.Max(960f, Screen.width - 18f));
            _window.height = Mathf.Min(940f, Mathf.Max(660f, Screen.height - 18f));
            _window.x = Mathf.Clamp(_window.x, 0f, Mathf.Max(0f, Screen.width - _window.width));
            _window.y = Mathf.Clamp(_window.y, 0f, Mathf.Max(0f, Screen.height - _window.height));
            _window = GUI.Window(941208, _window, DrawWindow, "PETRICHOR LEGACY — META PROGRESSION", _windowStyle);
            GUI.BringWindowToFront(941208);
        }

        private void DrawXpHud()
        {
            var p = SaveService.Current;
            var required = Mathf.Max(1, ProgressionService.XpRequiredForNextLevel(p.level));
            var fraction = Mathf.Clamp01((float)p.currentXp / required);
            var width = Mathf.Clamp(Screen.width * 0.15f, 205f, 270f);
            var outer = new Rect(8f, 12f, width, 20f);
            FillRect(outer, new Color(0.01f, 0.014f, 0.018f, 0.95f));
            var inner = new Rect(outer.x + 2f, outer.y + 2f, outer.width - 4f, outer.height - 4f);
            FillRect(new Rect(inner.x, inner.y, inner.width * fraction, inner.height), new Color(0.10f, 0.48f, 0.68f, 0.96f));
            DrawBorder(outer, new Color(0.42f, 0.61f, 0.70f, 1f), 1f);
            GUI.Label(outer, $"УР. {p.level}   {p.currentXp:N0}/{required:N0}", _hud);

            var elapsed = Time.unscaledTime - ProgressionService.LastAwardTime;
            if (elapsed >= 0f && elapsed < 2.8f && ProgressionService.LastAwardAmount > 0)
                GUI.Label(new Rect(8f, 33f, width + 120f, 18f), $"+{ProgressionService.LastAwardAmount:N0} XP — {ProgressionService.LastAwardReason}", _tiny);
        }

        private void DrawWindow(int id)
        {
            var p = SaveService.Current;
            GUI.Label(new Rect(16f, 26f, _window.width - 32f, 26f),
                $"Ур. {p.level}   Престиж {ProgressionService.PrestigeLevel(p.level)}   |   Очки: {p.unspentTalentPoints} талантов • {p.unspentMasteryPoints} мастерства • {p.unspentPerfectionPoints} совершенства   |   Активно: {ClassDisplay(p.activeClass)} / {SpecDisplay(p.activeSpecialization)}",
                _header);

            var tabY = 57f;
            var labels = new[] { "ДРЕВО", "МАСТЕРСТВО", "СОВЕРШЕНСТВО", "АРСЕНАЛ" };
            var tabWidth = (_window.width - 182f) / labels.Length;
            for (var i = 0; i < labels.Length; i++)
                if (GUI.Toggle(new Rect(12f + i * tabWidth, tabY, tabWidth - 5f, 34f), _tab == i, labels[i], "Button")) _tab = i;
            if (GUI.Button(new Rect(_window.width - 158f, tabY, 145f, 34f), "Закрыть")) SetOpen(false);

            var content = new Rect(12f, 98f, _window.width - 24f, _window.height - 130f);
            FillRect(content, new Color(0.022f, 0.028f, 0.033f, 1f));
            DrawBorder(content, new Color(0.16f, 0.23f, 0.27f, 1f), 1f);

            switch (_tab)
            {
                case 0: DrawTalentPage(p, content); break;
                case 1: DrawMasteryPage(p, content); break;
                case 2: DrawPerfectionPage(p, content); break;
                default: DrawLoadoutPage(p, content); break;
            }

            if (!string.IsNullOrEmpty(_status) && Time.unscaledTime < _statusUntil)
                GUI.Label(new Rect(18f, _window.height - 26f, _window.width - 36f, 19f), _status, _center);
            DrawTooltip();
            GUI.DragWindow(new Rect(0f, 0f, _window.width, 23f));
        }

        private void DrawTalentPage(ProfileProgress p, Rect area)
        {
            var categories = new[] { TalentBranch.Legacy, TalentBranch.Guardian, TalentBranch.Slayer, TalentBranch.Pathfinder, TalentBranch.Seeker };
            var y = area.y + 7f;
            var w = (area.width - 14f) / categories.Length;
            for (var i = 0; i < categories.Length; i++)
            {
                var branch = categories[i];
                var selected = SameCategory(_selectedBranch, branch);
                if (GUI.Toggle(new Rect(area.x + 7f + i * w, y, w - 5f, 31f), selected, BranchTitle(branch), "Button") && !SameCategory(_selectedBranch, branch))
                {
                    _selectedBranch = branch;
                    _pendingSpecId = string.Empty;
                    _treeScroll = Vector2.zero;
                }
            }

            var page = new Rect(area.x + 7f, area.y + 44f, area.width - 14f, area.height - 51f);
            if (_selectedBranch == TalentBranch.Legacy) DrawLegacySheet(p, page);
            else DrawClassSheet(p, page);
        }

        private void DrawLegacySheet(ProfileProgress p, Rect area)
        {
            GUI.Label(new Rect(area.x + 5f, area.y + 2f, area.width - 210f, 29f), "НАСЛЕДИЕ — универсальные бонусы", _header);
            if (GUI.Button(new Rect(area.xMax - 190f, area.y, 184f, 30f), "Сбросить таланты"))
            {
                ProgressionService.Respec(p);
                _pendingSpecId = string.Empty;
                SetStatus("Обычные таланты сброшены.");
            }

            var viewport = new Rect(area.x, area.y + 36f, area.width, area.height - 36f);
            const float contentHeight = 570f;
            _treeScroll = GUI.BeginScrollView(viewport, _treeScroll, new Rect(0f, 0f, viewport.width - 18f, Mathf.Max(contentHeight, viewport.height - 2f)));
            var panel = new Rect(4f, 4f, viewport.width - 28f, 545f);
            DrawBranchPanel(p, TalentBranch.Legacy, panel, "НАСЛЕДИЕ", false, string.Empty, 98f);
            GUI.EndScrollView();
        }

        private void DrawClassSheet(ProfileProgress p, Rect area)
        {
            var classId = TalentCatalog.ClassForBranch(_selectedBranch);
            if (string.IsNullOrEmpty(classId)) return;
            var baseBranch = BaseBranchForClass(classId);
            var spec1 = FirstSpecBranch(classId);
            var spec2 = SecondSpecBranch(classId);
            var spec3 = ThirdSpecBranch(classId);
            EnsurePendingSpec(p, classId, spec1, spec2, spec3);

            var active = p.activeClass == classId && (p.level < 20 || p.activeSpecialization == _pendingSpecId);
            var actionBar = new Rect(area.x, area.y, area.width, 38f);
            FillRect(actionBar, new Color(0.026f, 0.034f, 0.040f, 1f));
            DrawBorder(actionBar, new Color(0.14f, 0.21f, 0.25f, 1f), 1f);
            GUI.Label(new Rect(actionBar.x + 10f, actionBar.y + 7f, Mathf.Max(260f, actionBar.width - 650f), 24f),
                $"{ClassDisplay(classId).ToUpperInvariant()} • {SpecDisplay(_pendingSpecId)}" + (active ? " • АКТИВНЫЙ БИЛД" : string.Empty), _header);

            var resetRect = new Rect(actionBar.xMax - 186f, actionBar.y + 4f, 178f, 30f);
            var activateRect = new Rect(resetRect.x - 262f, actionBar.y + 4f, 252f, 30f);
            var activateText = active ? "АКТИВНО" : p.level < 10 ? "ОТКРОЕТСЯ НА 10 УР." : p.level < 20 ? "АКТИВИРОВАТЬ КЛАСС" : "АКТИВИРОВАТЬ КЛАСС + СПЕК";
            GUI.enabled = !active && p.level >= 10 && Run.instance == null;
            if (GUI.Button(activateRect, activateText)) ActivateClassSelection(p, classId, _pendingSpecId);
            GUI.enabled = true;
            if (GUI.Button(resetRect, "Сбросить таланты"))
            {
                ProgressionService.Respec(p);
                _pendingSpecId = string.Empty;
                SetStatus("Обычные таланты сброшены.");
                return;
            }

            var viewport = new Rect(area.x, area.y + 45f, area.width, area.height - 45f);
            const float baseHeight = 575f;
            const float specHeight = 610f;
            const float gapY = 16f;
            var contentHeight = baseHeight + gapY + specHeight + 18f;
            _treeScroll = GUI.BeginScrollView(viewport, _treeScroll, new Rect(0f, 0f, viewport.width - 18f, contentHeight));
            var innerW = viewport.width - 24f;

            DrawBranchPanel(p, baseBranch, new Rect(5f, 5f, innerW - 10f, baseHeight - 10f), $"ОСНОВА — {ClassDisplay(classId)}", false, string.Empty, 102f);

            var lowerY = baseHeight + gapY;
            var gapX = 10f;
            var colW = (innerW - 20f - gapX * 2f) / 3f;
            DrawBranchPanel(p, spec1, new Rect(5f, lowerY, colW, specHeight), BranchTitle(spec1), true, TalentCatalog.SpecForBranch(spec1), 104f);
            DrawBranchPanel(p, spec2, new Rect(5f + colW + gapX, lowerY, colW, specHeight), BranchTitle(spec2), true, TalentCatalog.SpecForBranch(spec2), 104f);
            DrawBranchPanel(p, spec3, new Rect(5f + (colW + gapX) * 2f, lowerY, colW, specHeight), BranchTitle(spec3), true, TalentCatalog.SpecForBranch(spec3), 104f);
            GUI.EndScrollView();
        }

        private void DrawBranchPanel(ProfileProgress p, TalentBranch branch, Rect panel, string title, bool selectableSpec, string specId, float rowStep)
        {
            var selected = selectableSpec && _pendingSpecId == specId;
            FillRect(panel, selected ? new Color(0.024f, 0.052f, 0.063f, 1f) : new Color(0.012f, 0.017f, 0.021f, 1f));
            DrawBorder(panel, selected ? new Color(0.18f, 0.56f, 0.66f, 1f) : new Color(0.13f, 0.20f, 0.24f, 1f), selected ? 2f : 1f);

            var headerRect = new Rect(panel.x + 7f, panel.y + 5f, panel.width - 14f, 31f);
            if (selectableSpec)
            {
                if (GUI.Toggle(headerRect, selected, selected ? $"✓ {title}" : title, "Button")) _pendingSpecId = specId;
            }
            else GUI.Label(headerRect, title, _center);

            var tree = new Rect(panel.x + 6f, panel.y + 42f, panel.width - 12f, panel.height - 48f);
            DrawBranchTree(p, branch, tree, rowStep);
        }

        private void DrawBranchTree(ProfileProgress p, TalentBranch branch, Rect canvas, float rowStep)
        {
            var defs = TalentCatalog.All.Where(x => x.Branch == branch).ToList();
            foreach (var def in defs)
            {
                if (string.IsNullOrEmpty(def.PrerequisiteId)) continue;
                var parent = TalentCatalog.Find(def.PrerequisiteId);
                if (parent == null || parent.Branch != branch) continue;
                var active = TalentCatalog.GetRank(p, parent.Id) >= def.PrerequisiteRank;
                DrawConnection(GetNodeRect(parent, canvas, rowStep), GetNodeRect(def, canvas, rowStep), active ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));
            }
            foreach (var def in defs) DrawTalentNode(p, def, GetNodeRect(def, canvas, rowStep));
        }

        private Rect GetNodeRect(TalentDef def, Rect canvas, float rowStep)
        {
            const float nodeHeight = 82f;
            float nodeWidth;
            float x;
            if (canvas.width < 650f)
            {
                nodeWidth = Mathf.Clamp(canvas.width * 0.44f, 178f, 225f);
                if (def.TreeColumn == 0) x = canvas.x + 7f;
                else if (def.TreeColumn == 2) x = canvas.xMax - nodeWidth - 7f;
                else x = canvas.center.x - nodeWidth * 0.5f;
            }
            else
            {
                nodeWidth = Mathf.Clamp(canvas.width * 0.23f, 250f, 340f);
                var centers = new[] { canvas.x + canvas.width * 0.22f, canvas.center.x, canvas.x + canvas.width * 0.78f };
                x = centers[Mathf.Clamp(def.TreeColumn, 0, 2)] - nodeWidth * 0.5f;
            }
            var y = canvas.y + 5f + def.TreeRow * rowStep;
            return new Rect(x, y, nodeWidth, nodeHeight);
        }

        private void DrawTalentNode(ProfileProgress p, TalentDef def, Rect rect)
        {
            var rank = TalentCatalog.GetRank(p, def.Id);
            var prereq = TalentCatalog.PrerequisiteMet(p, def);
            var levelOk = p.level >= def.UnlockLevel;
            var maxed = rank >= def.MaxRank;
            var activeBranch = TalentCatalog.IsBranchActive(p, def.Branch);
            var legendary = def.Id.EndsWith("_legendary", StringComparison.OrdinalIgnoreCase);
            var voidCapstone = def.Id.EndsWith("_void_capstone", StringComparison.OrdinalIgnoreCase);

            var fill = legendary ? new Color(0.18f, 0.045f, 0.045f, 1f) : voidCapstone ? new Color(0.11f, 0.055f, 0.16f, 1f) : maxed ? new Color(0.048f, 0.18f, 0.14f, 1f) : activeBranch ? new Color(0.055f, 0.118f, 0.14f, 1f) : new Color(0.050f, 0.058f, 0.064f, 1f);
            var border = legendary ? new Color(0.92f, 0.28f, 0.25f, 1f) : voidCapstone ? new Color(0.66f, 0.35f, 0.92f, 1f) : maxed ? new Color(0.23f, 0.68f, 0.48f, 1f) : activeBranch ? new Color(0.18f, 0.50f, 0.59f, 1f) : new Color(0.20f, 0.26f, 0.29f, 1f);
            FillRect(rect, fill);
            DrawBorder(rect, border, legendary || voidCapstone ? 2f : 1f);

            var iconRect = new Rect(rect.x + 7f, rect.y + 8f, 55f, 55f);
            FillRect(iconRect, new Color(0.02f, 0.025f, 0.03f, 0.96f));
            var icon = ResolveTalentIcon(def);
            if (icon != null) DrawSprite(iconRect, icon, levelOk ? Color.white : new Color(0.42f, 0.42f, 0.42f, 0.85f));
            else GUI.Label(iconRect, EffectGlyph(def), _center);
            DrawBorder(iconRect, border, 1f);

            var textX = rect.x + 68f;
            var textW = rect.width - 75f;
            GUI.Label(new Rect(textX, rect.y + 5f, textW, 21f), $"{def.Name} [{rank}/{def.MaxRank}]", _nodeTitle);
            GUI.Label(new Rect(textX, rect.y + 27f, textW, 24f), ShortEffect(def.Description), _nodeEffect);

            var label = maxed ? "Изучено" : !levelOk ? $"Откроется: ур. {def.UnlockLevel}" : !prereq ? "Нужен предыдущий узел" : $"Изучить — {def.PointCost}";
            GUI.enabled = levelOk && prereq && !maxed && p.unspentTalentPoints >= def.PointCost;
            if (GUI.Button(new Rect(textX, rect.yMax - 26f, textW, 22f), label))
            {
                if (!ProgressionService.TryBuyTalent(p, def.Id, out var error)) SetStatus(error);
                else SetStatus($"Изучено: {def.Name}.");
            }
            GUI.enabled = true;

            var tooltip = $"{def.Name} [{rank}/{def.MaxRank}]\n{def.Description}\nОткрытие: уровень {def.UnlockLevel}";
            if (!prereq) tooltip += "\nТребуется предыдущий узел.";
            GUI.Label(rect, new GUIContent(string.Empty, tooltip));
        }

        private Sprite ResolveTalentIcon(TalentDef def)
        {
            var candidates = PreferredIconCandidates(def.Id);
            foreach (var candidate in candidates)
            {
                var item = ItemCatalog.allItemDefs.FirstOrDefault(x => x != null && string.Equals(x.name, candidate, StringComparison.OrdinalIgnoreCase));
                if (item == null) continue;
                var sprite = _iconResolver.Resolve(item);
                if (sprite != null) return sprite;
            }
            return null;
        }

        private static string[] PreferredIconCandidates(string id)
        {
            id = (id ?? string.Empty).ToLowerInvariant();
            if (id.Contains("guardian_void_capstone")) return new[] { "BearVoid" };
            if (id.Contains("slayer_void_capstone")) return new[] { "BleedOnHitVoid" };
            if (id.Contains("path_void_capstone")) return new[] { "ChainLightningVoid" };
            if (id.Contains("seeker_void_capstone")) return new[] { "TreasureCacheVoid" };
            if (id.Contains("bastion_legendary")) return new[] { "CaptainDefenseMatrix" };
            if (id.Contains("unbroken_legendary")) return new[] { "IncreaseHealing" };
            if (id.Contains("vanguard_legendary")) return new[] { "ArmorReductionOnHit" };
            if (id.Contains("executioner_legendary")) return new[] { "Dagger" };
            if (id.Contains("hunter_legendary")) return new[] { "HeadHunter" };
            if (id.Contains("berserker_legendary")) return new[] { "ShockNearby" };
            if (id.Contains("scout_legendary")) return new[] { "AlienHead" };
            if (id.Contains("acro_legendary")) return new[] { "UtilitySkillMagazine" };
            if (id.Contains("saboteur_legendary")) return new[] { "BounceNearby" };
            if (id.Contains("merchant_legendary")) return new[] { "DroneWeapons" };
            if (id.Contains("prospector_legendary")) return new[] { "Clover" };
            if (id.Contains("relic_legendary")) return new[] { "Talisman" };
            if (id.Contains("crit")) return new[] { "CritGlasses" };
            if (id.Contains("cooldown") || id.Contains("technique") || id.Contains("relic")) return new[] { "Bandolier" };
            if (id.Contains("attack") || id.Contains("haste") || id.Contains("tempo") || id.Contains("berserker")) return new[] { "Syringe" };
            if (id.Contains("jump") || id.Contains("acro") || id.Contains("air")) return new[] { "Feather" };
            if (id.Contains("move") || id.Contains("route") || id.Contains("flow") || id.Contains("adrenaline") || id.Contains("sprint")) return new[] { "Hoof" };
            if (id.Contains("shield") || id.Contains("barrier") || id.Contains("stability") || id.Contains("bastion")) return new[] { "PersonalShield" };
            if (id.Contains("armor") || id.Contains("hardened") || id.Contains("iron")) return new[] { "ArmorPlate" };
            if (id.Contains("regen") || id.Contains("heal") || id.Contains("breath")) return new[] { "Medkit" };
            if (id.Contains("gold") || id.Contains("merchant") || id.Contains("capital") || id.Contains("treasure")) return new[] { "GoldOnHurt" };
            if (id.Contains("pack") || id.Contains("supply")) return new[] { "EquipmentMagazine" };
            if (id.Contains("hunter") || id.Contains("boss") || id.Contains("giant")) return new[] { "BossDamageBonus" };
            if (id.Contains("damage") || id.Contains("power") || id.Contains("focus") || id.Contains("verdict")) return new[] { "Crowbar" };
            return new[] { "Infusion", "Medkit" };
        }

        private static string EffectGlyph(TalentDef def)
        {
            var id = (def?.Id ?? string.Empty).ToLowerInvariant();
            if (id.Contains("legendary")) return "R";
            if (id.Contains("void_capstone")) return "V";
            if (id.Contains("armor") || id.Contains("shield")) return "DEF";
            if (id.Contains("damage") || id.Contains("power")) return "DMG";
            if (id.Contains("move") || id.Contains("jump") || id.Contains("sprint")) return "MOV";
            return "+";
        }

        private void ActivateClassSelection(ProfileProgress p, string classId, string specId)
        {
            if (!ProgressionService.TrySetActiveClass(p, classId, out var classError)) { SetStatus(classError); return; }
            if (p.level >= 20 && !string.IsNullOrEmpty(specId))
            {
                if (!ProgressionService.TrySetActiveSpecialization(p, specId, out var specError)) { SetStatus(specError); return; }
                SetStatus($"Активирован билд: {ClassDisplay(classId)} / {SpecDisplay(specId)}.");
            }
            else SetStatus($"Активирован класс: {ClassDisplay(classId)}.");
        }

        private void EnsurePendingSpec(ProfileProgress p, string classId, TalentBranch first, TalentBranch second, TalentBranch third)
        {
            if (!string.IsNullOrEmpty(_pendingSpecId) && ProgressionService.SpecBelongsToClass(_pendingSpecId, classId)) return;
            if (p.activeClass == classId && !string.IsNullOrEmpty(p.activeSpecialization) && ProgressionService.SpecBelongsToClass(p.activeSpecialization, classId))
                _pendingSpecId = p.activeSpecialization;
            else _pendingSpecId = TalentCatalog.SpecForBranch(first);
        }

        private void DrawMasteryPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 12f, area.y + 12f, area.width - 24f, area.height - 24f));
            GUILayout.Label($"БЕСКОНЕЧНОЕ МАСТЕРСТВО • доступно очков: {p.unspentMasteryPoints}", _header);
            GUILayout.Label("После 25 / 50 / 100 / 200 рангов эффективность новых рангов снижается. Работает только мастерство активного класса.", _small);
            GUILayout.Space(8f);
            if (p.level < 41) { GUILayout.Label("Мастерство откроется на 41 уровне.", _center); GUILayout.EndArea(); return; }
            if (string.IsNullOrEmpty(p.activeClass)) { GUILayout.Label("Сначала выбери активный класс.", _center); GUILayout.EndArea(); return; }

            _masteryScroll = GUILayout.BeginScrollView(_masteryScroll);
            foreach (var def in MasteryCatalog.All.Where(x => x.ClassId == p.activeClass))
            {
                var rank = MasteryCatalog.GetRank(p, def.Id);
                GUILayout.BeginVertical("box");
                GUILayout.BeginHorizontal();
                GUILayout.Label($"{def.Name} — ранг {rank}", _header, GUILayout.Width(330f));
                GUILayout.Label($"Эффективных рангов: {MasteryCatalog.EffectiveRanks(rank):0.##}", GUILayout.Width(250f));
                GUILayout.FlexibleSpace();
                GUI.enabled = p.unspentMasteryPoints > 0;
                if (GUILayout.Button("+1 ранг", GUILayout.Width(130f), GUILayout.Height(30f)))
                {
                    if (!ProgressionService.TryBuyMastery(p, def.Id, out var error)) SetStatus(error);
                    else SetStatus($"Мастерство повышено: {def.Name}.");
                }
                GUI.enabled = true;
                GUILayout.EndHorizontal();
                GUILayout.Label(def.Description, _small);
                GUILayout.EndVertical();
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        private void DrawPerfectionPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 12f, area.y + 12f, area.width - 24f, area.height - 24f));
            GUILayout.Label($"СОВЕРШЕНСТВО • 1 очко каждые 25 уровней • доступно: {p.unspentPerfectionPoints}", _header);
            GUILayout.Space(8f);
            _perfectionScroll = GUILayout.BeginScrollView(_perfectionScroll);
            foreach (var def in PerfectionCatalog.All)
            {
                var rank = PerfectionCatalog.GetRank(p, def.Id);
                GUILayout.BeginHorizontal("box");
                GUILayout.BeginVertical();
                GUILayout.Label($"{def.Name} [{rank}/{def.MaxRank}] — ур. {def.UnlockLevel}", _header);
                GUILayout.Label(def.Description, _small);
                GUILayout.EndVertical();
                GUI.enabled = p.level >= def.UnlockLevel && rank < def.MaxRank && p.unspentPerfectionPoints > 0;
                if (GUILayout.Button(rank >= def.MaxRank ? "Изучено" : "Изучить", GUILayout.Width(140f), GUILayout.Height(42f)))
                {
                    if (!ProgressionService.TryBuyPerfection(p, def.Id, out var error)) SetStatus(error);
                    else SetStatus($"Совершенство изучено: {def.Name}.");
                }
                GUI.enabled = true;
                GUILayout.EndHorizontal();
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        private void DrawLoadoutPage(ProfileProgress p, Rect area)
        {
            var capacity = ProgressionService.StartingCapacity(p);
            var used = StartingLoadoutService.UsedCapacity(p);
            GUI.Label(new Rect(area.x + 12f, area.y + 8f, area.width - 24f, 25f), $"АРСЕНАЛ — вместимость {used}/{capacity}", _header);
            GUI.Label(new Rect(area.x + 12f, area.y + 31f, area.width - 24f, 21f), "ЛКМ — добавить • ПКМ — убрать. Легендарный предмет из Арсенала существует отдельно от легендарного финала подкласса.", _small);

            var searchY = area.y + 58f;
            GUI.Label(new Rect(area.x + 12f, searchY + 4f, 52f, 23f), "Поиск:", _small);
            _search = GUI.TextField(new Rect(area.x + 66f, searchY, 250f, 27f), _search ?? string.Empty);
            var labels = new[] { "Все", "Белые", "Зелёные", "Boss", "Void", "Красные", "Lunar", "Hallowed" };
            var fx = area.x + 330f;
            var fw = Mathf.Max(70f, (area.width - 350f) / labels.Length);
            for (var i = 0; i < labels.Length; i++)
                if (GUI.Toggle(new Rect(fx + i * fw, searchY, fw - 4f, 27f), _itemFilter == i, labels[i], "Button")) _itemFilter = i;

            var bodyY = searchY + 36f;
            var bodyH = area.yMax - bodyY - 10f;
            var selectedW = Mathf.Clamp(area.width * 0.25f, 270f, 385f);
            var gridRect = new Rect(area.x + 10f, bodyY, area.width - selectedW - 25f, bodyH);
            var selectedRect = new Rect(gridRect.xMax + 10f, bodyY, selectedW, bodyH);
            FillRect(gridRect, new Color(0.010f, 0.015f, 0.019f, 1f));
            FillRect(selectedRect, new Color(0.014f, 0.020f, 0.025f, 1f));
            DrawBorder(gridRect, new Color(0.13f, 0.20f, 0.24f, 1f), 1f);
            DrawBorder(selectedRect, new Color(0.13f, 0.20f, 0.24f, 1f), 1f);

            var profile = LocalUserManager.GetFirstLocalUser()?.userProfile;
            IEnumerable<ItemDef> items = StartingLoadoutService.EnumerateEligibleItems(p, profile);
            if (!string.IsNullOrWhiteSpace(_search))
            {
                var needle = _search.Trim();
                items = items.Where(i => DisplayName(i).IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0 || (i.name ?? string.Empty).IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0);
            }
            var list = items.Where(ItemFilterMatches).OrderBy(ItemSortGroup).ThenBy(DisplayName).ToList();
            DrawAvailableItemGrid(p, list, gridRect, used, capacity);
            DrawSelectedItemGrid(p, selectedRect);
        }

        private void DrawAvailableItemGrid(ProfileProgress p, List<ItemDef> items, Rect rect, int used, int capacity)
        {
            const float tile = 82f;
            const float gap = 7f;
            var innerWidth = rect.width - 20f;
            var cols = Mathf.Max(3, Mathf.FloorToInt((innerWidth - gap) / (tile + gap)));
            var rows = Mathf.CeilToInt(items.Count / (float)cols);
            var contentHeight = Mathf.Max(rect.height - 8f, 8f + rows * (tile + gap));
            _itemScroll = GUI.BeginScrollView(new Rect(rect.x + 4f, rect.y + 4f, rect.width - 8f, rect.height - 8f), _itemScroll, new Rect(0f, 0f, innerWidth, contentHeight));
            for (var i = 0; i < items.Count; i++)
            {
                var col = i % cols;
                var row = i / cols;
                DrawItemTile(p, items[i], new Rect(4f + col * (tile + gap), 4f + row * (tile + gap), tile, tile), used, capacity);
            }
            GUI.EndScrollView();
        }

        private void DrawSelectedItemGrid(ProfileProgress p, Rect rect)
        {
            GUI.Label(new Rect(rect.x + 7f, rect.y + 5f, rect.width - 14f, 24f), "ВЫБРАНО", _center);
            var records = p.startingLoadout.Where(x => x.count > 0).ToList();
            const float tile = 72f;
            const float gap = 6f;
            var view = new Rect(rect.x + 5f, rect.y + 31f, rect.width - 10f, rect.height - 36f);
            var cols = Mathf.Max(2, Mathf.FloorToInt((view.width - gap) / (tile + gap)));
            var rows = Mathf.CeilToInt(records.Count / (float)cols);
            var contentHeight = Mathf.Max(view.height - 4f, 6f + rows * (tile + gap));
            _selectedItemScroll = GUI.BeginScrollView(view, _selectedItemScroll, new Rect(0f, 0f, view.width - 16f, contentHeight));
            for (var i = 0; i < records.Count; i++)
            {
                var item = StartingLoadoutService.FindItem(records[i].itemName);
                if (item == null) continue;
                var col = i % cols;
                var row = i / cols;
                DrawSelectedTile(p, item, records[i].count, new Rect(4f + col * (tile + gap), 4f + row * (tile + gap), tile, tile));
            }
            GUI.EndScrollView();
        }

        private void DrawItemTile(ProfileProgress p, ItemDef item, Rect rect, int used, int capacity)
        {
            var selected = p.startingLoadout.FirstOrDefault(x => x.itemName == item.name)?.count ?? 0;
            var cost = StartingLoadoutService.CostOfCopy(item, selected);
            var canFit = used + cost <= capacity;
            FillRect(rect, selected > 0 ? new Color(0.050f, 0.098f, 0.112f, 1f) : new Color(0.032f, 0.039f, 0.044f, 1f));
            DrawBorder(rect, selected > 0 ? new Color(0.20f, 0.62f, 0.70f, 1f) : TierColor(item), selected > 0 ? 2f : 1f);
            var icon = _iconResolver.Resolve(item);
            var iconRect = new Rect(rect.x + 5f, rect.y + 5f, rect.width - 10f, rect.height - 10f);
            if (icon != null) DrawSprite(iconRect, icon, canFit ? Color.white : new Color(0.42f, 0.42f, 0.42f, 0.84f));
            else GUI.Label(iconRect, "…", _center);

            if (selected > 0)
            {
                var badge = new Rect(rect.xMax - 26f, rect.y + 3f, 22f, 19f);
                FillRect(badge, new Color(0.02f, 0.025f, 0.03f, 0.92f));
                GUI.Label(badge, $"x{selected}", _tileLabel);
            }
            var costRect = new Rect(rect.x + 3f, rect.yMax - 21f, 35f, 18f);
            FillRect(costRect, new Color(0.02f, 0.025f, 0.03f, 0.90f));
            GUI.Label(costRect, $"{cost}", _tileLabel);
            GUI.Label(rect, new GUIContent(string.Empty, BuildItemTooltip(item, selected, cost, canFit)));

            var evt = Event.current;
            if (evt.type == EventType.MouseDown && rect.Contains(evt.mousePosition))
            {
                if (evt.button == 0)
                {
                    if (!StartingLoadoutService.TryAdd(p, item, out var error)) SetStatus(error);
                    else SetStatus($"Добавлено: {DisplayName(item)}.");
                }
                else if (evt.button == 1 && selected > 0)
                {
                    StartingLoadoutService.RemoveOne(p, item);
                    SetStatus($"Убрано: {DisplayName(item)}.");
                }
                evt.Use();
            }
        }

        private void DrawSelectedTile(ProfileProgress p, ItemDef item, int count, Rect rect)
        {
            FillRect(rect, new Color(0.038f, 0.052f, 0.059f, 1f));
            DrawBorder(rect, TierColor(item), 1f);
            var icon = _iconResolver.Resolve(item);
            if (icon != null) DrawSprite(new Rect(rect.x + 4f, rect.y + 4f, rect.width - 8f, rect.height - 8f), icon, Color.white);
            var badge = new Rect(rect.xMax - 27f, rect.y + 3f, 23f, 19f);
            FillRect(badge, new Color(0.02f, 0.025f, 0.03f, 0.92f));
            GUI.Label(badge, $"x{count}", _tileLabel);
            GUI.Label(rect, new GUIContent(string.Empty, $"{DisplayName(item)} x{count}\nЛКМ или ПКМ — убрать одну копию"));
            var evt = Event.current;
            if (evt.type == EventType.MouseDown && rect.Contains(evt.mousePosition))
            {
                StartingLoadoutService.RemoveOne(p, item);
                SetStatus($"Убрано: {DisplayName(item)}.");
                evt.Use();
            }
        }

        private bool ItemFilterMatches(ItemDef item)
        {
            if (_itemFilter == 0) return true;
            var tierName = StartingLoadoutService.TierName(item);
            switch (_itemFilter)
            {
                case 1: return item.tier == ItemTier.Tier1;
                case 2: return item.tier == ItemTier.Tier2;
                case 3: return item.tier == ItemTier.Boss;
                case 4: return item.tier == ItemTier.VoidTier1 || item.tier == ItemTier.VoidTier2 || item.tier == ItemTier.VoidTier3 || item.tier == ItemTier.VoidBoss;
                case 5: return item.tier == ItemTier.Tier3;
                case 6: return item.tier == ItemTier.Lunar;
                case 7: return Contains(tierName, "Hallowed") || Contains(tierName, "Cursed");
                default: return true;
            }
        }

        private static int ItemSortGroup(ItemDef item)
        {
            if (item == null) return 99;
            var name = StartingLoadoutService.TierName(item);
            if (Contains(name, "Hallowed") || Contains(name, "Cursed")) return 7;
            switch (item.tier)
            {
                case ItemTier.Tier1: return 1;
                case ItemTier.Tier2: return 2;
                case ItemTier.Boss: return 3;
                case ItemTier.VoidTier1:
                case ItemTier.VoidTier2:
                case ItemTier.VoidTier3:
                case ItemTier.VoidBoss: return 4;
                case ItemTier.Tier3: return 5;
                case ItemTier.Lunar: return 6;
                default: return 8;
            }
        }

        private static Color TierColor(ItemDef item)
        {
            if (item == null) return Color.gray;
            var name = StartingLoadoutService.TierName(item);
            if (Contains(name, "Hallowed") || Contains(name, "Cursed")) return new Color(0.95f, 0.80f, 0.36f, 1f);
            switch (item.tier)
            {
                case ItemTier.Tier1: return new Color(0.82f, 0.82f, 0.82f, 1f);
                case ItemTier.Tier2: return new Color(0.45f, 0.88f, 0.46f, 1f);
                case ItemTier.Tier3: return new Color(0.95f, 0.34f, 0.32f, 1f);
                case ItemTier.Boss: return new Color(0.95f, 0.82f, 0.35f, 1f);
                case ItemTier.Lunar: return new Color(0.42f, 0.70f, 0.95f, 1f);
                case ItemTier.VoidTier1:
                case ItemTier.VoidTier2:
                case ItemTier.VoidTier3:
                case ItemTier.VoidBoss: return new Color(0.75f, 0.42f, 0.92f, 1f);
                default: return new Color(0.55f, 0.65f, 0.70f, 1f);
            }
        }

        private static string BuildItemTooltip(ItemDef item, int selected, int cost, bool canFit)
        {
            var pickup = item != null ? Language.GetString(item.pickupToken) : string.Empty;
            if (string.IsNullOrWhiteSpace(pickup)) pickup = "Без описания";
            return $"{DisplayName(item)}\n{FriendlyTierName(item)}\n{pickup}\nЦена следующей копии: {cost}\nВыбрано: {selected}" + (canFit ? "" : "\nНедостаточно вместимости");
        }

        private static string FriendlyTierName(ItemDef item)
        {
            if (item == null) return "Неизвестно";
            var name = StartingLoadoutService.TierName(item);
            if (Contains(name, "Hallowed") || Contains(name, "Cursed")) return "Освящённый";
            switch (item.tier)
            {
                case ItemTier.Tier1: return "Обычный";
                case ItemTier.Tier2: return "Необычный";
                case ItemTier.Tier3: return "Легендарный";
                case ItemTier.Boss: return "Босс-предмет";
                case ItemTier.Lunar: return "Лунный";
                case ItemTier.VoidTier1:
                case ItemTier.VoidTier2:
                case ItemTier.VoidTier3:
                case ItemTier.VoidBoss: return "Пустотный";
                default: return name;
            }
        }

        private void DrawTooltip()
        {
            if (string.IsNullOrEmpty(GUI.tooltip)) return;
            var width = 390f;
            var height = Mathf.Max(64f, _small.CalcHeight(new GUIContent(GUI.tooltip), width - 18f) + 16f);
            var pos = Event.current.mousePosition;
            var rect = new Rect(pos.x + 18f, pos.y + 18f, width, height);
            rect.x = Mathf.Min(rect.x, _window.width - width - 8f);
            rect.y = Mathf.Min(rect.y, _window.height - height - 8f);
            FillRect(rect, new Color(0.013f, 0.018f, 0.022f, 0.99f));
            DrawBorder(rect, new Color(0.28f, 0.41f, 0.47f, 1f), 1f);
            GUI.Label(new Rect(rect.x + 8f, rect.y + 7f, rect.width - 16f, rect.height - 14f), GUI.tooltip, _small);
        }

        private static string ShortEffect(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return string.Empty;
            var clean = text.Replace("\n", " ").Trim();
            return clean.Length <= 62 ? clean : clean.Substring(0, 59) + "…";
        }

        private void DrawConnection(Rect parent, Rect child, Color color)
        {
            var start = new Vector2(parent.center.x, parent.yMax);
            var end = new Vector2(child.center.x, child.y);
            var mid = (start.y + end.y) * 0.5f;
            FillRect(new Rect(start.x - 1f, start.y, 2f, Mathf.Max(1f, mid - start.y)), color);
            FillRect(new Rect(Mathf.Min(start.x, end.x), mid - 1f, Mathf.Max(2f, Mathf.Abs(end.x - start.x)), 2f), color);
            FillRect(new Rect(end.x - 1f, mid, 2f, Mathf.Max(1f, end.y - mid)), color);
        }

        private static void DrawSprite(Rect rect, Sprite sprite, Color color)
        {
            if (sprite == null || sprite.texture == null) return;
            var tex = sprite.texture;
            var sr = sprite.rect;
            var uv = new Rect(sr.x / tex.width, sr.y / tex.height, sr.width / tex.width, sr.height / tex.height);
            var old = GUI.color;
            GUI.color = color;
            GUI.DrawTextureWithTexCoords(rect, tex, uv, true);
            GUI.color = old;
        }

        private static bool SameCategory(TalentBranch a, TalentBranch b)
        {
            if (b == TalentBranch.Legacy) return a == TalentBranch.Legacy;
            return TalentCatalog.ClassForBranch(a) == TalentCatalog.ClassForBranch(b);
        }

        private static TalentBranch BaseBranchForClass(string id)
        {
            if (id == "Guardian") return TalentBranch.Guardian;
            if (id == "Slayer") return TalentBranch.Slayer;
            if (id == "Pathfinder") return TalentBranch.Pathfinder;
            return TalentBranch.Seeker;
        }

        private static TalentBranch FirstSpecBranch(string id)
        {
            if (id == "Guardian") return TalentBranch.GuardianBastion;
            if (id == "Slayer") return TalentBranch.SlayerExecutioner;
            if (id == "Pathfinder") return TalentBranch.PathfinderScout;
            return TalentBranch.SeekerMerchant;
        }

        private static TalentBranch SecondSpecBranch(string id)
        {
            if (id == "Guardian") return TalentBranch.GuardianUnbroken;
            if (id == "Slayer") return TalentBranch.SlayerHunter;
            if (id == "Pathfinder") return TalentBranch.PathfinderAcrobat;
            return TalentBranch.SeekerProspector;
        }

        private static TalentBranch ThirdSpecBranch(string id)
        {
            if (id == "Guardian") return TalentBranch.GuardianVanguard;
            if (id == "Slayer") return TalentBranch.SlayerBerserker;
            if (id == "Pathfinder") return TalentBranch.PathfinderSaboteur;
            return TalentBranch.SeekerRelicKeeper;
        }

        private static string BranchTitle(TalentBranch branch)
        {
            switch (branch)
            {
                case TalentBranch.Legacy: return "НАСЛЕДИЕ";
                case TalentBranch.Guardian: return "СТРАЖ";
                case TalentBranch.GuardianBastion: return "БАСТИОН";
                case TalentBranch.GuardianUnbroken: return "НЕСОКРУШИМЫЙ";
                case TalentBranch.GuardianVanguard: return "АВАНГАРД";
                case TalentBranch.Slayer: return "ИСТРЕБИТЕЛЬ";
                case TalentBranch.SlayerExecutioner: return "ПАЛАЧ";
                case TalentBranch.SlayerHunter: return "ОХОТНИК";
                case TalentBranch.SlayerBerserker: return "БЕРСЕРК";
                case TalentBranch.Pathfinder: return "СЛЕДОПЫТ";
                case TalentBranch.PathfinderScout: return "РАЗВЕДЧИК";
                case TalentBranch.PathfinderAcrobat: return "АКРОБАТ";
                case TalentBranch.PathfinderSaboteur: return "ДИВЕРСАНТ";
                case TalentBranch.Seeker: return "ИСКАТЕЛЬ";
                case TalentBranch.SeekerMerchant: return "ТОРГОВЕЦ";
                case TalentBranch.SeekerProspector: return "СТАРАТЕЛЬ";
                default: return "РЕЛИКВАРИЙ";
            }
        }

        private static string ClassDisplay(string id)
        {
            if (id == "Guardian") return "Страж";
            if (id == "Slayer") return "Истребитель";
            if (id == "Pathfinder") return "Следопыт";
            if (id == "Seeker") return "Искатель";
            return "не выбран";
        }

        private static string SpecDisplay(string id)
        {
            if (id == "Bastion") return "Бастион";
            if (id == "Unbroken") return "Несокрушимый";
            if (id == "Vanguard") return "Авангард";
            if (id == "Executioner") return "Палач";
            if (id == "Hunter") return "Охотник";
            if (id == "Berserker") return "Берсерк";
            if (id == "Scout") return "Разведчик";
            if (id == "Acrobat") return "Акробат";
            if (id == "Saboteur") return "Диверсант";
            if (id == "Merchant") return "Торговец";
            if (id == "Prospector") return "Старатель";
            if (id == "RelicKeeper") return "Реликварий";
            return "не выбрана";
        }

        private static string DisplayName(ItemDef item)
        {
            if (item == null) return "<null>";
            var localized = Language.GetString(item.nameToken);
            return string.IsNullOrWhiteSpace(localized) ? item.name : localized;
        }

        private static bool Contains(string text, string part) => !string.IsNullOrEmpty(text) && text.IndexOf(part, StringComparison.OrdinalIgnoreCase) >= 0;

        private void SetStatus(string text)
        {
            _status = text ?? string.Empty;
            _statusUntil = Time.unscaledTime + 4f;
        }

        private void EnsureStyles()
        {
            if (_windowStyle != null) return;
            _windowTexture = new Texture2D(1, 1);
            _windowTexture.SetPixel(0, 0, new Color(0.020f, 0.027f, 0.032f, 1f));
            _windowTexture.Apply();
            _windowStyle = new GUIStyle(GUI.skin.window)
            {
                normal = { background = _windowTexture, textColor = Color.white },
                fontSize = 15,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.UpperCenter,
                padding = new RectOffset(8, 8, 8, 8)
            };
            _header = new GUIStyle(GUI.skin.label) { fontSize = 15, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _small = new GUIStyle(GUI.skin.label) { fontSize = 12, wordWrap = true, normal = { textColor = new Color(0.78f, 0.83f, 0.86f, 1f) } };
            _tiny = new GUIStyle(GUI.skin.label) { fontSize = 10, alignment = TextAnchor.MiddleLeft, normal = { textColor = new Color(0.83f, 0.90f, 0.94f, 1f) } };
            _nodeTitle = new GUIStyle(GUI.skin.label) { fontSize = 12, fontStyle = FontStyle.Bold, clipping = TextClipping.Clip, normal = { textColor = Color.white } };
            _nodeEffect = new GUIStyle(GUI.skin.label) { fontSize = 10, wordWrap = true, clipping = TextClipping.Clip, normal = { textColor = new Color(0.84f, 0.89f, 0.92f, 1f) } };
            _center = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 12, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _hud = new GUIStyle(_center) { fontSize = 10 };
            _tileLabel = new GUIStyle(_center) { fontSize = 10 };
        }

        private static void FillRect(Rect rect, Color color)
        {
            var old = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = old;
        }

        private static void DrawBorder(Rect rect, Color color, float thickness)
        {
            FillRect(new Rect(rect.x, rect.y, rect.width, thickness), color);
            FillRect(new Rect(rect.x, rect.yMax - thickness, rect.width, thickness), color);
            FillRect(new Rect(rect.x, rect.y, thickness, rect.height), color);
            FillRect(new Rect(rect.xMax - thickness, rect.y, thickness, rect.height), color);
        }
    }
}

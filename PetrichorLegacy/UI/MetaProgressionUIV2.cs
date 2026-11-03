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
    public sealed class MetaProgressionUIV2 : MonoBehaviour
    {
        private Rect _window = new Rect(50f, 40f, 1540f, 910f);
        private bool _open;
        private int _tab;
        private TalentBranch _selectedBranch = TalentBranch.Legacy;
        private string _pendingSpecId = string.Empty;
        private Vector2 _treeScroll;
        private Vector2 _masteryScroll;
        private Vector2 _perfectionScroll;
        private Vector2 _itemScroll;
        private Vector2 _selectedScroll;
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
        private GUIStyle _nodeDesc;
        private GUIStyle _center;
        private GUIStyle _hud;
        private GUIStyle _tileLabel;
        private Texture2D _windowTexture;

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
            PetrichorLegacyPlugin.Log?.LogInfo($"Meta progression UI toggled: {(open ? "OPEN" : "CLOSED")}");
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

            _window.width = Mathf.Min(1540f, Mathf.Max(920f, Screen.width - 36f));
            _window.height = Mathf.Min(910f, Mathf.Max(620f, Screen.height - 36f));
            _window.x = Mathf.Clamp(_window.x, 0f, Mathf.Max(0f, Screen.width - _window.width));
            _window.y = Mathf.Clamp(_window.y, 0f, Mathf.Max(0f, Screen.height - _window.height));

            _window = GUI.Window(941205, _window, DrawWindow, "PETRICHOR LEGACY — META PROGRESSION", _windowStyle);
            GUI.BringWindowToFront(941205);
        }

        private void DrawXpHud()
        {
            var p = SaveService.Current;
            var required = Mathf.Max(1, ProgressionService.XpRequiredForNextLevel(p.level));
            var fraction = Mathf.Clamp01((float)p.currentXp / required);
            var width = Mathf.Clamp(Screen.width * 0.20f, 260f, 340f);
            var outer = new Rect(16f, 18f, width, 25f);
            FillRect(outer, new Color(0.012f, 0.017f, 0.021f, 0.96f));
            var inner = new Rect(outer.x + 2f, outer.y + 2f, outer.width - 4f, outer.height - 4f);
            FillRect(new Rect(inner.x, inner.y, inner.width * fraction, inner.height), new Color(0.10f, 0.48f, 0.68f, 0.95f));
            DrawBorder(outer, new Color(0.46f, 0.66f, 0.76f, 1f), 1f);
            GUI.Label(outer, $"УР. {p.level}   XP {p.currentXp:N0}/{required:N0}", _hud);

            var elapsed = Time.unscaledTime - ProgressionService.LastAwardTime;
            if (elapsed >= 0f && elapsed < 3.0f && ProgressionService.LastAwardAmount > 0)
                GUI.Label(new Rect(outer.x, outer.yMax + 1f, outer.width, 19f), $"+{ProgressionService.LastAwardAmount:N0} XP — {ProgressionService.LastAwardReason}", _tiny);
        }

        private void DrawWindow(int id)
        {
            var p = SaveService.Current;
            GUI.Label(new Rect(18f, 28f, _window.width - 36f, 25f),
                $"Ур. {p.level}   Престиж {ProgressionService.PrestigeLevel(p.level)}   |   Очки: {p.unspentTalentPoints} талантов • {p.unspentMasteryPoints} мастерства • {p.unspentPerfectionPoints} совершенства   |   Активно: {ClassDisplay(p.activeClass)} / {SpecDisplay(p.activeSpecialization)}",
                _header);

            var tabY = 59f;
            var labels = new[] { "ДРЕВО", "МАСТЕРСТВО", "СОВЕРШЕНСТВО", "АРСЕНАЛ" };
            var tabWidth = (_window.width - 190f) / labels.Length;
            for (var i = 0; i < labels.Length; i++)
                if (GUI.Toggle(new Rect(14f + i * tabWidth, tabY, tabWidth - 5f, 33f), _tab == i, labels[i], "Button")) _tab = i;
            if (GUI.Button(new Rect(_window.width - 165f, tabY, 150f, 33f), "Закрыть")) SetOpen(false);

            var content = new Rect(14f, 100f, _window.width - 28f, _window.height - 132f);
            FillRect(content, new Color(0.024f, 0.030f, 0.036f, 1f));
            DrawBorder(content, new Color(0.17f, 0.24f, 0.28f, 1f), 1f);

            switch (_tab)
            {
                case 0: DrawTalentPage(p, content); break;
                case 1: DrawMasteryPage(p, content); break;
                case 2: DrawPerfectionPage(p, content); break;
                default: DrawLoadoutArea(p, content); break;
            }

            if (!string.IsNullOrEmpty(_status) && Time.unscaledTime < _statusUntil)
                GUI.Label(new Rect(20f, _window.height - 27f, _window.width - 40f, 20f), _status, _center);

            DrawTooltip();
            GUI.DragWindow(new Rect(0, 0, _window.width, 24f));
        }

        private void DrawTalentPage(ProfileProgress p, Rect area)
        {
            var categories = new[] { TalentBranch.Legacy, TalentBranch.Guardian, TalentBranch.Slayer, TalentBranch.Pathfinder, TalentBranch.Seeker };
            var y = area.y + 8f;
            var w = (area.width - 16f) / categories.Length;
            for (var i = 0; i < categories.Length; i++)
            {
                var branch = categories[i];
                var selected = SameCategory(_selectedBranch, branch);
                if (GUI.Toggle(new Rect(area.x + 8f + i * w, y, w - 5f, 32f), selected, BranchTitle(branch), "Button"))
                {
                    if (!SameCategory(_selectedBranch, branch))
                    {
                        _selectedBranch = branch;
                        _pendingSpecId = string.Empty;
                        _treeScroll = Vector2.zero;
                    }
                }
            }

            if (GUI.Button(new Rect(area.xMax - 190f, area.y + 47f, 174f, 28f), "Сбросить обычные таланты"))
            {
                ProgressionService.Respec(p);
                _pendingSpecId = string.Empty;
                SetStatus("Обычные таланты сброшены. Мастерство и Совершенство сохранены.");
            }

            var page = new Rect(area.x + 8f, area.y + 44f, area.width - 16f, area.height - 52f);
            if (_selectedBranch == TalentBranch.Legacy) DrawLegacySheet(p, page);
            else DrawClassSheet(p, page);
        }

        private void DrawLegacySheet(ProfileProgress p, Rect area)
        {
            var title = new Rect(area.x, area.y, area.width - 205f, 34f);
            GUI.Label(title, "НАСЛЕДИЕ — универсальные бонусы, работающие с любым классом", _header);
            var canvas = new Rect(area.x, area.y + 38f, area.width, area.height - 38f);
            FillRect(canvas, new Color(0.014f, 0.019f, 0.023f, 1f));
            DrawBorder(canvas, new Color(0.15f, 0.22f, 0.26f, 1f), 1f);
            DrawCompactBranchTree(p, TalentBranch.Legacy, canvas, 88f);
        }

        private void DrawClassSheet(ProfileProgress p, Rect area)
        {
            var classId = TalentCatalog.ClassForBranch(_selectedBranch);
            if (string.IsNullOrEmpty(classId)) return;
            var baseBranch = BaseBranchForClass(classId);
            var spec1 = FirstSpecBranch(classId);
            var spec2 = SecondSpecBranch(classId);
            EnsurePendingSpec(p, classId, spec1, spec2);

            var selectedSpec = _pendingSpecId;
            var active = p.activeClass == classId && p.activeSpecialization == selectedSpec;
            GUI.Label(new Rect(area.x + 4f, area.y + 2f, area.width - 450f, 28f),
                $"{ClassDisplay(classId).ToUpperInvariant()}   •   выбранная специализация: {SpecDisplay(selectedSpec)}", _header);

            var activateText = active ? "АКТИВНО" : p.level < 10 ? "КЛАСС ОТКРОЕТСЯ НА 10 УР." : p.level < 20 ? "АКТИВИРОВАТЬ КЛАСС" : "АКТИВИРОВАТЬ КЛАСС + СПЕК";
            GUI.enabled = !active && p.level >= 10 && Run.instance == null;
            if (GUI.Button(new Rect(area.xMax - 420f, area.y, 250f, 31f), activateText)) ActivateClassSelection(p, classId, selectedSpec);
            GUI.enabled = true;

            GUI.Label(new Rect(area.xMax - 160f, area.y + 4f, 155f, 24f), active ? "● активный билд" : "○ не активен", _small);

            var viewport = new Rect(area.x, area.y + 38f, area.width, area.height - 38f);
            var contentHeight = 742f;
            _treeScroll = GUI.BeginScrollView(viewport, _treeScroll, new Rect(0f, 0f, viewport.width - 18f, contentHeight));
            var innerW = viewport.width - 20f;

            var basePanel = new Rect(4f, 4f, innerW - 8f, 350f);
            DrawBranchPanel(p, baseBranch, basePanel, $"ОСНОВА — {ClassDisplay(classId)}", false, string.Empty);

            var lowerY = 363f;
            var gap = 10f;
            var half = (innerW - gap - 8f) * 0.5f;
            var left = new Rect(4f, lowerY, half, 365f);
            var right = new Rect(4f + half + gap, lowerY, half, 365f);
            DrawBranchPanel(p, spec1, left, BranchTitle(spec1), true, TalentCatalog.SpecForBranch(spec1));
            DrawBranchPanel(p, spec2, right, BranchTitle(spec2), true, TalentCatalog.SpecForBranch(spec2));

            GUI.EndScrollView();
        }

        private void DrawBranchPanel(ProfileProgress p, TalentBranch branch, Rect panel, string title, bool selectableSpec, string specId)
        {
            var selected = selectableSpec && _pendingSpecId == specId;
            FillRect(panel, selected ? new Color(0.027f, 0.055f, 0.066f, 1f) : new Color(0.014f, 0.019f, 0.023f, 1f));
            DrawBorder(panel, selected ? new Color(0.20f, 0.58f, 0.68f, 1f) : new Color(0.14f, 0.21f, 0.25f, 1f), selected ? 2f : 1f);

            var headerRect = new Rect(panel.x + 7f, panel.y + 5f, panel.width - 14f, 28f);
            if (selectableSpec)
            {
                if (GUI.Toggle(headerRect, selected, selected ? $"✓ {title}" : title, "Button")) _pendingSpecId = specId;
            }
            else GUI.Label(headerRect, title, _center);

            var tree = new Rect(panel.x + 5f, panel.y + 37f, panel.width - 10f, panel.height - 42f);
            DrawCompactBranchTree(p, branch, tree, 86f);
        }

        private void DrawCompactBranchTree(ProfileProgress p, TalentBranch branch, Rect canvas, float rowStep)
        {
            var defs = TalentCatalog.All.Where(x => x.Branch == branch).ToList();
            if (defs.Count == 0) return;

            foreach (var def in defs)
            {
                if (string.IsNullOrEmpty(def.PrerequisiteId)) continue;
                var parent = TalentCatalog.Find(def.PrerequisiteId);
                if (parent == null || parent.Branch != branch) continue;
                var active = TalentCatalog.GetRank(p, parent.Id) >= def.PrerequisiteRank;
                DrawConnection(GetCompactNodeRect(parent, canvas, rowStep), GetCompactNodeRect(def, canvas, rowStep),
                    active ? new Color(0.20f, 0.65f, 0.72f, 1f) : new Color(0.16f, 0.19f, 0.21f, 1f));
            }
            foreach (var def in defs) DrawTalentNodeCompact(p, def, GetCompactNodeRect(def, canvas, rowStep));
        }

        private Rect GetCompactNodeRect(TalentDef def, Rect canvas, float rowStep)
        {
            const float gap = 8f;
            var nodeWidth = Mathf.Clamp((canvas.width - 20f - gap * 2f) / 3f, 142f, 272f);
            const float nodeHeight = 78f;
            var total = nodeWidth * 3f + gap * 2f;
            var startX = canvas.x + Mathf.Max(6f, (canvas.width - total) * 0.5f);
            var x = startX + def.TreeColumn * (nodeWidth + gap);
            var y = canvas.y + 5f + def.TreeRow * rowStep;
            return new Rect(x, y, nodeWidth, nodeHeight);
        }

        private void DrawTalentNodeCompact(ProfileProgress p, TalentDef def, Rect rect)
        {
            var rank = TalentCatalog.GetRank(p, def.Id);
            var prereq = TalentCatalog.PrerequisiteMet(p, def);
            var levelOk = p.level >= def.UnlockLevel;
            var maxed = rank >= def.MaxRank;
            var activeBranch = TalentCatalog.IsBranchActive(p, def.Branch);

            var fill = maxed ? new Color(0.055f, 0.20f, 0.16f, 1f) : activeBranch ? new Color(0.065f, 0.135f, 0.16f, 1f) : new Color(0.055f, 0.064f, 0.070f, 1f);
            FillRect(rect, fill);
            DrawBorder(rect, maxed ? new Color(0.25f, 0.72f, 0.52f, 1f) : activeBranch ? new Color(0.20f, 0.53f, 0.62f, 1f) : new Color(0.22f, 0.28f, 0.31f, 1f), 1f);
            GUI.Label(new Rect(rect.x + 6f, rect.y + 3f, rect.width - 12f, 18f), $"{def.Name} [{rank}/{def.MaxRank}]", _nodeTitle);
            GUI.Label(new Rect(rect.x + 6f, rect.y + 20f, rect.width - 12f, 34f), def.Description, _nodeDesc);

            var label = maxed ? "Изучено" : !levelOk ? $"Откроется: ур. {def.UnlockLevel}" : !prereq ? "Нужен предыдущий узел" : $"Изучить — {def.PointCost}";
            GUI.enabled = levelOk && prereq && !maxed && p.unspentTalentPoints >= def.PointCost;
            if (GUI.Button(new Rect(rect.x + 5f, rect.yMax - 21f, rect.width - 10f, 18f), label))
            {
                if (!ProgressionService.TryBuyTalent(p, def.Id, out var error)) SetStatus(error);
                else SetStatus($"Изучено: {def.Name}.");
            }
            GUI.enabled = true;
        }

        private void ActivateClassSelection(ProfileProgress p, string classId, string specId)
        {
            if (!ProgressionService.TrySetActiveClass(p, classId, out var classError))
            {
                SetStatus(classError);
                return;
            }
            if (p.level >= 20 && !string.IsNullOrEmpty(specId))
            {
                if (!ProgressionService.TrySetActiveSpecialization(p, specId, out var specError))
                {
                    SetStatus(specError);
                    return;
                }
                SetStatus($"Активирован билд: {ClassDisplay(classId)} / {SpecDisplay(specId)}.");
            }
            else SetStatus($"Активирован класс: {ClassDisplay(classId)}.");
        }

        private void EnsurePendingSpec(ProfileProgress p, string classId, TalentBranch first, TalentBranch second)
        {
            if (!string.IsNullOrEmpty(_pendingSpecId) && ProgressionService.SpecBelongsToClass(_pendingSpecId, classId)) return;
            if (p.activeClass == classId && !string.IsNullOrEmpty(p.activeSpecialization) && ProgressionService.SpecBelongsToClass(p.activeSpecialization, classId))
                _pendingSpecId = p.activeSpecialization;
            else
                _pendingSpecId = TalentCatalog.SpecForBranch(first);
        }

        private void DrawMasteryPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 12f, area.y + 12f, area.width - 24f, area.height - 24f));
            GUILayout.Label($"БЕСКОНЕЧНОЕ МАСТЕРСТВО   •   доступно очков: {p.unspentMasteryPoints}", _header);
            GUILayout.Label("После 25 / 50 / 100 / 200 рангов новые ранги дают 75% / 50% / 30% / 20% базового эффекта. Работает мастерство только активного класса.", _small);
            GUILayout.Space(8f);
            if (p.level < 41)
            {
                GUILayout.Label("Мастерство откроется на 41 уровне.", _center);
                GUILayout.EndArea();
                return;
            }
            if (string.IsNullOrEmpty(p.activeClass))
            {
                GUILayout.Label("Сначала выбери активный класс во вкладке Древо.", _center);
                GUILayout.EndArea();
                return;
            }

            _masteryScroll = GUILayout.BeginScrollView(_masteryScroll);
            foreach (var def in MasteryCatalog.All.Where(x => x.ClassId == p.activeClass))
            {
                var rank = MasteryCatalog.GetRank(p, def.Id);
                GUILayout.BeginVertical("box");
                GUILayout.BeginHorizontal();
                GUILayout.Label($"{def.Name} — ранг {rank}", _nodeTitle, GUILayout.Width(310f));
                GUILayout.Label($"Эффективных рангов: {MasteryCatalog.EffectiveRanks(rank):0.##}", GUILayout.Width(230f));
                GUILayout.FlexibleSpace();
                GUI.enabled = p.unspentMasteryPoints > 0;
                if (GUILayout.Button("+1 ранг", GUILayout.Width(120f)))
                {
                    if (!ProgressionService.TryBuyMastery(p, def.Id, out var error)) SetStatus(error);
                    else SetStatus($"Мастерство повышено: {def.Name}.");
                }
                GUI.enabled = true;
                GUILayout.EndHorizontal();
                GUILayout.Label(def.Description, _nodeDesc);
                GUILayout.EndVertical();
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        private void DrawPerfectionPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 12f, area.y + 12f, area.width - 24f, area.height - 24f));
            GUILayout.Label($"СОВЕРШЕНСТВО   •   1 очко каждые 25 уровней   •   доступно: {p.unspentPerfectionPoints}", _header);
            GUILayout.Label("Престиж не сбрасывает уровень. Каждые 100 уровней он открывает следующий слой долгой прогрессии.", _small);
            GUILayout.Space(8f);
            _perfectionScroll = GUILayout.BeginScrollView(_perfectionScroll);
            foreach (var def in PerfectionCatalog.All)
            {
                var rank = PerfectionCatalog.GetRank(p, def.Id);
                GUILayout.BeginHorizontal("box");
                GUILayout.BeginVertical();
                GUILayout.Label($"{def.Name} [{rank}/{def.MaxRank}] — требуется ур. {def.UnlockLevel}", _nodeTitle);
                GUILayout.Label(def.Description, _nodeDesc);
                GUILayout.EndVertical();
                GUI.enabled = p.level >= def.UnlockLevel && rank < def.MaxRank && p.unspentPerfectionPoints > 0;
                if (GUILayout.Button(rank >= def.MaxRank ? "Изучено" : "Изучить", GUILayout.Width(130f), GUILayout.Height(42f)))
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

        private void DrawLoadoutArea(ProfileProgress p, Rect area)
        {
            var capacity = ProgressionService.StartingCapacity(p);
            var used = StartingLoadoutService.UsedCapacity(p);
            GUI.Label(new Rect(area.x + 12f, area.y + 8f, area.width - 24f, 24f), $"АРСЕНАЛ — вместимость {used}/{capacity}", _header);
            GUI.Label(new Rect(area.x + 12f, area.y + 31f, area.width - 24f, 20f),
                "ЛКМ по предмету — добавить. ПКМ — убрать одну копию. Красный/Lunar/Hallowed — максимум один предмет высокого тира суммарно.", _small);

            var searchY = area.y + 56f;
            GUI.Label(new Rect(area.x + 12f, searchY + 3f, 52f, 22f), "Поиск:", _small);
            _search = GUI.TextField(new Rect(area.x + 66f, searchY, 250f, 25f), _search ?? string.Empty);

            var filterLabels = new[] { "Все", "Белые", "Зелёные", "Boss", "Void", "Красные", "Lunar", "Hallowed" };
            var fx = area.x + 330f;
            var fw = Mathf.Max(70f, (area.width - 350f) / filterLabels.Length);
            for (var i = 0; i < filterLabels.Length; i++)
                if (GUI.Toggle(new Rect(fx + i * fw, searchY, fw - 4f, 25f), _itemFilter == i, filterLabels[i], "Button")) _itemFilter = i;

            var bodyY = searchY + 34f;
            var bodyH = area.yMax - bodyY - 10f;
            var selectedW = Mathf.Clamp(area.width * 0.26f, 270f, 390f);
            var gridRect = new Rect(area.x + 10f, bodyY, area.width - selectedW - 25f, bodyH);
            var selectedRect = new Rect(gridRect.xMax + 10f, bodyY, selectedW, bodyH);
            FillRect(gridRect, new Color(0.012f, 0.017f, 0.021f, 1f));
            FillRect(selectedRect, new Color(0.016f, 0.022f, 0.027f, 1f));
            DrawBorder(gridRect, new Color(0.14f, 0.21f, 0.25f, 1f), 1f);
            DrawBorder(selectedRect, new Color(0.14f, 0.21f, 0.25f, 1f), 1f);

            var userProfile = LocalUserManager.GetFirstLocalUser()?.userProfile;
            IEnumerable<ItemDef> items = StartingLoadoutService.EnumerateEligibleItems(p, userProfile);
            if (!string.IsNullOrWhiteSpace(_search))
            {
                var needle = _search.Trim();
                items = items.Where(i => DisplayName(i).IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0 || (i.name ?? string.Empty).IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0);
            }
            var list = items.Where(ItemFilterMatches).OrderBy(i => ItemSortGroup(i)).ThenBy(DisplayName).ToList();
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
            var contentHeight = Mathf.Max(rect.height - 10f, 10f + rows * (tile + gap));
            _itemScroll = GUI.BeginScrollView(new Rect(rect.x + 4f, rect.y + 4f, rect.width - 8f, rect.height - 8f), _itemScroll,
                new Rect(0f, 0f, innerWidth, contentHeight));

            for (var i = 0; i < items.Count; i++)
            {
                var col = i % cols;
                var row = i / cols;
                var tileRect = new Rect(5f + col * (tile + gap), 5f + row * (tile + gap), tile, tile);
                DrawItemTile(p, items[i], tileRect, used, capacity, true);
            }
            GUI.EndScrollView();
        }

        private void DrawSelectedItemGrid(ProfileProgress p, Rect rect)
        {
            GUI.Label(new Rect(rect.x + 8f, rect.y + 5f, rect.width - 16f, 22f), "ВЫБРАНО", _center);
            var records = p.startingLoadout.Where(x => x.count > 0).ToList();
            const float tile = 72f;
            const float gap = 6f;
            var view = new Rect(rect.x + 5f, rect.y + 30f, rect.width - 10f, rect.height - 35f);
            var cols = Mathf.Max(2, Mathf.FloorToInt((view.width - gap) / (tile + gap)));
            var rows = Mathf.CeilToInt(records.Count / (float)cols);
            var contentHeight = Mathf.Max(view.height - 4f, 6f + rows * (tile + gap));
            _selectedScroll = GUI.BeginScrollView(view, _selectedScroll, new Rect(0f, 0f, view.width - 16f, contentHeight));
            for (var i = 0; i < records.Count; i++)
            {
                var item = StartingLoadoutService.FindItem(records[i].itemName);
                if (item == null) continue;
                var col = i % cols;
                var row = i / cols;
                var tileRect = new Rect(4f + col * (tile + gap), 4f + row * (tile + gap), tile, tile);
                DrawSelectedTile(p, item, records[i].count, tileRect);
            }
            GUI.EndScrollView();
        }

        private void DrawItemTile(ProfileProgress p, ItemDef item, Rect rect, int used, int capacity, bool interactive)
        {
            var selected = p.startingLoadout.FirstOrDefault(x => x.itemName == item.name)?.count ?? 0;
            var cost = StartingLoadoutService.CostOfCopy(item, selected);
            var canFit = used + cost <= capacity;
            FillRect(rect, selected > 0 ? new Color(0.055f, 0.105f, 0.12f, 1f) : new Color(0.035f, 0.042f, 0.047f, 1f));
            DrawBorder(rect, selected > 0 ? new Color(0.22f, 0.65f, 0.72f, 1f) : TierColor(item), selected > 0 ? 2f : 1f);

            var iconRect = new Rect(rect.x + 6f, rect.y + 6f, rect.width - 12f, rect.height - 12f);
            DrawSprite(iconRect, item.pickupIconSprite, canFit ? Color.white : new Color(0.45f, 0.45f, 0.45f, 0.85f));
            if (item.pickupIconSprite == null) GUI.Label(iconRect, "?", _center);

            if (selected > 0)
            {
                var badge = new Rect(rect.xMax - 26f, rect.y + 3f, 22f, 19f);
                FillRect(badge, new Color(0.02f, 0.025f, 0.03f, 0.92f));
                GUI.Label(badge, $"x{selected}", _tileLabel);
            }
            var costRect = new Rect(rect.x + 3f, rect.yMax - 21f, 35f, 18f);
            FillRect(costRect, new Color(0.02f, 0.025f, 0.03f, 0.90f));
            GUI.Label(costRect, $"{cost}", _tileLabel);

            var tip = BuildItemTooltip(item, selected, cost, canFit);
            GUI.Label(rect, new GUIContent(string.Empty, tip));

            if (!interactive) return;
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
            FillRect(rect, new Color(0.04f, 0.055f, 0.062f, 1f));
            DrawBorder(rect, TierColor(item), 1f);
            DrawSprite(new Rect(rect.x + 5f, rect.y + 5f, rect.width - 10f, rect.height - 10f), item.pickupIconSprite, Color.white);
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
            if (item == null) return new Color(0.55f, 0.55f, 0.55f, 1f);
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
            return $"{DisplayName(item)}\n{StartingLoadoutService.TierName(item)}\n{pickup}\nЦена следующей копии: {cost}\nВыбрано: {selected}" + (canFit ? "" : "\nНедостаточно вместимости");
        }

        private void DrawTooltip()
        {
            if (string.IsNullOrEmpty(GUI.tooltip)) return;
            var size = _small.CalcSize(new GUIContent(GUI.tooltip));
            var width = Mathf.Clamp(size.x + 20f, 220f, 430f);
            var height = Mathf.Max(58f, _small.CalcHeight(new GUIContent(GUI.tooltip), width - 16f) + 14f);
            var pos = Event.current.mousePosition;
            var rect = new Rect(pos.x + 18f, pos.y + 18f, width, height);
            rect.x = Mathf.Min(rect.x, _window.width - width - 8f);
            rect.y = Mathf.Min(rect.y, _window.height - height - 8f);
            FillRect(rect, new Color(0.015f, 0.020f, 0.024f, 0.98f));
            DrawBorder(rect, new Color(0.30f, 0.43f, 0.49f, 1f), 1f);
            GUI.Label(new Rect(rect.x + 8f, rect.y + 6f, rect.width - 16f, rect.height - 12f), GUI.tooltip, _small);
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

        private static string BranchTitle(TalentBranch branch)
        {
            switch (branch)
            {
                case TalentBranch.Legacy: return "НАСЛЕДИЕ";
                case TalentBranch.Guardian: return "СТРАЖ";
                case TalentBranch.GuardianBastion: return "БАСТИОН";
                case TalentBranch.GuardianUnbroken: return "НЕСОКРУШИМЫЙ";
                case TalentBranch.Slayer: return "ИСТРЕБИТЕЛЬ";
                case TalentBranch.SlayerExecutioner: return "ПАЛАЧ";
                case TalentBranch.SlayerHunter: return "ОХОТНИК";
                case TalentBranch.Pathfinder: return "СЛЕДОПЫТ";
                case TalentBranch.PathfinderScout: return "РАЗВЕДЧИК";
                case TalentBranch.PathfinderAcrobat: return "АКРОБАТ";
                case TalentBranch.Seeker: return "ИСКАТЕЛЬ";
                case TalentBranch.SeekerMerchant: return "ТОРГОВЕЦ";
                default: return "СТАРАТЕЛЬ";
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
            if (id == "Executioner") return "Палач";
            if (id == "Hunter") return "Охотник";
            if (id == "Scout") return "Разведчик";
            if (id == "Acrobat") return "Акробат";
            if (id == "Merchant") return "Торговец";
            if (id == "Prospector") return "Старатель";
            return "не выбрана";
        }

        private static string DisplayName(ItemDef item)
        {
            if (item == null) return "<null>";
            var localized = Language.GetString(item.nameToken);
            return string.IsNullOrWhiteSpace(localized) ? item.name : localized;
        }

        private static bool Contains(string text, string part) =>
            !string.IsNullOrEmpty(text) && text.IndexOf(part, StringComparison.OrdinalIgnoreCase) >= 0;

        private void SetStatus(string text)
        {
            _status = text ?? string.Empty;
            _statusUntil = Time.unscaledTime + 4f;
        }

        private void EnsureStyles()
        {
            if (_windowStyle != null) return;
            _windowTexture = new Texture2D(1, 1);
            _windowTexture.SetPixel(0, 0, new Color(0.022f, 0.029f, 0.034f, 1f));
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
            _small = new GUIStyle(GUI.skin.label) { fontSize = 12, wordWrap = true, normal = { textColor = new Color(0.77f, 0.82f, 0.85f, 1f) } };
            _tiny = new GUIStyle(GUI.skin.label) { fontSize = 10, alignment = TextAnchor.MiddleLeft, normal = { textColor = new Color(0.82f, 0.89f, 0.93f, 1f) } };
            _nodeTitle = new GUIStyle(GUI.skin.label) { fontSize = 11, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _nodeDesc = new GUIStyle(GUI.skin.label) { fontSize = 10, wordWrap = true, normal = { textColor = new Color(0.84f, 0.88f, 0.90f, 1f) } };
            _center = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 12, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _hud = new GUIStyle(_center) { fontSize = 11 };
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

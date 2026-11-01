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
    public sealed class MetaProgressionUIV3 : MonoBehaviour
    {
        private Rect _window = new Rect(32f, 28f, 1540f, 910f);
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
        private readonly Dictionary<string, Sprite> _talentIconCache = new Dictionary<string, Sprite>();

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

            _window.width = Mathf.Min(1540f, Mathf.Max(920f, Screen.width - 24f));
            _window.height = Mathf.Min(910f, Mathf.Max(620f, Screen.height - 24f));
            _window.x = Mathf.Clamp(_window.x, 0f, Mathf.Max(0f, Screen.width - _window.width));
            _window.y = Mathf.Clamp(_window.y, 0f, Mathf.Max(0f, Screen.height - _window.height));

            _window = GUI.Window(941206, _window, DrawWindow, "PETRICHOR LEGACY — META PROGRESSION", _windowStyle);
            GUI.BringWindowToFront(941206);
        }

        private void DrawXpHud()
        {
            var p = SaveService.Current;
            var required = Mathf.Max(1, ProgressionService.XpRequiredForNextLevel(p.level));
            var fraction = Mathf.Clamp01((float)p.currentXp / required);
            var width = Mathf.Clamp(Screen.width * 0.16f, 220f, 285f);
            var outer = new Rect(10f, 13f, width, 20f);
            FillRect(outer, new Color(0.010f, 0.014f, 0.018f, 0.94f));
            var inner = new Rect(outer.x + 2f, outer.y + 2f, outer.width - 4f, outer.height - 4f);
            FillRect(new Rect(inner.x, inner.y, inner.width * fraction, inner.height), new Color(0.10f, 0.48f, 0.68f, 0.94f));
            DrawBorder(outer, new Color(0.42f, 0.61f, 0.70f, 1f), 1f);
            GUI.Label(outer, $"УР. {p.level}   {p.currentXp:N0}/{required:N0}", _hud);

            var elapsed = Time.unscaledTime - ProgressionService.LastAwardTime;
            if (elapsed >= 0f && elapsed < 2.8f && ProgressionService.LastAwardAmount > 0)
                GUI.Label(new Rect(outer.x, outer.yMax + 1f, outer.width + 80f, 17f), $"+{ProgressionService.LastAwardAmount:N0} XP — {ProgressionService.LastAwardReason}", _tiny);
        }

        private void DrawWindow(int id)
        {
            var p = SaveService.Current;
            GUI.Label(new Rect(16f, 26f, _window.width - 32f, 24f),
                $"Ур. {p.level}   Престиж {ProgressionService.PrestigeLevel(p.level)}   |   Очки: {p.unspentTalentPoints} талантов • {p.unspentMasteryPoints} мастерства • {p.unspentPerfectionPoints} совершенства   |   Активно: {ClassDisplay(p.activeClass)} / {SpecDisplay(p.activeSpecialization)}",
                _header);

            var tabY = 55f;
            var labels = new[] { "ДРЕВО", "МАСТЕРСТВО", "СОВЕРШЕНСТВО", "АРСЕНАЛ" };
            var tabWidth = (_window.width - 182f) / labels.Length;
            for (var i = 0; i < labels.Length; i++)
                if (GUI.Toggle(new Rect(12f + i * tabWidth, tabY, tabWidth - 5f, 31f), _tab == i, labels[i], "Button")) _tab = i;
            if (GUI.Button(new Rect(_window.width - 158f, tabY, 145f, 31f), "Закрыть")) SetOpen(false);

            var content = new Rect(12f, 93f, _window.width - 24f, _window.height - 123f);
            FillRect(content, new Color(0.022f, 0.028f, 0.033f, 1f));
            DrawBorder(content, new Color(0.16f, 0.23f, 0.27f, 1f), 1f);

            switch (_tab)
            {
                case 0: DrawTalentPage(p, content); break;
                case 1: DrawMasteryPage(p, content); break;
                case 2: DrawPerfectionPage(p, content); break;
                default: DrawLoadoutArea(p, content); break;
            }

            if (!string.IsNullOrEmpty(_status) && Time.unscaledTime < _statusUntil)
                GUI.Label(new Rect(18f, _window.height - 25f, _window.width - 36f, 18f), _status, _center);

            DrawTooltip();
            GUI.DragWindow(new Rect(0, 0, _window.width, 22f));
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
                if (GUI.Toggle(new Rect(area.x + 7f + i * w, y, w - 5f, 29f), selected, BranchTitle(branch), "Button"))
                {
                    if (!SameCategory(_selectedBranch, branch))
                    {
                        _selectedBranch = branch;
                        _pendingSpecId = string.Empty;
                        _treeScroll = Vector2.zero;
                    }
                }
            }

            var page = new Rect(area.x + 7f, area.y + 42f, area.width - 14f, area.height - 49f);
            if (_selectedBranch == TalentBranch.Legacy) DrawLegacySheet(p, page);
            else DrawClassSheet(p, page);
        }

        private void DrawLegacySheet(ProfileProgress p, Rect area)
        {
            GUI.Label(new Rect(area.x + 4f, area.y + 2f, area.width - 200f, 27f), "НАСЛЕДИЕ — универсальные бонусы", _header);
            if (GUI.Button(new Rect(area.xMax - 186f, area.y, 180f, 27f), "Сбросить таланты"))
            {
                ProgressionService.Respec(p);
                _pendingSpecId = string.Empty;
                SetStatus("Обычные таланты сброшены. Мастерство и Совершенство сохранены.");
            }

            var canvas = new Rect(area.x, area.y + 33f, area.width, area.height - 33f);
            FillRect(canvas, new Color(0.012f, 0.017f, 0.021f, 1f));
            DrawBorder(canvas, new Color(0.14f, 0.21f, 0.25f, 1f), 1f);
            DrawCompactBranchTree(p, TalentBranch.Legacy, canvas, 62f);
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
            var active = p.activeClass == classId && (p.level < 20 || p.activeSpecialization == selectedSpec);

            var actionBar = new Rect(area.x, area.y, area.width, 32f);
            FillRect(actionBar, new Color(0.026f, 0.034f, 0.040f, 1f));
            DrawBorder(actionBar, new Color(0.14f, 0.21f, 0.25f, 1f), 1f);
            GUI.Label(new Rect(actionBar.x + 8f, actionBar.y + 5f, Mathf.Max(260f, actionBar.width - 650f), 22f),
                $"{ClassDisplay(classId).ToUpperInvariant()}  •  {SpecDisplay(selectedSpec)}" + (active ? "  •  АКТИВНЫЙ БИЛД" : string.Empty), _header);

            var resetRect = new Rect(actionBar.xMax - 178f, actionBar.y + 3f, 170f, 26f);
            var activateRect = new Rect(resetRect.x - 248f, actionBar.y + 3f, 238f, 26f);
            var activateText = active ? "АКТИВНО" : p.level < 10 ? "ОТКРОЕТСЯ НА 10 УР." : p.level < 20 ? "АКТИВИРОВАТЬ КЛАСС" : "АКТИВИРОВАТЬ КЛАСС + СПЕК";
            GUI.enabled = !active && p.level >= 10 && Run.instance == null;
            if (GUI.Button(activateRect, activateText)) ActivateClassSelection(p, classId, selectedSpec);
            GUI.enabled = true;
            if (GUI.Button(resetRect, "Сбросить таланты"))
            {
                ProgressionService.Respec(p);
                _pendingSpecId = string.Empty;
                SetStatus("Обычные таланты сброшены. Мастерство и Совершенство сохранены.");
                return;
            }

            var viewport = new Rect(area.x, area.y + 37f, area.width, area.height - 37f);
            const float contentHeight = 590f;
            _treeScroll = GUI.BeginScrollView(viewport, _treeScroll, new Rect(0f, 0f, viewport.width - 18f, Mathf.Max(contentHeight, viewport.height - 2f)));
            var innerW = viewport.width - 20f;

            var basePanel = new Rect(4f, 3f, innerW - 8f, 276f);
            DrawBranchPanel(p, baseBranch, basePanel, $"ОСНОВА — {ClassDisplay(classId)}", false, string.Empty);

            const float lowerY = 286f;
            const float gap = 9f;
            var half = (innerW - gap - 8f) * 0.5f;
            var left = new Rect(4f, lowerY, half, 296f);
            var right = new Rect(4f + half + gap, lowerY, half, 296f);
            DrawBranchPanel(p, spec1, left, BranchTitle(spec1), true, TalentCatalog.SpecForBranch(spec1));
            DrawBranchPanel(p, spec2, right, BranchTitle(spec2), true, TalentCatalog.SpecForBranch(spec2));

            GUI.EndScrollView();
        }

        private void DrawBranchPanel(ProfileProgress p, TalentBranch branch, Rect panel, string title, bool selectableSpec, string specId)
        {
            var selected = selectableSpec && _pendingSpecId == specId;
            FillRect(panel, selected ? new Color(0.024f, 0.052f, 0.063f, 1f) : new Color(0.012f, 0.017f, 0.021f, 1f));
            DrawBorder(panel, selected ? new Color(0.18f, 0.56f, 0.66f, 1f) : new Color(0.13f, 0.20f, 0.24f, 1f), selected ? 2f : 1f);

            var headerRect = new Rect(panel.x + 6f, panel.y + 4f, panel.width - 12f, 24f);
            if (selectableSpec)
            {
                if (GUI.Toggle(headerRect, selected, selected ? $"✓ {title}" : title, "Button")) _pendingSpecId = specId;
            }
            else GUI.Label(headerRect, title, _center);

            var tree = new Rect(panel.x + 4f, panel.y + 31f, panel.width - 8f, panel.height - 35f);
            DrawCompactBranchTree(p, branch, tree, 58f);
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
                    active ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));
            }
            foreach (var def in defs) DrawTalentNodeCompact(p, def, GetCompactNodeRect(def, canvas, rowStep));
        }

        private Rect GetCompactNodeRect(TalentDef def, Rect canvas, float rowStep)
        {
            const float gap = 7f;
            var nodeWidth = Mathf.Clamp((canvas.width - 18f - gap * 2f) / 3f, 136f, 276f);
            const float nodeHeight = 52f;
            var total = nodeWidth * 3f + gap * 2f;
            var startX = canvas.x + Mathf.Max(4f, (canvas.width - total) * 0.5f);
            var x = startX + def.TreeColumn * (nodeWidth + gap);
            var y = canvas.y + 3f + def.TreeRow * rowStep;
            return new Rect(x, y, nodeWidth, nodeHeight);
        }

        private void DrawTalentNodeCompact(ProfileProgress p, TalentDef def, Rect rect)
        {
            var rank = TalentCatalog.GetRank(p, def.Id);
            var prereq = TalentCatalog.PrerequisiteMet(p, def);
            var levelOk = p.level >= def.UnlockLevel;
            var maxed = rank >= def.MaxRank;
            var activeBranch = TalentCatalog.IsBranchActive(p, def.Branch);

            var fill = maxed ? new Color(0.048f, 0.18f, 0.14f, 1f) : activeBranch ? new Color(0.055f, 0.118f, 0.14f, 1f) : new Color(0.050f, 0.058f, 0.064f, 1f);
            FillRect(rect, fill);
            DrawBorder(rect, maxed ? new Color(0.23f, 0.68f, 0.48f, 1f) : activeBranch ? new Color(0.18f, 0.50f, 0.59f, 1f) : new Color(0.20f, 0.26f, 0.29f, 1f), 1f);

            var iconRect = new Rect(rect.x + 4f, rect.y + 5f, 38f, 38f);
            FillRect(iconRect, new Color(0.020f, 0.025f, 0.030f, 0.95f));
            DrawSprite(iconRect, GetTalentIcon(def), levelOk ? Color.white : new Color(0.40f, 0.40f, 0.40f, 0.85f));
            DrawBorder(iconRect, new Color(0.25f, 0.32f, 0.35f, 1f), 1f);

            GUI.Label(new Rect(rect.x + 46f, rect.y + 2f, rect.width - 50f, 16f), $"{def.Name} [{rank}/{def.MaxRank}]", _nodeTitle);
            GUI.Label(new Rect(rect.x + 46f, rect.y + 18f, rect.width - 50f, 15f), ShortEffect(def.Description), _tiny);

            var label = maxed ? "Изучено" : !levelOk ? $"ур. {def.UnlockLevel}" : !prereq ? "нужен предыдущий" : $"Изучить — {def.PointCost}";
            GUI.enabled = levelOk && prereq && !maxed && p.unspentTalentPoints >= def.PointCost;
            if (GUI.Button(new Rect(rect.x + 46f, rect.yMax - 17f, rect.width - 51f, 15f), label))
            {
                if (!ProgressionService.TryBuyTalent(p, def.Id, out var error)) SetStatus(error);
                else SetStatus($"Изучено: {def.Name}.");
            }
            GUI.enabled = true;

            var tooltip = $"{def.Name} [{rank}/{def.MaxRank}]\n{def.Description}\nОткрытие: уровень {def.UnlockLevel}";
            if (!prereq) tooltip += "\nТребуется предыдущий узел.";
            tooltip += "\nИконка — визуальный ориентир эффекта; предмет не выдаётся.";
            GUI.Label(rect, new GUIContent(string.Empty, tooltip));
        }

        private Sprite GetTalentIcon(TalentDef def)
        {
            if (def == null) return null;
            if (_talentIconCache.TryGetValue(def.Id, out var cached)) return cached;
            var preferred = PreferredIconItem(def.Id);
            Sprite sprite = null;
            if (!string.IsNullOrEmpty(preferred))
            {
                var item = ItemCatalog.allItemDefs.FirstOrDefault(x => x != null && string.Equals(x.name, preferred, StringComparison.OrdinalIgnoreCase));
                sprite = item?.pickupIconSprite;
            }
            if (sprite == null)
            {
                var fallback = ItemCatalog.allItemDefs.FirstOrDefault(x => x != null && x.tier == ItemTier.Tier1 && x.pickupIconSprite != null);
                sprite = fallback?.pickupIconSprite;
            }
            _talentIconCache[def.Id] = sprite;
            return sprite;
        }

        private static string PreferredIconItem(string id)
        {
            id = (id ?? string.Empty).ToLowerInvariant();
            if (id.Contains("crit")) return "CritGlasses";
            if (id.Contains("cooldown") || id.Contains("technique")) return "Bandolier";
            if (id.Contains("attack") || id.Contains("haste") || id.Contains("tempo")) return "Syringe";
            if (id.Contains("jump") || id.Contains("acro") || id.Contains("air")) return "Feather";
            if (id.Contains("sprint")) return "SprintBonus";
            if (id.Contains("move") || id.Contains("route") || id.Contains("flow") || id.Contains("adrenaline") || id.Contains("pursuit")) return "Hoof";
            if (id.Contains("shield") || id.Contains("barrier") || id.Contains("stability") || id.Contains("bastion")) return "PersonalShield";
            if (id.Contains("armor") || id.Contains("hardened") || id.Contains("iron")) return "ArmorPlate";
            if (id.Contains("regen") || id.Contains("heal") || id.Contains("reserve") || id.Contains("breath")) return "Medkit";
            if (id.Contains("gold") || id.Contains("merchant") || id.Contains("capital") || id.Contains("treasure")) return "GoldOnHurt";
            if (id.Contains("pack") || id.Contains("supply")) return "EquipmentMagazine";
            if (id.Contains("hunter") || id.Contains("boss") || id.Contains("giant")) return "BossDamageBonus";
            if (id.Contains("damage") || id.Contains("power") || id.Contains("focus") || id.Contains("verdict")) return "Crowbar";
            if (id.Contains("health") || id.Contains("vitality") || id.Contains("endurance") || id.Contains("unbroken") || id.Contains("hp")) return "Infusion";
            return "Infusion";
        }

        private static string ShortEffect(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return string.Empty;
            var clean = text.Replace("\n", " ").Trim();
            return clean.Length <= 48 ? clean : clean.Substring(0, 45) + "…";
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
            else _pendingSpecId = TalentCatalog.SpecForBranch(first);
        }

        private void DrawMasteryPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 10f, area.y + 10f, area.width - 20f, area.height - 20f));
            GUILayout.Label($"БЕСКОНЕЧНОЕ МАСТЕРСТВО   •   доступно очков: {p.unspentMasteryPoints}", _header);
            GUILayout.Label("После 25 / 50 / 100 / 200 рангов новые ранги дают 75% / 50% / 30% / 20% базового эффекта. Работает мастерство только активного класса.", _small);
            GUILayout.Space(6f);
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
            GUILayout.BeginArea(new Rect(area.x + 10f, area.y + 10f, area.width - 20f, area.height - 20f));
            GUILayout.Label($"СОВЕРШЕНСТВО   •   1 очко каждые 25 уровней   •   доступно: {p.unspentPerfectionPoints}", _header);
            GUILayout.Label("Престиж не сбрасывает уровень. Каждые 100 уровней он открывает следующий слой долгой прогрессии.", _small);
            GUILayout.Space(6f);
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
                if (GUILayout.Button(rank >= def.MaxRank ? "Изучено" : "Изучить", GUILayout.Width(130f), GUILayout.Height(40f)))
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
            GUI.Label(new Rect(area.x + 10f, area.y + 7f, area.width - 20f, 23f), $"АРСЕНАЛ — вместимость {used}/{capacity}", _header);
            GUI.Label(new Rect(area.x + 10f, area.y + 28f, area.width - 20f, 19f), "ЛКМ — добавить • ПКМ — убрать одну копию • Красный/Lunar/Hallowed: максимум один высокий тир суммарно", _small);

            var searchY = area.y + 51f;
            GUI.Label(new Rect(area.x + 10f, searchY + 3f, 50f, 21f), "Поиск:", _small);
            _search = GUI.TextField(new Rect(area.x + 61f, searchY, 235f, 24f), _search ?? string.Empty);

            var filterLabels = new[] { "Все", "Белые", "Зелёные", "Boss", "Void", "Красные", "Lunar", "Hallowed" };
            var fx = area.x + 310f;
            var fw = Mathf.Max(66f, (area.width - 330f) / filterLabels.Length);
            for (var i = 0; i < filterLabels.Length; i++)
                if (GUI.Toggle(new Rect(fx + i * fw, searchY, fw - 4f, 24f), _itemFilter == i, filterLabels[i], "Button")) _itemFilter = i;

            var bodyY = searchY + 32f;
            var bodyH = area.yMax - bodyY - 8f;
            var selectedW = Mathf.Clamp(area.width * 0.24f, 255f, 360f);
            var gridRect = new Rect(area.x + 8f, bodyY, area.width - selectedW - 21f, bodyH);
            var selectedRect = new Rect(gridRect.xMax + 8f, bodyY, selectedW, bodyH);
            FillRect(gridRect, new Color(0.010f, 0.015f, 0.019f, 1f));
            FillRect(selectedRect, new Color(0.014f, 0.020f, 0.025f, 1f));
            DrawBorder(gridRect, new Color(0.13f, 0.20f, 0.24f, 1f), 1f);
            DrawBorder(selectedRect, new Color(0.13f, 0.20f, 0.24f, 1f), 1f);

            var userProfile = LocalUserManager.GetFirstLocalUser()?.userProfile;
            IEnumerable<ItemDef> items = StartingLoadoutService.EnumerateEligibleItems(p, userProfile);
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
            const float tile = 78f;
            const float gap = 6f;
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
            GUI.Label(new Rect(rect.x + 7f, rect.y + 4f, rect.width - 14f, 21f), "ВЫБРАНО", _center);
            var records = p.startingLoadout.Where(x => x.count > 0).ToList();
            const float tile = 68f;
            const float gap = 5f;
            var view = new Rect(rect.x + 4f, rect.y + 27f, rect.width - 8f, rect.height - 31f);
            var cols = Mathf.Max(2, Mathf.FloorToInt((view.width - gap) / (tile + gap)));
            var rows = Mathf.CeilToInt(records.Count / (float)cols);
            var contentHeight = Mathf.Max(view.height - 4f, 5f + rows * (tile + gap));
            _selectedScroll = GUI.BeginScrollView(view, _selectedScroll, new Rect(0f, 0f, view.width - 16f, contentHeight));
            for (var i = 0; i < records.Count; i++)
            {
                var item = StartingLoadoutService.FindItem(records[i].itemName);
                if (item == null) continue;
                var col = i % cols;
                var row = i / cols;
                DrawSelectedTile(p, item, records[i].count, new Rect(3f + col * (tile + gap), 3f + row * (tile + gap), tile, tile));
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

            var iconRect = new Rect(rect.x + 5f, rect.y + 5f, rect.width - 10f, rect.height - 10f);
            DrawSprite(iconRect, item.pickupIconSprite, canFit ? Color.white : new Color(0.42f, 0.42f, 0.42f, 0.84f));
            if (item.pickupIconSprite == null) GUI.Label(iconRect, "?", _center);

            if (selected > 0)
            {
                var badge = new Rect(rect.xMax - 25f, rect.y + 3f, 21f, 18f);
                FillRect(badge, new Color(0.02f, 0.025f, 0.03f, 0.92f));
                GUI.Label(badge, $"x{selected}", _tileLabel);
            }
            var costRect = new Rect(rect.x + 3f, rect.yMax - 20f, 32f, 17f);
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
            DrawSprite(new Rect(rect.x + 4f, rect.y + 4f, rect.width - 8f, rect.height - 8f), item.pickupIconSprite, Color.white);
            var badge = new Rect(rect.xMax - 26f, rect.y + 3f, 22f, 18f);
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
            var width = 360f;
            var height = Mathf.Max(55f, _small.CalcHeight(new GUIContent(GUI.tooltip), width - 16f) + 12f);
            var pos = Event.current.mousePosition;
            var rect = new Rect(pos.x + 17f, pos.y + 17f, width, height);
            rect.x = Mathf.Min(rect.x, _window.width - width - 7f);
            rect.y = Mathf.Min(rect.y, _window.height - height - 7f);
            FillRect(rect, new Color(0.013f, 0.018f, 0.022f, 0.99f));
            DrawBorder(rect, new Color(0.28f, 0.41f, 0.47f, 1f), 1f);
            GUI.Label(new Rect(rect.x + 7f, rect.y + 5f, rect.width - 14f, rect.height - 10f), GUI.tooltip, _small);
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
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                alignment = TextAnchor.UpperCenter,
                padding = new RectOffset(7, 7, 7, 7)
            };
            _header = new GUIStyle(GUI.skin.label) { fontSize = 14, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _small = new GUIStyle(GUI.skin.label) { fontSize = 11, wordWrap = true, normal = { textColor = new Color(0.77f, 0.82f, 0.85f, 1f) } };
            _tiny = new GUIStyle(GUI.skin.label) { fontSize = 9, alignment = TextAnchor.MiddleLeft, clipping = TextClipping.Clip, normal = { textColor = new Color(0.82f, 0.89f, 0.93f, 1f) } };
            _nodeTitle = new GUIStyle(GUI.skin.label) { fontSize = 10, fontStyle = FontStyle.Bold, clipping = TextClipping.Clip, normal = { textColor = Color.white } };
            _nodeDesc = new GUIStyle(GUI.skin.label) { fontSize = 10, wordWrap = true, normal = { textColor = new Color(0.84f, 0.88f, 0.90f, 1f) } };
            _center = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 11, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _hud = new GUIStyle(_center) { fontSize = 10 };
            _tileLabel = new GUIStyle(_center) { fontSize = 9 };
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

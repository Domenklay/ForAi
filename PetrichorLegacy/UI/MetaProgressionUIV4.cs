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
    public sealed class MetaProgressionUIV4 : MonoBehaviour
    {
        private Rect _window = new Rect(20f, 20f, 1540f, 910f);
        private bool _open;
        private int _tab;
        private TalentBranch _selectedBranch = TalentBranch.Legacy;
        private string _pendingSpecId = string.Empty;
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
        private GUIStyle _center;
        private GUIStyle _hud;
        private GUIStyle _tileLabel;
        private Texture2D _windowTexture;

        private readonly PickupIconResolver _icons = new PickupIconResolver();
        private readonly Dictionary<string, ItemDef> _talentItemCache = new Dictionary<string, ItemDef>();

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
            _icons.Dispose();
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

            _window.width = Mathf.Min(1540f, Mathf.Max(900f, Screen.width - 12f));
            _window.height = Mathf.Min(910f, Mathf.Max(600f, Screen.height - 12f));
            _window.x = Mathf.Clamp(_window.x, 0f, Mathf.Max(0f, Screen.width - _window.width));
            _window.y = Mathf.Clamp(_window.y, 0f, Mathf.Max(0f, Screen.height - _window.height));

            _window = GUI.Window(941207, _window, DrawWindow, "PETRICHOR LEGACY — META PROGRESSION", _windowStyle);
            GUI.BringWindowToFront(941207);
        }

        private void DrawXpHud()
        {
            var p = SaveService.Current;
            var required = Mathf.Max(1, ProgressionService.XpRequiredForNextLevel(p.level));
            var fraction = Mathf.Clamp01((float)p.currentXp / required);
            var width = Mathf.Clamp(Screen.width * 0.15f, 205f, 270f);
            var outer = new Rect(8f, 11f, width, 19f);
            FillRect(outer, new Color(0.010f, 0.014f, 0.018f, 0.94f));
            var inner = new Rect(outer.x + 2f, outer.y + 2f, outer.width - 4f, outer.height - 4f);
            FillRect(new Rect(inner.x, inner.y, inner.width * fraction, inner.height), new Color(0.10f, 0.48f, 0.68f, 0.94f));
            DrawBorder(outer, new Color(0.42f, 0.61f, 0.70f, 1f), 1f);
            GUI.Label(outer, $"УР. {p.level}  {p.currentXp:N0}/{required:N0}", _hud);

            var elapsed = Time.unscaledTime - ProgressionService.LastAwardTime;
            if (elapsed >= 0f && elapsed < 2.8f && ProgressionService.LastAwardAmount > 0)
                GUI.Label(new Rect(outer.x, outer.yMax + 1f, outer.width + 110f, 17f), $"+{ProgressionService.LastAwardAmount:N0} XP — {ProgressionService.LastAwardReason}", _tiny);
        }

        private void DrawWindow(int id)
        {
            var p = SaveService.Current;
            GUI.Label(new Rect(15f, 25f, _window.width - 30f, 23f),
                $"Ур. {p.level}   Престиж {ProgressionService.PrestigeLevel(p.level)}   |   Очки: {p.unspentTalentPoints} талантов • {p.unspentMasteryPoints} мастерства • {p.unspentPerfectionPoints} совершенства   |   Активно: {ClassDisplay(p.activeClass)} / {SpecDisplay(p.activeSpecialization)}",
                _header);

            var tabY = 53f;
            var labels = new[] { "ДРЕВО", "МАСТЕРСТВО", "СОВЕРШЕНСТВО", "АРСЕНАЛ" };
            var tabWidth = (_window.width - 176f) / labels.Length;
            for (var i = 0; i < labels.Length; i++)
                if (GUI.Toggle(new Rect(11f + i * tabWidth, tabY, tabWidth - 5f, 30f), _tab == i, labels[i], "Button")) _tab = i;
            if (GUI.Button(new Rect(_window.width - 153f, tabY, 142f, 30f), "Закрыть")) SetOpen(false);

            var content = new Rect(11f, 90f, _window.width - 22f, _window.height - 119f);
            FillRect(content, new Color(0.021f, 0.027f, 0.032f, 1f));
            DrawBorder(content, new Color(0.16f, 0.23f, 0.27f, 1f), 1f);

            switch (_tab)
            {
                case 0: DrawTalentPage(p, content); break;
                case 1: DrawMasteryPage(p, content); break;
                case 2: DrawPerfectionPage(p, content); break;
                default: DrawLoadoutArea(p, content); break;
            }

            if (!string.IsNullOrEmpty(_status) && Time.unscaledTime < _statusUntil)
                GUI.Label(new Rect(18f, _window.height - 24f, _window.width - 36f, 18f), _status, _center);

            DrawTooltip();
            GUI.DragWindow(new Rect(0, 0, _window.width, 21f));
        }

        private void DrawTalentPage(ProfileProgress p, Rect area)
        {
            var categories = new[] { TalentBranch.Legacy, TalentBranch.Guardian, TalentBranch.Slayer, TalentBranch.Pathfinder, TalentBranch.Seeker };
            var y = area.y + 6f;
            var w = (area.width - 12f) / categories.Length;
            for (var i = 0; i < categories.Length; i++)
            {
                var branch = categories[i];
                var selected = SameCategory(_selectedBranch, branch);
                if (GUI.Toggle(new Rect(area.x + 6f + i * w, y, w - 5f, 28f), selected, BranchTitle(branch), "Button"))
                {
                    if (!SameCategory(_selectedBranch, branch))
                    {
                        _selectedBranch = branch;
                        _pendingSpecId = string.Empty;
                    }
                }
            }

            var page = new Rect(area.x + 6f, area.y + 39f, area.width - 12f, area.height - 45f);
            if (_selectedBranch == TalentBranch.Legacy) DrawLegacySheet(p, page);
            else DrawClassSheet(p, page);
        }

        private void DrawLegacySheet(ProfileProgress p, Rect area)
        {
            var bar = new Rect(area.x, area.y, area.width, 31f);
            FillRect(bar, new Color(0.026f, 0.034f, 0.040f, 1f));
            DrawBorder(bar, new Color(0.14f, 0.21f, 0.25f, 1f), 1f);
            GUI.Label(new Rect(bar.x + 8f, bar.y + 4f, bar.width - 190f, 22f), "НАСЛЕДИЕ — универсальные бонусы", _header);
            if (GUI.Button(new Rect(bar.xMax - 174f, bar.y + 3f, 166f, 25f), "Сбросить таланты"))
            {
                ProgressionService.Respec(p);
                _pendingSpecId = string.Empty;
                SetStatus("Обычные таланты сброшены. Мастерство и Совершенство сохранены.");
            }

            var panel = new Rect(area.x, area.y + 36f, area.width, area.height - 36f);
            FillRect(panel, new Color(0.011f, 0.016f, 0.020f, 1f));
            DrawBorder(panel, new Color(0.13f, 0.20f, 0.24f, 1f), 1f);
            DrawBranchTree(p, TalentBranch.Legacy, new Rect(panel.x + 5f, panel.y + 6f, panel.width - 10f, panel.height - 12f));
        }

        private void DrawClassSheet(ProfileProgress p, Rect area)
        {
            var classId = TalentCatalog.ClassForBranch(_selectedBranch);
            if (string.IsNullOrEmpty(classId)) return;
            var baseBranch = BaseBranchForClass(classId);
            var spec1 = FirstSpecBranch(classId);
            var spec2 = SecondSpecBranch(classId);
            EnsurePendingSpec(p, classId, spec1);

            var selectedSpec = _pendingSpecId;
            var active = p.activeClass == classId && (p.level < 20 || p.activeSpecialization == selectedSpec);

            var actionBar = new Rect(area.x, area.y, area.width, 31f);
            FillRect(actionBar, new Color(0.026f, 0.034f, 0.040f, 1f));
            DrawBorder(actionBar, new Color(0.14f, 0.21f, 0.25f, 1f), 1f);

            var resetW = 152f;
            var activateW = 220f;
            var gap = 7f;
            var resetRect = new Rect(actionBar.xMax - resetW - 7f, actionBar.y + 3f, resetW, 25f);
            var activateRect = new Rect(resetRect.x - activateW - gap, actionBar.y + 3f, activateW, 25f);
            var titleW = Mathf.Max(220f, activateRect.x - actionBar.x - 14f);
            GUI.Label(new Rect(actionBar.x + 7f, actionBar.y + 4f, titleW, 22f),
                $"{ClassDisplay(classId).ToUpperInvariant()} • {SpecDisplay(selectedSpec)}" + (active ? " • АКТИВНО" : string.Empty), _header);

            var activateText = active ? "АКТИВНЫЙ БИЛД" : p.level < 10 ? "ОТКРОЕТСЯ НА 10 УР." : p.level < 20 ? "АКТИВИРОВАТЬ КЛАСС" : "АКТИВИРОВАТЬ КЛАСС + СПЕК";
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

            var body = new Rect(area.x, area.y + 36f, area.width, area.height - 36f);
            var gapY = 7f;
            var baseH = Mathf.Clamp(body.height * 0.43f, 205f, 255f);
            var specH = body.height - baseH - gapY;
            var gapX = 8f;
            var halfW = (body.width - gapX) * 0.5f;

            var basePanel = new Rect(body.x, body.y, body.width, baseH);
            var leftPanel = new Rect(body.x, body.y + baseH + gapY, halfW, specH);
            var rightPanel = new Rect(body.x + halfW + gapX, body.y + baseH + gapY, halfW, specH);

            DrawBranchPanel(p, baseBranch, basePanel, $"ОСНОВА — {ClassDisplay(classId)}", false, string.Empty);
            DrawBranchPanel(p, spec1, leftPanel, BranchTitle(spec1), true, TalentCatalog.SpecForBranch(spec1));
            DrawBranchPanel(p, spec2, rightPanel, BranchTitle(spec2), true, TalentCatalog.SpecForBranch(spec2));
        }

        private void DrawBranchPanel(ProfileProgress p, TalentBranch branch, Rect panel, string title, bool selectableSpec, string specId)
        {
            var selected = selectableSpec && _pendingSpecId == specId;
            FillRect(panel, selected ? new Color(0.024f, 0.052f, 0.063f, 1f) : new Color(0.011f, 0.016f, 0.020f, 1f));
            DrawBorder(panel, selected ? new Color(0.18f, 0.56f, 0.66f, 1f) : new Color(0.13f, 0.20f, 0.24f, 1f), selected ? 2f : 1f);

            var headerRect = new Rect(panel.x + 5f, panel.y + 4f, panel.width - 10f, 23f);
            if (selectableSpec)
            {
                if (GUI.Toggle(headerRect, selected, selected ? $"✓ {title}" : title, "Button")) _pendingSpecId = specId;
            }
            else GUI.Label(headerRect, title, _center);

            DrawBranchTree(p, branch, new Rect(panel.x + 4f, panel.y + 31f, panel.width - 8f, panel.height - 35f));
        }

        private void DrawBranchTree(ProfileProgress p, TalentBranch branch, Rect canvas)
        {
            var defs = TalentCatalog.All.Where(x => x.Branch == branch).ToList();
            if (defs.Count == 0) return;
            var maxRow = Mathf.Max(1, defs.Max(x => x.TreeRow));
            const float nodeH = 48f;
            var rowStep = Mathf.Max(48f, (canvas.height - nodeH - 5f) / maxRow);

            foreach (var def in defs)
            {
                if (string.IsNullOrEmpty(def.PrerequisiteId)) continue;
                var parent = TalentCatalog.Find(def.PrerequisiteId);
                if (parent == null || parent.Branch != branch) continue;
                var active = TalentCatalog.GetRank(p, parent.Id) >= def.PrerequisiteRank;
                DrawConnection(GetNodeRect(parent, canvas, rowStep), GetNodeRect(def, canvas, rowStep),
                    active ? new Color(0.19f, 0.61f, 0.70f, 1f) : new Color(0.14f, 0.17f, 0.19f, 1f));
            }
            foreach (var def in defs) DrawTalentNode(p, def, GetNodeRect(def, canvas, rowStep));
        }

        private Rect GetNodeRect(TalentDef def, Rect canvas, float rowStep)
        {
            const float gap = 7f;
            var nodeW = Mathf.Clamp((canvas.width - 14f - gap * 2f) / 3f, 128f, 280f);
            const float nodeH = 48f;
            var total = nodeW * 3f + gap * 2f;
            var startX = canvas.x + Mathf.Max(3f, (canvas.width - total) * 0.5f);
            return new Rect(startX + def.TreeColumn * (nodeW + gap), canvas.y + 2f + def.TreeRow * rowStep, nodeW, nodeH);
        }

        private void DrawTalentNode(ProfileProgress p, TalentDef def, Rect rect)
        {
            var rank = TalentCatalog.GetRank(p, def.Id);
            var prereq = TalentCatalog.PrerequisiteMet(p, def);
            var levelOk = p.level >= def.UnlockLevel;
            var maxed = rank >= def.MaxRank;
            var activeBranch = TalentCatalog.IsBranchActive(p, def.Branch);

            var fill = maxed ? new Color(0.048f, 0.18f, 0.14f, 1f) : activeBranch ? new Color(0.055f, 0.118f, 0.14f, 1f) : new Color(0.050f, 0.058f, 0.064f, 1f);
            FillRect(rect, fill);
            DrawBorder(rect, maxed ? new Color(0.23f, 0.68f, 0.48f, 1f) : activeBranch ? new Color(0.18f, 0.50f, 0.59f, 1f) : new Color(0.20f, 0.26f, 0.29f, 1f), 1f);

            var iconRect = new Rect(rect.x + 4f, rect.y + 5f, 36f, 36f);
            FillRect(iconRect, new Color(0.018f, 0.023f, 0.027f, 0.96f));
            var icon = GetTalentIcon(def);
            if (icon != null) DrawSprite(iconRect, icon, levelOk ? Color.white : new Color(0.42f, 0.42f, 0.42f, 0.85f));
            else GUI.Label(iconRect, EffectGlyph(def.Id), _center);
            DrawBorder(iconRect, new Color(0.25f, 0.32f, 0.35f, 1f), 1f);

            var textX = rect.x + 44f;
            var textW = rect.width - 48f;
            GUI.Label(new Rect(textX, rect.y + 2f, textW, 15f), $"{def.Name} [{rank}/{def.MaxRank}]", _nodeTitle);
            GUI.Label(new Rect(textX, rect.y + 17f, textW, 13f), ShortEffect(def.Description), _tiny);

            var label = maxed ? "Изучено" : !levelOk ? $"ур. {def.UnlockLevel}" : !prereq ? "нужен предыдущий" : $"Изучить — {def.PointCost}";
            GUI.enabled = levelOk && prereq && !maxed && p.unspentTalentPoints >= def.PointCost;
            if (GUI.Button(new Rect(textX, rect.yMax - 16f, textW, 14f), label))
            {
                if (!ProgressionService.TryBuyTalent(p, def.Id, out var error)) SetStatus(error);
                else SetStatus($"Изучено: {def.Name}.");
            }
            GUI.enabled = true;

            var tooltip = $"{def.Name} [{rank}/{def.MaxRank}]\n{def.Description}\nОткрывается на мета-уровне {def.UnlockLevel}.";
            if (!prereq) tooltip += "\nТребуется предыдущий узел.";
            tooltip += "\nИконка показывает тип эффекта; сам предмет не выдаётся.";
            GUI.Label(rect, new GUIContent(string.Empty, tooltip));
        }

        private Sprite GetTalentIcon(TalentDef def)
        {
            if (def == null) return null;
            if (!_talentItemCache.TryGetValue(def.Id, out var item))
            {
                var preferred = PreferredIconItem(def.Id);
                item = ItemCatalog.allItemDefs.FirstOrDefault(x => x != null && string.Equals(x.name, preferred, StringComparison.OrdinalIgnoreCase));
                _talentItemCache[def.Id] = item;
            }
            return _icons.Resolve(item);
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

        private static string EffectGlyph(string id)
        {
            id = (id ?? string.Empty).ToLowerInvariant();
            if (id.Contains("crit")) return "CR";
            if (id.Contains("armor") || id.Contains("iron")) return "AR";
            if (id.Contains("shield") || id.Contains("barrier")) return "SH";
            if (id.Contains("regen") || id.Contains("heal")) return "+";
            if (id.Contains("gold") || id.Contains("merchant")) return "$";
            if (id.Contains("move") || id.Contains("sprint") || id.Contains("jump")) return ">>";
            if (id.Contains("attack") || id.Contains("damage") || id.Contains("power")) return "AT";
            return "HP";
        }

        private static string ShortEffect(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return string.Empty;
            var clean = text.Replace("\n", " ").Replace(" за ранг.", "/ранг").Replace(" за ранг", "/ранг").Trim();
            return clean.Length <= 36 ? clean : clean.Substring(0, 33) + "…";
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

        private void EnsurePendingSpec(ProfileProgress p, string classId, TalentBranch first)
        {
            if (!string.IsNullOrEmpty(_pendingSpecId) && ProgressionService.SpecBelongsToClass(_pendingSpecId, classId)) return;
            if (p.activeClass == classId && !string.IsNullOrEmpty(p.activeSpecialization) && ProgressionService.SpecBelongsToClass(p.activeSpecialization, classId))
                _pendingSpecId = p.activeSpecialization;
            else _pendingSpecId = TalentCatalog.SpecForBranch(first);
        }

        private void DrawMasteryPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 10f, area.y + 10f, area.width - 20f, area.height - 20f));
            GUILayout.Label($"БЕСКОНЕЧНОЕ МАСТЕРСТВО • доступно очков: {p.unspentMasteryPoints}", _header);
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
                GUILayout.Label(def.Description, _small);
                GUILayout.EndVertical();
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        private void DrawPerfectionPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 10f, area.y + 10f, area.width - 20f, area.height - 20f));
            GUILayout.Label($"СОВЕРШЕНСТВО • 1 очко каждые 25 уровней • доступно: {p.unspentPerfectionPoints}", _header);
            GUILayout.Label("Престиж не сбрасывает уровень. Каждые 100 уровней он открывает следующий слой долгой прогрессии.", _small);
            GUILayout.Space(6f);
            _perfectionScroll = GUILayout.BeginScrollView(_perfectionScroll);
            foreach (var def in PerfectionCatalog.All)
            {
                var rank = PerfectionCatalog.GetRank(p, def.Id);
                GUILayout.BeginHorizontal("box");
                GUILayout.BeginVertical();
                GUILayout.Label($"{def.Name} [{rank}/{def.MaxRank}] — требуется ур. {def.UnlockLevel}", _nodeTitle);
                GUILayout.Label(def.Description, _small);
                GUILayout.EndVertical();
                GUI.enabled = p.level >= def.UnlockLevel && rank < def.MaxRank && p.unspentPerfectionPoints > 0;
                if (GUILayout.Button(rank >= def.MaxRank ? "Изучено" : "Изучить", GUILayout.Width(130f), GUILayout.Height(38f)))
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
            GUI.Label(new Rect(area.x + 9f, area.y + 6f, area.width - 18f, 22f), $"АРСЕНАЛ — вместимость {used}/{capacity}", _header);
            GUI.Label(new Rect(area.x + 9f, area.y + 27f, area.width - 18f, 18f), "ЛКМ — добавить • ПКМ — убрать • Красный/Lunar/Hallowed: максимум один высокий тир суммарно", _small);

            var searchY = area.y + 49f;
            GUI.Label(new Rect(area.x + 9f, searchY + 3f, 49f, 20f), "Поиск:", _small);
            _search = GUI.TextField(new Rect(area.x + 59f, searchY, 230f, 23f), _search ?? string.Empty);

            var filterLabels = new[] { "Все", "Белые", "Зелёные", "Boss", "Void", "Красные", "Lunar", "Hallowed" };
            var fx = area.x + 301f;
            var fw = Mathf.Max(64f, (area.width - 320f) / filterLabels.Length);
            for (var i = 0; i < filterLabels.Length; i++)
                if (GUI.Toggle(new Rect(fx + i * fw, searchY, fw - 4f, 23f), _itemFilter == i, filterLabels[i], "Button")) _itemFilter = i;

            var bodyY = searchY + 31f;
            var bodyH = area.yMax - bodyY - 7f;
            var selectedW = Mathf.Clamp(area.width * 0.24f, 250f, 360f);
            var gridRect = new Rect(area.x + 7f, bodyY, area.width - selectedW - 19f, bodyH);
            var selectedRect = new Rect(gridRect.xMax + 7f, bodyY, selectedW, bodyH);
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
            const float tile = 82f;
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
            const float tile = 72f;
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
            var icon = _icons.Resolve(item);
            if (icon != null) DrawSprite(iconRect, icon, canFit ? Color.white : new Color(0.42f, 0.42f, 0.42f, 0.84f));
            else GUI.Label(iconRect, "…", _center);

            if (selected > 0)
            {
                var badge = new Rect(rect.xMax - 27f, rect.y + 3f, 23f, 18f);
                FillRect(badge, new Color(0.02f, 0.025f, 0.03f, 0.92f));
                GUI.Label(badge, $"x{selected}", _tileLabel);
            }
            var costRect = new Rect(rect.x + 3f, rect.yMax - 20f, 34f, 17f);
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
            var icon = _icons.Resolve(item);
            if (icon != null) DrawSprite(new Rect(rect.x + 4f, rect.y + 4f, rect.width - 8f, rect.height - 8f), icon, Color.white);
            else GUI.Label(rect, "…", _center);
            var badge = new Rect(rect.xMax - 27f, rect.y + 3f, 23f, 18f);
            FillRect(badge, new Color(0.02f, 0.025f, 0.03f, 0.92f));
            GUI.Label(badge, $"x{count}", _tileLabel);
            GUI.Label(rect, new GUIContent(string.Empty, $"{DisplayName(item)} x{count}\n{FriendlyTierName(item)}\nЛКМ или ПКМ — убрать одну копию"));

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

        private static string FriendlyTierName(ItemDef item)
        {
            if (item == null) return "Неизвестный";
            var raw = StartingLoadoutService.TierName(item);
            if (Contains(raw, "Hallowed") || Contains(raw, "Cursed")) return "Освящённый";
            if (Contains(raw, "FoodTier")) return "Особый";
            switch (item.tier)
            {
                case ItemTier.Tier1: return "Обычный (белый)";
                case ItemTier.Tier2: return "Необычный (зелёный)";
                case ItemTier.Tier3: return "Легендарный (красный)";
                case ItemTier.Boss: return "Босс-предмет";
                case ItemTier.Lunar: return "Лунный";
                case ItemTier.VoidTier1:
                case ItemTier.VoidTier2:
                case ItemTier.VoidTier3:
                case ItemTier.VoidBoss: return "Пустотный";
                default: return "Особый";
            }
        }

        private static string BuildItemTooltip(ItemDef item, int selected, int cost, bool canFit)
        {
            var pickup = item != null ? Language.GetString(item.pickupToken) : string.Empty;
            if (string.IsNullOrWhiteSpace(pickup)) pickup = "Без описания";
            return $"{DisplayName(item)}\n{FriendlyTierName(item)}\n{pickup}\nЦена следующей копии: {cost}\nВыбрано: {selected}" + (canFit ? "" : "\nНедостаточно вместимости");
        }

        private void DrawTooltip()
        {
            if (string.IsNullOrEmpty(GUI.tooltip)) return;
            var width = 370f;
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

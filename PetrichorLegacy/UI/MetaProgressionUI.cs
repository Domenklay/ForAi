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
    public sealed class MetaProgressionUI : MonoBehaviour
    {
        private Rect _window = new Rect(60, 45, 1520, 900);
        private bool _open;
        private int _tab;
        private TalentBranch _selectedBranch = TalentBranch.Legacy;
        private Vector2 _itemScroll;
        private Vector2 _selectedScroll;
        private Vector2 _masteryScroll;
        private Vector2 _perfectionScroll;
        private string _search = string.Empty;
        private string _status = string.Empty;
        private float _statusUntil;
        private ConfigEntry<KeyboardShortcut> _toggleKey;

        private bool _cursorCaptured;
        private bool _previousCursorVisible;
        private CursorLockMode _previousCursorLock;

        private GUIStyle _windowStyle;
        private GUIStyle _header;
        private GUIStyle _small;
        private GUIStyle _nodeTitle;
        private GUIStyle _nodeDesc;
        private GUIStyle _center;
        private GUIStyle _hud;
        private Texture2D _windowTexture;

        public void Configure(ConfigEntry<KeyboardShortcut> toggleKey) => _toggleKey = toggleKey;

        private void Update()
        {
            SaveService.RefreshProfile();
            if (_toggleKey != null && _toggleKey.Value.IsDown())
                SetOpen(!_open);

            if (_open)
            {
                // RoR2 can relock the pointer every frame. Force the native cursor above IMGUI while this window is open.
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
            else
            {
                RestoreCursor();
            }
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
            if (Run.instance != null && SaveService.Current != null)
                DrawXpHud();
            if (!_open || SaveService.Current == null) return;

            _window.width = Mathf.Min(1520f, Mathf.Max(900f, Screen.width - 40f));
            _window.height = Mathf.Min(900f, Mathf.Max(600f, Screen.height - 40f));
            _window.x = Mathf.Clamp(_window.x, 0f, Mathf.Max(0f, Screen.width - _window.width));
            _window.y = Mathf.Clamp(_window.y, 0f, Mathf.Max(0f, Screen.height - _window.height));

            _window = GUI.Window(941204, _window, DrawWindow, "PETRICHOR LEGACY — META PROGRESSION", _windowStyle);
            GUI.BringWindowToFront(941204);
        }

        private void DrawXpHud()
        {
            var p = SaveService.Current;
            var required = Mathf.Max(1, ProgressionService.XpRequiredForNextLevel(p.level));
            var fraction = Mathf.Clamp01((float)p.currentXp / required);
            var width = Mathf.Clamp(Screen.width * 0.42f, 430f, 760f);
            var outer = new Rect((Screen.width - width) * 0.5f, 15f, width, 42f);
            FillRect(outer, new Color(0.015f, 0.02f, 0.025f, 0.98f));
            var inner = new Rect(outer.x + 4f, outer.y + 4f, outer.width - 8f, outer.height - 8f);
            FillRect(new Rect(inner.x, inner.y, inner.width * fraction, inner.height), new Color(0.10f, 0.48f, 0.68f, 1f));
            DrawBorder(outer, new Color(0.58f, 0.74f, 0.82f, 1f), 2f);
            GUI.Label(outer, $"УРОВЕНЬ {p.level}   •   ПРЕСТИЖ {ProgressionService.PrestigeLevel(p.level)}   •   XP {p.currentXp:N0} / {required:N0}", _hud);

            var elapsed = Time.unscaledTime - ProgressionService.LastAwardTime;
            if (elapsed >= 0f && elapsed < 3.5f && ProgressionService.LastAwardAmount > 0)
                GUI.Label(new Rect(outer.x, outer.yMax + 2f, outer.width, 24f), $"+{ProgressionService.LastAwardAmount:N0} XP — {ProgressionService.LastAwardReason}", _center);
        }

        private void DrawWindow(int id)
        {
            var p = SaveService.Current;
            GUI.Label(new Rect(18f, 28f, _window.width - 36f, 28f),
                $"Ур. {p.level}   Престиж {ProgressionService.PrestigeLevel(p.level)}   |   Очки: {p.unspentTalentPoints} талантов • {p.unspentMasteryPoints} мастерства • {p.unspentPerfectionPoints} совершенства   |   Активно: {ClassDisplay(p.activeClass)} / {SpecDisplay(p.activeSpecialization)}",
                _header);

            var tabY = 62f;
            var labels = new[] { "ДРЕВО", "МАСТЕРСТВО", "СОВЕРШЕНСТВО", "АРСЕНАЛ" };
            var tabWidth = (_window.width - 190f) / labels.Length;
            for (var i = 0; i < labels.Length; i++)
                if (GUI.Toggle(new Rect(14f + i * tabWidth, tabY, tabWidth - 5f, 34f), _tab == i, labels[i], "Button")) _tab = i;
            if (GUI.Button(new Rect(_window.width - 165f, tabY, 150f, 34f), "Закрыть")) SetOpen(false);

            var content = new Rect(14f, 104f, _window.width - 28f, _window.height - 137f);
            FillRect(content, new Color(0.028f, 0.035f, 0.042f, 1f));
            DrawBorder(content, new Color(0.18f, 0.25f, 0.29f, 1f), 1f);

            switch (_tab)
            {
                case 0: DrawTalentPage(p, content); break;
                case 1: DrawMasteryPage(p, content); break;
                case 2: DrawPerfectionPage(p, content); break;
                default: DrawLoadoutArea(p, content); break;
            }

            if (!string.IsNullOrEmpty(_status) && Time.unscaledTime < _statusUntil)
                GUI.Label(new Rect(20f, _window.height - 29f, _window.width - 40f, 22f), _status, _center);

            GUI.DragWindow(new Rect(0, 0, _window.width, 25f));
        }

        private void DrawTalentPage(ProfileProgress p, Rect area)
        {
            var topY = area.y + 8f;
            var categories = new[]
            {
                TalentBranch.Legacy, TalentBranch.Guardian, TalentBranch.Slayer, TalentBranch.Pathfinder, TalentBranch.Seeker
            };
            var w = (area.width - 16f) / categories.Length;
            for (var i = 0; i < categories.Length; i++)
            {
                var b = categories[i];
                var selected = SameCategory(_selectedBranch, b);
                if (GUI.Toggle(new Rect(area.x + 8f + i * w, topY, w - 5f, 32f), selected, BranchTitle(b), "Button"))
                    _selectedBranch = b;
            }

            var secondY = topY + 38f;
            if (_selectedBranch != TalentBranch.Legacy)
                DrawClassAndSpecControls(p, area, secondY);

            var canvasY = _selectedBranch == TalentBranch.Legacy ? secondY : secondY + 40f;
            var canvas = new Rect(area.x + 8f, canvasY, area.width - 16f, area.yMax - canvasY - 8f);
            FillRect(canvas, new Color(0.018f, 0.023f, 0.028f, 1f));
            DrawBorder(canvas, new Color(0.14f, 0.20f, 0.24f, 1f), 1f);
            DrawBranchTree(p, _selectedBranch, canvas);

            if (GUI.Button(new Rect(area.xMax - 190f, area.y + 48f, 170f, 28f), "Сбросить обычные таланты"))
            {
                ProgressionService.Respec(p);
                SetStatus("Обычные таланты сброшены. Мастерство и Совершенство сохранены.");
            }
        }

        private void DrawClassAndSpecControls(ProfileProgress p, Rect area, float y)
        {
            var classId = TalentCatalog.ClassForBranch(_selectedBranch);
            var baseBranch = BaseBranchForClass(classId);
            var spec1 = FirstSpecBranch(classId);
            var spec2 = SecondSpecBranch(classId);
            var left = area.x + 12f;

            if (GUI.Toggle(new Rect(left, y, 180f, 31f), _selectedBranch == baseBranch, "ОСНОВА", "Button")) _selectedBranch = baseBranch;
            if (GUI.Toggle(new Rect(left + 185f, y, 180f, 31f), _selectedBranch == spec1, BranchTitle(spec1), "Button")) _selectedBranch = spec1;
            if (GUI.Toggle(new Rect(left + 370f, y, 180f, 31f), _selectedBranch == spec2, BranchTitle(spec2), "Button")) _selectedBranch = spec2;

            var activeClass = p.activeClass == classId;
            if (GUI.Button(new Rect(area.xMax - 430f, y, 200f, 31f), activeClass ? "КЛАСС АКТИВЕН" : "Сделать класс активным"))
            {
                if (!ProgressionService.TrySetActiveClass(p, classId, out var error)) SetStatus(error);
                else SetStatus($"Активный класс: {ClassDisplay(classId)}.");
            }

            var specId = TalentCatalog.SpecForBranch(_selectedBranch);
            GUI.enabled = activeClass && !string.IsNullOrEmpty(specId);
            if (GUI.Button(new Rect(area.xMax - 220f, y, 200f, 31f), p.activeSpecialization == specId && !string.IsNullOrEmpty(specId) ? "СПЕК АКТИВЕН" : "Активировать специализацию"))
            {
                if (!ProgressionService.TrySetActiveSpecialization(p, specId, out var error)) SetStatus(error);
                else SetStatus($"Активная специализация: {SpecDisplay(specId)}.");
            }
            GUI.enabled = true;
        }

        private void DrawBranchTree(ProfileProgress p, TalentBranch branch, Rect canvas)
        {
            var defs = TalentCatalog.All.Where(x => x.Branch == branch).ToList();
            if (defs.Count == 0) return;

            foreach (var def in defs)
            {
                if (string.IsNullOrEmpty(def.PrerequisiteId)) continue;
                var parent = TalentCatalog.Find(def.PrerequisiteId);
                if (parent == null || parent.Branch != branch) continue;
                var active = TalentCatalog.GetRank(p, parent.Id) >= def.PrerequisiteRank;
                DrawConnection(GetNodeRect(parent, canvas), GetNodeRect(def, canvas), active ? new Color(0.20f, 0.65f, 0.72f, 1f) : new Color(0.18f, 0.20f, 0.22f, 1f));
            }
            foreach (var def in defs) DrawTalentNode(p, def, GetNodeRect(def, canvas));
        }

        private void DrawTalentNode(ProfileProgress p, TalentDef def, Rect rect)
        {
            var rank = TalentCatalog.GetRank(p, def.Id);
            var prereq = TalentCatalog.PrerequisiteMet(p, def);
            var levelOk = p.level >= def.UnlockLevel;
            var maxed = rank >= def.MaxRank;
            var isActiveBranch = TalentCatalog.IsBranchActive(p, def.Branch);

            var fill = maxed ? new Color(0.07f, 0.22f, 0.18f, 1f) : isActiveBranch ? new Color(0.08f, 0.15f, 0.18f, 1f) : new Color(0.065f, 0.075f, 0.082f, 1f);
            FillRect(rect, fill);
            DrawBorder(rect, maxed ? new Color(0.25f, 0.72f, 0.52f, 1f) : isActiveBranch ? new Color(0.22f, 0.55f, 0.65f, 1f) : new Color(0.24f, 0.30f, 0.33f, 1f), 2f);
            GUI.Label(new Rect(rect.x + 8f, rect.y + 6f, rect.width - 16f, 23f), $"{def.Name} [{rank}/{def.MaxRank}]", _nodeTitle);
            GUI.Label(new Rect(rect.x + 8f, rect.y + 29f, rect.width - 16f, 48f), def.Description, _nodeDesc);

            if (!levelOk)
                GUI.Label(new Rect(rect.x + 8f, rect.yMax - 51f, rect.width - 16f, 18f), $"Откроется на ур. {def.UnlockLevel}", _small);
            else if (!prereq)
                GUI.Label(new Rect(rect.x + 8f, rect.yMax - 51f, rect.width - 16f, 18f), "Нужен предыдущий узел", _small);

            GUI.enabled = levelOk && prereq && !maxed && p.unspentTalentPoints >= def.PointCost;
            if (GUI.Button(new Rect(rect.x + 8f, rect.yMax - 29f, rect.width - 16f, 23f), maxed ? "Изучено" : $"Изучить — {def.PointCost}"))
            {
                if (!ProgressionService.TryBuyTalent(p, def.Id, out var error)) SetStatus(error);
                else SetStatus($"Изучено: {def.Name}.");
            }
            GUI.enabled = true;
        }

        private void DrawMasteryPage(ProfileProgress p, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 12f, area.y + 12f, area.width - 24f, area.height - 24f));
            GUILayout.Label($"БЕСКОНЕЧНОЕ МАСТЕРСТВО   •   доступно очков: {p.unspentMasteryPoints}", _header);
            GUILayout.Label("Открывается с 41 уровня. После рангов 25 / 50 / 100 / 200 эффективность новых рангов снижается до 75% / 50% / 30% / 20%. Купленные мастерства других классов сохраняются, но работают только у активного класса.", _small);
            GUILayout.Space(8);

            if (p.level < 41)
            {
                GUILayout.Label("Мастерство ещё закрыто.", _center);
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
                var effective = MasteryCatalog.EffectiveRanks(rank);
                GUILayout.BeginVertical("box");
                GUILayout.BeginHorizontal();
                GUILayout.Label($"{def.Name} — ранг {rank}", _nodeTitle, GUILayout.Width(290));
                GUILayout.Label($"Эффективных рангов: {effective:0.##}", GUILayout.Width(220));
                GUILayout.FlexibleSpace();
                GUI.enabled = p.unspentMasteryPoints > 0;
                if (GUILayout.Button("+1 ранг", GUILayout.Width(120)))
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
            GUILayout.Space(8);
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
                if (GUILayout.Button(rank >= def.MaxRank ? "Изучено" : "Изучить", GUILayout.Width(130), GUILayout.Height(42)))
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
            GUILayout.BeginArea(new Rect(area.x + 10f, area.y + 10f, area.width - 20f, area.height - 20f));
            var capacity = ProgressionService.StartingCapacity(p);
            var used = StartingLoadoutService.UsedCapacity(p);
            GUILayout.Label($"АРСЕНАЛ — вместимость {used}/{capacity}", _header);
            GUILayout.Label("Открытия по мета-уровню: зелёные 15 • Boss 30 • Void 35 • красные 50 • Lunar 60 • Hallowed 80. Красный/Lunar/Hallowed — максимум один такой предмет суммарно.", _small);
            GUILayout.Space(6);

            GUILayout.BeginHorizontal();
            GUILayout.BeginVertical("box", GUILayout.Width(Mathf.Min(900f, area.width * 0.64f)));
            GUILayout.BeginHorizontal();
            GUILayout.Label("Поиск:", GUILayout.Width(60));
            _search = GUILayout.TextField(_search ?? string.Empty);
            GUILayout.EndHorizontal();
            _itemScroll = GUILayout.BeginScrollView(_itemScroll);
            var userProfile = LocalUserManager.GetFirstLocalUser()?.userProfile;
            IEnumerable<ItemDef> items = StartingLoadoutService.EnumerateEligibleItems(p, userProfile);
            if (!string.IsNullOrWhiteSpace(_search))
            {
                var needle = _search.Trim();
                items = items.Where(i => DisplayName(i).IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0 || i.name.IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0);
            }
            foreach (var item in items.OrderBy(i => (int)i.tier).ThenBy(DisplayName))
            {
                var selected = p.startingLoadout.FirstOrDefault(x => x.itemName == item.name)?.count ?? 0;
                var cost = StartingLoadoutService.CostOfCopy(item, selected);
                GUILayout.BeginHorizontal("box");
                GUILayout.Label(DisplayName(item), GUILayout.Width(400));
                GUILayout.Label(StartingLoadoutService.TierName(item), GUILayout.Width(125));
                GUILayout.Label($"{cost} мест", GUILayout.Width(80));
                if (GUILayout.Button("+", GUILayout.Width(44)))
                {
                    if (!StartingLoadoutService.TryAdd(p, item, out var error)) SetStatus(error);
                    else SetStatus($"Добавлено: {DisplayName(item)}.");
                }
                GUILayout.EndHorizontal();
            }
            GUILayout.EndScrollView();
            GUILayout.EndVertical();

            GUILayout.BeginVertical("box", GUILayout.ExpandWidth(true));
            GUILayout.Label("ВЫБРАНО", _nodeTitle);
            _selectedScroll = GUILayout.BeginScrollView(_selectedScroll);
            foreach (var record in p.startingLoadout.ToList())
            {
                var item = StartingLoadoutService.FindItem(record.itemName);
                if (item == null) continue;
                GUILayout.BeginHorizontal("box");
                GUILayout.Label($"{DisplayName(item)} x{record.count}", GUILayout.ExpandWidth(true));
                if (GUILayout.Button("−", GUILayout.Width(44))) StartingLoadoutService.RemoveOne(p, item);
                GUILayout.EndHorizontal();
            }
            GUILayout.EndScrollView();
            GUILayout.EndVertical();
            GUILayout.EndHorizontal();
            GUILayout.EndArea();
        }

        private Rect GetNodeRect(TalentDef def, Rect canvas)
        {
            var nodeWidth = Mathf.Min(300f, (canvas.width - 120f) / 3f);
            const float nodeHeight = 122f;
            var usable = canvas.width - 40f - nodeWidth;
            var x = canvas.x + 20f + usable * 0.5f * def.TreeColumn;
            var y = canvas.y + 18f + def.TreeRow * 140f;
            return new Rect(x, y, nodeWidth, nodeHeight);
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

        private static string BranchTitle(TalentBranch b)
        {
            switch (b)
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

        private void DrawConnection(Rect parent, Rect child, Color color)
        {
            var start = new Vector2(parent.center.x, parent.yMax);
            var end = new Vector2(child.center.x, child.y);
            var middleY = (start.y + end.y) * 0.5f;
            FillRect(new Rect(start.x - 1.5f, start.y, 3f, Mathf.Max(1f, middleY - start.y)), color);
            FillRect(new Rect(Mathf.Min(start.x, end.x), middleY - 1.5f, Mathf.Max(3f, Mathf.Abs(end.x - start.x)), 3f), color);
            FillRect(new Rect(end.x - 1.5f, middleY, 3f, Mathf.Max(1f, end.y - middleY)), color);
        }

        private static string DisplayName(ItemDef item)
        {
            if (item == null) return "<null>";
            var localized = Language.GetString(item.nameToken);
            return string.IsNullOrWhiteSpace(localized) ? item.name : localized;
        }

        private void SetStatus(string text)
        {
            _status = text ?? string.Empty;
            _statusUntil = Time.unscaledTime + 4f;
        }

        private void EnsureStyles()
        {
            if (_windowStyle != null) return;
            _windowTexture = new Texture2D(1, 1);
            _windowTexture.SetPixel(0, 0, new Color(0.025f, 0.032f, 0.038f, 1f));
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
            _small = new GUIStyle(GUI.skin.label) { fontSize = 12, wordWrap = true, normal = { textColor = new Color(0.72f, 0.78f, 0.81f, 1f) } };
            _nodeTitle = new GUIStyle(GUI.skin.label) { fontSize = 14, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _nodeDesc = new GUIStyle(GUI.skin.label) { fontSize = 12, wordWrap = true, normal = { textColor = new Color(0.86f, 0.89f, 0.91f, 1f) } };
            _center = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontSize = 13, fontStyle = FontStyle.Bold, normal = { textColor = Color.white } };
            _hud = new GUIStyle(_center) { fontSize = 14 };
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

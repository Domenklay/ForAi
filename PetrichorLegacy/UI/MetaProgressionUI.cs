using System;
using System.Collections.Generic;
using System.Linq;
using BepInEx.Configuration;
using PetrichorLegacy.Loadout;
using PetrichorLegacy.Persistence;
using PetrichorLegacy.Progression;
using RoR2;
using UnityEngine;

namespace PetrichorLegacy.UI
{
    public sealed class MetaProgressionUI : MonoBehaviour
    {
        private Rect _window = new Rect(80, 60, 1500, 850);
        private bool _open;
        private int _tab;
        private TalentBranch _selectedBranch = TalentBranch.Survival;
        private Vector2 _itemScroll;
        private Vector2 _selectedScroll;
        private string _search = "";
        private string _status = "";
        private float _statusUntil;
        private ConfigEntry<KeyboardShortcut> _toggleKey;

        private GUIStyle _hudLabel;
        private GUIStyle _hudAward;
        private GUIStyle _header;
        private GUIStyle _nodeTitle;
        private GUIStyle _nodeDesc;
        private GUIStyle _centerLabel;

        public void Configure(ConfigEntry<KeyboardShortcut> toggleKey)
        {
            _toggleKey = toggleKey;
        }

        private void Update()
        {
            SaveService.RefreshProfile();
            if (_toggleKey != null && _toggleKey.Value.IsDown())
            {
                _open = !_open;
                PetrichorLegacyPlugin.Log?.LogInfo($"Meta progression UI toggled: {(_open ? "OPEN" : "CLOSED")}");
            }
        }

        private void OnGUI()
        {
            EnsureStyles();

            if (Run.instance != null && SaveService.Current != null)
                DrawXpHud();

            if (!_open || SaveService.Current == null) return;

            var maxWidth = Mathf.Max(760f, Screen.width - 40f);
            var maxHeight = Mathf.Max(520f, Screen.height - 40f);
            _window.width = Mathf.Min(1500f, maxWidth);
            _window.height = Mathf.Min(850f, maxHeight);
            _window.x = Mathf.Clamp(_window.x, 0f, Mathf.Max(0f, Screen.width - _window.width));
            _window.y = Mathf.Clamp(_window.y, 0f, Mathf.Max(0f, Screen.height - _window.height));

            FillRect(_window, new Color(0.035f, 0.045f, 0.055f, 1f));
            DrawBorder(_window, new Color(0.30f, 0.38f, 0.44f, 1f), 2f);
            _window = GUI.Window(941204, _window, DrawWindow, "PETRICHOR LEGACY — META PROGRESSION");
        }

        private void DrawXpHud()
        {
            var p = SaveService.Current;
            var required = Mathf.Max(1, ProgressionService.XpRequiredForNextLevel(p.level));
            var fraction = Mathf.Clamp01((float)p.currentXp / required);
            var width = Mathf.Clamp(Screen.width * 0.38f, 380f, 720f);
            var outer = new Rect((Screen.width - width) * 0.5f, 16f, width, 38f);
            var inner = new Rect(outer.x + 3f, outer.y + 3f, outer.width - 6f, outer.height - 6f);

            FillRect(outer, new Color(0.02f, 0.025f, 0.03f, 0.98f));
            FillRect(new Rect(inner.x, inner.y, inner.width * fraction, inner.height), new Color(0.18f, 0.58f, 0.72f, 1f));
            DrawBorder(outer, new Color(0.55f, 0.72f, 0.80f, 1f), 2f);
            GUI.Label(outer, $"УРОВЕНЬ {p.level}     XP {p.currentXp} / {required}", _hudLabel);

            var elapsed = Time.unscaledTime - ProgressionService.LastAwardTime;
            if (elapsed >= 0f && elapsed < 3.5f && ProgressionService.LastAwardAmount > 0)
            {
                var awardRect = new Rect(outer.x, outer.y + outer.height + 2f, outer.width, 24f);
                GUI.Label(awardRect, $"+{ProgressionService.LastAwardAmount} XP — {ProgressionService.LastAwardReason}", _hudAward);
            }
        }

        private void DrawWindow(int id)
        {
            var p = SaveService.Current;

            GUI.Label(new Rect(14f, 25f, _window.width - 28f, 24f),
                $"Уровень {p.level}    XP {p.currentXp}/{ProgressionService.XpRequiredForNextLevel(p.level)}    Очки талантов: {p.unspentTalentPoints}    Забеги: {p.runsCompleted}    Победы: {p.wins}",
                _header);

            var tabY = 53f;
            var left = 12f;
            var tabWidth = Mathf.Max(180f, (_window.width - 380f) * 0.5f);
            if (GUI.Toggle(new Rect(left, tabY, tabWidth, 34f), _tab == 0, "ТАЛАНТЫ", "Button")) _tab = 0;
            if (GUI.Toggle(new Rect(left + tabWidth + 6f, tabY, tabWidth, 34f), _tab == 1, "СТАРТОВЫЙ НАБОР", "Button")) _tab = 1;

            if (GUI.Button(new Rect(_window.width - 350f, tabY, 190f, 34f), "Сбросить таланты"))
            {
                ProgressionService.Respec(p);
                SetStatus("Таланты сброшены; стартовый набор очищен.");
            }

            if (GUI.Button(new Rect(_window.width - 150f, tabY, 138f, 34f), "Закрыть"))
                _open = false;

            var content = new Rect(12f, 95f, _window.width - 24f, _window.height - 125f);
            FillRect(content, new Color(0.055f, 0.068f, 0.078f, 1f));
            DrawBorder(content, new Color(0.18f, 0.24f, 0.28f, 1f), 1f);

            if (_tab == 0)
                DrawTalents(p, content);
            else
                DrawLoadoutArea(p, content);

            if (!string.IsNullOrEmpty(_status) && Time.unscaledTime < _statusUntil)
                GUI.Label(new Rect(20f, _window.height - 27f, _window.width - 40f, 22f), _status, _centerLabel);

            GUI.DragWindow(new Rect(0, 0, _window.width, 23f));
        }

        private void DrawTalents(Models.ProfileProgress profile, Rect area)
        {
            var branches = new[]
            {
                TalentBranch.Survival,
                TalentBranch.Offense,
                TalentBranch.Mobility,
                TalentBranch.Fortune,
                TalentBranch.Expedition
            };

            var branchWidth = (area.width - 12f) / branches.Length;
            for (var i = 0; i < branches.Length; i++)
            {
                var branch = branches[i];
                var rect = new Rect(area.x + 4f + i * branchWidth, area.y + 5f, branchWidth - 4f, 34f);
                if (GUI.Toggle(rect, _selectedBranch == branch, BranchTitle(branch), "Button"))
                    _selectedBranch = branch;
            }

            var canvas = new Rect(area.x + 8f, area.y + 48f, area.width - 16f, area.height - 56f);
            FillRect(canvas, new Color(0.028f, 0.035f, 0.042f, 1f));
            DrawBorder(canvas, new Color(0.16f, 0.22f, 0.26f, 1f), 1f);

            var defs = TalentCatalog.All.Where(t => t.Branch == _selectedBranch).ToList();

            foreach (var def in defs)
            {
                if (string.IsNullOrEmpty(def.PrerequisiteId)) continue;
                var parent = TalentCatalog.Find(def.PrerequisiteId);
                if (parent == null || parent.Branch != _selectedBranch) continue;

                var parentRect = GetNodeRect(parent, canvas);
                var childRect = GetNodeRect(def, canvas);
                var active = TalentCatalog.GetRank(profile, parent.Id) >= def.PrerequisiteRank;
                DrawConnection(parentRect, childRect,
                    active ? new Color(0.22f, 0.63f, 0.74f, 1f) : new Color(0.20f, 0.23f, 0.25f, 1f));
            }

            foreach (var def in defs)
                DrawTalentNode(profile, def, GetNodeRect(def, canvas));
        }

        private void DrawTalentNode(Models.ProfileProgress profile, TalentDef def, Rect rect)
        {
            var rank = TalentCatalog.GetRank(profile, def.Id);
            var prereq = TalentCatalog.PrerequisiteMet(profile, def);
            var maxed = rank >= def.MaxRank;
            var affordable = profile.unspentTalentPoints >= def.PointCost;

            var fill = maxed
                ? new Color(0.10f, 0.25f, 0.22f, 1f)
                : prereq
                    ? new Color(0.10f, 0.16f, 0.20f, 1f)
                    : new Color(0.075f, 0.08f, 0.085f, 1f);

            FillRect(rect, fill);
            DrawBorder(rect, maxed ? new Color(0.30f, 0.75f, 0.58f, 1f) : new Color(0.28f, 0.37f, 0.42f, 1f), 2f);

            GUI.Label(new Rect(rect.x + 8f, rect.y + 6f, rect.width - 16f, 24f), $"{def.Name}   [{rank}/{def.MaxRank}]", _nodeTitle);
            GUI.Label(new Rect(rect.x + 8f, rect.y + 29f, rect.width - 16f, 45f), def.Description, _nodeDesc);

            var button = new Rect(rect.x + 8f, rect.yMax - 29f, rect.width - 16f, 23f);
            GUI.enabled = prereq && !maxed && affordable;
            var buttonText = maxed ? "Изучено" : def.PointCost == 1 ? "Изучить — 1 очко" : $"Изучить — {def.PointCost} очка";
            if (GUI.Button(button, buttonText) && !maxed)
            {
                if (!ProgressionService.TryBuyTalent(profile, def.Id, out var error)) SetStatus(error);
                else SetStatus($"Изучено: {def.Name}.");
            }
            GUI.enabled = true;

            if (!prereq && !string.IsNullOrEmpty(def.PrerequisiteId))
            {
                var parent = TalentCatalog.Find(def.PrerequisiteId);
                var requirement = parent != null ? $"Нужно: {parent.Name} {def.PrerequisiteRank}" : "Нужен предыдущий узел";
                GUI.Label(new Rect(rect.x + 8f, rect.yMax - 50f, rect.width - 16f, 18f), requirement, _nodeDesc);
            }
        }

        private Rect GetNodeRect(TalentDef def, Rect canvas)
        {
            var nodeWidth = Mathf.Min(260f, (canvas.width - 100f) / 3f);
            var nodeHeight = 116f;
            var usable = canvas.width - 40f - nodeWidth;
            var stepX = usable * 0.5f;
            var x = canvas.x + 20f + stepX * def.TreeColumn;
            var y = canvas.y + 18f + def.TreeRow * 136f;
            return new Rect(x, y, nodeWidth, nodeHeight);
        }

        private void DrawConnection(Rect parent, Rect child, Color color)
        {
            var start = new Vector2(parent.center.x, parent.yMax);
            var end = new Vector2(child.center.x, child.y);
            var middleY = (start.y + end.y) * 0.5f;

            FillRect(new Rect(start.x - 1.5f, start.y, 3f, Mathf.Max(1f, middleY - start.y)), color);
            var left = Mathf.Min(start.x, end.x);
            var right = Mathf.Max(start.x, end.x);
            FillRect(new Rect(left, middleY - 1.5f, Mathf.Max(3f, right - left), 3f), color);
            FillRect(new Rect(end.x - 1.5f, middleY, 3f, Mathf.Max(1f, end.y - middleY)), color);
        }

        private void DrawLoadoutArea(Models.ProfileProgress profile, Rect area)
        {
            GUILayout.BeginArea(new Rect(area.x + 8f, area.y + 8f, area.width - 16f, area.height - 16f));
            DrawLoadout(profile);
            GUILayout.EndArea();
        }

        private void DrawLoadout(Models.ProfileProgress profile)
        {
            var capacity = ProgressionService.StartingCapacity(profile);
            var used = StartingLoadoutService.UsedCapacity(profile);
            GUILayout.Label($"Вместимость: {used}/{capacity}. Каждая следующая копия одного предмета дороже предыдущей.");

            GUILayout.BeginHorizontal();
            GUILayout.BeginVertical("box", GUILayout.Width(Mathf.Min(900f, (_window.width - 60f) * 0.62f)));
            GUILayout.Label("ДОСТУПНЫЕ ПРЕДМЕТЫ (только открытые в Logbook)");
            GUILayout.BeginHorizontal();
            GUILayout.Label("Поиск:", GUILayout.Width(60));
            _search = GUILayout.TextField(_search ?? "");
            GUILayout.EndHorizontal();

            _itemScroll = GUILayout.BeginScrollView(_itemScroll);
            var userProfile = LocalUserManager.GetFirstLocalUser()?.userProfile;
            IEnumerable<ItemDef> items = StartingLoadoutService.EnumerateEligibleItems(profile, userProfile);
            if (!string.IsNullOrWhiteSpace(_search))
            {
                var needle = _search.Trim();
                items = items.Where(i => DisplayName(i).IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0 ||
                                         i.name.IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0);
            }

            foreach (var item in items.OrderBy(i => (int)i.tier).ThenBy(DisplayName))
            {
                var selected = profile.startingLoadout.FirstOrDefault(x => x.itemName == item.name)?.count ?? 0;
                var cost = StartingLoadoutService.CostOfCopy(item, selected);
                GUILayout.BeginHorizontal("box");
                GUILayout.Label(DisplayName(item), GUILayout.Width(390));
                GUILayout.Label(StartingLoadoutService.TierName(item), GUILayout.Width(125));
                GUILayout.Label($"Цена: {cost}", GUILayout.Width(80));
                GUI.enabled = used + cost <= capacity;
                if (GUILayout.Button("+", GUILayout.Width(45)))
                {
                    if (StartingLoadoutService.TryAdd(profile, item, out var error)) SetStatus($"Добавлено: {DisplayName(item)}");
                    else SetStatus(error);
                }
                GUI.enabled = true;
                GUILayout.EndHorizontal();
            }
            GUILayout.EndScrollView();
            GUILayout.EndVertical();

            GUILayout.BeginVertical("box", GUILayout.ExpandWidth(true));
            GUILayout.Label("ВЫБРАНО");
            _selectedScroll = GUILayout.BeginScrollView(_selectedScroll);
            foreach (var record in profile.startingLoadout.ToList())
            {
                var item = StartingLoadoutService.FindItem(record.itemName);
                if (item == null) continue;
                GUILayout.BeginHorizontal("box");
                GUILayout.Label($"{DisplayName(item)}  x{record.count}", GUILayout.ExpandWidth(true));
                if (GUILayout.Button("−", GUILayout.Width(45))) StartingLoadoutService.RemoveOne(profile, item);
                GUILayout.EndHorizontal();
            }
            GUILayout.EndScrollView();
            GUILayout.EndVertical();
            GUILayout.EndHorizontal();

            GUILayout.Space(4);
            GUILayout.Label("Hexes, Pages, Scrap, consumed/internal/key items не могут быть стартовыми. Hallowed открываются последним талантом ветки Экспедиции.");
        }

        private static string BranchTitle(TalentBranch branch)
        {
            switch (branch)
            {
                case TalentBranch.Survival: return "ВЫЖИВАНИЕ";
                case TalentBranch.Offense: return "УРОН";
                case TalentBranch.Mobility: return "МОБИЛЬНОСТЬ";
                case TalentBranch.Fortune: return "УДАЧА И ЛУТ";
                case TalentBranch.Expedition: return "ЭКСПЕДИЦИЯ";
                default: return branch.ToString();
            }
        }

        private static string DisplayName(ItemDef item)
        {
            if (item == null) return "<null>";
            var localized = Language.GetString(item.nameToken);
            return string.IsNullOrWhiteSpace(localized) ? item.name : localized;
        }

        private void SetStatus(string message)
        {
            _status = message ?? "";
            _statusUntil = Time.unscaledTime + 4f;
        }

        private void EnsureStyles()
        {
            if (_hudLabel != null) return;

            _hudLabel = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = 15,
                fontStyle = FontStyle.Bold
            };
            _hudLabel.normal.textColor = Color.white;

            _hudAward = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = 14,
                fontStyle = FontStyle.Bold
            };
            _hudAward.normal.textColor = new Color(0.68f, 0.91f, 1f, 1f);

            _header = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleLeft,
                fontSize = 15,
                fontStyle = FontStyle.Bold
            };
            _header.normal.textColor = Color.white;

            _nodeTitle = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.UpperCenter,
                fontSize = 14,
                fontStyle = FontStyle.Bold,
                wordWrap = true
            };
            _nodeTitle.normal.textColor = Color.white;

            _nodeDesc = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.UpperCenter,
                fontSize = 12,
                wordWrap = true
            };
            _nodeDesc.normal.textColor = new Color(0.84f, 0.88f, 0.90f, 1f);

            _centerLabel = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = 13,
                fontStyle = FontStyle.Bold
            };
            _centerLabel.normal.textColor = Color.white;
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

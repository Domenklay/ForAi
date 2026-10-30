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
        private Vector2 _itemScroll;
        private Vector2 _selectedScroll;
        private string _search = "";
        private string _status = "";
        private float _statusUntil;
        private ConfigEntry<KeyboardShortcut> _toggleKey;

        public void Configure(ConfigEntry<KeyboardShortcut> toggleKey)
        {
            _toggleKey = toggleKey;
        }

        private void Update()
        {
            SaveService.RefreshProfile();
            if (_toggleKey != null && _toggleKey.Value.IsDown() && PreGameController.instance != null)
                _open = !_open;
        }

        private void OnGUI()
        {
            if (!_open || PreGameController.instance == null || SaveService.Current == null) return;
            _window = GUI.Window(941204, _window, DrawWindow, "PETRICHOR LEGACY — META PROGRESSION");
        }

        private void DrawWindow(int id)
        {
            var p = SaveService.Current;
            GUILayout.BeginVertical();
            GUILayout.Label($"Уровень {p.level}    XP {p.currentXp}/{ProgressionService.XpRequiredForNextLevel(p.level)}    Очки талантов: {p.unspentTalentPoints}    Забеги: {p.runsCompleted}    Победы: {p.wins}");

            GUILayout.BeginHorizontal();
            if (GUILayout.Toggle(_tab == 0, "ТАЛАНТЫ", "Button", GUILayout.Height(34))) _tab = 0;
            if (GUILayout.Toggle(_tab == 1, "СТАРТОВЫЙ НАБОР", "Button", GUILayout.Height(34))) _tab = 1;
            if (GUILayout.Button("Сбросить таланты", GUILayout.Width(170), GUILayout.Height(34)))
            {
                ProgressionService.Respec(p);
                SetStatus("Таланты сброшены; стартовый набор очищен.");
            }
            if (GUILayout.Button("Закрыть", GUILayout.Width(110), GUILayout.Height(34))) _open = false;
            GUILayout.EndHorizontal();

            GUILayout.Space(8);
            if (_tab == 0) DrawTalents(p); else DrawLoadout(p);

            if (!string.IsNullOrEmpty(_status) && Time.unscaledTime < _statusUntil)
                GUILayout.Label(_status);

            GUILayout.EndVertical();
            GUI.DragWindow(new Rect(0, 0, _window.width, 25));
        }

        private void DrawTalents(Models.ProfileProgress profile)
        {
            GUILayout.BeginHorizontal();
            DrawBranch(profile, TalentBranch.Survival, "ВЫЖИВАНИЕ");
            DrawBranch(profile, TalentBranch.Offense, "УРОН");
            DrawBranch(profile, TalentBranch.Mobility, "МОБИЛЬНОСТЬ");
            DrawBranch(profile, TalentBranch.Fortune, "УДАЧА И ЛУТ");
            DrawBranch(profile, TalentBranch.Expedition, "ЭКСПЕДИЦИЯ");
            GUILayout.EndHorizontal();
        }

        private void DrawBranch(Models.ProfileProgress profile, TalentBranch branch, string title)
        {
            GUILayout.BeginVertical("box", GUILayout.Width(285));
            GUILayout.Label(title);
            foreach (var def in TalentCatalog.All.Where(t => t.Branch == branch))
            {
                var rank = TalentCatalog.GetRank(profile, def.Id);
                var prereq = TalentCatalog.PrerequisiteMet(profile, def);
                GUILayout.BeginVertical("box");
                GUILayout.Label($"{def.Name}  [{rank}/{def.MaxRank}]");
                GUILayout.Label(def.Description);
                GUI.enabled = prereq && rank < def.MaxRank && profile.unspentTalentPoints >= def.PointCost;
                if (GUILayout.Button(def.PointCost == 1 ? "Изучить — 1 очко" : $"Изучить — {def.PointCost} очка"))
                {
                    if (!ProgressionService.TryBuyTalent(profile, def.Id, out var error)) SetStatus(error);
                    else SetStatus($"Изучено: {def.Name}.");
                }
                GUI.enabled = true;
                if (!prereq) GUILayout.Label("Требуется предыдущий узел.");
                GUILayout.EndVertical();
            }
            GUILayout.EndVertical();
        }

        private void DrawLoadout(Models.ProfileProgress profile)
        {
            var capacity = ProgressionService.StartingCapacity(profile);
            var used = StartingLoadoutService.UsedCapacity(profile);
            GUILayout.Label($"Вместимость: {used}/{capacity}. Каждая следующая копия одного предмета дороже предыдущей.");

            GUILayout.BeginHorizontal();
            GUILayout.BeginVertical("box", GUILayout.Width(920));
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
                GUILayout.Label(DisplayName(item), GUILayout.Width(480));
                GUILayout.Label(StartingLoadoutService.TierName(item), GUILayout.Width(150));
                GUILayout.Label($"Цена: {cost}", GUILayout.Width(90));
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

            GUILayout.BeginVertical("box", GUILayout.Width(520));
            GUILayout.Label("ВЫБРАНО");
            _selectedScroll = GUILayout.BeginScrollView(_selectedScroll);
            foreach (var record in profile.startingLoadout.ToList())
            {
                var item = StartingLoadoutService.FindItem(record.itemName);
                if (item == null) continue;
                GUILayout.BeginHorizontal("box");
                GUILayout.Label($"{DisplayName(item)}  x{record.count}", GUILayout.Width(380));
                if (GUILayout.Button("−", GUILayout.Width(45))) StartingLoadoutService.RemoveOne(profile, item);
                GUILayout.EndHorizontal();
            }
            GUILayout.EndScrollView();
            GUILayout.EndVertical();
            GUILayout.EndHorizontal();

            GUILayout.Space(4);
            GUILayout.Label("Hexes, Pages, Scrap, consumed/internal/key items не могут быть стартовыми. Hallowed открываются последним талантом ветки Экспедиции.");
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
    }
}

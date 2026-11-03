using System;
using System.Collections.Generic;
using PetrichorLegacy.Progression;
using RoR2;
using UnityEngine;

namespace PetrichorLegacy.UI
{
    public sealed class MonsterRarityOverlay : MonoBehaviour
    {
        private readonly PickupIconResolver _icons = new PickupIconResolver();
        private GUIStyle _codeStyle;
        private GUIStyle _stackStyle;
        private GUIStyle _tooltipStyle;
        private Texture2D _pixel;

        private const float Icon = 18f;
        private const float Gap = 2f;
        private const int MaxItems = 5;
        private const int MaxTraits = 5;
        private const float MaxDistance = 95f;

        private void OnDestroy()
        {
            _icons.Dispose();
            if (_pixel != null) Destroy(_pixel);
        }

        private void OnGUI()
        {
            if (Run.instance == null) return;
            EnsureStyles();

            var camera = Camera.main;
            if (camera == null) return;

            var localBody = LocalUserManager.GetFirstLocalUser()?.cachedMaster?.GetBody();
            var mouse = Event.current.mousePosition;
            string hoverTooltip = null;

            foreach (var marker in MonsterTraitSystem.GetActiveMarkers())
            {
                if (marker == null) continue;
                var body = marker.GetComponent<CharacterBody>();
                if (body == null || body.healthComponent == null || !body.healthComponent.alive) continue;

                if (localBody != null && (body.corePosition - localBody.corePosition).sqrMagnitude > MaxDistance * MaxDistance)
                    continue;

                var height = Mathf.Max(1.8f, body.radius + 1.15f);
                var world = body.corePosition + Vector3.up * height;
                var screen = camera.WorldToScreenPoint(world);
                if (screen.z <= 0f) continue;

                var items = MonsterRaritySystem.GetVisibleCombatItems(body);
                var traits = marker.Traits ?? new List<string>();
                var itemCount = Mathf.Min(MaxItems, items.Count);
                var traitCount = Mathf.Min(MaxTraits, traits.Count);
                var hidden = Mathf.Max(0, items.Count - itemCount) + Mathf.Max(0, traits.Count - traitCount);
                var cells = itemCount + traitCount + (hidden > 0 ? 1 : 0);
                if (cells <= 0) continue;

                var width = cells * Icon + Mathf.Max(0, cells - 1) * Gap + 8f;
                var x = screen.x - width * 0.5f;
                var y = Screen.height - screen.y - 26f;
                var row = new Rect(x, y, width, Icon + 8f);
                Fill(row, new Color(0.01f, 0.014f, 0.018f, 0.72f));

                var cx = row.x + 4f;
                for (var i = 0; i < itemCount; i++)
                {
                    var entry = items[i];
                    var rect = new Rect(cx, row.y + 4f, Icon, Icon);
                    var sprite = _icons.Resolve(entry.Item);
                    if (sprite != null) DrawSprite(rect, sprite, Color.white);
                    else
                    {
                        Fill(rect, new Color(0.15f, 0.17f, 0.19f, 0.95f));
                        GUI.Label(rect, "I", _codeStyle);
                    }
                    if (entry.Count > 1)
                    {
                        var badge = new Rect(rect.xMax - 9f, rect.yMax - 9f, 10f, 10f);
                        Fill(badge, new Color(0f, 0f, 0f, 0.90f));
                        GUI.Label(badge, entry.Count.ToString(), _stackStyle);
                    }
                    GUI.Label(rect, new GUIContent(string.Empty, MonsterRaritySystem.ItemTooltip(entry)));
                    if (rect.Contains(mouse) && !string.IsNullOrEmpty(GUI.tooltip)) hoverTooltip = GUI.tooltip;
                    cx += Icon + Gap;
                }

                for (var i = 0; i < traitCount; i++)
                {
                    var def = MonsterTraitSystem.Find(traits[i]);
                    if (def == null) continue;
                    var rect = new Rect(cx, row.y + 4f, Icon, Icon);
                    Fill(rect, TraitColor(def.Category));
                    DrawBorder(rect, def.Major ? new Color(1f, 0.78f, 0.22f, 1f) : new Color(0f, 0f, 0f, 0.85f), def.Major ? 2f : 1f);
                    GUI.Label(rect, def.Code, _codeStyle);
                    var tip = def.Name + "\n" + def.Description;
                    GUI.Label(rect, new GUIContent(string.Empty, tip));
                    if (rect.Contains(mouse)) hoverTooltip = tip;
                    cx += Icon + Gap;
                }

                if (hidden > 0)
                {
                    var rect = new Rect(cx, row.y + 4f, Icon, Icon);
                    Fill(rect, new Color(0.18f, 0.20f, 0.23f, 0.96f));
                    GUI.Label(rect, "+" + hidden, _codeStyle);
                }
            }

            if (!string.IsNullOrEmpty(hoverTooltip) && Cursor.visible)
                DrawTooltip(hoverTooltip, mouse);
        }

        private void DrawTooltip(string text, Vector2 mouse)
        {
            const float width = 330f;
            var height = Mathf.Clamp(_tooltipStyle.CalcHeight(new GUIContent(text), width - 16f) + 14f, 44f, 150f);
            var rect = new Rect(mouse.x + 16f, mouse.y + 18f, width, height);
            rect.x = Mathf.Min(rect.x, Screen.width - width - 6f);
            rect.y = Mathf.Min(rect.y, Screen.height - height - 6f);
            Fill(rect, new Color(0.012f, 0.016f, 0.020f, 0.97f));
            DrawBorder(rect, new Color(0.30f, 0.42f, 0.48f, 1f), 1f);
            GUI.Label(new Rect(rect.x + 8f, rect.y + 6f, rect.width - 16f, rect.height - 12f), text, _tooltipStyle);
        }

        private void EnsureStyles()
        {
            if (_codeStyle != null) return;
            _pixel = new Texture2D(1, 1);
            _pixel.SetPixel(0, 0, Color.white);
            _pixel.Apply();
            _codeStyle = new GUIStyle(GUI.skin.label)
            {
                alignment = TextAnchor.MiddleCenter,
                fontSize = 8,
                fontStyle = FontStyle.Bold,
                normal = { textColor = Color.white }
            };
            _stackStyle = new GUIStyle(_codeStyle) { fontSize = 7 };
            _tooltipStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 11,
                wordWrap = true,
                normal = { textColor = Color.white }
            };
        }

        private static Color TraitColor(MonsterTraitCategory category)
        {
            switch (category)
            {
                case MonsterTraitCategory.Offense: return new Color(0.62f, 0.12f, 0.11f, 0.96f);
                case MonsterTraitCategory.Defense: return new Color(0.12f, 0.34f, 0.62f, 0.96f);
                case MonsterTraitCategory.Mobility: return new Color(0.54f, 0.43f, 0.10f, 0.96f);
                case MonsterTraitCategory.Sustain: return new Color(0.10f, 0.46f, 0.25f, 0.96f);
                case MonsterTraitCategory.Aura: return new Color(0.43f, 0.16f, 0.58f, 0.96f);
                default: return new Color(0.56f, 0.19f, 0.55f, 0.98f);
            }
        }

        private static void DrawSprite(Rect rect, Sprite sprite, Color tint)
        {
            if (sprite == null || sprite.texture == null) return;
            var tex = sprite.texture;
            var sr = sprite.rect;
            var uv = new Rect(sr.x / tex.width, sr.y / tex.height, sr.width / tex.width, sr.height / tex.height);
            var old = GUI.color;
            GUI.color = tint;
            GUI.DrawTextureWithTexCoords(rect, tex, uv, true);
            GUI.color = old;
        }

        private static void Fill(Rect rect, Color color)
        {
            var old = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = old;
        }

        private static void DrawBorder(Rect rect, Color color, float thickness)
        {
            Fill(new Rect(rect.x, rect.y, rect.width, thickness), color);
            Fill(new Rect(rect.x, rect.yMax - thickness, rect.width, thickness), color);
            Fill(new Rect(rect.x, rect.y, thickness, rect.height), color);
            Fill(new Rect(rect.xMax - thickness, rect.y, thickness, rect.height), color);
        }
    }
}

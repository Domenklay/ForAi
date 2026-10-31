using System;
using System.Collections.Generic;
using RoR2;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace PetrichorLegacy.UI
{
    /// <summary>
    /// Resolves RoR2 pickup icons from the modern PickupDef API.
    /// Vanilla/DLC pickups may expose only an Addressables reference instead of ItemDef.pickupIconSprite.
    /// </summary>
    internal sealed class PickupIconResolver : IDisposable
    {
        private sealed class Pending
        {
            public AsyncOperationHandle<Sprite> Handle;
            public bool Failed;
        }

        private readonly Dictionary<PickupIndex, Sprite> _resolved = new Dictionary<PickupIndex, Sprite>();
        private readonly Dictionary<PickupIndex, Pending> _pending = new Dictionary<PickupIndex, Pending>();

        public Sprite Resolve(ItemDef item)
        {
            if (item == null) return null;

            var pickupIndex = PickupCatalog.FindPickupIndex(item.itemIndex);
            if (pickupIndex == PickupIndex.none)
                return item.pickupIconSprite;

            if (_resolved.TryGetValue(pickupIndex, out var cached) && cached != null)
                return cached;

            var pickupDef = PickupCatalog.GetPickupDef(pickupIndex);
            if (pickupDef == null)
                return item.pickupIconSprite;

            // Some pickups still expose a direct sprite.
            try
            {
                var direct = pickupDef.GetIcon();
                if (direct != null)
                {
                    _resolved[pickupIndex] = direct;
                    return direct;
                }
            }
            catch
            {
                // Fall through to ItemDef / addressable reference.
            }

            if (item.pickupIconSprite != null)
            {
                _resolved[pickupIndex] = item.pickupIconSprite;
                return item.pickupIconSprite;
            }

            if (_pending.TryGetValue(pickupIndex, out var request))
            {
                if (request.Failed) return null;
                if (!request.Handle.IsValid() || !request.Handle.IsDone) return null;

                if (request.Handle.Status == AsyncOperationStatus.Succeeded && request.Handle.Result != null)
                {
                    _resolved[pickupIndex] = request.Handle.Result;
                    return request.Handle.Result;
                }

                request.Failed = true;
                return null;
            }

            try
            {
                var reference = pickupDef.GetIconReference();
                if (reference == null || !reference.RuntimeKeyIsValid()) return null;
                var handle = Addressables.LoadAssetAsync<Sprite>(reference.RuntimeKey);
                _pending[pickupIndex] = new Pending { Handle = handle };
            }
            catch (Exception ex)
            {
                PetrichorLegacyPlugin.Log?.LogWarning($"Could not request pickup icon for {item.name}: {ex.Message}");
            }

            return null;
        }

        public void Dispose()
        {
            foreach (var pending in _pending.Values)
            {
                try
                {
                    if (pending.Handle.IsValid()) Addressables.Release(pending.Handle);
                }
                catch { }
            }
            _pending.Clear();
            _resolved.Clear();
        }
    }
}

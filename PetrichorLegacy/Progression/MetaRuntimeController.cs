using RoR2;
using UnityEngine;

namespace PetrichorLegacy.Progression
{
    public sealed class MetaRuntimeController : MonoBehaviour
    {
        private CharacterBody _body;
        private bool _lastLowHealth;
        private bool _lastHunterHaste;
        private bool _lastPursuit;
        private float _nextCheck;

        public void Initialize(CharacterBody body)
        {
            _body = body;
            Refresh(true);
        }

        private void FixedUpdate()
        {
            if (_body == null || Time.fixedTime < _nextCheck) return;
            _nextCheck = Time.fixedTime + 0.20f;
            Refresh(false);
        }

        private void Refresh(bool force)
        {
            if (_body == null || _body.master == null) return;
            var low = _body.healthComponent != null && _body.healthComponent.combinedHealthFraction < 0.30f;
            var progress = ServerProgressionState.Get(_body.master);
            var haste = progress != null && progress.HunterHasteUntil > Time.fixedTime;
            var pursuit = progress != null && progress.PursuitUntil > Time.fixedTime;

            if (force || low != _lastLowHealth || haste != _lastHunterHaste || pursuit != _lastPursuit)
            {
                _lastLowHealth = low;
                _lastHunterHaste = haste;
                _lastPursuit = pursuit;
                _body.RecalculateStats();
            }
        }
    }
}

# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.15 deterministic bootstrap."""

import traceback

_loading = "base"

try:
    _loading = "deep_relationships"
    import deep_relationships as base
    base.flog('V0715 BOOTSTRAP START')

    _loading = "zz_deep_relationships_grievances"
    import zz_deep_relationships_grievances
    _loading = "zzy_deep_relationships_moodlets"
    import zzy_deep_relationships_moodlets as moodlets
    _loading = "zzzz_deep_relationships_persistence_v045"
    import zzzz_deep_relationships_persistence_v045
    _loading = "zzzzz_deep_relationships_core_v046"
    import zzzzz_deep_relationships_core_v046
    _loading = "zzzzzz_deep_relationships_reconciliation_v050"
    import zzzzzz_deep_relationships_reconciliation_v050
    _loading = "zzzzzzz_deep_relationships_v051"
    import zzzzzzz_deep_relationships_v051
    _loading = "zzzzzzzz_deep_relationships_memory_v060"
    import zzzzzzzz_deep_relationships_memory_v060
    _loading = "zzzzzzzzz_deep_relationships_v061"
    import zzzzzzzzz_deep_relationships_v061
    _loading = "zzzzzzzzzz_deep_relationships_v062"
    import zzzzzzzzzz_deep_relationships_v062
    _loading = "zzzzzzzzzzz_deep_relationships_breakup_v070"
    import zzzzzzzzzzz_deep_relationships_breakup_v070
    _loading = "zzzzzzzzzzzz_deep_relationships_v070_guard"
    import zzzzzzzzzzzz_deep_relationships_v070_guard
    _loading = "zzzzzzzzzzzzz_deep_relationships_notifications_v071"
    import zzzzzzzzzzzzz_deep_relationships_notifications_v071
    _loading = "zzzzzzzzzzzzzz_deep_relationships_stability_v072"
    import zzzzzzzzzzzzzz_deep_relationships_stability_v072
    _loading = "zzzzzzzzzzzzzzz_deep_relationships_stability_v072"
    import zzzzzzzzzzzzzzz_deep_relationships_stability_v072
    _loading = "zzzzzzzzzzzzzzz_deep_relationships_v073"
    import zzzzzzzzzzzzzzz_deep_relationships_v073
    _loading = "zzzzzzzzzzzzzzzz_deep_relationships_v075"
    import zzzzzzzzzzzzzzzz_deep_relationships_v075
    _loading = "zzzzzzzzzzzzzzzzz_deep_relationships_v076"
    import zzzzzzzzzzzzzzzzz_deep_relationships_v076
    _loading = "zzzzzzzzzzzzzzzzzz_deep_relationships_v078"
    import zzzzzzzzzzzzzzzzzz_deep_relationships_v078
    _loading = "zzzzzzzzzzzzzzzzzzz_deep_relationships_v079"
    import zzzzzzzzzzzzzzzzzzz_deep_relationships_v079
    _loading = "zzzzzzzzzzzzzzzzzzzz_deep_relationships_v0710"
    import zzzzzzzzzzzzzzzzzzzz_deep_relationships_v0710
    _loading = "zzzzzzzzzzzzzzzzzzzzz_deep_relationships_v0711"
    import zzzzzzzzzzzzzzzzzzzzz_deep_relationships_v0711 as final_layer
    _loading = 'zzzzzzzzzzzzzzzzzzzzzz_deep_relationships_v0714'
    import zzzzzzzzzzzzzzzzzzzzzz_deep_relationships_v0714
    base.VERSION = '0.7.15'
    moodlets.VERSION = '0.7.15'
    base.flog('V0715 FINAL STAGE DELIVERY LAYER IMPORTED')
except Exception as exc:
    # Never let v0.4.6's quiet logger hide the traceback again.
    message = 'V0715 BOOTSTRAP FAILED AT {}: {}: {}'.format(
        _loading, type(exc).__name__, exc
    )
    try:
        base.flog(message)
    except Exception:
        pass
    try:
        import zzzzz_deep_relationships_core_v046 as _diagnostic_core
        _diagnostic_core._RAW_FLOG(traceback.format_exc())
    except Exception:
        try:
            base.flog('V0715 BOOTSTRAP FAILED TRACE: {}'.format(
                traceback.format_exc()
            ))
        except Exception:
            pass

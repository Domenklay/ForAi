# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.10 deterministic bootstrap."""

import traceback

try:
    import deep_relationships as base
    base.flog('V0710 BOOTSTRAP START')

    import zz_deep_relationships_grievances
    import zzy_deep_relationships_moodlets as moodlets
    import zzzz_deep_relationships_persistence_v045
    import zzzzz_deep_relationships_core_v046
    import zzzzzz_deep_relationships_reconciliation_v050
    import zzzzzzz_deep_relationships_v051
    import zzzzzzzz_deep_relationships_memory_v060
    import zzzzzzzzz_deep_relationships_v061
    import zzzzzzzzzz_deep_relationships_v062
    import zzzzzzzzzzz_deep_relationships_breakup_v070
    import zzzzzzzzzzzz_deep_relationships_v070_guard
    import zzzzzzzzzzzzz_deep_relationships_notifications_v071
    import zzzzzzzzzzzzzz_deep_relationships_stability_v072
    import zzzzzzzzzzzzzzz_deep_relationships_stability_v072
    import zzzzzzzzzzzzzzz_deep_relationships_v073
    import zzzzzzzzzzzzzzzz_deep_relationships_v075
    import zzzzzzzzzzzzzzzzz_deep_relationships_v076
    import zzzzzzzzzzzzzzzzzz_deep_relationships_v078
    import zzzzzzzzzzzzzzzzzzz_deep_relationships_v079
    import zzzzzzzzzzzzzzzzzzzz_deep_relationships_v0710
    import zzzzzzzzzzzzzzzzzzzzz_deep_relationships_v0711 as final_layer

    base.VERSION = '0.7.11'
    moodlets.VERSION = '0.7.11'
    base.flog('V0711 FINAL STAGE DELIVERY LAYER IMPORTED')
except Exception:
    try:
        base.flog('V0711 BOOTSTRAP FAILED')
        base.flog(traceback.format_exc())
    except Exception:
        pass

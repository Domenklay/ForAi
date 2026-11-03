# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.8 deterministic bootstrap.

Import every shipped layer in the intended order, then install the visible
relationship-stage layer last.  This prevents Sims 4 archive import order from
allowing an older wrapper to overwrite the final stage/moodlet behavior.
"""

import traceback

try:
    import deep_relationships as base
    base.flog('V078 BOOTSTRAP START')

    # Fixed dependency/order chain.
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
    # Compatibility alias is deliberately imported before v0.7.3 because the
    # older v0.7.3 source references that historical typo.
    import zzzzzzzzzzzzzzz_deep_relationships_stability_v072
    import zzzzzzzzzzzzzzz_deep_relationships_v073
    import zzzzzzzzzzzzzzzz_deep_relationships_v075
    import zzzzzzzzzzzzzzzzz_deep_relationships_v076
    import zzzzzzzzzzzzzzzzzz_deep_relationships_v078 as final_layer

    base.VERSION = '0.7.8'
    moodlets.VERSION = '0.7.8'
    base.flog('V078 FINAL STAGE LAYER IMPORTED')
except Exception:
    try:
        base.flog('V078 BOOTSTRAP FAILED')
        base.flog(traceback.format_exc())
    except Exception:
        pass

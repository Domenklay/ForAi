# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.6 explicit bootstrap."""

import traceback

try:
    import deep_relationships as base
    base.flog('V076 BOOTSTRAP START')

    # Explicit final import: v0.7.6 pulls in v0.7.5 -> v0.7.3 -> v0.7.2 -> v0.7.1.
    import zzzzzzzzzzzzzzzzz_deep_relationships_v076 as final_layer

    base.VERSION = '0.7.6'
    try:
        import zzy_deep_relationships_moodlets as moodlets
        moodlets.VERSION = '0.7.6'
    except Exception:
        pass

    base.flog('V076 FINAL LAYERS IMPORTED')
except Exception:
    try:
        base.flog('V076 BOOTSTRAP FAILED')
        base.flog(traceback.format_exc())
    except Exception:
        pass

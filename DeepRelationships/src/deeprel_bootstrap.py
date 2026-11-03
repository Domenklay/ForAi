# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.7 explicit bootstrap."""

import traceback

try:
    import deep_relationships as base
    base.flog('V077 BOOTSTRAP START')

    # v0.7.7 includes the compatibility alias needed by the v0.7.3 import chain.
    import zzzzzzzzzzzzzzzzz_deep_relationships_v076 as final_layer

    base.VERSION = '0.7.7'
    try:
        import zzy_deep_relationships_moodlets as moodlets
        moodlets.VERSION = '0.7.7'
    except Exception:
        pass

    base.flog('V077 FINAL LAYERS IMPORTED')
except Exception:
    try:
        base.flog('V077 BOOTSTRAP FAILED')
        base.flog(traceback.format_exc())
    except Exception:
        pass

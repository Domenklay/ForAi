# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.5 explicit bootstrap."""

import traceback

try:
    import deep_relationships as base
    base.flog('V075 BOOTSTRAP START')

    # Explicitly import the final layer. Its dependency chain deterministically
    # installs v0.7.1 -> v0.7.2 -> v0.7.3 before the new stage-moodlet layer.
    import zzzzzzzzzzzzzzzz_deep_relationships_v075 as final_layer

    base.VERSION = '0.7.5'
    try:
        import zzy_deep_relationships_moodlets as moodlets
        moodlets.VERSION = '0.7.5'
    except Exception:
        pass

    base.flog('V075 FINAL LAYERS IMPORTED')
except Exception:
    try:
        base.flog('V075 BOOTSTRAP FAILED')
        base.flog(traceback.format_exc())
    except Exception:
        pass

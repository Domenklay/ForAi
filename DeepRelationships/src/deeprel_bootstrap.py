# -*- coding: utf-8 -*-
"""Deep Relationships v0.7.4 explicit bootstrap.

Sims 4 was loading the main script and older layers, but the log showed that
v0.7.1-v0.7.3 were not being executed automatically.  This short, early module
explicitly imports the final layer; that import chain installs v0.7.1, v0.7.2
and v0.7.3 in deterministic order.
"""

import traceback

try:
    import deep_relationships as base
    base.flog('V074 BOOTSTRAP START')

    # Importing v0.7.3 pulls in v0.7.2 -> v0.7.1 -> all required earlier layers.
    import zzzzzzzzzzzzzzz_deep_relationships_v073 as final_layer

    base.VERSION = '0.7.4'
    try:
        import zzy_deep_relationships_moodlets as moodlets
        moodlets.VERSION = '0.7.4'
    except Exception:
        pass

    base.flog('V074 FINAL LAYERS IMPORTED')
except Exception:
    try:
        base.flog('V074 BOOTSTRAP FAILED')
        base.flog(traceback.format_exc())
    except Exception:
        pass

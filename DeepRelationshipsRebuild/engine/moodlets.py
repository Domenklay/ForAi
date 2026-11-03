# -*- coding: utf-8 -*-
"""Stable Buff IDs and side-effect-free Buff changeset calculation."""
from stages import STAGES

STAGE_TO_BUFF = {
    "argument": 12004666048318715120,
    "deep_conflict": 12004666048318715121,
    "reconciliation": 12004666048318715122,
    "infidelity": 12004666048318715123,
    "refused_forgive": 12004666048318715124,
    "pause": 12004666048318715125,
    "breakup": 12004666048318715126,
    "exes": 12004666048318715127,
    "second_chance": 12004666048318715128,
    "recovery": 12004666048318715129,
}
STAGE_BUFFS = frozenset(STAGE_TO_BUFF.values())
assert set(STAGES) == set(STAGE_TO_BUFF)
assert len(STAGE_BUFFS) == len(STAGE_TO_BUFF) == 10


def changeset(current_ids, stage):
    """Compute (remove, add) without changing the game; preserve unrelated buffs.

    Exactly one or zero story-stage buffs may survive. Supplementary buffs
    (jealousy, instability, hurt, etc.) are never changed here.
    """
    if stage not in STAGE_TO_BUFF and stage is not None:
        raise ValueError("Unknown stage: {!r}".format(stage))
    current = set(current_ids or ())
    desired = ({STAGE_TO_BUFF[stage]} if stage is not None else set())
    existing_stages = current.intersection(STAGE_BUFFS)
    return (existing_stages - desired, desired - existing_stages)

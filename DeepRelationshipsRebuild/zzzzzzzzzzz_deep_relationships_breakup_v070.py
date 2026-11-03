# -*- coding: utf-8 -*-
"""Old tuning class names mapped to the new shared action runtime."""
from deep_relationships import _Interaction


class _DeepRelBreakupInteraction(_Interaction):
    pass


class DeepRelBreakupTalkInteraction(_DeepRelBreakupInteraction):
    ACTION="breakup_talk"
    NAME="Поговорить о расставании"


class DeepRelTakePauseInteraction(_DeepRelBreakupInteraction):
    ACTION="take_pause"
    NAME="Взять паузу"


class DeepRelSaveRelationshipInteraction(_DeepRelBreakupInteraction):
    ACTION="save_relationship"
    NAME="Попробовать спасти отношения"


class DeepRelDecideBreakupInteraction(_DeepRelBreakupInteraction):
    ACTION="decide_breakup"
    NAME="Решить расстаться"

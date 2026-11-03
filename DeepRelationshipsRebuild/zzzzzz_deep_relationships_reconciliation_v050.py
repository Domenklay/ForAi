# -*- coding: utf-8 -*-
"""Compatibility class names for existing Sims 4 interaction tuning.

These are declarations only, not old v0.5 gameplay layers. All logic
delegates to the single clean v0.8 runtime in deep_relationships.py.
"""
from deep_relationships import _Interaction


class _DeepRelReconciliationInteraction(_Interaction):
    pass


class DeepRelDiscussProblemsInteraction(_DeepRelReconciliationInteraction):
    ACTION="discuss"
    NAME="Обсудить проблемы"


class DeepRelApologizeInteraction(_DeepRelReconciliationInteraction):
    ACTION="apologize"
    NAME="Извиниться"


class DeepRelAdmitFaultInteraction(_DeepRelReconciliationInteraction):
    ACTION="admit_fault"
    NAME="Признать вину"


class DeepRelForgiveInteraction(_DeepRelReconciliationInteraction):
    ACTION="forgive"
    NAME="Простить"


class DeepRelNotReadyInteraction(_DeepRelReconciliationInteraction):
    ACTION="not_ready"
    NAME="Не готов простить"


class DeepRelSecondChanceInteraction(_DeepRelReconciliationInteraction):
    ACTION="second_chance"
    NAME="Дать второй шанс"

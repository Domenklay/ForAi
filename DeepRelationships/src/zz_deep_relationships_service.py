# -*- coding: utf-8 -*-
"""Central relationship-service observer for Deep Relationships v0.1.

Loaded after deep_relationships.py. It moves observation from RelationshipTracker
onto RelationshipService so changes made directly by game systems are not missed.
"""

from functools import wraps

import alarms
from date_and_time import create_time_span
from relationships.relationship_service import RelationshipService
from relationships.relationship_track import RelationshipTrack
from relationships.relationship_tracker import RelationshipTracker
from singletons import DEFAULT

import deep_relationships as base


def _restore_tracker_wrapper(function_name):
    try:
        current = getattr(RelationshipTracker, function_name)
        if getattr(current, '_deep_relationships_wrapped', False):
            original = getattr(current, '__wrapped__', None)
            if original is not None:
                setattr(RelationshipTracker, function_name, original)
    except Exception as exc:
        base.logger.exception('Unable to restore tracker method {}: {}', function_name, exc)


# Avoid double counting: the central service is the single observation point.
_restore_tracker_wrapper('add_relationship_score')
_restore_tracker_wrapper('set_relationship_score')


def _kind(track):
    if track is DEFAULT:
        # RelationshipService resolves DEFAULT to the normal inspector/friendship track.
        return 'friendship'
    try:
        if track is RelationshipTrack.ROMANCE_TRACK or track == RelationshipTrack.ROMANCE_TRACK:
            return 'romance'
        if track is RelationshipTrack.FRIENDSHIP_TRACK or track == RelationshipTrack.FRIENDSHIP_TRACK:
            return 'friendship'
    except Exception:
        pass
    return None


def _wrap_service(function_name, handler):
    original = getattr(RelationshipService, function_name)
    if getattr(original, '_deep_relationships_service_wrapped', False):
        return

    @wraps(original)
    def wrapper(*args, **kwargs):
        return handler(original, *args, **kwargs)

    wrapper._deep_relationships_service_wrapped = True
    setattr(RelationshipService, function_name, wrapper)


def _add_handler(original, self, sim_id_a, sim_id_b, increment, track=DEFAULT, threshold=None, **kwargs):
    result = original(self, sim_id_a, sim_id_b, increment, track=track, threshold=threshold, **kwargs)
    try:
        kind = _kind(track)
        if kind is not None:
            base.ENGINE.on_delta(sim_id_a, sim_id_b, float(increment), kind)
    except Exception as exc:
        base.logger.exception('RelationshipService.add observer failed: {}', exc)
    return result


def _set_handler(original, self, sim_id_a, sim_id_b, value, track=DEFAULT, threshold=None, **kwargs):
    kind = _kind(track)
    before = None
    if kind is not None:
        try:
            before = float(self.get_relationship_score(sim_id_a, sim_id_b, track=track))
        except Exception:
            before = None
    result = original(self, sim_id_a, sim_id_b, value, track=track, threshold=threshold, **kwargs)
    if kind is not None and before is not None:
        try:
            after = float(self.get_relationship_score(sim_id_a, sim_id_b, track=track))
            delta = after - before
            if abs(delta) > 0.0001:
                base.ENGINE.on_delta(sim_id_a, sim_id_b, delta, kind)
        except Exception as exc:
            base.logger.exception('RelationshipService.set observer failed: {}', exc)
    return result


_wrap_service('add_relationship_score', _add_handler)
_wrap_service('set_relationship_score', _set_handler)


# Alarm creation is attempted again on zone load. This makes the periodic
# relationship-decay system robust even if the custom service started before
# the game time service was fully available.
_original_zone_load = base.DeepRelationshipsService.on_zone_load


def _enhanced_zone_load(self, *args, **kwargs):
    try:
        if self._alarm_handle is None:
            self._alarm_handle = alarms.add_alarm(
                self,
                create_time_span(minutes=360),
                self._on_tick,
                repeating=True
            )
    except Exception as exc:
        base.logger.exception('Unable to start relationship alarm on zone load: {}', exc)
    return _original_zone_load(self, *args, **kwargs)


base.DeepRelationshipsService.on_zone_load = _enhanced_zone_load
base.logger.info('Deep Relationships central RelationshipService observer enabled.')

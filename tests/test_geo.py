"""Unit tests for geo.haversine."""
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from geo import haversine

# Generic coordinates used for testing — not real locations
_LAT_A, _LON_A = 12.9000, 77.6000   # point A (city area, generic)
_LAT_B, _LON_B = 12.9100, 77.6100   # point B (~1.4 km from A)
_LAT_BUS, _LON_BUS = 12.9050, 77.6050  # simulated bus position


def test_same_point_is_zero():
    assert haversine(_LAT_A, _LON_A, _LAT_A, _LON_A) == 0.0


def test_known_distance_approx():
    # ~1.4 km between two points ~0.01 degrees apart
    dist = haversine(_LAT_A, _LON_A, _LAT_B, _LON_B)
    assert 0.5 < dist < 5.0


def test_symmetry():
    d1 = haversine(_LAT_A, _LON_A, _LAT_B, _LON_B)
    d2 = haversine(_LAT_B, _LON_B, _LAT_A, _LON_A)
    assert math.isclose(d1, d2, rel_tol=1e-9)


def test_distance_is_positive():
    assert haversine(0.0, 0.0, 1.0, 1.0) > 0.0


def test_bus_within_geofence():
    # Simulated bus at _LAT_BUS/_LON_BUS, home at _LAT_A/_LON_A — should be within 5 km
    dist = haversine(_LAT_BUS, _LON_BUS, _LAT_A, _LON_A)
    assert 0.0 < dist < 5.0

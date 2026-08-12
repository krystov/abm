"""Tests for Adopter agent class."""

from agents import Adopter, AdopterType


class TestAdopter:
    def test_creation_residential(self):
        a = Adopter(
            agent_id=1,
            adopter_type=AdopterType.RESIDENTIAL,
            location=(50.0, 50.0),
            system_size=5.0,
            self_consumption_rate=0.30,
            electricity_price=0.25,
            discount_rate=0.04,
        )
        assert a.agent_id == 1
        assert a.adopter_type == AdopterType.RESIDENTIAL
        assert a.is_adopted is False
        assert a.system_size == 5.0
        assert 0 <= a.environmental_awareness <= 1

    def test_creation_commercial(self):
        a = Adopter(
            agent_id=2,
            adopter_type=AdopterType.COMMERCIAL_INDUSTRIAL,
            location=(30.0, 70.0),
            system_size=25.0,
            self_consumption_rate=0.20,
            electricity_price=0.20,
            discount_rate=0.05,
        )
        assert a.adopter_type == AdopterType.COMMERCIAL_INDUSTRIAL

    def test_location_is_tuple(self):
        a = Adopter(
            agent_id=3,
            adopter_type=AdopterType.UTILITY_SCALE,
            location=(10.0, 90.0),
            system_size=100.0,
        )
        assert isinstance(a.location, tuple)
        assert len(a.location) == 2

    def test_default_values(self):
        a = Adopter(
            agent_id=4,
            adopter_type=AdopterType.RESIDENTIAL,
            location=(0.0, 0.0),
        )
        assert a.is_adopted is False
        assert a.intention == 0.0
        assert a.pv_orientation == 0.9
        assert a.peer_radius_km == 1.0

    def test_update_awareness_assimilation(self):
        a = Adopter(
            agent_id=5,
            adopter_type=AdopterType.RESIDENTIAL,
            location=(0.0, 0.0),
            environmental_awareness=0.3,
        )
        a.update_awareness(media_coverage=0.8, assimilation_rate=0.1)
        expected = 0.3 * 0.9 + 0.8 * 0.1  # = 0.27 + 0.08 = 0.35
        assert abs(a.environmental_awareness - expected) < 0.001

    def test_update_awareness_converges_to_media(self):
        a = Adopter(
            agent_id=6,
            adopter_type=AdopterType.RESIDENTIAL,
            location=(0.0, 0.0),
            environmental_awareness=0.2,
        )
        for _ in range(100):
            a.update_awareness(media_coverage=0.9, assimilation_rate=0.05)
        assert abs(a.environmental_awareness - 0.9) < 0.01

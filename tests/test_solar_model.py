"""Tests for SolarModel agent initialisation (roof-size heterogeneity)."""

from agents import AdopterType
from model.solar_model import SolarModel

_CATEGORY_RANGES = {
    AdopterType.RESIDENTIAL: (0.5, 10.0),
    AdopterType.COMMERCIAL_INDUSTRIAL: (10.0, 40.0),
    AdopterType.UTILITY_SCALE: (40.0, 500.0),
}


def test_roof_size_bounds_system_size():
    model = SolarModel(n_ticks=1, n_adopters=300, use_llm=False, seed=7)
    for a in model.adopters:
        assert a.roof_size > 0
        lo, hi = _CATEGORY_RANGES[a.adopter_type]
        assert lo <= a.system_size <= hi


def test_system_size_is_roof_driven_when_unclipped():
    model = SolarModel(n_ticks=1, n_adopters=300, use_llm=False, seed=7)
    checked = 0
    for a in model.adopters:
        lo, hi = _CATEGORY_RANGES[a.adopter_type]
        expected = a.roof_size * 0.15
        if lo < expected < hi:  # interior, not clipped to a category boundary
            assert abs(a.system_size - expected) < 0.006
            checked += 1
    assert checked > 0  # the assertion actually exercised some agents

"""Tests for Manufacturer agent class."""

from agents import Manufacturer, Region
from schemas import ManufacturerDecision


class TestManufacturer:
    def test_creation_domestic(self):
        m = Manufacturer(
            manufacturer_id=1,
            region=Region.DOMESTIC,
            capacity=500.0,
            module_efficiency=0.15,
            production_cost=1.50,
            price=2.25,
            knowledge_stock=100.0,
            cumulative_production=500.0,
            employees=2000,
        )
        assert m.manufacturer_id == 1
        assert m.region == Region.DOMESTIC
        assert m.capacity == 500.0

    def test_creation_foreign(self):
        m = Manufacturer(
            manufacturer_id=2,
            region=Region.FOREIGN,
            capacity=2000.0,
            module_efficiency=0.14,
            production_cost=1.10,
            price=1.43,
            knowledge_stock=200.0,
            cumulative_production=2000.0,
            employees=5000,
        )
        assert m.region == Region.FOREIGN

    def test_apply_capacity_change_expand(self):
        m = Manufacturer(
            manufacturer_id=1,
            region=Region.DOMESTIC,
            capacity=500.0,
            module_efficiency=0.15,
        )
        original = m.capacity
        m._apply_capacity_change("expand", 0.10)
        assert m.capacity > original
        assert m.capacity <= original * 1.5  # within max increase

    def test_apply_capacity_change_reduce(self):
        m = Manufacturer(
            manufacturer_id=1,
            region=Region.DOMESTIC,
            capacity=100_000.0,
            min_capacity=1_000.0,
            module_efficiency=0.15,
        )
        original = m.capacity
        m._apply_capacity_change("reduce", 0.10)
        assert m.capacity < original

    def test_apply_capacity_change_maintain(self):
        m = Manufacturer(
            manufacturer_id=1,
            region=Region.DOMESTIC,
            capacity=500.0,
            module_efficiency=0.15,
        )
        original = m.capacity
        m._apply_capacity_change("maintain", 0.0)
        assert m.capacity == original

    def test_experience_curve_fallback(self):
        m = Manufacturer(
            manufacturer_id=1,
            region=Region.DOMESTIC,
            capacity=500.0,
            module_efficiency=0.15,
            production_cost=1.50,
            price=2.25,
            knowledge_stock=100.0,
            cumulative_production=500.0,
            sales=10.0,
            rd_spending=1000.0,
            learning_by_doing_rate=0.20,
            learning_by_research_rate=0.10,
            experience_curve_intercept=1.50,
            cp_initial=500.0,
            ks_initial=100.0,
            mark_up=0.50,
        )
        decision = m._experience_curve_fallback(0.25, 0.40, 600.0)
        assert isinstance(decision, ManufacturerDecision)
        assert decision.action in ("expand", "maintain", "reduce")

    def test_apply_llm_decision(self):
        m = Manufacturer(
            manufacturer_id=1,
            region=Region.DOMESTIC,
            capacity=500.0,
            module_efficiency=0.15,
            production_cost=1.50,
            price=2.25,
            knowledge_stock=100.0,
            cumulative_production=500.0,
            sales=10.0,
            rd_spending=1000.0,
            learning_by_doing_rate=0.20,
            learning_by_research_rate=0.10,
            experience_curve_intercept=1.50,
            cp_initial=500.0,
            ks_initial=100.0,
            mark_up=0.50,
        )
        decision = ManufacturerDecision(
            action="expand",
            change_percentage=0.10,
            rd_focus="cost_reduction",
            reasoning="Test decision",
        )
        m.apply_llm_decision(decision)
        assert m.capacity > 500.0

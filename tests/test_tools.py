"""Tests for agent tools: query functions and registry builders."""

from agents.tools import (
    _calculate_payback_years,
    _query_manufacturer_state,
    _query_market_conditions,
    _query_neighbor_adoption,
    build_adopter_tools,
    build_manufacturer_tools,
)


class TestQueryMarketConditions:
    def test_returns_all_fields(self):
        result = _query_market_conditions(
            electricity_price=0.25,
            fit_tariff=0.50,
            module_price_domestic=0.80,
            module_price_foreign=0.60,
            bos_cost=1.00,
            market_maturity=0.15,
        )
        assert result["electricity_price_eur_kwh"] == 0.25
        assert result["feed_in_tariff_eur_kwh"] == 0.50
        assert result["total_system_cost_eur_w"] == 1.80
        assert result["market_maturity_pct"] == 15.0

    def test_domestic_and_foreign_prices_differ(self):
        result = _query_market_conditions(0.25, 0.50, 0.80, 0.60, 1.00, 0.15)
        assert result["module_price_domestic_eur_w"] == 0.80
        assert result["module_price_foreign_eur_w"] == 0.60


class TestQueryNeighborAdoption:
    def test_high(self):
        r = _query_neighbor_adoption(0.45)
        assert r["social_pressure_level"] == "high"

    def test_moderate(self):
        r = _query_neighbor_adoption(0.15)
        assert r["social_pressure_level"] == "moderate"

    def test_low(self):
        r = _query_neighbor_adoption(0.05)
        assert r["social_pressure_level"] == "low"

    def test_pct(self):
        r = _query_neighbor_adoption(0.33)
        assert r["neighbour_adoption_pct"] == 33.0


class TestCalculatePayback:
    def test_excellent_investment(self):
        r = _calculate_payback_years(
            system_size_kw=5.0,
            module_price_per_w=0.50,
            bos_cost_per_w=0.30,
            electricity_price=0.25,
            fit_tariff=0.40,
            self_consumption_rate=0.30,
        )
        assert r["payback_years"] is not None
        assert r["payback_years"] < 8
        assert "excellent" in r["verdict"]

    def test_never_profitable(self):
        r = _calculate_payback_years(
            system_size_kw=5.0,
            module_price_per_w=5.00,
            bos_cost_per_w=3.00,
            electricity_price=0.25,
            fit_tariff=0.0,
            self_consumption_rate=0.30,
        )
        assert r["payback_years"] is None
        assert "never" in r["verdict"]

    def test_returns_investment_and_savings(self):
        r = _calculate_payback_years(5.0, 0.50, 0.30, 0.25, 0.40, 0.30)
        assert r["investment_eur"] > 0
        assert "annual_savings_eur" in r


class TestQueryManufacturerState:
    def test_returns_all_fields(self):
        r = _query_manufacturer_state(
            capacity=500.0, production_cost=0.80, price=1.20,
            module_efficiency=0.15, knowledge_stock=100.0,
            cumulative_production=2000.0, stock=50.0, sales=300.0,
        )
        assert r["capacity_mw_month"] == 500.0
        assert r["production_cost_eur_w"] == 0.80
        assert r["gross_margin_pct"] > 0
        assert r["capacity_utilization_pct"] == 60.0

    def test_capacity_utilization_zero_sales(self):
        r = _query_manufacturer_state(
            capacity=500.0, production_cost=0.80, price=1.20,
            module_efficiency=0.15, knowledge_stock=100.0,
            cumulative_production=2000.0, stock=50.0, sales=0.0,
        )
        assert r["capacity_utilization_pct"] == 0.0


class TestBuildAdopterTools:
    def test_registry_has_three_tools(self):
        reg = build_adopter_tools(
            electricity_price=0.25, fit_tariff=0.50,
            module_price_domestic=0.80, module_price_foreign=0.60,
            bos_cost=1.00, market_maturity=0.15, neighbour_ratio=0.25,
            system_size_kw=5.0, self_consumption_rate=0.30,
        )
        assert len(reg) == 3
        names = [s["function"]["name"] for s in reg.get_specs()]
        assert "query_market_conditions" in names
        assert "query_neighbor_adoption" in names
        assert "calculate_payback" in names

    def test_tools_return_json_strings(self):
        import asyncio
        reg = build_adopter_tools(
            electricity_price=0.25, fit_tariff=0.50,
            module_price_domestic=0.80, module_price_foreign=0.60,
            bos_cost=1.00, market_maturity=0.15, neighbour_ratio=0.25,
            system_size_kw=5.0, self_consumption_rate=0.30,
        )
        import json
        for spec in reg.get_specs():
            name = spec["function"]["name"]
            result = asyncio.run(reg.invoke(name, {}))
            parsed = json.loads(result)
            assert "error" not in parsed


class TestBuildManufacturerTools:
    def test_registry_has_two_tools(self):
        reg = build_manufacturer_tools(
            electricity_price=0.25, fit_tariff=0.50,
            order_backlog=100.0, tech_push_level=3,
            capacity=500.0, production_cost=0.80, price=1.20,
            module_efficiency=0.15, knowledge_stock=100.0,
            cumulative_production=2000.0, stock=50.0, sales=300.0,
        )
        assert len(reg) == 2
        names = [s["function"]["name"] for s in reg.get_specs()]
        assert "query_market_conditions" in names
        assert "query_my_state" in names

    def test_tools_return_json_strings(self):
        import asyncio, json
        reg = build_manufacturer_tools(
            electricity_price=0.25, fit_tariff=0.50,
            order_backlog=100.0, tech_push_level=3,
            capacity=500.0, production_cost=0.80, price=1.20,
            module_efficiency=0.15, knowledge_stock=100.0,
            cumulative_production=2000.0, stock=50.0, sales=300.0,
        )
        for spec in reg.get_specs():
            name = spec["function"]["name"]
            result = asyncio.run(reg.invoke(name, {}))
            parsed = json.loads(result)
            assert "error" not in parsed

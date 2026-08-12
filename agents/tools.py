"""
Callable tools for LLM-augmented ABM agents.

Each tool exposes market data or computation that an agent can query
during its LLM decision step (OpenAI function-calling compatible).
"""

from agents.agent_framework import Tool, ToolRegistry


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _query_market_conditions(
    electricity_price: float,
    fit_tariff: float,
    module_price_domestic: float,
    module_price_foreign: float,
    bos_cost: float,
    market_maturity: float,
) -> dict:
    """Return current market snapshotted data."""
    return {
        "electricity_price_eur_kwh": round(electricity_price, 4),
        "feed_in_tariff_eur_kwh": round(fit_tariff, 4),
        "module_price_domestic_eur_w": round(module_price_domestic, 4),
        "module_price_foreign_eur_w": round(module_price_foreign, 4),
        "bos_installation_cost_eur_w": round(bos_cost, 4),
        "total_system_cost_eur_w": round(module_price_domestic + bos_cost, 4),
        "market_maturity_pct": round(market_maturity * 100, 1),
    }


def _query_neighbor_adoption(neighbour_ratio: float) -> dict:
    """Return neighbor adoption statistics."""
    return {
        "neighbour_adoption_ratio": round(neighbour_ratio, 4),
        "neighbour_adoption_pct": round(neighbour_ratio * 100, 1),
        "social_pressure_level": (
            "high" if neighbour_ratio > 0.3 else
            "moderate" if neighbour_ratio > 0.1 else
            "low"
        ),
    }


def _calculate_payback_years(
    system_size_kw: float,
    module_price_per_w: float,
    bos_cost_per_w: float,
    electricity_price: float,
    fit_tariff: float,
    self_consumption_rate: float,
) -> dict:
    """Estimate simple payback period (ignoring discounting)."""
    investment = (module_price_per_w + bos_cost_per_w) * system_size_kw * 1000
    annual_gen = system_size_kw * 938.0 * 0.85  # kWh
    self_cons = annual_gen * self_consumption_rate
    export = annual_gen * (1 - self_consumption_rate)
    annual_savings = self_cons * electricity_price + export * fit_tariff
    maintenance = investment * 0.015
    net_annual = annual_savings - maintenance

    if net_annual <= 0:
        payback = None
        verdict = "never profitable"
    else:
        payback = round(investment / net_annual, 1)
        if payback < 8:
            verdict = "excellent investment"
        elif payback < 15:
            verdict = "good investment"
        elif payback < 20:
            verdict = "marginal investment"
        else:
            verdict = "poor investment"

    return {
        "investment_eur": round(investment, 0),
        "annual_savings_eur": round(net_annual, 0),
        "payback_years": payback,
        "verdict": verdict,
    }


def _query_manufacturer_state(
    capacity: float,
    production_cost: float,
    price: float,
    module_efficiency: float,
    knowledge_stock: float,
    cumulative_production: float,
    stock: float,
    sales: float,
) -> dict:
    """Return current manufacturer state summary."""
    return {
        "capacity_mw_month": round(capacity, 2),
        "production_cost_eur_w": round(production_cost, 4),
        "selling_price_eur_w": round(price, 4),
        "gross_margin_pct": round((price - production_cost) / max(price, 0.001) * 100, 1),
        "module_efficiency_pct": round(module_efficiency * 100, 2),
        "knowledge_stock": round(knowledge_stock, 1),
        "cumulative_production_mw": round(cumulative_production, 1),
        "inventory_mw": round(stock, 2),
        "sales_last_month_mw": round(sales, 2),
        "capacity_utilization_pct": round(sales / max(capacity, 0.001) * 100, 1),
    }


# ---------------------------------------------------------------------------
# Tool registry builder
# ---------------------------------------------------------------------------

def build_adopter_tools(
    electricity_price: float,
    fit_tariff: float,
    module_price_domestic: float,
    module_price_foreign: float,
    bos_cost: float,
    market_maturity: float,
    neighbour_ratio: float,
    system_size_kw: float,
    self_consumption_rate: float,
) -> ToolRegistry:
    """Create a tool registry with current market context baked in for an adopter."""
    registry = ToolRegistry()

    registry.register(Tool(
        name="query_market_conditions",
        description="Get current electricity price, feed-in tariff, module prices, and installation costs in Germany this month.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        fn=lambda: _query_market_conditions(
            electricity_price, fit_tariff,
            module_price_domestic, module_price_foreign,
            bos_cost, market_maturity,
        ),
    ))

    registry.register(Tool(
        name="query_neighbor_adoption",
        description="Check what fraction of your neighbours have already installed solar PV.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        fn=lambda: _query_neighbor_adoption(neighbour_ratio),
    ))

    registry.register(Tool(
        name="calculate_payback",
        description="Estimate the simple payback period (years) if you install a PV system of your size at current prices.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        fn=lambda: _calculate_payback_years(
            system_size_kw, module_price_domestic, bos_cost,
            electricity_price, fit_tariff, self_consumption_rate,
        ),
    ))

    return registry


def build_manufacturer_tools(
    electricity_price: float,
    fit_tariff: float,
    order_backlog: float,
    tech_push_level: float,
    capacity: float,
    production_cost: float,
    price: float,
    module_efficiency: float,
    knowledge_stock: float,
    cumulative_production: float,
    stock: float,
    sales: float,
) -> ToolRegistry:
    """Create a tool registry for a manufacturer agent."""
    registry = ToolRegistry()

    registry.register(Tool(
        name="query_market_conditions",
        description="Get current electricity price, FiT, and installer order backlog in Germany.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        fn=lambda: {
            "electricity_price_eur_kwh": round(electricity_price, 4),
            "feed_in_tariff_eur_kwh": round(fit_tariff, 4),
            "installer_order_backlog_mw": round(order_backlog, 2),
            "government_rd_push_level": int(tech_push_level),
        },
    ))

    registry.register(Tool(
        name="query_my_state",
        description="Get my current manufacturing state: capacity, costs, inventory, efficiency, knowledge stock.",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
        fn=lambda: _query_manufacturer_state(
            capacity, production_cost, price, module_efficiency,
            knowledge_stock, cumulative_production, stock, sales,
        ),
    ))

    return registry

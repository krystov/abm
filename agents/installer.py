"""
Installer agent — PV system installer (domestic or foreign).

State variables per Tables SI 3, SI 5 of the supplementary information.
The foreign installer is simplified: always meets demand.
"""

from dataclasses import dataclass

from agents.manufacturer import Region


@dataclass
class Installer:
    """PV system installer — one per region (domestic & foreign).

    The foreign installer is simplified: no employees, no stock, always meets
    demand (text §1.3.3.2). The domestic installer holds inventory, manages a
    workforce, and its non-module costs evolve via a one-factor experience curve.

    Table SI 3 — Supply-chain state variables:
        region, employees, order_backlog, stock_domestic, stock_foreign,
        cumulative_installations, demand, sales, labor_productivity, mark_up,
        min/max workforce constraints, past_months_demand

    Table SI 5 row 1 & 4 — Non-module experience curve:
        beta_learning_by_doing_non_module, experience_curve_intercept_non_module
    """

    installer_id: int
    region: Region
    employees: int = 0
    labor_productivity: float = 0.0
    min_employees: int = 1_000
    max_workforce_increase: float = 2.0
    max_workforce_decrease: float = 0.5
    order_backlog: float = 0.0
    stock_domestic: float = 0.0
    stock_foreign: float = 0.0
    demand_domestic: float = 0.0
    demand_foreign: float = 0.0
    sales_domestic: float = 0.0
    sales_foreign: float = 0.0
    bos_cost: float = 0.0
    mark_up: float = 0.0
    cumulative_installations: float = 0.0
    experience_curve_intercept_non_module: float = 3.354
    beta_learning_by_doing_non_module: float = -0.155
    past_months_demand: int = 6
    ci_initial: float = 1.0

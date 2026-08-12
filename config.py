"""
Central configuration for the Germany Solar PV Policy Mix ABM.

All tunable parameters are collected here so they can be adjusted without
digging through agent or model code.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Simulation-level configuration."""

    # Simulation horizon
    n_ticks: int = 312          # months (1991–2016 = 26 years)
    n_adopters: int = 500       # scaled 1:1000 from ~20.8M buildings

    # Random seed for reproducibility
    seed: int = 42

    # LLM settings
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.3
    llm_adopter_fraction: float = 0.05  # fraction of undecided adopters using LLM per tick
    llm_max_retries: int = 2

    # Whether to use real historical data (True) or synthetic (False)
    use_real_data: bool = False

    # Output
    results_path: str = "results.png"
    verbose: bool = True

    # API key (read from env if not set)
    openai_api_key: Optional[str] = None


@dataclass
class AdopterConfig:
    """Calibration parameters for adopter agents (Tables SI 1, SI 2, SI 11)."""

    # Population proportions (Table SI 1, scaled 1:1000)
    residential_population: int = 16_891
    commercial_population: int = 3_853
    utility_population: int = 85

    # System size ranges by category [kWp]
    residential_system_range: tuple = (0.5, 10.0)
    commercial_system_range: tuple = (10.0, 40.0)
    utility_system_range: tuple = (40.0, 10_000.0)

    # Self-consumption means by category
    residential_self_cons_mean: float = 0.30
    commercial_self_cons_mean: float = 0.20
    utility_self_cons_mean: float = 0.40
    self_cons_sd: float = 0.05

    # Electricity prices by category [EUR/kWh]
    residential_elec_price: float = 0.25
    commercial_elec_price: float = 0.20
    utility_elec_price: float = 0.18

    # Discount rates by category
    residential_discount: float = 0.04
    commercial_discount: float = 0.05
    utility_discount: float = 0.06

    # Technology sensing (Table SI 4)
    pv_performance_ratio: float = 0.85
    maintenance_cost_ratio: float = 0.015
    irradiation_kwh: float = 938.0

    # Peer effect radius [km] (Table SI 6)
    peer_radius_km: float = 1.0

    # TPB weights (Table SI 11)
    w_att: float = 0.55
    w_sn: float = 0.30
    w_pbc: float = 0.15
    w_env: float = 0.4
    w_eco: float = 0.6
    env_shortcut_threshold: float = 0.88

    # NPV calculation
    system_lifespan_months: int = 240


@dataclass
class ManufacturerConfig:
    """Calibration parameters for manufacturer agents (Tables SI 3, SI 5)."""

    # Domestic manufacturer defaults
    domestic_capacity: float = 500.0            # MW/month
    domestic_module_efficiency: float = 0.15    # 15%
    domestic_production_cost: float = 1.50      # EUR/W
    domestic_price: float = 2.25                # EUR/W
    domestic_knowledge_stock: float = 100.0
    domestic_cumulative_production: float = 500.0
    domestic_stock: float = 100.0
    domestic_employees: int = 2_000
    domestic_labor_productivity: float = 2.5    # kWp/month/worker
    domestic_mark_up: float = 0.50
    domestic_rd_spending_ratio: float = 0.05
    domestic_rd_spending: float = 50_000.0
    domestic_learning_by_doing: float = 0.20
    domestic_learning_by_research: float = 0.10
    domestic_experience_intercept: float = 1.50
    domestic_knowledge_depreciation: float = 0.008742
    domestic_spillover_in: float = 0.15
    domestic_spillover_delay: int = 12

    # Foreign manufacturer defaults
    foreign_capacity: float = 2_000.0
    foreign_module_efficiency: float = 0.14
    foreign_production_cost: float = 1.10
    foreign_price: float = 1.43
    foreign_knowledge_stock: float = 200.0
    foreign_cumulative_production: float = 2_000.0
    foreign_stock: float = 500.0
    foreign_employees: int = 5_000
    foreign_labor_productivity: float = 4.0
    foreign_mark_up: float = 0.30
    foreign_rd_spending_ratio: float = 0.02
    foreign_rd_spending: float = 30_000.0
    foreign_learning_by_doing: float = 0.18
    foreign_learning_by_research: float = 0.08
    foreign_experience_intercept: float = 1.10
    foreign_knowledge_depreciation: float = 0.008742
    foreign_spillover_in: float = 0.10
    foreign_spillover_delay: int = 18

    # Workforce constraints (Table SI 3)
    min_employees: int = 1_000
    max_workforce_increase: float = 2.0
    max_workforce_decrease: float = 0.5

    # Capacity constraints (Table SI 3)
    min_capacity: float = 50_000.0      # kWp/month = 50 MW/month
    utilization_rate_margin: float = 1.3333
    max_capacity_increase: float = 3.0
    max_capacity_decrease: float = 0.5

    # Knowledge dynamics (Table SI 5)
    knowledge_delay: int = 36
    knowledge_depreciation: float = 0.008742


@dataclass
class InstallerConfig:
    """Calibration parameters for installer agents (Tables SI 3, SI 5)."""

    # Domestic installer
    domestic_employees: int = 1_500
    domestic_labor_productivity: float = 2.0   # kWp/month/worker
    domestic_bos_cost: float = 1.00            # EUR/W
    domestic_mark_up: float = 0.25
    domestic_cumulative_installations: float = 200.0
    domestic_stock_domestic: float = 50.0
    domestic_stock_foreign: float = 50.0

    # Foreign installer
    foreign_employees: int = 500
    foreign_labor_productivity: float = 3.0
    foreign_bos_cost: float = 0.60
    foreign_mark_up: float = 0.20
    foreign_cumulative_installations: float = 800.0
    foreign_stock_domestic: float = 0.0
    foreign_stock_foreign: float = 200.0

    # Non-module experience curve (Table SI 5)
    experience_curve_intercept: float = 3.354
    learning_by_doing_rate: float = 0.102

    # Workforce constraints
    min_employees: int = 1_000
    max_workforce_increase: float = 2.0
    max_workforce_decrease: float = 0.5

    # Hiring memory
    past_months_demand: int = 6


# Singleton defaults
model = ModelConfig()
adopter = AdopterConfig()
manufacturer = ManufacturerConfig()
installer = InstallerConfig()

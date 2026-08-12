"""
Two-factor experience curve sub-model for manufacturer cost reduction.

§3.2:
  MC_t = MC_0 · (CP_t / CP_0)^(-b) · (KS_t / KS_0)^(-c)

where:
  CP_t = cumulative production (learning-by-doing)
  KS_t = knowledge stock     (learning-by-searching)

Knowledge stock evolves via perpetual inventory (§3.2.1):
  KS_t = (1 - δ) · KS_{t-1} + R&D_t
"""

import math


def update_knowledge_stock(
    ks_current: float,
    rd_spending: float,
    depreciation: float = 0.008742,
) -> float:
    """Perpetual inventory update for knowledge stock (Eq. 25).

    δ ≈ 10% p.a. → 0.008742 per month.
    """
    return (1.0 - depreciation) * ks_current + rd_spending


def compute_production_cost(
    cumulative_production: float,
    knowledge_stock: float,
    cp_initial: float,
    ks_initial: float,
    intercept: float,
    learning_by_doing_rate: float,
    learning_by_research_rate: float,
) -> float:
    """Two-factor experience curve (Eq. 24).

    MC_t = MC_0 · (CP_t / CP_0)^(-b) · (KS_t / KS_0)^(-c)

    Returns production cost in EUR/W.
    """
    cp_ratio = max(cumulative_production / max(cp_initial, 0.001), 0.001)
    ks_ratio = max(knowledge_stock / max(ks_initial, 0.001), 0.001)
    return (
        intercept
        * math.pow(cp_ratio, -learning_by_doing_rate)
        * math.pow(ks_ratio, -learning_by_research_rate)
    )


def compute_non_module_cost(
    cumulative_installations: float,
    ci_initial: float,
    intercept: float = 3.354,
    learning_rate: float = 0.102,
) -> float:
    """One-factor experience curve for installer BOS cost (Eq. 22).

    BOS_t = BOS_intercept · (CI_t / CI_0)^(-learning_rate)
    """
    ci_ratio = max(cumulative_installations / max(ci_initial, 0.001), 0.001)
    return intercept * math.pow(ci_ratio, -learning_rate)

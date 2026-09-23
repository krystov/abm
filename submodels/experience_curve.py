"""
Two-factor experience curve sub-model for manufacturer cost reduction.

Paper form (Supplementary Information, Equations 22 & 24, Tables SI 4 / SI 53):

  c_t = α · (CP_t / CP₀)^β_LBD · (KS_t / KS₀)^β_LBR      (PV modules, Eq. 24)
  BOS_t = α_I · (CI_t / CI₀)^β_I                          (non-module, Eq. 22)

where the exponents β are the log-log slopes (negative), each related to the
"learning rate" LR — the fractional cost reduction per doubling of the driver —
by β = log2(1 − LR).  The intercept α is the cost at the reference point
(CP = CP₀, KS = KS₀).  Table SI 53 reports α and β directly for each region.

Knowledge stock evolves via perpetual inventory (Equation 25):
  KS_t = (1 − δ) · KS_{t-1} + R&D_t
"""

import math

# ---------------------------------------------------------------------------
# Calibrated experience-curve parameters (Table SI 4 / SI 53 + §14-15)
# ---------------------------------------------------------------------------

# Intercepts α: cost [€/W] at the reference CP₀/KS₀ (or CI₀) baseline.
INTERCEPT_DOMESTIC = 2.882
INTERCEPT_FOREIGN = 2.448
INTERCEPT_NON_MODULE = 3.354

# Log-log slopes β (learning-by-doing, learning-by-research, non-module).
# LR = 1 − 2^β  ⇒  β = log2(1 − LR).
BETA_LBD_DOMESTIC = -0.074   # LR 5.0%   (per doubling of cumulative production)
BETA_LBD_FOREIGN = -0.448    # LR 26.7%
BETA_LBR_DOMESTIC = -0.814   # LR 43.1%  (per doubling of knowledge stock)
BETA_LBR_FOREIGN = -0.074    # LR 5.0%
BETA_NON_MODULE = -0.155     # LR 10.2%  (per doubling of cumulative installations)

# Knowledge depreciation δ ≈ 10% p.a. → 0.8742% per month (Table SI 4 / SI 53).
KNOWLEDGE_DEPRECIATION_MONTHLY = 0.008742


def learning_rate_to_beta(learning_rate: float) -> float:
    """Convert a learning rate (fraction) to its log-log slope β.

    β = log2(1 − LR) = ln(1 − LR) / ln(2).

    Examples (Table SI 53):
        LR 5.0%  → −0.074
        LR 10.2% → −0.155
        LR 26.7% → −0.448
        LR 43.1% → −0.814
    """
    if not 0.0 <= learning_rate < 1.0:
        raise ValueError(f"learning rate must be in [0, 1), got {learning_rate}")
    return math.log(1.0 - learning_rate) / math.log(2.0)


def update_knowledge_stock(
    ks_current: float,
    rd_spending: float,
    depreciation: float = KNOWLEDGE_DEPRECIATION_MONTHLY,
) -> float:
    """Perpetual inventory update for knowledge stock (Eq. 25).

    KS_t = (1 − δ) · KS_{t-1} + R&D_t,  δ ≈ 0.8742% per month (10% p.a.).
    """
    return (1.0 - depreciation) * ks_current + rd_spending


def compute_production_cost(
    cumulative_production: float,
    knowledge_stock: float,
    cp_initial: float,
    ks_initial: float,
    intercept: float,
    beta_learning_by_doing: float,
    beta_learning_by_research: float,
) -> float:
    """Two-factor experience curve for PV module cost (Eq. 24).

    c = α · (CP/CP₀)^β_LBD · (KS/KS₀)^β_LBR

    β_LBD and β_LBR are the negative log-log slopes (Table SI 53).  Returns
    production cost in EUR/W.
    """
    cp_ratio = max(cumulative_production / max(cp_initial, 0.001), 0.001)
    ks_ratio = max(knowledge_stock / max(ks_initial, 0.001), 0.001)
    return (
        intercept
        * math.pow(cp_ratio, beta_learning_by_doing)
        * math.pow(ks_ratio, beta_learning_by_research)
    )


def compute_non_module_cost(
    cumulative_installations: float,
    ci_initial: float,
    intercept: float = INTERCEPT_NON_MODULE,
    beta: float = BETA_NON_MODULE,
) -> float:
    """One-factor experience curve for installer BOS cost (Eq. 22).

    BOS_t = α_I · (CI_t / CI₀)^β_I,  with β_I = −0.155 (10.2% learning rate).
    """
    ci_ratio = max(cumulative_installations / max(ci_initial, 0.001), 0.001)
    return intercept * math.pow(ci_ratio, beta)

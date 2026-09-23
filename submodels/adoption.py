"""
Paper-faithful two-stage adoption sub-model.

Nuñez-Jimenez et al. (2022), Supplementary Information.

Stage 1 — Ideation (Equation 2): an adopter "gets the idea" to install PV when
    k_peers·PE + k_info·IN + k_awareness·AW + k_attractive·IRR > 0.5

Stage 2 — Economic & environmental evaluation (Equations 3–10): among those who
develop the idea, early adopters (residential AND AW > Θ_env) install directly;
everyone else computes domestic/foreign NPV and adopts iff the largest NPV ≥ 0
(ties resolved in favour of domestic modules).

Calibration values from Tables SI 10 / SI 11 / SI 15.
"""

import math
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Calibrated adoption parameters
# ---------------------------------------------------------------------------

# Ideation weights (Table SI 11): awareness, info, attractive are calibrated;
# peers is linearly dependent so the four sum to one.
K_AWARENESS = 0.52
K_INFO = 0.17
K_ATTRACTIVE = 0.12
K_PEERS = 1.0 - K_AWARENESS - K_INFO - K_ATTRACTIVE  # 0.19

IDEATION_THRESHOLD = 0.5

# High-awareness threshold Θ_env (Table SI 10/11): early adopters skip the
# economic evaluation and install directly.
ENV_THRESHOLD = 0.92

# Foreign-module discount premium R^f (Table SI 10: Df = 1.1% p.a.).
FOREIGN_DISCOUNT_PREMIUM = 0.011

# ---------------------------------------------------------------------------
# Technology sensing constants (Table SI 4)
# ---------------------------------------------------------------------------

PERFORMANCE_RATIO = 0.85
MAINTENANCE_RATIO = 0.015
AVERAGE_IRRADIATION = 938.0  # kWh/m²/year
LIFESPAN_YEARS = 20

# ---------------------------------------------------------------------------
# Scale effect (Equation 7)
# ---------------------------------------------------------------------------

SCALE_A = 1.1246
SCALE_B = -0.051


def scale_effect(system_size_kw: float) -> float:
    """Economies of scale for a PV system (Equation 7).

    SE = 1.1246 · S^-0.051 if S ≥ 1 kWp, else 1.2.
    """
    if system_size_kw >= 1.0:
        return SCALE_A * (system_size_kw ** SCALE_B)
    return 1.2


# ---------------------------------------------------------------------------
# Information index IN_t (Table SI 15 + Equation 30)
# ---------------------------------------------------------------------------

INFO_ALPHA = -52.76
INFO_K = -6.69e-8
INFO_X0 = -4.00
INFO_L = 53.75


def information_index(cumulative_world_mw: float) -> float:
    """Available information on PV, IN_t ∈ [0, 1].

    Logistic fit of Germany's normalised news articles against cumulative
    *world* installed capacity.  The x-axis is in kWp, hence the MW → kWp
    conversion.  Output is clipped to [0, 1].
    """
    cd_kw = cumulative_world_mw * 1000.0
    raw = INFO_ALPHA + INFO_L / (1.0 + math.exp(INFO_K * cd_kw + INFO_X0))
    return max(0.0, min(1.0, raw))


# ---------------------------------------------------------------------------
# Cash-flow / NPV / IRR (Equations 3–10)
# ---------------------------------------------------------------------------


def annual_generation_kwh(
    system_size_kw: float,
    irradiation: float,
    performance_ratio: float,
    production_factor: float,
) -> float:
    """Solar electricity generation EG_i (Equation 10), in kWh/year."""
    return system_size_kw * irradiation * performance_ratio * production_factor


def investment_cost(
    system_size_kw: float,
    system_price_per_w: float,
    scale: float,
) -> float:
    """Investment cost I (Equation 6), in EUR.

    S [kWp] × P [EUR/W] × 1000 [W/kWp] × SE.
    """
    return system_price_per_w * system_size_kw * 1000.0 * scale


def annual_cashflow(
    system_size_kw: float,
    system_price_per_w: float,
    scale: float,
    electricity_price: float,
    fit_tariff: float,
    self_consumption_rate: float,
    irradiation: float,
    performance_ratio: float,
    production_factor: float,
    maintenance_ratio: float,
) -> float:
    """Annual net cash flow AC − O&M + FITR (Equations 8, 9), in EUR/year."""
    inv = investment_cost(system_size_kw, system_price_per_w, scale)
    eg = annual_generation_kwh(
        system_size_kw, irradiation, performance_ratio, production_factor
    )
    revenue = eg * (
        self_consumption_rate * electricity_price
        + (1.0 - self_consumption_rate) * fit_tariff
    )
    return revenue - maintenance_ratio * inv


def npv(
    system_size_kw: float,
    system_price_per_w: float,
    electricity_price: float,
    fit_tariff: float,
    self_consumption_rate: float,
    discount_rate: float,
    irradiation: float = AVERAGE_IRRADIATION,
    performance_ratio: float = PERFORMANCE_RATIO,
    production_factor: float = 0.9,
    maintenance_ratio: float = MAINTENANCE_RATIO,
    lifespan_years: int = LIFESPAN_YEARS,
) -> float:
    """Net present value of a PV system over its FiT contract (Equations 3, 4).

    NPV = -I + Σ_{y=0}^{20} CF / (1 + r)^y,  with annual discount rate r.
    """
    scale = scale_effect(system_size_kw)
    inv = investment_cost(system_size_kw, system_price_per_w, scale)
    cf = annual_cashflow(
        system_size_kw,
        system_price_per_w,
        scale,
        electricity_price,
        fit_tariff,
        self_consumption_rate,
        irradiation,
        performance_ratio,
        production_factor,
        maintenance_ratio,
    )
    dr = max(discount_rate, -0.99)  # keep (1+r) positive
    npv = -inv
    for y in range(lifespan_years + 1):  # y = 0 .. 20 inclusive
        npv += cf / ((1.0 + dr) ** y)
    return npv


def compute_irr(
    system_price_per_w: float,
    electricity_price: float,
    fit_tariff: float,
    system_size_kw: float = 4.0,
    self_consumption_rate: float = 0.30,
    irradiation: float = AVERAGE_IRRADIATION,
    performance_ratio: float = PERFORMANCE_RATIO,
    production_factor: float = 0.9,
    maintenance_ratio: float = MAINTENANCE_RATIO,
    lifespan_years: int = LIFESPAN_YEARS,
) -> float:
    """Internal rate of return (IRR) for an average German household.

    The discount rate r that makes NPV(r) = 0, found by bisection.  Returns a
    fraction (e.g. 0.12 = 12%), clipped to [0, 10].  Negative IRRs (the
    investment never recovers) return 0.0.
    """
    def f(r: float) -> float:
        return npv(
            system_size_kw=system_size_kw,
            system_price_per_w=system_price_per_w,
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            self_consumption_rate=self_consumption_rate,
            discount_rate=r,
            irradiation=irradiation,
            performance_ratio=performance_ratio,
            production_factor=production_factor,
            maintenance_ratio=maintenance_ratio,
            lifespan_years=lifespan_years,
        )

    lo, hi = 0.0, 10.0
    f_lo, f_hi = f(lo), f(hi)
    if f_lo < 0.0:
        return 0.0          # NPV negative even at a 0% discount rate → IRR < 0
    if f_hi > 0.0:
        return hi           # still profitable at a 1000% rate — cap

    for _ in range(100):
        mid = (lo + hi) / 2.0
        if f(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# Two-stage decision
# ---------------------------------------------------------------------------


def ideation_score(
    peer_effect: float,
    information: float,
    environmental_awareness: float,
    irr: float,
) -> float:
    """Weighted ideation sum (Equation 2), IRR clipped to [0, 1]."""
    return (
        K_PEERS * peer_effect
        + K_INFO * information
        + K_AWARENESS * environmental_awareness
        + K_ATTRACTIVE * max(0.0, min(1.0, irr))
    )


@dataclass
class AdoptionEvaluation:
    """Outcome of the two-stage adoption decision for one agent in one month."""

    will_adopt: bool
    developed_idea: bool
    early_adopter: bool
    module_choice: Optional[str]  # 'domestic' | 'foreign' | None
    ideation: float
    npv_domestic: float
    npv_foreign: float


def evaluate_adoption(
    *,
    is_residential: bool,
    environmental_awareness: float,
    peer_effect: float,
    information: float,
    irr: float,
    system_size_kw: float,
    self_consumption_rate: float,
    electricity_price: float,
    fit_tariff: float,
    module_price_domestic: float,
    module_price_foreign: float,
    bos_cost: float,
    category_discount_rate: float,
    personal_discount_rate: float,
    production_factor: float = 0.9,
    irradiation: float = AVERAGE_IRRADIATION,
) -> AdoptionEvaluation:
    """Run both stages of the paper's adoption decision.

    Returns a structured outcome; `will_adopt` is True only when the agent
    develops the idea AND either is an early adopter or has a non-negative NPV.
    """
    score = ideation_score(peer_effect, information, environmental_awareness, irr)
    developed = score > IDEATION_THRESHOLD

    if not developed:
        return AdoptionEvaluation(
            will_adopt=False,
            developed_idea=False,
            early_adopter=False,
            module_choice=None,
            ideation=score,
            npv_domestic=0.0,
            npv_foreign=0.0,
        )

    # Early adopter: residential AND awareness above threshold → install now.
    if environmental_awareness > ENV_THRESHOLD and is_residential:
        return AdoptionEvaluation(
            will_adopt=True,
            developed_idea=True,
            early_adopter=True,
            module_choice="domestic",
            ideation=score,
            npv_domestic=0.0,
            npv_foreign=0.0,
        )

    # Economic evaluation: pick the largest non-negative NPV (tie → domestic).
    dr_dom = category_discount_rate + personal_discount_rate
    dr_for = dr_dom + FOREIGN_DISCOUNT_PREMIUM

    npv_d = npv(
        system_size_kw=system_size_kw,
        system_price_per_w=module_price_domestic + bos_cost,
        electricity_price=electricity_price,
        fit_tariff=fit_tariff,
        self_consumption_rate=self_consumption_rate,
        discount_rate=dr_dom,
        production_factor=production_factor,
        irradiation=irradiation,
    )
    npv_f = npv(
        system_size_kw=system_size_kw,
        system_price_per_w=module_price_foreign + bos_cost,
        electricity_price=electricity_price,
        fit_tariff=fit_tariff,
        self_consumption_rate=self_consumption_rate,
        discount_rate=dr_for,
        production_factor=production_factor,
        irradiation=irradiation,
    )

    if npv_d >= 0.0 and npv_d >= npv_f:
        return AdoptionEvaluation(
            will_adopt=True, developed_idea=True, early_adopter=False,
            module_choice="domestic", ideation=score,
            npv_domestic=npv_d, npv_foreign=npv_f,
        )
    if npv_f >= 0.0:
        return AdoptionEvaluation(
            will_adopt=True, developed_idea=True, early_adopter=False,
            module_choice="foreign", ideation=score,
            npv_domestic=npv_d, npv_foreign=npv_f,
        )
    return AdoptionEvaluation(
        will_adopt=False, developed_idea=True, early_adopter=False,
        module_choice=None, ideation=score,
        npv_domestic=npv_d, npv_foreign=npv_f,
    )

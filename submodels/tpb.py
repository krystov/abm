"""
TPB (Theory of Planned Behaviour) sub-model for adopter decision-making.

Implements the adoption intention formula (§3.1 of model_specification.md):
  I = w_att * A + w_sn * SN + w_pbc * PBC

along with the NPV-based economic attitude calculation (§3.1.2).
"""

import math


def compute_npv(
    system_size_kw: float,
    module_price_per_w: float,
    bos_cost_per_w: float,
    electricity_price: float,
    fit_tariff: float,
    self_consumption_rate: float,
    discount_rate: float,
    irradiation_kwh: float = 938.0,
    performance_ratio: float = 0.85,
    maintenance_ratio: float = 0.015,
    lifespan_months: int = 240,
) -> float:
    """Compute NPV for a potential PV system over its lifespan.

    Eq. from §3.1.2:
      NPV = Σ CF_t / (1+r)^t - I₀
    """
    total_cost_per_w = module_price_per_w + bos_cost_per_w
    investment = total_cost_per_w * system_size_kw * 1000  # €

    annual_gen_kwh = system_size_kw * irradiation_kwh * performance_ratio
    dr = max(discount_rate, 0.001)
    monthly_rate = (1 + dr) ** (1 / 12) - 1

    npv = -investment
    for m in range(1, lifespan_months + 1):
        month_gen = annual_gen_kwh / 12
        self_consumed = month_gen * self_consumption_rate
        exported = month_gen * (1 - self_consumption_rate)
        cashflow = (
            self_consumed * electricity_price
            + exported * fit_tariff
            - investment * maintenance_ratio / 12
        )
        npv += cashflow / ((1 + monthly_rate) ** m)

    return npv


def compute_tpb_intention(
    environmental_awareness: float,
    npv: float,
    neighbour_adoption_ratio: float,
    market_maturity: float,
    w_att: float = 0.55,
    w_sn: float = 0.30,
    w_pbc: float = 0.15,
    w_env: float = 0.4,
    w_eco: float = 0.6,
    env_threshold: float = 0.92,
    gamma: float = 5.0,
) -> float:
    """Compute adoption intention I via TPB.

    §3.1:
      I = w_att * A + w_sn * SN + w_pbc * PBC

    Attitude A combines environmental awareness and economic utility.
    High environmental awareness provides a graduated boost rather than a
    binary shortcut — agents need both environmental concern AND viable
    economics to adopt.
    """
    x = max(-700, min(700, -gamma * npv / 10_000))
    eco_norm = 1.0 / (1.0 + math.exp(x))
    eco = max(0.0, min(1.0, eco_norm))

    if environmental_awareness > env_threshold:
        # Graduated boost: scales from base attitude at threshold to 1.0 at env=1.0
        excess = (environmental_awareness - env_threshold) / (1.0 - env_threshold)
        base_attitude = w_env * env_threshold + w_eco * eco
        attitude = base_attitude + excess * (1.0 - base_attitude)
    else:
        attitude = w_env * environmental_awareness + w_eco * eco

    sn = neighbour_adoption_ratio
    pbc = market_maturity
    intention = w_att * attitude + w_sn * sn + w_pbc * pbc
    return max(0.0, min(1.0, intention))

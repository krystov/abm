"""
Labour market sub-model for installer workforce dynamics.

§3.3.1 — Workforce adjustment:
  ΔEmployees = α · (backlog_months - τ_target)

§3.3.2 — BOS cost quoting:
  BOS_t = BOS_base · (1 + β · backlog / employees)
"""


def adjust_workforce(
    employees: int,
    order_backlog: float,
    monthly_capacity: float,
    min_employees: int = 1_000,
    growth_rate: float = 1.05,
    shrink_rate: float = 0.95,
    backlog_hire_threshold: float = 6.0,
    backlog_fire_threshold: float = 1.0,
) -> int:
    """Adjust installer workforce based on order backlog pressure.

    If backlog requires > threshold months to clear → hire.
    If backlog < lower threshold months → fire.
    """
    months_to_clear = order_backlog / max(monthly_capacity, 0.001)

    if months_to_clear > backlog_hire_threshold:
        employees = int(employees * growth_rate)
    elif months_to_clear < backlog_fire_threshold:
        employees = int(employees * shrink_rate)

    return max(min_employees, employees)


def compute_bos_cost(
    base_bos: float,
    order_backlog: float,
    employees: int,
    beta: float = 0.3,
) -> float:
    """Dynamic BOS cost reflecting labour supply/demand tension."""
    if employees < 1:
        employees = 1
    utilisation = order_backlog / employees
    return base_bos * (1.0 + beta * utilisation)

"""
Analysis and visualisation for the Germany Solar PV Policy Mix ABM.

Provides summary statistics and matplotlib plots from the simulation history.
"""

from typing import Dict, List


def compute_metrics(history: List[dict]) -> Dict:
    """Extract key aggregate metrics from simulation history."""
    if not history:
        return {}

    final = history[-1]
    initial = history[0]

    mfg_decisions_dom = [
        r["domestic_decision"].action
        for r in history
        if r.get("domestic_decision")
    ]
    mfg_decisions_for = [
        r["foreign_decision"].action
        for r in history
        if r.get("foreign_decision")
    ]

    return {
        "duration_months": len(history),
        "duration_years": len(history) / 12,
        "final_installed_mw": final["total_installed_mw"],
        "final_adopted": final["n_adopted"],
        "final_adopted": final["n_adopted"],
        "initial_adopted": initial.get("n_adopted", 0),
        "domestic_cost_initial": round(initial["domestic_cost"], 4),
        "domestic_cost_final": round(final["domestic_cost"], 4),
        "domestic_cost_reduction_pct": round(
            (1 - final["domestic_cost"] / max(initial["domestic_cost"], 0.0001)) * 100, 1
        ),
        "foreign_cost_initial": round(initial["foreign_cost"], 4),
        "foreign_cost_final": round(final["foreign_cost"], 4),
        "foreign_cost_reduction_pct": round(
            (1 - final["foreign_cost"] / max(initial["foreign_cost"], 0.0001)) * 100, 1
        ),
        "domestic_efficiency_final": round(final.get("domestic_efficiency", 0), 4),
        "foreign_efficiency_final": round(final.get("foreign_efficiency", 0), 4),
        "avg_fit_tariff": round(
            sum(r["fit_tariff"] for r in history) / len(history), 4
        ),
        "domestic_decisions": {
            "expand": mfg_decisions_dom.count("expand"),
            "maintain": mfg_decisions_dom.count("maintain"),
            "reduce": mfg_decisions_dom.count("reduce"),
        },
        "foreign_decisions": {
            "expand": mfg_decisions_for.count("expand"),
            "maintain": mfg_decisions_for.count("maintain"),
            "reduce": mfg_decisions_for.count("reduce"),
        },
        "annual_adoptions": _annual_snapshots(history),
        "annual_additions": _annual_additions(history),
    }


def _annual_snapshots(history: List[dict]) -> Dict[int, dict]:
    """Extract December (tick % 12 == 11) snapshots keyed by year."""
    snapshots = {}
    for r in history:
        tick = r["tick"]
        if tick % 12 == 11 or tick == len(history) - 1:
            year = 1991 + tick // 12
            snapshots[year] = {
                "n_adopted": r["n_adopted"],
                "cumulative_mw": r["total_installed_mw"],
                "fit": r.get("fit_tariff", 0),
                "domestic_cost": r.get("domestic_cost", 0),
            }
    return snapshots


def _annual_additions(history: List[dict]) -> Dict[int, float]:
    """Compute MW added per year."""
    annual = {}
    prev_mw = 0.0
    current_year = 1991
    year_mw_start = 0.0
    for r in history:
        year = 1991 + r["tick"] // 12
        if year != current_year:
            annual[current_year] = round(r["total_installed_mw"] - year_mw_start, 2)
            current_year = year
            year_mw_start = r["total_installed_mw"]
    # final partial year
    if history:
        annual[current_year] = round(history[-1]["total_installed_mw"] - year_mw_start, 2)
    return annual


def print_summary(metrics: Dict) -> None:
    """Print a human-readable results summary with paper validation."""
    print("\n" + "=" * 62)
    print("  Simulation Results Summary")
    print("=" * 62)
    print(f"  Duration              : {metrics['duration_months']} months "
          f"({metrics['duration_years']:.1f} years)")
    print(f"  Final installed       : {metrics['final_installed_mw']:,.1f} MW")
    print(f"  Final adopted         : {metrics['final_adopted']} "
          f"(from {metrics['initial_adopted']} initial)")
    print(f"  Avg FiT               : {metrics['avg_fit_tariff']:.4f} EUR/kWh")
    print(f"  Domestic module cost  : {metrics['domestic_cost_initial']:.4f} → "
          f"{metrics['domestic_cost_final']:.4f} EUR/W "
          f"(-{metrics['domestic_cost_reduction_pct']:.1f}%)")
    print(f"  Foreign module cost   : {metrics['foreign_cost_initial']:.4f} → "
          f"{metrics['foreign_cost_final']:.4f} EUR/W "
          f"(-{metrics['foreign_cost_reduction_pct']:.1f}%)")
    print(f"  Domestic efficiency   : {metrics['domestic_efficiency_final']:.4f}")
    print(f"  Foreign efficiency    : {metrics['foreign_efficiency_final']:.4f}")
    print(f"  Domestic decisions    : expand={metrics['domestic_decisions']['expand']}, "
          f"maintain={metrics['domestic_decisions']['maintain']}, "
          f"reduce={metrics['domestic_decisions']['reduce']}")
    print(f"  Foreign decisions     : expand={metrics['foreign_decisions']['expand']}, "
          f"maintain={metrics['foreign_decisions']['maintain']}, "
          f"reduce={metrics['foreign_decisions']['reduce']}")

    # Validation checkpoints
    if metrics.get("annual_adoptions"):
        print("-" * 62)
        print("  Adoption Checkpoints (cumulative):")
        for year_check in [2000, 2004, 2008, 2012, 2016]:
            yr_data = metrics["annual_adoptions"].get(year_check)
            if yr_data:
                print(f"    {year_check}: {yr_data['n_adopted']} adopted, "
                      f"{yr_data['cumulative_mw']:.1f} MW, "
                      f"FiT={yr_data.get('fit', 0):.3f}")
        print("-" * 62)
        print("  Annual Additions (MW/year):")
        for year_check in [2000, 2004, 2008, 2012]:
            yr_data = metrics["annual_additions"].get(year_check)
            if yr_data:
                print(f"    {year_check}: +{yr_data:.2f} MW")

    print("=" * 62)


def plot_results(history: List[dict], save_path: str = "") -> None:
    """Generate plots of key simulation trajectories.

    Requires matplotlib.  Saves to `save_path` if provided, otherwise displays.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[metrics] matplotlib not installed — skipping plots")
        return

    ticks = [r["tick"] for r in history]
    years = [1991 + t / 12 for t in ticks]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Germany Solar PV Policy Mix ABM — Results", fontsize=13)

    # Top-left: Installed capacity
    ax = axes[0][0]
    ax.plot(years, [r["total_installed_mw"] for r in history], "b-", linewidth=1.5)
    ax.set_ylabel("Installed Capacity [MW]")
    ax.set_title("Cumulative PV Installations")
    ax.grid(True, alpha=0.3)

    # Top-right: Module cost
    ax = axes[0][1]
    ax.plot(years, [r["domestic_cost"] for r in history], label="Domestic MC", linewidth=1.5)
    ax.plot(years, [r["foreign_cost"] for r in history], label="Foreign MC", linewidth=1.5)
    ax.set_ylabel("Production Cost [EUR/W]")
    ax.set_title("Module Production Cost (Experience Curve)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Bottom-left: Adopters
    ax = axes[1][0]
    ax.plot(years, [r["n_adopted"] for r in history], "g-", linewidth=1.5)
    ax.set_ylabel("Adopters")
    ax.set_title("Cumulative Adopters")
    ax.grid(True, alpha=0.3)

    # Bottom-right: FiT and electricity price
    ax = axes[1][1]
    ax.plot(years, [r["fit_tariff"] for r in history], label="FiT", linewidth=1.5)
    ax.plot(years, [r["electricity_price"] for r in history], label="Elec. price", linewidth=1.5)
    ax.set_ylabel("EUR/kWh")
    ax.set_title("Policy & Price Signals")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"[metrics] Plot saved to {save_path}")
    else:
        plt.show()

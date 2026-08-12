"""
Macro environment for the Germany Solar PV Policy Mix ABM.

Manages the time-series of exogenous variables (electricity price, FiT,
media coverage, technology-push level) that drive agent behaviour each tick.

Supports both synthetic (plausible) data and loading from real historical CSVs.
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class MacroEnvironment:
    """Container for macroeconomic and policy time-series.

    Data is indexed by tick (0..n_ticks-1).  Use `from_synthetic()` to
    generate plausible German PV data or load real CSV data externally
    via `data_loader` and assign directly.
    """

    electricity_price: List[float] = field(default_factory=list)
    fit_tariff: List[float] = field(default_factory=list)
    media_coverage: List[float] = field(default_factory=list)
    tech_push_level: List[int] = field(default_factory=list)
    global_cumulative_mw: List[float] = field(default_factory=list)

    n_ticks: int = 0

    @classmethod
    def from_synthetic(cls, n_ticks: int = 312, seed: int = 42) -> "MacroEnvironment":
        """Generate plausible German PV policy data for 1991–2016."""
        rng = random.Random(seed)
        ticks = list(range(n_ticks))

        # Electricity price: rises from ~0.14 to ~0.29 €/kWh
        electricity_price = [
            0.14 + (0.15 * t / n_ticks) + rng.gauss(0, 0.002) for t in ticks
        ]

        # FiT: introduced ~2000 (tick 108), peaks ~2008, then declines
        fit_tariff = []
        for t in ticks:
            year = 1991 + t / 12
            if year < 2000:
                val = 0.0
            elif year < 2004:
                val = 0.35 + rng.gauss(0, 0.005)
            elif year < 2008:
                val = 0.50 + rng.gauss(0, 0.005)
            elif year < 2012:
                val = 0.40 + rng.gauss(0, 0.005)
            else:
                val = max(0.08, 0.30 - 0.22 * (year - 2012) / 4 + rng.gauss(0, 0.005))
            fit_tariff.append(max(0.0, val))

        # Media coverage: normalised index [0, 1], rising over time
        media = [
            max(0.0, min(1.0, 0.3 + 0.4 * (t / n_ticks) + rng.gauss(0, 0.05)))
            for t in ticks
        ]

        # Tech-push level: 1–5, government R&D intensity
        tech_push = [
            min(5, max(1, int(2.5 + 1.5 * t / n_ticks + rng.randint(-1, 1))))
            for t in ticks
        ]

        # Global cumulative PV capacity [MW] — approximate historical
        # Driven by exponential growth with annual growth rate rising over time
        global_cum = []
        g0 = 500.0   # ~0.5 GW in 1991
        for t in ticks:
            year = 1991 + t / 12
            # Annual growth rate: starts ~15%, rises to ~40% by 2010s
            gr = 0.15 + 0.25 * max(0, min(1, (year - 1991) / 20))
            months = t
            global_cum.append(g0 * ((1 + gr) ** (months / 12)))
        global_cumulative_mw = global_cum

        return cls(
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            media_coverage=media,
            tech_push_level=tech_push,
            global_cumulative_mw=global_cumulative_mw,
            n_ticks=n_ticks,
        )

    @classmethod
    def from_historical(cls, n_ticks: int = 312, seed: int = 42) -> "MacroEnvironment":
        """Load real historical data from data_loader and interpolate to monthly."""
        from data.data_loader import annual_to_monthly, load_historical_annual

        rng = random.Random(seed)
        annual = load_historical_annual()

        electricity_price = annual_to_monthly(annual, "elec_h", n_years=26)[:n_ticks]
        fit_tariff = annual_to_monthly(annual, "fit_h", n_years=26)[:n_ticks]
        media = annual_to_monthly(annual, "media", n_years=26)[:n_ticks]

        # Add small noise to avoid exact duplicates
        electricity_price = [v + rng.gauss(0, 0.001) for v in electricity_price]
        fit_tariff = [max(0.0, v + rng.gauss(0, 0.001)) for v in fit_tariff]
        media = [max(0.0, min(1.0, v + rng.gauss(0, 0.01))) for v in media]

        # Tech-push level from R&D spending (normalised 1-5)
        rd_annual = annual_to_monthly(annual, "rd_dom", n_years=26)[:n_ticks]
        rd_max = max(rd_annual) if rd_annual else 200
        tech_push = [min(5, max(1, int(1 + 4 * v / rd_max))) for v in rd_annual]

        # Global cumulative MW (same exponential model as synthetic)
        g0 = 500.0
        global_cum = []
        for t in range(n_ticks):
            year = 1991 + t / 12
            gr = 0.15 + 0.25 * max(0, min(1, (year - 1991) / 20))
            global_cum.append(g0 * ((1 + gr) ** (t / 12)))

        return cls(
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            media_coverage=media,
            tech_push_level=tech_push,
            global_cumulative_mw=global_cum,
            n_ticks=n_ticks,
        )

    def get(self, tick: int) -> dict:
        """Return macro variables for the given tick."""
        if tick >= self.n_ticks:
            raise IndexError(f"tick {tick} out of range (n_ticks={self.n_ticks})")
        return {
            "electricity_price": self.electricity_price[tick],
            "fit_tariff": self.fit_tariff[tick],
            "media_coverage": self.media_coverage[tick],
            "tech_push_level": self.tech_push_level[tick],
            "global_cumulative_mw": self.global_cumulative_mw[tick],
        }

    def __len__(self) -> int:
        return self.n_ticks

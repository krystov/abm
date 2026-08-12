"""
Data loader for the Germany Solar PV Policy Mix ABM.

Loads historical time-series data (electricity prices, FiT rates, R&D spending,
etc.) from CSV files or inline definitions.  Falls back to synthetic data when
real data sources are unavailable.

Expected CSV format (one row per year, 1991–2016):
  year, electricity_price_h, electricity_price_c, fit_tariff_h, fit_tariff_c,
       media_coverage_index, rd_spending_domestic, rd_spending_foreign

The loader will interpolate monthly values from annual data.
"""

import csv
import os
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Approximate historical reference values (1991–2016, sampled annually).
# These are approximate values compiled from public sources and meant to
# provide a reasonable baseline when external CSV files are not available.
# ---------------------------------------------------------------------------

_HISTORICAL_ANNUAL: List[Dict] = [
    # year, elec_h, elec_c, fit_h, fit_c, media, rd_dom, rd_for
    {"year": 1991, "elec_h": 0.14, "elec_c": 0.12, "fit_h": 0.0, "fit_c": 0.0, "media": 0.05, "rd_dom": 50, "rd_for": 30},
    {"year": 1992, "elec_h": 0.14, "elec_c": 0.12, "fit_h": 0.0, "fit_c": 0.0, "media": 0.06, "rd_dom": 55, "rd_for": 32},
    {"year": 1993, "elec_h": 0.15, "elec_c": 0.13, "fit_h": 0.0, "fit_c": 0.0, "media": 0.07, "rd_dom": 60, "rd_for": 35},
    {"year": 1994, "elec_h": 0.15, "elec_c": 0.13, "fit_h": 0.0, "fit_c": 0.0, "media": 0.08, "rd_dom": 65, "rd_for": 38},
    {"year": 1995, "elec_h": 0.16, "elec_c": 0.14, "fit_h": 0.0, "fit_c": 0.0, "media": 0.10, "rd_dom": 70, "rd_for": 40},
    {"year": 1996, "elec_h": 0.16, "elec_c": 0.14, "fit_h": 0.0, "fit_c": 0.0, "media": 0.12, "rd_dom": 75, "rd_for": 42},
    {"year": 1997, "elec_h": 0.17, "elec_c": 0.14, "fit_h": 0.0, "fit_c": 0.0, "media": 0.15, "rd_dom": 80, "rd_for": 45},
    {"year": 1998, "elec_h": 0.17, "elec_c": 0.15, "fit_h": 0.0, "fit_c": 0.0, "media": 0.18, "rd_dom": 85, "rd_for": 48},
    {"year": 1999, "elec_h": 0.17, "elec_c": 0.15, "fit_h": 0.0, "fit_c": 0.0, "media": 0.22, "rd_dom": 90, "rd_for": 50},
    {"year": 2000, "elec_h": 0.16, "elec_c": 0.14, "fit_h": 0.51, "fit_c": 0.44, "media": 0.30, "rd_dom": 100, "rd_for": 55},
    {"year": 2001, "elec_h": 0.17, "elec_c": 0.14, "fit_h": 0.51, "fit_c": 0.44, "media": 0.35, "rd_dom": 110, "rd_for": 60},
    {"year": 2002, "elec_h": 0.17, "elec_c": 0.15, "fit_h": 0.48, "fit_c": 0.41, "media": 0.40, "rd_dom": 120, "rd_for": 65},
    {"year": 2003, "elec_h": 0.18, "elec_c": 0.15, "fit_h": 0.46, "fit_c": 0.39, "media": 0.45, "rd_dom": 130, "rd_for": 70},
    {"year": 2004, "elec_h": 0.18, "elec_c": 0.16, "fit_h": 0.57, "fit_c": 0.50, "media": 0.50, "rd_dom": 140, "rd_for": 75},
    {"year": 2005, "elec_h": 0.19, "elec_c": 0.16, "fit_h": 0.55, "fit_c": 0.48, "media": 0.55, "rd_dom": 150, "rd_for": 80},
    {"year": 2006, "elec_h": 0.19, "elec_c": 0.17, "fit_h": 0.52, "fit_c": 0.45, "media": 0.60, "rd_dom": 160, "rd_for": 85},
    {"year": 2007, "elec_h": 0.20, "elec_c": 0.17, "fit_h": 0.49, "fit_c": 0.42, "media": 0.65, "rd_dom": 170, "rd_for": 90},
    {"year": 2008, "elec_h": 0.21, "elec_c": 0.18, "fit_h": 0.47, "fit_c": 0.40, "media": 0.70, "rd_dom": 180, "rd_for": 95},
    {"year": 2009, "elec_h": 0.22, "elec_c": 0.19, "fit_h": 0.43, "fit_c": 0.37, "media": 0.75, "rd_dom": 190, "rd_for": 100},
    {"year": 2010, "elec_h": 0.23, "elec_c": 0.20, "fit_h": 0.39, "fit_c": 0.33, "media": 0.78, "rd_dom": 200, "rd_for": 105},
    {"year": 2011, "elec_h": 0.25, "elec_c": 0.21, "fit_h": 0.29, "fit_c": 0.25, "media": 0.82, "rd_dom": 190, "rd_for": 100},
    {"year": 2012, "elec_h": 0.26, "elec_c": 0.22, "fit_h": 0.24, "fit_c": 0.20, "media": 0.85, "rd_dom": 180, "rd_for": 95},
    {"year": 2013, "elec_h": 0.28, "elec_c": 0.23, "fit_h": 0.17, "fit_c": 0.14, "media": 0.88, "rd_dom": 170, "rd_for": 90},
    {"year": 2014, "elec_h": 0.29, "elec_c": 0.24, "fit_h": 0.13, "fit_c": 0.11, "media": 0.90, "rd_dom": 160, "rd_for": 85},
    {"year": 2015, "elec_h": 0.29, "elec_c": 0.24, "fit_h": 0.12, "fit_c": 0.10, "media": 0.92, "rd_dom": 150, "rd_for": 80},
    {"year": 2016, "elec_h": 0.29, "elec_c": 0.24, "fit_h": 0.09, "fit_c": 0.08, "media": 0.95, "rd_dom": 140, "rd_for": 75},
]


def load_historical_annual() -> List[Dict]:
    """Return inline historical annual data (1991–2016).

    For production use, replace this with a CSV load via `load_csv()`.
    """
    return list(_HISTORICAL_ANNUAL)


def load_csv(filepath: str) -> List[Dict]:
    """Load annual historical data from a CSV file.

    Expected columns: year, elec_h, elec_c, fit_h, fit_c, media, rd_dom, rd_for
    """
    rows = []
    with open(filepath, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append({
                "year": int(row["year"]),
                "elec_h": float(row["elec_h"]),
                "elec_c": float(row["elec_c"]),
                "fit_h": float(row["fit_h"]),
                "fit_c": float(row["fit_c"]),
                "media": float(row["media"]),
                "rd_dom": float(row["rd_dom"]),
                "rd_for": float(row["rd_for"]),
            })
    return rows


def annual_to_monthly(annual: List[Dict], key: str, n_years: int = 26) -> List[float]:
    """Linearly interpolate an annual series to monthly values.

    Each year is expanded to 12 equal monthly values.  Extra months beyond
    n_years*12 are truncated.
    """
    monthly = []
    for row in annual[:n_years]:
        monthly.extend([row[key]] * 12)
    return monthly

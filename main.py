"""
Germany Solar PV Policy Mix ABM — entry point.

Runs the hybrid async model: manufacturers use LLM-augmented decision-making
(via asyncio.gather), adopters use both LLM (sampled fraction) and TPB formulas,
while installers run local labour-market formulas.
"""

import asyncio
import os
import sys
import time

from dotenv import load_dotenv

from agents.agent_framework import get_llm_model
from analysis.metrics import compute_metrics, plot_results, print_summary
from model.solar_model import SolarModel

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load environment variables (e.g. DEEPSEEK_API_KEY) from a local .env file.
load_dotenv()


async def main():
    print("=" * 62)
    print("  Germany Solar PV Policy Mix ABM  (Hybrid LLM + Experience Curve)")
    print("=" * 62)

    # Full run: 312 ticks (26 years, 1991-2016)
    # Set use_llm=False for fast formula-only mode; use_llm=True needs a key
    # (DEEPSEEK_API_KEY or OPENAI_API_KEY).
    has_key = bool(os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    use_llm = "--llm" in sys.argv and has_key
    use_real_data = "--real-data" in sys.argv
    model = SolarModel(
        n_ticks=312,
        n_adopters=500,
        llm_model=get_llm_model(),
        seed=42,
        llm_adopter_fraction=0.05,  # 5% of undecided adopters use LLM each tick
        use_llm=use_llm,
        use_real_data=use_real_data,
    )

    print(f"  Adopters          : {model.n_adopters}  ({model.llm_adopter_fraction:.0%} LLM-augmented)")
    print(f"  Manufacturers     : {len(model.manufacturers)}  (LLM-augmented)")
    print(f"  Installers        : {len(model.installers)}  (formula-based)")
    print(f"  Ticks             : {model.n_ticks}  months  (1991–2016)")
    print(f"  Data source       : {'historical' if use_real_data else 'synthetic'}")
    print(f"  LLM mode          : {'ON  (' + model.llm_model + ')' if use_llm else 'OFF (formula-only)'}")
    if os.environ.get("DEEPSEEK_API_KEY"):
        print(f"  LLM provider      : DeepSeek (base_url={os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')})")
    else:
        print(f"  OPENAI_API_KEY    : {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")
    print("-" * 62)

    t0 = time.perf_counter()
    history = await model.run(verbose=True)
    elapsed = time.perf_counter() - t0

    print("-" * 62)
    print(f"  Simulation complete: {len(history)} ticks in {elapsed:.1f}s")

    metrics = compute_metrics(history)
    print_summary(metrics)

    # Save plots
    try:
        plot_results(history, save_path="results.png")
    except Exception:
        pass

    return history


if __name__ == "__main__":
    asyncio.run(main())

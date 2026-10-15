"""
Decision-mode comparison: formula vs single-LLM vs board-of-directors.

Every mode runs the same simulation (same seed, population, macro path, tick
horizon); the only thing that differs is *how* manufacturers decide:

    formula : two-factor experience curve, no LLM at all
    single  : one LLM call per manufacturer per month
    board   : 5 AI directors vote, majority rule (agents/board.py)

Usage
-----
    python experiments/compare_decision_modes.py --modes formula --ticks 120
    python experiments/compare_decision_modes.py --modes single --ticks 120
    python experiments/compare_decision_modes.py --modes board  --ticks 120
    python experiments/compare_decision_modes.py --combine

Each run writes ``<out-dir>/<mode>.json``; ``--combine`` turns the JSON files
into a comparison table (Markdown) and a chart (PNG).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Windows consoles default to GBK; the report contains '€' and Chinese labels.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from agents.agent_framework import get_llm_model  # noqa: E402
from analysis.metrics import compute_metrics  # noqa: E402
from model.solar_model import SolarModel  # noqa: E402

# The LLM modes need DEEPSEEK_API_KEY / OPENAI_API_KEY; load .env explicitly
# (unlike main.py this script may be launched from anywhere).
try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass

MODES = ("formula", "single", "board")


# ---------------------------------------------------------------------------
# Running one mode
# ---------------------------------------------------------------------------


def build_model(mode: str, args) -> SolarModel:
    common = dict(
        n_ticks=args.ticks,
        n_adopters=args.adopters,
        seed=args.seed,
        llm_model=get_llm_model(),
        llm_adopter_fraction=args.adopter_llm,
        use_real_data=False,
    )
    if mode == "formula":
        return SolarModel(**common, use_llm=False, use_board=False)
    if mode == "single":
        return SolarModel(**common, use_llm=True, use_board=False)
    return SolarModel(
        **common,
        use_llm=True,
        use_board=True,
        board_size=args.board_size,
        board_temperature=args.board_temperature,
        board_verbose=False,
        board_log_path=str(args.out_dir / f"board_minutes{args.label}_{args.ticks}t.md"),
    )


def summarise(mode: str, model, history, seconds: float, args) -> dict:
    metrics = compute_metrics(history)
    actions, rd_focus, board_fallback = Counter(), Counter(), 0
    for record in history:
        for key in ("domestic_decision", "foreign_decision"):
            decision = record.get(key)
            if decision is None:
                continue
            actions[decision.action] += 1
            rd_focus[decision.rd_focus] += 1
        for key in ("domestic_board", "foreign_board"):
            board = record.get(key)
            if board and board.get("fallback_used"):
                board_fallback += 1

    trajectory = [
        {
            "tick": r["tick"],
            "year": 1991 + r["tick"] // 12,
            "domestic_cost": r["domestic_cost"],
            "foreign_cost": r["foreign_cost"],
            "domestic_capacity": r["domestic_capacity"],
            "domestic_efficiency": r["domestic_efficiency"],
            "n_adopted": r["n_adopted"],
            "installed_mw": r["total_installed_mw"],
        }
        for r in history
    ]

    return {
        "mode": mode,
        "config": {
            "seed": args.seed,
            "ticks": args.ticks,
            "adopters": args.adopters,
            "adopter_llm_fraction": args.adopter_llm,
            "llm_model": get_llm_model(),
            "board_size": args.board_size if mode == "board" else None,
            "board_temperature": (
                args.board_temperature if mode == "board" else None
            ),
        },
        "seconds": round(seconds, 1),
        "final": {
            "n_adopted": metrics["final_adopted"],
            "installed_mw": metrics["final_installed_mw"],
            "domestic_cost": metrics["domestic_cost_final"],
            "foreign_cost": metrics["foreign_cost_final"],
            "domestic_cost_reduction_pct": metrics["domestic_cost_reduction_pct"],
            "foreign_cost_reduction_pct": metrics["foreign_cost_reduction_pct"],
            "domestic_efficiency": metrics["domestic_efficiency_final"],
            "foreign_efficiency": metrics["foreign_efficiency_final"],
            "avg_fit": metrics["avg_fit_tariff"],
        },
        "actions": dict(actions),
        "rd_focus": dict(rd_focus),
        "manufacturer_llm_failures": {
            key: mfg.llm_failures for key, mfg in model.manufacturers.items()
        },
        "board_fallback_meetings": board_fallback,
        "board_stats": metrics.get("board_stats", {}),
        "trajectory": trajectory,
    }


async def run_mode(mode: str, args) -> dict:
    model = build_model(mode, args)
    print(f"[{mode}] start: ticks={args.ticks} seed={args.seed} "
          f"adopter_llm={args.adopter_llm}", flush=True)
    t0 = time.perf_counter()
    history = await model.run(verbose=False)
    seconds = time.perf_counter() - t0
    result = summarise(mode, model, history, seconds, args)
    print(f"[{mode}] done in {seconds:.1f}s | adopted={result['final']['n_adopted']} "
          f"| dom cost {result['final']['domestic_cost']} "
          f"| for cost {result['final']['foreign_cost']} "
          f"| rd {result['rd_focus']} "
          f"| llm_failures {result['manufacturer_llm_failures']}", flush=True)
    return result


# ---------------------------------------------------------------------------
# Combining the runs
# ---------------------------------------------------------------------------


def combine(out_dir: Path) -> None:
    runs = {}
    for mode in MODES:
        path = out_dir / f"{mode}.json"
        if path.exists():
            runs[mode] = json.loads(path.read_text(encoding="utf-8"))
    if not runs:
        raise SystemExit(f"no result files found in {out_dir}")

    lines = ["# Decision-mode comparison", ""]
    cfg = next(iter(runs.values()))["config"]
    lines.append(
        f"seed={cfg['seed']}, ticks={cfg['ticks']}, adopters={cfg['adopters']}, "
        f"adopter_llm_fraction={cfg['adopter_llm_fraction']}, "
        f"model={cfg['llm_model']}"
    )
    lines.append("")
    header = ("mode | seconds | adopted | installed MW | dom cost €/W "
              "| for cost €/W | dom eff | rd_focus votes | action votes")
    lines.append(header)
    lines.append("-" * len(header))
    for mode, run in runs.items():
        f = run["final"]
        lines.append(
            f"{mode} | {run['seconds']} | {f['n_adopted']} | {f['installed_mw']} "
            f"| {f['domestic_cost']} | {f['foreign_cost']} | {f['domestic_efficiency']} "
            f"| {run['rd_focus']} | {run['actions']}"
        )
    lines.append("")

    for mode, run in runs.items():
        stats = run.get("board_stats") or {}
        if stats:
            lines.append(
                f"- **{mode}** board: {stats['meetings']} 场会议，"
                f"一致通过 {stats['unanimous_pct']}%，"
                f"平票裁决 {stats['tie_broken_meetings']}，"
                f"未达半数 {stats['fallback_meetings']}，"
                f"平均反对 {stats['avg_dissent']} 票，"
                f"弃权 {stats['avg_abstain']} 票"
            )

    report = "\n".join(lines)
    (out_dir / "comparison.md").write_text(report, encoding="utf-8")
    print(report)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 3, figsize=(16, 4.2))
        for mode, run in runs.items():
            traj = run["trajectory"]
            years = [p["year"] for p in traj]
            axes[0].plot(years, [p["domestic_cost"] for p in traj], label=mode)
            axes[1].plot(years, [p["foreign_cost"] for p in traj], label=mode)
            axes[2].plot(years, [p["n_adopted"] for p in traj], label=mode)
        axes[0].set_title("Domestic module cost (EUR/W)")
        axes[1].set_title("Foreign module cost (EUR/W)")
        axes[2].set_title("Cumulative adopters")
        for ax in axes:
            ax.set_xlabel("year")
            ax.grid(alpha=0.3)
            ax.legend()
        fig.tight_layout()
        chart = out_dir / "decision_modes.png"
        fig.savefig(chart, dpi=130)
        print(f"\nchart -> {chart}")
    except Exception as exc:  # pragma: no cover - plotting is optional
        print(f"(chart skipped: {type(exc).__name__}: {exc})")


# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modes", default="formula",
                        help="comma-separated subset of formula,single,board")
    parser.add_argument("--ticks", type=int, default=120)
    parser.add_argument("--adopters", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--adopter-llm", type=float, default=0.0,
                        help="fraction of adopters using the LLM (0 isolates "
                             "the manufacturer decision mechanism)")
    parser.add_argument("--board-size", type=int, default=5)
    parser.add_argument("--board-temperature", type=float, default=0.6)
    parser.add_argument("--label", default="",
                        help="suffix for the minutes/output file names, e.g. _temp1.3")
    parser.add_argument("--out-dir", type=Path,
                        default=REPO_ROOT / "experiments" / "results")
    parser.add_argument("--combine", action="store_true",
                        help="only combine existing result files")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.combine:
        combine(args.out_dir)
        return

    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    if any(m in ("single", "board") for m in modes) and not (
        os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
    ):
        raise SystemExit(
            "LLM modes need DEEPSEEK_API_KEY or OPENAI_API_KEY — check .env "
            "(otherwise every call would silently fall back to the formula)"
        )

    for mode in modes:
        if mode not in MODES:
            raise SystemExit(f"unknown mode: {mode}")
        if mode == "board":
            minutes = args.out_dir / f"board_minutes{args.label}_{args.ticks}t.md"
            if minutes.exists():
                minutes.unlink()  # start a fresh transcript for this run
        result = asyncio.run(run_mode(mode, args))
        (args.out_dir / f"{mode}{args.label}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    combine(args.out_dir)


if __name__ == "__main__":
    main()

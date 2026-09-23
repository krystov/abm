"""
Manufacturer agent — PV module producer (domestic or foreign).

State variables per Tables SI 3, SI 5 of the supplementary information.
LLM-augmented capacity & R&D decisions with two-factor experience-curve fallback.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from openai import AsyncOpenAI
from agents.agent_framework import (
    ConversationMemory,
    create_llm_client,
    extract_json_object,
)
from agents.tools import build_manufacturer_tools
from schemas import ManufacturerDecision
from submodels.experience_curve import compute_production_cost, update_knowledge_stock


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Region(Enum):
    """Table SI 3: two regions for supplier agents."""
    DOMESTIC = "domestic"
    FOREIGN = "foreign"


class SupplierType(Enum):
    """Table SI 3: two supplier agent types."""
    MODULE_MANUFACTURER = "module_manufacturer"
    INSTALLER = "installer"


# ---------------------------------------------------------------------------
# Manufacturer
# ---------------------------------------------------------------------------


@dataclass
class Manufacturer:
    """PV module manufacturer — one per region (domestic & foreign).

    Table SI 3 — Supply-chain state variables:
        region, capacity, employees, stock, sales, revenue,
        labor_productivity, mark_up, min/max workforce & capacity constraints,
        rd_spending_ratio

    Table SI 5 — Two-factor experience-curve parameters:
        beta_learning_by_doing, beta_learning_by_research,
        experience_curve_intercept, knowledge_delay, knowledge_depreciation,
        knowledge_spillover_in_ratio, knowledge_spillover_delay
    """

    manufacturer_id: int
    region: Region
    capacity: float = 0.0
    module_efficiency: float = 0.0
    production_cost: float = 0.0
    price: float = 0.0
    knowledge_stock: float = 0.0
    cumulative_production: float = 0.0
    stock: float = 0.0
    sales: float = 0.0
    demand: float = 0.0
    revenue: float = 0.0
    employees: int = 0
    labor_productivity: float = 0.0
    min_employees: int = 1_000
    max_workforce_increase: float = 2.0
    max_workforce_decrease: float = 0.5
    mark_up: float = 0.0
    min_capacity: float = 50_000.0
    utilization_rate_margin: float = 1.3333
    max_capacity_increase: float = 3.0
    max_capacity_decrease: float = 0.5
    rd_spending_ratio: float = 0.0
    rd_spending: float = 0.0
    beta_learning_by_doing: float = 0.0
    beta_learning_by_research: float = 0.0
    experience_curve_intercept: float = 0.0
    knowledge_delay: int = 36
    knowledge_depreciation: float = 0.008742
    knowledge_spillover_in_ratio: float = 0.0
    knowledge_spillover_delay: int = 0
    cp_initial: float = 1.0
    ks_initial: float = 1.0
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    _llm_client: Optional[AsyncOpenAI] = field(default=None, repr=False, compare=False)

    # ------------------------------------------------------------------
    # LLM-augmented monthly decision
    # ------------------------------------------------------------------

    async def step_llm(
        self,
        electricity_price: float,
        fit_tariff: float,
        order_backlog: float,
        tech_push_level: float = 1.0,
        model_name: str = "gpt-4.1-mini",
        global_cumulative_mw: float = 500.0,
    ) -> ManufacturerDecision:
        """Query an LLM for the manufacturer's monthly decision.

        On failure the two-factor experience-curve formula is used as fallback.
        """
        prompt = self._build_llm_prompt(
            electricity_price, fit_tariff, order_backlog, tech_push_level
        )

        # Inject conversation memory for multi-turn context
        memory_ctx = self.memory.format_for_prompt()
        full_prompt = memory_ctx + "\n\n" + prompt if self.memory.history else prompt

        # Build tool registry for this decision context
        tools = build_manufacturer_tools(
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            order_backlog=order_backlog,
            tech_push_level=tech_push_level,
            capacity=self.capacity,
            production_cost=self.production_cost,
            price=self.price,
            module_efficiency=self.module_efficiency,
            knowledge_stock=self.knowledge_stock,
            cumulative_production=self.cumulative_production,
            stock=self.stock,
            sales=self.sales,
        )

        system_msg = (
            "You are a rational PV module manufacturer making monthly "
            "capacity and R&D decisions. You may call tools to query "
            "your current state before deciding. "
            "Respond with valid JSON only, following the ManufacturerDecision schema: "
            '{"action": "expand|maintain|reduce", '
            '"change_percentage": 0.0-0.5, '
            '"rd_focus": "efficiency|cost_reduction|none", '
            '"reasoning": "..."}'
        )

        try:
            if self._llm_client is None:
                self._llm_client = create_llm_client()

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": full_prompt},
            ]

            # Multi-turn tool-calling loop (max 3 rounds)
            for _ in range(3):
                response = await self._llm_client.chat.completions.create(
                    model=model_name,
                    temperature=0.3,
                    messages=messages,
                    tools=tools.get_specs() if len(tools) > 0 else None,
                    tool_choice="auto" if len(tools) > 0 else None,
                )

                msg = response.choices[0].message

                if msg.tool_calls:
                    messages.append(msg.model_dump())
                    for tc in msg.tool_calls:
                        args = json.loads(tc.function.arguments)
                        result = await tools.invoke(tc.function.name, args)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result,
                        })
                elif msg.content:
                    decision = ManufacturerDecision.model_validate(
                        extract_json_object(msg.content)
                    )
                    self.memory.record(0, decision, "LLM decision (with tools)")
                    return decision
                else:
                    break

            raise ValueError("Tool loop exceeded without valid decision")

        except Exception as exc:
            print(f"[manufacturer:{self.region.value}] step_llm error: {type(exc).__name__}: {exc}")
            fallback = self._experience_curve_fallback(
                electricity_price, fit_tariff, order_backlog, global_cumulative_mw
            )
            self.memory.record(0, fallback, "Experience-curve fallback (LLM unavailable)")
            return fallback

    def _build_llm_prompt(
        self,
        electricity_price: float,
        fit_tariff: float,
        order_backlog: float,
        tech_push_level: float,
    ) -> str:
        region_label = "Germany (domestic)" if self.region.value == "domestic" else "Foreign"
        return (
            f"You are a PV module manufacturer in {region_label}.\n\n"
            f"=== Market Context (this month) ===\n"
            f"  Retail electricity price : {electricity_price:.4f} €/kWh\n"
            f"  Feed-in tariff (FiT)     : {fit_tariff:.4f} €/kWh\n"
            f"  Installer order backlog  : {order_backlog:.2f} MW\n"
            f"  Government R&D push level: {tech_push_level:.0f} / 5\n\n"
            f"=== Your Current State ===\n"
            f"  Production capacity      : {self.capacity:.2f} MW/month\n"
            f"  Module efficiency        : {self.module_efficiency:.4f} (fraction)\n"
            f"  Production cost          : {self.production_cost:.4f} €/W\n"
            f"  Module price             : {self.price:.4f} €/W\n"
            f"  Knowledge stock (KS)     : {self.knowledge_stock:.2f}\n"
            f"  Cumulative production    : {self.cumulative_production:.2f} MW\n"
            f"  Current stock/inventory  : {self.stock:.2f} MW\n"
            f"  Sales last month         : {self.sales:.2f} MW\n"
            f"  Workforce (employees)    : {self.employees}\n\n"
            f"=== Decision Guidance ===\n"
            f"- High electricity prices + high FiT -> expand capacity.\n"
            f"- Large order backlog signals strong demand -> expand.\n"
            f"- If demand is weak and inventory piles up -> reduce.\n"
            f"- Choose rd_focus='efficiency' to improve module efficiency,\n"
            f"  'cost_reduction' to lower production cost,\n"
            f"  or 'none' if R&D budget is unavailable.\n"
            f"- change_percentage must be in [0.0, 0.5].\n\n"
            f"Output a single JSON object per the schema."
        )

    # ------------------------------------------------------------------
    # Deterministic fallback: two-factor experience curve
    # ------------------------------------------------------------------

    def _experience_curve_fallback(
        self,
        electricity_price: float,
        fit_tariff: float,
        order_backlog: float,
        global_cumulative_mw: float = 500.0,
    ) -> ManufacturerDecision:
        """Apply the paper's two-factor experience curve (Eq. 24-25) directly.

        Uses global cumulative PV capacity (exogenous) as the primary learning
        driver, plus individual knowledge stock for research-based learning.

        Capacity decisions are based on demand trend, not absolute backlog,
        since manufacturer capacities far exceed the scaled-down model demand.
        """
        self.cumulative_production += self.sales

        # Knowledge spillover from the other manufacturer
        # (handled externally via apply_spillover — this only updates own KS)
        self.knowledge_stock = update_knowledge_stock(
            ks_current=self.knowledge_stock,
            rd_spending=self.rd_spending,
            depreciation=self.knowledge_depreciation,
        )

        # Learning-by-doing driver.  NOTE: world installed capacity is used as a
        # proxy for cumulative production; the paper uses *regional* production,
        # but the foreign manufacturer's production is driven by the global
        # market (not modelled here), so a pure own-CP would stall learning.
        # See 测试记录.txt 第十三轮 for the tradeoff analysis.
        self.production_cost = compute_production_cost(
            cumulative_production=max(global_cumulative_mw, self.cumulative_production),
            knowledge_stock=self.knowledge_stock,
            cp_initial=self.cp_initial,
            ks_initial=self.ks_initial,
            intercept=self.experience_curve_intercept,
            beta_learning_by_doing=self.beta_learning_by_doing,
            beta_learning_by_research=self.beta_learning_by_research,
        )

        # Capacity decision: use demand relative to recent trend, not absolute
        backlog_ratio = order_backlog / max(self.capacity, 0.001)
        if backlog_ratio > 0.5:
            action = "expand"
            change_pct = min(0.15, backlog_ratio)
            change_pct = max(0.02, min(0.3, change_pct))
        elif backlog_ratio < 0.1:
            action = "reduce"
            change_pct = 0.05
        else:
            action = "maintain"
            change_pct = 0.0

        self._apply_capacity_change(action, change_pct)
        self.price = self.production_cost * (1.0 + self.mark_up)

        if self.rd_spending > 0 and self.region.value == "domestic":
            rd_focus = "cost_reduction"
        elif self.rd_spending > 0:
            rd_focus = "efficiency"
        else:
            rd_focus = "none"

        return ManufacturerDecision(
            action=action,
            change_percentage=round(change_pct, 4),
            rd_focus=rd_focus,
            reasoning=(
                f"Experience-curve fallback: CP={self.cumulative_production:.1f} MW, "
                f"KS={self.knowledge_stock:.1f}, MC={self.production_cost:.4f} €/W, "
                f"backlog={order_backlog:.1f} MW vs cap={self.capacity:.1f} MW"
            ),
        )

    def _apply_capacity_change(self, action: str, change_pct: float) -> None:
        """Adjust manufacturing capacity respecting SI 3 constraints."""
        if action == "expand":
            delta = self.capacity * change_pct
            new_cap = self.capacity + delta
            max_cap = self.capacity * (1.0 + self.max_capacity_increase)
            self.capacity = min(new_cap, max_cap, self.capacity * 4.0)
        elif action == "reduce":
            delta = self.capacity * change_pct
            new_cap = self.capacity - delta
            min_cap = max(
                self.capacity * (1.0 - self.max_capacity_decrease),
                self.min_capacity,
            )
            self.capacity = max(new_cap, min_cap)

    def apply_llm_decision(self, decision: ManufacturerDecision, global_cumulative_mw: float = 500.0) -> None:
        """Execute the validated LLM decision on this manufacturer's state."""
        self.cumulative_production += self.sales

        self.knowledge_stock = update_knowledge_stock(
            ks_current=self.knowledge_stock,
            rd_spending=self.rd_spending,
            depreciation=self.knowledge_depreciation,
        )

        if decision.rd_focus == "efficiency":
            self.module_efficiency = min(
                0.30, self.module_efficiency * (1.0 + 0.005)
            )
        elif decision.rd_focus == "cost_reduction":
            self.production_cost = compute_production_cost(
                cumulative_production=max(global_cumulative_mw, self.cumulative_production),
                knowledge_stock=self.knowledge_stock,
                cp_initial=self.cp_initial,
                ks_initial=self.ks_initial,
                intercept=self.experience_curve_intercept,
                beta_learning_by_doing=self.beta_learning_by_doing,
                beta_learning_by_research=self.beta_learning_by_research,
            )

        self._apply_capacity_change(decision.action, decision.change_percentage)
        self.price = self.production_cost * (1.0 + self.mark_up)

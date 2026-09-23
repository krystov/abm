"""
Solar PV Policy Mix ABM — hybrid async model.

Manufacturers query an LLM (AsyncOpenAI) each tick via asyncio.gather;
Adopters and Installers run traditional TPB / NPV / labour-market formulas
on the main event loop without LLM involvement.
"""

import asyncio
import math
import random
from typing import Dict, List

from agents import Adopter, AdopterType, Installer, Manufacturer, Region
from environment.macro_environment import MacroEnvironment
from schemas import ManufacturerDecision
from submodels.adoption import (
    compute_irr,
    evaluate_adoption,
    information_index,
)
from submodels.experience_curve import compute_non_module_cost
from submodels.labor_market import adjust_workforce


# ═══════════════════════════════════════════════════════════════════════════
# Solar Model
# ═══════════════════════════════════════════════════════════════════════════


class SolarModel:
    """Hybrid async ABM for Germany's solar PV policy mix.

    Scheduling each tick (per Section 1.1.5 of the supplementary information):
      1. update macro variables
      2. ask adopters [ evaluate-and-adopt ]        ← local TPB + NPV
      3. ask installers [ manage-orders ]           ← local labour logic
      4. ask manufacturers [ produce-and-learn ]    ← asyncio.gather(LLM calls)
      5. tick → next month
    """

    def __init__(
        self,
        n_ticks: int = 312,
        n_adopters: int = 500,
        llm_model: str = "deepseek-chat",
        seed: int = 42,
        llm_adopter_fraction: float = 0.05,
        use_llm: bool = True,
        use_real_data: bool = False,
        n_seed_adopters: int = 0,
    ):
        self.n_ticks = n_ticks
        self.n_adopters = n_adopters
        self.llm_model = llm_model
        self.llm_adopter_fraction = llm_adopter_fraction
        self.use_llm = use_llm
        self.use_real_data = use_real_data
        self.n_seed_adopters = n_seed_adopters
        self.rng = random.Random(seed)

        # Macro data: synthetic or real historical
        if use_real_data:
            self.macro = MacroEnvironment.from_historical(n_ticks, seed=seed)
        else:
            self.macro = MacroEnvironment.from_synthetic(n_ticks, seed=seed)

        # Agents
        self.adopters: List[Adopter] = []
        self.manufacturers: Dict[str, Manufacturer] = {}
        self.installers: Dict[str, Installer] = {}

        # Runtime state
        self.tick: int = 0
        self.total_installed_mw: float = 0.0
        self.pending_installation_mw: float = 0.0  # adoption→installation queue
        self.history: List[dict] = []

        self._init_agents()

    # ------------------------------------------------------------------
    # Agent initialisation
    # ------------------------------------------------------------------

    def _init_agents(self) -> None:
        """Create agent populations with empirically-calibrated defaults."""

        # --- Adopters -------------------------------------------------
        # Population proportions from Table SI 1 (scaled 1:1000)
        residential_frac = 16_891 / (16_891 + 3_853 + 85)  # ≈ 0.81
        commercial_frac = 3_853 / (16_891 + 3_853 + 85)    # ≈ 0.185
        # utility_frac is remainder

        for i in range(self.n_adopters):
            r = self.rng.random()
            if r < residential_frac:
                at = AdopterType.RESIDENTIAL
                sys_min, sys_max = 0.5, 10.0
                roof_mean, roof_sd = 45.0, 20.0   # usable roof area [m²]
                elec_price = 0.25
                disc_rate = 0.04
                self_cons_mean = 0.30
                consumption_mean = 300.0
                consumption_sd = 100.0
            elif r < residential_frac + commercial_frac:
                at = AdopterType.COMMERCIAL_INDUSTRIAL
                sys_min, sys_max = 10.0, 40.0
                roof_mean, roof_sd = 150.0, 60.0
                elec_price = 0.20
                disc_rate = 0.05
                self_cons_mean = 0.20
                consumption_mean = 2_000.0
                consumption_sd = 500.0
            else:
                at = AdopterType.UTILITY_SCALE
                sys_min, sys_max = 40.0, 500.0  # cap for manageable scale
                roof_mean, roof_sd = 1_200.0, 800.0
                elec_price = 0.18
                disc_rate = 0.06
                self_cons_mean = 0.40
                consumption_mean = 50_000.0
                consumption_sd = 10_000.0

            # Roof area drives system size (physical constraint), clipped to the
            # category's calibrated system-size range (Table SI 1).
            roof_size = max(1.0, self.rng.gauss(roof_mean, roof_sd))
            power_density = 0.15  # kWp per m² of usable roof
            system_size = round(max(sys_min, min(sys_max, roof_size * power_density)), 2)

            # Personal adoption threshold: innovator→laggard spectrum
            # N(0.50, 0.08) clipped → ~2% below 0.32, ~2% above 0.68
            # Positively correlated with discount rate: cautious = high threshold + high discount
            personal_threshold = max(0.28, min(0.72, self.rng.gauss(0.50, 0.08)))
            # Personal discount rate: wider spread for income/patience heterogeneity
            # Correlated with threshold: laggards discount future more heavily
            personal_dr = 0.01 * (personal_threshold - 0.50) + self.rng.gauss(0, 0.02)

            adopter = Adopter(
                agent_id=i,
                adopter_type=at,
                location=(self.rng.uniform(0, 100), self.rng.uniform(0, 100)),
                roof_size=round(roof_size, 2),
                system_size=round(system_size, 2),
                self_consumption_rate=round(
                    max(0.0, min(1.0, self.rng.gauss(self_cons_mean, 0.05))), 4
                ),
                electricity_price=elec_price,
                discount_rate=disc_rate,
                personal_discount_rate=round(personal_dr, 4),
                discount_foreign_pv=round(self.rng.uniform(0.01, 0.03), 4),
                pv_orientation=round(max(0.1, self.rng.gauss(0.9, 0.2)), 2),
                environmental_awareness=round(
                    max(0.0, min(1.0, self.rng.gauss(0.5, 0.2))), 4
                ),
                personal_threshold=round(personal_threshold, 4),
                monthly_consumption_kwh=round(max(10.0, self.rng.gauss(consumption_mean, consumption_sd)), 1),
            )
            self.adopters.append(adopter)

        # --- Manufacturers --------------------------------------------
        # Domestic (Germany)
        dom_mfg = Manufacturer(
            manufacturer_id=1,
            region=Region.DOMESTIC,
            capacity=500.0,          # MW/month
            module_efficiency=0.15,  # 15 %
            production_cost=2.882,   # €/W (Table SI 53 intercept α)
            price=4.323,             # €/W (50 % mark-up on intercept)
            knowledge_stock=100.0,
            cumulative_production=500.0,
            stock=100.0,
            cp_initial=500.0,
            ks_initial=100.0,
            employees=2_000,
            labor_productivity=2.5,  # kWp/month/worker
            mark_up=0.50,
            rd_spending_ratio=0.05,
            rd_spending=3.0,         # knowledge-stock increment/month (β_LBR=−0.814)
            beta_learning_by_doing=-0.074,   # LR 5.0% (Table SI 53)
            beta_learning_by_research=-0.814,  # LR 43.1%
            experience_curve_intercept=2.882,
            knowledge_depreciation=0.008742,
            knowledge_spillover_in_ratio=0.15,
            knowledge_spillover_delay=12,
        )
        # Foreign (e.g. China)
        for_mfg = Manufacturer(
            manufacturer_id=2,
            region=Region.FOREIGN,
            capacity=2_000.0,         # MW/month — much larger
            module_efficiency=0.14,   # 14 %
            production_cost=2.448,    # €/W (Table SI 53 intercept α)
            price=3.182,              # €/W (30 % mark-up on intercept)
            knowledge_stock=200.0,
            cumulative_production=2_000.0,
            stock=500.0,
            cp_initial=2_000.0,
            ks_initial=200.0,
            employees=5_000,
            labor_productivity=4.0,
            mark_up=0.30,
            rd_spending_ratio=0.02,
            rd_spending=6.0,          # knowledge-stock increment/month
            beta_learning_by_doing=-0.448,   # LR 26.7% (Table SI 53)
            beta_learning_by_research=-0.074,  # LR 5.0%
            experience_curve_intercept=2.448,
            knowledge_depreciation=0.008742,
            knowledge_spillover_in_ratio=0.10,
            knowledge_spillover_delay=18,
        )
        self.manufacturers = {"domestic": dom_mfg, "foreign": for_mfg}

        # --- Installers -----------------------------------------------
        dom_inst = Installer(
            installer_id=1,
            region=Region.DOMESTIC,
            employees=1_500,
            labor_productivity=2.0,  # kWp/month/worker
            order_backlog=0.0,
            stock_domestic=50.0,
            stock_foreign=50.0,
            bos_cost=1.00,           # €/W
            mark_up=0.25,
            cumulative_installations=200.0,
            ci_initial=200.0,
            experience_curve_intercept_non_module=3.354,
            beta_learning_by_doing_non_module=-0.155,
        )
        for_inst = Installer(
            installer_id=2,
            region=Region.FOREIGN,
            employees=500,
            labor_productivity=3.0,
            order_backlog=0.0,
            stock_domestic=0.0,
            stock_foreign=200.0,
            bos_cost=0.60,           # €/W — cheaper abroad
            mark_up=0.20,
            cumulative_installations=800.0,
            ci_initial=800.0,
            experience_curve_intercept_non_module=3.354,
            beta_learning_by_doing_non_module=-0.155,
        )
        self.installers = {"domestic": dom_inst, "foreign": for_inst}

        # --- Seed initial adopters (representing 1000-roofs programme 1990-1993) ---
        # These are pre-existing installations before simulation start
        if self.n_seed_adopters > 0:
            seed_candidates = self.rng.sample(
                [a for a in self.adopters if a.environmental_awareness > 0.7],
                min(self.n_seed_adopters, len([a for a in self.adopters if a.environmental_awareness > 0.7])),
            )
            seed_mw = 0.0
            for adopter in seed_candidates:
                adopter.is_adopted = True
                seed_mw += adopter.system_size / 1000
            self.total_installed_mw += seed_mw
            # Credit domestic installer with these pre-existing installations
            self.installers["domestic"].cumulative_installations += seed_mw

    # ------------------------------------------------------------------
    # TPB + NPV sub-models — delegated to submodels.tpb
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Adopter step (async — LLM for a fraction, TPB for the rest)
    # ------------------------------------------------------------------

    async def _step_adopters(
        self,
        electricity_price: float,
        fit_tariff: float,
        module_price_domestic: float,
        module_price_foreign: float,
        bos_cost_domestic: float,
        information: float,
        irr: float,
    ) -> float:
        """Process un-adopted adopters; add new demand to pending installation queue.

        A fraction (llm_adopter_fraction) of eligible adopters use LLM via
        asyncio.gather; the rest use the deterministic two-stage adoption formula.
        Returns (total new demand MW, domestic-module demand MW, foreign-module
        demand MW) added to the installation queue this tick.
        """
        new_demand_mw = 0.0
        demand_domestic_mw = 0.0
        demand_foreign_mw = 0.0
        neighbour_ratios = self._compute_neighbour_ratios()
        market_maturity = sum(1 for a in self.adopters if a.is_adopted) / max(
            1, len(self.adopters)
        )

        # Split undecided adopters into LLM and formula batches
        undecided = [a for a in self.adopters if not a.is_adopted]
        llm_ids: set = set()

        if self.use_llm and self.llm_adopter_fraction > 0:
            n_llm = max(1, int(len(undecided) * self.llm_adopter_fraction))
            llm_batch = self.rng.sample(undecided, min(n_llm, len(undecided)))
            llm_ids = {a.agent_id for a in llm_batch}

            # --- LLM batch (async) ---
            llm_tasks = []
            for adopter in llm_batch:
                nb_ratio = neighbour_ratios.get(adopter.agent_id, 0.0)
                llm_tasks.append(
                    adopter.step_llm(
                        electricity_price=electricity_price,
                        fit_tariff=fit_tariff,
                        module_price_domestic=module_price_domestic,
                        module_price_foreign=module_price_foreign,
                        bos_cost=bos_cost_domestic,
                        neighbour_ratio=nb_ratio,
                        market_maturity=market_maturity,
                        information=information,
                        irr=irr,
                        model_name=self.llm_model,
                    )
                )

            llm_decisions = await asyncio.gather(*llm_tasks)
            for adopter, decision in zip(llm_batch, llm_decisions):
                adopter.apply_llm_decision(decision)
                if decision.will_adopt:
                    new_demand_mw += adopter.system_size / 1000
                    # LLM path does not select a module; default to domestic.
                    demand_domestic_mw += adopter.system_size / 1000

        # --- Formula batch (sync, fast) ---
        for adopter in undecided:
            if adopter.agent_id in llm_ids:
                continue  # already processed via LLM

            nb_ratio = neighbour_ratios.get(adopter.agent_id, 0.0)

            outcome = evaluate_adoption(
                is_residential=adopter.adopter_type == AdopterType.RESIDENTIAL,
                environmental_awareness=adopter.environmental_awareness,
                peer_effect=nb_ratio,
                information=information,
                irr=irr,
                system_size_kw=adopter.system_size,
                self_consumption_rate=adopter.self_consumption_rate,
                electricity_price=adopter.electricity_price,
                fit_tariff=fit_tariff,
                module_price_domestic=module_price_domestic,
                module_price_foreign=module_price_foreign,
                bos_cost=bos_cost_domestic,
                category_discount_rate=adopter.discount_rate,
                personal_discount_rate=adopter.personal_discount_rate,
                production_factor=adopter.pv_orientation,
                irradiation=adopter.irradiation,
            )

            adopter.ideation = outcome.ideation
            adopter.npv_domestic = outcome.npv_domestic
            adopter.npv_foreign = outcome.npv_foreign
            adopter.module_choice = outcome.module_choice
            adopter.attitude = outcome.ideation
            adopter.social_norm = nb_ratio
            adopter.pbc = market_maturity
            adopter.intention = outcome.ideation

            if outcome.will_adopt:
                adopter.is_adopted = True
                new_demand_mw += adopter.system_size / 1000
                if outcome.module_choice == "foreign":
                    demand_foreign_mw += adopter.system_size / 1000
                else:
                    demand_domestic_mw += adopter.system_size / 1000

        return new_demand_mw, demand_domestic_mw, demand_foreign_mw

    def _compute_neighbour_ratios(self, radius_km: float = 10.0) -> Dict[int, float]:
        """Compute fraction of adopted neighbours within `radius_km` for each adopter."""
        adopted_coords = [
            a.location for a in self.adopters if a.is_adopted
        ]
        if not adopted_coords:
            return {a.agent_id: 0.0 for a in self.adopters}

        ratios = {}
        for adopter in self.adopters:
            x, y = adopter.location
            neighbours = 0
            total_check = 0
            for other in self.adopters:
                if other.agent_id == adopter.agent_id:
                    continue
                dx = x - other.location[0]
                dy = y - other.location[1]
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= radius_km:
                    total_check += 1
                    if other.is_adopted:
                        neighbours += 1
            ratios[adopter.agent_id] = (
                neighbours / total_check if total_check > 0 else 0.0
            )
        return ratios

    # ------------------------------------------------------------------
    # Installer step (sync — runs on main thread)
    # ------------------------------------------------------------------

    def _step_installers(self) -> float:
        """Process installation queue constrained by installer capacity.

        New demand accumulates in pending_installation_mw and is fulfilled
        gradually as installer capacity allows — modelling the real-world
        pipeline between adoption decision and physical installation.
        """
        if self.pending_installation_mw <= 0:
            return 0.0

        dom = self.installers["domestic"]
        for_ = self.installers["foreign"]

        # Domestic installer capacity
        dom_capacity = dom.employees * dom.labor_productivity / 1000  # MW/month
        dom_fulfilled = min(self.pending_installation_mw * 0.7, dom_capacity)
        dom.cumulative_installations += dom_fulfilled
        dom.order_backlog = max(0.0, self.pending_installation_mw - dom_fulfilled)

        dom.bos_cost = compute_non_module_cost(
            cumulative_installations=dom.cumulative_installations,
            ci_initial=dom.ci_initial,
            intercept=dom.experience_curve_intercept_non_module,
            beta=dom.beta_learning_by_doing_non_module,
        )
        dom.employees = adjust_workforce(
            employees=dom.employees,
            order_backlog=dom.order_backlog,
            monthly_capacity=dom_capacity,
            min_employees=dom.min_employees,
        )

        # Foreign installer capacity
        for_capacity = for_.employees * for_.labor_productivity / 1000  # MW/month
        for_fulfilled = min(self.pending_installation_mw * 0.3, for_capacity)
        for_.cumulative_installations += for_fulfilled

        for_.bos_cost = compute_non_module_cost(
            cumulative_installations=for_.cumulative_installations,
            ci_initial=for_.ci_initial,
            intercept=for_.experience_curve_intercept_non_module,
            beta=for_.beta_learning_by_doing_non_module,
        )

        total_fulfilled = dom_fulfilled + for_fulfilled
        self.pending_installation_mw = max(0.0, self.pending_installation_mw - total_fulfilled)
        self.total_installed_mw += total_fulfilled

        return self.pending_installation_mw

    # ------------------------------------------------------------------
    # Manufacturer step (async — LLM calls via asyncio.gather)
    # ------------------------------------------------------------------

    async def _step_manufacturers(
        self,
        electricity_price: float,
        fit_tariff: float,
        order_backlog: float,
        tech_push_level: float,
        global_cumulative_mw: float = 500.0,
    ) -> Dict[str, ManufacturerDecision]:
        """Concurrently query all manufacturers via step_llm (or fallback if use_llm=False)."""
        if self.use_llm:
            tasks = []
            for key, mfg in self.manufacturers.items():
                tasks.append(
                    mfg.step_llm(
                        electricity_price=electricity_price,
                        fit_tariff=fit_tariff,
                        order_backlog=order_backlog,
                        tech_push_level=float(tech_push_level),
                        model_name=self.llm_model,
                        global_cumulative_mw=global_cumulative_mw,
                    )
                )
            decisions = await asyncio.gather(*tasks)
        else:
            decisions = []
            for key, mfg in self.manufacturers.items():
                decisions.append(
                    mfg._experience_curve_fallback(
                        electricity_price=electricity_price,
                        fit_tariff=fit_tariff,
                        order_backlog=order_backlog,
                        global_cumulative_mw=global_cumulative_mw,
                    )
                )

        # Apply each decision
        result = {}
        for (key, mfg), decision in zip(self.manufacturers.items(), decisions):
            if self.use_llm:
                mfg.apply_llm_decision(decision, global_cumulative_mw=global_cumulative_mw)
            result[key] = decision

        # Knowledge spillover: less advanced learns from leader (gap-proportional)
        dom = self.manufacturers["domestic"]
        for_ = self.manufacturers["foreign"]
        ks_gap_dom = for_.knowledge_stock - dom.knowledge_stock
        ks_gap_for = dom.knowledge_stock - for_.knowledge_stock
        if ks_gap_dom > 0:
            dom.knowledge_stock += dom.knowledge_spillover_in_ratio * ks_gap_dom / 12
        if ks_gap_for > 0:
            for_.knowledge_stock += for_.knowledge_spillover_in_ratio * ks_gap_for / 12

        return result

    # ------------------------------------------------------------------
    # Full tick
    # ------------------------------------------------------------------

    async def step(self) -> dict:
        """Execute one tick (month) of the simulation."""
        t = self.tick

        # 1. Update macro variables ────────────────────────────────────
        mv = self.macro.get(t)
        electricity_price = mv["electricity_price"]
        fit_tariff = mv["fit_tariff"]
        media = mv["media_coverage"]
        tech_push = mv["tech_push_level"]
        global_cum_mw = mv.get("global_cumulative_mw", 500.0)

        # 2. Adopter decisions (async — LLM batch + formula) ─────────
        dom_mfg = self.manufacturers["domestic"]
        for_mfg = self.manufacturers["foreign"]
        dom_inst = self.installers["domestic"]

        # Available information IN_t (world cumulative deployment) and the
        # average-household IRR used as economic attractiveness in ideation.
        information = information_index(global_cum_mw)
        irr = compute_irr(
            system_price_per_w=dom_mfg.price + dom_inst.bos_cost,
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
        )

        new_demand_mw, demand_domestic_mw, demand_foreign_mw = await self._step_adopters(
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            module_price_domestic=dom_mfg.price,
            module_price_foreign=for_mfg.price,
            bos_cost_domestic=dom_inst.bos_cost,
            information=information,
            irr=irr,
        )
        self.pending_installation_mw += new_demand_mw

        # Track manufacturer module sales (MW) from adopter module choice.
        self.manufacturers["domestic"].sales = demand_domestic_mw
        self.manufacturers["foreign"].sales = demand_foreign_mw

        # 3. Installer response (sync) — draws from installation queue ─
        order_backlog = self._step_installers()

        # 4. Manufacturer decisions (async — LLM) ──────────────────────
        mfg_decisions = await self._step_manufacturers(
            electricity_price=electricity_price,
            fit_tariff=fit_tariff,
            order_backlog=order_backlog,
            tech_push_level=float(tech_push),
            global_cumulative_mw=global_cum_mw,
        )

        # 5. Bookkeeping ───────────────────────────────────────────────
        n_adopted = sum(1 for a in self.adopters if a.is_adopted)
        record = {
            "tick": t,
            "year": 1991 + t / 12,
            "electricity_price": round(electricity_price, 4),
            "fit_tariff": round(fit_tariff, 4),
            "media_coverage": round(media, 4),
            "information": round(information, 4),
            "irr": round(irr, 4),
            "tech_push": tech_push,
            "new_demand_mw": round(new_demand_mw, 4),
            "pending_installation_mw": round(self.pending_installation_mw, 4),
            "order_backlog_mw": round(order_backlog, 4),
            "total_installed_mw": round(self.total_installed_mw, 2),
            "n_adopted": n_adopted,
            "domestic_price": round(dom_mfg.price, 4),
            "foreign_price": round(for_mfg.price, 4),
            "domestic_cost": round(dom_mfg.production_cost, 4),
            "foreign_cost": round(for_mfg.production_cost, 4),
            "domestic_efficiency": round(dom_mfg.module_efficiency, 4),
            "foreign_efficiency": round(for_mfg.module_efficiency, 4),
            "domestic_capacity": round(dom_mfg.capacity, 2),
            "foreign_capacity": round(for_mfg.capacity, 2),
            "domestic_decision": mfg_decisions.get("domestic", None),
            "foreign_decision": mfg_decisions.get("foreign", None),
        }
        self.history.append(record)

        self.tick += 1
        return record

    # ------------------------------------------------------------------
    # Run full simulation
    # ------------------------------------------------------------------

    async def run(self, verbose: bool = True) -> List[dict]:
        """Run the model for all ticks."""
        for t in range(self.n_ticks):
            record = await self.step()
            if verbose and t % 12 == 0:
                year = 1991 + t // 12
                print(
                    f"[{year}] tick {t:4d} | "
                    f"FiT={record['fit_tariff']:.3f} | "
                    f"adopted={record['n_adopted']:5d}/{self.n_adopters} | "
                    f"installed={record['total_installed_mw']:8.1f} MW | "
                    f"dom MC={record['domestic_cost']:.4f} EUR/W | "
                    f"for MC={record['foreign_cost']:.4f} EUR/W"
                )
        return self.history

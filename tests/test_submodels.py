"""Tests for submodels: TPB, experience curve, labour market."""

import math

from submodels.tpb import compute_npv, compute_tpb_intention
from submodels.experience_curve import (
    compute_non_module_cost,
    compute_production_cost,
    learning_rate_to_beta,
    update_knowledge_stock,
)
from submodels.labor_market import adjust_workforce, compute_bos_cost


class TestNPV:
    def test_negative_npv_with_zero_fit(self):
        """Without FiT, NPV should be negative for typical system."""
        npv = compute_npv(
            system_size_kw=5.0,
            module_price_per_w=1.50,
            bos_cost_per_w=1.00,
            electricity_price=0.25,
            fit_tariff=0.0,
            self_consumption_rate=0.30,
            discount_rate=0.04,
        )
        assert npv < 0, f"Expected negative NPV without FiT, got {npv}"

    def test_positive_npv_with_high_fit(self):
        """High FiT should make NPV positive."""
        npv = compute_npv(
            system_size_kw=5.0,
            module_price_per_w=0.50,  # cheap modules
            bos_cost_per_w=0.50,
            electricity_price=0.30,
            fit_tariff=0.50,  # high FiT
            self_consumption_rate=0.30,
            discount_rate=0.04,
        )
        assert npv > 0, f"Expected positive NPV with high FiT, got {npv}"


class TestTPBIntention:
    def test_high_env_awareness_shortcut(self):
        """High env awareness gives graduated boost above base attitude."""
        intention_high = compute_tpb_intention(
            environmental_awareness=0.90,
            npv=-5000,
            neighbour_adoption_ratio=0.0,
            market_maturity=0.0,
        )
        intention_mid = compute_tpb_intention(
            environmental_awareness=0.50,
            npv=-5000,
            neighbour_adoption_ratio=0.0,
            market_maturity=0.0,
        )
        assert intention_high > intention_mid, (
            f"Higher env awareness should boost intention: "
            f"high={intention_high:.4f} vs mid={intention_mid:.4f}"
        )

    def test_low_intention_no_signals(self):
        """No neighbours, no market, bad NPV → low intention."""
        intention = compute_tpb_intention(
            environmental_awareness=0.3,
            npv=-10000,
            neighbour_adoption_ratio=0.0,
            market_maturity=0.0,
        )
        assert intention < 0.5


class TestLearningRateToBeta:
    def test_5_percent(self):
        assert math.isclose(learning_rate_to_beta(0.05), -0.074, rel_tol=1e-2)

    def test_10_2_percent(self):
        assert math.isclose(learning_rate_to_beta(0.102), -0.155, rel_tol=1e-2)

    def test_26_7_percent(self):
        assert math.isclose(learning_rate_to_beta(0.267), -0.448, rel_tol=1e-2)

    def test_43_1_percent(self):
        assert math.isclose(learning_rate_to_beta(0.431), -0.814, rel_tol=1e-2)

    def test_roundtrip(self):
        """β = log2(1 − LR) ⇔ LR = 1 − 2^β."""
        for lr in (0.05, 0.102, 0.267, 0.431):
            beta = learning_rate_to_beta(lr)
            assert math.isclose(1.0 - 2.0 ** beta, lr, rel_tol=1e-6)

    def test_rejects_out_of_range(self):
        for bad in (-0.1, 1.0, 1.5):
            try:
                learning_rate_to_beta(bad)
                assert False, f"expected ValueError for {bad}"
            except ValueError:
                pass


class TestExperienceCurve:
    def test_cost_decreases_with_more_production(self):
        """More cumulative production → lower cost (β_LBD negative)."""
        low_cp = compute_production_cost(
            cumulative_production=100.0,
            knowledge_stock=100.0,
            cp_initial=100.0,
            ks_initial=100.0,
            intercept=2.882,
            beta_learning_by_doing=-0.074,
            beta_learning_by_research=-0.814,
        )
        high_cp = compute_production_cost(
            cumulative_production=10000.0,
            knowledge_stock=100.0,
            cp_initial=100.0,
            ks_initial=100.0,
            intercept=2.882,
            beta_learning_by_doing=-0.074,
            beta_learning_by_research=-0.814,
        )
        assert high_cp < low_cp, "Cost should decrease with cumulative production"

    def test_cost_decreases_with_more_knowledge(self):
        """More knowledge stock → lower cost (β_LBR negative)."""
        low_ks = compute_production_cost(
            cumulative_production=1000.0,
            knowledge_stock=100.0,
            cp_initial=100.0,
            ks_initial=100.0,
            intercept=2.882,
            beta_learning_by_doing=-0.074,
            beta_learning_by_research=-0.814,
        )
        high_ks = compute_production_cost(
            cumulative_production=1000.0,
            knowledge_stock=10000.0,
            cp_initial=100.0,
            ks_initial=100.0,
            intercept=2.882,
            beta_learning_by_doing=-0.074,
            beta_learning_by_research=-0.814,
        )
        assert high_ks < low_ks, "Cost should decrease with knowledge stock"

    def test_paper_doubling_learning_rates(self):
        """Doubling a driver reduces cost by exactly the learning rate (Table SI 53)."""
        # Domestic LBD: 5% LR → doubling CP multiplies cost by 1 − 0.05 = 0.95.
        base = compute_production_cost(
            cumulative_production=1000.0, knowledge_stock=100.0,
            cp_initial=500.0, ks_initial=100.0, intercept=2.882,
            beta_learning_by_doing=-0.074, beta_learning_by_research=-0.814,
        )
        doubled = compute_production_cost(
            cumulative_production=2000.0, knowledge_stock=100.0,
            cp_initial=500.0, ks_initial=100.0, intercept=2.882,
            beta_learning_by_doing=-0.074, beta_learning_by_research=-0.814,
        )
        # Only CP doubles (KS held at baseline), so ratio is 2^β_LBD = 1 − 0.05.
        assert math.isclose(doubled / base, 2.0 ** -0.074, rel_tol=1e-6)
        assert math.isclose(doubled / base, 0.95, rel_tol=1e-6)

    def test_update_knowledge_stock(self):
        """Knowledge stock should accumulate with R&D and depreciate."""
        ks = update_knowledge_stock(100.0, 10.0, depreciation=0.01)
        expected = 0.99 * 100.0 + 10.0  # 109.0
        assert math.isclose(ks, expected, rel_tol=1e-6)

    def test_non_module_cost(self):
        """BOS cost should decrease with cumulative installations."""
        low = compute_non_module_cost(100.0, ci_initial=100.0)
        high = compute_non_module_cost(10000.0, ci_initial=100.0)
        assert high < low

    def test_non_module_paper_beta(self):
        """Non-module β = −0.155 (10.2% LR) → doubling halves by 2^−0.155."""
        base = compute_non_module_cost(200.0, ci_initial=200.0)
        doubled = compute_non_module_cost(400.0, ci_initial=200.0)
        assert math.isclose(doubled / base, 2.0 ** -0.155, rel_tol=1e-6)


class TestLaborMarket:
    def test_hire_when_backlog_high(self):
        """High backlog should trigger hiring."""
        new_emp = adjust_workforce(
            employees=1000,
            order_backlog=100.0,
            monthly_capacity=10.0,  # 10 months to clear → above threshold
            min_employees=100,
        )
        assert new_emp > 1000

    def test_fire_when_backlog_low(self):
        """Low backlog should trigger firing."""
        new_emp = adjust_workforce(
            employees=1000,
            order_backlog=1.0,
            monthly_capacity=10.0,  # 0.1 months to clear → below threshold
            min_employees=100,
        )
        assert new_emp < 1000

    def test_respect_min_employees(self):
        """Should not go below min_employees."""
        new_emp = adjust_workforce(
            employees=50,
            order_backlog=0.0,
            monthly_capacity=10.0,
            min_employees=100,
        )
        assert new_emp == 100

    def test_bos_cost_rises_with_utilisation(self):
        """Higher backlog per employee → higher BOS cost."""
        low = compute_bos_cost(1.0, order_backlog=10, employees=100)
        high = compute_bos_cost(1.0, order_backlog=100, employees=10)
        assert high > low

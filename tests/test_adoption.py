"""Tests for the paper-faithful two-stage adoption sub-model."""

import math

from submodels.adoption import (
    AdoptionEvaluation,
    compute_irr,
    evaluate_adoption,
    ideation_score,
    information_index,
    npv,
    scale_effect,
)


class TestScaleEffect:
    def test_small_system_flat_scale(self):
        assert scale_effect(0.5) == 1.2

    def test_large_system_declining_scale(self):
        assert scale_effect(5.0) < 1.2
        assert scale_effect(100.0) < scale_effect(10.0)

    def test_one_kwp_boundary(self):
        assert scale_effect(1.0) == 1.1246  # 1.1246 * 1^-0.051


class TestInformationIndex:
    def test_in_range(self):
        for mw in (0.0, 500.0, 40_000.0, 300_000.0):
            assert 0.0 <= information_index(mw) <= 1.0

    def test_monotonic_increasing(self):
        assert information_index(40_000.0) > information_index(500.0)
        assert information_index(300_000.0) > information_index(40_000.0)

    def test_saturates(self):
        assert information_index(300_000.0) > 0.9


class TestIRR:
    def test_zero_without_fit(self):
        irr = compute_irr(
            system_price_per_w=3.25, electricity_price=0.25, fit_tariff=0.0
        )
        assert irr == 0.0

    def test_positive_with_high_fit(self):
        irr = compute_irr(
            system_price_per_w=1.0, electricity_price=0.30, fit_tariff=0.50
        )
        assert irr > 0.0


class TestNPV:
    def test_negative_without_fit(self):
        val = npv(
            system_size_kw=5.0,
            system_price_per_w=3.25,
            electricity_price=0.25,
            fit_tariff=0.0,
            self_consumption_rate=0.30,
            discount_rate=0.04,
        )
        assert val < 0

    def test_positive_with_high_fit(self):
        val = npv(
            system_size_kw=5.0,
            system_price_per_w=1.0,
            electricity_price=0.30,
            fit_tariff=0.50,
            self_consumption_rate=0.30,
            discount_rate=0.04,
        )
        assert val > 0


class TestEvaluateAdoption:
    def _base_kwargs(self, **overrides):
        kwargs = dict(
            is_residential=True,
            environmental_awareness=0.5,
            peer_effect=0.0,
            information=0.0,
            irr=0.0,
            system_size_kw=5.0,
            self_consumption_rate=0.30,
            electricity_price=0.25,
            fit_tariff=0.0,
            module_price_domestic=2.0,
            module_price_foreign=1.5,
            bos_cost=1.0,
            category_discount_rate=0.04,
            personal_discount_rate=0.0,
        )
        kwargs.update(overrides)
        return kwargs

    def test_no_ideation_no_adopt(self):
        out = evaluate_adoption(**self._base_kwargs(environmental_awareness=0.4))
        assert out.will_adopt is False
        assert out.developed_idea is False

    def test_early_adopter_installs_directly(self):
        out = evaluate_adoption(
            **self._base_kwargs(
                environmental_awareness=0.95, information=0.1, is_residential=True,
            )
        )
        assert out.will_adopt is True
        assert out.early_adopter is True
        assert out.module_choice == "domestic"

    def test_non_residential_does_not_skip(self):
        # High awareness but commercial → must pass NPV evaluation.
        out = evaluate_adoption(
            **self._base_kwargs(
                environmental_awareness=0.95,
                information=0.1,
                is_residential=False,
                fit_tariff=0.0,
            )
        )
        assert out.early_adopter is False
        # Without FiT the NPV is negative → no adoption.
        assert out.will_adopt is False

    def test_economic_adoption_prefers_domestic_on_small_gap(self):
        # Foreign only slightly cheaper: the 1.1% foreign discount premium
        # makes domestic preferred (paper's stated "preference for domestic").
        out = evaluate_adoption(
            **self._base_kwargs(
                is_residential=False,
                environmental_awareness=0.6,
                peer_effect=0.5,
                information=0.5,
                irr=0.2,
                fit_tariff=0.45,
                electricity_price=0.30,
                module_price_domestic=0.5,
                module_price_foreign=0.4,
                bos_cost=0.5,
            )
        )
        assert out.will_adopt is True
        assert out.early_adopter is False
        assert out.module_choice == "domestic"

    def test_economic_adoption_prefers_cheaper_foreign(self):
        # Foreign much cheaper → overcomes the discount premium.
        out = evaluate_adoption(
            **self._base_kwargs(
                is_residential=False,
                environmental_awareness=0.6,
                peer_effect=0.5,
                information=0.5,
                irr=0.2,
                fit_tariff=0.45,
                electricity_price=0.30,
                module_price_domestic=0.5,
                module_price_foreign=0.2,
                bos_cost=0.5,
            )
        )
        assert out.will_adopt is True
        assert out.early_adopter is False
        assert out.module_choice == "foreign"

    def test_ideation_score_weights_sum_to_one(self):
        # With all four variables equal to 1, the score must equal 1.0.
        assert math.isclose(ideation_score(1.0, 1.0, 1.0, 1.0), 1.0, rel_tol=1e-9)

    def test_returns_evaluation_type(self):
        out = evaluate_adoption(**self._base_kwargs())
        assert isinstance(out, AdoptionEvaluation)

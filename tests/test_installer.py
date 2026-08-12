"""Tests for Installer agent class."""

from agents import Installer, Region


class TestInstaller:
    def test_creation_domestic(self):
        inst = Installer(
            installer_id=1,
            region=Region.DOMESTIC,
            employees=1500,
            labor_productivity=2.0,
            bos_cost=1.00,
            mark_up=0.25,
            cumulative_installations=200.0,
        )
        assert inst.installer_id == 1
        assert inst.region == Region.DOMESTIC
        assert inst.employees == 1500
        assert inst.bos_cost == 1.00

    def test_creation_foreign(self):
        inst = Installer(
            installer_id=2,
            region=Region.FOREIGN,
            employees=500,
            labor_productivity=3.0,
            bos_cost=0.60,
            mark_up=0.20,
            cumulative_installations=800.0,
        )
        assert inst.region == Region.FOREIGN

    def test_order_backlog_default_zero(self):
        inst = Installer(
            installer_id=1,
            region=Region.DOMESTIC,
        )
        assert inst.order_backlog == 0.0

    def test_inventory_defaults(self):
        inst = Installer(
            installer_id=1,
            region=Region.DOMESTIC,
        )
        assert inst.stock_domestic == 0.0
        assert inst.stock_foreign == 0.0

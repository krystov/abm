"""
Backward-compatible re-export shim for the agents package.

All agent definitions now live in agents/{adopter,manufacturer,installer}.py.
This module re-exports them so existing imports from 'agents' continue to work.
"""

from agents.adopter import Adopter, AdopterType
from agents.manufacturer import Manufacturer, Region, SupplierType
from agents.installer import Installer
from agents.agent_framework import BaseLLMAgent, ConversationMemory

__all__ = [
    "Adopter",
    "AdopterType",
    "Installer",
    "Manufacturer",
    "Region",
    "SupplierType",
    "BaseLLMAgent",
    "ConversationMemory",
]

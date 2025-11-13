"""
Shared components for Stage 4 multi-agent implementations.

Contains specialist agents and utilities used by both Supervisor 1 and Supervisor 2.
"""

from .specialist_agents import (
    create_order_operations_agent,
    create_product_inventory_agent,
    create_customer_account_agent,
    create_all_specialists,
)

from .specialist_prompts import (
    ORDER_OPERATIONS_PROMPT,
    PRODUCT_INVENTORY_PROMPT,
    CUSTOMER_ACCOUNT_PROMPT,
)

from .supervisor_prompts import SUPERVISOR_PROMPT

__all__ = [
    "create_order_operations_agent",
    "create_product_inventory_agent",
    "create_customer_account_agent",
    "create_all_specialists",
    "ORDER_OPERATIONS_PROMPT",
    "PRODUCT_INVENTORY_PROMPT",
    "CUSTOMER_ACCOUNT_PROMPT",
    "SUPERVISOR_PROMPT",
]

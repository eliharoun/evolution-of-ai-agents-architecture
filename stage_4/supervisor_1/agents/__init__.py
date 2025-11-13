"""
Agent components for Stage 4 Supervisor 1 implementation.
"""

# Import specialist agents from common (shared location)
from stage_4.common.specialist_agents import (
    create_order_operations_agent,
    create_product_inventory_agent,
    create_customer_account_agent,
    create_all_specialists,
)

__all__ = [
    "create_order_operations_agent",
    "create_product_inventory_agent",
    "create_customer_account_agent",
    "create_all_specialists",
]
